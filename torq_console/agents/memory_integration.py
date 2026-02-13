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

        # Cached clients to avoid per-call re-creation overhead
        self._supabase_client = None
        self._openai_client = None

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

    def _get_supabase(self):
        """Get or create cached Supabase client."""
        if self._supabase_client is None:
            from supabase import create_client
            self._supabase_client = create_client(
                os.getenv("SUPABASE_URL"),
                os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            )
        return self._supabase_client

    def _get_openai(self):
        """Get or create cached OpenAI client."""
        if self._openai_client is None:
            from openai import OpenAI
            self._openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        return self._openai_client

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
            import hashlib

            supabase = self._get_supabase()

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
            supabase = self._get_supabase()

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
            # Use cached clients instead of recreating per call
            openai_client = self._get_openai()

            response = await asyncio.to_thread(
                lambda: openai_client.embeddings.create(
                    input=query,
                    model="text-embedding-3-small"
                )
            )
            query_embedding = response.data[0].embedding

            supabase = self._get_supabase()

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
            supabase = self._get_supabase()

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
            supabase = self._get_supabase()

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

    def format_context_for_prompt(self, context: Dict[str, Any], preserve_full_context: bool = True,
                                    query: Optional[str] = None, use_optimizer: bool = True) -> str:
        """
        Format retrieved context for LLM prompt.

        Args:
            context: Context from get_relevant_context()
            preserve_full_context: If True, include full content (no truncation)
            query: Current query for Phase 1 adaptive optimization
            use_optimizer: Whether to use Phase 1 handoff optimizer

        Returns:
            Formatted string for prompt injection
        """
        if not context.get('memories') and not context.get('patterns'):
            return ""

        # Phase 1 Optimization: Use adaptive handoff optimizer
        if use_optimizer and query:
            try:
                from .handoff_optimizer import get_handoff_optimizer
                optimizer = get_handoff_optimizer()

                # Optimize memory context
                optimized = optimizer.optimize_memory_context(
                    memories=context.get('memories', []),
                    query=query,
                    max_length=2000  # Phase 1: Increased from 1000 to 2000
                )

                # Use optimized memories
                memories = optimized['memories']
            except Exception as e:
                self.logger.warning(f"Handoff optimizer failed, using fallback: {e}")
                memories = context.get('memories', [])[:5]
        else:
            memories = context.get('memories', [])[:5]

        prompt = "\n## Relevant Context from Memory\n\n"

        if memories:
            prompt += "### Previous Knowledge:\n"
            for mem in memories:
                content = mem.get('content', '')
                similarity = mem.get('similarity', 0) * 100

                # Phase 1: Smart context preservation
                if preserve_full_context:
                    max_length = 2000  # Phase 1: Increased from 1000 to 2000
                    if len(content) > max_length:
                        content = content[:max_length] + "..."
                else:
                    content = content[:200] + "..."

                # Show optimization info if available
                if mem.get('compressed'):
                    ratio = mem.get('compression_ratio', 1.0)
                    prompt += f"- [{similarity:.0f}% match, {ratio:.1%} compressed] {content}\n"
                else:
                    prompt += f"- [{similarity:.0f}% match] {content}\n"
            prompt += "\n"

        if context.get('patterns'):
            prompt += "### Learned Patterns:\n"
            for pattern in context['patterns']:
                pattern_type = pattern.get('pattern_type', 'unknown')
                success_rate = pattern.get('success_rate', 0) * 100
                pattern_content = pattern.get('pattern_content', {})
                if isinstance(pattern_content, dict) and pattern_content:
                    details = ', '.join(f"{k}: {v}" for k, v in list(pattern_content.items())[:3])
                    prompt += f"- {pattern_type} (success rate: {success_rate:.0f}%) - {details}\n"
                else:
                    prompt += f"- {pattern_type} (success rate: {success_rate:.0f}%)\n"
            prompt += "\n"

        return prompt

    def get_structured_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get context as structured data for handoffs.

        Preserves full information for Memory → Planning handoffs.

        Args:
            context: Context from get_relevant_context()

        Returns:
            Structured context with full preservation
        """
        return {
            'memories': context.get('memories', []),
            'patterns': context.get('patterns', []),
            'full_content': [mem.get('content', '') for mem in context.get('memories', [])],
            'similarity_scores': [mem.get('similarity', 0) for mem in context.get('memories', [])],
            'metadata': {
                'memory_count': len(context.get('memories', [])),
                'pattern_count': len(context.get('patterns', [])),
                'retrieval_method': 'semantic_search'
            }
        }


# Singleton instance for easy access
_memory_integration = None


def get_memory_integration(agent_id: str = "prince_flowers", user_id: str = "king_flowers") -> MemoryIntegration:
    """Get or create memory integration instance."""
    global _memory_integration
    if _memory_integration is None:
        _memory_integration = MemoryIntegration(agent_id=agent_id, user_id=user_id)
    return _memory_integration
