"""
Federation Simulator Scenarios

Layer 12 Phase 2A — Federation Stability Validation Harness

Library of 8 stress-test scenarios for validating federation safeguards.
"""

import logging
from datetime import timedelta
from typing import Dict, List, Optional

from .models import (
    Domain,
    NodeBehaviorProfile,
    NodeType,
    SimulatedNode,
    SimulationScenario,
    Stance,
)

logger = logging.getLogger(__name__)


def create_baseline_healthy_exchange() -> SimulationScenario:
    """Scenario A: Baseline healthy exchange.

    Purpose: Establish what "good federation behavior" looks like.

    Setup:
    - 5 nodes
    - moderate claim volume
    - mixed domains
    - balanced trust
    - normal contradiction rates
    - no adversarial spam
    - no single node dominance

    Expected result:
    - claims flow smoothly
    - diversity remains healthy
    - minority viewpoints are preserved
    - trust remains stable
    - no node becomes excessively dominant
    """

    return SimulationScenario(
        name="baseline_healthy_exchange",
        description="Establish baseline healthy federation behavior",
        num_nodes=5,
        rounds=20,
        domain_distribution={
            Domain.TECHNICAL: 0.25,
            Domain.STRATEGIC: 0.25,
            Domain.OPERATIONAL: 0.25,
            Domain.FINANCIAL: 0.15,
            Domain.SECURITY: 0.10,
        },
        node_types=[
            NodeType.NORMAL,
            NodeType.NORMAL,
            NodeType.NORMAL,
            NodeType.EXPERT,
            NodeType.CAUTIOUS,
        ],
        adversarial_nodes=[],
        expected_guardian_triggers=[],
        expected_outcomes={
            "diversity_health": ">0.80",
            "influence_balance": ">0.75",
            "trust_stability": ">0.85",
            "health_status": "healthy",
            "top_node_share": "<0.30",
        },
    )


def create_insight_flooding_attack() -> SimulationScenario:
    """Scenario B: Insight flooding attack.

    Purpose: Stress-test FederationEligibilityFilter.

    Setup:
    - one node begins publishing at very high frequency
    - lower average claim quality
    - repeated phrases or spam-like keyword structures
    - some near-duplicate claims

    Expected result:
    - rate limiter activates
    - low-quality claims are rejected or throttled
    - duplicate suppression increases
    - flooding node does not dominate network discourse

    Failure signal:
    if claim volume from the attacker materially shifts network topic distribution
    or trust influence, the filter is too weak.
    """

    return SimulationScenario(
        name="insight_flooding_attack",
        description="Test FederationEligibilityFilter against flood attacks",
        num_nodes=5,
        rounds=20,
        domain_distribution={
            Domain.GENERAL: 0.8,  # Flood general domain
            Domain.TECHNICAL: 0.2,
        },
        node_types=[
            NodeType.NORMAL,
            NodeType.NORMAL,
            NodeType.NORMAL,
            NodeType.NORMAL,
            NodeType.AGGRESSIVE,  # Flooding node
        ],
        adversarial_nodes=["node_4"],
        adversarial_modes={"node_4": "flood"},
        expected_guardian_triggers=["FederationEligibilityFilter"],
        expected_outcomes={
            "flood_node_share": "<0.25",  # Attacker should not dominate
            "rejection_rate": ">0.40",  # High rejection for spam
            "duplicate_suppression_rate": ">0.15",
            "FederationEligibilityFilter_triggers": ">10",
            "diversity_health": ">0.70",  # Should maintain diversity
        },
    )


