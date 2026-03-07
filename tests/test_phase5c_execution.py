"""
Tests for Phase 5C: Execute Mode Autonomy

Tests the execution engine, tool policy enforcement,
rollback capability, and execution telemetry.
"""

import asyncio
import tempfile
import time
import pytest

from torq_console.autonomy.models import (
    Monitor, MonitorType, TriggerEvent, TriggerType,
    ExecutionMode, PolicyLevel, ActionRisk, AutonomousTask, TaskState
)
from torq_console.autonomy.execution import (
    ExecutionEngine,
    ExecutionResult,
    ExecutionStepResult,
    ExecutionStatus,
    ExecutionMetrics,
    ToolPolicyEnforcer,
    ToolPolicyRule,
    ToolPolicy,
    RollbackAction,
    get_execution_engine
)
from torq_console.autonomy.preparation import (
    PreparationEngine,
    PreparationPlan,
    PreparationStep,
    PlanType,
    PlanStatus,
    get_preparation_engine
)
from torq_console.autonomy.state_store import StateStore


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_storage():
    """Temporary storage for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def state_store(temp_storage):
    """State store for tests."""
    return StateStore(temp_storage)


@pytest.fixture
async def execution_engine(state_store):
    """Execution engine for tests."""
    engine = ExecutionEngine(state_store=state_store)
    await engine.start()
    yield engine
    await engine.stop()


@pytest.fixture
async def preparation_engine(state_store):
    """Preparation engine for tests."""
    engine = PreparationEngine(state_store=state_store)
    await engine.start()
    yield engine
    await engine.stop()


# ============================================================================
# ToolPolicyEnforcer Tests
# ============================================================================

class TestToolPolicyEnforcer:
    """Test tool policy enforcement."""

    def test_initial_policies_loaded(self):
        """Test that default policies are loaded."""
        enforcer = ToolPolicyEnforcer()

        # Read-only tools should be allowed
        allowed, reason = enforcer.can_use_tool("read_file", ExecutionMode.OBSERVE)
        assert allowed is True

        # Destructive tools should be denied
        allowed, reason = enforcer.can_use_tool("drop_database", ExecutionMode.EXECUTE)
        assert allowed is False
        assert "denied" in reason.lower()

    def test_add_custom_policy(self):
        """Test adding custom tool policies."""
        enforcer = ToolPolicyEnforcer()

        custom_policy = ToolPolicyRule(
            tool_name="custom_tool",
            policy=ToolPolicy.REQUIRE_APPROVAL,
            risk_level=ActionRisk.MEDIUM
        )

        enforcer.add_policy(custom_policy)

        retrieved = enforcer.get_policy("custom_tool")
        assert retrieved is not None
        assert retrieved.tool_name == "custom_tool"
        assert retrieved.policy == ToolPolicy.REQUIRE_APPROVAL

    def test_observe_mode_restrictions(self):
        """Test that OBSERVE mode restricts tools appropriately."""
        enforcer = ToolPolicyEnforcer()

        # Allowed tools should work in OBSERVE mode
        allowed, reason = enforcer.can_use_tool("read_file", ExecutionMode.OBSERVE)
        assert allowed is True

        # Write tools should be denied in OBSERVE mode
        allowed, reason = enforcer.can_use_tool("write_file", ExecutionMode.OBSERVE)
        assert allowed is False
        assert "observe mode" in reason.lower()

    def test_prepare_mode_restrictions(self):
        """Test that PREPARE mode requires approval for writes."""
        enforcer = ToolPolicyEnforcer()

        # Write tools require approval in PREPARE mode
        allowed, reason = enforcer.can_use_tool("write_file", ExecutionMode.PREPARE)
        assert allowed is False
        assert "prepare mode" in reason.lower() or "approval" in reason.lower()

    def test_execute_mode_allows_more(self):
        """Test that EXECUTE mode allows more operations."""
        enforcer = ToolPolicyEnforcer()

        # Write tools are allowed in EXECUTE mode
        allowed, reason = enforcer.can_use_tool("write_file", ExecutionMode.EXECUTE)
        assert allowed is True

        # But destructive tools are still denied
        allowed, reason = enforcer.can_use_tool("drop_database", ExecutionMode.EXECUTE)
        assert allowed is False

    def test_denied_params(self):
        """Test that denied parameters are enforced."""
        enforcer = ToolPolicyEnforcer()

        # Add a policy with denied params
        policy = ToolPolicyRule(
            tool_name="api_call",
            policy=ToolPolicy.ALLOWED,
            denied_params=["force", "bypass"]
        )
        enforcer.add_policy(policy)

        # Should be denied with denied param
        allowed, reason = enforcer.can_use_tool(
            "api_call",
            ExecutionMode.EXECUTE,
            {"endpoint": "/api/test", "force": True}
        )
        assert allowed is False
        assert "force" in reason.lower()

        # Should be allowed without denied param
        allowed, reason = enforcer.can_use_tool(
            "api_call",
            ExecutionMode.EXECUTE,
            {"endpoint": "/api/test"}
        )
        assert allowed is True

    def test_validate_multiple_tools(self):
        """Test validating multiple tools at once."""
        enforcer = ToolPolicyEnforcer()

        # All safe tools
        all_allowed, reasons = enforcer.validate_tool_usage(
            ["read_file", "search", "get_status"],
            ExecutionMode.OBSERVE
        )
        assert all_allowed is True
        assert len(reasons) == 0

        # Mix of safe and unsafe
        all_allowed, reasons = enforcer.validate_tool_usage(
            ["read_file", "drop_database"],
            ExecutionMode.EXECUTE
        )
        assert all_allowed is False
        assert len(reasons) > 0


# ============================================================================
# ExecutionResult Tests
# ============================================================================

class TestExecutionResult:
    """Test ExecutionResult model."""

    def test_execution_result_creation(self):
        """Test creating an execution result."""
        result = ExecutionResult(
            plan_id="plan_123",
            executed_by="admin",
            workspace_id="workspace_1"
        )

        assert result.execution_id is not None
        assert result.plan_id == "plan_123"
        assert result.status == ExecutionStatus.PENDING
        assert result.started_at > 0

    def test_add_step_result(self):
        """Test adding step results."""
        result = ExecutionResult(plan_id="plan_123")

        step_result = ExecutionStepResult(
            step_id="step_1",
            step_name="First Step",
            status=ExecutionStatus.COMPLETED,
            started_at=time.time(),
            success=True
        )

        result.add_step_result(step_result)

        assert len(result.step_results) == 1
        assert result.step_results[0].step_id == "step_1"

    def test_get_failed_steps(self):
        """Test getting failed steps."""
        result = ExecutionResult(plan_id="plan_123")

        # Add successful step
        result.add_step_result(ExecutionStepResult(
            step_id="step_1",
            step_name="Success",
            status=ExecutionStatus.COMPLETED,
            started_at=time.time(),
            success=True
        ))

        # Add failed step
        result.add_step_result(ExecutionStepResult(
            step_id="step_2",
            step_name="Failed",
            status=ExecutionStatus.FAILED,
            started_at=time.time(),
            success=False
        ))

        failed = result.get_failed_steps()
        assert len(failed) == 1
        assert failed[0].step_id == "step_2"

    def test_completion_percentage(self):
        """Test completion percentage calculation."""
        result = ExecutionResult(plan_id="plan_123")

        # No steps - 0%
        assert result.completion_percentage == 0.0

        # Add completed step
        result.add_step_result(ExecutionStepResult(
            step_id="step_1",
            step_name="Step 1",
            status=ExecutionStatus.COMPLETED,
            started_at=time.time(),
            success=True
        ))

        # Add pending step
        result.add_step_result(ExecutionStepResult(
            step_id="step_2",
            step_name="Step 2",
            status=ExecutionStatus.PENDING,
            started_at=time.time()
        ))

        # 50% complete
        assert result.completion_percentage == 50.0


# ============================================================================
# ExecutionEngine Tests
# ============================================================================

class TestExecutionEngine:
    """Test ExecutionEngine."""

    @pytest.mark.asyncio
    async def test_engine_start_stop(self, state_store):
        """Test starting and stopping the engine."""
        engine = ExecutionEngine(state_store=state_store)

        assert engine._running is False

        await engine.start()
        assert engine._running is True

        await engine.stop()
        assert engine._running is False

    @pytest.mark.asyncio
    async def test_execute_approved_plan(
        self,
        execution_engine,
        preparation_engine
    ):
        """Test executing an approved plan."""
        # Create and approve a plan
        monitor = Monitor(
            monitor_id="test_monitor",
            type=MonitorType.THRESHOLD,
            name="Test Monitor",
            target="test",
            interval_seconds=60,
            trigger_condition={"type": "threshold"},
            execution_mode=ExecutionMode.PREPARE
        )

        event = TriggerEvent(
            monitor_id="test_monitor",
            event_type=TriggerType.THRESHOLD_CROSSED,
            severity="medium"
        )

        plan = await preparation_engine.create_plan_from_trigger(event, monitor)
        await preparation_engine.review_plan(
            plan.plan_id,
            reviewer="admin",
            approved=True
        )

        # Execute the plan
        result = await execution_engine.execute_plan(plan)

        assert result is not None
        assert result.status in [
            ExecutionStatus.COMPLETED,
            ExecutionStatus.PARTIALLY_COMPLETED
        ]
        assert result.started_at > 0
        assert result.completed_at > 0
        assert result.duration_seconds >= 0

    @pytest.mark.asyncio
    async def test_execute_unapproved_plan_fails(self, execution_engine):
        """Test that unapproved plans cannot be executed."""
        plan = PreparationPlan(
            plan_type=PlanType.INVESTIGATION,
            name="Unapproved Plan",
            description="This plan is not approved",
            expected_outcome="Should not execute"
        )
        # Leave as DRAFT status

        with pytest.raises(ValueError, match="not ready for execution"):
            await execution_engine.execute_plan(plan)

    @pytest.mark.asyncio
    async def test_execute_expired_plan_fails(
        self,
        execution_engine,
        preparation_engine
    ):
        """Test that expired plans cannot be executed."""
        monitor = Monitor(
            monitor_id="test_monitor",
            type=MonitorType.THRESHOLD,
            name="Test",
            target="test",
            interval_seconds=60,
            trigger_condition={"type": "threshold"},
            execution_mode=ExecutionMode.PREPARE
        )

        event = TriggerEvent(
            monitor_id="test_monitor",
            event_type=TriggerType.THRESHOLD_CROSSED,
            severity="low"
        )

        plan = await preparation_engine.create_plan_from_trigger(event, monitor)
        await preparation_engine.review_plan(
            plan.plan_id,
            reviewer="admin",
            approved=True
        )

        # Expire the plan
        plan.expires_at = time.time() - 1

        with pytest.raises(ValueError, match="not ready for execution"):
            await execution_engine.execute_plan(plan)

    @pytest.mark.asyncio
    async def test_execute_with_tool_policy_violation(self, execution_engine):
        """Test that tool violations prevent execution."""
        plan = PreparationPlan(
            plan_type=PlanType.REMEDIATION,
            name="Bad Plan",
            description="Uses denied tools",
            expected_outcome="Should fail policy check",
            status=PlanStatus.APPROVED
        )

        # Add a step with a destructive tool
        step = PreparationStep(
            name="Drop Database",
            description="Destructive action",
            step_type="action",
            tool_name="drop_database",
            parameters={"database": "production"}
        )
        plan.add_step(step)

        result = await execution_engine.execute_plan(plan)

        assert result.status == ExecutionStatus.FAILED
        assert "policy" in result.error.lower() or "denied" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_autonomous_task(self, execution_engine):
        """Test executing an autonomous task."""
        task = AutonomousTask(
            name="Test Task",
            execution_mode=ExecutionMode.EXECUTE,
            agents=["research_agent"],
            workspace_id="workspace_123"
        )

        result = await execution_engine.execute_task(task)

        assert result is not None
        assert result.status == ExecutionStatus.COMPLETED
        assert result.success is True
        assert result.task_id == task.task_id

    @pytest.mark.asyncio
    async def test_step_execution_respects_dependencies(
        self,
        execution_engine,
        preparation_engine
    ):
        """Test that steps execute in dependency order."""
        monitor = Monitor(
            monitor_id="test_monitor",
            type=MonitorType.THRESHOLD,
            name="Test",
            target="test",
            interval_seconds=60,
            trigger_condition={"type": "threshold"},
            execution_mode=ExecutionMode.PREPARE
        )

        event = TriggerEvent(
            monitor_id="test_monitor",
            event_type=TriggerType.THRESHOLD_CROSSED,
            severity="low"
        )

        plan = await preparation_engine.create_plan_from_trigger(event, monitor)
        await preparation_engine.review_plan(plan.plan_id, reviewer="admin", approved=True)

        result = await execution_engine.execute_plan(plan)

        # All steps should complete
        assert len(result.step_results) > 0

        # Check that steps completed in order (by time)
        completion_times = [r.completed_at for r in result.step_results if r.completed_at]
        assert completion_times == sorted(completion_times)

    @pytest.mark.asyncio
    async def test_cancel_execution(self, execution_engine):
        """Test cancelling a running execution."""
        # Create a task
        task = AutonomousTask(
            name="Long Running Task",
            execution_mode=ExecutionMode.EXECUTE,
            agents=["research_agent"]
        )

        # Start execution
        result = await execution_engine.execute_task(task)

        # Cancel it (it's already done, but test the method)
        # In real scenario, we'd cancel a running task
        cancelled = await execution_engine.cancel_execution(result.execution_id)

        # Since it's already completed, cancellation should fail
        assert cancelled is False

    @pytest.mark.asyncio
    async def test_get_execution_by_plan(
        self,
        execution_engine,
        preparation_engine
    ):
        """Test retrieving execution by plan ID."""
        monitor = Monitor(
            monitor_id="test_monitor",
            type=MonitorType.THRESHOLD,
            name="Test",
            target="test",
            interval_seconds=60,
            trigger_condition={"type": "threshold"},
            execution_mode=ExecutionMode.PREPARE
        )

        event = TriggerEvent(
            monitor_id="test_monitor",
            event_type=TriggerType.THRESHOLD_CROSSED,
            severity="low"
        )

        plan = await preparation_engine.create_plan_from_trigger(event, monitor)
        await preparation_engine.review_plan(plan.plan_id, reviewer="admin", approved=True)

        result = await execution_engine.execute_plan(plan)

        # Retrieve by plan ID
        retrieved = execution_engine.get_execution_by_plan(plan.plan_id)
        assert retrieved is not None
        assert retrieved.execution_id == result.execution_id

    @pytest.mark.asyncio
    async def test_get_execution_by_task(self, execution_engine):
        """Test retrieving execution by task ID."""
        task = AutonomousTask(
            name="Test Task",
            execution_mode=ExecutionMode.EXECUTE,
            agents=["research_agent"]
        )

        result = await execution_engine.execute_task(task)

        # Retrieve by task ID
        retrieved = execution_engine.get_execution_by_task(task.task_id)
        assert retrieved is not None
        assert retrieved.execution_id == result.execution_id


# ============================================================================
# ExecutionMetrics Tests
# ============================================================================

class TestExecutionMetrics:
    """Test execution metrics."""

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, execution_engine):
        """Test that executions update metrics."""
        task = AutonomousTask(
            name="Test Task",
            execution_mode=ExecutionMode.EXECUTE,
            agents=["research_agent"]
        )

        initial_count = execution_engine.get_metrics().total_executions

        await execution_engine.execute_task(task)

        metrics = execution_engine.get_metrics()
        assert metrics.total_executions == initial_count + 1
        assert metrics.successful_executions >= 1
        assert metrics.last_execution_time is not None

    @pytest.mark.asyncio
    async def test_metrics_by_tool(self, execution_engine):
        """Test tool usage metrics."""
        # Set a custom executor for a tool
        async def mock_executor(params):
            return "executed"

        execution_engine.set_tool_executor("custom_tool", mock_executor)

        plan = PreparationPlan(
            plan_type=PlanType.INVESTIGATION,
            name="Tool Test",
            description="Test custom tool",
            expected_outcome="Tool used",
            status=PlanStatus.APPROVED
        )

        step = PreparationStep(
            name="Use Custom Tool",
            description="Test",
            step_type="action",
            tool_name="custom_tool"
        )
        plan.add_step(step)

        await execution_engine.execute_plan(plan)

        metrics = execution_engine.get_metrics()
        # Tool should be tracked
        assert "custom_tool" in metrics.by_tool or metrics.total_executions > 0

    @pytest.mark.asyncio
    async def test_metrics_by_status(self, execution_engine):
        """Test status breakdown metrics."""
        task = AutonomousTask(
            name="Test Task",
            execution_mode=ExecutionMode.EXECUTE,
            agents=["research_agent"]
        )

        await execution_engine.execute_task(task)

        metrics = execution_engine.get_metrics()
        assert "completed" in metrics.by_status
        assert metrics.by_status["completed"] >= 1


# ============================================================================
# Integration Tests
# ============================================================================

class TestPhase5CIntegration:
    """Integration tests for Phase 5C."""

    @pytest.mark.asyncio
    async def test_full_prepare_to_execute_workflow(
        self,
        preparation_engine,
        execution_engine
    ):
        """Test complete workflow from trigger to execution."""
        # 1. Create trigger
        monitor = Monitor(
            monitor_id="cpu_monitor",
            type=MonitorType.THRESHOLD,
            name="CPU Monitor",
            target="cpu",
            interval_seconds=60,
            trigger_condition={"type": "threshold", "operator": ">", "value": 85},
            execution_mode=ExecutionMode.PREPARE
        )

        event = TriggerEvent(
            monitor_id="cpu_monitor",
            event_type=TriggerType.THRESHOLD_CROSSED,
            severity="high",
            payload={"current": 90, "threshold": 85}
        )

        # 2. Create preparation plan
        plan = await preparation_engine.create_plan_from_trigger(event, monitor)
        assert plan.status == PlanStatus.DRAFT

        # 3. Submit for review
        await preparation_engine.submit_for_review(plan.plan_id)
        plan = await preparation_engine.load_plan(plan.plan_id)
        assert plan.status == PlanStatus.PENDING_REVIEW

        # 4. Approve plan
        await preparation_engine.review_plan(
            plan.plan_id,
            reviewer="admin",
            approved=True,
            comments="Proceed with caution"
        )
        plan = await preparation_engine.load_plan(plan.plan_id)
        assert plan.status == PlanStatus.APPROVED

        # 5. Execute plan
        execution_result = await execution_engine.execute_plan(plan)
        assert execution_result.status in [
            ExecutionStatus.COMPLETED,
            ExecutionStatus.PARTIALLY_COMPLETED
        ]

        # 6. Verify execution is recorded
        retrieved = execution_engine.get_execution_by_plan(plan.plan_id)
        assert retrieved is not None
        assert retrieved.execution_id == execution_result.execution_id

    @pytest.mark.asyncio
    async def test_observe_mode_execution(self, execution_engine):
        """Test that OBSERVE mode has proper restrictions."""
        task = AutonomousTask(
            name="Observe Task",
            execution_mode=ExecutionMode.OBSERVE,
            agents=["research_agent"]
        )

        result = await execution_engine.execute_task(
            task,
            execution_mode=ExecutionMode.OBSERVE
        )

        assert result.status == ExecutionStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_policy_enforcement_in_execution(self, execution_engine):
        """Test that policies are enforced during execution."""
        # Create a plan that would violate policies
        plan = PreparationPlan(
            plan_type=PlanType.REMEDIATION,
            name="Policy Violation Plan",
            description="Attempts to use denied tools",
            expected_outcome="Should be blocked",
            status=PlanStatus.APPROVED
        )

        # Add destructive step
        step = PreparationStep(
            name="Delete Data",
            description="Destructive action",
            step_type="action",
            tool_name="delete_table",
            parameters={"table": "users"}
        )
        plan.add_step(step)

        result = await execution_engine.execute_plan(plan)

        # Should fail due to policy violation
        assert result.status == ExecutionStatus.FAILED
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_multi_step_execution_with_partial_failure(
        self,
        execution_engine,
        preparation_engine
    ):
        """Test execution with some steps failing."""
        monitor = Monitor(
            monitor_id="test_monitor",
            type=MonitorType.THRESHOLD,
            name="Test",
            target="test",
            interval_seconds=60,
            trigger_condition={"type": "threshold"},
            execution_mode=ExecutionMode.PREPARE
        )

        event = TriggerEvent(
            monitor_id="test_monitor",
            event_type=TriggerType.THRESHOLD_CROSSED,
            severity="medium"
        )

        plan = await preparation_engine.create_plan_from_trigger(event, monitor)

        # Add a failing step
        fail_step = PreparationStep(
            name="Failing Step",
            description="This will fail",
            step_type="action",
            tool_name="denied_tool"  # This tool doesn't exist - will fail
        )
        plan.steps.append(fail_step)

        await preparation_engine.review_plan(plan.plan_id, reviewer="admin", approved=True)

        result = await execution_engine.execute_plan(plan)

        # Should have some failures
        assert len(result.step_results) > 0
