"""
Network Simulation Executor for Phase 2B

Layer 12 Phase 2B — Multi-Node Federation Scale Validation

Binds together NodeRegistry, NetworkController, EventScheduler, NetworkMetricsCalculator
with the Phase 2A claim processing pipeline for end-to-end multi-node federation simulation.

Key requirement: Each node uses the REAL InboundFederatedClaimProcessor, not a simplified path.
"""

import asyncio
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from ..models import (
    Domain,
    SimulatedClaim,
    SimulatedNode,
    Stance,
    SimulationScenario,
    SimulationReport as Phase2AReport,
)
from ..metrics import unwrap_claim
from ..executor_async import AsyncFederationSimulationExecutor
from ..processor_adapter import ProcessorAdapter, ProcessedSimulationClaimResult
from ...inbound_claim_processor import InboundFederatedClaimProcessor
from ...federation_identity_guard import FederationIdentityGuard

from .node_registry import (
    FederatedNode,
    NodeRegistry,
    create_node,
    create_nodes_with_distribution,
)
from .network_controller import (
    NetworkController,
    NetworkConfig,
    EpochConfig,
    NetworkSnapshot,
    create_network_controller,
)
from .event_scheduler import (
    EventScheduler,
    ClaimPublicationEvent,
    TrustAdjustmentEvent,
    EpochEndEvent,
)
from .network_metrics import (
    NetworkMetricsCalculator,
    CentralityMetrics,
    NetworkHealthMetrics,
    InfluenceDistribution,
    NetworkCollapseIndicators,
)


logger = logging.getLogger(__name__)


@dataclass
class NetworkSimulationConfig:
    """Configuration for network simulation."""

    # Network configuration
    node_count: int = 10
    topology_type: str = "small_world"  # small_world, scale_free, random, hierarchical, complete
    domain_count: Optional[int] = None  # None = use all domains

    # Simulation configuration
    epochs: int = 20
    claims_per_epoch: int = 50
    adversarial_ratio: float = 0.0

    # Phase 2A integration
    enable_safeguards: bool = True
    enable_metrics: bool = True
    enable_predictive_metrics: bool = True

    # Trust configuration
    initial_trust_mean: float = 0.5
    initial_trust_std: float = 0.15
    trust_decay_rate: float = 0.01

    # Event scheduling
    event_interval_ms: int = 100
    enable_adversarial_events: bool = True
    adversarial_probability: float = 0.1

    # Output
    verbose: bool = False
    save_results: bool = True
    output_dir: Optional[str] = None

    # Reproducibility
    seed: Optional[int] = None


@dataclass
class EpochReport:
    """Report for a single simulation epoch."""

    epoch_number: int
    timestamp: datetime
    node_count: int
    active_nodes: int
    claims_generated: int
    claims_processed: int
    claims_accepted: int
    claims_quarantined: int
    claims_rejected: int

    # Trust state
    avg_trust: float
    min_trust: float
    max_trust: float
    quarantined_nodes: int

    # Network state
    network_density: float
    avg_path_length: float
    clustering_coefficient: float
    connected_components: int

    # Influence
    gini_coefficient: float
    top_1_influence_share: float
    top_5_influence_share: float

    # Predictive metrics (if enabled)
    eddr: Optional[float] = None
    aca: Optional[float] = None
    fcri: Optional[float] = None

    # Collapse indicators
    collapse_risk: str = "low"
    dominance_alert: bool = False
    fragmentation_acceleration: float = 0.0


