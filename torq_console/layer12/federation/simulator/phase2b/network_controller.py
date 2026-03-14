"""
Network Controller for Multi-Node Federation Simulation

Layer 12 Phase 2B — Multi-Node Federation Scale Validation

Controls network topology creation, node spawning, epoch orchestration,
and message routing for 10-50 node federation simulations.
"""

import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

import heapq
import math

from ..models import Domain
from .node_registry import (
    FederatedNode,
    NodeRegistry,
    create_node,
    create_nodes_with_distribution,
)


logger = logging.getLogger(__name__)


@dataclass
class NetworkTopology:
    """Represents the federation network structure.

    Stores the graph structure and provides analysis methods.
    """

    topology_id: str
    topology_type: str  # "small_world", "scale_free", "random", "hierarchical", "complete"
    node_count: int
    edge_count: int
    adjacency_list: Dict[str, Set[str]] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        # Ensure all nodes have an adjacency entry
        for node in list(self.adjacency_list.keys()):
            if node not in self.adjacency_list:
                self.adjacency_list[node] = set()

    def add_edge(self, source: str, target: str) -> None:
        """Add a directed edge from source to target."""
        if source not in self.adjacency_list:
            self.adjacency_list[source] = set()
        if target not in self.adjacency_list:
            self.adjacency_list[target] = set()

        self.adjacency_list[source].add(target)

    def add_undirected_edge(self, node1: str, node2: str) -> None:
        """Add an undirected edge between two nodes."""
        self.add_edge(node1, node2)
        self.add_edge(node2, node1)

    def remove_edge(self, source: str, target: str) -> None:
        """Remove an edge from source to target."""
        if source in self.adjacency_list:
            self.adjacency_list[source].discard(target)

    def get_neighbors(self, node_id: str) -> Set[str]:
        """Get neighbors of a node."""
        return self.adjacency_list.get(node_id, set())

    def get_degree(self, node_id: str) -> int:
        """Get degree (number of connections) of a node."""
        return len(self.get_neighbors(node_id))

    def average_degree(self) -> float:
        """Calculate average node degree."""
        if not self.adjacency_list:
            return 0.0
        total_degree = sum(len(neighbors) for neighbors in self.adjacency_list.values())
        return total_degree / len(self.adjacency_list)

    def max_degree(self) -> int:
        """Get maximum degree in the network."""
        return max((len(neighbors) for neighbors in self.adjacency_list.values()), default=0)

    def density(self) -> float:
        """Calculate network density."""
        n = len(self.adjacency_list)
        if n < 2:
            return 0.0
        max_edges = n * (n - 1)
        total_edges = sum(len(neighbors) for neighbors in self.adjacency_list.values())
        return total_edges / max_edges if max_edges > 0 else 0.0

    def clustering_coefficient(self, node_id: Optional[str] = None) -> float:
        """Calculate clustering coefficient.

        If node_id is provided, returns local clustering for that node.
        Otherwise returns average clustering coefficient.
        """
        if node_id:
            return self._local_clustering(node_id)

        # Average clustering coefficient
        if not self.adjacency_list:
            return 0.0
        coefficients = [self._local_clustering(n) for n in self.adjacency_list.keys()]
        return sum(coefficients) / len(coefficients) if coefficients else 0.0

    def _local_clustering(self, node_id: str) -> float:
        """Calculate local clustering coefficient for a node."""
        neighbors = self.get_neighbors(node_id)
        k = len(neighbors)

        if k < 2:
            return 0.0

        # Count edges between neighbors
        neighbor_pairs = 0
        for n1 in neighbors:
            for n2 in neighbors:
                if n1 != n2 and n2 in self.get_neighbors(n1):
                    neighbor_pairs += 1

        # Divide by 2 because we counted each edge twice
        possible_edges = k * (k - 1)
        return neighbor_pairs / (2 * possible_edges) if possible_edges > 0 else 0.0

    def shortest_path_length(self, source: str, target: str) -> int:
        """Calculate shortest path length using BFS."""
        if source == target:
            return 0

        visited = {source}
        queue = [(source, 0)]

        while queue:
            node, dist = queue.pop(0)

            for neighbor in self.get_neighbors(node):
                if neighbor == target:
                    return dist + 1
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, dist + 1))

        return -1  # No path found

    def average_path_length(self) -> float:
        """Calculate average shortest path length."""
        nodes = list(self.adjacency_list.keys())

        if len(nodes) < 2:
            return 0.0

        total_length = 0
        count = 0

        for i, source in enumerate(nodes):
            for target in nodes[i + 1:]:
                path_len = self.shortest_path_length(source, target)
                if path_len >= 0:  # Path exists
                    total_length += path_len
                    count += 1

        return total_length / count if count > 0 else 0.0

    def diameter(self) -> int:
        """Calculate network diameter (longest shortest path)."""
        nodes = list(self.adjacency_list.keys())

        if len(nodes) < 2:
            return 0

        max_length = 0

        for i, source in enumerate(nodes):
            for target in nodes[i + 1:]:
                path_len = self.shortest_path_length(source, target)
                if path_len > max_length:
                    max_length = path_len

        return max_length

    def connected_components(self) -> List[Set[str]]:
        """Find connected components using BFS."""
        visited = set()
        components = []

        for node in self.adjacency_list.keys():
            if node not in visited:
                component = set()
                queue = [node]

                while queue:
                    current = queue.pop(0)
                    if current not in visited:
                        visited.add(current)
                        component.add(current)
                        queue.extend(self.get_neighbors(current) - visited)

                components.append(component)

        return components

    def is_connected(self) -> bool:
        """Check if the network is connected."""
        return len(self.connected_components()) == 1

    def get_summary(self) -> Dict[str, Any]:
        """Get topology summary statistics."""
        components = self.connected_components()

        return {
            "topology_type": self.topology_type,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "average_degree": self.average_degree(),
            "max_degree": self.max_degree(),
            "density": self.density(),
            "clustering_coefficient": self.clustering_coefficient(),
            "average_path_length": self.average_path_length(),
            "diameter": self.diameter(),
            "connected_components": len(components),
            "largest_component_size": max((len(c) for c in components), default=0),
        }


