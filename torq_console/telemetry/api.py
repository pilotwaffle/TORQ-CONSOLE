"""
Adaptive System Telemetry API

Provides observability into the adaptive cognition loop.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from .collector import AdaptiveTelemetryCollector, EvaluationDistributionAnalyzer
from .models import (
    TelemetryReport,
    MetricDistribution,
    SystemAlert,
    ObservabilityConfig,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/telemetry", tags=["adaptive-telemetry"])


# ============================================================================
# Dependencies
# ============================================================================

def get_collector() -> AdaptiveTelemetryCollector:
    """Get telemetry collector instance."""
    from ..dependencies import get_supabase_client
    supabase = get_supabase_client()
    return AdaptiveTelemetryCollector(supabase)


def get_analyzer() -> EvaluationDistributionAnalyzer:
    """Get distribution analyzer instance."""
    from ..dependencies import get_supabase_client
    supabase = get_supabase_client()
    return EvaluationDistributionAnalyzer(supabase)


# ============================================================================
# Telemetry Report Endpoints
# ============================================================================

@router.get("/report", response_model=TelemetryReport)
async def get_telemetry_report(
    days_back: int = Query(7, ge=1, le=90, description="Lookback period in days"),
    collector: AdaptiveTelemetryCollector = Depends(get_collector),
):
    """
    Get comprehensive telemetry report.

    Includes signal volume, proposal flow, experiment outcomes,
    and system health assessment.
    """
    return await collector.collect_report(days_back=days_back)


@router.get("/signals")
async def get_signal_metrics(
    days_back: int = Query(7, ge=1, le=90),
    collector: AdaptiveTelemetryCollector = Depends(get_collector),
):
    """Get signal generation metrics grouped by family."""
    since = None  # Collector will compute
    from datetime import datetime, timedelta
    since = datetime.now() - timedelta(days=days_back)

    return await collector.collect_signal_volume_metrics(since)


@router.get("/proposals")
async def get_proposal_metrics(
    days_back: int = Query(7, ge=1, le=90),
    collector: AdaptiveTelemetryCollector = Depends(get_collector),
):
    """Get proposal flow metrics including approval rates."""
    from datetime import datetime, timedelta
    since = datetime.now() - timedelta(days=days_back)

    return await collector.collect_proposal_flow_metrics(since)


@router.get("/experiments")
async def get_experiment_metrics(
    days_back: int = Query(7, ge=1, le=90),
    collector: AdaptiveTelemetryCollector = Depends(get_collector),
):
    """Get experiment outcome metrics including success and rollback rates."""
    from datetime import datetime, timedelta
    since = datetime.now() - timedelta(days=days_back)

    return await collector.collect_experiment_metrics(since)


@router.get("/conversions")
async def get_conversion_metrics(
    days_back: int = Query(7, ge=1, le=90),
    collector: AdaptiveTelemetryCollector = Depends(get_collector),
):
    """
    Get signal-to-proposal conversion metrics.

    Healthy range: 5-25%. Above 25% indicates over-sensitive
    signal extraction; below 5% indicates overly strict rules.
    """
    from datetime import datetime, timedelta
    since = datetime.now() - timedelta(days=days_back)

    return await collector.collect_conversion_metrics(since)


# ============================================================================
# Distribution Analysis Endpoints
# ============================================================================

@router.get("/distributions")
async def get_metric_distributions(
    days_back: int = Query(7, ge=1, le=90),
    analyzer: EvaluationDistributionAnalyzer = Depends(get_analyzer),
):
    """
    Get evaluation metric distributions.

    Returns mean, median, p50, p75, p90, p95 for each metric.
    Used for baseline calibration and threshold tuning.
    """
    return await analyzer.analyze_distributions(days_back=days_back)


# ============================================================================
# System Health Endpoints
# ============================================================================

@router.get("/health")
async def get_system_health(
    days_back: int = Query(7, ge=1, le=90),
    collector: AdaptiveTelemetryCollector = Depends(get_collector),
):
    """
    Get overall system health assessment.

    Returns health score, quality indicators, and recommendations.
    """
    report = await collector.collect_report(days_back=days_back)
    return {
        "health_score": report.system_health.health_score,
        "signal_quality": report.system_health.signal_quality,
        "proposal_quality": report.system_health.proposal_quality,
        "experiment_quality": report.system_health.experiment_quality,
        "noisy_assets": report.system_health.noisy_assets,
        "recommendations": report.system_health.recommendations
    }


@router.get("/alerts")
async def get_system_alerts(
    days_back: int = Query(7, ge=1, le=90),
    collector: AdaptiveTelemetryCollector = Depends(get_collector),
):
    """
    Get active system alerts.

    Returns alerts about low signal quality, high rollback rates,
    noisy assets, and other issues requiring attention.
    """
    report = await collector.collect_report(days_back=days_back)

    alerts = []

    health = report.system_health

    # Low signal quality
    if health.signal_quality != "good":
        alerts.append(SystemAlert(
            alert_type="low_signal_quality",
            severity="warning" if health.signal_quality == "needs_attention" else "info",
            title="Signal quality needs attention",
            description=f"Signal generation may be too conservative or too noisy. Families: {list(report.signals.by_family.keys())}",
            metrics_snapshot={"signal_families": report.signals.by_family}
        ))

    # Volatile proposals
    if health.proposal_quality == "volatile":
        alerts.append(SystemAlert(
            alert_type="volatile_approval",
            severity="warning",
            title="Proposal approval rate is volatile",
            description=f"Approval rate: {report.proposals.approval_rate:.1%}. Should be 30-80%.",
            metrics_snapshot={"approval_rate": report.proposals.approval_rate}
        ))

    # High rollback rate
    if health.experiment_quality != "good":
        alerts.append(SystemAlert(
            alert_type="high_rollback_rate",
            severity="warning",
            title="Experiment rollback rate is concerning",
            description=f"Rollback rate: {report.experiments.rolled_back_count}/{report.experiments.total_experiments}",
            metrics_snapshot={
                "success_rate": report.experiments.success_rate,
                "rolled_back": report.experiments.rolled_back_count
            }
        ))

    # Noisy assets
    if health.noisy_assets:
        alerts.append(SystemAlert(
            alert_type="noisy_asset",
            severity="info",
            title="Noisy assets detected",
            description=f"Assets generating many proposals: {health.noisy_assets[:3]}",
            affected_assets=health.noisy_assets,
            metrics_snapshot={"noisy_assets": health.noisy_assets}
        ))

    # Low health score
    if health.health_score < 0.6:
        alerts.append(SystemAlert(
            alert_type="low_health_score",
            severity="critical",
            title="System health score is low",
            description=f"Health score: {health.health_score:.1%}. Review recommendations.",
            metrics_snapshot={"health_score": health.health_score}
        ))

    return alerts


# ============================================================================
# Configuration Endpoints
# ============================================================================

@router.get("/config", response_model=ObservabilityConfig)
async def get_observability_config():
    """Get current observability configuration."""
    # For now, return defaults - in production this would be stored in database
    return ObservabilityConfig()


@router.put("/config")
async def update_observability_config(
    config: ObservabilityConfig
):
    """Update observability configuration."""
    # In production, persist to database
    return {"success": True, "config": config}


# ============================================================================
# Readiness Assessment Endpoints
# ============================================================================

@router.get("/readiness")
async def get_readiness_assessment(
    days_observed: int = Query(14, ge=1, le=90, description="Days of observation to assess"),
    collector: AdaptiveTelemetryCollector = Depends(get_collector),
):
    """
    Assess whether the adaptive system is ready to leave observation mode.

    Returns a comprehensive assessment of three indicators:
    - Signal Stability: Conversion rate, distribution, volume plateau
    - Experiment Reliability: Success rate, rollback rate
    - Positive System Drift: Upward trend in baseline scores

    When all indicators show PASSING, the system can enable Tier 1 auto-promotion.
    """
    from ..adaptive_telemetry import AdaptiveReadinessChecker
    from ..dependencies import get_supabase_client

    supabase = get_supabase_client()
    analyzer = EvaluationDistributionAnalyzer(supabase)
    checker = AdaptiveReadinessChecker(supabase, collector, analyzer)

    return await checker.assess_readiness(days_observed=days_observed)


@router.get("/readiness/status")
async def get_readiness_status_only(
    collector: AdaptiveTelemetryCollector = Depends(get_collector),
):
    """
    Quick check: Can the system leave observation mode?

    Returns a simple boolean response suitable for health checks and dashboards.
    """
    from ..adaptive_telemetry import AdaptiveReadinessChecker
    from ..dependencies import get_supabase_client

    supabase = get_supabase_client()
    analyzer = EvaluationDistributionAnalyzer(supabase)
    checker = AdaptiveReadinessChecker(supabase, collector, analyzer)

    assessment = await checker.assess_readiness(days_observed=14)

    return {
        "can_leave_observation_mode": assessment.can_leave_observation_mode,
        "confidence": assessment.confidence,
        "days_observed": assessment.days_observed,
        "adaptations_per_week": assessment.adaptations_per_week,
        "velocity_status": assessment.velocity_status,
        "indicators": {
            "signal_stability": assessment.signal_stability.status,
            "experiment_reliability": assessment.experiment_reliability.status,
            "system_drift": assessment.system_drift.status,
        }
    }
