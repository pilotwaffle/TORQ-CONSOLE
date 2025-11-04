"""
Phase 1 Test Suite: Marvin Integration Foundation

Tests the core Marvin integration layer for TORQ Console.
This validates all Phase 1 components before proceeding to Phase 2.
"""

import sys
import os
import pytest
from typing import List
from enum import Enum

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


class TestPhase1Imports:
    """Test that all Phase 1 modules import correctly."""

    def test_import_core(self):
        """Test core module imports."""
        from torq_console.marvin_integration.core import TorqMarvinIntegration
        assert TorqMarvinIntegration is not None

    def test_import_models(self):
        """Test model imports."""
        from torq_console.marvin_integration.models import (
            TorqSpecAnalysis,
            TorqCodeReview,
            TorqResearchFindings,
            TorqTaskBreakdown,
            IntentClassification,
            Priority,
            Severity,
        )
        assert TorqSpecAnalysis is not None
        assert TorqCodeReview is not None
        assert TorqResearchFindings is not None
        assert TorqTaskBreakdown is not None
        assert IntentClassification is not None
        assert Priority is not None
        assert Severity is not None

    def test_import_agents(self):
        """Test agent factory imports."""
        from torq_console.marvin_integration.agents import (
            create_spec_analyzer,
            create_code_reviewer,
            create_research_agent,
            create_general_agent,
            create_task_planner,
            create_spec_kit_orchestrator,
            get_agent,
        )
        assert create_spec_analyzer is not None
        assert create_code_reviewer is not None
        assert create_research_agent is not None
        assert create_general_agent is not None
        assert create_task_planner is not None
        assert create_spec_kit_orchestrator is not None
        assert get_agent is not None

    def test_import_package(self):
        """Test package-level imports."""
        from torq_console.marvin_integration import (
            TorqMarvinIntegration,
            TorqSpecAnalysis,
            create_spec_analyzer,
        )
        assert TorqMarvinIntegration is not None
        assert TorqSpecAnalysis is not None
        assert create_spec_analyzer is not None


class TestPydanticModels:
    """Test that Pydantic models validate correctly."""

    def test_torq_spec_analysis_valid(self):
        """Test TorqSpecAnalysis with valid data."""
        from torq_console.marvin_integration.models import TorqSpecAnalysis, AnalysisConfidence

        analysis = TorqSpecAnalysis(
            clarity_score=0.85,
            completeness_score=0.70,
            feasibility_score=0.90,
            confidence=AnalysisConfidence.HIGH,
            missing_requirements=["Error handling not defined"],
            recommendations=["Add error handling requirements"],
            technical_risks=["Database scalability"],
            strengths=["Clear API structure"],
            summary="Good foundation, needs error handling details"
        )

        assert analysis.clarity_score == 0.85
        assert analysis.completeness_score == 0.70
        assert analysis.feasibility_score == 0.90
        assert analysis.confidence == AnalysisConfidence.HIGH
        assert len(analysis.missing_requirements) == 1
        assert len(analysis.recommendations) == 1

    def test_torq_spec_analysis_invalid_score(self):
        """Test TorqSpecAnalysis rejects invalid scores."""
        from torq_console.marvin_integration.models import TorqSpecAnalysis, AnalysisConfidence
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            TorqSpecAnalysis(
                clarity_score=1.5,  # Invalid: > 1.0
                completeness_score=0.70,
                feasibility_score=0.90,
                confidence=AnalysisConfidence.HIGH,
                missing_requirements=[],
                recommendations=[],
                technical_risks=[],
                strengths=[],
                summary="Test"
            )

    def test_code_issue_model(self):
        """Test CodeIssue model."""
        from torq_console.marvin_integration.models import CodeIssue, Severity

        issue = CodeIssue(
            severity=Severity.WARNING,
            line_number=42,
            description="Potential division by zero",
            suggestion="Add zero check before division",
            category="safety"
        )

        assert issue.severity == Severity.WARNING
        assert issue.line_number == 42
        assert "division by zero" in issue.description.lower()

    def test_torq_code_review_valid(self):
        """Test TorqCodeReview with valid data."""
        from torq_console.marvin_integration.models import (
            TorqCodeReview,
            CodeIssue,
            Severity,
        )

        review = TorqCodeReview(
            quality_score=7.5,
            issues=[
                CodeIssue(
                    severity=Severity.WARNING,
                    line_number=42,
                    description="Test issue",
                    suggestion="Test fix",
                    category="style"
                )
            ],
            summary="Good code",
            positive_aspects=["Clean structure"],
            security_concerns=[],
            performance_notes=[],
            maintainability_score=8.0,
            test_coverage_assessment="Good"
        )

        assert review.quality_score == 7.5
        assert len(review.issues) == 1
        assert review.maintainability_score == 8.0

    def test_task_breakdown_model(self):
        """Test TorqTaskBreakdown model."""
        from torq_console.marvin_integration.models import (
            TorqTaskBreakdown,
            Task,
            Milestone,
            Priority,
        )

        breakdown = TorqTaskBreakdown(
            project_title="Test Project",
            total_estimated_hours=100.0,
            tasks=[
                Task(
                    title="Setup",
                    description="Initial setup",
                    priority=Priority.HIGH,
                    estimated_hours=10.0,
                    dependencies=[],
                    skills_required=["Python"],
                    risks=[]
                )
            ],
            milestones=[
                Milestone(
                    title="MVP",
                    description="Minimum viable product",
                    target_date="Week 4",
                    tasks=["Setup"]
                )
            ],
            critical_path=["Setup"],
            resource_requirements={"dev": 2},
            risk_summary="Low risk",
            success_criteria=["Tests pass"]
        )

        assert breakdown.project_title == "Test Project"
        assert breakdown.total_estimated_hours == 100.0
        assert len(breakdown.tasks) == 1
        assert len(breakdown.milestones) == 1

    def test_enum_classifications(self):
        """Test enum classification models."""
        from torq_console.marvin_integration.models import (
            IntentClassification,
            SentimentClassification,
            ComplexityLevel,
            Priority,
        )

        # Test IntentClassification
        assert IntentClassification.SPEC_CREATE.value == "spec_create"
        assert IntentClassification.CODE_REVIEW.value == "code_review"

        # Test SentimentClassification
        assert SentimentClassification.POSITIVE.value == "positive"
        assert SentimentClassification.NEGATIVE.value == "negative"

        # Test ComplexityLevel
        assert ComplexityLevel.SIMPLE.value == "simple"
        assert ComplexityLevel.COMPLEX.value == "complex"

        # Test Priority
        assert Priority.HIGH.value == "high"
        assert Priority.URGENT.value == "urgent"


