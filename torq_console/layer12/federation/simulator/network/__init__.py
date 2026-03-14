"""
Federation Network Simulator

Layer 12 Phase 2B — Multi-Node Federation Scale Validation

Extends the single-process simulator to true multi-node federation simulation
that validates system stability under realistic distributed network conditions.

Components:
- NodeRegistry: Track simulated nodes and their evolving properties
- EventScheduler: Simulate asynchronous distributed activity
- NetworkController: Orchestrate multi-node simulation
- NetworkMetricsEngine: Network-scale metrics beyond node-level
- Scenarios: Predefined simulation scenarios for testing specific behaviors
"""

from .node_registry import NodeRegistry, SimulatedNetworkNode, create_node_registry
from .event_scheduler import EventScheduler, SimulationEvent, EventType, create_event_scheduler
from .network_controller import FederationNetworkController, NetworkTopology, NetworkSimulationConfig, create_network_controller
from .network_metrics import NetworkMetricsEngine, NetworkSnapshot, create_network_metrics_engine
from .scenarios import (
    NetworkScenarioConfig,
    RiskPosture,
    ScenarioType,
    ScenarioExecutionContext,
    SCENARIO_REGISTRY,
    calibrate_claim_quality_for_acceptance,
    create_scenario_config,
    get_baseline_scenario,
    get_claim_quality_for_scenario,
    get_contradiction_fragmentation_scenario,
    get_domain_capture_scenario,
    get_multi_node_adversarial_coalition_scenario,
    get_network_growth_scenario,
    get_scenario,
    get_trust_cascade_failure_scenario,
    list_scenarios,
)

__all__ = [
    "NodeRegistry",
    "SimulatedNetworkNode",
    "create_node_registry",
    "EventScheduler",
    "SimulationEvent",
    "EventType",
    "create_event_scheduler",
    "FederationNetworkController",
    "NetworkTopology",
    "NetworkSimulationConfig",
    "create_network_controller",
    "NetworkMetricsEngine",
    "NetworkSnapshot",
    "create_network_metrics_engine",
    # Scenarios
    "NetworkScenarioConfig",
    "RiskPosture",
    "ScenarioType",
    "ScenarioExecutionContext",
    "SCENARIO_REGISTRY",
    "calibrate_claim_quality_for_acceptance",
    "create_scenario_config",
    "get_baseline_scenario",
    "get_claim_quality_for_scenario",
    "get_contradiction_fragmentation_scenario",
    "get_domain_capture_scenario",
    "get_multi_node_adversarial_coalition_scenario",
    "get_network_growth_scenario",
    "get_scenario",
    "get_trust_cascade_failure_scenario",
    "list_scenarios",
]
