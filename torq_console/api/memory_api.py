"""
Memory Query API Endpoints - Phase 4H.1 Milestone 3

REST API for controlled memory retrieval and query.

Endpoints:
- GET /api/memory/{id} - Get by UUID
- GET /api/memory/by-id/{memory_id} - Get by human-readable ID
- POST /api/memory/query - Query with filters
- GET /api/memory/workspace/{workspace_id} - By workspace
- GET /api/memory/execution/{execution_id} - By execution
- GET /api/memory/inspection/{id} - Detailed inspection
- GET /api/memory/status/{status} - List by status
- GET /api/memory/expiring - List expiring soon
- GET /api/memory/statistics - System statistics
- GET /api/memory/access-log - Access audit log
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

# Import query service
from torq_console.strategic_memory.query_service import (
    MemoryQueryService,
    MemoryQuery,
    MemoryQueryResult,
    MemoryInspection,
    ProvenanceFilter,
    FreshnessFilter,
    get_memory_query_service,
)

# Import models
from torq_console.strategic_memory.models import (
    StrategicMemory,
    MemoryType,
    MemoryScope,
    MemoryStatus,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Router
# ============================================================================

router = APIRouter(prefix="/api/memory", tags=["memory"])


# ============================================================================
# Dependencies
# ============================================================================

def get_query_service() -> MemoryQueryService:
    """Get the memory query service instance."""
    # This would typically come from app state
    # For now, create a new instance (should be cached in production)
    from torq_console.main import get_supabase_client
    supabase = get_supabase_client()
    return get_memory_query_service(supabase_client=supabase)


# ============================================================================
# Request/Response Models
# ============================================================================

class MemoryQueryRequest(BaseModel):
    """Request model for memory query endpoint."""
    memory_types: Optional[List[MemoryType]] = None
    domains: Optional[List[str]] = None
    scopes: Optional[List[MemoryScope]] = None
    scope_keys: Optional[List[str]] = None

    statuses: Optional[List[MemoryStatus]] = None
    freshness: FreshnessFilter = FreshnessFilter.ACTIVE_ONLY

    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    min_durability: Optional[float] = Field(None, ge=0.0, le=1.0)
    has_effectiveness_score: bool = False

    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    expires_before: Optional[datetime] = None
    expires_after: Optional[datetime] = None

    min_usage_count: int = 0
    include_unused: bool = True

    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=500)

    sort_by: str = Field(default="created_at", pattern="^(created_at|confidence|durability_score|usage_count|last_used_at|title)$")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


class MemoryResponse(BaseModel):
    """Response model for a single memory."""
    id: str
    memory_type: str
    title: str
    domain: Optional[str]
    scope: str
    scope_key: Optional[str]
    confidence: float
    durability_score: float
    effectiveness_score: Optional[float]
    memory_content: Dict[str, Any]
    status: str
    created_at: datetime
    reviewed_at: Optional[datetime]
    expires_at: Optional[datetime]
    last_validated_at: Optional[datetime]
    usage_count: int
    last_used_at: Optional[datetime]

    # Computed fields
    is_stale: bool = False
    is_supplanted: bool = False


class MemoryQueryResponse(BaseModel):
    """Response model for memory query results."""
    memories: List[MemoryResponse]
    total_count: int
    offset: int
    limit: int
    has_more: bool
    query_runtime_ms: float
    filters_applied: List[str]
    stale_count: int


class MemoryInspectionResponse(BaseModel):
    """Response model for memory inspection."""
    memory: MemoryResponse

    # Provenance
    source_artifacts: List[Dict[str, Any]] = []
    related_patterns: List[Dict[str, Any]] = []
    related_insights: List[Dict[str, Any]] = []
    related_experiments: List[Dict[str, Any]] = []

    # Usage
    total_usage_count: int = 0
    recent_usage: List[Dict[str, Any]] = []

    # Effectiveness
    effectiveness_summary: Optional[Dict[str, Any]] = None

    # Governance
    is_stale: bool = False
    is_supplanted: bool = False
    supplanted_by: Optional[MemoryResponse] = None
    challenges: List[Dict[str, Any]] = []


class MemoryStatisticsResponse(BaseModel):
    """Response model for memory statistics."""
    total_memories: int
    expiring_soon_count: int
    query_stats: Dict[str, int]


class AccessLogResponse(BaseModel):
    """Response model for access log entries."""
    entries: List[Dict[str, Any]]
    total_logged: int


# ============================================================================
# Helper Functions
# ============================================================================

def _memory_to_response(memory: StrategicMemory) -> MemoryResponse:
    """Convert StrategicMemory to API response."""
    return MemoryResponse(
        id=memory.id,
        memory_type=memory.memory_type.value,
        title=memory.title,
        domain=memory.domain,
        scope=memory.scope.value,
        scope_key=memory.scope_key,
        confidence=memory.confidence,
        durability_score=memory.durability_score,
        effectiveness_score=memory.effectiveness_score,
        memory_content=memory.memory_content,
        status=memory.status.value,
        created_at=memory.created_at,
        reviewed_at=memory.reviewed_at,
        expires_at=memory.expires_at,
        last_validated_at=memory.last_validated_at,
        usage_count=memory.usage_count,
        last_used_at=memory.last_used_at,
        is_stale=memory.expires_at and memory.expires_at < datetime.now(),
        is_supplanted=memory.supplanted_by_memory_id is not None,
    )


def _inspection_to_response(inspection: MemoryInspection) -> MemoryInspectionResponse:
    """Convert MemoryInspection to API response."""
    return MemoryInspectionResponse(
        memory=_memory_to_response(inspection.memory),
        source_artifacts=inspection.source_artifacts,
        related_patterns=inspection.related_patterns,
        related_insights=inspection.related_insights,
        related_experiments=inspection.related_experiments,
        total_usage_count=inspection.total_usage_count,
        recent_usage=inspection.recent_usage,
        effectiveness_summary=inspection.effectiveness_summary,
        is_stale=inspection.is_stale,
        is_supplanted=inspection.is_supplanted,
        supplanted_by=_memory_to_response(inspection.supplanted_by) if inspection.supplanted_by else None,
        challenges=inspection.challenges,
    )


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory_by_uuid(
    memory_id: str,
    include_stale: bool = Query(False, description="Include expired memories"),
    service: MemoryQueryService = Depends(get_query_service),
):
    """
    Get a specific memory by UUID.

    Returns 404 if the memory doesn't exist or is stale (unless include_stale=True).
    """
    try:
        memory_uuid = UUID(memory_id)
        memory = await service.get_by_id(memory_uuid, include_stale=include_stale)

        if not memory:
            raise HTTPException(status_code=404, detail=f"Memory {memory_id} not found")

        return _memory_to_response(memory)

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid memory ID format")
    except Exception as e:
        logger.error(f"Error getting memory {memory_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-id/{memory_id}", response_model=MemoryResponse)
async def get_memory_by_human_id(
    memory_id: str,
    include_stale: bool = Query(False, description="Include expired memories"),
    service: MemoryQueryService = Depends(get_query_service),
):
    """
    Get a memory by human-readable ID (e.g., "MEM_1234567890").

    Returns 404 if the memory doesn't exist or is stale.
    """
    memory = await service.get_by_human_id(memory_id, include_stale=include_stale)

    if not memory:
        raise HTTPException(status_code=404, detail=f"Memory {memory_id} not found")

    return _memory_to_response(memory)


@router.post("/query", response_model=MemoryQueryResponse)
async def query_memories(
    request: MemoryQueryRequest,
    service: MemoryQueryService = Depends(get_query_service),
):
    """
    Query memories with comprehensive filtering.

    Supports filtering by:
    - Classification: memory_types, domains, scopes
    - Status and freshness: statuses, freshness
    - Scoring: min_confidence, min_durability
    - Temporal: created_after/before, expires_after/before
    - Usage: min_usage_count, include_unused
    - Pagination: offset, limit
    - Sorting: sort_by, sort_order
    """
    try:
        # Convert API request to internal query
        query = MemoryQuery(
            memory_types=request.memory_types,
            domains=request.domains,
            scopes=request.scopes,
            scope_keys=request.scope_keys,
            statuses=request.statuses,
            freshness=request.freshness,
            min_confidence=request.min_confidence,
            min_durability=request.min_durability,
            has_effectiveness_score=request.has_effectiveness_score,
            created_after=request.created_after,
            created_before=request.created_before,
            expires_before=request.expires_before,
            expires_after=request.expires_after,
            min_usage_count=request.min_usage_count,
            include_unused=request.include_unused,
            offset=request.offset,
            limit=request.limit,
            sort_by=request.sort_by,
            sort_order=request.sort_order,
        )

        result = await service.query(query)

        return MemoryQueryResponse(
            memories=[_memory_to_response(m) for m in result.memories],
            total_count=result.total_count,
            offset=result.offset,
            limit=result.limit,
            has_more=result.has_more,
            query_runtime_ms=result.query_runtime_ms,
            filters_applied=result.filters_applied,
            stale_count=result.stale_count,
        )

    except Exception as e:
        logger.error(f"Error querying memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspace/{workspace_id}", response_model=List[MemoryResponse])
async def get_memories_by_workspace(
    workspace_id: str,
    memory_types: Optional[str] = Query(None, description="Comma-separated memory types"),
    limit: int = Query(50, ge=1, le=500),
    service: MemoryQueryService = Depends(get_query_service),
):
    """
    Get memories associated with a specific workspace.

    Optionally filter by memory types (comma-separated).
    """
    try:
        workspace_uuid = UUID(workspace_id)

        types = None
        if memory_types:
            types = [MemoryType(t.strip()) for t in memory_types.split(",")]

        memories = await service.get_by_workspace(
            workspace_id=workspace_uuid,
            memory_types=types,
            limit=limit,
        )

        return [_memory_to_response(m) for m in memories]

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid workspace ID format")
    except Exception as e:
        logger.error(f"Error getting memories for workspace {workspace_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/execution/{execution_id}", response_model=List[MemoryResponse])
async def get_memories_by_execution(
    execution_id: str,
    limit: int = Query(50, ge=1, le=500),
    service: MemoryQueryService = Depends(get_query_service),
):
    """
    Get memories associated with a specific execution.
    """
    try:
        memories = await service.get_by_execution(
            execution_id=execution_id,
            limit=limit,
        )

        return [_memory_to_response(m) for m in memories]

    except Exception as e:
        logger.error(f"Error getting memories for execution {execution_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inspection/{memory_id}", response_model=MemoryInspectionResponse)
async def inspect_memory(
    memory_id: str,
    service: MemoryQueryService = Depends(get_query_service),
):
    """
    Get detailed inspection data for a memory.

    Includes provenance, usage statistics, effectiveness, and governance status.
    """
    try:
        memory_uuid = UUID(memory_id)
        inspection = await service.inspect(memory_uuid)

        if not inspection:
            raise HTTPException(status_code=404, detail=f"Memory {memory_id} not found")

        return _inspection_to_response(inspection)

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid memory ID format")
    except Exception as e:
        logger.error(f"Error inspecting memory {memory_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{status}", response_model=List[MemoryResponse])
async def list_memories_by_status(
    status: str,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    service: MemoryQueryService = Depends(get_query_service),
):
    """
    List memories by status.

    Valid statuses: candidate, active, deprecated, archived, supplanted
    """
    try:
        memory_status = MemoryStatus(status)
        result = await service.list_by_status(
            status=memory_status,
            limit=limit,
            offset=offset,
        )

        return [_memory_to_response(m) for m in result.memories]

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Valid values: {[s.value for s in MemoryStatus]}"
        )
    except Exception as e:
        logger.error(f"Error listing memories by status {status}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/expiring", response_model=List[MemoryResponse])
async def list_expiring_memories(
    days: int = Query(7, ge=1, le=365, description="Days to look ahead"),
    limit: int = Query(50, ge=1, le=500),
    service: MemoryQueryService = Depends(get_query_service),
):
    """
    List memories that will expire within the specified window.
    """
    try:
        memories = await service.list_expiring_soon(days=days, limit=limit)

        return [_memory_to_response(m) for m in memories]

    except Exception as e:
        logger.error(f"Error listing expiring memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics", response_model=MemoryStatisticsResponse)
async def get_memory_statistics(
    service: MemoryQueryService = Depends(get_query_service),
):
    """
    Get memory system statistics.

    Includes total counts, expiring memories, and query statistics.
    """
    try:
        stats = await service.get_statistics()

        return MemoryStatisticsResponse(
            total_memories=stats.get("total_memories", 0),
            expiring_soon_count=stats.get("expiring_soon_count", 0),
            query_stats=stats.get("query_stats", {}),
        )

    except Exception as e:
        logger.error(f"Error getting memory statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/access-log", response_model=AccessLogResponse)
async def get_access_log(
    limit: int = Query(100, ge=1, le=1000),
    service: MemoryQueryService = Depends(get_query_service),
):
    """
    Get recent memory access log entries.

    Returns the audit trail of memory queries and retrievals.
    """
    try:
        entries = service.get_access_log(limit=limit)

        return AccessLogResponse(
            entries=[e.model_dump() for e in entries],
            total_logged=len(service._access_log),
        )

    except Exception as e:
        logger.error(f"Error getting access log: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/access-log", status_code=204)
async def clear_access_log(
    service: MemoryQueryService = Depends(get_query_service),
):
    """
    Clear the memory access log.

    This endpoint requires appropriate permissions in production.
    """
    try:
        service.clear_access_log()
        return None

    except Exception as e:
        logger.error(f"Error clearing access log: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/query", response_model=Dict[str, int])
async def get_query_statistics(
    service: MemoryQueryService = Depends(get_query_service),
):
    """
    Get query performance statistics.

    Returns counts of different query types.
    """
    try:
        return service.get_statistics_summary()

    except Exception as e:
        logger.error(f"Error getting query statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stats/reset", status_code=204)
async def reset_query_statistics(
    service: MemoryQueryService = Depends(get_query_service),
):
    """
    Reset query statistics.

    This endpoint requires appropriate permissions in production.
    """
    try:
        service.reset_statistics()
        return None

    except Exception as e:
        logger.error(f"Error resetting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
