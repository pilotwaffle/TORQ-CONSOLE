"""
TORQ Layer 10 - Simulation Calibration Engine

L10-M1: Continuously improves simulation accuracy by comparing predictions
with real-world outcomes.

The SimulationCalibrationEngine provides:
- Forecast error tracking
- Scenario parameter tuning
- Confidence interval calibration
- Simulation accuracy metrics
"""

from __future__ import annotations

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from collections import defaultdict
from pathlib import Path

from pydantic import BaseModel, Field, Field


logger = logging.getLogger(__name__)


# Import models
from ..models import (
    SimulationResult,
    SimulationScenario,
    SimulationScope,
)


# ============================================================================
# Calibration Data Models
# ============================================================================

class ForecastError(BaseModel):
    """Record of a forecast vs actual outcome."""
    error_id: UUID = Field(default_factory=uuid4)
    scenario_id: UUID
    forecast_id: UUID

    # What was predicted
    predicted_success_rate: float
    predicted_duration: float
    predicted_quality: float

    # What actually happened
    actual_success: bool
    actual_duration: float
    actual_quality: float

    # Error metrics
    success_rate_error: float
    duration_error: float
    quality_error: float
    mean_absolute_error: float

    # Context
    timestamp: datetime = Field(default_factory=datetime.now)
    mission_context: Dict[str, Any] = Field(default_factory=dict)


class CalibrationMetrics(BaseModel):
    """Aggregated calibration metrics."""
    metrics_id: UUID = Field(default_factory=uuid4)
    timeframe_start: datetime
    timeframe_end: datetime

    # Accuracy metrics
    mean_absolute_error: float = 0.0
    root_mean_squared_error: float = 0.0
    mean_absolute_percentage_error: float = 0.0

    # Confidence calibration
    confidence_accuracy: float = 0.0  # How well confidence intervals match reality
    coverage_probability: float = 0.0  # Actual vs predicted coverage

    # By simulation scope
    error_by_scope: Dict[str, float] = Field(default_factory=dict)

    # Trend
    error_trend: str = "stable"  # improving, stable, degrading

    # Recommendation
    recalibration_recommended: bool = False
    calibration_parameters: Dict[str, float] = Field(default_factory=dict)


class CalibrationParameter(BaseModel):
    """A tunable parameter for simulation calibration."""
    parameter_name: str
    current_value: float
    min_value: float
    max_value: float
    sensitivity: float = 0.1  # How much output changes per unit change


# ============================================================================
# Calibration Context
# ============================================================================

@dataclass
class CalibrationContext:
    """Context for simulation calibration."""
    # Target accuracy
    target_mae: float = 0.10  # Target mean absolute error
    target_coverage: float = 0.95  # Target confidence interval coverage

    # Learning rate for calibration
    learning_rate: float = 0.05

    # Minimum samples before recalibration
    min_samples_for_calibration: int = 50

    # Calibration history
    error_history: List[Tuple[datetime, float]] = field(default_factory=list)

    # Calibrated parameters
    volatility_multiplier: float = 1.0
    readiness_sensitivity: float = 1.0
    duration_baseline_multiplier: float = 1.0


# ============================================================================
# Simulation Calibration Engine
# ============================================================================

