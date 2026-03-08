"""
Mission Graph API

REST API for mission graph planning and execution.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from .models import (
    Mission,
    MissionGraph,
    MissionNode,
    MissionCreateRequest,
    MissionGraphCreateRequest,
    GraphExecutionState,
    MissionStatus,
    MissionType,
    NodeType,
    NodeStatus,
)
from .builder import MissionGraphBuilder
from .scheduler import MissionGraphScheduler


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/missions", tags=["mission-graph"])


# ============================================================================
# Dependencies
# ============================================================================

def get_supabase():
    """Get Supabase client."""
    from ..dependencies import get_supabase_client
    return get_supabase_client()


def get_builder(supabase=Depends(get_supabase)):
    """Get mission graph builder instance."""
    from ..strategic_memory.retrieval import MemoryRetrievalEngine
    retrieval = MemoryRetrievalEngine(supabase)
    return MissionGraphBuilder(supabase, retrieval)


def get_scheduler(supabase=Depends(get_supabase)):
    """Get mission graph scheduler instance."""
    # Executor would be injected here
    return MissionGraphScheduler(supabase, executor=None)


# ============================================================================
# Mission Management
# ============================================================================

@router.post("/")
async def create_mission(
    request: MissionCreateRequest,
    supabase=Depends(get_supabase)
):
    """Create a new mission."""
    result = supabase.table("missions").insert({
        "title": request.title,
        "mission_type": request.mission_type.value,
        "objective": request.objective,
        "context": request.context,
        "constraints": request.constraints,
        "reasoning_strategy": request.reasoning_strategy.value if request.reasoning_strategy else None,
        "status": "draft"
    }).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create mission")

    mission_id = result.data[0]["id"]

    # Generate initial graph
    builder = get_builder(supabase)
    graph_request = MissionGraphCreateRequest(
        mission_id=mission_id,
        objective=request.objective,
        context=request.context,
        suggested_workstreams=[],
        required_deliverables=[],
        risk_areas=[],
        use_strategic_memory=True
    )

    graph = await builder.build_graph(graph_request)

    # Store graph
    await _store_graph(supabase, graph)

    return {
        "mission_id": mission_id,
        "graph_id": graph.id,
        "status": "created"
    }


@router.get("/")
async def list_missions(
    status: Optional[MissionStatus] = Query(None),
    mission_type: Optional[MissionType] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    supabase=Depends(get_supabase)
):
    """List missions with optional filters."""
    query = supabase.table("missions").select("*")

    if status:
        query = query.eq("status", status.value)
    if mission_type:
        query = query.eq("mission_type", mission_type.value)

    query = query.order("created_at", desc").range(0, limit - 1)

    result = query.execute()

    return {
        "missions": result.data if result.data else [],
        "count": len(result.data) if result.data else 0
    }


@router.get("/{mission_id}")
async def get_mission(
    mission_id: str,
    supabase=Depends(get_supabase)
):
    """Get a specific mission with its graph."""
    # Get mission
    mission_result = supabase.table("missions").select("*").eq("id", mission_id).execute()

    if not mission_result.data:
        raise HTTPException(status_code=404, detail="Mission not found")

    mission = mission_result.data[0]

    # Get active graph
    graph_result = supabase.table("mission_graphs").select("*").eq("mission_id", mission_id).order("created_at", desc).limit(1).execute()

    graph = graph_result.data[0] if graph_result.data else None

    # Get nodes
    nodes_result = supabase.table("mission_nodes").select("*").eq("mission_id", mission_id).execute()
    nodes = nodes_result.data if nodes_result.data else []

    # Get edges
    edges_result = supabase.table("mission_edges").select("*").eq("mission_id", mission_id).execute()
    edges = edges_result.data if edges_result.data else []

    return {
        "mission": mission,
        "graph": graph,
        "nodes": nodes,
        "edges": edges,
        "node_count": len(nodes),
        "edge_count": len(edges)
    }


@router.post("/{mission_id}/start")
async def start_mission(
    mission_id: str,
    supabase=Depends(get_supabase),
    scheduler: MissionGraphScheduler = Depends(get_scheduler)
):
    """Start executing a mission."""
    # Get mission
    mission_result = supabase.table("missions").select("*").eq("id", mission_id).execute()

    if not mission_result.data:
        raise HTTPException(status_code=404, detail="Mission not found")

    mission = Mission(**mission_result.data[0])

    # Get active graph
    graph_result = supabase.table("mission_graphs").select("*").eq("mission_id", mission_id).eq("status", "validated").order("created_at", desc).limit(1).execute()

    if not graph_result.data:
        raise HTTPException(status_code=400, detail="No validated graph found for mission")

    graph_data = graph_result.data[0]
    graph = await _load_graph(supabase, graph_data["id"])

    # Execute graph
    execution_state = await scheduler.execute_graph(mission, graph)

    return execution_state


# ============================================================================
# Graph Management
# ============================================================================

@router.post("/{mission_id}/graph")
async def create_graph(
    mission_id: str,
    request: MissionGraphCreateRequest,
    builder: MissionGraphBuilder = Depends(get_builder)
):
    """Create a new mission graph."""
    graph = await builder.build_graph(request)

    # Store graph
    supabase = get_supabase()
    await _store_graph(supabase, graph)

    return {
        "graph_id": graph.id,
        "node_count": len(graph.nodes),
        "edge_count": len(graph.edges),
        "validation_errors": graph.validation_errors,
        "validation_warnings": graph.validation_warnings
    }


@router.get("/{mission_id}/graph/validate")
async def validate_graph(
    mission_id: str,
    supabase=Depends(get_supabase)
):
    """Validate a mission graph structure."""
    # Get latest graph
    graph_result = supabase.table("mission_graphs").select("*").eq("mission_id", mission_id).order("created_at", desc).limit(1).execute()

    if not graph_result.data:
        raise HTTPException(status_code=404, detail="Graph not found")

    graph = await _load_graph(supabase, graph_result.data[0]["id"])

    # Validate
    from .builder import MissionGraphBuilder
    validator = MissionGraphBuilder(supabase)
    errors = validator._validate_graph_structure(graph)

    # Update status
    if errors:
        supabase.table("mission_graphs").update({
            "status": "draft",
            "validation_errors": errors
        }).eq("id", graph.id).execute()
    else:
        supabase.table("mission_graphs").update({
            "status": "validated",
            "validation_errors": []
        }).eq("id", graph.id).execute()

    return {
        "graph_id": graph.id,
        "valid": len(errors) == 0,
        "errors": errors
    }


# ============================================================================
# Node Execution
# ============================================================================

@router.get("/{mission_id}/nodes/ready")
async def get_ready_nodes(
    mission_id: str,
    supabase=Depends(get_supabase)
):
    """Get nodes ready for execution."""
    result = supabase.table("ready_mission_nodes").select("*").eq("mission_id", mission_id).execute()

    return {
        "ready_nodes": result.data if result.data else [],
        "count": len(result.data) if result.data else 0
    }


@router.post("/{mission_id}/nodes/{node_id}/execute")
async def execute_node(
    mission_id: str,
    node_id: str,
    supabase=Depends(get_supabase),
    scheduler: MissionGraphScheduler = Depends(get_scheduler)
):
    """Execute a specific node."""
    # Get node
    node_result = supabase.table("mission_nodes").select("*").eq("id", node_id).eq("mission_id", mission_id).execute()

    if not node_result.data:
        raise HTTPException(status_code=404, detail="Node not found")

    # This would trigger the scheduler to execute this node
    # For now, return status
    return {
        "node_id": node_id,
        "status": "execution_requested"
    }


@router.get("/{mission_id}/progress")
async def get_mission_progress(
    mission_id: str,
    supabase=Depends(get_supabase)
):
    """Get current mission progress."""
    result = supabase.table("mission_progress_summary").select("*").eq("mission_id", mission_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Mission not found")

    return result.data[0]


# ============================================================================
# Workstreams
# ============================================================================

@router.get("/{mission_id}/workstreams")
async def get_workstreams(
    mission_id: str,
    supabase=Depends(get_supabase)
):
    """Get workstreams for a mission."""
    result = supabase.table("workstreams").select("*").eq("mission_id", mission_id).execute()

    return {
        "workstreams": result.data if result.data else [],
        "count": len(result.data) if result.data else 0
    }


# ============================================================================
# Helper Functions
# ============================================================================

async def _store_graph(supabase, graph: MissionGraph):
    """Store a mission graph in the database."""
    # Store graph
    graph_result = supabase.table("mission_graphs").insert({
        "id": graph.id,
        "mission_id": graph.mission_id,
        "version": graph.version,
        "status": graph.status.value,
        "graph_metadata": graph.metadata,
        "validation_errors": graph.validation_errors,
        "validation_warnings": graph.validation_warnings,
        "node_count": len(graph.nodes),
        "edge_count": len(graph.edges)
    }).execute()

    # Store nodes
    for node in graph.nodes:
        supabase.table("mission_nodes").insert({
            "id": node.id,
            "graph_id": node.graph_id or graph.id,
            "mission_id": graph.mission_id,
            "node_type": node.node_type.value,
            "title": node.title,
            "description": node.description,
            "status": node.status.value,
            "priority": node.priority.value if node.priority else None,
            "agent_type": node.agent_type.value if node.agent_type else None,
            "reasoning_strategy": node.reasoning_strategy.value if node.reasoning_strategy else None,
            "input_requirements": node.input_requirements,
            "output_schema": node.output_schema,
            "depends_on_nodes": node.depends_on_nodes,
            "decision_condition": node.decision_condition,
            "evidence_type": node.evidence_type,
            "deliverable_type": node.deliverable_type,
            "format_spec": node.format_spec,
            "injected_memory_ids": node.injected_memory_ids,
            "estimated_duration_seconds": node.estimated_duration_seconds
        }).execute()

    # Store edges
    for edge in graph.edges:
        supabase.table("mission_edges").insert({
            "id": edge.id,
            "graph_id": edge.graph_id or graph.id,
            "mission_id": graph.mission_id,
            "source_node_id": edge.source_node_id,
            "target_node_id": edge.target_node_id,
            "edge_type": edge.edge_type.value,
            "condition": edge.condition
        }).execute()


async def _load_graph(supabase, graph_id: str) -> MissionGraph:
    """Load a mission graph from the database."""
    from .models import MissionNode, MissionEdge

    # Get nodes
    nodes_result = supabase.table("mission_nodes").select("*").eq("graph_id", graph_id).execute()
    nodes = [MissionNode(**n) for n in nodes_result.data] if nodes_result.data else []

    # Get edges
    edges_result = supabase.table("mission_edges").select("*").eq("graph_id", graph_id).execute()
    edges = [MissionEdge(**e) for e in edges_result.data] if edges_result.data else []

    return MissionGraph(
        id=graph_id,
        mission_id=nodes[0].mission_id if nodes else "",
        nodes=nodes,
        edges=edges
    )
