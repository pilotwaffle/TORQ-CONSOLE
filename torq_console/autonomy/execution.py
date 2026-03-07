"""
Execution Engine - Execute approved plans and autonomous tasks.

The Execution Engine is responsible for:
- Executing approved preparation plans
- Running autonomous tasks with proper safeguards
- Tool policy enforcement and validation
- Rollback on failure
- Execution telemetry and metrics
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone

from pydantic import BaseModel, Field

from .models import (
    Monitor, TriggerEvent, AutonomousTask, ExecutionMode,
    PolicyDecision, ActionRisk, PolicyLevel, TaskState
)
from .state_store import StateStore
from .preparation import PreparationPlan, PreparationStep, PlanStatus


logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Constants
# ============================================================================

class ExecutionStatus(str, Enum):
    """Status of execution operations."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLED_BACK = "rolled_back"
    PARTIALLY_COMPLETED = "partially_completed"


class ToolPolicy(str, Enum):
    """Tool usage policies."""
    ALLOWED = "allowed"                      # Tool can be used freely
    ALLOWED_WITH_LOG = "allowed_with_log"    # Tool can be used, must log
    REQUIRE_APPROVAL = "require_approval"    # Tool requires approval per use
    DENIED = "denied"                        # Tool cannot be used
    READ_ONLY = "read_only"                  # Tool can only read, not write


class RollbackAction(str, Enum):
    """Types of rollback actions."""
    NONE = "none"                    # No rollback needed
    AUTOMATIC = "automatic"          # Automatic rollback on failure
    MANUAL = "manual"                # Manual rollback required
    NOT_SUPPORTED = "not_supported"  # Rollback not supported


# ============================================================================
# Models
# ============================================================================

class ToolPolicyRule(BaseModel):
    """Policy rule for a specific tool."""
    tool_name: str
    policy: ToolPolicy
    risk_level: ActionRisk = ActionRisk.LOW
    description: Optional[str] = None
    allowed_params: Optional[List[str]] = None  # Whitelist of allowed params
    denied_params: Optional[List[str]] = None   # Blacklist of denied params

    class Config:
        json_encoders = {
            float: lambda v: round(v, 3)
        }


class ExecutionStepResult(BaseModel):
    """Result of executing a single step."""
    step_id: str
    step_name: str
    status: ExecutionStatus
    started_at: float
    completed_at: Optional[float] = None
    duration_seconds: float = 0.0

    # Results
    success: bool = False
    output: Optional[str] = None
    error: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)

    # Rollback
    rollback_action: RollbackAction = RollbackAction.NONE
    rollback_data: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            float: lambda v: round(v, 3)
        }


