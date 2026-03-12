"""
TORQ Layer 8 - Learning Analytics

L8-M1: Aggregates learning metrics across the autonomous intelligence layer.

Provides analytics and insights on the learning system performance.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from collections import defaultdict

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


# Import models
from .autonomous_models import (
    LearningMetrics,
    LearningTrend,
    SystemEvolutionSnapshot,
)


# ============================================================================
# Trend Analysis
# ============================================================================

class TrendAnalysis(BaseModel):
    """Analysis of a metric trend over time."""
    metric_name: str
    current_value: float
    previous_value: float
    change_percent: float
    trend: LearningTrend
    confidence: float

    class Config:
        use_enum_values = True


# ============================================================================
# Learning Analytics
# ============================================================================

class LearningAnalytics:
    """
    Aggregates learning metrics and provides analytics.

    Tracks trends, calculates system evolution, and provides
    insights into learning performance.
    """

    def __init__(self):
        """Initialize learning analytics."""
        # Metrics history
        self._metrics_history: List[LearningMetrics] = []
        self._snapshots: List[SystemEvolutionSnapshot] = []

        # Trend tracking
        self._metric_trends: Dict[str, List[float]] = defaultdict(list)

        # Aggregate statistics
        self._total_evaluations = 0
        self._total_improvements = 0

    async def record_metrics(
        self,
        metrics: LearningMetrics,
    ) -> None:
        """
        Record learning metrics.

        Args:
            metrics: LearningMetrics to record
        """
        self._metrics_history.append(metrics)

        # Track individual metric trends
        self._metric_trends["success_rate"].append(metrics.success_rate)
        self._metric_trends["implementation_rate"].append(metrics.implementation_rate)

        # Update aggregates
        self._total_evaluations += metrics.total_evaluations

        logger.debug(
            f"[LearningAnalytics] Recorded metrics: "
            f"success_rate={metrics.success_rate:.2f}"
        )

    async def create_snapshot(self) -> SystemEvolutionSnapshot:
        """
        Create a system evolution snapshot.

        Returns:
            SystemEvolutionSnapshot
        """
        # Get latest metrics
        latest_metrics = self._metrics_history[-1] if self._metrics_history else None

        # Calculate trends
        success_rate_trend = await self._calculate_trend("success_rate")
        pattern_accuracy_trend = await self._calculate_trend("pattern_accuracy")
        insight_confidence_trend = await self._calculate_trend("insight_confidence")

        # Gather recent improvements
        recent_improvements = await self._get_recent_improvements()

        # Calculate learning velocity
        learning_velocity = await self._calculate_learning_velocity()

        # Calculate system health
        system_health = await self._calculate_system_health()

        snapshot = SystemEvolutionSnapshot(
            total_missions_executed=self._total_evaluations,
            total_patterns_discovered=0,  # From pattern service
            total_insights_published=0,  # From insight service
            total_recommendations_generated=(
                latest_metrics.recommendations_generated if latest_metrics else 0
            ),
            system_health_score=system_health,
            learning_velocity=learning_velocity,
            success_rate_trend=success_rate_trend,
            pattern_accuracy_trend=pattern_accuracy_trend,
            insight_confidence_trend=insight_confidence_trend,
            recent_improvements=recent_improvements,
        )

        self._snapshots.append(snapshot)

        # Limit history
        if len(self._snapshots) > 100:
            self._snapshots = self._snapshots[-100:]

        return snapshot

    async def _calculate_trend(
        self,
        metric_name: str,
    ) -> LearningTrend:
        """Calculate trend for a metric."""
        values = self._metric_trends.get(metric_name, [])
        if len(values) < 3:
            return LearningTrend.STABLE

        recent = values[-5:]
        older = values[-10:-5] if len(values) >= 10 else values[:-5]

        if not older:
            return LearningTrend.STABLE

        avg_recent = sum(recent) / len(recent)
        avg_older = sum(older) / len(older)

        change = (avg_recent - avg_older) / max(avg_older, 0.01)

        if change > 0.1:
            return LearningTrend.IMPROVING
        elif change < -0.1:
            return LearningTrend.DECLINING
        else:
            return LearningTrend.STABLE

    async def _get_recent_improvements(self) -> List[str]:
        """Get recent system improvements."""
        improvements = []

        # Get recent metrics that show improvement
        for metrics in self._metrics_history[-10:]:
            if metrics.implementation_rate > 0.5:
                improvements.append(
                    f"Implemented {metrics.recommendations_implemented} recommendations"
                )

        return improvements[:10]

    async def _calculate_learning_velocity(self) -> float:
        """Calculate learning velocity (improvements per week)."""
        if not self._metrics_history:
            return 0.0

        # Look at last week of metrics
        cutoff = datetime.now() - timedelta(days=7)
        recent_metrics = [
            m for m in self._metrics_history
            if m.captured_at >= cutoff
        ]

        if not recent_metrics:
            return 0.0

        total_implementations = sum(
            m.recommendations_implemented for m in recent_metrics
        )

        return total_implementations / 7.0  # Per day

    async def _calculate_system_health(self) -> float:
        """Calculate overall system health score."""
        if not self._metrics_history:
            return 100.0

        latest = self._metrics_history[-1]

        # Health factors
        factors = []

        # Success rate
        factors.append(latest.success_rate * 100)

        # Implementation rate (active feedback loop)
        factors.append(latest.implementation_rate * 100)

        # Feedback loop active
        if latest.feedback_loop_active:
            factors.append(80.0)
        else:
            factors.append(40.0)

        # Average
        return sum(factors) / len(factors) if factors else 50.0

    async def get_metrics_summary(
        self,
        hours: int = 24,
    ) -> Dict[str, Any]:
        """
        Get summary of learning metrics.

        Args:
            hours: Lookback period in hours

        Returns:
            Summary of metrics
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_metrics = [
            m for m in self._metrics_history
            if m.captured_at >= cutoff
        ]

        if not recent_metrics:
            return {
                "period_hours": hours,
                "metrics_count": 0,
                "avg_success_rate": 0.0,
                "avg_implementation_rate": 0.0,
            }

        return {
            "period_hours": hours,
            "metrics_count": len(recent_metrics),
            "avg_success_rate": (
                sum(m.success_rate for m in recent_metrics) / len(recent_metrics)
            ),
            "avg_implementation_rate": (
                sum(m.implementation_rate for m in recent_metrics) / len(recent_metrics)
            ),
            "total_recommendations": sum(
                m.recommendations_generated for m in recent_metrics
            ),
            "total_implementations": sum(
                m.recommendations_implemented for m in recent_metrics
            ),
            "feedback_loop_active": any(
                m.feedback_loop_active for m in recent_metrics
            ),
        }

    async def get_trend_analysis(
        self,
        metric_name: str,
    ) -> Optional[TrendAnalysis]:
        """
        Get trend analysis for a specific metric.

        Args:
            metric_name: Name of the metric

        Returns:
            TrendAnalysis or None
        """
        values = self._metric_trends.get(metric_name, [])
        if len(values) < 2:
            return None

        current = values[-1]
        previous = values[-2] if len(values) >= 2 else current

        change_percent = (
            (current - previous) / max(previous, 0.01) * 100
            if previous > 0
            else 0.0
        )

        # Determine trend
        if change_percent > 5:
            trend = LearningTrend.IMPROVING
        elif change_percent < -5:
            trend = LearningTrend.DECLINING
        else:
            trend = LearningTrend.STABLE

        # Confidence based on data points
        confidence = min(1.0, len(values) / 20)

        return TrendAnalysis(
            metric_name=metric_name,
            current_value=current,
            previous_value=previous,
            change_percent=change_percent,
            trend=trend,
            confidence=confidence,
        )

    async def get_evolution_timeline(
        self,
        days: int = 30,
    ) -> List[SystemEvolutionSnapshot]:
        """
        Get evolution timeline.

        Args:
            days: Number of days to include

        Returns:
            List of snapshots
        """
        cutoff = datetime.now() - timedelta(days=days)

        return [
            s for s in self._snapshots
            if s.captured_at >= cutoff
        ]

    async def get_analytics_summary(self) -> Dict[str, Any]:
        """Get overall analytics summary."""
        latest_snapshot = (
            self._snapshots[-1] if self._snapshots else None
        )

        return {
            "total_metrics_captured": len(self._metrics_history),
            "total_snapshots": len(self._snapshots),
            "tracked_metrics": list(self._metric_trends.keys()),
            "current_system_health": (
                latest_snapshot.system_health_score if latest_snapshot else 0.0
            ),
            "learning_velocity": (
                latest_snapshot.learning_velocity if latest_snapshot else 0.0
            ),
            "recent_trends": {
                "success_rate": (
                    latest_snapshot.success_rate_trend.value if latest_snapshot else "unknown"
                ),
                "pattern_accuracy": (
                    latest_snapshot.pattern_accuracy_trend.value if latest_snapshot else "unknown"
                ),
                "insight_confidence": (
                    latest_snapshot.insight_confidence_trend.value if latest_snapshot else "unknown"
                ),
            },
        }


# Global learning analytics instance
_analytics: Optional[LearningAnalytics] = None


def get_learning_analytics() -> LearningAnalytics:
    """Get the global learning analytics instance."""
    global _analytics
    if _analytics is None:
        _analytics = LearningAnalytics()
    return _analytics
