"""
Phase 5 Tests - Autonomous Operations Foundation

Tests for monitors, triggers, tasks, policy engine, and approval workflows.
"""

import pytest
import asyncio
import time
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from torq_console.autonomy.models import (
    Monitor, MonitorType, TriggerEvent, TriggerType,
    AutonomousTask, TaskState, ExecutionMode,
    ApprovalRequest, ApprovalStatus,
    PolicyLevel, ActionRisk, PolicyDecision,
    TaskStateRecord, MonitorState
)
from torq_console.autonomy.trigger_engine import TriggerEngine, TriggerEvaluator
from torq_console.autonomy.task_engine import TaskEngine, TaskQueue, TaskScheduler
from torq_console.autonomy.policy_engine import PolicyEngine, PolicyRule
from torq_console.autonomy.approval_manager import ApprovalManager, ApprovalInbox
from torq_console.autonomy.execution_planner import ExecutionPlanner, ExecutionPlan
from torq_console.autonomy.state_store import StateStore


@pytest.fixture
def temp_storage():
    """Create a temporary directory for test storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def state_store(temp_storage):
    """Create a state store with temporary storage."""
    return StateStore(temp_storage)


# ============================================================================
# Model Tests
# ============================================================================

class TestMonitor:
    """Test Monitor model."""

    def test_monitor_creation(self):
        """Test creating a monitor."""
        monitor = Monitor(
            monitor_id="test_monitor",
            type=MonitorType.THRESHOLD,
            name="CPU Threshold Monitor",
            target="https://api.example.com/metrics/cpu",
            interval_seconds=300,
            trigger_condition={
                "type": "threshold",
                "field": "cpu_percent",
                "operator": ">",
                "value": 85
            },
            execution_mode=ExecutionMode.OBSERVE
        )

        assert monitor.monitor_id == "test_monitor"
        assert monitor.type == MonitorType.THRESHOLD
        assert monitor.enabled is True

    def test_monitor_is_due(self):
        """Test monitor due calculation."""
        monitor = Monitor(
            monitor_id="test_monitor",
            type=MonitorType.HEALTH_CHECK,
            name="Health Check",
            target="https://api.example.com/health",
            interval_seconds=60,
            trigger_condition={"type": "health_check"}
        )

        # New monitor is always due
        assert monitor.is_due is True

        # After check, not due until interval passes
        monitor.last_check = time.time()
        assert monitor.is_due is False

    def test_monitor_cooldown(self):
        """Test monitor cooldown after triggering."""
        monitor = Monitor(
            monitor_id="test_monitor",
            type=MonitorType.THRESHOLD,
            name="Threshold Monitor",
            target="https://api.example.com",
            interval_seconds=60,
            cooldown_seconds=300,
            trigger_condition={"type": "threshold", "operator": ">", "value": 100}
        )

        # Not in cooldown initially
        assert monitor.is_in_cooldown is False

        # After trigger, in cooldown
        monitor.last_trigger = time.time()
        assert monitor.is_in_cooldown is True

        # After cooldown period, not in cooldown
        monitor.last_trigger = time.time() - 301
        assert monitor.is_in_cooldown is False


class TestTriggerEvent:
    """Test TriggerEvent model."""

    def test_trigger_event_creation(self):
        """Test creating a trigger event."""
        event = TriggerEvent(
            monitor_id="test_monitor",
            event_type=TriggerType.THRESHOLD_CROSSED,
            severity="high",
            payload={"value": 90, "threshold": 85}
        )

        assert event.monitor_id == "test_monitor"
        assert event.event_type == TriggerType.THRESHOLD_CROSSED
        assert event.processed is False


class TestAutonomousTask:
    """Test AutonomousTask model."""

    def test_task_creation(self):
        """Test creating an autonomous task."""
        task = AutonomousTask(
            name="Research Task",
            execution_mode=ExecutionMode.OBSERVE,
            agents=["research_agent"],
            prompt_template="Research the following: {query}"
        )

        assert task.name == "Research Task"
        assert task.execution_mode == ExecutionMode.OBSERVE
        assert task.state == TaskState.CREATED

    def test_task_can_execute(self):
        """Test task execution eligibility."""
        # Task without approval can execute
        task = AutonomousTask(
            name="Execute Task",
            execution_mode=ExecutionMode.OBSERVE,
            agents=["research_agent"]
        )

        assert task.can_execute is True
        assert task.needs_approval is False

        # Task with approval cannot execute directly
        task.approval_required = True
        assert task.can_execute is False
        assert task.needs_approval is True

    def test_task_is_finished(self):
        """Test task completion status."""
        task = AutonomousTask(
            name="Test Task",
            execution_mode=ExecutionMode.OBSERVE,
            agents=["research_agent"]
        )

        assert task.is_finished is False

        task.state = TaskState.SUCCEEDED
        assert task.is_finished is True

        task.state = TaskState.FAILED
        assert task.is_finished is True


class TestPolicyDecision:
    """Test PolicyDecision model."""

    def test_policy_decision_allowed(self):
        """Test allowed policy decision."""
        decision = PolicyDecision(
            allowed=True,
            policy_level=PolicyLevel.ALLOW,
            reason="Low-risk observe operation"
        )

        assert decision.allowed is True
        assert decision.requires_approval is False
        assert decision.risk_level == ActionRisk.LOW

    def test_policy_decision_requires_approval(self):
        """Test approval-required policy decision."""
        decision = PolicyDecision(
            allowed=True,
            policy_level=PolicyLevel.REQUIRE_APPROVAL,
            reason="Production operation requires approval",
            requires_approval=True,
            risk_level=ActionRisk.HIGH
        )

        assert decision.allowed is True
        assert decision.requires_approval is True
        assert decision.risk_level == ActionRisk.HIGH

    def test_policy_decision_denied(self):
        """Test denied policy decision."""
        decision = PolicyDecision(
            allowed=False,
            policy_level=PolicyLevel.DENY,
            reason="Destructive action not allowed"
        )

        assert decision.allowed is False


# ============================================================================
# Trigger Engine Tests
# ============================================================================

class TestTriggerEvaluator:
    """Test trigger evaluation logic."""

    def test_threshold_trigger_above(self):
        """Test threshold trigger for value above limit."""
        monitor = Monitor(
            monitor_id="cpu_monitor",
            type=MonitorType.THRESHOLD,
            name="CPU Monitor",
            target="cpu",
            interval_seconds=60,
            trigger_condition={
                "type": "threshold",
                "field": "cpu_percent",
                "operator": ">",
                "value": 85
            }
        )

        evaluator = TriggerEvaluator()

        # Value above threshold
        event = evaluator.evaluate(monitor, 90)
        assert event is not None
        assert event.event_type == TriggerType.THRESHOLD_CROSSED
        assert event.payload["current"] == 90

        # Value below threshold
        event = evaluator.evaluate(monitor, 70)
        assert event is None

    def test_threshold_trigger_below(self):
        """Test threshold trigger for value below limit."""
        monitor = Monitor(
            monitor_id="memory_monitor",
            type=MonitorType.THRESHOLD,
            name="Memory Monitor",
            target="memory",
            interval_seconds=60,
            trigger_condition={
                "type": "threshold",
                "field": "memory_percent",
                "operator": "<",
                "value": 20
            }
        )

        evaluator = TriggerEvaluator()

        # Value below threshold
        event = evaluator.evaluate(monitor, 15)
        assert event is not None
        assert event.payload["current"] == 15

        # Value above threshold
        event = evaluator.evaluate(monitor, 50)
        assert event is None

    def test_status_change_trigger(self):
        """Test status change trigger."""
        monitor = Monitor(
            monitor_id="service_monitor",
            type=MonitorType.STATUS_CHANGE,
            name="Service Monitor",
            target="service",
            interval_seconds=60,
            trigger_condition={
                "type": "status_change",
                "field": "status",
            }
        )

        evaluator = TriggerEvaluator()

        # First check - no previous value
        event = evaluator.evaluate(monitor, "healthy")
        assert event is None  # No previous value, no trigger

        # Status changed
        event = evaluator.evaluate(monitor, "degraded", previous_value="healthy")
        assert event is not None
        assert event.event_type == TriggerType.STATUS_CHANGED

        # Status stayed same
        event = evaluator.evaluate(monitor, "degraded", previous_value="degraded")
        assert event is None

    def test_keyword_match_trigger(self):
        """Test keyword/topic match trigger."""
        monitor = Monitor(
            monitor_id="news_monitor",
            type=MonitorType.TOPIC,
            name="News Monitor",
            target="news",
            interval_seconds=3600,
            trigger_condition={
                "type": "keyword_match",
                "keywords": ["AI", "machine learning", "LLM"]
            }
        )

        evaluator = TriggerEvaluator()

        # Matching keyword
        event = evaluator.evaluate(monitor, "Breaking news in AI and machine learning")
        assert event is not None
        assert event.event_type == TriggerType.TOPIC_MATCHED

        # No matching keyword
        event = evaluator.evaluate(monitor, "Breaking news in sports")
        assert event is None

    def test_cooldown_suppression(self):
        """Test that cooldown suppresses repeated triggers."""
        monitor = Monitor(
            monitor_id="test_monitor",
            type=MonitorType.THRESHOLD,
            name="Test Monitor",
            target="test",
            interval_seconds=60,
            cooldown_seconds=300,
            trigger_condition={"type": "threshold", "operator": ">", "value": 85}
        )

        evaluator = TriggerEvaluator()

        # First trigger - not in cooldown yet, should trigger
        event = evaluator.evaluate(monitor, 90)
        assert event is not None

        # Set last_trigger to put monitor in cooldown
        monitor.last_trigger = time.time()

        # During cooldown - should suppress
        event = evaluator.evaluate(monitor, 95)
        assert event is None

        # After cooldown - should trigger again
        monitor.last_trigger = time.time() - 301
        event = evaluator.evaluate(monitor, 90)
        assert event is not None


# ============================================================================
# Task Engine Tests
# ============================================================================

class TestTaskQueue:
    """Test task queue operations."""

    def test_enqueue_dequeue(self):
        """Test basic enqueue and dequeue operations."""
        queue = TaskQueue()

        task = AutonomousTask(
            name="Test Task",
            execution_mode=ExecutionMode.OBSERVE,
            agents=["research_agent"]
        )

        assert queue.enqueue(task) is True
        assert queue.size() == 1

        retrieved_task = queue.dequeue()
        assert retrieved_task is not None
        assert retrieved_task.task_id == task.task_id
        assert queue.size() == 0

    def test_queue_order(self):
        """Test that queue maintains FIFO order."""
        queue = TaskQueue()

        tasks = [
            AutonomousTask(
                name=f"Task {i}",
                execution_mode=ExecutionMode.OBSERVE,
                agents=["research_agent"]
            )
            for i in range(3)
        ]

        for task in tasks:
            queue.enqueue(task)

        # Should retrieve in same order
        for i in range(3):
            task = queue.dequeue()
            assert task.name == f"Task {i}"

    def test_remove_task(self):
        """Test removing a specific task from queue."""
        queue = TaskQueue()

        task1 = AutonomousTask(
            name="Task 1",
            execution_mode=ExecutionMode.OBSERVE,
            agents=["research_agent"]
        )
        task2 = AutonomousTask(
            name="Task 2",
            execution_mode=ExecutionMode.OBSERVE,
            agents=["research_agent"]
        )

        queue.enqueue(task1)
        queue.enqueue(task2)

        # Remove middle task
        assert queue.remove(task1.task_id) is True
        assert queue.size() == 1

        # Try to remove already removed task
        assert queue.remove(task1.task_id) is False


class TestTaskScheduler:
    """Test task scheduler."""

    @pytest.mark.asyncio
    async def test_schedule_task(self):
        """Test scheduling a task for future execution."""
        scheduler = TaskScheduler()

        task = AutonomousTask(
            name="Scheduled Task",
            execution_mode=ExecutionMode.OBSERVE,
            agents=["research_agent"]
        )

        # Schedule for 1 second in the future
        await scheduler.schedule(task, delay_seconds=1)

        # Immediately should not have due tasks
        due_tasks = await scheduler.get_due_tasks()
        assert len(due_tasks) == 0

        # Wait for time to pass
        await asyncio.sleep(1.1)

        # Now should have due task
        due_tasks = await scheduler.get_due_tasks()
        assert len(due_tasks) == 1
        assert due_tasks[0].task_id == task.task_id

    @pytest.mark.asyncio
    async def test_cancel_scheduled_task(self):
        """Test canceling a scheduled task."""
        scheduler = TaskScheduler()

        task = AutonomousTask(
            name="To Cancel",
            execution_mode=ExecutionMode.OBSERVE,
            agents=["research_agent"]
        )

        await scheduler.schedule(task, delay_seconds=60)

        # Cancel before it runs
        result = await scheduler.cancel(task.task_id)
        assert result is True
        assert task.state == TaskState.CANCELLED

        # Should not have due tasks
        due_tasks = await scheduler.get_due_tasks()
        assert len(due_tasks) == 0


# ============================================================================
# Policy Engine Tests
# ============================================================================

class TestPolicyEngine:
    """Test policy engine evaluation."""

    def test_observe_mode_allowed(self):
        """Test that observe mode is auto-allowed."""
        engine = PolicyEngine()

        task = AutonomousTask(
            name="Observe Task",
            execution_mode=ExecutionMode.OBSERVE,
            agents=["research_agent"]
        )

        decision = engine.evaluate(task)

        assert decision.allowed is True
        assert decision.policy_level == PolicyLevel.ALLOW
        assert decision.requires_approval is False

    def test_prepare_mode_allowed_with_log(self):
        """Test that prepare mode is allowed with logging."""
        engine = PolicyEngine()

        task = AutonomousTask(
            name="Prepare Task",
            execution_mode=ExecutionMode.PREPARE,
            agents=["workflow_agent"]
        )

        decision = engine.evaluate(task)

        assert decision.allowed is True
        assert decision.policy_level == PolicyLevel.ALLOW_WITH_LOG

    def test_execute_mode_requires_approval(self):
        """Test that execute mode requires approval."""
        engine = PolicyEngine()

        task = AutonomousTask(
            name="Execute Task",
            execution_mode=ExecutionMode.EXECUTE,
            agents=["workflow_agent"]
        )

        decision = engine.evaluate(task)

        assert decision.allowed is True  # Allowed but needs approval
        assert decision.policy_level == PolicyLevel.REQUIRE_APPROVAL
        assert decision.requires_approval is True

    def test_destructive_action_denied(self):
        """Test that destructive actions are denied."""
        engine = PolicyEngine()

        task = AutonomousTask(
            name="Delete Database",
            execution_mode=ExecutionMode.EXECUTE,
            agents=["workflow_agent"],
            prompt_template="Delete all records from production database"
        )

        decision = engine.evaluate(task)

        assert decision.allowed is False
        assert decision.policy_level == PolicyLevel.DENY

    def test_prod_write_requires_approval(self):
        """Test that production write operations require approval."""
        engine = PolicyEngine()

        task = AutonomousTask(
            name="Update Config",
            execution_mode=ExecutionMode.PREPARE,
            agents=["workflow_agent"],
            environment="production",
            prompt_template="Update the configuration file"
        )

        decision = engine.evaluate(task, {"environment": "production"})

        assert decision.allowed is True
        assert decision.requires_approval is True
        assert decision.policy_level == PolicyLevel.REQUIRE_APPROVAL


# ============================================================================
# Approval Manager Tests
# ============================================================================

class TestApprovalManager:
    """Test approval manager operations."""

    @pytest.mark.asyncio
    async def test_create_approval_request(self, state_store):
        """Test creating an approval request."""
        manager = ApprovalManager(state_store)

        task = AutonomousTask(
            name="Execute Task",
            execution_mode=ExecutionMode.EXECUTE,
            agents=["workflow_agent"]
        )

        policy_decision = PolicyDecision(
            allowed=True,
            policy_level=PolicyLevel.REQUIRE_APPROVAL,
            reason="Execute mode requires approval",
            requires_approval=True,
            risk_level=ActionRisk.HIGH
        )

        approval = await manager.create_approval_request(task, policy_decision)

        assert approval is not None
        assert approval.status == ApprovalStatus.PENDING
        assert approval.risk_level == ActionRisk.HIGH
        assert approval.task_id == task.task_id

    @pytest.mark.asyncio
    async def test_approve_request(self, state_store):
        """Test approving an approval request."""
        manager = ApprovalManager(state_store)

        # Create approval request
        approval = ApprovalRequest(
            task_id="task_123",
            requested_action="Execute Task",
            action_description="Execute the workflow",
            risk_level=ActionRisk.HIGH,
            policy_level=PolicyLevel.REQUIRE_APPROVAL,
            trigger_reason="Policy requires approval for execute mode"
        )

        await state_store.save_approval(approval)

        # Approve it
        result = await manager.approve(
            approval.approval_id,
            approved_by="admin_123",
            comment="Looks good to proceed"
        )

        assert result is True

        # Verify status
        updated = await state_store.load_approval(approval.approval_id)
        assert updated.status == ApprovalStatus.APPROVED
        assert updated.approved_by == "admin_123"
        assert updated.approved_by == "admin_123"

    @pytest.mark.asyncio
    async def test_deny_request(self, state_store):
        """Test denying an approval request."""
        manager = ApprovalManager(state_store)

        approval = ApprovalRequest(
            task_id="task_123",
            requested_action="Execute Task",
            action_description="Execute the workflow",
            risk_level=ActionRisk.HIGH,
            policy_level=PolicyLevel.REQUIRE_APPROVAL,
            trigger_reason="Policy requires approval for execute mode"
        )

        await state_store.save_approval(approval)

        # Deny it
        result = await manager.deny(
            approval.approval_id,
            denied_by="admin_123",
            reason="Too risky, need manual review"
        )

        assert result is True

        # Verify status
        updated = await state_store.load_approval(approval.approval_id)
        assert updated.status == ApprovalStatus.DENIED
        assert updated.denied_reason == "Too risky, need manual review"

    @pytest.mark.asyncio
    async def test_approval_expiration(self, state_store):
        """Test approval expiration."""
        manager = ApprovalManager(state_store)
        manager.default_approval_timeout = 1  # 1 second timeout

        # Create approval with short timeout
        approval = ApprovalRequest(
            task_id="task_123",
            requested_action="Execute Task",
            action_description="Execute",
            risk_level=ActionRisk.MEDIUM,
            policy_level=PolicyLevel.REQUIRE_APPROVAL,
            trigger_reason="Policy requires approval",
            expires_at=time.time() - 1  # Already expired
        )

        await state_store.save_approval(approval)

        # Run expiration check
        await manager._expire_old_approvals()

        # Verify expired
        updated = await state_store.load_approval(approval.approval_id)
        assert updated.status == ApprovalStatus.EXPIRED


# ============================================================================
# Execution Planner Tests
# ============================================================================

class TestExecutionPlanner:
    """Test execution planning."""

    @pytest.mark.asyncio
    async def test_plan_from_threshold_trigger(self):
        """Test planning from threshold trigger."""
        planner = ExecutionPlanner()

        event = TriggerEvent(
            monitor_id="cpu_monitor",
            event_type=TriggerType.THRESHOLD_CROSSED,
            severity="high",
            payload={"current": 90, "threshold": 85}
        )

        monitor_config = {
            "type": MonitorType.THRESHOLD,
            "execution_mode": "observe"
        }

        plan = await planner.plan_from_trigger(event, monitor_config)

        assert plan.execution_mode == ExecutionMode.OBSERVE
        assert len(plan.agents) > 0
        assert plan.tool_policy == "required"
        assert plan.approval_required is False

    @pytest.mark.asyncio
    async def test_plan_from_status_change_trigger(self):
        """Test planning from status change trigger."""
        planner = ExecutionPlanner()

        event = TriggerEvent(
            monitor_id="service_monitor",
            event_type=TriggerType.STATUS_CHANGED,
            severity="high",
            payload={"previous": "healthy", "current": "degraded"}
        )

        monitor_config = {
            "type": MonitorType.STATUS_CHANGE,
            "execution_mode": "prepare"
        }

        plan = await planner.plan_from_trigger(event, monitor_config)

        assert plan.execution_mode == ExecutionMode.PREPARE
        assert "orchestration_agent" in plan.agents

    @pytest.mark.asyncio
    async def test_plan_from_topic_trigger(self):
        """Test planning from topic/news trigger."""
        planner = ExecutionPlanner()

        event = TriggerEvent(
            monitor_id="news_monitor",
            event_type=TriggerType.TOPIC_MATCHED,
            severity="low",
            payload={"topic": "AI", "context": "Breaking AI news"}
        )

        monitor_config = {
            "type": MonitorType.TOPIC,
            "execution_mode": "observe"
        }

        plan = await planner.plan_from_trigger(event, monitor_config)

        assert plan.execution_mode == ExecutionMode.OBSERVE
        assert "research_agent" in plan.agents
        assert plan.tool_policy == "required"


# ============================================================================
# Integration Tests
# ============================================================================

class TestPhase5AIntegration:
    """Integration tests for Phase 5A autonomous operations."""

    @pytest.mark.asyncio
    async def test_end_to_end_monitor_to_task(self, temp_storage):
        """Test complete flow from monitor trigger to task creation."""
        # Create components
        state_store = StateStore(temp_storage)
        trigger_engine = TriggerEngine(state_store)
        task_engine = TaskEngine(state_store)

        # Register a monitor
        monitor = Monitor(
            monitor_id="integration_monitor",
            type=MonitorType.THRESHOLD,
            name="Integration Test Monitor",
            target="test_metric",
            interval_seconds=60,
            trigger_condition={
                "type": "threshold",
                "operator": ">",
                "value": 100
            },
            execution_mode=ExecutionMode.OBSERVE
        )

        trigger_engine.register_monitor(monitor)

        # Add handler to create tasks on trigger
        triggered_events = []

        async def task_creator(event):
            triggered_events.append(event)
            task = await task_engine.create_task(
                name=f"Task for {event.monitor_id}",
                execution_mode=ExecutionMode.OBSERVE,
                trigger_event=event,
                monitor_id=event.monitor_id,
                agents=["research_agent"],
                prompt_template=f"Handle event: {event.event_type}"
            )
            return task

        trigger_engine.add_event_handler(task_creator)

        # Simulate trigger evaluation with value above threshold
        event = trigger_engine.evaluator.evaluate(monitor, 150)

        # Verify event was created
        assert event is not None
        assert event.event_type == TriggerType.THRESHOLD_CROSSED

        # Manually emit to trigger handler
        await trigger_engine._emit_event(event)

        # Verify task was created
        assert len(triggered_events) == 1

        tasks = task_engine.list_tasks()
        assert len(tasks) > 0

        # Find the created task
        task = next((t for t in tasks if t.monitor_id == monitor.monitor_id), None)
        assert task is not None
        assert task.execution_mode == ExecutionMode.OBSERVE

    @pytest.mark.asyncio
    async def test_policy_integration_with_task_engine(self, state_store):
        """Test policy engine integration with task creation."""
        task_engine = TaskEngine(state_store)
        policy_engine = PolicyEngine()

        # Create a task that requires approval
        task = await task_engine.create_task(
            name="Production Update",
            execution_mode=ExecutionMode.EXECUTE,
            agents=["workflow_agent"],
            prompt_template="Update production config",
            environment="production"
        )

        # Evaluate policy
        decision = policy_engine.evaluate(task, {"environment": "production"})

        # Verify policy decision
        assert decision.requires_approval is True
        assert decision.policy_level == PolicyLevel.REQUIRE_APPROVAL


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
