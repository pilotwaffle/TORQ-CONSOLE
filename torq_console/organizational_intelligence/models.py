"""
TORQ Layer 9: Organizational Intelligence Models

L9-M1: Data models for cross-mission learning and enterprise intelligence.

This module defines the data structures for:
- Cross-mission aggregation
- Enterprise knowledge graph
- Strategic insights
- Portfolio analytics
- Organizational playbooks
- Decision support
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
# Organizational Intelligence Records
# ============================================================================

class OrganizationalIntelligenceRecord(BaseModel):
    """A record of organization-level intelligence."""
    record_id: UUID = Field(default_factory=uuid4)
    record_type: str
    title: str
    summary: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    impact_score: float = Field(default=0.5, ge=0.0, le=1.0)

    # Evidence
    domains: List[str] = Field(default_factory=list)
    supporting_missions: List[str] = Field(default_factory=list)
    supporting_patterns: List[str] = Field(default_factory=list)
    supporting_insights: List[str] = Field(default_factory=list)

    # Timeframe
    timeframe_start: datetime
    timeframe_end: datetime

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = None

    class Config:
        use_enum_values = True


# ============================================================================
# Knowledge Graph Models
# ============================================================================

class GraphEntityType(str, Enum):
    """Types of entities in the knowledge graph."""
    MISSION = "mission"
    WORKFLOW = "workflow"
    CAPABILITY = "capability"
    AGENT = "agent"
    TOOL = "tool"
    TEAM = "team"
    PATTERN = "pattern"
    INSIGHT = "insight"
    READINESS_CANDIDATE = "readiness_candidate"
    RECOMMENDATION = "recommendation"
    DOMAIN = "domain"
    OBJECTIVE = "objective"
    RISK = "risk"
    OUTCOME = "outcome"
    PLAYBOOK = "playbook"


class GraphRelationType(str, Enum):
    """Types of relationships in the knowledge graph."""
    USED_TOOL = "used_tool"
    EXECUTED_BY = "executed_by"
    SUPPORTED_BY = "supported_by"
    LED_TO = "led_to"
    BLOCKED_BY = "blocked_by"
    PROMOTED_TO = "promoted_to"
    PREDICTED_BY = "predicted_by"
    SUPERSEDED_BY = "superseded_by"
    MITIGATED_BY = "mitigated_by"
    ASSOCIATED_WITH = "associated_with"
    REUSED_AS = "reused_as"
    INFLUENCED = "influenced"
    CONTAINS = "contains"
    DEPENDS_ON = "depends_on"


class KnowledgeGraphNode(BaseModel):
    """A node in the enterprise knowledge graph."""
    node_id: str
    node_type: GraphEntityType
    label: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    first_seen: Optional[datetime] = None

    # Relationships (edges)
    in_degree: int = 0
    out_degree: int = 0

    class Config:
        use_enum_values = True


class KnowledgeGraphEdge(BaseModel):
    """An edge in the enterprise knowledge graph."""
    edge_id: str
    source_id: str
    target_id: str
    relation_type: GraphRelationType
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    weight: float = Field(default=1.0)

    # Evidence
    evidence_count: int = Field(default=1)
    supporting_records: List[str] = Field(default_factory=list)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    last_observed: datetime = Field(default_factory=datetime.now)

    class Config:
        use_enum_values = True


class GraphPath(BaseModel):
    """A path through the knowledge graph."""
    path_id: str
    nodes: List[str]
    edges: List[str]
    source_id: str
    target_id: str
    length: int
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


# ============================================================================
# Strategic Insight Models
# ============================================================================

class StrategicInsightCategory(str, Enum):
    """Categories of strategic insights."""
    STRATEGIC_BOTTLENECK = "strategic_bottleneck"
    ENTERPRISE_BEST_PRACTICE = "enterprise_best_practice"
    RECURRING_ORGANIZATIONAL_RISK = "recurring_organizational_risk"
    CAPABILITY_MATURITY_SIGNAL = "capability_maturity_signal"
    CROSS_DOMAIN_OPPORTUNITY = "cross_domain_opportunity"
    GOVERNANCE_EFFICIENCY_SIGNAL = "governance_efficiency_signal"
    EXECUTION_LEVERAGE_POINT = "execution_leverage_point"


class StrategicInsight(BaseModel):
    """A strategic, organization-level insight."""
    insight_id: UUID = Field(default_factory=uuid4)
    category: StrategicInsightCategory
    title: str
    narrative: str

    # Scoring
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    impact_score: float = Field(default=0.5, ge=0.0, le=1.0)
    urgency: float = Field(default=0.5, ge=0.0, le=1.0)

    # Evidence
    evidence_refs: List[str] = Field(default_factory=list)
    supporting_missions: List[str] = Field(default_factory=list)
    supporting_patterns: List[str] = Field(default_factory=list)
    graph_paths: List[str] = Field(default_factory=list)

    # Recommendations
    recommendation_refs: List[str] = Field(default_factory=list)
    suggested_actions: List[str] = Field(default_factory=list)

    # Scope
    affected_domains: List[str] = Field(default_factory=list)
    affected_capabilities: List[str] = Field(default_factory=list)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None

    class Config:
        use_enum_values = True


# ============================================================================
# Portfolio Analytics Models
# ============================================================================

class PortfolioMetricSnapshot(BaseModel):
    """A snapshot of portfolio-wide metrics."""
    snapshot_id: UUID = Field(default_factory=uuid4)
    timeframe_start: datetime
    timeframe_end: datetime

    # Core metrics
    total_missions: int = 0
    successful_missions: float = 0.0
    mission_success_rate: float = 0.0

    # Readiness metrics
    total_candidates: int = 0
    ready_candidates: int = 0
    blocked_candidates: int = 0
    regression_count: int = 0

    # Pattern metrics
    active_patterns: int = 0
    validated_patterns: int = 0
    pattern_accuracy_avg: float = 0.0

    # Insight metrics
    total_insights: int = 0
    high_confidence_insights: int = 0

    # Learning metrics
    recommendations_generated: int = 0
    recommendations_implemented: int = 0
    implementation_rate: float = 0.0

    # Segmentation
    segment_by: Optional[str] = None
    segment_values: Dict[str, float] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        use_enum_values = True


class ReadinessHeatmapData(BaseModel):
    """Data for readiness heatmap visualization."""
    capability_class: str
    domain: Optional[str] = None
    total_candidates: int = 0
    ready_count: int = 0
    blocked_count: int = 0
    watchlist_count: int = 0
    regressed_count: int = 0
    avg_confidence: float = 0.0
    avg_time_to_ready: float = 0.0


class TrendDataPoint(BaseModel):
    """A single data point in a trend."""
    timestamp: datetime
    value: float
    segment: Optional[str] = None


class TrendAnalysis(BaseModel):
    """Analysis of a metric over time."""
    metric_name: str
    data_points: List[TrendDataPoint]
    trend_direction: str  # "improving", "stable", "declining"
    change_rate: float = 0.0
    confidence: float = 0.5

    class Config:
        use_enum_values = True


# ============================================================================
# Organizational Playbook Models
# ============================================================================

class OrganizationalPlaybook(BaseModel):
    """A reusable organizational operating playbook."""
    playbook_id: UUID = Field(default_factory=uuid4)
    title: str
    description: str

    # Applicability
    applicable_domains: List[str] = Field(default_factory=list)
    applicable_mission_types: List[str] = Field(default_factory=list)

    # Composition
    recommended_workflows: List[str] = Field(default_factory=list)
    recommended_tools: List[str] = Field(default_factory=list)
    recommended_agents: List[str] = Field(default_factory=list)
    recommended_patterns: List[str] = Field(default_factory=list)

    # Performance
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    readiness_success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    avg_execution_time: float = Field(default=0.0)

    # Usage
    reuse_count: int = 0
    last_used: Optional[datetime] = None
    lineage_refs: List[str] = Field(default_factory=list)

    # Validation
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    validated_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        use_enum_values = True


# ============================================================================
# Decision Support Models
# ============================================================================

class DecisionSupportRecommendation(BaseModel):
    """A recommendation from the decision support system."""
    recommendation_id: UUID = Field(default_factory=uuid4)
    title: str
    description: str
    recommendation_type: str

    # Evidence
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    impact_estimate: float = Field(default=0.5, ge=0.0, le=1.0)
    supporting_records: List[str] = Field(default_factory=list)
    graph_paths: List[GraphPath] = Field(default_factory=list)

    # Explanation
    rationale: str
    key_factors: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    alternatives: List[str] = Field(default_factory=list)

    # Suggested actions
    suggested_actions: List[str] = Field(default_factory=list)
    implementation_complexity: str = "medium"  # low, medium, high

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None

    class Config:
        use_enum_values = True


class DecisionSupportQuery(BaseModel):
    """A query to the decision support system."""
    query_id: UUID = Field(default_factory=uuid4)
    question: str
    query_type: str
    context: Dict[str, Any] = Field(default_factory=dict)

    # Results
    recommendations: List[DecisionSupportRecommendation] = Field(default_factory=list)
    summary: str = ""

    # Timing
    created_at: datetime = Field(default_factory=datetime.now)
    answered_at: Optional[datetime] = None

    class Config:
        use_enum_values = True


# ============================================================================
# Aggregation Models
# ============================================================================

class MissionGrouping(BaseModel):
    """A grouping of missions for aggregation."""
    grouping_id: str
    grouping_type: str  # "mission_type", "domain", "workflow", etc.
    grouping_key: str
    mission_ids: List[str] = Field(default_factory=list)

    # Aggregated metrics
    total_missions: int = 0
    success_count: int = 0
    success_rate: float = 0.0
    avg_duration: float = 0.0
    avg_quality_score: float = 0.0

    # Common patterns
    common_patterns: List[str] = Field(default_factory=list)
    common_tools: List[str] = Field(default_factory=list)
    common_agents: List[str] = Field(default_factory=list)

    timeframe_start: datetime
    timeframe_end: datetime

    class Config:
        use_enum_values = True


class CrossMissionAggregation(BaseModel):
    """Result of cross-mission aggregation."""
    aggregation_id: UUID = Field(default_factory=uuid4)
    aggregation_type: str  # "by_mission_type", "by_domain", etc.
    groupings: List[MissionGrouping] = Field(default_factory=list)

    # Overall statistics
    total_missions_analyzed: int = 0
    overall_success_rate: float = 0.0
    strategic_signals: List[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        use_enum_values = True


# ============================================================================
# Factory Functions
# ============================================================================

def create_organizational_intelligence(
    record_type: str,
    title: str,
    summary: str,
    **kwargs
) -> OrganizationalIntelligenceRecord:
    """Create an organizational intelligence record."""
    return OrganizationalIntelligenceRecord(
        record_type=record_type,
        title=title,
        summary=summary,
        **kwargs
    )


def create_knowledge_graph_node(
    node_id: str,
    node_type: GraphEntityType,
    label: str,
    **kwargs
) -> KnowledgeGraphNode:
    """Create a knowledge graph node."""
    return KnowledgeGraphNode(
        node_id=node_id,
        node_type=node_type,
        label=label,
        **kwargs
    )


def create_strategic_insight(
    category: StrategicInsightCategory,
    title: str,
    narrative: str,
    **kwargs
) -> StrategicInsight:
    """Create a strategic insight."""
    return StrategicInsight(
        category=category,
        title=title,
        narrative=narrative,
        **kwargs
    )


def create_portfolio_snapshot(
    timeframe_start: datetime,
    timeframe_end: datetime,
    **kwargs
) -> PortfolioMetricSnapshot:
    """Create a portfolio metrics snapshot."""
    return PortfolioMetricSnapshot(
        timeframe_start=timeframe_start,
        timeframe_end=timeframe_end,
        **kwargs
    )


def create_organizational_playbook(
    title: str,
    description: str,
    **kwargs
) -> OrganizationalPlaybook:
    """Create an organizational playbook."""
    return OrganizationalPlaybook(
        title=title,
        description=description,
        **kwargs
    )


def get_all_graph_entity_types() -> List[GraphEntityType]:
    """Get all graph entity types."""
    return list(GraphEntityType)


def get_all_graph_relation_types() -> List[GraphRelationType]:
    """Get all graph relation types."""
    return list(GraphRelationType)


def get_all_strategic_insight_categories() -> List[StrategicInsightCategory]:
    """Get all strategic insight categories."""
    return list(StrategicInsightCategory)
