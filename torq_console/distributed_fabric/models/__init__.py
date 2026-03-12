"""
TORQ Layer 11 - Distributed Fabric Models

L11-M1: Data models for the distributed intelligence fabric.

This package provides models for:
- Node identity and health tracking
- Federation contracts and artifacts
- Routing decisions and constraints
- Failover events and configuration

All models respect Pre-Fabric Boundary Hardening (PRD-011-PRE).
"""

from .node_models import (
    # Node Identity
    NodeRegion,
    NodeTier,
    NodeType,
    NodeStatus,
    NodeCapability,
    NodeIdentity,
    NodeHealthMetrics,
    NodeInfo,
    # Federation
    FederationArtifactType,
    RedactionLevel,
    FederationExportContract,
    FederationImportValidation,
    FederatedIntelligence,
    # Routing
    RoutingCapability,
    RoutingConstraints,
    RoutingRequest,
    RoutingDecision,
    # Failover
    FailoverTriggerType,
    FailoverEvent,
    FailoverConfig,
    # Registration
    NodeRegistrationRequest,
    NodeRegistrationResponse,
    NodeHeartbeat,
    NodeHeartbeatResponse,
    # Statistics
    FabricStatistics,
)

from .federation_models import (
    # Federation Artifacts
    FederatedArtifact,
    FederatedPattern,
    FederatedBenchmark,
    FederatedInsight,
    FederatedRecommendation,
    # Metadata
    FederationMetadata,
    SharingScope,
    # Requests/Responses
    FederationExportRequest,
    FederationExportResponse,
    FederationImportRequest,
    FederationImportResponse,
    # Links and Policies
    FederationLink,
    FederationLinkStatus,
    FederationPolicy,
)

__all__ = [
    # Node Identity
    "NodeRegion",
    "NodeTier",
    "NodeType",
    "NodeStatus",
    "NodeCapability",
    "NodeIdentity",
    "NodeHealthMetrics",
    "NodeInfo",
    # Federation (node_models)
    "FederationArtifactType",
    "RedactionLevel",
    "FederationExportContract",
    "FederationImportValidation",
    "FederatedIntelligence",
    # Federation (federation_models)
    "FederatedArtifact",
    "FederatedPattern",
    "FederatedBenchmark",
    "FederatedInsight",
    "FederatedRecommendation",
    "FederationMetadata",
    "SharingScope",
    "FederationExportRequest",
    "FederationExportResponse",
    "FederationImportRequest",
    "FederationImportResponse",
    "FederationLink",
    "FederationLinkStatus",
    "FederationPolicy",
    # Routing
    "RoutingCapability",
    "RoutingConstraints",
    "RoutingRequest",
    "RoutingDecision",
    # Failover
    "FailoverTriggerType",
    "FailoverEvent",
    "FailoverConfig",
    # Registration
    "NodeRegistrationRequest",
    "NodeRegistrationResponse",
    "NodeHeartbeat",
    "NodeHeartbeatResponse",
    # Statistics
    "FabricStatistics",
]


# Version info
__version__ = "1.0.0"
