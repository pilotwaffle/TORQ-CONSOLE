"""
TORQ Layer 10: Strategic Simulation & Decision Forecasting Models

L10-M1: Data models for scenario simulation, policy impact analysis,
strategic forecasting, and risk modeling.

This module defines the data structures for:
- Simulation scenarios and results
- Policy impact reports
- Strategic forecasts
- Risk assessments
- Planning workspace entities
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
# Simulation Scenario Models
# ============================================================================

class SimulationScope(str, Enum):
    """Scope of simulation scenarios."""
    SINGLE_MISSION = "single_mission"
    MISSION_TYPE = "mission_type"
    WORKFLOW = "workflow"
    CAPABILITY = "capability"
    POLICY_CHANGE = "policy_change"
    ORGANIZATIONAL = "organizational"
    TIMEFRAME = "timeframe"


class SimulationStatus(str, Enum):
    """Status of simulation runs."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SimulationParameter(BaseModel):
    """A parameter for a simulation scenario."""
    parameter_name: str
    parameter_value: Any
    parameter_type: str  # "string", "number", "boolean", "enum"
    description: str = ""
    default_value: Optional[Any] = None

    class Config:
        use_enum_values = True


class SimulationScenario(BaseModel):
    """A simulation scenario for testing strategic decisions."""
    scenario_id: UUID = Field(default_factory=uuid4)
    title: str
    description: str

    # Scope and parameters
    simulation_scope: SimulationScope
    parameters: Dict[str, Any] = Field(default_factory=dict)
    parameter_definitions: List[SimulationParameter] = Field(default_factory=list)

    # Target identification
    target_mission_id: Optional[str] = None
    target_workflow: Optional[str] = None
    target_capability: Optional[str] = None
    target_domain: Optional[str] = None

    # Simulation settings
    iterations: int = Field(default=100, ge=1, le=10000)
    confidence_level: float = Field(default=0.95, ge=0.0, le=1.0)

    # Metadata
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    tags: List[str] = Field(default_factory=list)

    class Config:
        use_enum_values = True


class SimulatedMissionOutcome(BaseModel):
    """Outcome of a simulated mission."""
    mission_id: str
    success: bool
    success_probability: float
    expected_duration: float
    expected_quality: float
    expected_token_usage: int
    readiness_at_execution: float
    confidence: float


class SimulationResult(BaseModel):
    """Results from running a simulation scenario."""
    result_id: UUID = Field(default_factory=uuid4)
    scenario_id: UUID

    # Predicted outcomes
    predicted_outcomes: Dict[str, float] = Field(default_factory=dict)
    readiness_forecast: Dict[str, float] = Field(default_factory=dict)
    risk_scores: Dict[str, float] = Field(default_factory=dict)

    # Mission-level results
    mission_outcomes: List[SimulatedMissionOutcome] = Field(default_factory=list)

    # Aggregate metrics
    total_simulations: int = 0
    success_rate: float = 0.0
    avg_duration: float = 0.0
    avg_quality: float = 0.0

    # Confidence
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence_interval: Optional[Dict[str, float]] = None

    # Status
    status: SimulationStatus = SimulationStatus.PENDING
    error_message: Optional[str] = None

    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        use_enum_values = True


# ============================================================================
# Policy Impact Models
# ============================================================================

class PolicyChangeType(str, Enum):
    """Types of policy changes."""
    READINESS_THRESHOLD = "readiness_threshold"
    PROMOTION_CRITERIA = "promotion_criteria"
    REGRESSION_THRESHOLD = "regression_threshold"
    VALIDATION_REQUIREMENT = "validation_requirement"
    GOVERNANCE_RULE = "governance_rule"


class PolicyImpactReport(BaseModel):
    """Report on the impact of a policy change."""
    report_id: UUID = Field(default_factory=uuid4)
    policy_id: str
    change_type: PolicyChangeType
    change_description: str

    # Baseline (current state)
    baseline_promotion_rate: float = 0.0
    baseline_regression_rate: float = 0.0
    baseline_ready_count: int = 0

    # Predicted impact
    predicted_promotion_rate: float = 0.0
    predicted_regression_rate: float = 0.0
    predicted_ready_count: int = 0

    # Changes
    promotion_rate_change: float = 0.0
    regression_rate_change: float = 0.0
    ready_count_change: int = 0

    # Affected capabilities
    affected_capabilities: List[str] = Field(default_factory=list)
    capabilities_at_risk: List[str] = Field(default_factory=list)
    capabilities_to_promote: List[str] = Field(default_factory=list)

    # Timeline
    implementation_timeline: Optional[str] = None
    stabilization_period: Optional[str] = None

    # Recommendations
    recommendations: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)

    # Confidence
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = None

    class Config:
        use_enum_values = True


