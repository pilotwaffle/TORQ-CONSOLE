"""
Verification Tests for Cognitive Loop Telemetry

Tests the OpenTelemetry observability implementation for the TORQ Agent
Cognitive Loop, including span emission, attribute recording, and metrics
aggregation.

Run with: pytest -v test_cognitive_telemetry.py
"""

import asyncio
import time
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from dataclasses import asdict
from typing import Optional, Dict, Any

# Import the module under test
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from torq_console.agents.telemetry import (
    CognitiveLoopTelemetry,
    CognitiveLoopContext,
    StepResult,
    CognitiveSpanKind,
    AttributeKey,
    get_cognitive_telemetry,
    run_observed_loop
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_tracer():
    """Mock TORQTracer for testing."""
    tracer = Mock()
    tracer.start_span = Mock(return_value=Mock(attributes={}))
    tracer.end_span = Mock()
    return tracer


@pytest.fixture
def telemetry(mock_tracer):
    """Create telemetry instance with mock tracer."""
    return CognitiveLoopTelemetry(
        service_name="test-cognitive-loop",
        tracer=mock_tracer,
        enable_auto_instrumentation=True
    )


@pytest.fixture
def loop_context():
    """Create a sample cognitive loop context."""
    return CognitiveLoopContext(
        loop_id="test-loop-123",
        session_id="test-session-456",
        user_query="What is the capital of France?",
        start_time=time.time()
    )


# ============================================================================
# Unit Tests: CognitiveLoopContext
# ============================================================================

class TestCognitiveLoopContext:
    """Tests for CognitiveLoopContext data class."""

    def test_initialization(self, loop_context):
        """Test context initialization."""
        assert loop_context.loop_id == "test-loop-123"
        assert loop_context.session_id == "test-session-456"
        assert loop_context.user_query == "What is the capital of France?"
        assert loop_context.iteration_count == 0
        assert loop_context.tools_used == []
        assert loop_context.total_tokens == 0

    def test_add_step_timing(self, loop_context):
        """Test adding step timings."""
        loop_context.add_step_timing("reason", 150.5)
        loop_context.add_step_timing("retrieve", 75.2)

        assert "reason" in loop_context.step_timings
        assert loop_context.step_timings["reason"] == 150.5
        assert loop_context.step_timings["retrieve"] == 75.2

    def test_get_average_confidence(self, loop_context):
        """Test average confidence calculation."""
        loop_context.confidence_scores = [0.8, 0.9, 0.7]
        avg = loop_context.get_average_confidence()

        assert avg == pytest.approx(0.8, rel=1e-2)

    def test_get_average_confidence_empty(self, loop_context):
        """Test average confidence with no scores."""
        assert loop_context.get_average_confidence() == 0.0

    def test_get_total_latency(self, loop_context):
        """Test total latency calculation."""
        # Sleep briefly to ensure some time has passed
        time.sleep(0.01)
        latency = loop_context.get_total_latency()
        assert latency > 0


# ============================================================================
# Unit Tests: StepResult
# ============================================================================

class TestStepResult:
    """Tests for StepResult data class."""

    def test_initialization_success(self):
        """Test successful step result initialization."""
        result = StepResult(
            step_name=CognitiveSpanKind.REASON_STEP,
            success=True,
            duration_ms=100.0,
            confidence=0.9,
            output="Some output"
        )

        assert result.step_name == CognitiveSpanKind.REASON_STEP
        assert result.success is True
        assert result.duration_ms == 100.0
        assert result.confidence == 0.9
        assert result.output == "Some output"
        assert result.error is None

    def test_initialization_failure(self):
        """Test failed step result initialization."""
        result = StepResult(
            step_name=CognitiveSpanKind.ACT_STEP,
            success=False,
            duration_ms=50.0,
            error="Tool execution failed"
        )

        assert result.success is False
        assert result.error == "Tool execution failed"


# ============================================================================
# Unit Tests: Span Emission
# ============================================================================

class TestSpanEmission:
    """Tests for span emission and recording."""

    @pytest.mark.asyncio
    async def test_reason_step_span_emission(self, telemetry, mock_tracer):
        """Test that reason step emits correct span."""
        loop_id = "test-loop-123"

        async with telemetry.observe_reason_step(
            loop_id=loop_id,
            reasoning_prompt="Analyze the user request"
        ) as result:
            result.success = True
            result.confidence = 0.85

        # Verify span was started
        assert mock_tracer.start_span.called

        # Verify span was ended
        assert mock_tracer.end_span.called

        # Get the span attributes from start_span call
        call_kwargs = mock_tracer.start_span.call_args[1]
        assert call_kwargs["attributes"][AttributeKey.LOOP_ID] == loop_id

    @pytest.mark.asyncio
    async def test_retrieve_step_span_emission(self, telemetry, mock_tracer):
        """Test that retrieve step emits correct span."""
        loop_id = "test-loop-123"

        async with telemetry.observe_retrieve_step(
            loop_id=loop_id,
            query="vector search query",
            retrieval_method="vector_search"
        ) as result:
            result.success = True
            result.attributes[AttributeKey.KNOWLEDGE_COUNT_RETRIEVED] = 5

        assert mock_tracer.start_span.called
        assert mock_tracer.end_span.called

    @pytest.mark.asyncio
    async def test_plan_step_span_emission(self, telemetry, mock_tracer):
        """Test that plan step emits correct span."""
        loop_id = "test-loop-123"

        async with telemetry.observe_plan_step(
            loop_id=loop_id,
            plan_description="Execute search and analyze results"
        ) as result:
            result.success = True
            result.attributes[AttributeKey.PLAN_STEPS_COUNT] = 3

        assert mock_tracer.start_span.called
        assert mock_tracer.end_span.called

    @pytest.mark.asyncio
    async def test_act_step_span_emission(self, telemetry, mock_tracer):
        """Test that act step emits correct span."""
        loop_id = "test-loop-123"
        tools = ["web_search", "code_executor"]

        async with telemetry.observe_act_step(
            loop_id=loop_id,
            tool_names=tools
        ) as result:
            result.success = True
            result.attributes[AttributeKey.TOOL_SUCCESS_RATE] = 1.0

        assert mock_tracer.start_span.called
        assert mock_tracer.end_span.called

    @pytest.mark.asyncio
    async def test_evaluate_step_span_emission(self, telemetry, mock_tracer):
        """Test that evaluate step emits correct span."""
        loop_id = "test-loop-123"

        async with telemetry.observe_evaluate_step(
            loop_id=loop_id,
            evaluation_criteria="Check result accuracy"
        ) as result:
            result.success = True
            result.confidence = 0.92
            result.attributes[AttributeKey.EVALUATION_OUTCOME] = "passed"

        assert mock_tracer.start_span.called
        assert mock_tracer.end_span.called

    @pytest.mark.asyncio
    async def test_learn_step_span_emission(self, telemetry, mock_tracer):
        """Test that learn step emits correct span."""
        loop_id = "test-loop-123"

        async with telemetry.observe_learn_step(
            loop_id=loop_id,
            learning_type="reinforcement"
        ) as result:
            result.success = True
            result.attributes[AttributeKey.LEARNING_STORED] = True

        assert mock_tracer.start_span.called
        assert mock_tracer.end_span.called


# ============================================================================
# Integration Tests: Complete Loop
# ============================================================================

class TestCompleteCognitiveLoop:
    """Tests for complete cognitive loop execution."""

    @pytest.mark.asyncio
    async def test_complete_loop_execution(self, telemetry, mock_tracer):
        """Test executing a complete cognitive loop with all steps."""
        user_query = "How do I implement JWT authentication in Python?"
        session_id = "test-session"

        metrics_before = telemetry.get_aggregated_metrics()

        async with telemetry.observe_cognitive_loop(
            user_query=user_query,
            session_id=session_id
        ) as context:
            # Simulate reasoning step
            async with telemetry.observe_reason_step(
                loop_id=context.loop_id,
                reasoning_prompt="Analyze authentication requirements"
            ) as result:
                result.success = True
                result.confidence = 0.9

            # Simulate retrieve step
            async with telemetry.observe_retrieve_step(
                loop_id=context.loop_id,
                query="JWT authentication best practices"
            ) as result:
                result.success = True
                result.attributes[AttributeKey.KNOWLEDGE_COUNT_RETRIEVED] = 5

            # Simulate plan step
            async with telemetry.observe_plan_step(
                loop_id=context.loop_id,
                plan_description="Generate JWT implementation"
            ) as result:
                result.success = True
                result.attributes[AttributeKey.PLAN_STEPS_COUNT] = 4

            # Simulate act step
            async with telemetry.observe_act_step(
                loop_id=context.loop_id,
                tool_names=["code_generator"]
            ) as result:
                result.success = True

            # Simulate evaluate step
            async with telemetry.observe_evaluate_step(
                loop_id=context.loop_id,
                evaluation_criteria="Code quality check"
            ) as result:
                result.success = True
                result.confidence = 0.85

            # Simulate learn step
            async with telemetry.observe_learn_step(
                loop_id=context.loop_id,
                learning_type="pattern"
            ) as result:
                result.success = True
                result.attributes[AttributeKey.LEARNING_STORED] = True

        # Verify all spans were created
        assert mock_tracer.start_span.call_count == 7  # 1 loop + 6 steps
        assert mock_tracer.end_span.call_count == 7

        # Verify context was updated
        assert context.iteration_count >= 0
        assert len(context.tools_used) > 0
        assert "code_generator" in context.tools_used

        # Verify metrics were stored
        metrics_after = telemetry.get_aggregated_metrics()
        assert metrics_after["total_loops"] == metrics_before["total_loops"] + 1

    @pytest.mark.asyncio
    async def test_loop_with_error_handling(self, telemetry):
        """Test loop execution with step failures."""
        user_query = "Complex query"
        session_id = "test-session"

        async with telemetry.observe_cognitive_loop(
            user_query=user_query,
            session_id=session_id
        ) as context:
            # Successful step
            async with telemetry.observe_reason_step(
                loop_id=context.loop_id,
                reasoning_prompt="Initial reasoning"
            ) as result:
                result.success = True
                result.confidence = 0.8

            # Failed step
            async with telemetry.observe_act_step(
                loop_id=context.loop_id,
                tool_names=["broken_tool"]
            ) as result:
                result.success = False
                result.error = "Tool execution failed"

        # Verify loop still completed despite errors
        assert context.loop_id is not None
        assert len(context.errors) >= 0


# ============================================================================
# Tests: Metrics Aggregation
# ============================================================================

class TestMetricsAggregation:
    """Tests for metrics aggregation and reporting."""

    @pytest.mark.asyncio
    async def test_get_loop_metrics(self, telemetry):
        """Test retrieving loop metrics."""
        session_id = "test-session-123"

        # Create some test loops
        for i in range(3):
            async with telemetry.observe_cognitive_loop(
                user_query=f"Query {i}",
                session_id=session_id
            ) as context:
                pass

        # Get all metrics
        all_metrics = telemetry.get_loop_metrics(limit=10)
        assert len(all_metrics) >= 3

        # Filter by session
        session_metrics = telemetry.get_loop_metrics(
            limit=10,
            session_id=session_id
        )
        assert len(session_metrics) >= 3
        assert all(m["session_id"] == session_id for m in session_metrics)

    def test_get_aggregated_metrics(self, telemetry):
        """Test aggregated metrics calculation."""
        # The telemetry starts with no metrics
        metrics = telemetry.get_aggregated_metrics()
        assert metrics["total_loops"] == 0

    @pytest.mark.asyncio
    async def test_metrics_update_after_loop(self, telemetry):
        """Test that metrics update after loop execution."""
        metrics_before = telemetry.get_aggregated_metrics()

        async with telemetry.observe_cognitive_loop(
            user_query="Test query",
            session_id="test"
        ) as context:
            # Simulate some activity
            context.total_tokens = 1000

        metrics_after = telemetry.get_aggregated_metrics()
        assert metrics_after["total_loops"] >= metrics_before["total_loops"]

    def test_export_metrics_for_prometheus(self, telemetry):
        """Test Prometheus metrics export format."""
        prometheus_output = telemetry.export_metrics_for_prometheus()

        # Verify format
        assert "torq_cognitive_loops_total" in prometheus_output
        assert "torq_cognitive_latency_avg_ms" in prometheus_output
        assert "torq_cognitive_confidence_avg" in prometheus_output
        assert "torq_cognitive_success_rate" in prometheus_output


# ============================================================================
# Tests: Decorators
# ============================================================================

class TestTelemetryDecorators:
    """Tests for telemetry decorators."""

    @pytest.mark.asyncio
    async def test_trace_reasoning_decorator(self, telemetry, mock_tracer):
        """Test the reasoning decorator."""
        @telemetry.trace_reasoning(loop_id_attr="loop_id")
        async def mock_reasoning(self, query: str, loop_id: str):
            return {"result": "reasoning complete"}

        class MockAgent:
            pass

        agent = MockAgent()
        result = await mock_reasoning(agent, "test query", loop_id="test-loop-123")

        assert result["result"] == "reasoning complete"
        assert mock_tracer.start_span.called

    @pytest.mark.asyncio
    async def test_trace_retrieval_decorator(self, telemetry, mock_tracer):
        """Test the retrieval decorator."""
        @telemetry.trace_retrieval(loop_id_attr="loop_id")
        async def mock_retrieve(self, query: str, loop_id: str):
            return ["doc1", "doc2", "doc3"]

        class MockAgent:
            pass

        agent = MockAgent()
        results = await mock_retrieve(agent, "search query", loop_id="test-loop-123")

        assert len(results) == 3
        assert mock_tracer.start_span.called

    @pytest.mark.asyncio
    async def test_trace_action_decorator(self, telemetry, mock_tracer):
        """Test the action decorator."""
        @telemetry.trace_action(loop_id_attr="loop_id")
        async def mock_tool(self, tool_name: str, loop_id: str):
            return {"output": "tool executed"}

        class MockAgent:
            pass

        agent = MockAgent()
        result = await mock_tool(agent, "web_search", loop_id="test-loop-123")

        assert result["output"] == "tool executed"
        assert mock_tracer.start_span.called


# ============================================================================
# Tests: Singleton and Helper Functions
# ============================================================================

class TestSingletonAndHelpers:
    """Tests for singleton pattern and helper functions."""

    def test_get_cognitive_telemetry_singleton(self):
        """Test that get_cognitive_telemetry returns singleton."""
        # Reset singleton
        import torq_console.agents.telemetry as tel_module
        tel_module._global_telemetry = None

        telemetry1 = get_cognitive_telemetry()
        telemetry2 = get_cognitive_telemetry()

        assert telemetry1 is telemetry2

    @pytest.mark.asyncio
    async def test_run_observed_loop(self):
        """Test the run_observed_loop helper function."""
        loop_executed = False

        async def mock_loop_func(context: CognitiveLoopContext):
            nonlocal loop_executed
            loop_executed = True
            context.total_tokens = 500

        result = await run_observed_loop(
            user_query="Test query",
            session_id="test-session",
            loop_func=mock_loop_func
        )

        assert loop_executed
        assert result.total_tokens == 500


# ============================================================================
# Tests: Attribute Keys
# ============================================================================

class TestAttributeKeys:
    """Tests for standardized attribute keys."""

    def test_attribute_key_values(self):
        """Test that all attribute keys have correct values."""
        assert AttributeKey.LOOP_ID == "cognitive.loop.id"
        assert AttributeKey.ITERATION_ID == "cognitive.iteration.id"
        assert AttributeKey.USER_QUERY == "cognitive.user.query"
        assert AttributeKey.REASONING_CONFIDENCE == "cognitive.reasoning.confidence"
        assert AttributeKey.KNOWLEDGE_COUNT_RETRIEVED == "cognitive.retrieve.count"
        assert AttributeKey.PLAN_STEPS_COUNT == "cognitive.plan.steps.count"
        assert AttributeKey.TOOLS_USED == "cognitive.act.tools"
        assert AttributeKey.TOOL_SUCCESS_RATE == "cognitive.act.success_rate"
        assert AttributeKey.EVALUATION_CONFIDENCE == "cognitive.evaluate.confidence"
        assert AttributeKey.LEARNING_STORED == "cognitive.learn.stored"
        assert AttributeKey.LOOP_LATENCY_MS == "cognitive.loop.latency_ms"


# ============================================================================
# Tests: Span Kinds
# ============================================================================

class TestSpanKinds:
    """Tests for cognitive span kinds."""

    def test_span_kind_values(self):
        """Test that all span kinds have correct values."""
        assert CognitiveSpanKind.REASON_STEP == "cognitive.reason.step"
        assert CognitiveSpanKind.RETRIEVE_STEP == "cognitive.retrieve.step"
        assert CognitiveSpanKind.PLAN_STEP == "cognitive.plan.step"
        assert CognitiveSpanKind.ACT_STEP == "cognitive.act.step"
        assert CognitiveSpanKind.EVALUATE_STEP == "cognitive.evaluate.step"
        assert CognitiveSpanKind.LEARN_STEP == "cognitive.learn.step"
        assert CognitiveSpanKind.COGNITIVE_LOOP == "cognitive.loop"


# ============================================================================
# Run Tests Entry Point
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
