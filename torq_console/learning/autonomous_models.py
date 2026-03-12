"""
TORQ Layer 8: Autonomous Intelligence & Continuous Learning Models

L8-M1: Data models for closed-loop self-improving AI governance.

This module defines the data structures for:
- Outcome evaluation from mission execution
- Pattern validation and prediction accuracy
- Insight evolution through supersession
- System recommendation generation
- Learning analytics and trends
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


# ============================================================================
# Outcome Analysis Models
# ============================================================================

class OutcomeCategory(str, Enum):
    """Categories of mission outcomes."""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    ERROR = "error"
    CANCELLED = "cancelled"


class PerformanceMetrics(BaseModel):
    """Performance metrics for a mission execution."""
    duration_seconds: float = Field(default=0.0)
    cpu_usage_percent: float = Field(default=0.0)
    memory_usage_mb: float = Field(default=0.0)
    token_count: int = Field(default=0)
    tool_calls: int = Field(default=0)
    error_count: int = Field(default=0)
    retry_count: int = Field(default=0)

    # Quality metrics
    output_quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    user_satisfaction_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    # Efficiency metrics
    tasks_completed: int = Field(default=0)
    tasks_per_minute: float = Field(default=0.0)
    average_response_time_ms: float = Field(default=0.0)

    class Config:
        use_enum_values = True


class ImprovementCandidate(BaseModel):
    """A potential improvement identified from outcome analysis."""
    category: str  # "routing", "tool_usage", "workflow", "resource_allocation"
    description: str
    current_impact: float  # Estimated impact of fixing (0-1)
    confidence: float  # Confidence in this improvement (0-1)
    suggested_action: str

    # Evidence
    supporting_missions: List[str] = Field(default_factory=list)
    expected_improvement: Optional[str] = None

    class Config:
        use_enum_values = True


class OutcomeEvaluation(BaseModel):
    """
    Evaluation of a mission execution outcome.

    Measures success, performance, and improvement opportunities.
    """
    evaluation_id: UUID = Field(default_factory=uuid4)
    mission_id: str
    execution_id: str

    # Outcome classification
    predicted_outcome: str
    actual_outcome: str
    outcome_category: OutcomeCategory

    # Success and performance
    success_score: float = Field(default=0.0, ge=0.0, le=1.0)
    performance_metrics: PerformanceMetrics = Field(default_factory=PerformanceMetrics)

    # Analysis
    predicted_vs_actual_match: bool = False
    prediction_accuracy: float = Field(default=0.0, ge=0.0, le=1.0)

    # Improvement signals
    detected_patterns: List[str] = Field(default_factory=list)
    improvement_candidates: List[ImprovementCandidate] = Field(default_factory=list)

    # Timing
    evaluated_at: datetime = Field(default_factory=datetime.now)
    mission_completed_at: datetime = Field(default_factory=datetime.now)

    # Context
    agent_id: Optional[str] = None
    workflow_id: Optional[str] = None

    class Config:
        use_enum_values = True


# ============================================================================
# Pattern Validation Models
# ============================================================================

class PatternValidationStatus(str, Enum):
    """Status of pattern validation."""
    VALIDATED = "validated"
    STRENGTHENED = "strengthened"
    WEAKENED = "weakened"
    SUPERSEDED = "superseded"
    DISPROVEN = "disproven"
    PENDING = "pending"


class PatternAccuracyMetrics(BaseModel):
    """Metrics tracking pattern prediction accuracy."""
    total_predictions: int = 0
    correct_predictions: int = 0
    false_positives: int = 0
    false_negatives: int = 0

    # Derived metrics
    accuracy: float = Field(default=0.0, ge=0.0, le=1.0)
    precision: float = Field(default=0.0, ge=0.0, le=1.0)
    recall: float = Field(default=0.0, ge=0.0, le=1.0)
    f1_score: float = Field(default=0.0, ge=0.0, le=1.0)

    def calculate_derived_metrics(self):
        """Calculate accuracy, precision, recall, F1."""
        if self.total_predictions > 0:
            self.accuracy = self.correct_predictions / self.total_predictions

        if self.correct_predictions + self.false_positives > 0:
            self.precision = self.correct_predictions / (
                self.correct_predictions + self.false_positives
            )

        if self.correct_predictions + self.false_negatives > 0:
            self.recall = self.correct_predictions / (
                self.correct_predictions + self.false_negatives
            )

        if self.precision + self.recall > 0:
            self.f1_score = 2 * (self.precision * self.recall) / (self.precision + self.recall)


class PatternDriftDetection(BaseModel):
    """Detection of pattern drift over time."""
    pattern_id: str

    # Drift metrics
    current_accuracy: float
    baseline_accuracy: float
    drift_magnitude: float  # Absolute difference

    # Trend
    accuracy_trend: str  # "improving", "stable", "declining"
    trend_confidence: float

    # Detection
    drift_detected: bool = False
    drift_severity: str = "none"  # "none", "low", "medium", "high"

    # Recommendation
    recommendation: Optional[str] = None

    class Config:
        use_enum_values = True


class PatternValidation(BaseModel):
    """
    Validation result for a predictive pattern.

    Tracks whether patterns accurately predict outcomes.
    """
    validation_id: UUID = Field(default_factory=uuid4)
    pattern_id: str

    # Validation results
    validation_status: PatternValidationStatus
    accuracy_metrics: PatternAccuracyMetrics = Field(default_factory=PatternAccuracyMetrics)

    # Confidence tracking
    original_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    current_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_adjustment: float = Field(default=0.0)

    # Drift detection
    drift_detection: Optional[PatternDriftDetection] = None

    # Evidence
    supporting_outcomes: List[str] = Field(default_factory=list)
    contradicting_outcomes: List[str] = Field(default_factory=list)

    # Timing
    validated_at: datetime = Field(default_factory=datetime.now)
    next_review_at: Optional[datetime] = None

    class Config:
        use_enum_values = True


# ============================================================================
# Insight Evolution Models
# ============================================================================

class InsightLifecycleStage(str, Enum):
    """Stages of insight lifecycle."""
    PUBLISHED = "published"
    VALIDATED = "validated"
    REINFORCED = "reinforced"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"
    REJECTED = "rejected"


class InsightLineage(BaseModel):
    """Lineage tracking for insight evolution."""
    insight_id: str
    parent_insight_id: Optional[str] = None
    child_insight_ids: List[str] = Field(default_factory=list)

    # Evolution tracking
    evolution_count: int = 0
    creation_source: str = "unknown"

    # Related insights
    merged_from: List[str] = Field(default_factory=list)
    split_into: List[str] = Field(default_factory=list)

    class Config:
        use_enum_values = True


class InsightSupersession(BaseModel):
    """Record of an insight being superseded by a better version."""
    supersession_id: UUID = Field(default_factory=uuid4)
    old_insight_id: str
    new_insight_id: str

    # Reason for supersession
    supersession_reason: str
    improvement_description: str

    # Comparison
    old_confidence: float
    new_confidence: float
    confidence_gain: float

    # Validation
    validated_by: Optional[str] = None
    validation_evidence: List[str] = Field(default_factory=list)

    # Timing
    superseded_at: datetime = Field(default_factory=datetime.now)

    class Config:
        use_enum_values = True


class InsightEvolution(BaseModel):
    """
    Evolution record for an insight.

    Tracks how insights change and improve over time.
    """
    evolution_id: UUID = Field(default_factory=uuid4)
    insight_id: str

    # Lifecycle
    current_stage: InsightLifecycleStage
    lineage: InsightLineage

    # Confidence tracking
    initial_confidence: float = Field(default=0.0)
    current_confidence: float = Field(default=0.0)
    confidence_history: List[float] = Field(default_factory=list)

    # Validation
    validation_count: int = 0
    reinforcement_count: int = 0
    contradiction_count: int = 0

    # Supersession
    superseded_by: Optional[str] = None
    superseded_at: Optional[datetime] = None

    # Timeline
    created_at: datetime = Field(default_factory=datetime.now)
    last_validated_at: Optional[datetime] = None
    last_evolved_at: Optional[datetime] = None

    class Config:
        use_enum_values = True


# ============================================================================
# Recommendation Models
# ============================================================================

class RecommendationType(str, Enum):
    """Types of system recommendations."""
    AGENT_ROUTING = "agent_routing"
    MISSION_WORKFLOW = "mission_workflow"
    TOOL_USAGE = "tool_usage"
    RESOURCE_ALLOCATION = "resource_allocation"
    NEW_CAPABILITY = "new_capability"
    PATTERN_DEPLOYMENT = "pattern_deployment"
    INSIGHT_UPDATE = "insight_update"
    READINESS_ADJUSTMENT = "readiness_adjustment"


class RecommendationPriority(str, Enum):
    """Priority levels for recommendations."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RecommendationSource(str, Enum):
    """Source of the recommendation."""
    OUTCOME_ANALYSIS = "outcome_analysis"
    PATTERN_VALIDATION = "pattern_validation"
    INSIGHT_EVOLUTION = "insight_evolution"
    LEARNING_FEEDBACK = "learning_feedback"
    ANOMALY_DETECTION = "anomaly_detection"


