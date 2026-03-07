"""
Phase 4A: Multi-Agent Foundation Tests

Tests for the executive controller, delegation system, and agent coordination.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from torq_console.agents.orchestration.execution_plan import (
    ExecutionPlan, ExecutionPlanBuilder, PlanTemplates,
    ExecutionMode, AgentTask, AgentRole, TaskPriority
)
from torq_console.agents.orchestration.delegation import (
    DelegationRequest, DelegationResult, DelegationPolicy,
    DelegationRule, DelegationRisk, DelegationEngine, DelegationRules
)
from torq_console.agents.orchestration.agent_coordinator import (
    AgentCoordinator, ExecutionSummary
)
from torq_console.agents.orchestration.executive_controller import (
    ExecutiveController, ExecutiveDecision,
    create_prince_flowers_executive
)


class TestExecutionPlan:
    """Test execution plan creation and management."""

    def test_plan_builder_basic(self):
        """Test basic plan builder usage."""
        plan = (ExecutionPlanBuilder()
                .with_id("test_plan")
                .with_mode(ExecutionMode.SEQUENTIAL)
                .with_priority(TaskPriority.NORMAL)
                .with_synthesis("Combine all results")
                .add_task(
                    agent_id="research_agent",
                    agent_role=AgentRole.RESEARCHER,
                    prompt="Research X",
                )
                .build())

        assert plan.plan_id == "test_plan"
        assert plan.mode == ExecutionMode.SEQUENTIAL
        assert len(plan.tasks) == 1
        assert plan.tasks[0].agent_id == "research_agent"

    def test_plan_with_dependencies(self):
        """Test plan with task dependencies."""
        plan = (ExecutionPlanBuilder()
                .with_id("dep_plan")
                .with_mode(ExecutionMode.SEQUENTIAL)
                .add_task(
                    agent_id="research_agent",
                    agent_role=AgentRole.RESEARCHER,
                    prompt="Step 1",
                    output_key="step1_result"
                )
                .add_task(
                    agent_id="workflow_agent",
                    agent_role=AgentRole.WORKFLOW,
                    prompt="Step 2 using step 1 results",
                    dependencies=["dep_plan_task_0"],
                    output_key="step2_result"
                )
                .build())

        assert len(plan.tasks) == 2
        assert plan.tasks[1].dependencies == ["dep_plan_task_0"]
        assert plan.tasks[1].output_key == "step2_result"

    def test_plan_progress_tracking(self):
        """Test plan progress tracking."""
        plan = (ExecutionPlanBuilder()
                .with_id("progress_plan")
                .with_mode(ExecutionMode.SEQUENTIAL)
                .add_task(
                    agent_id="research_agent",
                    agent_role=AgentRole.RESEARCHER,
                    prompt="Task 1"
                )
                .add_task(
                    agent_id="workflow_agent",
                    agent_role=AgentRole.WORKFLOW,
                    prompt="Task 2",
                    dependencies=["progress_plan_task_0"]
                )
                .build())

        assert plan.progress == 0.0

        # Mark first task complete
        plan.mark_task_started("progress_plan_task_0")
        plan.mark_task_completed("progress_plan_task_0", {"content": "Done"})

        assert plan.progress == 0.5

        # Mark second task complete
        plan.mark_task_started("progress_plan_task_1")
        plan.mark_task_completed("progress_plan_task_1", {"content": "Done"})

        assert plan.progress == 1.0
        assert plan.is_complete

    def test_plan_serialization(self):
        """Test plan to/from dict conversion."""
        plan = (ExecutionPlanBuilder()
                .with_id("serial_plan")
                .with_mode(ExecutionMode.PARALLEL)
                .add_task(
                    agent_id="research_agent",
                    agent_role=AgentRole.RESEARCHER,
                    prompt="Search for X"
                )
                .build())

        # Convert to dict
        plan_dict = plan.to_dict()

        assert plan_dict["plan_id"] == "serial_plan"
        assert plan_dict["mode"] == "parallel"
        assert len(plan_dict["tasks"]) == 1

        # Convert back from dict
        restored_plan = ExecutionPlan.from_dict(plan_dict)

        assert restored_plan.plan_id == plan.plan_id
        assert restored_plan.mode == plan.mode


class TestDelegationRules:
    """Test delegation rule evaluation."""

    def test_research_query_detection(self):
        """Test that research queries are correctly identified."""
        rules = DelegationRules.get_default_rules()

        # Research query should match research rule
        query = "Search for latest AI news"
        context = {}
        matching_rule = None

        for rule in rules:
            if rule.evaluate(query, context):
                matching_rule = rule
                break

        assert matching_rule is not None
        assert matching_rule.target_agent == "research_agent"
        assert matching_rule.agent_role == AgentRole.RESEARCHER

    def test_workflow_query_detection(self):
        """Test that workflow queries are correctly identified."""
        rules = DelegationRules.get_default_rules()

        query = "Build a marketing automation workflow"
        context = {}
        matching_rule = None

        for rule in rules:
            if rule.evaluate(query, context):
                matching_rule = rule
                break

        assert matching_rule is not None
        assert "workflow" in matching_rule.target_agent or matching_rule.agent_role == AgentRole.WORKFLOW

    def test_simple_query_no_delegation(self):
        """Test that simple queries don't trigger delegation."""
        engine = DelegationEngine()

        query = "Hello, how are you?"
        context = {}

        delegation = engine.evaluate_delegation(query, context)

        assert delegation is None

    def test_routing_override_triggers_delegation(self):
        """Test that routing overrides trigger appropriate delegation."""
        engine = DelegationEngine()

        query = "What is Bitcoin price today?"
        context = {
            "routing_override": {
                "active": True,
                "reason": "realtime_finance"
            }
        }

        delegation = engine.evaluate_delegation(query, context)

        # Should trigger delegation to research agent
        assert delegation is not None
        assert delegation.target_agent in ["research_agent", "workflow_agent"]


