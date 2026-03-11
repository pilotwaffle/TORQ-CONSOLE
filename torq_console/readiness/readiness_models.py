"""
TORQ Readiness Checker - Object Model and Policy Schema

Milestone 1: Readiness object model + policy schema

Defines candidate types, readiness states, dimensions, scoring envelopes,
hard-block rules, and policy profiles.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


# ============================================================================
# Candidate Types
# ============================================================================

class CandidateType(str, Enum):
    """
    Types of objects that can be evaluated for readiness.

    Each candidate type represents a different operational capability
    that TORQ can govern through observation mode transitions.
    """
    # Mission-level readiness
    MISSION_TYPE = "mission_type"
    """A type of mission (e.g., planning, execution, review)"""

    # Agent routing
    AGENT_ROUTE = "agent_route"
    """An agent routing rule or classifier"""

    # Tools and integrations
    TOOL = "tool"
    """An external tool or integration"""

    # Workflows and automation
    WORKFLOW = "workflow"
    """A workflow or automation sequence"""

    # Pattern-backed recommendations
    PATTERN_RECOMMENDATION = "pattern_recommendation"
    """A pattern-backed operational recommendation"""

    # Operational capabilities
    OPERATIONAL_CAPABILITY = "operational_capability"
    """A broader operational capability composed of multiple components"""

    # System services
    SYSTEM_SERVICE = "system_service"
    """A TORQ system service (e.g., memory, insights, patterns)"""


class CandidateScope(str, Enum):
    """
    Scope of the readiness candidate.

    Defines how broadly the candidate applies.
    """
    GLOBAL = "global"
    """Applies to all TORQ operations"""

    DOMAIN = "domain"
    """Applies to a specific domain (e.g., financial, legal)"""

    WORKSPACE = "workspace"
    """Applies to a specific workspace"""

    MISSION = "mission"
    """Applies to a specific mission type"""

    SPECIFIC = "specific"
    """Applies to a specific instance"""


# ============================================================================
# Readiness States and Outcomes
# ============================================================================

class ReadinessState(str, Enum):
    """
    Current observation mode state of a candidate.

    These states represent the operational lifecycle of capabilities
    as they move from observation through testing to active use.
    """
    OBSERVED = "observed"
    """Data collection only, not yet evaluated or in early evaluation"""

    WATCHLIST = "watchlist"
    """Promising but not yet sufficient for active use"""

    READY = "ready"
    """Eligible for active use under defined policy"""

    BLOCKED = "blocked"
    """Not safe to activate due to hard blocks or policy violations"""

    REGRESSED = "regressed"
    """Previously ready but evidence now degraded"""


class ReadinessOutcome(str, Enum):
    """
    Outcome of a readiness evaluation.

    This is the immediate decision from an evaluation, which may
    trigger a state transition.
    """
    READY = "ready"
    """Candidate meets readiness threshold"""

    WATCHLIST = "watchlist"
    """Candidate is promising but below ready threshold"""

    OBSERVED = "observed"
    """Candidate needs more data or has insufficient evidence"""

    BLOCKED = "blocked"
    """Candidate has hard blocks that prevent activation"""

    REGRESSED = "regressed"
    """Candidate was previously ready but has degraded"""

    REEVALUATE = "reevaluate"
    """Candidate needs re-evaluation due to evidence changes"""


# ============================================================================
# Core Readiness Models
# ============================================================================

class ReadinessCandidate(BaseModel):
    """
    A candidate for readiness evaluation.

    Represents any operational capability that TORQ can govern
    through observation mode transitions.
    """
    # Identification
    id: UUID = Field(default_factory=uuid4)
    candidate_type: CandidateType
    candidate_key: str  # e.g., "mission_type:planning" or "tool:slack"

    # Scope
    scope: CandidateScope = CandidateScope.GLOBAL
    scope_key: Optional[str] = None  # e.g., domain name or workspace ID

    # Metadata
    title: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    # Owner and stewardship
    owner: Optional[str] = None  # Team or person responsible
    steward: Optional[str] = None  # Person responsible for readiness

    # Current state
    current_state: ReadinessState = ReadinessState.OBSERVED
    current_state_since: datetime = Field(default_factory=datetime.now)

    # Policy profile
    policy_profile_id: str = "default"

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    notes: List[str] = Field(default_factory=list)

    class Config:
        use_enum_values = False


class EvidenceSummary(BaseModel):
    """
    Summary of evidence collected for a candidate.

    Aggregates evidence from multiple sources:
    - Execution history (5.2)
    - Artifacts (5.3)
    - Memory (4H.1)
    - Insights (Insight Publishing)
    - Patterns (4G)
    - Audit logs
    """
    # Execution evidence
    execution_count: int = 0
    success_rate: float = 0.0
    failure_rate: float = 0.0
    avg_runtime_ms: float = 0.0
    runtime_variance: float = 0.0
    retry_rate: float = 0.0
    last_execution_at: Optional[datetime] = None

    # Artifact evidence
    artifact_count: int = 0
    artifact_completeness_rate: float = 0.0
    missing_artifact_count: int = 0
    traceability_coverage: float = 0.0

    # Memory evidence
    governed_memory_count: int = 0
    memory_confidence_score: float = 0.0
    stale_memory_ratio: float = 0.0
    last_memory_validated_at: Optional[datetime] = None

    # Insight evidence
    approved_insight_count: int = 0
    insight_suppression_rate: float = 0.0
    stale_insight_exposure: int = 0
    insight_quality_score: float = 0.0

    # Pattern evidence
    validated_pattern_count: int = 0
    pattern_confidence_score: float = 0.0
    pattern_source_diversity: float = 0.0
    active_pattern_count: int = 0

    # Audit evidence
    audit_coverage_score: float = 0.0
    audit_log_completeness: float = 0.0
    governance_events_last_30d: int = 0

    # Freshness
    oldest_evidence_age_days: int = 0
    evidence_freshness_score: float = 0.0

    # Overall
    total_evidence_sources: int = 0
    evidence_collection_date: datetime = Field(default_factory=datetime.now)


class ReadinessScore(BaseModel):
    """
    Computed readiness score across all dimensions.

    Provides a detailed breakdown of how the candidate scores
    across each readiness dimension.
    """
    # Overall score
    overall_score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)  # Confidence in the score

    # Dimension scores (0.0 - 1.0)
    execution_stability: float = Field(default=0.0, ge=0.0, le=1.0)
    artifact_completeness: float = Field(default=0.0, ge=0.0, le=1.0)
    memory_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    insight_quality: float = Field(default=0.0, ge=0.0, le=1.0)
    pattern_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    audit_coverage: float = Field(default=0.0, ge=0.0, le=1.0)
    policy_compliance: float = Field(default=0.0, ge=0.0, le=1.0)
    operational_consistency: float = Field(default=0.0, ge=0.0, le=1.0)

    # Hard blocks
    hard_blocks: List[str] = Field(default_factory=list)

    # Warnings
    warnings: List[str] = Field(default_factory=list)

    # Score breakdown
    dimension_weights: Dict[str, float] = Field(default_factory=dict)
    dimension_scores_raw: Dict[str, float] = Field(default_factory=dict)

    # Computed at
    computed_at: datetime = Field(default_factory=datetime.now)


class ReadinessEvaluation(BaseModel):
    """
    Complete readiness evaluation result.

    Contains the candidate, evidence summary, computed score,
    outcome decision, and full audit trail.
    """
    # Identification
    id: UUID = Field(default_factory=uuid4)
    candidate_id: UUID
    evaluation_type: str = "scheduled"  # scheduled, requested, triggered

    # Evidence and scoring
    evidence: EvidenceSummary
    score: ReadinessScore

    # Decision
    outcome: ReadinessOutcome
    recommended_state: ReadinessState
    reason: str

    # Policy
    policy_profile_id: str
    policy_version: str = "1.0"

    # Previous state for comparison
    previous_state: Optional[ReadinessState] = None
    previous_score: Optional[float] = None

    # Regression detection
    is_regression: bool = False
    regression_delta: Optional[float] = None  # Score decrease amount

    # Transition recommendation
    should_transition: bool = False
    transition_reason: Optional[str] = None

    # Audit
    evaluated_at: datetime = Field(default_factory=datetime.now)
    evaluated_by: Optional[str] = None  # System or user
    evaluation_duration_ms: int = 0

    # Links
    related_evaluations: List[UUID] = Field(default_factory=list)
    evidence_links: Dict[str, str] = Field(default_factory=dict)


# ============================================================================
# Policy Models
# ============================================================================

class PolicyDimension(str, Enum):
    """
    Standard readiness evaluation dimensions.

    Each dimension represents a different aspect of readiness
    that contributes to the overall decision.
    """
    EXECUTION_STABILITY = "execution_stability"
    ARTIFACT_COMPLETENESS = "artifact_completeness"
    MEMORY_CONFIDENCE = "memory_confidence"
    INSIGHT_QUALITY = "insight_quality"
    PATTERN_CONFIDENCE = "pattern_confidence"
    AUDIT_COVERAGE = "audit_coverage"
    POLICY_COMPLIANCE = "policy_compliance"
    OPERATIONAL_CONSISTENCY = "operational_consistency"


class HardBlockRule(BaseModel):
    """
    A hard block rule that prevents readiness.

    Hard blocks are conditions that must be satisfied for a candidate
    to be considered ready, regardless of score.
    """
    id: str = Field(default_factory=lambda: f"block_{uuid4().hex[:8]}")
    name: str
    description: str

    # Dimension to check
    dimension: PolicyDimension

    # Block condition
    threshold_min: Optional[float] = None  # Minimum value required
    threshold_max: Optional[float] = None  # Maximum value allowed
    required_value: Optional[str] = None  # Exact match required

    # Block severity
    severity: str = "block"  # block, warning

    # Check logic
    def is_blocked(self, value: float) -> bool:
        """Check if a value triggers this hard block."""
        if self.threshold_min is not None and value < self.threshold_min:
            return True
        if self.threshold_max is not None and value > self.threshold_max:
            return True
        return False


class ReadinessThresholds(BaseModel):
    """
    Threshold values for readiness decisions.

    Defines the score boundaries for different outcomes.
    """
    # Score thresholds (0.0 - 1.0)
    watchlist_min: float = Field(default=0.4, ge=0.0, le=1.0)
    ready_min: float = Field(default=0.7, ge=0.0, le=1.0)
    regression_delta: float = Field(default=0.15, ge=0.0, le=1.0)

    # Evidence requirements
    min_execution_count: int = Field(default=10, ge=1)
    min_artifact_count: int = Field(default=5, ge=0)
    min_memory_count: int = Field(default=3, ge=0)
    min_pattern_count: int = Field(default=1, ge=0)

    # Freshness requirements
    max_evidence_age_days: int = Field(default=30, ge=1)

    # Hard block override
    hard_blocks_override: bool = False  # If true, hard blocks can fail but still pass with caution

    class Config:
        use_enum_values = False


class PolicyProfile(BaseModel):
    """
    A policy profile for readiness evaluation.

    Defines how candidates are scored and what thresholds apply.
    """
    # Identification
    id: str
    name: str
    description: Optional[str] = None

    # Dimension weights (must sum to 1.0)
    weights: Dict[PolicyDimension, float] = Field(
        default_factory=lambda: {
            PolicyDimension.EXECUTION_STABILITY: 0.20,
            PolicyDimension.ARTIFACT_COMPLETENESS: 0.15,
            PolicyDimension.MEMORY_CONFIDENCE: 0.10,
            PolicyDimension.INSIGHT_QUALITY: 0.15,
            PolicyDimension.PATTERN_CONFIDENCE: 0.10,
            PolicyDimension.AUDIT_COVERAGE: 0.10,
            PolicyDimension.POLICY_COMPLIANCE: 0.10,
            PolicyDimension.OPERATIONAL_CONSISTENCY: 0.10,
        }
    )

    # Thresholds
    thresholds: ReadinessThresholds = Field(default_factory=ReadinessThresholds)

    # Hard block rules
    hard_blocks: List[HardBlockRule] = Field(default_factory=list)

    # Candidate type overrides (specific settings for certain candidate types)
    candidate_type_overrides: Dict[CandidateType, Dict[str, Any]] = Field(
        default_factory=dict
    )

    # Metadata
    is_default: bool = False
    version: str = "1.0"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def validate_weights(self) -> bool:
        """Check that weights sum to approximately 1.0."""
        total = sum(self.weights.values())
        return 0.95 <= total <= 1.05


# ============================================================================
# Transition Models
# ============================================================================

class TransitionEvent(BaseModel):
    """
    A record of a state transition.

    Tracks all readiness state changes for audit purposes.
    """
    id: UUID = Field(default_factory=uuid4)
    candidate_id: UUID

    # Transition details
    from_state: ReadinessState
    to_state: ReadinessState
    transition_type: str  # promotion, demotion, regression, reassessment

    # Trigger
    triggered_by: str  # system, user_id, policy_id
    trigger_reason: str

    # Evaluation that triggered this
    evaluation_id: UUID

    # Policy
    policy_profile_id: str
    policy_version: str

    # Audit
    transitioned_at: datetime = Field(default_factory=datetime.now)
    transition_duration_ms: int = 0

    # Previous state for rollback
    previous_state_locked: bool = False


class TransitionRequest(BaseModel):
    """
    Request to transition a candidate to a new state.
    """
    candidate_id: UUID
    target_state: ReadinessState
    requested_by: str
    reason: Optional[str] = None
    force: bool = False  # Bypass normal checks
    evaluation_id: Optional[UUID] = None  # Evaluation that supports this


class TransitionResult(BaseModel):
    """
    Result of a transition request.
    """
    success: bool
    candidate_id: UUID
    from_state: Optional[ReadinessState] = None
    to_state: Optional[ReadinessState] = None
    reason: Optional[str] = None
    transition_event_id: Optional[UUID] = None
    errors: List[str] = Field(default_factory=list)


# ============================================================================
# Default Policy Profiles
# ============================================================================

DEFAULT_READINESS_THRESHOLDS = ReadinessThresholds(
    watchlist_min=0.4,
    ready_min=0.7,
    regression_delta=0.15,
    min_execution_count=10,
    min_artifact_count=5,
    min_memory_count=3,
    min_pattern_count=1,
    max_evidence_age_days=30,
)

DEFAULT_POLICY_PROFILES: Dict[str, PolicyProfile] = {
    "default": PolicyProfile(
        id="default",
        name="Default Readiness Policy",
        description="Standard policy for evaluating most candidate types",
        is_default=True,
    ),
    "strict": PolicyProfile(
        id="strict",
        name="Strict Readiness Policy",
        description="Higher thresholds for mission-critical capabilities",
        thresholds=ReadinessThresholds(
            watchlist_min=0.5,
            ready_min=0.85,
            regression_delta=0.10,
            min_execution_count=50,
            min_artifact_count=20,
            min_memory_count=10,
            min_pattern_count=3,
            max_evidence_age_days=14,
        ),
    ),
    "permissive": PolicyProfile(
        id="permissive",
        name="Permissive Readiness Policy",
        description="Lower thresholds for experimental or internal tools",
        thresholds=ReadinessThresholds(
            watchlist_min=0.3,
            ready_min=0.6,
            regression_delta=0.20,
            min_execution_count=3,
            min_artifact_count=1,
            min_memory_count=1,
            min_pattern_count=0,
            max_evidence_age_days=60,
        ),
    ),
}


# ============================================================================
# Validation Helpers
# ============================================================================

def validate_candidate_type_transition(
    from_state: ReadinessState,
    to_state: ReadinessState,
    force: bool = False
) -> tuple[bool, Optional[str]]:
    """
    Validate that a state transition is allowed.

    Args:
        from_state: Current state
        to_state: Desired state
        force: If true, bypass validation

    Returns:
        Tuple of (is_allowed, error_message)
    """
    if force:
        return True, None

    # Define valid transitions
    valid_transitions = {
        ReadinessState.OBSERVED: [
            ReadinessState.WATCHLIST,
            ReadinessState.READY,
            ReadinessState.BLOCKED,
        ],
        ReadinessState.WATCHLIST: [
            ReadinessState.OBSERVED,
            ReadinessState.READY,
            ReadinessState.BLOCKED,
        ],
        ReadinessState.READY: [
            ReadinessState.REGRESSED,
            ReadinessState.BLOCKED,
        ],
        ReadinessState.BLOCKED: [
            ReadinessState.OBSERVED,
            ReadinessState.WATCHLIST,
        ],
        ReadinessState.REGRESSED: [
            ReadinessState.OBSERVED,
            ReadinessState.WATCHLIST,
            ReadinessState.BLOCKED,
        ],
    }

    allowed = valid_transitions.get(from_state, [])
    if to_state not in allowed:
        return False, f"Invalid transition from {from_state.value} to {to_state.value}"

    return True, None


def get_default_policy_profile(candidate_type: Optional[CandidateType] = None) -> PolicyProfile:
    """Get the default policy profile for a candidate type."""
    return DEFAULT_POLICY_PROFILES["default"]
