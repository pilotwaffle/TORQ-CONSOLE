"""
Execution Fabric - Context Bus

Event-driven internal runtime for mission coordination.

Provides shared mission context across all agents and workstreams,
enabling reactive coordination without constant re-reading.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import UUID, uuid4
from collections import defaultdict

from .models import NodeType, NodeStatus


logger = logging.getLogger(__name__)


# ============================================================================
# Event Types
# ============================================================================

class MissionEventType(str, Enum):
    """Types of mission events on the context bus."""
    # Node lifecycle
    NODE_STARTED = "node.started"
    NODE_COMPLETED = "node.completed"
    NODE_FAILED = "node.failed"
    NODE_BLOCKED = "node.blocked"
    NODE_SKIPPED = "node.skipped"

    # Evidence & artifacts
    EVIDENCE_ADDED = "evidence.added"
    EVIDENCE_WITHDRAWN = "evidence.withdrawn"
    ARTIFACT_PRODUCED = "artifact.produced"

    # Risk & issues
    RISK_ESCALATED = "risk.escalated"
    RISK_MITIGATED = "risk.mitigated"
    BLOCKER_IDENTIFIED = "blocker.identified"
    BLOCKER_RESOLVED = "blocker.resolved"

    # Decision gates
    DECISION_REQUIRED = "decision.required"
    DECISION_MADE = "decision.made"
    DECISION_OVERRIDDEN = "decision.overridden"

    # Workstream
    WORKSTREAM_BLOCKED = "workstream.blocked"
    WORKSTREAM_UNBLOCKED = "workstream.unblocked"
    WORKSTREAM_PHASE_COMPLETE = "workstream.phase_complete"

    # Deliverable
    DELIVERABLE_READY = "deliverable.ready_for_synthesis"
    DELIVERABLE_COMPLETED = "deliverable.completed"

    # Mission control
    MISSION_PAUSED = "mission.paused"
    MISSION_RESUMED = "mission.resumed"
    MISSION_REPLANNING = "mission.replanning"
    MISSION_CANCELLED = "mission.cancelled"

    # Human interaction
    HUMAN_INPUT_REQUIRED = "human.input_required"
    HUMAN_APPROVAL_OBTAINED = "human.approval_obtained"
    HUMAN_OVERRIDE = "human.override"


# ============================================================================
# Event Model
# ============================================================================

@dataclass
class MissionEvent:
    """An event on the mission context bus."""
    mission_id: str
    event_type: MissionEventType
    id: str = field(default_factory=lambda: str(uuid4()))
    payload: Dict[str, Any] = field(default_factory=dict)

    # Source information
    source_node_id: Optional[str] = None
    source_agent_type: Optional[str] = None
    source_workstream_id: Optional[str] = None

    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    priority: str = "normal"  # low, normal, high, critical
    correlation_id: Optional[str] = None  # Link related events

    # Processing
    processed_by: List[str] = field(default_factory=list)  # Agent IDs that processed this
    acknowledged: bool = False


# ============================================================================
# Event Bus
# ============================================================================

class MissionContextBus:
    """
    Event-driven context bus for mission coordination.

    Maintains shared mission state and broadcasts events to
    subscribed agents and workstreams.
    """

    def __init__(self, supabase_client=None):
        self.supabase = supabase_client

        # Event storage
        self.events: Dict[str, MissionEvent] = {}

        # Subscriptions
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.node_subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.workstream_subscribers: Dict[str, List[Callable]] = defaultdict(list)

        # Event filters for subscriptions
        self.filters: Dict[str, Callable[[MissionEvent], bool]] = {}

    async def emit(
        self,
        event: MissionEvent
    ) -> List[str]:
        """
        Emit an event to the context bus.

        Returns list of subscriber IDs that received the event.
        """
        # Store event
        self.events[event.id] = event

        # Persist to database if available
        if self.supabase:
            await self._persist_event(event)

        # Deliver to matching subscribers
        delivered = []

        # Global subscribers
        for sub_id, subscriber in self.subscribers.items():
            if self._matches_filter(event, sub_id):
                try:
                    if isinstance(subscriber, str):
                        # String = agent ID to notify
                        delivered.append(sub_id)
                    else:
                        # Callable = async function to call
                        await subscriber(event)
                        delivered.append(sub_id)
                except Exception as e:
                    logger.error(f"Error delivering to subscriber {sub_id}: {e}")

        # Node-specific subscribers
        if event.source_node_id:
            for sub_id, subscriber in self.node_subscribers.get(event.source_node_id, {}).items():
                delivered.append(sub_id)
                try:
                    await subscriber(event)
                except Exception as e:
                    logger.error(f"Error delivering to node subscriber {sub_id}: {e}")

        # Workstream-specific subscribers
        if event.source_workstream_id:
            for sub_id, subscriber in self.workstream_subscribers.get(event.source_workstream_id, {}).items():
                delivered.append(sub_id)
                try:
                    await subscriber(event)
                except Exception as e:
                    logger.error(f"Error delivering to workstream subscriber {sub_id}: {e}")

        logger.debug(f"Event {event.event_type} emitted to {len(delivered)} subscribers")

        return delivered

    async def emit_node_completed(
        self,
        mission_id: str,
        node_id: str,
        agent_type: str,
        handoff_packet: Dict[str, Any],
        workstream_id: Optional[str] = None
    ):
        """Emit a node completion event with handoff data."""
        event = MissionEvent(
            mission_id=mission_id,
            event_type=MissionEventType.NODE_COMPLETED,
            payload={
                "node_id": node_id,
                "handoff_packet": handoff_packet
            },
            source_node_id=node_id,
            source_agent_type=agent_type,
            source_workstream_id=workstream_id
        )

        return await self.emit(event)

    async def emit_decision_required(
        self,
        mission_id: str,
        node_id: str,
        condition: Dict[str, Any],
        current_value: float
    ):
        """Emit a decision required event."""
        event = MissionEvent(
            mission_id=mission_id,
            event_type=MissionEventType.DECISION_REQUIRED,
            payload={
                "node_id": node_id,
                "condition": condition,
                "current_value": current_value
            },
            source_node_id=node_id,
            priority="high"
        )

        return await self.emit(event)

    async def emit_risk_escalated(
        self,
        mission_id: str,
        risk_description: str,
        severity: str,
        source_node_id: str,
        confidence: float,
        recommendations: List[str]
    ):
        """Emit a risk escalation event."""
        event = MissionEvent(
            mission_id=mission_id,
            event_type=MissionEventType.RISK_ESCALATED,
            payload={
                "risk_description": risk_description,
                "severity": severity,
                "confidence": confidence,
                "recommendations": recommendations
            },
            source_node_id=source_node_id,
            priority="high" if severity in ["critical", "high"] else "normal"
        )

        return await self.emit(event)

    async def get_recent_events(
        self,
        mission_id: str,
        event_types: Optional[List[MissionEventType]] = None,
        limit: int = 50
    ) -> List[MissionEvent]:
        """Get recent events for a mission."""
        since = datetime.now()

        events = []
        for event in self.events.values():
            if event.mission_id != mission_id:
                continue

            if event_types and event.event_type not in event_types:
                continue

            events.append(event)

        # Sort by timestamp descending
        events.sort(key=lambda e: e.timestamp, reverse=True)

        return events[:limit]

    # ========================================================================
    # Subscriptions
    # ========================================================================

    def subscribe(
        self,
        subscriber_id: str,
        handler: Callable,
        event_filter: Optional[Callable[[MissionEvent], bool]] = None
    ):
        """Subscribe to all mission events."""
        self.subscribers[subscriber_id] = handler
        if event_filter:
            self.filters[subscriber_id] = event_filter

    def subscribe_to_node(
        self,
        subscriber_id: str,
        node_id: str,
        handler: Callable
    ):
        """Subscribe to events for a specific node."""
        if node_id not in self.node_subscribers:
            self.node_subscribers[node_id] = {}
        self.node_subscribers[node_id][subscriber_id] = handler

    def subscribe_to_workstream(
        self,
        subscriber_id: str,
        workstream_id: str,
        handler: Callable
    ):
        """Subscribe to events for a specific workstream."""
        if workstream_id not in self.workstream_subscribers:
            self.workstream_subscribers[workstream_id] = {}
        self.workstream_subscribers[workstream_id][subscriber_id] = handler

    def unsubscribe(self, subscriber_id: str):
        """Unsubscribe from all events."""
        self.subscribers.pop(subscriber_id, None)
        self.filters.pop(subscriber_id, None)

    # ========================================================================
    # Internal Methods
    # ========================================================================

    async def _persist_event(self, event: MissionEvent):
        """Persist event to database."""
        try:
            self.supabase.table("mission_events").insert({
                "mission_id": event.mission_id,
                "event_type": event.event_type.value,
                "event_payload": event.payload,
                "source_node_id": event.source_node_id,
                "source_agent_type": event.source_agent_type,
                "created_at": event.timestamp.isoformat()
            }).execute()
        except Exception as e:
            logger.error(f"Error persisting event: {e}")

    def _matches_filter(self, event: MissionEvent, subscriber_id: str) -> bool:
        """Check if event matches subscriber's filter."""
        filter_fn = self.filters.get(subscriber_id)
        if filter_fn:
            try:
                return filter_fn(event)
            except Exception as e:
                logger.error(f"Error in filter for {subscriber_id}: {e}")
                return False
        return True


