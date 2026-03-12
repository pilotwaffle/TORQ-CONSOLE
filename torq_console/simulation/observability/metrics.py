"""
TORQ Layer 10 - Simulation Observability Metrics

L10-M1: Provides specialized observability metrics for simulation accuracy,
risk assessment, and forecasting performance.

This module provides metrics collectors and exporters for:
- Simulation runtime metrics
- Forecast confidence bands
- Risk score distributions
- Calibration accuracy tracking
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from collections import defaultdict
from functools import wraps

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


# ============================================================================
# Metric Types
# ============================================================================

class SimulationMetric(BaseModel):
    """A single simulation metric."""
    metric_name: str
    metric_value: float
    metric_unit: str
    timestamp: datetime
    tags: Dict[str, str] = {}
    dimensions: Dict[str, str] = {}


class MetricBatch(BaseModel):
    """A batch of metrics for export."""
    batch_id: UUID
    metrics: List[SimulationMetric]
    timestamp: datetime
    source: str


# ============================================================================
# Simulation Performance Metrics
# ============================================================================

@dataclass
class SimulationPerformanceTracker:
    """Tracks simulation performance metrics."""

    # Runtime metrics
    simulation_runtimes_ms: List[float] = field(default_factory=list)
    iteration_counts: List[int] = field(default_factory=list)

    # Outcome distributions
    success_rate_distribution: List[float] = field(default_factory=list)
    confidence_band_distribution: List[float] = field(default_factory=list)

    # Error tracking
    forecast_errors: List[float] = field(default_factory=list)

    def record_simulation(self, runtime_ms: float, iterations: int) -> None:
        """Record a simulation execution."""
        self.simulation_runtimes_ms.append(runtime_ms)
        self.iteration_counts.append(iterations)

    def record_outcome(self, success_rate: float, confidence: float) -> None:
        """Record simulation outcome distribution."""
        self.success_rate_distribution.append(success_rate)
        self.confidence_band_distribution.append(confidence)

    def record_forecast_error(self, error: float) -> None:
        """Record a forecast error."""
        self.forecast_errors.append(error)

    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics."""
        summary = {}

        if self.simulation_runtimes_ms:
            summary["avg_runtime_ms"] = sum(self.simulation_runtimes_ms) / len(self.simulation_runtimes_ms)
            summary["p95_runtime_ms"] = sorted(self.simulation_runtimes_ms)[int(len(self.simulation_runtimes_ms) * 0.95)]
            summary["p99_runtime_ms"] = sorted(self.simulation_runtimes_ms)[int(len(self.simulation_runtimes_ms) * 0.99)]

        if self.iteration_counts:
            summary["avg_iterations"] = sum(self.iteration_counts) / len(self.iteration_counts)
            summary["total_simulations"] = sum(self.iteration_counts)

        if self.success_rate_distribution:
            summary["avg_success_rate"] = sum(self.success_rate_distribution) / len(self.success_rate_distribution)
            summary["min_success_rate"] = min(self.success_rate_distribution)
            summary["max_success_rate"] = max(self.success_rate_distribution)

        if self.confidence_band_distribution:
            summary["avg_confidence"] = sum(self.confidence_band_distribution) / len(self.confidence_band_distribution)

        if self.forecast_errors:
            summary["mean_forecast_error"] = sum(self.forecast_errors) / len(self.forecast_errors)
            summary["forecast_error_std"] = self._calculate_std(self.forecast_errors)

        return summary

    def _calculate_std(self, values: List[float]) -> float:
        """Calculate standard deviation."""
        if not values:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        return variance ** 0.5


# ============================================================================
# Risk Metrics Collector
# ============================================================================

