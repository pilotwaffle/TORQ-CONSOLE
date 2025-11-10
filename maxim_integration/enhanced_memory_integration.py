"""
Enhanced Memory Integration for Prince Flowers Agent

Integrates MarvinAgentMemory and Supabase memory with the enhanced Prince Flowers agent
to achieve 95%+ performance through learning and context awareness.
"""

import asyncio
import json
import logging
import time
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from torq_console.agents.marvin_memory import MarvinAgentMemory, InteractionType
from torq_console.agents.memory_integration import get_memory_integration
from supabase_memory_config import get_supabase_setup, SupabaseConfig

@dataclass
class MemoryContext:
    """Context retrieved from memory for query processing."""
    relevant_memories: List[Dict]
    successful_patterns: List[Dict]
    query_routing_suggestions: List[Dict]
    tool_performance_history: Dict[str, float]
    user_preferences: Dict[str, Any]
    confidence_boost: float = 0.0

class EnhancedMemoryIntegration:
    """
    Enhanced memory integration combining Marvin and Supabase memory systems.

    Features:
    - Short-term memory: MarvinAgentMemory for session-based learning
    - Long-term memory: Supabase for persistent storage and semantic search
    - Pattern learning: Automatic pattern detection and optimization
    - Context awareness: Retrieve relevant context for each query
    - Performance tracking: Monitor and improve over time
    """

    def __init__(self, agent_id: str = "prince_flowers_enhanced", user_id: str = "king_flowers"):
        """Initialize enhanced memory integration."""
        self.agent_id = agent_id
        self.user_id = user_id
        self.logger = logging.getLogger(f"EnhancedMemory.{agent_id}")

        # Initialize memory systems
        self.marvin_memory = MarvinAgentMemory()
        self.supabase_memory = get_memory_integration()
        self.supabase_setup = get_supabase_setup()

        # Performance tracking
        self.session_start = time.time()
        self.interaction_count = 0
        self.successful_interactions = 0
        self.context_cache = {}
        self.pattern_cache = {}

        # Learning parameters
        self.learning_rate = 0.1
        self.context_threshold = 0.7
        self.pattern_success_threshold = 0.8

        self.logger.info("Enhanced memory integration initialized")

    async def initialize(self):
        """Initialize Supabase connection and validate setup."""
        if self.supabase_setup and self.supabase_setup.is_configured():
            try:
                # Test Supabase connection
                await self._test_supabase_connection()
                self.logger.info("Supabase memory connection verified")
                return True
            except Exception as e:
                self.logger.error(f"Supabase connection failed: {e}")
                return False
        else:
            self.logger.warning("Supabase not configured, using local memory only")
            return False

    async def _test_supabase_connection(self):
        """Test Supabase database connection."""
        if not self.supabase_memory.enabled:
            raise Exception("Supabase memory not enabled")

        # Test with a simple memory retrieval
        await self.supabase_memory.get_relevant_context("test", limit=1)

    async def get_context_for_query(
        self,
        query: str,
        intent: Optional[str] = None,
        limit: int = 5
    ) -> MemoryContext:
        """
        Retrieve relevant context for query processing.

        Args:
            query: Current query string
            intent: Query intent (optional)
            limit: Maximum number of memories to retrieve

        Returns:
            MemoryContext with relevant information
        """
        start_time = time.time()

        try:
            # Check cache first
            cache_key = hashlib.md5(f"{query}_{intent}_{limit}".encode()).hexdigest()
            if cache_key in self.context_cache:
                cached_context = self.context_cache[cache_key]
                if time.time() - cached_context['timestamp'] < 300:  # 5 minute cache
                    self.logger.debug(f"Context cache hit for query: {query[:30]}...")
                    return cached_context['context']

            # Retrieve from Supabase
            supabase_context = await self.supabase_memory.get_relevant_context(
                query=query,
                limit=limit,
                threshold=self.context_threshold
            ) if self.supabase_memory.enabled else {'memories': [], 'patterns': []}

            # Get routing patterns from memory
            routing_patterns = await self._get_routing_patterns(query, intent)

            # Get tool performance history
            tool_performance = await self._get_tool_performance_history()

            # Get user preferences
            user_preferences = await self._get_user_preferences()

            # Calculate confidence boost based on context quality
            confidence_boost = self._calculate_confidence_boost(
                supabase_context, routing_patterns, tool_performance
            )

            context = MemoryContext(
                relevant_memories=supabase_context.get('memories', []),
                successful_patterns=supabase_context.get('patterns', []),
                query_routing_suggestions=routing_patterns,
                tool_performance_history=tool_performance,
                user_preferences=user_preferences,
                confidence_boost=confidence_boost
            )

            # Cache the context
            self.context_cache[cache_key] = {
                'context': context,
                'timestamp': time.time()
            }

            retrieval_time = time.time() - start_time
            self.logger.debug(f"Context retrieved in {retrieval_time:.3f}s, "
                            f"boost: {confidence_boost:.2f}")

            return context

        except Exception as e:
            self.logger.error(f"Context retrieval failed: {e}")
            return MemoryContext(
                relevant_memories=[],
                successful_patterns=[],
                query_routing_suggestions=[],
                tool_performance_history={},
                user_preferences={},
                confidence_boost=0.0
            )

    async def record_interaction(
        self,
        query: str,
        response: str,
        intent: str,
        tools_used: List[str],
        success: bool,
        execution_time: float,
        confidence: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Record interaction in both memory systems.

        Args:
            query: User query
            response: Agent response
            intent: Query intent
            tools_used: List of tools used
            success: Whether interaction was successful
            execution_time: Time taken to process
            confidence: Agent confidence in response
            metadata: Additional metadata

        Returns:
            Marvin interaction ID
        """
        self.interaction_count += 1
        if success:
            self.successful_interactions += 1

        metadata = metadata or {}
        metadata.update({
            'intent': intent,
            'tools_used': tools_used,
            'execution_time': execution_time,
            'confidence': confidence,
            'timestamp': datetime.now().isoformat()
        })

        try:
            # Record in Marvin memory (short-term)
            marvin_interaction_id = self.marvin_memory.record_interaction(
                user_input=query,
                agent_response=response,
                agent_name=self.agent_id,
                interaction_type=InteractionType.GENERAL_CHAT,
                success=success
            )

            # Store in Supabase (long-term)
            if self.supabase_memory.enabled:
                await self.supabase_memory.store_interaction(
                    query=query,
                    response=response,
                    tools_used=tools_used,
                    success=success,
                    metadata=metadata
                )

                # Learn patterns from successful interactions
                if success:
                    await self._learn_from_interaction(
                        query, intent, tools_used, success, metadata
                    )

            # Update performance metrics
            await self._update_performance_metrics(
                intent, success, execution_time, confidence
            )

            # Clear relevant context cache
            self._clear_context_cache_for_query(query)

            self.logger.debug(f"Interaction recorded: {marvin_interaction_id}, "
                            f"success: {success}")

            return marvin_interaction_id

        except Exception as e:
            self.logger.error(f"Failed to record interaction: {e}")
            return f"error_{int(time.time())}"

    async def learn_from_feedback(
        self,
        interaction_id: str,
        feedback_score: float,
        feedback_text: Optional[str] = None
    ):
        """
        Learn from user feedback to improve future performance.

        Args:
            interaction_id: ID of the interaction
            feedback_score: User feedback score (0.0 - 1.0)
            feedback_text: Optional feedback text
        """
        try:
            # Update Marvin memory with feedback
            self.marvin_memory.add_feedback(
                interaction_id=interaction_id,
                score=feedback_score
            )

            # Learn from feedback in Supabase
            if self.supabase_memory.enabled:
                await self._learn_from_feedback(interaction_id, feedback_score, feedback_text)

            self.logger.info(f"Learned from feedback: {feedback_score:.2f} for {interaction_id}")

        except Exception as e:
            self.logger.error(f"Failed to learn from feedback: {e}")

    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        session_duration = time.time() - self.session_start
        session_success_rate = self.successful_interactions / max(self.interaction_count, 1)

        # Get long-term performance from Supabase
        long_term_metrics = await self._get_long_term_performance_metrics()

        return {
            'session_metrics': {
                'duration_seconds': session_duration,
                'total_interactions': self.interaction_count,
                'successful_interactions': self.successful_interactions,
                'success_rate': session_success_rate,
                'avg_interactions_per_minute': self.interaction_count / max(session_duration / 60, 1)
            },
            'long_term_metrics': long_term_metrics,
            'memory_status': {
                'marvin_memory_interactions': len(self.marvin_memory.get_interaction_history()),
                'supabase_enabled': self.supabase_memory.enabled,
                'cache_size': len(self.context_cache)
            },
            'learning_status': {
                'patterns_learned': len(self.pattern_cache),
                'context_threshold': self.context_threshold,
                'learning_rate': self.learning_rate
            }
        }

    async def _get_routing_patterns(self, query: str, intent: Optional[str]) -> List[Dict]:
        """Get successful routing patterns for similar queries."""
        try:
            if not self.supabase_memory.enabled:
                return []

            # This would typically query the query_routing_patterns table
            # For now, return some example patterns
            return [
                {
                    'query_pattern': 'explain',
                    'successful_intent': 'RESEARCH',
                    'success_rate': 0.92,
                    'recommended_tools': ['web_search', 'analyzer']
                },
                {
                    'query_pattern': 'generate code',
                    'successful_intent': 'CODE_GENERATION',
                    'success_rate': 0.88,
                    'recommended_tools': ['code_generation']
                }
            ]

        except Exception as e:
            self.logger.error(f"Failed to get routing patterns: {e}")
            return []

    async def _get_tool_performance_history(self) -> Dict[str, float]:
        """Get tool performance history from memory."""
        try:
            if not self.supabase_memory.enabled:
                return {}

            # This would typically query performance metrics
            # For now, return example performance data
            return {
                'web_search': 0.85,
                'code_generation': 0.78,
                'analyzer': 0.92,
                'pattern_extractor': 0.88,
                'sentiment_analysis': 0.75
            }

        except Exception as e:
            self.logger.error(f"Failed to get tool performance: {e}")
            return {}

    async def _get_user_preferences(self) -> Dict[str, Any]:
        """Get learned user preferences."""
        try:
            # This would retrieve stored preferences
            # For now, return basic preferences
            return {
                'response_style': 'detailed',
                'code_language': 'python',
                'preferred_tools': ['web_search', 'analyzer'],
                'complexity_preference': 'medium'
            }

        except Exception as e:
            self.logger.error(f"Failed to get user preferences: {e}")
            return {}

    def _calculate_confidence_boost(
        self,
        supabase_context: Dict,
        routing_patterns: List[Dict],
        tool_performance: Dict[str, float]
    ) -> float:
        """Calculate confidence boost based on available context."""
        boost = 0.0

        # Boost from relevant memories
        memories = supabase_context.get('memories', [])
        if memories:
            avg_similarity = sum(mem.get('similarity', 0) for mem in memories) / len(memories)
            boost += avg_similarity * 0.3

        # Boost from successful patterns
        if routing_patterns:
            avg_pattern_success = sum(p.get('success_rate', 0) for p in routing_patterns) / len(routing_patterns)
            boost += avg_pattern_success * 0.2

        # Boost from tool performance
        if tool_performance:
            avg_tool_performance = sum(tool_performance.values()) / len(tool_performance)
            boost += avg_tool_performance * 0.1

        return min(boost, 0.5)  # Cap boost at 0.5

    async def _learn_from_interaction(
        self,
        query: str,
        intent: str,
        tools_used: List[str],
        success: bool,
        metadata: Dict[str, Any]
    ):
        """Learn patterns from successful interactions."""
        if not success:
            return

        try:
            # Learn query routing patterns
            pattern_key = f"{intent}_{tuple(sorted(tools_used))}"
            if pattern_key not in self.pattern_cache:
                self.pattern_cache[pattern_key] = {
                    'success_count': 0,
                    'total_count': 0,
                    'avg_confidence': 0.0
                }

            pattern = self.pattern_cache[pattern_key]
            pattern['success_count'] += 1
            pattern['total_count'] += 1
            pattern['avg_confidence'] = (
                (pattern['avg_confidence'] * (pattern['success_count'] - 1) + metadata.get('confidence', 0.5)) /
                pattern['success_count']
            )

            # Store pattern in Supabase if it meets threshold
            success_rate = pattern['success_count'] / pattern['total_count']
            if success_rate >= self.pattern_success_threshold and pattern['total_count'] >= 3:
                await self.supabase_memory.learn_pattern(
                    pattern_type="query_routing",
                    pattern_data={
                        'intent': intent,
                        'tools_used': tools_used,
                        'success_rate': success_rate,
                        'avg_confidence': pattern['avg_confidence']
                    },
                    success=True
                )

        except Exception as e:
            self.logger.error(f"Failed to learn from interaction: {e}")

    async def _update_performance_metrics(
        self,
        intent: str,
        success: bool,
        execution_time: float,
        confidence: float
    ):
        """Update performance metrics in Supabase."""
        try:
            if not self.supabase_memory.enabled:
                return

            # This would store metrics in Supabase
            # For now, just log the metrics
            self.logger.debug(f"Performance metrics - Intent: {intent}, "
                            f"Success: {success}, Time: {execution_time:.3f}s, "
                            f"Confidence: {confidence:.2f}")

        except Exception as e:
            self.logger.error(f"Failed to update performance metrics: {e}")

    async def _get_long_term_performance_metrics(self) -> Dict[str, Any]:
        """Get long-term performance metrics from Supabase."""
        try:
            if not self.supabase_memory.enabled:
                return {}

            # This would query the agent_performance_metrics table
            # For now, return example metrics
            return {
                'overall_success_rate': 0.87,
                'avg_execution_time': 2.3,
                'avg_confidence': 0.84,
                'most_successful_intent': 'RESEARCH',
                'most_used_tool': 'web_search',
                'total_interactions': 1250,
                'learning_trend': 'improving'
            }

        except Exception as e:
            self.logger.error(f"Failed to get long-term metrics: {e}")
            return {}

    async def _learn_from_feedback(
        self,
        interaction_id: str,
        feedback_score: float,
        feedback_text: Optional[str]
    ):
        """Learn from user feedback in Supabase."""
        # This would store feedback in the learning_feedback table
        self.logger.debug(f"Feedback learned: {feedback_score:.2f}")

    def _get_marvin_interaction_type(self, intent: str) -> InteractionType:
        """Convert intent to Marvin interaction type."""
        intent_mapping = {
            'WEB_SEARCH': InteractionType.GENERAL_CHAT,
            'CODE_GENERATION': InteractionType.TECHNICAL_HELP,
            'RESEARCH': InteractionType.GENERAL_CHAT,
            'DEBUGGING': InteractionType.TECHNICAL_HELP
        }
        return intent_mapping.get(intent, InteractionType.GENERAL_CHAT)

    def _clear_context_cache_for_query(self, query: str):
        """Clear relevant context cache entries."""
        keys_to_remove = []
        for cache_key in self.context_cache:
            if any(word in cache_key.lower() for word in query.lower().split()[:3]):
                keys_to_remove.append(cache_key)

        for key in keys_to_remove:
            del self.context_cache[key]

        if keys_to_remove:
            self.logger.debug(f"Cleared {len(keys_to_remove)} context cache entries")

# Singleton instance
_enhanced_memory_integration = None

def get_enhanced_memory_integration(
    agent_id: str = "prince_flowers_enhanced",
    user_id: str = "king_flowers"
) -> EnhancedMemoryIntegration:
    """Get or create enhanced memory integration instance."""
    global _enhanced_memory_integration
    if _enhanced_memory_integration is None:
        _enhanced_memory_integration = EnhancedMemoryIntegration(agent_id, user_id)
    return _enhanced_memory_integration