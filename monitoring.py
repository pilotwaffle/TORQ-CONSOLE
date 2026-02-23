"""
TORQ Console: Drift/Regression Monitoring Module

This module provides monitoring and alerting functionality for detecting
drift and regression in TORQ Console based on learning_events data.

Key Features:
- Alert threshold comparison against 7-day baseline
- Drift detection algorithms
- Metric computation helpers
- Alert notification generation
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from enum import Enum

import httpx

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of alerts that can be generated."""
    FALLBACK_SPIKE = "fallback_spike"
    ERROR_SPIKE = "error_spike"
    LATENCY_SPIKE = "latency_spike"
    DUPLICATE_SPIKE = "duplicate_spike"
    MODEL_DRIFT = "model_drift"
    HEALTH_DECLINE = "health_decline"


@dataclass
class ThresholdConfig:
    """Configuration for alert thresholds."""
    low: float = 1.5      # Alert if deviation > 1.5x baseline
    medium: float = 2.0   # Alert if deviation > 2.0x baseline
    high: float = 3.0     # Alert if deviation > 3.0x baseline

    def get_severity(self, deviation_ratio: float) -> Optional[AlertSeverity]:
        """Determine severity based on deviation ratio."""
        if deviation_ratio >= self.high:
            return AlertSeverity.CRITICAL
        elif deviation_ratio >= self.medium:
            return AlertSeverity.HIGH
        elif deviation_ratio >= self.low:
            return AlertSeverity.MEDIUM
        return None


@dataclass
class MetricSnapshot:
    """Snapshot of current metrics."""
    metric_date: str
    total_events: int
    successful_events: int
    failed_events: int
    fallback_events: int
    duplicate_events: int
    fallback_rate: float
    error_rate: float
    duplicate_rate: float
    latency_p50: float
    latency_p95: float
    latency_p99: float
    health_score: float


@dataclass
class BaselineSnapshot:
    """Snapshot of baseline metrics."""
    baseline_name: str
    window_days: int
    fallback_rate: float
    error_rate: float
    duplicate_rate: float
    latency_p50: float
    latency_p95: float
    latency_p99: float
    valid_until: Optional[str] = None


@dataclass
class Alert:
    """Represents a monitoring alert."""
    alert_type: AlertType
    severity: AlertSeverity
    metric_name: str
    current_value: float
    baseline_value: float
    deviation_ratio: float
    threshold_config: ThresholdConfig
    metric_date: str
    comparison_window_days: int
    affected_model: Optional[str] = None
    affected_backend: Optional[str] = None
    affected_agent: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)


