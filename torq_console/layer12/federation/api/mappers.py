"""
API Response Mappers

Phase 1B - Convert internal Python models to API wire payloads matching shared TypeScript contracts.
"""

from datetime import datetime
from typing import Any

from torq_console.layer12.federation.types import (
    IdentityValidationResult as InternalIdentityResult,
    SignatureVerificationResult as InternalSignatureResult,
    InboundTrustDecision as InternalTrustDecision,
    FederatedClaimEnvelope,
    NodeCredentials,
    NodeTrustProfile,
)
from torq_console.layer12.federation.errors import FederationError


# ============================================================================
# API Response Models (matching shared TypeScript contracts)
# ============================================================================

def create_success_response(data: Any, request_id: str = None, processing_ms: float = 0) -> dict:
    """Create a standardized success API response."""
    return {
        "status": "success",
        "data": data,
        "meta": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "requestId": request_id or _generate_request_id(),
            "processingDurationMs": processing_ms,
            "apiVersion": "1.0.0",
        }
    }


def create_error_response(
    code: str,
    message: str,
    details: dict = None,
    status_code: int = 400
) -> dict:
    """Create a standardized error API response."""
    return {
        "status": "error",
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
        "meta": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "requestId": _generate_request_id(),
            "processingDurationMs": 0,
            "apiVersion": "1.0.0",
        },
    }, status_code


# ============================================================================
# Mappers: Internal Models → API Response Shapes
# ============================================================================

def map_identity_validation_result(
    internal: InternalIdentityResult
) -> dict:
    """Map internal IdentityValidationResult to API response shape."""
    return {
        "isValid": internal.is_valid,
        "nodeId": internal.node_id,
        "reasons": internal.reasons,
        "isRegistered": internal.is_registered,
        "isActive": internal.is_active,
        "credentialsMatch": internal.credentials_match,
    }


def map_signature_verification_result(
    internal: InternalSignatureResult
) -> dict:
    """Map internal SignatureVerificationResult to API response shape."""
    result = {
        "isValid": internal.is_valid,
        "algorithmSupported": internal.algorithm_supported,
        "signerMatchesSource": internal.signer_matches_source,
        "timestampValid": internal.timestamp_valid,
        "payloadHashMatches": internal.payload_hash_matches,
        "reasons": internal.reasons,
    }
    # Add algorithm if available from context
    # (This would be passed in from the caller in a full implementation)
    return result


def map_inbound_trust_decision(
    internal: InternalTrustDecision
) -> dict:
    """Map internal InboundTrustDecision to extended API response shape."""
    base = {
        "decision": internal.decision,
        "reasons": internal.reasons,
        "nodeTrustScore": internal.node_trust_score,
        "identityValid": internal.identity_valid,
        "signatureValid": internal.signature_valid,
        "nodeId": internal.node_id,
        "envelopeId": internal.envelope_id,
        "decidedAt": internal.decided_at.isoformat() if isinstance(internal.decided_at, datetime) else str(internal.decided_at),
        "metadata": internal.metadata or {},
    }

    # Add computed properties
    decision = internal.decision
    base.update({
        "shouldProceed": decision == "accept",
        "requiresQuarantine": decision == "quarantine",
        "isRejection": decision in ("reject", "reject_and_flag"),
        "requiresFlagging": decision == "reject_and_flag",
    })

    return base


def map_node_trust_profile(internal: NodeTrustProfile) -> dict:
    """Map internal NodeTrustProfile to API response shape."""
    return {
        "nodeId": internal.node_id,
        "baselineTrustScore": internal.baseline_trust_score,
        "trustTier": internal.trust_tier,
        "successfulExchanges": internal.successful_exchanges,
        "failedExchanges": internal.failed_exchanges,
        "lastUpdated": internal.last_updated.isoformat() if isinstance(internal.last_updated, datetime) else str(internal.last_updated),
        "isTrusted": internal.is_trusted,
        "isQuarantined": internal.is_quarantined,
    }


