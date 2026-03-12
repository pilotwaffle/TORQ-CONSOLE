"""
TORQ Layer 11 - Node Registry Service

L11-M1: Maintains global awareness of TORQ nodes in the fabric.

The NodeRegistryService provides:
- Node discovery and registration
- Node health monitoring
- Capability advertisement
- Region and tier metadata

This service is the foundation for all distributed operations.
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
    NodeIdentity,
    NodeHealthMetrics,
    NodeCapability,
    NodeStatus,
    NodeTier,
    NodeRegion,
    NodeType,
    NodeRegistrationRequest,
    NodeRegistrationResponse,
    NodeHeartbeat,
    NodeHeartbeatResponse,
    FabricStatistics,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Node Registry Storage
# ============================================================================

class NodeRegistryStorage:
    """Storage backend for node registry data."""

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize the storage backend."""
        self.storage_path = storage_path or Path.cwd() / "data" / "node_registry"
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # In-memory cache
        self._nodes: Dict[UUID, NodeInfo] = {}
        self._nodes_by_name: Dict[str, UUID] = {}
        self._nodes_by_region: Dict[NodeRegion, Set[UUID]] = defaultdict(set)
        self._nodes_by_tier: Dict[NodeTier, Set[UUID]] = defaultdict(set)
        self._nodes_by_status: Dict[NodeStatus, Set[UUID]] = defaultdict(set)

    def save_node(self, node: NodeInfo) -> None:
        """Save node information to storage."""
        node_path = self.storage_path / f"node_{node.node_id}.json"

        node_data = {
            "identity": node.identity.model_dump(mode='json'),
            "capabilities": [c.model_dump(mode='json') for c in node.capabilities],
            "health": node.health.model_dump(mode='json'),
            "federation_enabled": node.federation_enabled,
            "federation_policies": node.federation_policies,
            "trusted_nodes": [str(n) for n in node.trusted_nodes],
            "trust_score": node.trust_score,
        }

        node_path.write_text(json.dumps(node_data, indent=2))

    def load_node(self, node_id: UUID) -> Optional[NodeInfo]:
        """Load node information from storage."""
        node_path = self.storage_path / f"node_{node_id}.json"

        if not node_path.exists():
            return None

        try:
            data = json.loads(node_path.read_text())

            return NodeInfo(
                identity=NodeIdentity(**data["identity"]),
                capabilities=[NodeCapability(**c) for c in data.get("capabilities", [])],
                health=NodeHealthMetrics(**data.get("health", {})),
                federation_enabled=data.get("federation_enabled", False),
                federation_policies=data.get("federation_policies", []),
                trusted_nodes=[UUID(n) for n in data.get("trusted_nodes", [])],
                trust_score=data.get("trust_score", 1.0),
            )
        except Exception as e:
            logger.error(f"Error loading node {node_id}: {e}")
            return None

    def delete_node(self, node_id: UUID) -> None:
        """Delete node from storage."""
        node_path = self.storage_path / f"node_{node_id}.json"
        if node_path.exists():
            node_path.unlink()


# ============================================================================
# Node Registry Service
# ============================================================================

