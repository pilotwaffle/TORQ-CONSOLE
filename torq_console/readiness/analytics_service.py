"""
TORQ Readiness Checker - Analytics Service

Milestone 4: Aggregate readiness statistics and metrics.

Provides system-wide analytics for dashboards and reporting.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from statistics import median
from pydantic import BaseModel

from .readiness_models import (
    ReadinessState,
    ReadinessCandidate,
    CandidateType,
)
from .inspection_models import (
    StateDistribution,
    ReadinessMetrics,
    ReadinessTrend,
)
from .query_service import (
    get_query_service,
    get_candidate_storage,
    get_all_evaluations,
)
from .audit_service import (
    get_audit_service,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Analytics Service
# ============================================================================

class ReadinessAnalyticsService:
    """
    Service for computing readiness analytics.

    Provides aggregated metrics, state distributions, and trends
    for operational dashboards and reporting.
    """

    def __init__(self):
        self.query_service = get_query_service()
        self.audit_service = get_audit_service()

    def get_metrics(self) -> ReadinessMetrics:
        """
        Get comprehensive readiness metrics.

        Returns:
            ReadinessMetrics with system-wide statistics
        """
        candidates = list(get_candidate_storage().values())

        # Total candidates
        total_count = len(candidates)

        # State distribution
        state_counts = self.query_service.count_by_state()
        state_distribution = self._compute_state_distribution(state_counts, total_count)

        # Compute scores
        scores = self._get_all_scores()

        # Score statistics
        avg_score = sum(scores) / len(scores) if scores else 0.0
        median_score_val = median(scores) if scores else 0.0
        min_score = min(scores) if scores else 0.0
        max_score = max(scores) if scores else 0.0

        # Count by state
        ready_count = state_counts.get("ready", 0)
        blocked_count = state_counts.get("blocked", 0)
        regressed_count = state_counts.get("regressed", 0)

        # Block reasons
        block_reasons = self._get_block_reasons()

        # Promotion metrics
        promotion_rate, avg_promotion_time = self._compute_promotion_metrics()

        # Regression metrics
        regression_rate = regressed_count / total_count if total_count > 0 else 0.0

        # Policy compliance
        policy_compliance = self._compute_policy_compliance(candidates)

        # Trends
        ready_trend = self._compute_ready_trend()
        regression_trend = self._compute_regression_trend()

        return ReadinessMetrics(
            total_candidates=total_count,
            state_distribution=state_distribution,
            promotion_rate=promotion_rate,
            avg_promotion_time_days=avg_promotion_time,
            regression_rate=regression_rate,
            regressed_count=regressed_count,
            blocked_count=blocked_count,
            block_reasons=block_reasons,
            avg_score=avg_score,
            median_score=median_score_val,
            min_score=min_score,
            max_score=max_score,
            policy_compliance_rate=policy_compliance,
            ready_trend=ready_trend,
            regression_trend=regression_trend,
        )

    def get_state_distribution(self) -> List[StateDistribution]:
        """
        Get distribution of candidates across readiness states.

        Returns:
            List of StateDistribution entries
        """
        state_counts = self.query_service.count_by_state()
        total = sum(state_counts.values())

        return self._compute_state_distribution(state_counts, total)

    def get_promotion_rate(self, days: int = 30) -> float:
        """
        Compute promotion rate over a time period.

        Args:
            days: Number of days to look back

        Returns:
            Promotion rate (0.0 - 1.0)
        """
        promotion_rate, _ = self._compute_promotion_metrics(days)
        return promotion_rate

    def get_regression_rate(self) -> float:
        """
        Get current regression rate.

        Returns:
            Regression rate (0.0 - 1.0)
        """
        candidates = list(get_candidate_storage().values())
        total = len(candidates)

        if total == 0:
            return 0.0

        regressed = sum(1 for c in candidates if c.current_state == ReadinessState.REGRESSED)
        return regressed / total

    def get_blocked_candidates(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get blocked candidates with blocking reasons.

        Args:
            limit: Maximum number of candidates

        Returns:
            List of blocked candidate summaries
        """
        blocked = []

        for candidate in get_candidate_storage().values():
            if candidate.current_state == ReadinessState.BLOCKED:
                # Get latest evaluation for blocking reasons
                evals = get_all_evaluations().get(candidate.id, [])
                latest = max(evals, key=lambda e: e.evaluated_at) if evals else None

                summary = {
                    "candidate_id": str(candidate.id),
                    "candidate_type": candidate.candidate_type.value,
                    "title": candidate.title,
                    "blocked_since": candidate.current_state_since.isoformat(),
                    "blocking_reasons": latest.score.hard_blocks if latest else [],
                }
                blocked.append(summary)

                if len(blocked) >= limit:
                    break

        return blocked

    def get_readiness_trends(
        self,
        days: int = 30,
    ) -> List[ReadinessTrend]:
        """
        Get readiness trends over time.

        Args:
            days: Number of days of history

        Returns:
            List of daily ReadinessTrend entries
        """
        trends = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Get all transitions in the period
        filters = type('Filters', (), {
            'start_time': start_date,
            'end_time': end_date,
            'limit': 10000,
            'offset': 0,
            'sort_order': 'desc',
        })()

        transitions = self.audit_service.list_transitions(filters)

        # Group by date
        daily_data: Dict[str, Dict[str, Any]] = {}

        for transition in transitions:
            date_str = transition.transitioned_at.date().isoformat()

            if date_str not in daily_data:
                daily_data[date_str] = {
                    "date": transition.transitioned_at.replace(hour=0, minute=0, second=0, microsecond=0),
                    "ready_count": 0,
                    "blocked_count": 0,
                    "regressed_count": 0,
                    "scores": [],
                }

            # Update counts based on target state
            if transition.to_state == "ready":
                daily_data[date_str]["ready_count"] += 1
            elif transition.to_state == "blocked":
                daily_data[date_str]["blocked_count"] += 1
            elif transition.to_state == "regressed":
                daily_data[date_str]["regressed_count"] += 1

            # Add score if available
            if transition.evaluation_score is not None:
                daily_data[date_str]["scores"].append(transition.evaluation_score)

        # Convert to trend objects
        for date_str, data in sorted(daily_data.items()):
            avg_score = sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0.0

            trends.append(ReadinessTrend(
                date=data["date"],
                ready_count=data["ready_count"],
                blocked_count=data["blocked_count"],
                regressed_count=data["regressed_count"],
                avg_score=avg_score,
            ))

        return trends

    def _compute_state_distribution(
        self,
        state_counts: Dict[str, int],
        total: int,
    ) -> List[StateDistribution]:
        """Compute state distribution from counts."""
        distribution = []

        for state, count in state_counts.items():
            # Get average score for this state
            state_scores = []
            for candidate in get_candidate_storage().values():
                if candidate.current_state.value == state:
                    evals = get_all_evaluations().get(candidate.id, [])
                    if evals:
                        latest = max(evals, key=lambda e: e.evaluated_at)
                        state_scores.append(latest.score.overall_score)

            avg_score = sum(state_scores) / len(state_scores) if state_scores else 0.0

            distribution.append(StateDistribution(
                state=state,
                count=count,
                percentage=count / total if total > 0 else 0.0,
                avg_score=avg_score,
            ))

        # Sort by state name for consistency
        distribution.sort(key=lambda d: d.state)

        return distribution

    def _get_all_scores(self) -> List[float]:
        """Get all current scores."""
        all_evaluations = get_all_evaluations()
        scores = []

        for candidate_id, evals in all_evaluations.items():
            if evals:
                latest = max(evals, key=lambda e: e.evaluated_at)
                scores.append(latest.score.overall_score)

        return scores

    def _get_block_reasons(self) -> Dict[str, int]:
        """Aggregate block reasons across all blocked candidates."""
        reasons: Dict[str, int] = {}

        for candidate in get_candidate_storage().values():
            if candidate.current_state == ReadinessState.BLOCKED:
                evals = get_all_evaluations().get(candidate.id, [])
                if evals:
                    latest = max(evals, key=lambda e: e.evaluated_at)
                    for block in latest.score.hard_blocks:
                        reasons[block] = reasons.get(block, 0) + 1

        return reasons

    def _compute_promotion_metrics(
        self,
        days: int = 30,
    ) -> tuple[float, float]:
        """Compute promotion rate and average promotion time."""
        start_date = datetime.now() - timedelta(days=days)

        # Count promotions to READY
        filters = type('Filters', (), {
            'to_state': "ready",
            'start_time': start_date,
            'end_time': None,
            'limit': 10000,
            'offset': 0,
            'sort_order': 'desc',
        })()

        promotions = self.audit_service.list_transitions(filters)

        # Count candidates that could be promoted
        total_promotable = sum(
            1 for c in get_candidate_storage().values()
            if c.created_at >= start_date or c.current_state in [ReadinessState.READY, ReadinessState.WATCHLIST]
        )

        promotion_rate = len(promotions) / total_promotable if total_promotable > 0 else 0.0

        # Compute average time to promotion
        # This is a simplified calculation - in production would track actual time
        avg_promotion_time = 7.0  # Placeholder: would compute from actual data

        return promotion_rate, avg_promotion_time

    def _compute_policy_compliance(self, candidates: List[ReadinessCandidate]) -> float:
        """Compute policy compliance rate."""
        if not candidates:
            return 0.0

        compliant = 0

        for candidate in candidates:
            evals = get_all_evaluations().get(candidate.id, [])
            if evals:
                latest = max(evals, key=lambda e: e.evaluated_at)
                if not latest.score.hard_blocks:
                    compliant += 1

        return compliant / len(candidates)

    def _compute_ready_trend(self) -> str:
        """Compute readiness trend direction."""
        # Simplified trend calculation
        recent_scores = []
        older_scores = []

        cutoff = datetime.now() - timedelta(days=7)

        for candidate_id, evals in get_all_evaluations().items():
            recent = [e for e in evals if e.evaluated_at >= cutoff]
            older = [e for e in evals if e.evaluated_at < cutoff]

            recent_scores.extend([e.score.overall_score for e in recent])
            older_scores.extend([e.score.overall_score for e in older])

        if not recent_scores or not older_scores:
            return "stable"

        recent_avg = sum(recent_scores) / len(recent_scores)
        older_avg = sum(older_scores) / len(older_scores)

        diff = recent_avg - older_avg

        if diff > 0.05:
            return "improving"
        elif diff < -0.05:
            return "declining"
        else:
            return "stable"

    def _compute_regression_trend(self) -> str:
        """Compute regression trend direction."""
        regressed_count = sum(
            1 for c in get_candidate_storage().values()
            if c.current_state == ReadinessState.REGRESSED
        )

        # Get recent regressions
        cutoff = datetime.now() - timedelta(days=7)
        recent_regressions = 0

        for candidate in get_candidate_storage().values():
            if candidate.current_state == ReadinessState.REGRESSED:
                if candidate.current_state_since >= cutoff:
                    recent_regressions += 1

        if recent_regressions > 3:
            return "increasing"
        elif recent_regressions == 0:
            return "stable"
        else:
            return "elevated"


# Global analytics service instance
_analytics_service: Optional[ReadinessAnalyticsService] = None


def get_analytics_service() -> ReadinessAnalyticsService:
    """Get the global analytics service instance."""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = ReadinessAnalyticsService()
    return _analytics_service