class TestDelegationEngine:
    """Test delegation engine functionality."""

    @pytest.mark.asyncio
    async def test_delegation_engine_no_match(self):
        """Test delegation engine with no matching rules."""
        engine = DelegationEngine([])  # No rules

        query = "Random query that won't match"
        context = {}

        delegation = engine.evaluate_delegation(query, context)

        assert delegation is None

    @pytest.mark.asyncio
    async def test_create_plan_from_delegation(self):
        """Test creating execution plan from delegation."""
        engine = DelegationEngine()

        query = "Latest AI news"
        context = {}

        delegation = engine.evaluate_delegation(query, context)

        if delegation:
            plan = engine.create_execution_plan(query, context, delegation)

            assert plan is not None
            assert len(plan.tasks) > 0
            assert plan.routing_reason == "research_query"


class TestExecutiveController:
    """Test executive controller decision making."""

    @pytest.mark.asyncio
    async def test_executive_direct_handling(self):
        """Test that simple queries are handled directly."""
        controller = ExecutiveController()

        query = "Hello, how are you?"
        context = {}

        decision = await controller._decide_execution_strategy(query, context)

        assert decision.should_delegate is False
        assert decision.execution_mode == ExecutionMode.SINGLE_AGENT
        assert "simple" in decision.reason.lower()

    @pytest.mark.asyncio
    async def test_executive_delegates_complex_queries(self):
        """Test that complex queries trigger delegation."""
        controller = ExecutiveController()

        # Use a query that has "and then" pattern for multi-step planning
        query = "Plan the architecture and then implement the data pipeline"
        context = {}

        decision = await controller._decide_execution_strategy(query, context)

        # Should delegate for complex multi-part query
        assert decision.should_delegate is True
        # Complex multi-part queries should use multi-agent mode
        assert decision.execution_mode in [
            ExecutionMode.SEQUENTIAL,
            ExecutionMode.PARALLEL
        ]


class TestPlanTemplates:
    """Test predefined plan templates."""

    def test_research_plan_template(self):
        """Test research plan template."""
        plan = PlanTemplates.research_plan("What is quantum computing?")

        assert plan.mode == ExecutionMode.SINGLE_AGENT
        assert len(plan.tasks) == 1
        assert plan.tasks[0].agent_role == AgentRole.RESEARCHER

    def test_parallel_analysis_template(self):
        """Test parallel analysis template."""
        plan = PlanTemplates.parallel_analysis(
            query="Analyze market trends",
            agents=["research_agent", "workflow_agent"]
        )

        assert plan.mode == ExecutionMode.PARALLEL
        # Should have parallel tasks + synthesis task
        assert len(plan.tasks) >= 2

    def test_workflow_with_research_template(self):
        """Test workflow with research template."""
        plan = PlanTemplates.workflow_with_research(
            goal="Create a customer onboarding system"
        )

        assert plan.mode == ExecutionMode.SEQUENTIAL
        # Should have 3 tasks: research, workflow, synthesis
        assert len(plan.tasks) == 3


class TestExecutionSummary:
    """Test execution summary functionality."""

    def test_summary_success_rate(self):
        """Test success rate calculation."""
        summary = ExecutionSummary(
            plan_id="test",
            mode=ExecutionMode.SEQUENTIAL,
            total_tasks=4,
            completed_tasks=3,
            failed_tasks=1,
            total_time=10.0
        )

        assert summary.success_rate == 0.75

    def test_summary_is_successful_threshold(self):
        """Test success threshold for summary."""
        # 50% success rate should be successful
        summary1 = ExecutionSummary(
            plan_id="test",
            mode=ExecutionMode.PARALLEL,
            total_tasks=4,
            completed_tasks=2,
            failed_tasks=2,
            total_time=10.0
        )
        assert summary1.is_successful is True

        # All failed should not be successful
        summary2 = ExecutionSummary(
            plan_id="test",
            mode=ExecutionMode.SEQUENTIAL,
            total_tasks=2,
            completed_tasks=0,
            failed_tasks=2,
            total_time=10.0
        )
        assert summary2.is_successful is False


