"""
Evaluation Engine - API

FastAPI endpoints for execution evaluation.
"""

from __future__ import annotations

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from .models import (
    EvaluatorType,
    ExecutionEvaluationCreate,
    ExecutionEvaluationResponse,
)
from .service import EvaluationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/executions", tags=["evaluation"])


def get_evaluation_service() -> EvaluationService:
    """Get evaluation service instance."""
    from ..dependencies import get_supabase_client, get_optional_llm_client

    supabase = get_supabase_client()
    llm_client = get_optional_llm_client()
    return EvaluationService(supabase, llm_client)


@router.post("/{execution_id}/evaluate", response_model=ExecutionEvaluationResponse)
async def evaluate_execution(
    execution_id: str,
    evaluator_type: EvaluatorType = EvaluatorType.HYBRID,
    service: EvaluationService = Depends(get_evaluation_service),
):
    """
    Evaluate a completed execution.

    Scores execution quality across multiple dimensions.
    """
    # Fetch execution data
    from ..dependencies import get_supabase_client
    supabase = get_supabase_client()

    # Get execution details
    exec_result = supabase.table("task_executions").select("*").eq(
        "execution_id", execution_id
    ).execute()

    if not exec_result.data:
        raise HTTPException(status_code=404, detail="Execution not found")

    execution = exec_result.data[0]

    # Get workspace entries if workspace_id exists
    workspace_id = execution.get("workspace_id")
    grouped_entries = {}

    if workspace_id:
        from ..workspace.service import WorkspaceService
        workspace_service = WorkspaceService(supabase)
        grouped = await workspace_service.list_entries_grouped(workspace_id)
        grouped_entries = grouped.model_dump()

    # Build evaluation request
    request = ExecutionEvaluationCreate(
        execution_id=execution_id,
        workspace_id=workspace_id,
        evaluator_type=evaluator_type,
    )

    # Evaluate
    return await service.evaluate_execution(
        request,
        execution_data=execution,
        grouped_entries=grouped_entries,
    )


@router.get("/{execution_id}/evaluation", response_model=ExecutionEvaluationResponse)
async def get_evaluation(
    execution_id: str,
    service: EvaluationService = Depends(get_evaluation_service),
):
    """Get the latest evaluation for an execution."""
    from ..dependencies import get_supabase_client
    supabase = get_supabase_client()

    result = supabase.table("execution_evaluations").select("*").eq(
        "execution_id", execution_id
    ).order("created_at", desc=True).limit(1).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    evaluation = result.data[0]
    return ExecutionEvaluationResponse(
        evaluation_id=evaluation["id"],
        execution_id=evaluation["execution_id"],
        workspace_id=evaluation.get("workspace_id"),
        overall_score=evaluation["overall_score"],
        reasoning_score=evaluation["reasoning_score"],
        outcome_score=evaluation["outcome_score"],
        risk_score=evaluation["risk_score"],
        coherence_score=evaluation["coherence_score"],
        actionability_score=evaluation["actionability_score"],
        metrics=evaluation.get("metrics", {}),
        evaluator_type=evaluation["evaluator_type"],
        evaluation_content=evaluation.get("evaluation_content", {}),
        created_at=evaluation["created_at"],
    )


@router.get("/{execution_id}/evaluations")
async def list_evaluations(
    execution_id: str,
    service: EvaluationService = Depends(get_evaluation_service),
):
    """List all evaluations for an execution."""
    from ..dependencies import get_supabase_client
    supabase = get_supabase_client()

    result = supabase.table("execution_evaluations").select("*").eq(
        "execution_id", execution_id
    ).order("created_at", desc=True).execute()

    return result.data