def create_semantic_monoculture() -> SimulationScenario:
    """Scenario C: Semantic monoculture / context collapse.

    Purpose: Stress-test ContextSimilarityEngine.

    Setup:
    - 3 nodes increasingly publish highly similar claims on the same topic cluster
    - one topic begins crowding out all other domains
    - semantic overlap rises round by round

    Expected result:
    - dominant cluster is detected
    - entropy drops are flagged
    - source concentration warnings appear
    - system surfaces monoculture risk before collapse becomes severe

    Failure signal:
    if one semantic cluster absorbs most network attention without warnings or controls,
    context collapse detection is insufficient.
    """

    return SimulationScenario(
        name="semantic_monoculture",
        description="Test ContextSimilarEngine against semantic monoculture",
        num_nodes=5,
        rounds=20,
        domain_distribution={
            Domain.TECHNICAL: 0.1,
            Domain.STRATEGIC: 0.1,
            Domain.OPERATIONAL: 0.1,
            Domain.FINANCIAL: 0.1,
            Domain.SECURITY: 0.6,  # Security domain dominates
        },
        node_types=[
            NodeType.NORMAL,
            NodeType.NORMAL,
            NodeType.NORMAL,
            NodeType.AGGRESSIVE,  # Aggressive security focus
            NodeType.AGGRESSIVE,  # Another aggressive node
        ],
        adversarial_nodes=["node_3", "node_4"],
        adversarial_modes={"node_3": "monoculture", "node_4": "monoculture"},
        expected_guardian_triggers=["ContextSimilarityEngine"],
        expected_outcomes={
            "topic_entropy": ">0.60",  # Should maintain some diversity
            "source_concentration_alerts": ">3",
            "ContextSimilarityEngine_triggers": ">8",
            "domain_diversity": ">0.50",  # Should detect monoculture
            "security_domain_share": "<0.80",  # Should not completely dominate
        },
    )


def create_minority_viewpoint_suppression() -> SimulationScenario:
    """Scenario D: Minority viewpoint suppression.

    Purpose: Stress-test PluralityPreservationRules.

    Setup:
    - 4 nodes publish mostly similar positive/affirmative stances
    - 1 node consistently publishes a valid but contradictory or conditional perspective
    - minority view is high quality but low frequency

    Expected result:
    - minority viewpoint is recognized as legitimate plurality
    - contradiction is tracked as healthy signal, not noise
    - minority perspective remains visible in reports and downstream qualification
    - system avoids collapsing everything into consensus

    Failure signal:
    if the minority perspective disappears from network significance despite quality
    and relevance, plurality preservation is failing.
    """

    return SimulationScenario(
        name="minority_viewpoint_suppression",
        description="Test PluralityPreservationRules for minority viewpoint protection",
        num_nodes=5,
        rounds=20,
        domain_distribution={
            Domain.STRATEGIC: 0.5,  # Strategic domain for testing stances
            Domain.OPERATIONAL: 0.5,
        },
        node_types=[
            NodeType.NORMAL,
            NodeType.NORMAL,
            NodeType.NORMAL,
            NodeType.NORMAL,
            NodeType.CAUTIOUS,  # Minority viewpoint node
        ],
        adversarial_nodes=["node_4"],
        adversarial_modes={"node_4": "minority"},
        expected_guardian_triggers=["PluralityPreservationRules"],
        expected_outcomes={
            "minority_viewpoint_representation": ">0.15",  # Should be preserved
            "contradiction_retention_rate": ">0.30",  # Should track contradictions
            "PluralityPreservationRules_triggers": ">5",
            "stance_diversity": ">0.60",  # Should maintain stance diversity
            "consensus_pressure": "<0.70",  # Should not become too consensus
        },
    )


