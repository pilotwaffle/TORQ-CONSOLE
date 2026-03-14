"""
Phase 2B Network Simulation Scenarios

Layer 12 Phase 2B — Multi-Node Federation Scale Validation

Predefined network simulation scenarios that test specific federation behaviors:
- network_growth: Federation expansion dynamics
- domain_capture: Single domain dominance
- trust_cascade_failure: Trust collapse propagation
- contradiction_fragmentation: Network splitting from disagreement
- multi_node_adversarial_coalition: Coordinated adversarial behavior
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .network_controller import NetworkSimulationConfig, NetworkTopology
from ..models import Domain, NodeBehaviorProfile, NodeType, Stance


# ============================================================================
# Scenario Types
# ============================================================================

class ScenarioType(str, Enum):
    """Predefined network simulation scenarios."""

    NETWORK_GROWTH = "network_growth"
    DOMAIN_CAPTURE = "domain_capture"
    TRUST_CASCADE_FAILURE = "trust_cascade_failure"
    CONTRADICTION_FRAGMENTATION = "contradiction_fragmentation"
    MULTI_NODE_ADVERSARIAL_COALITION = "multi_node_adversarial_coalition"
    BASELINE = "baseline"


# ============================================================================
# Expected Risk Posture
# ============================================================================

class RiskPosture(str, Enum):
    """Expected risk classification for scenario."""

    LOW = "low"  # Healthy federation, low risk
    MODERATE = "moderate"  # Some concerning patterns
    ELEVATED = "elevated"  # Significant risk indicators
    HIGH = "high"  # Critical risk, potential failure
    CRITICAL = "critical"  # Imminent collapse or capture


# ============================================================================
# Scenario Configuration
# ============================================================================

class NetworkScenarioConfig(BaseModel):
    """Configuration for a specific network simulation scenario."""

    scenario_type: ScenarioType = Field(..., description="Type of scenario")
    name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Scenario description")

    # Network configuration
    base_config: NetworkSimulationConfig = Field(
        ...,
        description="Base simulation configuration"
    )

    # Scenario-specific overrides
    node_count: int = Field(default=10, ge=1, le=50, description="Number of nodes")
    topology: NetworkTopology = Field(default=NetworkTopology.SMALL_WORLD)
    epochs: int = Field(default=25, ge=1, description="Simulation epochs")

    # Node behavior distribution
    adversarial_ratio: float = Field(default=0.1, ge=0.0, le=0.5)
    trust_distribution: str = Field(
        default="uniform",
        description="How trust is distributed: uniform, skewed, bimodal"
    )

    # Domain distribution
    num_domains: int = Field(default=5, ge=1, description="Active domains")
    domain_concentration: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="How concentrated domain expertise is"
    )

    # Claim generation
    claims_per_epoch: int = Field(default=20, ge=0)
    claim_quality_bias: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Average claim quality (affects acceptance)"
    )

    # Expected outcomes
    expected_risk_posture: RiskPosture = Field(
        default=RiskPosture.MODERATE,
        description="Expected risk level"
    )
    expected_acceptance_rate: tuple = Field(
        default=(0.2, 0.4),
        description="Expected (min, max) acceptance rate"
    )
    expected_resilience_range: tuple = Field(
        default=(0.5, 0.8),
        description="Expected (min, max) resilience score"
    )

    # Random seed for reproducibility
    random_seed: Optional[int] = Field(None, description="Random seed")

    class Config:
        use_enum_values = True


# ============================================================================
# Scenario Presets
# ============================================================================

def get_baseline_scenario() -> NetworkScenarioConfig:
    """Get baseline healthy federation scenario."""
    return NetworkScenarioConfig(
        scenario_type=ScenarioType.BASELINE,
        name="Baseline Healthy Federation",
        description="A well-functioning federation with balanced nodes",
        base_config=NetworkSimulationConfig(),
        node_count=10,
        topology=NetworkTopology.SMALL_WORLD,
        epochs=25,
        adversarial_ratio=0.1,
        trust_distribution="uniform",
        num_domains=5,
        domain_concentration=0.2,
        claims_per_epoch=20,
        claim_quality_bias=0.75,
        expected_risk_posture=RiskPosture.LOW,
        expected_acceptance_rate=(0.3, 0.5),
        expected_resilience_range=(0.7, 0.9),
        random_seed=42,
    )


def get_network_growth_scenario() -> NetworkScenarioConfig:
    """
    Network growth scenario - federation expansion dynamics.

    Tests how the federation handles new nodes joining:
    - Initially small network
    - Nodes added over time
    - Mix of experienced and new nodes
    - Tests trust integration of new members
    """
    return NetworkScenarioConfig(
        scenario_type=ScenarioType.NETWORK_GROWTH,
        name="Network Growth",
        description="Simulates federation growth with new nodes joining over time",
        base_config=NetworkSimulationConfig(
            num_nodes=20,
            num_epochs=50,
        ),
        node_count=20,
        topology=NetworkTopology.SMALL_WORLD,
        epochs=50,
        adversarial_ratio=0.05,  # Fewer adversarial nodes
        trust_distribution="skewed",  # Some high-trust, some new low-trust
        num_domains=6,
        domain_concentration=0.3,
        claims_per_epoch=40,
        claim_quality_bias=0.72,
        expected_risk_posture=RiskPosture.MODERATE,
        expected_acceptance_rate=(0.25, 0.45),
        expected_resilience_range=(0.65, 0.85),
        random_seed=100,
    )


def get_domain_capture_scenario() -> NetworkScenarioConfig:
    """
    Domain capture scenario - single domain dominance.

    Tests vulnerability to domain monoculture:
    - One domain dominates (e.g., TECHNICAL)
    - Other domains marginalized
    - Tests diversity erosion detection
    - Expected: EDDR should spike
    """
    return NetworkScenarioConfig(
        scenario_type=ScenarioType.DOMAIN_CAPTURE,
        name="Domain Capture",
        description="Single domain dominance scenario - tests diversity erosion",
        base_config=NetworkSimulationConfig(
            num_nodes=15,
            num_epochs=40,
        ),
        node_count=15,
        topology=NetworkTopology.HUB_AND_SPOKE,
        epochs=40,
        adversarial_ratio=0.0,  # No explicit adversarial nodes
        trust_distribution="bimodal",  # High trust in dominant domain, low in others
        num_domains=3,
        domain_concentration=0.8,  # HIGH concentration - one domain dominates
        claims_per_epoch=30,
        claim_quality_bias=0.70,
        expected_risk_posture=RiskPosture.HIGH,
        expected_acceptance_rate=(0.15, 0.35),  # Lower due to monoculture
        expected_resilience_range=(0.4, 0.7),
        random_seed=200,
    )


def get_trust_cascade_failure_scenario() -> NetworkScenarioConfig:
    """
    Trust cascade failure scenario.

    Tests vulnerability to trust collapse:
    - High-trust hub nodes begin failing
    - Trust scores cascade downward
    - Tests federation resilience to shock
    - Expected: FCRI should spike during cascade
    """
    return NetworkScenarioConfig(
        scenario_type=ScenarioType.TRUST_CASCADE_FAILURE,
        name="Trust Cascade Failure",
        description="Simulates trust collapse propagation through network",
        base_config=NetworkSimulationConfig(
            num_nodes=12,
            num_epochs=30,
        ),
        node_count=12,
        topology=NetworkTopology.HUB_AND_SPOKE,  # Vulnerable to cascade
        epochs=30,
        adversarial_ratio=0.15,  # Some adversarial nodes to trigger cascade
        trust_distribution="skewed",  # Hub has high trust initially
        num_domains=4,
        domain_concentration=0.4,
        claims_per_epoch=25,
        claim_quality_bias=0.65,  # Lower quality triggers cascade
        expected_risk_posture=RiskPosture.CRITICAL,
        expected_acceptance_rate=(0.05, 0.20),  # Collapses over time
        expected_resilience_range=(0.2, 0.6),  # Declines significantly
        random_seed=300,
    )


def get_contradiction_fragmentation_scenario() -> NetworkScenarioConfig:
    """
    Contradiction fragmentation scenario.

    Tests network splitting from irreconcilable disagreement:
    - Two opposing stance camps emerge
    - High contradiction detection
    - Network fragments into clusters
    - Tests FCRI under fragmentation stress
    """
    return NetworkScenarioConfig(
        scenario_type=ScenarioType.CONTRADICTION_FRAGMENTATION,
        name="Contradiction Fragmentation",
        description="Network splitting from opposing stance clusters",
        base_config=NetworkSimulationConfig(
            num_nodes=16,
            num_epochs=35,
        ),
        node_count=16,
        topology=NetworkTopology.RANDOM_GRAPH,  # More prone to fragmentation
        epochs=35,
        adversarial_ratio=0.0,  # Structural, not adversarial
        trust_distribution="bimodal",  # Two camps
        num_domains=5,
        domain_concentration=0.3,
        claims_per_epoch=35,
        claim_quality_bias=0.68,
        expected_risk_posture=RiskPosture.ELEVATED,
        expected_acceptance_rate=(0.1, 0.3),  # Lower due to contradictions
        expected_resilience_range=(0.3, 0.65),  # Fragments over time
        random_seed=400,
    )


def get_multi_node_adversarial_coalition_scenario() -> NetworkScenarioConfig:
    """
    Multi-node adversarial coalition scenario.

    Tests coordinated adversarial behavior:
    - Multiple adversarial nodes coordinate
    - Attempts to manipulate consensus
    - Tests federation immune response
    - Expected: ACA should rise early
    """
    return NetworkScenarioConfig(
        scenario_type=ScenarioType.MULTI_NODE_ADVERSARIAL_COALITION,
        name="Multi-Node Adversarial Coalition",
        description="Coordinated adversarial nodes attempting manipulation",
        base_config=NetworkSimulationConfig(
            num_nodes=20,
            num_epochs=40,
            adversarial_ratio=0.3,  # 30% adversarial
        ),
        node_count=20,
        topology=NetworkTopology.SMALL_WORLD,  # Good for coordination
        epochs=40,
        adversarial_ratio=0.3,  # High adversarial ratio
        trust_distribution="uniform",
        num_domains=5,
        domain_concentration=0.25,
        claims_per_epoch=40,
        claim_quality_bias=0.60,  # Adversarial nodes push low quality
        expected_risk_posture=RiskPosture.HIGH,
        expected_acceptance_rate=(0.1, 0.25),  # Lower due to adversarial activity
        expected_resilience_range=(0.4, 0.7),
        random_seed=500,
    )


# ============================================================================
# Scenario Registry
# ============================================================================

SCENARIO_REGISTRY: Dict[ScenarioType, NetworkScenarioConfig] = {
    ScenarioType.BASELINE: get_baseline_scenario(),
    ScenarioType.NETWORK_GROWTH: get_network_growth_scenario(),
    ScenarioType.DOMAIN_CAPTURE: get_domain_capture_scenario(),
    ScenarioType.TRUST_CASCADE_FAILURE: get_trust_cascade_failure_scenario(),
    ScenarioType.CONTRADICTION_FRAGMENTATION: get_contradiction_fragmentation_scenario(),
    ScenarioType.MULTI_NODE_ADVERSARIAL_COALITION: get_multi_node_adversarial_coalition_scenario(),
}


def get_scenario(scenario_type: ScenarioType) -> NetworkScenarioConfig:
    """Get scenario configuration by type."""
    if scenario_type not in SCENARIO_REGISTRY:
        raise ValueError(f"Unknown scenario type: {scenario_type}")
    return SCENARIO_REGISTRY[scenario_type]


def list_scenarios() -> List[NetworkScenarioConfig]:
    """List all available scenarios."""
    return list(SCENARIO_REGISTRY.values())


# ============================================================================
# Scenario Factory
# ============================================================================

def create_scenario_config(
    scenario_type: ScenarioType,
    **overrides
) -> NetworkSimulationConfig:
    """
    Create NetworkSimulationConfig from scenario.

    Applies scenario-specific settings to base configuration.

    Args:
        scenario_type: Type of scenario
        **overrides: Additional configuration overrides

    Returns:
        NetworkSimulationConfig ready for simulation
    """
    scenario = get_scenario(scenario_type)

    # Build config from scenario
    config = NetworkSimulationConfig(
        num_nodes=overrides.get('num_nodes', scenario.node_count),
        topology=overrides.get('topology', scenario.topology),
        num_epochs=overrides.get('epochs', scenario.epochs),
        adversarial_ratio=overrides.get('adversarial_ratio', scenario.adversarial_ratio),
        num_domains=scenario.num_domains,
        claims_per_epoch=scenario.claims_per_epoch,
        random_seed=overrides.get('random_seed', scenario.random_seed),
    )

    return config


# ============================================================================
# Scenario Execution Context
# ============================================================================

@dataclass
class ScenarioExecutionContext:
    """Context for running a scenario simulation."""

    scenario: NetworkScenarioConfig
    config: NetworkSimulationConfig
    start_time: datetime
    end_time: Optional[datetime] = None
    result: Optional[Any] = None  # NetworkSimulationResult

    # Validation results
    acceptance_rate_match: bool = False
    resilience_match: bool = False
    risk_posture_match: bool = False

    def validate_outcomes(self) -> Dict[str, Any]:
        """Validate simulation results against scenario expectations."""
        if not self.result:
            return {"status": "no_results"}

        acceptance_in_range = (
            self.result.acceptance_rate >= self.scenario.expected_acceptance_rate[0]
            and self.result.acceptance_rate <= self.scenario.expected_acceptance_rate[1]
        )
        self.acceptance_rate_match = acceptance_in_range

        if self.result.final_network_metrics:
            resilience = self.result.final_network_metrics.network_resilience_score
            resilience_in_range = (
                resilience >= self.scenario.expected_resilience_range[0]
                and resilience <= self.scenario.expected_resilience_range[1]
            )
            self.resilience_match = resilience_in_range

        return {
            "acceptance_rate": self.result.acceptance_rate,
            "acceptance_rate_expected": self.scenario.expected_acceptance_rate,
            "acceptance_match": acceptance_in_range,
            "resilience": (
                self.result.final_network_metrics.network_resilience_score
                if self.result.final_network_metrics else None
            ),
            "resilience_expected": self.scenario.expected_resilience_range,
            "resilience_match": self.resilience_match,
            "risk_posture": self.scenario.expected_risk_posture,
        }


# ============================================================================
# Claim Generation Calibration
# ============================================================================

def calibrate_claim_quality_for_acceptance(
    target_acceptance: float,
    current_acceptance: float,
    current_quality: float,
) -> float:
    """
    Adjust claim quality bias to achieve target acceptance rate.

    Uses simple proportional adjustment:
    - If acceptance too low, increase quality
    - If acceptance too high, decrease quality

    Args:
        target_acceptance: Desired acceptance rate (0-1)
        current_acceptance: Current observed rate (0-1)
        current_quality: Current claim quality bias (0-1)

    Returns:
        Adjusted quality bias
    """
    if current_acceptance < 0.01:
        # Avoid division by zero
        adjustment = 0.1
    else:
        # Proportional adjustment
        ratio = target_acceptance / max(current_acceptance, 0.01)
        adjustment = (ratio - 1.0) * 0.5

    new_quality = max(0.5, min(0.95, current_quality + adjustment))
    return new_quality


def get_claim_quality_for_scenario(scenario_type: ScenarioType) -> float:
    """
    Get recommended claim quality bias for a scenario.

    Based on scenario calibration requirements.
    """
    # These values are calibrated for meaningful signal-rich behavior
    calibration_map = {
        ScenarioType.BASELINE: 0.78,  # Higher quality for baseline
        ScenarioType.NETWORK_GROWTH: 0.76,
        ScenarioType.DOMAIN_CAPTURE: 0.72,
        ScenarioType.TRUST_CASCADE_FAILURE: 0.68,  # Lower to trigger cascade
        ScenarioType.CONTRADICTION_FRAGMENTATION: 0.70,
        ScenarioType.MULTI_NODE_ADVERSARIAL_COALITION: 0.65,  # Low for adversarial
    }
    return calibration_map.get(scenario_type, 0.75)
