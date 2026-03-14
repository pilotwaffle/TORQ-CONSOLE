"""
Federation API Routes

Phase 1B - FastAPI endpoints for federation layer operations.
These routes expose FederationIdentityGuard functionality to the browser console.
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from torq_console.layer12.federation.federation_identity_guard import (
    FederationIdentityGuard,
    create_identity_guard,
)
from torq_console.layer12.federation.config import default_config
from torq_console.layer12.federation.types import (
    FederatedClaimEnvelope,
    NodeCredentials,
)
from torq_console.layer12.federation.errors import (
    FederationError,
    UnknownNodeError,
    ReplayAttackError,
    DuplicateSuppressionError,
)
from . import mappers
from .validation import (
    ValidateIdentityRequest,
    VerifySignatureRequest,
    EvaluateInboundTrustRequest,
    RegisterNodeRequest,
    GetNodeTrustProfileRequest,
    ListNodesRequest,
    ProcessInboundClaimRequest,
    PublishClaimRequest,
    RunTestScenarioRequest,
)

logger = logging.getLogger(__name__)

# Create router with prefix
router = APIRouter(prefix="/api/l12/federation", tags=["federation"])

# Global identity guard instance (would be initialized properly in production)
_guard: FederationIdentityGuard = create_identity_guard(config=default_config)

# Global claim processor instance (lazy loaded)
_processor = None

# Global publisher instance (lazy loaded)
_publisher = None

# Global exchange tracker instance
from torq_console.layer12.federation.exchange_tracker import get_exchange_tracker


def get_guard() -> FederationIdentityGuard:
    """Get the global identity guard instance."""
    return _guard


def get_processor():
    """Get or create the global claim processor instance."""
    global _processor
    if _processor is None:
        from torq_console.layer12.federation.inbound_claim_processor import create_inbound_claim_processor
        _processor = create_inbound_claim_processor(identity_guard=_guard)
    return _processor


def get_publisher():
    """Get or create the global publisher instance."""
    global _publisher
    if _publisher is None:
        from torq_console.layer12.federation.outbound_publisher import create_outbound_publisher, PublisherConfig
        from torq_console.layer12.federation.types import NodeCredentials

        # Create default credentials for the local node
        credentials = NodeCredentials(
            node_id="local_node",
            key_id="local_key",
            public_key="local_pubkey",
            trust_tier="trusted",
            is_active=True,
        )
        _publisher = create_outbound_publisher(
            credentials=credentials,
            config=PublisherConfig(local_node_id="local_node", enable_dispatch=False),
        )
    return _publisher


# ============================================================================
# Identity Validation Endpoint
# ============================================================================

@router.post("/validate-identity", response_model=None)
async def validate_identity(
    request: Request,
    body: ValidateIdentityRequest,
) -> JSONResponse:
    """
    Validate a node's identity credentials.

    Checks:
    - Node ID exists and is registered
    - Node is active
    - Credentials match registration
    - Protocol version is supported

    Returns:
        IdentityValidationResult with validation status
    """
    start_time = datetime.utcnow()
    request_id = mappers._generate_request_id()

    try:
        guard = get_guard()

        # Create NodeCredentials from request
        credentials = NodeCredentials(
            node_id=request.nodeId,
            key_id=request.credentials.keyId if request.credentials else "",
            public_key=request.credentials.publicKey if request.credentials else "",
        )

        # Validate identity
        result = await guard.validate_node_identity(
            node_id=request.nodeId,
            credentials=credentials,
        )

        # Map to API response shape
        data = mappers.map_identity_validation_result(result)
        processing_ms = mappers.calculate_processing_duration(start_time)

        response = mappers.create_success_response(
            data=data,
            request_id=request_id,
            processing_ms=processing_ms,
        )

        return JSONResponse(content=response)

    except FederationError as e:
        error_response, status_code = mappers.map_federation_error_to_response(e)
        return JSONResponse(content=error_response, status_code=status_code)

    except Exception as e:
        logger.exception(f"Unexpected error in validate-identity: {e}")
        error_response, status_code = mappers.create_error_response(
            code="IDENTITY_VALIDATION_FAILED",
            message="An unexpected error occurred",
            details={"error": str(e)},
            status_code=500,
        )
        return JSONResponse(content=error_response, status_code=status_code)


# ============================================================================
# Signature Verification Endpoint
# ============================================================================

@router.post("/verify-signature", response_model=None)
async def verify_signature(
    request: Request,
    body: VerifySignatureRequest,
) -> JSONResponse:
    """
    Verify the signature on a federated claim envelope.

    Checks:
    - Signature exists and is well-formed
    - Signer node matches source node
    - Signature timestamp is valid
    - Payload hash matches signature
    - Algorithm is supported

    Returns:
        SignatureVerificationResult with verification status
    """
    start_time = datetime.utcnow()
    request_id = mappers._generate_request_id()

    try:
        guard = get_guard()

        # Convert EnvelopeInput to FederatedClaimEnvelope
        envelope = _convert_envelope_input(body.envelope)

        # Verify signature
        result = await guard.verify_artifact_signature(envelope)

        # Map to API response shape
        data = mappers.map_signature_verification_result(result)
        processing_ms = mappers.calculate_processing_duration(start_time)

        response = mappers.create_success_response(
            data=data,
            request_id=request_id,
            processing_ms=processing_ms,
        )

        return JSONResponse(content=response)

    except FederationError as e:
        error_response, status_code = mappers.map_federation_error_to_response(e)
        return JSONResponse(content=error_response, status_code=status_code)

    except Exception as e:
        logger.exception(f"Unexpected error in verify-signature: {e}")
        error_response, status_code = mappers.create_error_response(
            code="SIGNATURE_VERIFICATION_FAILED",
            message="An unexpected error occurred",
            details={"error": str(e)},
            status_code=500,
        )
        return JSONResponse(content=error_response, status_code=status_code)


# ============================================================================
# Inbound Trust Evaluation Endpoint
# ============================================================================

@router.post("/evaluate-inbound-trust", response_model=None)
async def evaluate_inbound_trust(
    request: Request,
    body: EvaluateInboundTrustRequest,
) -> JSONResponse:
    """
    Evaluate whether to accept, quarantine, or reject an inbound claim.

    Combines:
    - Identity validation
    - Signature verification
    - Trust baseline evaluation

    Returns:
        Extended InboundTrustDecision with decision outcome
    """
    start_time = datetime.utcnow()
    request_id = mappers._generate_request_id()

    try:
        guard = get_guard()

        # Convert EnvelopeInput to FederatedClaimEnvelope
        envelope = _convert_envelope_input(body.envelope)

        # Evaluate trust
        decision = await guard.evaluate_inbound_trust(
            envelope=envelope,
            presented_credentials=None,  # Use registered credentials
        )

        # Map to extended API response shape
        data = mappers.map_inbound_trust_decision(decision)
        processing_ms = mappers.calculate_processing_duration(start_time)

        response = mappers.create_success_response(
            data=data,
            request_id=request_id,
            processing_ms=processing_ms,
        )

        return JSONResponse(content=response)

    except FederationError as e:
        error_response, status_code = mappers.map_federation_error_to_response(e)
        return JSONResponse(content=error_response, status_code=status_code)

    except Exception as e:
        logger.exception(f"Unexpected error in evaluate-inbound-trust: {e}")
        error_response, status_code = mappers.create_error_response(
            code="TRUST_EVALUATION_FAILED",
            message="An unexpected error occurred",
            details={"error": str(e)},
            status_code=500,
        )
        return JSONResponse(content=error_response, status_code=status_code)


# ============================================================================
# Node Management Endpoints
# ============================================================================

@router.post("/nodes/register", response_model=None)
async def register_node(
    request: Request,
    body: RegisterNodeRequest,
) -> JSONResponse:
    """Register a new node in the federation."""
    start_time = datetime.utcnow()
    request_id = mappers._generate_request_id()

    try:
        guard = get_guard()

        # Create NodeCredentials
        credentials = NodeCredentials(
            node_id=body.credentials.nodeId,
            key_id=body.credentials.keyId,
            public_key=body.credentials.publicKey,
            trust_tier=body.trustTier,
            is_active=body.isActive,
        )

        # Register the node
        guard.register_node(credentials)

        data = {
            "success": True,
            "nodeId": credentials.node_id,
        }
        processing_ms = mappers.calculate_processing_duration(start_time)

        response = mappers.create_success_response(
            data=data,
            request_id=request_id,
            processing_ms=processing_ms,
        )

        return JSONResponse(content=response)

    except Exception as e:
        logger.exception(f"Unexpected error in register-node: {e}")
        error_response, status_code = mappers.create_error_response(
            code="IDENTITY_VALIDATION_FAILED",
            message="Failed to register node",
            details={"error": str(e)},
            status_code=500,
        )
        return JSONResponse(content=error_response, status_code=status_code)


@router.get("/nodes/{node_id}/trust-profile", response_model=None)
async def get_node_trust_profile(
    request: Request,
    node_id: str,
) -> JSONResponse:
    """Get the trust profile for a specific node."""
    start_time = datetime.utcnow()
    request_id = mappers._generate_request_id()

    try:
        guard = get_guard()

        # Get trust profile
        profile = await guard.get_node_trust_baseline(node_id)

        data = mappers.map_node_trust_profile(profile)
        processing_ms = mappers.calculate_processing_duration(start_time)

        response = mappers.create_success_response(
            data=data,
            request_id=request_id,
            processing_ms=processing_ms,
        )

        return JSONResponse(content=response)

    except UnknownNodeError as e:
        error_response, status_code = mappers.map_federation_error_to_response(e)
        return JSONResponse(content=error_response, status_code=status_code)

    except Exception as e:
        logger.exception(f"Unexpected error in get-node-trust-profile: {e}")
        error_response, status_code = mappers.create_error_response(
            code="TRUST_EVALUATION_FAILED",
            message="Failed to get node trust profile",
            details={"error": str(e)},
            status_code=500,
        )
        return JSONResponse(content=error_response, status_code=status_code)


@router.get("/nodes", response_model=None)
async def list_nodes(
    request: Request,
    status: str | None = None,
    trust_tier: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> JSONResponse:
    """List registered nodes with optional filtering."""
    start_time = datetime.utcnow()
    request_id = mappers._generate_request_id()

    try:
        guard = get_guard()

        # Get nodes from registry
        nodes_list = []
        for node_id, creds in guard._node_registry.items():
            # Apply filters
            if status and creds.is_active != (status == "active"):
                continue
            if trust_tier and creds.trust_tier != trust_tier:
                continue

            # Get trust profile
            profile = guard._trust_profiles.get(node_id)
            trust_score = profile.baseline_trust_score if profile else 0.0

            nodes_list.append({
                "nodeId": creds.node_id,
                "trustTier": creds.trust_tier or "unknown",
                "status": "active" if creds.is_active else "inactive",
                "baselineTrustScore": trust_score,
                "lastSeen": creds.last_seen.isoformat() if creds.last_seen else None,
            })

        # Apply pagination
        total = len(nodes_list)
        paginated = nodes_list[offset:offset + limit]

        data = {
            "nodes": paginated,
            "total": total,
        }
        processing_ms = mappers.calculate_processing_duration(start_time)

        response = mappers.create_success_response(
            data=data,
            request_id=request_id,
            processing_ms=processing_ms,
        )

        return JSONResponse(content=response)

    except Exception as e:
        logger.exception(f"Unexpected error in list-nodes: {e}")
        error_response, status_code = mappers.create_error_response(
            code="IDENTITY_VALIDATION_FAILED",
            message="Failed to list nodes",
            details={"error": str(e)},
            status_code=500,
        )
        return JSONResponse(content=error_response, status_code=status_code)


# ============================================================================
# Claim Processing Endpoint
# ============================================================================

@router.post("/process-inbound-claim", response_model=None)
async def process_inbound_claim(
    request: Request,
    body: ProcessInboundClaimRequest,
) -> JSONResponse:
    """
    Process an inbound federated claim through the full pipeline.

    This is the authoritative endpoint for all inbound federation claims.
    It orchestrates:
    - Identity validation
    - Signature verification
    - Replay protection
    - Duplicate suppression
    - Trust evaluation
    - Persistence (when enabled)
    - Qualification (when enabled)
    - Contradiction detection (when enabled)
    - Audit logging

    Returns:
        ClaimProcessingResult with complete processing outcome
    """
    start_time = datetime.utcnow()
    request_id = mappers._generate_request_id()

    try:
        processor = get_processor()

        # Convert EnvelopeInput to FederatedClaimEnvelope
        envelope = _convert_envelope_input(body.envelope)

        # Process the claim
        result = await processor.process_claim(
            envelope=envelope,
            skip_replay_check=body.options.skipReplayCheck if body.options else False,
            skip_duplicate_check=body.options.skipDuplicateCheck if body.options else False,
            force_accept=body.options.forceAccept if body.options else False,
        )

        # Convert result to dict
        data = result.to_dict()
        processing_ms = mappers.calculate_processing_duration(start_time)

        response = mappers.create_success_response(
            data=data,
            request_id=request_id,
            processing_ms=processing_ms,
        )

        return JSONResponse(content=response)

    except ReplayAttackError as e:
        # Replay attacks should return 403 Forbidden
        error_response, status_code = mappers.create_error_response(
            code="REPLAY_ATTACK",
            message=e.message,
            details=e.details if hasattr(e, 'details') else {},
            status_code=403,
        )
        return JSONResponse(content=error_response, status_code=status_code)

    except DuplicateSuppressionError as e:
        # Duplicates might return 409 Conflict
        error_response, status_code = mappers.create_error_response(
            code="DUPLICATE_CLAIM",
            message=e.message,
            details=e.details if hasattr(e, 'details') else {},
            status_code=409,
        )
        return JSONResponse(content=error_response, status_code=status_code)

    except FederationError as e:
        error_response, status_code = mappers.map_federation_error_to_response(e)
        return JSONResponse(content=error_response, status_code=status_code)

    except Exception as e:
        logger.exception(f"Unexpected error in process-inbound-claim: {e}")
        error_response, status_code = mappers.create_error_response(
            code="CLAIM_PROCESSING_FAILED",
            message="An unexpected error occurred while processing the claim",
            details={"error": str(e)},
            status_code=500,
        )
        return JSONResponse(content=error_response, status_code=status_code)


# ============================================================================
# Processor Statistics Endpoint
# ============================================================================

@router.get("/processor/statistics", response_model=None)
async def get_processor_statistics(request: Request) -> JSONResponse:
    """Get statistics from the claim processor."""
    request_id = mappers._generate_request_id()

    try:
        processor = get_processor()
        stats = processor.get_statistics()

        response = mappers.create_success_response(
            data=stats,
            request_id=request_id,
        )

        return JSONResponse(content=response)

    except Exception as e:
        logger.exception(f"Unexpected error in get-processor-statistics: {e}")
        error_response, status_code = mappers.create_error_response(
            code="STATISTICS_ERROR",
            message="Failed to get processor statistics",
            details={"error": str(e)},
            status_code=500,
        )
        return JSONResponse(content=error_response, status_code=status_code)


# ============================================================================
# Publish Claim Endpoint
# ============================================================================

@router.post("/publish-claim", response_model=None)
async def publish_claim(
    request: Request,
    body: PublishClaimRequest,
) -> JSONResponse:
    """
    Publish a federated claim to a target node.

    This endpoint creates a signed claim envelope and prepares it for
    transmission to the target node.

    Pipeline:
    1. Validate artifact draft
    2. Create FederatedArtifactPayload
    3. Create signature
    4. Create federation trace
    5. Assemble envelope
    6. Persist outbound record
    7. Return envelope for dispatch

    Returns:
        PublishResult with envelope ID, signature status, and trace info
    """
    start_time = datetime.utcnow()
    request_id = mappers._generate_request_id()

    try:
        publisher = get_publisher()

        # Convert request to ArtifactDraft
        from torq_console.layer12.federation.outbound_publisher import ArtifactDraft

        draft = ArtifactDraft(
            artifact_id=body.draft.artifactId,
            artifact_type=body.draft.artifactType,
            title=body.draft.title,
            claim_text=body.draft.claimText,
            summary=body.draft.summary,
            confidence=body.draft.confidence,
            provenance_score=body.draft.provenanceScore,
            origin_layer=body.draft.originLayer,
            origin_insight_id=body.draft.originInsightId,
            context=body.draft.context,
            limitations=body.draft.limitations,
            tags=body.draft.tags,
        )

        # Convert options
        from torq_console.layer12.federation.outbound_publisher import PublishOptions

        options = PublishOptions(
            signature_algorithm=body.options.signatureAlgorithm if body.options else "ED25519",
            include_trace=body.options.includeTrace if body.options else True,
            dispatch_immediately=body.options.dispatchImmediately if body.options else True,
        )

        # Publish the claim
        result = await publisher.publish_claim(
            draft=draft,
            target_node_id=body.targetNodeId,
            options=options,
        )

        # Convert result to dict
        data = {
            "success": result.success,
            "envelopeId": result.envelope_id,
            "correlationId": result.correlation_id,
            "messageId": result.message_id,
            "publishedAt": result.published_at.isoformat(),
            "targetNodeId": result.target_node_id,
            "signatureStatus": result.signature_status,
            "dispatchStatus": result.dispatch_status,
            "errorMessage": result.error_message,
            "envelope": result.envelope.model_dump() if result.envelope else None,
        }

        processing_ms = mappers.calculate_processing_duration(start_time)

        response = mappers.create_success_response(
            data=data,
            request_id=request_id,
            processing_ms=processing_ms,
        )

        return JSONResponse(content=response)

    except Exception as e:
        logger.exception(f"Unexpected error in publish-claim: {e}")
        error_response, status_code = mappers.create_error_response(
            code="CLAIM_PUBLISH_FAILED",
            message="Failed to publish claim",
            details={"error": str(e)},
            status_code=500,
        )
        return JSONResponse(content=error_response, status_code=status_code)


# ============================================================================
# Exchange Trace Endpoint
# ============================================================================

@router.get("/exchange-trace/{correlation_id}", response_model=None)
async def get_exchange_trace(
    request: Request,
    correlation_id: str,
) -> JSONResponse:
    """
    Get the complete exchange trace for a correlation ID.

    Returns the full lifecycle of a federated claim exchange:
    - Published (Node A creates and sends)
    - In Transit (network transport)
    - Received (Node B receives)
    - Processing (Node B validates)
    - Completed (final disposition)

    Returns:
        ExchangeTrace with full event timeline
    """
    request_id = mappers._generate_request_id()

    try:
        tracker = get_exchange_tracker()
        trace = tracker.get_exchange_trace(correlation_id)

        if trace is None:
            error_response, status_code = mappers.create_error_response(
                code="TRACE_NOT_FOUND",
                message=f"Exchange trace not found for correlation ID: {correlation_id}",
                status_code=404,
            )
            return JSONResponse(content=error_response, status_code=status_code)

        response = mappers.create_success_response(
            data=trace.to_dict(),
            request_id=request_id,
        )

        return JSONResponse(content=response)

    except Exception as e:
        logger.exception(f"Unexpected error in get-exchange-trace: {e}")
        error_response, status_code = mappers.create_error_response(
            code="TRACE_ERROR",
            message="Failed to get exchange trace",
            details={"error": str(e)},
            status_code=500,
        )
        return JSONResponse(content=error_response, status_code=status_code)


# ============================================================================
# Health/Status Endpoint (Enhanced)
# ============================================================================

@router.get("/status", response_model=None)
async def get_federation_status(request: Request) -> JSONResponse:
    """Get the current status of the federation layer."""
    request_id = mappers._generate_request_id()

    guard = get_guard()
    processor = get_processor()

    # Get processor statistics
    processor_stats = processor.get_statistics()

    data = {
        "protocolVersion": "1.0.0",
        "nodeId": "local",  # Would be actual node ID in production
        "activeConnections": len(guard._node_registry),
        "totalClaimsProcessed": processor_stats.get("totalProcessed", 0),
        "totalClaimsAccepted": processor_stats.get("acceptedCount", 0),
        "totalClaimsQuarantined": processor_stats.get("quarantinedCount", 0),
        "totalClaimsRejected": processor_stats.get("rejectedCount", 0),
        "uptimeSeconds": processor_stats.get("uptimeSeconds", 0),
        "health": {
            "identityService": True,
            "signatureVerification": True,
            "trustEvaluation": True,
            "nodeRegistry": len(guard._node_registry) > 0,
            "replayProtection": processor.config.enable_replay_protection,
            "duplicateSuppression": processor.config.enable_duplicate_suppression,
        },
        "performance": {
            "avgValidationTimeMs": 50.0,  # Placeholder
            "p95ValidationTimeMs": 100.0,  # Placeholder
            "claimsPerSecond": 0.0,  # Placeholder
            "memoryUsageMB": 128.0,  # Placeholder
        },
    }

    response = mappers.create_success_response(
        data=data,
        request_id=request_id,
    )

    return JSONResponse(content=response)


# ============================================================================
# Helper Functions
# ============================================================================

def _convert_envelope_input(envelope_input) -> FederatedClaimEnvelope:
    """Convert EnvelopeInput to FederatedClaimEnvelope."""
    from torq_console.layer12.federation.types import (
        FederatedArtifactPayload,
        ArtifactSignature,
        FederationTrace,
    )

    # Parse datetime strings
    sent_at = datetime.fromisoformat(envelope_input.sentAt.replace("Z", "+00:00"))
    signed_at = datetime.fromisoformat(envelope_input.signature.signedAt.replace("Z", "+00:00"))

    return FederatedClaimEnvelope(
        envelope_id=envelope_input.envelopeId,
        protocol_version=envelope_input.protocolVersion,
        source_node_id=envelope_input.sourceNodeId,
        target_node_id=envelope_input.targetNodeId,
        sent_at=sent_at,
        artifact=FederatedArtifactPayload(
            artifact_id=envelope_input.artifact.artifactId,
            artifact_type=envelope_input.artifact.artifactType,
            title=envelope_input.artifact.title,
            claim_text=envelope_input.artifact.claimText,
            summary=envelope_input.artifact.summary,
            confidence=envelope_input.artifact.confidence,
            provenance_score=envelope_input.artifact.provenanceScore,
            origin_layer=envelope_input.artifact.originLayer,
            origin_insight_id=envelope_input.artifact.originInsightId,
            context=envelope_input.artifact.context,
            limitations=envelope_input.artifact.limitations,
            tags=envelope_input.artifact.tags,
        ),
        signature=ArtifactSignature(
            algorithm=envelope_input.signature.algorithm,
            signer_node_id=envelope_input.signature.signerNodeId,
            signature_value=envelope_input.signature.signatureValue,
            signed_at=signed_at,
        ),
        trace=FederationTrace(
            message_id=envelope_input.trace.messageId,
            hop_count=envelope_input.trace.hopCount,
            prior_node_ids=envelope_input.trace.priorNodeIds,
            correlation_id=envelope_input.trace.correlationId,
        ),
    )


# ============================================================================
# Router Export
# ============================================================================

def get_router() -> APIRouter:
    """Get the federation API router."""
    return router
