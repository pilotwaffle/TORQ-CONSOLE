"""
Federation Layer Configuration

Phase 1B - Configuration settings for federation operations.
"""

from typing import Literal
from typing_extensions import TypeAlias
from pydantic import BaseModel, Field, field_validator


# Protocol versioning
FEDERATION_PROTOCOL_VERSION = "1.0.0"
SUPPORTED_PROTOCOL_VERSIONS = ["1.0.0"]

# Decision outcome type
DecisionOutcome: TypeAlias = Literal["accept", "quarantine", "reject", "reject_and_flag"]

# Signature algorithms
SUPPORTED_SIGNATURE_ALGORITHMS = ["ED25519", "RSA-2048", "RSA-4096", "ECDSA-P256", "SIMULATED"]

# Trust thresholds
TRUST_THRESHOLD_ACCEPT = 0.75
TRUST_THRESHOLD_QUARANTINE_MIN = 0.45
TRUST_THRESHOLD_QUARANTINE_MAX = 0.74
TRUST_THRESHOLD_REJECT = 0.45

# Signature validity
SIGNATURE_TOLERANCE_SECONDS = 300  # 5 minutes clock skew allowed


class TrustThresholds(BaseModel):
    """Trust score thresholds for decision making."""

    accept_min: float = Field(
        default=TRUST_THRESHOLD_ACCEPT,
        ge=0.0,
        le=1.0,
        description="Minimum trust score for automatic acceptance"
    )
    quarantine_min: float = Field(
        default=TRUST_THRESHOLD_QUARANTINE_MIN,
        ge=0.0,
        le=1.0,
        description="Minimum trust score for quarantine (below this is reject)"
    )
    quarantine_max: float = Field(
        default=TRUST_THRESHOLD_QUARANTINE_MAX,
        ge=0.0,
        le=1.0,
        description="Maximum trust score for quarantine (above this is accept)"
    )

    @field_validator("quarantine_max")
    @classmethod
    def validate_quarantine_range(cls, v: float, info) -> float:
        """Ensure quarantine_max is greater than quarantine_min."""
        if "quarantine_min" in info.data and v <= info.data["quarantine_min"]:
            raise ValueError("quarantine_max must be greater than quarantine_min")
        return v


class NodeRegistryConfig(BaseModel):
    """Configuration for node registry operations."""

    allow_unknown_nodes: bool = Field(
        default=False,
        description="Whether to accept claims from unknown nodes"
    )
    require_active_status: bool = Field(
        default=True,
        description="Whether nodes must be active to send claims"
    )
    unknown_node_default_trust: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Default trust score for unknown nodes"
    )


class SignatureConfig(BaseModel):
    """Configuration for signature verification."""

    supported_algorithms: list[str] = Field(
        default_factory=lambda: SUPPORTED_SIGNATURE_ALGORITHMS.copy(),
        description="List of supported signature algorithms"
    )
    clock_tolerance_seconds: int = Field(
        default=SIGNATURE_TOLERANCE_SECONDS,
        ge=0,
        description="Allowed clock skew in seconds"
    )
    require_signature: bool = Field(
        default=True,
        description="Whether signatures are required on all envelopes"
    )


class FederationConfig(BaseModel):
    """Main configuration for the federation layer."""

    protocol_version: str = Field(
        default=FEDERATION_PROTOCOL_VERSION,
        description="Current federation protocol version"
    )
    supported_protocol_versions: list[str] = Field(
        default_factory=lambda: SUPPORTED_PROTOCOL_VERSIONS.copy(),
        description="List of supported protocol versions"
    )

    trust_thresholds: TrustThresholds = Field(
        default_factory=TrustThresholds,
        description="Trust score thresholds for decisions"
    )
    node_registry: NodeRegistryConfig = Field(
        default_factory=NodeRegistryConfig,
        description="Node registry configuration"
    )
    signature: SignatureConfig = Field(
        default_factory=SignatureConfig,
        description="Signature verification configuration"
    )

    def get_trust_decision(self, trust_score: float) -> DecisionOutcome:
        """Get decision outcome based on trust score."""
        if trust_score >= self.trust_thresholds.accept_min:
            return "accept"
        if self.trust_thresholds.quarantine_min <= trust_score <= self.trust_thresholds.quarantine_max:
            return "quarantine"
        return "reject"

    def is_protocol_version_supported(self, version: str) -> bool:
        """Check if a protocol version is supported."""
        return version in self.supported_protocol_versions

    def is_algorithm_supported(self, algorithm: str) -> bool:
        """Check if a signature algorithm is supported."""
        return algorithm in self.signature.supported_algorithms


# Default configuration instance
default_config = FederationConfig()
