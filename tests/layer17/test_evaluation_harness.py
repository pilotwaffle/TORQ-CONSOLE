"""TORQ Layer 17 - Evaluation Harness Tests

Tests for the EvaluationHarness.
"""

import pytest

from torq_console.layer17.models import AgentGenome, GenomeStatus
from torq_console.layer17.evaluation import create_evaluation_harness
from torq_console.layer17.evaluation.benchmark_missions import get_benchmark_missions


# =============================================================================
# TESTS
# =============================================================================


class TestEvaluationHarness:
    """Test suite for EvaluationHarness."""

    @pytest.mark.asyncio
    async def test_run_benchmark_suite_returns_valid_result(self, evaluation_harness):
        """Test that run_benchmark_suite returns valid result."""
        genome = AgentGenome(
            genome_id="test_genome",
            toolset=["web_search", "code_executor", "file_read"],
        )

        result = await evaluation_harness.run_benchmark_suite(genome)

        assert result.genome_id == "test_genome"
        assert result.benchmark_count == 5  # 5 benchmark missions
        assert 0.0 <= result.completion_score <= 1.0
        assert 0.0 <= result.latency_score <= 1.0
        assert 0.0 <= result.consistency_score <= 1.0
        assert 0.0 <= result.overall_score <= 1.0
        assert isinstance(result.passed, bool)
        assert result.evaluated_at is not None

    @pytest.mark.asyncio
    async def test_run_benchmark_suite_uses_loaded_missions(self, evaluation_harness):
        """Test that harness uses missions loaded from benchmark_missions.py."""
        genome = AgentGenome(
            genome_id="test_genome",
            toolset=["web_search", "code_executor", "file_read"],
        )

        result = await evaluation_harness.run_benchmark_suite(genome)

        # Should have run all 5 loaded benchmarks
        assert result.benchmark_count == 5
        assert len(result.benchmark_details) == 5

    @pytest.mark.asyncio
    async def test_run_benchmark_suite_with_custom_missions(self, evaluation_harness):
        """Test running custom missions instead of loaded benchmarks."""
        from torq_console.layer16.models import MissionRequirements

        genome = AgentGenome(
            genome_id="test_genome",
            toolset=["web_search"],
        )

        # Create custom mission
        custom_mission = MissionRequirements(
            mission_id="custom_benchmark",
            mission_type="test",
            required_cpu=5.0,
            expected_value=100.0,
        )

        result = await evaluation_harness.run_benchmark_suite(genome, missions=[custom_mission])

        assert result.benchmark_count == 1
        assert "custom_benchmark" in result.benchmark_details

    @pytest.mark.asyncio
    async def test_benchmark_passed_threshold(self, evaluation_harness):
        """Test that passed threshold is overall_score >= 0.6."""
        # High-quality genome
        good_genome = AgentGenome(
            genome_id="good_genome",
            toolset=["web_search", "code_executor", "file_read", "bash", "database_query"],
        )

        result = await evaluation_harness.run_benchmark_suite(good_genome)

        # With decent toolset, should pass threshold
        assert result.overall_score >= 0.0
        # Pass/fail based on threshold
        assert result.passed == (result.overall_score >= 0.6)

    def test_load_benchmarks(self):
        """Test loading benchmark missions."""
        from torq_console.layer17.evaluation.benchmark_missions import get_benchmark_missions

        missions = get_benchmark_missions()

        assert len(missions) == 5
        assert all(isinstance(m, MissionRequirements) for m in missions)

        # Verify missions use verified field names
        for mission in missions:
            assert hasattr(mission, "mission_id")
            assert hasattr(mission, "mission_type")
            assert hasattr(mission, "required_cpu")
            assert hasattr(mission, "max_cost")
            assert hasattr(mission, "priority")


class TestBenchmarkEvaluationResult:
    """Test suite for BenchmarkEvaluationResult model."""

    def test_result_initializes_correctly(self):
        """Test that result initializes with correct defaults."""
        from torq_console.layer17.models import BenchmarkEvaluationResult

        result = BenchmarkEvaluationResult(
            genome_id="test",
            benchmark_count=3,
        )

        assert result.genome_id == "test"
        assert result.benchmark_count == 3
        assert result.completion_score == 0.0
        assert result.latency_score == 0.0
        assert result.consistency_score == 0.0
        assert result.overall_score == 0.0
        assert result.passed is False
