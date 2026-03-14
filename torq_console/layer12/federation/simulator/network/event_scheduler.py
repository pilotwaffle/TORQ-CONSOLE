"""
Event Scheduler for Federation Network Simulator

Layer 12 Phase 2B — Multi-Node Federation Scale Validation

Simulates asynchronous distributed activity through event-driven scheduling.
Instead of round-based only, introduces realistic temporal event patterns.

Event types:
- claim_publish: Node publishes a claim
- claim_propagation: Claim spreads through network
- claim_process: Node processes an inbound claim
- trust_update: Trust score changes
- node_behavior_shift: Node behavior changes
- domain_influence_update: Domain influence rebalances
"""

import asyncio
import heapq
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional, Set
from uuid import uuid4

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


# ============================================================================
# Event Types
# ============================================================================

class EventType(str, Enum):
    """Types of simulation events."""

    CLAIM_PUBLISH = "claim_publish"
    CLAIM_PROPAGATION = "claim_propagation"
    CLAIM_PROCESS = "claim_process"
    TRUST_UPDATE = "trust_update"
    NODE_BEHAVIOR_SHIFT = "node_behavior_shift"
    DOMAIN_INFLUENCE_UPDATE = "domain_influence_update"
    NETWORK_SNAPSHOT = "network_snapshot"


# ============================================================================
# Simulation Event
# ============================================================================

class SimulationEvent(BaseModel):
    """An event in the federation simulation."""

    event_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique event ID")
    event_type: EventType = Field(..., description="Type of event")
    source_node: str = Field(..., description="Node that initiated the event")
    target_nodes: List[str] = Field(default_factory=list, description="Target nodes for this event")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When event occurs")
    priority: int = Field(default=0, description="Event priority (higher = earlier)")

    # Event payload
    payload: Dict[str, Any] = Field(default_factory=dict, description="Event-specific data")

    # Processing metadata
    processed: bool = Field(default=False, description="Whether event has been processed")
    processing_duration_ms: float = Field(default=0.0, description="Time to process event")

    class Config:
        use_enum_values = True

    def __lt__(self, other: "SimulationEvent") -> bool:
        """Compare events for priority queue (higher priority first)."""
        if self.priority != other.priority:
            return self.priority > other.priority
        return self.timestamp < other.timestamp


# ============================================================================
# Event Batch
# ============================================================================

class EventBatch(BaseModel):
    """A batch of events to process together."""

    batch_id: str = Field(default_factory=lambda: str(uuid4()))
    events: List[SimulationEvent] = Field(default_factory=list)
    batch_timestamp: datetime = Field(default_factory=datetime.utcnow)
    total_events: int = Field(default=0, ge=0)

    def add_event(self, event: SimulationEvent) -> None:
        """Add an event to this batch."""
        self.events.append(event)
        self.total_events += 1


# ============================================================================
# Event Scheduler
# ============================================================================