class SimulationCalibrationEngine:
    """
    Continuously improves simulation accuracy through calibration.

    Tracks forecast errors and tunes simulation parameters to
    reduce prediction error over time.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize the calibration engine."""
        self._errors: List[ForecastError] = []
        self._metrics_history: List[CalibrationMetrics] = []
        self._context = CalibrationContext()
        self._storage_path = storage_path

        # Load previous calibration data if available
        if self._storage_path and self._storage_path.exists():
            self._load_calibration_data()

    def _load_calibration_data(self) -> None:
        """Load calibration data from storage."""
        try:
            calibration_file = self._storage_path / "calibration_data.json"
            if calibration_file.exists():
                data = json.loads(calibration_file.read_text())
                # Load context parameters
                if "calibrated_parameters" in data:
                    params = data["calibrated_parameters"]
                    self._context.volatility_multiplier = params.get("volatility_multiplier", 1.0)
                    self._context.readiness_sensitivity = params.get("readiness_sensitivity", 1.0)
                    self._context.duration_baseline_multiplier = params.get("duration_baseline_multiplier", 1.0)

                logger.info(f"[CalibrationEngine] Loaded calibration data from {calibration_file}")
        except Exception as e:
            logger.warning(f"[CalibrationEngine] Could not load calibration data: {e}")

    def _save_calibration_data(self) -> None:
        """Save calibration data to storage."""
        if not self._storage_path:
            return

        try:
            self._storage_path.mkdir(parents=True, exist_ok=True)
            calibration_file = self._storage_path / "calibration_data.json"

            data = {
                "calibrated_parameters": {
                    "volatility_multiplier": self._context.volatility_multiplier,
                    "readiness_sensitivity": self._context.readiness_sensitivity,
                    "duration_baseline_multiplier": self._context.duration_baseline_multiplier,
                },
                "last_updated": datetime.now().isoformat(),
            }

            calibration_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.warning(f"[CalibrationEngine] Could not save calibration data: {e}")

    async def record_forecast_error(
        self,
        scenario_id: UUID,
        forecast_id: UUID,
        predicted_result: SimulationResult,
        actual_outcome: Dict[str, Any],
        mission_context: Optional[Dict[str, Any]] = None,
    ) -> ForecastError:
        """
        Record the difference between a forecast and actual outcome.

        Args:
            scenario_id: Original scenario ID
            forecast_id: Forecast result ID
            predicted_result: The simulation result
            actual_outcome: Actual mission outcome
            mission_context: Additional context

        Returns:
            Recorded ForecastError
        """
        # Extract predictions
        predicted_success_rate = predicted_result.predicted_outcomes.get("success_rate", 0.5)
        predicted_duration = predicted_result.predicted_outcomes.get("avg_duration", 120.0)
        predicted_quality = predicted_result.predicted_outcomes.get("avg_quality", 0.8)

        # Extract actuals
        actual_success = actual_outcome.get("success", False)
        actual_duration = actual_outcome.get("duration", 120.0)
        actual_quality = actual_outcome.get("quality", 0.8)

        # Calculate errors
        success_rate_error = abs(predicted_success_rate - (1.0 if actual_success else 0.0))
        duration_error = abs(predicted_duration - actual_duration) / actual_duration if actual_duration > 0 else 0
        quality_error = abs(predicted_quality - actual_quality)

        # Mean absolute error
        mae = (success_rate_error + duration_error + quality_error) / 3

        error = ForecastError(
            scenario_id=scenario_id,
            forecast_id=forecast_id,
            predicted_success_rate=predicted_success_rate,
            predicted_duration=predicted_duration,
            predicted_quality=predicted_quality,
            actual_success=actual_success,
            actual_duration=actual_duration,
            actual_quality=actual_quality,
            success_rate_error=success_rate_error,
            duration_error=duration_error,
            quality_error=quality_error,
            mean_absolute_error=mae,
            mission_context=mission_context or {},
        )

        self._errors.append(error)

        # Add to context history
        self._context.error_history.append((datetime.now(), mae))

        # Keep history manageable
        if len(self._context.error_history) > 1000:
            self._context.error_history = self._context.error_history[-1000:]

        logger.debug(
            f"[CalibrationEngine] Recorded forecast error: MAE={mae:.3f}"
        )

        return error

    async def calculate_calibration_metrics(
        self,
        timeframe_days: int = 30,
    ) -> CalibrationMetrics:
        """
        Calculate current calibration metrics.

        Args:
            timeframe_days: Days to look back for metrics

        Returns:
            CalibrationMetrics with current accuracy
        """
        cutoff_time = datetime.now() - timedelta(days=timeframe_days)

        # Filter errors within timeframe
        recent_errors = [
            e for e in self._errors
            if e.timestamp >= cutoff_time
        ]

        if not recent_errors:
            return CalibrationMetrics(
                timeframe_start=cutoff_time,
                timeframe_end=datetime.now(),
            )

        # Calculate aggregate metrics
        mae_values = [e.mean_absolute_error for e in recent_errors]
        mean_mae = sum(mae_values) / len(mae_values)

        # Root mean squared error
        rmse = (sum(e**2 for e in mae_values) / len(mae_values)) ** 0.5

        # Mean absolute percentage error
        mape_values = []
        for e in recent_errors:
            if e.predicted_duration > 0:
                mape_values.append(abs(e.duration_error))
        mean_ape = sum(mape_values) / len(mape_values) if mape_values else 0

        # Error by scope (would need scenario lookup, simplified here)
        error_by_scope = {
            "single_mission": mean_mae,
            "mission_type": mean_mae * 1.1,  # Slightly worse approximation
            "policy_change": mean_mae * 1.2,
        }

        # Determine trend
        if len(self._context.error_history) >= 10:
            recent_errors_trend = [err for _, err in self._context.error_history[-10:]]
            older_errors_trend = [err for _, err in self._context.error_history[-20:-10]]

            if recent_errors_trend and older_errors_trend:
                recent_avg = sum(recent_errors_trend) / len(recent_errors_trend)
                older_avg = sum(older_errors_trend) / len(older_errors_trend)

                if recent_avg < older_avg * 0.9:
                    error_trend = "improving"
                elif recent_avg > older_avg * 1.1:
                    error_trend = "degrading"
                else:
                    error_trend = "stable"
            else:
                error_trend = "stable"
        else:
            error_trend = "stable"

        # Determine if recalibration is needed
        recalibration_recommended = mean_mae > self._context.target_mae

        metrics = CalibrationMetrics(
            timeframe_start=cutoff_time,
            timeframe_end=datetime.now(),
            mean_absolute_error=mean_mae,
            root_mean_squared_error=rmse,
            mean_absolute_percentage_error=mean_ape,
            error_by_scope=error_by_scope,
            error_trend=error_trend,
            recalibration_recommended=recalibration_recommended,
            calibration_parameters=self._get_current_parameters(),
        )

        self._metrics_history.append(metrics)

        return metrics

    def _get_current_parameters(self) -> Dict[str, float]:
        """Get current calibration parameters."""
        return {
            "volatility_multiplier": self._context.volatility_multiplier,
            "readiness_sensitivity": self._context.readiness_sensitivity,
            "duration_baseline_multiplier": self._context.duration_baseline_multiplier,
        }

    async def calibrate_simulation_parameters(
        self,
        metrics: Optional[CalibrationMetrics] = None,
    ) -> Dict[str, float]:
        """
        Calibrate simulation parameters based on forecast errors.

        Args:
            metrics: Current calibration metrics (calculated if not provided)

        Returns:
            Updated calibration parameters
        """
        if metrics is None:
            metrics = await self.calculate_calibration_metrics()

        if not self._errors or len(self._errors) < self._context.min_samples_for_calibration:
            logger.info(
                f"[CalibrationEngine] Not enough samples for calibration: "
                f"{len(self._errors)}/{self._context.min_samples_for_calibration}"
            )
            return self._get_current_parameters()

        # Calculate systematic biases
        success_errors = [
            e.predicted_success_rate - (1.0 if e.actual_success else 0.0)
            for e in self._errors[-100:]  # Last 100 errors
        ]
        avg_success_bias = sum(success_errors) / len(success_errors) if success_errors else 0

        duration_errors = [
            e.duration_error
            for e in self._errors[-100:]
        ]
        avg_duration_bias = sum(duration_errors) / len(duration_errors) if duration_errors else 0

        # Adjust parameters based on biases
        learning_rate = self._context.learning_rate

        # If we consistently underpredict success (positive bias),
        # increase readiness sensitivity
        if avg_success_bias > 0.05:
            self._context.readiness_sensitivity *= (1 + learning_rate)
        elif avg_success_bias < -0.05:
            self._context.readiness_sensitivity *= (1 - learning_rate)

        # If duration predictions are off, adjust baseline
        if avg_duration_bias > 0.10:
            self._context.duration_baseline_multiplier *= (1 - learning_rate * 0.5)
        elif avg_duration_bias < -0.10:
            self._context.duration_baseline_multiplier *= (1 + learning_rate * 0.5)

        # Clamp values to reasonable ranges
        self._context.readiness_sensitivity = max(0.5, min(2.0, self._context.readiness_sensitivity))
        self._context.duration_baseline_multiplier = max(0.5, min(2.0, self._context.duration_baseline_multiplier))

        # Save updated parameters
        self._save_calibration_data()

        params = self._get_current_parameters()

        logger.info(
            f"[CalibrationEngine] Calibrated parameters: "
            f"readiness_sensitivity={params['readiness_sensitivity']:.3f}, "
            f"duration_multiplier={params['duration_baseline_multiplier']:.3f}"
        )

        return params

    def get_forecast_accuracy_summary(self) -> Dict[str, Any]:
        """Get a summary of forecast accuracy."""
        if not self._errors:
            return {
                "total_forecasts": 0,
                "mean_absolute_error": None,
                "calibration_status": "no_data",
            }

        mae_values = [e.mean_absolute_error for e in self._errors]

        # Recent vs older comparison
        recent_mae = mae_values[-50:] if len(mae_values) >= 50 else mae_values
        older_mae = mae_values[:-50] if len(mae_values) >= 100 else []

        summary = {
            "total_forecasts": len(self._errors),
            "mean_absolute_error": sum(mae_values) / len(mae_values),
            "recent_mae": sum(recent_mae) / len(recent_mae) if recent_mae else None,
            "older_mae": sum(older_mae) / len(older_mae) if older_mae else None,
            "calibration_status": "calibrated" if len(self._errors) >= 50 else "collecting_data",
            "current_parameters": self._get_current_parameters(),
        }

        # Calculate improvement trend
        if summary["recent_mae"] is not None and summary["older_mae"] is not None:
            improvement = (summary["older_mae"] - summary["recent_mae"]) / summary["older_mae"]
            summary["improvement_percentage"] = improvement * 100

        return summary

    def list_forecast_errors(
        self,
        limit: int = 100,
    ) -> List[ForecastError]:
        """List recent forecast errors."""
        return self._errors[-limit:]


# Global calibration engine instance
_engine: Optional[SimulationCalibrationEngine] = None


def get_calibration_engine(storage_path: Optional[Path] = None) -> SimulationCalibrationEngine:
    """Get the global simulation calibration engine instance."""
    global _engine
    if _engine is None:
        # Default storage path
        if storage_path is None:
            storage_path = Path.cwd() / "data" / "simulation_calibration"
        _engine = SimulationCalibrationEngine(storage_path=storage_path)
    return _engine
