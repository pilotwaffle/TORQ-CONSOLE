"""
Graph Engine for Task Graph management.

Provides CRUD operations for task graphs and node/edge management.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

from .models import (
    TaskGraphCreate,
    TaskGraphResponse,
    NodeDefinition,
    EdgeDefinition,
    GraphStatus,
    NodeStatus,
)

logger = logging.getLogger(__name__)


class TaskGraph:
    """
    In-memory representation of a task graph.

    Used for execution planning and validation.
    """

    def __init__(
        self,
        graph_id: UUID,
        name: str,
        nodes: List[NodeDefinition],
        edges: List[EdgeDefinition],
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.graph_id = graph_id
        self.name = name
        self.description = description
        self.nodes = nodes
        self.edges = edges
        self.config = config or {}
        self.node_map = {n.node_id: n for n in nodes if n.node_id}
        self.created_at = datetime.now(timezone.utc)

    def get_node(self, node_id: UUID) -> Optional[NodeDefinition]:
        """Get a node by ID."""
        return self.node_map.get(node_id)

    def get_start_nodes(self) -> List[NodeDefinition]:
        """Get nodes with no dependencies (entry points)."""
        return [n for n in self.nodes if not n.depends_on]

    def get_outgoing_edges(self, node_id: UUID) -> List[EdgeDefinition]:
        """Get edges originating from a node."""
        return [e for e in self.edges if e.source_node_id == node_id]

    def validate(self) -> List[str]:
        """
        Validate the graph structure.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check all referenced nodes exist
        node_ids = {n.node_id for n in self.nodes if n.node_id}
        for edge in self.edges:
            if edge.source_node_id not in node_ids:
                errors.append(f"Edge source node {edge.source_node_id} not found")
            if edge.target_node_id not in node_ids:
                errors.append(f"Edge target node {edge.target_node_id} not found")

        # Check node dependencies exist
        for node in self.nodes:
            for dep_id in node.depends_on:
                if dep_id not in node_ids:
                    errors.append(f"Node {node.name} depends on non-existent node {dep_id}")

        # Check for cycles (via dependency resolver)
        from .dependency_resolver import DependencyResolver
        from .models import TaskGraphNode

        graph_nodes = [
            TaskGraphNode(
                node_id=n.node_id or uuid4(),
                name=n.name,
                node_type=n.node_type,
                agent_id=n.agent_id,
                tool_name=n.tool_name,
                parameters=n.parameters,
                retry_policy=n.retry_policy,
                timeout_seconds=n.timeout_seconds,
                depends_on=n.depends_on,
            )
            for n in self.nodes
        ]

        resolver = DependencyResolver(graph_nodes)
        cycle = resolver.detect_cycles()
        if cycle:
            errors.append(f"Cycle detected: {cycle}")

        return errors


