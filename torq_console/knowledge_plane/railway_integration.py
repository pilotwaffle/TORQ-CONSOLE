"""
TORQ Knowledge Plane - Railway Integration

This module adds Knowledge Plane endpoints to the Railway app.
It's designed to be imported directly in railway_app.py to add the routes.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ============================================================================
# Knowledge Plane Models
# =============================================================================

class KnowledgeCategory(str):
    """Knowledge categories."""
    CODE = "code"
    DOCUMENTATION = "documentation"
    CONCEPT = "concept"
    BEST_PRACTICE = "best_practice"
    TROUBLESHOOTING = "troubleshooting"
    ARCHITECTURE = "architecture"
    CONFIGURATION = "configuration"
    WORKFLOW = "workflow"
    OTHER = "other"

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(enum=[cls.CODE, cls.DOCUMENTATION, cls.CONCEPT,
                                   cls.BEST_PRACTICE, cls.TROUBLESHOOTING,
                                   cls.ARCHITECTURE, cls.CONFIGURATION,
                                   cls.WORKFLOW, cls.OTHER])

    @classmethod
    def validate(cls, v):
        if v not in [cls.CODE, cls.DOCUMENTATION, cls.CONCEPT,
                     cls.BEST_PRACTICE, cls.TROUBLESHOOTING,
                     cls.ARCHITECTURE, cls.CONFIGURATION,
                     cls.WORKFLOW, cls.OTHER]:
            v = cls.OTHER
        return v


class KnowledgeStoreRequest(BaseModel):
    """Request to store knowledge."""
    content: str = Field(..., description="Knowledge content")
    title: Optional[str] = Field(None, description="Optional title")
    category: str = Field("other", description="Knowledge category")
    tags: List[str] = Field(default_factory=list, description="Tags")
    source: Optional[str] = Field(None, description="Source")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")


class KnowledgeSearchRequest(BaseModel):
    """Request to search knowledge."""
    query: str = Field(..., description="Search query")
    category: Optional[str] = Field(None, description="Filter by category")
    tags: List[str] = Field(default_factory=list, description="Filter by tags")
    limit: int = Field(10, ge=1, le=100, description="Max results")


class KnowledgeEntry(BaseModel):
    """A knowledge entry."""
    id: str
    content: str
    title: Optional[str]
    category: str
    tags: List[str]
    source: Optional[str]
    created_at: str
    similarity: Optional[float] = None


# ============================================================================
# Knowledge Plane Router (Lightweight for Railway)
# =============================================================================

def create_knowledge_router() -> APIRouter:
    """Create the Knowledge Plane API router."""
    router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

    @router.post("/store")
    async def store_knowledge(request: KnowledgeStoreRequest):
        """Store a knowledge entry."""
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

        if not supabase_url or not supabase_key:
            raise HTTPException(
                status_code=503,
                detail="Supabase not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY."
            )

        import httpx
        import uuid

        entry_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        entry_data = {
            "id": entry_id,
            "content": request.content,
            "title": request.title,
            "category": request.category,
            "tags": request.tags,
            "source": request.source,
            "metadata": request.metadata,
            "created_at": now,
            "updated_at": now
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{supabase_url}/rest/v1/torq_knowledge",
                    headers={
                        "apikey": supabase_key,
                        "Authorization": f"Bearer {supabase_key}",
                        "Content-Type": "application/json"
                    },
                    json=entry_data,
                    timeout=30.0
                )
                response.raise_for_status()

            return {
                "success": True,
                "id": entry_id,
                "message": "Knowledge stored successfully",
                "created_at": now
            }

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # Table doesn't exist, create it
                await _init_knowledge_table()
                # Retry the store
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{supabase_url}/rest/v1/torq_knowledge",
                        headers={
                            "apikey": supabase_key,
                            "Authorization": f"Bearer {supabase_key}",
                            "Content-Type": "application/json"
                        },
                        json=entry_data,
                        timeout=30.0
                    )
                    response.raise_for_status()
                return {
                    "success": True,
                    "id": entry_id,
                    "message": "Knowledge stored successfully (table created)",
                    "created_at": now
                }
            raise HTTPException(status_code=500, detail=f"Failed to store: {str(e)}")

    @router.post("/search")
    async def search_knowledge(request: KnowledgeSearchRequest):
        """Search the knowledge base."""
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

        if not supabase_url or not supabase_key:
            raise HTTPException(
                status_code=503,
                detail="Supabase not configured."
            )

        import httpx
        import time

        start_time = time.time()

        try:
            params = {
                "select": "id,content,title,category,tags,source,created_at",
                "order": "created_at.desc",
                "limit": request.limit
            }

            # Add category filter
            if request.category:
                params["category"] = f"eq.{request.category}"

            # Add text search filter
            if request.query:
                params["or"] = f"(title.ilike.*{request.query}*,content.ilike.*{request.query}*)"

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{supabase_url}/rest/v1/torq_knowledge",
                    headers={
                        "apikey": supabase_key,
                        "Authorization": f"Bearer {supabase_key}"
                    },
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()

            results = response.json()
            execution_time = (time.time() - start_time) * 1000

            return {
                "query": request.query,
                "total": len(results),
                "results": results,
                "execution_time_ms": round(execution_time, 2)
            }

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {
                "query": request.query,
                "total": 0,
                "results": [],
                "execution_time_ms": 0,
                "error": str(e)
            }

    @router.get("/recent")
    async def get_recent_knowledge(
        limit: int = Query(20, ge=1, le=100, description="Number of entries")
    ):
        """Get recent knowledge entries."""
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

        if not supabase_url or not supabase_key:
            raise HTTPException(status_code=503, detail="Supabase not configured.")

        import httpx

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{supabase_url}/rest/v1/torq_knowledge",
                    headers={
                        "apikey": supabase_key,
                        "Authorization": f"Bearer {supabase_key}"
                    },
                    params={
                        "select": "id,content,title,category,tags,source,created_at",
                        "order": "created_at.desc",
                        "limit": limit
                    },
                    timeout=30.0
                )
                response.raise_for_status()

            return {
                "total": len(response.json()),
                "results": response.json()
            }

        except Exception as e:
            return {
                "total": 0,
                "results": [],
                "error": str(e)
            }

    @router.get("/stats")
    async def get_knowledge_stats():
        """Get knowledge base statistics."""
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

        if not supabase_url or not supabase_key:
            raise HTTPException(status_code=503, detail="Supabase not configured.")

        import httpx

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{supabase_url}/rest/v1/torq_knowledge",
                    headers={
                        "apikey": supabase_key,
                        "Authorization": f"Bearer {supabase_key}"
                    },
                    params={
                        "select": "id,category,source,tags,created_at",
                        "limit": 1000
                    },
                    timeout=30.0
                )
                response.raise_for_status()

            entries = response.json()

            by_category = {}
            by_source = {}
            all_tags = set()
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

            return {
                "total_entries": len(entries),
                "by_category": by_category,
                "by_source": by_source,
                "oldest_entry": min(timestamps) if timestamps else None,
                "newest_entry": max(timestamps) if timestamps else None,
                "total_tags": len(all_tags),
                "unique_tags": sorted(list(all_tags))[:50]
            }

        except Exception as e:
            return {
                "total_entries": 0,
                "by_category": {},
                "by_source": {},
                "error": str(e)
            }

    @router.get("/health")
    async def knowledge_health():
        """Knowledge Plane health check."""
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        openai_key = os.environ.get("OPENAI_API_KEY")

        return {
            "status": "healthy" if supabase_url else "degraded",
            "supabase_configured": bool(supabase_url),
            "openai_configured": bool(openai_key),
            "redis_configured": bool(os.environ.get("REDIS_URL")),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    return router


async def _init_knowledge_table():
    """Initialize the torq_knowledge table in Supabase."""
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        logger.warning("Cannot init knowledge table: Supabase not configured")
        return

    import httpx

    # Use the Supabase SQL API to create the table
    create_sql = """
    CREATE TABLE IF NOT EXISTS torq_knowledge (
        id TEXT PRIMARY KEY,
        content TEXT NOT NULL,
        title TEXT,
        category TEXT DEFAULT 'other',
        tags TEXT[] DEFAULT '{}',
        source TEXT,
        metadata JSONB DEFAULT '{}',
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_knowledge_category ON torq_knowledge(category);
    CREATE INDEX IF NOT EXISTS idx_knowledge_tags ON torq_knowledge USING GIN(tags);
    CREATE INDEX IF NOT EXISTS idx_knowledge_created ON torq_knowledge(created_at DESC);

    COMMENT ON TABLE torq_knowledge IS 'TORQ Knowledge Plane - semantic knowledge storage';
    """

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{supabase_url}/rest/v1/rpc/exec",
                headers={
                    "apikey": supabase_key,
                    "Authorization": f"Bearer {supabase_key}",
                    "Content-Type": "application/json"
                },
                json={"query": create_sql},
                timeout=30.0
            )
            # Might fail due to permissions, log and continue
            if response.status_code not in [200, 201]:
                logger.warning(f"Failed to auto-create table: {response.text}")
    except Exception as e:
        logger.warning(f"Failed to init knowledge table: {e}")


# Importable router instance
knowledge_router = create_knowledge_router()
