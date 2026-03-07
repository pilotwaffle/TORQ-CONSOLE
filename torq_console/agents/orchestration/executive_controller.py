"""
Executive Controller - Prince Flowers as Multi-Agent Executive

This is the Phase 4 implementation where Prince Flowers becomes the executive
controller that coordinates specialist agents rather than doing all work itself.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

from .execution_plan import (
    ExecutionPlan, ExecutionPlanBuilder, PlanTemplates,
    ExecutionMode, AgentRole, TaskPriority
)
from .delegation import (
    DelegationRequest, DelegationResult, DelegationPolicy,
    DelegationEngine, DelegationRule, DelegationRisk
)
from .agent_coordinator import AgentCoordinator, ExecutionSummary, AgentGetter
from ..core.base_agent import BaseAgent, AgentContext, AgentResult, AgentCapability


logger = logging.getLogger(__name__)


@dataclass
class ExecutiveDecision:
    """
    Prince Flowers' decision on how to handle a request.

    Attributes:
        should_delegate: Whether to delegate to a specialist
        execution_mode: How to execute (single, sequential, parallel, etc.)
        delegation_request: The delegation if applicable
        execution_plan: The full execution plan
        reason: Why this decision was made
    """
    should_delegate: bool
    execution_mode: ExecutionMode
    delegation_request: Optional[DelegationRequest] = None
    execution_plan: Optional[ExecutionPlan] = None
    reason: str = ""


class ExecutiveController:
    """
    Prince Flowers as the executive controller of TORQ Console.

    Phase 4A: Foundation for multi-agent orchestration.

    Responsibilities:
    - Receive all user requests
    - Decide between handling directly vs delegating
    - Create execution plans for multi-agent work
    - Coordinate specialist agents
    - Synthesize results into coherent responses
    - Maintain conversation context across delegations

    Prince Flowers is always the "face" of TORQ Console - users always
    interact with Prince Flowers, even when work is delegated.
    """

    def __init__(self, agent_registry=None):
        self.agent_registry = agent_registry
        self.delegation_engine = DelegationEngine()
        self.coordinator = AgentCoordinator(agent_registry)
        self.logger = logging.getLogger(__name__)

        # Conversation state
        self._conversation_state: Dict[str, Any] = {}

        # Executive metrics
        self.total_requests = 0
        self.delegate_count = 0
        self.direct_handle_count = 0

    async def process_request(
        self,
        query: str,
        context: Dict[str, Any],
        agent_getter: Optional[callable] = None
    ) -> ExecutionSummary:
        """
        Process a request as the executive controller.

        This is the main entry point for multi-agent orchestration.

        Args:
            query: The user's request
            context: Execution context (session, routing info, etc.)
            agent_getter: Function to get agent instances

        Returns:
            ExecutionSummary with the final response and metadata
        """
        start_time = __import__('time').time()
        self.total_requests += 1

        self.logger.info(f"ExecutiveController processing: {query[:100]}...")

        try:
            # Step 1: Make executive decision
            decision = await self._decide_execution_strategy(query, context)

            self.logger.info(
                f"Executive decision: delegate={decision.should_delegate}, "
                f"mode={decision.execution_mode}, reason={decision.reason}"
            )

            # Step 2: Execute based on decision
            if decision.should_delegate and decision.execution_plan:
                self.delegate_count += 1
                summary = await self._execute_with_delegation(
                    decision.execution_plan,
                    context,
                    agent_getter or self._default_agent_getter()
                )
            else:
                # Handle directly (Prince Flowers responds)
                self.direct_handle_count += 1
                summary = await self._handle_directly(query, context, agent_getter)

            # Add executive metadata
            summary.metadata["executed_by"] = "prince_flowers_executive"
            summary.metadata["decision"] = {
                "delegated": decision.should_delegate,
                "mode": decision.execution_mode.value,
                "reason": decision.reason
            }

            return summary

        except Exception as e:
            logger.error(f"ExecutiveController error: {e}")
            return ExecutionSummary(
                plan_id="error",
                mode=ExecutionMode.SINGLE_AGENT,
                total_tasks=0,
                completed_tasks=0,
                failed_tasks=0,
                total_time=__import__('time').time() - start_time,
                final_response=f"I encountered an error processing your request: {str(e)}",
                errors=[str(e)]
            )

    async def _decide_execution_strategy(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> ExecutiveDecision:
        """
        Decide how to handle a request.

        This is the "brain" of Prince Flowers - determining whether
        to delegate, what mode to use, and creating execution plans.
        """
        query_lower = query.lower()

        # Check routing override first (Phase 2 integration)
        routing_override = context.get("routing_override", {})
        if routing_override.get("active"):
            # Real-time queries should use research agent with tool enforcement
            return ExecutiveDecision(
                should_delegate=True,
                execution_mode=ExecutionMode.SINGLE_AGENT,
                reason="routing_override_active"
            )

        # Check for delegation rules
        delegation = self.delegation_engine.evaluate_delegation(query, context)

        if delegation:
            # Create execution plan for delegation
            plan = self.delegation_engine.create_execution_plan(query, context, delegation)

            return ExecutiveDecision(
                should_delegate=True,
                execution_mode=plan.mode,
                delegation_request=delegation,
                execution_plan=plan,
                reason=delegation.target_agent
            )

        # Determine complexity for mode selection
        if self._is_simple_query(query):
            return ExecutiveDecision(
                should_delegate=False,
                execution_mode=ExecutionMode.SINGLE_AGENT,
                reason="simple_query"
            )
        elif self._is_complex_multi_part(query):
            return ExecutiveDecision(
                should_delegate=True,
                execution_mode=ExecutionMode.SEQUENTIAL,
                execution_plan=PlanTemplates.research_then_synthesis(query),
                reason="complex_multi_part"
            )
        else:
            return ExecutiveDecision(
                should_delegate=False,
                execution_mode=ExecutionMode.SINGLE_AGENT,
                reason="default_handling"
            )

    async def _execute_with_delegation(
        self,
        plan: ExecutionPlan,
        context: Dict[str, Any],
        agent_getter: callable
    ) -> ExecutionSummary:
        """Execute a plan that involves specialist agents."""
        self.logger.info(f"Executing delegated plan {plan.plan_id}")

        # Check for approval requirement
        if plan.approval_required:
            self.logger.info(f"Plan {plan.plan_id} requires approval")
            # TODO: Implement approval flow
            # For now, mark as approved for autonomous execution
            # Phase 5 will add real approval gates

        # Execute the plan
        summary = await self.coordinator.execute_plan(plan, context, agent_getter)

        return summary

    async def _handle_directly(
        self,
        query: str,
        context: Dict[str, Any],
        agent_getter: Optional[callable]
    ) -> ExecutionSummary:
        """Handle request directly without delegation."""
        # Prince Flowers handles it directly
        # For now, use the research agent for most queries
        # In Phase 4B, Prince Flowers will have its own direct response capability

        # Use research agent for direct handling
        plan = PlanTemplates.research_plan(query)

        summary = await self.coordinator.execute_plan(
            plan,
            context,
            agent_getter or self._default_agent_getter()
        )

        # Override the "executed_by" metadata since we handled it
        summary.metadata["executed_by"] = "prince_flowers_direct"
        summary.metadata["decision"] = {
            "delegated": False,
            "mode": ExecutionMode.SINGLE_AGENT.value,
            "reason": "direct_handling"
        }

        return summary

    def _is_simple_query(self, query: str) -> bool:
        """Check if query is simple enough for direct handling."""
        query_lower = query.lower()

        # Simple conversational patterns
        simple_starters = [
            "hello", "hi ", "hey ", "thanks", "thank you",
            "explain", "what is", "how do", "help"
        ]

        # Short queries
        if len(query.split()) <= 5:
            return True

        # Check for simple starters
        return any(query_lower.startswith(s) for s in simple_starters)

    def _is_complex_multi_part(self, query: str) -> bool:
        """Check if query requires multiple steps/agents."""
        query_lower = query.lower()

        # Multi-part indicators
        multi_part_indicators = [
            " and then ", " then ", "after that",
            " also ", "additionally ", "furthermore",
            "analyze from multiple"
        ]

        return any(indicator in query_lower for indicator in multi_part_indicators)

    def _default_agent_getter(self) -> callable:
        """Get default agent getter function."""
        async def get_agent(agent_id: str):
            # Try to get from registry
            if self.agent_registry:
                agent = await self.agent_registry.get_agent(agent_id)
                if agent:
                    return agent

            # Fallback to returning None
            self.logger.warning(f"Agent {agent_id} not found in registry")
            return None

        return get_agent

    # ========================================================================
    # Conversation State Management (for Phase 5 autonomous operations)
    # ========================================================================

    def set_conversation_state(
        self,
        session_id: str,
        key: str,
        value: Any
    ) -> None:
        """Set conversation state for a session."""
        if session_id not in self._conversation_state:
            self._conversation_state[session_id] = {}
        self._conversation_state[session_id][key] = value

    def get_conversation_state(
        self,
        session_id: str,
        key: str,
        default: Any = None
    ) -> Any:
        """Get conversation state for a session."""
        return self._conversation_state.get(session_id, {}).get(key, default)

    def clear_conversation_state(self, session_id: str) -> None:
        """Clear conversation state for a session."""
        if session_id in self._conversation_state:
            del self._conversation_state[session_id]

    # ========================================================================
    # Metrics and Telemetry
    # ========================================================================

    def get_metrics(self) -> Dict[str, Any]:
        """Get executive controller metrics."""
        return {
            "total_requests": self.total_requests,
            "delegate_count": self.delegate_count,
            "direct_handle_count": self.direct_handle_count,
            "delegation_rate": (
                self.delegate_count / self.total_requests
                if self.total_requests > 0 else 0
            ),
            "active_plans": len(self.coordinator._active_plans),
            "plan_history_size": len(self.coordinator._plan_history),
        }


# ============================================================================
# Prince Flowers Executive Agent
# ============================================================================

class PrinceFlowersExecutive(BaseAgent):
    """
    Prince Flowers as the Executive Agent of TORQ Console.

    Phase 4A: This agent now acts as the executive controller that
    coordinates specialist agents rather than doing all work itself.

    Key difference from before:
    - OLD: Prince Flowers handled all requests directly
    - NEW: Prince Flowers decides HOW to handle requests (delegate vs direct)
              and coordinates specialist agents

    Prince Flowers is always the "face" users see - even when work is
    delegated, Prince Flowers synthesizes the final response.
    """

    def __init__(self, llm_provider=None, config=None):
        # Initialize with executive capabilities
        super().__init__(
            agent_id="torq_prince_flowers_executive",
            agent_name="Prince Flowers",
            capabilities=[
                AgentCapability.CONVERSATION,
                AgentCapability.ORCHESTRATION,
                AgentCapability.RESEARCH,
                AgentCapability.MEMORY_MANAGEMENT,
            ],
            llm_provider=llm_provider,
            config=config
        )

        # Initialize executive controller
        self.executive = ExecutiveController(agent_registry=config.get("agent_registry") if config else None)

        self.logger.info("PrinceFlowersExecutive initialized as multi-agent executive")

    async def _execute_request(
        self,
        request: str,
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """
        Execute request as executive controller.

        This is the main method - all requests to Prince Flowers go through here.
        """
        self.logger.info(f"Prince Flowers executive processing: {request[:100]}...")

        # Convert context to dict
        context_dict = {}
        if context:
            context_dict = {
                "session_id": context.session_id,
                "user_id": context.user_id,
                "workspace_id": context.workspace_id,
                "metadata": context.metadata,
                "environment": context.environment,
            }

        # Add routing context if available
        if context and hasattr(context, 'metadata'):
            context_dict.update(context.metadata)

        # Get agent getter for specialist access
        agent_getter = self._create_agent_getter()

        # Execute as executive controller
        summary = await self.executive.process_request(
            request,
            context_dict,
            agent_getter
        )

        # Convert ExecutionSummary to AgentResult
        return AgentResult(
            success=summary.is_successful,
            content=summary.final_response,
            execution_time=summary.total_time,
            metadata={
                **summary.metadata,
                "agent_results": summary.agent_results,
                "errors": summary.errors,
                "plan_id": summary.plan_id,
                "execution_mode": summary.mode.value,
            },
            warnings=[],
            error="\n".join(summary.errors) if summary.errors else None
        )

    def _create_agent_getter(self) -> callable:
        """Create a function to get specialist agents."""
        async def get_specialist_agent(agent_id: str):
            # Use custom agent_getter if provided during process_request
            if hasattr(self, '_custom_agent_getter') and self._custom_agent_getter:
                agent = await self._custom_agent_getter(agent_id)
                if agent is not None:
                    return agent

            # Try to get agent from registry
            if self.agent_registry:
                agent_card = await self.agent_registry.get_agent(agent_id)
                if agent_card:
                    # In a real implementation, we'd get the actual agent instance
                    # For now, we create a simple mock
                    from ..core.research_agent import ResearchAgent
                    from ..core.workflow_agent import WorkflowAgent
                    from ..core.conversational_agent import ConversationalAgent

                    if agent_id == "research_agent":
                        return ResearchAgent(llm_provider=self.llm_provider, config=self.config)
                    elif agent_id == "workflow_agent":
                        return WorkflowAgent(llm_provider=self.llm_provider, config=self.config)
                    elif agent_id == "conversational_agent":
                        return ConversationalAgent(llm_provider=self.llm_provider, config=self.config)

            self.logger.warning(f"Could not instantiate agent {agent_id}")
            return None

        return get_specialist_agent

    async def process_request(
        self,
        query: str,
        context: Optional[AgentContext] = None,
        agent_getter: Optional[callable] = None
    ) -> AgentResult:
        """
        Process a request with optional agent getter.

        This method provides an extended interface for the executive agent
        that accepts an optional agent_getter parameter for accessing
        specialist agents during delegation.

        Args:
            query: The user's request
            context: Optional execution context (AgentContext or dict)
            agent_getter: Optional function to get specialist agent instances

        Returns:
            AgentResult with the final response
        """
        # Convert dict context to AgentContext if needed
        if isinstance(context, dict):
            context = AgentContext(
                session_id=context.get("session_id", ""),
                user_id=context.get("user_id"),
                workspace_id=context.get("workspace_id"),
                metadata=context.get("metadata", {}),
                environment=context.get("environment", {})
            )

        # Store agent_getter for use in _create_agent_getter
        self._custom_agent_getter = agent_getter

        # Call the base process_request which will call _execute_request
        return await super().process_request(query, context)


# ============================================================================
# Convenience Functions
# ============================================================================

def create_executive_controller(agent_registry=None) -> ExecutiveController:
    """Create an executive controller instance."""
    return ExecutiveController(agent_registry=agent_registry)


def create_prince_flowers_executive(llm_provider=None, config=None) -> PrinceFlowersExecutive:
    """Create Prince Flowers executive agent."""
    return PrinceFlowersExecutive(llm_provider=llm_provider, config=config)
