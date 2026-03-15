"""TORQ Layer 13 - Economic Intelligence Data Models

This module defines the core data structures for economic evaluation,
resource allocation, and opportunity cost calculations.
"""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, field_validator


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def datetime_utcnow() -> datetime:
    """Get current UTC datetime.

    This function exists for compatibility and testing purposes.
    """
    return datetime.utcnow()


# =============================================================================
# MISSION PROPOSAL MODELS
# =============================================================================


class MissionProposal(BaseModel):
    """Mission proposal submitted for economic evaluation.

    Input from Layer 8 (Mission Control) containing mission requirements
    and resource estimates from Layer 9 (Capability Registry).
    """

    # Identity
    mission_id: str
    mission_type: str
    description: str

    # Value metrics (Layer 2: Base Value input)
    user_value: float = Field(ge=0.0, le=1.0, description="User-provided importance score")
    urgency: float = Field(ge=0.0, le=1.0, description="Time sensitivity (decays over time)")
    strategic_fit: float = Field(
        ge=0.0, le=1.0, description="Alignment with strategic goals"
    )

    # Execution requirements (from Layer 9)
    required_capabilities: list[str] = Field(
        default_factory=list, description="Required capabilities from registry"
    )
    estimated_cost: float = Field(gt=0, description="Estimated cost in budget units")
    estimated_duration_seconds: int = Field(gt=0, description="Estimated execution time")

    # Constraints
    deadline: datetime | None = Field(None, description="Mission deadline, if any")
    prerequisites: list[str] = Field(
        default_factory=list, description="Mission IDs that must complete first"
    )

    # Federation (optional, from Layer 11/12)
    federation_result_id: str | None = Field(
        None, description="Federation validation result ID"
    )
    requires_validation: bool = Field(
        True, description="Whether federation validation is required"
    )

    @field_validator("required_capabilities")
    @classmethod
    def validate_capabilities(cls, v: list[str]) -> list[str]:
        """Ensure capabilities list is not None."""
        return v or []

    @field_validator("prerequisites")
    @classmethod
    def validate_prerequisites(cls, v: list[str]) -> list[str]:
        """Ensure prerequisites list is not None."""
        return v or []


class FederationResult(BaseModel):
    """Federation validation result from Layer 12.

    Used in Layer 3 (Execution Quality Modifier) to adjust scores
    based on multi-node validation confidence.
    """

    claim_id: str
    acceptance_rate: float = Field(ge=0.0, le=1.0, description="Fraction of nodes that accepted")
    confidence: float = Field(ge=0.0, le=1.0, description="Validation confidence score")
    participating_nodes: int = Field(ge=1, description="Number of nodes that participated")
    node_consensus: float = Field(
        ge=0.0, le=1.0, default=0.0, description="Agreement level among nodes"
    )

    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# RESOURCE CONSTRAINT MODELS
# =============================================================================


class ResourceConstraints(BaseModel):
    """Resource availability and budget constraints.

    Defines the limits within which economic allocation must operate.
    Used across all layers of the evaluation pipeline.
    """

    # Monetary budget
    total_budget: float = Field(gt=0, description="Total available budget")
    budget_remaining: float = Field(ge=0, description="Remaining budget for allocation")

    # Resource limits (from Layer 9 capability registry)
    max_compute_units: int | None = Field(None, description="Maximum compute units available")
    max_api_calls: int | None = Field(None, description="Maximum API calls allowed")
    max_execution_time_seconds: int | None = Field(None, description="Maximum execution time")

    # Time constraints
    allocation_deadline: datetime | None = Field(None, description="When allocation must complete")

    # Priority constraints
    require_federation_validation: bool = Field(
        True, description="Whether federation validation is required"
    )
    min_confidence_threshold: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Minimum confidence for acceptance"
    )

    # Strategic constraints
    required_mission_types: list[str] = Field(
        default_factory=list, description="Mission types that must be prioritized"
    )
    forbidden_mission_types: list[str] = Field(
        default_factory=list, description="Mission types that should be rejected"
    )

    @field_validator("budget_remaining")
    @classmethod
    def validate_budget_remaining(cls, v: float, info) -> float:
        """Ensure remaining budget doesn't exceed total."""
        if "total_budget" in info.data and v > info.data["total_budget"]:
            return info.data["total_budget"]
        return v


