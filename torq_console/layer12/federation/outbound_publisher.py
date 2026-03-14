"""
Outbound Claim Publisher for Federation Layer

Phase 1B - Publish federated claims to other nodes.

This module handles the outbound side of federation:
- Creating signed claim envelopes
- Attaching federation trace metadata
- Dispatching envelopes to target nodes
- Tracking publish status and results
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Literal
from pydantic import BaseModel, Field

from torq_console.layer12.federation.config import FederationConfig, FEDERATION_PROTOCOL_VERSION
from torq_console.layer12.federation.types import (
    FederatedClaimEnvelope,
    FederatedArtifactPayload,
    ArtifactSignature,
    FederationTrace,
    NodeCredentials,
)
from torq_console.layer12.federation.errors import FederationError

logger = logging.getLogger(__name__)


# ============================================================================
# Publishing Types
# ============================================================================

class ArtifactDraft(BaseModel):
    """Draft artifact for publication."""

    artifact_id: str | None = Field(None, description="Artifact ID (generated if null)")
    artifact_type: str = Field(..., description="Type of artifact")
    title: str = Field(..., description="Human-readable title")
    claim_text: str = Field(..., description="The core claim or assertion")
    summary: str | None = Field(None, description="Optional summary")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    provenance_score: float | None = Field(None, ge=0.0, le=1.0)
    origin_layer: str = Field(..., description="Origin layer (e.g., 'layer4')")
    origin_insight_id: str | None = Field(None, description="Original insight ID")
    context: dict[str, Any] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class PublishTarget(BaseModel):
    """Target node for publication."""

    node_id: str
    endpoint: str | None = None  # Transport endpoint
    trust_required: bool = True


class PublishResult(BaseModel):
    """Result of a publish operation."""

    success: bool
    envelope_id: str
    correlation_id: str
    message_id: str
    published_at: datetime
    target_node_id: str
    signature_status: Literal["signed", "pending", "failed"]
    dispatch_status: Literal["dispatched", "queued", "failed"]
    error_message: str | None = None
    envelope: FederatedClaimEnvelope | None = None


class PublishOptions(BaseModel):
    """Options for claim publication."""

    signature_algorithm: str = Field("ED25519", description="Signature algorithm to use")
    include_trace: bool = Field(True, description="Include federation trace")
    dispatch_immediately: bool = Field(True, description="Dispatch to target immediately")
    ttl_seconds: int | None = Field(None, description="Time-to-live for the envelope")


# ============================================================================
# Publisher Configuration
# ============================================================================

class PublisherConfig(BaseModel):
    """Configuration for the outbound publisher."""

    local_node_id: str = Field(..., description="This node's ID")
    default_signature_algorithm: str = Field("ED25519", description="Default signing algorithm")
    signature_ttl_seconds: int = Field(300, ge=0, description="Signature validity window")
    trace_hop_limit: int = Field(10, ge=1, description="Maximum hops before rejection")
    enable_payload_persistence: bool = Field(True, description="Persist outbound payloads")
    enable_dispatch: bool = Field(True, description="Enable actual dispatch (vs test mode)")


# ============================================================================
# Federation Trace Manager
# ============================================================================

class FederationTraceManager:
    """
    Manages federation trace metadata for outbound envelopes.

    The trace tracks the path of a message through the federation:
    - message_id: Unique message identifier
    - correlation_id: Groups related messages (request/response)
    - hop_count: Number of nodes this message has passed through
    - prior_node_ids: Ordered list of prior nodes in the path
    """

    def __init__(self, config: PublisherConfig | None = None):
        self.config = config or PublisherConfig(local_node_id="local")
        self.logger = logging.getLogger(__name__)

    def create_trace(
        self,
        correlation_id: str | None = None,
        prior_node_ids: list[str] | None = None,
    ) -> FederationTrace:
        """
        Create a new federation trace for an outbound message.

        Args:
            correlation_id: Optional correlation ID for request/response tracking
            prior_node_ids: Ordered list of prior nodes (for forwarded messages)

        Returns:
            FederationTrace for the outbound message
        """
        import uuid

        message_id = f"msg_{uuid.uuid4().hex}"
        hop_count = len(prior_node_ids or [])

        trace = FederationTrace(
            message_id=message_id,
            hop_count=hop_count,
            prior_node_ids=prior_node_ids or [],
            correlation_id=correlation_id,
        )

        self.logger.debug(
            f"Created federation trace: message_id={message_id}, "
            f"hop_count={hop_count}, correlation_id={correlation_id}"
        )

        return trace

    def validate_trace(self, trace: FederationTrace) -> tuple[bool, str | None]:
        """
        Validate a federation trace for acceptance.

        Args:
            trace: The trace to validate

        Returns:
            Tuple of (is_valid, reason_if_invalid)
        """
        # Check hop count limit
        if trace.hop_count >= self.config.trace_hop_limit:
            return False, f"Hop count {trace.hop_count} exceeds limit {self.config.trace_hop_limit}"

        # Check for loops (same node appearing twice)
        if len(trace.prior_node_ids) != len(set(trace.prior_node_ids)):
            return False, "Loop detected in prior_node_ids"

        return True, None

    def extend_trace(
        self,
        trace: FederationTrace,
        adding_node_id: str,
    ) -> FederationTrace:
        """
        Extend a trace with the current node.

        Args:
            trace: Original trace
            adding_node_id: Node ID to add to the path

        Returns:
            Extended FederationTrace
        """
        return FederationTrace(
            message_id=trace.message_id,
            hop_count=trace.hop_count + 1,
            prior_node_ids=[*trace.prior_node_ids, adding_node_id],
            correlation_id=trace.correlation_id,
        )


# ============================================================================
# Signature Manager
# ============================================================================

class SignatureManager:
    """
    Manages outbound signature creation.

    Phase 1B: Simulated signatures (production would use actual crypto)
    Phase 1C: Real ED25519/RSA signatures
    """

    def __init__(self, credentials: NodeCredentials, config: PublisherConfig | None = None):
        """
        Initialize the signature manager.

        Args:
            credentials: This node's signing credentials
            config: Publisher configuration
        """
        self.credentials = credentials
        self.config = config or PublisherConfig(local_node_id=credentials.node_id)
        self.logger = logging.getLogger(__name__)

    def create_signature(
        self,
        artifact: FederatedArtifactPayload,
        algorithm: str | None = None,
    ) -> ArtifactSignature:
        """
        Create a signature for an artifact payload.

        Phase 1B: Uses simulated signatures
        Phase 1C: Will use actual cryptographic signing

        Args:
            artifact: The artifact to sign
            algorithm: Signature algorithm (uses config default if None)

        Returns:
            ArtifactSignature for the artifact
        """
        algorithm = algorithm or self.config.default_signature_algorithm
        signed_at = datetime.now(timezone.utc)

        # Phase 1B: Simulated signature
        # Phase 1C: Real cryptographic signature using:
        # - cryptography.hazmat.primitives.asymmetric.ed25519
        # - Or cryptography.hazmat.primitives.asymmetric.rsa
        import uuid
        signature_value = f"sig_{uuid.uuid4().hex}_{self.credentials.node_id}_{signed_at.isoformat()}"

        signature = ArtifactSignature(
            algorithm=algorithm,
            signer_node_id=self.credentials.node_id,
            signature_value=signature_value,
            signed_at=signed_at,
        )

        self.logger.debug(
            f"Created signature: algorithm={algorithm}, "
            f"signer={self.credentials.node_id}, artifact={artifact.artifact_id}"
        )

        return signature


# ============================================================================
# Outbound Claim Publisher
# ============================================================================

class OutboundClaimPublisher:
    """
    Publishes federated claims to other nodes.

    This is the authoritative outbound service for all federation
    publication. It coordinates artifact creation, signing, tracing,
    envelope construction, and dispatch.

    All outbound federation should flow through this publisher.
    """

    def __init__(
        self,
        credentials: NodeCredentials,
        config: PublisherConfig | None = None,
        federation_config: FederationConfig | None = None,
    ):
        """
        Initialize the outbound publisher.

        Args:
            credentials: This node's credentials for signing
            config: Publisher configuration
            federation_config: Federation layer configuration
        """
        self.credentials = credentials
        self.config = config or PublisherConfig(local_node_id=credentials.node_id)
        self.federation_config = federation_config
        self.trace_manager = FederationTraceManager(self.config)
        self.signature_manager = SignatureManager(credentials, self.config)
        self.logger = logging.getLogger(__name__)

        # Statistics
        self._total_published = 0
        self._total_dispatched = 0
        self._total_failed = 0
        self._publisher_started_at = datetime.utcnow()

        # Outbound registry (tracking published envelopes)
        self._published_envelopes: dict[str, FederatedClaimEnvelope] = {}

    async def publish_claim(
        self,
        draft: ArtifactDraft,
        target_node_id: str,
        options: PublishOptions | None = None,
    ) -> PublishResult:
        """
        Publish a claim to a target node.

        Pipeline:
        1. Validate draft
        2. Create FederatedArtifactPayload
        3. Create signature
        4. Create federation trace
        5. Assemble envelope
        6. Persist outbound record
        7. Dispatch to target

        Args:
            draft: The artifact draft to publish
            target_node_id: Target node ID
            options: Publishing options

        Returns:
            PublishResult with publication outcome
        """
        options = options or PublishOptions()
        published_at = datetime.utcnow(timezone.utc)

        # Generate IDs
        import uuid
        envelope_id = f"env_{uuid.uuid4().hex}"
        correlation_id = f"corr_{uuid.uuid4().hex}"

        # Generate artifact ID if not provided
        if not draft.artifact_id:
            draft.artifact_id = f"artifact_{uuid.uuid4().hex}"

        self.logger.info(
            f"Publishing claim: {envelope_id} → {target_node_id}, "
            f"artifact={draft.artifact_id}"
        )

        try:
            # Step 1: Create artifact payload
            artifact = FederatedArtifactPayload(
                artifact_id=draft.artifact_id,
                artifact_type=draft.artifact_type.lower(),
                title=draft.title,
                claim_text=draft.claim_text,
                summary=draft.summary,
                confidence=draft.confidence,
                provenance_score=draft.provenance_score,
                origin_layer=draft.origin_layer.lower(),
                origin_insight_id=draft.origin_insight_id,
                context=draft.context,
                limitations=draft.limitations,
                tags=draft.tags,
            )

            # Step 2: Create signature
            signature = self.signature_manager.create_signature(
                artifact=artifact,
                algorithm=options.signature_algorithm,
            )

            # Step 3: Create trace
            trace = self.trace_manager.create_trace(
                correlation_id=correlation_id,
                prior_node_ids=[],
            )

            # Step 4: Assemble envelope
            envelope = FederatedClaimEnvelope(
                envelope_id=envelope_id,
                protocol_version=FEDERATION_PROTOCOL_VERSION,
                source_node_id=self.credentials.node_id,
                target_node_id=target_node_id,
                sent_at=published_at,
                artifact=artifact,
                signature=signature,
                trace=trace,
            )

            # Step 5: Persist outbound record
            if self.config.enable_payload_persistence:
                self._published_envelopes[envelope_id] = envelope
                self.logger.debug(f"Persisted outbound envelope: {envelope_id}")

            # Step 6: Dispatch to target
            dispatch_status = "queued"
            if self.config.enable_dispatch and options.dispatch_immediately:
                await self._dispatch_envelope(envelope, target_node_id)
                dispatch_status = "dispatched"
                self._total_dispatched += 1
            else:
                self.logger.debug(f"Envelope queued (dispatch disabled): {envelope_id}")

            # Success
            self._total_published += 1

            return PublishResult(
                success=True,
                envelope_id=envelope_id,
                correlation_id=correlation_id,
                message_id=trace.message_id,
                published_at=published_at,
                target_node_id=target_node_id,
                signature_status="signed",
                dispatch_status=dispatch_status,  # type: ignore
                envelope=envelope,
            )

        except Exception as e:
            self._total_failed += 1
            self.logger.error(f"Failed to publish claim: {e}")

            return PublishResult(
                success=False,
                envelope_id=envelope_id,
                correlation_id=correlation_id,
                message_id="",
                published_at=published_at,
                target_node_id=target_node_id,
                signature_status="failed",
                dispatch_status="failed",  # type: ignore
                error_message=str(e),
                envelope=None,
            )

    async def _dispatch_envelope(
        self,
        envelope: FederatedClaimEnvelope,
        target_node_id: str,
    ) -> None:
        """
        Dispatch an envelope to a target node.

        Phase 1B: Simulated dispatch (logs the action)
        Phase 1C: Real HTTP/WebSocket transport via Layer 11

        Args:
            envelope: The envelope to dispatch
            target_node_id: Target node ID
        """
        # Phase 1B: Log the dispatch
        self.logger.info(
            f"Dispatching envelope {envelope.envelope_id} to node {target_node_id}"
        )

        # Phase 1C: Real dispatch via Layer 11 transport
        # Would integrate with:
        # - torq_console.layer11.federation_transport
        # - HTTP POST to target node's /api/l12/federation/process-inbound-claim
        # - WebSocket for real-time push

    def get_published_envelope(self, envelope_id: str) -> FederatedClaimEnvelope | None:
        """Get a previously published envelope by ID."""
        return self._published_envelopes.get(envelope_id)

    def get_statistics(self) -> dict[str, Any]:
        """Get publisher statistics."""
        uptime = (datetime.utcnow() - self._publisher_started_at).total_seconds()

        return {
            "totalPublished": self._total_published,
            "totalDispatched": self._total_dispatched,
            "totalFailed": self._total_failed,
            "dispatchRate": self._total_dispatched / max(self._total_published, 1),
            "uptimeSeconds": uptime,
            "publisherStartedAt": self._publisher_started_at.isoformat(),
            "trackedEnvelopes": len(self._published_envelopes),
        }


def create_outbound_publisher(
    credentials: NodeCredentials,
    config: PublisherConfig | None = None,
    federation_config: FederationConfig | None = None,
) -> OutboundClaimPublisher:
    """
    Factory function to create an OutboundClaimPublisher.

    Args:
        credentials: This node's signing credentials
        config: Publisher configuration
        federation_config: Federation layer configuration

    Returns:
        Configured OutboundClaimPublisher instance
    """
    return OutboundClaimPublisher(
        credentials=credentials,
        config=config,
        federation_config=federation_config,
    )
