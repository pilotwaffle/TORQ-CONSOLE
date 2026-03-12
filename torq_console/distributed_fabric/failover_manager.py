"""
TORQ Layer 11 - Failover Manager

L11-M1: Maintains system resilience through automatic failover.

The FailoverManager provides:
- Node health monitoring
- Automatic workload rerouting
- Graceful failure recovery
- Failover event tracking

All failover operations respect Pre-Fabric Boundary Hardening (PRD-011-PRE):
- Operational state is protected during migration
- Audit trails track all failover events
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict

from pydantic import BaseModel

from .models import (
    NodeInfo,
    NodeStatus,
    NodeHealthMetrics,
    FailoverTriggerType,
    FailoverEvent,
    FailoverConfig,
)
from .node_registry_service import get_node_registry_service
from .capability_router import get_capability_router, RoutingRequest, RoutingCapability


logger = logging.getLogger(__name__)


# ============================================================================
# Failover Storage
# ============================================================================

class FailoverStorage:
    """Storage for failover events and configuration."""

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize failover storage."""
        self.storage_path = storage_path or Path.cwd() / "data" / "failover"
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Subdirectories
        (self.storage_path / "events").mkdir(exist_ok=True)
        (self.storage_path / "config").mkdir(exist_ok=True)

        # In-memory cache
        self._events: List[FailoverEvent] = []
        self._config: Optional[FailoverConfig] = None

        # Load existing data
        self._load_events()
        self._load_config()

    def _load_events(self) -> None:
        """Load existing failover events."""
        for event_file in self.storage_path.glob("events/*.json"):
            try:
                data = json.loads(event_file.read_text())
                event = FailoverEvent(**data)
                self._events.append(event)
            except Exception as e:
                logger.debug(f"Error loading event from {event_file}: {e}")

        # Sort by triggered_at
        self._events.sort(key=lambda e: e.triggered_at, reverse=True)

    def _load_config(self) -> None:
        """Load failover configuration."""
        config_file = self.storage_path / "config" / "failover_config.json"
        if config_file.exists():
            try:
                data = json.loads(config_file.read_text())
                self._config = FailoverConfig(**data)
            except Exception as e:
                logger.debug(f"Error loading config: {e}")

    def save_event(self, event: FailoverEvent) -> None:
        """Save a failover event."""
        event_path = (
            self.storage_path / "events" /
            f"{event.event_id}.json"
        )
        event_path.write_text(event.model_dump_json(indent=2))
        self._events.append(event)

    def save_config(self, config: FailoverConfig) -> None:
        """Save failover configuration."""
        config_file = self.storage_path / "config" / "failover_config.json"
        config_file.write_text(config.model_dump_json(indent=2))
        self._config = config


# ============================================================================
# Failover Manager
# ============================================================================