# =============================================================================
# ECONOMIC SCORE MODELS
# =============================================================================


class EconomicScore(BaseModel):
    """Result of economic evaluation through Layers 1-4.

    This model captures the complete evaluation result for a mission
    proposal after passing through the first four layers of the pipeline.
    """

    # Identity
    candidate_id: str
    mission_type: str

    # Layer 1: Feasibility Gate
    eligible: bool = Field(default=True, description="Whether the proposal passed feasibility checks")
    rejection_reason: str | None = Field(default=None, description="Reason for rejection, if any")

    # Layer 2: Base Value (intrinsic value independent of execution)
    base_value: float = Field(default=0.0, ge=0.0, le=1.0, description="Base value score")

    # Layer 3: Execution Quality Modifier
    execution_modifier: float = Field(default=1.0, ge=0.0, le=2.0, description="Quality adjustment multiplier")
    quality_adjusted_value: float = Field(default=0.0, ge=0.0, description="Value after quality adjustment")

    # Layer 4: Economic Efficiency (value per unit cost)
    efficiency: float = Field(default=0.0, ge=0.0, description="Value achieved per cost unit")

    # Layer 5: Portfolio Allocation (final scores)
    strategic_bonus: float = Field(default=0.0, ge=-0.5, le=0.5, description="Strategic adjustment")
    opportunity_cost_penalty: float = Field(default=0.0, ge=0.0, description="Penalty from opportunity cost")
    final_priority_score: float = Field(default=0.0, ge=0.0, description="Final priority for allocation")

    # Metadata
    evaluation_timestamp: datetime = Field(default_factory=datetime_utcnow)
    federation_validated: bool = Field(default=False, description="Whether federation validation occurred")
    federation_confidence: float | None = Field(None, description="Federation confidence if validated")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


# =============================================================================
# ALLOCATION RESULT MODELS
# =============================================================================


class OpportunityCostResult(BaseModel):
    """Opportunity cost analysis for a rejected mission.

    Quantifies the cost of not selecting a mission in favor of
    the chosen alternative(s).
    """

    rejected_mission_id: str
    rejected_mission_value: float

    best_accepted_alternative_id: str | None = Field(
        None, description="ID of closest accepted mission"
    )
    best_accepted_alternative_value: float = Field(
        0.0, description="Value of the best accepted alternative"
    )

    opportunity_cost: float = Field(
        ge=0.0, description="Value difference between rejected and best accepted"
    )

    # Normalized cost (relative to budget)
    opportunity_cost_ratio: float = Field(
        ge=0.0, description="Cost as ratio of total budget"
    )

    # Strategic impact assessment
    strategic_impact: Literal["low", "medium", "high"] = Field(
        "medium", description="Strategic impact of this rejection"
    )


class AllocationResult(BaseModel):
    """Result of budget allocation process (Layer 5).

    Output from ResourceAllocationEngine containing the final
    allocation decisions and associated metrics.
    """

    # Funded missions
    funded_mission_ids: list[str] = Field(default_factory=list, description="Mission IDs selected for funding")
    funded_total_cost: float = Field(default=0.0, ge=0.0, description="Total cost of funded missions")
    funded_total_value: float = Field(default=0.0, description="Total value of funded missions")

    # Queued missions (valid but not funded due to budget)
    queued_mission_ids: list[str] = Field(default_factory=list, description="Mission IDs queued for next budget")
    queued_total_cost: float = Field(default=0.0, ge=0.0, description="Total cost of queued missions")
    queued_total_value: float = Field(default=0.0, description="Total value of queued missions")

    # Rejected missions
    rejected_mission_ids: list[str] = Field(default_factory=list, description="Mission IDs rejected")
    rejected_reasons: dict[str, str] = Field(
        default_factory=dict, description="Rejection reason for each rejected mission"
    )

    # Budget status
    budget_utilization: float = Field(ge=0.0, le=1.0, description="Fraction of budget used")
    remaining_budget: float = Field(ge=0.0, description="Unallocated budget")

    # Opportunity costs
    opportunity_costs: dict[str, OpportunityCostResult] = Field(
        default_factory=dict, description="Opportunity cost for each rejection"
    )

    # Metrics
    allocation_efficiency: float = Field(ge=0.0, description="Total value achieved per dollar spent")
    regret_score: float = Field(ge=0.0, description="Value of best foregone alternative")

    # Timestamp
    allocation_timestamp: datetime = Field(default_factory=datetime_utcnow)