class EventScheduler:
    """
    Schedules and manages asynchronous simulation events.

    Features:
    - Priority-based event queue
    - Event batching for performance
    - Temporal event simulation
    - Event cancellation and rescheduling
    """

    def __init__(
        self,
        batch_size: int = 100,
        batch_window_ms: int = 100,
        enable_shuffle: bool = True,
    ):
        """
        Initialize the event scheduler.

        Args:
            batch_size: Maximum events per batch
            batch_window_ms: Time window to collect events before batching
            enable_shuffle: Whether to shuffle events within batch for realism
        """
        self.batch_size = batch_size
        self.batch_window_ms = batch_window_ms
        self.enable_shuffle = enable_shuffle

        # Event queue (priority queue implemented with heap)
        self._event_queue: List[SimulationEvent] = []
        self._event_lookup: Dict[str, SimulationEvent] = {}  # event_id -> event

        # Event handlers
        self._handlers: Dict[EventType, List[Callable]] = {
            event_type: []
            for event_type in EventType
        }

        # Statistics
        self._total_events_scheduled = 0
        self._total_events_processed = 0
        self._total_events_cancelled = 0

        self.logger = logging.getLogger(__name__)

    def schedule_event(
        self,
        event_type: EventType,
        source_node: str,
        target_nodes: Optional[List[str]] = None,
        payload: Optional[Dict[str, Any]] = None,
        priority: int = 0,
        delay_ms: int = 0,
    ) -> SimulationEvent:
        """
        Schedule a new simulation event.

        Args:
            event_type: Type of event
            source_node: Node initiating the event
            target_nodes: Target nodes (if applicable)
            payload: Event-specific data
            priority: Event priority (higher = earlier)
            delay_ms: Delay before event becomes eligible

        Returns:
            The scheduled SimulationEvent
        """
        event = SimulationEvent(
            event_type=event_type,
            source_node=source_node,
            target_nodes=target_nodes or [],
            payload=payload or {},
            priority=priority,
        )

        # Apply delay if specified
        if delay_ms > 0:
            event.timestamp = event.timestamp + timedelta(milliseconds=delay_ms)

        # Add to queue
        heapq.heappush(self._event_queue, event)
        self._event_lookup[event.event_id] = event
        self._total_events_scheduled += 1

        self.logger.debug(
            f"Scheduled {event_type.value} from {source_node} "
            f"(priority={priority}, delay={delay_ms}ms)"
        )

        return event

    def register_handler(
        self,
        event_type: EventType,
        handler: Callable[[SimulationEvent], Awaitable[Any]],
    ) -> None:
        """
        Register an async event handler.

        Args:
            event_type: Type of event to handle
            handler: Async function that processes the event
        """
        self._handlers[event_type].append(handler)
        self.logger.debug(f"Registered handler for {event_type.value}")

    async def process_next_batch(self) -> EventBatch:
        """
        Process the next batch of eligible events.

        Returns:
            EventBatch containing processed events
        """
        batch = EventBatch()
        cutoff_time = datetime.utcnow() + timedelta(milliseconds=self.batch_window_ms)
        events_processed = 0

        # Collect events until batch size or window expires
        while (
            self._event_queue
            and events_processed < self.batch_size
            and datetime.utcnow() < cutoff_time
        ):
            event = heapq.heappop(self._event_queue)

            # Skip if cancelled
            if event.event_id not in self._event_lookup:
                self._total_events_cancelled += 1
                continue

            # Skip if delayed
            if event.timestamp > datetime.utcnow():
                # Put back and wait
                heapq.heappush(self._event_queue, event)
                break

            batch.add_event(event)
            events_processed += 1

        # Shuffle batch if enabled (for realism)
        if self.enable_shuffle and len(batch.events) > 1:
            random.shuffle(batch.events)

        # Process events in batch
        for event in batch.events:
            await self._process_event(event)
            event.processed = True
            self._total_events_processed += 1

        self.logger.info(f"Processed batch of {len(batch.events)} events")
        return batch

    async def _process_event(self, event: SimulationEvent) -> None:
        """Process a single event by calling registered handlers."""
        start_time = datetime.utcnow()

        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                # Handle both enum and string event_type
                event_type_str = event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type)
                self.logger.error(
                    f"Handler error for {event_type_str} "
                    f"(event {event.event_id}): {e}",
                    exc_info=True
                )

        # Track processing time
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        event.processing_duration_ms = duration_ms

    def cancel_event(self, event_id: str) -> bool:
        """
        Cancel a scheduled event.

        Args:
            event_id: Event to cancel

        Returns:
            True if event was found and cancelled
        """
        if event_id in self._event_lookup:
            del self._event_lookup[event_id]
            self._total_events_cancelled += 1
            self.logger.debug(f"Cancelled event {event_id}")
            return True
        return False

    def get_pending_count(self) -> int:
        """Get number of pending events in queue."""
        # Count only events not cancelled and not delayed
        now = datetime.utcnow()
        return sum(
            1 for event in self._event_queue
            if event.event_id in self._event_lookup and event.timestamp <= now
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        return {
            "total_scheduled": self._total_events_scheduled,
            "total_processed": self._total_events_processed,
            "total_cancelled": self._total_events_cancelled,
            "pending_count": self.get_pending_count(),
            "queue_size": len(self._event_queue),
        }

    def clear(self) -> None:
        """Clear all pending events."""
        self._event_queue.clear()
        self._event_lookup.clear()
        self.logger.debug("Cleared event queue")


def create_event_scheduler(
    batch_size: int = 100,
    batch_window_ms: int = 100,
    enable_shuffle: bool = True,
) -> EventScheduler:
    """Factory function to create an EventScheduler."""
    return EventScheduler(
        batch_size=batch_size,
        batch_window_ms=batch_window_ms,
        enable_shuffle=enable_shuffle,
    )
