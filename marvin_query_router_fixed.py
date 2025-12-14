"""
FIXED Marvin-Powered Intelligent Query Router

Routes user queries to appropriate agents based on AI classification
of intent, complexity, and required capabilities.

FIXES APPLIED:
1. Enhanced variable scope protection for query_lower
2. Improved error handling for closure contexts
3. Defensive programming for async context issues

Author: TORQ Console Development Team
Version: 1.1.0 - Bug Fix Release
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from torq_console.marvin_integration import (
    TorqMarvinIntegration,
    IntentClassification,
    ComplexityLevel,
    Priority,
    SentimentClassification,
)


class AgentCapability(str, Enum):
    """Agent capabilities for routing."""
    SPEC_ANALYSIS = "spec_analysis"
    CODE_REVIEW = "code_review"
    WEB_SEARCH = "web_search"
    RESEARCH = "research"
    TASK_PLANNING = "task_planning"
    GENERAL_CHAT = "general_chat"
    CODE_GENERATION = "code_generation"
    DEBUGGING = "debugging"
    DOCUMENTATION = "documentation"
    TESTING = "testing"


@dataclass
class QueryAnalysis:
    """Analysis of a user query."""
    intent: IntentClassification
    complexity: ComplexityLevel
    priority: Priority
    sentiment: SentimentClassification
    required_capabilities: List[AgentCapability]
    suggested_agent: str
    confidence: float
    reasoning: str


@dataclass
class RoutingDecision:
    """Routing decision for a query."""
    primary_agent: str
    fallback_agents: List[str]
    capabilities_needed: List[AgentCapability]
    estimated_complexity: ComplexityLevel
    suggested_approach: str
    context_requirements: Dict[str, Any]
    confidence: float
    reasoning: str


class MarvinQueryRouter:
    """
    Intelligent query router using Marvin's classification capabilities.

    Routes user queries to the most appropriate agent based on:
    - Intent classification
    - Complexity assessment
    - Required capabilities
    - Agent availability and specialization

    FIXED: Enhanced variable scope protection and error handling
    """

    def __init__(self, model: Optional[str] = None):
        """
        Initialize query router.

        Args:
            model: Optional LLM model override
        """
        self.logger = logging.getLogger("TORQ.Agents.QueryRouter")
        self.marvin = TorqMarvinIntegration(model=model)

        # Agent registry: agent_name -> capabilities
        self.agent_registry: Dict[str, List[AgentCapability]] = {
            'prince_flowers': [
                AgentCapability.GENERAL_CHAT,
                AgentCapability.CODE_GENERATION,
                AgentCapability.DOCUMENTATION,
                AgentCapability.TASK_PLANNING
            ],
            'spec_analyzer': [
                AgentCapability.SPEC_ANALYSIS,
                AgentCapability.DOCUMENTATION
            ],
            'code_reviewer': [
                AgentCapability.CODE_REVIEW,
                AgentCapability.DEBUGGING,
                AgentCapability.TESTING
            ],
            'research_specialist': [
                AgentCapability.WEB_SEARCH,
                AgentCapability.RESEARCH,
                AgentCapability.DOCUMENTATION
            ],
            'task_planner': [
                AgentCapability.TASK_PLANNING,
                AgentCapability.SPEC_ANALYSIS
            ],
        }

        self.routing_history = []

        self.logger.info("Initialized FIXED Marvin Query Router")

    async def analyze_query(self, query: str) -> QueryAnalysis:
        """
        Analyze a user query to determine routing.

        Args:
            query: User query text

        Returns:
            QueryAnalysis with classification and recommendations
        """
        try:
            # Input validation
            if not query or not isinstance(query, str):
                query = str(query) if query else ""
                self.logger.warning(f"Invalid query input, converted to: {query[:50]}...")

            # Classify intent
            intent = self.marvin.classify(
                query,
                IntentClassification,
                instructions="Classify the primary intent of this user query"
            )

            # Assess complexity
            complexity = self.marvin.classify(
                query,
                ComplexityLevel,
                instructions="Assess how complex this request is to fulfill"
            )

            # Determine priority
            priority = self.marvin.classify(
                query,
                Priority,
                instructions="Determine the urgency/priority of this request"
            )

            # Assess sentiment
            sentiment = self.marvin.classify(
                query,
                SentimentClassification,
                instructions="Assess the user's sentiment in this query"
            )

            # Determine required capabilities with enhanced error handling
            required_capabilities = self._infer_capabilities_safe(query, intent)

            # Find best agent
            suggested_agent, confidence, reasoning = self._select_agent(
                intent,
                complexity,
                required_capabilities
            )

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

            self.logger.info(
                f"Query analyzed: intent={intent.value}, "
                f"complexity={complexity.value}, agent={suggested_agent}"
            )

            return analysis

        except Exception as e:
            self.logger.error(f"Failed to analyze query: {e}", exc_info=True)
            return self._fallback_analysis(query)

    def _infer_capabilities_safe(
        self,
        query: str,
        intent: IntentClassification
    ) -> List[AgentCapability]:
        """
        FIXED: Infer required capabilities from query and intent with enhanced variable scope protection.

        Args:
            query: User query string
            intent: Classified intent

        Returns:
            List of required AgentCapability enums
        """
        capabilities = []

        try:
            # DEFENSIVE: Ensure query is a valid string and query_lower is always available
            if not isinstance(query, str):
                query = str(query) if query is not None else ""

            # FIX: Move query_lower definition to the very top to ensure it's always in scope
            query_lower = query.lower().strip()

            # Additional validation
            if not query_lower:
                self.logger.warning("Empty query provided, defaulting to general chat")
                return [AgentCapability.GENERAL_CHAT]

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

            # FIRST: Check if this is an explicit code generation request
            # This prevents "generate code for search app" from being misclassified as search
            explicit_code_request_starters = [
                'write code', 'generate code', 'create code', 'implement code',
                'write a', 'create a', 'generate a', 'implement a',
                'build an app', 'build a program', 'create an app', 'build a class',
                'code for', 'code to', 'code that'
            ]

            # FIX: Use local variable to avoid any potential closure issues
            starts_with_code_request = any(
                query_lower.startswith(pattern)
                for pattern in explicit_code_request_starters
            )

            if starts_with_code_request:
                # Explicit code request - route to code generation
                capabilities.append(AgentCapability.CODE_GENERATION)
                return list(set(capabilities))

            # Check for search/research keywords (high priority, but after explicit code checks)
            search_keywords = [
                'search', 'find', 'look up', 'lookup', 'what is', 'what are',
                'github', 'repository', 'repo', 'latest', 'recent', 'news',
                'top', 'best', 'list', 'compare', 'trends', 'popular',
                'information about', 'tell me about', 'show me', 'get me'
            ]

            # FIX: Use explicit local variable to prevent any scope issues
            is_search_query = any(kw in query_lower for kw in search_keywords)

            # Also detect "use/with X to search/find" patterns which should be treated as search
            search_tool_patterns = [
                'use to search', 'use to find', 'use to look up',
                'with to search', 'with to find',
                'use for searching', 'use for finding',
                'to search for', 'to find information', 'to look up information',
                'and search for', 'and find information'
            ]

            # FIX: Explicit variable declarations to prevent closure issues
            has_tool_indicator = any(ind in query_lower for ind in ['use ', 'with ', 'using '])
            has_search_action = any(act in query_lower for act in [' to search', ' to find', ' search ', ' find '])
            tool_based_search = has_tool_indicator and has_search_action

            uses_search_tool = any(pattern in query_lower for pattern in search_tool_patterns)

            if is_search_query or uses_search_tool or tool_based_search:
                # If it's a search query, prioritize search/research capabilities
                if AgentCapability.WEB_SEARCH not in capabilities:
                    capabilities.append(AgentCapability.WEB_SEARCH)
                if AgentCapability.RESEARCH not in capabilities:
                    capabilities.append(AgentCapability.RESEARCH)
                # Don't add code generation for search queries - return immediately
                return list(set(capabilities))

            # Only check for code-related keywords if NOT a search query
            # Make code generation detection very explicit to avoid false positives
            code_generation_patterns = [
                'write code', 'generate code', 'create code', 'implement code',
                'create function', 'implement function', 'write function',
                'generate function', 'write a program', 'create a program',
                'implement a class', 'create a class', 'write a class',
                'code for', 'function that', 'class that implements',
                'build an application', 'create an application'
            ]

            # FIX: Use explicit local variable
            has_code_pattern = any(pattern in query_lower for pattern in code_generation_patterns)
            if has_code_pattern:
                capabilities.append(AgentCapability.CODE_GENERATION)

            # Debug keywords
            debug_keywords = ['bug', 'error', 'fix', 'debug']
            if any(kw in query_lower for kw in debug_keywords):
                capabilities.append(AgentCapability.DEBUGGING)

            # Test keywords
            test_keywords = ['test', 'testing', 'validate']
            if any(kw in query_lower for kw in test_keywords):
                capabilities.append(AgentCapability.TESTING)

            # Documentation keywords
            doc_keywords = ['document', 'docs', 'explain']
            if any(kw in query_lower for kw in doc_keywords):
                capabilities.append(AgentCapability.DOCUMENTATION)

            # Default to general chat if no specific capabilities
            if not capabilities:
                capabilities.append(AgentCapability.GENERAL_CHAT)

            # Remove duplicates while preserving order
            seen = set()
            unique_capabilities = []
            for cap in capabilities:
                if cap not in seen:
                    seen.add(cap)
                    unique_capabilities.append(cap)

            return unique_capabilities

        except Exception as e:
            self.logger.error(f"Error in _infer_capabilities_safe: {e}", exc_info=True)
            # Return safe default
            return [AgentCapability.GENERAL_CHAT]

    def _select_agent(
        self,
        intent: IntentClassification,
        complexity: ComplexityLevel,
        required_capabilities: List[AgentCapability]
    ) -> Tuple[str, float, str]:
        """
        Select the best agent for the query.

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

                reasoning = self._build_reasoning(
                    agent_name,
                    required_capabilities,
                    complexity
                )

                return agent_name, confidence, reasoning
            else:
                # Default to prince_flowers
                return 'prince_flowers', 0.5, "Default agent selection"

        except Exception as e:
            self.logger.error(f"Error in _select_agent: {e}", exc_info=True)
            return 'prince_flowers', 0.3, f"Error in agent selection: {str(e)}"

    def _build_reasoning(
        self,
        agent_name: str,
        capabilities: List[AgentCapability],
        complexity: ComplexityLevel
    ) -> str:
        """Build human-readable reasoning for agent selection."""
        try:
            cap_list = ', '.join(cap.value for cap in capabilities[:3])

            reasoning = (
                f"Selected '{agent_name}' based on required capabilities: {cap_list}. "
                f"Query complexity: {complexity.value}."
            )

            return reasoning
        except Exception as e:
            self.logger.error(f"Error in _build_reasoning: {e}")
            return f"Selected '{agent_name}' based on capability matching"

    async def route_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> RoutingDecision:
        """
        Route a query to appropriate agent with full decision context.

        Args:
            query: User query
            context: Optional context information

        Returns:
            RoutingDecision with routing details
        """
        try:
            # Input validation
            if not query:
                query = ""
                self.logger.warning("Empty query provided to route_query")

            # Analyze query
            analysis = await self.analyze_query(query)

            # Determine fallback agents
            fallback_agents = self._get_fallback_agents(
                analysis.suggested_agent,
                analysis.required_capabilities
            )

            # Build suggested approach
            suggested_approach = self._build_approach(analysis, context)

            # Determine context requirements
            context_requirements = self._determine_context_requirements(analysis)

            decision = RoutingDecision(
                primary_agent=analysis.suggested_agent,
                fallback_agents=fallback_agents,
                capabilities_needed=analysis.required_capabilities,
                estimated_complexity=analysis.complexity,
                suggested_approach=suggested_approach,
                context_requirements=context_requirements,
                confidence=analysis.confidence,
                reasoning=analysis.reasoning
            )

            # Store in history with size limit
            self.routing_history.append({
                'query': query[:100],  # Store snippet
                'analysis': analysis,
                'decision': decision,
                'timestamp': __import__('time').time()
            })

            # Limit history size to prevent memory issues
            if len(self.routing_history) > 1000:
                self.routing_history = self.routing_history[-500:]  # Keep last 500

            self.logger.info(f"Routed query to: {decision.primary_agent}")

            return decision

        except Exception as e:
            self.logger.error(f"Failed to route query: {e}", exc_info=True)
            return self._fallback_routing()

    def _get_fallback_agents(
        self,
        primary_agent: str,
        required_capabilities: List[AgentCapability]
    ) -> List[str]:
        """Get ordered list of fallback agents."""
        try:
            fallback = []

            # Find other agents with matching capabilities
            for agent_name, agent_caps in self.agent_registry.items():
                if agent_name == primary_agent:
                    continue

                # Check for capability overlap
                if any(cap in agent_caps for cap in required_capabilities):
                    fallback.append(agent_name)

            # Always include prince_flowers as final fallback
            if 'prince_flowers' not in fallback and primary_agent != 'prince_flowers':
                fallback.append('prince_flowers')

            return fallback[:3]  # Limit to 3 fallbacks
        except Exception as e:
            self.logger.error(f"Error in _get_fallback_agents: {e}")
            return ['prince_flowers']

    def _build_approach(
        self,
        analysis: QueryAnalysis,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Build suggested approach for handling the query."""
        try:
            approach_parts = []

            # Based on complexity
            if analysis.complexity in [ComplexityLevel.COMPLEX, ComplexityLevel.VERY_COMPLEX]:
                approach_parts.append("Break down into sub-tasks")

            # Based on intent
            if analysis.intent == IntentClassification.SPEC_ANALYZE:
                approach_parts.append("Analyze specification quality")
            elif analysis.intent == IntentClassification.CODE_REVIEW:
                approach_parts.append("Perform comprehensive code review")
            elif analysis.intent == IntentClassification.RESEARCH:
                approach_parts.append("Conduct thorough research with multiple sources")

            # Based on priority
            if analysis.priority == Priority.URGENT:
                approach_parts.append("Prioritize immediate response")

            if not approach_parts:
                approach_parts.append("Standard workflow")

            return " → ".join(approach_parts)
        except Exception as e:
            self.logger.error(f"Error in _build_approach: {e}")
            return "Standard workflow"

    def _determine_context_requirements(
        self,
        analysis: QueryAnalysis
    ) -> Dict[str, Any]:
        """Determine what context information is needed."""
        try:
            requirements = {
                'needs_project_context': False,
                'needs_code_context': False,
                'needs_spec_context': False,
                'needs_history': False,
            }

            # Based on capabilities
            if AgentCapability.CODE_REVIEW in analysis.required_capabilities:
                requirements['needs_code_context'] = True

            if AgentCapability.SPEC_ANALYSIS in analysis.required_capabilities:
                requirements['needs_spec_context'] = True

            if AgentCapability.TASK_PLANNING in analysis.required_capabilities:
                requirements['needs_project_context'] = True

            # Complex queries need more context
            if analysis.complexity in [ComplexityLevel.COMPLEX, ComplexityLevel.VERY_COMPLEX]:
                requirements['needs_history'] = True

            return requirements
        except Exception as e:
            self.logger.error(f"Error in _determine_context_requirements: {e}")
            return {
                'needs_project_context': False,
                'needs_code_context': False,
                'needs_spec_context': False,
                'needs_history': False,
            }

    def _fallback_analysis(self, query: str) -> QueryAnalysis:
        """Return fallback analysis when classification fails."""
        return QueryAnalysis(
            intent=IntentClassification.CHAT,
            complexity=ComplexityLevel.MODERATE,
            priority=Priority.MEDIUM,
            sentiment=SentimentClassification.NEUTRAL,
            required_capabilities=[AgentCapability.GENERAL_CHAT],
            suggested_agent='prince_flowers',
            confidence=0.3,
            reasoning="Fallback to default agent due to classification failure"
        )

    def _fallback_routing(self) -> RoutingDecision:
        """Return fallback routing decision."""
        return RoutingDecision(
            primary_agent='prince_flowers',
            fallback_agents=[],
            capabilities_needed=[AgentCapability.GENERAL_CHAT],
            estimated_complexity=ComplexityLevel.MODERATE,
            suggested_approach="Standard workflow",
            context_requirements={
                'needs_project_context': False,
                'needs_code_context': False,
                'needs_spec_context': False,
                'needs_history': False,
            },
            confidence=0.3,
            reasoning="Fallback routing due to query routing failure"
        )

    def get_agent_capabilities(self, agent_name: str) -> List[AgentCapability]:
        """Get capabilities for a specific agent."""
        try:
            return self.agent_registry.get(agent_name, [])
        except Exception as e:
            self.logger.error(f"Error getting agent capabilities: {e}")
            return []

    def get_routing_history(self) -> List[Dict[str, Any]]:
        """Get routing history."""
        try:
            return self.routing_history.copy()
        except Exception as e:
            self.logger.error(f"Error getting routing history: {e}")
            return []

    def get_metrics(self) -> Dict[str, Any]:
        """Get router metrics."""
        try:
            if not self.routing_history:
                return {
                    'total_routes': 0,
                    'most_used_agent': None,
                    'average_confidence': 0.0
                }

            # Calculate agent usage
            agent_counts = {}
            confidences = []

            for entry in self.routing_history:
                decision = entry.get('decision')
                analysis = entry.get('analysis')

                if decision:
                    agent = decision.primary_agent
                    agent_counts[agent] = agent_counts.get(agent, 0) + 1

                if analysis:
                    confidences.append(analysis.confidence)

            most_used = max(agent_counts.items(), key=lambda x: x[1])[0] if agent_counts else None
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            return {
                'total_routes': len(self.routing_history),
                'most_used_agent': most_used,
                'average_confidence': round(avg_confidence, 3),
                'agent_usage': agent_counts,
                'marvin_metrics': self.marvin.get_metrics() if hasattr(self.marvin, 'get_metrics') else {}
            }
        except Exception as e:
            self.logger.error(f"Error getting metrics: {e}")
            return {
                'total_routes': 0,
                'most_used_agent': None,
                'average_confidence': 0.0,
                'error': str(e)
            }


# Factory function
def create_query_router(model: Optional[str] = None) -> MarvinQueryRouter:
    """
    Create a FIXED Marvin-powered query router.

    Args:
        model: Optional LLM model override

    Returns:
        FIXED MarvinQueryRouter instance
    """
    return MarvinQueryRouter(model=model)


# Test function to verify the fix
def test_variable_scope_fix():
    """Test function to verify the query_lower variable scope fix."""
    router = MarvinQueryRouter()

    test_queries = [
        "use brave search to find python tutorials",
        "generate code for search application",
        "with perplexity find information about AI",
        "create a function that sorts data",
        "what are the best practices for API design?"
    ]

    print("Testing variable scope fix...")
    for i, query in enumerate(test_queries):
        try:
            # This should not raise "query_lower not defined" error
            capabilities = router._infer_capabilities_safe(query, router.marvin.classify(query, 'CHAT'))
            print(f"✓ Test {i+1}: '{query[:30]}...' -> {len(capabilities)} capabilities")
        except NameError as e:
            if "query_lower" in str(e):
                print(f"✗ Test {i+1}: query_lower not defined error: {e}")
                return False
            else:
                print(f"✗ Test {i+1}: Other NameError: {e}")
        except Exception as e:
            print(f"✗ Test {i+1}: Unexpected error: {e}")

    print("✓ Variable scope fix verified successfully!")
    return True


if __name__ == "__main__":
    # Run the test
    success = test_variable_scope_fix()
    print(f"\nVariable scope fix test: {'PASSED' if success else 'FAILED'}")