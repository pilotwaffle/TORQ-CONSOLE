"""
Delegation System - Multi-Agent Coordination

Defines how Prince Flowers delegates tasks to specialist agents
and how results flow back through the system.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Awaitable

from pydantic import BaseModel, Field

from .execution_plan import ExecutionPlan, AgentTask, AgentRole, ExecutionMode


class DelegationPolicy(str, Enum):
    """
    Policy for how Prince Flowers should delegate.

    DIRECT: Prince Flowers handles it directly
    CONSULT: Ask specialist for input, but Prince decides
    DELEGATE: Specialist handles it, Prince reviews
    AUTONOMOUS: Specialist handles it fully (with approval gates)
    """
    DIRECT = "direct"
    CONSULT = "consult"
    DELEGATE = "delegate"
    AUTONOMOUS = "autonomous"


class DelegationRisk(str, Enum):
    """Risk level of a delegated task."""
    LOW = "low"          # Read-only, no side effects
    MEDIUM = "medium"    # Creates content, no external actions
    HIGH = "high"        # External side effects, system changes
    CRITICAL = "critical"  # Destructive, requires explicit approval


@dataclass
class DelegationRequest:
    """
    A request from Prince Flowers to delegate work to a specialist agent.

    Attributes:
        request_id: Unique identifier
        parent_plan: The execution plan this delegation is part of
        target_agent: Which agent to delegate to
        agent_role: The role that agent will play
        task: The specific task to perform
        context: Additional context for the task
        policy: How to handle the delegation
        risk: Risk level of this delegation
        requires_approval: Whether this needs approval before execution
        timeout: Maximum time to allow
    """
    request_id: str
    parent_plan: str
    target_agent: str
    agent_role: AgentRole
    task: str
    context: Dict[str, Any] = field(default_factory=dict)
    policy: DelegationPolicy = DelegationPolicy.DELEGATE
    risk: DelegationRisk = DelegationRisk.MEDIUM
    requires_approval: bool = False
    timeout: int = 120
    created_at: float = field(default_factory=time.time)

    # State tracking
    status: str = "pending"  # pending, approved, rejected, running, completed, failed
    approved_by: Optional[str] = None
    approved_at: Optional[float] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None


@dataclass
class DelegationResult:
    """
    Result from a specialist agent after delegation.

    Attributes:
        request_id: The original delegation request ID
        success: Whether the delegation succeeded
        agent_id: Which agent handled this
        agent_role: Role the agent played
        content: The main response content
        data: Structured data returned by the agent
        execution_time: How long the delegation took
        metadata: Additional information
        error: Error message if failed
    """
    request_id: str
    success: bool
    agent_id: str
    agent_role: AgentRole
    content: str
    data: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    @property
    def has_data(self) -> bool:
        """Check if result has structured data."""
        return bool(self.data)

    @property
    def has_error(self) -> bool:
        """Check if result has an error."""
        return self.error is not None


# ============================================================================
# Delegation Rules
# ============================================================================

class DelegationRule:
    """
    Rule for when to delegate to a specialist agent.

    Rules are evaluated in order; first matching rule wins.
    """

    def __init__(
        self,
        name: str,
        condition: Callable[[str, Dict[str, Any]], bool],
        target_agent: str,
        agent_role: AgentRole,
        policy: DelegationPolicy = DelegationPolicy.DELEGATE,
        risk: DelegationRisk = DelegationRisk.MEDIUM,
        reason: str = ""
    ):
        self.name = name
        self.condition = condition
        self.target_agent = target_agent
        self.agent_role = agent_role
        self.policy = policy
        self.risk = risk
        self.reason = reason

    def evaluate(self, query: str, context: Dict[str, Any]) -> bool:
        """Evaluate if this rule applies to the given query."""
        try:
            return self.condition(query, context)
        except Exception:
            return False


class DelegationRules:
    """
    Built-in delegation rules for Prince Flowers.

    These rules determine when Prince Flowers should delegate to specialists
    versus handling the request directly.
    """

    @staticmethod
    def get_default_rules() -> List[DelegationRule]:
        """Get default delegation rules.

        Rules are evaluated in order; first matching rule wins.
        More specific rules should come before general ones.
        """
        return [
            # Complex multi-step planning goes to Orchestration Agent (check first)
            DelegationRule(
                name="complex_planning",
                condition=lambda q, c: DelegationRules._is_complex_planning(q, c),
                target_agent="orchestration_agent",
                agent_role=AgentRole.ORCHESTRATOR,
                policy=DelegationPolicy.CONSULT,
                risk=DelegationRisk.MEDIUM,
                reason="Query requires complex multi-step planning"
            ),

            # Workflow building goes to Workflow Agent
            DelegationRule(
                name="workflow_building",
                condition=lambda q, c: DelegationRules._is_workflow_query(q, c),
                target_agent="workflow_agent",
                agent_role=AgentRole.WORKFLOW,
                policy=DelegationPolicy.DELEGATE,
                risk=DelegationRisk.MEDIUM,
                reason="Query requires workflow design or automation"
            ),

            # Code writing goes to Workflow Agent (code generation capability)
            DelegationRule(
                name="code_generation",
                condition=lambda q, c: DelegationRules._is_code_query(q, c),
                target_agent="workflow_agent",
                agent_role=AgentRole.WORKFLOW,
                policy=DelegationPolicy.DELEGATE,
                risk=DelegationRisk.MEDIUM,
                reason="Query requires code generation"
            ),

            # Research queries go to Research Agent (check last - most general)
            DelegationRule(
                name="research_query",
                condition=lambda q, c: DelegationRules._is_research_query(q, c),
                target_agent="research_agent",
                agent_role=AgentRole.RESEARCHER,
                policy=DelegationPolicy.DELEGATE,
                risk=DelegationRisk.LOW,
                reason="Query requires research and information gathering"
            ),
        ]

    @staticmethod
    def _is_research_query(query: str, context: Dict[str, Any]) -> bool:
        """Check if query is research-oriented."""
        query_lower = query.lower()

        research_keywords = [
            "search", "find", "research", "look up", "investigate",
            "latest", "current", "news", "what's happening",
            "compare", "analysis", "data"
        ]

        # Check for explicit research intent
        if any(kw in query_lower for kw in research_keywords):
            return True

        # Check routing override
        routing_override = context.get("routing_override", {})
        if routing_override.get("active"):
            return routing_override.get("reason") in [
                "current_news", "latest_ai", "realtime_finance",
                "realtime_lookup", "current_lookup"
            ]

        return False

    @staticmethod
    def _is_workflow_query(query: str, context: Dict[str, Any]) -> bool:
        """Check if query is workflow-oriented."""
        query_lower = query.lower()

        workflow_keywords = [
            "workflow", "automate", "automation", "pipeline",
            "build a", "create a", "design a",
            "steps to", "process for", "how do i"
        ]

        return any(kw in query_lower for kw in workflow_keywords)

    @staticmethod
    def _is_complex_planning(query: str, context: Dict[str, Any]) -> bool:
        """Check if query requires complex planning."""
        query_lower = query.lower()

        planning_keywords = [
            "plan", "strategy", "roadmap", "architecture",
            "multi-step", "comprehensive", "end-to-end"
        ]

        # Check for AND patterns suggesting multiple requirements
        if " and " in query_lower and query_lower.count(" and ") >= 2:
            return True

        return any(kw in query_lower for kw in planning_keywords)

    @staticmethod
    def _is_code_query(query: str, context: Dict[str, Any]) -> bool:
        """Check if query requires code generation."""
        query_lower = query.lower()

        code_keywords = [
            "write", "generate", "create", "implement",
            "function", "class", "code", "script"
        ]

        # Must have code-related term
        code_terms = ["function", "class", "api", "endpoint", "method", "script"]
        has_code_term = any(term in query_lower for term in code_terms)

        return has_code_term and any(kw in query_lower for kw in code_keywords)


# ============================================================================
# Delegation Engine
# ============================================================================

class DelegationEngine:
    """
    Engine for managing delegation from Prince Flowers to specialists.

    Responsibilities:
    - Evaluate delegation rules
    - Create delegation requests
    - Track delegation state
    - Collect and aggregate results
    """

    def __init__(self, rules: Optional[List[DelegationRule]] = None):
        self.rules = rules or DelegationRules.get_default_rules()
        self._active_delegations: Dict[str, DelegationRequest] = {}
        self.logger = __import__('logging').getLogger(__name__)

    def evaluate_delegation(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> Optional[DelegationRequest]:
        """
        Evaluate if a query should be delegated.

        Returns:
            DelegationRequest if delegation is needed, None otherwise
        """
        for rule in self.rules:
            if rule.evaluate(query, context):
                self.logger.info(
                    f"Delegation rule '{rule.name}' matched: "
                    f"target={rule.target_agent}, policy={rule.policy}"
                )

                return DelegationRequest(
                    request_id=f"del_{uuid.uuid4().hex[:8]}",
                    parent_plan=context.get("plan_id", ""),
                    target_agent=rule.target_agent,
                    agent_role=rule.agent_role,
                    task=query,
                    context=context,
                    policy=rule.policy,
                    risk=rule.risk,
                    requires_approval=rule.risk in [DelegationRisk.HIGH, DelegationRisk.CRITICAL]
                )

        # No rule matched - Prince Flowers handles directly
        return None

    def create_execution_plan(
        self,
        query: str,
        context: Dict[str, Any],
        delegation: DelegationRequest
    ) -> ExecutionPlan:
        """
        Create an execution plan from a delegation request.

        This is the bridge between delegation and execution planning.
        """
        from .execution_plan import ExecutionPlanBuilder, PlanTemplates

        # Choose plan template based on agent role and policy
        if delegation.agent_role == AgentRole.RESEARCHER:
            # Research-focused plan
            return PlanTemplates.research_plan(query, delegation.target_agent)

        elif delegation.agent_role == AgentRole.WORKFLOW:
            # Workflow building plan
            return PlanTemplates.workflow_with_research(query)

        elif delegation.agent_role == AgentRole.ORCHESTRATOR:
            # Complex planning - may need multiple steps
            return PlanTemplates.research_then_synthesis(query)

        else:
            # Default single-agent plan
            return PlanTemplates.research_plan(query, delegation.target_agent)

    async def execute_delegation(
        self,
        delegation: DelegationRequest,
        agent_registry
    ) -> DelegationResult:
        """
        Execute a delegation request by calling the target agent.

        Args:
            delegation: The delegation request
            agent_registry: Registry to get agent instances

        Returns:
            DelegationResult with the agent's response
        """
        start_time = time.time()

        # Update status
        delegation.status = "running"
        delegation.started_at = start_time

        try:
            # Get agent instance
            agent = await agent_registry.get_agent(delegation.target_agent)
            if not agent:
                return DelegationResult(
                    request_id=delegation.request_id,
                    success=False,
                    agent_id=delegation.target_agent,
                    agent_role=delegation.agent_role,
                    content="",
                    error=f"Agent {delegation.target_agent} not found"
                )

            # Execute the task
            from ..core.base_agent import AgentContext
            agent_context = AgentContext(
                session_id=delegation.context.get("session_id", ""),
                metadata=delegation.context
            )

            result = await agent.process_request(delegation.task, agent_context)

            # Create delegation result
            delegation_result = DelegationResult(
                request_id=delegation.request_id,
                success=result.success,
                agent_id=delegation.target_agent,
                agent_role=delegation.agent_role,
                content=result.content,
                data=result.metadata,
                execution_time=time.time() - start_time,
                error=result.error
            )

            # Update delegation status
            delegation.status = "completed" if result.success else "failed"
            delegation.completed_at = time.time()

            return delegation_result

        except Exception as e:
            self.logger.error(f"Delegation execution failed: {e}")
            delegation.status = "failed"
            delegation.completed_at = time.time()

            return DelegationResult(
                request_id=delegation.request_id,
                success=False,
                agent_id=delegation.target_agent,
                agent_role=delegation.agent_role,
                content="",
                error=str(e)
            )
