"""
Federation Network Controller

Layer 12 Phase 2B — Multi-Node Federation Scale Validation

Orchestrates multi-node federation simulation with:
- Node spawning and topology configuration
- Event-driven simulation epochs
- Claim routing through real processor pipeline
- Network metrics collection and reporting

This is the main entry point for Phase 2B network simulations.
"""

import asyncio
import logging
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional, Set, Tuple

import numpy as np
from pydantic import BaseModel, Field

from .node_registry import NodeRegistry, SimulatedNetworkNode, create_node_registry
from .event_scheduler import EventScheduler, EventType, SimulationEvent, create_event_scheduler
from .network_metrics import NetworkMetricsEngine, NetworkSnapshot, create_network_metrics_engine
from ..models import Domain, NodeType, NodeBehaviorProfile, Stance
from ..processor_adapter import ProcessorAdapter
from ..metrics import FederationMetricsAggregator
from torq_console.layer12.federation.config import TRUST_THRESHOLD_ACCEPT


logger = logging.getLogger(__name__)


# ============================================================================
# Network Topology
# ============================================================================

class NetworkTopology(str, Enum):
    """Supported network topologies for simulation."""

    FULLY_CONNECTED = "fully_connected"
    SMALL_WORLD = "small_world"
    HUB_AND_SPOKE = "hub_and_spoke"
    RANDOM_GRAPH = "random_graph"
    LINEAR = "linear"


# ============================================================================
# Network Simulation Configuration
# ============================================================================

class NetworkSimulationConfig(BaseModel):
    """Configuration for network simulation."""

    # Node configuration
    num_nodes: int = Field(default=10, ge=1, le=50, description="Number of nodes in network")
    topology: NetworkTopology = Field(default=NetworkTopology.SMALL_WORLD, description="Network topology")

    # Trust initialization
    min_trust: float = Field(default=0.4, ge=0.0, le=1.0, description="Minimum initial trust")
    max_trust: float = Field(default=0.9, ge=0.0, le=1.0, description="Maximum initial trust")

    # Simulation parameters
    num_epochs: int = Field(default=50, ge=1, description="Number of simulation epochs")
    claims_per_epoch: int = Field(default=20, ge=0, description="Target claims per epoch")
    claims_per_node_per_epoch: float = Field(default=2.0, ge=0.0, description="Claims per node per epoch")

    # Domain configuration
    num_domains: int = Field(default=5, ge=1, description="Number of knowledge domains")
    adversarial_ratio: float = Field(
        default=0.1,
        ge=0.0,
        le=0.5,
        description="Ratio of adversarial nodes"
    )

    # Random seed for reproducibility
    random_seed: Optional[int] = Field(None, description="Random seed for reproducibility")

    # Performance settings
    batch_events: bool = Field(default=True, description="Batch events for performance")
    event_batch_size: int = Field(default=100, ge=1, description="Events per batch")


# ============================================================================
# Network Simulation Result
# ============================================================================

class NetworkSimulationResult(BaseModel):
    """Result of a network simulation."""

    config: NetworkSimulationConfig = Field(..., description="Simulation configuration")
    start_time: datetime = Field(..., description="Simulation start time")
    end_time: datetime = Field(..., description="Simulation end time")
    duration_ms: float = Field(..., description="Simulation duration in milliseconds")

    # Results
    total_epochs_completed: int = Field(..., ge=0, description="Epochs completed")
    total_claims_processed: int = Field(..., ge=0, description="Total claims processed")
    total_claims_accepted: int = Field(..., ge=0, description="Total claims accepted")
    acceptance_rate: float = Field(..., ge=0.0, le=1.0, description="Overall acceptance rate")

    # Network snapshots (one per epoch)
    snapshots: List[NetworkSnapshot] = Field(default_factory=list, description="Network state per epoch")

    # Final metrics
    final_network_metrics: Optional[NetworkSnapshot] = Field(
        None,
        description="Final network state"
    )


# ============================================================================
# Federation Network Controller
# ============================================================================

