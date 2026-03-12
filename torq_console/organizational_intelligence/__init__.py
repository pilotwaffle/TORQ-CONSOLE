"""
TORQ Layer 9 Organizational Intelligence - Main Module

L9-M1: Cross-mission learning, enterprise knowledge graph, and strategic decision intelligence.
"""

from .models import (
    # Organizational Intelligence
    OrganizationalIntelligenceRecord,
    create_organizational_intelligence,

    # Knowledge Graph
    GraphEntityType,
    GraphRelationType,
    KnowledgeGraphNode,
    KnowledgeGraphEdge,
    GraphPath,
    create_knowledge_graph_node,
    get_all_graph_entity_types,
    get_all_graph_relation_types,

    # Strategic Insights
    StrategicInsightCategory,
    StrategicInsight,
    create_strategic_insight,
    get_all_strategic_insight_categories,

    # Portfolio Analytics
    PortfolioMetricSnapshot,
    ReadinessHeatmapData,
    TrendDataPoint,
    TrendAnalysis,
    create_portfolio_snapshot,

    # Playbooks
    OrganizationalPlaybook,
    create_organizational_playbook,

    # Decision Support
    DecisionSupportRecommendation,
    DecisionSupportQuery,

    # Aggregation
    MissionGrouping,
    CrossMissionAggregation,
)

from .aggregation import get_cross_mission_aggregator
from .knowledge_graph import get_knowledge_graph_service

__all__ = [
    # Models
    "OrganizationalIntelligenceRecord",
    "GraphEntityType",
    "GraphRelationType",
    "KnowledgeGraphNode",
    "KnowledgeGraphEdge",
    "GraphPath",
    "StrategicInsightCategory",
    "StrategicInsight",
    "PortfolioMetricSnapshot",
    "ReadinessHeatmapData",
    "TrendDataPoint",
    "TrendAnalysis",
    "OrganizationalPlaybook",
    "DecisionSupportRecommendation",
    "DecisionSupportQuery",
    "MissionGrouping",
    "CrossMissionAggregation",
    # Factory functions
    "create_organizational_intelligence",
    "create_knowledge_graph_node",
    "create_strategic_insight",
    "create_portfolio_snapshot",
    "create_organizational_playbook",
    "get_all_graph_entity_types",
    "get_all_graph_relation_types",
    "get_all_strategic_insight_categories",
    # Services
    "get_cross_mission_aggregator",
    "get_knowledge_graph_service",
]


def get_layer9_services() -> dict:
    """Get all Layer 9 organizational intelligence services."""
    return {
        "cross_mission_aggregator": get_cross_mission_aggregator(),
        "knowledge_graph": get_knowledge_graph_service(),
    }
