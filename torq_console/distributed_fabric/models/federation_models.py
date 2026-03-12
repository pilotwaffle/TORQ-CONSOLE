"""
TORQ Layer 11 - Distributed Fabric Federation Models

L11-M1: Models for federated intelligence sharing between TORQ nodes.

This module extends the IntelligenceArtifact standard from Pre-Fabric
Boundary Hardening with federation-specific capabilities.

Key Principles:
- Operational state never leaves its origin node
- Strategic state cannot federate directly (only via audit artifacts)
- Analytical intelligence is the primary federation product
- All federated artifacts are redacted and governed
"""

from __future__ import annotations

import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


# ============================================================================
# Federation Artifact Models
# ============================================================================

class SharingScope(str, Enum):
    """Scope of sharing for federated artifacts."""
    PRIVATE = "private"           # Single node only
    ORGANIZATION = "organization"  # Within organization
    FEDERATION = "federation"     # Across trusted nodes
    PUBLIC = "public"             # Any node


class FederationMetadata(BaseModel):
    """Metadata attached to all federated artifacts."""
    # Source
    source_node_id: UUID
    source_node_name: str
    source_region: str
    source_organization: Optional[str] = None

    # Classification
    artifact_type: str
    sharing_scope: SharingScope
    sensitivity_level: str = "internal"  # public, internal, confidential

    # Integrity
    content_hash: str
    signature: Optional[str] = None

    # Validity
    created_at: datetime
    expires_at: Optional[datetime] = None
    ttl_seconds: Optional[int] = None

    # Governance
    governance_tags: List[str] = Field(default_factory=list)
    policy_references: List[str] = Field(default_factory=list)
    export_authority: str = "system"

    # Federation
    federation_path: List[UUID] = Field(default_factory=list)  # Nodes this has passed through
    hop_count: int = 0


class FederatedArtifact(BaseModel):
    """
    A federated intelligence artifact.

    This is the primary unit of data exchange between TORQ nodes.
    It wraps the IntelligenceArtifact standard with federation metadata.
    """
    artifact_id: UUID = Field(default_factory=uuid4)

    # Core content (redacted)
    artifact_type: str
    title: str
    description: str
    content: Dict[str, Any]

    # Quality
    confidence: float = Field(ge=0.0, le=1.0)
    quality_score: Optional[float] = Field(default=Field(default=None, ge=0.0, le=1.0))

    # Lineage
    source_artifact_ids: List[UUID] = Field(default_factory=list)
    origin_node_id: UUID
    derivation_chain: List[str] = Field(default_factory=list)

    # Federation metadata
    federation_metadata: FederationMetadata

    # Redaction info
    redaction_level: str
    redacted_fields: List[str] = Field(default_factory=list)

    # Usage constraints (enforces Pre-Fabric boundary hardening)
    usage_scope: str = "reference_only"  # NEVER becomes operational state

    @property
    def source_node_id(self) -> UUID:
        """Convenience property to access source node ID from federation metadata."""
        return self.federation_metadata.source_node_id

    @property
    def sharing_scope(self) -> SharingScope:
        """Convenience property to access sharing scope from federation metadata."""
        return self.federation_metadata.sharing_scope

    @classmethod
    def from_intelligence_artifact(
        cls,
        artifact_id: UUID,
        artifact_type: str,
        title: str,
        description: str,
        content: Dict[str, Any],
        confidence: float,
        source_node_id: UUID,
        source_node_name: str,
        source_region: str,
        redaction_level: str = "standard",
        sharing_scope: SharingScope = SharingScope.FEDERATION,
        governance_tags: Optional[List[str]] = None,
        expires_at: Optional[datetime] = None,
    ) -> "FederatedArtifact":
        """Create a federated artifact from an intelligence artifact."""
        # Calculate content hash
        content_str = json.dumps(content, sort_keys=True)
        content_hash = hashlib.sha256(content_str.encode()).hexdigest()

        # Apply redaction based on level
        redacted_fields = []
        redacted_content = content.copy()

        if redaction_level in ("minimal", "standard", "aggressive"):
            # Remove sensitive patterns
            for key in list(redacted_content.keys()):
                if any(pattern in key.lower() for pattern in [
                    "secret", "token", "password", "key", "private",
                    "_id", "internal", "workspace", "user_id"
                ]):
                    if redaction_level != "minimal" or key.endswith("_id"):
                        redacted_fields.append(key)
                        if redaction_level == "aggressive":
                            redacted_content.pop(key, None)
                        else:
                            redacted_content[key] = "***"

        federation_metadata = FederationMetadata(
            source_node_id=source_node_id,
            source_node_name=source_node_name,
            source_region=source_region,
            artifact_type=artifact_type,
            sharing_scope=sharing_scope,
            content_hash=content_hash,
            created_at=datetime.now(),
            expires_at=expires_at,
            governance_tags=governance_tags or [],
        )

        return cls(
            artifact_type=artifact_type,
            title=title,
            description=str(description),  # Fix: ensure description is string
            content=redacted_content,
            confidence=confidence,
            source_node_id=source_node_id,
            origin_node_id=source_node_id,  # Add origin_node_id
            federation_metadata=federation_metadata,
            redaction_level=redaction_level,
            redacted_fields=redacted_fields,
        )

    def is_valid(self) -> bool:
        """Check if the artifact is still valid."""
        # Check expiration
        if self.federation_metadata.expires_at:
            if datetime.now() > self.federation_metadata.expires_at:
                return False

        # Check hop count (prevent infinite loops)
        if self.federation_metadata.hop_count > 10:
            return False

        return True

    def can_consume(self, consumer_node_id: UUID, trusted_nodes: Set[UUID]) -> bool:
        """Check if a node can consume this artifact."""
        # Private artifacts only for source node
        if self.federation_metadata.sharing_scope == SharingScope.PRIVATE:
            return consumer_node_id == self.federation_metadata.source_node_id

        # Federation artifacts require trust
        if self.federation_metadata.sharing_scope == SharingScope.FEDERATION:
            return self.federation_metadata.source_node_id in trusted_nodes

        # Organization and public are generally allowed
        return True

    def add_hop(self, node_id: UUID) -> None:
        """Record that this artifact has passed through a node."""
        self.federation_metadata.federation_path.append(node_id)
        self.federation_metadata.hop_count += 1