@dataclass
class NetworkConfig:
    """Configuration for network generation."""

    node_count: int = 10
    topology_type: str = "small_world"  # small_world, scale_free, random, hierarchical, complete
    connection_probability: float = 0.3  # For random graphs
    rewiring_probability: float = 0.1  # For small-world
    attachment_exponent: float = 2.0  # For scale-free (preferential attachment)
    min_connections: int = 2
    max_connections: int = 5
    domain_distribution: Optional[List[Domain]] = None
    trust_distribution: str = "uniform"  # uniform, normal, skewed
    adversarial_ratio: float = 0.0


@dataclass
class EpochConfig:
    """Configuration for simulation epochs."""

    epochs: int = 20
    claims_per_epoch: int = 50
    event_interval_ms: int = 100
    enable_adversarial_events: bool = True
    adversarial_probability: float = 0.1
    trust_decay_rate: float = 0.01
    enable_reputation_events: bool = True


@dataclass
class NetworkSnapshot:
    """Snapshot of network state at a point in time."""

    timestamp: datetime
    epoch: int
    node_count: int
    active_nodes: int
    quarantined_nodes: int
    avg_trust: float
    avg_influence: float
    topology_summary: Dict[str, Any]
    influential_nodes: List[str]
    adversarial_nodes: List[str]


