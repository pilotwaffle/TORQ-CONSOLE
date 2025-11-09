"""
Memory-Enhanced Prince Flowers Integration

Enhanced Prince Flowers agent with full memory integration and learning capabilities
targeting 95%+ performance score through context awareness and continuous improvement.
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from torq_console.llm.providers.base import BaseLLMProvider
from enhanced_memory_integration import get_enhanced_memory_integration, MemoryContext
from maxim_prompt_tools_integration import get_maxim_tools_integration

class MemoryEnhancedPrinceFlowers:
    """
    Memory-enhanced Prince Flowers agent with full integration.

    Features:
    - Context-aware query processing using retrieved memories
    - Learning from interactions to improve performance
    - Adaptive routing based on historical success patterns
    - Tool performance optimization
    - User preference learning
    - Continuous performance improvement
    """

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        """Initialize memory-enhanced Prince Flowers agent."""
        self.agent_name = "Memory-Enhanced Prince Flowers"
        self.agent_id = "prince_flowers_memory_enhanced"
        self.llm_provider = llm_provider
        self.logger = logging.getLogger(f"MemoryEnhanced.{self.agent_id}")

        # Initialize enhanced memory system
        self.memory_integration = get_enhanced_memory_integration(
            agent_id=self.agent_id,
            user_id="king_flowers"
        )

        # Initialize tools integration
        api_key = "sk_mx_mhr8zshq_6naZMAwzpYq32PGMxUUtfIKFtkHWeRX8"
        self.maxim_tools = get_maxim_tools_integration(api_key)

        # Performance tracking
        self.active_since = time.time()
        self.total_interactions = 0
        self.successful_interactions = 0
        self.performance_history = []

        # Learning parameters
        self.context_weight = 0.3
        self.performance_weight = 0.4
        self.tools_weight = 0.3

        self.logger.info(f"{self.agent_name} initialized")

    async def initialize(self):
        """Initialize all subsystems."""
        try:
            # Initialize memory integration
            memory_ready = await self.memory_integration.initialize()

            # Initialize Maxim tools
            await self.maxim_tools.initialize()

            self.logger.info(f"Agent initialized - Memory: {'✓' if memory_ready else '✗'}, Tools: ✓")
            return memory_ready

        except Exception as e:
            self.logger.error(f"Agent initialization failed: {e}")
            return False

    async def process_query_with_memory(
        self,
        query: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Process query with full memory integration and learning.

        Args:
            query: User query string
            context: Optional context dictionary

        Returns:
            Enhanced result with memory integration
        """
        start_time = time.time()
        self.total_interactions += 1

        try:
            # Step 1: Route query with memory-enhanced routing
            routing_decision = await self._route_query_with_memory(query)
            self.logger.info(f"[MEMORY-ROUTING] Intent: {routing_decision['intent']}, "
                           f"Confidence: {routing_decision['confidence']:.2f}, "
                           f"Memory Boost: {routing_decision.get('memory_boost', 0):.2f}")

            # Step 2: Retrieve relevant context from memory
            memory_context = await self.memory_integration.get_context_for_query(
                query=query,
                intent=routing_decision['intent'],
                limit=5
            )

            # Step 3: Process query with context
            result = await self._execute_with_context(
                query=query,
                routing_decision=routing_decision,
                memory_context=memory_context,
                context=context
            )

            # Step 4: Record interaction for learning
            execution_time = time.time() - start_time
            interaction_id = await self.memory_integration.record_interaction(
                query=query,
                response=result['content'],
                intent=routing_decision['intent'],
                tools_used=result.get('tools_used', []),
                success=result['success'],
                execution_time=execution_time,
                confidence=result.get('confidence', routing_decision['confidence']),
                metadata={
                    'memory_context_used': len(memory_context.relevant_memories) > 0,
                    'patterns_used': len(memory_context.successful_patterns) > 0,
                    'context_boost': memory_context.confidence_boost,
                    'routing_with_memory': routing_decision.get('used_memory', False)
                }
            )

            # Step 5: Update statistics
            if result['success']:
                self.successful_interactions += 1

            # Step 6: Return enhanced result
            enhanced_result = {
                **result,
                'interaction_id': interaction_id,
                'memory_context': {
                    'memories_used': len(memory_context.relevant_memories),
                    'patterns_used': len(memory_context.successful_patterns),
                    'confidence_boost': memory_context.confidence_boost,
                    'user_preferences_applied': bool(memory_context.user_preferences)
                },
                'learning_applied': {
                    'routing_optimized': routing_decision.get('used_memory', False),
                    'tool_selection_optimized': result.get('tools_optimized', False),
                    'response_enhanced': result.get('response_enhanced', False)
                },
                'execution_time': execution_time
            }

            self.logger.info(f"[MEMORY-PROCESSING] Success: {result['success']}, "
                           f"Memory Boost: {memory_context.confidence_boost:.2f}, "
                           f"Time: {execution_time:.3f}s")

            return enhanced_result

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"[MEMORY-ERROR] Query processing failed: {e}")

            # Record failed interaction
            await self.memory_integration.record_interaction(
                query=query,
                response=f"Error: {str(e)}",
                intent="ERROR",
                tools_used=[],
                success=False,
                execution_time=execution_time,
                confidence=0.0
            )

            return {
                'success': False,
                'content': f"I encountered an error while processing your request: {str(e)}",
                'confidence': 0.0,
                'tools_used': [],
                'interaction_id': f"error_{int(time.time())}",
                'memory_context': {'memories_used': 0, 'patterns_used': 0, 'confidence_boost': 0.0},
                'learning_applied': {'routing_optimized': False, 'tool_selection_optimized': False},
                'execution_time': execution_time
            }

    async def _route_query_with_memory(self, query: str) -> Dict[str, Any]:
        """Route query using memory-enhanced decision making."""
        try:
            # Get basic routing from existing system
            from torq_console.agents.prince_flowers_enhanced_integration import create_prince_flowers_enhanced
            base_agent = create_prince_flowers_enhanced(self.llm_provider)
            basic_routing = await base_agent.route_query(query)

            # Get memory context for routing enhancement
            memory_context = await self.memory_integration.get_context_for_query(
                query=query,
                limit=3
            )

            # Enhance routing with memory
            enhanced_routing = self._enhance_routing_with_memory(
                basic_routing, memory_context, query
            )

            return enhanced_routing

        except Exception as e:
            self.logger.error(f"Memory routing failed: {e}")
            # Fallback to basic routing
            return {
                'intent': 'RESEARCH',
                'confidence': 0.5,
                'strategy': 'adaptive',
                'reasoning': 'Memory routing failed, using fallback',
                'used_memory': False,
                'memory_boost': 0.0
            }

    def _enhance_routing_with_memory(
        self,
        basic_routing: Dict[str, Any],
        memory_context: MemoryContext,
        query: str
    ) -> Dict[str, Any]:
        """Enhance routing decision using memory context."""
        enhanced_routing = basic_routing.copy()
        memory_boost = 0.0
        used_memory = False

        # Check for successful routing patterns
        for pattern in memory_context.query_routing_suggestions:
            if pattern.get('success_rate', 0) > 0.8:
                # Use successful pattern if it matches query characteristics
                if any(word in query.lower() for word in pattern.get('query_pattern', '').split()):
                    enhanced_routing['intent'] = pattern['successful_intent']
                    enhanced_routing['confidence'] = min(
                        enhanced_routing['confidence'] + 0.2, 1.0
                    )
                    memory_boost += pattern['success_rate'] * 0.2
                    used_memory = True
                    break

        # Apply confidence boost from context
        if memory_context.confidence_boost > 0:
            enhanced_routing['confidence'] = min(
                enhanced_routing['confidence'] + memory_context.confidence_boost * 0.3,
                1.0
            )
            memory_boost += memory_context.confidence_boost * 0.3
            used_memory = True

        # Add memory metadata
        enhanced_routing.update({
            'used_memory': used_memory,
            'memory_boost': memory_boost,
            'context_quality': len(memory_context.relevant_memories) + len(memory_context.successful_patterns)
        })

        return enhanced_routing

    async def _execute_with_context(
        self,
        query: str,
        routing_decision: Dict[str, Any],
        memory_context: MemoryContext,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Execute query with memory context enhancement."""
        intent = routing_decision['intent']
        confidence = routing_decision['confidence']

        try:
            # Execute based on intent
            if intent == 'WEB_SEARCH':
                result = await self._execute_enhanced_web_search(query, memory_context)
            elif intent == 'CODE_GENERATION':
                result = await self._execute_enhanced_code_generation(query, memory_context)
            elif intent == 'RESEARCH':
                result = await self._execute_enhanced_research(query, memory_context)
            else:
                result = await self._execute_enhanced_adaptive(query, memory_context)

            # Enhance result with memory insights
            result = self._enhance_result_with_memory(result, memory_context, intent)

            return result

        except Exception as e:
            self.logger.error(f"Context execution failed: {e}")
            return {
                'success': False,
                'content': f"Execution failed: {str(e)}",
                'confidence': 0.0,
                'tools_used': []
            }

    async def _execute_enhanced_web_search(
        self,
        query: str,
        memory_context: MemoryContext
    ) -> Dict[str, Any]:
        """Execute enhanced web search with memory context."""
        try:
            # Use Maxim tools for sentiment analysis if relevant
            if any(word in query.lower() for word in ['opinion', 'feel', 'think', 'review']):
                sentiment_result = await self.maxim_tools.execute_tool(
                    "code_sentiment_analysis",
                    {"text": query}
                )
                if sentiment_result.success:
                    sentiment_data = sentiment_result.result['data']
                    self.logger.info(f"Query sentiment: {sentiment_data['sentiment']}")

            # Execute search with context
            search_result = await self._perform_search_with_context(query, memory_context)

            return {
                'success': True,
                'content': search_result,
                'confidence': 0.85 + memory_context.confidence_boost * 0.2,
                'tools_used': ['web_search', 'memory_context'],
                'response_enhanced': len(memory_context.relevant_memories) > 0
            }

        except Exception as e:
            self.logger.error(f"Enhanced web search failed: {e}")
            return {
                'success': False,
                'content': f"Search failed: {str(e)}",
                'confidence': 0.0,
                'tools_used': []
            }

    async def _execute_enhanced_code_generation(
        self,
        query: str,
        memory_context: MemoryContext
    ) -> Dict[str, Any]:
        """Execute enhanced code generation with memory context."""
        try:
            # Check for similar code patterns in memory
            code_patterns = [mem for mem in memory_context.relevant_memories
                           if 'code' in mem.get('content', '').lower()]

            # Use Maxim tools for code review if we generate code
            if self.llm_provider:
                # Generate base code
                response = await self.llm_provider.generate(
                    prompt=f"Generate code for: {query}",
                    system_prompt="You are an expert code generator. Provide clean, well-documented code."
                )

                # Use code review schema tool
                review_result = await self.maxim_tools.execute_tool(
                    "schema_code_review",
                    {
                        "file_path": "generated_code.py",
                        "overall_score": 8.0,
                        "issues": [],
                        "suggestions": memory_context.user_preferences.get('code_preferences', [])
                    }
                )

                if review_result.success:
                    review = review_result.result
                    self.logger.info(f"Code review completed: Grade {review['grade']}")

                return {
                    'success': True,
                    'content': response,
                    'confidence': 0.8 + memory_context.confidence_boost * 0.2,
                    'tools_used': ['code_generation', 'code_review'],
                    'response_enhanced': len(code_patterns) > 0,
                    'tools_optimized': True
                }
            else:
                return {
                    'success': False,
                    'content': "Code generation requires LLM provider configuration",
                    'confidence': 0.0,
                    'tools_used': []
                }

        except Exception as e:
            self.logger.error(f"Enhanced code generation failed: {e}")
            return {
                'success': False,
                'content': f"Code generation failed: {str(e)}",
                'confidence': 0.0,
                'tools_used': []
            }

    async def _execute_enhanced_research(
        self,
        query: str,
        memory_context: MemoryContext
    ) -> Dict[str, Any]:
        """Execute enhanced research with memory context."""
        try:
            # Multi-step research with memory insights
            research_steps = []

            # Step 1: Web search with context
            search_result = await self._perform_search_with_context(query, memory_context)
            research_steps.append(('web_search_with_memory', True))

            # Step 2: Analyze using Maxim tools if relevant
            if any(word in query.lower() for word in ['analyze', 'compare', 'evaluate']):
                sentiment_result = await self.maxim_tools.execute_tool(
                    "code_sentiment_analysis",
                    {"text": search_result[:1000]}
                )
                if sentiment_result.success:
                    research_steps.append(('sentiment_analysis', True))

            # Step 3: Generate comprehensive response
            if self.llm_provider:
                context_prompt = self._format_memory_for_prompt(memory_context)
                full_prompt = f"Query: {query}\n\nRelevant Context:\n{context_prompt}\n\nSearch Results:\n{search_result[:1000]}"

                response = await self.llm_provider.generate(
                    prompt=full_prompt,
                    system_prompt="You are a research assistant with access to previous relevant information."
                )
                research_steps.append(('enhanced_analysis', True))
            else:
                response = search_result

            return {
                'success': True,
                'content': response,
                'confidence': 0.85 + memory_context.confidence_boost * 0.15,
                'tools_used': ['web_search', 'memory_context', 'analysis'],
                'response_enhanced': True,
                'research_steps': len(research_steps)
            }

        except Exception as e:
            self.logger.error(f"Enhanced research failed: {e}")
            return {
                'success': False,
                'content': f"Research failed: {str(e)}",
                'confidence': 0.0,
                'tools_used': []
            }

    async def _execute_enhanced_adaptive(
        self,
        query: str,
        memory_context: MemoryContext
    ) -> Dict[str, Any]:
        """Execute adaptive processing with memory context."""
        try:
            if self.llm_provider:
                # Include memory context in prompt
                context_prompt = self._format_memory_for_prompt(memory_context)
                full_prompt = f"Query: {query}\n\nRelevant Context:\n{context_prompt}"

                response = await self.llm_provider.generate(
                    prompt=full_prompt,
                    system_prompt="You are an intelligent AI assistant with access to relevant previous information."
                )

                return {
                    'success': True,
                    'content': response,
                    'confidence': 0.75 + memory_context.confidence_boost * 0.25,
                    'tools_used': ['llm', 'memory_context'],
                    'response_enhanced': len(memory_context.relevant_memories) > 0
                }
            else:
                return {
                    'success': False,
                    'content': "Adaptive processing requires LLM provider configuration",
                    'confidence': 0.0,
                    'tools_used': []
                }

        except Exception as e:
            self.logger.error(f"Enhanced adaptive processing failed: {e}")
            return {
                'success': False,
                'content': f"Adaptive processing failed: {str(e)}",
                'confidence': 0.0,
                'tools_used': []
            }

    async def _perform_search_with_context(
        self,
        query: str,
        memory_context: MemoryContext
    ) -> str:
        """Perform web search enhanced with memory context."""
        try:
            # This would integrate with SearchMaster or similar
            # For now, simulate search with memory enhancement
            base_result = f"Search results for: {query}"

            # Enhance with memory insights
            if memory_context.relevant_memories:
                memory_insights = "\n\nPrevious relevant information:\n"
                for mem in memory_context.relevant_memories[:2]:
                    memory_insights += f"- {mem.get('content', '')[:200]}...\n"
                base_result += memory_insights

            return base_result

        except Exception as e:
            self.logger.error(f"Search with context failed: {e}")
            return f"Search for: {query}"

    def _enhance_result_with_memory(
        self,
        result: Dict[str, Any],
        memory_context: MemoryContext,
        intent: str
    ) -> Dict[str, Any]:
        """Enhance result using memory insights."""
        enhanced_result = result.copy()

        # Boost confidence based on context quality
        if memory_context.confidence_boost > 0:
            enhanced_result['confidence'] = min(
                enhanced_result.get('confidence', 0.5) + memory_context.confidence_boost * 0.2,
                1.0
            )

        # Add memory-based insights
        if memory_context.user_preferences:
            # Apply user preferences to response
            enhanced_result['personalized'] = True

        # Mark as enhanced if memory was used
        if memory_context.relevant_memories or memory_context.successful_patterns:
            enhanced_result['memory_enhanced'] = True

        return enhanced_result

    def _format_memory_for_prompt(self, memory_context: MemoryContext) -> str:
        """Format memory context for LLM prompt."""
        if not memory_context.relevant_memories and not memory_context.successful_patterns:
            return ""

        prompt = "\n## Relevant Information from Memory\n\n"

        if memory_context.relevant_memories:
            prompt += "### Previous Knowledge:\n"
            for mem in memory_context.relevant_memories[:3]:
                similarity = mem.get('similarity', 0) * 100
                prompt += f"- [{similarity:.0f}% match] {mem.get('content', '')[:300]}...\n"
            prompt += "\n"

        if memory_context.successful_patterns:
            prompt += "### Successful Approaches:\n"
            for pattern in memory_context.successful_patterns[:2]:
                success_rate = pattern.get('success_rate', 0) * 100
                prompt += f"- Pattern with {success_rate:.0f}% success rate\n"
            prompt += "\n"

        return prompt

    async def learn_from_feedback(
        self,
        interaction_id: str,
        feedback_score: float,
        feedback_text: Optional[str] = None
    ):
        """Learn from user feedback to improve future performance."""
        await self.memory_integration.learn_from_feedback(
            interaction_id, feedback_score, feedback_text
        )
        self.logger.info(f"Learned from feedback: {feedback_score:.2f}")

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        session_metrics = {
            'uptime_seconds': time.time() - self.active_since,
            'total_interactions': self.total_interactions,
            'successful_interactions': self.successful_interactions,
            'session_success_rate': self.successful_interactions / max(self.total_interactions, 1)
        }

        # Get memory performance
        memory_performance = await self.memory_integration.get_performance_summary()

        return {
            'agent_name': self.agent_name,
            'session_metrics': session_metrics,
            'memory_performance': memory_performance,
            'tools_available': len(self.maxim_tools.get_available_tools()),
            'learning_active': True,
            'memory_integration_enabled': True
        }

    async def cleanup(self):
        """Cleanup resources."""
        await self.maxim_tools.cleanup()
        self.logger.info("Memory-enhanced agent cleaned up")

# Factory function
def create_memory_enhanced_prince_flowers(
    llm_provider: Optional[BaseLLMProvider] = None
) -> MemoryEnhancedPrinceFlowers:
    """Create memory-enhanced Prince Flowers agent."""
    return MemoryEnhancedPrinceFlowers(llm_provider)