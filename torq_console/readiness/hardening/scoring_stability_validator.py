"""
TORQ Readiness Checker - Scoring Stability Validator

Milestone 5: Ensure deterministic scoring across repeated evaluations.

Validates that readiness scoring produces consistent results across
multiple evaluation runs, detecting instability and variance issues.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID
from statistics import stdev, mean

from pydantic import BaseModel


logger = logging.getLogger(__name__)


# ============================================================================
# Score History Entry
# ============================================================================

class ScoreHistoryEntry(BaseModel):
    """
    A single score measurement for a candidate.
    """
    candidate_id: UUID
    score: float
    evaluated_at: datetime
    evaluation_id: UUID
    dimension_scores: Optional[Dict[str, float]] = None

    class Config:
        use_enum_values = True


# ============================================================================
# Stability Report
# ============================================================================

class StabilityReport(BaseModel):
    """
    Report on scoring stability for a candidate.
    """
    candidate_id: UUID
    evaluation_count: int

    mean_score: float
    median_score: float
    std_deviation: float
    min_score: float
    max_score: float
    score_range: float

    is_stable: bool
    stability_threshold: float

    dimension_stability: Dict[str, Dict[str, float]]

    first_evaluated_at: Optional[datetime] = None
    last_evaluated_at: Optional[datetime] = None

    warnings: List[str] = []

    class Config:
        use_enum_values = True


# ============================================================================
# Scoring Stability Validator
# ============================================================================

class ScoringStabilityValidator:
    """
    Validates scoring stability across multiple evaluations.

    Ensures that repeated evaluations produce consistent scores,
    detecting instability that could indicate:
    - Flaky evidence collection
    - Non-deterministic scoring logic
    - External dependency issues
    """

    # Maximum allowed standard deviation for stable scores
    DEFAULT_STABILITY_THRESHOLD = 0.05

    # Minimum evaluations required to assess stability
    MIN_EVALUATIONS_FOR_STABILITY = 3

    def __init__(self, stability_threshold: float = DEFAULT_STABILITY_THRESHOLD):
        """
        Initialize the stability validator.

        Args:
            stability_threshold: Maximum allowed standard deviation
        """
        self.stability_threshold = stability_threshold
        # Score history per candidate
        self._score_history: Dict[UUID, List[ScoreHistoryEntry]] = {}

    def record_evaluation(
        self,
        candidate_id: UUID,
        score: float,
        evaluation_id: UUID,
        dimension_scores: Optional[Dict[str, float]] = None,
        evaluated_at: Optional[datetime] = None,
    ):
        """
        Record a score evaluation for stability tracking.

        Args:
            candidate_id: ID of the candidate
            score: Overall readiness score
            evaluation_id: ID of the evaluation
            dimension_scores: Optional dimension breakdown
            evaluated_at: When the evaluation occurred (defaults to now)
        """
        entry = ScoreHistoryEntry(
            candidate_id=candidate_id,
            score=score,
            evaluated_at=evaluated_at or datetime.now(),
            evaluation_id=evaluation_id,
            dimension_scores=dimension_scores,
        )

        if candidate_id not in self._score_history:
            self._score_history[candidate_id] = []

        self._score_history[candidate_id].append(entry)

        logger.debug(
            f"[StabilityValidator] Recorded score {score:.3f} "
            f"for candidate {str(candidate_id)[:8]} "
            f"(eval #{len(self._score_history[candidate_id])})"
        )

    def calculate_stability(
        self,
        candidate_id: UUID,
        window: Optional[int] = None,
    ) -> Optional[StabilityReport]:
        """
        Calculate stability metrics for a candidate.

        Args:
            candidate_id: ID of the candidate
            window: Optional limit on number of recent evaluations to consider

        Returns:
            StabilityReport with metrics, or None if insufficient data
        """
        history = self._score_history.get(candidate_id, [])

        if window:
            history = history[-window:]

        if len(history) < 2:
            return None

        scores = [entry.score for entry in history]

        # Calculate statistics
        mean_score = mean(scores)
        median_score = sorted(scores)[len(scores) // 2]
        std_dev = stdev(scores) if len(scores) > 1 else 0.0
        min_score = min(scores)
        max_score = max(scores)
        score_range = max_score - min_score

        # Determine stability
        is_stable = std_dev <= self.stability_threshold

        # Calculate dimension stability
        dimension_stability = self._calculate_dimension_stability(history)

        # Generate warnings
        warnings = []
        if not is_stable:
            warnings.append(
                f"Score variance (σ={std_dev:.3f}) exceeds threshold "
                f"(threshold={self.stability_threshold:.3f})"
            )

        if score_range > 0.2:
            warnings.append(
                f"Large score range detected: {min_score:.2f} - {max_score:.2f}"
            )

        # Get time range
        first_at = min(e.evaluated_at for e in history) if history else None
        last_at = max(e.evaluated_at for e in history) if history else None

        report = StabilityReport(
            candidate_id=candidate_id,
            evaluation_count=len(history),
            mean_score=mean_score,
            median_score=median_score,
            std_deviation=std_dev,
            min_score=min_score,
            max_score=max_score,
            score_range=score_range,
            is_stable=is_stable,
            stability_threshold=self.stability_threshold,
            dimension_stability=dimension_stability,
            first_evaluated_at=first_at,
            last_evaluated_at=last_at,
            warnings=warnings,
        )

        return report

    def _calculate_dimension_stability(
        self,
        history: List[ScoreHistoryEntry],
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate stability metrics for each dimension.

        Args:
            history: Score history entries

        Returns:
            Dictionary mapping dimension names to stability stats
        """
        dimension_data: Dict[str, List[float]] = {}

        for entry in history:
            if entry.dimension_scores:
                for dim, score in entry.dimension_scores.items():
                    if dim not in dimension_data:
                        dimension_data[dim] = []
                    dimension_data[dim].append(score)

        stability = {}
        for dim, scores in dimension_data.items():
            if len(scores) >= 2:
                dim_mean = mean(scores)
                dim_std = stdev(scores)
                stability[dim] = {
                    "mean": dim_mean,
                    "std_deviation": dim_std,
                    "is_stable": dim_std <= self.stability_threshold,
                    "sample_count": len(scores),
                }
            else:
                stability[dim] = {
                    "mean": scores[0] if scores else 0.0,
                    "std_deviation": 0.0,
                    "is_stable": True,
                    "sample_count": len(scores),
                }

        return stability

    def is_score_stable(
        self,
        candidate_id: UUID,
        window: Optional[int] = None,
    ) -> bool:
        """
        Quick check if a candidate's scores are stable.

        Args:
            candidate_id: ID of the candidate
            window: Optional limit on evaluations to consider

        Returns:
            True if scores are stable, False otherwise or insufficient data
        """
        report = self.calculate_stability(candidate_id, window)
        return report.is_stable if report else False

    def get_score_history(
        self,
        candidate_id: UUID,
        limit: Optional[int] = None,
    ) -> List[ScoreHistoryEntry]:
        """
        Get score history for a candidate.

        Args:
            candidate_id: ID of the candidate
            limit: Optional limit on number of entries

        Returns:
            List of score history entries
        """
        history = self._score_history.get(candidate_id, [])

        if limit:
            history = history[-limit:]

        return history

    def detect_anomalies(
        self,
        candidate_id: UUID,
        threshold_std: float = 2.0,
    ) -> List[ScoreHistoryEntry]:
        """
        Detect anomalous scores (outliers) for a candidate.

        Args:
            candidate_id: ID of the candidate
            threshold_std: Number of standard deviations for outlier detection

        Returns:
            List of anomalous score entries
        """
        history = self._score_history.get(candidate_id, [])

        if len(history) < self.MIN_EVALUATIONS_FOR_STABILITY:
            return []

        scores = [entry.score for entry in history]
        mean_score = mean(scores)
        std = stdev(scores) if len(scores) > 1 else 0.0

        if std == 0:
            return []

        anomalies = []
        for entry in history:
            z_score = abs(entry.score - mean_score) / std
            if z_score > threshold_std:
                anomalies.append(entry)

        return anomalies

    def get_system_stability_summary(self) -> Dict[str, Any]:
        """
        Get system-wide stability summary.

        Returns:
            Dictionary with stability statistics
        """
        total_candidates = len(self._score_history)
        stable_count = 0
        unstable_count = 0
        insufficient_data = 0

        for candidate_id in self._score_history:
            report = self.calculate_stability(candidate_id)
            if report is None:
                insufficient_data += 1
            elif report.is_stable:
                stable_count += 1
            else:
                unstable_count += 1

        return {
            "total_candidates": total_candidates,
            "stable_candidates": stable_count,
            "unstable_candidates": unstable_count,
            "insufficient_data": insufficient_data,
            "stability_threshold": self.stability_threshold,
        }

    def clear_history(self, candidate_id: Optional[UUID] = None):
        """
        Clear score history for a candidate or all candidates.

        Args:
            candidate_id: ID of candidate to clear, or None for all
        """
        if candidate_id:
            if candidate_id in self._score_history:
                del self._score_history[candidate_id]
                logger.info(
                    f"[StabilityValidator] Cleared history for candidate {str(candidate_id)[:8]}"
                )
        else:
            self._score_history.clear()
            logger.info("[StabilityValidator] Cleared all history")


# Global scoring stability validator instance
_stability_validator: Optional[ScoringStabilityValidator] = None


def get_scoring_stability_validator() -> ScoringStabilityValidator:
    """Get the global scoring stability validator instance."""
    global _stability_validator
    if _stability_validator is None:
        _stability_validator = ScoringStabilityValidator()
    return _stability_validator
