"""
Core economic models for Layer 13.

These models define the data structures for economic evaluation, resource
allocation, and opportunity cost analysis. All models store intermediate
scoring values for explainability.
"""

from dataclasses import dataclass, field
from datetime import timedelta
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Enums
# =============================================================================

class ResourceType(str, Enum):
    """Types of resources that can be allocated."""
    COMPUTE = "compute"  # CPU/GPU cycles
    API = "api"  # API call budget
    TOKEN = "token"  # LLM token budget
    TIME = "time"  # Wall-clock time
    ATTENTION = "attention"  # Human-in-loop required
    FINANCIAL = "financial"  # Monetary budget


class AllocationStrategy(str, Enum):
    """Resource allocation strategies."""
    GREEDY = "greedy"  # Pick highest net-benefit first
    OPTIMAL = "optimal"  # Solve knapsack for optimal bundle
    SATISFICE = "satisfice"  # Good enough, fast selection


class RecommendationReason(str, Enum):
    """Reasons for action recommendations."""
    INSUFFICIENT_BUDGET = "insufficient_budget"
    LOW_CONFIDENCE = "low_confidence"
    HIGH_RISK = "high_risk"
    DEPENDENCIES_MISSING = "dependencies_missing"
    POLICY_VIOLATION = "policy_violation"
    NEGATIVE_NET_VALUE = "negative_net_value"
    OPPORTUNITY_COST_TOO_HIGH = "opportunity_cost_too_high"
    STRATEGIC_MISALIGNMENT = "strategic_misalignment"


# =============================================================================
# Stage 1: Feasibility & Input Models
# =============================================================================

@dataclass
class ResourceCost:
    """
    Multi-dimensional resource cost for an action.

    Layer 13 handles multiple constraint dimensions, not just financial cost.
    """
    compute_budget: float = 0.0  # in compute units
    api_call_budget: int = 0  # number of API calls
    token_budget: int = 0  # number of LLM tokens
    time_budget: timedelta = field(default_factory=lambda: timedelta(0))
    human_attention_required: bool = False
    financial_cost: float = 0.0  # monetary cost if applicable


@dataclass
class ResourceConstraint:
    """
    Available resource limits for economic evaluation.
    """
    max_compute: float = float('inf')
    max_api_calls: int = 1000
    max_tokens: int = 100000
    max_time: timedelta = field(default_factory=lambda: timedelta(hours=1))
    max_financial: float = 1000.0
    resource_type: ResourceType = ResourceType.COMPUTE


class ActionCandidate(BaseModel):
    """
    Potential action for economic evaluation.

    This model represents a candidate action that will be evaluated through
    the staged scoring pipeline. All 10 fields are required for proper evaluation.

    Attributes:
        id: Unique identifier for this action
        description: Human-readable description
        domain: Which layer/domain this action comes from
        estimated_value: Intrinsic value if successful (0-1 normalized or raw)
        estimated_cost: Resource cost dimensions
        confidence: Probability of success (0-1), from Layer 10
        risk: Probability of negative outcome (0-1)
        urgency: Time pressure (0-1), higher = more urgent
        time_to_realization: How long until value is realized
        dependencies: List of action IDs that must complete first
        strategic_alignment: Alignment with long-term goals (0-1)
        reversibility: Can this action be undone? (0-1, higher = more reversible)
        resource_type: Which budget pool to draw from
    """

    # Identity
    id: str
    description: str
    domain: str

    # Economic Dimensions
    estimated_value: float = Field(ge=0, description="Intrinsic value if successful")
    estimated_cost: ResourceCost

    # Uncertainty Dimensions
    confidence: float = Field(ge=0, le=1, description="Probability of success (Layer 10)")
    risk: float = Field(ge=0, le=1, description="Probability of negative outcome")

    # Timing Dimensions
    urgency: float = Field(ge=0, le=1, default=0.5, description="Time pressure")
    time_to_realization: float = Field(ge=0, default=1.0, description="Time until value (normalized)")

    # Structural Dimensions
    dependencies: List[str] = Field(default_factory=list, description="Required prerequisite action IDs")

    # Strategic Dimensions
    strategic_alignment: float = Field(ge=0, le=1, default=0.5, description="Alignment with goals")
    reversibility: float = Field(ge=0, le=1, default=0.5, description="Can be undone?")

    # Resource Specification
    resource_type: ResourceType = Field(default=ResourceType.COMPUTE)

    @field_validator('estimated_cost', mode='before')
    @classmethod
    def parse_cost(cls, v: Any) -> ResourceCost:
        """Parse ResourceCost from dict or existing instance."""
        if isinstance(v, ResourceCost):
            return v
        if isinstance(v, dict):
            return ResourceCost(**v)
        if isinstance(v, (int, float)):
            # Simple cost becomes compute budget
            return ResourceCost(compute_budget=float(v))
        return ResourceCost()


