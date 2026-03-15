"""TORQ Layer 15 - Core Data Models

This module defines the core data structures for strategic foresight,
scenario projection, and long-term consequence analysis.
"""

from datetime import datetime
from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def datetime_utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.utcnow()


# =============================================================================
# L14 INTEGRATION HOOK
# =============================================================================


class DecisionPacket(BaseModel):
    """Integration hook from Layer 14 to Layer 15.

    This is the canonical input format for Layer 15 strategic foresight.
    It combines the outputs from Layer 13 (economics) and Layer 14 (legitimacy).
    """

    # Identity
    decision_id: str = Field(description="Unique decision identifier")
    mission_id: str | None = Field(default=None, description="Associated mission ID")

    # Layer 13: Economic Intelligence Output
    economic_result: dict = Field(
        default_factory=dict,
        description="Economic evaluation result from Layer 13",
    )
    economic_priority_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Priority score from Layer 13"
    )
    estimated_cost: float = Field(default=0.0, gt=0, description="Estimated cost")
    budget_remaining: float = Field(default=0.0, ge=0.0, description="Remaining budget")

    # Layer 14: Constitutional Legitimacy Output
    legitimacy_result: dict = Field(
        default_factory=dict,
        description="Legitimacy evaluation result from Layer 14",
    )
    legitimacy_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Legitimacy score from Layer 14"
    )
    execution_authorized: bool = Field(
        default=False, description="Whether execution is authorized by Layer 14"
    )

    # Decision Context
    action_type: str = Field(description="Type of action")
    action_description: str = Field(description="Description of the action")
    proposing_agent_id: str = Field(description="Agent proposing the action")
    target_resources: list[str] = Field(
        default_factory=list, description="Resources this action will use"
    )

    # Strategic Context
    mission_horizon: Literal["short", "medium", "long"] = Field(
        default="medium", description="Time horizon for impact assessment"
    )
    is_governance_change: bool = Field(
        default=False, description="Whether this changes governance"
    )
    is_budget_change: bool = Field(
        default=False, description="Whether this changes budget allocation"
    )

    # Foresight Candidate Flag
    foresight_candidate: bool = Field(
        default=True, description="Whether this decision should undergo foresight analysis"
    )

    # Timestamp
    created_at: datetime = Field(default_factory=datetime_utcnow)

    @property
    def foresight_required(self) -> bool:
        """Check if foresight analysis is required."""
        if not self.foresight_candidate:
            return False
        if not self.execution_authorized:
            return False  # Not authorized, no need for foresight
        if self.estimated_cost > 500:
            return True  # High-cost decisions always require foresight
        if self.is_governance_change:
            return True  # Governance changes require foresight
        return False


# =============================================================================
# STRATEGIC FORESIGHT MODELS
# =============================================================================


class ScenarioProjection(BaseModel):
    """A projected future scenario.

    Represents one plausible future trajectory resulting from
    a decision, with associated outcomes and confidence.
    """

    scenario_id: str = Field(description="Unique scenario identifier")
    decision_id: str = Field(description="Associated decision ID")
    horizon: Literal["short", "medium", "long"] = Field(
        description="Time horizon for this projection"
    )

    # Scenario Definition
    assumptions: list[str] = Field(
        default_factory=list, description="Key assumptions for this scenario"
    )
    projected_outcomes: dict[str, float] = Field(
        default_factory=dict,
        description="Projected outcome metrics (e.g., efficiency, resilience)",
    )

    # Confidence
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence in projection")

    # Narrative
    notes: list[str] = Field(default_factory=list, description="Additional notes")
    created_at: datetime = Field(default_factory=datetime_utcnow)


class BranchComparison(BaseModel):
    """Comparison between strategic branches.

    Compares different strategic paths by expected value, resilience,
    risk profile, and time horizon.
    """

    compared_paths: list[str] = Field(description="IDs of paths being compared")
    decision_id: str = Field(description="Associated decision ID")

    # Value Comparison
    expected_value_by_horizon: dict[str, dict[str, float]] = Field(
        default_factory=dict,
        description="Expected value for each path at each horizon",
    )

    # Risk Profile
    risk_profile: dict[str, float] = Field(
        default_factory=dict,
        description="Risk score for each path (0=low risk, 1=high risk)",
    )

    # Resilience
    resilience_score: dict[str, float] = Field(
        default_factory=dict,
        description="Resilience score for each path (0=fragile, 1=resilient)",
    )

    # Recommendation
    recommended_path: str | None = Field(
        default=None, description="ID of recommended path"
    )

    created_at: datetime = Field(default_factory=datetime_utcnow)