@dataclass
class NetworkSimulationReport:
    """Complete report for a network simulation."""

    scenario_name: str
    config: NetworkSimulationConfig
    started_at: datetime
    completed_at: datetime
    execution_time: timedelta

    # Network state
    initial_node_count: int
    final_node_count: int
    topology_type: str

    # Results
    epochs_completed: int
    epoch_reports: List[EpochReport] = field(default_factory=list)

    # Aggregated metrics
    total_claims_generated: int = 0
    total_claims_processed: int = 0
    total_claims_accepted: int = 0
    total_claims_quarantined: int = 0
    total_claims_rejected: int = 0

    # Acceptance rate
    overall_acceptance_rate: float = 0.0

    # Network health (final)
    final_network_health: float = 0.0
    final_collapse_risk: str = "low"

    # Success
    success: bool = True
    error: Optional[str] = None

    # Snapshots
    network_snapshots: List[NetworkSnapshot] = field(default_factory=list)

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of simulation results."""
        if not self.epoch_reports:
            return {}

        final = self.epoch_reports[-1] if self.epoch_reports else None

        return {
            "scenario": self.scenario_name,
            "epochs": self.epochs_completed,
            "nodes": self.final_node_count,
            "topology": self.topology_type,
            "total_claims": self.total_claims_processed,
            "acceptance_rate": self.overall_acceptance_rate,
            "final_health": self.final_network_health,
            "collapse_risk": self.final_collapse_risk,
            "final_eddr": final.eddr if final else None,
            "final_aca": final.aca if final else None,
            "final_fcri": final.fcri if final else None,
            "success": self.success,
        }


class NetworkSimulationExecutor:
    """
    Main executor for Phase 2B network simulations.

    Binds together:
    - NodeRegistry: Node lifecycle and state
    - NetworkController: Topology and orchestration
    - EventScheduler: Event-driven execution
    - NetworkMetricsCalculator: Network-scale metrics
    - ProcessorAdapter: Phase 2A claim processing integration

    Each claim is processed through the REAL InboundFederatedClaimProcessor.
    """

    def __init__(
        self,
        config: NetworkSimulationConfig,
        processor: InboundFederatedClaimProcessor,
        identity_guard: FederationIdentityGuard,
    ):
        self.config = config
        self.processor = processor
        self.identity_guard = identity_guard

        # Initialize Phase 2A adapter for real claim processing
        self.adapter = ProcessorAdapter(processor, identity_guard)

        # Initialize Phase 2B components
        self.registry = NodeRegistry()
        self.controller: Optional[NetworkController] = None
        self.scheduler: Optional[EventScheduler] = None
        self.metrics_calculator: Optional[NetworkMetricsCalculator] = None

        # State
        self.current_epoch: int = 0
        self.claims_processed_this_epoch: int = 0
        self.epoch_results: List[ProcessedSimulationClaimResult] = []

        # Set random seed for reproducibility
        if config.seed is not None:
            random.seed(config.seed)

        self.logger = logging.getLogger(__name__)

    async def initialize(self) -> None:
        """Initialize the network simulation."""
        self.logger.info(f"Initializing {self.config.node_count}-node network simulation...")

        # Build network controller and topology
        network_config = NetworkConfig(
            node_count=self.config.node_count,
            topology_type=self.config.topology_type,
            adversarial_ratio=self.config.adversarial_ratio,
        )
        self.controller = NetworkController(self.registry, network_config)
        self.controller.build_topology()

        # Configure epochs
        self.controller.epoch_config = EpochConfig(
            epochs=self.config.epochs,
            claims_per_epoch=self.config.claims_per_epoch,
            event_interval_ms=self.config.event_interval_ms,
            enable_adversarial_events=self.config.enable_adversarial_events,
            adversarial_probability=self.config.adversarial_probability,
            trust_decay_rate=self.config.trust_decay_rate,
        )

        # Initialize event scheduler
        self.scheduler = EventScheduler(self.controller, self.registry)

        # Initialize metrics calculator
        self.metrics_calculator = NetworkMetricsCalculator(self.controller, self.registry)

        # Register all nodes with the processor adapter
        for node in self.registry.get_all_nodes():
            self.adapter.register_node(node)

        self.logger.info(
            f"Network initialized: {self.config.node_count} nodes, "
            f"{self.controller.topology.topology_type} topology"
        )

    async def run_simulation(
        self,
        scenario: Optional[SimulationScenario] = None,
    ) -> NetworkSimulationReport:
        """
        Run the complete network simulation.

        Args:
            scenario: Optional scenario to use (creates nodes/claims from scenario)

        Returns:
            NetworkSimulationReport with full results
        """
        started_at = datetime.utcnow()
        scenario_name = scenario.name if scenario else "network_simulation"

        self.logger.info(f"Starting network simulation: {scenario_name}")

        try:
            await self.initialize()

            # Take initial snapshot
            initial_snapshot = self.controller.take_snapshot()
            self.controller.snapshots.append(initial_snapshot)

            epoch_reports = []

            # Run epochs
            for epoch in range(1, self.config.epochs + 1):
                self.current_epoch = epoch
                self.claims_processed_this_epoch = 0
                self.epoch_results.clear()

                self.logger.info(f"Starting epoch {epoch}/{self.config.epochs}")

                # Generate and process claims for this epoch
                await self._run_epoch(scenario)

                # Collect epoch metrics
                epoch_report = await self._collect_epoch_report(epoch)
                epoch_reports.append(epoch_report)

                if self.config.verbose:
                    self._log_epoch_report(epoch_report)

                # Take snapshot
                self.controller.take_snapshot()

            # Collect final metrics
            final_metrics = self.metrics_calculator.get_network_summary()

            # Build report
            completed_at = datetime.utcnow()
            report = NetworkSimulationReport(
                scenario_name=scenario_name,
                config=self.config,
                started_at=started_at,
                completed_at=completed_at,
                execution_time=completed_at - started_at,
                initial_node_count=self.config.node_count,
                final_node_count=self.registry.get_node_count(),
                topology_type=self.config.topology_type,
                epochs_completed=self.config.epochs,
                epoch_reports=epoch_reports,
                network_snapshots=self.controller.snapshots,
            )

            # Aggregate totals
            for er in epoch_reports:
                report.total_claims_generated += er.claims_generated
                report.total_claims_processed += er.claims_processed
                report.total_claims_accepted += er.claims_accepted
                report.total_claims_quarantined += er.claims_quarantined
                report.total_claims_rejected += er.claims_rejected

            if report.total_claims_processed > 0:
                report.overall_acceptance_rate = (
                    report.total_claims_accepted / report.total_claims_processed
                )

            report.final_network_health = final_metrics.get("health_score", 0)
            report.final_collapse_risk = final_metrics.get("collapse_risk", {}).get("level", "unknown")

            self.logger.info(
                f"Simulation complete: {report.epochs_completed} epochs, "
                f"{report.total_claims_processed} claims processed, "
                f"{report.overall_acceptance_rate:.1%} acceptance rate"
            )

            return report

        except Exception as e:
            self.logger.error(f"Simulation failed: {e}", exc_info=True)

            return NetworkSimulationReport(
                scenario_name=scenario_name,
                config=self.config,
                started_at=started_at,
                completed_at=datetime.utcnow(),
                execution_time=timedelta(0),
                initial_node_count=self.config.node_count,
                final_node_count=self.registry.get_node_count(),
                topology_type=self.config.topology_type,
                epochs_completed=self.current_epoch,
                success=False,
                error=str(e),
            )

    async def _run_epoch(self, scenario: Optional[SimulationScenario]) -> None:
        """Run a single simulation epoch."""
        # Get all active nodes
        active_nodes = self.registry.get_active_nodes()

        if not active_nodes:
            self.logger.warning("No active nodes, skipping epoch")
            return

        # Generate claims from nodes
        claims_to_process = []

        for node in active_nodes:
            # Determine how many claims this node should generate
            claim_count = node.behavior.get_claim_count_for_epoch(
                base_claims=max(1, self.config.claims_per_epoch // len(active_nodes))
            )

            for _ in range(claim_count):
                claim = self._generate_claim_from_node(node, scenario)
                if claim:
                    claims_to_process.append((claim, node))

        # Shuffle claims to simulate asynchronous arrival
        random.shuffle(claims_to_process)

        # Process claims in parallel
        batch_size = 10
        for i in range(0, len(claims_to_process), batch_size):
            batch = claims_to_process[i:i + batch_size]
            results = await self._process_claim_batch(batch)
            self.epoch_results.extend(results)

        # Advance epoch in controller (applies trust decay)
        self.controller.advance_epoch()

    def _generate_claim_from_node(
        self,
        node: FederatedNode,
        scenario: Optional[SimulationScenario],
    ) -> Optional[SimulatedClaim]:
        """Generate a claim from a node based on its behavior profile."""
        try:
            # Sample stance based on node's distribution
            stance = node.behavior.sample_stance()

            # Sample quality
            quality = node.behavior.sample_quality()

            # Confidence based on quality and trust
            base_confidence = 0.5 + (node.current_trust * 0.3) + (quality * 0.2)

            # Domain from node's specialization
            domain = node.domain_spec.primary_domain

            claim = SimulatedClaim(
                claim_id=str(uuid4()),
                source_node_id=node.node_id,
                domain=domain,
                stance=stance,
                confidence=min(0.95, max(0.3, base_confidence)),
                provenance_quality=quality,
                content=f"Claim from {node.node_id}",
                timestamp=datetime.utcnow(),
            )

            return claim

        except Exception as e:
            self.logger.warning(f"Failed to generate claim from {node.node_id}: {e}")
            return None

    async def _process_claim_batch(
        self,
        batch: List[Tuple[SimulatedClaim, FederatedNode]],
    ) -> List[ProcessedSimulationClaimResult]:
        """Process a batch of claims through the real processor."""
        results = []

        for claim, node in batch:
            try:
                # Convert FederatedNode to SimulatedNode for Phase 2A compatibility
                sim_node = self._federated_to_simulated(node)

                # Process through the REAL Phase 2A pipeline
                round_context = {
                    "round_num": self.current_epoch,
                    "scenario_name": "network_simulation",
                }

                result = await self.adapter.process_simulated_claim(
                    sim_claim=claim,
                    origin_node=sim_node,
                    round_context=round_context,
                )

                results.append(result)
                self.claims_processed_this_epoch += 1

            except Exception as e:
                self.logger.warning(f"Failed to process claim {claim.claim_id}: {e}")
                # Create error result
                results.append(
                    ProcessedSimulationClaimResult(
                        claim=claim,
                        accepted=False,
                        status="error",
                        rejection_reason=f"Processing error: {str(e)}",
                        error=str(e),
                    )
                )

        return results

    def _federated_to_simulated(self, node: FederatedNode) -> SimulatedNode:
        """Convert FederatedNode to SimulatedNode for Phase 2A compatibility."""
        # Create a compatible SimulatedNode
        from ..models import NodeBehaviorProfile, NodeState, NodeType, QualityLevel

        # Determine node type
        node_type = NodeType.NORMAL
        if node.behavior.adversarial_mode == "flood":
            node_type = NodeType.FLOOD
        elif node.behavior.adversarial_mode == "monoculture":
            node_type = NodeType.MONOCULTURE
        elif node.behavior.adversarial_mode == "capture":
            node_type = NodeType.AUTHORITY_CAPTURE

        # Map quality mean to QualityLevel
        quality_mean = node.behavior.quality_mean
        if quality_mean >= 0.8:
            quality_level = QualityLevel.HIGH
        elif quality_mean >= 0.5:
            quality_level = QualityLevel.MEDIUM
        else:
            quality_level = QualityLevel.LOW

        # Create node behavior profile
        node_profile = NodeBehaviorProfile(
            baseline_trust=node.trust_state.baseline_trust,
            domains=[node.domain_spec.primary_domain],
            base_claim_rate=node.behavior.claim_frequency,
            stance_bias=node.behavior.stance_distribution.copy(),
            quality_level=quality_level,
            adversarial_mode=node.behavior.adversarial_mode,
            node_type=node_type,
        )

        # Create node state
        node_state = NodeState(
            node_id=node.node_id,
            profile=node_profile,
            current_trust=node.trust_state.current_trust,
        )

        # Create simulated node
        sim_node = SimulatedNode(
            node_id=node.node_id,
            profile=node_profile,
            state=node_state,
        )

        return sim_node

    async def _collect_epoch_report(self, epoch_number: int) -> EpochReport:
        """Collect metrics for the current epoch."""
        # Count claim outcomes
        claims_generated = len(self.epoch_results)
        claims_processed = sum(1 for r in self.epoch_results if r.status != "error")
        claims_accepted = sum(1 for r in self.epoch_results if r.accepted)
        claims_quarantined = sum(1 for r in self.epoch_results if r.status == "quarantined")
        claims_rejected = sum(1 for r in self.epoch_results if r.status == "rejected")

        # Trust state
        nodes = self.registry.get_all_nodes()
        trusts = [n.current_trust for n in nodes]
        avg_trust = sum(trusts) / len(trusts) if trusts else 0.5
        min_trust = min(trusts) if trusts else 0.0
        max_trust = max(trusts) if trusts else 1.0
        quarantined = self.registry.get_quarantined_nodes()

        # Network metrics
        health_metrics = self.metrics_calculator.calculate_network_health()
        influence = self.metrics_calculator.calculate_influence_distribution()
        collapse = self.metrics_calculator.calculate_collapse_indicators()

        # Predictive metrics (simplified for now - full integration would require
        # maintaining claim history across epochs)
        eddr = None
        aca = None
        fcri = None

        report = EpochReport(
            epoch_number=epoch_number,
            timestamp=datetime.utcnow(),
            node_count=len(nodes),
            active_nodes=len(nodes) - len(quarantined),
            claims_generated=claims_generated,
            claims_processed=claims_processed,
            claims_accepted=claims_accepted,
            claims_quarantined=claims_quarantined,
            claims_rejected=claims_rejected,
            avg_trust=avg_trust,
            min_trust=min_trust,
            max_trust=max_trust,
            quarantined_nodes=len(quarantined),
            network_density=health_metrics.density,
            avg_path_length=health_metrics.avg_path_length,
            clustering_coefficient=health_metrics.clustering,
            connected_components=health_metrics.connected_components,
            gini_coefficient=influence.gini_coefficient,
            top_1_influence_share=influence.top_1_share,
            top_5_influence_share=influence.top_5_share,
            eddr=eddr,
            aca=aca,
            fcri=fcri,
            collapse_risk=collapse.get_collapse_risk(),
            dominance_alert=collapse.dominance_alert,
            fragmentation_acceleration=collapse.fragmentation_acceleration,
        )

        return report

    def _log_epoch_report(self, report: EpochReport) -> None:
        """Log epoch report summary."""
        self.logger.info(
            f"Epoch {report.epoch_number}: "
            f"{report.claims_accepted}/{report.claims_processed} accepted, "
            f"avg_trust={report.avg_trust:.3f}, "
            f"health={report.network_density:.2f}, "
            f"risk={report.collapse_risk}"
        )


def create_network_executor(
    config: NetworkSimulationConfig,
    processor: Optional[InboundFederatedClaimProcessor] = None,
    identity_guard: Optional[FederationIdentityGuard] = None,
) -> NetworkSimulationExecutor:
    """
    Factory function to create a network simulation executor.

    Args:
        config: Network simulation configuration
        processor: Optional pre-configured claim processor
        identity_guard: Optional pre-configured identity guard

    Returns:
        Configured NetworkSimulationExecutor
    """
    if identity_guard is None:
        from ...federation_identity_guard import FederationIdentityGuard
        identity_guard = FederationIdentityGuard()

    if processor is None:
        from ...inbound_claim_processor import (
            InboundFederatedClaimProcessor,
            ProcessorConfig,
        )
        from ...safeguards.federation_eligibility_filter import (
            create_eligibility_filter,
        )
        from ...safeguards.context_similarity_engine import (
            create_context_similarity_engine,
        )
        from ...safeguards.plurality_preservation_rules import (
            create_plurality_preservation_rules,
        )
        from ...safeguards.allocative_boundary_guard import (
            create_allocative_boundary_guard,
        )
        from ...safeguards.trust_decay_model import (
            create_trust_decay_model,
        )

        processor_config = ProcessorConfig(
            enable_eligibility_filter=True,
            enable_similarity_engine=True,
            enable_plurality_preservation=True,
            enable_allocative_boundaries=True,
            enable_trust_decay=True,
        )

        processor = InboundFederatedClaimProcessor(
            identity_guard=identity_guard,
            config=processor_config,
            eligibility_filter=create_eligibility_filter(),
            similarity_engine=create_context_similarity_engine(),
            plurality_rules=create_plurality_preservation_rules(),
            allocative_guard=create_allocative_boundary_guard(),
            trust_decay=create_trust_decay_model(),
        )

    return NetworkSimulationExecutor(config, processor, identity_guard)


async def run_network_simulation(
    node_count: int = 10,
    topology_type: str = "small_world",
    epochs: int = 20,
    claims_per_epoch: int = 50,
    verbose: bool = True,
) -> NetworkSimulationReport:
    """
    Quick-start function to run a network simulation.

    Args:
        node_count: Number of nodes in the network
        topology_type: Type of network topology
        epochs: Number of simulation epochs
        claims_per_epoch: Claims to generate per epoch
        verbose: Enable verbose logging

    Returns:
        NetworkSimulationReport with results
    """
    from ...federation_identity_guard import FederationIdentityGuard
    from ...inbound_claim_processor import InboundFederatedClaimProcessor

    # Create config
    config = NetworkSimulationConfig(
        node_count=node_count,
        topology_type=topology_type,
        epochs=epochs,
        claims_per_epoch=claims_per_epoch,
        verbose=verbose,
    )

    # Create processor and guard
    from ...inbound_claim_processor import (
        InboundFederatedClaimProcessor,
        ProcessorConfig,
    )
    from ...safeguards.federation_eligibility_filter import (
        create_eligibility_filter,
    )
    from ...safeguards.context_similarity_engine import (
        create_context_similarity_engine,
    )
    from ...safeguards.plurality_preservation_rules import (
        create_plurality_preservation_rules,
    )
    from ...safeguards.allocative_boundary_guard import (
        create_allocative_boundary_guard,
    )
    from ...safeguards.trust_decay_model import (
        create_trust_decay_model,
    )

    identity_guard = FederationIdentityGuard()

    processor_config = ProcessorConfig(
        enable_eligibility_filter=True,
        enable_similarity_engine=True,
        enable_plurality_preservation=True,
        enable_allocative_boundaries=True,
        enable_trust_decay=True,
    )

    processor = InboundFederatedClaimProcessor(
        identity_guard=identity_guard,
        config=processor_config,
        eligibility_filter=create_eligibility_filter(),
        similarity_engine=create_context_similarity_engine(),
        plurality_rules=create_plurality_preservation_rules(),
        allocative_guard=create_allocative_boundary_guard(),
        trust_decay=create_trust_decay_model(),
    )

    # Create and run executor
    executor = create_network_executor(config, processor, identity_guard)
    report = await executor.run_simulation()

    return report