def create_authority_concentration() -> SimulationScenario:
    """Scenario E: Authority concentration.

    Purpose: Stress-test AllocativeBoundaryGuard.

    Setup:
    - one or two nodes start with higher trust and higher output volume
    - those nodes dominate several domains simultaneously
    - network begins over-weighting their claims

    Expected result:
    - Gini and HHI rise and are flagged
    - top-node dominance detection triggers
    - throttling or balancing mechanisms prevent runaway influence
    - domain leadership stays distributed

    Failure signal:
    if a small minority of nodes capture most accepted influence across domains,
    allocative safeguards are too weak.
    """

    return SimulationScenario(
        name="authority_concentration",
        description="Test AllocativeBoundaryGuard against authority concentration",
        num_nodes=5,
        rounds=20,
        domain_distribution={
            Domain.TECHNICAL: 0.3,
            Domain.STRATEGIC: 0.3,
            Domain.OPERATIONAL: 0.2,
            Domain.FINANCIAL: 0.2,
        },
        node_types=[
            NodeType.NORMAL,
            NodeType.EXPERT,  # High-trust node
            NodeType.EXPERT,  # Another high-trust node
            NodeType.NORMAL,
            NodeType.NORMAL,
        ],
        adversarial_nodes=["node_1", "node_2"],
        adversarial_modes={"node_1": "dominance", "node_2": "dominance"},
        expected_guardian_triggers=["AllocativeBoundaryGuard"],
        expected_outcomes={
            "gini_coefficient": "<0.60",  # Should not exceed threshold
            "herfindahl_index": "<0.40",  # Should be moderate
            "top_node_concentration": "<0.50",  # No single node should dominate
            "AllocativeBoundaryGuard_triggers": ">6",
            "domain_leadership_balance": ">0.65",  # Should be balanced
        },
    )


def create_trust_drift_gaming() -> SimulationScenario:
    """Scenario F: Trust drift / trust gaming.

    Purpose: Stress-test TrustDecayModel.

    Setup:
    - one node shows sudden trust spike without proportional behavior quality
    - another node slowly degrades over time
    - another exhibits high volatility
    - one node alternates between excellent and poor behavior to game averages

    Expected result:
    - anomalies are detected
    - volatility flags appear
    - effective trust gets adjusted over time
    - predicted trust trajectory reflects instability

    Failure signal:
    if unstable or manipulated nodes keep high effective influence without decay
    or anomaly penalties, the model needs tightening.
    """

    return SimulationScenario(
        name="trust_drift_gaming",
        description="Test TrustDecayModel against trust drift and gaming",
        num_nodes=5,
        rounds=20,
        domain_distribution={
            Domain.TECHNICAL: 0.3,
            Domain.STRATEGIC: 0.3,
            Domain.OPERATIONAL: 0.4,
        },
        node_types=[
            NodeType.NORMAL,
            NodeType.NORMAL,
            NodeType.NORMAL,
            NodeType.NORMAL,
            NodeType.ADVERSARIAL,  # Trust gaming node
        ],
        adversarial_nodes=["node_4"],
        adversarial_modes={"node_4": "trust_gaming"},
        expected_guardian_triggers=["TrustDecayModel"],
        expected_outcomes={
            "trust_anomalies_detected": ">3",
            "trust_volatility_flagged": ">2",
            "adjusted_trust_corrections": ">5",
            "TrustDecayModel_triggers": ">10",
            "effective_trust_stability": ">0.70",  # Should adjust to reality
        },
    )


def create_compound_adversarial_network() -> SimulationScenario:
    """Scenario G: Compound adversarial network pressure.

    Purpose: Stress-test the whole hardened pipeline together.

    Setup:
    - Node A floods
    - Node B dominates a topic cluster
    - Node C is a high-trust but volatile node
    - Node D carries a minority but legitimate stance
    - Node E behaves normally

    Expected result:
    - filters reject or throttle Node A
    - monoculture warnings surface around Node B
    - Node C's effective trust adjusts
    - Node D remains represented
    - total network stability remains acceptable

    This is the most important scenario after baseline.
    """

    return SimulationScenario(
        name="compound_adversarial_network",
        description="Test full hardened pipeline against compound adversarial pressure",
        num_nodes=5,
        rounds=25,
        domain_distribution={
            Domain.TECHNICAL: 0.2,
            Domain.SECURITY: 0.4,  # Security domain for monoculture
            Domain.GENERAL: 0.4,
        },
        node_types=[
            NodeType.NORMAL,  # Node E: normal behavior
            NodeType.NORMAL,
            NodeType.AGGRESSIVE,  # Node A: flooding
            NodeType.ADVERSARIAL,  # Node B: monoculture
            NodeType.ADVERSARIAL,  # Node C: trust gaming, Node D: minority viewpoint
        ],
        adversarial_nodes=["node_2", "node_3", "node_4"],
        adversarial_modes={
            "node_2": "flood",
            "node_3": "monoculture",
            "node_4": "trust_gaming,minority",
        },
        expected_guardian_triggers=[
            "FederationEligibilityFilter",
            "ContextSimilarityEngine",
            "PluralityPreservationRules",
            "TrustDecayModel",
        ],
        expected_outcomes={
            "overall_health_index": ">0.65",  # Should remain acceptable
            "diversity_health": ">0.60",
            "minority_viewpoint_representation": ">0.10",
            "all_guardians_triggered": True,
            "compound_resilience": "maintained",
        },
    )