# =============================================================================
# EVALUATION CONTEXT MODELS
# =============================================================================


class EvaluationContext(BaseModel):
    """Context for economic evaluation.

    Provides additional context that may affect evaluation decisions
    beyond the immediate proposal and constraints.
    """

    current_time: datetime = Field(default_factory=datetime_utcnow)
    active_mission_count: int = Field(default=0, ge=0, description="Number of currently active missions")
    recent_success_rate: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Recent mission success rate"
    )
    resource_pressure: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Current resource utilization pressure"
    )

    # Historical data for learning
    historical_outcomes: dict[str, float] = Field(
        default_factory=dict, description="Historical value achieved by mission type"
    )


# =============================================================================
# CONFIGURATION MODELS
# =============================================================================


class EvaluationWeights(BaseModel):
    """Weights for economic evaluation scoring.

    Defines how different factors contribute to the final score.
    """

    # Layer 2: Base Value Weights
    user_value_weight: float = Field(default=0.6, ge=0.0, le=1.0)
    urgency_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    strategic_fit_weight: float = Field(default=0.1, ge=0.0, le=1.0)

    # Layer 3: Confidence Weights
    confidence_weight: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence_threshold: float = Field(default=0.3, ge=0.0, le=1.0)

    # Layer 4: Efficiency
    cost_epsilon: float = Field(default=0.01, gt=0.0, description="Small value to prevent division by zero")

    # Layer 5: Strategic Bonus
    strategic_bonus_cap: float = Field(default=0.5, ge=0.0, description="Maximum strategic bonus")
    opportunity_cost_threshold: float = Field(
        default=0.1, ge=0.0, description="Minimum cost ratio to record opportunity cost"
    )

    @field_validator("user_value_weight", "urgency_weight", "strategic_fit_weight")
    @classmethod
    def validate_weights_sum(cls, v: float, info) -> float:
        """Ensure weights are reasonable (will be normalized during evaluation)."""
        return v


class EconomicConfiguration(BaseModel):
    """Complete configuration for economic evaluation.

    Combines weights and other configuration parameters for the
    economic intelligence system.
    """

    weights: EvaluationWeights = Field(default_factory=EvaluationWeights)

    # Feasibility gate thresholds
    min_confidence_for_eligibility: float = Field(default=0.3, ge=0.0, le=1.0)
    allow_risky_proposals: bool = Field(default=True, description="Allow low-confidence proposals")

    # Allocation parameters
    allocation_algorithm: Literal["greedy", "knapsack", "hybrid"] = Field(
        default="greedy", description="Algorithm to use for allocation"
    )
    allow_partial_funding: bool = Field(default=False, description="Allow partial mission funding")

    # Logging and monitoring
    enable_evaluation_logging: bool = Field(default=False)
    log_all_scores: bool = Field(default=False)


# =============================================================================
# ALL EXPORTS
# =============================================================================

__all__ = [
    # Mission Proposal Models
    "MissionProposal",
    "FederationResult",
    # Resource Constraint Models
    "ResourceConstraints",
    # Economic Score Models
    "EconomicScore",
    "datetime_utcnow",
    # Allocation Result Models
    "OpportunityCostResult",
    "AllocationResult",
    # Evaluation Context Models
    "EvaluationContext",
    # Configuration Models
    "EvaluationWeights",
    "EconomicConfiguration",
]
