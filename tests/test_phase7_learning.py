"""
Tests for Phase 7: Self-Improvement & Agent Generation

Tests the learning engine, outcome tracking, pattern detection,
improvement suggestions, and feedback collection.
"""

import asyncio
import tempfile
import time
import pytest
import pytest_asyncio

from torq_console.autonomy.learning import (
    LearningEngine,
    TaskOutcome,
    OutcomeCategory,
    PerformanceMetrics,
    ImprovementSuggestion,
    ImprovementType,
    ModelFeedback,
    FeedbackType,
    ObservationRecord,
    get_learning_engine
)
from torq_console.autonomy.state_store import StateStore
from torq_console.autonomy.execution import (
    ExecutionResult,
    ExecutionStatus
)
from torq_console.autonomy.preparation import (
    PreparationPlan,
    PlanType,
    PlanStatus
)


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


@pytest_asyncio.fixture
async def learning_engine(state_store):
    """Learning engine for tests."""
    engine = LearningEngine(state_store=state_store)
    await engine.start()
    yield engine
    await engine.stop()


# ============================================================================
# TaskOutcome Tests
# ============================================================================

class TestTaskOutcome:
    """Test TaskOutcome model."""

    def test_outcome_creation(self):
        """Test creating a task outcome."""
        outcome = TaskOutcome(
            category=OutcomeCategory.SUCCESS,
            success=True,
            duration_seconds=10.5,
            task_type="investigation",
            agents_used=["research_agent"],
            tools_used=["web_search"]
        )

        assert outcome.outcome_id is not None
        assert outcome.success is True
        assert outcome.category == OutcomeCategory.SUCCESS
        assert outcome.quality_score == 1.0  # Default for success

    def test_outcome_failure(self):
        """Test failure outcome."""
        outcome = TaskOutcome(
            category=OutcomeCategory.FAILURE,
            success=False,
            duration_seconds=5.0,
            failure_reason="Tool not available",
            error_message="Tool 'custom_tool' not found"
        )

        assert outcome.success is False
        assert outcome.failure_reason == "Tool not available"
        assert outcome.error_message == "Tool 'custom_tool' not found"

    def test_outcome_with_scores(self):
        """Test outcome with quality and satisfaction scores."""
        outcome = TaskOutcome(
            category=OutcomeCategory.SUCCESS,
            success=True,
            duration_seconds=8.0,
            quality_score=0.8,
            user_satisfaction=0.9
        )

        assert outcome.quality_score == 0.8
        assert outcome.user_satisfaction == 0.9


# ============================================================================
# PerformanceMetrics Tests
# ============================================================================

class TestPerformanceMetrics:
    """Test PerformanceMetrics model."""

    def test_metrics_creation(self):
        """Test creating performance metrics."""
        metrics = PerformanceMetrics(
            scope_type="agent",
            scope_id="research_agent"
        )

        assert metrics.metrics_id is not None
        assert metrics.total_executions == 0
        assert metrics.success_rate == 0.0

    def test_record_execution_success(self):
        """Test recording successful execution."""
        metrics = PerformanceMetrics(
            scope_type="agent",
            scope_id="research_agent"
        )

        outcome = TaskOutcome(
            category=OutcomeCategory.SUCCESS,
            success=True,
            duration_seconds=5.0,
            quality_score=0.8
        )

        metrics.record_execution(outcome)

        assert metrics.total_executions == 1
        assert metrics.successful_executions == 1
        assert metrics.failed_executions == 0
        assert metrics.success_rate == 1.0
        assert metrics.avg_quality_score == 0.8

    def test_record_execution_failure(self):
        """Test recording failed execution."""
        metrics = PerformanceMetrics(
            scope_type="agent",
            scope_id="research_agent"
        )

        outcome = TaskOutcome(
            category=OutcomeCategory.FAILURE,
            success=False,
            duration_seconds=3.0,
            quality_score=0.2
        )

        metrics.record_execution(outcome)

        assert metrics.total_executions == 1
        assert metrics.successful_executions == 0
        assert metrics.failed_executions == 1
        assert metrics.success_rate == 0.0
        assert metrics.avg_quality_score == 0.2

    def test_record_mixed_executions(self):
        """Test recording mix of successes and failures."""
        metrics = PerformanceMetrics(
            scope_type="agent",
            scope_id="research_agent"
        )

        # 3 successes
        for i in range(3):
            outcome = TaskOutcome(
                category=OutcomeCategory.SUCCESS,
                success=True,
                duration_seconds=5.0,
                quality_score=0.7
            )
            metrics.record_execution(outcome)

        # 2 failures
        for i in range(2):
            outcome = TaskOutcome(
                category=OutcomeCategory.FAILURE,
                success=False,
                duration_seconds=3.0,
                quality_score=0.3
            )
            metrics.record_execution(outcome)

        assert metrics.total_executions == 5
        assert metrics.successful_executions == 3
        assert metrics.failed_executions == 2
        assert metrics.success_rate == 0.6

    def test_timing_stats(self):
        """Test timing statistics."""
        metrics = PerformanceMetrics(
            scope_type="task_type",
            scope_id="investigation"
        )

        durations = [2.0, 5.0, 8.0, 10.0]
        for duration in durations:
            outcome = TaskOutcome(
                category=OutcomeCategory.SUCCESS,
                success=True,
                duration_seconds=duration
            )
            metrics.record_execution(outcome)

        assert metrics.avg_duration_seconds == sum(durations) / len(durations)
        assert metrics.min_duration_seconds == 2.0
        assert metrics.max_duration_seconds == 10.0


