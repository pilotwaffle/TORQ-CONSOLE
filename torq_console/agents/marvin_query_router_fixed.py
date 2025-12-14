"""
Fixed version of MarvinQueryRouter with better error handling for the query_lower scope issue.
"""

import logging
from typing import Dict, List, Tuple, Optional, Any
import asyncio

try:
    from ..marvin_integration.core import TorqMarvinIntegration
    MARVIN_AVAILABLE = True
except ImportError:
    MARVIN_AVAILABLE = False
    logging.warning("Marvin integration not available - using fallback router")

try:
    from ..marvin_integration.models import (
        IntentClassification, ComplexityLevel, Priority, SentimentClassification,
        AgentCapability, QueryAnalysis
    )
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False
    # Define fallback classes if models are not available
    class IntentClassification:
        CHAT = 'chat'
        WEB_SEARCH = 'web_search'
        RESEARCH = 'research'
        CODE_GENERATION = 'code_generation'
        SPEC_ANALYSIS = 'spec_analysis'

    class ComplexityLevel:
        LOW = 'low'
        MODERATE = 'moderate'
        HIGH = 'high'

    class Priority:
        LOW = 'low'
        MEDIUM = 'medium'
        HIGH = 'high'

    class SentimentClassification:
        NEUTRAL = 'neutral'
        POSITIVE = 'positive'
        NEGATIVE = 'negative'

    class AgentCapability:
        GENERAL_CHAT = 'general_chat'
        WEB_SEARCH = 'web_search'
        RESEARCH = 'research'
        CODE_GENERATION = 'code_generation'
        CODE_REVIEW = 'code_review'
        DEBUGGING = 'debugging'
        TESTING = 'testing'
        DOCUMENTATION = 'documentation'
        TASK_PLANNING = 'task_planning'
        SPEC_ANALYSIS = 'spec_analysis'

    # Simple fallback QueryAnalysis class
    from dataclasses import dataclass
    from typing import List

    @dataclass
    class QueryAnalysis:
        intent: str
        complexity: str
        priority: str
        sentiment: str
        required_capabilities: List[str]
        suggested_agent: str
        confidence: float
        reasoning: str