class RecommendationStatus(str, Enum):
    """Status of a recommendation."""
    PENDING = "pending"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"
    SUPERSEDED = "superseded"


class SystemRecommendation(BaseModel):
    """
    A system improvement recommendation.

    Generated from learning signals and validated as readiness candidates.
    """
    recommendation_id: UUID = Field(default_factory=uuid4)

    # Classification
    recommendation_type: RecommendationType
    priority: RecommendationPriority
    source: RecommendationSource

    # Content
    title: str
    description: str
    proposed_action: str

    # Evidence
    supporting_patterns: List[str] = Field(default_factory=list)
    supporting_outcomes: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    # Expected impact
    expected_improvement: Optional[str] = None
    estimated_effort: Optional[str] = None

    # Readiness integration
    readiness_candidate_id: Optional[str] = None
    readiness_candidate_state: Optional[str] = None

    # Status tracking
    status: RecommendationStatus = RecommendationStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    reviewed_at: Optional[datetime] = None
    implemented_at: Optional[datetime] = None

    # Implementation
    implemented_by: Optional[str] = None
    implementation_notes: Optional[str] = None

    class Config:
        use_enum_values = True


# ============================================================================
# Learning Analytics Models
# ============================================================================

class LearningTrend(str, Enum):
    """Trend directions for learning metrics."""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    UNKNOWN = "unknown"


