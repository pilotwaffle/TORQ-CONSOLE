"""
TORQ Layer 11 - Distributed Fabric Node Models

L11-M1: Data models for distributed TORQ nodes and fabric operations.

This module provides:
- Node identity and capability models
- Node health and status tracking
- Federation contract models
- Routing decision models
All models respect Pre-Fabric boundary hardening (PRD-011-PRE).
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


# ============================================================================
# Node Identity Models
# ============================================================================

class NodeRegion(str, Enum):
    """Geographic or logical regions for TORQ nodes."""
    US_EAST = "us_east"
    US_WEST = "us_west"
    EUROPE = "europe"
    ASIA_PACIFIC = "asia_pacific"
    GLOBAL = "global"
    LOCAL = "local"


class NodeTier(str, Enum):
    """Performance/capability tiers for nodes."""
    ENTERPRISE = "enterprise"  # High-capacity, full features
    STANDARD = "standard"     # Balanced capacity
    EDGE = "edge"            # Lightweight, edge deployment
    RESEARCH = "research"     # Experimental features


class NodeType(str, Enum):
    """Types of TORQ nodes."""
    PRIMARY = "primary"           # Main production node
    SECONDARY = "secondary"       # Backup/failover node
    COMPUTE = "compute"           # Compute-optimized
    STORAGE = "storage"           # Storage-optimized
    ANALYTICS = "analytics"       # Analytics-specialized
    FEDERATION = "federation"     # Federation gateway


class NodeStatus(str, Enum):
    """Operational status of a node."""
    STARTING = "starting"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    DRAINING = "draining"         # Graceful shutdown in progress
    MAINTENANCE = "maintenance"
    TERMINATED = "terminated"


class NodeCapability(BaseModel):
    """A capability that a TORQ node provides."""
    capability_id: UUID = Field(default_factory=uuid4)
    capability_name: str
    capability_type: str  # execution, memory, insight, pattern, etc.

    # Capacity
    capacity_units: int = 1
    max_concurrent_workloads: int = 10
    current_workload_count: int = 0

    # Performance
    avg_latency_ms: float = 50.0
    p95_latency_ms: float = 100.0
    p99_latency_ms: float = 200.0

    # Features
    supported_features: List[str] = Field(default_factory=list)
    enabled_domains: List[str] = Field(default_factory=list)

    # Constraints
    governance_constraints: Dict[str, Any] = Field(default_factory=dict)
    federation_eligible: bool = False


class NodeIdentity(BaseModel):
    """Identity information for a TORQ node."""
    node_id: UUID = Field(default_factory=uuid4)
    node_name: str
    node_type: NodeType
    node_tier: NodeTier
    region: NodeRegion

    # Network
    host_address: str
    port: int = 8443
    api_endpoint: Optional[str] = None

    # Organization
    organization_id: Optional[str] = None
    organization_name: Optional[str] = None

    # Metadata
    version: str = "1.0.0"
    labels: Dict[str, str] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)

    # Registration
    registered_at: datetime = Field(default_factory=datetime.now)
    last_heartbeat: Optional[datetime] = None


class NodeHealthMetrics(BaseModel):
    """Health metrics for a TORQ node."""
    node_id: UUID

    # Status
    status: NodeStatus = NodeStatus.STARTING
    health_score: float = Field(ge=0.0, le=1.0, default=1.0)

    # Resources
    cpu_utilization: float = Field(ge=0.0, le=1.0, default=0.0)
    memory_utilization: float = Field(ge=0.0, le=1.0, default=0.0)
    storage_utilization: float = Field(ge=0.0, le=1.0, default=0.0)

    # Workload
    active_workloads: int = 0
    queued_workloads: int = 0
    completed_workloads: int = 0
    failed_workloads: int = 0

    # Latency
    avg_response_time_ms: float = 0.0
    error_rate: float = Field(ge=0.0, le=1.0, default=0.0)

    # Timestamps
    measured_at: datetime = Field(default_factory=datetime.now)
    last_health_check: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None  # Added for tracking

    # Issues
    active_issues: List[str] = Field(default_factory=list)
    degraded_capabilities: List[str] = Field(default_factory=list)


class NodeInfo(BaseModel):
    """Complete information about a TORQ node."""
    identity: NodeIdentity
    capabilities: List[NodeCapability] = Field(default_factory=list)
    health: NodeHealthMetrics

    # Federation
    federation_enabled: bool = False
    federation_policies: List[str] = Field(default_factory=list)

    # Trust
    trusted_nodes: List[UUID] = Field(default_factory=list)
    trust_score: float = Field(ge=0.0, le=1.0, default=1.0)

    @property
    def node_id(self) -> UUID:
        return self.identity.node_id

    @property
    def is_healthy(self) -> bool:
        return self.health.status in (NodeStatus.HEALTHY, NodeStatus.STARTING, NodeStatus.DEGRADED)

    @property
    def can_accept_workload(self) -> bool:
        if not self.is_healthy:
            return False
        for cap in self.capabilities:
            if cap.current_workload_count < cap.max_concurrent_workloads:
                return True
        return False

    def get_capability(self, capability_name: str) -> Optional[NodeCapability]:
        for cap in self.capabilities:
            if cap.capability_name == capability_name:
                return cap
        return None


# ============================================================================
# Federation Models
# ============================================================================

class FederationArtifactType(str, Enum):
    """Types of artifacts that can be federated."""
    PATTERN = "pattern"
    INSIGHT = "insight"
    BENCHMARK = "benchmark"
    RECOMMENDATION = "recommendation"
    POLICY_REFERENCE = "policy_reference"
    AGGREGATED_STATISTICS = "aggregated_statistics"


class RedactionLevel(str, Enum):
    """Levels of redaction for federated artifacts."""
    NONE = "none"
    MINIMAL = "minimal"
    STANDARD = "standard"
    AGGRESSIVE = "aggressive"


class FederationExportContract(BaseModel):
    """Contract for exporting intelligence across nodes."""
    export_id: UUID = Field(default_factory=uuid4)
    source_node_id: UUID
    source_artifact_id: UUID

    # Content
    artifact_type: FederationArtifactType
    artifact_summary: str
    artifact_metadata: Dict[str, Any]

    # Redaction
    redaction_level: RedactionLevel
    redacted_fields: List[str] = Field(default_factory=list)

    # Destination
    target_node_ids: List[UUID]
    target_audience: str = "federation"

    # Validity
    export_timestamp: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    ttl_seconds: Optional[int] = None

    # Governance
    export_authority: str
    governance_tags: List[str] = Field(default_factory=list)
    policy_references: List[str] = Field(default_factory=list)

    # Integrity
    artifact_hash: str
    signature: Optional[str] = None


class FederationImportValidation(BaseModel):
    """Result of validating a federated import."""
    is_valid: bool
    validation_errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    # Checks
    signature_valid: bool = False
    source_authorized: bool = False
    redaction_compliant: bool = False
    within_ttl: bool = False

    # Artifacts
    validated_artifact: Optional[Dict[str, Any]] = None


class FederatedIntelligence(BaseModel):
    """Intelligence received from federation."""
    artifact_id: UUID = Field(default_factory=uuid4)
    source_node_id: UUID
    source_node_name: str

    # Content (redacted)
    artifact_type: FederationArtifactType
    content: Dict[str, Any]

    # Provenance
    exported_at: datetime
    imported_at: datetime = Field(default_factory=datetime.now)

    # Quality
    confidence: float = Field(ge=0.0, le=1.0)
    quality_score: Optional[float] = None

    # Usage Constraints
    usage_scope: str = "reference_only"  # NEVER becomes operational state
    expires_at: Optional[datetime] = None

    # Lineage
    origin_artifact_hash: Optional[str] = None
    derivation_chain: List[str] = Field(default_factory=list)


# ============================================================================
# Routing Models
# ============================================================================

class RoutingCapability(BaseModel):
    """Capability requirement for routing."""
    capability_name: str
    min_capacity: int = 1
    preferred_domains: List[str] = Field(default_factory=list)
    required_features: List[str] = Field(default_factory=list)


class RoutingConstraints(BaseModel):
    """Constraints for routing decisions."""
    max_latency_ms: Optional[float] = None
    preferred_regions: List[NodeRegion] = Field(default_factory=list)
    excluded_nodes: List[UUID] = Field(default_factory=list)
    required_tier: Optional[NodeTier] = None
    governance_tags: List[str] = Field(default_factory=list)
    cost_preference: str = "balanced"  # low_latency, balanced, cost_optimized


class RoutingRequest(BaseModel):
    """Request to route a workload to an optimal node."""
    request_id: UUID = Field(default_factory=uuid4)
    workload_type: str
    capability_requirements: List[RoutingCapability]

    # Constraints
    constraints: RoutingConstraints = Field(default_factory=RoutingConstraints)

    # Context
    requesting_node_id: Optional[UUID] = None
    priority: int = Field(default=0, ge=0, le=10)
    timeout_seconds: int = Field(default=30, ge=1)

    # Timestamp
    requested_at: datetime = Field(default_factory=datetime.now)


class RoutingDecision(BaseModel):
    """Decision for routing a workload."""
    request_id: UUID
    selected_node_id: UUID
    selected_node_name: str

    # Scoring
    confidence: float = Field(ge=0.0, le=1.0)
    routing_score: float = Field(ge=0.0, le=1.0)

    # Reasoning
    routing_reason: str
    considered_alternatives: List[Dict[str, Any]] = Field(default_factory=list)
    fallback_nodes: List[UUID] = Field(default_factory=list)

    # Expected Performance
    estimated_latency_ms: float
    estimated_cost: Optional[float] = None

    # Timestamp
    decided_at: datetime = Field(default_factory=datetime.now)


# ============================================================================
# Failover Models
# ============================================================================

class FailoverTriggerType(str, Enum):
    """Types of failover triggers."""
    NODE_UNHEALTHY = "node_unhealthy"
    HIGH_LATENCY = "high_latency"
    HIGH_ERROR_RATE = "high_error_rate"
    MAINTENANCE = "maintenance"
    MANUAL = "manual"


class FailoverEvent(BaseModel):
    """Record of a failover event."""
    event_id: UUID = Field(default_factory=uuid4)
    trigger_type: FailoverTriggerType

    # Nodes
    primary_node_id: UUID
    failover_node_id: UUID

    # Workload
    affected_workloads: List[UUID] = Field(default_factory=list)
    migrated_workloads: int = 0
    failed_migrations: int = 0

    # Timing
    triggered_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None

    # Reasoning
    trigger_reason: str
    recovery_steps: List[str] = Field(default_factory=list)

    # Status
    success: bool = False
    remaining_issues: List[str] = Field(default_factory=list)


class FailoverConfig(BaseModel):
    """Configuration for automatic failover."""
    auto_failover_enabled: bool = True

    # Thresholds
    health_score_threshold: float = 0.5
    error_rate_threshold: float = 0.1
    latency_threshold_ms: float = 1000.0

    # Timing
    heartbeat_interval_seconds: int = 30
    failover_timeout_seconds: int = 300
    graceful_shutdown_seconds: int = 60

    # Constraints
    max_concurrent_failovers: int = 3
    require_same_region: bool = True
    require_same_tier: bool = True


# ============================================================================
# Node Registration Models
# ============================================================================

class NodeRegistrationRequest(BaseModel):
    """Request to register a new node in the fabric."""
    node_name: str
    node_type: NodeType
    node_tier: NodeTier
    region: NodeRegion

    # Network
    host_address: str
    port: int = 8443

    # Organization
    organization_id: Optional[str] = None
    organization_name: Optional[str] = None

    # Capabilities
    capabilities: List[Dict[str, Any]] = Field(default_factory=list)

    # Metadata
    version: str = "1.0.0"
    labels: Dict[str, str] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)

    # Authentication
    auth_token: Optional[str] = None
    certificate: Optional[str] = None


class NodeRegistrationResponse(BaseModel):
    """Response to node registration."""
    success: bool
    node_id: Optional[UUID] = None
    message: str

    # Assigned configuration
    assigned_fabric_id: Optional[str] = None
    federation_policies: List[str] = Field(default_factory=list)

    # Next steps
    heartbeat_interval_seconds: int = 30
    api_endpoints: Dict[str, str] = Field(default_factory=dict)


class NodeHeartbeat(BaseModel):
    """Heartbeat from a node to maintain registration."""
    node_id: UUID
    timestamp: datetime = Field(default_factory=datetime.now)

    # Status
    status: NodeStatus
    health_score: float = Field(ge=0.0, le=1.0)

    # Workload
    active_workloads: int = 0
    avg_response_time_ms: float = 0.0

    # Issues
    issues: List[str] = Field(default_factory=list)


class NodeHeartbeatResponse(BaseModel):
    """Response to a heartbeat."""
    acknowledged: bool
    fabric_status: Dict[str, Any] = Field(default_factory=dict)

    # Commands
    commands: List[str] = Field(default_factory=list)
    requested_actions: List[str] = Field(default_factory=list)

    # Configuration updates
    config_version: Optional[str] = None
    new_policies: List[str] = Field(default_factory=list)


# ============================================================================
# Statistics Models
# ============================================================================

class FabricStatistics(BaseModel):
    """Aggregate statistics for the TORQ fabric."""
    total_nodes: int = 0
    healthy_nodes: int = 0
    degraded_nodes: int = 0
    unhealthy_nodes: int = 0

    # Nodes by tier
    nodes_by_tier: Dict[str, int] = Field(default_factory=dict)

    # Nodes by region
    nodes_by_region: Dict[str, int] = Field(default_factory=dict)

    # Workload
    total_workloads: int = 0
    total_capacity: int = 0
    utilization_rate: float = 0.0

    # Federation
    total_exports: int = 0
    total_imports: int = 0
    active_federation_links: int = 0

    # Failover
    failover_events_24h: int = 0
    avg_failover_duration_seconds: float = 0.0

    # Timestamp
    calculated_at: datetime = Field(default_factory=datetime.now)


# ============================================================================
# Export Helper Functions
# ============================================================================

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
    # Federation
    "FederationArtifactType",
    "RedactionLevel",
    "FederationExportContract",
    "FederationImportValidation",
    "FederatedIntelligence",
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
