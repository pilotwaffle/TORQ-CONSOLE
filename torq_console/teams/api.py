"""
Agent Teams - API Routes

Phase 5.2: Agent Teams as a governed execution primitive.

This module provides FastAPI routes for team management and execution.
"""

from __future__ import annotations

import logging
import asyncio
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .models import (
    TeamDefinitionResponse,
    TeamExecutionResponse,
    TeamMessageResponse,
    TeamDecisionResponse,
    CreateTeamRequest,
    ExecuteTeamNodeRequest,
    TeamPattern,
    DecisionPolicy,
    TeamExecutionStatus,
    TeamRole,
    TeamExecutionResult,
)
from .registry import TeamDefinitionRegistry, get_registry, initialize_registry
from .orchestrator import AgentTeamOrchestrator, execute_team_node
from .persistence import TeamPersistence


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/teams", tags=["agent-teams"])


# ============================================================================
# Dependencies
# ============================================================================

def get_supabase():
    """Get Supabase client."""
    from ..dependencies import get_supabase_client
    return get_supabase_client()


def get_team_registry(supabase=Depends(get_supabase)) -> TeamDefinitionRegistry:
    """Get team registry."""
    registry = get_registry()
    if not registry._loaded_from_db:
        asyncio.create_task(initialize_registry(supabase))
    return registry


def get_orchestrator(supabase=Depends(get_supabase)) -> AgentTeamOrchestrator:
    """Get team orchestrator."""
    registry = get_team_registry(supabase)
    return AgentTeamOrchestrator(supabase, registry)


def get_persistence(supabase=Depends(get_supabase)) -> TeamPersistence:
    """Get team persistence."""
    return TeamPersistence(supabase)


# ============================================================================
# Team Definitions
# ============================================================================

@router.get("", response_model=List[TeamDefinitionResponse])
async def list_teams(
    pattern: Optional[TeamPattern] = Query(None),
    is_active: bool = Query(True),
    registry: TeamDefinitionRegistry = Depends(get_team_registry),
):
    """
    List all team definitions.

    Query Parameters:
    - pattern: Filter by collaboration pattern
    - is_active: Only show active teams
    """
    teams = registry.list_active() if is_active else registry.list_all()

    if pattern:
        teams = [t for t in teams if t.pattern == pattern]

    return [
        TeamDefinitionResponse(
            id=str(t.id),
            team_id=t.team_id,
            name=t.name,
            description=t.description,
            pattern=t.pattern.value,
            decision_policy=t.decision_policy.value,
            max_rounds=t.max_rounds,
            members=[
                {
                    "role_name": m.role_name.value,
                    "agent_type": m.agent_type,
                    "confidence_weight": m.confidence_weight,
                    "execution_order": m.execution_order,
                    "is_required": m.is_required,
                }
                for m in t.members
            ],
            is_active=t.is_active,
            created_at=t.created_at,
            updated_at=t.updated_at,
        )
        for t in teams
    ]


@router.get("/{team_id}", response_model=TeamDefinitionResponse)
async def get_team(
    team_id: str,
    registry: TeamDefinitionRegistry = Depends(get_team_registry),
):
    """Get a specific team definition."""
    definition = registry.get_by_team_id(team_id)
    if not definition:
        raise HTTPException(status_code=404, detail=f"Team not found: {team_id}")

    return TeamDefinitionResponse(
        id=str(definition.id),
        team_id=definition.team_id,
        name=definition.name,
        description=definition.description,
        pattern=definition.pattern.value,
        decision_policy=definition.decision_policy.value,
        max_rounds=definition.max_rounds,
        members=[
            {
                "role_name": m.role_name.value,
                "agent_type": m.agent_type,
                "confidence_weight": m.confidence_weight,
                "execution_order": m.execution_order,
                "is_required": m.is_required,
            }
            for m in definition.members
        ],
        is_active=definition.is_active,
        created_at=definition.created_at,
        updated_at=definition.updated_at,
    )


