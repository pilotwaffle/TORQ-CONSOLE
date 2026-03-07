"""
Execution Provenance Tracking

Phase 8 Hardening: Production-grade traceability for all external actions.

This module provides complete traceability from trigger to verification,
ensuring every action can be audited and debugged.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


logger = __import__("logging").getLogger(__name__)


# ============================================================================
# Enums
# ============================================================================

class ProvenanceEventType(str, Enum):
    """Types of provenance events."""
    TRIGGER_CREATED = "trigger_created"
    PLAN_GENERATED = "plan_generated"
    PLAN_APPROVED = "plan_approved"
    PLAN_DENIED = "plan_denied"
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    NODE_STARTED = "node_started"
    NODE_COMPLETED = "node_completed"
    NODE_FAILED = "node_failed"
    ACTION_SUBMITTED = "action_submitted"
    ACTION_EXECUTING = "action_executing"
    ACTION_SUCCEEDED = "action_succeeded"
    ACTION_FAILED = "action_failed"
    ACTION_RETRYING = "action_retrying"
    VERIFICATION_PASSED = "verification_passed"
    VERIFICATION_FAILED = "verification_failed"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_DENIED = "approval_denied"
    CIRCUIT_BREAKER_OPENED = "circuit_breaker_opened"
    CIRCUIT_BREAKER_CLOSED = "circuit_breaker_closed"


# ============================================================================
# Provenance Models
# ============================================================================

class ExecutionProvenance(BaseModel):
    """
    Complete provenance record for an action execution.

    This links together the entire execution chain:
    trigger -> plan -> approval -> workflow -> node -> connector action -> result
    """
    provenance_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Root trace ID (all related actions share this)
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Execution chain
    trigger_id: Optional[str] = None  # What triggered this execution
    trigger_type: Optional[str] = None  # "monitor", "user", "schedule", "api"
    trigger_data: Dict[str, Any] = Field(default_factory=dict)

    plan_id: Optional[str] = None  # Preparation plan if applicable
    approval_id: Optional[str] = None  # Approval request if applicable

    workflow_execution_id: Optional[str] = None  # Workflow execution
    workflow_id: Optional[str] = None  # Workflow definition
    node_id: Optional[str] = None  # Workflow node

    # Action details
    action_id: str  # External action ID
    connector_type: str
    action_type: str
    idempotency_key: Optional[str] = None  # For deduplication

    # Execution details
    workspace_id: Optional[str] = None
    environment: Optional[str] = None
    requested_by: Optional[str] = None  # User or agent

    # Risk and approval
    risk_level: str = "MEDIUM"
    required_approval: bool = False
    granted_approval: bool = False
    approver: Optional[str] = None

    # Execution results
    status: str = "pending"  # pending, running, succeeded, failed, cancelled
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None

    # Connector health
    connector_healthy: bool = True
    circuit_breaker_open: bool = False

    # Timing
    created_at: float = Field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    duration_seconds: Optional[float] = None

    # Verification
    verified: bool = False
    verification_message: Optional[str] = None

    # Retry info
    retry_count: int = 0
    max_retries: int = 3

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Links to related provenance records
    parent_provenance_id: Optional[str] = None
    child_provenance_ids: List[str] = Field(default_factory=list)


class ProvenanceEvent(BaseModel):
    """Individual event in the provenance chain."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provenance_id: str  # Links to ExecutionProvenance
    trace_id: str  # Root trace ID

    event_type: ProvenanceEventType
    timestamp: float = Field(default_factory=time.time)

    # Event data
    data: Dict[str, Any] = Field(default_factory=dict)

    # Source
    source: str = "system"  # "user", "agent", "system", "connector"
    source_id: Optional[str] = None

    # Context
    workspace_id: Optional[str] = None
    environment: Optional[str] = None


# ============================================================================
# Provenance Store
# ============================================================================