class LearningMetrics(BaseModel):
    """
    Aggregated learning metrics across the system.
    """
    metrics_id: UUID = Field(default_factory=uuid4)
    captured_at: datetime = Field(default_factory=datetime.now)

    # Outcome metrics
    total_evaluations: int = 0
    success_rate: float = 0.0
    average_success_score: float = 0.0

    # Pattern metrics
    patterns_validated: int = 0
    pattern_accuracy_avg: float = 0.0
    high_confidence_patterns: int = 0

    # Insight metrics
    insights_evolved: int = 0
    insights_superseded: int = 0
    avg_insight_confidence: float = 0.0

    # Recommendation metrics
    recommendations_generated: int = 0
    recommendations_implemented: int = 0
    implementation_rate: float = 0.0

    # Feedback loop health
    feedback_loop_active: bool = False
    avg_feedback_duration_hours: float = 0.0

    class Config:
        use_enum_values = True


class SystemEvolutionSnapshot(BaseModel):
    """
    Snapshot of system evolution at a point in time.
    """
    snapshot_id: UUID = Field(default_factory=uuid4)
    captured_at: datetime = Field(default_factory=datetime.now)

    # System state
    total_missions_executed: int = 0
    total_patterns_discovered: int = 0
    total_insights_published: int = 0
    total_recommendations_generated: int = 0

    # Quality metrics
    system_health_score: float = 0.0
    learning_velocity: float = 0.0  # Rate of improvement per week

    # Trends
    success_rate_trend: LearningTrend = LearningTrend.STABLE
    pattern_accuracy_trend: LearningTrend = LearningTrend.STABLE
    insight_confidence_trend: LearningTrend = LearningTrend.STABLE

    # Notable events
    recent_improvements: List[str] = Field(default_factory=list)
    emerging_patterns: List[str] = Field(default_factory=list)
    critical_recommendations: List[str] = Field(default_factory=list)

    class Config:
        use_enum_values = True


# ============================================================================
# Factory Functions
# ============================================================================

def create_outcome_evaluation(
    mission_id: str,
    execution_id: str,
    predicted_outcome: str,
    actual_outcome: str,
    success_score: float,
    **kwargs
) -> OutcomeEvaluation:
    """Create an outcome evaluation with default values."""
    return OutcomeEvaluation(
        mission_id=mission_id,
        execution_id=execution_id,
        predicted_outcome=predicted_outcome,
        actual_outcome=actual_outcome,
        success_score=success_score,
        predicted_vs_actual_match=(predicted_outcome == actual_outcome),
        **kwargs
    )


def create_pattern_validation(
    pattern_id: str,
    validation_status: PatternValidationStatus,
    **kwargs
) -> PatternValidation:
    """Create a pattern validation with default values."""
    return PatternValidation(
        pattern_id=pattern_id,
        validation_status=validation_status,
        **kwargs
    )


def create_system_recommendation(
    recommendation_type: RecommendationType,
    title: str,
    description: str,
    proposed_action: str,
    **kwargs
) -> SystemRecommendation:
    """Create a system recommendation with default values."""
    return SystemRecommendation(
        recommendation_type=recommendation_type,
        title=title,
        description=description,
        proposed_action=proposed_action,
        **kwargs
    )


def get_default_recommendation_types() -> List[RecommendationType]:
    """Get list of all recommendation types."""
    return list(RecommendationType)


def get_default_outcome_categories() -> List[OutcomeCategory]:
    """Get list of all outcome categories."""
    return list(OutcomeCategory)
