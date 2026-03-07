"""
Preparation Engine - Plan and recommendation generation for Prepare Mode.

The Preparation Engine is responsible for:
- Converting trigger events into actionable preparation plans
- Generating recommendations without executing actions
- Running dry-run simulations
- Managing plan review workflow
- Storing and retrieving preparation plans
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone

from pydantic import BaseModel, Field

from .models import (
    Monitor, TriggerEvent, AutonomousTask, ExecutionMode,
    PolicyDecision, ActionRisk, PolicyLevel
)
from .state_store import StateStore


logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Constants
# ============================================================================

class PlanType(str, Enum):
    """Types of preparation plans."""
    INVESTIGATION = "investigation"       # Gather more information
    REMEDIATION = "remediation"           # Fix identified issue
    OPTIMIZATION = "optimization"         # Improve performance/cost
    SECURITY = "security"                 # Address security concern
    COMPLIANCE = "compliance"             # Meet compliance requirement
    SCALING = "scaling"                   # Scale resources up/down
    NOTIFICATION = "notification"         # Alert stakeholders


class PlanStatus(str, Enum):
    """Status of preparation plans."""
    DRAFT = "draft"                       # Initial plan, not yet reviewed
    PENDING_REVIEW = "pending_review"     # Awaiting review
    UNDER_REVIEW = "under_review"         # Currently being reviewed
    APPROVED = "approved"                 # Plan approved for execution
    REJECTED = "rejected"                 # Plan rejected
    EXPIRED = "expired"                   # Plan expired (not executed in time)
    EXECUTED = "executed"                 # Plan was executed
    SUPERSEDED = "superseded"             # Replaced by newer plan


class SimulationResult(str, Enum):
    """Results of dry-run simulations."""
    SUCCESS = "success"                   # Simulation completed successfully
    WARNING = "warning"                   # Simulation completed with warnings
    FAILURE = "failure"                   # Simulation failed
    TIMEOUT = "timeout"                   # Simulation timed out
    SKIPPED = "skipped"                   # Simulation not applicable


# ============================================================================
# Models
# ============================================================================

class PreparationStep(BaseModel):
    """A single step in a preparation plan."""
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    step_type: str  # investigation, action, verification, notification

    # Execution details
    agent_id: Optional[str] = None  # Which agent should execute
    tool_name: Optional[str] = None  # Which tool to use
    parameters: Dict[str, Any] = Field(default_factory=dict)

    # Estimated impact
    estimated_duration_seconds: Optional[int] = None
    estimated_cost: Optional[float] = None  # In credits or actual cost
    risk_level: ActionRisk = ActionRisk.LOW

    # Dependencies
    depends_on: List[str] = Field(default_factory=list)  # step_ids
    optional: bool = False

    # Status
    status: str = "pending"  # pending, completed, skipped, failed


class DryRunResult(BaseModel):
    """Results of a dry-run simulation."""
    result_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    plan_id: str
    simulated_at: float = Field(default_factory=time.time)

    # Overall result
    result: SimulationResult
    confidence: float = 0.0  # 0.0 to 1.0

    # Predicted outcomes
    predicted_duration_seconds: Optional[int] = None
    predicted_cost: Optional[float] = None
    predicted_side_effects: List[str] = Field(default_factory=list)

    # Step-by-step results
    step_results: List[Dict[str, Any]] = Field(default_factory=list)

    # Warnings and errors
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

    # Recommendations
    recommendations: List[str] = Field(default_factory=list)

    class Config:
        json_encoders = {
            float: lambda v: round(v, 3)
        }


class PreparationPlan(BaseModel):
    """
    A preparation plan for handling a trigger event.

    Plans are created in PREPARE mode and must be reviewed
    before any actions are taken.
    """
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    plan_type: PlanType
    name: str
    description: str

    # Origin
    trigger_event_id: Optional[str] = None
    monitor_id: Optional[str] = None
    task_id: Optional[str] = None

    # Plan content
    steps: List[PreparationStep] = Field(default_factory=list)

    # Expected outcomes
    expected_outcome: str
    success_criteria: List[str] = Field(default_factory=list)

    # Risk assessment
    risk_level: ActionRisk = ActionRisk.LOW
    estimated_duration_seconds: Optional[int] = None
    estimated_cost: Optional[float] = None

    # Status
    status: PlanStatus = PlanStatus.DRAFT
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)

    # Review
    created_by: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[float] = None
    review_comments: Optional[str] = None

    # Execution
    approved_by: Optional[str] = None
    approved_at: Optional[float] = None
    executed_at: Optional[float] = None

    # Dry run results
    dry_run_result: Optional[DryRunResult] = None

    # Expiration
    expires_at: Optional[float] = None  # Plan expires if not executed

    # Workspace/tenant
    workspace_id: Optional[str] = None
    environment: Optional[str] = None

    class Config:
        json_encoders = {
            float: lambda v: round(v, 3)
        }

    def add_step(self, step: PreparationStep) -> None:
        """Add a step to the plan."""
        self.steps.append(step)
        self.updated_at = time.time()

    def get_step_by_id(self, step_id: str) -> Optional[PreparationStep]:
        """Get a step by ID."""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None

    def get_ready_steps(self) -> List[PreparationStep]:
        """Get steps whose dependencies are satisfied."""
        ready = []
        completed_step_ids = {s.step_id for s in self.steps if s.status == "completed"}

        for step in self.steps:
            if step.status != "pending":
                continue

            # Check if all dependencies are met
            deps_met = all(dep in completed_step_ids for dep in step.depends_on)
            if deps_met:
                ready.append(step)

        return ready

    @property
    def is_ready_for_execution(self) -> bool:
        """Check if plan is ready for execution."""
        return (
            self.status == PlanStatus.APPROVED and
            (self.expires_at is None or self.expires_at > time.time())
        )

    @property
    def is_expired(self) -> bool:
        """Check if plan has expired."""
        return self.expires_at is not None and self.expires_at <= time.time()


class Recommendation(BaseModel):
    """
    A recommendation generated from analysis.

    Recommendations are lighter-weight than full plans and
    can be generated automatically.
    """
    recommendation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str

    # Classification
    category: str  # performance, security, cost, reliability, etc.
    priority: str  # low, medium, high, critical
    impact: str  # estimated impact

    # Source
    source_type: str  # monitor, analysis, user, etc.
    source_id: Optional[str] = None

    # Content
    recommendation: str  # What should be done
    rationale: str  # Why this is recommended
    evidence: List[str] = Field(default_factory=list)  # Supporting evidence

    # Actionability
    estimated_effort: Optional[str] = None  # "5 minutes", "1 hour", etc.
    estimated_cost: Optional[float] = None

    # Status
    status: str = "pending"  # pending, acknowledged, dismissed, implemented
    created_at: float = Field(default_factory=time.time)
    acknowledged_at: Optional[float] = None
    dismissed_at: Optional[float] = None

    # Workspace
    workspace_id: Optional[str] = None
    environment: Optional[str] = None

    class Config:
        json_encoders = {
            float: lambda v: round(v, 3)
        }


# ============================================================================
# Preparation Engine
# ============================================================================

class PreparationEngine:
    """
    Engine for creating and managing preparation plans.

    This is the core of PREPARE mode autonomy:
    - Converts triggers into actionable plans
    - Generates recommendations
    - Runs dry-run simulations
    - Manages plan review workflow
    """

    def __init__(
        self,
        state_store: Optional[StateStore] = None,
        dry_run_enabled: bool = True
    ):
        self.state_store = state_store
        self.dry_run_enabled = dry_run_enabled
        self.logger = logging.getLogger(__name__)

        # Plan storage (in-memory + persisted)
        self._plans: Dict[str, PreparationPlan] = {}
        self._recommendations: Dict[str, Recommendation] = {}

        # Dry-run simulator
        self._simulator: Optional[Callable] = None

        # Background expiration checker
        self._running = False
        self._expiration_task: Optional[asyncio.Task] = None

    def set_dry_run_simulator(self, simulator: Callable):
        """Set the dry-run simulation function."""
        self._simulator = simulator

    async def start(self):
        """Start the preparation engine."""
        if self._running:
            return

        self._running = True
        self._expiration_task = asyncio.create_task(self._check_expirations())
        self.logger.info("Preparation engine started")

    async def stop(self):
        """Stop the preparation engine."""
        self._running = False

        if self._expiration_task:
            self._expiration_task.cancel()

        try:
            await self._expiration_task
        except asyncio.CancelledError:
            pass

        self.logger.info("Preparation engine stopped")

    async def create_plan_from_trigger(
        self,
        event: TriggerEvent,
        monitor: Monitor,
        policy_decision: Optional[PolicyDecision] = None
    ) -> PreparationPlan:
        """
        Create a preparation plan from a trigger event.

        Args:
            event: The trigger event
            monitor: The monitor that generated the event
            policy_decision: Optional policy decision

        Returns:
            Created PreparationPlan
        """
        self.logger.info(f"Creating preparation plan for event: {event.event_id}")

        # Determine plan type based on monitor
        plan_type = self._determine_plan_type(event, monitor)

        # Generate plan content
        plan = PreparationPlan(
            plan_type=plan_type,
            name=f"{plan_type.value.title()} Plan for {monitor.name}",
            description=f"Preparation plan for {event.event_type.value} on {monitor.target}",
            trigger_event_id=event.event_id,
            monitor_id=monitor.monitor_id,
            expected_outcome=f"Address {event.event_type.value} condition",
            workspace_id=event.workspace_id or monitor.workspace_id,
            environment=event.environment or monitor.environment,
            risk_level=self._assess_plan_risk(event, monitor)
        )

        # Generate steps based on trigger type
        steps = await self._generate_steps(event, monitor, policy_decision)
        plan.steps = steps

        # Set expiration (24 hours default)
        plan.expires_at = time.time() + (24 * 3600)

        # Store the plan
        await self.save_plan(plan)
        self._plans[plan.plan_id] = plan

        # Run dry-run simulation if enabled
        if self.dry_run_enabled:
            plan.dry_run_result = await self.run_dry_run(plan)

        self.logger.info(f"Created preparation plan: {plan.plan_id}")
        return plan

    def _determine_plan_type(
        self,
        event: TriggerEvent,
        monitor: Monitor
    ) -> PlanType:
        """Determine the plan type from event and monitor."""
        monitor_type_map = {
            "health_check": PlanType.INVESTIGATION,
            "threshold": PlanType.REMEDIATION,
            "schedule": PlanType.OPTIMIZATION,
            "status_change": PlanType.INVESTIGATION,
            "absence": PlanType.NOTIFICATION,
            "topic": PlanType.NOTIFICATION,
            "workflow_failure": PlanType.REMEDIATION,
            "policy_violation": PlanType.COMPLIANCE
        }

        return monitor_type_map.get(
            monitor.type.value,
            PlanType.INVESTIGATION
        )

    def _assess_plan_risk(
        self,
        event: TriggerEvent,
        monitor: Monitor
    ) -> ActionRisk:
        """Assess the risk level of a plan."""
        # Start with severity from event
        severity_map = {
            "low": ActionRisk.LOW,
            "medium": ActionRisk.MEDIUM,
            "high": ActionRisk.HIGH,
            "critical": ActionRisk.CRITICAL
        }

        base_risk = severity_map.get(event.severity, ActionRisk.LOW)

        # Adjust based on execution mode
        if monitor.execution_mode == ExecutionMode.OBSERVE:
            return ActionRisk.LOW
        elif monitor.execution_mode == ExecutionMode.PREPARE:
            return min(base_risk, ActionRisk.MEDIUM)
        else:  # EXECUTE
            return base_risk

    async def _generate_steps(
        self,
        event: TriggerEvent,
        monitor: Monitor,
        policy_decision: Optional[PolicyDecision]
    ) -> List[PreparationStep]:
        """Generate preparation steps based on trigger event."""
        steps = []

        # Common first step: investigate
        steps.append(PreparationStep(
            name="Investigate Trigger",
            description=f"Investigate the {event.event_type.value} trigger on {monitor.target}",
            step_type="investigation",
            agent_id="research_agent",
            parameters={
                "target": monitor.target,
                "event_data": event.model_dump()
            },
            estimated_duration_seconds=300,
            risk_level=ActionRisk.LOW
        ))

        # Add steps based on event type
        if event.event_type.value == "threshold_crossed":
            steps.extend(await self._threshold_steps(event, monitor))
        elif event.event_type.value == "workflow_failed":
            steps.extend(await self._workflow_failure_steps(event, monitor))
        elif event.event_type.value == "status_changed":
            steps.extend(await self._status_change_steps(event, monitor))
        elif event.event_type.value == "topic_matched":
            steps.extend(await self._topic_steps(event, monitor))

        # Common final step: verification
        steps.append(PreparationStep(
            name="Verify Resolution",
            description="Verify that the issue has been resolved",
            step_type="verification",
            agent_id="research_agent",
            parameters={"target": monitor.target},
            depends_on=[steps[-2].step_id] if len(steps) >= 2 else [],
            estimated_duration_seconds=120,
            risk_level=ActionRisk.LOW
        ))

        return steps

    async def _threshold_steps(
        self,
        event: TriggerEvent,
        monitor: Monitor
    ) -> List[PreparationStep]:
        """Generate steps for threshold triggers."""
        steps = []

        payload = event.payload or {}
        field_name = payload.get("field", "value")
        current_value = payload.get("current", "unknown")
        threshold = payload.get("threshold", "unknown")

        # Analysis step
        steps.append(PreparationStep(
            name="Analyze Threshold Crossing",
            description=f"Analyze why {field_name} crossed threshold {threshold}",
            step_type="investigation",
            agent_id="research_agent",
            parameters={
                "metric": field_name,
                "current_value": current_value,
                "threshold": threshold
            },
            depends_on=[],
            estimated_duration_seconds=300,
            risk_level=ActionRisk.LOW
        ))

        # Remediation step (if in PREPARE mode, this is just planning)
        steps.append(PreparationStep(
            name="Prepare Remediation Plan",
            description=f"Plan actions to bring {field_name} back within threshold",
            step_type="action",
            agent_id="workflow_agent",
            parameters={
                "metric": field_name,
                "target_value": threshold,
                "action": "prepare_only"
            },
            depends_on=[steps[-1].step_id],
            estimated_duration_seconds=600,
            risk_level=ActionRisk.MEDIUM
        ))

        return steps

    async def _workflow_failure_steps(
        self,
        event: TriggerEvent,
        monitor: Monitor
    ) -> List[PreparationStep]:
        """Generate steps for workflow failure triggers."""
        steps = []

        steps.append(PreparationStep(
            name="Analyze Failure",
            description="Analyze the workflow execution failure",
            step_type="investigation",
            agent_id="research_agent",
            parameters={
                "workflow_id": monitor.target,
                "event_data": event.model_dump()
            },
            depends_on=[],
            estimated_duration_seconds=300,
            risk_level=ActionRisk.LOW
        ))

        steps.append(PreparationStep(
            name="Prepare Fix",
            description="Prepare a fix for the workflow",
            step_type="action",
            agent_id="workflow_agent",
            parameters={
                "action": "prepare_fix"
            },
            depends_on=[steps[-1].step_id],
            estimated_duration_seconds=600,
            risk_level=ActionRisk.MEDIUM
        ))

        return steps

    async def _status_change_steps(
        self,
        event: TriggerEvent,
        monitor: Monitor
    ) -> List[PreparationStep]:
        """Generate steps for status change triggers."""
        steps = []

        payload = event.payload or {}
        from_status = payload.get("from", "unknown")
        to_status = payload.get("to", "unknown")

        steps.append(PreparationStep(
            name="Investigate Status Change",
            description=f"Investigate status change from {from_status} to {to_status}",
            step_type="investigation",
            agent_id="research_agent",
            parameters={
                "from_status": from_status,
                "to_status": to_status
            },
            depends_on=[],
            estimated_duration_seconds=300,
            risk_level=ActionRisk.LOW
        ))

        return steps

    async def _topic_steps(
        self,
        event: TriggerEvent,
        monitor: Monitor
    ) -> List[PreparationStep]:
        """Generate steps for topic match triggers."""
        steps = []

        payload = event.payload or {}
        text = payload.get("text", "")[:200]
        keywords = payload.get("matched_keywords", [])

        steps.append(PreparationStep(
            name="Analyze Topic Match",
            description=f"Analyze content matching keywords: {', '.join(keywords)}",
            step_type="investigation",
            agent_id="research_agent",
            parameters={
                "text": text,
                "keywords": keywords
            },
            depends_on=[],
            estimated_duration_seconds=180,
            risk_level=ActionRisk.LOW
        ))

        return steps

    async def run_dry_run(
        self,
        plan: PreparationPlan
    ) -> Optional[DryRunResult]:
        """
        Run a dry-run simulation of the plan.

        Args:
            plan: The plan to simulate

        Returns:
            DryRunResult with simulation outcomes
        """
        self.logger.info(f"Running dry-run for plan: {plan.plan_id}")

        if not self._simulator:
            # Default simple simulation
            return self._default_simulation(plan)

        try:
            result = await self._simulator(plan)
            return result
        except Exception as e:
            self.logger.error(f"Dry-run simulation failed: {e}")
            return DryRunResult(
                plan_id=plan.plan_id,
                result=SimulationResult.FAILURE,
                confidence=0.0,
                errors=[str(e)]
            )

    def _default_simulation(self, plan: PreparationPlan) -> DryRunResult:
        """Default simple simulation when no simulator is set."""
        total_duration = sum(
            s.estimated_duration_seconds or 0
            for s in plan.steps
        )

        return DryRunResult(
            plan_id=plan.plan_id,
            result=SimulationResult.SUCCESS,
            confidence=0.8,
            predicted_duration_seconds=total_duration,
            step_results=[
                {
                    "step_id": s.step_id,
                    "step_name": s.name,
                    "result": "success",
                    "duration": s.estimated_duration_seconds
                }
                for s in plan.steps
            ],
            recommendations=[
                "Review plan steps before execution",
                "Ensure dependencies are correctly ordered"
            ]
        )

    async def save_plan(self, plan: PreparationPlan) -> bool:
        """Save a plan to storage."""
        if self.state_store:
            try:
                # Use the task storage for plans (reuse structure)
                from .models import TaskStateRecord, TaskState
                record = TaskStateRecord(
                    task_id=f"plan_{plan.plan_id}",
                    state=TaskState.CREATED,  # Use a valid TaskState enum
                    timestamp=time.time(),
                    data={
                        "plan": plan.model_dump(),
                        "plan_type": "preparation"
                    }
                )
                await self.state_store.save_task_state(record)
                return True
            except Exception as e:
                self.logger.error(f"Error saving plan: {e}")
        return False

    async def load_plan(self, plan_id: str) -> Optional[PreparationPlan]:
        """Load a plan from storage."""
        # Check cache first
        if plan_id in self._plans:
            return self._plans[plan_id]

        if self.state_store:
            try:
                from .models import TaskStateRecord
                # Load from task storage
                tasks = await self.state_store.list_tasks(state="plan_saved")
                for task in tasks:
                    if task.task_id == f"plan_{plan_id}":
                        plan_data = task.data.get("plan")
                        if plan_data:
                            plan = PreparationPlan(**plan_data)
                            self._plans[plan_id] = plan
                            return plan
            except Exception as e:
                self.logger.error(f"Error loading plan: {e}")

        return None

    async def submit_for_review(self, plan_id: str) -> bool:
        """Submit a plan for review."""
        plan = await self.load_plan(plan_id)
        if not plan:
            return False

        plan.status = PlanStatus.PENDING_REVIEW
        plan.updated_at = time.time()
        await self.save_plan(plan)
        return True

    async def review_plan(
        self,
        plan_id: str,
        reviewer: str,
        approved: bool,
        comments: Optional[str] = None
    ) -> bool:
        """
        Review and approve/reject a plan.

        Args:
            plan_id: Plan to review
            reviewer: Who is reviewing
            approved: True to approve, False to reject
            comments: Optional review comments

        Returns:
            True if successful
        """
        plan = await self.load_plan(plan_id)
        if not plan:
            return False

        plan.reviewed_by = reviewer
        plan.reviewed_at = time.time()
        plan.review_comments = comments

        if approved:
            plan.status = PlanStatus.APPROVED
            plan.approved_by = reviewer
            plan.approved_at = time.time()
        else:
            plan.status = PlanStatus.REJECTED

        plan.updated_at = time.time()
        await self.save_plan(plan)

        self.logger.info(
            f"Plan {plan_id} {'approved' if approved else 'rejected'} "
            f"by {reviewer}"
        )
        return True

    async def list_plans(
        self,
        status: Optional[PlanStatus] = None,
        workspace_id: Optional[str] = None,
        limit: int = 100
    ) -> List[PreparationPlan]:
        """List plans with optional filtering."""
        plans = []

        # Include cached plans first
        for plan in self._plans.values():
            # Apply filters
            if status and plan.status != status:
                continue
            if workspace_id and plan.workspace_id != workspace_id:
                continue

            plans.append(plan)

        # Also get plans from storage if available
        if self.state_store:
            try:
                from .models import TaskState
                tasks = await self.state_store.list_tasks(
                    state=None,  # Get all
                    workspace_id=workspace_id,
                    limit=limit * 2  # Get more, then filter
                )

                for task in tasks:
                    if task.task_id.startswith("plan_"):
                        # Skip if already in cache
                        plan_id = task.task_id.replace("plan_", "")
                        if plan_id in self._plans:
                            continue

                        plan_data = task.data.get("plan")
                        if plan_data:
                            plan = PreparationPlan(**plan_data)

                            # Apply filters
                            if status and plan.status != status:
                                continue

                            plans.append(plan)

            except Exception as e:
                self.logger.error(f"Error listing plans: {e}")

        # Sort by created_at (newest first)
        plans.sort(key=lambda p: p.created_at, reverse=True)
        return plans[:limit]

    async def _check_expirations(self):
        """Background task to check for expired plans."""
        while self._running:
            try:
                plans = await self.list_plans(status=PlanStatus.APPROVED)

                for plan in plans:
                    if plan.is_expired:
                        plan.status = PlanStatus.EXPIRED
                        plan.updated_at = time.time()
                        await self.save_plan(plan)
                        self.logger.info(f"Plan {plan.plan_id} expired")

                await asyncio.sleep(60)  # Check every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error checking expirations: {e}")
                await asyncio.sleep(60)

    # ========================================================================
    # Recommendations
    # ========================================================================

    async def create_recommendation(
        self,
        title: str,
        description: str,
        category: str,
        recommendation: str,
        rationale: str,
        priority: str = "medium",
        source_type: str = "analysis",
        source_id: Optional[str] = None,
        evidence: Optional[List[str]] = None,
        estimated_effort: Optional[str] = None,
        workspace_id: Optional[str] = None
    ) -> Recommendation:
        """Create a new recommendation."""
        rec = Recommendation(
            title=title,
            description=description,
            category=category,
            priority=priority,
            impact=priority,  # Use priority as impact default
            source_type=source_type,
            source_id=source_id,
            recommendation=recommendation,
            rationale=rationale,
            evidence=evidence or [],
            estimated_effort=estimated_effort,
            workspace_id=workspace_id
        )

        self._recommendations[rec.recommendation_id] = rec

        if self.state_store:
            try:
                from .models import TaskStateRecord, TaskState
                record = TaskStateRecord(
                    task_id=f"rec_{rec.recommendation_id}",
                    state=TaskState.CREATED,  # Use a valid TaskState enum
                    timestamp=time.time(),
                    data={"recommendation": rec.model_dump()}
                )
                await self.state_store.save_task_state(record)
            except Exception as e:
                self.logger.error(f"Error saving recommendation: {e}")

        return rec

    async def list_recommendations(
        self,
        status: Optional[str] = None,
        category: Optional[str] = None,
        workspace_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Recommendation]:
        """List recommendations with optional filtering."""
        recs = list(self._recommendations.values())

        # Apply filters
        if status:
            recs = [r for r in recs if r.status == status]
        if category:
            recs = [r for r in recs if r.category == category]
        if workspace_id:
            recs = [r for r in recs if r.workspace_id == workspace_id]

        # Sort by created_at
        recs.sort(key=lambda r: r.created_at, reverse=True)
        return recs[:limit]

    async def acknowledge_recommendation(
        self,
        recommendation_id: str
    ) -> bool:
        """Acknowledge a recommendation."""
        rec = self._recommendations.get(recommendation_id)
        if not rec:
            return False

        rec.status = "acknowledged"
        rec.acknowledged_at = time.time()
        return True

    async def dismiss_recommendation(
        self,
        recommendation_id: str
    ) -> bool:
        """Dismiss a recommendation."""
        rec = self._recommendations.get(recommendation_id)
        if not rec:
            return False

        rec.status = "dismissed"
        rec.dismissed_at = time.time()
        return True

    def get_metrics(self) -> Dict[str, Any]:
        """Get preparation engine metrics."""
        return {
            "total_plans": len(self._plans),
            "plans_by_status": {
                status.value: sum(1 for p in self._plans.values() if p.status == status)
                for status in PlanStatus
            },
            "total_recommendations": len(self._recommendations),
            "recommendations_by_status": {},
            "dry_run_enabled": self.dry_run_enabled,
            "is_running": self._running
        }


# Singleton instance
_preparation_engine: Optional[PreparationEngine] = None


def get_preparation_engine(
    state_store: Optional[StateStore] = None
) -> PreparationEngine:
    """Get the singleton preparation engine instance."""
    global _preparation_engine
    if _preparation_engine is None:
        _preparation_engine = PreparationEngine(state_store=state_store)
    return _preparation_engine