class TaskGraphEngine:
    """
    Manages task graph lifecycle and persistence.

    Provides:
    - Graph CRUD operations
    - Validation
    - Node/edge management
    """

    def __init__(self, supabase_client=None):
        """
        Initialize the graph engine.

        Args:
            supabase_client: Supabase client for persistence
        """
        self.supabase = supabase_client

    async def create_graph(self, graph_data: TaskGraphCreate) -> TaskGraphResponse:
        """
        Create a new task graph.

        Args:
            graph_data: Graph creation request

        Returns:
            Created graph response

        Raises:
            ValueError: If graph validation fails
        """
        # Generate IDs for nodes without them
        nodes_with_ids = []
        for node in graph_data.nodes:
            if not node.node_id:
                node = node.model_copy(update={"node_id": uuid4()})
            nodes_with_ids.append(node)

        # Create in-memory graph for validation
        temp_graph = TaskGraph(
            graph_id=uuid4(),
            name=graph_data.name,
            nodes=nodes_with_ids,
            edges=graph_data.edges,
            description=graph_data.description,
            config=graph_data.config,
        )

        # Validate
        errors = temp_graph.validate()
        if errors:
            raise ValueError(f"Graph validation failed: {errors}")

        # Persist to database
        if self.supabase:
            # Insert graph
            graph_result = self.supabase.table("task_graphs").insert({
                "name": graph_data.name,
                "description": graph_data.description,
                "config": graph_data.config,
                "status": "draft",
            }).execute()

            graph_id = UUID(graph_result.data[0]["graph_id"])

            # Insert nodes
            for node in nodes_with_ids:
                self.supabase.table("task_nodes").insert({
                    "graph_id": str(graph_id),
                    "node_id": str(node.node_id),
                    "name": node.name,
                    "description": node.description,
                    "node_type": node.node_type.value,
                    "agent_id": node.agent_id,
                    "tool_name": node.tool_name,
                    "parameters": node.parameters,
                    "retry_policy": node.retry_policy.dict() if node.retry_policy else {},
                    "timeout_seconds": node.timeout_seconds,
                    "depends_on": [str(d) for d in node.depends_on],
                    "position_x": node.position_x,
                    "position_y": node.position_y,
                }).execute()

            # Insert edges
            for edge in graph_data.edges:
                self.supabase.table("task_edges").insert({
                    "graph_id": str(graph_id),
                    "source_node_id": str(edge.source_node_id),
                    "target_node_id": str(edge.target_node_id),
                    "condition": edge.condition,
                }).execute()

            return TaskGraphResponse(
                graph_id=graph_id,
                name=graph_data.name,
                description=graph_data.description,
                status=GraphStatus.DRAFT,
                created_at=temp_graph.created_at,
                updated_at=datetime.now(timezone.utc),
                nodes=nodes_with_ids,
                edges=graph_data.edges,
                config=graph_data.config,
            )

        # Without database, return in-memory graph
        return TaskGraphResponse(
            graph_id=temp_graph.graph_id,
            name=temp_graph.name,
            description=temp_graph.description,
            status=GraphStatus.DRAFT,
            created_at=temp_graph.created_at,
            updated_at=datetime.now(timezone.utc),
            nodes=temp_graph.nodes,
            edges=temp_graph.edges,
            config=temp_graph.config,
        )

    async def get_graph(self, graph_id: UUID) -> Optional[TaskGraphResponse]:
        """
        Get a graph by ID.

        Args:
            graph_id: Graph ID

        Returns:
            Graph response or None
        """
        if self.supabase:
            # Get graph
            graph_result = self.supabase.table("task_graphs").select("*").eq("graph_id", str(graph_id)).execute()

            if not graph_result.data:
                return None

            graph_data = graph_result.data[0]

            # Get nodes
            nodes_result = self.supabase.table("task_nodes").select("*").eq("graph_id", str(graph_id)).execute()

            # Get edges
            edges_result = self.supabase.table("task_edges").select("*").eq("graph_id", str(graph_id)).execute()

            # Build response
            nodes = [
                NodeDefinition(
                    node_id=UUID(n["node_id"]),
                    name=n["name"],
                    description=n.get("description"),
                    node_type=n["node_type"],
                    agent_id=n.get("agent_id"),
                    tool_name=n.get("tool_name"),
                    parameters=n.get("parameters", {}),
                    position_x=n.get("position_x", 0),
                    position_y=n.get("position_y", 0),
                    depends_on=[UUID(d) for d in n.get("depends_on", [])],
                )
                for n in nodes_result.data
            ]

            edges = [
                EdgeDefinition(
                    source_node_id=UUID(e["source_node_id"]),
                    target_node_id=UUID(e["target_node_id"]),
                    condition=e.get("condition"),
                )
                for e in edges_result.data
            ]

            return TaskGraphResponse(
                graph_id=UUID(graph_data["graph_id"]),
                name=graph_data["name"],
                description=graph_data.get("description"),
                status=GraphStatus(graph_data["status"]),
                created_at=datetime.fromisoformat(graph_data["created_at"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(graph_data["updated_at"].replace("Z", "+00:00")),
                nodes=nodes,
                edges=edges,
                config=graph_data.get("config", {}),
            )

        return None

    async def list_graphs(
        self,
        status: Optional[GraphStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[TaskGraphResponse]:
        """
        List task graphs.

        Args:
            status: Filter by status
            limit: Max results
            offset: Results offset

        Returns:
            List of graph responses
        """
        if self.supabase:
            query = self.supabase.table("task_graphs").select("*")

            if status:
                query = query.eq("status", status.value)

            query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
            result = query.execute()

            return [
                TaskGraphResponse(
                    graph_id=UUID(g["graph_id"]),
                    name=g["name"],
                    description=g.get("description"),
                    status=GraphStatus(g["status"]),
                    created_at=datetime.fromisoformat(g["created_at"].replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat(g["updated_at"].replace("Z", "+00:00")),
                    nodes=[],  # Nodes loaded separately
                    edges=[],
                    config=g.get("config", {}),
                )
                for g in result.data
            ]

        return []

    async def delete_graph(self, graph_id: UUID) -> bool:
        """
        Delete a graph.

        Args:
            graph_id: Graph ID

        Returns:
            True if deleted
        """
        if self.supabase:
            result = self.supabase.table("task_graphs").delete().eq("graph_id", str(graph_id)).execute()
            return len(result.data) > 0
        return False

    async def update_graph_status(
        self,
        graph_id: UUID,
        status: GraphStatus,
    ) -> bool:
        """
        Update graph status.

        Args:
            graph_id: Graph ID
            status: New status

        Returns:
            True if updated
        """
        if self.supabase:
            result = self.supabase.table("task_graphs").update({
                "status": status.value,
            }).eq("graph_id", str(graph_id)).execute()
            return len(result.data) > 0
        return False
