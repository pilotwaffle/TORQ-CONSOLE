"""
TORQ Control Plane - System Monitoring

L7-M1: Real-time system metrics and health monitoring.

Aggregates metrics from all TORQ subsystems for the
operational dashboard.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


# ============================================================================
# Metrics Models
# ============================================================================

class SystemMetrics(BaseModel):
    """
    Aggregated system metrics.
    """
    timestamp: datetime = Field(default_factory=datetime.now)

    # Readiness metrics
    total_candidates: int = 0
    ready_candidates: int = 0
    blocked_candidates: int = 0
    watchlist_candidates: int = 0
    regressed_candidates: int = 0
    promotion_rate: float = 0.0

    # Mission metrics
    active_missions: int = 0
    running_agents: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0

    # Pattern metrics
    discovered_patterns: int = 0
    validated_patterns: int = 0
    patterns_in_use: int = 0

    # Insight metrics
    total_insights: int = 0
    approved_insights: int = 0
    pending_insights: int = 0

    # Memory metrics
    governed_memory_items: int = 0
    memory_confidence_score: float = 0.0

    # System health
    health_score: float = 100.0
    active_alerts: int = 0
    critical_alerts: int = 0

    # Performance
    avg_response_time_ms: float = 0.0
    throughput_per_minute: float = 0.0

    class Config:
        use_enum_values = True


class ServiceHealth(BaseModel):
    """
    Health status of a service.
    """
    name: str
    status: str  # healthy, degraded, down
    last_check: datetime
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    uptime_seconds: float = 0.0

    class Config:
        use_enum_values = True


class MetricsSnapshot(BaseModel):
    """
    Snapshot of metrics at a point in time.
    """
    timestamp: datetime
    metrics: SystemMetrics
    service_health: Dict[str, ServiceHealth]


# ============================================================================
# System Monitor
# ============================================================================

class SystemMonitor:
    """
    Monitors system metrics and health.

    Aggregates data from all TORQ subsystems and provides
    real-time metrics for dashboards.
    """

    def __init__(self, update_interval: int = 30):
        """
        Initialize the system monitor.

        Args:
            update_interval: Seconds between metric updates
        """
        self.update_interval = update_interval
        self._current_metrics: SystemMetrics = SystemMetrics()
        self._service_health: Dict[str, ServiceHealth] = {}
        self._metrics_history: List[MetricsSnapshot] = []
        self._running = False
        self._update_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start background metric collection."""
        if self._running:
            return

        self._running = True
        self._update_task = asyncio.create_task(self._update_loop())
        logger.info("[SystemMonitor] Started metric collection")

    async def stop(self):
        """Stop background metric collection."""
        if not self._running:
            return

        self._running = False

        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass

        logger.info("[SystemMonitor] Stopped metric collection")

    async def _update_loop(self):
        """Background update loop."""
        while self._running:
            try:
                await self.update_metrics()
                await asyncio.sleep(self.update_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[SystemMonitor] Update error: {e}")
                await asyncio.sleep(self.update_interval)

    async def update_metrics(self) -> SystemMetrics:
        """
        Update all metrics from subsystems.

        Returns:
            Updated SystemMetrics
        """
        # Update readiness metrics
        await self._update_readiness_metrics()

        # Update mission metrics
        await self._update_mission_metrics()

        # Update pattern metrics
        await self._update_pattern_metrics()

        # Update insight metrics
        await self._update_insight_metrics()

        # Update memory metrics
        await self._update_memory_metrics()

        # Update system health
        await self._update_system_health()

        # Update service health
        await self._update_service_health()

        # Save snapshot
        snapshot = MetricsSnapshot(
            timestamp=datetime.now(),
            metrics=self._current_metrics,
            service_health=self._service_health,
        )
        self._metrics_history.append(snapshot)

        # Limit history
        if len(self._metrics_history) > 1440:  # 24 hours at 30s intervals
            self._metrics_history = self._metrics_history[-1440:]

        return self._current_metrics

    async def _update_readiness_metrics(self):
        """Update metrics from readiness system."""
        try:
            from ...readiness.query_service import get_query_service
            from ...readiness.analytics_service import get_analytics_service

            query_service = get_query_service()
            analytics_service = get_analytics_service()

            # Get counts by state
            all_candidates = query_service.list_candidates()
            self._current_metrics.total_candidates = all_candidates.total_count

            ready = query_service.list_ready_candidates(limit=500)
            self._current_metrics.ready_candidates = ready.total_count

            blocked = query_service.list_blocked_candidates(limit=500)
            self._current_metrics.blocked_candidates = blocked.total_count

            # Get analytics
            metrics = analytics_service.get_metrics()
            self._current_metrics.watchlist_candidates = (
                metrics.state_distribution.get("watchlist", {}).get("count", 0)
                if isinstance(metrics.state_distribution, dict)
                else sum(s.count for s in metrics.state_distribution if s.state == "watchlist")
            )
            self._current_metrics.regressed_candidates = metrics.regressed_count
            self._current_metrics.promotion_rate = metrics.promotion_rate

        except ImportError:
            logger.debug("[SystemMonitor] Readiness service not available")
        except Exception as e:
            logger.warning(f"[SystemMonitor] Readiness metrics error: {e}")

    async def _update_mission_metrics(self):
        """Update metrics from mission system."""
        try:
            # Placeholder - would integrate with mission system
            pass
        except Exception as e:
            logger.warning(f"[SystemMonitor] Mission metrics error: {e}")

    async def _update_pattern_metrics(self):
        """Update metrics from pattern intelligence."""
        try:
            # Placeholder - would integrate with pattern system
            pass
        except Exception as e:
            logger.warning(f"[SystemMonitor] Pattern metrics error: {e}")

    async def _update_insight_metrics(self):
        """Update metrics from insight publishing."""
        try:
            # Placeholder - would integrate with insight system
            pass
        except Exception as e:
            logger.warning(f"[SystemMonitor] Insight metrics error: {e}")

    async def _update_memory_metrics(self):
        """Update metrics from governed memory."""
        try:
            # Placeholder - would integrate with memory system
            pass
        except Exception as e:
            logger.warning(f"[SystemMonitor] Memory metrics error: {e}")

    async def _update_system_health(self):
        """Calculate overall system health score."""
        # Simple health calculation based on subsystems
        health_factors = []

        # Readiness health (ready candidates vs total)
        if self._current_metrics.total_candidates > 0:
            ready_ratio = (
                self._current_metrics.ready_candidates /
                self._current_metrics.total_candidates
            )
            health_factors.append(ready_ratio * 100)

        # Low blocked candidates is good
        if self._current_metrics.total_candidates > 0:
            blocked_penalty = (
                self._current_metrics.blocked_candidates /
                self._current_metrics.total_candidates
            ) * 50
            health_factors.append(max(0, 100 - blocked_penalty))

        # Few critical alerts is good
        if self._current_metrics.critical_alerts == 0:
            health_factors.append(100)
        else:
            health_factors.append(max(0, 100 - self._current_metrics.critical_alerts * 20))

        # Average the factors
        if health_factors:
            self._current_metrics.health_score = sum(health_factors) / len(health_factors)

    async def _update_service_health(self):
        """Update health status of connected services."""
        services = ["readiness", "missions", "patterns", "insights", "memory"]

        for service in services:
            # Check service health
            health = await self._check_service_health(service)
            self._service_health[service] = health

    async def _check_service_health(self, service: str) -> ServiceHealth:
        """
        Check health of a specific service.

        Args:
            service: Service name

        Returns:
            ServiceHealth status
        """
        start = datetime.now()
        status = "healthy"
        error = None

        try:
            if service == "readiness":
                from ...readiness.analytics_service import get_analytics_service
                get_analytics_service()
            elif service == "missions":
                # TODO: Implement mission health check
                pass
            elif service == "patterns":
                # TODO: Implement pattern health check
                pass
            elif service == "insights":
                # TODO: Implement insight health check
                pass
            elif service == "memory":
                # TODO: Implement memory health check
                pass

        except ImportError:
            status = "down"
            error = "Service not available"
        except Exception as e:
            status = "degraded"
            error = str(e)

        response_time = (datetime.now() - start).total_seconds() * 1000

        return ServiceHealth(
            name=service,
            status=status,
            last_check=datetime.now(),
            response_time_ms=response_time,
            error_message=error,
        )

    def get_metrics(self) -> SystemMetrics:
        """
        Get current system metrics.

        Returns:
            Current SystemMetrics
        """
        return self._current_metrics

    def get_service_health(self) -> Dict[str, ServiceHealth]:
        """
        Get health status of all services.

        Returns:
            Dictionary of service health
        """
        return self._service_health

    def get_metrics_history(
        self,
        hours: int = 24,
    ) -> List[MetricsSnapshot]:
        """
        Get historical metrics.

        Args:
            hours: Number of hours of history

        Returns:
            List of metric snapshots
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        return [
            s for s in self._metrics_history
            if s.timestamp >= cutoff
        ]

    def get_aggregated_metrics(
        self,
        period: str = "hour",
    ) -> Dict[str, Any]:
        """
        Get aggregated metrics over a time period.

        Args:
            period: Aggregation period (hour, day, week)

        Returns:
            Aggregated metrics
        """
        history = self.get_metrics_history(hours=24 if period == "hour" else 168)

        if not history:
            return {}

        # Calculate aggregations
        avg_health = sum(s.metrics.health_score for s in history) / len(history)
        max_ready = max(s.metrics.ready_candidates for s in history)
        min_blocked = min(s.metrics.blocked_candidates for s in history)

        return {
            "avg_health_score": avg_health,
            "max_ready_candidates": max_ready,
            "min_blocked_candidates": min_blocked,
            "data_points": len(history),
            "period": period,
        }


# Global system monitor instance
_monitor: Optional[SystemMonitor] = None


def get_system_monitor(update_interval: int = 30) -> SystemMonitor:
    """Get the global system monitor instance."""
    global _monitor
    if _monitor is None:
        _monitor = SystemMonitor(update_interval=update_interval)
    return _monitor