def map_envelope_to_dict(envelope: FederatedClaimEnvelope) -> dict:
    """Map FederatedClaimEnvelope to dictionary for API response."""
    return {
        "envelopeId": envelope.envelope_id,
        "protocolVersion": envelope.protocol_version,
        "sourceNodeId": envelope.source_node_id,
        "targetNodeId": envelope.target_node_id,
        "sentAt": envelope.sent_at.isoformat() if isinstance(envelope.sent_at, datetime) else str(envelope.sent_at),
        "artifact": {
            "artifactId": envelope.artifact.artifact_id,
            "artifactType": envelope.artifact.artifact_type,
            "title": envelope.artifact.title,
            "claimText": envelope.artifact.claim_text,
            "summary": envelope.artifact.summary,
            "confidence": envelope.artifact.confidence,
            "provenanceScore": envelope.artifact.provenance_score,
            "originLayer": envelope.artifact.origin_layer,
            "originInsightId": envelope.artifact.origin_insight_id,
            "context": envelope.artifact.context,
            "limitations": envelope.artifact.limitations,
            "tags": envelope.artifact.tags,
        },
        "signature": {
            "algorithm": envelope.signature.algorithm,
            "signerNodeId": envelope.signature.signer_node_id,
            "signatureValue": envelope.signature.signature_value,
            "signedAt": envelope.signature.signed_at.isoformat() if isinstance(envelope.signature.signed_at, datetime) else str(envelope.signature.signed_at),
        },
        "trace": {
            "messageId": envelope.trace.message_id,
            "hopCount": envelope.trace.hop_count,
            "priorNodeIds": envelope.trace.prior_node_ids,
            "correlationId": envelope.trace.correlation_id,
        },
    }


def map_node_credentials_to_dict(credentials: NodeCredentials) -> dict:
    """Map NodeCredentials to dictionary for API response."""
    return {
        "nodeId": credentials.node_id,
        "keyId": credentials.key_id,
        "publicKey": credentials.public_key,
        "trustTier": credentials.trust_tier,
        "isActive": credentials.is_active,
        "registeredAt": credentials.registered_at.isoformat() if credentials.registered_at else None,
        "lastSeen": credentials.last_seen.isoformat() if credentials.last_seen else None,
    }


# ============================================================================
# Error Code Mapping
# ============================================================================

def map_federation_error_to_response(error: FederationError) -> tuple[dict, int]:
    """Map a FederationError to API error response with status code."""
    error_code = _get_error_code(error)
    status_code = _get_status_code_for_error(error_code)

    error_response = {
        "code": error_code,
        "message": error.message,
        "details": error.details,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    return create_error_response(error_code, error.message, error.details, status_code)


def _get_error_code(error: FederationError) -> str:
    """Get the error code for a FederationError."""
    error_type = type(error).__name__

    # Map exception types to error codes
    error_code_map = {
        "IdentityValidationError": "IDENTITY_VALIDATION_FAILED",
        "SignatureVerificationError": "SIGNATURE_VERIFICATION_FAILED",
        "TrustEvaluationError": "TRUST_EVALUATION_FAILED",
        "UnknownNodeError": "UNKNOWN_NODE",
        "QuarantineException": "QUARANTINE",
        "ProtocolVersionError": "UNSUPPORTED_PROTOCOL_VERSION",
        "ReplayAttackError": "REPLAY_ATTACK_DETECTED",
        "DuplicateSuppressionError": "DUPLICATE_CLAIM",
    }

    return error_code_map.get(error_type, "IDENTITY_VALIDATION_FAILED")


def _get_status_code_for_error(error_code: str) -> int:
    """Map error code to HTTP status code."""
    status_code_map = {
        "IDENTITY_VALIDATION_FAILED": 400,
        "SIGNATURE_VERIFICATION_FAILED": 400,
        "TRUST_EVALUATION_FAILED": 400,
        "UNKNOWN_NODE": 404,
        "QUARANTINE": 403,
        "UNSUPPORTED_PROTOCOL_VERSION": 426,
        "REPLAY_ATTACK_DETECTED": 403,
        "DUPLICATE_CLAIM": 409,
    }

    return status_code_map.get(error_code, 400)


# ============================================================================
# Request Validation Helpers
# ============================================================================

def validate_node_id(node_id: str) -> None:
    """Validate that a node ID is present and non-empty."""
    if not node_id or not node_id.strip():
        raise ValueError("node_id is required and cannot be empty")


def validate_envelope_id(envelope_id: str) -> None:
    """Validate that an envelope ID is present and non-empty."""
    if not envelope_id or not envelope_id.strip():
        raise ValueError("envelope_id is required and cannot be empty")


def validate_protocol_version(version: str, supported_versions: list[str] = None) -> None:
    """Validate that a protocol version is supported."""
    if supported_versions and version not in supported_versions:
        from torq_console.layer12.federation.errors import ProtocolVersionError
        raise ProtocolVersionError(
            f"Unsupported protocol version: {version}",
            details={
                "requestedVersion": version,
                "supportedVersions": supported_versions or ["1.0.0"]
            }
        )


# ============================================================================
# Utilities
# ============================================================================

def _generate_request_id() -> str:
    """Generate a unique request ID."""
    import uuid
    return f"req_{uuid.uuid4().hex[:16]}"


def calculate_processing_duration(start_time: datetime) -> float:
    """Calculate processing duration in milliseconds."""
    return (datetime.utcnow() - start_time).total_seconds() * 1000
