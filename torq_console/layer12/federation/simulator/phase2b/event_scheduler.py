"""
Event Scheduler for Federation Network Simulation

Layer 12 Phase 2B — Multi-Node Federation Scale Validation

Event-driven simulation engine that replaces loop-based execution.
Provides discrete event simulation with priority queue scheduling.
"""

import asyncio
import heapq
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import uuid4

from .node_registry import FederatedNode, NodeRegistry
from .network_controller import NetworkController


logger = logging.getLogger(__name__)


@dataclass
class SimulationEvent:
    """Base class for simulation events.

    Events are ordered by timestamp for execution.
    """

    event_id: str
    timestamp: float
    event_type: str
    priority: int = 0

    def __lt__(self, other):
        """For priority queue ordering (by timestamp, then priority)."""
        if self.timestamp != other.timestamp:
            return self.timestamp < other.timestamp
        return self.priority > other.priority

    def __repr__(self):
        return f"SimulationEvent(id={self.event_id[:8]}, type={self.event_type}, t={self.timestamp:.2f})"


@dataclass
class ClaimPublicationEvent(SimulationEvent):
    """Event: Node publishes a claim to the network."""

    event_id: str = ""
    timestamp: float = 0.0
    event_type: str = "claim_publication"
    priority: int = 0
    node_id: str = ""
    claim: Any = None  # SimulatedClaim
    target_nodes: List[str] = field(default_factory=list)
    broadcast_radius: int = 1


@dataclass
class TrustAdjustmentEvent(SimulationEvent):
    """Event: Trust score adjustment for a node."""

    event_id: str = ""
    timestamp: float = 0.0
    event_type: str = "trust_adjustment"
    priority: int = 0
    node_id: str = ""
    adjustment: float = 0.0
    reason: str = ""
    source_event: Optional[str] = None  # Event that caused this adjustment


@dataclass
class NodeJoinEvent(SimulationEvent):
    """Event: New node joins the federation."""

    event_id: str = ""
    timestamp: float = 0.0
    event_type: str = "node_join"
    priority: int = 0
    node: Optional[FederatedNode] = None
    connect_to: List[str] = field(default_factory=list)  # Nodes to connect to


@dataclass
class NodeLeaveEvent(SimulationEvent):
    """Event: Node leaves the federation."""

    event_id: str = ""
    timestamp: float = 0.0
    event_type: str = "node_leave"
    priority: int = 0
    node_id: str = ""
    reason: str = ""


@dataclass
class EdgeAddEvent(SimulationEvent):
    """Event: New connection added between nodes."""

    event_id: str = ""
    timestamp: float = 0.0
    event_type: str = "edge_add"
    priority: int = 0
    source: str = ""
    target: str = ""


@dataclass
class EdgeRemoveEvent(SimulationEvent):
    """Event: Connection removed between nodes."""

    event_id: str = ""
    timestamp: float = 0.0
    event_type: str = "edge_remove"
    priority: int = 0
    source: str = ""
    target: str = ""
    reason: str = ""


@dataclass
class EpochEndEvent(SimulationEvent):
    """Event: Epoch boundary marker.

    Triggered at the end of each epoch to compute metrics and
    apply epoch-level updates.
    """

    event_id: str = ""
    timestamp: float = 0.0
    event_type: str = "epoch_end"
    priority: int = 0
    epoch_number: int = 0
    epoch_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AdversarialAttackEvent(SimulationEvent):
    """Event: Coordinated adversarial behavior begins."""

    event_id: str = ""
    timestamp: float = 0.0
    event_type: str = "adversarial_attack"
    priority: int = 0
    attack_type: str = ""  # "flood", "sybil", "capture", "partition"
    participants: List[str] = field(default_factory=list)
    intensity: float = 0.5
    duration: float = 5.0  # How long the attack lasts


@dataclass
class NetworkPartitionEvent(SimulationEvent):
    """Event: Network partition occurs."""

    event_id: str = ""
    timestamp: float = 0.0
    event_type: str = "network_partition"
    priority: int = 0
    partition_groups: List[List[str]] = field(default_factory=list)
    duration: Optional[float] = None  # None = permanent until healed


@dataclass
class NetworkHealEvent(SimulationEvent):
    """Event: Network partition heals."""

    event_id: str = ""
    timestamp: float = 0.0
    event_type: str = "network_heal"
    priority: int = 0
    partition_groups: List[List[str]] = field(default_factory=list)