class TestTorqMarvinIntegration:
    """Test TorqMarvinIntegration class."""

    def test_initialization_default(self):
        """Test initialization with defaults."""
        from torq_console.marvin_integration import TorqMarvinIntegration

        integration = TorqMarvinIntegration()

        assert integration.model == "anthropic/claude-sonnet-4-20250514"
        assert integration.metrics is not None
        assert integration.metrics['extractions'] == 0
        assert integration.metrics['casts'] == 0

    def test_initialization_custom_model(self):
        """Test initialization with custom model."""
        from torq_console.marvin_integration import TorqMarvinIntegration

        integration = TorqMarvinIntegration(model="openai/gpt-4")

        assert integration.model == "openai/gpt-4"

    def test_get_metrics(self):
        """Test get_metrics method."""
        from torq_console.marvin_integration import TorqMarvinIntegration

        integration = TorqMarvinIntegration()
        metrics = integration.get_metrics()

        assert isinstance(metrics, dict)
        assert 'extractions' in metrics
        assert 'casts' in metrics
        assert 'classifications' in metrics
        assert 'generations' in metrics
        assert 'task_runs' in metrics

    def test_reset_metrics(self):
        """Test reset_metrics method."""
        from torq_console.marvin_integration import TorqMarvinIntegration

        integration = TorqMarvinIntegration()
        integration.metrics['extractions'] = 10
        integration.reset_metrics()

        assert integration.metrics['extractions'] == 0


class TestAgentFactories:
    """Test agent factory functions."""

    def test_create_spec_analyzer(self):
        """Test create_spec_analyzer factory."""
        from torq_console.marvin_integration import create_spec_analyzer
        import marvin

        agent = create_spec_analyzer()

        assert isinstance(agent, marvin.Agent)
        assert agent.name == "Spec Analyzer"
        assert "specification" in agent.instructions.lower()

    def test_create_code_reviewer(self):
        """Test create_code_reviewer factory."""
        from torq_console.marvin_integration import create_code_reviewer
        import marvin

        agent = create_code_reviewer()

        assert isinstance(agent, marvin.Agent)
        assert agent.name == "Code Reviewer"
        assert "code" in agent.instructions.lower()

    def test_create_research_agent(self):
        """Test create_research_agent factory."""
        from torq_console.marvin_integration import create_research_agent
        import marvin

        agent = create_research_agent()

        assert isinstance(agent, marvin.Agent)
        assert agent.name == "Research Specialist"
        assert "research" in agent.instructions.lower()

    def test_create_task_planner(self):
        """Test create_task_planner factory."""
        from torq_console.marvin_integration import create_task_planner
        import marvin

        agent = create_task_planner()

        assert isinstance(agent, marvin.Agent)
        assert agent.name == "Task Planner"
        assert "task" in agent.instructions.lower() or "plan" in agent.instructions.lower()

    def test_create_spec_kit_orchestrator(self):
        """Test create_spec_kit_orchestrator factory."""
        from torq_console.marvin_integration import create_spec_kit_orchestrator
        import marvin

        agent = create_spec_kit_orchestrator()

        assert isinstance(agent, marvin.Agent)
        assert agent.name == "Spec-Kit Orchestrator"
        assert "spec-kit" in agent.instructions.lower()

    def test_create_general_agent(self):
        """Test create_general_agent factory."""
        from torq_console.marvin_integration import create_general_agent
        import marvin

        agent = create_general_agent(name="Custom Agent", instructions="Custom instructions")

        assert isinstance(agent, marvin.Agent)
        assert agent.name == "Custom Agent"
        assert agent.instructions == "Custom instructions"

    def test_get_agent_valid(self):
        """Test get_agent with valid agent type."""
        from torq_console.marvin_integration import get_agent
        import marvin

        agent = get_agent("spec_analyzer")

        assert isinstance(agent, marvin.Agent)
        assert agent.name == "Spec Analyzer"

    def test_get_agent_invalid(self):
        """Test get_agent with invalid agent type."""
        from torq_console.marvin_integration import get_agent

        with pytest.raises(ValueError) as exc_info:
            get_agent("nonexistent_agent")

        assert "Unknown agent type" in str(exc_info.value)


