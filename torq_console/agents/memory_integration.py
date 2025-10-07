"""
Supabase Enhanced Memory Integration for Prince Flowers Agent

Provides seamless integration between TORQ Prince Flowers and the
enhanced Supabase memory system with RAG capabilities.
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime


class MemoryIntegration:
    """
    Integration layer for Supabase enhanced memory system.

    Provides Prince Flowers with:
    - Persistent memory storage across sessions
    - Semantic search using RAG
    - Pattern learning and recall
    - Context-aware information retrieval
    """

    def __init__(self, agent_id: str = "prince_flowers", user_id: str = "king_flowers"):
        """Initialize memory integration."""
        self.agent_id = agent_id
        self.user_id = user_id
        self.logger = logging.getLogger(f"MemoryIntegration.{agent_id}")

        # Check if Supabase memory is available
        self.enabled = self._check_availability()

        if self.enabled:
            self.logger.info(f"Enhanced memory enabled for agent {agent_id}")
        else:
            self.logger.warning("Enhanced memory not available - using local fallback")

    def _check_availability(self) -> bool:
        """Check if Supabase memory system is configured."""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")

        return all([supabase_url, supabase_key, openai_key])

    async def store_interaction(
        self,
        query: str,
        response: str,
        tools_used: List[str],
        success: bool,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store an interaction in long-term memory.

        Args:
            query: User's query
            response: Agent's response
            tools_used: List of tools used
            success: Whether interaction was successful
            metadata: Additional metadata

        Returns:
            Success status
        """
        if not self.enabled:
            return False

        try:
            # Import MCP client (lazy import to avoid dependency issues)
            from supabase import create_client
            import hashlib

            supabase = create_client(
                os.getenv("SUPABASE_URL"),
                os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            )

            # Store the interaction as knowledge
            content = f"Query: {query}\nResponse: {response}\nTools: {', '.join(tools_used)}"

            # Generate content hash for deduplication
            content_hash = hashlib.sha256(content.encode()).hexdigest()

            importance = 8 if success else 5  # Higher importance for successful interactions

            data = {
                'user_id': self.user_id,
                'agent_id': self.agent_id,
                'memory_tier': 'long',
                'memory_type': 'knowledge',
                'content': content,
                'content_hash': content_hash,
                'importance_score': importance,
                'metadata': {
                    **(metadata or {}),
                    'query': query,
                    'tools_used': tools_used,
                    'success': success,
                    'timestamp': datetime.now().isoformat()
                }
            }

            result = await asyncio.to_thread(
                lambda: supabase.table('enhanced_memory').insert(data).execute()
            )

            self.logger.debug(f"Stored interaction memory: {query[:50]}...")
            return True

        except Exception as e:
            self.logger.error(f"Failed to store interaction: {e}")
            return False

    async def learn_pattern(
        self,
        pattern_type: str,
        pattern_data: Dict[str, Any],
        success: bool = True
    ) -> bool:
        """
        Store a learned pattern for future reference.

        Args:
            pattern_type: Type of pattern (tool_selection, reasoning_strategy, etc.)
            pattern_data: Pattern details
            success: Whether pattern was successful

        Returns:
            Success status
        """
        if not self.enabled:
            return False

        try:
            from supabase import create_client

            supabase = create_client(
                os.getenv("SUPABASE_URL"),
                os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            )

            data = {
                'agent_id': self.agent_id,
                'pattern_type': pattern_type,
                'pattern_content': pattern_data,
                'success_count': 1 if success else 0,
                'failure_count': 0 if success else 1
            }

            result = await asyncio.to_thread(
                lambda: supabase.table('agent_patterns').upsert(
                    data,
                    on_conflict='agent_id,pattern_type'
                ).execute()
            )

            self.logger.debug(f"Stored pattern: {pattern_type}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to store pattern: {e}")
            return False

    async def get_relevant_context(
        self,
        query: str,
        limit: int = 5,
        threshold: float = 0.78
    ) -> Dict[str, Any]:
        """
        Retrieve relevant context for current query using semantic search.

        Args:
            query: Current query
            limit: Maximum results to return
            threshold: Similarity threshold

        Returns:
            Dictionary with relevant memories and patterns
        """
        if not self.enabled:
            return {'memories': [], 'patterns': []}

        try:
            from supabase import create_client
            from openai import OpenAI

            # Generate embedding for query
            openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            response = await asyncio.to_thread(
                lambda: openai_client.embeddings.create(
                    input=query,
                    model="text-embedding-3-small"
                )
            )
            query_embedding = response.data[0].embedding

            supabase = create_client(
                os.getenv("SUPABASE_URL"),
                os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            )

            # Search memories
            memories_result = await asyncio.to_thread(
                lambda: supabase.rpc(
                    'match_memories',
                    {
                        'query_embedding': query_embedding,
                        'match_user_id': self.user_id,
                        'match_threshold': threshold,
                        'match_count': limit
                    }
                ).execute()
            )

            # Search patterns
            patterns_result = await asyncio.to_thread(
                lambda: supabase.rpc(
                    'match_agent_patterns',
                    {
                        'query_embedding': query_embedding,
                        'match_agent_id': self.agent_id,
                        'match_threshold': 0.7,
                        'match_count': 3
                    }
                ).execute()
            )

            return {
                'memories': memories_result.data or [],
                'patterns': patterns_result.data or []
            }

        except Exception as e:
            self.logger.error(f"Failed to get context: {e}")
            return {'memories': [], 'patterns': []}

    async def store_entity(
        self,
        entity_type: str,
        entity_name: str,
        attributes: Dict[str, Any],
        relationships: Optional[List[Dict[str, str]]] = None
    ) -> bool:
        """
        Store a codebase entity for knowledge graph.

        Args:
            entity_type: Type of entity (file, function, class, etc.)
            entity_name: Name/identifier
            attributes: Entity attributes
            relationships: Relationships to other entities

        Returns:
            Success status
        """
        if not self.enabled:
            return False

        try:
            from supabase import create_client

            supabase = create_client(
                os.getenv("SUPABASE_URL"),
                os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            )

            data = {
                'user_id': self.user_id,
                'entity_type': entity_type,
                'entity_name': entity_name,
                'attributes': attributes,
                'relationships': relationships or []
            }

            result = await asyncio.to_thread(
                lambda: supabase.table('codebase_entities').upsert(
                    data,
                    on_conflict='user_id,entity_type,entity_name'
                ).execute()
            )

            self.logger.debug(f"Stored entity: {entity_type}/{entity_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to store entity: {e}")
            return False

    async def get_entity(
        self,
        entity_type: str,
        entity_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific entity from knowledge graph.

        Args:
            entity_type: Type of entity
            entity_name: Name/identifier

        Returns:
            Entity data if found
        """
        if not self.enabled:
            return None

        try:
            from supabase import create_client

            supabase = create_client(
                os.getenv("SUPABASE_URL"),
                os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            )

            result = await asyncio.to_thread(
                lambda: supabase.table('codebase_entities')
                .select('*')
                .eq('user_id', self.user_id)
                .eq('entity_type', entity_type)
                .eq('entity_name', entity_name)
                .execute()
            )

            if result.data and len(result.data) > 0:
                return result.data[0]

            return None

        except Exception as e:
            self.logger.error(f"Failed to get entity: {e}")
            return None

    def format_context_for_prompt(self, context: Dict[str, Any]) -> str:
        """
        Format retrieved context for LLM prompt.

        Args:
            context: Context from get_relevant_context()

        Returns:
            Formatted string for prompt injection
        """
        if not context.get('memories') and not context.get('patterns'):
            return ""

        prompt = "\n## Relevant Context from Memory\n\n"

        if context.get('memories'):
            prompt += "### Previous Knowledge:\n"
            for mem in context['memories'][:3]:  # Top 3 most relevant
                similarity = mem.get('similarity', 0) * 100
                prompt += f"- [{similarity:.0f}% match] {mem.get('content', '')[:200]}...\n"
            prompt += "\n"

        if context.get('patterns'):
            prompt += "### Learned Patterns:\n"
            for pattern in context['patterns']:
                pattern_type = pattern.get('pattern_type', 'unknown')
                success_rate = pattern.get('success_rate', 0) * 100
                prompt += f"- {pattern_type} (success rate: {success_rate:.0f}%)\n"
            prompt += "\n"

        return prompt


# Singleton instance for easy access
_memory_integration = None


def get_memory_integration(agent_id: str = "prince_flowers", user_id: str = "king_flowers") -> MemoryIntegration:
    """Get or create memory integration instance."""
    global _memory_integration
    if _memory_integration is None:
        _memory_integration = MemoryIntegration(agent_id=agent_id, user_id=user_id)
    return _memory_integration
