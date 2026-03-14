"""
Federation Layer Type Definitions

Phase 1B - Canonical data models for federated claim exchange.
"""

from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator


class FederatedArtifactPayload(BaseModel):
    """The core insight/artifact being federated."""

    artifact_id: str = Field(..., description="Unique identifier for this artifact")
    artifact_type: str = Field(..., description="Type of artifact (e.g., 'insight', 'pattern', 'strategy')")
    title: str = Field(..., description="Human-readable title")
    claim_text: str = Field(..., description="The core claim or assertion")
    summary: str | None = Field(None, description="Optional summary of the claim")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    provenance_score: float | None = Field(None, ge=0.0, le=1.0, description="Provenance reliability score")
    origin_layer: str = Field(..., description="Origin layer within source node (e.g., 'layer4')")
    origin_insight_id: str | None = Field(None, description="Original insight ID if applicable")
    context: dict[str, Any] = Field(default_factory=dict, description="Additional context metadata")
    limitations: list[str] = Field(default_factory=list, description="Known limitations")
    tags: list[str] = Field(default_factory=list, description="Categorization tags")

    @field_validator("artifact_type")
    @classmethod
    def normalize_artifact_type(cls, v: str) -> str:
        """Normalize artifact type to lowercase."""
        return v.lower().strip()


class ArtifactSignature(BaseModel):
    """Cryptographic signature for an artifact."""

    algorithm: str = Field(..., description="Signature algorithm used")
    signer_node_id: str = Field(..., description="Node ID that created the signature")
    signature_value: str = Field(..., description="Base64-encoded signature value")
    signed_at: datetime = Field(..., description="When the signature was created")

    @field_validator("algorithm")
    @classmethod
    def normalize_algorithm(cls, v: str) -> str:
        """Normalize algorithm name to uppercase."""
        return v.upper().strip()


class FederationTrace(BaseModel):
    """Trace information for federated message routing."""

    message_id: str = Field(..., description="Unique message identifier")
    hop_count: int = Field(default=0, ge=0, description="Number of hops this message has taken")
    prior_node_ids: list[str] = Field(default_factory=list, description="IDs of prior nodes in route")
    correlation_id: str | None = Field(None, description="Optional correlation ID for request/response tracking")

    @field_validator("hop_count")
    @classmethod
    def validate_hop_count(cls, v: int, info) -> int:
        """Ensure hop_count matches prior_node_ids length."""
        if "prior_node_ids" in info.data and v != len(info.data["prior_node_ids"]):
            raise ValueError("hop_count must equal length of prior_node_ids")
        return v


class FederatedClaimEnvelope(BaseModel):
    """Complete envelope for a federated claim."""

    envelope_id: str = Field(..., description="Unique identifier for this envelope")
    protocol_version: str = Field(..., description="Federation protocol version")
    source_node_id: str = Field(..., description="Node ID sending this claim")
    target_node_id: str | None = Field(None, description="Target node ID (None for broadcast)")
    sent_at: datetime = Field(..., description="When the envelope was sent")
    artifact: FederatedArtifactPayload = Field(..., description="The artifact payload")
    signature: ArtifactSignature = Field(..., description="Artifact signature")
    trace: FederationTrace = Field(..., description="Federation trace information")

    @field_validator("source_node_id")
    @classmethod
    def validate_source_node_id(cls, v: str) -> str:
        """Normalize and validate source node ID."""
        if not v or not v.strip():
            raise ValueError("source_node_id cannot be empty")
        return v.strip()

    @field_validator("protocol_version")
    @classmethod
    def validate_protocol_version(cls, v: str) -> str:
        """Normalize protocol version."""
        return v.strip()


