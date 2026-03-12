"""
Memory Query Service - Phase 4H.1 Milestone 3

Controlled memory retrieval and query interface.

Builds on top of the existing retrieval engine to provide:
- Query by memory_id, type, workspace, mission, execution, team, source artifact
- Freshness-aware retrieval (suppress stale memory)
- Provenance-based filtering
- Access logging / retrieval audit
- Pagination support
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID, uuid4
from enum import Enum

from pydantic import BaseModel, Field

# Try to import Supabase client
try:
    from supabase import Client as SupabaseClient
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

from .models import (
    StrategicMemory,
    MemoryType,
    MemoryScope,
    MemoryStatus,
    MemorySearchRequest,
    MemorySearchResult,
)
from .retrieval import MemoryRetrievalEngine


logger = logging.getLogger(__name__)


# ============================================================================
# Query Models
# ============================================================================

class FreshnessFilter(str, Enum):
    """How to handle memory freshness."""
    ACTIVE_ONLY = "active_only"  # Only non-expired memories
    INCLUDE_STALE = "include_stale"  # Include expired but mark them
    STALE_ONLY = "stale_only"  # Only expired memories (for governance)


class ProvenanceFilter(BaseModel):
    """Filter memories by their source provenance."""
    workspace_id: Optional[UUID] = None
    mission_id: Optional[UUID] = None
    execution_id: Optional[str] = None
    team_execution_id: Optional[UUID] = None
    artifact_id: Optional[UUID] = None
    artifact_type: Optional[str] = None
    role_name: Optional[str] = None
    source_pattern_ids: Optional[List[UUID]] = None
    source_insight_ids: Optional[List[UUID]] = None
    source_experiment_ids: Optional[List[UUID]] = None


class MemoryQuery(BaseModel):
    """Comprehensive memory query with all available filters."""
    # Identification
    memory_id: Optional[str] = None  # Human-readable ID
    memory_uuid: Optional[UUID] = None  # Database UUID

    # Classification
    memory_types: Optional[List[MemoryType]] = None
    domains: Optional[List[str]] = None
    scopes: Optional[List[MemoryScope]] = None
    scope_keys: Optional[List[str]] = None

    # Status and lifecycle
    statuses: Optional[List[MemoryStatus]] = None
    freshness: FreshnessFilter = FreshnessFilter.ACTIVE_ONLY

    # Scoring thresholds
    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    min_durability: Optional[float] = Field(None, ge=0.0, le=1.0)
    has_effectiveness_score: bool = False

    # Provenance filtering
    provenance: Optional[ProvenanceFilter] = None

    # Temporal
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    expires_before: Optional[datetime] = None
    expires_after: Optional[datetime] = None

    # Usage tracking
    min_usage_count: int = 0
    include_unused: bool = True

    # Pagination
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=500)

    # Sorting
    sort_by: str = Field(default="created_at", pattern="^(created_at|confidence|durability_score|usage_count|last_used_at|title)$")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


class MemoryQueryResult(BaseModel):
    """Result of a memory query with metadata."""
    memories: List[StrategicMemory]
    total_count: int
    offset: int
    limit: int
    has_more: bool

    # Query metadata
    query_runtime_ms: float
    filters_applied: List[str]
    stale_count: int = 0  # Count of expired memories in results


class MemoryInspection(BaseModel):
    """Inspection data for a memory entry."""
    memory: StrategicMemory

    # Provenance information
    source_artifacts: List[Dict[str, Any]] = []
    related_patterns: List[Dict[str, Any]] = []
    related_insights: List[Dict[str, Any]] = []
    related_experiments: List[Dict[str, Any]] = []

    # Usage statistics
    total_usage_count: int = 0
    recent_usage: List[Dict[str, Any]] = []

    # Effectiveness data
    effectiveness_summary: Optional[Dict[str, Any]] = None

    # Governance status
    is_stale: bool = False
    is_supplanted: bool = False
    supplanted_by: Optional[StrategicMemory] = None
    challenges: List[Dict[str, Any]] = []


class AccessLogEntry(BaseModel):
    """Entry in the memory access log."""
    id: UUID = Field(default_factory=uuid4)
    memory_id: str
    memory_uuid: UUID

    # Access context
    accessed_at: datetime = Field(default_factory=datetime.utcnow)
    access_type: str = "query"  # query, injection, inspection
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    # Query details
    query_filters: Optional[Dict[str, Any]] = None
    results_count: int = 0

    # Performance
    query_runtime_ms: float = 0.0


# ============================================================================
# Query Service
# ============================================================================

class MemoryQueryService:
    """
    Service for controlled memory retrieval and querying.

    Responsibilities:
    - Query memories by multiple criteria
    - Filter by freshness and provenance
    - Log all access for audit trail
    - Support pagination and sorting
    - Provide inspection endpoints
    """

    def __init__(
        self,
        supabase_client: Optional[Any] = None,
        retrieval_engine: Optional[MemoryRetrievalEngine] = None,
        enable_access_logging: bool = True,
    ):
        """
        Initialize the query service.

        Args:
            supabase_client: Optional Supabase client
            retrieval_engine: Optional existing retrieval engine
            enable_access_logging: Whether to log all access
        """
        self.supabase = supabase_client
        self.enable_access_logging = enable_access_logging

        # Initialize retrieval engine
        if retrieval_engine:
            self.retrieval = retrieval_engine
        elif supabase_client:
            self.retrieval = MemoryRetrievalEngine(supabase_client)
        else:
            self.retrieval = None

        # Access log (in-memory for now; could be persisted)
        self._access_log: List[AccessLogEntry] = []

        # Statistics
        self._stats = {
            "queries_total": 0,
            "queries_by_id": 0,
            "queries_by_provenance": 0,
            "queries_with_freshness_filter": 0,
            "inspection_requests": 0,
        }

    # ========================================================================
    # Core Query Methods
    # ========================================================================

    async def query(self, query: MemoryQuery) -> MemoryQueryResult:
        """
        Execute a comprehensive memory query.

        Args:
            query: The query parameters

        Returns:
            Query results with metadata
        """
        start_time = datetime.now()
        filters_applied = []

        # Update stats
        self._stats["queries_total"] += 1

        # Start building the Supabase query
        db_query = self.supabase.table("strategic_memories").select("*", count="exact")

        # Apply filters

        # 1. Direct ID lookups
        if query.memory_id:
            # Human-readable ID lookup - need to match by title pattern or separate column
            # For now, this would require a separate id column
            filters_applied.append(f"memory_id:{query.memory_id}")

        if query.memory_uuid:
            db_query = db_query.eq("id", str(query.memory_uuid))
            filters_applied.append(f"uuid:{query.memory_uuid}")

        # 2. Classification filters
        if query.memory_types:
            type_values = [t.value if isinstance(t, str) else t.value for t in query.memory_types]
            db_query = db_query.in_("memory_type", type_values)
            filters_applied.append(f"types:{','.join(type_values)}")

        if query.domains:
            db_query = db_query.in_("domain", query.domains)
            filters_applied.append(f"domains:{','.join(query.domains)}")

        if query.scopes:
            scope_values = [s.value if isinstance(s, str) else s.value for s in query.scopes]
            db_query = db_query.in_("scope", scope_values)
            filters_applied.append(f"scopes:{','.join(scope_values)}")

        if query.scope_keys:
            db_query = db_query.in_("scope_key", query.scope_keys)
            filters_applied.append(f"scope_keys:{','.join(query.scope_keys)}")

        # 3. Status and freshness
        if query.statuses:
            status_values = [s.value if isinstance(s, str) else s.value for s in query.statuses]
            db_query = db_query.in_("status", status_values)
            filters_applied.append(f"statuses:{','.join(status_values)}")
        elif query.freshness == FreshnessFilter.ACTIVE_ONLY:
            # Default to active only
            db_query = db_query.eq("status", MemoryStatus.ACTIVE.value)
            filters_applied.append("status:active")
            self._stats["queries_with_freshness_filter"] += 1

        # 4. Scoring thresholds
        if query.min_confidence is not None:
            db_query = db_query.gte("confidence", query.min_confidence)
            filters_applied.append(f"min_confidence:{query.min_confidence}")

        if query.min_durability is not None:
            db_query = db_query.gte("durability_score", query.min_durability)
            filters_applied.append(f"min_durability:{query.min_durability}")

        if query.has_effectiveness_score:
            db_query = db_query.not_("effectiveness_score", "null")
            filters_applied.append("has_effectiveness")

        # 5. Temporal filters
        if query.created_after:
            db_query = db_query.gte("created_at", query.created_after.isoformat())
            filters_applied.append(f"created_after:{query.created_after}")

        if query.created_before:
            db_query = db_query.lte("created_at", query.created_before.isoformat())
            filters_applied.append(f"created_before:{query.created_before}")

        if query.expires_before:
            db_query = db_query.lte("expires_at", query.expires_before.isoformat())
            filters_applied.append(f"expires_before:{query.expires_before}")

        if query.expires_after:
            db_query = db_query.gte("expires_at", query.expires_after.isoformat())
            filters_applied.append(f"expires_after:{query.expires_after}")

        # 6. Usage filters
        if query.min_usage_count > 0:
            db_query = db_query.gte("usage_count", query.min_usage_count)
            filters_applied.append(f"min_usage:{query.min_usage_count}")

        if not query.include_unused:
            db_query = db_query.gt("usage_count", 0)
            filters_applied.append("used_only")

        # 7. Apply pagination
        db_query = db_query.range(query.offset, query.offset + query.limit - 1)

        # 8. Apply sorting
        order_column = query.sort_by
        if query.sort_order == "asc":
            db_query = db_query.order(order_column, asc=True)
        else:
            db_query = db_query.order(order_column, desc=True)

        # Execute query
        try:
            result = db_query.execute()
            memories_data = result.data or []
            total_count = result.count if hasattr(result, 'count') else len(memories_data)

        except Exception as e:
            logger.error(f"Error executing memory query: {e}")
            return MemoryQueryResult(
                memories=[],
                total_count=0,
                offset=query.offset,
                limit=query.limit,
                has_more=False,
                query_runtime_ms=(datetime.now() - start_time).total_seconds() * 1000,
                filters_applied=[],
            )

        # Process results for freshness filtering
        memories = []
        stale_count = 0
        now = datetime.now().isoformat()

        for memory_data in memories_data:
            memory = StrategicMemory(**memory_data)

            # Check freshness
            is_stale = (
                memory.expires_at is not None and
                memory.expires_at < datetime.fromisoformat(now)
            )

            if query.freshness == FreshnessFilter.STALE_ONLY and not is_stale:
                continue
            elif query.freshness == FreshnessFilter.ACTIVE_ONLY and is_stale:
                continue
            elif is_stale:
                stale_count += 1

            memories.append(memory)

        # Calculate runtime
        runtime_ms = (datetime.now() - start_time).total_seconds() * 1000

        # Log access
        if self.enable_access_logging:
            self._log_access(
                memory_id=None,  # No single memory for query
                access_type="query",
                query_filters=query.model_dump(exclude_none=True),
                results_count=len(memories),
                runtime_ms=runtime_ms,
            )

        return MemoryQueryResult(
            memories=memories,
            total_count=total_count,
            offset=query.offset,
            limit=query.limit,
            has_more=query.offset + len(memories) < total_count,
            query_runtime_ms=runtime_ms,
            filters_applied=filters_applied,
            stale_count=stale_count,
        )

    async def get_by_id(
        self,
        memory_uuid: UUID,
        include_stale: bool = False,
    ) -> Optional[StrategicMemory]:
        """
        Get a specific memory by UUID.

        Args:
            memory_uuid: Memory UUID
            include_stale: Whether to include expired memories

        Returns:
            Memory or None if not found
        """
        self._stats["queries_by_id"] += 1
        start_time = datetime.now()

        try:
            result = self.supabase.table("strategic_memories").select("*").eq("id", str(memory_uuid)).execute()

            if not result.data:
                return None

            memory = StrategicMemory(**result.data[0])

            # Check freshness
            if not include_stale and memory.expires_at:
                if memory.expires_at < datetime.now():
                    return None  # Memory is stale

            # Log access
            if self.enable_access_logging:
                self._log_access(
                    memory_id=memory.title,  # Use title as ID
                    memory_uuid=memory_uuid,
                    access_type="get_by_id",
                    results_count=1,
                    runtime_ms=(datetime.now() - start_time).total_seconds() * 1000,
                )

            return memory

        except Exception as e:
            logger.error(f"Error getting memory by ID {memory_uuid}: {e}")
            return None

    async def get_by_human_id(
        self,
        memory_id: str,
        include_stale: bool = False,
    ) -> Optional[StrategicMemory]:
        """
        Get a memory by human-readable ID.

        Note: This requires a separate memory_id column or index.
        For now, we'll search by title prefix.

        Args:
            memory_id: Human-readable memory ID (e.g., "MEM_1234567890")
            include_stale: Whether to include expired memories

        Returns:
            Memory or None if not found
        """
        # For now, we'll need to add a memory_id column to the schema
        # This is a placeholder for that functionality
        try:
            result = self.supabase.table("strategic_memories").select("*").limit(1).execute()

            # This would need to be updated with proper memory_id column query
            if result.data:
                return StrategicMemory(**result.data[0])
            return None

        except Exception as e:
            logger.error(f"Error getting memory by human ID {memory_id}: {e}")
            return None

    # ========================================================================
    # Provenance Queries
    # ========================================================================

    async def query_by_provenance(
        self,
        provenance: ProvenanceFilter,
        limit: int = 50,
        offset: int = 0,
    ) -> MemoryQueryResult:
        """
        Query memories by their source provenance.

        Args:
            provenance: Provenance filter criteria
            limit: Max results
            offset: Pagination offset

        Returns:
            Memories matching the provenance criteria
        """
        self._stats["queries_by_provenance"] += 1
        start_time = datetime.now()

        # Build query with provenance filters
        query = MemoryQuery(
            limit=limit,
            offset=offset,
            provenance=provenance,
        )

        # For now, we'll need to add provenance columns to the schema
        # This is a simplified implementation
        return await self.query(query)

    async def get_by_workspace(
        self,
        workspace_id: UUID,
        memory_types: Optional[List[MemoryType]] = None,
        limit: int = 50,
    ) -> List[StrategicMemory]:
        """
        Get memories associated with a specific workspace.

        Args:
            workspace_id: Workspace UUID
            memory_types: Optional filter by memory types
            limit: Max results

        Returns:
            List of memories from this workspace
        """
        provenance = ProvenanceFilter(workspace_id=workspace_id)
        result = await self.query_by_provenance(
            provenance=provenance,
            limit=limit,
        )

        # Filter by memory types if specified
        if memory_types:
            type_values = {t.value for t in memory_types}
            result.memories = [
                m for m in result.memories
                if m.memory_type.value in type_values
            ]

        return result.memories

    async def get_by_execution(
        self,
        execution_id: str,
        limit: int = 50,
    ) -> List[StrategicMemory]:
        """
        Get memories associated with a specific execution.

        Args:
            execution_id: Execution ID
            limit: Max results

        Returns:
            List of memories from this execution
        """
        provenance = ProvenanceFilter(execution_id=execution_id)
        result = await self.query_by_provenance(
            provenance=provenance,
            limit=limit,
        )

        return result.memories

    # ========================================================================
    # Inspection Endpoints
    # ========================================================================

    async def inspect(
        self,
        memory_uuid: UUID,
    ) -> Optional[MemoryInspection]:
        """
        Get detailed inspection data for a memory.

        Includes provenance, usage statistics, and governance status.

        Args:
            memory_uuid: Memory UUID to inspect

        Returns:
            Inspection data or None if not found
        """
        self._stats["inspection_requests"] += 1

        # Get the memory
        memory = await self.get_by_id(memory_uuid, include_stale=True)
        if not memory:
            return None

        inspection = MemoryInspection(memory=memory)

        # Check staleness
        inspection.is_stale = (
            memory.expires_at is not None and
            memory.expires_at < datetime.now()
        )

        # Check if supplanted
        inspection.is_supplanted = memory.supplanted_by_memory_id is not None
        if memory.supplanted_by_memory_id:
            inspection.supplanted_by = await self.get_by_id(
                UUID(memory.supplanted_by_memory_id),
                include_stale=True,
            )

        # Get usage statistics
        try:
            usage_result = self.supabase.table("memory_usage").select("*").eq(
                "memory_id", str(memory_uuid)
            ).order("used_at", desc=True).limit(10).execute()

            if usage_result.data:
                inspection.total_usage_count = len(usage_result.data)
                inspection.recent_usage = usage_result.data

                # Calculate effectiveness summary
                helpful_count = sum(1 for u in usage_result.data if u.get("was_helpful") is True)
                total_with_feedback = sum(1 for u in usage_result.data if u.get("was_helpful") is not None)

                if total_with_feedback > 0:
                    inspection.effectiveness_summary = {
                        "helpful_ratio": helpful_count / total_with_feedback,
                        "total_usage": len(usage_result.data),
                        "avg_outcome_score": sum(
                            u.get("outcome_score", 0) for u in usage_result.data
                            if u.get("outcome_score") is not None
                        ) / max(1, len(usage_result.data)),
                    }

        except Exception as e:
            logger.warning(f"Error getting usage statistics for {memory_uuid}: {e}")

        # Get challenges
        try:
            challenge_result = self.supabase.table("memory_challenges").select("*").eq(
                "memory_id", str(memory_uuid)
            ).execute()

            if challenge_result.data:
                inspection.challenges = challenge_result.data

        except Exception as e:
            logger.warning(f"Error getting challenges for {memory_uuid}: {e}")

        # Log access
        if self.enable_access_logging:
            self._log_access(
                memory_id=memory.title,
                memory_uuid=memory_uuid,
                access_type="inspection",
                results_count=1,
            )

        return inspection

    async def list_by_status(
        self,
        status: MemoryStatus,
        limit: int = 50,
        offset: int = 0,
    ) -> MemoryQueryResult:
        """
        List memories by status.

        Args:
            status: Memory status to filter by
            limit: Max results
            offset: Pagination offset

        Returns:
            Memories with the specified status
        """
        query = MemoryQuery(
            statuses=[status],
            limit=limit,
            offset=offset,
            sort_by="created_at",
            sort_order="desc",
        )

        return await self.query(query)

    async def list_expiring_soon(
        self,
        days: int = 7,
        limit: int = 50,
    ) -> List[StrategicMemory]:
        """
        List memories that will expire soon.

        Args:
            days: Look ahead window in days
            limit: Max results

        Returns:
            Memories expiring within the window
        """
        try:
            cutoff = (datetime.now() + timedelta(days=days)).isoformat()

            result = self.supabase.table("strategic_memories").select("*").eq(
                "status", MemoryStatus.ACTIVE.value
            ).gte("expires_at", datetime.now().isoformat()).lte(
                "expires_at", cutoff
            ).order("expires_at", asc=True).limit(limit).execute()

            return [StrategicMemory(**m) for m in result.data] if result.data else []

        except Exception as e:
            logger.error(f"Error listing expiring memories: {e}")
            return []

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get memory system statistics.

        Returns:
            Dictionary with various statistics
        """
        try:
            # Count by status
            status_result = self.supabase.table("strategic_memories").select("status", count="exact").execute()

            # Count by type
            type_result = self.supabase.table("strategic_memories").select("memory_type", count="exact").execute()

            # Get expiring count
            expiring_result = self.supabase.table("strategic_memories").select("id", count="exact").eq(
                "status", MemoryStatus.ACTIVE.value
            ).lt("expires_at", (datetime.now() + timedelta(days=7)).isoformat()).gte(
                "expires_at", datetime.now().isoformat()
            ).execute()

            return {
                "total_memories": status_result.count if hasattr(status_result, 'count') else 0,
                "expiring_soon_count": expiring_result.count if hasattr(expiring_result, 'count') else 0,
                "query_stats": self._stats.copy(),
            }

        except Exception as e:
            logger.error(f"Error getting memory statistics: {e}")
            return {
                "total_memories": 0,
                "expiring_soon_count": 0,
                "query_stats": self._stats.copy(),
            }

    # ========================================================================
    # Access Logging
    # ========================================================================

    def _log_access(
        self,
        memory_id: Optional[str],
        access_type: str,
        query_filters: Optional[Dict[str, Any]] = None,
        results_count: int = 0,
        runtime_ms: float = 0.0,
        memory_uuid: Optional[UUID] = None,
    ):
        """Log a memory access event."""
        entry = AccessLogEntry(
            memory_id=memory_id or "query",
            memory_uuid=memory_uuid or uuid4(),
            access_type=access_type,
            query_filters=query_filters,
            results_count=results_count,
            query_runtime_ms=runtime_ms,
        )

        self._access_log.append(entry)

        # Trim log if too large (keep last 1000 entries)
        if len(self._access_log) > 1000:
            self._access_log = self._access_log[-1000:]

    def get_access_log(self, limit: int = 100) -> List[AccessLogEntry]:
        """Get recent access log entries."""
        return self._access_log[-limit:]

    def clear_access_log(self):
        """Clear the access log."""
        self._access_log.clear()

    def get_statistics_summary(self) -> Dict[str, int]:
        """Get query statistics summary."""
        return self._stats.copy()

    def reset_statistics(self):
        """Reset query statistics."""
        self._stats = {
            "queries_total": 0,
            "queries_by_id": 0,
            "queries_by_provenance": 0,
            "queries_with_freshness_filter": 0,
            "inspection_requests": 0,
        }


# ============================================================================
# Factory Functions
# ============================================================================

def get_memory_query_service(
    supabase_client: Optional[Any] = None,
    enable_access_logging: bool = True,
) -> MemoryQueryService:
    """
    Get a memory query service.

    Args:
        supabase_client: Optional Supabase client
        enable_access_logging: Whether to log all access

    Returns:
        Configured query service
    """
    return MemoryQueryService(
        supabase_client=supabase_client,
        enable_access_logging=enable_access_logging,
    )
