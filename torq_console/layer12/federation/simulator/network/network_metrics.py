"""
Network Metrics Engine for Federation Simulator

Layer 12 Phase 2B — Multi-Node Federation Scale Validation

Network-scale metrics that extend beyond single-node metrics:
- Network density and connectivity
- Domain competition indices
- Contradiction clustering analysis
- Cross-domain knowledge transfer
- Node survival and churn rates
- Network resilience scoring
"""

import logging
import math
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
from pydantic import BaseModel, Field

from .node_registry import NodeRegistry, SimulatedNetworkNode
from ..models import Domain


logger = logging.getLogger(__name__)


# ============================================================================
# Network Snapshot
# ============================================================================

class NetworkSnapshot(BaseModel):
    """Point-in-time snapshot of network state."""

    snapshot_id: str = Field(..., description="Unique snapshot identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When snapshot was taken")
    epoch: int = Field(..., ge=0, description="Simulation epoch number")

    # Network structure
    total_nodes: int = Field(..., ge=0, description="Total nodes in network")
    active_nodes: int = Field(..., ge=0, description="Active nodes")
    total_edges: int = Field(..., ge=0, description="Total network connections")

    # Network metrics
    network_density: float = Field(..., ge=0.0, le=1.0, description="Edge density (0-1)")
    avg_clustering: float = Field(..., ge=0.0, le=1.0, description="Average clustering coefficient")
    avg_path_length: float = Field(..., ge=0.0, description="Average shortest path length")

    # Domain metrics
    domain_count: int = Field(..., ge=0, description="Number of active domains")
    domain_competition_index: float = Field(
        ...,
        ge=0.0,
        description="Competition between domains (higher = more competitive)"
    )

    # Contradiction metrics
    contradiction_clusters: int = Field(..., ge=0, description="Number of contradiction clusters")
    avg_cluster_size: float = Field(..., ge=0.0, description="Average cluster size")
    fragmentation_index: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Network fragmentation (higher = more fragmented)"
    )

    # Influence metrics
    gini_coefficient: float = Field(..., ge=0.0, le=1.0, description="Inequality in influence")
    herfindahl_index: float = Field(..., ge=0.0, description="Market concentration of influence")
    top_node_concentration: float = Field(..., ge=0.0, le=1.0, description="Top node's influence share")

    # Resilience metrics
    node_survival_rate: float = Field(..., ge=0.0, le=1.0, description="Nodes remaining from initial")
    network_resilience_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall resilience (higher = more resilient)"
    )

    class Config:
        arbitrary_types_allowed = True


# ============================================================================
# Network Metrics Engine
# ============================================================================

