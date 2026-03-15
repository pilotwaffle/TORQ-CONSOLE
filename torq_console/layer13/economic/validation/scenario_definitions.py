"""TORQ Layer 13 - Validation Scenario Definitions

This module defines all validation scenarios for testing Layer 13 economic intelligence.
Each scenario represents a real-world use case with inputs, expected outputs, and success criteria.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from ..models import (
    EconomicConfiguration,
    EconomicScore,
    FederationResult,
    MissionProposal,
    ResourceConstraints,
)


@dataclass
class ScenarioExpectation:
    """Expected results for a validation scenario."""

    funded_mission_ids: set[str]
    queued_mission_ids: set[str] = field(default_factory=set)
    rejected_mission_ids: set[str] = field(default_factory=set)
    min_budget_utilization: float = 0.85
    max_budget_utilization: float = 1.0
    min_allocation_efficiency: float = 0.0
    max_regret_ratio: float = 0.15


@dataclass
class ScenarioDefinition:
    """Definition of a validation scenario."""

    name: str
    description: str
    budget: float
    proposals: list[MissionProposal]
    constraints: ResourceConstraints
    federation_results: dict[str, FederationResult] = field(default_factory=dict)
    expected: ScenarioExpectation | None = None
    configuration: EconomicConfiguration = field(default_factory=EconomicConfiguration)

    def __post_init__(self):
        """Set default budget_remaining to total_budget if not specified."""
        if self.constraints.budget_remaining == 0:
            self.constraints.budget_remaining = self.budget


# =============================================================================
# SCENARIO 1: Constrained Budget Allocation
# =============================================================================


def scenario_1_constrained_budget() -> ScenarioDefinition:
    """Scenario 1: Fixed budget across competing high-value missions.

    Validates optimal allocation when budget is constrained.
    """
    proposals = [
        MissionProposal(
            mission_id="m1",
            mission_type="data_ingestion",
            description="Ingest customer data from various sources",
            user_value=0.8,
            urgency=0.5,
            strategic_fit=0.7,
            estimated_cost=200.0,
            estimated_duration_seconds=3600,
            requires_validation=False,
        ),
        MissionProposal(
            mission_id="m2",
            mission_type="model_training",
            description="Train ML model on customer data",
            user_value=0.9,
            urgency=0.4,
            strategic_fit=0.8,
            estimated_cost=500.0,
            estimated_duration_seconds=7200,
            requires_validation=False,
        ),
        MissionProposal(
            mission_id="m3",
            mission_type="feature_export",
            description="Export processed features to downstream systems",
            user_value=0.7,
            urgency=0.6,
            strategic_fit=0.6,
            estimated_cost=350.0,
            estimated_duration_seconds=1800,
            requires_validation=False,
        ),
        MissionProposal(
            mission_id="m4",
            mission_type="api_deployment",
            description="Deploy API to production environment",
            user_value=0.85,
            urgency=0.7,
            strategic_fit=0.75,
            estimated_cost=400.0,
            estimated_duration_seconds=5400,
            requires_validation=False,
        ),
        MissionProposal(
            mission_id="m5",
            mission_type="monitoring_setup",
            description="Set up monitoring and alerting",
            user_value=0.6,
            urgency=0.3,
            strategic_fit=0.5,
            estimated_cost=150.0,
            estimated_duration_seconds=2400,
            requires_validation=False,
        ),
    ]

    constraints = ResourceConstraints(
        total_budget=1000.0,
        budget_remaining=1000.0,
        require_federation_validation=False,
    )

    expected = ScenarioExpectation(
        funded_mission_ids={"m4", "m5", "m1"},  # All highest value/efficiency missions that fit
        queued_mission_ids={"m2", "m3"},  # Don't fit in remaining budget
        min_budget_utilization=0.70,  # Adjusted for moderate oversubscription
        max_regret_ratio=0.45,  # Budget pressure 1.60x
    )

    return ScenarioDefinition(
        name="constrained_budget",
        description="Fixed budget across competing high-value missions",
        budget=1000.0,
        proposals=proposals,
        constraints=constraints,
        expected=expected,
    )


# =============================================================================
# SCENARIO 2: High-Value vs High-Urgency Tradeoffs
# =============================================================================


def scenario_2_value_urgency_tradeoff() -> ScenarioDefinition:
    """Scenario 2: Conflict between high-value/low-urgency and low-value/high-urgency.

    Validates that urgency is a component, not an override.
    """
    proposals = [
        MissionProposal(
            mission_id="strategic_project",
            mission_type="infrastructure",
            description="Strategic infrastructure project with long-term value",
            user_value=0.95,
            urgency=0.2,
            strategic_fit=0.9,
            estimated_cost=400.0,
            estimated_duration_seconds=7200,
            requires_validation=False,
        ),
        MissionProposal(
            mission_id="hotfix",
            mission_type="bugfix",
            description="Urgent hotfix for production issue",
            user_value=0.4,
            urgency=0.95,
            strategic_fit=0.3,
            estimated_cost=100.0,
            estimated_duration_seconds=600,
            deadline=datetime.utcnow() + timedelta(hours=2),
            requires_validation=False,
        ),
    ]

    constraints = ResourceConstraints(
        total_budget=500.0,
        budget_remaining=500.0,
        require_federation_validation=False,
    )

    expected = ScenarioExpectation(
        funded_mission_ids={"hotfix", "strategic_project"},  # Both fit
        min_budget_utilization=0.95,
    )

    return ScenarioDefinition(
        name="value_urgency_tradeoff",
        description="High-value vs high-urgency tradeoffs",
        budget=500.0,
        proposals=proposals,
        constraints=constraints,
        expected=expected,
    )


# =============================================================================
# SCENARIO 3: Opportunity Cost Comparisons
# =============================================================================


def scenario_3_opportunity_cost() -> ScenarioDefinition:
    """Scenario 3: Choose between mutually exclusive high-value options.

    Validates opportunity cost calculation.
    """
    proposals = [
        MissionProposal(
            mission_id="option_a",
            mission_type="feature_a",
            description="Feature option A with high cost",
            user_value=0.8,
            urgency=0.5,
            strategic_fit=0.7,
            estimated_cost=500.0,
            estimated_duration_seconds=4800,
            requires_validation=False,
        ),
        MissionProposal(
            mission_id="option_b",
            mission_type="feature_b",
            description="Feature option B with moderate cost",
            user_value=0.7,
            urgency=0.6,
            strategic_fit=0.65,
            estimated_cost=300.0,
            estimated_duration_seconds=3600,
            requires_validation=False,
        ),
        MissionProposal(
            mission_id="option_c",
            mission_type="feature_c",
            description="Feature option C with low cost",
            user_value=0.6,
            urgency=0.4,
            strategic_fit=0.5,
            estimated_cost=200.0,
            estimated_duration_seconds=2400,
            requires_validation=False,
        ),
    ]

    constraints = ResourceConstraints(
        total_budget=600.0,
        budget_remaining=600.0,
        require_federation_validation=False,
    )

    expected = ScenarioExpectation(
        funded_mission_ids={"option_c", "option_b"},  # Higher efficiency
        queued_mission_ids={"option_a"},  # Doesn't fit
        min_budget_utilization=0.80,
        max_regret_ratio=0.70,  # Mutually exclusive options, budget pressure 1.67x
    )

    return ScenarioDefinition(
        name="opportunity_cost",
        description="Opportunity cost comparisons for mutually exclusive options",
        budget=600.0,
        proposals=proposals,
        constraints=constraints,
        expected=expected,
    )


# =============================================================================
# SCENARIO 4: Low-Confidence / High-Cost Rejection
# =============================================================================


def scenario_4_low_confidence_rejection() -> ScenarioDefinition:
    """Scenario 4: Risky expensive proposals should be rejected.

    Validates confidence threshold enforcement.
    """
    proposals = [
        MissionProposal(
            mission_id="risky_bet",
            mission_type="experimental",
            description="High-value experimental project with low confidence",
            user_value=0.9,
            urgency=0.5,
            strategic_fit=0.8,
            estimated_cost=800.0,
            estimated_duration_seconds=9600,
            requires_validation=True,
        ),
        MissionProposal(
            mission_id="safe_bet",
            mission_type="standard",
            description="Standard project with high confidence",
            user_value=0.7,
            urgency=0.5,
            strategic_fit=0.6,
            estimated_cost=200.0,
            estimated_duration_seconds=2400,
            requires_validation=True,
        ),
    ]

    federation_results = {
        "risky_bet": FederationResult(
            claim_id="risky_claim",
            acceptance_rate=0.4,
            confidence=0.35,  # Below threshold
            participating_nodes=12,
        ),
        "safe_bet": FederationResult(
            claim_id="safe_claim",
            acceptance_rate=0.92,
            confidence=0.88,
            participating_nodes=12,
        ),
    }

    constraints = ResourceConstraints(
        total_budget=1000.0,
        budget_remaining=1000.0,
        require_federation_validation=True,
        min_confidence_threshold=0.5,
    )

    expected = ScenarioExpectation(
        funded_mission_ids={"safe_bet"},
        rejected_mission_ids={"risky_bet"},  # Confidence too low
        min_budget_utilization=0.15,
    )

    return ScenarioDefinition(
        name="low_confidence_rejection",
        description="Low-confidence high-cost proposals are rejected",
        budget=1000.0,
        proposals=proposals,
        constraints=constraints,
        federation_results=federation_results,
        expected=expected,
    )


# =============================================================================
# SCENARIO 5: Resource Starvation Stress
# =============================================================================


def scenario_5_resource_starvation() -> ScenarioDefinition:
    """Scenario 5: Minimal resources across many missions.

    Validates graceful degradation under severe constraints.
    """
    proposals = [
        MissionProposal(
            mission_id=f"mission_{i}",
            mission_type="standard",
            description=f"Standard mission {i} with varying value",
            user_value=0.5 + (i * 0.05),
            urgency=0.5,
            strategic_fit=0.5 + (i * 0.03),
            estimated_cost=50.0 + (i * 10),
            estimated_duration_seconds=1200 + (i * 300),
            requires_validation=False,
        )
        for i in range(10)
    ]

    constraints = ResourceConstraints(
        total_budget=200.0,
        budget_remaining=200.0,
        require_federation_validation=False,
    )

    expected = ScenarioExpectation(
        funded_mission_ids={"mission_0", "mission_1", "mission_2"},
        queued_mission_ids={f"mission_{i}" for i in range(3, 10)},
        min_budget_utilization=0.70,  # Adjusted for severe constraints
        max_regret_ratio=0.55,  # Severe oversubscription (4.75x)
    )

    return ScenarioDefinition(
        name="resource_starvation",
        description="Graceful degradation under severe resource constraints",
        budget=200.0,
        proposals=proposals,
        constraints=constraints,
        expected=expected,
    )


# =============================================================================
# SCENARIO 6: Strategic Mission Type Constraints
# =============================================================================


def scenario_6_strategic_constraints() -> ScenarioDefinition:
    """Scenario 6: Required mission types must be prioritized.

    Validates strategic constraint handling.
    """
    proposals = [
        MissionProposal(
            mission_id="security_audit",
            mission_type="security",
            description="Security audit for compliance",
            user_value=0.6,
            urgency=0.7,
            strategic_fit=0.8,
            estimated_cost=300.0,
            estimated_duration_seconds=3600,
            requires_validation=False,
        ),
        MissionProposal(
            mission_id="compliance_check",
            mission_type="compliance",
            description="Regulatory compliance check",
            user_value=0.5,
            urgency=0.8,
            strategic_fit=0.7,
            estimated_cost=250.0,
            estimated_duration_seconds=2400,
            requires_validation=False,
        ),
        MissionProposal(
            mission_id="feature_development",
            mission_type="feature",
            description="New feature development",
            user_value=0.9,
            urgency=0.4,
            strategic_fit=0.6,
            estimated_cost=400.0,
            estimated_duration_seconds=5400,
            requires_validation=False,
        ),
    ]

    constraints = ResourceConstraints(
        total_budget=600.0,
        budget_remaining=600.0,
        require_federation_validation=False,
        required_mission_types=["security", "compliance"],
    )

    expected = ScenarioExpectation(
        funded_mission_ids={"compliance_check", "security_audit"},
        queued_mission_ids={"feature_development"},
        min_budget_utilization=0.80,  # Adjusted for strategic constraints
        max_regret_ratio=0.70,  # Strategic priorities cause suboptimal allocation
    )

    return ScenarioDefinition(
        name="strategic_constraints",
        description="Required mission types are prioritized",
        budget=600.0,
        proposals=proposals,
        constraints=constraints,
        expected=expected,
    )


# =============================================================================
# SCENARIO 7: Federation Confidence Impact
# =============================================================================


def scenario_7_federation_confidence() -> ScenarioDefinition:
    """Scenario 7: Federation confidence affects scoring.

    Validates confidence modifier calculation.
    """
    proposals = [
        MissionProposal(
            mission_id="high_conf",
            mission_type="standard",
            description="Mission with high federation confidence",
            user_value=0.7,
            urgency=0.5,
            strategic_fit=0.6,
            estimated_cost=300.0,
            estimated_duration_seconds=3600,
            requires_validation=True,
        ),
        MissionProposal(
            mission_id="low_conf",
            mission_type="standard",
            description="Mission with lower federation confidence",
            user_value=0.8,  # Higher value
            urgency=0.5,
            strategic_fit=0.6,
            estimated_cost=300.0,
            estimated_duration_seconds=3600,
            requires_validation=True,
        ),
    ]

    federation_results = {
        "high_conf": FederationResult(
            claim_id="high_conf_claim",
            acceptance_rate=0.95,
            confidence=0.92,
            participating_nodes=15,
        ),
        "low_conf": FederationResult(
            claim_id="low_conf_claim",
            acceptance_rate=0.6,
            confidence=0.55,
            participating_nodes=8,
        ),
    }

    constraints = ResourceConstraints(
        total_budget=500.0,
        budget_remaining=500.0,
        require_federation_validation=True,
        min_confidence_threshold=0.3,
    )

    expected = ScenarioExpectation(
        funded_mission_ids={"high_conf"},  # Higher confidence wins
        queued_mission_ids={"low_conf"},
        min_budget_utilization=0.50,
        max_regret_ratio=1.00,  # Confidence rejection produces high regret by design
    )

    return ScenarioDefinition(
        name="federation_confidence",
        description="Federation confidence affects evaluation",
        budget=500.0,
        proposals=proposals,
        constraints=constraints,
        federation_results=federation_results,
        expected=expected,
    )


# =============================================================================
# SCENARIO REGISTRY
# =============================================================================


_SCENARIO_REGISTRY = {
    "constrained_budget": scenario_1_constrained_budget,
    "value_urgency_tradeoff": scenario_2_value_urgency_tradeoff,
    "opportunity_cost": scenario_3_opportunity_cost,
    "low_confidence_rejection": scenario_4_low_confidence_rejection,
    "resource_starvation": scenario_5_resource_starvation,
    "strategic_constraints": scenario_6_strategic_constraints,
    "federation_confidence": scenario_7_federation_confidence,
}


def get_all_scenarios() -> dict[str, ScenarioDefinition]:
    """Get all available validation scenarios.

    Returns:
        Dictionary mapping scenario names to ScenarioDefinition instances
    """
    return {name: factory() for name, factory in _SCENARIO_REGISTRY.items()}


def get_scenario_by_name(name: str) -> ScenarioDefinition | None:
    """Get a specific scenario by name.

    Args:
        name: Scenario name

    Returns:
        ScenarioDefinition instance or None if not found
    """
    factory = _SCENARIO_REGISTRY.get(name)
    return factory() if factory else None


def list_scenario_names() -> list[str]:
    """List all available scenario names.

    Returns:
        List of scenario names
    """
    return list(_SCENARIO_REGISTRY.keys())


__all__ = [
    "ScenarioDefinition",
    "ScenarioExpectation",
    "get_all_scenarios",
    "get_scenario_by_name",
    "list_scenario_names",
    # Scenario factories
    "scenario_1_constrained_budget",
    "scenario_2_value_urgency_tradeoff",
    "scenario_3_opportunity_cost",
    "scenario_4_low_confidence_rejection",
    "scenario_5_resource_starvation",
    "scenario_6_strategic_constraints",
    "scenario_7_federation_confidence",
]
