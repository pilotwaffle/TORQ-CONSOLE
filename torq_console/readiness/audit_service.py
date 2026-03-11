"""
TORQ Readiness Checker - Audit Service

Milestone 4: Governance audit visibility and retrieval.

Provides access to transition history, governance actions,
and compliance auditing capabilities.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel

from .transition_controller import (
    TransitionAuditLog,
    get_audit_logs,
    add_audit_log,
    get_all_audit_logs,
)
from .inspection_models import (
    TransitionRecord,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Audit Filters
# ============================================================================

class TransitionAuditFilter(BaseModel):
    """
    Filter parameters for transition audit queries.
    """
    # Candidate filter
    candidate_id: Optional[UUID] = None

    # Actor filter
    actor: Optional[str] = None

    # State filter
    from_state: Optional[str] = None
    to_state: Optional[str] = None

    # Transition type filter
    transition_type: Optional[str] = None

    # Time range filter
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    # Forced transition filter
    forced_only: bool = False

    # Pagination
    limit: int = 100
    offset: int = 0

    # Sort order
    sort_order: str = "desc"  # desc = most recent first


# ============================================================================
# Audit Service
# ============================================================================

class ReadinessAuditService:
    """
    Service for accessing readiness governance audit logs.

    Provides visibility into all state transitions, governance actions,
    and compliance events.
    """

    def get_transition_history(
        self,
        candidate_id: UUID,
        limit: int = 100,
    ) -> List[TransitionRecord]:
        """
        Get transition history for a specific candidate.

        Args:
            candidate_id: ID of the candidate
            limit: Maximum number of records to return

        Returns:
            List of TransitionRecords, most recent first
        """
        audit_logs = get_audit_logs(candidate_id)

        # Sort by transition time descending
        audit_logs.sort(key=lambda l: l.transitioned_at, reverse=True)

        # Limit results
        audit_logs = audit_logs[:limit]

        return self._convert_to_records(audit_logs)

    def list_transitions(
        self,
        filters: Optional[TransitionAuditFilter] = None,
    ) -> List[TransitionRecord]:
        """
        List transitions with optional filtering.

        Args:
            filters: Optional filter parameters

        Returns:
            List of matching TransitionRecords
        """
        if filters is None:
            filters = TransitionAuditFilter()

        # Collect all audit logs across all candidates
        all_audit_logs = get_all_audit_logs()
        all_logs: List[TransitionAuditLog] = []
        for logs in all_audit_logs.values():
            all_logs.extend(logs)

        # Apply filters
        filtered = all_logs

        if hasattr(filters, 'candidate_id') and filters.candidate_id:
            filtered = [log for log in filtered if log.candidate_id == filters.candidate_id]

        if hasattr(filters, 'actor') and filters.actor:
            filtered = [log for log in filtered if log.triggered_by == filters.actor]

        if hasattr(filters, 'from_state') and filters.from_state:
            filtered = [log for log in filtered if log.from_state.value == filters.from_state]

        if hasattr(filters, 'to_state') and filters.to_state:
            filtered = [log for log in filtered if log.to_state.value == filters.to_state]

        if hasattr(filters, 'transition_type') and filters.transition_type:
            filtered = [log for log in filtered if log.transition_type == filters.transition_type]

        if hasattr(filters, 'start_time') and filters.start_time:
            filtered = [log for log in filtered if log.transitioned_at >= filters.start_time]

        if hasattr(filters, 'end_time') and filters.end_time:
            filtered = [log for log in filtered if log.transitioned_at <= filters.end_time]

        if hasattr(filters, 'forced_only') and filters.forced_only:
            filtered = [log for log in filtered if log.force_used]

        # Sort
        reverse = filters.sort_order.lower() == "desc"
        filtered.sort(key=lambda l: l.transitioned_at, reverse=reverse)

        # Paginate
        start = filters.offset
        end = start + filters.limit
        paginated = filtered[start:end]

        return self._convert_to_records(paginated)

    def get_forced_transitions(
        self,
        candidate_id: Optional[UUID] = None,
        limit: int = 100,
    ) -> List[TransitionRecord]:
        """
        Get all forced transitions.

        Args:
            candidate_id: Optional candidate filter
            limit: Maximum number of records

        Returns:
            List of forced transition records
        """
        filters = TransitionAuditFilter(
            candidate_id=candidate_id,
            forced_only=True,
            limit=limit,
        )
        return self.list_transitions(filters)

    def get_governance_override_count(
        self,
        candidate_id: Optional[UUID] = None,
    ) -> int:
        """
        Count governance override actions.

        Args:
            candidate_id: Optional candidate filter

        Returns:
            Number of governance overrides
        """
        filters = TransitionAuditFilter(
            candidate_id=candidate_id,
            forced_only=True,
            limit=10000,  # High limit for counting
        )

        records = self.list_transitions(filters)
        return sum(1 for r in records if r.governance_override)

    def get_transitions_by_actor(
        self,
        actor: str,
        limit: int = 100,
    ) -> List[TransitionRecord]:
        """
        Get all transitions performed by a specific actor.

        Args:
            actor: Actor identifier (user ID or system)
            limit: Maximum number of records

        Returns:
            List of transition records
        """
        filters = TransitionAuditFilter(
            actor=actor,
            limit=limit,
        )
        return self.list_transitions(filters)

    def get_compliance_summary(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get compliance summary for a time period.

        Args:
            start_time: Start of period (optional)
            end_time: End of period (optional)

        Returns:
            Dictionary with compliance metrics
        """
        filters = TransitionAuditFilter(
            start_time=start_time,
            end_time=end_time,
            limit=10000,
        )

        all_transitions = self.list_transitions(filters)

        # Compute metrics
        total_transitions = len(all_transitions)
        forced_transitions = sum(1 for t in all_transitions if t.forced)
        governance_overrides = sum(1 for t in all_transitions if t.governance_override)

        # Count by transition type
        transition_types: Dict[str, int] = {}
        for transition in all_transitions:
            ttype = transition.transition_type
            transition_types[ttype] = transition_types.get(ttype, 0) + 1

        # Count by actor
        actor_counts: Dict[str, int] = {}
        for transition in all_transitions:
            actor = transition.triggered_by
            actor_counts[actor] = actor_counts.get(actor, 0) + 1

        return {
            "total_transitions": total_transitions,
            "forced_transitions": forced_transitions,
            "forced_transition_rate": forced_transitions / total_transitions if total_transitions > 0 else 0.0,
            "governance_overrides": governance_overrides,
            "transition_types": transition_types,
            "actor_counts": actor_counts,
            "period_start": start_time.isoformat() if start_time else None,
            "period_end": end_time.isoformat() if end_time else None,
        }

    def _convert_to_records(
        self,
        audit_logs: List[TransitionAuditLog],
    ) -> List[TransitionRecord]:
        """Convert audit logs to transition records."""
        records = []

        for log in audit_logs:
            record = TransitionRecord(
                id=log.id,
                candidate_id=log.candidate_id,
                from_state=log.from_state.value,
                to_state=log.to_state.value,
                transition_type=log.transition_type,
                triggered_by=log.triggered_by,
                trigger_reason=log.trigger_reason,
                evaluation_id=log.evaluation_id,
                evaluation_score=log.evaluation_score,
                evaluation_outcome=log.evaluation_outcome.value if log.evaluation_outcome else None,
                policy_profile_id=log.policy_profile_id,
                policy_version=log.policy_version,
                forced=log.force_used,
                governance_override=log.governance_override,
                approved_by=log.approved_by,
                transitioned_at=log.transitioned_at,
                duration_ms=log.transition_duration_ms,
                state_locked=log.previous_state_locked,
            )
            records.append(record)

        return records


# Global audit service instance
_audit_service: Optional[ReadinessAuditService] = None


def get_audit_service() -> ReadinessAuditService:
    """Get the global audit service instance."""
    global _audit_service
    if _audit_service is None:
        _audit_service = ReadinessAuditService()
    return _audit_service