# ============================================================================
# ImprovementSuggestion Tests
# ============================================================================

class TestImprovementSuggestion:
    """Test ImprovementSuggestion model."""

    def test_suggestion_creation(self):
        """Test creating an improvement suggestion."""
        suggestion = ImprovementSuggestion(
            improvement_type=ImprovementType.PERFORMANCE,
            priority="high",
            target_type="agent",
            target_id="research_agent",
            title="Slow execution",
            description="Agent takes too long",
            current_state="Average: 120s",
            proposed_state="Optimize to < 60s",
            expected_impact="Faster responses",
            implementation_complexity="moderate"
        )

        assert suggestion.suggestion_id is not None
        assert suggestion.improvement_type == ImprovementType.PERFORMANCE
        assert suggestion.priority == "high"
        assert suggestion.status == "pending"

    def test_suggestion_with_evidence(self):
        """Test suggestion with supporting evidence."""
        suggestion = ImprovementSuggestion(
            improvement_type=ImprovementType.RELIABILITY,
            priority="critical",
            target_type="agent",
            target_id="api_agent",
            title="High failure rate",
            description="Agent fails frequently",
            current_state="50% failure rate",
            proposed_state="Improve error handling",
            evidence=["Failed 10 of last 20 executions", "User complaints increased"],
            expected_impact="Higher reliability",
            implementation_complexity="complex"
        )

        assert len(suggestion.evidence) == 2


# ============================================================================
# ModelFeedback Tests
# ============================================================================

class TestModelFeedback:
    """Test ModelFeedback model."""

    def test_feedback_creation(self):
        """Test creating feedback."""
        feedback = ModelFeedback(
            agent_id="research_agent",
            feedback_type=FeedbackType.POSITIVE,
            rating=0.9,
            comment="Great work!",
            source_type="user"
        )

        assert feedback.feedback_id is not None
        assert feedback.feedback_type == FeedbackType.POSITIVE
        assert feedback.rating == 0.9

    def test_negative_feedback(self):
        """Test negative feedback."""
        feedback = ModelFeedback(
            agent_id="workflow_agent",
            feedback_type=FeedbackType.NEGATIVE,
            rating=0.2,
            comment="Too slow",
            source_type="user"
        )

        assert feedback.feedback_type == FeedbackType.NEGATIVE
        assert feedback.rating == 0.2

    def test_correction_feedback(self):
        """Test correction feedback."""
        feedback = ModelFeedback(
            agent_id="code_agent",
            feedback_type=FeedbackType.CORRECTION,
            comment="Used wrong syntax",
            task_id="task_123",
            source_type="user"
        )

        assert feedback.feedback_type == FeedbackType.CORRECTION


# ============================================================================
# ObservationRecord Tests
# ============================================================================

