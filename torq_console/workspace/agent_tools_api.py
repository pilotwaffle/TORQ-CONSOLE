"""
Agent Workspace Tools API

FastAPI endpoints for agents to interact with the Shared Cognitive Workspace.
These endpoints are designed to be called by agents during execution.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from .service import WorkspaceService
from .models import WorkspaceEntryCreate, WorkspaceEntryType
from .tools import (
    WorkspaceWriteFactRequest,
    WorkspaceWriteHypothesisRequest,
    WorkspaceWriteQuestionRequest,
    WorkspaceWriteDecisionRequest,
    WorkspaceWriteNoteRequest,
    WorkspaceAttachArtifactRequest,
    WorkspaceReadContextRequest,
    WorkspaceGetSummaryRequest,
    EntryImportance,
    EntrySourceType,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/workspaces/{workspace_id}/agent", tags=["agent-workspace-tools"])


def get_workspace_service() -> WorkspaceService:
    """Get workspace service instance."""
    from ..dependencies import get_supabase_client
    from ..dependencies import get_optional_llm_client

    supabase = get_supabase_client()
    llm_client = get_optional_llm_client()
    return WorkspaceService(supabase, llm_client)


@router.post("/fact")
async def write_fact(
    workspace_id: str,
    request: WorkspaceWriteFactRequest,
    service: WorkspaceService = Depends(get_workspace_service),
):
    """Write a fact to the workspace."""
    if request.workspace_id != workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id mismatch")

    entry = WorkspaceEntryCreate(
        entry_type=WorkspaceEntryType.FACT,
        content={
            "fact": request.fact,
            "source": request.source,
            **request.metadata,
        },
        source_agent="agent",
        confidence=request.confidence,
        importance=request.importance,
        source_type=request.source_type,
    )

    result = await service.add_entry(workspace_id, entry)
    return {"success": True, "memory_id": result.memory_id}


@router.post("/hypothesis")
async def write_hypothesis(
    workspace_id: str,
    request: WorkspaceWriteHypothesisRequest,
    service: WorkspaceService = Depends(get_workspace_service),
):
    """Write a hypothesis to the workspace."""
    if request.workspace_id != workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id mismatch")

    entry = WorkspaceEntryCreate(
        entry_type=WorkspaceEntryType.HYPOTHESIS,
        content={
            "hypothesis": request.hypothesis,
            "reasoning": request.reasoning,
            **request.metadata,
        },
        source_agent="agent",
        confidence=request.confidence,
        importance=request.importance,
        source_type=request.source_type,
    )

    result = await service.add_entry(workspace_id, entry)
    return {"success": True, "memory_id": result.memory_id}


@router.post("/question")
async def write_question(
    workspace_id: str,
    request: WorkspaceWriteQuestionRequest,
    service: WorkspaceService = Depends(get_workspace_service),
):
    """Write a question to the workspace."""
    if request.workspace_id != workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id mismatch")

    entry = WorkspaceEntryCreate(
        entry_type=WorkspaceEntryType.QUESTION,
        content={
            "question": request.question,
            "priority": request.priority,
            "context": request.context,
            **request.metadata,
        },
        source_agent="agent",
        confidence=0.9,
        importance=request.importance,
        source_type=request.source_type,
    )

    result = await service.add_entry(workspace_id, entry)
    return {"success": True, "memory_id": result.memory_id}


@router.post("/decision")
async def write_decision(
    workspace_id: str,
    request: WorkspaceWriteDecisionRequest,
    service: WorkspaceService = Depends(get_workspace_service),
):
    """Write a decision to the workspace."""
    if request.workspace_id != workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id mismatch")

    entry = WorkspaceEntryCreate(
        entry_type=WorkspaceEntryType.DECISION,
        content={
            "decision": request.decision,
            "rationale": request.rationale,
            "alternatives": request.alternatives,
            **request.metadata,
        },
        source_agent="agent",
        confidence=0.95,
        importance=request.importance,
        source_type=request.source_type,
    )

    result = await service.add_entry(workspace_id, entry)
    return {"success": True, "memory_id": result.memory_id}


@router.post("/note")
async def write_note(
    workspace_id: str,
    request: WorkspaceWriteNoteRequest,
    service: WorkspaceService = Depends(get_workspace_service),
):
    """Write a note to the workspace."""
    if request.workspace_id != workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id mismatch")

    entry = WorkspaceEntryCreate(
        entry_type=WorkspaceEntryType.NOTE,
        content={
            "note": request.note,
            "category": request.category,
            **request.metadata,
        },
        source_agent="agent",
        confidence=0.8,
        importance=request.importance,
        source_type=request.source_type,
    )

    result = await service.add_entry(workspace_id, entry)
    return {"success": True, "memory_id": result.memory_id}


@router.post("/artifact")
async def attach_artifact(
    workspace_id: str,
    request: WorkspaceAttachArtifactRequest,
    service: WorkspaceService = Depends(get_workspace_service),
):
    """Attach an artifact to the workspace."""
    if request.workspace_id != workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id mismatch")

    entry = WorkspaceEntryCreate(
        entry_type=WorkspaceEntryType.ARTIFACT,
        content={
            "artifact_type": request.artifact_type,
            "title": request.title,
            "data": request.content,
            **request.metadata,
        },
        source_agent="agent",
        confidence=0.95,
        importance=request.importance,
        source_type=request.source_type,
    )

    result = await service.add_entry(workspace_id, entry)
    return {"success": True, "memory_id": result.memory_id}


@router.get("/context")
async def read_context(
    workspace_id: str,
    entry_types: Optional[str] = None,
    limit: int = 100,
    service: WorkspaceService = Depends(get_workspace_service),
):
    """Read workspace context for agent awareness."""
    grouped = await service.list_entries_grouped(workspace_id)

    if entry_types:
        types_filter = entry_types.split(",")
        result = {}
        for entry_type in types_filter:
            key = entry_type.rstrip("s")
            if key in ["fact", "hypothesis", "question", "decision", "artifact", "note"]:
                result[key] = grouped.model_dump()[key]
        return result

    return grouped.model_dump()


@router.get("/summary")
async def get_summary(
    workspace_id: str,
    include_counts: bool = True,
    service: WorkspaceService = Depends(get_workspace_service),
):
    """Get workspace summary for agent context."""
    summary = await service.summarize_workspace(workspace_id)

    if include_counts:
        grouped = await service.list_entries_grouped(workspace_id)
        summary.model_dump()["entry_counts"] = {
            "facts": len(grouped.facts),
            "hypotheses": len(grouped.hypotheses),
            "questions": len(grouped.questions),
            "decisions": len(grouped.decisions),
            "artifacts": len(grouped.artifacts),
            "notes": len(grouped.notes),
        }

    return summary.model_dump()


@router.get("/tools")
async def list_agent_tools():
    """List available workspace tools for agents."""
    from .tools import list_available_tools, get_tool_schema

    tools = []
    for tool_name in list_available_tools():
        schema = get_tool_schema(tool_name)
        tools.append({
            "name": tool_name,
            "display_name": schema["name"],
            "description": schema["description"],
            "parameters": schema["parameters"],
        })

    return {"tools": tools}