# ============================================================================
# Event Handler Decorators
# ============================================================================

def on_event(event_type: MissionEventType):
    """Decorator to register handler for specific event type."""
    def decorator(func):
        func.event_type = event_type
        return func
    return decorator


# ============================================================================
# Context Bus Manager
# ============================================================================

class ContextBusManager:
    """
    Manages context bus instances for active missions.

    Provides singleton access to the context bus for each mission.
    """

    _instances: Dict[str, MissionContextBus] = {}

    @classmethod
    def get_bus(cls, mission_id: str, supabase_client=None) -> MissionContextBus:
        """Get or create context bus for a mission."""
        if mission_id not in cls._instances:
            cls._instances[mission_id] = MissionContextBus(supabase_client)
        return cls._instances[mission_id]

    @classmethod
    def destroy_bus(cls, mission_id: str):
        """Destroy context bus for a completed mission."""
        bus = cls._instances.pop(mission_id, None)
        if bus:
            # Clear subscriptions
            bus.subscribers.clear()
            bus.node_subscribers.clear()
            bus.workstream_subscribers.clear()
            bus.events.clear()


# ============================================================================
# Quick Start Functions
# ========================================================================

async def notify_node_completion(
    mission_id: str,
    node_id: str,
    agent_type: str,
    handoff_packet: Dict[str, Any],
    workstream_id: Optional[str] = None
):
    """Quick helper: Notify that a node completed with handoff."""
    from ..dependencies import get_supabase_client
    supabase = get_supabase_client()
    bus = ContextBusManager.get_bus(mission_id, supabase)

    return await bus.emit_node_completed(
        mission_id, node_id, agent_type, handoff_packet, workstream_id
    )


async def require_decision(
    mission_id: str,
    node_id: str,
    condition: Dict[str, Any],
    current_value: float
):
    """Quick helper: Require a decision at a gate."""
    from ..dependencies import get_supabase_client
    supabase = get_supabase_client()
    bus = ContextBusManager.get_bus(mission_id, supabase)

    return await bus.emit_decision_required(
        mission_id, node_id, condition, current_value
    )


async def escalate_risk(
    mission_id: str,
    risk_description: str,
    severity: str,
    source_node_id: str,
    confidence: float,
    recommendations: List[str]
):
    """Quick helper: Escalate a risk to the team."""
    from ..dependencies import get_supabase_client
    supabase = get_supabase_client()
    bus = ContextBusManager.get_bus(mission_id, supabase)

    return await bus.emit_risk_escalated(
        mission_id, risk_description, severity, source_node_id, confidence, recommendations
    )