class FederationNetworkController:
    """
    Orchestrates multi-node federation simulation.

    This is the main coordinator for Phase 2B simulations. It manages:
    - Node lifecycle (creation, registration, evolution)
    - Network topology setup
    - Event scheduling and processing
    - Claim routing through the real processor
    - Metrics collection and reporting
    """

    def __init__(
        self,
        config: NetworkSimulationConfig,
        processor_adapter: ProcessorAdapter,
        claim_quality_bias: float = 0.78,  # Calibrated for ~25-45% acceptance
    ):
        """
        Initialize the network controller.

        Args:
            config: Simulation configuration
            processor_adapter: Adapter to the real claim processor
            claim_quality_bias: Quality bias for claim generation (0.5-0.95)
        """
        self.config = config
        self.adapter = processor_adapter
        self.claim_quality_bias = claim_quality_bias
        self.logger = logging.getLogger(__name__)

        # Set random seed if specified
        if config.random_seed:
            random.seed(config.random_seed)
            np.random.seed(config.random_seed)

        # Initialize components
        self.node_registry = create_node_registry()
        self.event_scheduler = create_event_scheduler()
        self.metrics_engine = create_network_metrics_engine(self.node_registry)

        # Initialize calibrated claim generator
        from .claim_generator import create_claim_generator
        self.claim_generator = create_claim_generator(quality_bias=claim_quality_bias)

        # Additional metrics aggregator
        self.metrics_aggregator = FederationMetricsAggregator()

        # Network state
        self._current_epoch = 0
        self._topology_edges: Set[Tuple[str, str]] = set()
        self._running = False

        # Statistics
        self._total_claims_processed = 0
        self._total_claims_accepted = 0

    async def run_simulation(
        self,
        progress_callback: Optional[Callable[[int, NetworkSnapshot], Awaitable[None]]] = None,
    ) -> NetworkSimulationResult:
        """
        Run the complete network simulation.

        Args:
            progress_callback: Optional async callback after each epoch

        Returns:
            NetworkSimulationResult with complete results
        """
        start_time = datetime.utcnow()
        self._running = True
        self.logger.info(f"Starting network simulation: {self.config.num_nodes} nodes, {self.config.num_epochs} epochs")

        try:
            # Phase 1: Initialize network
            await self._initialize_network()
            await self._setup_topology()

            # Phase 2: Run simulation epochs
            for epoch in range(self.config.num_epochs):
                if not self._running:
                    self.logger.info(f"Simulation stopped at epoch {epoch}")
                    break

                self._current_epoch = epoch + 1
                self.logger.info(f"Epoch {self._current_epoch}/{self.config.num_epochs}")

                # Run epoch and capture snapshot
                snapshot = await self._run_epoch()

                # Progress callback
                if progress_callback:
                    await progress_callback(self._current_epoch, snapshot)

            # Phase 3: Finalize
            end_time = datetime.utcnow()
            duration_ms = (end_time - start_time).total_seconds() * 1000

            result = NetworkSimulationResult(
                config=self.config,
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                total_epochs_completed=self._current_epoch,
                total_claims_processed=self._total_claims_processed,
                total_claims_accepted=self._total_claims_accepted,
                acceptance_rate=(
                    self._total_claims_accepted / self._total_claims_processed
                    if self._total_claims_processed > 0 else 0.0
                ),
                snapshots=self.metrics_engine.get_snapshot_history(),
                final_network_metrics=(
                    self.metrics_engine.get_snapshot_history(last_n=1)[-1]
                    if self.metrics_engine.get_snapshot_history()
                    else None
                ),
            )

            self.logger.info(
                f"Simulation complete: {self._total_claims_processed} claims processed, "
                f"{self._total_claims_accepted} accepted ({result.acceptance_rate:.1%})"
            )

            return result

        finally:
            self._running = False

    async def _initialize_network(self) -> None:
        """Create and register all network nodes."""
        self.logger.info("Initializing network nodes...")

        nodes_per_domain = self.config.num_domains / self.config.num_nodes
        domains_list = list(Domain)[:self.config.num_domains]

        for i in range(self.config.num_nodes):
            node_id = f"network_node_{i:03d}"

            # Determine node type
            is_adversarial = i < (self.config.num_nodes * self.config.adversarial_ratio)
            node_type = NodeType.ADVERSARIAL if is_adversarial else NodeType.NORMAL

            # Calculate trust score based on node type
            # Normal nodes: trust >= TRUST_THRESHOLD_ACCEPT (0.75) to enable acceptance
            # Adversarial nodes: lower trust in quarantine range
            if is_adversarial:
                # Adversarial nodes get low trust (quarantine range)
                trust = 0.40 + random.uniform(0.0, 0.15)  # 0.40-0.55
            else:
                # Normal nodes get high trust (accept range) with some variation
                # Most should be >= 0.75 for meaningful acceptance
                trust = TRUST_THRESHOLD_ACCEPT + random.uniform(0.0, 0.15)  # 0.75-0.90

            # Assign domain specialization
            domain_index = int(i * nodes_per_domain) % self.config.num_domains
            domain_specializations = [domains_list[domain_index]]

            # Create behavior profile
            behavior_profile = NodeBehaviorProfile(
                node_type=node_type,
                baseline_trust=trust,
            )

            # Register node
            node = self.node_registry.register_node(
                node_id=node_id,
                node_type=node_type,
                baseline_trust=trust,
                domain_specializations=domain_specializations,
                behavior_profile=behavior_profile,
            )

            self.logger.debug(f"Created {node_id}: {node_type.value}, trust={trust:.2f}, domains={domain_specializations}")

        # Register all nodes with the processor adapter (required for claim processing)
        all_nodes = self.node_registry.get_all_nodes()
        for node in all_nodes:
            self.adapter.register_node(node)

    async def _setup_topology(self) -> None:
        """Setup network topology based on configuration."""
        self.logger.info(f"Setting up {self.config.topology.value} topology...")

        nodes = self.node_registry.get_all_nodes()
        node_ids = [n.node_id for n in nodes]

        if self.config.topology == NetworkTopology.FULLY_CONNECTED:
            self._setup_fully_connected(node_ids)
        elif self.config.topology == NetworkTopology.SMALL_WORLD:
            self._setup_small_world(node_ids)
        elif self.config.topology == NetworkTopology.HUB_AND_SPOKE:
            self._setup_hub_and_spoke(node_ids)
        elif self.config.topology == NetworkTopology.RANDOM_GRAPH:
            self._setup_random_graph(node_ids)
        elif self.config.topology == NetworkTopology.LINEAR:
            self._setup_linear(node_ids)
        else:
            self.logger.warning(f"Unknown topology {self.config.topology}, using small_world")
            self._setup_small_world(node_ids)

        self.logger.info(f"Topology setup complete: {len(self._topology_edges)} edges")

    def _setup_fully_connected(self, node_ids: List[str]) -> None:
        """Setup fully connected topology (all-to-all)."""
        for i, node_a in enumerate(node_ids):
            for node_b in node_ids[i + 1:]:
                self._topology_edges.add((node_a, node_b))
                self._topology_edges.add((node_b, node_a))

                # Add neighbor connections
                self.node_registry.add_network_neighbor(node_a, node_b, 1.0)
                self.node_registry.add_network_neighbor(node_b, node_a, 1.0)

    def _setup_small_world(self, node_ids: List[str]) -> None:
        """Setup small-world topology (Watts-Strogatz model)."""
        k = 4  # Each node connects to k nearest neighbors
        p = 0.1  # Rewiring probability

        n = len(node_ids)
        for i, node_id in enumerate(node_ids):
            # Connect to k nearest neighbors (with wraparound)
            for j in range(1, k // 2 + 1):
                neighbor_idx = (i + j) % n
                neighbor_id = node_ids[neighbor_idx]
                self._topology_edges.add((node_id, neighbor_id))

                # Randomly rewire with probability p
                if random.random() < p:
                    new_neighbor_idx = random.choice([idx for idx in range(n) if idx != i])
                    new_neighbor = node_ids[new_neighbor_idx]
                    self.node_registry.add_network_neighbor(node_id, new_neighbor, 0.8)
                else:
                    self.node_registry.add_network_neighbor(node_id, neighbor_id, 1.0)

    def _setup_hub_and_spoke(self, node_ids: List[str]) -> None:
        """Setup hub-and-spoke topology (central hub connects to all)."""
        if not node_ids:
            return

        hub = node_ids[0]
        spokes = node_ids[1:]

        # Hub connects to all spokes
        for spoke in spokes:
            self._topology_edges.add((hub, spoke))
            self._topology_edges.add((spoke, hub))
            self.node_registry.add_network_neighbor(hub, spoke, 1.0)
            self.node_registry.add_network_neighbor(spoke, hub, 1.0)

    def _setup_random_graph(self, node_ids: List[str]) -> None:
        """Setup random graph topology (Erdos-Renyi model)."""
        n = len(node_ids)
        p = 0.3  # Connection probability

        for i in range(n):
            for j in range(i + 1, n):
                if random.random() < p:
                    node_a, node_b = node_ids[i], node_ids[j]
                    self._topology_edges.add((node_a, node_b))
                    self._topology_edges.add((node_b, node_a))
                    self.node_registry.add_network_neighbor(node_a, node_b, random.random())
                    self.node_registry.add_network_neighbor(node_b, node_a, random.random())

    def _setup_linear(self, node_ids: List[str]) -> None:
        """Setup linear topology (chain)."""
        for i in range(len(node_ids) - 1):
            node_a, node_b = node_ids[i], node_ids[i + 1]
            self._topology_edges.add((node_a, node_b))
            self._topology_edges.add((node_b, node_a))
            self.node_registry.add_network_neighbor(node_a, node_b, 1.0)
            self.node_registry.add_network_neighbor(node_b, node_a, 1.0)

    async def _run_epoch(self) -> NetworkSnapshot:
        """
        Run a single simulation epoch.

        An epoch consists of:
        1. Generate claim_publish events
        2. Route claims to processors
        3. Collect metrics
        4. Capture network snapshot

        Returns:
            NetworkSnapshot of state after epoch
        """
        epoch_start = datetime.utcnow()

        # Step 1: Schedule claim generation events
        await self._schedule_claim_generation()

        # Step 2: Process all events through handlers
        await self._process_event_loop()

        # Step 3: Capture snapshot
        snapshot = self.metrics_engine.capture_snapshot(
            epoch=self._current_epoch,
            total_nodes=self.config.num_nodes,
            topology_edges=self._topology_edges,
        )

        epoch_duration = (datetime.utcnow() - epoch_start).total_seconds()
        self.logger.info(
            f"Epoch {self._current_epoch} complete in {epoch_duration:.2f}s: "
            f"{snapshot.active_nodes} active nodes, "
            f"resilience={snapshot.network_resilience_score:.2f}"
        )

        return snapshot

    async def _schedule_claim_generation(self) -> None:
        """Schedule claim publication events for this epoch."""
        nodes = self.node_registry.get_all_nodes()

        # Calculate target claims per node
        target_claims = int(self.config.claims_per_epoch)
        claims_per_node = self.config.claims_per_node_per_epoch

        for node in nodes:
            # Number of claims for this node (Poisson-like)
            num_claims = np.random.poisson(claims_per_node)
            num_claims = max(0, min(num_claims, target_claims))

            # Schedule claim publication events (no delay for simulation)
            for _ in range(num_claims):
                self.event_scheduler.schedule_event(
                    event_type=EventType.CLAIM_PUBLISH,
                    source_node=node.node_id,
                    payload={"epoch": self._current_epoch},
                    priority=random.randint(0, 10),
                    delay_ms=0,  # No delay - process immediately for simulation
                )

        self.logger.debug(f"Scheduled claims for {len(nodes)} nodes")

    async def _process_event_loop(self) -> None:
        """Process all pending events through handlers."""
        # Register handlers
        self.event_scheduler.register_handler(
            EventType.CLAIM_PUBLISH,
            self._handle_claim_publish,
        )

        # Process batches until no more events
        max_iterations = 100  # Safety limit
        iteration = 0

        while self.event_scheduler.get_pending_count() > 0 and iteration < max_iterations:
            await self.event_scheduler.process_next_batch()
            iteration += 1

        if iteration >= max_iterations:
            self.logger.warning("Event loop reached safety limit")

    async def _handle_claim_publish(self, event: SimulationEvent) -> None:
        """
        Handle a claim publication event.

        This routes the claim through the real processor pipeline.
        """
        node_id = event.source_node
        node = self.node_registry.get_node(node_id)

        if not node:
            self.logger.warning(f"Claim publish from unknown node {node_id}")
            return

        # Generate calibrated claim using the claim generator
        claim = self.claim_generator.generate_claim(
            node=node,
            epoch=self._current_epoch,
        )

        # Process through real processor
        try:
            result = await self.adapter.process_simulated_claim(
                sim_claim=claim,
                origin_node=node,
                round_context={
                    "epoch": self._current_epoch,
                    "simulation_type": "network",
                },
            )

            self._total_claims_processed += 1
            if result.accepted:
                self._total_claims_accepted += 1

            # Update node trust based on outcome
            new_trust = result.effective_trust
            if new_trust != node.current_trust:
                self.node_registry.update_trust_state(node_id, new_trust)

            # Update domain influence
            if result.accepted:
                self.node_registry.update_domain_influence(
                    node_id, claim.domain, True
                )

            self.logger.debug(
                f"Processed claim {claim.claim_id}: "
                f"accepted={result.accepted}, trust={new_trust:.2f}"
            )

        except Exception as e:
            self.logger.error(f"Error processing claim {claim.claim_id}: {e}")

    def stop(self) -> None:
        """Stop the simulation (graceful shutdown)."""
        self._running = False
        self.logger.info("Simulation stop requested")

    def get_status(self) -> Dict[str, Any]:
        """Get current simulation status."""
        return {
            "running": self._running,
            "current_epoch": self._current_epoch,
            "total_epochs": self.config.num_epochs,
            "pending_events": self.event_scheduler.get_pending_count(),
            "total_nodes": len(self.node_registry.get_all_nodes()),
            "total_edges": len(self._topology_edges),
            "claims_processed": self._total_claims_processed,
            "claims_accepted": self._total_claims_accepted,
        }


def create_network_controller(
    config: NetworkSimulationConfig,
    processor_adapter: ProcessorAdapter,
    claim_quality_bias: float = 0.78,
) -> FederationNetworkController:
    """Factory function to create a FederationNetworkController.

    Args:
        config: Simulation configuration
        processor_adapter: Adapter to the real claim processor
        claim_quality_bias: Quality bias for claim generation (0.5-0.95)
    """
    return FederationNetworkController(
        config=config,
        processor_adapter=processor_adapter,
        claim_quality_bias=claim_quality_bias,
    )
