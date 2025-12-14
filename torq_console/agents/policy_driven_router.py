"""
Policy-Driven Router for TORQ Console

Enhances the existing MarvinQueryRouter with policy enforcement, version tracking,
and comprehensive telemetry logging for all routing decisions.
"""

import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from .marvin_query_router import (
    MarvinQueryRouter,
    QueryAnalysis,
    RoutingDecision,
    AgentCapability
)
from .policy_framework import (
    PolicyFramework,
    PolicyComplianceStatus,
    get_policy_framework,
    IntentMapping,
    AgentDefinition
)
from ..core.telemetry.event import (
    TorqEvent,
    TorqEventType,
    EventSeverity,
    RoutingStrategy,
    RoutingDecisionEvent
)


@dataclass
class PolicyRoutingDecision:
    """Enhanced routing decision with policy compliance information."""
    base_decision: RoutingDecision
    policy_version: str
    compliance_status: PolicyComplianceStatus
    policy_violations: List[str]
    fallback_path: List[str]
    estimated_cost: float
    estimated_latency: int
    escalation_triggered: bool
    policy_metadata: Dict[str, Any]


class PolicyDrivenRouter:
    """
    Policy-driven router that enforces routing policies.

    Wraps the existing MarvinQueryRouter with policy enforcement, ensuring all
    routing decisions are policy-compliant and fully logged with version tracking.
    """

    def __init__(self, model: Optional[str] = None, policy_framework: Optional[PolicyFramework] = None):
        """
        Initialize policy-driven router.

        Args:
            model: Optional LLM model override
            policy_framework: Optional policy framework instance
        """
        self.logger = logging.getLogger("TORQ.Agents.PolicyDrivenRouter")

        # Initialize base router
        self.base_router = MarvinQueryRouter(model=model)

        # Initialize policy framework
        self.policy_framework = policy_framework or get_policy_framework()

        # Track routing metrics
        self.routing_metrics = {
            'total_routes': 0,
            'compliant_routes': 0,
            'escalations': 0,
            'fallbacks': 0,
            'violations': 0
        }

        self.logger.info(f"Policy-Driven Router initialized with policy v{self.policy_framework.get_policy_version()}")

    async def route_query(
        self,
        query: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> PolicyRoutingDecision:
        """
        Route a query with policy enforcement and comprehensive logging.

        Args:
            query: User query
            session_id: Session identifier for telemetry
            context: Optional context information

        Returns:
            PolicyRoutingDecision with full policy context
        """
        start_time = time.time()
        routing_time_ms = 0

        try:
            # Step 1: Get base routing decision from Marvin
            base_decision = await self.base_router.route_query(query, context)

            # Step 2: Extract intent and analyze with policy
            intent = self._extract_intent_from_decision(base_decision)
            confidence = base_decision.confidence

            # Step 3: Estimate cost and latency
            estimated_cost, estimated_latency = self._estimate_query_metrics(
                base_decision.primary_agent,
                base_decision.estimated_complexity,
                query
            )

            # Step 4: Validate against policy
            compliance_status, violations = self.policy_framework.validate_routing_decision(
                intent=intent,
                selected_agent=base_decision.primary_agent,
                confidence_score=confidence,
                estimated_cost=estimated_cost,
                estimated_latency=estimated_latency
            )

            # Step 5: Handle escalations and fallbacks if needed
            final_agent, fallback_path, escalation_triggered = self._handle_policy_compliance(
                intent, base_decision.primary_agent, compliance_status, violations
            )

            # Step 6: Create enhanced routing decision
            policy_decision = PolicyRoutingDecision(
                base_decision=base_decision,
                policy_version=self.policy_framework.get_policy_version(),
                compliance_status=compliance_status,
                policy_violations=violations,
                fallback_path=fallback_path,
                estimated_cost=estimated_cost,
                estimated_latency=estimated_latency,
                escalation_triggered=escalation_triggered,
                policy_metadata=self.policy_framework.get_policy_metrics()
            )

            # Step 7: Update base decision if agent was changed
            if final_agent != base_decision.primary_agent:
                policy_decision.base_decision.primary_agent = final_agent
                policy_decision.base_decision.fallback_agents = self._update_fallback_agents(
                    final_agent, base_decision.fallback_agents
                )

                # Update reasoning to reflect policy changes
                original_reasoning = base_decision.reasoning
                policy_decision.base_decision.reasoning = (
                    f"{original_reasoning} | Policy Applied: "
                    f"Escalated to {final_agent} due to: {', '.join(violations)}"
                )

            # Step 8: Calculate routing time
            routing_time_ms = int((time.time() - start_time) * 1000)

            # Step 9: Log comprehensive routing decision
            await self._log_routing_decision(
                session_id=session_id,
                query=query,
                intent=intent,
                policy_decision=policy_decision,
                routing_time_ms=routing_time_ms
            )

            # Step 10: Update metrics
            self._update_routing_metrics(compliance_status, escalation_triggered)

            self.logger.info(
                f"Query routed with policy - Agent: {final_agent}, "
                f"Compliance: {compliance_status.value}, "
                f"Violations: {len(violations)}, "
                f"Latency: {routing_time_ms}ms"
            )

            return policy_decision

        except Exception as e:
            routing_time_ms = int((time.time() - start_time) * 1000)
            self.logger.error(f"Policy-driven routing failed: {e}", exc_info=True)
            return self._create_fallback_decision(query, session_id, str(e), routing_time_ms)

    def _extract_intent_from_decision(self, decision: RoutingDecision) -> str:
        """Extract intent string from routing decision."""
        # Map capabilities to intent based on the decision
        if not decision.capabilities_needed:
            return "general_chat"

        # Priority mapping for capabilities to intent
        capability_intent_map = {
            AgentCapability.WEB_SEARCH: "web_search",
            AgentCapability.CODE_GENERATION: "code_generation",
            AgentCapability.DEBUGGING: "debugging",
            AgentCapability.DOCUMENTATION: "documentation",
            AgentCapability.TESTING: "testing",
            AgentCapability.RESEARCH: "research",
            AgentCapability.SPEC_ANALYSIS: "spec_analysis",
            AgentCapability.TASK_PLANNING: "task_planning",
            AgentCapability.CODE_REVIEW: "debugging"  # Map code review to debugging intent
        }

        # Find the highest priority capability
        for capability, intent in capability_intent_map.items():
            if capability in decision.capabilities_needed:
                return intent

        return "general_chat"

    def _estimate_query_metrics(
        self,
        agent_name: str,
        complexity_level,
        query: str
    ) -> Tuple[float, int]:
        """
        Estimate cost and latency for a query.

        Args:
            agent_name: Target agent
            complexity_level: Query complexity level
            query: Query text

        Returns:
            Tuple of (estimated_cost_usd, estimated_latency_ms)
        """
        # Estimate tokens based on query length (rough approximation)
        query_tokens = len(query.split()) * 1.3  # ~1.3 tokens per word
        estimated_output_tokens = query_tokens * 0.7  # Estimated response length
        total_tokens = int(query_tokens + estimated_output_tokens)

        # Map complexity level to multiplier
        complexity_multipliers = {
            "simple": 0.5,
            "moderate": 1.0,
            "complex": 2.0,
            "very_complex": 3.0
        }
        complexity_str = complexity_level.value if hasattr(complexity_level, 'value') else str(complexity_level)
        complexity_multiplier = complexity_multipliers.get(complexity_str, 1.0)

        # Get cost and latency estimates from policy
        estimated_cost = self.policy_framework.estimate_cost(
            agent_name, total_tokens, complexity_multiplier
        )

        estimated_latency = self.policy_framework.estimate_latency(
            agent_name, complexity_str
        )

        return estimated_cost, estimated_latency

    def _handle_policy_compliance(
        self,
        intent: str,
        primary_agent: str,
        compliance_status: PolicyComplianceStatus,
        violations: List[str]
    ) -> Tuple[str, List[str], bool]:
        """
        Handle policy compliance and determine final agent.

        Args:
            intent: User intent
            primary_agent: Originally selected agent
            compliance_status: Policy compliance status
            violations: List of policy violations

        Returns:
            Tuple of (final_agent, fallback_path, escalation_triggered)
        """
        if compliance_status == PolicyComplianceStatus.COMPLIANT:
            return primary_agent, [], False

        # Non-compliant - need escalation or fallback
        escalation_triggered = True

        # Get fallback agents from policy
        fallback_agents = self.policy_framework.get_fallback_agents(
            intent, primary_agent, violations
        )

        # Select first available fallback agent
        final_agent = fallback_agents[0] if fallback_agents else "prince_flowers"

        self.logger.info(
            f"Policy escalation triggered - Primary: {primary_agent}, "
            f"Final: {final_agent}, Violations: {violations}"
        )

        return final_agent, fallback_agents, escalation_triggered

    def _update_fallback_agents(self, primary_agent: str, original_fallbacks: List[str]) -> List[str]:
        """Update fallback agents list when primary agent changes."""
        # Remove the new primary agent from fallbacks if present
        updated_fallbacks = [agent for agent in original_fallbacks if agent != primary_agent]

        # Add the original primary agent if it's not already there
        if primary_agent not in updated_fallbacks:
            updated_fallbacks.insert(0, primary_agent)

        return updated_fallbacks[:3]  # Limit to 3 fallbacks

    async def _log_routing_decision(
        self,
        session_id: str,
        query: str,
        intent: str,
        policy_decision: PolicyRoutingDecision,
        routing_time_ms: int
    ) -> None:
        """
        Log comprehensive routing decision with policy information.

        Args:
            session_id: Session identifier
            query: User query
            intent: Classified intent
            policy_decision: Policy routing decision
            routing_time_ms: Time taken for routing
        """
        try:
            # Extract candidate agents and scores from base decision
            candidate_agents = [policy_decision.base_decision.primary_agent] + policy_decision.base_decision.fallback_agents
            agent_scores = {
                policy_decision.base_decision.primary_agent: policy_decision.base_decision.confidence
            }

            # Add scores for fallback agents (estimated)
            for i, agent in enumerate(policy_decision.base_decision.fallback_agents):
                agent_scores[agent] = policy_decision.base_decision.confidence * (0.9 ** (i + 1))

            # Create routing event with policy information
            routing_event = self.policy_framework.log_routing_decision(
                session_id=session_id,
                query=query,
                intent=intent,
                selected_agent=policy_decision.base_decision.primary_agent,
                confidence_score=policy_decision.base_decision.confidence,
                estimated_cost=policy_decision.estimated_cost,
                estimated_latency=policy_decision.estimated_latency,
                routing_time_ms=routing_time_ms,
                candidate_agents=candidate_agents,
                agent_scores=agent_scores,
                compliance_status=policy_decision.compliance_status,
                violations=policy_decision.policy_violations,
                fallback_path=policy_decision.fallback_path
            )

            # Log scored candidates if policy requires it
            if self.policy_framework.current_policy.monitoring.get("log_candidate_scoring", False):
                self._log_scored_candidates(candidate_agents, agent_scores, intent)

            # Log fallback path if policy requires it
            if self.policy_framework.current_policy.monitoring.get("log_fallback_paths", False) and policy_decision.fallback_path:
                self._log_fallback_path(
                    policy_decision.base_decision.primary_agent,
                    policy_decision.fallback_path,
                    policy_decision.policy_violations
                )

            # Log policy version if policy requires it
            if self.policy_framework.current_policy.monitoring.get("log_policy_version", False):
                self.logger.info(f"Routing decision made using policy version: {policy_decision.policy_version}")

        except Exception as e:
            self.logger.error(f"Failed to log routing decision: {e}", exc_info=True)

    def _log_scored_candidates(self, candidates: List[str], scores: Dict[str, float], intent: str) -> None:
        """Log scored candidates for routing decision."""
        self.logger.info(f"Scored candidates for intent '{intent}':")
        for agent in candidates:
            score = scores.get(agent, 0.0)
            self.logger.info(f"  - {agent}: {score:.3f}")

    def _log_fallback_path(self, primary_agent: str, fallback_path: List[str], violations: List[str]) -> None:
        """Log fallback path and triggering violations."""
        if fallback_path:
            path_str = " → ".join([primary_agent] + fallback_path)
            self.logger.info(f"Fallback path: {path_str}")
            self.logger.info(f"Triggered by violations: {', '.join(violations)}")

    def _update_routing_metrics(self, compliance_status: PolicyComplianceStatus, escalation_triggered: bool) -> None:
        """Update routing metrics."""
        self.routing_metrics['total_routes'] += 1

        if compliance_status == PolicyComplianceStatus.COMPLIANT:
            self.routing_metrics['compliant_routes'] += 1
        else:
            self.routing_metrics['violations'] += 1

            if compliance_status == PolicyComplianceStatus.ESCALATION:
                self.routing_metrics['escalations'] += 1
            elif compliance_status == PolicyComplianceStatus.FALLBACK:
                self.routing_metrics['fallbacks'] += 1

    def _create_fallback_decision(
        self,
        query: str,
        session_id: str,
        error_message: str,
        routing_time_ms: int
    ) -> PolicyRoutingDecision:
        """Create fallback routing decision when policy routing fails."""
        self.logger.warning(f"Creating fallback routing decision due to: {error_message}")

        # Create minimal base decision
        from .marvin_query_router import ComplexityLevel, Priority, SentimentClassification
        fallback_base = RoutingDecision(
            primary_agent="prince_flowers",
            fallback_agents=[],
            capabilities_needed=[AgentCapability.GENERAL_CHAT],
            estimated_complexity=ComplexityLevel.MODERATE,
            suggested_approach="Fallback workflow",
            context_requirements={},
            confidence=0.3,
            reasoning=f"Fallback due to policy routing failure: {error_message}"
        )

        return PolicyRoutingDecision(
            base_decision=fallback_base,
            policy_version=self.policy_framework.get_policy_version(),
            compliance_status=PolicyComplianceStatus.VIOLATION,
            policy_violations=[f"Policy routing failure: {error_message}"],
            fallback_path=[],
            estimated_cost=0.03,
            estimated_latency=3000,
            escalation_triggered=True,
            policy_metadata={}
        )

    async def analyze_query(self, query: str) -> QueryAnalysis:
        """
        Analyze query using base router (unchanged interface).

        Args:
            query: User query text

        Returns:
            QueryAnalysis with classification and recommendations
        """
        return await self.base_router.analyze_query(query)

    def get_policy_metrics(self) -> Dict[str, Any]:
        """Get comprehensive policy and routing metrics."""
        base_metrics = self.base_router.get_metrics()
        policy_metrics = self.policy_framework.get_policy_metrics()

        return {
            "policy_version": self.policy_framework.get_policy_version(),
            "routing_metrics": self.routing_metrics,
            "compliance_rate": (
                self.routing_metrics['compliant_routes'] / max(self.routing_metrics['total_routes'], 1)
            ),
            "escalation_rate": (
                self.routing_metrics['escalations'] / max(self.routing_metrics['total_routes'], 1)
            ),
            "fallback_rate": (
                self.routing_metrics['fallbacks'] / max(self.routing_metrics['total_routes'], 1)
            ),
            "base_router_metrics": base_metrics,
            "policy_framework_metrics": policy_metrics
        }

    def reload_policy(self) -> None:
        """Reload the routing policy."""
        self.policy_framework.reload_policy()
        self.logger.info(f"Policy reloaded - New version: {self.policy_framework.get_policy_version()}")

    def get_policy_version(self) -> str:
        """Get current policy version."""
        return self.policy_framework.get_policy_version()


# Factory function
def create_policy_driven_router(
    model: Optional[str] = None,
    policy_framework: Optional[PolicyFramework] = None
) -> PolicyDrivenRouter:
    """
    Create a policy-driven router.

    Args:
        model: Optional LLM model override
        policy_framework: Optional policy framework instance

    Returns:
        PolicyDrivenRouter instance
    """
    return PolicyDrivenRouter(model=model, policy_framework=policy_framework)