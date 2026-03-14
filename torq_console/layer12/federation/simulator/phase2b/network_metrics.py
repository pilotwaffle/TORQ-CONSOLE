"""
Network-Scale Metrics for Multi-Node Federation Analysis

Layer 12 Phase 2B — Multi-Node Federation Scale Validation

Calculates network-level metrics including centrality, clustering,
influence distribution, and collapse risk indicators.
"""

import logging
import math
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

from .node_registry import FederatedNode, NodeRegistry
from .network_controller import NetworkController


logger = logging.getLogger(__name__)


@dataclass
class CentralityMetrics:
    """Centrality measures for network analysis.

    All values are normalized to [0, 1].
    """

    degree_centrality: Dict[str, float]  # Node connection importance
    betweenness_centrality: Dict[str, float]  # Node bridge importance
    eigenvector_centrality: Dict[str, float]  # Node influence importance
    pagerank: Dict[str, float]  # PageRank scores

    def get_top_nodes(self, metric: str = "degree_centrality", top_n: int = 5) -> List[Tuple[str, float]]:
        """Get top N nodes by a centrality metric."""
        values = getattr(self, metric, {})
        sorted_nodes = sorted(values.items(), key=lambda x: x[1], reverse=True)
        return sorted_nodes[:top_n]

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        all_metrics = [
            self.degree_centrality,
            self.betweenness_centrality,
            self.eigenvector_centrality,
            self.pagerank,
        ]

        summaries = {}
        for name, values in zip(
            ["degree", "betweenness", "eigenvector", "pagerank"],
            all_metrics
        ):
            if values:
                vals = list(values.values())
                summaries[name] = {
                    "mean": np.mean(vals),
                    "std": np.std(vals),
                    "min": np.min(vals),
                    "max": np.max(vals),
                    "median": np.median(vals),
                }

        return summaries


@dataclass
class NetworkHealthMetrics:
    """Network-level health indicators."""

    density: float  # Connection density (0-1)
    clustering: float  # Clustering coefficient (0-1)
    avg_path_length: float  # Average shortest path
    diameter: int  # Longest shortest path
    connected_components: int  # Network fragmentation count
    largest_component_size: int  # Nodes in largest component
    fragmentation_ratio: float  # Ratio of nodes not in largest component

    def get_health_score(self) -> float:
        """Calculate overall health score (0-1)."""
        # Density score (prefer moderate density: 0.2-0.6 is ideal)
        density_score = 1.0 - abs(self.density - 0.4) / 0.4

        # Clustering score (higher is generally better for small-world networks)
        clustering_score = min(1.0, self.clustering * 2)

        # Connectivity score
        connectivity_score = 1.0 if self.connected_components == 1 else 0.5 / self.connected_components

        # Fragmentation score (lower is better)
        fragmentation_score = 1.0 - self.fragmentation_ratio

        # Weighted average
        return (
            0.2 * density_score +
            0.2 * clustering_score +
            0.3 * connectivity_score +
            0.3 * fragmentation_score
        )


@dataclass
class InfluenceDistribution:
    """Inequality metrics for influence distribution."""

    gini_coefficient: float  # 0 = equal, 1 = maximal inequality
    herfindahl_index: float  # Market concentration (0-1)
    top_1_share: float  # Top node's share (0-1)
    top_5_share: float  # Top 5 nodes' share (0-1)
    top_10_share: float  # Top 10 nodes' share (0-1)
    lorenz_curve: List[Tuple[float, float]]  # Cumulative share curve

    def get_inequality_level(self) -> str:
        """Get inequality classification."""
        if self.gini_coefficient < 0.2:
            return "very_equal"
        elif self.gini_coefficient < 0.4:
            return "moderately_equal"
        elif self.gini_coefficient < 0.6:
            return "unequal"
        else:
            return "highly_unequal"


@dataclass
class NetworkCollapseIndicators:
    """Leading indicators of network collapse."""

    fragmentation_acceleration: float  # Rate of component splitting
    centrality_concentration: float  # Power centralizing in few nodes
    bridge_failure_rate: float  # Critical edges failing
    information_bottleneck_score: float  # Flow concentration
    cascade_risk: float  # Cascading failure probability
    dominance_alert: bool  # Single node dominance detected
    minority_suppression: float  # Minority viewpoint suppression score

    def get_collapse_risk(self) -> str:
        """Get collapse risk level."""
        # Weighted risk score
        risk = (
            0.2 * self.fragmentation_acceleration +
            0.2 * self.centrality_concentration +
            0.15 * self.bridge_failure_rate +
            0.15 * self.information_bottleneck_score +
            0.2 * self.cascade_risk +
            0.1 * self.minority_suppression
        )

        if risk < 0.2:
            return "low"
        elif risk < 0.4:
            return "moderate"
        elif risk < 0.6:
            return "elevated"
        else:
            return "high"


