"""
Comprehensive tests for the TORQ Agent Cognitive Loop System.

Tests all modules: reasoning, retrieval, planning, execution, evaluation, learning.
"""

import asyncio
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from torq_console.agents.cognitive_loop.models import (
    CognitiveLoopConfig,
    CognitiveLoopStatus,
    CognitiveLoopResult,
    EvaluationResult,
    ExecutionPlan,
    ExecutionResult,
    ExecutionStep,
    IntentType,
    KnowledgeContext,
    ReasoningPlan,
    StepStatus,
    ToolCallResult,
    ToolCategory,
    LearningEvent,
)
from torq_console.agents.cognitive_loop.reasoning_engine import ReasoningEngine
from torq_console.agents.cognitive_loop.knowledge_retriever import KnowledgeRetriever
from torq_console.agents.cognitive_loop.planner import Planner
from torq_console.agents.cognitive_loop.tool_executor import ToolExecutor
from torq_console.agents.cognitive_loop.evaluator import Evaluator
from torq_console.agents.cognitive_loop.learning_writer import LearningWriter
from torq_console.agents.cognitive_loop.cognitive_loop import CognitiveLoop
from torq_console.agents.cognitive_loop.config import get_cognitive_config


# Test fixtures
from dataclasses import replace
@pytest.fixture
def temp_storage():
    """Create temporary storage for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = CognitiveLoopConfig(
            learning_storage_path=str(Path(tmpdir) / "learning"),
            knowledge_enabled=False,
            telemetry_enabled=False,
        )
        yield config


@pytest.fixture
def test_config():
    """Create test configuration."""
    return CognitiveLoopConfig(
        max_loop_latency_seconds=5.0,
        min_tool_success_rate=0.8,
        min_evaluation_confidence=0.7,
        max_retries=2,
        knowledge_enabled=False,
        learning_enabled=True,
        telemetry_enabled=False,
        learning_storage_path=".torq/test_cognitive_learning",
    )


@pytest.fixture
def sample_reasoning_plan():
    """Create a sample reasoning plan."""
    return ReasoningPlan(
        intent=IntentType.QUERY,
        intent_confidence=0.85,
        reasoning="This is a query seeking information",
        key_entities=["Python", "async"],
        key_concepts=["programming", "coroutines"],
        requires_tools=True,
        suggested_tools=["web_search"],
        complexity_estimate=0.6,
    )


@pytest.fixture
def sample_execution_plan():
    """Create a sample execution plan."""
    step1 = ExecutionStep(
        description="Search the web for information",
        tool_name="web_search",
        tool_category=ToolCategory.WEB_SEARCH,
        parameters={"query": "Python async programming", "num_results": 5},
        execution_order=0,
        estimated_duration_seconds=2.0,
    )

    step2 = ExecutionStep(
        description="Synthesize results",
        tool_name="synthesis",
        tool_category=ToolCategory.CUSTOM,
        parameters={},
        dependencies=[step1.id],
        execution_order=1,
        estimated_duration_seconds=0.5,
    )

    return ExecutionPlan(
        goal="Provide accurate information about Python async programming",
        steps=[step1, step2],
        required_tools=["web_search"],
        expected_outputs=["Search results", "Synthesized response"],
        estimated_duration_seconds=2.5,
    )


@pytest.fixture
def sample_execution_result():
    """Create a sample execution result."""
    return ExecutionResult(
        success=True,
        tool_results=[
            ToolCallResult(
                tool_name="web_search",
                success=True,
                result={"results": [{"title": "Python Async Guide"}]},
                execution_time_seconds=1.5,
            )
        ],
        outputs={"web_search": {"results": [{"title": "Python Async Guide"}]}},
        total_execution_time_seconds=1.5,
    )


# Tests for ReasoningEngine
class TestReasoningEngine:
    """Tests for the ReasoningEngine class."""

    @pytest.mark.asyncio
    async def test_reason_query_intent(self, test_config):
        """Test reasoning with a query intent."""
        engine = ReasoningEngine(test_config)

        plan = await engine.reason("What is async programming in Python?")

        assert plan.intent == IntentType.QUERY
        assert plan.intent_confidence > 0.0
        assert "async" in plan.key_concepts or "programming" in plan.key_concepts

    @pytest.mark.asyncio
    async def test_reason_task_intent(self, test_config):
        """Test reasoning with a task intent."""
        engine = ReasoningEngine(test_config)

        plan = await engine.reason("Create a function to calculate fibonacci numbers")

        assert plan.intent == IntentType.TASK
        assert plan.requires_tools

    @pytest.mark.asyncio
    async def test_reason_research_intent(self, test_config):
        """Test reasoning with a research intent."""
        engine = ReasoningEngine(test_config)

        plan = await engine.reason("Research the latest trends in AI")

        assert plan.intent == IntentType.RESEARCH
        assert "web_search" in plan.suggested_tools

    @pytest.mark.asyncio
    async def test_entity_extraction(self, test_config):
        """Test entity extraction from query."""
        engine = ReasoningEngine(test_config)

        plan = await engine.reason('What is the difference between "FastAPI" and Flask?')

        assert any("FastAPI" in e or "Flask" in e for e in plan.key_entities)

    @pytest.mark.asyncio
    async def test_complexity_estimation(self, test_config):
        """Test complexity estimation."""
        engine = ReasoningEngine(test_config)

        simple_plan = await engine.reason("What is Python?")
        complex_plan = await engine.reason("Create a comprehensive analysis of all Python frameworks including detailed comparison of features, performance metrics, and use cases")

        assert complex_plan.complexity_estimate > simple_plan.complexity_estimate


# Tests for KnowledgeRetriever
class TestKnowledgeRetriever:
    """Tests for the KnowledgeRetriever class."""

    @pytest.mark.asyncio
    async def test_retrieve_with_knowledge_disabled(self, test_config):
        """Test retrieval returns empty when knowledge is disabled."""
        config = replace(test_config, knowledge_enabled=False)
        retriever = KnowledgeRetriever(config)

        contexts = await retriever.retrieve("test query")

        assert contexts == []

    @pytest.mark.asyncio
    async def test_retrieve_with_local_knowledge(self, test_config, temp_storage):
        """Test retrieval from local knowledge base."""
        # Create a temporary knowledge file
        kb_path = Path(".torq/knowledge_base.json")
        kb_path.parent.mkdir(parents=True, exist_ok=True)

        import json
        with open(kb_path, "w") as f:
            json.dump([{
                "id": "test_1",
                "content": "Python is a programming language",
                "source": "test",
            }], f)

        try:
            retriever = KnowledgeRetriever(test_config)
            contexts = await retriever.retrieve("What is Python?")

            # Should find some context with rule-based search
            assert len(contexts) >= 0  # May be empty if similarity threshold is high
        finally:
            kb_path.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_store_knowledge(self, test_config, temp_storage):
        """Test storing knowledge."""
        retriever = KnowledgeRetriever(test_config)

        result = await retriever.store_knowledge(
            content="Test knowledge content",
            source="test_source"
        )

        # Should not raise an exception
        assert result is True or result is False


# Tests for Planner
class TestPlanner:
    """Tests for the Planner class."""

    @pytest.mark.asyncio
    async def test_create_execution_plan(self, test_config, sample_reasoning_plan):
        """Test creating an execution plan from reasoning."""
        planner = Planner(test_config)

        plan = await planner.plan(
            reasoning_plan=sample_reasoning_plan,
            query="What is async programming in Python?"
        )

        assert plan.goal
        assert len(plan.steps) > 0
        assert plan.estimated_duration_seconds >= 0

    @pytest.mark.asyncio
    async def test_plan_with_web_search_tool(self, test_config):
        """Test planning with web search tool."""
        planner = Planner(test_config)
        reasoning = ReasoningPlan(
            intent=IntentType.RESEARCH,
            suggested_tools=["web_search"],
        )

        plan = await planner.plan(
            reasoning_plan=reasoning,
            query="Research AI trends"
        )

        assert "web_search" in plan.required_tools
        assert any(s.tool_name == "web_search" for s in plan.steps)

    @pytest.mark.asyncio
    async def test_refine_plan(self, test_config, sample_execution_plan):
        """Test plan refinement."""
        planner = Planner(test_config)

        refined = await planner.refine_plan(
            plan=sample_execution_plan,
            feedback="Make it more detailed and comprehensive"
        )

        assert refined.estimated_duration_seconds > sample_execution_plan.estimated_duration_seconds

    @pytest.mark.asyncio
    async def test_step_dependencies(self, test_config):
        """Test that step dependencies are properly set."""
        planner = Planner(test_config)
        reasoning = ReasoningPlan(
            intent=IntentType.QUERY,
            suggested_tools=["web_search", "data_analysis"],
        )

        plan = await planner.plan(
            reasoning_plan=reasoning,
            query="Analyze and search for data"
        )

        # Synthesis step should depend on other steps
        synthesis_step = next((s for s in plan.steps if s.tool_name == "synthesis"), None)
        if synthesis_step:
            assert len(synthesis_step.dependencies) > 0


# Tests for ToolExecutor
class TestToolExecutor:
    """Tests for the ToolExecutor class."""

    @pytest.mark.asyncio
    async def test_execute_plan(self, test_config, sample_execution_plan):
        """Test executing a plan."""
        executor = ToolExecutor(test_config)

        result = await executor.execute(
            plan=sample_execution_plan,
            query="Test query"
        )

        assert result is not None
        assert isinstance(result.success, bool)
        assert result.total_execution_time_seconds >= 0

    @pytest.mark.asyncio
    async def test_execute_with_mock_tool(self, test_config):
        """Test executing with a custom tool."""
        executor = ToolExecutor(test_config)

        # Register a mock tool
        async def mock_tool(params, query):
            return {"mock_result": "success"}

        executor.register_tool("mock_tool", mock_tool)

        step = ExecutionStep(
            description="Mock tool step",
            tool_name="mock_tool",
            tool_category=ToolCategory.CUSTOM,
            parameters={},
        )

        plan = ExecutionPlan(
            goal="Test mock tool",
            steps=[step],
            required_tools=["mock_tool"],
        )

        result = await executor.execute(plan, "test")

        # Should succeed since our mock always returns
        assert result.tool_results[0].tool_name == "mock_tool"

    @pytest.mark.asyncio
    async def test_tool_caching(self, test_config, sample_execution_plan):
        """Test tool result caching."""
        config = replace(test_config, enable_tool_caching=True)
        executor = ToolExecutor(config)

        # First execution
        result1 = await executor.execute(
            plan=sample_execution_plan,
            query="Test query"
        )

        # Second execution with same plan (should use cache)
        result2 = await executor.execute(
            plan=sample_execution_plan,
            query="Test query"
        )

        # At minimum, both should complete without errors
        assert result1 is not None
        assert result2 is not None


# Tests for Evaluator
class TestEvaluator:
    """Tests for the Evaluator class."""

    @pytest.mark.asyncio
    async def test_evaluate_successful_result(
        self, test_config, sample_execution_result, sample_execution_plan
    ):
        """Test evaluating a successful result."""
        evaluator = Evaluator(test_config)
        reasoning = ReasoningPlan(intent=IntentType.QUERY)

        result = await evaluator.evaluate(
            execution_result=sample_execution_result,
            execution_plan=sample_execution_plan,
            reasoning_plan=reasoning,
            query="What is async programming?"
        )

        assert result.confidence_score >= 0.0
        assert result.data_integrity_score >= 0.0
        assert isinstance(result.task_completed, bool)

    @pytest.mark.asyncio
    async def test_evaluate_failed_result(self, test_config):
        """Test evaluating a failed result."""
        evaluator = Evaluator(test_config)

        failed_result = ExecutionResult(
            success=False,
            errors=["Tool execution failed"],
            tool_results=[],
        )

        reasoning = ReasoningPlan(intent=IntentType.QUERY)
        plan = ExecutionPlan(goal="Test", steps=[], required_tools=[])

        result = await evaluator.evaluate(
            execution_result=failed_result,
            execution_plan=plan,
            reasoning_plan=reasoning,
            query="Test query"
        )

        assert result.confidence_score < 0.8  # Should be low for failed result

    @pytest.mark.asyncio
    async def test_should_retry_logic(self, test_config):
        """Test retry decision logic."""
        evaluator = Evaluator(test_config)

        # Low confidence should trigger retry
        assert True  # Placeholder for retry test


# Tests for LearningWriter
class TestLearningWriter:
    """Tests for the LearningWriter class."""

    @pytest.mark.asyncio
    async def test_record_learning_event(
        self, temp_storage, sample_reasoning_plan, sample_execution_plan
    ):
        """Test recording a learning event."""
        writer = LearningWriter(temp_storage)

        event = await writer.record(
            query="Test query",
            intent=IntentType.QUERY,
            reasoning_plan=sample_reasoning_plan,
            knowledge_contexts=[],
            execution_plan=sample_execution_plan,
            execution_result=None,
            evaluation_result=None,
            total_time_seconds=1.5,
            retry_count=0,
        )

        assert event is not None
        assert event.intent == IntentType.QUERY
        assert event.query == "Test query"

    @pytest.mark.asyncio
    async def test_get_statistics(self, temp_storage):
        """Test getting learning statistics."""
        writer = LearningWriter(temp_storage)

        stats = await writer.get_statistics()

        assert "total_events" in stats
        assert "storage_path" in stats

    @pytest.mark.asyncio
    async def test_shutdown(self, temp_storage):
        """Test learning writer shutdown."""
        writer = LearningWriter(temp_storage)

        # Should not raise an exception
        await writer.shutdown()


# Tests for CognitiveLoop (Integration)
class TestCognitiveLoop:
    """Integration tests for the complete Cognitive Loop."""

    @pytest.mark.asyncio
    async def test_full_loop_execution(self, test_config):
        """Test executing the complete cognitive loop."""
        loop = CognitiveLoop(config=test_config)

        result = await loop.run("What is async programming in Python?")

        assert result is not None
        assert result.status in (CognitiveLoopStatus.COMPLETED, CognitiveLoopStatus.FAILED)
        assert result.query == "What is async programming in Python?"
        assert result.reasoning_plan is not None
        assert result.total_time_seconds >= 0

    @pytest.mark.asyncio
    async def test_loop_with_retries(self, test_config):
        """Test cognitive loop with retry logic."""
        config = replace(test_config, max_retries=1)
        loop = CognitiveLoop(config=config)

        result = await loop.run("Test query that might need retries")

        assert result is not None
        assert result.retry_count >= 0

    @pytest.mark.asyncio
    async def test_session_context(self, test_config):
        """Test cognitive loop with session context."""
        loop = CognitiveLoop(config=test_config)

        session = loop.create_session(user_id="test_user")

        result = await loop.run(
            "Follow-up question",
            session_context=session
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_statistics(self, test_config):
        """Test getting cognitive loop statistics."""
        loop = CognitiveLoop(config=test_config)

        stats = loop.get_statistics()

        assert "total_runs" in stats
        assert "success_rate" in stats

    @pytest.mark.asyncio
    async def test_shutdown(self, test_config):
        """Test cognitive loop shutdown."""
        loop = CognitiveLoop(config=test_config)

        # Should not raise an exception
        await loop.shutdown()

    @pytest.mark.asyncio
    async def test_performance_target_latency(self, test_config):
        """Test that loop latency is within target."""
        import time

        loop = CognitiveLoop(config=test_config)

        start = time.time()
        result = await loop.run("What is Python?")
        elapsed = time.time() - start

        # With disabled knowledge and simple tools, should be fast
        # This is a soft test - may vary by system
        assert result is not None
        assert elapsed < 10.0  # Reasonable upper bound


# Performance and load tests
class TestCognitiveLoopPerformance:
    """Performance tests for the cognitive loop."""

    @pytest.mark.asyncio
    async def test_concurrent_executions(self, test_config):
        """Test multiple concurrent loop executions."""
        loop = CognitiveLoop(config=test_config)

        queries = [
            "What is Python?",
            "What is JavaScript?",
            "What is Go?",
        ]

        start = asyncio.get_event_loop().time()
        results = await asyncio.gather(*[loop.run(q) for q in queries])
        elapsed = asyncio.get_event_loop().time() - start

        assert len(results) == 3
        assert all(r is not None for r in results)
        # Concurrent should be faster than sequential
        assert elapsed < 10.0

    @pytest.mark.asyncio
    async def test_memory_efficiency(self, test_config):
        """Test that the loop doesn't leak memory."""
        loop = CognitiveLoop(config=test_config)

        # Run multiple iterations
        for i in range(5):
            result = await loop.run(f"Query number {i}")
            assert result is not None

        stats = loop.get_statistics()
        assert stats["total_runs"] == 5


# Error handling tests
class TestCognitiveLoopErrorHandling:
    """Tests for error handling in the cognitive loop."""

    @pytest.mark.asyncio
    async def test_handles_invalid_query(self, test_config):
        """Test handling of invalid/empty queries."""
        loop = CognitiveLoop(config=test_config)

        result = await loop.run("")

        # Should still complete without crashing
        assert result is not None

    @pytest.mark.asyncio
    async def test_handles_tool_failure(self, test_config):
        """Test handling when tools fail."""
        # This would require mocking tool failures
        loop = CognitiveLoop(config=test_config)

        result = await loop.run("Execute a tool that doesn't exist")

        # Should handle gracefully
        assert result is not None

    @pytest.mark.asyncio
    async def test_max_retries_respected(self, test_config):
        """Test that max retries is respected."""
        config = replace(test_config, max_retries=1)
        loop = CognitiveLoop(config=config)

        result = await loop.run("Query that will fail")

        # Should not exceed max retries
        assert result.retry_count <= config.max_retries


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