class FeasibilityResult(BaseModel):
    """
    Result of Stage 1 feasibility gate.

    The feasibility gate filters candidates before scoring to prevent
    bad options from contaminating the ranking.
    """
    eligible: bool
    rejection_reason: Optional[RecommendationReason] = None
    rejection_detail: Optional[str] = None

    # Detailed checks
    policy_allowed: bool = True
    dependencies_satisfied: bool = True
    confidence_above_floor: bool = True
    risk_below_ceiling: bool = True
    resource_minimums_met: bool = True


class EconomicContext(BaseModel):
    """
    Context for economic evaluation.

    Contains budget constraints, risk tolerance, and configuration
    for the scoring pipeline.
    """
    # Resource constraints
    budget: ResourceConstraint = Field(default_factory=ResourceConstraint)

    # Risk and confidence thresholds
    risk_tolerance: float = Field(ge=0, le=1, default=0.5, description="Acceptable risk level")
    confidence_floor: float = Field(ge=0, le=1, default=0.3, description="Minimum confidence to proceed")
    risk_ceiling: float = Field(ge=0, le=1, default=0.8, description="Maximum allowed risk")

    # Time horizon
    time_horizon: timedelta = Field(default_factory=lambda: timedelta(hours=1))

    # Weights for scoring (can be configured)
    value_weight: float = 0.5
    urgency_weight: float = 0.25
    speed_weight: float = 0.25
    confidence_weight: float = 0.6
    simplicity_weight: float = 0.2
    risk_penalty_weight: float = 0.2
    qav_weight: float = 0.55  # Quality-adjusted value in final
    efficiency_weight: float = 0.25  # Efficiency in final
    strategy_weight: float = 0.20  # Strategic alignment in final
    opp_cost_weight: float = 0.15  # Opportunity cost penalty

    # Policy constraints
    allowed_domains: List[str] = Field(default_factory=list)
    blocked_domains: List[str] = Field(default_factory=list)


# =============================================================================
# Stage 2-4: Scoring Models
# =============================================================================

class EconomicScore(BaseModel):
    """
    Complete economic evaluation of an action candidate.

    CRITICAL: Stores ALL intermediate values for explainability.
    Does NOT collapse to a single final score.

    Stages:
    1. Feasibility: eligible, rejection_reason
    2. Base Value: base_value, normalized_value, urgency_score, time_score
    3. Execution Modifier: execution_modifier, confidence, risk, dependency
    4. Combined: quality_adjusted_value
    5. Efficiency: efficiency, cost
    6. Portfolio: strategic_bonus, opportunity_cost_penalty
    7. Final: final_priority_score, recommendation
    """

    # Identity
    candidate_id: str

    # ---------- Stage 1: Feasibility Gate ----------
    eligible: bool = True
    rejection_reason: Optional[RecommendationReason] = None

    # ---------- Stage 2: Base Value (intrinsic upside, no cost) ----------
    base_value: float = 0.0
    normalized_value: float = 0.0  # Value normalized against candidate set
    urgency_score: float = 0.0
    time_realization_score: float = 0.0

    # ---------- Stage 3: Execution Quality Modifier ----------
    execution_modifier: float = 1.0  # Applied to base_value (0.1 - 1.25)
    confidence_factor: float = 0.5  # From candidate.confidence
    risk_penalty: float = 0.0  # Derived from candidate.risk
    dependency_simplicity: float = 1.0  # 1/(1 + len(dependencies))

    # ---------- Stage 3 Combined ----------
    quality_adjusted_value: float = 0.0  # base_value * execution_modifier

    # ---------- Stage 4: Economic Efficiency ----------
    efficiency: float = 0.0  # qav / cost
    total_cost: float = 0.0  # Normalized total resource cost

    # ---------- Stage 5: Portfolio Considerations ----------
    strategic_bonus: float = 0.0  # From strategic_alignment or dependency unlocks
    opportunity_cost_penalty: float = 0.0  # Value of sacrificed alternatives
    dependency_unlock_bonus: float = 0.0  # Bonus for enabling other actions

    # ---------- Final Score ----------
    final_priority_score: float = 0.0
    recommendation: Literal["execute", "defer", "reject"] = "defer"

    # ---------- Explainability ----------
    rationale: str = ""
    score_breakdown: Dict[str, float] = Field(default_factory=dict)

    @field_validator('recommendation', mode='before')
    @classmethod
    def validate_recommendation(cls, v: Any) -> Literal["execute", "defer", "reject"]:
        """Ensure recommendation is valid."""
        if v not in ("execute", "defer", "reject"):
            return "defer"
        return v


class ScoringConfig(BaseModel):
    """Configuration for the scoring pipeline."""

    # Feasibility gate settings
    enable_feasibility_gate: bool = True
    require_dependencies_satisfied: bool = True
    require_confidence_above_floor: bool = True
    require_risk_below_ceiling: bool = True

    # Scoring weights (can override EconomicContext)
    value_weight: float = 0.5
    urgency_weight: float = 0.25
    speed_weight: float = 0.25
    confidence_weight: float = 0.6
    simplicity_weight: float = 0.2
    risk_penalty_weight: float = 0.2

    # Final score weights
    qav_weight: float = 0.55
    efficiency_weight: float = 0.25
    strategy_weight: float = 0.20
    opp_cost_weight: float = 0.15

    # Thresholds
    execute_threshold: float = 0.6  # Above this = execute
    reject_threshold: float = 0.3  # Below this = reject
    cost_floor: float = 1.0  # Minimum cost for efficiency calc