@dataclass
class ScheduledClaimEvent(SimulationEvent):
    """Event: Claim scheduled for future publication."""

    event_id: str = ""
    timestamp: float = 0.0
    event_type: str = "scheduled_claim"
    priority: int = 0
    node_id: str = ""
    domain: Any = None  # Domain enum
    stance: Any = None  # Stance enum
    confidence: float = 0.5
    quality: float = 0.5


@dataclass
class EventResult:
    """Result of processing an event."""

    event_id: str
    success: bool
    error: Optional[str] = None
    side_effects: List[str] = field(default_factory=list)
    next_events: List[SimulationEvent] = field(default_factory=list)
    processing_time_ms: float = 0.0


class EventScheduler:
    """Event-driven simulation scheduler.

    Maintains a priority queue of events and executes them in timestamp order.
    Supports discrete event simulation with lookahead and event cancellation.
    """

    def __init__(
        self,
        controller: NetworkController,
        registry: NodeRegistry,
        auto_advance: bool = True,
    ):
        self.controller = controller
        self.registry = registry
        self.auto_advance = auto_advance

        self.event_queue: List[SimulationEvent] = []
        self.current_time: float = 0.0
        self.event_log: List[SimulationEvent] = []
        self.processed_events: Dict[str, EventResult] = {}
        self.cancelled_events: Set[str] = set()

        # Event handlers by type
        self.handlers: Dict[str, Callable] = {
            "claim_publication": self._handle_claim_publication,
            "trust_adjustment": self._handle_trust_adjustment,
            "node_join": self._handle_node_join,
            "node_leave": self._handle_node_leave,
            "edge_add": self._handle_edge_add,
            "edge_remove": self._handle_edge_remove,
            "epoch_end": self._handle_epoch_end,
            "adversarial_attack": self._handle_adversarial_attack,
            "network_partition": self._handle_network_partition,
            "network_heal": self._handle_network_heal,
            "scheduled_claim": self._handle_scheduled_claim,
        }

        # Metrics
        self.total_events_processed = 0
        self.total_events_scheduled = 0
        self.event_counts_by_type: Dict[str, int] = {}

        self.logger = logging.getLogger(__name__)

    def schedule(self, event: SimulationEvent) -> str:
        """Schedule an event for execution.

        Args:
            event: The event to schedule

        Returns:
            The event ID
        """
        heapq.heappush(self.event_queue, event)
        self.total_events_scheduled += 1

        event_type = event.event_type
        self.event_counts_by_type[event_type] = self.event_counts_by_type.get(event_type, 0) + 1

        self.logger.debug(f"Scheduled {event_type} event {event.event_id[:8]} at t={event.timestamp:.2f}")

        return event.event_id

    def cancel(self, event_id: str) -> bool:
        """Cancel a scheduled event.

        Note: This marks the event as cancelled. It will be skipped when
        it reaches the front of the queue.
        """
        self.cancelled_events.add(event_id)
        self.logger.debug(f"Cancelled event {event_id[:8]}")
        return True

    def schedule_at(
        self,
        timestamp: float,
        event_type: str,
        **kwargs,
    ) -> str:
        """Schedule an event at a specific timestamp."""
        event_id = str(uuid4())

        if event_type == "claim_publication":
            event = ClaimPublicationEvent(
                event_id=event_id,
                timestamp=timestamp,
                event_type=event_type,
                **kwargs,
            )
        elif event_type == "trust_adjustment":
            event = TrustAdjustmentEvent(
                event_id=event_id,
                timestamp=timestamp,
                event_type=event_type,
                **kwargs,
            )
        elif event_type == "epoch_end":
            event = EpochEndEvent(
                event_id=event_id,
                timestamp=timestamp,
                event_type=event_type,
                **kwargs,
            )
        else:
            # Generic event
            event = SimulationEvent(
                event_id=event_id,
                timestamp=timestamp,
                event_type=event_type,
            )

        return self.schedule(event)

    def schedule_delayed(self, delay: float, event_type: str, **kwargs) -> str:
        """Schedule an event after a delay from current time."""
        return self.schedule_at(self.current_time + delay, event_type, **kwargs)

    def schedule_claim_publication(
        self,
        node_id: str,
        claim: Any,
        delay: float = 0.0,
        broadcast_radius: int = 1,
    ) -> str:
        """Schedule a claim publication from a node."""
        event_id = str(uuid4())
        event = ClaimPublicationEvent(
            event_id=event_id,
            timestamp=self.current_time + delay,
            event_type="claim_publication",
            node_id=node_id,
            claim=claim,
            broadcast_radius=broadcast_radius,
        )
        return self.schedule(event)

    def schedule_trust_adjustment(
        self,
        node_id: str,
        adjustment: float,
        reason: str,
        delay: float = 0.0,
    ) -> str:
        """Schedule a trust adjustment."""
        event_id = str(uuid4())
        event = TrustAdjustmentEvent(
            event_id=event_id,
            timestamp=self.current_time + delay,
            event_type="trust_adjustment",
            node_id=node_id,
            adjustment=adjustment,
            reason=reason,
        )
        return self.schedule(event)

    def schedule_epoch_end(self, epoch_number: int, delay: float = 0.0) -> str:
        """Schedule epoch boundary."""
        event_id = str(uuid4())
        event = EpochEndEvent(
            event_id=event_id,
            timestamp=self.current_time + delay,
            event_type="epoch_end",
            epoch_number=epoch_number,
        )
        return self.schedule(event)

    def schedule_adversarial_attack(
        self,
        attack_type: str,
        participants: List[str],
        intensity: float = 0.5,
        delay: float = 0.0,
        duration: float = 5.0,
    ) -> str:
        """Schedule an adversarial attack event."""
        event_id = str(uuid4())
        event = AdversarialAttackEvent(
            event_id=event_id,
            timestamp=self.current_time + delay,
            event_type="adversarial_attack",
            attack_type=attack_type,
            participants=participants,
            intensity=intensity,
            duration=duration,
        )
        return self.schedule(event)

    def run(self, duration: float) -> None:
        """Run simulation until time duration.

        Processes all events with timestamp <= current_time + duration.
        """
        target_time = self.current_time + duration

        while self.has_more_events() and self.next_event_time() <= target_time:
            self.step()

        self.current_time = target_time
        self.logger.info(f"Simulation advanced to t={self.current_time:.2f}")

    def run_until_complete(self, max_duration: float = 1000.0) -> None:
        """Run simulation until no more events or max_duration reached."""
        start_time = self.current_time

        while self.has_more_events() and (self.current_time - start_time) < max_duration:
            self.step()

        self.logger.info(f"Simulation complete at t={self.current_time:.2f}")

    def step(self) -> bool:
        """Execute next event.

        Returns:
            False if no events remain, True otherwise
        """
        if not self.event_queue:
            return False

        # Pop next event
        event = heapq.heappop(self.event_queue)

        # Check if cancelled
        if event.event_id in self.cancelled_events:
            self.cancelled_events.discard(event.event_id)
            return True

        # Update current time
        self.current_time = event.timestamp

        # Process event
        result = self.process_event(event)

        # Schedule any next events
        for next_event in result.next_events:
            self.schedule(next_event)

        self.total_events_processed += 1
        return True

    async def step_async(self) -> bool:
        """Execute next event asynchronously."""
        if not self.event_queue:
            return False

        event = heapq.heappop(self.event_queue)

        if event.event_id in self.cancelled_events:
            self.cancelled_events.discard(event.event_id)
            return True

        self.current_time = event.timestamp
        result = await self.process_event_async(event)

        for next_event in result.next_events:
            self.schedule(next_event)

        self.total_events_processed += 1
        return True

    def has_more_events(self) -> bool:
        """Check if there are more events to process."""
        return len(self.event_queue) > 0

    def next_event_time(self) -> Optional[float]:
        """Get timestamp of next event."""
        if not self.event_queue:
            return None
        return self.event_queue[0].timestamp

    def peek_next_event(self) -> Optional[SimulationEvent]:
        """Look at next event without removing it."""
        if not self.event_queue:
            return None
        return self.event_queue[0]

    def process_event(self, event: SimulationEvent) -> EventResult:
        """Process a single event."""
        started_at = datetime.utcnow()

        try:
            handler = self.handlers.get(event.event_type)
            if handler is None:
                return EventResult(
                    event_id=event.event_id,
                    success=False,
                    error=f"No handler for event type: {event.event_type}",
                )

            self.logger.debug(f"Processing {event.event_type} event {event.event_id[:8]}")

            # Call handler
            next_events = handler(event)

            processing_time = (datetime.utcnow() - started_at).total_seconds() * 1000

            result = EventResult(
                event_id=event.event_id,
                success=True,
                next_events=next_events or [],
                processing_time_ms=processing_time,
            )

            self.event_log.append(event)
            self.processed_events[event.event_id] = result

            return result

        except Exception as e:
            processing_time = (datetime.utcnow() - started_at).total_seconds() * 1000

            self.logger.error(
                f"Error processing event {event.event_id}: {e}",
                exc_info=True,
            )

            return EventResult(
                event_id=event.event_id,
                success=False,
                error=str(e),
                processing_time_ms=processing_time,
            )

    async def process_event_async(self, event: SimulationEvent) -> EventResult:
        """Process a single event asynchronously."""
        # For now, use the sync handler
        # In the future, certain handlers can be made async
        return self.process_event(event)

    # Event Handlers

    def _handle_claim_publication(self, event: ClaimPublicationEvent) -> List[SimulationEvent]:
        """Handle claim publication event."""
        node = self.registry.get_node(event.node_id)
        if not node:
            self.logger.warning(f"Node {event.node_id} not found for claim publication")
            return []

        # Broadcast to neighbors
        recipients = self.controller.broadcast_claim(
            event.claim,
            event.node_id,
            radius=event.broadcast_radius,
        )

        self.logger.debug(
            f"Claim from {event.node_id} broadcast to {len(recipients)} nodes"
        )

        return []

    def _handle_trust_adjustment(self, event: TrustAdjustmentEvent) -> List[SimulationEvent]:
        """Handle trust adjustment event."""
        self.registry.update_trust(
            event.node_id,
            event.adjustment,
            event.reason,
        )

        return []

    def _handle_node_join(self, event: NodeJoinEvent) -> List[SimulationEvent]:
        """Handle node join event."""
        self.registry.register_node(event.node)

        # Add connections
        for target_id in event.connect_to:
            if self.controller.topology:
                self.controller.topology.add_undirected_edge(event.node.node_id, target_id)

        self.logger.info(f"Node {event.node.node_id} joined the federation")

        return []

    def _handle_node_leave(self, event: NodeLeaveEvent) -> List[SimulationEvent]:
        """Handle node leave event."""
        node = self.registry.get_node(event.node_id)
        if node:
            node.identity.is_active = False

        self.logger.info(f"Node {event.node_id} left: {event.reason}")

        return []

    def _handle_edge_add(self, event: EdgeAddEvent) -> List[SimulationEvent]:
        """Handle edge addition event."""
        if self.controller.topology:
            self.controller.topology.add_undirected_edge(event.source, event.target)

            # Update node connections
            source_node = self.registry.get_node(event.source)
            target_node = self.registry.get_node(event.target)
            if source_node:
                source_node.add_connection(event.target)
            if target_node:
                target_node.add_connection(event.source)

        return []

    def _handle_edge_remove(self, event: EdgeRemoveEvent) -> List[SimulationEvent]:
        """Handle edge removal event."""
        if self.controller.topology:
            self.controller.topology.remove_edge(event.source, event.target)
            self.controller.topology.remove_edge(event.target, event.source)

            # Update node connections
            source_node = self.registry.get_node(event.source)
            target_node = self.registry.get_node(event.target)
            if source_node:
                source_node.remove_connection(event.target)
            if target_node:
                target_node.remove_connection(event.source)

        return []

    def _handle_epoch_end(self, event: EpochEndEvent) -> List[SimulationEvent]:
        """Handle epoch end event."""
        self.controller.advance_epoch()

        # Take snapshot
        snapshot = self.controller.take_snapshot()

        self.logger.info(
            f"Epoch {event.epoch_number} ended. "
            f"Active nodes: {snapshot.active_nodes}, "
            f"Avg trust: {snapshot.avg_trust:.3f}"
        )

        # Schedule next epoch end if not the last one
        next_events = []
        if event.epoch_number < self.controller.epoch_config.epochs:
            epoch_duration = 1.0  # Default: 1 time unit per epoch
            next_event = EpochEndEvent(
                event_id=str(uuid4()),
                timestamp=self.current_time + epoch_duration,
                event_type="epoch_end",
                epoch_number=event.epoch_number + 1,
            )
            next_events.append(next_event)

        return next_events

    def _handle_adversarial_attack(self, event: AdversarialAttackEvent) -> List[SimulationEvent]:
        """Handle adversarial attack event."""
        self.logger.warning(
            f"Adversarial attack '{event.attack_type}' started by {len(event.participants)} nodes"
        )

        # Apply adversarial behavior to participants
        for node_id in event.participants:
            node = self.registry.get_node(node_id)
            if node:
                node.behavior.set_adversarial_mode(
                    event.attack_type,
                    event.intensity,
                    coordination_group=f"attack_{event.event_id[:8]}",
                )

        # Schedule attack end
        if event.duration > 0:
            end_event = AdversarialAttackEvent(
                event_id=str(uuid4()),
                timestamp=self.current_time + event.duration,
                event_type="adversarial_attack_end",
                attack_type=f"{event.attack_type}_end",
                participants=event.participants,
                intensity=0.0,
            )
            return [end_event]

        return []

    def _handle_network_partition(self, event: NetworkPartitionEvent) -> List[SimulationEvent]:
        """Handle network partition event."""
        if not self.controller.topology:
            return []

        self.logger.warning(
            f"Network partitioned into {len(event.partition_groups)} groups"
        )

        # Remove edges between groups
        edges_removed = []
        for i, group1 in enumerate(event.partition_groups):
            for group2 in event.partition_groups[i + 1:]:
                for node1 in group1:
                    for node2 in group2:
                        if node2 in self.controller.topology.get_neighbors(node1):
                            self.controller.topology.remove_edge(node1, node2)
                            self.controller.topology.remove_edge(node2, node1)
                            edges_removed.append((node1, node2))

        self.logger.debug(f"Removed {len(edges_removed)} edges during partition")

        # Schedule heal if duration is specified
        next_events = []
        if event.duration is not None:
            heal_event = NetworkHealEvent(
                event_id=str(uuid4()),
                timestamp=self.current_time + event.duration,
                event_type="network_heal",
                partition_groups=event.partition_groups,
            )
            next_events.append(heal_event)

        return next_events

    def _handle_network_heal(self, event: NetworkHealEvent) -> List[SimulationEvent]:
        """Handle network heal event."""
        if not self.controller.topology:
            return []

        self.logger.info("Network partition healed")

        # Restore edges between groups
        edges_restored = 0
        for i, group1 in enumerate(event.partition_groups):
            for group2 in event.partition_groups[i + 1:]:
                for node1 in group1:
                    for node2 in group2:
                        # Restore connection
                        self.controller.topology.add_undirected_edge(node1, node2)
                        edges_restored += 1

        self.logger.debug(f"Restored {edges_restored} edges during heal")

        return []

    def _handle_scheduled_claim(self, event: ScheduledClaimEvent) -> List[SimulationEvent]:
        """Handle scheduled claim event - creates and publishes a claim."""
        from ..models import SimulatedClaim

        node = self.registry.get_node(event.node_id)
        if not node:
            return []

        # Create claim
        claim = SimulatedClaim(
            claim_id=str(uuid4()),
            domain=event.domain,
            content=f"Scheduled claim from {event.node_id}",
            stance=event.stance,
            confidence=event.confidence,
            provenance_quality=event.quality,
            timestamp=datetime.utcnow(),
        )

        # Publish immediately
        pub_event = ClaimPublicationEvent(
            event_id=str(uuid4()),
            timestamp=self.current_time,
            event_type="claim_publication",
            node_id=event.node_id,
            claim=claim,
            broadcast_radius=1,
        )

        return [pub_event]

    def get_statistics(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        return {
            "current_time": self.current_time,
            "events_pending": len(self.event_queue),
            "events_processed": self.total_events_processed,
            "events_scheduled": self.total_events_scheduled,
            "events_cancelled": len(self.cancelled_events),
            "events_by_type": self.event_counts_by_type.copy(),
        }


def create_event_scheduler(
    controller: NetworkController,
    registry: NodeRegistry,
) -> EventScheduler:
    """Factory function to create an event scheduler."""
    return EventScheduler(controller, registry)
