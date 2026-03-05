"""
Knowledge Retriever for the TORQ Agent Cognitive Loop.

Queries the Knowledge Plane via vector search to retrieve relevant context.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from .models import (
    CognitiveLoopConfig,
    KnowledgeContext,
    SessionContext,
)


logger = logging.getLogger(__name__)


class KnowledgeRetriever:
    """
    Retrieves relevant knowledge from the Knowledge Plane.

    Uses vector search with pgvector (Supabase) or fallback to
    local embeddings for context retrieval.
    """

    def __init__(self, config: CognitiveLoopConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.KnowledgeRetriever")
        self._embedding_cache: Dict[str, List[float]] = {}
        self._supabase_client = None
        self._local_embeddings = None

        # Initialize connection to knowledge plane
        self._initialize_knowledge_plane()

    def _initialize_knowledge_plane(self):
        """Initialize connection to the Knowledge Plane."""
        try:
            # Try to connect to Supabase for vector search
            supabase_url = self._get_env_var("SUPABASE_URL")
            supabase_key = self._get_env_var("SUPABASE_SERVICE_KEY")

            if supabase_url and supabase_key:
                from supabase import create_client
                self._supabase_client = create_client(supabase_url, supabase_key)
                self.logger.info("Connected to Supabase Knowledge Plane")
        except Exception as e:
            self.logger.warning(f"Could not connect to Supabase: {e}")
            self._supabase_client = None

        # Initialize local embeddings as fallback
        try:
            self._initialize_local_embeddings()
        except Exception as e:
            self.logger.warning(f"Could not initialize local embeddings: {e}")

    def _get_env_var(self, name: str) -> Optional[str]:
        """Get environment variable."""
        import os
        return os.getenv(name)

    def _initialize_local_embeddings(self):
        """Initialize local embedding model as fallback."""
        try:
            from sentence_transformers import SentenceTransformer
            model_name = "all-MiniLM-L6-v2"  # Fast, efficient model
            self._local_embeddings = SentenceTransformer(model_name)
            self.logger.info("Initialized local embedding model")
        except ImportError:
            self.logger.info("sentence_transformers not available, using dummy embeddings")
        except Exception as e:
            self.logger.warning(f"Failed to initialize local embeddings: {e}")

    async def retrieve(
        self,
        query: str,
        session_context: Optional[SessionContext] = None,
        max_results: Optional[int] = None,
        **kwargs
    ) -> List[KnowledgeContext]:
        """
        Retrieve relevant knowledge contexts for the query.

        Args:
            query: The query to search for
            session_context: Current session context
            max_results: Maximum number of contexts to retrieve
            **kwargs: Additional parameters

        Returns:
            List of relevant KnowledgeContext objects
        """
        if not self.config.knowledge_enabled:
            return []

        start_time = time.time()
        max_results = max_results or self.config.max_knowledge_contexts

        # Generate query embedding
        query_embedding = await self._generate_embedding(query)

        # Search for relevant contexts
        contexts = []

        if self._supabase_client:
            # Use Supabase vector search
            contexts = await self._search_supabase(query_embedding, max_results)
        elif self._local_embeddings:
            # Use local knowledge base
            contexts = await self._search_local(query, query_embedding, max_results)
        else:
            # Use rule-based retrieval
            contexts = await self._search_rule_based(query, max_results)

        # Filter by similarity threshold
        contexts = [
            c for c in contexts
            if c.similarity >= self.config.knowledge_similarity_threshold
        ]

        execution_time = time.time() - start_time

        self.logger.debug(
            f"Retrieved {len(contexts)} knowledge contexts in {execution_time:.3f}s"
        )

        return contexts

    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for the given text."""
        # Check cache
        if text in self._embedding_cache:
            return self._embedding_cache[text]

        embedding = []

        if self._supabase_client:
            # Use Supabase embedding generation (if configured)
            embedding = await self._generate_embedding_supabase(text)
        elif self._local_embeddings:
            # Use local model
            embedding = self._local_embeddings.encode(text).tolist()
        else:
            # Use simple hash-based embedding (fallback)
            embedding = self._simple_embedding(text)

        # Cache the embedding
        self._embedding_cache[text] = embedding

        return embedding

    async def _generate_embedding_supabase(self, text: str) -> List[float]:
        """Generate embedding using Supabase's edge function or API."""
        try:
            # Try to use OpenAI API for embeddings (if configured)
            api_key = self._get_env_var("OPENAI_API_KEY")
            if api_key:
                import openai
                client = openai.AsyncOpenAI(api_key=api_key)
                response = await client.embeddings.create(
                    model="text-embedding-3-small",
                    input=text
                )
                return response.data[0].embedding
        except Exception as e:
            self.logger.warning(f"Supabase embedding generation failed: {e}")

        # Fall back to local or simple embedding
        if self._local_embeddings:
            return self._local_embeddings.encode(text).tolist()
        return self._simple_embedding(text)

    def _simple_embedding(self, text: str, dimensions: int = 384) -> List[float]:
        """Generate a simple hash-based embedding as fallback."""
        import hashlib

        # Create a hash-based embedding
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()

        # Convert to float values
        embedding = []
        for i in range(dimensions):
            byte_index = i % len(hash_bytes)
            value = hash_bytes[byte_index] / 255.0
            embedding.append(value)

        return embedding

    async def _search_supabase(
        self,
        query_embedding: List[float],
        max_results: int
    ) -> List[KnowledgeContext]:
        """Search using Supabase pgvector."""
        contexts = []

        try:
            # Query the knowledge table with vector similarity
            result = self._supabase_client.rpc(
                "match_knowledge",
                {
                    "query_embedding": query_embedding,
                    "match_threshold": self.config.knowledge_similarity_threshold,
                    "match_count": max_results
                }
            )

            if result.data:
                for item in result.data:
                    contexts.append(KnowledgeContext(
                        id=item.get("id", ""),
                        content=item.get("content", ""),
                        source=item.get("source", "supabase"),
                        similarity=item.get("similarity", 0.0),
                        metadata=item.get("metadata", {})
                    ))
        except Exception as e:
            self.logger.warning(f"Supabase search failed: {e}")

        return contexts

    async def _search_local(
        self,
        query: str,
        query_embedding: List[float],
        max_results: int
    ) -> List[KnowledgeContext]:
        """Search using local knowledge base and embeddings."""
        contexts = []

        try:
            # Load local knowledge base
            knowledge_base = self._load_local_knowledge()

            # Calculate similarities
            from scipy.spatial.distance import cosine

            results = []
            for item in knowledge_base:
                item_embedding = await self._generate_embedding(item.get("content", ""))
                similarity = 1 - cosine(query_embedding, item_embedding)

                if similarity >= self.config.knowledge_similarity_threshold:
                    results.append((similarity, item))

            # Sort by similarity and take top results
            results.sort(key=lambda x: x[0], reverse=True)

            for similarity, item in results[:max_results]:
                contexts.append(KnowledgeContext(
                    id=item.get("id", ""),
                    content=item.get("content", ""),
                    source=item.get("source", "local"),
                    similarity=similarity,
                    metadata=item.get("metadata", {})
                ))
        except Exception as e:
            self.logger.warning(f"Local search failed: {e}")

        return contexts

    async def _search_rule_based(
        self,
        query: str,
        max_results: int
    ) -> List[KnowledgeContext]:
        """Search using simple keyword matching."""
        contexts = []

        try:
            # Load local knowledge base
            knowledge_base = self._load_local_knowledge()

            query_lower = query.lower()
            query_words = set(query_lower.split())

            results = []
            for item in knowledge_base:
                content = item.get("content", "").lower()
                words = set(content.split())

                # Calculate overlap
                overlap = len(query_words & words)
                if overlap > 0:
                    similarity = min(overlap / len(query_words), 1.0)
                    results.append((similarity, item))

            # Sort by similarity
            results.sort(key=lambda x: x[0], reverse=True)

            for similarity, item in results[:max_results]:
                contexts.append(KnowledgeContext(
                    id=item.get("id", ""),
                    content=item.get("content", ""),
                    source=item.get("source", "rule_based"),
                    similarity=similarity,
                    metadata=item.get("metadata", {})
                ))
        except Exception as e:
            self.logger.warning(f"Rule-based search failed: {e}")

        return contexts

    def _load_local_knowledge(self) -> List[Dict[str, Any]]:
        """Load knowledge from local storage."""
        import json
        from pathlib import Path

        knowledge_path = Path(".torq/knowledge_base.json")
        knowledge_base = []

        if knowledge_path.exists():
            try:
                with open(knowledge_path, "r") as f:
                    knowledge_base = json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load local knowledge: {e}")

        return knowledge_base

    async def store_knowledge(
        self,
        content: str,
        source: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store new knowledge in the Knowledge Plane.

        Args:
            content: The knowledge content to store
            source: Source of the knowledge
            metadata: Additional metadata

        Returns:
            True if storage was successful
        """
        try:
            embedding = await self._generate_embedding(content)

            knowledge_item = {
                "id": f"knowledge_{int(asyncio.get_event_loop().time() * 1000)}",
                "content": content,
                "source": source,
                "embedding": embedding,
                "metadata": metadata or {},
                "created_at": time.time()
            }

            if self._supabase_client:
                # Store in Supabase
                self._supabase_client.table("knowledge").insert(knowledge_item).execute()
            else:
                # Store locally
                self._store_local_knowledge(knowledge_item)

            self.logger.debug(f"Stored knowledge from source: {source}")
            return True

        except Exception as e:
            self.logger.warning(f"Failed to store knowledge: {e}")
            return False

    def _store_local_knowledge(self, item: Dict[str, Any]):
        """Store knowledge item locally."""
        import json
        from pathlib import Path

        knowledge_path = Path(".torq/knowledge_base.json")
        knowledge_base = []

        if knowledge_path.exists():
            try:
                with open(knowledge_path, "r") as f:
                    knowledge_base = json.load(f)
            except Exception:
                pass

        knowledge_base.append(item)

        # Ensure directory exists
        knowledge_path.parent.mkdir(parents=True, exist_ok=True)

        with open(knowledge_path, "w") as f:
            json.dump(knowledge_base, f, indent=2)

    async def emit_telemetry(
        self,
        phase: str,
        data: Dict[str, Any],
        run_id: Optional[str] = None
    ):
        """Emit telemetry for the knowledge retrieval phase."""
        if not self.config.telemetry_enabled:
            return

        try:
            from torq_console.core.telemetry.event import create_system_event
            from torq_console.core.telemetry.integration import get_telemetry_integration

            integration = get_telemetry_integration()
            await integration.record_agent_run(
                agent_name="knowledge_retriever",
                agent_type="cognitive_loop",
                status="started",
                run_id=run_id,
                **{f"retrieve.{k}": v for k, v in data.items()}
            )
        except Exception as e:
            self.logger.warning(f"Failed to emit telemetry: {e}")
