"""
TORQ Readiness Checker - Regression Detector

Milestone 5: Detect readiness degradation over time.

Identifies when candidates regress from higher readiness states
to lower states, tracking score drops and policy violations.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID
from enum import Enum

from pydantic import BaseModel


logger = logging.getLogger(__name__)


# Import readiness models
from ..readiness_models import ReadinessState


# ============================================================================
# Regression Severity
# ============================================================================

class RegressionSeverity(str, Enum):
    """Severity levels for regression events."""
    CRITICAL = "critical"  # READY → BLOCKED or major score drop
    HIGH = "high"  # READY → REGRESSED or WATCHLIST
    MEDIUM = "medium"  # WATCHLIST → BLOCKED or score drop
    LOW = "low"  # Minor score changes


# ============================================================================
# Regression Event Model
# ============================================================================

class RegressionEvent(BaseModel):
    """
    Record of a detected regression event.

    Captures the details of when a candidate's readiness degraded.
    """
    id: UUID
    candidate_id: UUID
    candidate_type: str
    title: str

    previous_state: str
    new_state: str

    previous_score: float
    new_score: float
    score_delta: float

    severity: RegressionSeverity
    reason: str

    dimensions_affected: List[str]

    detected_at: datetime
    first_evaluation_id: Optional[UUID] = None
    previous_evaluation_id: Optional[UUID] = None

    is_resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None

    class Config:
        use_enum_values = True


# ============================================================================
# Regression Detector
# ============================================================================

class RegressionDetector:
    """
    Detects readiness regression events.

    Monitors candidates for:
    - State transitions to lower readiness
    - Score drops below thresholds
    - Evidence confidence degradation
    - New policy violations
    """

    # State hierarchy (higher index = higher readiness)
    STATE_HIERARCHY = {
        ReadinessState.BLOCKED: 0,
        ReadinessState.REGRESSED: 1,
        ReadinessState.OBSERVED: 2,
        ReadinessState.WATCHLIST: 3,
        ReadinessState.READY: 4,
    }

    # Score drop thresholds for severity
    CRITICAL_SCORE_DROP = 0.30
    HIGH_SCORE_DROP = 0.20
    MEDIUM_SCORE_DROP = 0.10

    def __init__(self):
        # Storage for regression events
        self._regression_events: Dict[UUID, List[RegressionEvent]] = {}
        # Track previous scores per candidate
        self._previous_scores: Dict[UUID, float] = {}
        # Track previous states per candidate
        self._previous_states: Dict[UUID, ReadinessState] = {}

    def detect_regression(
        self,
        candidate_id: UUID,
        candidate_type: str,
        title: str,
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
        Detect if a transition represents a regression.

        Args:
            candidate_id: ID of the candidate
            candidate_type: Type of candidate
            title: Candidate title
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
        # Get state hierarchy positions
        prev_level = self.STATE_HIERARCHY.get(previous_state, -1)
        new_level = self.STATE_HIERARCHY.get(new_state, -1)

        # Check for state regression
        state_regressed = new_level < prev_level

        # Check for score regression
        score_delta = new_score - previous_score
        score_regressed = score_delta < -self.MEDIUM_SCORE_DROP

        # Determine if this is a regression event
        is_regression = state_regressed or score_regressed

        if not is_regression:
            # Update tracking for next time
            self._previous_scores[candidate_id] = new_score
            self._previous_states[candidate_id] = new_state
            return None

        # Determine severity
        severity = self._calculate_severity(
            previous_state, new_state, previous_score, new_score
        )

        # Build reason
        reason_parts = []
        if state_regressed:
            reason_parts.append(f"State: {previous_state.value} → {new_state.value}")
        if score_regressed:
            reason_parts.append(f"Score: {previous_score:.2f} → {new_score:.2f}")

        reason = ", ".join(reason_parts)

        # Identify affected dimensions
        dimensions_affected = []
        if dimension_scores:
            for dim, score in dimension_scores.items():
                if score < 0.7:  # Below acceptable threshold
                    dimensions_affected.append(dim)

        if hard_blocks:
            dimensions_affected.extend(hard_blocks)

        # Create regression event
        event = RegressionEvent(
            id=new_evaluation_id or UUID('00000000-0000-0000-0000-000000000000'),
            candidate_id=candidate_id,
            candidate_type=candidate_type,
            title=title,
            previous_state=previous_state.value,
            new_state=new_state.value,
            previous_score=previous_score,
            new_score=new_score,
            score_delta=score_delta,
            severity=severity,
            reason=reason,
            dimensions_affected=dimensions_affected,
            detected_at=datetime.now(),
            previous_evaluation_id=previous_evaluation_id,
            first_evaluation_id=new_evaluation_id,
        )

        # Store event
        if candidate_id not in self._regression_events:
            self._regression_events[candidate_id] = []
        self._regression_events[candidate_id].append(event)

        # Update tracking
        self._previous_scores[candidate_id] = new_score
        self._previous_states[candidate_id] = new_state

        logger.warning(
            f"[RegressionDetector] Regression detected for {candidate_type} "
            f"{str(candidate_id)[:8]}: {reason} "
            f"(severity: {severity.value})"
        )

        return event

    def _calculate_severity(
        self,
        previous_state: ReadinessState,
        new_state: ReadinessState,
        previous_score: float,
        new_score: float,
    ) -> RegressionSeverity:
        """Calculate regression severity based on state and score changes."""
        score_drop = previous_score - new_score

        # Critical: READY → BLOCKED or large score drop
        if (
            previous_state == ReadinessState.READY and
            new_state == ReadinessState.BLOCKED
        ) or score_drop >= self.CRITICAL_SCORE_DROP:
            return RegressionSeverity.CRITICAL

        # High: READY → REGRESSED or significant score drop
        if (
            previous_state == ReadinessState.READY and
            new_state in [ReadinessState.REGRESSED, ReadinessState.WATCHLIST]
        ) or score_drop >= self.HIGH_SCORE_DROP:
            return RegressionSeverity.HIGH

        # Medium: Medium score drop or moderate state drop
        if score_drop >= self.MEDIUM_SCORE_DROP:
            return RegressionSeverity.MEDIUM

        # Low: Minor changes
        return RegressionSeverity.LOW

    def get_regressions(
        self,
        candidate_id: Optional[UUID] = None,
        severity: Optional[RegressionSeverity] = None,
        resolved_only: bool = False,
        unresolved_only: bool = False,
        limit: int = 100,
    ) -> List[RegressionEvent]:
        """
        Get regression events with optional filtering.

        Args:
            candidate_id: Optional candidate filter
            severity: Optional severity filter
            resolved_only: Only show resolved regressions
            unresolved_only: Only show unresolved regressions
            limit: Maximum number of events

        Returns:
            List of matching regression events
        """
        events = []

        if candidate_id:
            candidate_events = self._regression_events.get(candidate_id, [])
            events.extend(candidate_events)
        else:
            for candidate_events in self._regression_events.values():
                events.extend(candidate_events)

        # Apply filters
        filtered = events

        if severity:
            # Convert enum to string for comparison since event.severity is stored as string
            severity_str = severity if isinstance(severity, str) else severity.value
            filtered = [e for e in filtered if e.severity == severity_str]

        if resolved_only:
            filtered = [e for e in filtered if e.is_resolved]

        if unresolved_only:
            filtered = [e for e in filtered if not e.is_resolved]

        # Sort by detection time (most recent first)
        filtered.sort(key=lambda e: e.detected_at, reverse=True)

        return filtered[:limit]

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
        for candidate_events in self._regression_events.values():
            for event in candidate_events:
                if event.id == regression_id:
                    event.is_resolved = True
                    event.resolved_at = datetime.now()
                    event.resolution_notes = resolution_notes
                    logger.info(
                        f"[RegressionDetector] Resolved regression {str(regression_id)[:8]}: "
                        f"{resolution_notes or 'No notes'}"
                    )
                    return True

        return False

    def get_regression_count(self) -> Dict[str, int]:
        """
        Get count of regressions by severity.

        Returns:
            Dictionary with severity counts
        """
        counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "total": 0,
            "unresolved": 0,
        }

        for events in self._regression_events.values():
            for event in events:
                # severity is stored as string due to Pydantic use_enum_values=True
                severity_value = event.severity if isinstance(event.severity, str) else event.severity.value
                counts[severity_value] += 1
                counts["total"] += 1
                if not event.is_resolved:
                    counts["unresolved"] += 1

        return counts


# Global regression detector instance
_regression_detector: Optional[RegressionDetector] = None


def get_regression_detector() -> RegressionDetector:
    """Get the global regression detector instance."""
    global _regression_detector
    if _regression_detector is None:
        _regression_detector = RegressionDetector()
    return _regression_detector