class ExecutionResult(BaseModel):
    """Result of executing a plan or task."""
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    plan_id: Optional[str] = None
    task_id: Optional[str] = None

    # Overall status
    status: ExecutionStatus = ExecutionStatus.PENDING
    started_at: float = Field(default_factory=time.time)
    completed_at: Optional[float] = None
    duration_seconds: float = 0.0

    # Steps
    step_results: List[ExecutionStepResult] = Field(default_factory=list)

    # Final outcome
    success: bool = False
    output: Optional[str] = None
    error: Optional[str] = None

    # Resources used
    agent_ids: List[str] = Field(default_factory=list)
    tools_used: List[str] = Field(default_factory=list)

    # Rollback
    rolled_back: bool = False
    rollback_reason: Optional[str] = None

    # Metadata
    workspace_id: Optional[str] = None
    environment: Optional[str] = None
    executed_by: Optional[str] = None  # User or system that triggered execution

    class Config:
        json_encoders = {
            float: lambda v: round(v, 3)
        }

    def add_step_result(self, result: ExecutionStepResult) -> None:
        """Add a step result."""
        self.step_results.append(result)

    def get_failed_steps(self) -> List[ExecutionStepResult]:
        """Get all failed steps."""
        return [r for r in self.step_results if r.status == ExecutionStatus.FAILED]

    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage."""
        if not self.step_results:
            return 0.0
        completed = sum(1 for r in self.step_results if r.status != ExecutionStatus.PENDING)
        return (completed / len(self.step_results)) * 100


class ExecutionMetrics(BaseModel):
    """Execution metrics tracking."""
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    rolled_back_executions: int = 0

    total_steps_executed: int = 0
    total_duration_seconds: float = 0.0

    by_tool: Dict[str, int] = Field(default_factory=dict)
    by_agent: Dict[str, int] = Field(default_factory=dict)
    by_status: Dict[str, int] = Field(default_factory=dict)

    last_execution_time: Optional[float] = None

    class Config:
        json_encoders = {
            float: lambda v: round(v, 3)
        }


# ============================================================================
# Tool Policy Enforcer
# ============================================================================

class ToolPolicyEnforcer:
    """
    Enforces tool usage policies.

    Validates tool usage before execution to ensure
    only approved operations are performed.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._policies: Dict[str, ToolPolicyRule] = {}
        self._load_default_policies()

    def _load_default_policies(self):
        """Load default tool policies."""
        # Read-only tools (safe)
        read_only_tools = [
            "read_file", "list_files", "search", "grep",
            "get_status", "health_check", "fetch",
            "web_search", "api_get"
        ]

        for tool in read_only_tools:
            self._policies[tool] = ToolPolicyRule(
                tool_name=tool,
                policy=ToolPolicy.ALLOWED,
                risk_level=ActionRisk.LOW
            )

        # Write tools (require approval)
        write_tools = [
            "write_file", "update_file", "delete_file",
            "api_post", "api_put", "api_delete",
            "send_email", "post_message", "create_resource"
        ]

        for tool in write_tools:
            self._policies[tool] = ToolPolicyRule(
                tool_name=tool,
                policy=ToolPolicy.REQUIRE_APPROVAL,
                risk_level=ActionRisk.HIGH
            )

        # Destructive tools (denied in autonomous mode)
        destructive_tools = [
            "drop_database", "delete_table", "format_disk",
            "shutdown_service", "delete_user", "revoke_access"
        ]

        for tool in destructive_tools:
            self._policies[tool] = ToolPolicyRule(
                tool_name=tool,
                policy=ToolPolicy.DENIED,
                risk_level=ActionRisk.CRITICAL,
                description="Destructive tool - denied in autonomous mode"
            )

    def add_policy(self, policy: ToolPolicyRule) -> None:
        """Add or update a tool policy."""
        self._policies[policy.tool_name] = policy

    def get_policy(self, tool_name: str) -> Optional[ToolPolicyRule]:
        """Get policy for a specific tool."""
        return self._policies.get(tool_name)

    def can_use_tool(
        self,
        tool_name: str,
        execution_mode: ExecutionMode,
        params: Optional[Dict[str, Any]] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Check if a tool can be used.

        Returns:
            (allowed, reason)
        """
        policy = self.get_policy(tool_name)

        # No specific policy - allow with log
        if policy is None:
            return True, "No specific policy - allowing with log"

        # Check policy level
        if policy.policy == ToolPolicy.DENIED:
            return False, f"Tool {tool_name} is denied: {policy.description}"

        # OBSERVE mode - only allow read-only tools
        if execution_mode == ExecutionMode.OBSERVE:
            if policy.policy != ToolPolicy.ALLOWED:
                return False, f"OBSERVE mode: tool {tool_name} requires higher privileges"

        # PREPARE mode - require approval for write operations
        if execution_mode == ExecutionMode.PREPARE:
            if policy.policy == ToolPolicy.REQUIRE_APPROVAL:
                return False, f"PREPARE mode: tool {tool_name} requires explicit approval"

        # EXECUTE mode - still enforce DENIED policy
        if policy.policy == ToolPolicy.DENIED:
            return False, f"Tool {tool_name} is denied"

        # Check denied params
        if policy.denied_params and params:
            for denied in policy.denied_params:
                if denied in params:
                    return False, f"Parameter '{denied}' is not allowed for tool {tool_name}"

        return True, None

    def validate_tool_usage(
        self,
        tools: List[str],
        execution_mode: ExecutionMode,
        params_map: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> tuple[bool, List[str]]:
        """
        Validate multiple tools.

        Returns:
            (all_allowed, denial_reasons)
        """
        all_allowed = True
        reasons = []

        for tool in tools:
            params = params_map.get(tool) if params_map else None
            allowed, reason = self.can_use_tool(tool, execution_mode, params)

            if not allowed:
                all_allowed = False
                if reason:
                    reasons.append(reason)

        return all_allowed, reasons


# ============================================================================
# Execution Engine
# ============================================================================

class ExecutionEngine:
    """
    Engine for executing approved plans and autonomous tasks.

    This is the core of EXECUTE mode autonomy:
    - Executes approved preparation plans
    - Runs autonomous tasks with safeguards
    - Enforces tool policies
    - Handles rollbacks on failure
    - Tracks execution metrics
    """

    def __init__(
        self,
        state_store: Optional[StateStore] = None,
        policy_enforcer: Optional[ToolPolicyEnforcer] = None
    ):
        self.state_store = state_store
        self.policy_enforcer = policy_enforcer or ToolPolicyEnforcer()
        self.logger = logging.getLogger(__name__)

        # Execution storage
        self._executions: Dict[str, ExecutionResult] = {}
        self._executions_by_plan: Dict[str, str] = {}  # plan_id -> execution_id
        self._executions_by_task: Dict[str, str] = {}  # task_id -> execution_id

        # Metrics
        self._metrics = ExecutionMetrics()

        # Tool executors (simulated for now)
        self._tool_executors: Dict[str, Callable] = {}

        # Background processing
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None

    def set_tool_executor(self, tool_name: str, executor: Callable) -> None:
        """Set a custom tool executor."""
        self._tool_executors[tool_name] = executor

    async def start(self) -> None:
        """Start the execution engine."""
        if self._running:
            return

        self._running = True
        self.logger.info("Execution engine started")

    async def stop(self) -> None:
        """Stop the execution engine."""
        self._running = False

        if self._processor_task:
            self._processor_task.cancel()

            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Execution engine stopped")

    async def execute_plan(
        self,
        plan: PreparationPlan,
        executed_by: Optional[str] = None
    ) -> ExecutionResult:
        """
        Execute an approved preparation plan.

        Args:
            plan: The plan to execute
            executed_by: Who triggered the execution

        Returns:
            ExecutionResult with full execution details
        """
        self.logger.info(f"Executing plan: {plan.plan_id}")

        # Check plan is ready for execution
        if not plan.is_ready_for_execution:
            raise ValueError(
                f"Plan {plan.plan_id} is not ready for execution. "
                f"Status: {plan.status}, Expired: {plan.is_expired}"
            )

        # Create execution result
        result = ExecutionResult(
            plan_id=plan.plan_id,
            executed_by=executed_by or "system",
            workspace_id=plan.workspace_id,
            environment=plan.environment
        )

        result.status = ExecutionStatus.RUNNING
        result.started_at = time.time()

        # Store execution
        self._executions[result.execution_id] = result
        self._executions_by_plan[plan.plan_id] = result.execution_id

        try:
            # Validate tools before execution
            tools_to_use = [
                step.tool_name
                for step in plan.steps
                if step.tool_name
            ]

            all_allowed, reasons = self.policy_enforcer.validate_tool_usage(
                tools_to_use,
                ExecutionMode.EXECUTE
            )

            if not all_allowed:
                result.status = ExecutionStatus.FAILED
                result.error = f"Tool policy violations: {'; '.join(reasons)}"
                result.completed_at = time.time()
                result.duration_seconds = result.completed_at - result.started_at
                return result

            # Execute steps in dependency order
            completed_steps: Set[str] = set()

            for step in plan.steps:
                # Check if dependencies are met
                if step.depends_on:
                    if not all(dep in completed_steps for dep in step.depends_on):
                        self.logger.warning(f"Step {step.step_id} dependencies not met, skipping")
                        continue

                # Skip optional steps if previous failed
                if step.optional and result.get_failed_steps():
                    self.logger.info(f"Skipping optional step {step.step_id} due to failures")
                    continue

                # Execute the step
                step_result = await self._execute_step(step, ExecutionMode.EXECUTE)
                result.add_step_result(step_result)

                if step_result.status == ExecutionStatus.COMPLETED:
                    completed_steps.add(step.step_id)
                elif not step.optional:
                    # Critical step failed - stop execution
                    self.logger.error(f"Critical step {step.step_id} failed, stopping execution")

                    # Attempt rollback if configured
                    if step.rollback_action != RollbackAction.NONE:
                        await self._rollback_execution(result, plan)

                    break

            # Determine overall status
            if result.get_failed_steps():
                if completed_steps:
                    result.status = ExecutionStatus.PARTIALLY_COMPLETED
                else:
                    result.status = ExecutionStatus.FAILED
            else:
                result.status = ExecutionStatus.COMPLETED
                result.success = True

        except Exception as e:
            self.logger.error(f"Error executing plan {plan.plan_id}: {e}")
            result.status = ExecutionStatus.FAILED
            result.error = str(e)

        finally:
            result.completed_at = time.time()
            result.duration_seconds = result.completed_at - result.started_at

            # Update metrics
            self._update_metrics(result)

            # Persist result
            await self._save_execution_result(result)

        self.logger.info(
            f"Plan execution {result.execution_id} completed: "
            f"status={result.status.value}, duration={result.duration_seconds:.2f}s"
        )

        return result

    async def execute_task(
        self,
        task: AutonomousTask,
        execution_mode: ExecutionMode = ExecutionMode.EXECUTE
    ) -> ExecutionResult:
        """
        Execute an autonomous task.

        Args:
            task: The task to execute
            execution_mode: The execution mode to use

        Returns:
            ExecutionResult with full execution details
        """
        self.logger.info(f"Executing task: {task.task_id}")

        result = ExecutionResult(
            task_id=task.task_id,
            executed_by="system",
            workspace_id=task.workspace_id,
            environment=task.environment
        )

        result.status = ExecutionStatus.RUNNING
        result.started_at = time.time()

        # Store execution
        self._executions[result.execution_id] = result
        self._executions_by_task[task.task_id] = result.execution_id

        try:
            # Simulate task execution
            # In production, this would use the agent coordinator
            await asyncio.sleep(0.1)  # Simulate work

            result.status = ExecutionStatus.COMPLETED
            result.success = True
            result.output = f"Task {task.name} completed successfully"

            result.agent_ids = task.agents or []

        except Exception as e:
            self.logger.error(f"Error executing task {task.task_id}: {e}")
            result.status = ExecutionStatus.FAILED
            result.error = str(e)

        finally:
            result.completed_at = time.time()
            result.duration_seconds = result.completed_at - result.started_at

            # Update metrics
            self._update_metrics(result)

            # Persist result
            await self._save_execution_result(result)

        return result

    async def _execute_step(
        self,
        step: PreparationStep,
        execution_mode: ExecutionMode
    ) -> ExecutionStepResult:
        """Execute a single preparation step."""
        result = ExecutionStepResult(
            step_id=step.step_id,
            step_name=step.name,
            status=ExecutionStatus.RUNNING,
            started_at=time.time()
        )

        try:
            # Validate tool usage
            if step.tool_name:
                allowed, reason = self.policy_enforcer.can_use_tool(
                    step.tool_name,
                    execution_mode,
                    step.parameters
                )

                if not allowed:
                    result.status = ExecutionStatus.FAILED
                    result.error = f"Tool not allowed: {reason}"
                    result.completed_at = time.time()
                    result.duration_seconds = result.completed_at - result.started_at
                    return result

            # Execute the tool
            if step.tool_name and step.tool_name in self._tool_executors:
                # Custom executor
                executor = self._tool_executors[step.tool_name]
                output = await executor(step.parameters)
                result.output = str(output)
            else:
                # Simulated execution
                await asyncio.sleep(0.05)  # Simulate work

                if step.step_type == "investigation":
                    result.output = f"Investigation completed for {step.name}"
                elif step.step_type == "action":
                    result.output = f"Action completed: {step.name}"
                elif step.step_type == "verification":
                    result.output = f"Verification passed: {step.name}"
                else:
                    result.output = f"Step completed: {step.name}"

            result.status = ExecutionStatus.COMPLETED
            result.success = True

        except Exception as e:
            self.logger.error(f"Error executing step {step.step_id}: {e}")
            result.status = ExecutionStatus.FAILED
            result.error = str(e)

        finally:
            result.completed_at = time.time()
            result.duration_seconds = result.completed_at - result.started_at

        return result

    async def _rollback_execution(
        self,
        result: ExecutionResult,
        plan: PreparationPlan
    ) -> None:
        """Attempt to rollback a failed execution."""
        self.logger.info(f"Attempting rollback for execution {result.execution_id}")

        # In a real system, this would execute rollback actions
        # For now, just mark as rolled back
        result.rolled_back = True
        result.rollback_reason = "Automatic rollback due to step failure"
        result.status = ExecutionStatus.ROLLED_BACK

        self._metrics.rolled_back_executions += 1

    async def _save_execution_result(self, result: ExecutionResult) -> bool:
        """Save execution result to storage."""
        if self.state_store:
            try:
                from .models import TaskStateRecord, TaskState
                state = TaskState.SUCCEEDED if result.success else TaskState.FAILED
                record = TaskStateRecord(
                    task_id=f"exec_{result.execution_id}",
                    state=state,
                    timestamp=time.time(),
                    data={
                        "execution": result.model_dump(),
                        "type": "execution_result"
                    }
                )
                await self.state_store.save_task_state(record)
                return True
            except Exception as e:
                self.logger.error(f"Error saving execution result: {e}")
        return False

    def _update_metrics(self, result: ExecutionResult) -> None:
        """Update execution metrics."""
        self._metrics.total_executions += 1

        if result.status == ExecutionStatus.COMPLETED:
            self._metrics.successful_executions += 1
        elif result.status in [ExecutionStatus.FAILED, ExecutionStatus.ROLLED_BACK]:
            self._metrics.failed_executions += 1

        self._metrics.total_steps_executed += len(result.step_results)
        self._metrics.total_duration_seconds += result.duration_seconds

        for tool in result.tools_used:
            self._metrics.by_tool[tool] = self._metrics.by_tool.get(tool, 0) + 1

        for agent in result.agent_ids:
            self._metrics.by_agent[agent] = self._metrics.by_agent.get(agent, 0) + 1

        status_key = result.status.value
        self._metrics.by_status[status_key] = self._metrics.by_status.get(status_key, 0) + 1

        self._metrics.last_execution_time = time.time()

    def get_execution(self, execution_id: str) -> Optional[ExecutionResult]:
        """Get an execution result by ID."""
        return self._executions.get(execution_id)

    def get_execution_by_plan(self, plan_id: str) -> Optional[ExecutionResult]:
        """Get execution result for a plan."""
        execution_id = self._executions_by_plan.get(plan_id)
        if execution_id:
            return self.get_execution(execution_id)
        return None

    def get_execution_by_task(self, task_id: str) -> Optional[ExecutionResult]:
        """Get execution result for a task."""
        execution_id = self._executions_by_task.get(task_id)
        if execution_id:
            return self.get_execution(execution_id)
        return None

    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution."""
        result = self.get_execution(execution_id)
        if not result:
            return False

        if result.status != ExecutionStatus.RUNNING:
            return False

        result.status = ExecutionStatus.CANCELLED
        result.completed_at = time.time()
        result.duration_seconds = result.completed_at - result.started_at

        await self._save_execution_result(result)
        return True

    def get_metrics(self) -> ExecutionMetrics:
        """Get execution metrics."""
        return self._metrics


# Singleton instance
_execution_engine: Optional[ExecutionEngine] = None


def get_execution_engine(
    state_store: Optional[StateStore] = None
) -> ExecutionEngine:
    """Get the singleton execution engine instance."""
    global _execution_engine
    if _execution_engine is None:
        _execution_engine = ExecutionEngine(state_store=state_store)
    return _execution_engine
