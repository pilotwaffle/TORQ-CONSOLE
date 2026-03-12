"""
TORQ Readiness Checker - Scoring Validation Service

Milestone 5: Service for scoring stability validation.

Provides interface for tracking score history and validating
stability across multiple evaluations.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


logger = logging.getLogger(__name__)


# Import from hardening layer
from ..hardening.scoring_stability_validator import (
    ScoringStabilityValidator,
    ScoreHistoryEntry,
    StabilityReport,
    get_scoring_stability_validator,
)


# ============================================================================
# System Stability Summary
# ============================================================================

class SystemStabilitySummary(BaseModel):
    """
    Summary of scoring stability across all candidates.
    """
    total_candidates: int
    stable_candidates: int
    unstable_candidates: int
    insufficient_data: int

    stability_threshold: float

    unstable_candidates_list: List[Dict[str, Any]]


# ============================================================================
# Scoring Validation Service
# ============================================================================

class ScoringValidationService:
    """
    Service for scoring stability validation.

    Tracks score history, computes stability metrics,
    and detects anomalous evaluations.
    """

    def __init__(self):
        """Initialize the scoring validation service."""
        self.validator = get_scoring_stability_validator()

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
            evaluated_at: When the evaluation occurred
        """
        self.validator.record_evaluation(
            candidate_id=candidate_id,
            score=score,
            evaluation_id=evaluation_id,
            dimension_scores=dimension_scores,
            evaluated_at=evaluated_at,
        )

    def validate_score_stability(
        self,
        candidate_id: UUID,
        window: Optional[int] = None,
    ) -> Optional[StabilityReport]:
        """
        Validate scoring stability for a candidate.

        Args:
            candidate_id: ID of the candidate
            window: Optional limit on evaluations to consider

        Returns:
            StabilityReport with metrics, or None if insufficient data
        """
        return self.validator.calculate_stability(
            candidate_id=candidate_id,
            window=window,
        )

    def is_candidate_stable(
        self,
        candidate_id: UUID,
        window: Optional[int] = None,
    ) -> Optional[bool]:
        """
        Quick check if a candidate's scores are stable.

        Args:
            candidate_id: ID of the candidate
            window: Optional limit on evaluations to consider

        Returns:
            True if stable, False if unstable, None if insufficient data
        """
        report = self.validate_score_stability(candidate_id, window)
        return report.is_stable if report else None

    def get_score_history(
        self,
        candidate_id: UUID,
        limit: Optional[int] = None,
    ) -> List[ScoreHistoryEntry]:
        """
        Get score history for a candidate.

        Args:
            candidate_id: ID of the candidate
            limit: Optional limit on entries

        Returns:
            List of score history entries
        """
        return self.validator.get_score_history(
            candidate_id=candidate_id,
            limit=limit,
        )

    def detect_anomalies(
        self,
        candidate_id: UUID,
        threshold_std: float = 2.0,
    ) -> List[ScoreHistoryEntry]:
        """
        Detect anomalous scores for a candidate.

        Args:
            candidate_id: ID of the candidate
            threshold_std: Standard deviation threshold for outliers

        Returns:
            List of anomalous score entries
        """
        return self.validator.detect_anomalies(
            candidate_id=candidate_id,
            threshold_std=threshold_std,
        )

    def calculate_score_variance(
        self,
        candidate_id: UUID,
        window: Optional[int] = None,
    ) -> Optional[float]:
        """
        Calculate score variance for a candidate.

        Args:
            candidate_id: ID of the candidate
            window: Optional limit on evaluations to consider

        Returns:
            Standard deviation of scores, or None if insufficient data
        """
        report = self.validate_score_stability(candidate_id, window)
        return report.std_deviation if report else None

    def get_system_summary(self) -> SystemStabilitySummary:
        """
        Get system-wide stability summary.

        Returns:
            SystemStabilitySummary with aggregate statistics
        """
        summary = self.validator.get_system_stability_summary()

        # Find unstable candidates
        unstable_list = []
        for candidate_id in self.validator._score_history:
            report = self.validator.calculate_stability(candidate_id)
            if report and not report.is_stable:
                unstable_list.append({
                    "candidate_id": str(candidate_id),
                    "std_deviation": report.std_deviation,
                    "score_range": report.score_range,
                    "evaluation_count": report.evaluation_count,
                })

        return SystemStabilitySummary(
            total_candidates=summary["total_candidates"],
            stable_candidates=summary["stable_candidates"],
            unstable_candidates=summary["unstable_candidates"],
            insufficient_data=summary["insufficient_data"],
            stability_threshold=summary["stability_threshold"],
            unstable_candidates_list=unstable_list,
        )

    def get_stability_threshold(self) -> float:
        """
        Get the current stability threshold.

        Returns:
            Maximum allowed standard deviation for stable scores
        """
        return self.validator.stability_threshold

    def clear_history(
        self,
        candidate_id: Optional[UUID] = None,
    ):
        """
        Clear score history.

        Args:
            candidate_id: ID of candidate to clear, or None for all
        """
        self.validator.clear_history(candidate_id=candidate_id)


# Global scoring validation service instance
_scoring_validation_service: Optional[ScoringValidationService] = None


def get_scoring_validation_service() -> ScoringValidationService:
    """Get the global scoring validation service instance."""
    global _scoring_validation_service
    if _scoring_validation_service is None:
        _scoring_validation_service = ScoringValidationService()
    return _scoring_validation_service