class PolicySimulationConfig(BaseModel):
    """Configuration for policy simulation."""
    policy_id: str
    change_type: PolicyChangeType
    current_value: Any
    proposed_value: Any
    affected_domains: List[str] = Field(default_factory=list)
    simulation_iterations: int = 1000

    class Config:
        use_enum_values = True


# ============================================================================
# Strategic Forecasting Models
# ============================================================================

class ForecastType(str, Enum):
    """Types of strategic forecasts."""
    CAPABILITY_ADOPTION = "capability_adoption"
    MISSION_SUCCESS_TREND = "mission_success_trend"
    WORKFLOW_OPTIMIZATION = "workflow_optimization"
    READINESS_TREND = "readiness_trend"
    PERFORMANCE_PROJECTION = "performance_projection"
    RESOURCE_UTILIZATION = "resource_utilization"


class ForecastTrendDirection(str, Enum):
    """Direction of forecasted trends."""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    VOLATILE = "volatile"


class ForecastDataPoint(BaseModel):
    """A single data point in a forecast."""
    timestamp: datetime
    predicted_value: float
    confidence_lower: Optional[float] = None
    confidence_upper: Optional[float] = None
    segment: Optional[str] = None


class StrategicForecast(BaseModel):
    """A strategic prediction of future outcomes."""
    forecast_id: UUID = Field(default_factory=uuid4)
    forecast_type: ForecastType
    title: str
    description: str

    # Timeframe
    timeframe_start: datetime
    timeframe_end: datetime
    forecast_horizon_days: int

    # Predicted metrics
    predicted_metrics: Dict[str, float] = Field(default_factory=dict)
    trend_direction: ForecastTrendDirection = ForecastTrendDirection.STABLE

    # Data points
    data_points: List[ForecastDataPoint] = Field(default_factory=list)

    # Key insights
    key_insights: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)

    # Confidence
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    methodology: str = ""

    # Scope
    scope: str = "global"  # global, domain, capability, workflow
    scope_value: Optional[str] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    created_by: Optional[str] = None

    class Config:
        use_enum_values = True


# ============================================================================
# Risk Modeling Models
# ============================================================================

class RiskCategory(str, Enum):
    """Categories of risk."""
    EXECUTION = "execution"
    GOVERNANCE = "governance"
    OPERATIONAL_COMPLEXITY = "operational_complexity"
    READINESS_INSTABILITY = "readiness_instability"
    SYSTEMIC_PATTERN_DRIFT = "systemic_pattern_drift"
    CAPABILITY_DEGRADATION = "capability_degradation"
    RESOURCE_CONSTRAINT = "resource_constraint"
    STRATEGIC_MISALIGNMENT = "strategic_misalignment"