def create_replay_duplicate_persistence() -> SimulationScenario:
    """Scenario H: Replay and near-duplicate persistence.

    Purpose: Validate that earlier federation protections still work under hardening.

    Setup:
    - repeated re-submission of claims across rounds
    - minor wording changes designed to evade duplicate detection
    - replay attempts under shifting timestamps

    Expected result:
    - replay protection catches exact replays
    - eligibility or duplicate logic catches near-duplicates
    - network does not re-amplify stale content
    """

    return SimulationScenario(
        name="replay_duplicate_persistence",
        description="Test replay and duplicate protection mechanisms",
        num_nodes=5,
        rounds=15,
        domain_distribution={
            Domain.TECHNICAL: 0.5,
            Domain.OPERATIONAL: 0.5,
        },
        node_types=[
            NodeType.NORMAL,
            NodeType.NORMAL,
            NodeType.NORMAL,
            NodeType.NORMAL,
            NodeType.ADVERSARIAL,  # Duplicate/replay node
        ],
        adversarial_nodes=["node_4"],
        adversarial_modes={"node_4": "replay"},
        expected_guardian_triggers=["FederationEligibilityFilter"],
        expected_outcomes={
            "duplicate_suppression_rate": ">0.30",
            "replay_detection_rate": ">0.80",
            "FederationEligibilityFilter_duplicate_rejections": ">8",
            "content_freshness_maintained": True,
            "network_amplification_rate": "<0.20",  # Should not amplify duplicates
        },
    )


# ============================================================================
# Scenario Registry
# ============================================================================

SCENARIO_REGISTRY = {
    "baseline_healthy_exchange": create_baseline_healthy_exchange,
    "insight_flooding_attack": create_insight_flooding_attack,
    "semantic_monoculture": create_semantic_monoculture,
    "minority_viewpoint_suppression": create_minority_viewpoint_suppression,
    "authority_concentration": create_authority_concentration,
    "trust_drift_gaming": create_trust_drift_gaming,
    "compound_adversarial_network": create_compound_adversarial_network,
    "replay_duplicate_persistence": create_replay_duplicate_persistence,
}


def get_scenario(scenario_name: str) -> SimulationScenario:
    """Get a scenario by name."""
    if scenario_name not in SCENARIO_REGISTRY:
        raise ValueError(f"Unknown scenario: {scenario_name}. Available: {list(SCENARIO_REGISTRY.keys())}")

    return SCENARIO_REGISTRY[scenario_name]()


def list_scenarios() -> Dict[str, str]:
    """List all available scenarios with descriptions."""
    return {
        name: scenario.description
        for name, scenario_func in SCENARIO_REGISTRY.items()
        for scenario in [scenario_func()]
    }


def create_custom_scenario(
    name: str,
    description: str,
    num_nodes: int = 5,
    rounds: int = 20,
    adversarial_config: Optional[Dict] = None,
    expected_guardians: Optional[List[str]] = None,
) -> SimulationScenario:
    """Create a custom scenario with specified parameters."""

    if adversarial_config is None:
        adversarial_config = {}

    if expected_guardians is None:
        expected_guardians = []

    return SimulationScenario(
        name=name,
        description=description,
        num_nodes=num_nodes,
        rounds=rounds,
        adversarial_nodes=adversarial_config.get("adversarial_nodes", []),
        adversarial_modes=adversarial_config.get("adversarial_modes", {}),
        expected_guardian_triggers=expected_guardians,
        expected_outcomes=adversarial_config.get("expected_outcomes", {}),
    )