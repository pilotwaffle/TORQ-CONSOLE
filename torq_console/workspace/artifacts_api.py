"""
Workspace Artifacts API - Phase 5.3 Milestone 4

FastAPI router for artifact retrieval and inspection.

This provides the read layer for workspace artifacts.
"""

from __future__ import annotations

from typing import List, Optional, Union
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from .artifact_models import ArtifactType, WorkspaceArtifactListParams
from .artifact_persistence import WorkspaceArtifactPersistence
from .artifact_read_service import WorkspaceArtifactReadService, get_artifact_read_service
from .artifact_view_models import (
    ArtifactDetailViewModel,
    ArtifactListResponse,
    TraceabilityChainViewModel,
    TraceabilityViewModel,
)
from ..dependencies import get_supabase_client


router = APIRouter(prefix="/workspaces/artifacts", tags=["workspace-artifacts"])


# ============================================================================
# Dependencies
# ============================================================================

def get_artifact_persistence():
    """Get artifact persistence instance."""
    from .artifact_persistence import WorkspaceArtifactPersistence
    return WorkspaceArtifactPersistence(get_supabase_client())


def get_read_service(
    persistence: WorkspaceArtifactPersistence = Depends(get_artifact_persistence),
) -> WorkspaceArtifactReadService:
    """Get artifact read service instance."""
    return get_artifact_read_service(persistence)


# ============================================================================
# Request/Response Models
# ============================================================================

class ArtifactListFilters(BaseModel):
    """Filters for artifact list query."""

    workspace_id: Optional[str] = Field(None, description="Filter by workspace ID")
    execution_id: Optional[str] = Field(None, description="Filter by execution ID")
    mission_id: Optional[UUID] = Field(None, description="Filter by mission ID")
    node_id: Optional[UUID] = Field(None, description="Filter by node ID")
    team_execution_id: Optional[UUID] = Field(None, description="Filter by team execution ID")
    artifact_type: Optional[ArtifactType] = Field(None, description="Filter by artifact type")
    role_name: Optional[str] = Field(None, description="Filter by role name")
    round_number: Optional[int] = Field(None, description="Filter by round number")
    tool_name: Optional[str] = Field(None, description="Filter by tool name")


class ArtifactListQuery(BaseModel):
    """Query parameters for artifact list."""

    filters: Optional[ArtifactListFilters] = Field(None, description="Filters to apply")
    limit: int = Field(50, ge=1, le=100, description="Page size")
    offset: int = Field(0, ge=0, description="Page offset")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")


# ============================================================================
# Endpoints
# ============================================================================

