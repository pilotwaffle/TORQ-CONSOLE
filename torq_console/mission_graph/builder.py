"""
Mission Graph Builder

Creates mission graphs from objectives, context, strategic memory, and known patterns.

The builder transforms a user's objective into a structured graph of:
- Objectives (top-level goals)
- Tasks (concrete work items)
- Decisions (branch points)
- Evidence (required data)
- Deliverables (expected outputs)
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from .models import (
    Mission,
    MissionGraph,
    MissionNode,
    MissionEdge,
    NodeType,
    NodeStatus,
    NodePriority,
    EdgeType,
    MissionType,
    ReasoningStrategy,
    AgentType,
    GateCondition,
    DecisionGateType,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Graph Templates
# ============================================================================

class GraphTemplate:
    """Template for common mission graph patterns."""

    @staticmethod
    def analysis_template(mission_id: str) -> MissionGraph:
        """Template for analysis missions (research, investigation, assessment)."""
        nodes = [
            MissionNode(
                id=str(uuid.uuid4()),
                graph_id=mission_id,
                node_type=NodeType.OBJECTIVE,
                title="Analysis objective",
                status=NodeStatus.PENDING
            ),
            MissionNode(
                id=str(uuid.uuid4()),
                graph_id=mission_id,
                node_type=NodeType.TASK,
                title="Gather evidence",
                agent_type=AgentType.SPECIALIST,
                reasoning_strategy=ReasoningStrategy.EVIDENCE_WEIGHTED,
                status=NodeStatus.PENDING
            ),
            MissionNode(
                id=str(uuid.uuid4()),
                graph_id=mission_id,
                node_type=NodeType.TASK,
                title="Analyze patterns",
                agent_type=AgentType.SPECIALIST,
                status=NodeStatus.PENDING
            ),
            MissionNode(
                id=str(uuid.uuid4()),
                graph_id=mission_id,
                node_type=NodeType.DECISION,
                title="Quality gate",
                decision_condition={
                    "gate_type": "confidence_threshold",
                    "metric": "analysis_confidence",
                    "operator": ">=",
                    "value": 0.70,
                    "on_pass": "continue",
                    "on_fail": "spawn_validation"
                },
                status=NodeStatus.PENDING
            ),
            MissionNode(
                id=str(uuid.uuid4()),
                graph_id=mission_id,
                node_type=NodeType.DELIVERABLE,
                title="Analysis report",
                deliverable_type="report",
                status=NodeStatus.PENDING
            )
        ]

        # Wire up dependencies
        nodes[1].depends_on_nodes = [nodes[0].id]
        nodes[2].depends_on_nodes = [nodes[0].id]
        nodes[3].depends_on_nodes = [nodes[1].id, nodes[2].id]
        nodes[4].depends_on_nodes = [nodes[3].id]

        edges = GraphTemplate._create_edges_from_nodes(nodes, mission_id)

        return MissionGraph(
            id=str(uuid.uuid4()),
            mission_id=mission_id,
            nodes=nodes,
            edges=edges
        )

    @staticmethod
    def planning_template(mission_id: str) -> MissionGraph:
        """Template for planning missions (strategy, roadmap, execution plan)."""
        nodes = [
            MissionNode(
                id=str(uuid.uuid4()),
                graph_id=mission_id,
                node_type=NodeType.OBJECTIVE,
                title="Planning objective",
                status=NodeStatus.PENDING
            ),
            MissionNode(
                id=str(uuid.uuid4()),
                graph_id=mission_id,
                node_type=NodeType.TASK,
                title="Decompose requirements",
                agent_type=AgentType.STRATEGIC_PLANNER,
                reasoning_strategy=ReasoningStrategy.DECOMPOSITION_FIRST,
                status=NodeStatus.PENDING
            ),
            MissionNode(
                id=str(uuid.uuid4()),
                graph_id=mission_id,
                node_type=NodeType.TASK,
                title="Identify risks",
                agent_type=AgentType.RISK_QA,
                reasoning_strategy=ReasoningStrategy.RISK_FIRST,
                status=NodeStatus.PENDING
            ),
            MissionNode(
                id=str(uuid.uuid4()),
                graph_id=mission_id,
                node_type=NodeType.TASK,
                title="Estimate resources",
                agent_type=AgentType.DOMAIN_LEAD,
                status=NodeStatus.PENDING
            ),
            MissionNode(
                id=str(uuid.uuid4()),
                graph_id=mission_id,
                node_type=NodeType.DECISION,
                title="Feasibility gate",
                decision_condition={
                    "gate_type": "risk_threshold",
                    "metric": "overall_risk",
                    "operator": "<=",
                    "value": 0.50,
                    "on_pass": "continue",
                    "on_fail": "escalate"
                },
                status=NodeStatus.PENDING
            ),
            MissionNode(
                id=str(uuid.uuid4()),
                graph_id=mission_id,
                node_type=NodeType.DELIVERABLE,
                title="Execution plan",
                deliverable_type="plan",
                status=NodeStatus.PENDING
            )
        ]

        # Dependencies
        nodes[1].depends_on_nodes = [nodes[0].id]
        nodes[2].depends_on_nodes = [nodes[0].id]
        nodes[3].depends_on_nodes = [nodes[1].id]
        nodes[4].depends_on_nodes = [nodes[2].id, nodes[3].id]
        nodes[5].depends_on_nodes = [nodes[4].id]

        edges = GraphTemplate._create_edges_from_nodes(nodes, mission_id)

        return MissionGraph(
            id=str(uuid.uuid4()),
            mission_id=mission_id,
            nodes=nodes,
            edges=edges
        )

    @staticmethod
    def evaluation_template(mission_id: str) -> MissionGraph:
        """Template for evaluation missions (risk assessment, audit, review)."""
        nodes = [
            MissionNode(
                id=str(uuid.uuid4()),
                graph_id=mission_id,
                node_type=NodeType.OBJECTIVE,
                title="Evaluation objective",
                status=NodeStatus.PENDING
            ),
            MissionNode(
                id=str(uuid.uuid4()),
                graph_id=mission_id,
                node_type=NodeType.EVIDENCE,
                title="Gather baseline data",
                evidence_type="baseline",
                status=NodeStatus.PENDING
            ),
            MissionNode(
                id=str(uuid.uuid4()),
                graph_id=mission_id,
                node_type=NodeType.TASK,
                title="Assess current state",
                agent_type=AgentType.SPECIALIST,
                status=NodeStatus.PENDING
            ),
            MissionNode(
                id=str(uuid.uuid4()),
                graph_id=mission_id,
                node_type=NodeType.TASK,
                title="Identify gaps",
                agent_type=AgentType.RISK_QA,
                reasoning_strategy=ReasoningStrategy.CONTRADICTION_FIRST,
                status=NodeStatus.PENDING
            ),
            MissionNode(
                id=str(uuid.uuid4()),
                graph_id=mission_id,
                node_type=NodeType.DECISION,
                title="Compliance gate",
                decision_condition={
                    "gate_type": "evidence_completeness",
                    "metric": "required_evidence_present",
                    "operator": "==",
                    "value": 1.0,
                    "on_pass": "continue",
                    "on_fail": "gather_more_evidence"
                },
                status=NodeStatus.PENDING
            ),
            MissionNode(
                id=str(uuid.uuid4()),
                graph_id=mission_id,
                node_type=NodeType.DELIVERABLE,
                title="Evaluation report",
                deliverable_type="report",
                status=NodeStatus.PENDING
            )
        ]

        # Dependencies
        nodes[1].depends_on_nodes = [nodes[0].id]
        nodes[2].depends_on_nodes = [nodes[1].id]
        nodes[3].depends_on_nodes = [nodes[2].id]
        nodes[4].depends_on_nodes = [nodes[3].id]
        nodes[5].depends_on_nodes = [nodes[4].id]

        edges = GraphTemplate._create_edges_from_nodes(nodes, mission_id)

        return MissionGraph(
            id=str(uuid.uuid4()),
            mission_id=mission_id,
            nodes=nodes,
            edges=edges
        )

    @staticmethod
    def _create_edges_from_nodes(nodes: List[MissionNode], graph_id: str) -> List[MissionEdge]:
        """Create edges from node dependencies."""
        edges = []

        for node in nodes:
            for dep_id in node.depends_on_nodes:
                edges.append(MissionEdge(
                    id=str(uuid.uuid4()),
                    graph_id=graph_id,
                    source_node_id=dep_id,
                    target_node_id=node.id,
                    edge_type=EdgeType.DEPENDS_ON
                ))

        return edges


# ============================================================================
# Mission Graph Builder
# ============================================================================

class MissionGraphBuilder:
    """
    Builds mission graphs from objectives and context.

    Responsibilities:
    - Transform objective into graph structure
    - Apply strategic memory patterns
    - Create appropriate node types
    - Wire dependencies
    - Attach reasoning strategies
    """

    def __init__(self, supabase_client, retrieval_engine=None):
        self.supabase = supabase_client
        self.retrieval = retrieval_engine

    async def build_graph(
        self,
        request: "MissionGraphCreateRequest"
    ) -> MissionGraph:
        """
        Build a mission graph from the request.

        Uses templates, strategic memory, and context to create
        an appropriate graph structure.
        """
        # Select base template based on mission type
        mission = await self._get_mission(request.mission_id)
        if not mission:
            raise ValueError(f"Mission {request.mission_id} not found")

        # Get template for mission type
        template = self._get_template_for_mission(mission)

        # Customize template with context
        graph = await self._customize_graph(template, request)

        # Inject strategic memory patterns
        if request.use_strategic_memory and self.retrieval:
            graph = await self._apply_memory_patterns(graph, request)

        # Validate graph structure
        validation_errors = self._validate_graph_structure(graph)

        if validation_errors:
            graph.validation_errors = validation_errors
            graph.status = GraphStatus.DRAFT
        else:
            graph.status = GraphStatus.VALIDATED

        graph.updated_at = datetime.now()

        return graph

    async def build_from_objective(
        self,
        objective: str,
        mission_type: MissionType,
        context: Dict[str, Any],
        strategic_memory_ids: Optional[List[str]] = None
    ) -> MissionGraph:
        """
        Build a graph directly from an objective string.

        Convenience method for quick graph creation.
        """
        # Determine template from mission type
        template = self._get_template_for_type(mission_type)

        graph = MissionGraph(
            id=str(uuid.uuid4()),
            mission_id=str(uuid.uuid4()),
            nodes=template.nodes.copy(),
            edges=template.edges.copy()
        )

        # Customize with objective and context
        if graph.nodes:
            graph.nodes[0].title = objective
            graph.nodes[0].description = context.get("description", objective)

        # Attach strategic memory
        if strategic_memory_ids:
            for node in graph.nodes:
                node.injected_memory_ids = strategic_memory_ids.copy()

        return graph

    # ========================================================================
    # Internal Methods
    # ========================================================================

    async def _get_mission(self, mission_id: str) -> Optional[Mission]:
        """Get mission by ID."""
        try:
            result = self.supabase.table("missions").select("*").eq("id", mission_id).execute()
            if result.data:
                return Mission(**result.data[0])
        except Exception as e:
            logger.error(f"Error getting mission: {e}")
        return None

    def _get_template_for_mission(self, mission: Mission) -> MissionGraph:
        """Get appropriate template for mission type."""
        return self._get_template_for_type(mission.mission_type)

    def _get_template_for_type(self, mission_type: MissionType) -> MissionGraph:
        """Get template by mission type."""
        templates = {
            MissionType.ANALYSIS: GraphTemplate.analysis_template,
            MissionType.PLANNING: GraphTemplate.planning_template,
            MissionType.EVALUATION: GraphTemplate.evaluation_template,
            MissionType.DESIGN: GraphTemplate.planning_template,
            MissionType.TRANSFORMATION: GraphTemplate.planning_template,
        }

        template_fn = templates.get(mission_type, GraphTemplate.analysis_template)
        return template_fn("placeholder_mission_id")

    async def _customize_graph(
        self,
        template: MissionGraph,
        request: "MissionGraphCreateRequest"
    ) -> MissionGraph:
        """Customize template with request context."""
        # Create new IDs for this graph
        graph_id = str(uuid.uuid4())
        mission_id = request.mission_id

        # Remap nodes with new IDs
        id_map = {}
        nodes = []

        for node in template.nodes:
            new_id = str(uuid.uuid4())
            id_map[node.id] = new_id

            new_node = MissionNode(
                id=new_id,
                graph_id=graph_id,
                node_type=node.node_type,
                title=node.title,
                description=node.description,
                agent_type=node.agent_type,
                reasoning_strategy=request.reasoning_strategy or node.reasoning_strategy,
                status=NodeStatus.PENDING
            )

            # Remap dependencies
            if node.depends_on_nodes:
                new_node.depends_on_nodes = [id_map[old_id] for old_id in node.depends_on_nodes]

            nodes.append(new_node)

        # Remap edges
        edges = []
        for edge in template.edges:
            new_source = id_map.get(edge.source_node_id)
            new_target = id_map.get(edge.target_node_id)

            if new_source and new_target:
                edges.append(MissionEdge(
                    id=str(uuid.uuid4()),
                    graph_id=graph_id,
                    source_node_id=new_source,
                    target_node_id=new_target,
                    edge_type=edge.edge_type,
                    condition=edge.condition
                ))

        # Add context-specific nodes
        additional_nodes = await self._create_context_nodes(
            graph_id,
            mission_id,
            request
        )

        nodes.extend(additional_nodes)

        return MissionGraph(
            id=graph_id,
            mission_id=mission_id,
            nodes=nodes,
            edges=edges,
            metadata={
                "customized_from": template.id,
                "context": request.context
            }
        )

    async def _create_context_nodes(
        self,
        graph_id: str,
        mission_id: str,
        request: "MissionGraphCreateRequest"
    ) -> List[MissionNode]:
        """Create additional nodes based on context."""
        nodes = []

        # Risk area nodes
        for risk_area in request.risk_areas:
            nodes.append(MissionNode(
                id=str(uuid.uuid4()),
                graph_id=graph_id,
                node_type=NodeType.TASK,
                title=f"Assess {risk_area} risk",
                agent_type=AgentType.RISK_QA,
                reasoning_strategy=ReasoningStrategy.RISK_FIRST,
                status=NodeStatus.PENDING
            ))

        # Deliverable nodes
        for deliverable in request.required_deliverables:
            nodes.append(MissionNode(
                id=str(uuid.uuid4()),
                graph_id=graph_id,
                node_type=NodeType.DELIVERABLE,
                title=f"Generate {deliverable}",
                deliverable_type=deliverable.lower().replace(" ", "_"),
                status=NodeStatus.PENDING
            ))

        return nodes

    async def _apply_memory_patterns(
        self,
        graph: MissionGraph,
        request: "MissionGraphCreateRequest"
    ) -> MissionGraph:
        """Apply strategic memory patterns to the graph."""
        # This would query strategic memory for relevant patterns
        # and modify the graph structure accordingly

        # For now, return unchanged
        return graph

    def _validate_graph_structure(self, graph: MissionGraph) -> List[str]:
        """Validate graph structure for common issues."""
        errors = []

        # Check for cycles
        if self._has_cycles(graph):
            errors.append("Graph contains cycles")

        # Check for orphaned nodes
        node_ids = {n.id for n in graph.nodes}
        for node in graph.nodes:
            if node.depends_on_nodes:
                for dep_id in node.depends_on_nodes:
                    if dep_id not in node_ids:
                        errors.append(f"Node {node.id} depends on non-existent node {dep_id}")

        # Check for deliverables without support
        for node in graph.nodes:
            if node.node_type == NodeType.DELIVERABLE:
                if not node.depends_on_nodes:
                    errors.append(f"Deliverable {node.id} has no dependencies")

        return errors

    def _has_cycles(self, graph: MissionGraph) -> bool:
        """Check if graph contains cycles using DFS."""
        # Build adjacency list
        adj = {n.id: [] for n in graph.nodes}
        for edge in graph.edges:
            if edge.edge_type == EdgeType.DEPENDS_ON:
                adj[edge.source_node_id].append(edge.target_node_id)

        # DFS cycle detection
        visited = set()
        rec_stack = set()

        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)

            for neighbor in adj.get(node_id, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node_id)
            return False

        for node_id in adj:
            if node_id not in visited:
                if dfs(node_id):
                    return True

        return False
