from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from .models import (
    WorkspaceCreate,
    WorkspaceEntryCreate,
    WorkspaceEntryUpdate,
    WorkspaceSummaryRequest,
    WorkspaceScopeType,
)
from .service import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


class GetOrCreateWorkspaceRequest(BaseModel):
    """Request to get or create a workspace by scope."""
    scope_type: WorkspaceScopeType = Field(..., description="Type of scope (session, workflow_execution, agent_team)")
    scope_id: str = Field(..., min_length=1, max_length=255, description="Scope identifier")
    title: Optional[str] = Field(None, description="Optional title for new workspace")
    description: Optional[str] = Field(None, description="Optional description for new workspace")
    created_by: Optional[str] = Field(None, description="Optional creator identifier")


def get_workspace_service() -> WorkspaceService:
    from torq_console.dependencies import get_optional_llm_client, get_supabase_client
    return WorkspaceService(get_supabase_client(), get_optional_llm_client())


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_workspace(payload: WorkspaceCreate, service: WorkspaceService = Depends(get_workspace_service)):
    return await service.create_workspace(payload)


@router.post("/get-or-create", status_code=status.HTTP_200_OK)
async def get_or_create_workspace(
    payload: GetOrCreateWorkspaceRequest,
    service: WorkspaceService = Depends(get_workspace_service)
):
    """
    Get or create a workspace by scope.

    This is the primary endpoint for workspace integration. It will:
    1. Return an existing workspace if one matches the scope
    2. Create a new workspace if none exists

    This provides idempotency for workspace creation.
    """
    return await service.get_or_create_workspace(
        scope_type=payload.scope_type.value,
        scope_id=payload.scope_id,
        title=payload.title,
        description=payload.description,
        created_by=payload.created_by
    )


@router.get("/by-scope")
async def get_workspace_by_scope(
    scope_type: WorkspaceScopeType = Query(..., description="Type of scope"),
    scope_id: str = Query(..., description="Scope identifier"),
    service: WorkspaceService = Depends(get_workspace_service)
):
    """
    Get a workspace by scope. Returns 404 if not found.

    Use POST /get-or-create for idempotent get-or-create behavior.
    """
    workspace = await service.get_workspace_by_scope(scope_type.value, scope_id)
    if not workspace:
        raise HTTPException(
            status_code=404,
            detail=f"Workspace not found for scope_type={scope_type.value}, scope_id={scope_id}"
        )
    return workspace


@router.get("/{workspace_id}")
async def get_workspace(workspace_id: str, service: WorkspaceService = Depends(get_workspace_service)):
    workspace = await service.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


@router.get("/{workspace_id}/entries")
async def list_workspace_entries(workspace_id: str, grouped: bool = True, service: WorkspaceService = Depends(get_workspace_service)):
    return await service.list_entries_grouped(workspace_id) if grouped else await service.list_entries(workspace_id)


@router.post("/{workspace_id}/entries", status_code=status.HTTP_201_CREATED)
async def add_workspace_entry(workspace_id: str, payload: WorkspaceEntryCreate, tenant_id: str = "default", service: WorkspaceService = Depends(get_workspace_service)):
    workspace = await service.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return await service.add_entry(workspace_id, payload, tenant_id=tenant_id)


@router.patch("/{workspace_id}/entries/{memory_id}")
async def update_workspace_entry(workspace_id: str, memory_id: str, payload: WorkspaceEntryUpdate, service: WorkspaceService = Depends(get_workspace_service)):
    updated = await service.update_entry(workspace_id, memory_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Workspace entry not found")
    return updated


@router.post("/{workspace_id}/entries/{memory_id}/resolve")
async def resolve_workspace_entry(workspace_id: str, memory_id: str, service: WorkspaceService = Depends(get_workspace_service)):
    resolved = await service.resolve_entry(workspace_id, memory_id)
    if not resolved:
        raise HTTPException(status_code=404, detail="Workspace entry not found")
    return resolved


@router.post("/{workspace_id}/summarize")
async def summarize_workspace(workspace_id: str, payload: WorkspaceSummaryRequest, service: WorkspaceService = Depends(get_workspace_service)):
    workspace = await service.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return await service.summarize_workspace(workspace_id, model=payload.model)
