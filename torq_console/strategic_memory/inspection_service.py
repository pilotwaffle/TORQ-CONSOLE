"""
Memory Inspection Service - Phase 4H.1 Milestone 4

Provides comprehensive inspection, audit, and control capabilities for strategic memory.

Responsibilities:
- Memory record detail inspection
- Traceability views (memory → artifact → workspace/execution/team)
- Validation decision visibility
- Retrieval audit inspection
- Control hooks (disable, expire, supersede)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

try:
    from supabase import Client as SupabaseClient
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

from .models import (
    StrategicMemory,
    MemoryType,
    MemoryStatus,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Inspection Models
# ============================================================================

class MemoryRecordDetail(BaseModel):
    """Complete detail for a memory record."""
    memory: StrategicMemory

    # Validation history
    validation_events: List[Dict[str, Any]] = []
    total_validations: int = 0

    # Access history
    recent_access: List[Dict[str, Any]] = []
    total_access_count: int = 0
    last_accessed_at: Optional[datetime] = None

    # Related memories
    related_memories: List[Dict[str, Any]] = []

    # Control state
    is_disabled: bool = False
    is_marked_for_supersession: bool = False
    has_forced_expiration: bool = False


class MemoryTraceability(BaseModel):
    """Traceability chain from memory to source."""
    memory_id: str
    memory_title: str
    memory_type: str

    # Source chain
    source_artifacts: List[Dict[str, Any]] = []
    source_patterns: List[Dict[str, Any]] = []
    source_insights: List[Dict[str, Any]] = []
    source_experiments: List[Dict[str, Any]] = []

    # Workspace context
    workspace_id: Optional[UUID] = None
    workspace_name: Optional[str] = None
    mission_id: Optional[UUID] = None
    execution_id: Optional[str] = None
    team_execution_id: Optional[UUID] = None

    # Temporal trace
    created_at: datetime
    artifact_created_at: Optional[datetime] = None
    time_to_memory_hours: Optional[float] = None


class ValidationDecisionReport(BaseModel):
    """Report on why a memory was accepted or rejected."""
    memory_id: Optional[str]  # None if rejected before storage
    artifact_id: UUID

    decision: str  # ACCEPT, REJECT, REVIEW
    decision_reason: Optional[str]

    # Scores at time of validation
    confidence_score: Optional[float] = None
    completeness_score: Optional[float] = None
    durability_score: Optional[float] = None

    # Rule evaluation
    eligibility_rules_checked: List[str] = []
    rules_passed: List[str] = []
    rules_failed: List[str] = []

    # Why was it rejected?
    rejection_reason: Optional[str] = None
    failing_rule: Optional[str] = None
    rejection_message: Optional[str] = None

    # Conflicts
    conflicts_detected: bool = False
    conflict_details: Dict[str, Any] = {}

    # Temporal
    validated_at: datetime
    validator_type: str  # automated, human, hybrid
    validator_id: Optional[str] = None


class RejectionLogEntry(BaseModel):
    """Detailed entry from rejection log."""
    id: UUID
    artifact_id: UUID
    workspace_id: UUID
    proposed_memory_type: str
    title: str
    summary: Optional[str]

    rejection_reason: str
    rejection_message: Optional[str]
    failing_rule: Optional[str]

    confidence_score: float
    completeness_score: float

    rejected_at: datetime
    validator_version: str

    # Review tracking
    reviewed: bool = False
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None


class RetrievalAuditRecord(BaseModel):
    """Record from retrieval access log."""
    id: UUID
    memory_id: str
    memory_uuid: UUID
    access_type: str
    accessed_at: datetime

    user_id: Optional[str] = None
    session_id: Optional[str] = None

    query_filters: Dict[str, Any] = {}
    results_count: int = 0
    query_runtime_ms: float = 0.0

    # Context
    workflow_type: Optional[str] = None
    domain: Optional[str] = None
    execution_id: Optional[UUID] = None


class RetrievalAuditSummary(BaseModel):
    """Summary of retrieval activity."""
    memory_id: str

    total_access_count: int = 0
    query_count: int = 0
    injection_count: int = 0
    inspection_count: int = 0

    # Recent activity
    recent_queries: List[Dict[str, Any]] = []
    recent_injections: List[Dict[str, Any]] = []

    # Performance
    avg_query_runtime_ms: float = 0.0
    avg_results_per_query: float = 0.0

    # Top users
    top_users: List[Dict[str, Any]] = []


class GovernanceAction(BaseModel):
    """A governance control action."""
    action_type: str  # disable, enable, expire, supersede, lock_quality, unlock
    memory_id: UUID
    reason: str

    # Action-specific parameters
    expires_at: Optional[datetime] = None
    superseded_by: Optional[UUID] = None
    quality_gate_version: Optional[str] = None

    # Metadata
    performed_by: str
    performed_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None


class GovernanceActionResult(BaseModel):
    """Result of a governance action."""
    success: bool
    action_type: str
    memory_id: UUID

    before_state: Dict[str, Any] = {}
    after_state: Dict[str, Any] = {}

    message: str = ""
    error: Optional[str] = None


# ============================================================================
# Inspection Service
# ============================================================================

class MemoryInspectionService:
    """
    Service for inspecting memory records, traceability, and audit trails.

    Responsibilities:
    - Detailed memory record inspection
    - Traceability chain reconstruction
    - Validation decision visibility
    - Retrieval audit inspection
    - Control action execution
    """

    def __init__(self, supabase_client: Optional[Any] = None):
        """
        Initialize the inspection service.

        Args:
            supabase_client: Optional Supabase client
        """
        self.supabase = supabase_client

    # ========================================================================
    # Memory Record Inspection
    # ========================================================================

    async def get_memory_detail(
        self,
        memory_uuid: UUID,
    ) -> Optional[MemoryRecordDetail]:
        """
        Get complete detail for a memory record.

        Includes validation history, access history, related memories,
        and control state.
        """
        if not self.supabase:
            logger.warning("No Supabase client available")
            return None

        try:
            # Get the memory
            result = self.supabase.table("strategic_memories").select("*").eq(
                "id", str(memory_uuid)
            ).execute()

            if not result.data:
                return None

            memory = StrategicMemory(**result.data[0])

            detail = MemoryRecordDetail(memory=memory)

            # Get validation events
            validation_result = self.supabase.table("memory_validation_events").select("*").eq(
                "memory_id", str(memory_uuid)
            ).order("validated_at", desc=True).limit(20).execute()
            detail.validation_events = validation_result.data or []
            detail.total_validations = len(detail.validation_events)

            # Get access history
            access_result = self.supabase.table("memory_access_log").select("*").eq(
                "memory_id", str(memory_uuid)
            ).order("accessed_at", desc=True).limit(20).execute()
            detail.recent_access = access_result.data or []
            detail.total_access_count = len(self.supabase.table("memory_access_log").select("*", count="exact").eq(
                "memory_id", str(memory_uuid)
            ).execute().count or [])

            if detail.recent_access:
                detail.last_accessed_at = datetime.fromisoformat(
                    detail.recent_access[0]["accessed_at"]
                )

            # Get control state
            control_result = self.supabase.table("memory_control_state").select("*").eq(
                "memory_id", str(memory_uuid)
            ).execute()
            if control_result.data:
                state = control_result.data[0]
                detail.is_disabled = state.get("disabled", False)
                detail.is_marked_for_supersession = state.get("marked_for_supersession", False)
                detail.has_forced_expiration = state.get("force_expiration", False)

            return detail

        except Exception as e:
            logger.error(f"Error getting memory detail for {memory_uuid}: {e}")
            return None

    # ========================================================================
    # Traceability
    # ========================================================================

    async def get_traceability(
        self,
        memory_uuid: UUID,
    ) -> Optional[MemoryTraceability]:
        """
        Get traceability chain from memory to source.

        Reconstructs: memory → source artifact → workspace/execution/team
        """
        if not self.supabase:
            return None

        try:
            # Get the memory
            result = self.supabase.table("strategic_memories").select("*").eq(
                "id", str(memory_uuid)
            ).execute()

            if not result.data:
                return None

            memory = StrategicMemory(**result.data[0])

            traceability = MemoryTraceability(
                memory_id=memory.id,
                memory_title=memory.title,
                memory_type=memory.memory_type.value,
                created_at=memory.created_at,
            )

            # Get source artifacts (if we have artifact linking)
            # This would require artifact_id to be stored on the memory
            # For now, return basic info
            return traceability

        except Exception as e:
            logger.error(f"Error getting traceability for {memory_uuid}: {e}")
            return None

    async def get_source_chain(
        self,
        artifact_id: UUID,
    ) -> Dict[str, Any]:
        """
        Get the source chain for an artifact.

        Returns: workspace → mission → execution → team context
        """
        if not self.supabase:
            return {}

        try:
            # This would query the artifacts table when we have it
            return {
                "artifact_id": str(artifact_id),
                "note": "Source chain tracking requires artifact table integration"
            }
        except Exception as e:
            logger.error(f"Error getting source chain for {artifact_id}: {e}")
            return {}

    # ========================================================================
    # Validation Decision Visibility
    # ========================================================================

    async def get_validation_decisions(
        self,
        memory_id: Optional[UUID] = None,
        artifact_id: Optional[UUID] = None,
        limit: int = 50,
    ) -> List[ValidationDecisionReport]:
        """
        Get validation decision reports.

        Args:
            memory_id: Filter by memory UUID
            artifact_id: Filter by artifact UUID
            limit: Max results

        Returns:
            List of validation decision reports
        """
        if not self.supabase:
            return []

        try:
            query = self.supabase.table("memory_validation_events").select("*")

            if memory_id:
                query = query.eq("memory_id", str(memory_id))
            if artifact_id:
                query = query.eq("candidate_artifact_id", str(artifact_id))

            result = query.order("validated_at", desc=True).limit(limit).execute()

            reports = []
            for event in result.data or []:
                reports.append(ValidationDecisionReport(
                    memory_id=event.get("memory_id"),
                    artifact_id=UUID(event["candidate_artifact_id"]),
                    decision=event["decision"],
                    decision_reason=event.get("decision_reason"),
                    confidence_score=event.get("confidence_score"),
                    completeness_score=event.get("completeness_score"),
                    durability_score=event.get("durability_score"),
                    eligibility_rules_checked=event.get("eligibility_rules_checked", []),
                    rules_passed=event.get("rules_passed", []),
                    rules_failed=event.get("rules_failed", []),
                    conflicts_detected=event.get("conflicts_detected", False),
                    conflict_details=event.get("conflict_details", {}),
                    validated_at=datetime.fromisoformat(event["validated_at"]),
                    validator_type=event.get("validator_type", "automated"),
                    validator_id=event.get("validator_id"),
                ))

            return reports

        except Exception as e:
            logger.error(f"Error getting validation decisions: {e}")
            return []

    async def get_rejection_logs(
        self,
        workspace_id: Optional[UUID] = None,
        reviewed_only: bool = False,
        limit: int = 50,
    ) -> List[RejectionLogEntry]:
        """
        Get rejection log entries.

        Args:
            workspace_id: Filter by workspace
            reviewed_only: Only show reviewed entries
            limit: Max results

        Returns:
            List of rejection log entries
        """
        if not self.supabase:
            return []

        try:
            query = self.supabase.table("memory_rejection_log").select("*")

            if workspace_id:
                query = query.eq("workspace_id", str(workspace_id))

            if reviewed_only:
                query = query.eq("reviewed", True)

            result = query.order("rejected_at", desc=True).limit(limit).execute()

            entries = []
            for entry in result.data or []:
                entries.append(RejectionLogEntry(
                    id=UUID(entry["id"]),
                    artifact_id=UUID(entry["artifact_id"]),
                    workspace_id=UUID(entry["workspace_id"]),
                    proposed_memory_type=entry["proposed_memory_type"],
                    title=entry["title"],
                    summary=entry.get("summary"),
                    rejection_reason=entry["rejection_reason"],
                    rejection_message=entry.get("rejection_message"),
                    failing_rule=entry.get("failing_rule"),
                    confidence_score=entry["confidence_score"],
                    completeness_score=entry["completeness_score"],
                    rejected_at=datetime.fromisoformat(entry["rejected_at"]),
                    validator_version=entry["validator_version"],
                    reviewed=entry.get("reviewed", False),
                    reviewed_by=entry.get("reviewed_by"),
                    reviewed_at=datetime.fromisoformat(entry["reviewed_at"]) if entry.get("reviewed_at") else None,
                    review_notes=entry.get("review_notes"),
                ))

            return entries

        except Exception as e:
            logger.error(f"Error getting rejection logs: {e}")
            return []

    async def explain_rejection(
        self,
        artifact_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        """
        Explain why a candidate was rejected.

        Returns detailed information about the rejection:
        - Which rule failed
        - What scores were too low
        - What conflicts existed
        """
        if not self.supabase:
            return None

        try:
            result = self.supabase.table("memory_rejection_log").select("*").eq(
                "artifact_id", str(artifact_id)
            ).execute()

            if not result.data:
                return None

            rejection = result.data[0]

            return {
                "artifact_id": str(artifact_id),
                "title": rejection["title"],
                "summary": rejection.get("summary"),
                "rejection_reason": rejection["rejection_reason"],
                "rejection_message": rejection.get("rejection_message"),
                "failing_rule": rejection.get("failing_rule"),
                "scores_at_rejection": {
                    "confidence": rejection["confidence_score"],
                    "completeness": rejection["completeness_score"],
                },
                "rejected_at": rejection["rejected_at"],
                "can_be_resubmitted": self._can_be_resubmitted(rejection),
            }

        except Exception as e:
            logger.error(f"Error explaining rejection for {artifact_id}: {e}")
            return None

    def _can_be_resubmitted(self, rejection: Dict[str, Any]) -> bool:
        """Determine if a rejected candidate could be resubmitted."""
        reason = rejection["rejection_reason"]

        # Certain rejections are resubmittable
        resubmittable_reasons = [
            "low_confidence",
            "low_completeness",
            "temporal_conflict",
        ]

        return reason in resubmittable_reasons

    # ========================================================================
    # Retrieval Audit
    # ========================================================================

    async def get_retrieval_audit(
        self,
        memory_id: str,
        limit: int = 100,
    ) -> List[RetrievalAuditRecord]:
        """
        Get retrieval audit records for a memory.

        Shows all access events with query context.
        """
        if not self.supabase:
            return []

        try:
            result = self.supabase.table("memory_access_log").select("*").eq(
                "memory_id", memory_id
            ).order("accessed_at", desc=True).limit(limit).execute()

            records = []
            for entry in result.data or []:
                records.append(RetrievalAuditRecord(
                    id=UUID(entry["id"]),
                    memory_id=entry["memory_id"],
                    memory_uuid=UUID(entry["memory_uuid"]),
                    access_type=entry["access_type"],
                    accessed_at=datetime.fromisoformat(entry["accessed_at"]),
                    user_id=entry.get("user_id"),
                    session_id=entry.get("session_id"),
                    query_filters=entry.get("query_filters", {}),
                    results_count=entry.get("results_count", 0),
                    query_runtime_ms=entry.get("query_runtime_ms", 0),
                    workflow_type=entry.get("workflow_type"),
                    domain=entry.get("domain"),
                    execution_id=UUID(entry["execution_id"]) if entry.get("execution_id") else None,
                ))

            return records

        except Exception as e:
            logger.error(f"Error getting retrieval audit for {memory_id}: {e}")
            return []

    async def get_retrieval_summary(
        self,
        memory_id: str,
    ) -> Optional[RetrievalAuditSummary]:
        """
        Get summary of retrieval activity for a memory.

        Aggregates access by type and provides top users.
        """
        if not self.supabase:
            return None

        try:
            # Get all access records
            result = self.supabase.table("memory_access_log").select("*").eq(
                "memory_id", memory_id
            ).execute()

            records = result.data or []

            summary = RetrievalAuditSummary(memory_id=memory_id)
            summary.total_access_count = len(records)

            # Aggregate by access type
            query_count = 0
            injection_count = 0
            inspection_count = 0
            total_runtime = 0
            total_results = 0
            user_counts: Dict[str, int] = {}

            for record in records:
                access_type = record["access_type"]
                if access_type == "query":
                    query_count += 1
                elif access_type == "injection":
                    injection_count += 1
                elif access_type == "inspection":
                    inspection_count += 1

                total_runtime += record.get("query_runtime_ms", 0)
                total_results += record.get("results_count", 0)

                user_id = record.get("user_id")
                if user_id:
                    user_counts[user_id] = user_counts.get(user_id, 0) + 1

            summary.query_count = query_count
            summary.injection_count = injection_count
            summary.inspection_count = inspection_count

            if len(records) > 0:
                summary.avg_query_runtime_ms = total_runtime / len(records)
                summary.avg_results_per_query = total_results / max(1, query_count)

            # Top users
            summary.top_users = [
                {"user_id": uid, "access_count": count}
                for uid, count in sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            ]

            return summary

        except Exception as e:
            logger.error(f"Error getting retrieval summary for {memory_id}: {e}")
            return None

    # ========================================================================
    # Control Hooks
    # ========================================================================

    async def execute_governance_action(
        self,
        action: GovernanceAction,
    ) -> GovernanceActionResult:
        """
        Execute a governance control action.

        Actions:
        - disable: Disable memory from being queried
        - enable: Re-enable a disabled memory
        - expire: Force expiration of a memory
        - supersede: Mark memory as superseded by another
        - lock_quality: Lock quality gate version
        - unlock: Unlock quality gate
        """
        if not self.supabase:
            return GovernanceActionResult(
                success=False,
                action_type=action.action_type,
                memory_id=action.memory_id,
                error="No Supabase client available"
            )

        try:
            # Get current state
            current_result = self.supabase.table("strategic_memories").select("*").eq(
                "id", str(action.memory_id)
            ).execute()

            if not current_result.data:
                return GovernanceActionResult(
                    success=False,
                    action_type=action.action_type,
                    memory_id=action.memory_id,
                    error="Memory not found"
                )

            current_memory = current_result.data[0]
            before_state = {
                "status": current_memory.get("status"),
                "disabled": False,
                "expires_at": current_memory.get("expires_at"),
            }

            # Check if control state exists
            control_result = self.supabase.table("memory_control_state").select("*").eq(
                "memory_id", str(action.memory_id)
            ).execute()
            has_control = bool(control_result.data)

            if has_control:
                before_state.update({
                    "disabled": control_result.data[0].get("disabled", False),
                    "force_expiration": control_result.data[0].get("force_expiration", False),
                    "marked_for_supersession": control_result.data[0].get("marked_for_supersession", False),
                })

            # Execute action
            if action.action_type == "disable":
                await self._disable_memory(action, has_control)

            elif action.action_type == "enable":
                await self._enable_memory(action, has_control)

            elif action.action_type == "expire":
                await self._expire_memory(action, has_control)

            elif action.action_type == "supersede":
                await self._supersede_memory(action, has_control)

            elif action.action_type == "lock_quality":
                await self._lock_quality(action, has_control)

            elif action.action_type == "unlock":
                await self._unlock_quality(action, has_control)

            else:
                return GovernanceActionResult(
                    success=False,
                    action_type=action.action_type,
                    memory_id=action.memory_id,
                    error=f"Unknown action type: {action.action_type}"
                )

            # Get new state
            new_result = self.supabase.table("strategic_memories").select("*").eq(
                "id", str(action.memory_id)
            ).execute()
            after_state = {
                "status": new_result.data[0].get("status"),
                "expires_at": new_result.data[0].get("expires_at"),
            }

            if has_control:
                new_control = self.supabase.table("memory_control_state").select("*").eq(
                    "memory_id", str(action.memory_id)
                ).execute()
                if new_control.data:
                    after_state.update({
                        "disabled": new_control.data[0].get("disabled", False),
                        "force_expiration": new_control.data[0].get("force_expiration", False),
                        "marked_for_supersession": new_control.data[0].get("marked_for_supersession", False),
                    })

            return GovernanceActionResult(
                success=True,
                action_type=action.action_type,
                memory_id=action.memory_id,
                before_state=before_state,
                after_state=after_state,
                message=f"{action.action_type} action completed successfully",
            )

        except Exception as e:
            logger.error(f"Error executing governance action {action.action_type}: {e}")
            return GovernanceActionResult(
                success=False,
                action_type=action.action_type,
                memory_id=action.memory_id,
                error=str(e)
            )

    async def _disable_memory(self, action: GovernanceAction, has_control: bool):
        """Disable a memory from being queried."""
        if has_control:
            # Update existing control state
            self.supabase.table("memory_control_state").update({
                "disabled": True,
                "disabled_at": datetime.now().isoformat(),
                "disabled_by": action.performed_by,
                "disabled_reason": action.reason,
            }).eq("memory_id", str(action.memory_id)).execute()
        else:
            # Create new control state
            self.supabase.table("memory_control_state").insert({
                "memory_id": str(action.memory_id),
                "disabled": True,
                "disabled_at": datetime.now().isoformat(),
                "disabled_by": action.performed_by,
                "disabled_reason": action.reason,
                "controlled_by": action.performed_by,
            }).execute()

    async def _enable_memory(self, action: GovernanceAction, has_control: bool):
        """Re-enable a disabled memory."""
        if has_control:
            self.supabase.table("memory_control_state").update({
                "disabled": False,
                "disabled_at": None,
                "disabled_by": None,
                "disabled_reason": None,
            }).eq("memory_id", str(action.memory_id)).execute()

    async def _expire_memory(self, action: GovernanceAction, has_control: bool):
        """Force expiration of a memory."""
        expires_at = action.expires_at or datetime.now()

        # Update the memory itself
        self.supabase.table("strategic_memories").update({
            "expires_at": expires_at.isoformat(),
        }).eq("id", str(action.memory_id)).execute()

        # Also update control state
        if has_control:
            self.supabase.table("memory_control_state").update({
                "force_expiration": True,
                "forced_expires_at": expires_at.isoformat(),
            }).eq("memory_id", str(action.memory_id)).execute()
        else:
            self.supabase.table("memory_control_state").insert({
                "memory_id": str(action.memory_id),
                "force_expiration": True,
                "forced_expires_at": expires_at.isoformat(),
                "controlled_by": action.performed_by,
            }).execute()

    async def _supersede_memory(self, action: GovernanceAction, has_control: bool):
        """Mark memory as superseded by another."""
        if not action.superseded_by:
            raise ValueError("superseded_by memory ID is required for supersede action")

        # Update the memory
        self.supabase.table("strategic_memories").update({
            "status": MemoryStatus.SUPPLANTED.value,
            "supplanted_by_memory_id": str(action.superseded_by),
        }).eq("id", str(action.memory_id)).execute()

        # Create supersession record
        self.supabase.table("memory_supersessions").insert({
            "old_memory_id": str(action.memory_id),
            "new_memory_id": str(action.superseded_by),
            "reason": action.reason,
        }).execute()

    async def _lock_quality(self, action: GovernanceAction, has_control: bool):
        """Lock quality gate to a specific version."""
        if has_control:
            self.supabase.table("memory_control_state").update({
                "quality_gate_locked": True,
                "quality_gate_version": action.quality_gate_version,
            }).eq("memory_id", str(action.memory_id)).execute()
        else:
            self.supabase.table("memory_control_state").insert({
                "memory_id": str(action.memory_id),
                "quality_gate_locked": True,
                "quality_gate_version": action.quality_gate_version,
                "controlled_by": action.performed_by,
            }).execute()

    async def _unlock_quality(self, action: GovernanceAction, has_control: bool):
        """Unlock quality gate."""
        if has_control:
            self.supabase.table("memory_control_state").update({
                "quality_gate_locked": False,
                "quality_gate_version": None,
            }).eq("memory_id", str(action.memory_id)).execute()

    # ========================================================================
    # Governance Dashboard
    # ========================================================================

    async def get_memories_needing_attention(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get memories that need governance attention."""
        if not self.supabase:
            return []

        try:
            # Query the view
            result = self.supabase.table("memories_needing_governance").select("*").limit(limit).execute()
            return result.data or []

        except Exception as e:
            logger.error(f"Error getting memories needing attention: {e}")
            return []

    async def get_governance_statistics(self) -> Dict[str, Any]:
        """Get governance statistics."""
        if not self.supabase:
            return {}

        try:
            stats = {}

            # Total memories
            total_result = self.supabase.table("strategic_memories").select("id", count="exact").execute()
            stats["total_memories"] = total_result.count or 0

            # Disabled memories
            disabled_result = self.supabase.table("memory_control_state").select("id", count="exact").eq(
                "disabled", True
            ).execute()
            stats["disabled_count"] = disabled_result.count or 0

            # Rejections pending review
            rejection_result = self.supabase.table("memory_rejection_log").select("id", count="exact").eq(
                "reviewed", False
            ).execute()
            stats["rejections_pending_review"] = rejection_result.count or 0

            # Unresolved challenges
            challenge_result = self.supabase.table("memory_challenges").select("id", count="exact").eq(
                "resolved", False
            ).execute()
            stats["unresolved_challenges"] = challenge_result.count or 0

            return stats

        except Exception as e:
            logger.error(f"Error getting governance statistics: {e}")
            return {}


# ============================================================================
# Factory Functions
# ============================================================================

def get_memory_inspection_service(supabase_client: Optional[Any] = None) -> MemoryInspectionService:
    """
    Get a memory inspection service.

    Args:
        supabase_client: Optional Supabase client

    Returns:
        Configured inspection service
    """
    return MemoryInspectionService(supabase_client=supabase_client)