class TestAgentCoordinator:
    """Test agent coordination functionality."""

    @pytest.mark.asyncio
    async def test_single_agent_execution(self):
        """Test single agent execution mode."""
        coordinator = AgentCoordinator()

        # Create a simple single-agent plan
        from torq_console.agents.orchestration.execution_plan import PlanTemplates
        plan = PlanTemplates.research_plan("Test query")

        # Mock agent getter
        async def mock_agent_getter(agent_id):
            mock_agent = AsyncMock()
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.content = "Research result"
            mock_result.metadata = {}
            mock_result.execution_time = 1.0
            mock_agent.process_request.return_value = mock_result
            return mock_agent

        summary = await coordinator.execute_plan(
            plan,
            {},
            mock_agent_getter
        )

        assert summary.is_successful
        assert summary.completed_tasks == 1
        assert summary.final_response == "Research result"

    @pytest.mark.asyncio
    async def test_sequential_execution_with_dependencies(self):
        """Test sequential execution with task dependencies."""
        coordinator = AgentCoordinator()

        # Create plan with dependencies
        plan = (ExecutionPlanBuilder()
                .with_id("sequential_test")
                .with_mode(ExecutionMode.SEQUENTIAL)
                .add_task(
                    agent_id="agent1",
                    agent_role=AgentRole.RESEARCHER,
                    prompt="Step 1"
                )
                .add_task(
                    agent_id="agent2",
                    agent_role=AgentRole.WORKFLOW,
                    prompt="Step 2",
                    dependencies=["sequential_test_task_0"]
                )
                .build())

        # Mock agent getter
        async def mock_agent_getter(agent_id):
            mock_agent = AsyncMock()
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.content = f"Result from {agent_id}"
            mock_result.metadata = {}
            mock_result.execution_time = 1.0
            mock_agent.process_request.return_value = mock_result
            return mock_agent

        summary = await coordinator.execute_plan(
            plan,
            {},
            mock_agent_getter
        )

        assert summary.completed_tasks == 2
        assert len(summary.agent_results) == 2


class TestPrinceFlowersExecutive:
    """Test Prince Flowers as executive agent."""

    @pytest.mark.asyncio
    async def test_executive_processes_request(self):
        """Test that executive processes requests correctly."""
        executive = create_prince_flowers_executive()

        # Mock agent registry
        mock_registry = MagicMock()
        mock_registry.get_agent = AsyncMock(return_value=None)

        # Create a simple query
        result = await executive.process_request(
            "Hello, how are you?",
            {"session_id": "test123"},
            lambda agent_id: None  # No agents available
        )

        # Should get a result
        assert result is not None
        assert hasattr(result, 'success')

    @pytest.mark.asyncio
    async def test_executive_metrics(self):
        """Test executive controller metrics."""
        controller = ExecutiveController()

        # Simulate some activity
        controller.total_requests = 5
        controller.delegate_count = 2
        controller.direct_handle_count = 3

        metrics = controller.get_metrics()

        assert metrics["total_requests"] == 5
        assert metrics["delegate_count"] == 2
        assert metrics["direct_handle_count"] == 3
        assert metrics["delegation_rate"] == 0.4


# ============================================================================
# Integration Tests
# ============================================================================

class TestPhase4AIntegration:
    """Integration tests for Phase 4A multi-agent foundation."""

    @pytest.mark.asyncio
    async def test_end_to_end_delegation_flow(self):
        """Test complete flow from query to delegation to result."""
        # Setup
        controller = ExecutiveController()

        query = "Search for latest AI trends"
        context = {"session_id": "integration_test"}

        # This test validates the delegation decision flow
        # In a full system, it would actually execute with real agents
        decision = await controller._decide_execution_strategy(query, context)

        # Validate decision structure
        assert hasattr(decision, 'should_delegate')
        assert hasattr(decision, 'execution_mode')
        assert hasattr(decision, 'reason')

    @pytest.mark.asyncio
    async def test_plan_template_consistency(self):
        """Test that plan templates create valid execution plans."""
        templates = [
            PlanTemplates.research_plan("Test"),
            PlanTemplates.research_then_synthesis("Test"),
            PlanTemplates.parallel_analysis("Test", ["agent1", "agent2"]),
            PlanTemplates.workflow_with_research("Goal"),
        ]

        for plan in templates:
            # Basic validation
            assert plan.plan_id is not None
            assert len(plan.tasks) > 0
            assert plan.estimated_duration > 0
            assert plan.final_synthesis is not None

            # Task validation
            for task in plan.tasks:
                assert task.task_id is not None
                assert task.agent_id is not None
                assert task.agent_role is not None
                assert task.prompt is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
