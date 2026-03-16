"""TORQ Layer 17 - Evaluation Harness

This module implements benchmark evaluation for agent genomes.
"""

import time
from datetime import datetime, timedelta

from ..models import AgentGenome, BenchmarkEvaluationResult
from ...layer16.models import MissionRequirements


# =============================================================================
# EVALUATION HARNESS
# =============================================================================


class EvaluationHarness:
    """Harness for evaluating agent genomes against benchmark missions.

    This is NOT final ecosystem fitness - just benchmark results.
    Phase 4 does not claim evolutionary fitness.
    """

    def __init__(self):
        """Initialize the evaluation harness."""
        self._benchmark_missions = []

    def load_benchmarks(self, missions: list[MissionRequirements]):
        """Load benchmark missions for evaluation.

        Args:
            missions: List of benchmark mission requirements
        """
        self._benchmark_missions = missions

    async def run_benchmark_suite(
        self,
        genome: AgentGenome,
        missions: list[MissionRequirements] | None = None,
    ) -> BenchmarkEvaluationResult:
        """Run benchmark suite against a genome.

        Args:
            genome: Genome to evaluate
            missions: Optional mission list (uses loaded benchmarks if None)

        Returns:
            BenchmarkEvaluationResult with structured scores

        Note:
            This is a simplified evaluator. In production, this would
            actually execute missions with the agent configuration.
        """
        start_time = time.time()
        start = datetime.utcnow()

        # Use provided missions or loaded benchmarks
        if missions is None:
            missions = self._benchmark_missions

        # Run each benchmark
        completion_scores = []
        latency_scores = []
        details = {}

        for mission in missions:
            result = await self._evaluate_single_benchmark(genome, mission)
            completion_scores.append(result["completion"])
            latency_scores.append(result["latency"])
            details[mission.mission_id] = result

        duration_ms = (time.time() - start_time) * 1000

        # Calculate aggregate scores
        completion_score = sum(completion_scores) / len(completion_scores) if completion_scores else 0.0
        latency_score = sum(latency_scores) / len(latency_scores) if latency_scores else 0.0
        consistency_score = self._calculate_consistency(completion_scores)
        overall_score = (completion_score * 0.4 + latency_score * 0.3 + consistency_score * 0.3)

        # Pass threshold: overall score >= 0.6
        passed = overall_score >= 0.6

        result = BenchmarkEvaluationResult(
            genome_id=genome.genome_id,
            benchmark_count=len(missions),
            completion_score=completion_score,
            latency_score=latency_score,
            consistency_score=consistency_score,
            overall_score=overall_score,
            passed=passed,
            evaluated_at=start,
            evaluation_duration_ms=duration_ms,
            benchmark_details=details,
        )

        return result

    async def _evaluate_single_benchmark(
        self,
        genome: AgentGenome,
        mission: MissionRequirements,
    ) -> dict[str, float]:
        """Evaluate genome against a single benchmark mission.

        Args:
            genome: Genome being evaluated
            mission: Mission requirements

        Returns:
            Dictionary with completion and latency scores

        Note:
            Simplified evaluation. In production, would:
            - Instantiate agent with genome.toolset
            - Execute mission with genome.llm_model
            - Measure actual results
        """
        # Simplified capability matching
        required_tools = {
            "web": "web_search",
            "code": "code_executor",
            "data": "database_query",
            "api": "api_call",
        }

        # Calculate completion score based on toolset match
        # This is a heuristic - production would execute actual missions
        has_required = sum(
            1 for tool in required_tools.values()
            if tool in genome.toolset
        )
        total_required = len(required_tools)
        completion = has_required / max(total_required, 1)

        # Calculate latency score based on toolset size
        # More tools = potentially slower
        toolset_ratio = len(genome.toolset) / genome.max_toolset_size
        latency = 1.0 - (toolset_ratio * 0.3)  # Max 30% penalty

        return {
            "completion": completion,
            "latency": latency,
        }

    def _calculate_consistency(self, scores: list[float]) -> float:
        """Calculate consistency score across benchmarks.

        Args:
            scores: List of scores

        Returns:
            Consistency score (0.0 to 1.0)
        """
        if not scores or len(scores) < 2:
            return 1.0

        # Low variance = high consistency
        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        std = variance ** 0.5

        # Coefficient of variation (inverted for score)
        cv = std / max(mean, 0.01)
        consistency = max(0.0, 1.0 - cv)

        return consistency


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def create_evaluation_harness() -> EvaluationHarness:
    """Factory function to create an evaluation harness.

    Returns:
        Configured EvaluationHarness instance
    """
    return EvaluationHarness()


# =============================================================================
# ALL EXPORTS
# =============================================================================

__all__ = [
    "EvaluationHarness",
    "create_evaluation_harness",
]