class FailoverManager:
    """
    Maintains system resilience through automatic failover.

    Responsibilities:
    - Monitor node health and trigger failover when needed
    - Select appropriate failover targets
    - Coordinate workload migration
    - Track failover events for audit
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize the failover manager."""
        self._storage = FailoverStorage(storage_path)
        self._registry = get_node_registry_service()
        self._router = get_capability_router()

        # Configuration
        self._config = self._storage._config or FailoverConfig()

        # Active failovers (track in-progress migrations)
        self._active_failovers: Dict[UUID, FailoverEvent] = {}

        # Monitoring task
        self._monitoring_task: Optional[asyncio.Task] = None

    # ========================================================================
    # Configuration
    # ========================================================================

    def get_config(self) -> FailoverConfig:
        """Get current failover configuration."""
        return self._config

    async def update_config(self, config: FailoverConfig) -> FailoverConfig:
        """Update failover configuration."""
        self._config = config
        self._storage.save_config(config)

        # Restart monitoring if enabled
        if config.auto_failover_enabled and self._monitoring_task is None:
            await self.start_monitoring()

        logger.info("[FailoverManager] Updated failover configuration")

        return config

    # ========================================================================
    # Health Monitoring
    # ========================================================================

    async def start_monitoring(self) -> None:
        """Start health monitoring for all nodes."""
        if self._monitoring_task is not None:
            return

        self._monitoring_task = asyncio.create_task(self._monitor_loop())

        logger.info("[FailoverManager] Started health monitoring")

    async def stop_monitoring(self) -> None:
        """Stop health monitoring."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            self._monitoring_task = None

        logger.info("[FailoverManager] Stopped health monitoring")

    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while True:
            try:
                await self._check_node_health()
                await asyncio.sleep(self._config.heartbeat_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[FailoverManager] Error in monitor loop: {e}")
                await asyncio.sleep(5)

    async def _check_node_health(self) -> None:
        """Check health of all nodes and trigger failover if needed."""
        if not self._config.auto_failover_enabled:
            return

        nodes = self._registry.list_nodes()

        for node in nodes:
            # Check if node needs failover
            trigger = await self._evaluate_failover_trigger(node)

            if trigger:
                await self._initiate_failover(node, trigger)

    async def _evaluate_failover_trigger(
        self,
        node: NodeInfo,
    ) -> Optional[FailoverTriggerType]:
        """Evaluate if a node needs failover."""
        # Skip if already in maintenance or terminated
        if node.health.status in (NodeStatus.MAINTENANCE, NodeStatus.TERMINATED):
            return None

        # Check health score
        if node.health.health_score < self._config.health_score_threshold:
            return FailoverTriggerType.NODE_UNHEALTHY

        # Check error rate
        if node.health.error_rate > self._config.error_rate_threshold:
            return FailoverTriggerType.HIGH_ERROR_RATE

        # Check latency
        if node.health.avg_response_time_ms > self._config.latency_threshold_ms:
            return FailoverTriggerType.HIGH_LATENCY

        return None

    # ========================================================================
    # Failover Execution
    # ========================================================================

    async def _initiate_failover(
        self,
        failing_node: NodeInfo,
        trigger: FailoverTriggerType,
    ) -> Optional[FailoverEvent]:
        """Initiate failover for a failing node."""
        # Check for active failover
        if failing_node.node_id in self._active_failovers:
            return None

        # Check concurrent failover limit
        if len(self._active_failovers) >= self._config.max_concurrent_failovers:
            logger.warning(
                f"[FailoverManager] Max concurrent failovers reached, "
                f"skipping {failing_node.identity.node_name}"
            )
            return None

        # Select failover target
        target_node = await self._select_failover_target(failing_node)

        if not target_node:
            logger.error(
                f"[FailoverManager] No failover target available for "
                f"{failing_node.identity.node_name}"
            )
            return None

        # Create failover event
        event = FailoverEvent(
            trigger_type=trigger,
            primary_node_id=failing_node.node_id,
            failover_node_id=target_node.node_id,
            trigger_reason=f"Node {failing_node.identity.node_name} triggered {trigger.value}",
        )

        self._active_failovers[failing_node.node_id] = event

        logger.info(
            f"[FailoverManager] Initiating failover from "
            f"{failing_node.identity.node_name} to "
            f"{target_node.identity.node_name}"
        )

        # Execute failover
        await self._execute_failover(event, failing_node, target_node)

        return event

    async def _select_failover_target(
        self,
        failing_node: NodeInfo,
    ) -> Optional[NodeInfo]:
        """Select the best target for failover."""
        # Get healthy nodes
        candidates = self._registry.get_healthy_nodes()

        # Filter out the failing node itself
        candidates = [n for n in candidates if n.node_id != failing_node.node_id]

        # Filter by constraints
        if self._config.require_same_region:
            candidates = [
                n for n in candidates
                if n.identity.region == failing_node.identity.region
            ]

        if self._config.require_same_tier:
            candidates = [
                n for n in candidates
                if n.identity.node_tier == failing_node.identity.node_tier
            ]

        # Filter by capacity
        candidates = [n for n in candidates if n.can_accept_workload]

        if not candidates:
            return None

        # Sort by health score and capacity
        candidates.sort(
            key=lambda n: (n.health.health_score, sum(
                cap.max_concurrent_workloads - cap.current_workload_count
                for cap in n.capabilities
            )),
            reverse=True,
        )

        return candidates[0]

    async def _execute_failover(
        self,
        event: FailoverEvent,
        primary_node: NodeInfo,
        failover_node: NodeInfo,
    ) -> None:
        """Execute the failover process."""
        start_time = datetime.now()

        try:
            # Update node status
            primary_node.health.status = NodeStatus.UNHEALTHY

            # Simulate workload migration
            # In a real implementation, this would:
            # 1. Pause new workloads to primary
            # 2. Migrate active workloads to failover node
            # 3. Update routing tables
            # 4. Resume workloads on failover node

            migrated = 0
            failed = 0

            # For each capability, migrate workloads
            for cap in primary_node.capabilities:
                if cap.current_workload_count > 0:
                    # Find matching capability on failover node
                    failover_cap = failover_node.get_capability(cap.capability_name)
                    if failover_cap and failover_cap.current_workload_count < failover_cap.max_concurrent_workloads:
                        # Migrate workload
                        workload_count = min(
                            cap.current_workload_count,
                            failover_cap.max_concurrent_workloads - failover_cap.current_workload_count
                        )
                        failover_cap.current_workload_count += workload_count
                        cap.current_workload_count -= workload_count
                        migrated += workload_count

                        event.affected_workloads.append(uuid4())  # Placeholder for actual workload IDs
                    else:
                        failed += cap.current_workload_count

            event.migrated_workloads = migrated
            event.failed_migrations = failed
            event.success = failed == 0

            # Record completion
            event.completed_at = datetime.now()
            event.duration_seconds = (event.completed_at - start_time).total_seconds()

            if event.success:
                event.recovery_steps.append("Successfully migrated all workloads")
                primary_node.health.status = NodeStatus.MAINTENANCE
            else:
                event.recovery_steps.append(f"Partial migration: {failed} workloads failed")
                event.remaining_issues.append(f"{failed} workloads could not be migrated")

            # Save event
            self._storage.save_event(event)

            logger.info(
                f"[FailoverManager] Failover completed: "
                f"{migrated} migrated, {failed} failed in {event.duration_seconds:.2f}s"
            )

        except Exception as e:
            event.success = False
            event.remaining_issues.append(str(e))
            event.completed_at = datetime.now()
            event.duration_seconds = (event.completed_at - start_time).total_seconds()

            self._storage.save_event(event)

            logger.error(f"[FailoverManager] Failover failed: {e}")

        finally:
            # Remove from active failovers
            self._active_failovers.pop(primary_node.node_id, None)

    # ========================================================================
    # Manual Failover
    # ========================================================================

    async def initiate_manual_failover(
        self,
        primary_node_id: UUID,
        reason: str,
    ) -> Optional[FailoverEvent]:
        """Initiate a manual failover."""
        primary_node = self._registry.get_node(primary_node_id)
        if not primary_node:
            logger.error(f"[FailoverManager] Node {primary_node_id} not found")
            return None

        event = await self._initiate_failover(
            primary_node,
            FailoverTriggerType.MANUAL,
        )

        if event:
            event.trigger_reason = reason

        return event

    # ========================================================================
    # Statistics
    # ========================================================================

    def get_failover_statistics(
        self,
        hours: int = 24,
    ) -> Dict[str, Any]:
        """Get failover statistics for a time window."""
        cutoff = datetime.now() - timedelta(hours=hours)

        recent_events = [
            e for e in self._storage._events
            if e.triggered_at >= cutoff
        ]

        successful = [e for e in recent_events if e.success]
        failed = [e for e in recent_events if not e.success]

        durations = [e.duration_seconds for e in successful if e.duration_seconds]

        return {
            "total_failovers": len(recent_events),
            "successful_failovers": len(successful),
            "failed_failovers": len(failed),
            "success_rate": len(successful) / len(recent_events) if recent_events else 1.0,
            "avg_duration_seconds": sum(durations) / len(durations) if durations else 0,
            "active_failovers": len(self._active_failovers),
            "by_trigger_type": self._count_by_trigger(recent_events),
        }

    def _count_by_trigger(self, events: List[FailoverEvent]) -> Dict[str, int]:
        """Count events by trigger type."""
        counts = defaultdict(int)
        for event in events:
            counts[event.trigger_type.value] += 1
        return dict(counts)

    def get_failover_events(
        self,
        limit: int = 50,
        node_id: Optional[UUID] = None,
    ) -> List[FailoverEvent]:
        """Get failover events with optional filtering."""
        events = self._storage._events

        if node_id:
            events = [
                e for e in events
                if e.primary_node_id == node_id or e.failover_node_id == node_id
            ]

        return events[:limit]


# Global failover manager instance
_manager: Optional[FailoverManager] = None


def get_failover_manager(storage_path: Optional[Path] = None) -> FailoverManager:
    """Get the global failover manager instance."""
    global _manager
    if _manager is None:
        _manager = FailoverManager(storage_path)
    return _manager
