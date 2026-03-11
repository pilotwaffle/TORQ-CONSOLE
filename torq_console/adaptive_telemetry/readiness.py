"""
Adaptive System Readiness Checker

Determines when the adaptive system is ready to transition from
observation mode to guarded automatic promotion.

Monitors three key indicators:
1. Signal Stability - conversion rate, distribution, volume
2. Experiment Reliability - success/rollback rates, sample size attainment
3. Positive System Drift - upward trend in baseline evaluation scores

Once all three indicators stabilize, Tier 1 changes can auto-promote.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Literal
from dataclasses import dataclass
from enum import Enum

from ..telemetry.models import (
    TelemetryReport,
    ConversionMetrics,
    SignalVolumeMetrics,
    ProposalFlowMetrics,
    ExperimentMetrics,
    MetricDistribution,
)


logger = logging.getLogger(__name__)


class ReadinessStatus(str, Enum):
    """Status of a readiness indicator."""
    STABILIZING = "stabilizing"  # Not enough data yet
    PASSING = "passing"  # Within acceptable range
    FAILING = "failing"  # Outside acceptable range
    UNKNOWN = "unknown"  # Cannot determine


@dataclass
class IndicatorStatus:
    """Status of a single readiness indicator with details."""
    indicator: str
    status: ReadinessStatus
    value: Optional[float]  # Current metric value
    target_min: Optional[float]  # Minimum acceptable
    target_max: Optional[float]  # Maximum acceptable
    trend: List[float]  # Historical values for trend analysis
    message: str  # Human-readable assessment
    days_observed: int  # Days of data available


@dataclass
class ReadinessAssessment:
    """Complete readiness assessment for leaving observation mode."""
    can_leave_observation_mode: bool
    confidence: float  # 0.0 to 1.0
    assessed_at: datetime

    # Individual indicator statuses
    signal_stability: IndicatorStatus
    experiment_reliability: IndicatorStatus
    system_drift: IndicatorStatus

    # Adaptation velocity
    adaptations_per_week: float
    velocity_status: Literal["too_low", "healthy", "too_high"]

    # Recommendations
    recommendations: List[str]

    # Minimum days observed
    days_observed: int


class AdaptiveReadinessChecker:
    """
    Evaluates whether the adaptive system is ready for guarded auto-promotion.

    Checks signal stability, experiment reliability, and positive system drift.
    """

    # Target ranges for healthy adaptive system
    MIN_DAYS_OBSERVATION = 10
    IDEAL_DAYS_OBSERVATION = 14

    # Signal stability targets
    CONVERSION_RATE_MIN = 0.05  # 5%
    CONVERSION_RATE_MAX = 0.25  # 25%
    CONVERSION_STABILITY_DAYS = 7  # Days within target range

    # Experiment reliability targets
    SUCCESS_RATE_MIN = 0.60  # 60%
    SUCCESS_RATE_MAX = 0.95  # 95% (too high = too conservative)
    ROLLBACK_RATE_MAX = 0.15  # 15%
    MIN_EXPERIMENTS = 10  # Minimum experiments before assessment

    # System drift targets
    DRIFT_IMPROVEMENT_MIN = 0.01  # 1% improvement over period
    DRIFT_PERIOD_DAYS = 14  # Days to measure drift

    # Adaptation velocity targets
    VELOCITY_MIN = 2  # promotions per week
    VELOCITY_MAX = 6  # promotions per week

    def __init__(self, supabase_client, collector, analyzer):
        self.supabase = supabase_client
        self.collector = collector
        self.analyzer = analyzer

        # Historical data storage
        self.historical_signals: List[float] = []
        self.historical_conversions: List[float] = []
        self.historical_success: List[float] = []
        self.historical_scores: List[float] = []

    async def assess_readiness(
        self,
        days_observed: int = 14
    ) -> ReadinessAssessment:
        """
        Assess whether the system is ready to leave observation mode.

        Returns a complete assessment with all three indicators.
        """
        now = datetime.now()

        # Fetch historical data for trend analysis
        await self._load_historical_data(days_observed)

        # Assess each indicator
        signal_status = await self._assess_signal_stability(days_observed)
        experiment_status = await self._assess_experiment_reliability(days_observed)
        drift_status = await self._assess_system_drift(days_observed)

        # Calculate overall readiness
        can_leave = all([
            s.status == ReadinessStatus.PASSING for s in [signal_status, experiment_status, drift_status]
        ])

        # Calculate confidence based on how close to ideal thresholds
        confidence = self._calculate_confidence(
            signal_status, experiment_status, drift_status
        )

        # Assess adaptation velocity
        velocity_status = await self._assess_adaptation_velocity(days_observed)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            signal_status, experiment_status, drift_status, velocity_status, can_leave
        )

        return ReadinessAssessment(
            can_leave_observation_mode=can_leave,
            confidence=confidence,
            assessed_at=now,
            signal_stability=signal_status,
            experiment_reliability=experiment_status,
            system_drift=drift_status,
            adaptations_per_week=self._calculate_promotions_per_week(days_observed),
            velocity_status=velocity_status,
            recommendations=recommendations,
            days_observed=days_observed
        )

    async def _assess_signal_stability(
        self,
        days_observed: int
    ) -> IndicatorStatus:
        """Assess whether signal generation is stable."""
        if days_observed < self.MIN_DAYS_OBSERVATION:
            return IndicatorStatus(
                indicator="signal_stability",
                status=ReadinessStatus.STABILIZING,
                value=None,
                target_min=self.CONVERSION_RATE_MIN,
                target_max=self.CONVERSION_RATE_MAX,
                trend=self.historical_conversions[-7:] if len(self.historical_conversions) >= 7 else [],
                message=f"Collecting data ({days_observed}/{self.MIN_DAYS_OBSERVATION} days minimum)"
            )

        # Check conversion rate stability
        if len(self.historical_conversions) >= self.CONVERSION_STABILITY_DAYS:
            recent_rates = self.historical_conversions[-self.CONVERSION_STABILITY_DAYS:]
            avg_rate = sum(recent_rates) / len(recent_rates)

            # Check if within target range
            in_range = self.CONVERSION_RATE_MIN <= avg_rate <= self.CONVERSION_RATE_MAX

            # Check for stability (low variance)
            variance = max(recent_rates) - min(recent_rates)
            is_stable = variance < 0.10  # Less than 10% variance

            if in_range and is_stable:
                status = ReadinessStatus.PASSING
                message = f"Conversion rate stable at {avg_rate:.1%} (target: 5-25%)"
            else:
                status = ReadinessStatus.FAILING if not in_range else ReadinessStatus.STABILIZING
                message = f"Conversion rate {'outside' if not in_range else 'unstable'} at {avg_rate:.1%} (variance: {variance:.1%})"
        else:
            status = ReadinessStatus.STABILIZING
            message = "Insufficient data for conversion rate stability assessment"

        return IndicatorStatus(
            indicator="signal_stability",
            status=status,
            value=self.historical_conversions[-1] if self.historical_conversions else None,
            target_min=self.CONVERSION_RATE_MIN,
            target_max=self.CONVERSION_RATE_MAX,
            trend=self.historical_conversions[-7:] if len(self.historical_conversions) >= 7 else [],
            message=message
        )

    async def _assess_experiment_reliability(
        self,
        days_observed: int
    ) -> IndicatorStatus:
        """Assess whether experiments are producing reliable results."""
        if len(self.historical_success) < 3:
            return IndicatorStatus(
                indicator="experiment_reliability",
                status=ReadinessStatus.STABILIZING,
                value=None,
                target_min=self.SUCCESS_RATE_MIN,
                target_max=self.SUCCESS_RATE_MAX,
                trend=[],
                message=f"Need more experiment outcomes ({len(self.historical_success)} experiments, minimum 3)"
            )

        # Check success rate
        success_rate = self.historical_success[-1] if self.historical_success else 0

        # Check if in healthy range
        in_range = self.SUCCESS_RATE_MIN <= success_rate <= self.SUCCESS_RATE_MAX

        # Calculate rollback rate from experiment data
        rollback_rate = await self._get_rollback_rate(days_observed)
        rollback_ok = rollback_rate < self.ROLLBACK_RATE_MAX

        if in_range and rollback_ok:
            status = ReadinessStatus.PASSING
            message = f"Experiment success rate healthy: {success_rate:.1%}, rollback rate: {rollback_rate:.1%}"
        elif success_rate > self.SUCCESS_RATE_MAX:
            status = ReadinessStatus.FAILING
            message = f"Success rate too high ({success_rate:.1%}) - proposals may be too conservative"
        elif success_rate < self.SUCCESS_RATE_MIN:
            status = ReadinessStatus.FAILING
            message = f"Success rate too low ({success_rate:.1%}) - experiments may be unreliable"
        else:
            status = ReadinessStatus.STABILIZING
            message = f"Success rate {success_rate:.1%}, but rollback rate {rollback_rate:.1%} concerning"

        return IndicatorStatus(
            indicator="experiment_reliability",
            status=status,
            value=success_rate,
            target_min=self.SUCCESS_RATE_MIN,
            target_max=self.SUCCESS_RATE_MAX,
            trend=self.historical_success[-7:] if len(self.historical_success) >= 7 else [],
            message=message
        )

    async def _assess_system_drift(
        self,
        days_observed: int
    ) -> IndicatorStatus:
        """Assess whether system performance is trending upward (positive drift)."""
        if len(self.historical_scores) < self.DRIFT_PERIOD_DAYS:
            return IndicatorStatus(
                indicator="system_drift",
                status=ReadinessStatus.STABILIZING,
                value=None,
                target_min=self.DRIFT_IMPROVEMENT_MIN,
                target_max=None,
                trend=self.historical_scores[-7:] if len(self.historical_scores) >= 7 else [],
                message=f"Need more score data ({len(self.historical_scores)} days, minimum {self.DRIFT_PERIOD_DAYS})"
            )

        # Calculate improvement over period
        early_scores = self.historical_scores[-self.DRIFT_PERIOD_DAYS:]
        recent_scores = self.historical_scores[-7:]  # Most recent week

        if not early_scores or not recent_scores:
            return IndicatorStatus(
                indicator="system_drift",
                status=ReadinessStatus.UNKNOWN,
                value=None,
                target_min=self.DRIFT_IMPROVEMENT_MIN,
                target_max=None,
                trend=[],
                message="Insufficient score data for drift assessment"
            )

        early_avg = sum(early_scores) / len(early_scores)
        recent_avg = sum(recent_scores) / len(recent_scores)
        improvement = recent_avg - early_avg

        # Check for positive drift
        if improvement >= self.DRIFT_IMPROVEMENT_MIN:
            status = ReadinessStatus.PASSING
            direction = "upward"
        elif improvement <= -self.DRIFT_IMPROVEMENT_MIN:
            status = ReadinessStatus.FAILING
            direction = "downward"
        else:
            status = ReadinessStatus.STABILIZING
            direction = "flat"

        message = f"System performance {direction}: {early_avg:.2f} → {recent_avg:.2f} ({improvement:+.2f})"

        return IndicatorStatus(
            indicator="system_drift",
            status=status,
            value=improvement,
            target_min=self.DRIFT_IMPROVEMENT_MIN,
            target_max=None,
            trend=self.historical_scores[-7:] if len(self.historical_scores) >= 7 else [],
            message=message
        )

    async def _assess_adaptation_velocity(
        self,
        days_observed: int
    ) -> Literal["too_low", "healthy", "too_high"]:
        """Assess whether promotion rate is healthy."""
        promotions_per_week = self._calculate_promotions_per_week(days_observed)

        if promotions_per_week < self.VELOCITY_MIN:
            return "too_low"
        elif promotions_per_week > self.VELOCITY_MAX:
            return "too_high"
        else:
            return "healthy"

    def _calculate_promotions_per_week(self, days_observed: int) -> float:
        """Calculate promotions per week from experiment data."""
        # Query promoted experiments
        try:
            since = datetime.now() - timedelta(days=days_observed)
            result = self.supabase.table("behavior_experiments").select("*").eq("status", "promoted").gte("promoted_at", since.isoformat()).execute()

            promoted_count = len(result.data) if result.data else 0
            weeks = max(days_observed / 7, 1)

            return round(promoted_count / weeks, 1)

        except Exception as e:
            logger.error(f"Error calculating promotion velocity: {e}")
            return 0.0

    async def _get_rollback_rate(self, days_observed: int) -> float:
        """Calculate rollback rate over the period."""
        try:
            since = datetime.now() - timedelta(days=days_observed)
            result = self.supabase.table("behavior_experiments").select("*").in_("status", ["promoted", "rolled_back"]).gte("completed_at", since.isoformat()).execute()

            total = len(result.data) if result.data else 0
            rolled_back = len([e for e in result.data if e.get("status") == "rolled_back"]) if result.data else 0

            return (rolled_back / total) if total > 0 else 0.0

        except Exception as e:
            logger.error(f"Error calculating rollback rate: {e}")
            return 0.0

    async def _load_historical_data(self, days_back: int):
        """Load historical metrics for trend analysis."""
        since = datetime.now() - timedelta(days=days_back)

        # This would load from adaptive_metrics table or compute aggregations
        # For now, we'll use the telemetry collector
        report = await self.collector.collect_report(days_back=days_back)

        # Store conversion rates
        if hasattr(report, 'conversions') and report.conversions:
            self.historical_conversions.append(report.conversions.conversion_rate)

        # Store success rates
        if report.experiments:
            self.historical_success.append(report.experiments.success_rate)

        # Store distribution for median score
        distributions = await self.analyzer.analyze_distributions(days_back=days_back)
        if distributions and "overall_score" in distributions:
            self.historical_scores.append(distributions["overall_score"].median)

    def _calculate_confidence(
        self,
        signal_status: IndicatorStatus,
        experiment_status: IndicatorStatus,
        drift_status: IndicatorStatus
    ) -> float:
        """Calculate overall confidence in the readiness assessment."""
        scores = []

        # Signal stability contributes 30%
        if signal_status.status == ReadinessStatus.PASSING:
            scores.append(0.3)
        elif signal_status.status == ReadinessStatus.STABILIZING:
            scores.append(0.1)

        # Experiment reliability contributes 40%
        if experiment_status.status == ReadinessStatus.PASSING:
            scores.append(0.4)
        elif experiment_status.status == ReadinessStatus.STABILIZING:
            scores.append(0.15)

        # System drift contributes 30%
        if drift_status.status == ReadinessStatus.PASSING:
            scores.append(0.3)
        elif drift_status.status == ReadinessStatus.STABILIZING:
            scores.append(0.1)

        return round(sum(scores), 2)

    def _generate_recommendations(
        self,
        signal_status: IndicatorStatus,
        experiment_status: IndicatorStatus,
        drift_status: IndicatorStatus,
        velocity_status: str,
        can_leave: bool
    ) -> List[str]:
        """Generate actionable recommendations based on assessment."""
        recommendations = []

        if not can_leave:
            recommendations.append("Continue in observation mode until all indicators pass")

        # Signal-specific recommendations
        if signal_status.status == ReadinessStatus.FAILING:
            recommendations.append(f"Signal stability issue: {signal_status.message}")

        # Experiment-specific recommendations
        if experiment_status.status == ReadinessStatus.FAILING:
            recommendations.append(f"Experiment reliability issue: {experiment_status.message}")

        # Drift-specific recommendations
        if drift_status.status == ReadinessStatus.FAILING:
            recommendations.append(f"System drift concern: {drift_status.message} - review recent promotions")

        # Velocity recommendations
        if velocity_status == "too_low":
            recommendations.append("Adaptation velocity is low - consider reviewing promotion criteria")
        elif velocity_status == "too_high":
            recommendations.append("Adaptation velocity is high - increase guardrails or review criteria")

        # Passing recommendations
        if can_leave:
            recommendations.append("All indicators passing - ready to enable Tier 1 auto-promotion")
            recommendations.append("Continue monitoring conversion rate and experiment success")
            recommendations.append("Maintain rollback rate below 15%")

        return recommendations


class ReadinessConfiguration:
    """Configuration for readiness assessment."""

    def __init__(
        self,
        min_days_observation: int = 10,
        ideal_days_observation: int = 14,
        conversion_rate_min: float = 0.05,
        conversion_rate_max: float = 0.25,
        success_rate_min: float = 0.60,
        success_rate_max: float = 0.95,
        rollback_rate_max: float = 0.15,
        drift_improvement_min: float = 0.01,
        velocity_min: float = 2,
        velocity_max: float = 6
    ):
        self.min_days_observation = min_days_observation
        self.ideal_days_observation = ideal_days_observation
        self.conversion_rate_min = conversion_rate_min
        self.conversion_rate_max = conversion_rate_max
        self.success_rate_min = success_rate_min
        self.success_rate_max = success_rate_max
        self.rollback_rate_max = rollback_rate_max
        self.drift_improvement_min = drift_improvement_min
        self.velocity_min = velocity_min
        self.velocity_max = velocity_max
