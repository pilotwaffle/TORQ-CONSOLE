"""
TORQ Knowledge Plane API Module

FastAPI endpoints for knowledge storage, retrieval, and management.
Implements semantic search using embeddings and Supabase for persistence.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from enum import Enum

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ============================================================================
# Request/Response Models
# =============================================================================

class KnowledgeCategory(str, Enum):
    """Knowledge entry categories."""
    CODE = "code"
    DOCUMENTATION = "documentation"
    CONCEPT = "concept"
    BEST_PRACTICE = "best_practice"
    TROUBLESHOOTING = "troubleshooting"
    ARCHITECTURE = "architecture"
    CONFIGURATION = "configuration"
    WORKFLOW = "workflow"
    OTHER = "other"


class KnowledgeStoreRequest(BaseModel):
    """Request to store knowledge entry."""
    content: str = Field(..., description="The knowledge content to store")
    title: Optional[str] = Field(None, description="Optional title for the knowledge")
    category: KnowledgeCategory = Field(KnowledgeCategory.OTHER, description="Knowledge category")
    tags: List[str] = Field(default_factory=list, description="Tags for organization")
    source: Optional[str] = Field(None, description="Source of the knowledge (e.g., agent, user)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    embedding: Optional[List[float]] = Field(None, description="Pre-computed embedding (optional)")


class KnowledgeSearchRequest(BaseModel):
    """Request to search knowledge."""
    query: str = Field(..., description="Search query")
    category: Optional[KnowledgeCategory] = Field(None, description="Filter by category")
    tags: List[str] = Field(default_factory=list, description="Filter by tags")
    limit: int = Field(10, ge=1, le=100, description="Maximum results to return")
    threshold: float = Field(0.7, ge=0.0, le=1.0, description="Similarity threshold")


class KnowledgeEntry(BaseModel):
    """A knowledge entry."""
    id: str
    content: str
    title: Optional[str]
    category: KnowledgeCategory
    tags: List[str]
    source: Optional[str]
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str
    similarity: Optional[float] = None


class KnowledgeStoreResponse(BaseModel):
    """Response from knowledge store operation."""
    success: bool
    id: str
    message: str
    created_at: str


class KnowledgeSearchResponse(BaseModel):
    """Response from knowledge search."""
    query: str
    total: int
    results: List[KnowledgeEntry]
    execution_time_ms: float


class KnowledgeRecentResponse(BaseModel):
    """Response from recent knowledge query."""
    total: int
    results: List[KnowledgeEntry]


class KnowledgeStatsResponse(BaseModel):
    """Knowledge base statistics."""
    total_entries: int
    by_category: Dict[str, int]
    by_source: Dict[str, int]
    oldest_entry: Optional[str]
    newest_entry: Optional[str]
    total_tags: int
    unique_tags: List[str]


# ============================================================================
# Knowledge Storage Backend
# =============================================================================

class KnowledgeStorageBackend:
    """Handles knowledge persistence with Supabase."""

    def __init__(self):
        self.supabase_url = os.environ.get("SUPABASE_URL")
        self.supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        self.openai_key = os.environ.get("OPENAI_API_KEY")
        self.redis_url = os.environ.get("REDIS_URL")

        self._table_name = "torq_knowledge"
        self._cache_enabled = bool(self.redis_url)
        self._cache_ttl = 3600  # 1 hour

    def is_configured(self) -> bool:
        """Check if storage backend is properly configured."""
        return bool(self.supabase_url and self.supabase_key)

    async def health_check(self) -> Dict[str, Any]:
        """Health check for knowledge storage."""
        status = {
            "supabase_configured": bool(self.supabase_url),
            "openai_configured": bool(self.openai_key),
            "redis_configured": bool(self.redis_url),
            "table_exists": False
        }

        if self.supabase_url:
            try:
                # Try to query the table
                result = await self._execute_query(
                    method="GET",
                    path=f"/rest/v1/{self._table_name}",
                    params={"select": "id", "limit": 1}
                )
                status["table_exists"] = result is not None
            except Exception as e:
                logger.warning(f"Knowledge table check failed: {e}")
                status["table_check_error"] = str(e)

        return status

    async def initialize_table(self) -> bool:
        """Initialize the knowledge table in Supabase if it doesn't exist."""
        if not self.supabase_url or not self.supabase_key:
            logger.warning("Supabase not configured, skipping table initialization")
            return False

        try:
            # Check if table exists first
            health = await self.health_check()
            if health.get("table_exists"):
                logger.info("Knowledge table already exists")
                return True

            # Create table via SQL
            create_sql = """
            CREATE TABLE IF NOT EXISTS torq_knowledge (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                title TEXT,
                category TEXT NOT NULL,
                tags TEXT[] DEFAULT '{}',
                source TEXT,
                metadata JSONB DEFAULT '{}',
                embedding VECTOR(1536),
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS idx_knowledge_category ON torq_knowledge(category);
            CREATE INDEX IF NOT EXISTS idx_knowledge_tags ON torq_knowledge USING GIN(tags);
            CREATE INDEX IF NOT EXISTS idx_knowledge_created ON torq_knowledge(created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_knowledge_embedding ON torq_knowledge USING ivfflat(embedding vector_cosine_ops) WITH (lists = 100);
            """

            await self._execute_sql(create_sql)
            logger.info("Knowledge table initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize knowledge table: {e}")
            return False

    async def store(self, request: KnowledgeStoreRequest) -> KnowledgeStoreResponse:
        """Store a knowledge entry."""
        import uuid
        import httpx

        entry_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        # Generate embedding if not provided
        embedding = request.embedding
        if embedding is None and self.openai_key:
            embedding = await self._generate_embedding(request.content)

        # Prepare entry data
        entry_data = {
            "id": entry_id,
            "content": request.content,
            "title": request.title,
            "category": request.category.value,
            "tags": request.tags,
            "source": request.source,
            "metadata": request.metadata,
            "created_at": now,
            "updated_at": now
        }

        if embedding:
            entry_data["embedding"] = embedding

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.supabase_url}/rest/v1/{self._table_name}",
                    headers={
                        "apikey": self.supabase_key,
                        "Authorization": f"Bearer {self.supabase_key}",
                        "Content-Type": "application/json"
                    },
                    json=entry_data,
                    timeout=30.0
                )
                response.raise_for_status()

            # Invalidate cache
            await self._invalidate_cache()

            return KnowledgeStoreResponse(
                success=True,
                id=entry_id,
                message="Knowledge stored successfully",
                created_at=now
            )

        except Exception as e:
            logger.error(f"Failed to store knowledge: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to store knowledge: {str(e)}")

    async def search(self, request: KnowledgeSearchRequest) -> KnowledgeSearchResponse:
        """Search for knowledge entries."""
        import time
        start_time = time.time()

        try:
            if self.openai_key:
                # Semantic search with embeddings
                results = await self._semantic_search(request)
            else:
                # Fallback to text search
                results = await self._text_search(request)

            execution_time = (time.time() - start_time) * 1000

            return KnowledgeSearchResponse(
                query=request.query,
                total=len(results),
                results=results[:request.limit],
                execution_time_ms=round(execution_time, 2)
            )

        except Exception as e:
            logger.error(f"Failed to search knowledge: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to search knowledge: {str(e)}")

    async def get_recent(self, limit: int = 20) -> KnowledgeRecentResponse:
        """Get recent knowledge entries."""
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.supabase_url}/rest/v1/{self._table_name}",
                    headers={
                        "apikey": self.supabase_key,
                        "Authorization": f"Bearer {self.supabase_key}"
                    },
                    params={
                        "select": "id,content,title,category,tags,source,metadata,created_at,updated_at",
                        "order": "created_at.desc",
                        "limit": limit
                    },
                    timeout=30.0
                )
                response.raise_for_status()

            entries = [
                KnowledgeEntry(**entry, similarity=None)
                for entry in response.json()
            ]

            return KnowledgeRecentResponse(
                total=len(entries),
                results=entries
            )

        except Exception as e:
            logger.error(f"Failed to get recent knowledge: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get recent knowledge: {str(e)}")

    async def get_stats(self) -> KnowledgeStatsResponse:
        """Get knowledge base statistics."""
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                # Get all entries for stats
                response = await client.get(
                    f"{self.supabase_url}/rest/v1/{self._table_name}",
                    headers={
                        "apikey": self.supabase_key,
                        "Authorization": f"Bearer {self.supabase_key}"
                    },
                    params={
                        "select": "id,category,source,tags,created_at",
                        "limit": 1000
                    },
                    timeout=30.0
                )
                response.raise_for_status()

            entries = response.json()

            # Calculate stats
            by_category: Dict[str, int] = {}
            by_source: Dict[str, int] = {}
            all_tags: set = set()
            timestamps = []

            for entry in entries:
                cat = entry.get("category", "other")
                by_category[cat] = by_category.get(cat, 0) + 1

                src = entry.get("source", "unknown")
                by_source[src] = by_source.get(src, 0) + 1

                tags = entry.get("tags", [])
                if isinstance(tags, list):
                    all_tags.update(tags)

                created = entry.get("created_at")
                if created:
                    timestamps.append(created)

            return KnowledgeStatsResponse(
                total_entries=len(entries),
                by_category=by_category,
                by_source=by_source,
                oldest_entry=min(timestamps) if timestamps else None,
                newest_entry=max(timestamps) if timestamps else None,
                total_tags=len(all_tags),
                unique_tags=sorted(list(all_tags))[:50]  # Limit to 50 tags
            )

        except Exception as e:
            logger.error(f"Failed to get knowledge stats: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get knowledge stats: {str(e)}")

    async def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding using OpenAI API."""
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.openai_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "text-embedding-3-small",
                        "input": text[:8191]  # OpenAI limit
                    },
                    timeout=30.0
                )
                response.raise_for_status()

            data = response.json()
            return data["data"][0]["embedding"]

        except Exception as e:
            logger.warning(f"Failed to generate embedding: {e}")
            return None

    async def _semantic_search(self, request: KnowledgeSearchRequest) -> List[KnowledgeEntry]:
        """Perform semantic search using embeddings."""
        query_embedding = await self._generate_embedding(request.query)
        if not query_embedding:
            return await self._text_search(request)

        import httpx

        try:
            # Use Supabase RPC for vector similarity search
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.supabase_url}/rest/v1/rpc/match_knowledge",
                    headers={
                        "apikey": self.supabase_key,
                        "Authorization": f"Bearer {self.supabase_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "query_embedding": query_embedding,
                        "match_threshold": request.threshold,
                        "match_count": request.limit
                    },
                    timeout=30.0
                )

                if response.status_code == 404:
                    # RPC function not found, fall back to text search
                    return await self._text_search(request)

                response.raise_for_status()

            results = []
            for entry in response.json():
                results.append(KnowledgeEntry(
                    id=entry["id"],
                    content=entry["content"],
                    title=entry.get("title"),
                    category=entry["category"],
                    tags=entry.get("tags", []),
                    source=entry.get("source"),
                    metadata=entry.get("metadata", {}),
                    created_at=entry["created_at"],
                    updated_at=entry["updated_at"],
                    similarity=entry.get("similarity")
                ))

            return results

        except Exception as e:
            logger.warning(f"Semantic search failed, falling back to text search: {e}")
            return await self._text_search(request)

    async def _text_search(self, request: KnowledgeSearchRequest) -> List[KnowledgeEntry]:
        """Perform basic text search."""
        import httpx

        try:
            params = {
                "select": "id,content,title,category,tags,source,metadata,created_at,updated_at",
                "order": "created_at.desc",
                "limit": request.limit
            }

            # Add filters
            if request.category:
                params["category"] = f"eq.{request.category.value}"

            # Add text search
            if request.query:
                params["content"] = f"ilike.*{request.query}*"

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.supabase_url}/rest/v1/{self._table_name}",
                    headers={
                        "apikey": self.supabase_key,
                        "Authorization": f"Bearer {self.supabase_key}"
                    },
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()

            results = []
            for entry in response.json():
                results.append(KnowledgeEntry(**entry, similarity=None))

            return results

        except Exception as e:
            logger.error(f"Text search failed: {e}")
            return []

    async def _execute_query(self, method: str, path: str, params: Dict = None, json_data: Dict = None) -> Any:
        """Execute a Supabase query."""
        import httpx

        url = f"{self.supabase_url}{path}"
        headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(url, headers=headers, params=params, timeout=30.0)
            elif method == "POST":
                response = await client.post(url, headers=headers, json=json_data, timeout=30.0)
            elif method == "PATCH":
                response = await client.patch(url, headers=headers, json=json_data, timeout=30.0)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers, params=params, timeout=30.0)
            else:
                raise ValueError(f"Unknown method: {method}")

            response.raise_for_status()
            return response.json() if response.content else None

    async def _execute_sql(self, sql: str) -> Any:
        """Execute raw SQL via Supabase."""
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.supabase_url}/rest/v1/rpc/exec_sql",
                headers={
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                    "Content-Type": "application/json"
                },
                json={"sql": sql},
                timeout=30.0
            )
            return response.json()

    async def _invalidate_cache(self):
        """Invalidate Redis cache if enabled."""
        if not self._cache_enabled:
            return

        try:
            import redis.asyncio as redis
            client = redis.from_url(self.redis_url)
            await client.delete("knowledge:recent", "knowledge:stats")
            await client.close()
        except Exception as e:
            logger.warning(f"Failed to invalidate cache: {e}")


# Global backend instance
_backend: Optional[KnowledgeStorageBackend] = None


def get_backend() -> KnowledgeStorageBackend:
    """Get or create the knowledge storage backend."""
    global _backend
    if _backend is None:
        _backend = KnowledgeStorageBackend()
    return _backend


# ============================================================================
# FastAPI Router
# =============================================================================

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.post("/store", response_model=KnowledgeStoreResponse)
async def store_knowledge(request: KnowledgeStoreRequest):
    """Store a new knowledge entry."""
    backend = get_backend()

    if not backend.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Knowledge storage backend not configured. Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY."
        )

    return await backend.store(request)


@router.post("/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(request: KnowledgeSearchRequest):
    """Search the knowledge base."""
    backend = get_backend()

    if not backend.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Knowledge storage backend not configured. Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY."
        )

    return await backend.search(request)


@router.get("/recent", response_model=KnowledgeRecentResponse)
async def get_recent_knowledge(
    limit: int = Query(20, ge=1, le=100, description="Number of recent entries to return")
):
    """Get recent knowledge entries."""
    backend = get_backend()

    if not backend.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Knowledge storage backend not configured. Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY."
        )

    return await backend.get_recent(limit)


@router.get("/stats", response_model=KnowledgeStatsResponse)
async def get_knowledge_stats():
    """Get knowledge base statistics."""
    backend = get_backend()

    if not backend.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Knowledge storage backend not configured. Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY."
        )

    return await backend.get_stats()


@router.get("/health")
async def knowledge_health_check():
    """Health check for the Knowledge Plane."""
    backend = get_backend()

    health = {
        "status": "healthy" if backend.is_configured() else "degraded",
        "backend_configured": backend.is_configured(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    if backend.is_configured():
        storage_health = await backend.health_check()
        health.update(storage_health)

    return health
