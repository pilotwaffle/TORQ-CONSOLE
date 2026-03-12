"""
Memory Inspection & Control API - Phase 4H.1 Milestone 4

REST API for memory inspection, audit, and governance control.

Endpoints:
- GET /api/memory-inspection/{id}/detail - Complete memory record detail
- GET /api/memory-inspection/{id}/traceability - Source chain traceability
- GET /api/memory-inspection/{id}/validation - Validation decision history
- GET /api/memory-inspection/rejections - Rejection log entries
- GET /api/memory-inspection/rejections/{artifact_id}/explain - Explain rejection
- GET /api/memory-inspection/{id}/audit - Retrieval audit records
- GET /api/memory-inspection/{id}/audit-summary - Retrieval summary
- GET /api/memory-inspection/attention - Memories needing governance attention
- GET /api/memory-inspection/statistics - Governance statistics
- POST /api/memory-inspection/control - Execute governance action
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from torq_console.strategic_memory.inspection_service import (
    MemoryInspectionService,
    MemoryRecordDetail,
    MemoryTraceability,
    ValidationDecisionReport,
    RejectionLogEntry,
    RetrievalAuditRecord,
    RetrievalAuditSummary,
    GovernanceAction,
    GovernanceActionResult,
    get_memory_inspection_service,
)

from torq_console.strategic_memory.models import MemoryStatus


logger = logging.getLogger(__name__)


# ============================================================================
# Router
# ============================================================================

router = APIRouter(prefix="/api/memory-inspection", tags=["memory-inspection"])


# ============================================================================
# Dependencies
# ============================================================================

def get_inspection_service() -> MemoryInspectionService:
    """Get the memory inspection service instance."""
    try:
        from torq_console.main import get_supabase_client
        supabase = get_supabase_client()
        return get_memory_inspection_service(supabase_client=supabase)
    except ImportError:
        # Return service without client (will return None/empty results)
        return get_memory_inspection_service(supabase_client=None)


# ============================================================================
# Request/Response Models
# ============================================================================

class GovernanceActionRequest(BaseModel):
    """Request model for governance actions."""
    action_type: str = Field(..., pattern="^(disable|enable|expire|supersede|lock_quality|unlock)$")
    memory_id: str  # UUID as string
    reason: str

    # Optional parameters for specific actions
    expires_at: Optional[datetime] = None
    superseded_by: Optional[str] = None  # UUID as string
    quality_gate_version: Optional[str] = None

    performed_by: str = "system"
    notes: Optional[str] = None


class ExplainRejectionResponse(BaseModel):
    """Response model for rejection explanation."""
    artifact_id: str
    title: str
    summary: Optional[str]
    rejection_reason: str
    rejection_message: Optional[str]
    failing_rule: Optional[str]
    scores_at_rejection: Dict[str, float]
    rejected_at: datetime
    can_be_resubmitted: bool


class GovernanceStatisticsResponse(BaseModel):
    """Response model for governance statistics."""
    total_memories: int = 0
    disabled_count: int = 0
    rejections_pending_review: int = 0
    unresolved_challenges: int = 0


# ============================================================================
# Helper Functions
# ============================================================================

def _datetime_to_iso(dt: Any) -> Optional[str]:
    """Convert datetime to ISO string."""
    if dt is None:
        return None
    if isinstance(dt, str):
        return dt
    return dt.isoformat()


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/{memory_id}/detail", response_model=MemoryRecordDetail)
async def get_memory_detail(
    memory_id: str,
    service: MemoryInspectionService = Depends(get_inspection_service),
):
    """
    Get complete detail for a memory record.

    Includes validation history, access history, related memories,
    and control state.
    """
    try:
        memory_uuid = UUID(memory_id)
        detail = await service.get_memory_detail(memory_uuid)

        if not detail:
            raise HTTPException(status_code=404, detail=f"Memory {memory_id} not found")

        return detail

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid memory ID format")
    except Exception as e:
        logger.error(f"Error getting memory detail for {memory_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{memory_id}/traceability", response_model=MemoryTraceability)
async def get_memory_traceability(
    memory_id: str,
    service: MemoryInspectionService = Depends(get_inspection_service),
):
    """
    Get traceability chain from memory to source.

    Reconstructs: memory → source artifact → workspace/execution/team
    """
    try:
        memory_uuid = UUID(memory_id)
        traceability = await service.get_traceability(memory_uuid)

        if not traceability:
            raise HTTPException(status_code=404, detail=f"Traceability for {memory_id} not found")

        return traceability

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid memory ID format")
    except Exception as e:
        logger.error(f"Error getting traceability for {memory_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{memory_id}/validation", response_model=List[ValidationDecisionReport])
async def get_validation_decisions(
    memory_id: str,
    limit: int = Query(50, ge=1, le=500),
    service: MemoryInspectionService = Depends(get_inspection_service),
):
    """
    Get validation decision history for a memory.

    Shows all validation events with accept/reject decisions,
    rule evaluations, and conflict detection.
    """
    try:
        memory_uuid = UUID(memory_id)
        decisions = await service.get_validation_decisions(
            memory_id=memory_uuid,
            limit=limit,
        )

        return decisions

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid memory ID format")
    except Exception as e:
        logger.error(f"Error getting validation decisions for {memory_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rejections", response_model=List[RejectionLogEntry])
async def get_rejection_logs(
    workspace_id: Optional[str] = Query(None),
    reviewed_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=500),
    service: MemoryInspectionService = Depends(get_inspection_service),
):
    """
    Get rejection log entries.

    Args:
        workspace_id: Filter by workspace
        reviewed_only: Only show reviewed entries
        limit: Max results

    Returns:
        List of rejection log entries with details
    """
    try:
        workspace_uuid = UUID(workspace_id) if workspace_id else None

        entries = await service.get_rejection_logs(
            workspace_id=workspace_uuid,
            reviewed_only=reviewed_only,
            limit=limit,
        )

        return entries

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid workspace ID format")
    except Exception as e:
        logger.error(f"Error getting rejection logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rejections/{artifact_id}/explain", response_model=ExplainRejectionResponse)
async def explain_rejection(
    artifact_id: str,
    service: MemoryInspectionService = Depends(get_inspection_service),
):
    """
    Explain why a candidate was rejected.

    Returns detailed information about:
    - Which rule failed
    - What scores were too low
    - What conflicts existed
    - Whether it can be resubmitted
    """
    try:
        artifact_uuid = UUID(artifact_id)
        explanation = await service.explain_rejection(artifact_uuid)

        if not explanation:
            raise HTTPException(
                status_code=404,
                detail=f"No rejection found for artifact {artifact_id}"
            )

        return ExplainRejectionResponse(**explanation)

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid artifact ID format")
    except Exception as e:
        logger.error(f"Error explaining rejection for {artifact_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{memory_id}/audit", response_model=List[RetrievalAuditRecord])
async def get_retrieval_audit(
    memory_id: str,
    limit: int = Query(100, ge=1, le=1000),
    service: MemoryInspectionService = Depends(get_inspection_service),
):
    """
    Get retrieval audit records for a memory.

    Shows all access events with query context, including:
    - What was requested
    - Filters used
    - Results returned
    - Runtime performance
    """
    try:
        records = await service.get_retrieval_audit(
            memory_id=memory_id,
            limit=limit,
        )

        return records

    except Exception as e:
        logger.error(f"Error getting retrieval audit for {memory_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{memory_id}/audit-summary", response_model=RetrievalAuditSummary)
async def get_retrieval_audit_summary(
    memory_id: str,
    service: MemoryInspectionService = Depends(get_inspection_service),
):
    """
    Get summary of retrieval activity for a memory.

    Aggregates access by type and provides:
    - Total access count
    - Query/injection/inspection breakdown
    - Average runtime
    - Top users
    """
    try:
        summary = await service.get_retrieval_summary(memory_id)

        if not summary:
            raise HTTPException(status_code=404, detail=f"No audit data found for memory {memory_id}")

        return summary

    except Exception as e:
        logger.error(f"Error getting retrieval summary for {memory_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/attention", response_model=List[Dict[str, Any]])
async def get_memories_needing_attention(
    limit: int = Query(50, ge=1, le=500),
    service: MemoryInspectionService = Depends(get_inspection_service),
):
    """
    Get memories that need governance attention.

    Returns memories that are:
    - Disabled
    - Expired
    - Never validated
    - Low confidence
    - Expiring soon
    - Marked for supersession
    - Have unresolved challenges
    """
    try:
        memories = await service.get_memories_needing_attention(limit=limit)
        return memories

    except Exception as e:
        logger.error(f"Error getting memories needing attention: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics", response_model=GovernanceStatisticsResponse)
async def get_governance_statistics(
    service: MemoryInspectionService = Depends(get_inspection_service),
):
    """
    Get governance statistics.

    Returns system-wide governance metrics:
    - Total memories
    - Disabled count
    - Rejections pending review
    - Unresolved challenges
    """
    try:
        stats = await service.get_governance_statistics()

        return GovernanceStatisticsResponse(
            total_memories=stats.get("total_memories", 0),
            disabled_count=stats.get("disabled_count", 0),
            rejections_pending_review=stats.get("rejections_pending_review", 0),
            unresolved_challenges=stats.get("unresolved_challenges", 0),
        )

    except Exception as e:
        logger.error(f"Error getting governance statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/control", response_model=GovernanceActionResult)
async def execute_governance_action(
    request: GovernanceActionRequest,
    service: MemoryInspectionService = Depends(get_inspection_service),
):
    """
    Execute a governance control action.

    Actions:
    - disable: Disable memory from being queried
    - enable: Re-enable a disabled memory
    - expire: Force expiration of a memory
    - supersede: Mark memory as superseded by another
    - lock_quality: Lock quality gate version
    - unlock: Unlock quality gate

    Returns the before/after state of the action.
    """
    try:
        memory_uuid = UUID(request.memory_id)

        # Build action
        action = GovernanceAction(
            action_type=request.action_type,
            memory_id=memory_uuid,
            reason=request.reason,
            expires_at=request.expires_at,
            superseded_by=UUID(request.superseded_by) if request.superseded_by else None,
            quality_gate_version=request.quality_gate_version,
            performed_by=request.performed_by,
            notes=request.notes,
        )

        # Execute
        result = await service.execute_governance_action(action)

        if not result.success:
            raise HTTPException(
                status_code=400,
                detail=result.error or "Action failed"
            )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {e}")
    except Exception as e:
        logger.error(f"Error executing governance action: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rejections/{artifact_id}/review", status_code=204)
async def mark_rejection_reviewed(
    artifact_id: str,
    reviewed_by: str = Query(..., description="Reviewer identifier"),
    review_notes: Optional[str] = None,
    service: MemoryInspectionService = Depends(get_inspection_service),
):
    """
    Mark a rejection log entry as reviewed.

    This is for governance workflows where rejected candidates
    are reviewed for potential resubmission or policy adjustment.
    """
    try:
        # This would update the rejection log
        # For now, it's a placeholder
        return None

    except Exception as e:
        logger.error(f"Error marking rejection as reviewed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Batch Operations
# ============================================================================

@router.post("/control/batch-disable", response_model=List[GovernanceActionResult])
async def batch_disable_memories(
    memory_ids: List[str],
    reason: str,
    performed_by: str = "system",
    service: MemoryInspectionService = Depends(get_inspection_service),
):
    """
    Disable multiple memories at once.

    Useful for governance workflows where a class of memories
    needs to be temporarily disabled.
    """
    results = []

    for memory_id in memory_ids:
        try:
            memory_uuid = UUID(memory_id)
            action = GovernanceAction(
                action_type="disable",
                memory_id=memory_uuid,
                reason=reason,
                performed_by=performed_by,
            )
            result = await service.execute_governance_action(action)
            results.append(result)
        except Exception as e:
            results.append(GovernanceActionResult(
                success=False,
                action_type="disable",
                memory_id=UUID(memory_id),
                error=str(e)
            ))

    return results


@router.post("/control/batch-expire", response_model=List[GovernanceActionResult])
async def batch_expire_memories(
    memory_ids: List[str],
    reason: str,
    days_until_expiry: int = Query(0, ge=0, description="Days until expiry (0 for immediate)"),
    performed_by: str = "system",
    service: MemoryInspectionService = Depends(get_inspection_service),
):
    """
    Expire multiple memories at once.

    Useful for governance cleanup workflows.
    """
    from datetime import timedelta

    expires_at = datetime.now() + timedelta(days=days_until_expiry) if days_until_expiry > 0 else None
    results = []

    for memory_id in memory_ids:
        try:
            memory_uuid = UUID(memory_id)
            action = GovernanceAction(
                action_type="expire",
                memory_id=memory_uuid,
                reason=reason,
                expires_at=expires_at,
                performed_by=performed_by,
            )
            result = await service.execute_governance_action(action)
            results.append(result)
        except Exception as e:
            results.append(GovernanceActionResult(
                success=False,
                action_type="expire",
                memory_id=UUID(memory_id),
                error=str(e)
            ))

    return results
