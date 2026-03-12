"""
TORQ Readiness Checker - Regression Service

Milestone 5: Service for detecting and managing readiness regressions.

Provides high-level interface for regression detection, tracking,
and resolution management.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


logger = logging.getLogger(__name__)


# Import from hardening layer
from ..hardening.regression_detector import (
    RegressionDetector,
    RegressionEvent,
    RegressionSeverity,
    get_regression_detector,
)

# Import models
from ..readiness_models import (
    ReadinessState,
    ReadinessCandidate,
)


# ============================================================================
# Regression Summary
# ============================================================================

class RegressionSummary(BaseModel):
    """
    Summary of regression status.
    """
    total_regressions: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    unresolved_count: int
    resolved_count: int

    recent_regressions: List[RegressionEvent]


# ============================================================================
# Regression Service
# ============================================================================

class RegressionService:
    """
    Service for managing readiness regressions.

    Provides detection, tracking, and resolution capabilities
    for readiness degradation events.
    """

    def __init__(self):
        """Initialize the regression service."""
        self.detector = get_regression_detector()

    def detect_and_record(
        self,
        candidate: ReadinessCandidate,
        previous_state: ReadinessState,
        new_state: ReadinessState,
        previous_score: float,
        new_score: float,
        previous_evaluation_id: Optional[UUID] = None,
        new_evaluation_id: Optional[UUID] = None,
        dimension_scores: Optional[Dict[str, float]] = None,
        hard_blocks: Optional[List[str]] = None,
    ) -> Optional[RegressionEvent]:
        """
        Detect and record a regression if it occurred.

        Args:
            candidate: The candidate being evaluated
            previous_state: Previous readiness state
            new_state: New readiness state
            previous_score: Previous readiness score
            new_score: New readiness score
            previous_evaluation_id: Previous evaluation ID
            new_evaluation_id: New evaluation ID
            dimension_scores: Optional dimension breakdown
            hard_blocks: Optional hard block reasons

        Returns:
            RegressionEvent if regression detected, None otherwise
        """
        return self.detector.detect_regression(
            candidate_id=candidate.id,
            candidate_type=candidate.candidate_type.value,
            title=candidate.title,
            previous_state=previous_state,
            new_state=new_state,
            previous_score=previous_score,
            new_score=new_score,
            previous_evaluation_id=previous_evaluation_id,
            new_evaluation_id=new_evaluation_id,
            dimension_scores=dimension_scores,
            hard_blocks=hard_blocks,
        )

    def list_regressions(
        self,
        severity: Optional[RegressionSeverity] = None,
        resolved_only: bool = False,
        unresolved_only: bool = False,
        limit: int = 100,
    ) -> List[RegressionEvent]:
        """
        List regression events with optional filtering.

        Args:
            severity: Optional severity filter
            resolved_only: Only show resolved regressions
            unresolved_only: Only show unresolved regressions
            limit: Maximum number of events

        Returns:
            List of matching regression events
        """
        return self.detector.get_regressions(
            severity=severity,
            resolved_only=resolved_only,
            unresolved_only=unresolved_only,
            limit=limit,
        )

    def get_candidate_regressions(
        self,
        candidate_id: UUID,
        unresolved_only: bool = False,
    ) -> List[RegressionEvent]:
        """
        Get regression events for a specific candidate.

        Args:
            candidate_id: ID of the candidate
            unresolved_only: Only show unresolved regressions

        Returns:
            List of regression events for the candidate
        """
        return self.detector.get_regressions(
            candidate_id=candidate_id,
            unresolved_only=unresolved_only,
        )

    def resolve_regression(
        self,
        regression_id: UUID,
        resolution_notes: Optional[str] = None,
    ) -> bool:
        """
        Mark a regression event as resolved.

        Args:
            regression_id: ID of the regression event
            resolution_notes: Optional notes about resolution

        Returns:
            True if regression was resolved, False if not found
        """
        return self.detector.resolve_regression(
            regression_id=regression_id,
            resolution_notes=resolution_notes,
        )

    def get_summary(self) -> RegressionSummary:
        """
        Get a summary of regression status.

        Returns:
            RegressionSummary with counts and recent events
        """
        counts = self.detector.get_regression_count()
        recent = self.detector.get_regressions(limit=10)

        return RegressionSummary(
            total_regressions=counts["total"],
            critical_count=counts["critical"],
            high_count=counts["high"],
            medium_count=counts["medium"],
            low_count=counts["low"],
            unresolved_count=counts["unresolved"],
            resolved_count=counts["total"] - counts["unresolved"],
            recent_regressions=recent,
        )

    def get_unresolved_by_severity(self) -> Dict[str, List[RegressionEvent]]:
        """
        Get unresolved regressions grouped by severity.

        Returns:
            Dictionary mapping severity to list of unresolved events
        """
        result = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
        }

        unresolved = self.detector.get_regressions(unresolved_only=True)

        for event in unresolved:
            result[event.severity.value].append(event)

        return result


# Global regression service instance
_regression_service: Optional[RegressionService] = None


def get_regression_service() -> RegressionService:
    """Get the global regression service instance."""
    global _regression_service
    if _regression_service is None:
        _regression_service = RegressionService()
    return _regression_service