# ============================================================================
# Pattern Export Models
# ============================================================================

class FederatedPattern(FederatedArtifact):
    """A learned pattern shared between nodes."""

    @classmethod
    def create(
        cls,
        pattern_id: UUID,
        pattern_name: str,
        pattern_type: str,
        description: str,
        confidence: float,
        source_node_id: UUID,
        source_node_name: str,
        source_region: str,
        pattern_data: Dict[str, Any],
        sample_size: int = 0,
        redaction_level: str = "standard",
    ) -> "FederatedPattern":
        """Create a federated pattern artifact."""
        content = {
            "pattern_id": str(pattern_id),
            "pattern_name": pattern_name,
            "pattern_type": pattern_type,
            "sample_size": sample_size,
            "pattern_data": pattern_data,
        }

        artifact = cls.from_intelligence_artifact(
            artifact_id=uuid4(),
            artifact_type="learned_pattern",
            title=f"Pattern: {pattern_name}",
            description=str(description),  # Fix: ensure description is string
            content=content,
            confidence=confidence,
            source_node_id=source_node_id,
            source_node_name=source_node_name,
            source_region=source_region,
            redaction_level=redaction_level,
            sharing_scope=SharingScope.FEDERATION,
        )

        # Store original pattern_id in metadata
        artifact.federation_metadata.policy_references.append(f"pattern:{pattern_id}")

        return artifact


class FederatedBenchmark(FederatedArtifact):
    """A benchmark summary shared between nodes."""

    @classmethod
    def create(
        cls,
        metric_name: str,
        metric_type: str,
        statistics: Dict[str, float],
        sample_size: int,
        source_node_id: UUID,
        source_node_name: str,
        source_region: str,
        confidence: float = 0.95,
        redaction_level: str = "standard",
    ) -> "FederatedBenchmark":
        """Create a federated benchmark artifact."""
        content = {
            "metric_name": metric_name,
            "metric_type": metric_type,
            "statistics": statistics,  # mean, median, p95, p99, etc.
            "sample_size": sample_size,
        }

        return cls.from_intelligence_artifact(
            artifact_id=uuid4(),
            artifact_type="benchmark",
            title=f"Benchmark: {metric_name}",
            description=f"{metric_type} benchmark from {sample_size} samples",
            content=content,
            confidence=confidence,
            source_node_id=source_node_id,
            source_node_name=source_node_name,
            source_region=source_region,
            redaction_level=redaction_level,
            sharing_scope=SharingScope.FEDERATION,
            governance_tags=["benchmark", metric_type],
        )


