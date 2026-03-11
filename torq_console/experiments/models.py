"""
Behavior Version & Experiment Models

Defines the data structures for versioned behavior experiments.
Implements the proposal → experiment → assignment → impact measurement flow.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


# ============================================================================
# Behavior Version Models
# ============================================================================

class BehaviorAssetType(str, Enum):
    """Types of behavior assets that can be versioned."""
    AGENT_PROMPT = "agent_prompt"
    AGENT_SYSTEM_INSTRUCTIONS = "agent_system_instructions"
    ROUTING_PROFILE = "routing_profile"
    TOOL_PREFERENCES = "tool_preferences"
    SYNTHESIS_PROMPT = "synthesis_prompt"
    EVALUATION_PROFILE = "evaluation_profile"


class BehaviorVersionStatus(str, Enum):
    """Lifecycle status of a behavior version."""
    DRAFT = "draft"
    ACTIVE = "active"  # Currently in production
    CANDIDATE = "candidate"  # Being tested in an experiment
    ARCHIVED = "archived"
    ROLLED_BACK = "rolled_back"


class BehaviorVersionCreate(BaseModel):
    """Create a new behavior version."""
    asset_type: BehaviorAssetType
    asset_key: str = Field(..., description="Identifier like 'planner', 'financial_analysis_router'")
    version: str = Field(..., description="Version identifier like 'v1', 'v2', '2026-03-07-a'")
    content: Dict[str, Any] = Field(..., description="Actual behavior configuration")
    created_from_proposal_id: Optional[str] = None
    parent_version_id: Optional[str] = None


class BehaviorVersionRead(BaseModel):
    """A behavior version read from the database."""
    id: str
    asset_type: BehaviorAssetType
    asset_key: str
    version: str
    content: Dict[str, Any]
    created_from_proposal_id: Optional[str]
    parent_version_id: Optional[str]
    status: BehaviorVersionStatus
    created_at: datetime


# ============================================================================
# Experiment Models
# ============================================================================

class ExperimentStatus(str, Enum):
    """Lifecycle status of an experiment."""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    PROMOTED = "promoted"
    ROLLED_BACK = "rolled_back"


class AssignmentMode(str, Enum):
    """How traffic is assigned between control and candidate."""
    PERCENTAGE_HASH = "percentage_hash"  # Deterministic hash-based percentage
    WORKFLOW_TYPE = "workflow_type"  # Assignment by workflow type
    TENANT_SCOPE = "tenant_scope"  # Assignment by tenant/environment


class AssignmentConfig(BaseModel):
    """Configuration for traffic assignment."""
    mode: AssignmentMode
    candidate_percent: int = Field(default=20, ge=0, le=100, description="Percent of traffic to candidate")
    workflow_types: Optional[List[str]] = Field(None, description="For workflow_type mode")
    tenants: Optional[List[str]] = Field(None, description="For tenant_scope mode")
    hash_seed: Optional[str] = Field(None, description="Optional seed for hash determination")


class GuardrailMetric(BaseModel):
    """A guardrail metric that must not regress."""
    metric: str
    min_delta: Optional[float] = Field(None, description="Minimum acceptable change (can be negative)")
    max_delta: Optional[float] = Field(None, description="Maximum acceptable change")


class PromotionRule(BaseModel):
    """Rules for promoting a candidate to production."""
    primary_metric_min_improvement: float = Field(default=0.05, description="Minimum improvement threshold")
    minimum_sample_size: int = Field(default=30, ge=1, description="Minimum executions per variant")
    confidence_threshold: float = Field(default=0.90, ge=0.0, le=1.0, description="Statistical confidence required")


class SuccessMetrics(BaseModel):
    """Success metrics for an experiment."""
    primary_metric: str = Field(..., description="Main metric to evaluate")
    guardrails: List[GuardrailMetric] = Field(default_factory=list)
    promotion_rule: PromotionRule = Field(default_factory=PromotionRule)
    secondary_metrics: List[str] = Field(default_factory=list, description="Additional metrics to track")


class ExperimentVariant(BaseModel):
    """A variant in an experiment (control or candidate)."""
    variant_name: Literal["control", "candidate"]
    behavior_version_id: str
    rollout_percent: Optional[int] = None


class BehaviorExperimentCreate(BaseModel):
    """Create a new behavior experiment."""
    proposal_id: str = Field(..., description="Source adaptation proposal")
    asset_type: BehaviorAssetType
    asset_key: str
    control_version_id: str
    candidate_version_id: str
    hypothesis: str = Field(..., description="What change is expected and why")
    assignment_config: AssignmentConfig
    success_metrics: SuccessMetrics
    minimum_sample_size: int = Field(default=30, ge=1)


class BehaviorExperimentRead(BaseModel):
    """An experiment read from the database."""
    id: str
    proposal_id: str
    asset_type: BehaviorAssetType
    asset_key: str
    control_version_id: str
    candidate_version_id: str
    hypothesis: str
    assignment_config: AssignmentConfig
    success_metrics: SuccessMetrics
    minimum_sample_size: int
    status: ExperimentStatus
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    promoted_at: Optional[datetime]
    rolled_back_at: Optional[datetime]


# ============================================================================
# Assignment Models
# ============================================================================

class ExperimentAssignment(BaseModel):
    """Record of which variant an execution received."""
    id: str
    experiment_id: str
    execution_id: str
    assigned_variant: Literal["control", "candidate"]
    behavior_version_id: str
    assignment_reason: str
    created_at: datetime


class AssignmentRequest(BaseModel):
    """Request to determine assignment for an execution."""
    experiment_id: str
    execution_id: str
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context for assignment")


class AssignmentResponse(BaseModel):
    """Response with assignment decision."""
    experiment_id: str
    execution_id: str
    assigned_variant: Literal["control", "candidate"]
    behavior_version_id: str
    behavior_content: Dict[str, Any]


# ============================================================================
# Impact Measurement Models
# ============================================================================

class MetricComparison(BaseModel):
    """Comparison of a metric between control and candidate."""
    metric_name: str
    control_value: float
    candidate_value: float
    delta_value: float
    delta_percent: float
    confidence: float
    sample_control: int
    sample_candidate: int
    is_significant: bool
    is_improvement: bool


class AdaptationImpact(BaseModel):
    """Impact measurement for an experiment."""
    id: str
    experiment_id: str
    proposal_id: str
    metric_name: str
    control_value: float
    candidate_value: float
    delta_value: float
    confidence: float
    sample_control: int
    sample_candidate: int
    measured_at: datetime


class ExperimentImpactSummary(BaseModel):
    """Aggregated impact summary for an experiment."""
    experiment_id: str
    proposal_id: str
    status: ExperimentStatus

    # Sample sizes
    sample_control: int
    sample_candidate: int
    total_assignments: int

    # Primary metric
    primary_metric: MetricComparison

    # Guardrail results
    guardrail_results: List[MetricComparison]

    # All metrics
    all_metrics: List[MetricComparison]

    # Recommendation
    can_promote: bool
    should_rollback: bool
    promotion_reason: str
    rollback_reason: Optional[str] = None

    # Generated at
    generated_at: datetime


# ============================================================================
# Promotion/Rollback Models
# ============================================================================

class PromotionDecision(BaseModel):
    """Decision to promote an experiment."""
    experiment_id: str
    promoted_by: str
    promotion_reason: str
    metrics_summary: Dict[str, Any]


class RollbackDecision(BaseModel):
    """Decision to rollback an experiment."""
    experiment_id: str
    rolled_back_by: str
    rollback_reason: str
    metrics_summary: Dict[str, Any]
    immediate: bool = Field(default=True, description="Execute rollback immediately")


# ============================================================================
# Experiment Analysis Models
# ============================================================================

class ExperimentAnalysis(BaseModel):
    """Statistical analysis of experiment results."""
    experiment_id: str

    # Sample sizes
    n_control: int
    n_candidate: int

    # Power analysis
    statistical_power: float
    minimum_detectable_effect: float

    # Status
    has_minimum_sample_size: bool
    is_ready_for_decision: bool

    # Recommendations
    recommended_action: Literal["promote", "continue", "rollback", "reject"]
    confidence_in_recommendation: float
    reasoning: str
