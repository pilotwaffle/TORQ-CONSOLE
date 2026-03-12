"""
TORQ Layer 10 - Strategic Forecasting Engine

L10-M1: Generates long-term predictions of system and organizational outcomes.

The StrategicForecastingEngine provides:
- Capability adoption forecasts
- Mission success trend predictions
- Performance projections
- Readiness forecasting
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4
from dataclasses import dataclass
from collections import defaultdict
import math

from pydantic import BaseModel


logger = logging.getLogger(__name__)


# Import models
from ..models import (
    StrategicForecast,
    ForecastType,
    ForecastTrendDirection,
    ForecastDataPoint,
)


# ============================================================================
# Forecasting Context
# ============================================================================

@dataclass
class ForecastingContext:
    """Context data for strategic forecasting."""
    # Current metrics
    current_capability_count: int = 100
    current_success_rate: float = 0.75
    current_avg_quality: float = 0.80
    current_readiness_avg: float = 0.70

    # Historical trends (monthly)
    monthly_capability_growth: float = 0.05  # 5% growth per month
    monthly_success_trend: float = 0.01  # 1% improvement per month
    monthly_quality_trend: float = 0.005  # 0.5% improvement per month

    # Volatility factors
    success_volatility: float = 0.05
    quality_volatility: float = 0.03
    readiness_volatility: float = 0.04

    # Seasonality (if applicable)
    seasonal_factor: float = 0.0

    # Domain-specific trends
    domain_trends: Dict[str, float] = None

    def __post_init__(self):
        if self.domain_trends is None:
            self.domain_trends = {
                "finance": 0.02,
                "technology": 0.03,
                "operations": 0.01,
            }


# ============================================================================
# Strategic Forecasting Engine
# ============================================================================

class StrategicForecastingEngine:
    """
    Generates long-term strategic predictions.

    Uses trend analysis, pattern recognition, and statistical modeling
    to forecast future organizational and system outcomes.
    """

    def __init__(self):
        """Initialize the forecasting engine."""
        self._forecasts: Dict[UUID, StrategicForecast] = {}
        self._context = ForecastingContext()

    def set_forecasting_context(self, context: ForecastingContext) -> None:
        """Set the forecasting context data."""
        self._context = context
        logger.debug(f"[ForecastingEngine] Updated forecasting context")

    async def generate_forecast(
        self,
        forecast_type: ForecastType,
        title: str,
        description: str,
        timeframe_days: int,
        scope: str = "global",
        scope_value: Optional[str] = None,
        context_override: Optional[ForecastingContext] = None,
    ) -> StrategicForecast:
        """
        Generate a strategic forecast.

        Args:
            forecast_type: Type of forecast to generate
            title: Forecast title
            description: Forecast description
            timeframe_days: Number of days to forecast
            scope: Scope of forecast (global, domain, capability)
            scope_value: Specific scope value
            context_override: Optional context override

        Returns:
            StrategicForecast with predictions
        """
        context = context_override or self._context

        timeframe_start = datetime.now()
        timeframe_end = timeframe_start + timedelta(days=timeframe_days)

        forecast = StrategicForecast(
            forecast_type=forecast_type,
            title=title,
            description=description,
            timeframe_start=timeframe_start,
            timeframe_end=timeframe_end,
            forecast_horizon_days=timeframe_days,
            scope=scope,
            scope_value=scope_value,
        )

        logger.info(
            f"[ForecastingEngine] Generating {forecast_type} forecast: '{title}' "
            f"({timeframe_days} days)"
        )

        # Generate forecast based on type
        if forecast_type == ForecastType.CAPABILITY_ADOPTION:
            await self._forecast_capability_adoption(forecast, context)
        elif forecast_type == ForecastType.MISSION_SUCCESS_TREND:
            await self._forecast_mission_success(forecast, context)
        elif forecast_type == ForecastType.READINESS_TREND:
            await self._forecast_readiness_trend(forecast, context)
        elif forecast_type == ForecastType.PERFORMANCE_PROJECTION:
            await self._forecast_performance(forecast, context)
        elif forecast_type == ForecastType.WORKFLOW_OPTIMIZATION:
            await self._forecast_workflow_optimization(forecast, context)
        else:
            await self._forecast_generic(forecast, context)

        # Determine trend direction
        forecast.trend_direction = self._determine_trend_direction(forecast)

        # Generate insights
        self._generate_insights(forecast)

        # Set confidence
        forecast.confidence = self._calculate_confidence(forecast, context)
        forecast.methodology = "Trend extrapolation with volatility modeling"

        self._forecasts[forecast.forecast_id] = forecast

        logger.info(
            f"[ForecastingEngine] Forecast complete: {forecast.trend_direction} trend"
        )

        return forecast

    async def _forecast_capability_adoption(
        self,
        forecast: StrategicForecast,
        context: ForecastingContext,
    ) -> None:
        """Forecast capability adoption over time."""
        current_count = context.current_capability_count
        growth_rate = context.monthly_capability_growth
        monthly_periods = forecast.forecast_horizon_days / 30

        # Generate data points (weekly)
        data_points = []
        for week in range(int(forecast.forecast_horizon_days / 7)):
            t = week / 4  # Convert to months
            projected_count = current_count * (1 + growth_rate) ** t

            # Add some volatility
            volatility = context.success_volatility * projected_count * 0.1
            confidence_lower = projected_count - volatility * 1.96
            confidence_upper = projected_count + volatility * 1.96

            timestamp = forecast.timeframe_start + timedelta(weeks=week)
            data_points.append(ForecastDataPoint(
                timestamp=timestamp,
                predicted_value=projected_count,
                confidence_lower=max(0, confidence_lower),
                confidence_upper=confidence_upper,
            ))

        forecast.data_points = data_points

        # Final predictions
        final_count = current_count * (1 + growth_rate) ** monthly_periods
        forecast.predicted_metrics = {
            "final_capability_count": final_count,
            "total_new_capabilities": final_count - current_count,
            "adoption_rate": growth_rate,
        }

    async def _forecast_mission_success(
        self,
        forecast: StrategicForecast,
        context: ForecastingContext,
    ) -> None:
        """Forecast mission success trends."""
        current_rate = context.current_success_rate
        monthly_improvement = context.monthly_success_trend
        monthly_periods = forecast.forecast_horizon_days / 30

        # Apply domain-specific trend if applicable
        if forecast.scope_value and forecast.scope_value in context.domain_trends:
            monthly_improvement = context.domain_trends[forecast.scope_value]

        # Generate data points
        data_points = []
        for week in range(int(forecast.forecast_horizon_days / 7)):
            t = week / 4  # Convert to months

            # Logistic-like growth with diminishing returns
            improvement = monthly_improvement * t / (1 + 0.1 * t)
            predicted_rate = min(0.98, current_rate + improvement)

            # Confidence interval
            std_dev = context.success_volatility * math.sqrt(t)
            confidence_lower = max(0, predicted_rate - 1.96 * std_dev)
            confidence_upper = min(1, predicted_rate + 1.96 * std_dev)

            timestamp = forecast.timeframe_start + timedelta(weeks=week)
            data_points.append(ForecastDataPoint(
                timestamp=timestamp,
                predicted_value=predicted_rate,
                confidence_lower=confidence_lower,
                confidence_upper=confidence_upper,
            ))

        forecast.data_points = data_points

        # Final prediction
        final_improvement = monthly_improvement * monthly_periods / (1 + 0.1 * monthly_periods)
        final_rate = min(0.98, current_rate + final_improvement)

        forecast.predicted_metrics = {
            "initial_success_rate": current_rate,
            "final_success_rate": final_rate,
            "improvement": final_rate - current_rate,
            "relative_improvement": (final_rate - current_rate) / current_rate,
        }

    async def _forecast_readiness_trend(
        self,
        forecast: StrategicForecast,
        context: ForecastingContext,
    ) -> None:
        """Forecast readiness trends."""
        current_avg = context.current_readiness_avg

        # Generate data points
        data_points = []
        for week in range(int(forecast.forecast_horizon_days / 7)):
            t = week / 4

            # Slight improvement trend with mean-reversion
            trend = 0.005 * t
            mean_reversion = (0.8 - current_avg) * (1 - math.exp(-0.1 * t))
            predicted_readiness = current_avg + trend + mean_reversion
            predicted_readiness = max(0.5, min(0.95, predicted_readiness))

            # Confidence interval
            std_dev = context.readiness_volatility * math.sqrt(t)
            confidence_lower = max(0, predicted_readiness - 1.96 * std_dev)
            confidence_upper = min(1, predicted_readiness + 1.96 * std_dev)

            timestamp = forecast.timeframe_start + timedelta(weeks=week)
            data_points.append(ForecastDataPoint(
                timestamp=timestamp,
                predicted_value=predicted_readiness,
                confidence_lower=confidence_lower,
                confidence_upper=confidence_upper,
            ))

        forecast.data_points = data_points

        # Final prediction
        t = forecast.forecast_horizon_days / 30
        trend = 0.005 * t
        mean_reversion = (0.8 - current_avg) * (1 - math.exp(-0.1 * t))
        final_readiness = max(0.5, min(0.95, current_avg + trend + mean_reversion))

        forecast.predicted_metrics = {
            "initial_readiness_avg": current_avg,
            "final_readiness_avg": final_readiness,
            "change": final_readiness - current_avg,
        }

    async def _forecast_performance(
        self,
        forecast: StrategicForecast,
        context: ForecastingContext,
    ) -> None:
        """Forecast overall system performance."""
        current_quality = context.current_avg_quality
        current_success = context.current_success_rate

        # Combined performance score
        current_performance = (current_quality + current_success) / 2

        data_points = []
        for week in range(int(forecast.forecast_horizon_days / 7)):
            t = week / 4

            # Improvement with diminishing returns
            quality_improvement = context.monthly_quality_trend * t / (1 + 0.1 * t)
            success_improvement = context.monthly_success_trend * t / (1 + 0.1 * t)

            predicted_quality = min(0.98, current_quality + quality_improvement)
            predicted_success = min(0.98, current_success + success_improvement)
            predicted_performance = (predicted_quality + predicted_success) / 2

            timestamp = forecast.timeframe_start + timedelta(weeks=week)
            data_points.append(ForecastDataPoint(
                timestamp=timestamp,
                predicted_value=predicted_performance,
                segment="overall",
            ))

        forecast.data_points = data_points

        # Final predictions
        t = forecast.forecast_horizon_days / 30
        final_quality = min(0.98, current_quality + context.monthly_quality_trend * t / (1 + 0.1 * t))
        final_success = min(0.98, current_success + context.monthly_success_trend * t / (1 + 0.1 * t))

        forecast.predicted_metrics = {
            "initial_performance": current_performance,
            "final_performance": (final_quality + final_success) / 2,
            "quality_score": final_quality,
            "success_score": final_success,
        }

    async def _forecast_workflow_optimization(
        self,
        forecast: StrategicForecast,
        context: ForecastingContext,
    ) -> None:
        """Forecast workflow optimization outcomes."""
        # Efficiency gains from optimization
        baseline_duration = 120.0  # seconds
        optimization_rate = 0.02  # 2% efficiency gain per month

        data_points = []
        for week in range(int(forecast.forecast_horizon_days / 7)):
            t = week / 4
            efficiency_gain = 1 - (1 - optimization_rate) ** t
            predicted_duration = baseline_duration * (1 - efficiency_gain)

            timestamp = forecast.timeframe_start + timedelta(weeks=week)
            data_points.append(ForecastDataPoint(
                timestamp=timestamp,
                predicted_value=predicted_duration,
                segment="duration",
            ))

        forecast.data_points = data_points

        forecast.predicted_metrics = {
            "initial_avg_duration": baseline_duration,
            "final_avg_duration": baseline_duration * (1 - (1 - optimization_rate) ** (forecast.forecast_horizon_days / 30)),
            "efficiency_improvement": optimization_rate,
        }

    async def _forecast_generic(
        self,
        forecast: StrategicForecast,
        context: ForecastingContext,
    ) -> None:
        """Generate a generic forecast."""
        # Simple trend-based forecast
        current_value = context.current_success_rate
        trend = 0.01

        data_points = []
        for week in range(int(forecast.forecast_horizon_days / 7)):
            t = week / 4
            predicted_value = current_value + trend * t
            predicted_value = max(0, min(1, predicted_value))

            timestamp = forecast.timeframe_start + timedelta(weeks=week)
            data_points.append(ForecastDataPoint(
                timestamp=timestamp,
                predicted_value=predicted_value,
            ))

        forecast.data_points = data_points
        forecast.predicted_metrics = {"predicted_value": predicted_value}

    def _determine_trend_direction(self, forecast: StrategicForecast) -> ForecastTrendDirection:
        """Determine the direction of the forecasted trend."""
        if not forecast.data_points or len(forecast.data_points) < 2:
            return ForecastTrendDirection.STABLE

        first_value = forecast.data_points[0].predicted_value
        last_value = forecast.data_points[-1].predicted_value

        change = (last_value - first_value) / first_value if first_value != 0 else 0

        # Calculate volatility
        values = [dp.predicted_value for dp in forecast.data_points]
        if len(values) > 1:
            mean = sum(values) / len(values)
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            std_dev = math.sqrt(variance)
            cv = std_dev / mean if mean != 0 else 0

            # High coefficient of variation = volatile
            if cv > 0.15:
                return ForecastTrendDirection.VOLATILE

        if change > 0.02:
            return ForecastTrendDirection.IMPROVING
        elif change < -0.02:
            return ForecastTrendDirection.DECLINING
        else:
            return ForecastTrendDirection.STABLE

    def _generate_insights(self, forecast: StrategicForecast) -> None:
        """Generate key insights from the forecast."""
        forecast.key_insights = []
        forecast.opportunities = []
        forecast.risk_factors = []

        if not forecast.data_points:
            return

        first_value = forecast.data_points[0].predicted_value
        last_value = forecast.data_points[-1].predicted_value
        change_pct = ((last_value - first_value) / first_value * 100) if first_value != 0 else 0

        # Generate insights based on change
        if change_pct > 10:
            forecast.key_insights.append(f"Strong positive trend projected: +{change_pct:.1f}%")
            forecast.opportunities.append("Capitalize on positive momentum")
        elif change_pct > 0:
            forecast.key_insights.append(f"Modest improvement projected: +{change_pct:.1f}%")
        elif change_pct < -10:
            forecast.key_insights.append(f"Significant decline projected: {change_pct:.1f}%")
            forecast.risk_factors.append("Intervention recommended to reverse trend")
        else:
            forecast.key_insights.append("Stable performance projected")

        # Trend-specific insights
        if forecast.trend_direction == ForecastTrendDirection.VOLATILE:
            forecast.risk_factors.append("High volatility indicates uncertainty")
            forecast.key_insights.append("Consider stabilizing interventions")

        if forecast.trend_direction == ForecastTrendDirection.IMPROVING:
            forecast.opportunities.append("Accelerate improvements with targeted investments")

        # Check for plateaus
        if len(forecast.data_points) > 4:
            recent_changes = [
                abs(forecast.data_points[i].predicted_value - forecast.data_points[i-1].predicted_value)
                for i in range(len(forecast.data_points)-3, len(forecast.data_points))
            ]
            if all(c < 0.01 for c in recent_changes):
                forecast.key_insights.append("Plateau detected - may need new initiatives")

    def _calculate_confidence(
        self,
        forecast: StrategicForecast,
        context: ForecastingContext,
    ) -> float:
        """Calculate confidence in the forecast."""
        base_confidence = 0.8

        # Reduce confidence for longer timeframes
        horizon_penalty = min(0.3, forecast.forecast_horizon_days / 365 * 0.2)

        # Reduce confidence for volatile forecasts
        volatility_penalty = 0
        if forecast.trend_direction == ForecastTrendDirection.VOLATILE:
            volatility_penalty = 0.2

        # Increase confidence for strong trends
        trend_bonus = 0
        if forecast.trend_direction in (ForecastTrendDirection.IMPROVING, ForecastTrendDirection.DECLINING):
            trend_bonus = 0.05

        confidence = base_confidence - horizon_penalty - volatility_penalty + trend_bonus
        return max(0.3, min(0.95, confidence))

    def get_forecast(self, forecast_id: UUID) -> Optional[StrategicForecast]:
        """Get a forecast by ID."""
        return self._forecasts.get(forecast_id)

    def list_forecasts(self) -> List[StrategicForecast]:
        """List all forecasts."""
        return list(self._forecasts.values())


# Global forecasting engine instance
_engine: Optional[StrategicForecastingEngine] = None


def get_forecasting_engine() -> StrategicForecastingEngine:
    """Get the global strategic forecasting engine instance."""
    global _engine
    if _engine is None:
        _engine = StrategicForecastingEngine()
    return _engine