class TestObservationRecord:
    """Test ObservationRecord model."""

    def test_observation_creation(self):
        """Test creating an observation."""
        observation = ObservationRecord(
            agent_id="research_agent",
            behavior_type="task_execution",
            observation="Agent consistently succeeds on research tasks",
            pattern_type="success_pattern",
            confidence=0.9,
            source="system"
        )

        assert observation.observation_id is not None
        assert observation.pattern_type == "success_pattern"
        assert observation.confidence == 0.9


# ============================================================================
# LearningEngine Tests
# ============================================================================

class TestLearningEngine:
    """Test LearningEngine."""

    @pytest.mark.asyncio
    async def test_engine_start_stop(self, state_store):
        """Test starting and stopping the engine."""
        engine = LearningEngine(state_store=state_store)

        assert engine._running is False

        await engine.start()
        assert engine._running is True

        await engine.stop()
        assert engine._running is False

    @pytest.mark.asyncio
    async def test_record_execution_outcome(self, learning_engine):
        """Test recording execution outcomes."""
        execution = ExecutionResult(
            task_id="task_123",
            status=ExecutionStatus.COMPLETED,
            success=True,
            duration_seconds=10.0,
            agent_ids=["research_agent"],
            tools_used=["web_search"],
            workspace_id="ws_123"
        )

        outcome = await learning_engine.record_execution(
            execution=execution,
            quality_score=0.8,
            user_satisfaction=0.9,
            cost_estimate=0.5
        )

        assert outcome.task_id == "task_123"
        assert outcome.success is True
        assert outcome.quality_score == 0.8
        assert outcome.user_satisfaction == 0.9

    @pytest.mark.asyncio
    async def test_collect_feedback(self, learning_engine):
        """Test collecting feedback."""
        feedback = await learning_engine.collect_feedback(
            feedback_type=FeedbackType.POSITIVE,
            rating=0.9,
            comment="Excellent work",
            agent_id="research_agent",
            source_type="user"
        )

        assert feedback.feedback_id is not None
        assert feedback.feedback_type == FeedbackType.POSITIVE
        assert feedback.rating == 0.9

    @pytest.mark.asyncio
    async def test_feedback_generates_observations(self, learning_engine):
        """Test that feedback generates observations."""
        # Low rating should generate failure pattern
        await learning_engine.collect_feedback(
            feedback_type=FeedbackType.NEGATIVE,
            rating=0.2,
            comment="Not good",
            agent_id="test_agent"
        )

        # Should have created observation
        observations = [o for o in learning_engine._observations if o.agent_id == "test_agent"]
        assert len(observations) > 0
        assert observations[0].pattern_type == "failure_pattern"

    @pytest.mark.asyncio
    async def test_detect_patterns_failure_rate(self, learning_engine):
        """Test pattern detection for high failure rates."""
        # Create some outcomes with high failure rate for an agent
        agent_id = "problematic_agent"
        for i in range(10):
            execution = ExecutionResult(
                task_id=f"task_{i}",
                status=ExecutionStatus.COMPLETED,
                success=(i < 3),  # 3 successes, 7 failures
                duration_seconds=5.0,
                agent_ids=[agent_id]
            )

            await learning_engine.record_execution(execution=execution)

        # Detect patterns
        suggestions = await learning_engine.detect_patterns()

        # Should suggest improvement for problematic agent
        agent_suggestions = [
            s for s in suggestions
            if s.target_id == agent_id and s.improvement_type == ImprovementType.RELIABILITY
        ]

        assert len(agent_suggestions) > 0

    @pytest.mark.asyncio
    async def test_detect_patterns_slow_tasks(self, learning_engine):
        """Test pattern detection for slow tasks."""
        # Create some slow task outcomes
        task_type = "heavy_analysis"
        for duration in [30, 45, 60, 90, 120]:  # All > 60s
            outcome = TaskOutcome(
                category=OutcomeCategory.SUCCESS,
                success=True,
                duration_seconds=duration,
                task_type=task_type
            )
            learning_engine._outcomes.append(outcome)

        suggestions = await learning_engine.detect_patterns()

        # Should suggest performance improvement
        perf_suggestions = [
            s for s in suggestions
            if s.improvement_type == ImprovementType.PERFORMANCE
        ]

        assert len(perf_suggestions) > 0

    @pytest.mark.asyncio
    async def test_generate_suggestions(self, learning_engine):
        """Test generating improvement suggestions."""
        # Add some outcomes
        for i in range(5):
            execution = ExecutionResult(
                task_id=f"task_{i}",
                status=ExecutionStatus.COMPLETED,
                success=True,
                duration_seconds=10.0,
                agent_ids=["test_agent"]
            )
            await learning_engine.record_execution(execution=execution)

        # Generate suggestions
        suggestions = await learning_engine.generate_suggestions()

        assert isinstance(suggestions, list)

    @pytest.mark.asyncio
    async def test_filter_suggestions_by_priority(self, learning_engine):
        """Test filtering suggestions by priority."""
        # Create suggestions with different priorities
        suggestion1 = ImprovementSuggestion(
            improvement_type=ImprovementType.PERFORMANCE,
            priority="low",
            target_type="system",
            title="Minor optimization",
            description="Small performance tweak",
            current_state="Current state",
            proposed_state="Improved state",
            expected_impact="Minor improvement",
            implementation_complexity="simple"
        )

        suggestion2 = ImprovementSuggestion(
            improvement_type=ImprovementType.RELIABILITY,
            priority="high",
            target_type="agent",
            target_id="test_agent",
            title="Critical fix",
            description="Fix critical bug",
            current_state="Buggy state",
            proposed_state="Fixed state",
            expected_impact="Major reliability improvement",
            implementation_complexity="moderate"
        )

        learning_engine._suggestions.extend([suggestion1, suggestion2])

        # Filter by priority
        high_priority = await learning_engine.generate_suggestions(min_priority="medium")

        assert suggestion2.title in [s.title for s in high_priority]
        assert suggestion1.title not in [s.title for s in high_priority]

    @pytest.mark.asyncio
    async def test_implement_suggestion(self, learning_engine):
        """Test marking a suggestion as implemented."""
        suggestion = ImprovementSuggestion(
            improvement_type=ImprovementType.PERFORMANCE,
            priority="medium",
            target_type="system",
            title="Test suggestion",
            description="Test description",
            current_state="Current",
            proposed_state="Proposed",
            expected_impact="Test impact",
            implementation_complexity="simple"
        )

        learning_engine._suggestions.append(suggestion)

        result = await learning_engine.implement_suggestion(
            suggestion.suggestion_id,
            implemented_by="admin"
        )

        assert result is True
        assert suggestion.status == "implemented"

    def test_get_top_performers(self, learning_engine):
        """Test getting top performing agents."""
        # Add some metrics
        metrics1 = PerformanceMetrics(
            scope_type="agent",
            scope_id="agent_a"
        )
        metrics1.total_executions = 10
        metrics1.successful_executions = 9  # 90% success

        metrics2 = PerformanceMetrics(
            scope_type="agent",
            scope_id="agent_b"
        )
        metrics2.total_executions = 10
        metrics2.successful_executions = 7  # 70% success

        learning_engine._metrics["agent:agent_a"] = metrics1
        learning_engine._metrics["agent:agent_b"] = metrics2

        top_performers = learning_engine.get_top_performers("agent")

        assert len(top_performers) >= 2
        # agent_a should be first (higher success rate)
        assert top_performers[0][0] == "agent_a"
        assert top_performers[0][1] >= top_performers[1][1]

    def test_get_underperformers(self, learning_engine):
        """Test getting underperforming agents."""
        # Add some metrics
        metrics1 = PerformanceMetrics(
            scope_type="agent",
            scope_id="agent_a"
        )
        metrics1.total_executions = 10
        metrics1.successful_executions = 8  # 80% success

        metrics2 = PerformanceMetrics(
            scope_type="agent",
            scope_id="agent_b"
        )
        metrics2.total_executions = 10
        metrics2.successful_executions = 4  # 40% success

        metrics3 = PerformanceMetrics(
            scope_type="agent",
            scope_id="agent_c"
        )
        metrics3.total_executions = 2  # Not enough data
        metrics3.successful_executions = 1

        learning_engine._metrics["agent:agent_a"] = metrics1
        learning_engine._metrics["agent:agent_b"] = metrics2
        learning_engine._metrics["agent:agent_c"] = metrics3

        underperformers = learning_engine.get_underperformers("agent", threshold=0.7)

        # agent_b is below threshold
        assert ("agent_b", 0.4) in underperformers
        # agent_a is above threshold
        assert ("agent_a", 0.8) not in underperformers
        # agent_c doesn't have enough data
        assert ("agent_c", 0.5) not in underperformers

    def test_get_metrics(self, learning_engine):
        """Test getting performance metrics."""
        # Create a metric
        metrics = PerformanceMetrics(
            scope_type="agent",
            scope_id="test_agent"
        )
        learning_engine._metrics["agent:test_agent"] = metrics

        # Get all metrics
        all_metrics = learning_engine.get_metrics()
        assert len(all_metrics) >= 1

        # Get by scope type
        agent_metrics = learning_engine.get_metrics(scope_type="agent")
        assert len(agent_metrics) >= 1

        # Get by scope ID
        specific_metrics = learning_engine.get_metrics(
            scope_type="agent",
            scope_id="test_agent"
        )
        assert len(specific_metrics) == 1


