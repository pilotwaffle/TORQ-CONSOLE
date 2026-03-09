"""
Operator Control Surface API

Phase 6: Mission Command Center

REST API for the Operator Control Surface - a web-based UI that provides
real-time visibility into missions, nodes, workstreams, events, and handoffs.

This module extends the existing mission_graph API with endpoints designed
for UI consumption, including pagination, filtering, and SSE for real-time
updates.
"""

from __future__ import annotations

import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/control", tags=["operator-control"])


# ============================================================================
# Dependencies
# ============================================================================

def get_supabase():
    """Get Supabase client."""
    from ..dependencies import get_supabase_client
    return get_supabase_client()


# ============================================================================
# Pydantic Models for Control Surface
# ============================================================================

class MissionListItem(BaseModel):
    """Mission summary for list view."""
    id: str
    title: str
    objective: str
    status: str
    mission_type: str
    progress: Dict[str, int] = Field(default_factory=dict)
    created_at: str
    updated_at: str


class MissionListResponse(BaseModel):
    """Response for mission list endpoint."""
    missions: List[MissionListItem]
    total: int
    page: int
    per_page: int


class NodeState(str, Enum):
    """Node state for visualization coloring."""
    COMPLETED = "completed"
    RUNNING = "running"
    READY = "ready"
    PENDING = "pending"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class GraphNode(BaseModel):
    """Node for graph visualization."""
    id: str
    title: str
    type: str
    status: NodeState
    workstream_id: Optional[str] = None
    position: Optional[Dict[str, float]] = None


class GraphEdge(BaseModel):
    """Edge for graph visualization."""
    id: str
    source: str
    target: str
    condition: Optional[str] = None


class MissionGraphResponse(BaseModel):
    """Response for mission graph endpoint."""
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class WorkstreamHealth(str, Enum):
    """Health status of a workstream."""
    HEALTHY = "healthy"
    AT_RISK = "at_risk"
    FAILED = "failed"
    IDLE = "idle"


class WorkstreamStatus(BaseModel):
    """Workstream health status."""
    id: str
    name: str
    health: WorkstreamHealth
    progress: Dict[str, int] = Field(default_factory=dict)
    active_nodes: int = 0
    blocked_nodes: int = 0
    failed_nodes: int = 0
    completed_nodes: int = 0
    total_nodes: int = 0
    last_activity: Optional[str] = None


class WorkstreamsResponse(BaseModel):
    """Response for workstreams endpoint."""
    workstreams: List[WorkstreamStatus]