class ProvenanceStore:
    """
    Stores and queries execution provenance records.

    Provides complete traceability for:
    - Auditing actions
    - Debugging failures
    - Analyzing performance
    - Compliance reporting
    """

    def __init__(self):
        self._provenance: Dict[str, ExecutionProvenance] = {}
        self._events: List[ProvenanceEvent] = []
        self._by_trace_id: Dict[str, List[str]] = {}  # trace_id -> [provenance_ids]
        self._by_idempotency: Dict[str, str] = {}  # idempotency_key -> provenance_id

        self.logger = logger

    def create_provenance(
        self,
        action_id: str,
        connector_type: str,
        action_type: str,
        trace_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        **kwargs
    ) -> ExecutionProvenance:
        """Create a new provenance record."""
        trace_id = trace_id or str(uuid.uuid4())

        # Check for existing idempotency key
        if idempotency_key and idempotency_key in self._by_idempotency:
            existing_id = self._by_idempotency[idempotency_key]
            existing = self._provenance.get(existing_id)
            if existing:
                self.logger.info(f"Idempotency key hit: {idempotency_key}")
                return existing

        provenance = ExecutionProvenance(
            action_id=action_id,
            connector_type=connector_type,
            action_type=action_type,
            trace_id=trace_id,
            idempotency_key=idempotency_key,
            **kwargs
        )

        self._provenance[provenance.provenance_id] = provenance

        if trace_id not in self._by_trace_id:
            self._by_trace_id[trace_id] = []
        self._by_trace_id[trace_id].append(provenance.provenance_id)

        if idempotency_key:
            self._by_idempotency[idempotency_key] = provenance.provenance_id

        # Record creation event
        self.record_event(
            provenance.provenance_id,
            trace_id,
            ProvenanceEventType.ACTION_SUBMITTED,
            data={"action_id": action_id, "connector": connector_type}
        )

        return provenance

    def record_event(
        self,
        provenance_id: str,
        trace_id: str,
        event_type: ProvenanceEventType,
        data: Optional[Dict[str, Any]] = None,
        source: str = "system",
        source_id: Optional[str] = None
    ) -> ProvenanceEvent:
        """Record a provenance event."""
        event = ProvenanceEvent(
            provenance_id=provenance_id,
            trace_id=trace_id,
            event_type=event_type,
            data=data or {},
            source=source,
            source_id=source_id
        )

        self._events.append(event)

        # Update provenance status based on event
        provenance = self._provenance.get(provenance_id)
        if provenance:
            self._update_provenance_from_event(provenance, event)

        return event

    def _update_provenance_from_event(self, provenance: ExecutionProvenance, event: ProvenanceEvent) -> None:
        """Update provenance based on event."""
        if event.event_type == ProvenanceEventType.ACTION_EXECUTING:
            provenance.status = "running"
            provenance.started_at = event.timestamp
        elif event.event_type == ProvenanceEventType.ACTION_SUCCEEDED:
            provenance.status = "succeeded"
            provenance.completed_at = event.timestamp
            if provenance.started_at:
                provenance.duration_seconds = event.timestamp - provenance.started_at
        elif event.event_type == ProvenanceEventType.ACTION_FAILED:
            provenance.status = "failed"
            provenance.completed_at = event.timestamp
            provenance.error_message = event.data.get("error")
            provenance.error_code = event.data.get("error_code")
            if provenance.started_at:
                provenance.duration_seconds = event.timestamp - provenance.started_at
        elif event.event_type == ProvenanceEventType.VERIFICATION_PASSED:
            provenance.verified = True
            provenance.verification_message = event.data.get("message")
        elif event.event_type == ProvenanceEventType.VERIFICATION_FAILED:
            provenance.verified = False
            provenance.verification_message = event.data.get("message")
        elif event.event_type == ProvenanceEventType.APPROVAL_GRANTED:
            provenance.granted_approval = True
            provenance.approver = event.data.get("approver")
        elif event.event_type == ProvenanceEventType.CIRCUIT_BREAKER_OPENED:
            provenance.circuit_breaker_open = True

    def get_provenance(self, provenance_id: str) -> Optional[ExecutionProvenance]:
        """Get a provenance record by ID."""
        return self._provenance.get(provenance_id)

    def get_by_action_id(self, action_id: str) -> Optional[ExecutionProvenance]:
        """Get provenance by action ID."""
        for p in self._provenance.values():
            if p.action_id == action_id:
                return p
        return None

    def get_by_idempotency_key(self, idempotency_key: str) -> Optional[ExecutionProvenance]:
        """Get provenance by idempotency key."""
        provenance_id = self._by_idempotency.get(idempotency_key)
        if provenance_id:
            return self._provenance.get(provenance_id)
        return None

    def get_by_trace(self, trace_id: str) -> List[ExecutionProvenance]:
        """Get all provenance records for a trace."""
        provenance_ids = self._by_trace_id.get(trace_id, [])
        return [
            self._provenance[pid]
            for pid in provenance_ids
            if pid in self._provenance
        ]

    def get_events(self, provenance_id: str) -> List[ProvenanceEvent]:
        """Get all events for a provenance record."""
        return [
            e for e in self._events
            if e.provenance_id == provenance_id
        ]

    def get_trace_events(self, trace_id: str) -> List[ProvenanceEvent]:
        """Get all events for a trace."""
        return [
            e for e in self._events
            if e.trace_id == trace_id
        ]

    def query(
        self,
        workspace_id: Optional[str] = None,
        connector_type: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        limit: int = 100
    ) -> List[ExecutionProvenance]:
        """Query provenance records with filters."""
        results = list(self._provenance.values())

        if workspace_id:
            results = [p for p in results if p.workspace_id == workspace_id]

        if connector_type:
            results = [p for p in results if p.connector_type == connector_type]

        if status:
            results = [p for p in results if p.status == status]

        if start_time:
            results = [p for p in results if p.created_at >= start_time]

        if end_time:
            results = [p for p in results if p.created_at <= end_time]

        # Sort by created_at descending
        results.sort(key=lambda p: p.created_at, reverse=True)

        return results[:limit]

    def get_statistics(self) -> Dict[str, Any]:
        """Get provenance statistics."""
        total = len(self._provenance)
        by_status = {}
        by_connector = {}
        by_workspace = {}

        for p in self._provenance.values():
            by_status[p.status] = by_status.get(p.status, 0) + 1
            by_connector[p.connector_type] = by_connector.get(p.connector_type, 0) + 1
            if p.workspace_id:
                by_workspace[p.workspace_id] = by_workspace.get(p.workspace_id, 0) + 1

        return {
            "total_provenance": total,
            "total_events": len(self._events),
            "by_status": by_status,
            "by_connector": by_connector,
            "by_workspace": by_workspace,
            "unique_traces": len(self._by_trace_id),
            "idempotency_keys": len(self._by_idempotency),
        }


# ============================================================================
# Singleton
# ============================================================================

_global_store: Optional[ProvenanceStore] = None


def get_provenance_store() -> ProvenanceStore:
    """Get the global provenance store."""
    global _global_store
    if _global_store is None:
        _global_store = ProvenanceStore()
    return _global_store


# Export
__all__ = [
    'ProvenanceEventType',
    'ExecutionProvenance',
    'ProvenanceEvent',
    'ProvenanceStore',
    'get_provenance_store',
]
