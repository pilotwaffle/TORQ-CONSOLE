"""
TORQ Layer 9 - Enterprise Knowledge Graph Service

L9-M1: Manages the organizational knowledge graph.

The KnowledgeGraphService maintains entities and relationships
across all TORQ layers for organizational intelligence.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from uuid import UUID, uuid4
from collections import defaultdict

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


# Import models
from ..models import (
    KnowledgeGraphNode,
    KnowledgeGraphEdge,
    GraphPath,
    GraphEntityType,
    GraphRelationType,
)


# ============================================================================
# Knowledge Graph Service
# ============================================================================

class KnowledgeGraphService:
    """
    Manages the enterprise knowledge graph.

    Stores entities (missions, workflows, agents, tools, etc.)
    and relationships between them for organizational intelligence.
    """

    def __init__(self):
        """Initialize the knowledge graph service."""
        # Graph storage
        self._nodes: Dict[str, KnowledgeGraphNode] = {}
        self._edges: Dict[str, KnowledgeGraphEdge] = {}

        # Indexes - use str keys to avoid enum issues with use_enum_values
        self._nodes_by_type: Dict[str, Dict[str, KnowledgeGraphNode]] = defaultdict(dict)
        self._edges_by_source: Dict[str, Set[str]] = defaultdict(set)
        self._edges_by_target: Dict[str, Set[str]] = defaultdict(set)
        self._edges_by_relation: Dict[str, Set[str]] = defaultdict(set)

    async def add_node(
        self,
        node: KnowledgeGraphNode,
    ) -> KnowledgeGraphNode:
        """
        Add a node to the knowledge graph.

        Args:
            node: Node to add

        Returns:
            The added/updated node
        """
        node.last_updated = datetime.now()

        # Set first seen if new
        if node.node_id not in self._nodes:
            node.first_seen = datetime.now()
            # Update degree counts - use enum value as string key
            type_key = node.node_type.value if hasattr(node.node_type, 'value') else str(node.node_type)
            self._nodes_by_type[type_key][node.node_id] = node
        else:
            # Preserve first_seen from existing
            existing = self._nodes[node.node_id]
            node.first_seen = existing.first_seen

        self._nodes[node.node_id] = node

        node_type_str = node.node_type.value if hasattr(node.node_type, 'value') else str(node.node_type)
        logger.debug(
            f"[KnowledgeGraph] Added node {node.node_id}: {node_type_str}"
        )

        return node

    async def add_edge(
        self,
        edge: KnowledgeGraphEdge,
    ) -> KnowledgeGraphEdge:
        """
        Add an edge to the knowledge graph.

        Args:
            edge: Edge to add

        Returns:
            The added edge
        """
        # Ensure nodes exist
        if edge.source_id not in self._nodes:
            raise ValueError(f"Source node not found: {edge.source_id}")
        if edge.target_id not in self._nodes:
            raise ValueError(f"Target node not found: {edge.target_id}")

        self._edges[edge.edge_id] = edge

        # Update indexes
        self._edges_by_source[edge.source_id].add(edge.edge_id)
        self._edges_by_target[edge.target_id].add(edge.edge_id)
        # Use enum value as string key
        relation_key = edge.relation_type.value if hasattr(edge.relation_type, 'value') else str(edge.relation_type)
        self._edges_by_relation[relation_key].add(edge.edge_id)

        # Update node degrees
        if edge.source_id in self._nodes:
            self._nodes[edge.source_id].out_degree += 1
        if edge.target_id in self._nodes:
            self._nodes[edge.target_id].in_degree += 1

        relation_str = edge.relation_type.value if hasattr(edge.relation_type, 'value') else str(edge.relation_type)
        logger.debug(
            f"[KnowledgeGraph] Added edge {edge.edge_id}: "
            f"{edge.source_id} -> {relation_str} -> {edge.target_id}"
        )

        return edge

    async def get_node(
        self,
        node_id: str,
    ) -> Optional[KnowledgeGraphNode]:
        """
        Get a node by ID.

        Args:
            node_id: Node ID

        Returns:
            KnowledgeGraphNode or None
        """
        return self._nodes.get(node_id)

    async def get_neighbors(
        self,
        node_id: str,
        relation_type: Optional[GraphRelationType] = None,
        direction: str = "out",
    ) -> List[KnowledgeGraphNode]:
        """
        Get neighbors of a node.

        Args:
            node_id: Center node ID
            relation_type: Optional relation filter
            direction: "in", "out", or "both"

        Returns:
            List of neighboring nodes
        """
        if node_id not in self._nodes:
            return []

        edge_ids = set()
        if direction in ("out", "both"):
            edge_ids.update(self._edges_by_source.get(node_id, set()))
        if direction in ("in", "both"):
            edge_ids.update(self._edges_by_target.get(node_id, set()))

        neighbor_ids = set()
        for edge_id in edge_ids:
            edge = self._edges.get(edge_id)
            if edge:
                if relation_type is None or edge.relation_type == relation_type:
                    if edge.source_id == node_id:
                        neighbor_ids.add(edge.target_id)
                    if edge.target_id == node_id:
                        neighbor_ids.add(edge.source_id)

        neighbors = [
            self._nodes[nid]
            for nid in neighbor_ids
            if nid in self._nodes
        ]

        return neighbors

    async def find_paths(
        self,
        source_id: str,
        target_id: str,
        max_length: int = 5,
        relation_types: Optional[List[GraphRelationType]] = None,
    ) -> List[GraphPath]:
        """
        Find paths between two nodes.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            max_length: Maximum path length
            relation_types: Optional allowed relation types

        Returns:
            List of paths
        """
        if source_id not in self._nodes or target_id not in self._nodes:
            return []

        paths = []

        # BFS for shortest paths
        from collections import deque

        queue = deque([(source_id, [source_id])])
        visited = {source_id}

        while queue:
            current, path = queue.popleft()

            if len(path) > max_length + 1:
                continue

            if current == target_id:
                # Build edge list
                edge_ids = []
                for i in range(len(path) - 1):
                    # Find edge between path[i] and path[i+1]
                    for edge_id, edge in self._edges.items():
                        if (
                            edge.source_id == path[i]
                            and edge.target_id == path[i + 1]
                        ):
                            if relation_types is None or edge.relation_type in relation_types:
                                edge_ids.append(edge_id)
                                break

                paths.append(GraphPath(
                    path_id=str(uuid4()),
                    nodes=path,
                    edges=edge_ids,
                    source_id=source_id,
                    target_id=target_id,
                    length=len(path) - 1,
                    confidence=self._calculate_path_confidence(edge_ids),
                ))
                continue

            # Explore neighbors
            for edge_id in self._edges_by_source.get(current, set()):
                edge = self._edges.get(edge_id)
                if edge and edge.target_id not in visited:
                    if relation_types is None or edge.relation_type in relation_types:
                        visited.add(edge.target_id)
                        queue.append((edge.target_id, path + [edge.target_id]))

        return paths

    def _calculate_path_confidence(self, edge_ids: List[str]) -> float:
        """Calculate confidence of a path from its edges."""
        if not edge_ids:
            return 0.0

        confidences = [
            self._edges[eid].confidence
            for eid in edge_ids
            if eid in self._edges
        ]

        return sum(confidences) / len(confidences) if confidences else 0.0

    async def query_subgraph(
        self,
        node_types: Optional[List[GraphEntityType]] = None,
        relation_types: Optional[List[GraphRelationType]] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Query a subgraph with filters.

        Args:
            node_types: Optional node type filter
            relation_types: Optional relation type filter
            filters: Optional metadata filters

        Returns:
            Dictionary with nodes and edges
        """
        nodes = list(self._nodes.values())
        edges = list(self._edges.values())

        # Filter by node type
        if node_types:
            nodes = [n for n in nodes if n.node_type in node_types]

        # Filter by relation type
        if relation_types:
            edges = [e for e in edges if e.relation_type in relation_types]

        # Filter by metadata
        if filters:
            filtered_nodes = []
            for node in nodes:
                match = True
                for key, value in filters.items():
                    if node.metadata.get(key) != value:
                        match = False
                        break
                if match:
                    filtered_nodes.append(node)
            nodes = filtered_nodes

        node_ids = {n.node_id for n in nodes}
        edges = [e for e in edges if e.source_id in node_ids and e.target_id in node_ids]

        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
        }

    async def get_graph_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the knowledge graph.

        Returns:
            Statistics dictionary
        """
        # Count by node type
        node_type_counts = defaultdict(int)
        for node in self._nodes.values():
            node_type = node.node_type.value if hasattr(node.node_type, 'value') else str(node.node_type)
            node_type_counts[node_type] += 1

        # Count by relation type
        relation_type_counts = defaultdict(int)
        for edge in self._edges.values():
            relation_type = edge.relation_type.value if hasattr(edge.relation_type, 'value') else str(edge.relation_type)
            relation_type_counts[relation_type] += 1

        # Calculate graph metrics
        total_nodes = len(self._nodes)
        total_edges = len(self._edges)
        avg_degree = (
            sum(n.in_degree + n.out_degree for n in self._nodes.values()) / total_nodes
            if total_nodes > 0
            else 0
        )

        return {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "node_type_counts": dict(node_type_counts),
            "relation_type_counts": dict(relation_type_counts),
            "avg_degree": avg_degree,
            "isolated_nodes": sum(
                1 for n in self._nodes.values()
                if n.in_degree == 0 and n.out_degree == 0
            ),
        }


# Global knowledge graph service instance
_service: Optional[KnowledgeGraphService] = None


def get_knowledge_graph_service() -> KnowledgeGraphService:
    """Get the global knowledge graph service instance."""
    global _service
    if _service is None:
        _service = KnowledgeGraphService()
    return _service