class NodeCredentials(BaseModel):
    """Registered credentials for a federated node."""

    node_id: str = Field(..., description="Unique node identifier")
    key_id: str = Field(..., description="Key identifier")
    public_key: str = Field(..., description="Public key for signature verification")
    trust_tier: str | None = Field(None, description="Trust tier (e.g., 'trusted', 'verified', 'unknown')")
    is_active: bool = Field(default=True, description="Whether the node is currently active")
    registered_at: datetime | None = Field(None, description="When the node was registered")
    last_seen: datetime | None = Field(None, description="Last activity timestamp")

    @field_validator("node_id")
    @classmethod
    def validate_node_id(cls, v: str) -> str:
        """Normalize node ID."""
        if not v or not v.strip():
            raise ValueError("node_id cannot be empty")
        return v.strip()


class NodeTrustProfile(BaseModel):
    """Trust profile for a node."""

    node_id: str = Field(..., description="Node identifier")
    baseline_trust_score: float = Field(..., ge=0.0, le=1.0, description="Baseline trust score")
    trust_tier: str = Field(default="unknown", description="Trust tier classification")
    successful_exchanges: int = Field(default=0, ge=0, description="Count of successful exchanges")
    failed_exchanges: int = Field(default=0, ge=0, description="Count of failed exchanges")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last profile update")
    is_trusted: bool = Field(default=False, description="Whether node is in trusted set")
    is_quarantined: bool = Field(default=False, description="Whether node is quarantined")

    @property
    def total_exchanges(self) -> int:
        """Total number of exchanges with this node."""
        return self.successful_exchanges + self.failed_exchanges

    @property
    def success_rate(self) -> float:
        """Success rate for exchanges with this node."""
        if self.total_exchanges == 0:
            return 0.0
        return self.successful_exchanges / self.total_exchanges


class IdentityValidationResult(BaseModel):
    """Result of node identity validation."""

    is_valid: bool = Field(..., description="Whether identity is valid")
    node_id: str = Field(..., description="Node ID that was validated")
    reasons: list[str] = Field(default_factory=list, description="Validation failure reasons")
    is_registered: bool = Field(default=False, description="Whether node is registered")
    is_active: bool = Field(default=False, description="Whether node is active")
    credentials_match: bool = Field(default=False, description="Whether credentials match registration")


class SignatureVerificationResult(BaseModel):
    """Result of artifact signature verification."""

    is_valid: bool = Field(..., description="Whether signature is valid")
    algorithm_supported: bool = Field(default=True, description="Whether algorithm is supported")
    signer_matches_source: bool = Field(default=False, description="Whether signer matches source node")
    timestamp_valid: bool = Field(default=True, description="Whether signature timestamp is valid")
    payload_hash_matches: bool = Field(default=False, description="Whether payload hash matches")
    reasons: list[str] = Field(default_factory=list, description="Verification failure reasons")


class InboundTrustDecision(BaseModel):
    """Decision on whether to accept an inbound claim."""

    decision: Literal["accept", "quarantine", "reject", "reject_and_flag"] = Field(
        ...,
        description="Trust decision outcome"
    )
    reasons: list[str] = Field(default_factory=list, description="Reasons for the decision")
    node_trust_score: float = Field(..., ge=0.0, le=1.0, description="Trust score of source node")
    identity_valid: bool = Field(default=False, description="Whether identity validation passed")
    signature_valid: bool = Field(default=False, description="Whether signature verification passed")
    node_id: str = Field(..., description="Source node ID")
    envelope_id: str = Field(..., description="Envelope ID being decided")
    decided_at: datetime = Field(default_factory=datetime.utcnow, description="When decision was made")

    @property
    def should_proceed(self) -> bool:
        """Whether the envelope should proceed to processing."""
        return self.decision == "accept"

    @property
    def requires_quarantine(self) -> bool:
        """Whether the envelope should be quarantined."""
        return self.decision == "quarantine"

    @property
    def is_rejection(self) -> bool:
        """Whether the envelope was rejected."""
        return self.decision in ("reject", "reject_and_flag")

    @property
    def requires_flagging(self) -> bool:
        """Whether the rejection requires flagging."""
        return self.decision == "reject_and_flag"
