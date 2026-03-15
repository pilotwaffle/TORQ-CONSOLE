"""TORQ Layer 15 - API Router

This module provides the minimal API surface for Layer 15 strategic foresight.
"""

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..models import DecisionPacket, StrategicForesightResult
from ..services import StrategicForesightService


# =============================================================================
# API MODELS
# =============================================================================


class ForesightEvaluateRequest(BaseModel):
    """Request model for foresight evaluation."""
    decision_id: str
    mission_id: str | None = None
    economic_result: dict
    legitimacy_result: dict
    economic_priority_score: float
    legitimacy_score: float
    execution_authorized: bool
    estimated_cost: float
    budget_remaining: float
    action_type: str
    action_description: str
    proposing_agent_id: str
    target_resources: list[str] = []
    mission_horizon: Literal["short", "medium", "long"] = "medium"
    is_governance_change: bool = False
    is_budget_change: bool = False
    foresight_candidate: bool = True


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str


# =============================================================================
# API ROUTER
# =============================================================================


router = APIRouter(
    prefix="/api/l15",
    tags=["foresight"],
)

# Service singleton
_foresight_service: StrategicForesightService | None = None


def get_foresight_service() -> StrategicForesightService:
    """Get the foresight service instance."""
    global _foresight_service
    if _foresight_service is None:
        _foresight_service = StrategicForesightService()
    return _foresight_service


@router.post("/foresight/evaluate", response_model=StrategicForesightResult)
async def evaluate_foresight(request: ForesightEvaluateRequest) -> StrategicForesightResult:
    """Evaluate a decision through strategic foresight.

    Args:
        request: Foresight evaluation request

    Returns:
        StrategicForesightResult with strategic assessment
    """
    service = get_foresight_service()

    # Convert request to DecisionPacket
    packet = DecisionPacket(**request.model_dump())

    # Evaluate through foresight service
    result = await service.evaluate_decision(packet)

    return result


@router.get("/foresight/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint for the foresight service.

    Returns:
        Health status
    """
    return HealthResponse(
        status="healthy",
        service="strategic_foresight",
        version="0.15.0-planning",
    )


# =============================================================================
# OPTIONAL ENDPOINTS (can be added later)
# =============================================================================

@router.post("/foresight/project")
async def project_scenarios(request: ForesightEvaluateRequest):
    """Project scenarios for a decision.

    Optional endpoint for scenario-only evaluation.
    Can be added in v2 if needed.
    """
    raise HTTPException(status_code=501, detail="Not implemented - use /evaluate endpoint")


@router.post("/foresight/compare")
async def compare_branches(request: ForesightEvaluateRequest):
    """Compare strategic branches.

    Optional endpoint for branch comparison only.
    Can be added in v2 if needed.
    """
    raise HTTPException(status_code=501, detail="Not implemented - use /evaluate endpoint")


@router.post("/foresight/optionality")
async def assess_optionality(request: ForesightEvaluateRequest):
    """Assess optionality of a decision.

    Optional endpoint for optionality assessment only.
    Can be added in v2 if needed.
    """
    raise HTTPException(status_code=501, detail="Not implemented - use /evaluate endpoint")


@router.post("/foresight/alignment")
async def assess_alignment(request: ForesightEvaluateRequest):
    """Assess horizon alignment of a decision.

    Optional endpoint for horizon alignment only.
    Can be added in v2 if needed.
    """
    raise HTTPException(status_code=501, detail="Not implemented - use /evaluate endpoint")


__all__ = ["router"]