# ============================================================================
# Integration Tests
# ============================================================================

class TestPhase7Integration:
    """Integration tests for Phase 7."""

    @pytest.mark.asyncio
    async def test_learning_feedback_loop(self, learning_engine):
        """Test the complete learning and feedback loop."""
        # 1. Execute task and record outcome
        execution = ExecutionResult(
            task_id="learning_task_1",
            status=ExecutionStatus.COMPLETED,
            success=True,
            duration_seconds=15.0,
            agent_ids=["research_agent"],
            tools_used=["web_search"]
        )

        outcome = await learning_engine.record_execution(
            execution=execution,
            quality_score=0.7
        )

        # 2. Collect user feedback
        feedback = await learning_engine.collect_feedback(
            feedback_type=FeedbackType.POSITIVE,
            rating=0.8,
            comment="Good result",
            agent_id="research_agent",
            task_id="learning_task_1"
        )

        # 3. Get summary
        summary = learning_engine.get_learning_summary()

        assert summary["total_outcomes"] >= 1
        assert summary["total_feedback"] >= 1

    @pytest.mark.asyncio
    async def test_pattern_detection_creates_suggestions(self, learning_engine):
        """Test that pattern detection creates actionable suggestions."""
        # Create outcomes showing a pattern
        agent_id = "struggling_agent"
        for i in range(8):
            execution = ExecutionResult(
                task_id=f"task_{i}",
                status=ExecutionStatus.FAILED,
                success=False,
                duration_seconds=5.0,
                agent_ids=[agent_id],
                error=f"Error {i}"
            )
            await learning_engine.record_execution(execution=execution)

        # Generate suggestions based on patterns
        suggestions = await learning_engine.generate_suggestions()

        # Should have detected the high failure rate
        reliability_suggestions = [
            s for s in suggestions
            if s.improvement_type == ImprovementType.RELIABILITY
        ]

        assert len(reliability_suggestions) > 0

    @pytest.mark.asyncio
    async def test_learning_summary_comprehensive(self, learning_engine):
        """Test that learning summary is comprehensive."""
        # Add some data
        execution = ExecutionResult(
            task_id="test_task",
            status=ExecutionStatus.COMPLETED,
            success=True,
            duration_seconds=10.0,
            agent_ids=["test_agent"]
        )
        await learning_engine.record_execution(execution=execution)

        await learning_engine.collect_feedback(
            feedback_type=FeedbackType.POSITIVE,
            rating=0.9,
            agent_id="test_agent"
        )

        suggestion = ImprovementSuggestion(
            improvement_type=ImprovementType.PERFORMANCE,
            priority="low",
            target_type="system",
            title="Test suggestion",
            description="Test description",
            current_state="Current",
            proposed_state="Proposed",
            expected_impact="Test impact",
            implementation_complexity="simple"
        )
        learning_engine._suggestions.append(suggestion)

        summary = learning_engine.get_learning_summary()

        # Check all fields
        assert "total_outcomes" in summary
        assert "success_rate" in summary
        assert "total_suggestions" in summary
        assert "total_feedback" in summary
        assert "total_observations" in summary
        assert "tracked_metrics" in summary
        assert "is_running" in summary