class EventSeverity(str, Enum):
    """Severity level for events."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class EventItem(BaseModel):
    """Event item for stream."""
    id: str
    event_type: str
    entity_id: str
    entity_type: str
    severity: EventSeverity
    event_data: Dict[str, Any] = Field(default_factory=dict)
    created_at: str


class EventStreamResponse(BaseModel):
    """Response for event stream endpoint."""
    events: List[EventItem]
    total: int
    limit: int
    offset: int


class HandoffFormat(str, Enum):
    """Handoff format type."""
    RICH = "rich"
    MINIMAL = "minimal"


class HandoffItem(BaseModel):
    """Handoff item for viewer."""
    id: str
    source_node_id: str
    target_node_id: str
    source_node_title: str
    target_node_title: str
    confidence: float
    summary: str
    artifacts: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    format: HandoffFormat
    created_at: str


class HandoffsResponse(BaseModel):
    """Response for handoffs endpoint."""
    handoffs: List[HandoffItem]


class NodeDetail(BaseModel):
    """Detailed node information."""
    id: str
    title: str
    type: str
    status: NodeState
    description: Optional[str] = None
    agent_type: Optional[str] = None
    workstream_id: Optional[str] = None
    output_summary: Optional[str] = None
    event_count: int = 0
    handoff_count: int = 0
    created_at: str
    updated_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


# ============================================================================
# Mission Portfolio Endpoints
# ============================================================================

@router.get("/missions", response_model=MissionListResponse)
async def list_missions_control(
    status: Optional[str] = Query(None, description="Filter by status"),
    mission_type: Optional[str] = Query(None, description="Filter by mission type"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("updated_at", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    supabase=Depends(get_supabase)
):
    """
    Get list of missions for the Mission Portfolio Panel.

    Returns missions with progress tracking and status indicators.
    Supports pagination, filtering, and sorting.
    """
    # Build query
    query = supabase.table("missions").select("*")

    # Apply filters
    if status:
        query = query.eq("status", status)
    if mission_type:
        query = query.eq("mission_type", mission_type)

    # Apply sorting
    query = query.order(sort_by, desc=(sort_order == "desc"))

    # Apply pagination
    start = (page - 1) * per_page
    end = start + per_page - 1
    query = query.range(start, end)

    result = query.execute()

    if not result.data:
        return MissionListResponse(missions=[], total=0, page=page, per_page=per_page)

    # Get count for total
    count_result = supabase.table("missions").select("*", count="exact")
    if status:
        count_result = count_result.eq("status", status)
    if mission_type:
        count_result = count_result.eq("mission_type", mission_type)
    count_result = count_result.execute()
    total = count_result.count or 0

    # Enrich with progress information
    missions_with_progress = []
    for mission in result.data:
        mission_id = mission["id"]

        # Get node counts for progress
        nodes_result = supabase.table("mission_nodes").select("status")\
            .eq("mission_id", mission_id).execute()

        nodes = nodes_result.data if nodes_result.data else []
        completed = sum(1 for n in nodes if n.get("status") == "completed")
        total_nodes = len(nodes)

        missions_with_progress.append(MissionListItem(
            id=mission["id"],
            title=mission.get("title", ""),
            objective=mission.get("objective", ""),
            status=mission.get("status", "draft"),
            mission_type=mission.get("mission_type", "analysis"),
            progress={
                "completed": completed,
                "total": total_nodes,
                "percent": round(completed / total_nodes * 100) if total_nodes > 0 else 0
            },
            created_at=mission.get("created_at", ""),
            updated_at=mission.get("updated_at", "")
        ))

    return MissionListResponse(
        missions=missions_with_progress,
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/missions/{mission_id}/detail")
async def get_mission_detail(
    mission_id: str,
    supabase=Depends(get_supabase)
):
    """
    Get detailed mission information for the Mission Detail page header.

    Returns mission with full context and graph metadata.
    """
    # Get mission
    mission_result = supabase.table("missions").select("*").eq("id", mission_id).execute()

    if not mission_result.data:
        raise HTTPException(status_code=404, detail="Mission not found")

    mission = mission_result.data[0]

    # Get progress
    nodes_result = supabase.table("mission_nodes").select("status")\
        .eq("mission_id", mission_id).execute()

    nodes = nodes_result.data if nodes_result.data else []
    completed = sum(1 for n in nodes if n.get("status") == "completed")
    total_nodes = len(nodes)

    # Get active graph
    graph_result = supabase.table("mission_graphs").select("*")\
        .eq("mission_id", mission_id).order("created_at", desc=True).limit(1).execute()

    graph = graph_result.data[0] if graph_result.data else None

    return {
        "mission": mission,
        "progress": {
            "completed": completed,
            "total": total_nodes,
            "percent": round(completed / total_nodes * 100) if total_nodes > 0 else 0
        },
        "graph": graph,
        "node_count": total_nodes
    }


# ============================================================================
# Mission Graph View Endpoints
# ============================================================================

@router.get("/missions/{mission_id}/graph", response_model=MissionGraphResponse)
async def get_mission_graph_control(
    mission_id: str,
    supabase=Depends(get_supabase)
):
    """
    Get mission graph for interactive visualization.

    Returns nodes and edges in React Flow format with status coloring.
    """
    # Get nodes
    nodes_result = supabase.table("mission_nodes").select("*")\
        .eq("mission_id", mission_id).order("sequence_order").execute()

    if not nodes_result.data:
        return MissionGraphResponse(nodes=[], edges=[])

    # Convert to graph nodes with state mapping
    graph_nodes = []
    for node in nodes_result.data:
        # Map status to NodeState
        status = node.get("status", "pending")
        if status in ["ready", "running", "blocked", "skipped"]:
            node_state = NodeState(status)
        else:
            node_state = NodeState.COMPLETED if status == "completed" else NodeState.PENDING
            if status == "failed":
                node_state = NodeState.FAILED

        graph_nodes.append(GraphNode(
            id=node["id"],
            title=node.get("title", ""),
            type=node.get("node_type", "task"),
            status=node_state,
            workstream_id=node.get("workstream_id"),
            position=None  # Could be stored/calculated separately
        ))

    # Get edges
    edges_result = supabase.table("mission_edges").select("*")\
        .eq("mission_id", mission_id).execute()

    graph_edges = []
    if edges_result.data:
        for edge in edges_result.data:
            graph_edges.append(GraphEdge(
                id=edge["id"],
                source=edge.get("source_node_id", ""),
                target=edge.get("target_node_id", ""),
                condition=edge.get("condition")
            ))

    return MissionGraphResponse(nodes=graph_nodes, edges=graph_edges)


@router.get("/missions/{mission_id}/nodes/{node_id}/detail")
async def get_node_detail(
    mission_id: str,
    node_id: str,
    supabase=Depends(get_supabase)
):
    """
    Get detailed node information for the Node Detail Panel.

    Returns node with agent info, output summary, and related counts.
    """
    # Get node
    node_result = supabase.table("mission_nodes").select("*")\
        .eq("id", node_id).eq("mission_id", mission_id).execute()

    if not node_result.data:
        raise HTTPException(status_code=404, detail="Node not found")

    node = node_result.data[0]

    # Count events
    events_count_result = supabase.table("mission_events").select("*", count="exact")\
        .eq("entity_id", node_id).execute()

    # Count handoffs (source or target)
    handoffs_count_result = supabase.table("mission_handoffs").select("*", count="exact")\
        .or_(f"source_node_id.eq.{node_id},target_node_id.eq.{node_id}").execute()

    return NodeDetail(
        id=node["id"],
        title=node.get("title", ""),
        type=node.get("node_type", "task"),
        status=NodeState(node.get("status", "pending")),
        description=node.get("description"),
        agent_type=node.get("agent_type"),
        workstream_id=node.get("workstream_id"),
        output_summary=node.get("output_summary"),  # If stored
        event_count=events_count_result.count or 0,
        handoff_count=handoffs_count_result.count or 0,
        created_at=node.get("created_at", ""),
        updated_at=node.get("updated_at", ""),
        started_at=node.get("started_at"),
        completed_at=node.get("completed_at")
    )


# ============================================================================
# Workstream Health Dashboard Endpoints
# ============================================================================

def _calculate_workstream_health(
    active: int,
    blocked: int,
    failed: int,
    completed: int,
    pending: int,
    last_activity: Optional[str]
) -> WorkstreamHealth:
    """
    Calculate workstream health based on node states.

    Logic from workstream_state.py:
    - healthy: no blocked nodes, at least one active
    - at_risk: has blocked nodes, but making progress
    - failed: has failed nodes, no progress in 5 minutes
    - idle: no active nodes, no failed nodes
    """
    if failed > 0:
        # Check if recent progress
        if last_activity:
            last_time = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
            if datetime.now(last_time.tzinfo) - last_time > timedelta(minutes=5):
                return WorkstreamHealth.FAILED

    if blocked > 0:
        if active > 0 or completed > 0:
            return WorkstreamHealth.AT_RISK
        return WorkstreamHealth.AT_RISK

    if active > 0:
        return WorkstreamHealth.HEALTHY

    if pending > 0:
        return WorkstreamHealth.IDLE

    return WorkstreamHealth.IDLE


@router.get("/missions/{mission_id}/workstreams/health", response_model=WorkstreamsResponse)
async def get_workstreams_health(
    mission_id: str,
    supabase=Depends(get_supabase)
):
    """
    Get workstream health status for the Workstream Health Dashboard.

    Returns each workstream with calculated health, progress, and activity.
    """
    # Get all nodes with workstream info
    nodes_result = supabase.table("mission_nodes").select("*")\
        .eq("mission_id", mission_id).not_.is_("workstream_id", "null").execute()

    if not nodes_result.data:
        return WorkstreamsResponse(workstreams=[])

    # Group by workstream
    workstream_data: Dict[str, Dict[str, Any]] = {}

    for node in nodes_result.data:
        ws_id = node.get("workstream_id")
        if not ws_id:
            continue

        if ws_id not in workstream_data:
            workstream_data[ws_id] = {
                "id": ws_id,
                "name": f"Workstream {ws_id[:8]}",  # Could be enhanced with names
                "nodes": [],
                "last_activity": None
            }

        workstream_data[ws_id]["nodes"].append(node)
        # Track latest activity
        updated = node.get("updated_at", "")
        if not workstream_data[ws_id]["last_activity"] or updated > workstream_data[ws_id]["last_activity"]:
            workstream_data[ws_id]["last_activity"] = updated

    # Calculate health for each workstream
    workstreams = []
    for ws_id, data in workstream_data.items():
        nodes = data["nodes"]

        active = sum(1 for n in nodes if n.get("status") == "running")
        blocked = sum(1 for n in nodes if n.get("status") == "blocked")
        failed = sum(1 for n in nodes if n.get("status") == "failed")
        completed = sum(1 for n in nodes if n.get("status") == "completed")
        pending = sum(1 for n in nodes if n.get("status") in ["pending", "ready"])
        total = len(nodes)

        health = _calculate_workstream_health(
            active=active,
            blocked=blocked,
            failed=failed,
            completed=completed,
            pending=pending,
            last_activity=data["last_activity"]
        )

        workstreams.append(WorkstreamStatus(
            id=ws_id,
            name=data["name"],
            health=health,
            progress={"completed": completed, "total": total},
            active_nodes=active,
            blocked_nodes=blocked,
            failed_nodes=failed,
            completed_nodes=completed,
            total_nodes=total,
            last_activity=data["last_activity"]
        ))

    return WorkstreamsResponse(workstreams=workstreams)


# ============================================================================
# Event Stream Endpoints
# ============================================================================

@router.get("/missions/{mission_id}/events", response_model=EventStreamResponse)
async def get_mission_events(
    mission_id: str,
    limit: int = Query(100, ge=1, le=1000, description="Max events to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    supabase=Depends(get_supabase)
):
    """
    Get events for the Event Stream.

    Returns paginated events with filtering options.
    """
    # Build query
    query = supabase.table("mission_events").select("*")
    query = query.eq("mission_id", mission_id)

    # Apply filters
    if event_type:
        query = query.eq("event_type", event_type)
    if severity:
        query = query.eq("severity", severity)
    if entity_type:
        query = query.eq("entity_type", entity_type)

    # Get total count
    count_result = query.copy().select("*", count="exact").execute()
    total = count_result.count or 0

    # Apply pagination and ordering
    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

    result = query.execute()

    events = []
    if result.data:
        for event in result.data:
            events.append(EventItem(
                id=event["id"],
                event_type=event.get("event_type", ""),
                entity_id=event.get("entity_id", ""),
                entity_type=event.get("entity_type", ""),
                severity=EventSeverity(event.get("severity", "info")),
                event_data=event.get("event_data", {}),
                created_at=event.get("created_at", "")
            ))

    return EventStreamResponse(
        events=events,
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/missions/{mission_id}/events/stream")
async def stream_mission_events(
    mission_id: str,
    supabase=Depends(get_supabase)
):
    """
    Server-Sent Events endpoint for real-time event streaming.

    Clients can connect to receive events as they occur.
    """
    async def event_generator():
        """Generate SSE events."""
        # Track last event timestamp
        last_timestamp = datetime.utcnow()

        try:
            while True:
                # Query for new events
                query = supabase.table("mission_events").select("*")\
                    .eq("mission_id", mission_id)\
                    .gt("created_at", last_timestamp.isoformat())\
                    .order("created_at", desc=True)\
                    .limit(100)

                result = await asyncio.to_thread(query.execute)

                if result.data:
                    for event in reversed(result.data):  # Send in chronological order
                        event_data = {
                            "id": event["id"],
                            "event_type": event.get("event_type", ""),
                            "entity_id": event.get("entity_id", ""),
                            "entity_type": event.get("entity_type", ""),
                            "severity": event.get("severity", "info"),
                            "event_data": event.get("event_data", {}),
                            "created_at": event.get("created_at", "")
                        }
                        yield f"data: {json.dumps(event_data)}\n\n"

                        # Update timestamp
                        created = event.get("created_at", "")
                        if created:
                            last_timestamp = datetime.fromisoformat(created.replace('Z', '+00:00'))

                # Wait before polling again
                await asyncio.sleep(2)

        except asyncio.CancelledError:
            # Client disconnected
            logger.info(f"SSE client disconnected for mission {mission_id}")
        except Exception as e:
            logger.error(f"Error in SSE stream for mission {mission_id}: {e}")
            yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


# ============================================================================
# Handoff Viewer Endpoints
# ============================================================================

@router.get("/missions/{mission_id}/handoffs", response_model=HandoffsResponse)
async def get_mission_handoffs(
    mission_id: str,
    source_node_id: Optional[str] = Query(None, description="Filter by source node"),
    target_node_id: Optional[str] = Query(None, description="Filter by target node"),
    supabase=Depends(get_supabase)
):
    """
    Get handoffs for the Handoff Viewer.

    Returns all handoffs with source/target node information.
    """
    # Build query
    query = supabase.table("mission_handoffs").select("*")
    query = query.eq("mission_id", mission_id)

    if source_node_id:
        query = query.eq("source_node_id", source_node_id)
    if target_node_id:
        query = query.eq("target_node_id", target_node_id)

    query = query.order("created_at", desc=True)

    result = query.execute()

    handoffs = []
    if result.data:
        # Get node titles in bulk
        node_ids = set()
        for h in result.data:
            node_ids.add(h.get("source_node_id"))
            node_ids.add(h.get("target_node_id"))

        node_titles = {}
        if node_ids:
            nodes_result = supabase.table("mission_nodes").select("id, title")\
                .in_("id", list(node_ids)).execute()
            if nodes_result.data:
                node_titles = {n["id"]: n["title"] for n in nodes_result.data}

        for handoff in result.data:
            source_id = handoff.get("source_node_id", "")
            target_id = handoff.get("target_node_id", "")

            handoffs.append(HandoffItem(
                id=handoff["id"],
                source_node_id=source_id,
                target_node_id=target_id,
                source_node_title=node_titles.get(source_id, "Unknown"),
                target_node_title=node_titles.get(target_id, "Unknown"),
                confidence=handoff.get("confidence", 0.0),
                summary=handoff.get("summary", ""),
                artifacts=handoff.get("artifacts", []),
                recommendations=handoff.get("recommendations", []),
                dependencies=handoff.get("dependencies", []),
                format=HandoffFormat(handoff.get("format", "minimal")),
                created_at=handoff.get("created_at", "")
            ))

    return HandoffsResponse(handoffs=handoffs)


@router.get("/missions/{mission_id}/handoffs/{handoff_id}")
async def get_handoff_detail(
    mission_id: str,
    handoff_id: str,
    supabase=Depends(get_supabase)
):
    """
    Get detailed handoff information.

    Returns full handoff packet with all metadata.
    """
    result = supabase.table("mission_handoffs").select("*")\
        .eq("id", handoff_id).eq("mission_id", mission_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Handoff not found")

    return result.data[0]


# ============================================================================
# Dashboard Summary Endpoints
# ============================================================================

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    supabase=Depends(get_supabase)
):
    """
    Get dashboard summary for the Mission Portfolio Panel.

    Returns aggregate statistics across all missions.
    """
    # Get mission counts by status
    missions_result = supabase.table("missions").select("status", count="exact").execute()

    status_counts: Dict[str, int] = {}
    if missions_result.data:
        for m in missions_result.data:
            status = m.get("status", "draft")
            status_counts[status] = status_counts.get(status, 0) + 1

    # Get recent activity
    recent_events_result = supabase.table("mission_events").select("*")\
        .order("created_at", desc=True).limit(10).execute()

    recent_events = recent_events_result.data if recent_events_result.data else []

    # Get active missions
    active_result = supabase.table("missions").select("*")\
        .in_("status", ["running", "scheduled"]).order("updated_at", desc=True).limit(5).execute()

    active_missions = active_result.data if active_result.data else []

    return {
        "status_counts": status_counts,
        "total_missions": sum(status_counts.values()),
        "active_missions_count": len(active_missions),
        "recent_events": recent_events,
        "active_missions": active_missions
    }