@dataclass
class RiskMetricsCollector:
    """Collects and aggregates risk-related metrics."""

    # Risk score distribution
    risk_scores_by_category: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))

    # Mitigation tracking
    mitigation_trigger_count: int = 0
    mitigation_success_count: int = 0

    # Policy simulation frequency
    policy_simulations: List[datetime] = field(default_factory=list)

    # Severity distribution
    severity_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def record_risk_assessment(
        self,
        category: str,
        risk_score: float,
        severity: str,
    ) -> None:
        """Record a risk assessment."""
        self.risk_scores_by_category[category].append(risk_score)
        self.severity_counts[severity] += 1

    def record_mitigation_trigger(self) -> None:
        """Record a mitigation being triggered."""
        self.mitigation_trigger_count += 1

    def record_mitigation_success(self) -> None:
        """Record a successful mitigation."""
        self.mitigation_success_count += 1

    def record_policy_simulation(self) -> None:
        """Record a policy simulation run."""
        self.policy_simulations.append(datetime.now())

    def get_summary(self, timeframe_minutes: int = 60) -> None:
        """Get risk metrics summary."""
        cutoff = datetime.now() - timedelta(minutes=timeframe_minutes)
        recent_policy_sims = [t for t in self.policy_simulations if t >= cutoff]

        summary = {
            "total_risk_assessments": sum(
                len(scores) for scores in self.risk_scores_by_category.values()
            ),
            "avg_risk_score_by_category": {},
            "mitigation_trigger_count": self.mitigation_trigger_count,
            "mitigation_success_count": self.mitigation_success_count,
            "mitigation_success_rate": (
                self.mitigation_success_count / self.mitigation_trigger_count
                if self.mitigation_trigger_count > 0
                else 0
            ),
            "policy_simulations_last_hour": len(recent_policy_sims),
            "severity_distribution": dict(self.severity_counts),
        }

        # Calculate average risk score by category
        for cat, scores in self.risk_scores_by_category.items():
            if scores:
                summary["avg_risk_score_by_category"][cat] = sum(scores) / len(scores)

        return summary


# ============================================================================
# Metrics Decorator
# ============================================================================

def track_simulation_metrics(func: Callable) -> Callable:
    """
    Decorator to track simulation execution metrics.

    Usage:
        @track_simulation_metrics
        async def run_simulation(self, scenario_id: UUID) -> SimulationResult:
            ...
    """
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        start_time = time.time()
        try:
            result = await func(self, *args, **kwargs)

            # Record metrics
            runtime_ms = (time.time() - start_time) * 1000

            if hasattr(self, "_performance_tracker"):
                iterations = getattr(result, "total_simulations", 0)
                self._performance_tracker.record_simulation(runtime_ms, iterations)

                if hasattr(result, "success_rate"):
                    self._performance_tracker.record_outcome(
                        result.success_rate,
                        getattr(result, "confidence", 0.5)
                    )

            return result
        except Exception as e:
            # Record failure
            runtime_ms = (time.time() - start_time) * 1000
            logger.error(f"[Metrics] Simulation failed after {runtime_ms:.2f}ms: {e}")
            raise

    return wrapper


# ============================================================================
# Metrics Export Service
# ============================================================================

class SimulationMetricsExporter:
    """Exports simulation metrics to external systems."""

    def __init__(self):
        """Initialize the metrics exporter."""
        self._performance_tracker = SimulationPerformanceTracker()
        self._risk_collector = RiskMetricsCollector()

    def get_performance_tracker(self) -> SimulationPerformanceTracker:
        """Get the performance tracker."""
        return self._performance_tracker

    def get_risk_collector(self) -> RiskMetricsCollector:
        """Get the risk collector."""
        return self._risk_collector

    async def export_metrics_batch(self) -> MetricBatch:
        """
        Export current metrics as a batch.

        Returns:
            MetricBatch with current metrics
        """
        metrics = []

        # Performance metrics
        perf_summary = self._performance_tracker.get_summary()
        for name, value in perf_summary.items():
            metrics.append(SimulationMetric(
                metric_name=f"simulation.{name}",
                metric_value=float(value) if isinstance(value, (int, float)) else 0.0,
                metric_unit="",
                timestamp=datetime.now(),
                tags={"layer": "10"},
            ))

        # Risk metrics
        risk_summary = self._risk_collector.get_summary()
        for name, value in risk_summary.items():
            if isinstance(value, (int, float)):
                metrics.append(SimulationMetric(
                    metric_name=f"risk.{name}",
                    metric_value=float(value),
                    metric_unit="",
                    timestamp=datetime.now(),
                    tags={"layer": "10"},
                ))

        return MetricBatch(
            batch_id=uuid4(),
            metrics=metrics,
            timestamp=datetime.now(),
            source="torq_simulation_layer",
        )

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get all current metrics as a dictionary."""
        return {
            "performance": self._performance_tracker.get_summary(),
            "risk": self._risk_collector.get_summary(),
        }


# Global metrics exporter instance
_exporter: Optional[SimulationMetricsExporter] = None


def get_metrics_exporter() -> SimulationMetricsExporter:
    """Get the global simulation metrics exporter instance."""
    global _exporter
    if _exporter is None:
        _exporter = SimulationMetricsExporter()
    return _exporter