class NodeRegistryService:
    """
    Maintains global awareness of TORQ nodes in the fabric.

    Responsibilities:
    - Node discovery and registration
    - Node health monitoring
    - Capability advertisement
    - Region and tier metadata
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize the node registry service."""
        self._storage = NodeRegistryStorage(storage_path)

        # In-memory caches
        self._nodes: Dict[UUID, NodeInfo] = {}
        self._nodes_by_name: Dict[str, UUID] = {}
        self._nodes_by_region: Dict[NodeRegion, Set[UUID]] = defaultdict(set)
        self._nodes_by_tier: Dict[NodeTier, Set[UUID]] = defaultdict(set)
        self._nodes_by_status: Dict[NodeStatus, Set[UUID]] = defaultdict(set)

        # Heartbeat tracking
        self._heartbeat_intervals: Dict[UUID, timedelta] = {}
        self._heartbeat_tasks: Dict[UUID, asyncio.Task] = {}

        # Load existing nodes
        self._load_nodes()

    def _load_nodes(self) -> None:
        """Load existing nodes from storage."""
        for node_file in self._storage.storage_path.glob("node_*.json"):
            try:
                node_id = UUID(node_file.stem.replace("node_", ""))
                node = self._storage.load_node(node_id)
                if node:
                    self._add_to_cache(node)
            except Exception as e:
                logger.debug(f"Error loading node from {node_file}: {e}")

    def _add_to_cache(self, node: NodeInfo) -> None:
        """Add node to in-memory cache."""
        self._nodes[node.node_id] = node
        self._nodes_by_name[node.identity.node_name] = node.node_id
        self._nodes_by_region[node.identity.region].add(node.node_id)
        self._nodes_by_tier[node.identity.node_tier].add(node.node_id)
        self._nodes_by_status[node.health.status].add(node.node_id)

    def _remove_from_cache(self, node_id: UUID) -> None:
        """Remove node from in-memory cache."""
        if node_id not in self._nodes:
            return

        node = self._nodes[node_id]

        del self._nodes[node_id]
        if node.identity.node_name in self._nodes_by_name:
            del self._nodes_by_name[node.identity.node_name]

        self._nodes_by_region[node.identity.region].discard(node_id)
        self._nodes_by_tier[node.identity.node_tier].discard(node_id)
        self._nodes_by_status[node.health.status].discard(node_id)

    def _update_status_in_cache(self, node_id: UUID, old_status: NodeStatus, new_status: NodeStatus) -> None:
        """Update node status in cache."""
        self._nodes_by_status[old_status].discard(node_id)
        self._nodes_by_status[new_status].add(node_id)

    async def register_node(
        self,
        request: NodeRegistrationRequest,
        registering_node_id: Optional[UUID] = None,
    ) -> NodeRegistrationResponse:
        """
        Register a new TORQ node in the fabric.

        Args:
            request: Node registration request
            registering_node_id: ID of node performing registration (for auth)

        Returns:
            NodeRegistrationResponse with assigned node ID
        """
        # Check for existing node with same name
        existing_id = self._nodes_by_name.get(request.node_name)
        if existing_id:
            existing_node = self._nodes[existing_id]
            # Update existing node
            await self.update_node_info(existing_id, request)
            return NodeRegistrationResponse(
                success=True,
                node_id=existing_id,
                message="Node re-registered successfully",
                heartbeat_interval_seconds=30,
            )

        # Create new node identity
        node_identity = NodeIdentity(
            node_name=request.node_name,
            node_type=request.node_type,
            node_tier=request.node_tier,
            region=request.region,
            host_address=request.host_address,
            port=request.port,
            organization_id=request.organization_id,
            organization_name=request.organization_name,
            version=request.version,
            labels=request.labels,
            tags=request.tags,
        )

        # Create capabilities from request
        capabilities = []
        for cap_data in request.capabilities:
            capabilities.append(NodeCapability(**cap_data))

        # Create initial health metrics
        health = NodeHealthMetrics(
            node_id=node_identity.node_id,
            status=NodeStatus.STARTING,
            health_score=1.0,
        )

        # Create node info
        node = NodeInfo(
            identity=node_identity,
            capabilities=capabilities,
            health=health,
            federation_enabled=False,  # Requires explicit enable
        )

        # Save to storage
        self._storage.save_node(node)

        # Add to cache
        self._add_to_cache(node)

        # Start heartbeat monitoring
        await self._start_heartbeat_monitoring(node.node_id)

        logger.info(
            f"[NodeRegistry] Registered node: {request.node_name} "
            f"({node_identity.node_id}) in {request.region.value}"
        )

        return NodeRegistrationResponse(
            success=True,
            node_id=node_identity.node_id,
            message="Node registered successfully",
            assigned_fabric_id=str(node_identity.node_id),
            heartbeat_interval_seconds=30,
        )

    async def update_node_info(
        self,
        node_id: UUID,
        request: NodeRegistrationRequest,
    ) -> Optional[NodeInfo]:
        """Update information for an existing node."""
        node = self._nodes.get(node_id)
        if not node:
            return None

        old_status = node.health.status

        # Update identity fields
        node.identity.host_address = request.host_address
        node.identity.port = request.port
        node.identity.organization_id = request.organization_id
        node.identity.organization_name = request.organization_name
        node.identity.version = request.version
        node.identity.labels.update(request.labels)
        node.identity.tags = request.tags

        # Update capabilities
        new_capabilities = []
        for cap_data in request.capabilities:
            new_capabilities.append(NodeCapability(**cap_data))
        node.capabilities = new_capabilities

        # Save
        self._storage.save_node(node)

        # Update status cache if changed
        if node.health.status != old_status:
            self._update_status_in_cache(node_id, old_status, node.health.status)

        return node

    async def process_heartbeat(self, heartbeat: NodeHeartbeat) -> NodeHeartbeatResponse:
        """
        Process a heartbeat from a node.

        Args:
            heartbeat: Heartbeat data from node

        Returns:
            HeartbeatResponse with any commands or updates
        """
        node = self._nodes.get(heartbeat.node_id)
        if not node:
            return NodeHeartbeatResponse(
                acknowledged=False,
                fabric_status={"error": "Node not registered"}
            )

        # Update health metrics
        node.health.last_heartbeat = heartbeat.timestamp
        node.health.status = heartbeat.status
        node.health.health_score = heartbeat.health_score
        node.health.active_workloads = heartbeat.active_workloads
        node.health.avg_response_time_ms = heartbeat.avg_response_time_ms

        # Update issues
        node.health.active_issues = heartbeat.issues

        old_status = node.health.status

        # Determine health status based on heartbeat
        if heartbeat.status == NodeStatus.HEALTHY:
            if heartbeat.health_score < 0.5:
                node.health.status = NodeStatus.DEGRADED
        elif heartbeat.status == NodeStatus.UNHEALTHY:
            # Trigger failover consideration
            pass

        # Update status cache if changed
        if node.health.status != old_status:
            self._update_status_in_cache(heartbeat.node_id, old_status, node.health.status)

        # Save updated health
        self._storage.save_node(node)

        # Check for node transition
        commands = []
        requested_actions = []

        if node.health.status == NodeStatus.UNHEALTHY:
            commands.append("prepare_for_failover")
            requested_actions.append("Reduce workload or prepare for migration")

        # Build fabric status
        fabric_status = {
            "total_nodes": len(self._nodes),
            "healthy_nodes": len(self._nodes_by_status[NodeStatus.HEALTHY]),
            "degraded_nodes": len(self._nodes_by_status[NodeStatus.DEGRADED]),
            "unhealthy_nodes": len(self._nodes_by_status[NodeStatus.UNHEALTHY]),
        }

        return NodeHeartbeatResponse(
            acknowledged=True,
            fabric_status=fabric_status,
            commands=commands,
            requested_actions=requested_actions,
        )

    async def _start_heartbeat_monitoring(self, node_id: UUID) -> None:
        """Start monitoring for missed heartbeats."""
        interval = timedelta(seconds=30)

        async def monitor_heartbeat():
            while node_id in self._nodes:
                try:
                    await asyncio.sleep(interval.total_seconds)
                except asyncio.CancelledError:
                    break

                node = self._nodes.get(node_id)
                if not node:
                    break

                # Check for stale heartbeat
                if node.health.last_heartbeat:
                    time_since = datetime.now() - node.health.last_heartbeat
                    if time_since > timedelta(seconds=90):  # 3 missed heartbeats
                        if node.health.status in (NodeStatus.HEALTHY, NodeStatus.DEGRADED):
                            old_status = node.health.status
                            node.health.status = NodeStatus.UNHEALTHY
                            node.health.active_issues.append("Missed heartbeats")
                            self._update_status_in_cache(node_id, old_status, node.health.status)

                            logger.warning(
                                f"[NodeRegistry] Node {node.identity.node_name} "
                                f"marked unhealthy due to missed heartbeats"
                            )

        task = asyncio.create_task(monitor_heartbeat())
        self._heartbeat_tasks[node_id] = task

    def get_node(self, node_id: UUID) -> Optional[NodeInfo]:
        """Get node information by ID."""
        return self._nodes.get(node_id)

    def get_node_by_name(self, node_name: str) -> Optional[NodeInfo]:
        """Get node information by name."""
        node_id = self._nodes_by_name.get(node_name)
        if node_id:
            return self._nodes.get(node_id)
        return None

    def list_nodes(
        self,
        status: Optional[NodeStatus] = None,
        region: Optional[NodeRegion] = None,
        tier: Optional[NodeTier] = None,
        limit: int = 100,
    ) -> List[NodeInfo]:
        """List nodes with optional filtering."""
        nodes = list(self._nodes.values())

        # Apply filters
        if status:
            nodes = [n for n in nodes if n.health.status == status]
        if region:
            nodes = [n for n in nodes if n.identity.region == region]
        if tier:
            nodes = [n for n in nodes if n.identity.node_tier == tier]

        # Sort by health score
        nodes.sort(key=lambda n: n.health.health_score, reverse=True)

        return nodes[:limit]

    def get_nodes_by_capability(self, capability_name: str) -> List[NodeInfo]:
        """Get nodes that provide a specific capability."""
        return [
            n for n in self._nodes.values()
            if any(c.capability_name == capability_name for c in n.capabilities)
        ]

    def get_healthy_nodes(self) -> List[NodeInfo]:
        """Get all healthy nodes (including starting nodes that can accept workloads)."""
        return [
            n for n in self._nodes.values()
            if n.health.status in (NodeStatus.HEALTHY, NodeStatus.STARTING, NodeStatus.DEGRADED)
        ]

    def get_nodes_in_region(self, region: NodeRegion) -> List[NodeInfo]:
        """Get nodes in a specific region."""
        node_ids = self._nodes_by_region.get(region, set())
        return [self._nodes.get(nid) for nid in node_ids if nid in self._nodes]

    def get_statistics(self) -> FabricStatistics:
        """Get fabric-wide statistics."""
        stats = FabricStatistics()

        stats.total_nodes = len(self._nodes)
        stats.healthy_nodes = len(self._nodes_by_status[NodeStatus.HEALTHY])
        stats.degraded_nodes = len(self._nodes_by_status[NodeStatus.DEGRADED])
        stats.unhealthy_nodes = len(self._nodes_by_status[NodeStatus.UNHEALTHY])

        # By tier
        for tier, node_ids in self._nodes_by_tier.items():
            stats.nodes_by_tier[tier.value] = len(node_ids)

        # By region
        for region, node_ids in self._nodes_by_region.items():
            stats.nodes_by_region[region.value] = len(node_ids)

        # Workload
        for node in self._nodes.values():
            stats.total_workloads += node.health.active_workloads
            for cap in node.capabilities:
                stats.total_capacity += cap.max_concurrent_workloads

        if stats.total_capacity > 0:
            stats.utilization_rate = stats.total_workloads / stats.total_capacity

        return stats

    async def deregister_node(self, node_id: UUID) -> bool:
        """
        Deregister a node from the fabric.

        Args:
            node_id: ID of node to deregister

        Returns:
            True if deregistered successfully
        """
        if node_id not in self._nodes:
            return False

        node = self._nodes[node_id]

        # Stop heartbeat monitoring
        if node_id in self._heartbeat_tasks:
            self._heartbeat_tasks[node_id].cancel()
            del self._heartbeat_tasks[node_id]

        # Remove from cache
        self._remove_from_cache(node_id)

        # Delete from storage
        self._storage.delete_node(node_id)

        logger.info(f"[NodeRegistry] Deregistered node: {node.identity.node_name} ({node_id})")

        return True


# Global node registry service instance
_service: Optional[NodeRegistryService] = None


def get_node_registry_service(storage_path: Optional[Path] = None) -> NodeRegistryService:
    """Get the global node registry service instance."""
    global _service
    if _service is None:
        _service = NodeRegistryService(storage_path)
    return _service
