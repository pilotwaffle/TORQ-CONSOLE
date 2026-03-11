"""
Learning Signal API

FastAPI endpoints for the Learning Signal Engine.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from .service import LearningSignalService
from .models import (
    LearningSignalCreate,
    LearningSignalRead,
    LearningSignalUpdate,
    ExtractionResult,
    ExtractionContext,
    AggregatedSignal,
    LearningSignalType,
    SignalStrength,
    SignalSource,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/learning", tags=["learning-signals"])


# ============================================================================
# Dependencies
# ============================================================================

def get_learning_service() -> LearningSignalService:
    """Get learning signal service instance."""
    from ..dependencies import get_supabase_client
    from ..dependencies import get_optional_llm_client

    supabase = get_supabase_client()
    llm_client = get_optional_llm_client()
    return LearningSignalService(supabase, llm_client)


# ============================================================================
# Request/Response Models
# ============================================================================

class ExtractSignalsRequest(BaseModel):
    """Request to extract learning signals."""
    agent_id: Optional[str] = Field(None, description="Filter by agent ID")
    workflow_id: Optional[str] = Field(None, description="Filter by workflow ID")
    time_window_hours: int = Field(default=168, description="Lookback window in hours (default 1 week)")
    use_llm_summarization: bool = Field(default=False, description="Use LLM for signal summarization")
    min_execution_count: int = Field(default=3, description="Minimum executions for pattern detection")


class SignalAcknowledgeRequest(BaseModel):
    """Request to acknowledge a signal."""
    notes: Optional[str] = Field(None, description="Optional notes about acknowledgment")


class SignalIncorporateRequest(BaseModel):
    """Request to incorporate a signal into behavior."""
    adaptation_description: str = Field(..., description="Description of the adaptation made")
    adaptation_version: Optional[str] = Field(None, description="Version of the adapted component")


# ============================================================================
# Signal Extraction Endpoints
# ============================================================================

@router.post("/extract", response_model=ExtractionResult)
async def extract_signals(
    request: ExtractSignalsRequest,
    service: LearningSignalService = Depends(get_learning_service),
):
    """
    Extract learning signals from recent executions.

    This runs the two-pass signal extraction process:
    1. Deterministic rules extract explicit patterns
    2. Optional LLM summarization for signal clusters

    Returns the extraction result with detected signals.
    """
    context = ExtractionContext(
        execution_id=None,
        agent_id=request.agent_id,
        workflow_id=request.workflow_id,
        time_window_hours=request.time_window_hours,
        min_execution_count=request.min_execution_count
    )

    try:
        result = await service.extract_signals(
            context=context,
            use_llm_summarization=request.use_llm_summarization
        )
        return result
    except Exception as e:
        logger.error(f"Error extracting signals: {e}")
        raise HTTPException(status_code=500, detail=f"Signal extraction failed: {str(e)}")


@router.get("/signals", response_model=List[LearningSignalRead])
async def list_signals(
    scope_type: Optional[str] = Query(None, description="Filter by scope type"),
    scope_id: Optional[str] = Query(None, description="Filter by scope ID"),
    signal_type: Optional[LearningSignalType] = Query(None, description="Filter by signal type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    service: LearningSignalService = Depends(get_learning_service),
):
    """List learning signals with optional filters."""
    try:
        signals = await service.get_signals(
            scope_type=scope_type,
            scope_id=scope_id,
            signal_type=signal_type,
            status=status,
            limit=limit
        )
        return signals
    except Exception as e:
        logger.error(f"Error listing signals: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list signals: {str(e)}")


@router.get("/signals/{signal_id}", response_model=LearningSignalRead)
async def get_signal(
    signal_id: str,
    service: LearningSignalService = Depends(get_learning_service),
):
    """Get a specific learning signal by ID."""
    signal = await service.get_signal(signal_id)

    if not signal:
        raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")

    return signal


@router.put("/signals/{signal_id}", response_model=LearningSignalRead)
async def update_signal(
    signal_id: str,
    update: LearningSignalUpdate,
    service: LearningSignalService = Depends(get_learning_service),
):
    """Update a learning signal."""
    signal = await service.update_signal(signal_id, update)

    if not signal:
        raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")

    return signal


@router.post("/signals/{signal_id}/acknowledge", response_model=Dict[str, Any])
async def acknowledge_signal(
    signal_id: str,
    request: SignalAcknowledgeRequest,
    service: LearningSignalService = Depends(get_learning_service),
):
    """
    Acknowledge a learning signal.

    Marks the signal as acknowledged but not yet incorporated.
    Use this to indicate that the signal has been reviewed.
    """
    success = await service.acknowledge_signal(signal_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")

    result = {"success": True, "message": "Signal acknowledged"}
    if request.notes:
        # Store notes in metadata
        await service.update_signal(signal_id, LearningSignalUpdate(
            metadata={"acknowledgment_notes": request.notes}
        ))

    return result


@router.post("/signals/{signal_id}/incorporate", response_model=Dict[str, Any])
async def incorporate_signal(
    signal_id: str,
    request: SignalIncorporateRequest,
    service: LearningSignalService = Depends(get_learning_service),
):
    """
    Incorporate a learning signal into behavior.

    Marks the signal as incorporated and records the adaptation made.
    Use this when a signal has been acted upon and behavior has changed.
    """
    success = await service.incorporate_signal(signal_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")

    # Store adaptation details in metadata
    await service.update_signal(signal_id, LearningSignalUpdate(
        metadata={
            "adaptation_description": request.adaptation_description,
            "adaptation_version": request.adaptation_version,
            "incorporated_at": None  # Will use updated_at
        }
    ))

    return {
        "success": True,
        "message": "Signal incorporated",
        "adaptation": request.adaptation_description
    }


@router.post("/signals/{signal_id}/reject", response_model=Dict[str, Any])
async def reject_signal(
    signal_id: str,
    service: LearningSignalService = Depends(get_learning_service),
):
    """
    Reject a learning signal.

    Marks the signal as rejected.
    Use this when a signal is determined to be spurious or not actionable.
    """
    success = await service.reject_signal(signal_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")

    return {"success": True, "message": "Signal rejected"}


# ============================================================================
# Signal Aggregation Endpoints
# ============================================================================

@router.get("/aggregated", response_model=List[AggregatedSignal])
async def get_aggregated_signals(
    scope_type: Optional[str] = Query(None, description="Filter by scope type"),
    scope_id: Optional[str] = Query(None, description="Filter by scope ID"),
    service: LearningSignalService = Depends(get_learning_service),
):
    """
    Get aggregated learning signals.

    Aggregates related signals into higher-level patterns.
    Useful for identifying systemic issues across multiple executions.
    """
    try:
        aggregated = await service.aggregate_signals(
            scope_type=scope_type,
            scope_id=scope_id
        )
        return aggregated
    except Exception as e:
        logger.error(f"Error aggregating signals: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to aggregate signals: {str(e)}")


# ============================================================================
# Signal Types Reference
# ============================================================================

@router.get("/types", response_model=Dict[str, Dict[str, Any]])
async def list_signal_types():
    """
    List available learning signal types with descriptions.

    Returns a reference of all signal types that can be extracted.
    """
    return {
        "prompt_improvement": {
            "prompt_structure_clarity": "Detects unclear prompt structure through low coherence",
            "prompt_missing_context": "Detects missing context through tool failures",
            "prompt_ambiguous_instructions": "Detects ambiguous instruction patterns"
        },
        "routing_adjustment": {
            "routing_misalignment": "Detects when queries go to the wrong agent",
            "routing_missing_capability": "Detects missing capabilities for routing",
            "routing_overspecialization": "Detects when agents are too narrow"
        },
        "tool_preference": {
            "tool_preference_emergent": "Detects tools that consistently work well",
            "tool_avoidance_pattern": "Detects tools that should be avoided",
            "tool_inefficiency": "Detects tools causing problems"
        },
        "reasoning_pattern": {
            "repeated_unresolved_questions": "Detects questions that stay unresolved",
            "repeated_contradiction": "Detects repeated contradictions in reasoning",
            "risk_pattern_critical": "Detects critical risk patterns",
            "coherence_degradation": "Detects declining coherence over time"
        }
    }


@router.get("/stats", response_model=Dict[str, Any])
async def get_signal_stats(
    service: LearningSignalService = Depends(get_learning_service),
):
    """Get statistics about learning signals."""
    try:
        pending = await service.get_signals(status="pending")
        acknowledged = await service.get_signals(status="acknowledged")
        incorporated = await service.get_signals(status="incorporated")

        # Count by type
        by_type = {}
        for signal in pending + acknowledged:
            st = signal.signal_type.value
            by_type[st] = by_type.get(st, 0) + 1

        return {
            "total_pending": len(pending),
            "total_acknowledged": len(acknowledged),
            "total_incorporated": len(incorporated),
            "by_type": by_type,
            "strength_distribution": {
                "conclusive": sum(1 for s in pending if s.strength == SignalStrength.CONCLUSIVE),
                "strong": sum(1 for s in pending if s.strength == SignalStrength.STRONG),
                "moderate": sum(1 for s in pending if s.strength == SignalStrength.MODERATE),
                "weak": sum(1 for s in pending if s.strength == SignalStrength.WEAK)
            }
        }
    except Exception as e:
        logger.error(f"Error getting signal stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")
