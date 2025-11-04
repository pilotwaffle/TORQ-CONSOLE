"""
Marvin-Powered Intelligent Query Router

Routes user queries to appropriate agents based on AI classification
of intent, complexity, and required capabilities.
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


class MarvinQueryRouter:
    """
    Intelligent query router using Marvin's classification capabilities.

    Routes user queries to the most appropriate agent based on:
    - Intent classification
    - Complexity assessment
    - Required capabilities
    - Agent availability and specialization
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

        self.logger.info("Initialized Marvin Query Router")

    async def analyze_query(self, query: str) -> QueryAnalysis:
        """
        Analyze a user query to determine routing.

        Args:
            query: User query text

        Returns:
            QueryAnalysis with classification and recommendations
        """
        try:
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

            # Determine required capabilities
            required_capabilities = self._infer_capabilities(query, intent)

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

    def _infer_capabilities(
        self,
        query: str,
        intent: IntentClassification
    ) -> List[AgentCapability]:
        """Infer required capabilities from query and intent."""
        capabilities = []

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

        # Keyword-based capability detection
        query_lower = query.lower()

        if any(kw in query_lower for kw in ['code', 'function', 'class', 'implement']):
            capabilities.append(AgentCapability.CODE_GENERATION)

        if any(kw in query_lower for kw in ['bug', 'error', 'fix', 'debug']):
            capabilities.append(AgentCapability.DEBUGGING)

        if any(kw in query_lower for kw in ['test', 'testing', 'validate']):
            capabilities.append(AgentCapability.TESTING)

        if any(kw in query_lower for kw in ['document', 'docs', 'explain']):
            capabilities.append(AgentCapability.DOCUMENTATION)

        # Default to general chat if no specific capabilities
        if not capabilities:
            capabilities.append(AgentCapability.GENERAL_CHAT)

        return list(set(capabilities))  # Remove duplicates

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

    def _build_reasoning(
        self,
        agent_name: str,
        capabilities: List[AgentCapability],
        complexity: ComplexityLevel
    ) -> str:
        """Build human-readable reasoning for agent selection."""
        cap_list = ', '.join(cap.value for cap in capabilities[:3])

        reasoning = (
            f"Selected '{agent_name}' based on required capabilities: {cap_list}. "
            f"Query complexity: {complexity.value}."
        )

        return reasoning

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
                context_requirements=context_requirements
            )

            # Store in history
            self.routing_history.append({
                'query': query[:100],  # Store snippet
                'analysis': analysis,
                'decision': decision
            })

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

    def _build_approach(
        self,
        analysis: QueryAnalysis,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Build suggested approach for handling the query."""
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

    def _determine_context_requirements(
        self,
        analysis: QueryAnalysis
    ) -> Dict[str, Any]:
        """Determine what context information is needed."""
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
            }
        )

    def get_agent_capabilities(self, agent_name: str) -> List[AgentCapability]:
        """Get capabilities for a specific agent."""
        return self.agent_registry.get(agent_name, [])

    def get_routing_history(self) -> List[Dict[str, Any]]:
        """Get routing history."""
        return self.routing_history

    def get_metrics(self) -> Dict[str, Any]:
        """Get router metrics."""
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
            'marvin_metrics': self.marvin.get_metrics()
        }


# Factory function
def create_query_router(model: Optional[str] = None) -> MarvinQueryRouter:
    """
    Create a Marvin-powered query router.

    Args:
        model: Optional LLM model override

    Returns:
        MarvinQueryRouter instance
    """
    return MarvinQueryRouter(model=model)