class ConsequenceAnalysis(BaseModel):
    """Analysis of second-order consequences.

    Evaluates downstream effects of a decision beyond immediate outcomes.
    """

    decision_id: str = Field(description="Associated decision ID")

    # Direct Effects (First-Order)
    direct_effects: dict[str, float] = Field(
        default_factory=dict,
        description="Immediate, direct effects of the decision",
    )

    # Second-Order Effects
    second_order_effects: dict[str, float] = Field(
        default_factory=dict,
        description="Downstream, indirect effects",
    )

    # Systemic Risks
    systemic_risks: dict[str, float] = Field(
        default_factory=dict,
        description="Risks to system-level properties (e.g., fragility, centralization)",
    )

    # Delayed Benefits
    delayed_benefits: dict[str, float] = Field(
        default_factory=dict,
        description="Benefits that manifest over time",
    )

    # Net Assessment
    net_second_order_score: float = Field(
        default=0.0, ge=-1.0, le=1.0,
        description="Net second-order effect score (-1=harmful, +1=beneficial)",
    )

    created_at: datetime = Field(default_factory=datetime_utcnow)


class OptionalityAssessment(BaseModel):
    """Assessment of decision optionality and reversibility.

    Evaluates how much a decision preserves or limits future options.
    """

    decision_id: str = Field(description="Associated decision ID")

    # Optionality Score
    optionality_score: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Optionality score (0=locks in future, 1=preserves options)",
    )

    # Lock-In Risk
    lock_in_risk: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Risk of path dependency (0=flexible, 1=locked in)",
    )

    # Reversibility
    reversible: bool = Field(default=True, description="Whether decision is reversible")

    # Mitigation Options
    mitigation_options: list[str] = Field(
        default_factory=list,
        description="Options to mitigate lock-in risk",
    )

    # Path Narrowing
    path_narrowing_score: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="How much this narrows future path options",
    )

    created_at: datetime = Field(default_factory=datetime_utcnow)


class HorizonAlignmentResult(BaseModel):
    """Assessment of alignment across time horizons.

    Scores whether a decision helps or harms short, medium, and
    long-term mission objectives.
    """

    decision_id: str = Field(description="Associated decision ID")

    # Horizon Scores
    short_term_score: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Alignment with short-term objectives (0-3 months)",
    )
    medium_term_score: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Alignment with medium-term objectives (3-12 months)",
    )
    long_term_score: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Alignment with long-term objectives (12+ months)",
    )

    # Delta
    alignment_delta: float = Field(
        default=0.0,
        description="Variance across horizons (lower = more consistent)",
    )

    # Overall
    aligned: bool = Field(default=False, description="Whether well-aligned across horizons")

    created_at: datetime = Field(default_factory=datetime_utcnow)


class StrategicForesightResult(BaseModel):
    """Complete strategic foresight evaluation result.

    Combines all Layer 15 engine outputs into a single result
    for decision recommendation.
    """

    decision_id: str = Field(description="Associated decision ID")

    # Component Results
    scenario_projections: list[ScenarioProjection] = Field(
        default_factory=list, description="Projected future scenarios"
    )
    branch_comparison: BranchComparison | None = Field(
        default=None, description="Branch comparison analysis"
    )
    consequence_analysis: ConsequenceAnalysis | None = Field(
        default=None, description="Second-order consequence analysis"
    )
    optionality_assessment: OptionalityAssessment | None = Field(
        default=None, description="Optionality assessment"
    )
    horizon_alignment: HorizonAlignmentResult | None = Field(
        default=None, description="Horizon alignment analysis"
    )

    # Strategic Score
    strategic_score: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Overall strategic score (0-1)",
    )

    # Recommendation
    recommendation: Literal["approve", "condition", "reject", "defer"] = Field(
        default="defer", description="Strategic recommendation"
    )
    recommendation_reason: str = Field(
        default="", description="Explanation for recommendation"
    )

    # Warnings
    warnings: list[str] = Field(default_factory=list, description="Strategic warnings")

    # Metadata
    evaluated_at: datetime = Field(default_factory=datetime_utcnow)
    requires_deep_foresight: bool = Field(
        default=False, description="Whether deeper analysis is recommended"
    )


# =============================================================================
# SCORING POLICY
# =============================================================================


class StrategicWeights(BaseModel):
    """Weights for strategic scoring.

    Defines how different factors contribute to the overall
    strategic score.
    """

    long_term_value_weight: float = Field(default=0.30, ge=0.0, le=1.0)
    resilience_score_weight: float = Field(default=0.25, ge=0.0, le=1.0)
    optionality_score_weight: float = Field(default=0.20, ge=0.0, le=1.0)
    horizon_alignment_weight: float = Field(default=0.15, ge=0.0, le=1.0)
    lock_in_risk_penalty: float = Field(default=0.10, ge=0.0, le=1.0)


# =============================================================================
# ALL EXPORTS
# =============================================================================

__all__ = [
    # Integration Hook
    "DecisionPacket",
    # Foresight Models
    "ScenarioProjection",
    "BranchComparison",
    "ConsequenceAnalysis",
    "OptionalityAssessment",
    "HorizonAlignmentResult",
    "StrategicForesightResult",
    # Scoring
    "StrategicWeights",
    # Utility
    "datetime_utcnow",
]