class NetworkController:
    """Controls network topology and orchestration.

    Responsibilities:
    - Build network topologies (small-world, scale-free, etc.)
    - Spawn and manage nodes
    - Route messages between nodes
    - Orchestrate epoch boundaries
    - Generate network snapshots
    """

    def __init__(
        self,
        registry: NodeRegistry,
        config: NetworkConfig,
    ):
        self.registry = registry
        self.config = config
        self.topology: Optional[NetworkTopology] = None
        self.current_epoch: int = 0
        self.epoch_config: EpochConfig = EpochConfig()
        self.message_log: List[Dict[str, Any]] = []
        self.snapshots: List[NetworkSnapshot] = []
        self.logger = logging.getLogger(__name__)

    def build_topology(self) -> NetworkTopology:
        """Build the network topology based on config."""
        self.logger.info(f"Building {self.config.topology_type} topology with {self.config.node_count} nodes")

        # Create nodes first
        nodes = create_nodes_with_distribution(
            count=self.config.node_count,
            domains=self.config.domain_distribution,
            trust_distribution=self.config.trust_distribution,
            adversarial_ratio=self.config.adversarial_ratio,
        )

        # Register nodes
        for node in nodes:
            self.registry.register_node(node)

        # Build topology based on type
        if self.config.topology_type == "small_world":
            self.topology = self._build_small_world_topology()
        elif self.config.topology_type == "scale_free":
            self.topology = self._build_scale_free_topology()
        elif self.config.topology_type == "random":
            self.topology = self._build_random_topology()
        elif self.config.topology_type == "hierarchical":
            self.topology = self._build_hierarchical_topology()
        elif self.config.topology_type == "complete":
            self.topology = self._build_complete_topology()
        else:
            self.logger.warning(f"Unknown topology type {self.config.topology_type}, using small_world")
            self.topology = self._build_small_world_topology()

        # Update node connections
        self._update_node_connections()

        self.logger.info(
            f"Built {self.topology.topology_type} topology: "
            f"{self.topology.node_count} nodes, {self.topology.edge_count} edges"
        )

        return self.topology

    def _build_small_world_topology(self) -> NetworkTopology:
        """Build a Watts-Strogatz small-world topology."""
        n = self.config.node_count
        k = self.config.min_connections  # Each node connects to k nearest neighbors
        p = self.config.rewiring_probability

        topology = NetworkTopology(
            topology_id=f"sw_{n}_{datetime.utcnow().timestamp()}",
            topology_type="small_world",
            node_count=n,
            edge_count=0,
        )

        # Create ring lattice
        for i in range(n):
            node_id = f"node_{i:04d}"
            # Connect to k nearest neighbors
            for j in range(1, k // 2 + 1):
                neighbor1 = f"node_{(i + j) % n:04d}"
                neighbor2 = f"node_{(i - j) % n:04d}"
                topology.add_undirected_edge(node_id, neighbor1)
                topology.add_undirected_edge(node_id, neighbor2)

        # Rewire edges with probability p
        edges_to_rewire = []
        for source, targets in list(topology.adjacency_list.items()):
            for target in list(targets):
                if source < target:  # Process each edge once
                    if random.random() < p:
                        edges_to_rewire.append((source, target))

        for source, target in edges_to_rewire:
            # Remove old edge
            topology.remove_edge(source, target)
            topology.remove_edge(target, source)

            # Add new edge to random node
            new_target = random.choice([n for n in topology.adjacency_list.keys() if n != source])
            topology.add_undirected_edge(source, new_target)

        # Recalculate edge count
        topology.edge_count = sum(len(targets) for targets in topology.adjacency_list.values()) // 2

        return topology

    def _build_scale_free_topology(self) -> NetworkTopology:
        """Build a Barabási-Albert scale-free topology."""
        n = self.config.node_count
        m = min(self.config.min_connections, n - 1)

        topology = NetworkTopology(
            topology_id=f"sf_{n}_{datetime.utcnow().timestamp()}",
            topology_type="scale_free",
            node_count=n,
            edge_count=0,
        )

        # Start with a small complete graph
        initial_nodes = min(m + 1, n)
        for i in range(initial_nodes):
            node_id = f"node_{i:04d}"
            for j in range(i + 1, initial_nodes):
                other_id = f"node_{j:04d}"
                topology.add_undirected_edge(node_id, other_id)

        # Add remaining nodes with preferential attachment
        for new_node_idx in range(initial_nodes, n):
            new_node_id = f"node_{new_node_idx:04d}"

            # Calculate node degrees for preferential attachment
            node_degrees = {
                node_id: topology.get_degree(node_id)
                for node_id in topology.adjacency_list.keys()
            }
            total_degree = sum(node_degrees.values())

            if total_degree == 0:
                # If no edges yet, connect randomly
                targets = random.sample(list(topology.adjacency_list.keys()), min(m, len(topology.adjacency_list)))
            else:
                # Preferential attachment
                targets = set()
                while len(targets) < m and len(targets) < len(topology.adjacency_list):
                    # Select node with probability proportional to degree
                    r = random.random() * total_degree
                    cumulative = 0
                    for node_id, degree in node_degrees.items():
                        cumulative += degree
                        if cumulative >= r:
                            if node_id != new_node_id:
                                targets.add(node_id)
                            break

            for target in list(targets)[:m]:
                topology.add_undirected_edge(new_node_id, target)

        topology.edge_count = sum(len(targets) for targets in topology.adjacency_list.values()) // 2

        return topology

    def _build_random_topology(self) -> NetworkTopology:
        """Build an Erdős-Rényi random topology."""
        n = self.config.node_count
        p = self.config.connection_probability

        topology = NetworkTopology(
            topology_id=f"er_{n}_{datetime.utcnow().timestamp()}",
            topology_type="random",
            node_count=n,
            edge_count=0,
        )

        # Add each edge with probability p
        for i in range(n):
            node1 = f"node_{i:04d}"
            for j in range(i + 1, n):
                node2 = f"node_{j:04d}"
                if random.random() < p:
                    topology.add_undirected_edge(node1, node2)

        topology.edge_count = sum(len(targets) for targets in topology.adjacency_list.values()) // 2

        return topology

    def _build_hierarchical_topology(self) -> NetworkTopology:
        """Build a hierarchical topology with layers."""
        n = self.config.node_count

        topology = NetworkTopology(
            topology_id=f"hier_{n}_{datetime.utcnow().timestamp()}",
            topology_type="hierarchical",
            node_count=n,
            edge_count=0,
        )

        # Simple hierarchy: root -> intermediaries -> leaves
        if n < 3:
            return self._build_complete_topology()

        root = f"node_0000"
        intermediaries = []
        leaves = []

        # Assign roles
        for i in range(1, n):
            node_id = f"node_{i:04d}"
            if i <= max(2, n // 5):  # Top 20% are intermediaries
                intermediaries.append(node_id)
            else:
                leaves.append(node_id)

        # Connect root to intermediaries
        for inter in intermediaries:
            topology.add_undirected_edge(root, inter)

        # Connect intermediaries to leaves
        for inter in intermediaries:
            # Each intermediary connects to a subset of leaves
            leaves_per_inter = max(1, len(leaves) // len(intermediaries))
            for leaf in leaves[:leaves_per_inter]:
                topology.add_undirected_edge(inter, leaf)
            leaves = leaves[leaves_per_inter:]

        # Connect any remaining leaves to closest intermediary
        for leaf in leaves:
            if intermediaries:
                topology.add_undirected_edge(leaf, intermediaries[0])

        topology.edge_count = sum(len(targets) for targets in topology.adjacency_list.values()) // 2

        return topology

    def _build_complete_topology(self) -> NetworkTopology:
        """Build a complete graph."""
        n = self.config.node_count

        topology = NetworkTopology(
            topology_id=f"comp_{n}_{datetime.utcnow().timestamp()}",
            topology_type="complete",
            node_count=n,
            edge_count=0,
        )

        # Connect all pairs
        for i in range(n):
            node1 = f"node_{i:04d}"
            for j in range(i + 1, n):
                node2 = f"node_{j:04d}"
                topology.add_undirected_edge(node1, node2)

        topology.edge_count = n * (n - 1) // 2

        return topology

    def _update_node_connections(self) -> None:
        """Update node connection sets from topology."""
        if not self.topology:
            return

        for node_id, neighbors in self.topology.adjacency_list.items():
            node = self.registry.get_node(node_id)
            if node:
                node.connections = neighbors.copy()

    def spawn_nodes(
        self,
        count: int,
        behavior_profile: str = "mixed",
        domain: Optional[Domain] = None,
        initial_trust: float = 0.5,
    ) -> List[str]:
        """Spawn new nodes and add them to the network.

        Args:
            count: Number of nodes to spawn
            behavior_profile: "mixed", "honest", "adversarial"
            domain: Optional domain specialization
            initial_trust: Starting trust score

        Returns:
            List of new node IDs
        """
        new_node_ids = []
        existing_count = self.registry.get_node_count()

        for i in range(count):
            node_idx = existing_count + i
            node_id = f"node_{node_idx:04d}"
            display_name = f"Node {node_idx}"

            # Select domain
            if domain:
                selected_domain = domain
            else:
                from ..models import Domain
                selected_domain = random.choice(list(Domain))

            # Determine if adversarial
            adversarial_mode = None
            adversarial_intensity = 0.0
            if behavior_profile == "adversarial" or (behavior_profile == "mixed" and random.random() < 0.2):
                adversarial_mode = random.choice(["flood", "monoculture", "capture"])
                adversarial_intensity = random.uniform(0.3, 0.7)

            node = create_node(
                node_id=node_id,
                display_name=display_name,
                domain=selected_domain,
                initial_trust=initial_trust,
                adversarial_mode=adversarial_mode,
                adversarial_intensity=adversarial_intensity,
            )

            self.registry.register_node(node)
            new_node_ids.append(node_id)

        self.logger.info(f"Spawned {count} new nodes: {new_node_ids}")

        return new_node_ids

    def route_claim(
        self,
        claim_envelope: Any,
        source: str,
        target: str,
    ) -> bool:
        """Route a claim from source to target.

        Returns True if routing succeeded.
        """
        source_node = self.registry.get_node(source)
        target_node = self.registry.get_node(target)

        if not source_node or not target_node:
            self.logger.warning(f"Cannot route claim: source or target not found")
            return False

        if not source_node.is_connected_to(target):
            self.logger.debug(f"No direct connection from {source} to {target}")
            return False

        # Log the message
        self.message_log.append({
            "timestamp": datetime.utcnow(),
            "source": source,
            "target": target,
            "claim_id": getattr(claim_envelope, 'envelope_id', 'unknown'),
            "type": "route",
        })

        return True

    def broadcast_claim(
        self,
        claim_envelope: Any,
        source: str,
        radius: int = 1,
        exclude: Optional[Set[str]] = None,
    ) -> List[str]:
        """Broadcast claim to neighbors within radius.

        Args:
            claim_envelope: The claim to broadcast
            source: Source node ID
            radius: Broadcast radius (1 = direct neighbors only)
            exclude: Nodes to exclude from broadcast

        Returns:
            List of nodes that received the claim
        """
        if not self.topology:
            self.logger.warning("Cannot broadcast: no topology")
            return []

        exclude = exclude or {source}
        recipients = set()
        frontier = {source}

        for _ in range(radius):
            next_frontier = set()
            for node_id in frontier:
                neighbors = self.topology.get_neighbors(node_id)
                for neighbor in neighbors:
                    if neighbor not in exclude and neighbor not in recipients:
                        recipients.add(neighbor)
                        next_frontier.add(neighbor)
            frontier = next_frontier

        # Filter out quarantined nodes
        active_recipients = []
        for r in recipients:
            node = self.registry.get_node(r)
            if node and not node.is_quarantined:
                active_recipients.append(r)

        # Log the broadcast
        self.message_log.append({
            "timestamp": datetime.utcnow(),
            "source": source,
            "recipients": active_recipients,
            "claim_id": getattr(claim_envelope, 'envelope_id', 'unknown'),
            "type": "broadcast",
            "radius": radius,
        })

        return active_recipients

    def advance_epoch(self) -> int:
        """Advance to the next epoch.

        Returns the new epoch number.
        """
        self.current_epoch += 1

        # Apply trust decay
        if self.epoch_config.trust_decay_rate > 0:
            self.registry.apply_trust_decay(self.epoch_config.trust_decay_rate)

        self.logger.debug(f"Advanced to epoch {self.current_epoch}")

        return self.current_epoch

    def take_snapshot(self) -> NetworkSnapshot:
        """Take a snapshot of the current network state."""
        summary = self.registry.get_network_summary()
        topology_summary = self.topology.get_summary() if self.topology else {}

        snapshot = NetworkSnapshot(
            timestamp=datetime.utcnow(),
            epoch=self.current_epoch,
            node_count=summary["total_nodes"],
            active_nodes=summary["active_nodes"],
            quarantined_nodes=summary["quarantined_nodes"],
            avg_trust=summary["avg_trust"],
            avg_influence=summary["avg_influence"],
            topology_summary=topology_summary,
            influential_nodes=[n.node_id for n in self.registry.get_influential_nodes(5)],
            adversarial_nodes=[n.node_id for n in self.registry.get_adversarial_nodes()],
        )

        self.snapshots.append(snapshot)
        return snapshot

    def get_network_state(self) -> Dict[str, Any]:
        """Get comprehensive network state."""
        summary = self.registry.get_network_summary()
        topology_summary = self.topology.get_summary() if self.topology else {}

        return {
            "epoch": self.current_epoch,
            "registry_summary": summary,
            "topology_summary": topology_summary,
            "message_count": len(self.message_log),
            "snapshot_count": len(self.snapshots),
        }

    def get_shortest_path(self, source: str, target: str) -> Optional[List[str]]:
        """Get shortest path between two nodes using BFS.

        Returns list of node IDs from source to target, or None if no path.
        """
        if not self.topology:
            return None

        if source == target:
            return [source]

        # BFS
        visited = {source}
        queue = [(source, [source])]

        while queue:
            node, path = queue.pop(0)

            for neighbor in self.topology.get_neighbors(node):
                if neighbor == target:
                    return path + [neighbor]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return None

    def get_node_centrality(self, node_id: str) -> Dict[str, float]:
        """Calculate centrality measures for a node."""
        if not self.topology:
            return {}

        n = self.topology.node_count

        # Degree centrality
        degree = self.topology.get_degree(node_id)
        degree_centrality = degree / (n - 1) if n > 1 else 0

        # Approximate betweenness (simplified)
        # Full betweenness is O(n^3), using approximation
        betweenness = self._approximate_betweenness(node_id)

        return {
            "degree": degree,
            "degree_centrality": degree_centrality,
            "betweenness_approx": betweenness,
        }

    def _approximate_betweenness(self, node_id: str, samples: int = 50) -> float:
        """Approximate betweenness centrality using sampling."""
        if not self.topology:
            return 0.0

        nodes = list(self.topology.adjacency_list.keys())
        if len(nodes) < 3:
            return 0.0

        count = 0
        for _ in range(samples):
            source = random.choice(nodes)
            target = random.choice(nodes)

            if source != target and source != node_id and target != node_id:
                path = self.get_shortest_path(source, target)
                if path and node_id in path:
                    count += 1

        return count / samples


def create_network_controller(
    node_count: int = 10,
    topology_type: str = "small_world",
    adversarial_ratio: float = 0.0,
) -> NetworkController:
    """Factory function to create a configured network controller.

    Args:
        node_count: Number of nodes in the network
        topology_type: Type of topology to build
        adversarial_ratio: Fraction of nodes that are adversarial

    Returns:
        Configured NetworkController with built topology
    """
    registry = NodeRegistry()
    config = NetworkConfig(
        node_count=node_count,
        topology_type=topology_type,
        adversarial_ratio=adversarial_ratio,
    )

    controller = NetworkController(registry, config)
    controller.build_topology()

    return controller
