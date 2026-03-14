"""
Request Validation Models

Phase 1B - Pydantic models for validating API request bodies.
Ensures requests match the shared TypeScript contracts.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ============================================================================
# Identity Validation Request Models
# ============================================================================

class ValidateIdentityRequest(BaseModel):
    """Request model for validate-identity endpoint."""
    nodeId: str = Field(..., min_length=1, description="Node ID to validate")
    credentials: Optional["CredentialsInput"] = Field(None, description="Optional presented credentials")
    options: Optional["ValidationOptions"] = Field(None, description="Validation options")

    @field_validator("nodeId")
    @classmethod
    def strip_node_id(cls, v: str) -> str:
        """Strip whitespace from node ID."""
        return v.strip()


class CredentialsInput(BaseModel):
    """Credentials input for validation."""
    keyId: str = Field(..., description="Key identifier")
    publicKey: str = Field(..., description="Public key (Base64)")


class ValidationOptions(BaseModel):
    """Options for validation operations."""
    requireActive: Optional[bool] = Field(True, description="Check if node is active")
    verifyCredentials: Optional[bool] = Field(True, description="Verify credentials match registration")


# ============================================================================
# Signature Verification Request Models
# ============================================================================

class VerifySignatureRequest(BaseModel):
    """Request model for verify-signature endpoint."""
    envelope: "EnvelopeInput" = Field(..., description="Envelope containing signature to verify")
    options: Optional["SignatureVerificationOptions"] = Field(None, description="Verification options")


class EnvelopeInput(BaseModel):
    """Envelope input for API requests."""
    envelopeId: str = Field(..., min_length=1)
    protocolVersion: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    sourceNodeId: str = Field(..., min_length=1)
    targetNodeId: Optional[str] = None
    sentAt: str = Field(...)  # ISO 8601 datetime
    artifact: "ArtifactInput"
    signature: "SignatureInput"
    trace: "TraceInput"

    @field_validator("sentAt")
    @classmethod
    def parse_datetime(cls, v: str) -> str:
        """Ensure sentAt is a valid ISO 8601 datetime."""
        try:
            # Try parsing to validate format
            datetime.fromisoformat(v.replace("Z", "+00:00"))
            return v
        except ValueError:
            raise ValueError("sentAt must be a valid ISO 8601 datetime")


class ArtifactInput(BaseModel):
    """Artifact payload input."""
    artifactId: str = Field(..., min_length=1)
    artifactType: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    claimText: str = Field(..., min_length=1)
    summary: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    provenanceScore: Optional[float] = Field(None, ge=0.0, le=1.0)
    originLayer: str = Field(..., pattern=r"^layer\d+$")
    originInsightId: Optional[str] = None
    context: dict[str, Any] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class SignatureInput(BaseModel):
    """Signature input for API requests."""
    algorithm: str = Field(..., description="Signature algorithm (ED25519, RSA-2048, etc.)")
    signerNodeId: str = Field(..., min_length=1)
    signatureValue: str = Field(..., min_length=1)
    signedAt: str = Field(...)  # ISO 8601 datetime

    @field_validator("signedAt")
    @classmethod
    def parse_datetime(cls, v: str) -> str:
        """Ensure signedAt is a valid ISO 8601 datetime."""
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
            return v
        except ValueError:
            raise ValueError("signedAt must be a valid ISO 8601 datetime")

    @field_validator("algorithm")
    @classmethod
    def normalize_algorithm(cls, v: str) -> str:
        """Normalize algorithm name to uppercase."""
        return v.upper().strip()


class TraceInput(BaseModel):
    """Federation trace input."""
    messageId: str = Field(..., min_length=1)
    hopCount: int = Field(..., ge=0)
    priorNodeIds: list[str] = Field(default_factory=list)
    correlationId: Optional[str] = None


class SignatureVerificationOptions(BaseModel):
    """Options for signature verification."""
    clockToleranceSeconds: Optional[int] = Field(300, ge=0, description="Clock skew tolerance in seconds")
    skipTimestampCheck: Optional[bool] = Field(False, description="Skip timestamp validation")
    skipHashCheck: Optional[bool] = Field(False, description="Skip payload hash verification")


# ============================================================================
# Trust Evaluation Request Models
# ============================================================================

class EvaluateInboundTrustRequest(BaseModel):
    """Request model for evaluate-inbound-trust endpoint."""
    envelope: EnvelopeInput = Field(..., description="Envelope to evaluate")
    preComputed: Optional["PreComputedValidations"] = Field(None, description="Optional pre-computed validations")
    options: Optional["EvaluationOptions"] = Field(None, description="Evaluation options")


class PreComputedValidations(BaseModel):
    """Pre-computed validation results to skip re-computation."""
    identityValidation: Optional[dict] = None
    signatureVerification: Optional[dict] = None


class EvaluationOptions(BaseModel):
    """Options for trust evaluation."""
    skipIdentityCheck: Optional[bool] = Field(False, description="Skip identity validation")
    skipSignatureCheck: Optional[bool] = Field(False, description="Skip signature verification")
    forceTrustScore: Optional[float] = Field(None, ge=0.0, le=1.0, description="Override trust score (testing only)")


# ============================================================================
# Node Registration Models
# ============================================================================

class RegisterNodeRequest(BaseModel):
    """Request model for registering a new node."""
    credentials: CredentialsInput = Field(..., description="Node credentials to register")
    trustTier: Optional[str] = Field("unknown", description="Initial trust tier")
    isActive: Optional[bool] = Field(True, description="Start node as active")


# ============================================================================
# Query Models
# ============================================================================

class GetNodeTrustProfileRequest(BaseModel):
    """Request model for getting node trust profile."""
    nodeId: str = Field(..., min_length=1)


class ListNodesRequest(BaseModel):
    """Request model for listing nodes."""
    status: Optional[str] = None
    trustTier: Optional[str] = None
    offset: Optional[int] = Field(0, ge=0)
    limit: Optional[int] = Field(50, ge=1, le=1000)


# ============================================================================
# Claim Processing Request Models
# ============================================================================

class ProcessInboundClaimOptions(BaseModel):
    """Options for claim processing."""
    skipReplayCheck: Optional[bool] = Field(False, description="Skip replay protection check")
    skipDuplicateCheck: Optional[bool] = Field(False, description="Skip duplicate suppression check")
    forceAccept: Optional[bool] = Field(False, description="Force acceptance regardless of validation (testing only)")


class ProcessInboundClaimRequest(BaseModel):
    """Request model for processing an inbound claim."""
    envelope: EnvelopeInput = Field(..., description="The claim envelope to process")
    options: Optional[ProcessInboundClaimOptions] = Field(None, description="Processing options")


# ============================================================================
# Publish Claim Request Models
# ============================================================================

class ArtifactDraftInput(BaseModel):
    """Artifact draft input for publication."""
    artifactId: Optional[str] = Field(None, description="Artifact ID (generated if null)")
    artifactType: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    claimText: str = Field(..., min_length=1)
    summary: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    provenanceScore: Optional[float] = Field(None, ge=0.0, le=1.0)
    originLayer: str = Field(..., pattern=r"^layer\d+$")
    originInsightId: Optional[str] = None
    context: dict[str, Any] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class PublishClaimOptions(BaseModel):
    """Options for claim publication."""
    signatureAlgorithm: Optional[str] = Field("ED25519", description="Signature algorithm")
    includeTrace: Optional[bool] = Field(True, description="Include federation trace")
    dispatchImmediately: Optional[bool] = Field(True, description="Dispatch to target immediately")


class PublishClaimRequest(BaseModel):
    """Request model for publishing a federated claim."""
    draft: ArtifactDraftInput = Field(..., description="Artifact draft to publish")
    targetNodeId: str = Field(..., min_length=1, description="Target node ID")
    options: Optional[PublishClaimOptions] = Field(None, description="Publication options")


# ============================================================================
# Two-Node Harness Request Models
# ============================================================================

class TestNodeConfigInput(BaseModel):
    """Test node configuration input."""
    nodeId: str = Field(..., min_length=1)
    keyId: str = Field(..., min_length=1)
    publicKey: str = Field(..., min_length=1)
    trustTier: Optional[str] = Field("trusted")
    baselineTrustScore: Optional[float] = Field(0.8, ge=0.0, le=1.0)
    isActive: Optional[bool] = Field(True)


class RunTestScenarioRequest(BaseModel):
    """Request to run a test scenario."""
    scenarioName: Literal["trusted_exchange", "low_trust_sender", "replay_attack", "duplicate_content", "contradiction"] = Field(
        ...,
        description="Scenario to run"
    )
    draft: ArtifactDraftInput = Field(..., description="Claim to test with")


# ============================================================================
# Update forward references
# ============================================================================

# Update forward references
ValidateIdentityRequest.model_rebuild()
VerifySignatureRequest.model_rebuild()
EnvelopeInput.model_rebuild()
EvaluateInboundTrustRequest.model_rebuild()
ProcessInboundClaimRequest.model_rebuild()
PublishClaimRequest.model_rebuild()
RunTestScenarioRequest.model_rebuild()
