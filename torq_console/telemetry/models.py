"""
Adaptive System Telemetry Models

Data structures for system observability and baseline calibration.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ============================================================================
# Telemetry Report Models
# ============================================================================

class TelemetryMetric(BaseModel):
    """A single telemetry data point."""
    metric_name: str
    metric_value: float
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MetricDistribution(BaseModel):
    """Statistical distribution of a metric."""
    metric_name: str
    count: int
    mean: float
    median: float
    p50: float
    p75: float
    p90: float
    p95: float


class SignalVolumeMetrics(BaseModel):
    """Signal generation metrics."""
    total_signals: int
    signals_per_day: float
    by_family: Dict[str, int] = Field(default_factory=dict)
    by_strength: Dict[str, int] = Field(default_factory=dict)
    by_source: Dict[str, int] = Field(default_factory=dict)


class ProposalFlowMetrics(BaseModel):
    """Proposal generation and approval metrics."""
    total_proposals: int
    proposals_per_day: float
    by_status: Dict[str, int] = Field(default_factory=dict)
    by_risk_tier: Dict[str, int] = Field(default_factory=dict)
    by_asset: Dict[str, int] = Field(default_factory=dict)
    approval_rate: float


class ExperimentMetrics(BaseModel):
    """Experiment outcome metrics."""
    total_experiments: int
    experiments_per_day: float
    by_status: Dict[str, int] = Field(default_factory=dict)
    currently_running: int
    total_assignments: int
    promoted_count: int
    rolled_back_count: int
    success_rate: float


class ConversionMetrics(BaseModel):
    """Signal-to-proposal conversion metrics."""
    total_signals: int
    total_proposals: int
    conversion_rate: float  # proposals / signals (healthy: 5-25%)
    pending_signals: int
    by_signal_type: Dict[str, int] = Field(default_factory=dict)


class SystemHealthMetrics(BaseModel):
    """Aggregated system health indicators."""
    health_score: float  # 0.0 to 1.0
    signal_quality: str  # "good" | "needs_attention"
    proposal_quality: str  # "good" | "volatile"
    experiment_quality: str  # "good" | "unstable"
    noisy_assets: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class TelemetryReport(BaseModel):
    """Comprehensive telemetry report for the adaptive system."""
    period_days: int
    from_date: datetime
    to_date: datetime
    signals: SignalVolumeMetrics
    proposals: ProposalFlowMetrics
    experiments: ExperimentMetrics
    conversions: ConversionMetrics
    system_health: SystemHealthMetrics
    generated_at: datetime


# ============================================================================
# Observability Models
# ============================================================================

class ObservabilityConfig(BaseModel):
    """Configuration for telemetry collection."""
    observation_mode: bool = Field(default=True, description="Run in observation mode (no auto-promotion)")
    aggressive_promotion: bool = Field(default=False, description="Enable aggressive promotion (not recommended)")
    min_promotion_confidence: float = Field(default=0.90, ge=0.0, le=1.0)
    min_promotion_sample_size: int = Field(default=50, ge=1)

    # Noisy asset detection
    max_proposals_per_asset_per_week: int = Field(default=5, ge=1)
    max_rollback_rate: float = Field(default=0.20, ge=0.0, le=1.0)

    # Alerting thresholds
    alert_on_low_signal_quality: bool = Field(default=True)
    alert_on_high_rollback_rate: bool = Field(default=True)
    alert_on_noisy_assets: bool = Field(default=True)


class SystemAlert(BaseModel):
    """An alert about system behavior requiring attention."""
    alert_type: str  # "low_signal_quality", "high_rollback_rate", "noisy_asset", "volatile_approval"
    severity: str  # "info" | "warning" | "critical"
    title: str
    description: str
    affected_assets: List[str] = Field(default_factory=list)
    metrics_snapshot: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    resolved: bool = False