class RiskSeverity(str, Enum):
    """Severity levels for risks."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RiskMitigation(BaseModel):
    """A mitigation strategy for a risk."""
    mitigation_id: str
    strategy: str
    description: str
    estimated_cost: Optional[float] = None
    estimated_effort: Optional[str] = None  # "low", "medium", "high"
    effectiveness: float = Field(default=0.5, ge=0.0, le=1.0)


class RiskAssessment(BaseModel):
    """Assessment of a specific risk."""
    risk_id: UUID = Field(default_factory=uuid4)
    title: str
    description: str
    risk_category: RiskCategory

    # Risk scoring
    probability: float = Field(default=0.5, ge=0.0, le=1.0)
    impact: float = Field(default=0.5, ge=0.0, le=1.0)
    severity: RiskSeverity = RiskSeverity.MEDIUM

    # Risk score (probability × impact)
    risk_score: float = Field(default=0.25)

    # Context
    affected_capabilities: List[str] = Field(default_factory=list)
    affected_workflows: List[str] = Field(default_factory=list)
    affected_domains: List[str] = Field(default_factory=list)

    # Mitigation
    mitigation_options: List[RiskMitigation] = Field(default_factory=list)
    recommended_mitigation: Optional[str] = None

    # Monitoring
    monitoring_indicators: List[str] = Field(default_factory=list)
    review_frequency: Optional[str] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    assessed_by: Optional[str] = None
    status: str = "open"  # open, mitigating, resolved, accepted

    class Config:
        use_enum_values = True


class RiskModelReport(BaseModel):
    """Aggregated risk model report."""
    report_id: UUID = Field(default_factory=uuid4)
    scenario_id: Optional[UUID] = None

    # Aggregate risk scores
    overall_risk_score: float = 0.0
    risk_by_category: Dict[str, float] = Field(default_factory=dict)
    risk_by_severity: Dict[str, int] = Field(default_factory=dict)

    # Top risks
    top_risks: List[RiskAssessment] = Field(default_factory=list)
    critical_risk_count: int = 0
    high_risk_count: int = 0

    # Trend analysis
    risk_trend: str = "stable"  # increasing, stable, decreasing

    # Recommendations
    prioritized_mitigations: List[str] = Field(default_factory=list)
    strategic_recommendations: List[str] = Field(default_factory=list)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = None


# ============================================================================
# Planning Workspace Models
# ============================================================================

class PlanningSessionStatus(str, Enum):
    """Status of planning sessions."""
    DRAFT = "draft"
    ACTIVE = "active"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    ARCHIVED = "archived"


class ScenarioComparison(BaseModel):
    """Comparison between multiple simulation scenarios."""
    comparison_id: UUID = Field(default_factory=uuid4)
    scenario_ids: List[UUID] = Field(default_factory=list)

    # Comparison metrics
    metric_comparisons: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    winner_by_metric: Dict[str, UUID] = Field(default_factory=dict)

    # Overall assessment
    recommended_scenario: Optional[UUID] = None
    recommendation_rationale: str = ""

    # Trade-offs
    trade_offs: List[str] = Field(default_factory=list)
    considerations: List[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.now)


class PlanningSession(BaseModel):
    """A collaborative planning session."""
    session_id: UUID = Field(default_factory=uuid4)
    title: str
    description: str
    status: PlanningSessionStatus = PlanningSessionStatus.DRAFT

    # Associated scenarios
    scenario_ids: List[UUID] = Field(default_factory=list)
    comparison_id: Optional[UUID] = None

    # Participants
    participants: List[str] = Field(default_factory=list)
    owner: Optional[str] = None

    # Decisions
    decisions: List[str] = Field(default_factory=list)
    action_items: List[str] = Field(default_factory=list)

    # Timeline
    planning_horizon_start: Optional[datetime] = None
    planning_horizon_end: Optional[datetime] = None
    target_date: Optional[datetime] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    class Config:
        use_enum_values = True


# ============================================================================
# Factory Functions
# ============================================================================

def create_simulation_scenario(
    title: str,
    description: str,
    simulation_scope: SimulationScope,
    **kwargs
) -> SimulationScenario:
    """Create a simulation scenario."""
    return SimulationScenario(
        title=title,
        description=description,
        simulation_scope=simulation_scope,
        **kwargs
    )


def create_policy_impact_report(
    policy_id: str,
    change_type: PolicyChangeType,
    change_description: str,
    **kwargs
) -> PolicyImpactReport:
    """Create a policy impact report."""
    return PolicyImpactReport(
        policy_id=policy_id,
        change_type=change_type,
        change_description=change_description,
        **kwargs
    )


def create_strategic_forecast(
    forecast_type: ForecastType,
    title: str,
    description: str,
    timeframe_start: datetime,
    timeframe_end: datetime,
    **kwargs
) -> StrategicForecast:
    """Create a strategic forecast."""
    return StrategicForecast(
        forecast_type=forecast_type,
        title=title,
        description=description,
        timeframe_start=timeframe_start,
        timeframe_end=timeframe_end,
        forecast_horizon_days=(timeframe_end - timeframe_start).days,
        **kwargs
    )


def create_risk_assessment(
    title: str,
    description: str,
    risk_category: RiskCategory,
    **kwargs
) -> RiskAssessment:
    """Create a risk assessment."""
    return RiskAssessment(
        title=title,
        description=description,
        risk_category=risk_category,
        **kwargs
    )


def create_planning_session(
    title: str,
    description: str,
    **kwargs
) -> PlanningSession:
    """Create a planning session."""
    return PlanningSession(
        title=title,
        description=description,
        **kwargs
    )


# ============================================================================
# Enum Accessors
# ============================================================================

def get_all_simulation_scopes() -> List[SimulationScope]:
    """Get all simulation scope types."""
    return list(SimulationScope)


def get_all_policy_change_types() -> List[PolicyChangeType]:
    """Get all policy change types."""
    return list(PolicyChangeType)


def get_all_forecast_types() -> List[ForecastType]:
    """Get all forecast types."""
    return list(ForecastType)


def get_all_risk_categories() -> List[RiskCategory]:
    """Get all risk categories."""
    return list(RiskCategory)


def get_all_risk_severities() -> List[RiskSeverity]:
    """Get all risk severity levels."""
    return list(RiskSeverity)