class TestMarvinIntegrationMethods:
    """Test TorqMarvinIntegration methods (require API key)."""

    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"),
        reason="No API key available"
    )
    def test_extract_basic(self):
        """Test basic extract functionality."""
        from torq_console.marvin_integration import TorqMarvinIntegration

        integration = TorqMarvinIntegration()

        # Extract numbers from text
        result = integration.extract(
            "I bought 3 apples and 5 oranges",
            int,
            instructions="extract quantities"
        )

        assert isinstance(result, list)
        assert len(result) > 0
        assert integration.metrics['extractions'] == 1

    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"),
        reason="No API key available"
    )
    def test_classify_basic(self):
        """Test basic classify functionality."""
        from torq_console.marvin_integration import TorqMarvinIntegration
        from enum import Enum

        class Sentiment(Enum):
            POSITIVE = "positive"
            NEGATIVE = "negative"

        integration = TorqMarvinIntegration()

        result = integration.classify("I love this!", Sentiment)

        assert isinstance(result, Sentiment)
        assert integration.metrics['classifications'] == 1

    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"),
        reason="No API key available"
    )
    def test_create_agent_method(self):
        """Test create_agent method."""
        from torq_console.marvin_integration import TorqMarvinIntegration
        import marvin

        integration = TorqMarvinIntegration()

        agent = integration.create_agent(
            name="Test Agent",
            instructions="Test instructions"
        )

        assert isinstance(agent, marvin.Agent)
        assert agent.name == "Test Agent"


class TestPhase1Integration:
    """Integration tests for Phase 1 components working together."""

    def test_full_workflow_models_and_agents(self):
        """Test that models and agents work together."""
        from torq_console.marvin_integration import (
            create_spec_analyzer,
            TorqSpecAnalysis,
        )

        # Create spec analyzer agent
        agent = create_spec_analyzer()

        # Verify agent can theoretically produce TorqSpecAnalysis
        # (actual production would require API call)
        assert agent is not None

        # Verify TorqSpecAnalysis model structure matches agent's purpose
        sample = TorqSpecAnalysis(
            clarity_score=0.8,
            completeness_score=0.7,
            feasibility_score=0.9,
            confidence="high",
            missing_requirements=[],
            recommendations=[],
            technical_risks=[],
            strengths=[],
            summary="Test"
        )

        assert sample is not None

    def test_integration_class_with_models(self):
        """Test integration class metrics work with model operations."""
        from torq_console.marvin_integration import TorqMarvinIntegration

        integration = TorqMarvinIntegration()

        # Verify metrics start at zero
        metrics = integration.get_metrics()
        assert metrics['extractions'] == 0
        assert metrics['casts'] == 0

        # Verify reset works
        integration.reset_metrics()
        metrics = integration.get_metrics()
        assert all(v == 0 for v in metrics.values())


def run_tests():
    """Run all Phase 1 tests."""
    print("=" * 70)
    print("PHASE 1 TEST SUITE: Marvin Integration Foundation")
    print("=" * 70)
    print()

    # Run pytest with verbose output
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-ra",
        "--color=yes"
    ])

    print()
    print("=" * 70)
    if exit_code == 0:
        print("✅ PHASE 1 TESTS PASSED - Ready to proceed to Phase 2")
    else:
        print("❌ PHASE 1 TESTS FAILED - Fix issues before proceeding")
    print("=" * 70)

    return exit_code


if __name__ == "__main__":
    exit(run_tests())
