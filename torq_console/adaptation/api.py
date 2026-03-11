"""
Adaptation Proposal API

FastAPI endpoints for the Adaptation Policy Engine.
Manages proposal lifecycle: generate, review, apply, rollback.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends, Body
from pydantic import BaseModel, Field

from .service import AdaptationProposalService
from .models import (
    AdaptationProposalRead,
    ApprovalStatus,
    RiskTier,
    PolicyConfig,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/adaptation", tags=["adaptation-proposals"])


# ============================================================================
# Dependencies
# ============================================================================

def get_adaptation_service() -> AdaptationProposalService:
    """Get adaptation proposal service instance."""
    from ..dependencies import get_supabase_client

    supabase = get_supabase_client()
    return AdaptationProposalService(supabase)


# ============================================================================
# Request/Response Models
# ============================================================================

class GenerateProposalRequest(BaseModel):
    """Request to generate a proposal from a signal."""
    signal_id: str = Field(..., description="Learning signal ID")
    target_scope: Optional[str] = Field(None, description="Override target scope")
    force_create: bool = Field(default=False, description="Bypass policy guardrails")


class ReviewProposalRequest(BaseModel):
    """Request to review a proposal."""
    reviewed_by: str = Field(..., description="Reviewer identifier")
    approved: bool = Field(..., description="True to approve, False to reject")
    review_notes: Optional[str] = Field(None, description="Review notes")
    metrics_baseline: Optional[Dict[str, float]] = Field(None, description="Baseline metrics for comparison")


class ApplyProposalRequest(BaseModel):
    """Request to apply a proposal."""
    applied_by: str = Field(..., description="User/system applying the change")
    force_apply: bool = Field(default=False, description="Bypass policy checks")


class RollbackProposalRequest(BaseModel):
    """Request to rollback a proposal."""
    rolled_back_by: str = Field(..., description="User/system rolling back")
    reason: str = Field(..., description="Reason for rollback")


class BulkGenerateRequest(BaseModel):
    """Request to generate proposals from multiple signals."""
    signal_ids: List[str] = Field(..., description="Learning signal IDs")
    force_create: bool = Field(default=False, description="Bypass policy guardrails")


# ============================================================================
# Proposal Generation Endpoints
# ========================================================================

@router.post("/generate", response_model=AdaptationProposalRead)
async def generate_proposal(
    request: GenerateProposalRequest,
    service: AdaptationProposalService = Depends(get_adaptation_service),
):
    """
    Generate an adaptation proposal from a learning signal.

    The signal is evaluated against policy guardrails:
    - Minimum evidence count
    - Cooldown period
    - Max open proposals
    - Duplicate detection

    If eligible, a proposal is created with appropriate risk tier
    and approval mode.
    """
    # Fetch the signal
    from ..dependencies import get_supabase_client
    supabase = get_supabase_client()

    try:
        result = supabase.table("learning_signals").select("*").eq("signal_id", request.signal_id).limit(1).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail=f"Signal {request.signal_id} not found")
        signal = result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching signal: {str(e)}")

    proposal = await service.generate_proposal_from_signal(
        signal=signal,
        target_scope=request.target_scope,
        force_create=request.force_create
    )

    if not proposal:
        raise HTTPException(
            status_code=400,
            detail="Signal not eligible for proposal or could not be mapped"
        )

    return proposal


@router.post("/generate/bulk", response_model=List[AdaptationProposalRead])
async def generate_proposals_bulk(
    request: BulkGenerateRequest,
    service: AdaptationProposalService = Depends(get_adaptation_service),
):
    """Generate proposals from multiple learning signals."""
    from ..dependencies import get_supabase_client
    supabase = get_supabase_client()

    # Fetch signals
    try:
        result = supabase.table("learning_signals").select("*").in_("signal_id", request.signal_ids).execute()
        signals = result.data if result.data else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching signals: {str(e)}")

    proposals = await service.generate_proposals_from_signals(
        signals=signals,
        force_create=request.force_create
    )

    return proposals


# ============================================================================
# Proposal Query Endpoints
# ========================================================================

@router.get("/proposals", response_model=List[AdaptationProposalRead])
async def list_proposals(
    target_scope: Optional[str] = Query(None, description="Filter by target scope"),
    risk_tier: Optional[RiskTier] = Query(None, description="Filter by risk tier"),
    status: Optional[ApprovalStatus] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    service: AdaptationProposalService = Depends(get_adaptation_service),
):
    """List adaptation proposals with optional filters."""
    try:
        proposals = await service.list_proposals(
            target_scope=target_scope,
            risk_tier=risk_tier,
            status=status,
            limit=limit
        )
        return proposals
    except Exception as e:
        logger.error(f"Error listing proposals: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list proposals: {str(e)}")


@router.get("/proposals/pending", response_model=List[AdaptationProposalRead])
async def get_pending_proposals(
    limit: int = Query(100, ge=1, le=1000),
    service: AdaptationProposalService = Depends(get_adaptation_service),
):
    """Get proposals pending review."""
    proposals = await service.get_pending_proposals(limit=limit)
    return proposals


@router.get("/proposals/approved", response_model=List[AdaptationProposalRead])
async def get_approved_proposals(
    limit: int = Query(100, ge=1, le=1000),
    service: AdaptationProposalService = Depends(get_adaptation_service),
):
    """Get proposals approved but not yet applied."""
    proposals = await service.get_approved_proposals(limit=limit)
    return proposals


@router.get("/proposals/{proposal_id}", response_model=AdaptationProposalRead)
async def get_proposal(
    proposal_id: str,
    service: AdaptationProposalService = Depends(get_adaptation_service),
):
    """Get a specific proposal by ID."""
    proposal = await service.get_proposal(proposal_id)

    if not proposal:
        raise HTTPException(status_code=404, detail=f"Proposal {proposal_id} not found")

    return proposal


# ============================================================================
# Proposal Review Endpoints
# ========================================================================

@router.post("/proposals/{proposal_id}/review", response_model=AdaptationProposalRead)
async def review_proposal(
    proposal_id: str,
    request: ReviewProposalRequest,
    service: AdaptationProposalService = Depends(get_adaptation_service),
):
    """
    Review and approve/reject a proposal.

    Use this endpoint to:
    - Approve Tier 2 (medium risk) proposals
    - Approve Tier 3 (high risk) proposals
    - Reject any proposal
    """
    proposal = await service.review_proposal(
        proposal_id=proposal_id,
        reviewed_by=request.reviewed_by,
        approved=request.approved,
        review_notes=request.review_notes,
        metrics_baseline=request.metrics_baseline
    )

    if not proposal:
        raise HTTPException(status_code=404, detail=f"Proposal {proposal_id} not found")

    return proposal


@router.post("/proposals/{proposal_id}/approve", response_model=AdaptationProposalRead)
async def approve_proposal(
    proposal_id: str,
    reviewed_by: str = Body(..., embed=True),
    review_notes: Optional[str] = Body(None, embed=True),
    service: AdaptationProposalService = Depends(get_adaptation_service),
):
    """Approve a proposal (shortcut for review with approved=True)."""
    return await service.approve_proposal(
        proposal_id=proposal_id,
        reviewed_by=reviewed_by,
        review_notes=review_notes
    )


@router.post("/proposals/{proposal_id}/reject", response_model=AdaptationProposalRead)
async def reject_proposal(
    proposal_id: str,
    reviewed_by: str = Body(..., embed=True),
    review_notes: Optional[str] = Body(None, embed=True),
    service: AdaptationProposalService = Depends(get_adaptation_service),
):
    """Reject a proposal (shortcut for review with approved=False)."""
    return await service.reject_proposal(
        proposal_id=proposal_id,
        reviewed_by=reviewed_by,
        review_notes=review_notes
    )


# ============================================================================
# Proposal Application Endpoints
# ========================================================================

@router.post("/proposals/{proposal_id}/apply")
async def apply_proposal(
    proposal_id: str,
    request: ApplyProposalRequest,
    service: AdaptationProposalService = Depends(get_adaptation_service),
):
    """
    Apply an approved proposal.

    Creates a versioned behavior change and returns rollback instructions.
    Only approved proposals can be applied (unless force_apply=True).
    """
    result = await service.apply_proposal(
        proposal_id=proposal_id,
        applied_by=request.applied_by,
        force_apply=request.force_apply
    )

    if not result:
        raise HTTPException(
            status_code=400,
            detail="Cannot apply proposal (not approved, policy violation, or not found)"
        )

    return result


@router.post("/proposals/{proposal_id}/rollback")
async def rollback_proposal(
    proposal_id: str,
    request: RollbackProposalRequest,
    service: AdaptationProposalService = Depends(get_adaptation_service),
):
    """
    Rollback an applied proposal.

    Restores the previous behavior version.
    Only applied proposals can be rolled back.
    """
    success = await service.rollback_proposal(
        proposal_id=proposal_id,
        rolled_back_by=request.rolled_back_by,
        reason=request.reason
    )

    if not success:
        raise HTTPException(
            status_code=400,
            detail="Cannot rollback proposal (not found or not in APPLIED status)"
        )

    return {"success": True, "message": "Proposal rolled back"}


# ============================================================================
# Policy Configuration Endpoints
# ========================================================================

@router.get("/policy/config", response_model=PolicyConfig)
async def get_policy_config(
    service: AdaptationProposalService = Depends(get_adaptation_service),
):
    """Get current policy configuration."""
    return service.config


@router.put("/policy/config", response_model=PolicyConfig)
async def update_policy_config(
    config: PolicyConfig,
    service: AdaptationProposalService = Depends(get_adaptation_service),
):
    """Update policy configuration (admin only)."""
    # In production, add admin check here
    service.config = config
    return config


# ============================================================================
# Statistics Endpoints
# ========================================================================

@router.get("/stats")
async def get_adaptation_stats(
    service: AdaptationProposalService = Depends(get_adaptation_service),
):
    """Get statistics about adaptation proposals."""
    all_proposals = await service.list_proposals(limit=10000)

    # Count by status
    by_status = {}
    for proposal in all_proposals:
        status = proposal.status.value
        by_status[status] = by_status.get(status, 0) + 1

    # Count by risk tier
    by_risk_tier = {}
    for proposal in all_proposals:
        tier = proposal.risk_tier.value
        by_risk_tier[tier] = by_risk_tier.get(tier, 0) + 1

    # Count by adaptation type
    by_type = {}
    for proposal in all_proposals:
        atype = proposal.adaptation_type.value
        by_type[atype] = by_type.get(atype, 0) + 1

    return {
        "total_proposals": len(all_proposals),
        "by_status": by_status,
        "by_risk_tier": by_risk_tier,
        "by_adaptation_type": by_type,
        "pending_review": by_status.get("pending_review", 0),
        "approved_not_applied": by_status.get("approved", 0),
        "applied": by_status.get("applied", 0),
    }