class MarvinQueryRouterFixed:
    """
    Fixed version of Marvin Query Router with better error handling.

    This version includes additional error handling to prevent the query_lower scope issue.
    """

    def __init__(self, model: Optional[str] = None):
        """Initialize the query router with better error handling."""
        self.logger = logging.getLogger("TORQ.Agents.QueryRouter")

        try:
            if MARVIN_AVAILABLE:
                self.marvin = TorqMarvinIntegration(model=model)
            else:
                self.marvin = None
                self.logger.warning("Marvin not available - using fallback routing only")
        except Exception as e:
            self.logger.error(f"Failed to initialize Marvin: {e}")
            self.marvin = None

        # Agent registry: agent_name -> capabilities
        self.agent_registry: Dict[str, List[AgentCapability]] = {
            'prince_flowers': [
                AgentCapability.GENERAL_CHAT,
                AgentCapability.RESEARCH,
                AgentCapability.WEB_SEARCH
            ],
            'code_generation': [
                AgentCapability.CODE_GENERATION,
                AgentCapability.CODE_REVIEW
            ],
            'debugging': [
                AgentCapability.DEBUGGING,
                AgentCapability.CODE_GENERATION
            ],
            'documentation': [
                AgentCapability.DOCUMENTATION,
                AgentCapability.CODE_REVIEW
            ],
            'testing': [
                AgentCapability.TESTING,
                AgentCapability.CODE_GENERATION
            ],
            'web_search': [
                AgentCapability.WEB_SEARCH,
                AgentCapability.RESEARCH
            ]
        }

        self.routing_history = []
        self.logger.info("Initialized Marvin Query Router (Fixed)")

    async def analyze_query(self, query: str) -> QueryAnalysis:
        """
        Analyze a user query to determine routing with enhanced error handling.

        This version includes additional safeguards to prevent variable scope issues.
        """
        try:
            if not self.marvin:
                return self._fallback_analysis(query)

            # Pre-process the query to ensure it's a valid string
            if not isinstance(query, str):
                query = str(query) if query is not None else ""

            # Ensure query is not empty after processing
            if not query.strip():
                return self._fallback_analysis("empty query")

            # Use a try-catch block specifically for the Marvin classification
            try:
                # Classify intent
                intent = await asyncio.wait_for(
                    self._safe_classify_intent(query),
                    timeout=5.0  # Add timeout to prevent hanging
                )

            except Exception as e:
                self.logger.error(f"Intent classification failed: {e}")
                intent = IntentClassification.CHAT  # Safe fallback

            try:
                # Assess complexity
                complexity = await asyncio.wait_for(
                    self._safe_classify_complexity(query),
                    timeout=5.0
                )
            except Exception as e:
                self.logger.error(f"Complexity assessment failed: {e}")
                complexity = ComplexityLevel.MODERATE  # Safe fallback

            try:
                # Determine priority
                priority = await asyncio.wait_for(
                    self._safe_classify_priority(query),
                    timeout=5.0
                )
            except Exception as e:
                self.logger.error(f"Priority assessment failed: {e}")
                priority = Priority.MEDIUM  # Safe fallback

            try:
                # Assess sentiment
                sentiment = await asyncio.wait_for(
                    self._safe_classify_sentiment(query),
                    timeout=5.0
                )
            except Exception as e:
                self.logger.error(f"Sentiment assessment failed: {e}")
                sentiment = SentimentClassification.NEUTRAL  # Safe fallback

            # Determine required capabilities with enhanced error handling
            try:
                required_capabilities = self._safe_infer_capabilities(query, intent)
            except Exception as e:
                self.logger.error(f"Capability inference failed: {e}")
                required_capabilities = [AgentCapability.GENERAL_CHAT]  # Safe fallback

            # Find best agent with error handling
            try:
                suggested_agent, confidence, reasoning = self._safe_select_agent(
                    intent,
                    complexity,
                    required_capabilities
                )
            except Exception as e:
                self.logger.error(f"Agent selection failed: {e}")
                suggested_agent = 'prince_flowers'
                confidence = 0.5
                reasoning = "Fallback agent selection due to error"

            analysis = QueryAnalysis(
                intent=intent,
                complexity=complexity,
                priority=priority,
                sentiment=sentiment,
                required_capabilities=required_capabilities,
                suggested_agent=suggested_agent,
                confidence=confidence,
                reasoning=reasoning
            )

            # Record routing decision
            self.routing_history.append({
                'query': query[:100],  # Truncate for storage
                'analysis': analysis,
                'timestamp': asyncio.get_event_loop().time()
            })

            return analysis

        except Exception as e:
            self.logger.error(f"Complete query analysis failed: {e}", exc_info=True)
            return self._fallback_analysis(query)

    async def _safe_classify_intent(self, query: str) -> IntentClassification:
        """Safely classify intent with timeout and error handling."""
        return await self.marvin.classify(
            query,
            IntentClassification,
            instructions="Classify the primary intent of this user query"
        )

    async def _safe_classify_complexity(self, query: str) -> ComplexityLevel:
        """Safely assess complexity with timeout and error handling."""
        return await self.marvin.classify(
            query,
            ComplexityLevel,
            instructions="Assess how complex this request is to fulfill"
        )

    async def _safe_classify_priority(self, query: str) -> Priority:
        """Safely determine priority with timeout and error handling."""
        return await self.marvin.classify(
            query,
            Priority,
            instructions="Determine the urgency/priority of this request"
        )

    async def _safe_classify_sentiment(self, query: str) -> SentimentClassification:
        """Safely assess sentiment with timeout and error handling."""
        return await self.marvin.classify(
            query,
            SentimentClassification,
            instructions="Assess the user's sentiment in this query"
        )

    def _safe_infer_capabilities(
        self,
        query: str,
        intent: IntentClassification
    ) -> List[AgentCapability]:
        """
        Safely infer required capabilities from query and intent.

        This version includes additional safeguards to prevent variable scope issues.
        """
        try:
            capabilities = []

            # Convert query to lowercase ONCE at the very beginning
            # This ensures it's always available throughout the method
            query_lower = query.lower() if isinstance(query, str) else str(query).lower()

            # Map intent to capabilities
            intent_capability_map = {
                IntentClassification.SPEC_CREATE: [AgentCapability.SPEC_ANALYSIS],
                IntentClassification.SPEC_ANALYZE: [AgentCapability.SPEC_ANALYSIS],
                IntentClassification.CODE_REVIEW: [AgentCapability.CODE_REVIEW],
                IntentClassification.WEB_SEARCH: [AgentCapability.WEB_SEARCH],
                IntentClassification.RESEARCH: [AgentCapability.RESEARCH],
                IntentClassification.TASK_PLANNING: [AgentCapability.TASK_PLANNING],
                IntentClassification.CHAT: [AgentCapability.GENERAL_CHAT],
            }

            capabilities.extend(intent_capability_map.get(intent, []))

            # Define all keyword patterns at the beginning to avoid scope issues
            explicit_code_patterns = [
                'write code', 'generate code', 'create code', 'implement code',
                'write a', 'create a', 'generate a', 'implement a',
                'build an app', 'build a program', 'create an app', 'build a class',
                'code for', 'code to', 'code that'
            ]

            search_keywords = [
                'search', 'find', 'look up', 'lookup', 'what is', 'what are',
                'github', 'repository', 'repo', 'latest', 'recent', 'news',
                'top', 'best', 'list', 'compare', 'trends', 'popular',
                'information about', 'tell me about', 'show me', 'get me'
            ]

            code_generation_patterns = [
                'write code', 'generate code', 'create code', 'implement code',
                'create function', 'implement function', 'write function',
                'generate function', 'write a program', 'create a program',
                'implement a class', 'create a class', 'write a class',
                'code for', 'function that', 'class that implements',
                'build an application', 'create an application'
            ]

            debug_keywords = ['bug', 'error', 'fix', 'debug']
            test_keywords = ['test', 'testing', 'validate']
            doc_keywords = ['document', 'docs', 'explain']

            # Check for explicit code generation request
            starts_with_code_request = any(
                query_lower.startswith(pattern) for pattern in explicit_code_patterns
            )

            if starts_with_code_request:
                capabilities.append(AgentCapability.CODE_GENERATION)
                return list(set(capabilities))

            # Check for search/research keywords
            is_search_query = any(kw in query_lower for kw in search_keywords)

            if is_search_query:
                if AgentCapability.WEB_SEARCH not in capabilities:
                    capabilities.append(AgentCapability.WEB_SEARCH)
                if AgentCapability.RESEARCH not in capabilities:
                    capabilities.append(AgentCapability.RESEARCH)
                return list(set(capabilities))

            # Check for other capabilities
            if any(pattern in query_lower for pattern in code_generation_patterns):
                capabilities.append(AgentCapability.CODE_GENERATION)

            if any(kw in query_lower for kw in debug_keywords):
                capabilities.append(AgentCapability.DEBUGGING)

            if any(kw in query_lower for kw in test_keywords):
                capabilities.append(AgentCapability.TESTING)

            if any(kw in query_lower for kw in doc_keywords):
                capabilities.append(AgentCapability.DOCUMENTATION)

            # Default to general chat if no specific capabilities
            if not capabilities:
                capabilities.append(AgentCapability.GENERAL_CHAT)

            return list(set(capabilities))  # Remove duplicates

        except Exception as e:
            self.logger.error(f"Error in _safe_infer_capabilities: {e}")
            return [AgentCapability.GENERAL_CHAT]  # Safe fallback

    def _safe_select_agent(
        self,
        intent: IntentClassification,
        complexity: ComplexityLevel,
        required_capabilities: List[AgentCapability]
    ) -> Tuple[str, float, str]:
        """
        Safely select the best agent for the query.

        Returns:
            Tuple of (agent_name, confidence, reasoning)
        """
        try:
            # Score each agent based on capability match
            agent_scores = {}

            for agent_name, agent_caps in self.agent_registry.items():
                # Calculate capability match score
                matched_caps = set(required_capabilities) & set(agent_caps)
                total_required = len(required_capabilities)

                if total_required > 0:
                    match_score = len(matched_caps) / total_required
                else:
                    match_score = 0.5  # Neutral score

                agent_scores[agent_name] = match_score

            # Select agent with highest score
            if agent_scores:
                best_agent = max(agent_scores.items(), key=lambda x: x[1])
                agent_name, confidence = best_agent

                reasoning = self._safe_build_reasoning(
                    agent_name,
                    required_capabilities,
                    complexity
                )

                return agent_name, confidence, reasoning
            else:
                # Default to prince_flowers
                return 'prince_flowers', 0.5, "Default agent selection"

        except Exception as e:
            self.logger.error(f"Error in _safe_select_agent: {e}")
            return 'prince_flowers', 0.5, "Fallback agent selection due to error"

    def _safe_build_reasoning(
        self,
        agent_name: str,
        capabilities: List[AgentCapability],
        complexity: ComplexityLevel
    ) -> str:
        """Safely build human-readable reasoning for agent selection."""
        try:
            if capabilities:
                cap_list = ', '.join(cap.value for cap in capabilities[:3])
                reasoning = (
                    f"Selected '{agent_name}' based on required capabilities: {cap_list}. "
                    f"Query complexity: {complexity.value}."
                )
            else:
                reasoning = f"Selected '{agent_name}' as default agent. Query complexity: {complexity.value}."

            return reasoning
        except Exception as e:
            self.logger.error(f"Error in _safe_build_reasoning: {e}")
            return f"Selected '{agent_name}' using fallback reasoning."

    def _fallback_analysis(self, query: str) -> QueryAnalysis:
        """
        Provide fallback analysis when Marvin is not available.
        """
        query_lower = query.lower() if isinstance(query, str) else str(query).lower()

        # Simple keyword-based fallback
        if any(word in query_lower for word in ['search', 'find', 'what is', 'what are']):
            intent = IntentClassification.WEB_SEARCH
            required_capabilities = [AgentCapability.WEB_SEARCH, AgentCapability.RESEARCH]
        elif any(word in query_lower for word in ['write', 'create', 'generate', 'implement', 'code']):
            intent = IntentClassification.CODE_GENERATION
            required_capabilities = [AgentCapability.CODE_GENERATION]
        else:
            intent = IntentClassification.CHAT
            required_capabilities = [AgentCapability.GENERAL_CHAT]

        return QueryAnalysis(
            intent=intent,
            complexity=ComplexityLevel.MODERATE,
            priority=Priority.MEDIUM,
            sentiment=SentimentClassification.NEUTRAL,
            required_capabilities=required_capabilities,
            suggested_agent='prince_flowers',
            confidence=0.5,
            reasoning='Fallback analysis due to Marvin unavailability'
        )


def create_query_router_fixed(model: Optional[str] = None) -> MarvinQueryRouterFixed:
    """
    Create a fixed Marvin-powered query router.

    Args:
        model: Optional LLM model override

    Returns:
        MarvinQueryRouterFixed instance
    """
    return MarvinQueryRouterFixed(model=model)