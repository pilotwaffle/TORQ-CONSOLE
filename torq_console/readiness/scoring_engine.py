"""
TORQ Readiness Checker - Scoring Engine

Milestone 2: Compute readiness scores from collected evidence.

Takes evidence from all collectors and produces:
- Dimension-level scores
- Weighted overall score
- Hard-block evaluation
- Final readiness outcome
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from pydantic import BaseModel, Field

from .readiness_models import (
    PolicyProfile,
    PolicyDimension,
    ReadinessScore,
    ReadinessState,
    ReadinessOutcome,
    ReadinessEvaluation,
    EvidenceSummary,
    ReadinessThresholds,
)
from .readiness_policy import (
    get_policy_registry,
    get_hard_block_evaluator,
    get_policy_applicator,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Scoring Context
# ============================================================================

class ScoringContext(BaseModel):
    """
    Context for a readiness scoring operation.

    Contains the candidate, policy profile, and any
    additional configuration for the scoring operation.
    """
    candidate_id: UUID
    candidate_type: str
    candidate_key: str

    # Policy
    policy_profile_id: str = "default"

    # Scoring options
    include_dimension_breakdown: bool = True
    include_raw_values: bool = True
    minimum_confidence: float = 0.3  # Minimum confidence to emit a decision

    # Metadata
    scored_at: datetime = Field(default_factory=datetime.now)
    scored_by: Optional[str] = None


# ============================================================================
# Score Breakdown
# ============================================================================

class ScoreBreakdown(BaseModel):
    """
    Detailed breakdown of a readiness score.

    Provides transparency into how each dimension contributed
    to the overall score and decision.
    """
    # Overall
    overall_score: float
    overall_confidence: float

    # Dimension scores
    dimension_scores: Dict[str, float] = Field(default_factory=dict)

    # Dimension weights applied
    dimension_weights: Dict[str, float] = Field(default_factory=dict)

    # Dimension contributions (weight * score)
    dimension_contributions: Dict[str, float] = Field(default_factory=dict)

    # Evidence summary
    evidence_summary: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    # Raw values from collectors
    raw_values: Dict[str, Dict[str, float]] = Field(default_factory=dict)

    # Hard blocks
    hard_blocks: List[str] = Field(default_factory=list)

    # Warnings
    warnings: List[str] = Field(default_factory=list)

    # Scoring metadata
    scored_at: datetime = Field(default_factory=datetime.now)
    scoring_duration_ms: int = 0


# ============================================================================
# Scoring Engine
# ============================================================================

class ReadinessScoringEngine:
    """
    Computes readiness scores from collected evidence.

    Takes evidence from all dimension collectors, applies
    policy weights, evaluates hard blocks, and produces
    a readiness outcome with full audit trail.
    """

    def __init__(
        self,
        policy_registry=None,
        block_evaluator=None,
        policy_applicator=None
    ):
        """
        Initialize the scoring engine.

        Args:
            policy_registry: Policy registry instance
            block_evaluator: Hard block evaluator
            policy_applicator: Policy applicator
        """
        self.policy_registry = policy_registry or get_policy_registry()
        self.block_evaluator = block_evaluator or get_hard_block_evaluator()
        self.policy_applicator = policy_applicator or get_policy_applicator()

    async def score(
        self,
        collector_results: Dict[str, Any],
        context: ScoringContext
    ) -> ScoreBreakdown:
        """
        Compute readiness score from collector results.

        Args:
            collector_results: Results from evidence collectors
            context: Scoring context

        Returns:
            ScoreBreakdown with detailed score information
        """
        start_time = datetime.now()

        # Get policy profile
        profile = self.policy_registry.get_profile(context.policy_profile_id)
        if profile is None:
            profile = self.policy_registry.get_default_profile()

        # Extract dimension scores from collector results
        dimension_scores: Dict[str, float] = {}
        raw_values: Dict[str, Dict[str, float]] = {}
        evidence_summary: Dict[str, Dict[str, Any]] = {}
        warnings: List[str] = []

        for dimension_name, result in collector_results.items():
            if not result.has_sufficient_data:
                warnings.append(f"Insufficient data for {dimension_name}")
                dimension_scores[dimension_name] = 0.3  # Low score for missing data
                continue

            # Get normalized score from collector
            if result.normalized_scores:
                # Extract the score for this dimension
                dim_score = list(result.normalized_scores.values())[0]
                dimension_scores[dimension_name] = dim_score

            # Store raw values
            if result.raw_values:
                raw_values[dimension_name] = result.raw_values

            # Store evidence data
            if result.data:
                evidence_summary[dimension_name] = result.data

        # Map dimension names to policy dimensions
        policy_dimension_scores = self._map_to_policy_dimensions(dimension_scores)

        # Apply weights
        weights = profile.weights
        dimension_weights = {dim.value: weight for dim, weight in weights.items()}

        contributions = {}
        for dim_name, score in policy_dimension_scores.items():
            weight = dimension_weights.get(dim_name, 0.0)
            contributions[dim_name] = weight * score

        # Compute overall score
        overall_score = sum(contributions.values())

        # Compute confidence based on data completeness
        data_completeness = len([d for d in dimension_scores.values() if d > 0]) / len(self.policy_applicator.registry.list_profiles())
        confidence = min(0.5 + (data_completeness * 0.5), 1.0)

        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        return ScoreBreakdown(
            overall_score=overall_score,
            overall_confidence=confidence,
            dimension_scores=policy_dimension_scores,
            dimension_weights=dimension_weights,
            dimension_contributions=contributions,
            evidence_summary=evidence_summary,
            raw_values=raw_values,
            warnings=warnings,
            scoring_duration_ms=duration_ms,
        )

    def _map_to_policy_dimensions(
        self,
        dimension_scores: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Map collector dimension names to policy dimension names.

        Args:
            dimension_scores: Scores from collectors

        Returns:
            Dictionary mapping policy dimension names to scores
        """
        mapping = {
            "execution_stability": PolicyDimension.EXECUTION_STABILITY.value,
            "artifact_completeness": PolicyDimension.ARTIFACT_COMPLETENESS.value,
            "memory_confidence": PolicyDimension.MEMORY_CONFIDENCE.value,
            "insight_quality": PolicyDimension.INSIGHT_QUALITY.value,
            "pattern_confidence": PolicyDimension.PATTERN_CONFIDENCE.value,
            "audit_coverage": PolicyDimension.AUDIT_COVERAGE.value,
            "policy_compliance": PolicyDimension.POLICY_COMPLIANCE.value,
            "operational_consistency": PolicyDimension.OPERATIONAL_CONSISTENCY.value,
        }

        result = {}
        for collector_dim, policy_dim in mapping.items():
            if collector_dim in dimension_scores:
                result[policy_dim] = dimension_scores[collector_dim]

        return result

    async def evaluate(
        self,
        collector_results: Dict[str, Any],
        context: ScoringContext,
        previous_state: Optional[ReadinessState] = None,
        previous_score: Optional[float] = None,
    ) -> ReadinessEvaluation:
        """
        Perform complete readiness evaluation.

        Args:
            collector_results: Results from evidence collectors
            context: Scoring context
            previous_state: Previous readiness state
            previous_score: Previous overall score

        Returns:
            Complete ReadinessEvaluation with decision
        """
        start_time = datetime.now()

        # Get policy profile
        profile = self.policy_registry.get_profile(context.policy_profile_id)
        if profile is None:
            profile = self.policy_registry.get_default_profile()

        # Compute score breakdown
        breakdown = await self.score(collector_results, context)

        # Build ReadinessScore
        score = ReadinessScore(
            overall_score=breakdown.overall_score,
            confidence=breakdown.overall_confidence,
            execution_stability=breakdown.dimension_scores.get(PolicyDimension.EXECUTION_STABILITY.value, 0.0),
            artifact_completeness=breakdown.dimension_scores.get(PolicyDimension.ARTIFACT_COMPLETENESS.value, 0.0),
            memory_confidence=breakdown.dimension_scores.get(PolicyDimension.MEMORY_CONFIDENCE.value, 0.0),
            insight_quality=breakdown.dimension_scores.get(PolicyDimension.INSIGHT_QUALITY.value, 0.0),
            pattern_confidence=breakdown.dimension_scores.get(PolicyDimension.PATTERN_CONFIDENCE.value, 0.0),
            audit_coverage=breakdown.dimension_scores.get(PolicyDimension.AUDIT_COVERAGE.value, 0.0),
            policy_compliance=breakdown.dimension_scores.get(PolicyDimension.POLICY_COMPLIANCE.value, 0.0),
            operational_consistency=breakdown.dimension_scores.get(PolicyDimension.OPERATIONAL_CONSISTENCY.value, 0.0),
            hard_blocks=breakdown.hard_blocks,
            warnings=breakdown.warnings,
            dimension_weights=breakdown.dimension_weights,
            dimension_scores_raw=breakdown.raw_values,
            computed_at=breakdown.scored_at,
        )

        # Determine outcome
        outcome, recommended_state, reason, should_transition = self.policy_applicator.determine_outcome(
            profile, score, previous_state, previous_score
        )

        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        # Create evaluation record
        evaluation = ReadinessEvaluation(
            candidate_id=context.candidate_id,
            evaluation_type="scheduled",
            evidence=await self._build_evidence_summary(collector_results),
            score=score,
            outcome=outcome,
            recommended_state=recommended_state,
            reason=reason,
            policy_profile_id=context.policy_profile_id,
            previous_state=previous_state,
            previous_score=previous_score,
            should_transition=should_transition,
            evaluated_at=breakdown.scored_at,
            evaluation_duration_ms=duration_ms,
        )

        return evaluation

    async def _build_evidence_summary(
        self,
        collector_results: Dict[str, Any]
    ) -> EvidenceSummary:
        """Build EvidenceSummary from collector results."""
        summary = EvidenceSummary()

        # Aggregate evidence from all collectors
        for result in collector_results.values():
            if not result.has_sufficient_data:
                continue

            data = result.data

            # Map to evidence summary fields
            if "total_executions" in data:
                summary.execution_count = data.get("total_executions", 0)
                summary.success_rate = data.get("successful_executions", 0) / max(data.get("total_executions", 1), 0.0)

            if "total_artifacts" in data:
                summary.artifact_count = data.get("total_artifacts", 0)
                summary.artifact_completeness_rate = data.get("complete_artifacts", 0) / max(data.get("total_artifacts", 1), 0.0)

            if "governed_memory_count" in data:
                summary.governed_memory_count = data.get("governed_memory_count", 0)
                summary.memory_confidence_score = data.get("avg_confidence_score", 0.0)

            if "approved_insight_count" in data:
                summary.approved_insight_count = data.get("approved_insight_count", 0)
                summary.insight_quality_score = data.get("avg_quality_score", 0.0)

            if "validated_pattern_count" in data:
                summary.validated_pattern_count = data.get("validated_pattern_count", 0)
                summary.pattern_confidence_score = data.get("avg_confidence_score", 0.0)

            if "total_retrievals" in data:
                summary.audit_coverage_score = data.get("audit_log_completeness", 0.0)

            if "last_execution_at" in data:
                summary.last_execution_at = datetime.fromisoformat(data["last_execution_at"])

            if "last_validated_at" in data:
                summary.last_memory_validated_at = datetime.fromisoformat(data["last_validated_at"])

        # Compute overall freshness
        summary.total_evidence_sources = len([r for r in collector_results.values() if r.has_sufficient_data])

        return summary


# Global scoring engine instance
_scoring_engine: Optional[ReadinessScoringEngine] = None


def get_scoring_engine() -> ReadinessScoringEngine:
    """Get the global scoring engine instance."""
    global _scoring_engine
    if _scoring_engine is None:
        _scoring_engine = ReadinessScoringEngine()
    return _scoring_engine


async def compute_readiness_score(
    collector_results: Dict[str, Any],
    context: ScoringContext,
    previous_state: Optional[ReadinessState] = None,
    previous_score: Optional[float] = None
) -> ReadinessEvaluation:
    """
    Compute readiness score from collector results.

    Convenience function that uses the global scoring engine.

    Args:
        collector_results: Results from evidence collectors
        context: Scoring context
        previous_state: Previous readiness state
        previous_score: Previous overall score

    Returns:
        Complete ReadinessEvaluation with decision
    """
    engine = get_scoring_engine()
    return await engine.evaluate(collector_results, context, previous_state, previous_score)