@dataclass
class NetworkFlowMetrics:
    """Metrics related to information flow through the network."""

    avg_flow_distance: float  # Average path length for successful flows
    flow_success_rate: float  # Fraction of flows that reach destination
    bottlenecks: List[str]  # Nodes that are flow bottlenecks
    isolated_nodes: List[str]  # Nodes that can't reach others
    propagation_speed: float  # Average hops per time unit


class NetworkMetricsCalculator:
    """Calculate network-scale metrics."""

    def __init__(self, controller: NetworkController, registry: NodeRegistry):
        self.controller = controller
        self.registry = registry
        self.logger = logging.getLogger(__name__)

        # Cache for expensive calculations
        self._centrality_cache: Optional[CentralityMetrics] = None
        self._cache_topology_id: Optional[str] = None

    def _invalidate_cache(self):
        """Invalidate cached metrics."""
        self._centrality_cache = None
        self._cache_topology_id = None

    def calculate_all(self) -> Dict[str, Any]:
        """Calculate all network metrics."""
        self._invalidate_cache()

        return {
            "centrality": self.calculate_centrality(),
            "health": self.calculate_network_health(),
            "influence_distribution": self.calculate_influence_distribution(),
            "collapse_indicators": self.calculate_collapse_indicators(),
            "flow": self.calculate_flow_metrics(),
        }

    def calculate_centrality(self) -> CentralityMetrics:
        """Calculate all centrality measures."""
        if self.controller.topology is None:
            return CentralityMetrics({}, {}, {}, {})

        # Check cache
        if self._cache_topology_id == self.controller.topology.topology_id:
            return self._centrality_cache

        topology = self.controller.topology
        nodes = list(topology.adjacency_list.keys())
        n = len(nodes)

        if n == 0:
            return CentralityMetrics({}, {}, {}, {})

        # Degree centrality
        degree_cent = {}
        max_degree = n - 1
        for node in nodes:
            degree = topology.get_degree(node)
            degree_cent[node] = degree / max_degree if max_degree > 0 else 0

        # Betweenness centrality (using approximation for performance)
        betweenness_cent = self._calculate_betweenness_approx(topology, nodes)

        # Eigenvector centrality (power iteration)
        eigen_cent = self._calculate_eigenvector_centrality(topology, nodes)

        # PageRank
        pagerank = self._calculate_pagerank(topology, nodes)

        self._centrality_cache = CentralityMetrics(
            degree_centrality=degree_cent,
            betweenness_centrality=betweenness_cent,
            eigenvector_centrality=eigen_cent,
            pagerank=pagerank,
        )
        self._cache_topology_id = topology.topology_id

        return self._centrality_cache

    def _calculate_betweenness_approx(
        self,
        topology,
        nodes: List[str],
        samples: int = 100,
    ) -> Dict[str, float]:
        """Calculate approximate betweenness centrality using sampling."""
        betweenness = {node: 0.0 for node in nodes}

        if len(nodes) < 3:
            return betweenness

        for _ in range(samples):
            # Random source and target
            source = np.random.choice(nodes)
            target = np.random.choice(nodes)

            if source == target:
                continue

            # BFS to find shortest paths
            paths = self._find_all_shortest_paths(topology, source, target)

            if not paths:
                continue

            # Count how many paths each node is on
            for node in nodes:
                if node == source or node == target:
                    continue
                for path in paths:
                    if node in path:
                        betweenness[node] += 1

        # Normalize
        max_betweenness = max(betweenness.values()) if betweenness else 1
        if max_betweenness > 0:
            betweenness = {k: v / max_betweenness for k, v in betweenness.items()}

        return betweenness

    def _find_all_shortest_paths(
        self,
        topology,
        source: str,
        target: str,
    ) -> List[List[str]]:
        """Find all shortest paths between source and target using BFS."""
        if source == target:
            return [[source]]

        # BFS with path tracking
        queue = deque([[source]])
        visited = {source}
        paths = []
        shortest_length = None

        while queue:
            path = queue.popleft()
            node = path[-1]

            if shortest_length is not None and len(path) > shortest_length:
                continue

            for neighbor in topology.get_neighbors(node):
                if neighbor == target:
                    new_path = path + [neighbor]
                    paths.append(new_path)
                    shortest_length = len(new_path)
                elif neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(path + [neighbor])

        return paths

    def _calculate_eigenvector_centrality(
        self,
        topology,
        nodes: List[str],
        max_iter: int = 100,
        tol: float = 1e-6,
    ) -> Dict[str, float]:
        """Calculate eigenvector centrality using power iteration."""
        n = len(nodes)
        if n == 0:
            return {}

        # Initialize
        x = {node: 1.0 for node in nodes}

        # Power iteration
        for _ in range(max_iter):
            x_new = {}
            for node in nodes:
                x_new[node] = sum(x[neighbor] for neighbor in topology.get_neighbors(node))

            # Normalize
            norm = math.sqrt(sum(v * v for v in x_new.values()))
            if norm < tol:
                break

            x_new = {k: v / norm for k, v in x_new.items()}

            # Check convergence
            diff = sum(abs(x_new[node] - x[node]) for node in nodes)
            if diff < tol:
                break

            x = x_new

        # Ensure non-negative and normalize
        min_val = min(x.values())
        if min_val < 0:
            x = {k: v - min_val for k, v in x.items()}

        norm = sum(x.values())
        if norm > 0:
            x = {k: v / norm for k, v in x.items()}

        return x

    def _calculate_pagerank(
        self,
        topology,
        nodes: List[str],
        alpha: float = 0.85,
        max_iter: int = 100,
        tol: float = 1e-6,
    ) -> Dict[str, float]:
        """Calculate PageRank scores."""
        n = len(nodes)
        if n == 0:
            return {}

        # Initialize uniformly
        pr = {node: 1.0 / n for node in nodes}

        # Power iteration
        for _ in range(max_iter):
            pr_new = {}
            for node in nodes:
                # Sum of PR from incoming links
                incoming_sum = 0.0
                for other in nodes:
                    if node in topology.get_neighbors(other):
                        out_degree = topology.get_degree(other)
                        if out_degree > 0:
                            incoming_sum += pr[other] / out_degree

                pr_new[node] = (1 - alpha) / n + alpha * incoming_sum

            # Check convergence
            diff = sum(abs(pr_new[node] - pr[node]) for node in nodes)
            if diff < tol:
                break

            pr = pr_new

        return pr

    def calculate_network_health(self) -> NetworkHealthMetrics:
        """Calculate network health indicators."""
        if self.controller.topology is None:
            return NetworkHealthMetrics(0, 0, 0, 0, 0, 0, 0)

        topology = self.controller.topology
        summary = topology.get_summary()

        components = topology.connected_components()
        largest_size = max((len(c) for c in components), default=0)
        total_nodes = topology.node_count

        fragmentation_ratio = 1.0 - (largest_size / total_nodes) if total_nodes > 0 else 0

        return NetworkHealthMetrics(
            density=summary.get("density", 0),
            clustering=summary.get("clustering_coefficient", 0),
            avg_path_length=summary.get("average_path_length", 0),
            diameter=summary.get("diameter", 0),
            connected_components=len(components),
            largest_component_size=largest_size,
            fragmentation_ratio=fragmentation_ratio,
        )

    def calculate_influence_distribution(self) -> InfluenceDistribution:
        """Calculate influence inequality metrics."""
        nodes = self.registry.get_all_nodes()

        if not nodes:
            return InfluenceDistribution(0, 0, 0, 0, 0, [])

        # Get influence scores
        influences = sorted([n.influence_score for n in nodes])

        # Gini coefficient
        gini = self._calculate_gini(influences)

        # Herfindahl-Hirschman Index
        hhi = sum(i * i for i in influences)

        # Top node shares
        n = len(influences)
        top_1_share = influences[-1] if n > 0 else 0
        top_5_share = sum(influences[-5:]) / n if n >= 5 else sum(influences) / n
        top_10_share = sum(influences[-10:]) / n if n >= 10 else sum(influences) / n

        # Lorenz curve
        lorenz = self._calculate_lorenz(influences)

        return InfluenceDistribution(
            gini_coefficient=gini,
            herfindahl_index=hhi,
            top_1_share=top_1_share,
            top_5_share=top_5_share,
            top_10_share=top_10_share,
            lorenz_curve=lorenz,
        )

    def _calculate_gini(self, values: List[float]) -> float:
        """Calculate Gini coefficient."""
        n = len(values)
        if n == 0:
            return 0

        sorted_values = sorted(values)
        cumsum = np.cumsum(sorted_values)
        total = cumsum[-1]

        if total == 0:
            return 0

        # Gini = (n+1)/(n-1) - (2/(n*(n-1)*total)) * sum((n+1-i)*values[i])
        gini = (2 * sum((i + 1) * v for i, v in enumerate(sorted_values))) / (n * total) - (n + 1) / n

        return max(0, min(1, gini))

    def _calculate_lorenz(self, values: List[float]) -> List[Tuple[float, float]]:
        """Calculate Lorenz curve points."""
        n = len(values)
        if n == 0:
            return []

        sorted_values = sorted(values)
        total = sum(sorted_values)

        if total == 0:
            return [(i / n, 0) for i in range(n + 1)]

        cumsum = 0
        lorenz = [(0, 0)]

        for i, v in enumerate(sorted_values):
            cumsum += v
            x = (i + 1) / n
            y = cumsum / total
            lorenz.append((x, y))

        return lorenz

    def calculate_collapse_indicators(self) -> NetworkCollapseIndicators:
        """Calculate collapse risk indicators."""
        health = self.calculate_network_health()
        influence = self.calculate_influence_distribution()
        centrality = self.calculate_centrality()

        # Fragmentation acceleration (change from baseline)
        fragmentation_acceleration = max(0, health.fragmentation_ratio - 0.1)

        # Centrality concentration (top 20% control how much)
        nodes = self.registry.get_all_nodes()
        if nodes:
            top_20_percent = max(1, len(nodes) // 5)
            top_centralities = sorted(
                [centrality.eigenvector_centrality.get(n.node_id, 0) for n in nodes],
                reverse=True
            )[:top_20_percent]
            centrality_concentration = sum(top_centralities)
        else:
            centrality_concentration = 0

        # Bridge failure rate (edges whose removal would fragment network)
        bridge_failure_rate = self._calculate_bridge_vulnerability()

        # Information bottleneck (how much flow goes through few nodes)
        bottleneck_score = self._calculate_bottleneck_score(centrality)

        # Cascade risk (based on clustering and centralization)
        cascade_risk = (
            0.5 * centrality_concentration +
            0.3 * (1 - health.clustering) +
            0.2 * influence.gini_coefficient
        )

        # Dominance alert
        dominance_alert = influence.top_1_share > 0.3 or influence.top_5_share > 0.7

        # Minority suppression (based on stance diversity)
        minority_suppression = self._calculate_minority_suppression()

        return NetworkCollapseIndicators(
            fragmentation_acceleration=fragmentation_acceleration,
            centrality_concentration=centrality_concentration,
            bridge_failure_rate=bridge_failure_rate,
            information_bottleneck_score=bottleneck_score,
            cascade_risk=cascade_risk,
            dominance_alert=dominance_alert,
            minority_suppression=minority_suppression,
        )

    def _calculate_bridge_vulnerability(self) -> float:
        """Calculate bridge edge vulnerability."""
        if self.controller.topology is None:
            return 0

        topology = self.controller.topology
        nodes = list(topology.adjacency_list.keys())

        if len(nodes) < 2:
            return 0

        # Count bridges (edges whose removal increases components)
        bridge_count = 0
        total_edges = 0

        for i, node1 in enumerate(nodes):
            for node2 in topology.get_neighbors(node1):
                if node1 < node2:  # Count each edge once
                    total_edges += 1
                    # Temporarily remove edge
                    topology.remove_edge(node1, node2)
                    topology.remove_edge(node2, node1)

                    # Check if still connected
                    if not topology.is_connected():
                        bridge_count += 1

                    # Restore edge
                    topology.add_undirected_edge(node1, node2)

        return bridge_count / total_edges if total_edges > 0 else 0

    def _calculate_bottleneck_score(self, centrality: CentralityMetrics) -> float:
        """Calculate information bottleneck score."""
        if not centrality.pagerank:
            return 0

        pr_values = list(centrality.pagerank.values())
        top_3_sum = sum(sorted(pr_values, reverse=True)[:3])

        return top_3_sum

    def _calculate_minority_suppression(self) -> float:
        """Calculate minority viewpoint suppression score."""
        nodes = self.registry.get_all_nodes()

        if not nodes:
            return 0

        # Check stance distribution
        from ..models import Stance

        stance_counts = defaultdict(int)
        for node in nodes:
            stance = node.behavior.sample_stance()
            stance_counts[stance] += 1

        if not stance_counts:
            return 0

        # If one stance dominates, suppression is high
        max_count = max(stance_counts.values())
        total = sum(stance_counts.values())

        dominance = max_count / total

        # Suppression score
        return max(0, (dominance - 0.5) * 2)  # 0 when balanced, 1 when single stance

    def calculate_flow_metrics(self) -> NetworkFlowMetrics:
        """Calculate metrics related to information flow."""
        if self.controller.topology is None:
            return NetworkFlowMetrics(0, 0, [], [], 0)

        topology = self.controller.topology

        # Average flow distance
        avg_distance = topology.average_path_length()

        # Flow success rate (probability random nodes can reach each other)
        nodes = list(topology.adjacency_list.keys())
        successful_flows = 0
        total_flows = min(100, len(nodes) * (len(nodes) - 1) // 2)

        for _ in range(min(50, total_flows)):
            source = np.random.choice(nodes)
            target = np.random.choice(nodes)

            if source != target and topology.shortest_path_length(source, target) >= 0:
                successful_flows += 1

        flow_success_rate = successful_flows / min(50, total_flows) if total_flows > 0 else 0

        # Find bottlenecks (high betweenness)
        centrality = self.calculate_centrality()
        bottlenecks = [
            node for node, bw in centrality.betweenness_centrality.items()
            if bw > 0.7
        ]

        # Find isolated nodes (can't reach others)
        isolated = []
        components = topology.connected_components()
        if len(components) > 1:
            # Nodes in smaller components are isolated from the main network
            largest_component = max(components, key=len)
            for component in components:
                if component != largest_component:
                    isolated.extend(component)

        # Propagation speed (inverse of average path length)
        propagation_speed = 1.0 / (avg_distance + 1) if avg_distance > 0 else 1.0

        return NetworkFlowMetrics(
            avg_flow_distance=avg_distance,
            flow_success_rate=flow_success_rate,
            bottlenecks=bottlenecks,
            isolated_nodes=isolated,
            propagation_speed=propagation_speed,
        )

    def detect_critical_nodes(self, threshold: float = 0.8) -> List[str]:
        """Detect nodes whose removal would fragment the network.

        Args:
            threshold: Centrality threshold for criticality

        Returns:
            List of critical node IDs
        """
        centrality = self.calculate_centrality()
        health = self.calculate_network_health()

        critical_nodes = []

        # Nodes with high betweenness are critical for connectivity
        for node, bw in centrality.betweenness_centrality.items():
            if bw >= threshold:
                critical_nodes.append(node)

        # Nodes with very high degree are also critical
        max_degree = health.density * len(centrality.degree_centrality)
        for node, degree in centrality.degree_centrality.items():
            if degree >= threshold * max_degree:
                if node not in critical_nodes:
                    critical_nodes.append(node)

        return critical_nodes

    def get_network_summary(self) -> Dict[str, Any]:
        """Get comprehensive network metrics summary."""
        centrality = self.calculate_centrality()
        health = self.calculate_network_health()
        influence = self.calculate_influence_distribution()
        collapse = self.calculate_collapse_indicators()
        flow = self.calculate_flow_metrics()

        return {
            "health_score": health.get_health_score(),
            "health_metrics": {
                "density": health.density,
                "clustering": health.clustering,
                "avg_path_length": health.avg_path_length,
                "connected_components": health.connected_components,
                "fragmentation_ratio": health.fragmentation_ratio,
            },
            "centrality": {
                "top_degree": centrality.get_top_nodes("degree_centrality", 5),
                "top_betweenness": centrality.get_top_nodes("betweenness_centrality", 5),
                "top_pagerank": centrality.get_top_nodes("pagerank", 5),
            },
            "influence": {
                "gini": influence.gini_coefficient,
                "inequality": influence.get_inequality_level(),
                "top_1_share": influence.top_1_share,
                "top_5_share": influence.top_5_share,
            },
            "collapse_risk": {
                "level": collapse.get_collapse_risk(),
                "cascade_risk": collapse.cascade_risk,
                "dominance_alert": collapse.dominance_alert,
                "fragmentation_acceleration": collapse.fragmentation_acceleration,
            },
            "flow": {
                "avg_distance": flow.avg_flow_distance,
                "success_rate": flow.flow_success_rate,
                "bottlenecks": flow.bottlenecks,
                "isolated": flow.isolated_nodes,
            },
        }


def create_network_metrics_calculator(
    controller: NetworkController,
    registry: NodeRegistry,
) -> NetworkMetricsCalculator:
    """Factory function to create a network metrics calculator."""
    return NetworkMetricsCalculator(controller, registry)