@router.get("", response_model=ArtifactListResponse)
async def list_artifacts(
    workspace_id: Optional[str] = Query(None, description="Filter by workspace ID"),
    execution_id: Optional[str] = Query(None, description="Filter by execution ID"),
    mission_id: Optional[UUID] = Query(None, description="Filter by mission ID"),
    node_id: Optional[UUID] = Query(None, description="Filter by node ID"),
    team_execution_id: Optional[UUID] = Query(None, description="Filter by team execution ID"),
    artifact_type: Optional[ArtifactType] = Query(None, description="Filter by artifact type"),
    role_name: Optional[str] = Query(None, description="Filter by role name"),
    round_number: Optional[int] = Query(None, description="Filter by round number"),
    tool_name: Optional[str] = Query(None, description="Filter by tool name"),
    limit: int = Query(50, ge=1, le=100, description="Page size"),
    offset: int = Query(0, ge=0, description="Page offset"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    read_service: WorkspaceArtifactReadService = Depends(get_read_service),
):
    """
    List workspace artifacts with filtering and pagination.

    Supports filtering by:
    - workspace_id (most common)
    - execution_id (all artifacts for an execution)
    - mission_id (all artifacts for a mission)
    - node_id (all artifacts for a node)
    - team_execution_id (all artifacts for a team execution)
    - artifact_type (filter by type)
    - role_name (filter by role)
    - round_number (filter by round)
    - tool_name (filter by tool)

    Returns paginated results with total count.
    """
    # Build params from query parameters
    params = WorkspaceArtifactListParams(
        workspace_id=workspace_id,
        execution_id=execution_id,
        mission_id=mission_id,
        node_id=node_id,
        team_execution_id=team_execution_id,
        artifact_type=artifact_type,
        tool_name=tool_name,
        limit=limit,
        offset=offset,
        order_by=sort_by,
        order_desc=(sort_order == "desc"),
    )

    # Get paginated results
    result = await read_service.list_artifacts_paginated(params)

    # Apply role_name and round_number filters (post-query for team-specific filters)
    artifacts = result["artifacts"]
    if role_name is not None:
        artifacts = [a for a in artifacts if a.role_name == role_name]
    if round_number is not None:
        artifacts = [a for a in artifacts if a.round_number == round_number]

    # Create response
    return ArtifactListResponse.create(
        artifacts=artifacts,
        total_count=result["total_count"],
        limit=limit,
        offset=offset,
    )


@router.get("/by-workspace/{workspace_id}", response_model=ArtifactListResponse)
async def list_artifacts_by_workspace(
    workspace_id: str,
    artifact_type: Optional[ArtifactType] = Query(None, description="Filter by artifact type"),
    limit: int = Query(50, ge=1, le=100, description="Page size"),
    offset: int = Query(0, ge=0, description="Page offset"),
    read_service: WorkspaceArtifactReadService = Depends(get_read_service),
):
    """
    List artifacts for a specific workspace.

    This is the most common query path for artifact inspection.
    """
    artifacts = await read_service.list_by_workspace(
        workspace_id=workspace_id,
        limit=limit,
        offset=offset,
        artifact_type=artifact_type,
    )

    # Get total count
    params = WorkspaceArtifactListParams(
        workspace_id=workspace_id,
        artifact_type=artifact_type,
        limit=limit,
        offset=offset,
    )
    total_count = await read_service.count_artifacts(params)

    return ArtifactListResponse.create(
        artifacts=artifacts,
        total_count=total_count,
        limit=limit,
        offset=offset,
    )


@router.get("/by-execution/{execution_id}", response_model=List[TraceabilityViewModel])
async def list_artifacts_by_execution(
    execution_id: str,
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    read_service: WorkspaceArtifactReadService = Depends(get_read_service),
):
    """
    List all artifacts for a specific execution.

    Shows all tool outputs, role outputs, and decisions for an execution.
    """
    return await read_service.list_by_execution(
        execution_id=execution_id,
        limit=limit,
        offset=offset,
    )


@router.get("/by-mission/{mission_id}", response_model=List[TraceabilityViewModel])
async def list_artifacts_by_mission(
    mission_id: UUID,
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    read_service: WorkspaceArtifactReadService = Depends(get_read_service),
):
    """
    List all artifacts for a specific mission.

    Shows all artifacts across all executions of a mission.
    """
    return await read_service.list_by_mission(
        mission_id=mission_id,
        limit=limit,
        offset=offset,
    )


@router.get("/by-node/{node_id}", response_model=List[TraceabilityViewModel])
async def list_artifacts_by_node(
    node_id: UUID,
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    read_service: WorkspaceArtifactReadService = Depends(get_read_service),
):
    """
    List all artifacts for a specific node.

    Shows all artifacts produced by a specific node.
    """
    return await read_service.list_by_node(
        node_id=node_id,
        limit=limit,
        offset=offset,
    )


@router.get("/by-team/{team_execution_id}", response_model=List[TraceabilityViewModel])
async def list_artifacts_by_team(
    team_execution_id: UUID,
    round_number: Optional[int] = Query(None, description="Filter by round number"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    read_service: WorkspaceArtifactReadService = Depends(get_read_service),
):
    """
    List all artifacts for a specific team execution.

    Shows all role outputs and decisions for a team execution.
    Can optionally filter by round number.
    """
    return await read_service.list_by_team_execution(
        team_execution_id=team_execution_id,
        limit=limit,
        offset=offset,
        round_number=round_number,
    )


@router.get("/by-type/{artifact_type}", response_model=List[TraceabilityViewModel])
async def list_artifacts_by_type(
    artifact_type: ArtifactType,
    workspace_id: Optional[str] = Query(None, description="Filter by workspace ID"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    read_service: WorkspaceArtifactReadService = Depends(get_read_service),
):
    """
    List all artifacts of a specific type.

    Can optionally filter by workspace.
    """
    return await read_service.list_by_type(
        artifact_type=artifact_type,
        workspace_id=workspace_id,
        limit=limit,
        offset=offset,
    )


@router.get("/{artifact_id}", response_model=ArtifactDetailViewModel)
async def get_artifact_detail(
    artifact_id: UUID,
    read_service: WorkspaceArtifactReadService = Depends(get_read_service),
):
    """
    Get full artifact detail including traceability chain.

    Returns complete artifact content, execution metadata,
    and the full traceability chain from workspace to artifact.
    """
    artifact = await read_service.get_artifact_detail(artifact_id)
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact {artifact_id} not found",
        )
    return artifact


@router.get("/{artifact_id}/traceability", response_model=TraceabilityChainViewModel)
async def get_artifact_traceability(
    artifact_id: UUID,
    read_service: WorkspaceArtifactReadService = Depends(get_read_service),
):
    """
    Get traceability chain for an artifact.

    Returns the full chain: workspace -> mission -> node -> execution -> team -> role -> artifact
    """
    artifact = await read_service.get_artifact_detail(artifact_id)
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact {artifact_id} not found",
        )
    return artifact.traceability
