"""
Behavior Experiment API

FastAPI endpoints for the Experiment & Versioning Layer.
Manages experiments, assignments, analysis, and promotion/rollback.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends, Body

from .service import BehaviorExperimentService
from .models import (
    BehaviorVersionCreate,
    BehaviorVersionRead,
    BehaviorExperimentCreate,
    BehaviorExperimentRead,
    ExperimentStatus,
    AssignmentRequest,
    AssignmentResponse,
    ExperimentImpactSummary,
    PromotionDecision,
    RollbackDecision,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/experiments", tags=["behavior-experiments"])


# ============================================================================
# Dependencies
# ============================================================================

def get_experiment_service() -> BehaviorExperimentService:
    """Get experiment service instance."""
    from ..dependencies import get_supabase_client
    supabase = get_supabase_client()
    return BehaviorExperimentService(supabase)


# ============================================================================
# Behavior Version Endpoints
# ============================================================================

@router.post("/versions", response_model=BehaviorVersionRead)
async def create_behavior_version(
    version: BehaviorVersionCreate,
    service: BehaviorExperimentService = Depends(get_experiment_service),
):
    """Create a new behavior version."""
    result = await service.create_behavior_version(version)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create behavior version")
    return result


@router.get("/versions/{version_id}", response_model=BehaviorVersionRead)
async def get_behavior_version(
    version_id: str,
    service: BehaviorExperimentService = Depends(get_experiment_service),
):
    """Get a behavior version by ID."""
    result = await service.get_behavior_version(version_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Version {version_id} not found")
    return result


@router.get("/versions/active")
async def get_active_behavior_version(
    asset_type: str = Query(..., description="Asset type"),
    asset_key: str = Query(..., description="Asset key"),
    service: BehaviorExperimentService = Depends(get_experiment_service),
):
    """Get the currently active version for an asset."""
    result = await service.get_active_version(asset_type, asset_key)
    if not result:
        raise HTTPException(status_code=404, detail=f"No active version for {asset_type}:{asset_key}")
    return result


# ============================================================================
# Experiment Endpoints
# ============================================================================

@router.post("", response_model=BehaviorExperimentRead)
async def create_experiment(
    experiment: BehaviorExperimentCreate,
    service: BehaviorExperimentService = Depends(get_experiment_service),
):
    """Create a new experiment from an approved proposal."""
    result = await service.create_experiment(experiment)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create experiment (may have overlapping experiment)")
    return result


@router.post("/from-proposal/{proposal_id}", response_model=BehaviorExperimentRead)
async def create_experiment_from_proposal(
    proposal_id: str,
    hypothesis: Optional[str] = Body(None),
    service: BehaviorExperimentService = Depends(get_experiment_service),
):
    """
    Create an experiment from an approved adaptation proposal.

    This is the main integration point with the Adaptation Policy Engine.
    Automatically creates the candidate version and sets up the experiment.
    """
    result = await service.create_experiment_from_proposal(proposal_id, hypothesis)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create experiment from proposal")
    return result


@router.get("", response_model=List[BehaviorExperimentRead])
async def list_experiments(
    asset_key: Optional[str] = Query(None),
    status: Optional[ExperimentStatus] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    service: BehaviorExperimentService = Depends(get_experiment_service),
):
    """List experiments with optional filters."""
    return await service.list_experiments(asset_key=asset_key, status=status, limit=limit)


@router.get("/running", response_model=List[BehaviorExperimentRead])
async def get_running_experiments(
    service: BehaviorExperimentService = Depends(get_experiment_service),
):
    """Get all currently running experiments."""
    return await service.list_experiments(status=ExperimentStatus.RUNNING)


@router.get("/{experiment_id}", response_model=BehaviorExperimentRead)
async def get_experiment(
    experiment_id: str,
    service: BehaviorExperimentService = Depends(get_experiment_service),
):
    """Get experiment details."""
    result = await service.get_experiment(experiment_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Experiment {experiment_id} not found")
    return result


@router.post("/{experiment_id}/start", response_model=BehaviorExperimentRead)
async def start_experiment(
    experiment_id: str,
    service: BehaviorExperimentService = Depends(get_experiment_service),
):
    """Start an experiment, beginning traffic assignment."""
    result = await service.start_experiment(experiment_id)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to start experiment")
    return result


@router.post("/{experiment_id}/pause")
async def pause_experiment(
    experiment_id: str,
    service: BehaviorExperimentService = Depends(get_experiment_service),
):
    """Pause an experiment (stops new assignments)."""
    # For now, just update status
    from ..dependencies import get_supabase_client
    supabase = get_supabase_client()

    result = supabase.table("behavior_experiments").update({
        "status": "paused"
    }).eq("id", experiment_id).execute()

    if result.data:
        return {"success": True, "message": "Experiment paused"}

    raise HTTPException(status_code=400, detail="Failed to pause experiment")


# ============================================================================
# Assignment Endpoints
# ========================================================================

@router.post("/assign", response_model=AssignmentResponse)
async def assign_execution(
    request: AssignmentRequest,
    service: BehaviorExperimentService = Depends(get_experiment_service),
):
    """
    Determine which variant an execution should receive.

    This is called at execution start to determine behavior.
    Assignment is deterministic and recorded for traceability.
    """
    result = await service.assign_execution(request)
    if not result:
        raise HTTPException(status_code=400, detail="Assignment failed")

    return result


# ============================================================================
# Analysis Endpoints
# ========================================================================

@router.get("/{experiment_id}/results", response_model=ExperimentImpactSummary)
async def get_experiment_results(
    experiment_id: str,
    service: BehaviorExperimentService = Depends(get_experiment_service),
):
    """Get impact summary and analysis for an experiment."""
    result = await service.analyze_experiment(experiment_id)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to analyze experiment")

    return result


@router.get("/{experiment_id}/assignments")
async def get_experiment_assignments(
    experiment_id: str,
    variant: Optional[str] = Query(None, description="Filter by variant"),
    service: BehaviorExperimentService = Depends(get_experiment_service),
):
    """Get assignment records for an experiment."""
    from ..dependencies import get_supabase_client
    supabase = get_supabase_client()

    query = supabase.table("experiment_assignments").select("*").eq("experiment_id", experiment_id)

    if variant:
        query = query.eq("assigned_variant", variant)

    query = query.order("created_at", desc=True).limit(1000)

    result = query.execute()
    return result.data or []


# ============================================================================
# Promotion and Rollback Endpoints
# ========================================================================

@router.post("/{experiment_id}/promote")
async def promote_experiment(
    experiment_id: str,
    promoted_by: str = Body(..., embed=True),
    promotion_reason: Optional[str] = Body(None, embed=True),
    service: BehaviorExperimentService = Depends(get_experiment_service),
):
    """
    Promote the candidate version to production.

    Sets candidate as active, archives control.
    """
    # First analyze to get current state
    analysis = await service.analyze_experiment(experiment_id)

    decision = PromotionDecision(
        experiment_id=experiment_id,
        promoted_by=promoted_by,
        promotion_reason=promotion_reason or (analysis.promotion_reason if analysis else "Manual promotion"),
        metrics_summary=analysis.model_dump() if analysis else {}
    )

    success = await service.promote_experiment(decision)

    if not success:
        raise HTTPException(status_code=400, detail="Failed to promote experiment")

    return {
        "success": True,
        "message": "Candidate version promoted to active",
        "experiment_id": experiment_id
    }


@router.post("/{experiment_id}/rollback")
async def rollback_experiment(
    experiment_id: str,
    rolled_back_by: str = Body(..., embed=True),
    rollback_reason: Optional[str] = Body(None, embed=True),
    immediate: bool = Body(True, embed=True),
    service: BehaviorExperimentService = Depends(get_experiment_service),
):
    """
    Rollback an experiment.

    Ensures control version is active.
    """
    # First analyze to get current state
    analysis = await service.analyze_experiment(experiment_id)

    decision = RollbackDecision(
        experiment_id=experiment_id,
        rolled_back_by=rolled_back_by,
        rollback_reason=rollback_reason or (analysis.rollback_reason if analysis else "Manual rollback"),
        immediate=immediate,
        metrics_summary=analysis.model_dump() if analysis else {}
    )

    success = await service.rollback_experiment(decision)

    if not success:
        raise HTTPException(status_code=400, detail="Failed to rollback experiment")

    return {
        "success": True,
        "message": "Experiment rolled back, control version active",
        "experiment_id": experiment_id
    }


# ============================================================================
# Statistics Endpoints
# ========================================================================

@router.get("/stats")
async def get_experiment_stats(
    service: BehaviorExperimentService = Depends(get_experiment_service),
):
    """Get statistics about experiments."""
    all_experiments = await service.list_experiments(limit=1000)

    by_status = {}
    for exp in all_experiments:
        status = exp.status.value
        by_status[status] = by_status.get(status, 0) + 1

    running = [e for e in all_experiments if e.status == ExperimentStatus.RUNNING]

    return {
        "total_experiments": len(all_experiments),
        "by_status": by_status,
        "currently_running": len(running),
        "running_experiments": [
            {"id": e.id, "asset_key": e.asset_key, "created_at": e.created_at}
            for e in running
        ]
    }
