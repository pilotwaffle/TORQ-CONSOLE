"""
Phase 2B — Multi-Node Federation Scale Validation

This package extends the Phase 2A simulator to support:
- 10-50 node federation networks
- Multiple topology types (small-world, scale-free, hierarchical)
- Event-driven simulation
- Network-scale metrics and collapse detection

Components:
- NodeRegistry: Node identity, trust, domain specialization, influence tracking
- NetworkController: Topology creation, node spawning, epoch orchestration
- EventScheduler: Event-driven simulation engine
- NetworkMetrics: Centrality, clustering, collapse indicators
- Topologies: Network topology generators
- Behaviors: Node behavior profiles and adversarial modes
"""

from .node_registry import (
    NodeIdentity,
    NodeTrustState,
    DomainSpecialization,
    InfluenceProfile,
    BehaviorProfile,
    FederatedNode,
    NodeRegistry,
    create_node,
    create_nodes_with_distribution,
)

from .network_controller import (
    NetworkTopology,
    NetworkConfig,
    EpochConfig,
    NetworkSnapshot,
    NetworkController,
    create_network_controller,
)

from .event_scheduler import (
    SimulationEvent,
    ClaimPublicationEvent,
    TrustAdjustmentEvent,
    NodeJoinEvent,
    NodeLeaveEvent,
    EpochEndEvent,
    AdversarialAttackEvent,
    NetworkPartitionEvent,
    NetworkHealEvent,
    EventResult,
    EventScheduler,
    create_event_scheduler,
)

from .network_metrics import (
    CentralityMetrics,
    NetworkHealthMetrics,
    InfluenceDistribution,
    NetworkCollapseIndicators,
    NetworkFlowMetrics,
    NetworkMetricsCalculator,
    create_network_metrics_calculator,
)

__all__ = [
    # Node Registry
    "NodeIdentity",
    "NodeTrustState",
    "DomainSpecialization",
    "InfluenceProfile",
    "BehaviorProfile",
    "FederatedNode",
    "NodeRegistry",
    "create_node",
    "create_nodes_with_distribution",
    # Network Controller
    "NetworkTopology",
    "NetworkConfig",
    "EpochConfig",
    "NetworkSnapshot",
    "NetworkController",
    "create_network_controller",
    # Event Scheduler
    "SimulationEvent",
    "ClaimPublicationEvent",
    "TrustAdjustmentEvent",
    "NodeJoinEvent",
    "NodeLeaveEvent",
    "EpochEndEvent",
    "AdversarialAttackEvent",
    "NetworkPartitionEvent",
    "NetworkHealEvent",
    "EventResult",
    "EventScheduler",
    "create_event_scheduler",
    # Network Metrics
    "CentralityMetrics",
    "NetworkHealthMetrics",
    "InfluenceDistribution",
    "NetworkCollapseIndicators",
    "NetworkFlowMetrics",
    "NetworkMetricsCalculator",
    "create_network_metrics_calculator",
]
