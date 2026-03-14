"""
Exchange Tracker for Federation Layer

Phase 1B - Track end-to-end federation exchange lifecycle.

This module tracks the full path of a federated claim:
- Published (Node A creates and sends)
- In Transit (network transport)
- Received (Node B receives)
- Processing (Node B validates)
- Completed (final disposition)

The tracker enables correlation_id-based tracing across nodes.
"""

import logging
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Any, Literal
from pydantic import BaseModel, Field

from torq_console.layer12.federation.types import FederatedClaimEnvelope

logger = logging.getLogger(__name__)


# ============================================================================
# Exchange Event Types
# ============================================================================

class ExchangeEventType:
    """Types of exchange events."""
    PUBLISHED = "published"
    DISPATCHED = "dispatched"
    IN_TRANSIT = "in_transit"
    RECEIVED = "received"
    VALIDATING = "validating"
    IDENTITY_CHECKED = "identity_checked"
    SIGNATURE_CHECKED = "signature_checked"
    REPLAY_CHECKED = "replay_checked"
    DUPLICATE_CHECKED = "duplicate_checked"
    TRUST_DECIDED = "trust_decided"
    ACCEPTED = "accepted"
    QUARANTINED = "quarantined"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================================
# Exchange Event
# ============================================================================

class ExchangeEvent(BaseModel):
    """A single event in the exchange lifecycle."""

    event_id: str = Field(..., description="Unique event ID")
    event_type: str = Field(..., description="Type of event")
    correlation_id: str = Field(..., description="Correlation ID for the exchange")
    envelope_id: str = Field(..., description="Envelope ID")
    node_id: str = Field(..., description="Node where event occurred")
    timestamp: datetime = Field(..., description="When the event occurred")
    source_node_id: str | None = Field(None, description="Source node ID (for receive events)")
    target_node_id: str | None = Field(None, description="Target node ID (for publish events)")
    status: str | None = Field(None, description="Status result for validation events")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional event details")
    error_message: str | None = Field(None, description="Error message if failed")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "eventId": self.event_id,
            "eventType": self.event_type,
            "correlationId": self.correlation_id,
            "envelopeId": self.envelope_id,
            "nodeId": self.node_id,
            "timestamp": self.timestamp.isoformat(),
            "sourceNodeId": self.source_node_id,
            "targetNodeId": self.target_node_id,
            "status": self.status,
            "details": self.details,
            "errorMessage": self.error_message,
        }


# ============================================================================
# Exchange Trace
# ============================================================================

class ExchangeTrace(BaseModel):
    """Complete trace of a federation exchange."""

    correlation_id: str = Field(..., description="Correlation ID for the exchange")
    envelope_id: str = Field(..., description="Envelope ID")
    source_node_id: str = Field(..., description="Publishing node ID")
    target_node_id: str | None = Field(None, description="Target node ID (null for broadcast)")
    created_at: datetime = Field(..., description="When the exchange was created")
    status: Literal["pending", "in_progress", "completed", "failed"] = Field(..., description="Exchange status")
    final_disposition: Literal["accepted", "quarantined", "rejected"] | None = Field(None, description="Final claim disposition")
    events: list[ExchangeEvent] = Field(default_factory=list, description="Timeline of events")

    def add_event(self, event: ExchangeEvent) -> None:
        """Add an event to the trace."""
        self.events.append(event)
        self.events.sort(key=lambda e: e.timestamp)

    def get_events_by_type(self, event_type: str) -> list[ExchangeEvent]:
        """Get all events of a specific type."""
        return [e for e in self.events if e.event_type == event_type]

    def latest_event(self) -> ExchangeEvent | None:
        """Get the most recent event."""
        return self.events[-1] if self.events else None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "correlationId": self.correlation_id,
            "envelopeId": self.envelope_id,
            "sourceNodeId": self.source_node_id,
            "targetNodeId": self.target_node_id,
            "createdAt": self.created_at.isoformat(),
            "status": self.status,
            "finalDisposition": self.final_disposition,
            "eventCount": len(self.events),
            "events": [e.to_dict() for e in self.events],
        }


# ============================================================================
# Exchange Tracker Configuration
# ============================================================================

