"""
Federation Simulator Package

Layer 12 Phase 2A — Federation Stability Validation Harness

A comprehensive testing framework for validating TORQ federation safeguards
under realistic network pressure and adversarial conditions.
"""

# Version
__version__ = "1.0.0"
__author__ = "TORQ Team"
__description__ = "TORQ Federation Stability Validation Harness"

# Exports
from .models import (
    # Enums
    NodeType,
    Stance,
    QualityLevel,
    Domain,

    # Node models
    NodeBehaviorProfile,
    NodeState,
    SimulatedNode,

    # Claim models
    SimulatedClaim,

    # Simulation models
    SimulationRound,
    SimulationScenario,
    SimulationMetrics,
    SimulationReport,

    # Predictive risk models
    PredictiveRiskStatus,
    EpistemicDiversityDecayResult,
    AuthorityCaptureAccelerationResult,
    FederationCollapseRiskResult,
    RoundSummary,
)

from .scenarios import (
    SCENARIO_REGISTRY,
    get_scenario,
    list_scenarios,
    create_custom_scenario,
    # Specific scenario creators
    create_baseline_healthy_exchange,
    create_insight_flooding_attack,
    create_semantic_monoculture,
    create_minority_viewpoint_suppression,
    create_authority_concentration,
    create_trust_drift_gaming,
    create_compound_adversarial_network,
    create_replay_duplicate_persistence,
)

from .metrics import FederationMetricsAggregator

from .health_index import (
    FederationHealthIndexCalculator,
    FederationHealthTracker,
    HealthStatus,
)

from .executor import FederationSimulationExecutor
from .executor_async import (
    AsyncFederationSimulationExecutor,
    create_async_executor,
)
from .processor_adapter import (
    ProcessorAdapter,
    ProcessedSimulationClaimResult,
    process_claims_batch,
)

from .assertions import (
    AssertionRegistry,
    AssertionResult,
    AssertionStatus,
    # Assertion sets
    create_baseline_healthy_assertions,
    create_insight_flooding_assertions,
    create_semantic_monoculture_assertions,
    create_authority_concentration_assertions,
    create_compound_adversarial_assertions,
    AssertionRunner,
)

# Public API
__all__ = [
    # Models
    "NodeType",
    "Stance",
    "QualityLevel",
    "Domain",
    "HealthStatus",
    "NodeBehaviorProfile",
    "NodeState",
    "SimulatedNode",
    "SimulatedClaim",
    "SimulationRound",
    "SimulationScenario",
    "SimulationMetrics",
    "SimulationReport",
    "PredictiveRiskStatus",
    "EpistemicDiversityDecayResult",
    "AuthorityCaptureAccelerationResult",
    "FederationCollapseRiskResult",
    "RoundSummary",

    # Scenarios
    "SCENARIO_REGISTRY",
    "get_scenario",
    "list_scenarios",
    "create_custom_scenario",
    "create_baseline_healthy_exchange",
    "create_insight_flooding_attack",
    "create_semantic_monoculture",
    "create_minority_viewpoint_suppression",
    "create_authority_concentration",
    "create_trust_drift_gaming",
    "create_compound_adversarial_network",
    "create_replay_duplicate_persistence",

    # Metrics
    "FederationMetricsAggregator",

    # Health Index
    "FederationHealthIndexCalculator",
    "FederationHealthTracker",

    # Executors
    "FederationSimulationExecutor",
    "AsyncFederationSimulationExecutor",
    "create_async_executor",

    # Processor Adapter
    "ProcessorAdapter",
    "ProcessedSimulationClaimResult",
    "process_claims_batch",

    # Assertions
    "AssertionRegistry",
    "AssertionResult",
    "AssertionStatus",
    "create_baseline_healthy_assertions",
    "create_insight_flooding_assertions",
    "create_semantic_monoculture_assertions",
    "create_authority_concentration_assertions",
    "create_compound_adversarial_assertions",
    "AssertionRunner",
]