class FederatedInsight(FederatedArtifact):
    """An insight or anomaly detection shared between nodes."""

    @classmethod
    def create(
        cls,
        insight_type: str,
        description: str,
        insight_data: Dict[str, Any],
        severity: str,
        confidence: float,
        source_node_id: UUID,
        source_node_name: str,
        source_region: str,
        redaction_level: str = "standard",
    ) -> "FederatedInsight":
        """Create a federated insight artifact."""
        content = {
            "insight_type": insight_type,
            "severity": severity,
            "insight_data": insight_data,
        }

        return cls.from_intelligence_artifact(
            artifact_id=uuid4(),
            artifact_type="insight",
            title=f"Insight: {insight_type}",
            description=description,
            content=content,
            confidence=confidence,
            source_node_id=source_node_id,
            source_node_name=source_node_name,
            source_region=source_region,
            redaction_level=redaction_level,
            sharing_scope=SharingScope.FEDERATION,
            governance_tags=["insight", insight_type, severity],
        )


class FederatedRecommendation(FederatedArtifact):
    """A recommendation shared between nodes."""

    @classmethod
    def create(
        cls,
        recommendation_type: str,
        description: str,
        recommendation_data: Dict[str, Any],
        expected_impact: Dict[str, float],
        confidence: float,
        source_node_id: UUID,
        source_node_name: str,
        source_region: str,
        redaction_level: str = "standard",
    ) -> "FederatedRecommendation":
        """Create a federated recommendation artifact."""
        content = {
            "recommendation_type": recommendation_type,
            "recommendation_data": recommendation_data,
            "expected_impact": expected_impact,
        }

        return cls.from_intelligence_artifact(
            artifact_id=uuid4(),
            artifact_type="recommendation",
            title=f"Recommendation: {recommendation_type}",
            description=description,
            content=content,
            confidence=confidence,
            source_node_id=source_node_id,
            source_node_name=source_node_name,
            source_region=source_region,
            redaction_level=redaction_level,
            sharing_scope=SharingScope.FEDERATION,
            governance_tags=["recommendation", recommendation_type],
        )


# ============================================================================
# Federation Request/Response Models
# ============================================================================

class FederationExportRequest(BaseModel):
    """Request to export artifacts to federation."""
    requesting_node_id: UUID
    artifact_ids: List[UUID]

    # Target
    target_node_ids: Optional[List[UUID]] = None  # None = broadcast to federation
    target_audience: str = "federation"

    # Redaction
    redaction_level: str = "standard"
    custom_redactions: List[str] = Field(default_factory=list)

    # Validity
    ttl_seconds: Optional[int] = None
    expires_at: Optional[datetime] = None

    # Governance
    export_authority: str = "system"
    governance_tags: List[str] = Field(default_factory=list)

    # Timestamp
    requested_at: datetime = Field(default_factory=datetime.now)


class FederationExportResponse(BaseModel):
    """Response to a federation export request."""
    success: bool
    export_id: UUID = Field(default_factory=uuid4)

    # Results
    exported_artifacts: List[UUID] = Field(default_factory=list)
    failed_artifacts: List[Dict[str, str]] = Field(default_factory=list)

    # Contracts
    export_contracts: List[Dict[str, Any]] = Field(default_factory=list)

    # Warnings
    warnings: List[str] = Field(default_factory=list)

    # Timestamp
    exported_at: datetime = Field(default_factory=datetime.now)