class ExchangeTrackerConfig(BaseModel):
    """Configuration for exchange tracking."""

    max_tracked_exchanges: int = Field(10000, description="Maximum exchanges to track")
    exchange_ttl_seconds: int = Field(86400 * 7, description="Time before exchange records expire (7 days)")
    enable_event_persistence: bool = Field(True, description="Persist events to storage")
    cleanup_interval_seconds: int = Field(3600, description="Interval between cleanup runs")


# ============================================================================
# Exchange Tracker Service
# ============================================================================

class ExchangeTrackerService:
    """
    Tracks federation exchanges end-to-end.

    This service maintains a complete audit trail of all federation
    exchanges, enabling:
    - Correlation ID-based tracing
    - End-to-end lifecycle visibility
    - Debugging and diagnostics
    - Compliance auditing
    """

    def __init__(self, config: ExchangeTrackerConfig | None = None):
        """
        Initialize the exchange tracker.

        Args:
            config: Tracker configuration
        """
        self.config = config or ExchangeTrackerConfig()
        self.logger = logging.getLogger(__name__)

        # Track exchanges by correlation_id
        self._exchanges: OrderedDict[str, ExchangeTrace] = OrderedDict()

        # Track exchanges by envelope_id (reverse lookup)
        self._envelope_to_correlation: dict[str, str] = {}

        # Statistics
        self._total_tracked = 0
        self._service_started_at = datetime.utcnow()

    def _generate_event_id(self) -> str:
        """Generate a unique event ID."""
        import uuid
        return f"evt_{uuid.uuid4().hex}"

    def create_exchange(
        self,
        correlation_id: str,
        envelope_id: str,
        source_node_id: str,
        target_node_id: str | None = None,
    ) -> ExchangeTrace:
        """
        Create a new exchange trace.

        Args:
            correlation_id: Correlation ID for the exchange
            envelope_id: Envelope ID being exchanged
            source_node_id: Publishing node ID
            target_node_id: Target node ID

        Returns:
            ExchangeTrace for tracking
        """
        trace = ExchangeTrace(
            correlation_id=correlation_id,
            envelope_id=envelope_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            created_at=datetime.utcnow(),
            status="pending",
        )

        self._exchanges[correlation_id] = trace
        self._envelope_to_correlation[envelope_id] = correlation_id
        self._total_tracked += 1

        self.logger.debug(f"Created exchange trace: {correlation_id}")
        return trace

    def record_event(
        self,
        correlation_id: str,
        event_type: str,
        node_id: str,
        envelope_id: str | None = None,
        status: str | None = None,
        details: dict[str, Any] | None = None,
        error_message: str | None = None,
        source_node_id: str | None = None,
        target_node_id: str | None = None,
    ) -> ExchangeEvent:
        """
        Record an event in an exchange trace.

        Args:
            correlation_id: Correlation ID for the exchange
            event_type: Type of event
            node_id: Node where event occurred
            envelope_id: Envelope ID (optional, looked up from correlation_id if None)
            status: Status result (for validation events)
            details: Additional event details
            error_message: Error message if failed
            source_node_id: Source node ID
            target_node_id: Target node ID

        Returns:
            The recorded ExchangeEvent
        """
        trace = self._exchanges.get(correlation_id)
        if trace is None:
            self.logger.warning(f"Exchange trace not found: {correlation_id}")
            # Create trace if it doesn't exist
            trace = self.create_exchange(
                correlation_id=correlation_id,
                envelope_id=envelope_id or "unknown",
                source_node_id=source_node_id or node_id,
                target_node_id=target_node_id,
            )

        if envelope_id is None:
            envelope_id = trace.envelope_id

        event = ExchangeEvent(
            event_id=self._generate_event_id(),
            event_type=event_type,
            correlation_id=correlation_id,
            envelope_id=envelope_id,
            node_id=node_id,
            timestamp=datetime.utcnow(),
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            status=status,
            details=details or {},
            error_message=error_message,
        )

        trace.add_event(event)
        self._exchanges.move_to_end(correlation_id)

        # Update exchange status based on event type
        self._update_exchange_status(trace, event)

        return event

    def _update_exchange_status(self, trace: ExchangeTrace, event: ExchangeEvent) -> None:
        """Update exchange status based on the latest event."""
        if event.event_type in (ExchangeEventType.FAILED,):
            trace.status = "failed"
        elif event.event_type in (ExchangeEventType.ACCEPTED, ExchangeEventType.QUARANTINED, ExchangeEventType.REJECTED):
            trace.status = "completed"
            if event.event_type == ExchangeEventType.ACCEPTED:
                trace.final_disposition = "accepted"
            elif event.event_type == ExchangeEventType.QUARANTINED:
                trace.final_disposition = "quarantined"
            elif event.event_type == ExchangeEventType.REJECTED:
                trace.final_disposition = "rejected"
        elif event.event_type in (ExchangeEventType.DISPATCHED, ExchangeEventType.IN_TRANSIT, ExchangeEventType.RECEIVED):
            trace.status = "in_progress"

    def get_exchange_trace(self, correlation_id: str) -> ExchangeTrace | None:
        """
        Get the complete exchange trace by correlation ID.

        Args:
            correlation_id: Correlation ID to look up

        Returns:
            ExchangeTrace if found, None otherwise
        """
        return self._exchanges.get(correlation_id)

    def get_exchange_by_envelope(self, envelope_id: str) -> ExchangeTrace | None:
        """
        Get exchange trace by envelope ID.

        Args:
            envelope_id: Envelope ID to look up

        Returns:
            ExchangeTrace if found, None otherwise
        """
        correlation_id = self._envelope_to_correlation.get(envelope_id)
        if correlation_id:
            return self._exchanges.get(correlation_id)
        return None

    def list_exchanges(
        self,
        source_node_id: str | None = None,
        target_node_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ExchangeTrace]:
        """
        List exchange traces with optional filtering.

        Args:
            source_node_id: Filter by source node
            target_node_id: Filter by target node
            status: Filter by status
            limit: Maximum results to return
            offset: Pagination offset

        Returns:
            List of ExchangeTrace (newest first)
        """
        traces = list(reversed(self._exchanges.values()))

        # Apply filters
        if source_node_id:
            traces = [t for t in traces if t.source_node_id == source_node_id]
        if target_node_id:
            traces = [t for t in traces if t.target_node_id == target_node_id]
        if status:
            traces = [t for t in traces if t.status == status]

        # Apply pagination
        return traces[offset:offset + limit]

    def _cleanup_expired_exchanges(self) -> None:
        """Remove expired exchange traces."""
        cutoff = datetime.utcnow() - timedelta(seconds=self.config.exchange_ttl_seconds)

        expired = [
            correlation_id for correlation_id, trace in self._exchanges.items()
            if trace.created_at < cutoff
        ]

        for correlation_id in expired:
            trace = self._exchanges.pop(correlation_id, None)
            if trace:
                self._envelope_to_correlation.pop(trace.envelope_id, None)

        if expired:
            self.logger.debug(f"Cleaned up {len(expired)} expired exchange traces")

        # Enforce LRU limit
        while len(self._exchanges) > self.config.max_tracked_exchanges:
            self._exchanges.popitem(last=False)

    def get_statistics(self) -> dict[str, Any]:
        """Get tracker statistics."""
        uptime = (datetime.utcnow() - self._service_started_at).total_seconds()

        # Count by status
        status_counts: dict[str, int] = {}
        for trace in self._exchanges.values():
            status_counts[trace.status] = status_counts.get(trace.status, 0) + 1

        return {
            "totalTracked": self._total_tracked,
            "activeExchanges": len(self._exchanges),
            "statusBreakdown": status_counts,
            "uptimeSeconds": uptime,
            "serviceStartedAt": self._service_started_at.isoformat(),
        }


# ============================================================================
# Global Tracker Instance
# =============================================================================

_global_tracker: ExchangeTrackerService | None = None


def get_exchange_tracker() -> ExchangeTrackerService:
    """Get the global exchange tracker instance."""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = ExchangeTrackerService()
    return _global_tracker


def create_exchange_tracker(config: ExchangeTrackerConfig | None = None) -> ExchangeTrackerService:
    """
    Factory function to create an ExchangeTrackerService.

    Args:
        config: Tracker configuration

    Returns:
        Configured ExchangeTrackerService instance
    """
    return ExchangeTrackerService(config=config)
