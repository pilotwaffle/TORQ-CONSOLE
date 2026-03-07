"""
Tests for Phase 5B: Prepare Mode Autonomy

Tests the preparation engine, plan generation, dry-run simulation,
and recommendation system.
"""

import asyncio
import tempfile
import time
import pytest

from torq_console.autonomy.models import (
    Monitor, MonitorType, TriggerEvent, TriggerType,
    ExecutionMode, PolicyLevel, ActionRisk, AutonomousTask
)
from torq_console.autonomy.preparation import (
    PreparationEngine,
    PreparationPlan,
    PreparationStep,
    PlanType,
    PlanStatus,
    Recommendation,
    DryRunResult,
    SimulationResult,
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
async def preparation_engine(state_store):
    """Preparation engine for tests."""
    engine = PreparationEngine(state_store=state_store)
    await engine.start()
    yield engine
    await engine.stop()


@pytest.fixture
def sample_monitor():
    """Sample monitor for testing."""
    return Monitor(
        monitor_id="test_monitor",
        type=MonitorType.THRESHOLD,
        name="CPU Monitor",
        target="cpu",
        interval_seconds=60,
        trigger_condition={
            "type": "threshold",
            "field": "cpu_percent",
            "operator": ">",
            "value": 85
        },
        execution_mode=ExecutionMode.PREPARE,
        cooldown_seconds=300
    )


@pytest.fixture
def sample_trigger_event(sample_monitor):
    """Sample trigger event for testing."""
    return TriggerEvent(
        monitor_id=sample_monitor.monitor_id,
        event_type=TriggerType.THRESHOLD_CROSSED,
        severity="high",
        payload={
            "field": "cpu_percent",
            "current": 90,
            "operator": ">",
            "threshold": 85,
            "target": "cpu"
        },
        workspace_id="workspace_123",
        environment="production"
    )


# ============================================================================
# PreparationPlan Tests
# ============================================================================

class TestPreparationPlan:
    """Test PreparationPlan model."""

    def test_plan_creation(self):
        """Test creating a preparation plan."""
        plan = PreparationPlan(
            plan_type=PlanType.INVESTIGATION,
            name="Investigation Plan",
            description="Investigate the issue",
            expected_outcome="Understand the root cause"
        )

        assert plan.plan_id is not None
        assert plan.plan_type == PlanType.INVESTIGATION
        assert plan.status == PlanStatus.DRAFT
        assert plan.created_at > 0

    def test_add_step(self):
        """Test adding steps to a plan."""
        plan = PreparationPlan(
            plan_type=PlanType.REMEDIATION,
            name="Remediation Plan",
            description="Fix the issue",
            expected_outcome="Issue is resolved"
        )

        step = PreparationStep(
            name="Investigate",
            description="Initial investigation",
            step_type="investigation"
        )

        plan.add_step(step)

        assert len(plan.steps) == 1
        assert plan.steps[0].name == "Investigate"

    def test_get_step_by_id(self):
        """Test getting a step by ID."""
        plan = PreparationPlan(
            plan_type=PlanType.INVESTIGATION,
            name="Investigation Plan",
            description="Investigate",
            expected_outcome="Root cause found"
        )

        step = PreparationStep(
            name="Step 1",
            description="First step",
            step_type="investigation"
        )
        plan.add_step(step)

        found = plan.get_step_by_id(step.step_id)
        assert found is not None
        assert found.name == "Step 1"

        not_found = plan.get_step_by_id("nonexistent")
        assert not_found is None

    def test_get_ready_steps(self):
        """Test getting steps whose dependencies are satisfied."""
        plan = PreparationPlan(
            plan_type=PlanType.REMEDIATION,
            name="Remediation Plan",
            description="Fix it",
            expected_outcome="Fixed"
        )

        step1 = PreparationStep(
            name="Step 1",
            description="First",
            step_type="investigation"
        )
        step2 = PreparationStep(
            name="Step 2",
            description="Second",
            step_type="action",
            depends_on=[step1.step_id]
        )
        step3 = PreparationStep(
            name="Step 3",
            description="Third",
            step_type="verification",
            depends_on=[step2.step_id]
        )

        plan.add_step(step1)
        plan.add_step(step2)
        plan.add_step(step3)

        # Initially only step1 is ready
        ready = plan.get_ready_steps()
        assert len(ready) == 1
        assert ready[0].step_id == step1.step_id

        # After step1 completes, step2 is ready
        step1.status = "completed"
        ready = plan.get_ready_steps()
        assert len(ready) == 1
        assert ready[0].step_id == step2.step_id

    def test_is_ready_for_execution(self):
        """Test checking if plan is ready for execution."""
        plan = PreparationPlan(
            plan_type=PlanType.REMEDIATION,
            name="Remediation Plan",
            description="Fix it",
            expected_outcome="Fixed"
        )

        # Not approved, not ready
        assert plan.is_ready_for_execution is False

        # Approved but expired
        plan.status = PlanStatus.APPROVED
        plan.expires_at = time.time() - 1
        assert plan.is_ready_for_execution is False

        # Approved and not expired
        plan.expires_at = time.time() + 3600
        assert plan.is_ready_for_execution is True

    def test_is_expired(self):
        """Test checking if plan is expired."""
        plan = PreparationPlan(
            plan_type=PlanType.INVESTIGATION,
            name="Investigation Plan",
            description="Investigate",
            expected_outcome="Root cause"
        )

        # No expiration
        assert plan.is_expired is False

        # Future expiration
        plan.expires_at = time.time() + 3600
        assert plan.is_expired is False

        # Past expiration
        plan.expires_at = time.time() - 1
        assert plan.is_expired is True


# ============================================================================
# Recommendation Tests
# ============================================================================

class TestRecommendation:
    """Test Recommendation model."""

    def test_recommendation_creation(self):
        """Test creating a recommendation."""
        rec = Recommendation(
            title="Optimize Database Queries",
            description="Some queries are slow",
            category="performance",
            priority="high",
            impact="high",  # Required field
            source_type="analysis",  # Required field
            recommendation="Add indexes to frequently queried columns",
            rationale="Query latency is above SLA",
            evidence=["Query X took 5s", "Query Y took 3s"]
        )

        assert rec.recommendation_id is not None
        assert rec.title == "Optimize Database Queries"
        assert rec.category == "performance"
        assert rec.status == "pending"
        assert len(rec.evidence) == 2

    def test_recommendation_with_estimates(self):
        """Test recommendation with effort and cost estimates."""
        rec = Recommendation(
            title="Add Caching Layer",
            description="Implement Redis caching",
            category="performance",
            priority="medium",
            impact="medium",  # Required field
            source_type="analysis",  # Required field
            recommendation="Add Redis for hot data",
            rationale="Reduce database load",
            estimated_effort="2 hours",
            estimated_cost=50.0
        )

        assert rec.estimated_effort == "2 hours"
        assert rec.estimated_cost == 50.0


# ============================================================================
# PreparationEngine Tests
# ============================================================================

class TestPreparationEngine:
    """Test PreparationEngine."""

    @pytest.mark.asyncio
    async def test_engine_start_stop(self, state_store):
        """Test starting and stopping the engine."""
        engine = PreparationEngine(state_store=state_store)

        assert engine._running is False

        await engine.start()
        assert engine._running is True

        await engine.stop()
        assert engine._running is False

    @pytest.mark.asyncio
    async def test_create_plan_from_trigger(
        self,
        preparation_engine,
        sample_trigger_event,
        sample_monitor
    ):
        """Test creating a plan from a trigger event."""
        plan = await preparation_engine.create_plan_from_trigger(
            sample_trigger_event,
            sample_monitor
        )

        assert plan is not None
        assert plan.plan_id is not None
        assert plan.monitor_id == sample_monitor.monitor_id
        assert plan.trigger_event_id == sample_trigger_event.event_id
        assert plan.status == PlanStatus.DRAFT
        assert len(plan.steps) > 0
        assert plan.dry_run_result is not None  # Dry-run should have run

    @pytest.mark.asyncio
    async def test_plan_type_determination(self, preparation_engine):
        """Test that plan type is determined correctly."""
        # Test health check -> investigation
        health_monitor = Monitor(
            monitor_id="health_monitor",
            type=MonitorType.HEALTH_CHECK,
            name="Health Check",
            target="https://api.example.com/health",
            interval_seconds=60,
            trigger_condition={"type": "health_check"},
            execution_mode=ExecutionMode.PREPARE
        )

        health_event = TriggerEvent(
            monitor_id="health_monitor",
            event_type=TriggerType.THRESHOLD_CROSSED,
            severity="low"
        )

        plan = await preparation_engine.create_plan_from_trigger(
            health_event,
            health_monitor
        )

        assert plan.plan_type == PlanType.INVESTIGATION

        # Test threshold -> remediation
        threshold_monitor = Monitor(
            monitor_id="threshold_monitor",
            type=MonitorType.THRESHOLD,
            name="Threshold Monitor",
            target="cpu",
            interval_seconds=60,
            trigger_condition={"type": "threshold", "operator": ">", "value": 85},
            execution_mode=ExecutionMode.PREPARE
        )

        threshold_event = TriggerEvent(
            monitor_id="threshold_monitor",
            event_type=TriggerType.THRESHOLD_CROSSED,
            severity="high"
        )

        plan = await preparation_engine.create_plan_from_trigger(
            threshold_event,
            threshold_monitor
        )

        assert plan.plan_type == PlanType.REMEDIATION

    @pytest.mark.asyncio
    async def test_threshold_steps_generation(
        self,
        preparation_engine,
        sample_trigger_event,
        sample_monitor
    ):
        """Test that threshold triggers generate appropriate steps."""
        plan = await preparation_engine.create_plan_from_trigger(
            sample_trigger_event,
            sample_monitor
        )

        # Should have investigation, analysis, remediation, verification
        assert len(plan.steps) >= 3

        step_names = [s.name for s in plan.steps]
        assert any("Investigate" in name for name in step_names)
        assert any("Verify" in name for name in step_names)

    @pytest.mark.asyncio
    async def test_workflow_failure_steps(self, preparation_engine):
        """Test steps for workflow failure."""
        monitor = Monitor(
            monitor_id="workflow_monitor",
            type=MonitorType.WORKFLOW_FAILURE,
            name="Workflow Monitor",
            target="workflow_123",
            interval_seconds=60,
            trigger_condition={"type": "workflow_failure"},
            execution_mode=ExecutionMode.PREPARE
        )

        event = TriggerEvent(
            monitor_id="workflow_monitor",
            event_type=TriggerType.WORKFLOW_FAILED,
            severity="high",
            payload={"error": "Task failed"}
        )

        plan = await preparation_engine.create_plan_from_trigger(event, monitor)

        # Should have analysis and fix steps
        assert len(plan.steps) >= 2
        step_types = [s.step_type for s in plan.steps]
        assert "investigation" in step_types

    @pytest.mark.asyncio
    async def test_submit_for_review(
        self,
        preparation_engine,
        sample_trigger_event,
        sample_monitor
    ):
        """Test submitting a plan for review."""
        plan = await preparation_engine.create_plan_from_trigger(
            sample_trigger_event,
            sample_monitor
        )

        result = await preparation_engine.submit_for_review(plan.plan_id)

        assert result is True

        # Reload and check status
        reloaded = await preparation_engine.load_plan(plan.plan_id)
        assert reloaded.status == PlanStatus.PENDING_REVIEW

    @pytest.mark.asyncio
    async def test_review_plan_approve(
        self,
        preparation_engine,
        sample_trigger_event,
        sample_monitor
    ):
        """Test approving a plan."""
        plan = await preparation_engine.create_plan_from_trigger(
            sample_trigger_event,
            sample_monitor
        )

        result = await preparation_engine.review_plan(
            plan.plan_id,
            reviewer="admin_123",
            approved=True,
            comments="Looks good"
        )

        assert result is True

        # Check status
        reloaded = await preparation_engine.load_plan(plan.plan_id)
        assert reloaded.status == PlanStatus.APPROVED
        assert reloaded.reviewed_by == "admin_123"
        assert reloaded.approved_by == "admin_123"
        assert reloaded.review_comments == "Looks good"

    @pytest.mark.asyncio
    async def test_review_plan_reject(
        self,
        preparation_engine,
        sample_trigger_event,
        sample_monitor
    ):
        """Test rejecting a plan."""
        plan = await preparation_engine.create_plan_from_trigger(
            sample_trigger_event,
            sample_monitor
        )

        result = await preparation_engine.review_plan(
            plan.plan_id,
            reviewer="admin_123",
            approved=False,
            comments="Too risky, need more analysis"
        )

        assert result is True

        # Check status
        reloaded = await preparation_engine.load_plan(plan.plan_id)
        assert reloaded.status == PlanStatus.REJECTED
        assert reloaded.reviewed_by == "admin_123"
        assert reloaded.approved_by is None  # Not set when rejected

    @pytest.mark.asyncio
    async def test_list_plans(
        self,
        preparation_engine,
        sample_trigger_event,
        sample_monitor
    ):
        """Test listing plans."""
        # Create multiple plans
        plan1 = await preparation_engine.create_plan_from_trigger(
            sample_trigger_event,
            sample_monitor
        )

        # Modify and submit
        await preparation_engine.submit_for_review(plan1.plan_id)

        # List all plans
        all_plans = await preparation_engine.list_plans()
        assert len(all_plans) >= 1

        # Filter by status
        draft_plans = await preparation_engine.list_plans(status=PlanStatus.DRAFT)
        pending_plans = await preparation_engine.list_plans(status=PlanStatus.PENDING_REVIEW)

        # plan1 should be in pending, not draft
        assert plan1.plan_id not in [p.plan_id for p in draft_plans]
        assert plan1.plan_id in [p.plan_id for p in pending_plans]

    @pytest.mark.asyncio
    async def test_plan_expiration(
        self,
        preparation_engine,
        sample_trigger_event,
        sample_monitor
    ):
        """Test plan expiration logic."""
        plan = await preparation_engine.create_plan_from_trigger(
            sample_trigger_event,
            sample_monitor
        )

        # Approve it
        await preparation_engine.review_plan(
            plan.plan_id,
            reviewer="admin",
            approved=True
        )

        # Set expiration to past
        plan.expires_at = time.time() - 1
        await preparation_engine.save_plan(plan)

        # Check if expired
        reloaded = await preparation_engine.load_plan(plan.plan_id)
        assert reloaded.is_expired is True
        assert reloaded.is_ready_for_execution is False


# ============================================================================
# Dry Run Tests
# ============================================================================

class TestDryRun:
    """Test dry-run simulation."""

    @pytest.mark.asyncio
    async def test_default_dry_run(
        self,
        preparation_engine,
        sample_trigger_event,
        sample_monitor
    ):
        """Test default dry-run simulation."""
        plan = await preparation_engine.create_plan_from_trigger(
            sample_trigger_event,
            sample_monitor
        )

        # Dry-run should have been created automatically
        assert plan.dry_run_result is not None
        assert plan.dry_run_result.result == SimulationResult.SUCCESS
        assert plan.dry_run_result.confidence > 0
        assert len(plan.dry_run_result.step_results) == len(plan.steps)

    @pytest.mark.asyncio
    async def test_custom_dry_run_simulator(self, state_store):
        """Test custom dry-run simulator."""
        engine = PreparationEngine(state_store=state_store)

        # Custom simulator
        async def custom_simulator(plan):
            return DryRunResult(
                plan_id=plan.plan_id,
                result=SimulationResult.WARNING,
                confidence=0.5,
                warnings=["Custom warning"],
                recommendations=["Custom recommendation"]
            )

        engine.set_dry_run_simulator(custom_simulator)

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

        plan = await engine.create_plan_from_trigger(event, monitor)

        assert plan.dry_run_result.result == SimulationResult.WARNING
        assert "Custom warning" in plan.dry_run_result.warnings


# ============================================================================
# Recommendation Tests
# ============================================================================

class TestRecommendations:
    """Test recommendation management."""

    @pytest.mark.asyncio
    async def test_create_recommendation(self, preparation_engine):
        """Test creating a recommendation."""
        rec = await preparation_engine.create_recommendation(
            title="Add Index",
            description="Query is slow",
            category="performance",
            recommendation="Add index on user_id column",
            rationale="Query takes 5 seconds",
            priority="high",
            evidence=["Query log shows slow query"],
            estimated_effort="30 minutes"
        )

        assert rec.recommendation_id is not None
        assert rec.title == "Add Index"
        assert rec.category == "performance"
        assert rec.status == "pending"

    @pytest.mark.asyncio
    async def test_list_recommendations(self, preparation_engine):
        """Test listing recommendations."""
        # Create recommendations
        await preparation_engine.create_recommendation(
            title="Rec 1",
            description="First",
            category="performance",
            recommendation="Do this",
            rationale="Because",
            priority="high"
        )

        await preparation_engine.create_recommendation(
            title="Rec 2",
            description="Second",
            category="security",
            recommendation="Do that",
            rationale="Why not",
            priority="medium"
        )

        # List all
        all_recs = await preparation_engine.list_recommendations()
        assert len(all_recs) >= 2

        # Filter by category
        perf_recs = await preparation_engine.list_recommendations(category="performance")
        assert len(perf_recs) >= 1

    @pytest.mark.asyncio
    async def test_acknowledge_recommendation(self, preparation_engine):
        """Test acknowledging a recommendation."""
        rec = await preparation_engine.create_recommendation(
            title="Test Rec",
            description="Test",
            category="test",
            recommendation="Test action",
            rationale="Test reason"
        )

        result = await preparation_engine.acknowledge_recommendation(
            rec.recommendation_id
        )

        assert result is True

        recs = await preparation_engine.list_recommendations(status="acknowledged")
        assert rec.recommendation_id in [r.recommendation_id for r in recs]

    @pytest.mark.asyncio
    async def test_dismiss_recommendation(self, preparation_engine):
        """Test dismissing a recommendation."""
        rec = await preparation_engine.create_recommendation(
            title="Test Rec",
            description="Test",
            category="test",
            recommendation="Test action",
            rationale="Test reason"
        )

        result = await preparation_engine.dismiss_recommendation(
            rec.recommendation_id
        )

        assert result is True

        recs = await preparation_engine.list_recommendations(status="dismissed")
        assert rec.recommendation_id in [r.recommendation_id for r in recs]


# ============================================================================
# Integration Tests
# ============================================================================

class TestPhase5BIntegration:
    """Integration tests for Phase 5B."""

    @pytest.mark.asyncio
    async def test_end_to_end_prepare_workflow(
        self,
        preparation_engine,
        sample_trigger_event,
        sample_monitor
    ):
        """Test complete prepare workflow."""
        # 1. Trigger event creates plan
        plan = await preparation_engine.create_plan_from_trigger(
            sample_trigger_event,
            sample_monitor
        )
        assert plan.status == PlanStatus.DRAFT

        # 2. Submit for review
        await preparation_engine.submit_for_review(plan.plan_id)
        plan = await preparation_engine.load_plan(plan.plan_id)
        assert plan.status == PlanStatus.PENDING_REVIEW

        # 3. Review and approve
        await preparation_engine.review_plan(
            plan.plan_id,
            reviewer="admin",
            approved=True,
            comments="Approved for execution"
        )
        plan = await preparation_engine.load_plan(plan.plan_id)
        assert plan.status == PlanStatus.APPROVED

        # 4. Check ready for execution
        assert plan.is_ready_for_execution is True

        # 5. Check dry-run was performed
        assert plan.dry_run_result is not None
        assert plan.dry_run_result.result == SimulationResult.SUCCESS

    @pytest.mark.asyncio
    async def test_risk_assessment(self, preparation_engine):
        """Test risk assessment for different scenarios."""
        # Low risk - observe mode
        observe_monitor = Monitor(
            monitor_id="observe_monitor",
            type=MonitorType.HEALTH_CHECK,
            name="Observe Monitor",
            target="api",
            interval_seconds=60,
            trigger_condition={"type": "health_check"},
            execution_mode=ExecutionMode.OBSERVE
        )

        low_event = TriggerEvent(
            monitor_id="observe_monitor",
            event_type=TriggerType.THRESHOLD_CROSSED,
            severity="low"
        )

        low_plan = await preparation_engine.create_plan_from_trigger(
            low_event,
            observe_monitor
        )
        assert low_plan.risk_level == ActionRisk.LOW

        # High risk - execute mode with critical severity
        execute_monitor = Monitor(
            monitor_id="execute_monitor",
            type=MonitorType.THRESHOLD,
            name="Execute Monitor",
            target="critical_system",
            interval_seconds=60,
            trigger_condition={"type": "threshold"},
            execution_mode=ExecutionMode.EXECUTE
        )

        critical_event = TriggerEvent(
            monitor_id="execute_monitor",
            event_type=TriggerType.THRESHOLD_CROSSED,
            severity="critical"
        )

        high_plan = await preparation_engine.create_plan_from_trigger(
            critical_event,
            execute_monitor
        )
        assert high_plan.risk_level == ActionRisk.CRITICAL

    @pytest.mark.asyncio
    async def test_metrics(self, preparation_engine):
        """Test getting preparation engine metrics."""
        # Create some data
        await preparation_engine.create_recommendation(
            title="Test",
            description="Test",
            category="test",
            recommendation="Test",
            rationale="Test"
        )

        metrics = preparation_engine.get_metrics()

        assert metrics["total_recommendations"] >= 1
        assert metrics["dry_run_enabled"] is True
        assert metrics["is_running"] is True
