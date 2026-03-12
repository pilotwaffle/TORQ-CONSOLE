"""
TORQ Layer 11: Distributed Intelligence Fabric

L11-M1: Transforms TORQ from a single intelligent runtime into a distributed
intelligence fabric capable of operating across multiple nodes, regions, and
organizations.

This module provides:
- NodeRegistryService: Node discovery and health monitoring
- CapabilityRouter: Intelligent workload routing across nodes
- FederationController: Secure cross-node communication
- FailoverManager: Automatic resilience and recovery

All operations respect Pre-Fabric Boundary Hardening (PRD-011-PRE):
- Operational state never leaves its origin node
- Strategic state cannot federate directly (only via audit artifacts)
- Analytical intelligence is the primary federation product
- Every node remains independently functional
"""

from __future__ import annotations

import logging


logger = logging.getLogger(__name__)


# Import models
from .models import (
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

from .models.federation_models import (
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

# Import services
from .node_registry_service import (
    NodeRegistryService,
    get_node_registry_service,
)
from .capability_router import (
    CapabilityRouter,
    get_capability_router,
)
from .federation_controller import (
    FederationController,
    get_federation_controller,
)
from .failover_manager import (
    FailoverManager,
    get_failover_manager,
)


__all__ = [
    # Models - Node Identity
    "NodeRegion",
    "NodeTier",
    "NodeType",
    "NodeStatus",
    "NodeCapability",
    "NodeIdentity",
    "NodeHealthMetrics",
    "NodeInfo",
    # Models - Federation
    "FederationArtifactType",
    "RedactionLevel",
    "FederationExportContract",
    "FederationImportValidation",
    "FederatedIntelligence",
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
    # Models - Routing
    "RoutingCapability",
    "RoutingConstraints",
    "RoutingRequest",
    "RoutingDecision",
    # Models - Failover
    "FailoverTriggerType",
    "FailoverEvent",
    "FailoverConfig",
    # Models - Registration
    "NodeRegistrationRequest",
    "NodeRegistrationResponse",
    "NodeHeartbeat",
    "NodeHeartbeatResponse",
    # Models - Statistics
    "FabricStatistics",
    # Services
    "NodeRegistryService",
    "get_node_registry_service",
    "CapabilityRouter",
    "get_capability_router",
    "FederationController",
    "get_federation_controller",
    "FailoverManager",
    "get_failover_manager",
]


def get_layer11_services() -> dict:
    """Get all Layer 11 services for integration."""
    return {
        "node_registry": get_node_registry_service(),
        "capability_router": get_capability_router(),
        "failover_manager": get_failover_manager(),
        # Federation controller is per-node, so not included here
    }


# Version info
__version__ = "1.0.0"
