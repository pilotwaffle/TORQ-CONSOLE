"""
TORQ Console Layer 12: Distributed Epistemic Layer

This layer provides:
- Federated claim exchange between nodes
- Identity verification and trust management
- Cross-node insight integration
- Distributed qualification and contradiction detection
"""

from torq_console.layer12.federation import (
    # Types
    FederatedClaimEnvelope,
    FederatedArtifactPayload,
    ArtifactSignature,
    FederationTrace,
    NodeCredentials,
    NodeTrustProfile,
    IdentityValidationResult,
    SignatureVerificationResult,
    InboundTrustDecision,
    # Config
    FederationConfig,
    default_config,
    # Errors
    FederationError,
    IdentityValidationError,
    SignatureVerificationError,
    TrustEvaluationError,
    UnknownNodeError,
    QuarantineException,
    ReplayAttackError,
    DuplicateSuppressionError,
)

# Processor exports
from torq_console.layer12.federation.inbound_claim_processor import (
    InboundFederatedClaimProcessor,
    ClaimProcessingResult,
    ProcessorConfig,
    create_inbound_claim_processor,
)

# Protection services
from torq_console.layer12.federation.replay_protection import (
    ReplayProtectionService,
    ReplayProtectionConfig,
    ReplayProtectionResult,
    create_replay_protection,
)

from torq_console.layer12.federation.duplicate_suppression import (
    DuplicateSuppressionService,
    DuplicateSuppressionConfig,
    DuplicateSuppressionResult,
    create_duplicate_suppression,
)

__all__ = [
    # Types
    "FederatedClaimEnvelope",
    "FederatedArtifactPayload",
    "ArtifactSignature",
    "FederationTrace",
    "NodeCredentials",
    "NodeTrustProfile",
    "IdentityValidationResult",
    "SignatureVerificationResult",
    "InboundTrustDecision",
    # Config
    "FederationConfig",
    "default_config",
    # Errors
    "FederationError",
    "IdentityValidationError",
    "SignatureVerificationError",
    "TrustEvaluationError",
    "UnknownNodeError",
    "QuarantineException",
    "ReplayAttackError",
    "DuplicateSuppressionError",
    # Processor
    "InboundFederatedClaimProcessor",
    "ClaimProcessingResult",
    "ProcessorConfig",
    "create_inbound_claim_processor",
    # Protection
    "ReplayProtectionService",
    "ReplayProtectionConfig",
    "ReplayProtectionResult",
    "create_replay_protection",
    "DuplicateSuppressionService",
    "DuplicateSuppressionConfig",
    "DuplicateSuppressionResult",
    "create_duplicate_suppression",
]