class NetworkMetricsEngine:
    """
    Calculates network-scale metrics for federation simulation.

    Extends beyond single-node metrics to capture:
    - Structural network properties
    - Cross-domain interaction patterns
    - Contradiction clustering behavior
    - Long-horizon network evolution
    """

    def __init__(self, node_registry: NodeRegistry):
        """
        Initialize the metrics engine.

        Args:
            node_registry: Registry of network nodes
        """
        self.node_registry = node_registry
        self.logger = logging.getLogger(__name__)

        # Historical tracking
        self._snapshots: List[NetworkSnapshot] = []
        self._node_influence_history: Dict[str, List[float]] = defaultdict(list)

    def capture_snapshot(
        self,
        epoch: int,
        total_nodes: int,
        topology_edges: Set[Tuple[str, str]],
    ) -> NetworkSnapshot:
        """
        Capture a point-in-time snapshot of network state.

        Args:
            epoch: Current simulation epoch
            total_nodes: Total nodes in network
            topology_edges: Set of (node_a, node_b) edges

        Returns:
            NetworkSnapshot with current metrics
        """
        snapshot_id = f"snapshot_epoch_{epoch}_{datetime.utcnow().isoformat()}"

        nodes = self.node_registry.get_all_nodes()
        active_nodes = [n for n in nodes if n.is_active]

        # Calculate network structure metrics
        network_density = self._calculate_density(total_nodes, len(topology_edges))
        avg_clustering = self._calculate_clustering_coefficient(nodes, topology_edges)
        avg_path_length = self._calculate_avg_path_length(nodes, topology_edges)

        # Calculate domain metrics
        domain_metrics = self._calculate_domain_metrics(nodes)
        domain_competition_index = domain_metrics["competition_index"]

        # Calculate contradiction metrics
        contradiction_metrics = self._calculate_contradiction_metrics(nodes)
        contradiction_clusters = contradiction_metrics["cluster_count"]
        avg_cluster_size = contradiction_metrics["avg_cluster_size"]
        fragmentation_index = contradiction_metrics["fragmentation_index"]

        # Calculate influence metrics
        influence_metrics = self._calculate_influence_metrics(nodes)
        gini = influence_metrics["gini"]
        hhi = influence_metrics["hhi"]
        top_concentration = influence_metrics["top_concentration"]

        # Calculate resilience
        resilience_score = self._calculate_resilience(
            network_density,
            avg_clustering,
            fragmentation_index,
            len(active_nodes),
            total_nodes,
        )

        snapshot = NetworkSnapshot(
            snapshot_id=snapshot_id,
            epoch=epoch,
            total_nodes=total_nodes,
            active_nodes=len(active_nodes),
            total_edges=len(topology_edges),
            network_density=network_density,
            avg_clustering=avg_clustering,
            avg_path_length=avg_path_length,
            domain_count=domain_metrics["domain_count"],
            domain_competition_index=domain_competition_index,
            contradiction_clusters=contradiction_clusters,
            avg_cluster_size=avg_cluster_size,
            fragmentation_index=fragmentation_index,
            gini_coefficient=gini,
            herfindahl_index=hhi,
            top_node_concentration=top_concentration,
            node_survival_rate=len(active_nodes) / max(total_nodes, 1),
            network_resilience_score=resilience_score,
        )

        self._snapshots.append(snapshot)

        # Update influence history
        for node in nodes:
            self._node_influence_history[node.node_id].append(node.current_trust)

        self.logger.info(
            f"Captured snapshot epoch_{epoch}: "
            f"density={network_density:.2f}, resilience={resilience_score:.2f}"
        )

        return snapshot

    def _calculate_density(self, num_nodes: int, num_edges: int) -> float:
        """Calculate network edge density."""
        if num_nodes < 2:
            return 0.0
        max_edges = (num_nodes * (num_nodes - 1)) / 2
        return num_edges / max_edges if max_edges > 0 else 0.0

    def _calculate_clustering_coefficient(
        self,
        nodes: List[SimulatedNetworkNode],
        edges: Set[Tuple[str, str]],
    ) -> float:
        """Calculate average clustering coefficient."""
        if not nodes:
            return 0.0

        clustering_scores = []

        for node in nodes:
            neighbors = list(node.network_neighbors.keys())
            k = len(neighbors)

            if k < 2:
                clustering_scores.append(0.0)
                continue

            # Count connections between neighbors
            neighbor_connections = 0
            for i, neighbor_a in enumerate(neighbors):
                for neighbor_b in neighbors[i + 1:]:
                    if (neighbor_a, neighbor_b) in edges or (neighbor_b, neighbor_a) in edges:
                        neighbor_connections += 1

            # Possible connections between k neighbors
            possible = k * (k - 1) / 2
            clustering = neighbor_connections / possible if possible > 0 else 0.0
            clustering_scores.append(clustering)

        return np.mean(clustering_scores) if clustering_scores else 0.0

    def _calculate_avg_path_length(
        self,
        nodes: List[SimulatedNetworkNode],
        edges: Set[Tuple[str, str]],
    ) -> float:
        """Calculate average shortest path length (BFS approximation)."""
        if not nodes:
            return 0.0

        node_ids = [n.node_id for n in nodes]
        if len(node_ids) < 2:
            return 0.0

        # Build adjacency list
        adj = {node_id: set() for node_id in node_ids}
        for a, b in edges:
            if a in adj:
                adj[a].add(b)
            if b in adj:
                adj[b].add(a)

        # Calculate average shortest path
        total_path_length = 0
        path_count = 0

        for start in node_ids[:10]:  # Sample to avoid O(n^3) on large networks
            # BFS
            distances = {start: 0}
            queue = [start]
            visited = {start}

            while queue:
                current = queue.pop(0)
                for neighbor in adj[current]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        distances[neighbor] = distances[current] + 1
                        queue.append(neighbor)

            # Sum distances (excluding start)
            for node_id, dist in distances.items():
                if node_id != start:
                    total_path_length += dist
                    path_count += 1

        return total_path_length / path_count if path_count > 0 else 0.0

    def _calculate_domain_metrics(self, nodes: List[SimulatedNetworkNode]) -> Dict[str, Any]:
        """Calculate domain-level metrics."""
        domain_influence = defaultdict(float)
        domain_representatives = defaultdict(set)  # domain -> node_ids

        for node in nodes:
            for domain_str, influence in node.domain_influence.items():
                domain_influence[domain_str] += influence.influence_score
                domain_representatives[domain_str].add(node.node_id)

        if not domain_influence:
            return {
                "domain_count": 0,
                "competition_index": 0.0,
            }

        # Domain competition index (Herfindahl-style)
        total_influence = sum(domain_influence.values())
        if total_influence == 0:
            return {
                "domain_count": len(domain_influence),
                "competition_index": 0.0,
            }

        # HHI for domains (lower = more competitive, higher = concentrated)
        hhi = sum((share / total_influence) ** 2 for share in domain_influence.values())

        # Convert to competition index (inverse of concentration)
        n_domains = len(domain_influence)
        competition_index = (1 - hhi) * (n_domains / (n_domains - 1)) if n_domains > 1 else 0.0

        return {
            "domain_count": n_domains,
            "competition_index": competition_index,
        }

    def _calculate_contradiction_metrics(self, nodes: List[SimulatedNetworkNode]) -> Dict[str, float]:
        """Calculate contradiction clustering metrics."""
        if not nodes:
            return {
                "cluster_count": 0,
                "avg_cluster_size": 0.0,
                "fragmentation_index": 0.0,
            }

        # Group nodes by domain specialization instead of stance bias
        # (stance_bias is a dict and unhashable, domain clustering is more meaningful)
        domain_groups = defaultdict(set)
        for node in nodes:
            if node.domain_specializations:
                # Use primary domain as clustering key
                primary_domain = node.domain_specializations[0]
                domain_groups[primary_domain].add(node.node_id)
            else:
                domain_groups["general"].add(node.node_id)

        # A "cluster" is a group of nodes in the same domain
        clusters = [group for group in domain_groups.values() if len(group) > 0]
        cluster_sizes = [len(c) for c in clusters]

        if not cluster_sizes:
            return {
                "cluster_count": 0,
                "avg_cluster_size": 0.0,
                "fragmentation_index": 0.0,
            }

        avg_cluster_size = float(np.mean(cluster_sizes))

        # Fragmentation index (higher = more fragmented)
        n_clusters = len(clusters)
        max_cluster_size = max(cluster_sizes)
        # Fragmentation measures how evenly distributed nodes are across clusters
        # Higher = more evenly distributed (more fragmented)
        fragmentation_index = (n_clusters - 1) / (len(nodes) - 1) if len(nodes) > 1 else 0.0

        return {
            "cluster_count": n_clusters,
            "avg_cluster_size": avg_cluster_size,
            "fragmentation_index": fragmentation_index,
        }

    def _calculate_influence_metrics(self, nodes: List[SimulatedNetworkNode]) -> Dict[str, float]:
        """Calculate influence concentration metrics."""
        if not nodes:
            return {"gini": 0.0, "hhi": 0.0, "top_concentration": 0.0}

        # Influence based on trust score
        influences = [node.current_trust for node in nodes]

        # Gini coefficient (normalized to [0, 1])
        sorted_influences = sorted(influences)
        n = len(influences)
        if n == 0:
            return {"gini": 0.0, "hhi": 0.0, "top_concentration": 0.0}

        total = sum(influences)
        if total == 0:
            return {"gini": 0.0, "hhi": 0.0, "top_concentration": 0.0}

        # Standard Gini coefficient formula
        # G = (sum of |x_i - x_j| for all i,j) / (2 * n * sum(x))
        # Simplified: G = 1 - (2 / (n+1)) * (sum of cumulative ranks / total)
        cumsum = 0
        gini_numerator = 0
        for i, value in enumerate(sorted_influences):
            cumsum += value
            # Gini using mean difference formula
            gini_numerator += (2 * (i + 1) - n - 1) * value

        gini = abs(gini_numerator) / (n * total) if n > 0 and total > 0 else 0.0
        gini = max(0.0, min(1.0, gini))  # Clamp to [0, 1]

        # Herfindahl Index
        shares = [inf / total for inf in influences]
        hhi = sum(share ** 2 for share in shares)

        # Top node concentration
        top_concentration = max(influences) / total if total > 0 else 0.0

        return {
            "gini": gini,
            "hhi": hhi,
            "top_concentration": top_concentration,
        }

    def _calculate_resilience(
        self,
        density: float,
        clustering: float,
        fragmentation: float,
        active_nodes: int,
        total_nodes: int,
    ) -> float:
        """
        Calculate overall network resilience score.

        Higher = more resilient.

        Factors:
        - Density: Well-connected networks are more resilient
        - Clustering: Clusters provide redundancy
        - Fragmentation: Fragmented networks are less resilient (inverse)
        - Node survival: More active nodes = more resilient
        """
        # Weighted components
        density_score = density  # 0-1
        clustering_score = clustering  # 0-1
        survival_score = active_nodes / max(total_nodes, 1)  # 0-1
        fragmentation_penalty = fragmentation  # 0-1, higher is worse

        # Resilience = connectivity + redundancy - fragmentation
        resilience = (
            0.3 * density_score +
            0.3 * clustering_score +
            0.3 * survival_score -
            0.1 * fragmentation_penalty
        )

        return max(0.0, min(1.0, resilience))

    def get_snapshot_history(self, last_n: Optional[int] = None) -> List[NetworkSnapshot]:
        """Get historical snapshots."""
        if last_n:
            return self._snapshots[-last_n:]
        return self._snapshots.copy()

    def get_network_evolution_trend(self, metric_name: str) -> List[float]:
        """
        Get the trend of a metric over time.

        Args:
            metric_name: Name of metric to track

        Returns:
            List of metric values over time
        """
        values = []
        for snapshot in self._snapshots:
            if hasattr(snapshot, metric_name):
                values.append(getattr(snapshot, metric_name))
        return values

    def get_statistics(self) -> Dict[str, Any]:
        """Get metrics engine statistics."""
        return {
            "total_snapshots": len(self._snapshots),
            "tracked_nodes": len(self._node_influence_history),
            "avg_history_length": (
                sum(len(h) for h in self._node_influence_history.values()) /
                max(len(self._node_influence_history), 1)
            ),
        }


def create_network_metrics_engine(node_registry: NodeRegistry) -> NetworkMetricsEngine:
    """Factory function to create a NetworkMetricsEngine."""
    return NetworkMetricsEngine(node_registry=node_registry)
