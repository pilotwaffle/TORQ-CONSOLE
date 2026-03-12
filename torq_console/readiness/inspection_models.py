"""
TORQ Readiness Checker - Inspection and Query Models

Milestone 4: Data models for inspection, query, and audit layer.

Provides human-readable representations of readiness state,
transition history, and analytics data.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


# ============================================================================
# Inspection Models
# ============================================================================

class TransitionRecord(BaseModel):
    """
    A record of a readiness state transition.

    Provides human-readable representation of transition history.
    """
    # Identification
    id: UUID
    candidate_id: UUID

    # Transition details
    from_state: str
    to_state: str
    transition_type: str  # promotion, demotion, regression, forced, block, unblock

    # Trigger
    triggered_by: str  # system, user_id
    trigger_reason: str

    # Evaluation context
    evaluation_id: Optional[UUID] = None
    evaluation_score: Optional[float] = None
    evaluation_outcome: Optional[str] = None

    # Policy
    policy_profile_id: str
    policy_version: str

    # Governance
    forced: bool = False
    governance_override: bool = False
    approved_by: Optional[str] = None

    # Timing
    transitioned_at: datetime
    duration_ms: int = 0

    # State after transition
    state_locked: bool = False


class DimensionScoreView(BaseModel):
    """
    Human-readable view of a dimension score.
    """
    dimension: str
    score: float
    label: str  # e.g., "Excellent", "Good", "Fair", "Poor"
    weight: float
    contribution: float

    # Evidence
    sample_size: int = 0
    data_freshness: float = 1.0

    # Issues
    warnings: List[str] = Field(default_factory=list)
    hard_blocks: List[str] = Field(default_factory=list)


class EvidenceSummaryView(BaseModel):
    """
    Human-readable summary of collected evidence.
    """
    # Execution evidence
    execution_count: int = 0
    success_rate: float = 0.0
    avg_runtime_ms: float = 0.0

    # Artifact evidence
    artifact_count: int = 0
    artifact_completeness_rate: float = 0.0

    # Memory evidence
    governed_memory_count: int = 0
    memory_confidence_score: float = 0.0

    # Insight evidence
    approved_insight_count: int = 0
    insight_quality_score: float = 0.0

    # Pattern evidence
    validated_pattern_count: int = 0
    pattern_confidence_score: float = 0.0

    # Audit evidence
    audit_coverage_score: float = 0.0

    # Freshness
    last_execution_at: Optional[datetime] = None
    last_memory_validated_at: Optional[datetime] = None
    oldest_evidence_age_days: int = 0

    # Overall
    total_evidence_sources: int = 0
    evidence_freshness_score: float = 0.0


class GovernanceActionView(BaseModel):
    """
    Human-readable view of a governance action.
    """
    id: UUID
    action_type: str
    description: str

    # Actor
    requested_by: str
    reason: Optional[str] = None

    # Execution
    executed_at: Optional[datetime] = None
    success: bool = True
    error_message: Optional[str] = None

    # Result
    transition_event_id: Optional[UUID] = None


class ReadinessInspection(BaseModel):
    """
    Complete inspection view of a readiness candidate.

    Assembles all relevant information for human operators
    to understand the current readiness state.
    """
    # Identification
    candidate_id: UUID
    candidate_type: str
    candidate_key: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None

    # Current state
    current_state: str
    state_since: datetime
    time_in_state_days: float = 0.0

    # Readiness score
    current_score: float
    confidence: float
    score_label: str  # e.g., "Excellent", "Good", "Fair", "Poor"

    # Dimension breakdown
    dimension_scores: List[DimensionScoreView]

    # Evidence
    evidence_summary: EvidenceSummaryView

    # Governance status
    hard_blocks: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    regression_flags: List[str] = Field(default_factory=list)

    # Policy
    policy_profile: str
    policy_profile_name: str
    policy_version: str

    # Latest evaluation
    latest_evaluation_id: Optional[UUID] = None
    latest_evaluation_at: Optional[datetime] = None
    latest_evaluation_outcome: Optional[str] = None
    latest_evaluation_reason: Optional[str] = None

    # Transition history (most recent first)
    transition_history: List[TransitionRecord] = Field(default_factory=list)

    # Governance actions
    recent_governance_actions: List[GovernanceActionView] = Field(default_factory=list)

    # Metadata
    created_at: datetime
    updated_at: datetime
    last_assessed_at: Optional[datetime] = None

    # Owner
    owner: Optional[str] = None
    steward: Optional[str] = None


# ============================================================================
# Query Models
# ============================================================================

class CandidateListFilter(BaseModel):
    """
    Filter parameters for listing readiness candidates.
    """
    candidate_type: Optional[str] = None
    state: Optional[str] = None
    policy_profile: Optional[str] = None
    owner: Optional[str] = None

    # Score filtering
    min_score: Optional[float] = None
    max_score: Optional[float] = None

    # Time filtering
    created_after: Optional[datetime] = None
    updated_after: Optional[datetime] = None

    # Pagination
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)

    # Sorting
    sort_by: str = Field(default="updated_at")
    sort_order: str = Field(default="desc")


class CandidateListItem(BaseModel):
    """
    Summary view of a candidate for list views.
    """
    candidate_id: UUID
    candidate_type: str
    candidate_key: Optional[str] = None
    title: Optional[str] = None

    current_state: str
    state_since: datetime

    score: float
    confidence: float

    policy_profile: str

    # Governance status
    has_hard_blocks: bool = False
    is_regressed: bool = False

    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_assessed_at: Optional[datetime] = None


class CandidateListResult(BaseModel):
    """
    Result of a candidate list query.
    """
    candidates: List[CandidateListItem]
    total_count: int
    limit: int
    offset: int
    has_more: bool


# ============================================================================
# Analytics Models
# ============================================================================

class StateDistribution(BaseModel):
    """Distribution of candidates across readiness states."""
    state: str
    count: int
    percentage: float
    avg_score: float


class ReadinessMetrics(BaseModel):
    """Aggregated readiness metrics."""
    total_candidates: int = 0

    # State distribution
    state_distribution: List[StateDistribution] = Field(default_factory=list)

    # Promotion metrics
    promotion_rate: float = 0.0
    avg_promotion_time_days: float = 0.0

    # Regression metrics
    regression_rate: float = 0.0
    regressed_count: int = 0

    # Blocked metrics
    blocked_count: int = 0
    block_reasons: Dict[str, int] = Field(default_factory=dict)

    # Score distribution
    avg_score: float = 0.0
    median_score: float = 0.0
    min_score: float = 0.0
    max_score: float = 0.0

    # Compliance
    policy_compliance_rate: float = 0.0

    # Trends
    ready_trend: str = "stable"  # improving, stable, declining
    regression_trend: str = "stable"


class ReadinessTrend(BaseModel):
    """Readiness trend over time."""
    date: datetime
    ready_count: int
    blocked_count: int
    regressed_count: int
    avg_score: float


# ============================================================================
# Report Models
# ============================================================================

class ReadinessReportSection(BaseModel):
    """A section of a readiness report."""
    title: str
    content: str
    data: Optional[Dict[str, Any]] = None


class CandidateReadinessReport(BaseModel):
    """
    Detailed readiness report for a single candidate.
    """
    # Report metadata
    report_id: UUID
    candidate_id: UUID
    generated_at: datetime
    generated_by: str

    # Candidate info
    candidate_type: str
    candidate_key: Optional[str] = None
    title: Optional[str] = None

    # Current state
    current_state: str
    current_score: float

    # Report sections
    sections: List[ReadinessReportSection] = Field(default_factory=list)

    # Recommendations
    recommendations: List[str] = Field(default_factory=list)

    # Blocking issues
    blocking_issues: List[str] = Field(default_factory=list)

    # Next steps
    suggested_actions: List[str] = Field(default_factory=list)


class SystemReadinessReport(BaseModel):
    """
    System-wide readiness report.
    """
    # Report metadata
    report_id: UUID
    generated_at: datetime
    generated_by: str

    # Time period
    period_start: datetime
    period_end: datetime

    # Overall metrics
    total_candidates: int
    ready_count: int
    blocked_count: int
    regressed_count: int

    # Report sections
    executive_summary: str
    state_distribution: List[StateDistribution]
    blocking_issues: Dict[str, List[str]] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)

    # Detailed sections
    sections: List[ReadinessReportSection] = Field(default_factory=list)


# ============================================================================
# Helpers
# ============================================================================

def get_score_label(score: float) -> str:
    """Get human-readable label for a score."""
    if score >= 0.9:
        return "Excellent"
    elif score >= 0.75:
        return "Good"
    elif score >= 0.6:
        return "Fair"
    elif score >= 0.4:
        return "Marginal"
    else:
        return "Poor"


def get_dimension_label(dimension: str, score: float) -> str:
    """Get label for a specific dimension score."""
    # Dimensions have different thresholds
    high_thresholds = {
        "execution_stability": 0.85,
        "artifact_completeness": 0.90,
        "memory_confidence": 0.80,
        "insight_quality": 0.80,
        "pattern_confidence": 0.75,
        "audit_coverage": 0.85,
        "policy_compliance": 0.90,
        "operational_consistency": 0.85,
    }

    threshold = high_thresholds.get(dimension, 0.75)

    if score >= threshold + 0.1:
        return "Excellent"
    elif score >= threshold:
        return "Good"
    elif score >= threshold - 0.15:
        return "Fair"
    else:
        return "Needs Improvement"