@router.post("", response_model=TeamDefinitionResponse)
async def create_team(
    request: CreateTeamRequest,
    supabase=Depends(get_supabase),
    registry: TeamDefinitionRegistry = Depends(get_team_registry),
):
    """Create a new team definition."""
    from .models import TeamDefinition, TeamMemberRole, TeamPattern, DecisionPolicy

    # Check if team_id already exists
    if registry.get_by_team_id(request.team_id):
        raise HTTPException(status_code=400, detail=f"Team already exists: {request.team_id}")

    # Create team definition
    definition = TeamDefinition(
        team_id=request.team_id,
        name=request.name,
        description=request.description,
        pattern=TeamPattern(request.pattern.value) if isinstance(request.pattern, TeamPattern) else request.pattern,
        decision_policy=DecisionPolicy(request.decision_policy.value) if isinstance(request.decision_policy, DecisionPolicy) else request.decision_policy,
        max_rounds=request.max_rounds,
        members=[
            TeamMemberRole(
                role_name=TeamRole(m.role_name),
                agent_type=m.agent_type,
                confidence_weight=m.confidence_weight,
                execution_order=m.execution_order,
                is_required=m.is_required,
            )
            for m in request.members
        ],
    )

    # Persist to database
    team_data = {
        "team_id": definition.team_id,
        "name": definition.name,
        "description": definition.description,
        "pattern": definition.pattern.value,
        "decision_policy": definition.decision_policy.value,
        "max_rounds": definition.max_rounds,
    }

    result = supabase.table("agent_teams").insert(team_data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create team")

    definition.id = UUID(result.data[0]["id"])

    # Persist members
    for member in definition.members:
        member_data = {
            "team_id": str(definition.id),
            "role_name": member.role_name.value,
            "agent_type": member.agent_type,
            "confidence_weight": member.confidence_weight,
            "execution_order": member.execution_order,
            "is_required": member.is_required,
        }
        supabase.table("agent_team_members").insert(member_data).execute()

    # Register in memory
    registry.register(definition)

    return TeamDefinitionResponse(
        id=str(definition.id),
        team_id=definition.team_id,
        name=definition.name,
        description=definition.description,
        pattern=definition.pattern.value,
        decision_policy=definition.decision_policy.value,
        max_rounds=definition.max_rounds,
        members=[
            {
                "role_name": m.role_name.value,
                "agent_type": m.agent_type,
                "confidence_weight": m.confidence_weight,
                "execution_order": m.execution_order,
                "is_required": m.is_required,
            }
            for m in definition.members
        ],
        is_active=definition.is_active,
        created_at=definition.created_at,
        updated_at=definition.updated_at,
    )


# ============================================================================
# Team Executions
# ============================================================================

@router.get("/executions", response_model=List[TeamExecutionResponse])
async def list_executions(
    mission_id: Optional[str] = Query(None),
    status: Optional[TeamExecutionStatus] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    persistence: TeamPersistence = Depends(get_persistence),
):
    """List team executions with optional filters."""
    mission_uuid = UUID(mission_id) if mission_id else None
    executions = await persistence.list_executions(mission_uuid, status, limit)

    return [
        TeamExecutionResponse(
            id=str(e.id),
            mission_id=str(e.mission_id),
            node_id=str(e.node_id),
            execution_id=e.execution_id,
            team_id=str(e.team_id),
            status=e.status.value,
            current_round=e.current_round,
            max_rounds=e.max_rounds,
            final_confidence=e.final_confidence,
            decision_outcome=e.decision_outcome.value if e.decision_outcome else None,
            started_at=e.started_at,
            completed_at=e.completed_at,
            message_count=0,  # Would need to query separately
            duration_seconds=None,
        )
        for e in executions
    ]


@router.get("/executions/{execution_id}", response_model=TeamExecutionResponse)
async def get_execution(
    execution_id: str,
    persistence: TeamPersistence = Depends(get_persistence),
):
    """Get a specific team execution."""
    try:
        execution = await persistence.get_execution(UUID(execution_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid execution ID")

    if not execution:
        raise HTTPException(status_code=404, detail=f"Execution not found: {execution_id}")

    return TeamExecutionResponse(
        id=str(execution.id),
        mission_id=str(execution.mission_id),
        node_id=str(execution.node_id),
        execution_id=execution.execution_id,
        team_id=str(execution.team_id),
        status=execution.status.value,
        current_round=execution.current_round,
        max_rounds=execution.max_rounds,
        final_confidence=execution.final_confidence,
        decision_outcome=execution.decision_outcome.value if execution.decision_outcome else None,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        message_count=0,
        duration_seconds=None,
    )


@router.get("/executions/{execution_id}/messages", response_model=List[TeamMessageResponse])
async def get_execution_messages(
    execution_id: str,
    round_number: Optional[int] = Query(None),
    persistence: TeamPersistence = Depends(get_persistence),
):
    """Get messages for a team execution."""
    try:
        messages = await persistence.get_messages(UUID(execution_id), round_number)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid execution ID")

    return [
        TeamMessageResponse(
            id=str(m.id),
            team_execution_id=str(m.team_execution_id),
            round_number=m.round_number,
            sender_role=m.sender_role.value,
            receiver_role=m.receiver_role.value,
            message_type=m.message_type.value,
            content=m.content,
            text_content=m.text_content,
            confidence=m.confidence,
            created_at=m.created_at,
        )
        for m in messages
    ]


@router.get("/executions/{execution_id}/decision", response_model=TeamDecisionResponse)
async def get_execution_decision(
    execution_id: str,
    persistence: TeamPersistence = Depends(get_persistence),
):
    """Get the final decision for a team execution."""
    try:
        decision = await persistence.get_decision(UUID(execution_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid execution ID")

    if not decision:
        raise HTTPException(status_code=404, detail=f"Decision not found: {execution_id}")

    return TeamDecisionResponse(
        id=str(decision.id),
        team_execution_id=str(decision.team_execution_id),
        final_output=decision.final_output,
        text_output=decision.text_output,
        decision_policy=decision.decision_policy,
        approval_summary=decision.approval_summary,
        dissent_summary=decision.dissent_summary,
        validator_status=decision.validator_status.value,
        validator_notes=decision.validator_notes,
        confidence_score=decision.confidence_score,
        confidence_breakdown=decision.confidence_breakdown,
        revision_count=decision.revision_count,
        escalation_count=decision.escalation_count,
        created_at=decision.created_at,
    )


# ============================================================================
# Mission Integration
# ============================================================================

@router.post("/missions/{mission_id}/nodes/{node_id}/run-team")
async def run_team_node(
    mission_id: str,
    node_id: str,
    request: ExecuteTeamNodeRequest,
    supabase=Depends(get_supabase),
):
    """
    Execute a mission node using an agent team.

    This endpoint initiates team execution and returns the result.
    For long-running executions, consider using the execution_id
    to poll for status.
    """
    result = await execute_team_node(
        supabase=supabase,
        mission_id=mission_id,
        node_id=node_id,
        team_id=request.team_id,
        objective=request.objective,
        constraints=request.constraints,
        prior_outputs=request.prior_outputs,
        workspace_id=request.workspace_id,
    )

    return {
        "team_execution_id": str(result.team_execution_id),
        "final_output": result.final_output,
        "text_output": result.text_output,
        "confidence_score": result.confidence_score,
        "validator_status": result.validator_status.value,
        "decision_policy": result.decision_policy,
        "has_dissent": result.dissent_summary.get("has_dissent", False),
        "dissenting_roles": result.dissent_summary.get("dissenting_roles", []),
    }


@router.get("/missions/{mission_id}/team-executions", response_model=List[TeamExecutionResponse])
async def get_mission_team_executions(
    mission_id: str,
    persistence: TeamPersistence = Depends(get_persistence),
):
    """Get all team executions for a mission."""
    try:
        executions = await persistence.list_executions(UUID(mission_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid mission ID")

    return [
        TeamExecutionResponse(
            id=str(e.id),
            mission_id=str(e.mission_id),
            node_id=str(e.node_id),
            execution_id=e.execution_id,
            team_id=str(e.team_id),
            status=e.status.value,
            current_round=e.current_round,
            max_rounds=e.max_rounds,
            final_confidence=e.final_confidence,
            decision_outcome=e.decision_outcome.value if e.decision_outcome else None,
            started_at=e.started_at,
            completed_at=e.completed_at,
            message_count=0,
            duration_seconds=None,
        )
        for e in executions
    ]


# ============================================================================
# Server-Sent Events for Live Updates
# ============================================================================

async def team_event_streamer(
    execution_id: str,
    persistence: TeamPersistence = Depends(get_persistence),
):
    """Stream team execution events via SSE."""
    import json
    from datetime import datetime

    execution_uuid = UUID(execution_id)

    while True:
        # Check execution status
        execution = await persistence.get_execution(execution_uuid)
        if not execution:
            yield f"event: error\ndata: {{'message': 'Execution not found'}}\n\n"
            break

        # Send status update
        status_data = {
            "execution_id": execution_id,
            "status": execution.status.value,
            "current_round": execution.current_round,
            "max_rounds": execution.max_rounds,
            "final_confidence": execution.final_confidence,
            "timestamp": datetime.utcnow().isoformat(),
        }
        yield f"event: status\ndata: {json.dumps(status_data)}\n\n"

        # If completed, send final state and close
        if execution.status in (TeamExecutionStatus.COMPLETED, TeamExecutionStatus.FAILED, TeamExecutionStatus.BLOCKED):
            decision = await persistence.get_decision(execution_uuid)
            if decision:
                decision_data = {
                    "execution_id": execution_id,
                    "final_output": decision.final_output,
                    "text_output": decision.text_output,
                    "confidence_score": decision.confidence_score,
                    "validator_status": decision.validator_status.value,
                    "has_dissent": decision.dissent_summary.get("has_dissent", False),
                }
                yield f"event: complete\ndata: {json.dumps(decision_data)}\n\n"
            break

        # Wait before next poll
        await asyncio.sleep(1)


@router.get("/executions/{execution_id}/events/stream")
async def stream_team_events(
    execution_id: str,
    persistence: TeamPersistence = Depends(get_persistence),
):
    """Stream team execution events via Server-Sent Events."""
    return StreamingResponse(
        team_event_streamer(execution_id, persistence),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
