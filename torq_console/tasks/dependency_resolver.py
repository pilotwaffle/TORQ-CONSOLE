"""
Dependency Resolver for Task Graph Engine.

Resolves execution order for nodes in a DAG based on dependencies.
"""

from typing import List, Dict, Set, Optional
from collections import deque
from uuid import UUID

from .models import TaskGraphNode, NodeStatus


class DependencyResolver:
    """
    Resolves node execution order based on dependencies.

    Handles:
    - Topological sorting for sequential execution
    - Parallel execution detection
    - Cycle detection
    """

    def __init__(self, nodes: List[TaskGraphNode]):
        self.nodes = nodes
        self.node_map = {node.node_id: node for node in nodes}
        self.adjacency = self._build_adjacency_list()
        self.in_degree = self._build_in_degree()

    def _build_adjacency_list(self) -> Dict[UUID, List[UUID]]:
        """Build adjacency list representation of the graph."""
        adjacency = {node.node_id: [] for node in self.nodes}
        for node in self.nodes:
            for dep_id in node.depends_on:
                if dep_id in adjacency:
                    adjacency[dep_id].append(node.node_id)
        return adjacency

    def _build_in_degree(self) -> Dict[UUID, int]:
        """Build in-degree count for each node."""
        in_degree = {node.node_id: len(node.depends_on) for node in self.nodes}
        return in_degree

    def detect_cycles(self) -> Optional[List[UUID]]:
        """
        Detect cycles using DFS.

        Returns:
            List of node IDs forming a cycle, or None if no cycle.
        """
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {node.node_id: WHITE for node in self.nodes}
        cycle_path = []

        def dfs(node_id: UUID, path: List[UUID]) -> bool:
            color[node_id] = GRAY
            cycle_path.append(node_id)

            for neighbor in self.adjacency.get(node_id, []):
                if color[neighbor] == GRAY:
                    # Found a cycle
                    cycle_start = cycle_path.index(neighbor)
                    return cycle_path[cycle_start:]
                if color[neighbor] == WHITE:
                    result = dfs(neighbor, cycle_path)
                    if result:
                        return result

            cycle_path.pop()
            color[node_id] = BLACK
            return None

        for node in self.nodes:
            if color[node.node_id] == WHITE:
                cycle = dfs(node.node_id, [])
                if cycle:
                    return cycle

        return None

    def get_ready_nodes(self, completed: Set[UUID]) -> List[UUID]:
        """
        Get nodes whose dependencies are all satisfied.

        Args:
            completed: Set of node IDs that have completed

        Returns:
            List of node IDs ready to execute
        """
        ready = []
        for node in self.nodes:
            if node.node_id not in completed:
                # Check if all dependencies are satisfied
                deps_satisfied = all(
                    dep_id in completed
                    for dep_id in node.depends_on
                )
                if deps_satisfied:
                    ready.append(node.node_id)
        return ready

    def topological_sort(self) -> List[List[UUID]]:
        """
        Generate execution layers for the DAG.

        Returns:
            List of layers, where each layer contains nodes that can be executed in parallel.
        """
        # Check for cycles first
        cycle = self.detect_cycles()
        if cycle:
            raise ValueError(f"Cycle detected in graph: {cycle}")

        # Kahn's algorithm for topological sorting with layers
        in_degree = self.in_degree.copy()
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        layers = []
        visited = set()

        while queue:
            current_layer = list(queue)
            layers.append(current_layer)

            # Process all nodes in current layer
            for node_id in current_layer:
                visited.add(node_id)
                # Reduce in-degree for neighbors
                for neighbor in self.adjacency.get(node_id, []):
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0 and neighbor not in visited:
                        queue.append(neighbor)

            # Clear queue for next layer
            queue = deque(
                node_id for node_id in in_degree
                if in_degree[node_id] == 0 and node_id not in visited
            )

        # Check if all nodes were visited
        if len(visited) != len(self.nodes):
            remaining = [n.node_id for n in self.nodes if n.node_id not in visited]
            raise ValueError(f"Cycle detected involving nodes: {remaining}")

        return layers

    def can_execute_parallel(self, node_ids: List[UUID]) -> bool:
        """
        Determine if nodes can be executed in parallel.

        Args:
            node_ids: List of node IDs to check

        Returns:
            True if nodes have no dependencies between each other
        """
        node_set = set(node_ids)
        for node_id in node_ids:
            node = self.node_map.get(node_id)
            if node:
                # Check if this node depends on any other in the set
                for dep_id in node.depends_on:
                    if dep_id in node_set:
                        return False
        return True

    def get_execution_path(self, target_node_id: UUID) -> List[UUID]:
        """
        Get the execution path to reach a target node.

        Args:
            target_node_id: Target node ID

        Returns:
            Ordered list of node IDs leading to target
        """
        visited = set()
        path = []

        def dfs_collect(node_id: UUID) -> bool:
            if node_id in visited:
                return True

            visited.add(node_id)

            # First visit dependencies
            node = self.node_map.get(node_id)
            if node:
                for dep_id in node.depends_on:
                    if not dfs_collect(dep_id):
                        return False

            path.append(node_id)
            return True

        dfs_collect(target_node_id)
        return path

    def estimate_parallel_potential(self) -> float:
        """
        Estimate parallel execution potential.

        Returns:
            Ratio of parallelizable nodes to total nodes (0-1)
        """
        layers = self.topological_sort()

        # Count nodes in layers with >1 node (parallel layers)
        parallel_nodes = sum(len(layer) for layer in layers if len(layer) > 1)

        return parallel_nodes / len(self.nodes) if self.nodes else 0