# =============================================================================
# Stage 5: Allocation Models
# =============================================================================

class OpportunityCostAnalysis(BaseModel):
    """
    Analysis of opportunity costs for a chosen action.

    Answers: "What value do we sacrifice by choosing this action?"
    """

    chosen_action_id: str

    # Best alternatives that were excluded
    excluded_alternatives: List[str] = Field(default_factory=list)

    # Value sacrificed
    total_excluded_value: float = 0.0
    total_excluded_efficiency: float = 0.0

    # Regret metrics
    opportunity_cost: float = 0.0  # Value of best excluded - value of chosen
    regret_score: float = 0.0  # Normalized regret (0-1)

    # Budget consideration
    remaining_budget_after_choice: float = 0.0
    could_fit_alternatives: bool = True


class AllocatedAction(BaseModel):
    """
    A single action included in the allocation plan.
    """

    action_id: str
    allocated_budget: float  # Actual resources allocated
    expected_value: float  # Risk-adjusted expected value
    priority_rank: int  # Rank in the allocation order
    score: Optional[EconomicScore] = None  # Full scoring details


class AllocationPlan(BaseModel):
    """
    Resource allocation across a set of actions.

    This is the OUTPUT of Layer 13 - the optimal bundle of actions
    given budget constraints, NOT just a sorted list.
    """

    # Plan metadata
    plan_id: str
    total_budget: float
    allocated_budget: float
    remaining_budget: float

    # Allocated actions (the bundle)
    allocated_actions: List[AllocatedAction] = Field(default_factory=list)

    # Metrics
    expected_total_value: float = 0.0
    expected_regret: float = 0.0  # Value of best excluded actions
    allocation_efficiency: float = 0.0  # Computed as allocated_budget / total_budget

    # Deferred and rejected
    deferred_actions: List[str] = Field(default_factory=list)  # Positive value but budget constrained
    rejected_actions: List[str] = Field(default_factory=list)  # Negative or failed feasibility

    # Strategy used
    strategy: AllocationStrategy = AllocationStrategy.GREEDY

    # Explainability
    rationale: str = ""
    allocation_trace: List[str] = Field(default_factory=list)


# =============================================================================
# Integration Models (Layers 8-12 consumption)
# =============================================================================

class Layer8MetaControlSignal(BaseModel):
    """Input from Layer 8 (Meta-Control)."""
    action_candidates: List[str]
    control_signal: Dict[str, Any] = Field(default_factory=dict)


class Layer9PolicyConstraint(BaseModel):
    """Input from Layer 9 (Execution Policies)."""
    allowed_actions: List[str] = Field(default_factory=list)
    blocked_actions: List[str] = Field(default_factory=list)
    resource_limits: Dict[str, float] = Field(default_factory=dict)


class Layer10PlanningGraph(BaseModel):
    """Input from Layer 10 (Planning/Verification)."""
    confidence_scores: Dict[str, float] = Field(default_factory=dict)
    verification_status: Dict[str, str] = Field(default_factory=dict)


class Layer11ExecutionOutcome(BaseModel):
    """Input from Layer 11 (Learning)."""
    success_probabilities: Dict[str, float] = Field(default_factory=dict)
    learned_preferences: Dict[str, float] = Field(default_factory=dict)


class Layer12FederatedInsight(BaseModel):
    """Input from Layer 12 (Federation)."""
    consensus_scores: Dict[str, float] = Field(default_factory=dict)
    network_wide_agreement: Dict[str, bool] = Field(default_factory=dict)


class IntegrationInputs(BaseModel):
    """
    Combined inputs from Layers 8-12 for Layer 13 integration.
    """

    layer8: Optional[Layer8MetaControlSignal] = None
    layer9: Optional[Layer9PolicyConstraint] = None
    layer10: Optional[Layer10PlanningGraph] = None
    layer11: Optional[Layer11ExecutionOutcome] = None
    layer12: Optional[Layer12FederatedInsight] = None

    def get_merged_constraints(self) -> ResourceConstraint:
        """Merge constraints from all layers."""
        constraints = ResourceConstraint()

        if self.layer9:
            # Apply Layer 9 resource limits
            if "compute" in self.layer9.resource_limits:
                constraints.max_compute = self.layer9.resource_limits["compute"]
            if "financial" in self.layer9.resource_limits:
                constraints.max_financial = self.layer9.resource_limits["financial"]

        return constraints

    def get_merged_confidence(self) -> Dict[str, float]:
        """Merge confidence scores from Layer 10 and Layer 11."""
        confidence = {}

        if self.layer10:
            confidence.update(self.layer10.confidence_scores)

        if self.layer11:
            # Layer 11 success probabilities can inform confidence
            for action_id, prob in self.layer11.success_probabilities.items():
                # Average Layer 10 confidence with Layer 11 success probability
                layer10_conf = confidence.get(action_id, 0.5)
                confidence[action_id] = (layer10_conf + prob) / 2

        return confidence