class DriftDetector:
    """
    Detects drift and regression by comparing current metrics against baseline.

    Algorithm:
    1. Fetch current day metrics from mv_daily_metrics
    2. Fetch 7-day rolling baseline
    3. For each metric, calculate deviation ratio (current / baseline)
    4. Compare against thresholds to determine severity
    5. Generate alerts for significant deviations
    """

    DEFAULT_THRESHOLDS = ThresholdConfig(low=1.5, medium=2.0, high=3.0)

    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        thresholds: Optional[ThresholdConfig] = None
    ):
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.thresholds = thresholds or self.DEFAULT_THRESHOLDS

    async def get_current_metrics(self, date: Optional[str] = None) -> Optional[MetricSnapshot]:
        """Fetch current day metrics from materialized view."""
        target_date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.supabase_url}/rest/v1/mv_daily_metrics",
                headers={
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                },
                params={"metric_date": f"eq.{target_date}", "limit": 1}
            )

        if response.status_code != 200:
            logger.error(f"Failed to fetch current metrics: {response.status_code}")
            return None

        data = response.json()
        if not data:
            logger.warning(f"No metrics found for date: {target_date}")
            return None

        row = data[0]
        return MetricSnapshot(
            metric_date=row.get("metric_date"),
            total_events=row.get("total_events", 0),
            successful_events=row.get("successful_events", 0),
            failed_events=row.get("failed_events", 0),
            fallback_events=row.get("fallback_events", 0),
            duplicate_events=row.get("duplicate_events", 0),
            fallback_rate=float(row.get("fallback_rate", 0)),
            error_rate=float(row.get("error_rate", 0)),
            duplicate_rate=float(row.get("duplicate_rate", 0)),
            latency_p50=float(row.get("latency_p50", 0) or 0),
            latency_p95=float(row.get("latency_p95", 0) or 0),
            latency_p99=float(row.get("latency_p99", 0) or 0),
            health_score=float(row.get("health_score", 0) or 0),
        )

    async def get_baseline(self, baseline_name: str = "7day_rolling") -> Optional[BaselineSnapshot]:
        """Fetch baseline metrics for comparison."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.supabase_url}/rest/v1/monitoring_baseline",
                headers={
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                },
                params={"baseline_name": f"eq.{baseline_name}", "limit": 1}
            )

        if response.status_code != 200:
            logger.error(f"Failed to fetch baseline: {response.status_code}")
            return None

        data = response.json()
        if not data:
            logger.warning(f"No baseline found: {baseline_name}")
            return None

        row = data[0]
        return BaselineSnapshot(
            baseline_name=row.get("baseline_name"),
            window_days=row.get("baseline_window_days", 7),
            fallback_rate=float(row.get("baseline_fallback_rate", 0) or 0),
            error_rate=float(row.get("baseline_error_rate", 0) or 0),
            duplicate_rate=float(row.get("baseline_duplicate_rate", 0) or 0),
            latency_p50=float(row.get("baseline_latency_p50", 0) or 0),
            latency_p95=float(row.get("baseline_latency_p95", 0) or 0),
            latency_p99=float(row.get("baseline_latency_p99", 0) or 0),
            valid_until=row.get("valid_until"),
        )

    def calculate_deviation(self, current: float, baseline: float) -> Optional[float]:
        """Calculate deviation ratio (current / baseline)."""
        if baseline == 0:
            # If baseline is 0, any current value is infinite deviation
            # But we need to handle this carefully
            if current > 0:
                return float('inf')  # Max deviation
            return 1.0  # Both 0, no deviation
        if current < 0:
            current = 0
        return round(current / baseline, 4)

    def detect_fallback_spike(
        self,
        current: MetricSnapshot,
        baseline: BaselineSnapshot
    ) -> Optional[Alert]:
        """Detect fallback rate spike."""
        if baseline.fallback_rate == 0:
            if current.fallback_rate > 0.01:  # More than 1% when baseline was 0
                deviation = float('inf')
            else:
                return None
        else:
            deviation = self.calculate_deviation(current.fallback_rate, baseline.fallback_rate)

        severity = self.thresholds.get_severity(deviation)
        if not severity:
            return None

        return Alert(
            alert_type=AlertType.FALLBACK_SPIKE,
            severity=severity,
            metric_name="fallback_rate",
            current_value=current.fallback_rate,
            baseline_value=baseline.fallback_rate,
            deviation_ratio=deviation,
            threshold_config=self.thresholds,
            metric_date=current.metric_date,
            comparison_window_days=baseline.window_days,
            context={
                "absolute_increase": round(current.fallback_rate - baseline.fallback_rate, 4),
                "current_percentage": round(current.fallback_rate * 100, 2),
                "baseline_percentage": round(baseline.fallback_rate * 100, 2),
            }
        )

    def detect_error_spike(
        self,
        current: MetricSnapshot,
        baseline: BaselineSnapshot
    ) -> Optional[Alert]:
        """Detect error rate spike."""
        if baseline.error_rate == 0:
            if current.error_rate > 0.01:
                deviation = float('inf')
            else:
                return None
        else:
            deviation = self.calculate_deviation(current.error_rate, baseline.error_rate)

        severity = self.thresholds.get_severity(deviation)
        if not severity:
            return None

        return Alert(
            alert_type=AlertType.ERROR_SPIKE,
            severity=severity,
            metric_name="error_rate",
            current_value=current.error_rate,
            baseline_value=baseline.error_rate,
            deviation_ratio=deviation,
            threshold_config=self.thresholds,
            metric_date=current.metric_date,
            comparison_window_days=baseline.window_days,
            context={
                "absolute_increase": round(current.error_rate - baseline.error_rate, 4),
            }
        )

    def detect_latency_spike(
        self,
        current: MetricSnapshot,
        baseline: BaselineSnapshot
    ) -> Optional[Alert]:
        """Detect latency spike (p95)."""
        if baseline.latency_p95 == 0:
            return None

        deviation = self.calculate_deviation(current.latency_p95, baseline.latency_p95)
        severity = self.thresholds.get_severity(deviation)
        if not severity:
            return None

        return Alert(
            alert_type=AlertType.LATENCY_SPIKE,
            severity=severity,
            metric_name="latency_p95",
            current_value=current.latency_p95,
            baseline_value=baseline.latency_p95,
            deviation_ratio=deviation,
            threshold_config=self.thresholds,
            metric_date=current.metric_date,
            comparison_window_days=baseline.window_days,
            context={
                "absolute_increase_ms": round(current.latency_p95 - baseline.latency_p95, 2),
                "current_p50": current.latency_p50,
                "current_p99": current.latency_p99,
            }
        )

    def detect_duplicate_spike(
        self,
        current: MetricSnapshot,
        baseline: BaselineSnapshot
    ) -> Optional[Alert]:
        """Detect duplicate/retry rate spike."""
        if baseline.duplicate_rate == 0:
            if current.duplicate_rate > 0.05:
                deviation = float('inf')
            else:
                return None
        else:
            deviation = self.calculate_deviation(current.duplicate_rate, baseline.duplicate_rate)

        severity = self.thresholds.get_severity(deviation)
        if not severity:
            return None

        return Alert(
            alert_type=AlertType.DUPLICATE_SPIKE,
            severity=severity,
            metric_name="duplicate_rate",
            current_value=current.duplicate_rate,
            baseline_value=baseline.duplicate_rate,
            deviation_ratio=deviation,
            threshold_config=self.thresholds,
            metric_date=current.metric_date,
            comparison_window_days=baseline.window_days,
            context={
                "absolute_increase": round(current.duplicate_rate - baseline.duplicate_rate, 4),
            }
        )

    def detect_health_decline(
        self,
        current: MetricSnapshot,
        baseline: BaselineSnapshot
    ) -> Optional[Alert]:
        """Detect significant health score decline."""
        # Health score decline is inverse (lower = worse)
        if current.health_score >= 80:
            return None

        # If health dropped below 50, that's critical
        if current.health_score < 50:
            return Alert(
                alert_type=AlertType.HEALTH_DECLINE,
                severity=AlertSeverity.CRITICAL,
                metric_name="health_score",
                current_value=current.health_score,
                baseline_value=100.0,  # Ideal baseline
                deviation_ratio=round((100 - current.health_score) / 100, 4),
                threshold_config=self.thresholds,
                metric_date=current.metric_date,
                comparison_window_days=baseline.window_days,
                context={
                    "health_category": "critical" if current.health_score < 50 else "warning" if current.health_score < 70 else "good",
                }
            )

        return None

    async def detect_all_drifts(self, date: Optional[str] = None) -> List[Alert]:
        """Run all drift detection algorithms and return alerts."""
        current = await self.get_current_metrics(date)
        if not current:
            logger.warning("No current metrics available for drift detection")
            return []

        baseline = await self.get_baseline()
        if not baseline:
            logger.warning("No baseline available for drift detection")
            return []

        alerts = []

        # Run all detectors
        fallback_alert = self.detect_fallback_spike(current, baseline)
        if fallback_alert:
            alerts.append(fallback_alert)

        error_alert = self.detect_error_spike(current, baseline)
        if error_alert:
            alerts.append(error_alert)

        latency_alert = self.detect_latency_spike(current, baseline)
        if latency_alert:
            alerts.append(latency_alert)

        duplicate_alert = self.detect_duplicate_spike(current, baseline)
        if duplicate_alert:
            alerts.append(duplicate_alert)

        health_alert = self.detect_health_decline(current, baseline)
        if health_alert:
            alerts.append(health_alert)

        return alerts

    async def save_alert(self, alert: Alert) -> Optional[str]:
        """Save alert to monitoring_alerts table."""
        payload = {
            "alert_type": alert.alert_type.value,
            "severity": alert.severity.value,
            "metric_name": alert.metric_name,
            "current_value": alert.current_value,
            "baseline_value": alert.baseline_value,
            "deviation_ratio": alert.deviation_ratio,
            "threshold_low": alert.threshold_config.low,
            "threshold_medium": alert.threshold_config.medium,
            "threshold_high": alert.threshold_config.high,
            "metric_date": alert.metric_date,
            "comparison_window_days": alert.comparison_window_days,
            "affected_model": alert.affected_model,
            "affected_backend": alert.affected_backend,
            "affected_agent": alert.affected_agent,
            "context_data": alert.context,
            "status": "open",
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self.supabase_url}/rest/v1/monitoring_alerts",
                headers={
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                    "Content-Type": "application/json",
                    "Prefer": "return=representation",
                },
                json=payload
            )

        if response.status_code not in (200, 201):
            logger.error(f"Failed to save alert: {response.status_code} {response.text}")
            return None

        data = response.json()
        if data and len(data) > 0:
            return data[0].get("id")
        return None

    async def check_and_alert(
        self,
        date: Optional[str] = None,
        auto_save: bool = True
    ) -> Dict[str, Any]:
        """
        Main entry point: Check for drifts and optionally save alerts.

        Returns:
            Dict with alert counts and details.
        """
        alerts = await self.detect_all_drifts(date)

        result = {
            "metric_date": date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "alerts_detected": len(alerts),
            "alerts_by_severity": {},
            "alerts_by_type": {},
            "alerts": [],
        }

        for alert in alerts:
            severity = alert.severity.value
            alert_type = alert.alert_type.value

            result["alerts_by_severity"][severity] = result["alerts_by_severity"].get(severity, 0) + 1
            result["alerts_by_type"][alert_type] = result["alerts_by_type"].get(alert_type, 0) + 1

            alert_dict = {
                "type": alert_type,
                "severity": severity,
                "metric": alert.metric_name,
                "current": alert.current_value,
                "baseline": alert.baseline_value,
                "deviation": alert.deviation_ratio,
                "context": alert.context,
            }
            result["alerts"].append(alert_dict)

            if auto_save:
                alert_id = await self.save_alert(alert)
                if alert_id:
                    alert_dict["alert_id"] = alert_id
                    alert_dict["saved"] = True
                else:
                    alert_dict["saved"] = False

        return result


class MonitoringSummary:
    """
    Generate monitoring summaries for dashboards and reports.
    """

    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key

    async def get_summary(
        self,
        window_days: int = 7,
        include_hourly: bool = False
    ) -> Dict[str, Any]:
        """
        Get monitoring summary for the specified window.

        Args:
            window_days: Number of days to include in summary
            include_hourly: Whether to include hourly breakdown

        Returns:
            Dict with metrics, trends, and alerts summary.
        """
        start_date = (datetime.now(timezone.utc) - timedelta(days=window_days)).strftime("%Y-%m-%d")
        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Fetch daily metrics
            metrics_response = await client.get(
                f"{self.supabase_url}/rest/v1/mv_daily_metrics",
                headers={
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                },
                params={
                    "metric_date": f"gte.{start_date}",
                    "order": "metric_date.desc",
                }
            )

            # Fetch alerts
            alerts_response = await client.get(
                f"{self.supabase_url}/rest/v1/monitoring_alerts",
                headers={
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                },
                params={
                    "metric_date": f"gte.{start_date}",
                    "order": "created_at.desc",
                }
            )

            # Fetch baseline
            baseline_response = await client.get(
                f"{self.supabase_url}/rest/v1/monitoring_baseline",
                headers={
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                },
                params={"baseline_name": "eq.7day_rolling"}
            )

        metrics = metrics_response.json() if metrics_response.status_code == 200 else []
        alerts = alerts_response.json() if alerts_response.status_code == 200 else []
        baseline = baseline_response.json() if baseline_response.status_code == 200 else []
        baseline_data = baseline[0] if baseline else {}

        # Calculate summary stats
        total_events = sum(m.get("total_events", 0) for m in metrics)
        avg_fallback_rate = sum(m.get("fallback_rate", 0) for m in metrics) / max(len(metrics), 1)
        avg_error_rate = sum(m.get("error_rate", 0) for m in metrics) / max(len(metrics), 1)
        avg_health_score = sum(m.get("health_score", 0) for m in metrics) / max(len(metrics), 1)

        # Alert summary
        open_alerts = [a for a in alerts if a.get("status") == "open"]
        alerts_by_severity = {}
        for alert in open_alerts:
            severity = alert.get("severity", "unknown")
            alerts_by_severity[severity] = alerts_by_severity.get(severity, 0) + 1

        # Trend calculation (compare last 3 days to previous 3)
        if len(metrics) >= 6:
            recent = metrics[:3]
            previous = metrics[3:6]

            recent_fallback = sum(m.get("fallback_rate", 0) for m in recent) / 3
            previous_fallback = sum(m.get("fallback_rate", 0) for m in previous) / 3
            fallback_trend = "up" if recent_fallback > previous_fallback * 1.1 else "down" if recent_fallback < previous_fallback * 0.9 else "stable"

            recent_latency = sum(m.get("latency_p95", 0) or 0 for m in recent) / 3
            previous_latency = sum(m.get("latency_p95", 0) or 0 for m in previous) / 3
            latency_trend = "up" if recent_latency > previous_latency * 1.1 else "down" if recent_latency < previous_latency * 0.9 else "stable"
        else:
            fallback_trend = "unknown"
            latency_trend = "unknown"

        return {
            "window": {
                "start_date": start_date,
                "end_date": end_date,
                "days": len(metrics),
            },
            "metrics": {
                "total_events": total_events,
                "avg_fallback_rate": round(avg_fallback_rate, 4),
                "avg_error_rate": round(avg_error_rate, 4),
                "avg_health_score": round(avg_health_score, 2),
                "latest": metrics[0] if metrics else None,
            },
            "baseline": {
                "fallback_rate": baseline_data.get("baseline_fallback_rate"),
                "error_rate": baseline_data.get("baseline_error_rate"),
                "latency_p95": baseline_data.get("baseline_latency_p95"),
                "valid_until": baseline_data.get("valid_until"),
            },
            "trends": {
                "fallback_rate": fallback_trend,
                "latency_p95": latency_trend,
            },
            "alerts": {
                "total_open": len(open_alerts),
                "by_severity": alerts_by_severity,
                "recent": alerts[:5] if alerts else [],
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def get_alerts(
        self,
        threshold: str = "medium",
        status: str = "open",
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get alerts filtered by threshold/severity.

        Args:
            threshold: Minimum severity level (low, medium, high, critical)
            status: Alert status filter (open, acknowledged, resolved, ignored)
            limit: Maximum number of alerts to return

        Returns:
            List of alert dictionaries.
        """
        severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        min_severity_level = severity_order.get(threshold, 1)

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.supabase_url}/rest/v1/monitoring_alerts",
                headers={
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                },
                params={
                    "status": f"eq.{status}",
                    "order": "created_at.desc",
                    "limit": limit * 2,  # Fetch extra for filtering
                }
            )

        if response.status_code != 200:
            logger.error(f"Failed to fetch alerts: {response.status_code}")
            return []

        all_alerts = response.json()

        # Filter by severity threshold
        filtered = []
        for alert in all_alerts:
            alert_severity = alert.get("severity", "low")
            if severity_order.get(alert_severity, 0) >= min_severity_level:
                filtered.append(alert)
                if len(filtered) >= limit:
                    break

        return filtered


def create_detector(supabase_url: str, supabase_key: str) -> DriftDetector:
    """Factory function to create a DriftDetector."""
    return DriftDetector(supabase_url, supabase_key)


def create_summary(supabase_url: str, supabase_key: str) -> MonitoringSummary:
    """Factory function to create a MonitoringSummary."""
    return MonitoringSummary(supabase_url, supabase_key)
