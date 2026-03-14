"""
TORQ Console Layer 12: Federation

Phase 1B - Federated claim exchange and identity verification.

This module provides:
- Federated claim envelope types
- Identity validation and signature verification
- Trust-based inbound decision making
- Node registry and credential management
- Inbound claim processing pipeline
- Replay protection
- Duplicate suppression
"""

from torq_console.layer12.federation.types import (
    FederatedClaimEnvelope,
    FederatedArtifactPayload,
    ArtifactSignature,
    FederationTrace,
    NodeCredentials,
    NodeTrustProfile,
    IdentityValidationResult,
    SignatureVerificationResult,
    InboundTrustDecision,
)

from torq_console.layer12.federation.config import (
    FederationConfig,
    TrustThresholds,
    NodeRegistryConfig,
    SignatureConfig,
    default_config,
)

from torq_console.layer12.federation.errors import (
    FederationError,
    IdentityValidationError,
    SignatureVerificationError,
    TrustEvaluationError,
    UnknownNodeError,
    QuarantineException,
    ProtocolVersionError,
    ReplayAttackError,
    DuplicateSuppressionError,
)

from torq_console.layer12.federation.federation_identity_guard import (
    FederationIdentityGuard,
    create_identity_guard,
)

from torq_console.layer12.federation.inbound_claim_processor import (
    InboundFederatedClaimProcessor,
    ClaimProcessingResult,
    ProcessorConfig,
    create_inbound_claim_processor,
)

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

from torq_console.layer12.federation.outbound_publisher import (
    OutboundClaimPublisher,
    ArtifactDraft,
    PublishTarget,
    PublishResult,
    PublishOptions,
    PublisherConfig,
    create_outbound_publisher,
)

from torq_console.layer12.federation.exchange_tracker import (
    ExchangeTrackerService,
    ExchangeEventType,
    ExchangeEvent,
    ExchangeTrace,
    ExchangeTrackerConfig,
    get_exchange_tracker,
    create_exchange_tracker,
)

from torq_console.layer12.federation.two_node_harness import (
    TwoNodeFederationHarness,
    TestNodeConfig,
    TestScenario,
    TestScenarios,
    create_two_node_harness,
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
    "TrustThresholds",
    "NodeRegistryConfig",
    "SignatureConfig",
    "default_config",
    # Errors
    "FederationError",
    "IdentityValidationError",
    "SignatureVerificationError",
    "TrustEvaluationError",
    "UnknownNodeError",
    "QuarantineException",
    "ProtocolVersionError",
    "ReplayAttackError",
    "DuplicateSuppressionError",
    # Core Services
    "FederationIdentityGuard",
    "create_identity_guard",
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
    # Outbound
    "OutboundClaimPublisher",
    "ArtifactDraft",
    "PublishTarget",
    "PublishResult",
    "PublishOptions",
    "PublisherConfig",
    "create_outbound_publisher",
    # Tracking
    "ExchangeTrackerService",
    "ExchangeEventType",
    "ExchangeEvent",
    "ExchangeTrace",
    "ExchangeTrackerConfig",
    "get_exchange_tracker",
    "create_exchange_tracker",
    # Testing
    "TwoNodeFederationHarness",
    "TestNodeConfig",
    "TestScenario",
    "TestScenarios",
    "create_two_node_harness",
]

__version__ = "1.0.0"
__phase__ = "1B"
