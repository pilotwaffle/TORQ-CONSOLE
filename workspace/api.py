"""
Shared Cognitive Workspace - API Endpoints

FastAPI routes for workspace and entry management.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from .models import (
    WorkspaceCreate,
    WorkspaceResponse,
    WorkspaceEntryCreate,
    WorkspaceEntryUpdate,
    WorkspaceEntryResponse,
    WorkspaceEntriesResponse,
    WorkspaceResolveRequest,
    WorkspaceScopeType,
    WorkspaceEntryType,
    WorkspaceSummaryResponse,
)
from .service import workspace_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])


# ============================================================================
# Workspace Endpoints
# ============================================================================

@router.post("", response_model=WorkspaceResponse)
async def create_workspace(payload: WorkspaceCreate):
    """
    Create a new workspace.

    Used when:
    - Session begins
    - Workflow execution begins
    - Agent team task begins
    """
    try:
        return await workspace_service.create_workspace(payload)
    except Exception as e:
        logger.error(f"Failed to create workspace: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(workspace_id: str):
    """Get a workspace by ID."""
    workspace = await workspace_service.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


@router.get("/scope/{scope_type}/{scope_id}", response_model=WorkspaceResponse)
async def get_workspace_by_scope(
    scope_type: WorkspaceScopeType,
    scope_id: str
):
    """
    Get or create a workspace by scope.

    This is the primary entry point for most operations.
    """
    workspace = await workspace_service.get_workspace_by_scope(scope_type.value, scope_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


# ============================================================================
# Entry Endpoints
# ============================================================================

@router.post("/{workspace_id}/entries", response_model=WorkspaceEntryResponse)
async def add_entry(
    workspace_id: str,
    entry: WorkspaceEntryCreate
):
    """
    Add an entry to a workspace.

    Agents use this to contribute facts, hypotheses, questions, etc.
    """
    # Verify workspace exists
    workspace = await workspace_service.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    try:
        return await workspace_service.add_entry(workspace_id, entry)
    except Exception as e:
        logger.error(f"Failed to add entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workspace_id}/entries", response_model=WorkspaceEntriesResponse)
async def list_entries(
    workspace_id: str,
    entry_type: Optional[WorkspaceEntryType] = Query(None),
    status: Optional[str] = Query(None)
):
    """
    List all entries in a workspace, grouped by type.

    Query params:
    - entry_type: Filter by entry type
    - status: Filter by status
    """
    # Verify workspace exists
    workspace = await workspace_service.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    return await workspace_service.list_entries(
        workspace_id,
        entry_type,
        status
    )


@router.get("/{workspace_id}/entries/{memory_id}", response_model=WorkspaceEntryResponse)
async def get_entry(
    workspace_id: str,
    memory_id: str
):
    """Get a specific entry."""
    entry = await workspace_service.get_entry(workspace_id, memory_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.patch("/{workspace_id}/entries/{memory_id}", response_model=WorkspaceEntryResponse)
async def update_entry(
    workspace_id: str,
    memory_id: str,
    update: WorkspaceEntryUpdate
):
    """
    Update a workspace entry.

    Used when agents refine hypotheses or revise decisions.
    """
    entry = await workspace_service.update_entry(workspace_id, memory_id, update)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.post("/{workspace_id}/entries/{memory_id}/resolve", response_model=WorkspaceEntryResponse)
async def resolve_question(
    workspace_id: str,
    memory_id: str,
    request: WorkspaceResolveRequest
):
    """
    Resolve a question entry with an answer.

    Marks the question as resolved and stores the resolution.
    """
    entry = await workspace_service.resolve_question(workspace_id, memory_id, request.resolution)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.delete("/{workspace_id}/entries/{memory_id}")
async def delete_entry(
    workspace_id: str,
    memory_id: str
):
    """
    Soft delete an entry.

    Sets deleted_at timestamp instead of removing the row.
    """
    success = await workspace_service.delete_entry(workspace_id, memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"deleted": True}


# ============================================================================
# Summarization
# ============================================================================

class WorkspaceSummaryRequest(BaseModel):
    """Request to summarize workspace state."""
    include_entries: bool = True
    max_entries: int = 50


@router.post("/{workspace_id}/summarize", response_model=WorkspaceSummaryResponse)
async def summarize_workspace(
    workspace_id: str,
    request: WorkspaceSummaryRequest = Depends()
):
    """
    Generate an LLM summary of workspace state.

    Returns:
    - Current understanding
    - Unresolved questions
    - Key decisions
    """
    from datetime import datetime

    # Get entries
    entries = await workspace_service.list_entries(workspace_id)

    # For now, return a basic summary
    # TODO: Integrate with LLM for intelligent summarization

    facts_summary = [f.content.get("claim", str(entry.content)) for entry in entries.facts[:5]]
    questions_list = [entry.content.get("question", str(entry.content)) for entry in entries.questions]
    decisions_list = [entry.content.get("decision", str(entry.content)) for entry in entries.decisions]

    return WorkspaceSummaryResponse(
        workspace_id=workspace_id,
        summary=f"Workspace contains {entries.total} entries across {len([e for e in [entries.facts, entries.hypotheses, entries.questions, entries.decisions, entries.artifacts, entries.notes] if e])} categories.",
        current_understanding=f"Known {len(entries.facts)} facts. {len(entries.hypotheses)} hypotheses being tested.",
        unresolved_questions=questions_list,
        key_decisions=decisions_list,
        generated_at=datetime.now()
    )