class FederationImportRequest(BaseModel):
    """Request to import artifacts from federation."""
    requesting_node_id: UUID
    source_node_ids: Optional[List[UUID]] = None  # None = any source

    # Filters
    artifact_types: Optional[List[str]] = None
    min_confidence: float = 0.0
    required_governance_tags: List[str] = Field(default_factory=list)

    # Limits
    max_artifacts: int = 100
    max_age_seconds: Optional[int] = None

    # Timestamp
    requested_at: datetime = Field(default_factory=datetime.now)


class FederationImportResponse(BaseModel):
    """Response to a federation import request."""
    success: bool
    import_id: UUID = Field(default_factory=uuid4)

    # Artifacts
    imported_artifacts: List[FederatedArtifact] = Field(default_factory=list)

    # Validation
    validation_results: List[FederationImportValidation] = Field(default_factory=list)

    # Warnings
    warnings: List[str] = Field(default_factory=list)

    # Timestamp
    imported_at: datetime = Field(default_factory=datetime.now)


# ============================================================================
# Federation Link Models
# ============================================================================

class FederationLinkStatus(str, Enum):
    """Status of a federation link between nodes."""
    ACTIVE = "active"
    DEGRADED = "degraded"
    DISCONNECTED = "disconnected"
    BLOCKED = "blocked"


class FederationLink(BaseModel):
    """A federation link between two nodes."""
    link_id: UUID = Field(default_factory=uuid4)
    source_node_id: UUID
    target_node_id: UUID

    # Status
    status: FederationLinkStatus = FederationLinkStatus.ACTIVE
    last_ping: Optional[datetime] = None
    last_successful_export: Optional[datetime] = None

    # Statistics
    total_exports: int = 0
    total_imports: int = 0
    failed_exports: int = 0
    failed_imports: int = 0
    avg_latency_ms: float = 0.0

    # Configuration
    enabled: bool = True
    trust_level: float = Field(ge=0.0, le=1.0, default=1.0)
    allowed_artifact_types: List[str] = Field(default_factory=list)

    # Constraints
    max_bandwidth_mbps: Optional[int] = None
    rate_limit_per_second: Optional[int] = None

    @property
    def is_healthy(self) -> bool:
        return self.status == FederationLinkStatus.ACTIVE and self.enabled

    @property
    def success_rate(self) -> float:
        total = self.total_exports + self.total_imports
        failed = self.failed_exports + self.failed_imports
        if total == 0:
            return 1.0
        return (total - failed) / total


class FederationPolicy(BaseModel):
    """Policy governing federation between nodes."""
    policy_id: UUID = Field(default_factory=uuid4)
    policy_name: str

    # Scope
    source_nodes: List[UUID] = Field(default_factory=list)
    target_nodes: List[UUID] = Field(default_factory=list)
    artifact_types: List[str] = Field(default_factory=list)

    # Rules
    allowed_sharing_scopes: List[SharingScope] = Field(default_factory=list)
    required_governance_tags: List[str] = Field(default_factory=list)
    forbidden_governance_tags: List[str] = Field(default_factory=list)

    # Redaction
    min_redaction_level: str = "standard"
    custom_redactions: Dict[str, List[str]] = Field(default_factory=dict)

    # Validation
    requires_signature: bool = True
    requires_encryption: bool = True

    # Timing
    effective_start: datetime = Field(default_factory=datetime.now)
    effective_end: Optional[datetime] = None

    # Metadata
    created_by: str = "system"
    version: str = "1.0"


# ============================================================================
# Import validation from node_models
# ============================================================================

# Re-export key types for convenience
from .node_models import (
    FederationImportValidation,
    RedactionLevel,
    FederationArtifactType,
)


# ============================================================================
# Export Helper Functions
# ============================================================================

__all__ = [
    # Federation Artifacts
    "FederatedArtifact",
    "FederatedPattern",
    "FederatedBenchmark",
    "FederatedInsight",
    "FederatedRecommendation",
    # Metadata
    "FederationMetadata",
    "SharingScope",
    # Requests/Responses
    "FederationExportRequest",
    "FederationExportResponse",
    "FederationImportRequest",
    "FederationImportResponse",
    # Links and Policies
    "FederationLink",
    "FederationLinkStatus",
    "FederationPolicy",
    # Re-exports
    "FederationImportValidation",
    "RedactionLevel",
    "FederationArtifactType",
]
