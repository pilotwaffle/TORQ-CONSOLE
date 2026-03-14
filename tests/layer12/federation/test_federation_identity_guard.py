"""
Test Suite for FederationIdentityGuard

Phase 1B - Comprehensive tests for identity validation,
signature verification, and trust-based decision making.
"""

import pytest
from datetime import datetime, timedelta

from torq_console.layer12.federation.federation_identity_guard import (
    FederationIdentityGuard,
    create_identity_guard,
)
from torq_console.layer12.federation.types import (
    FederatedClaimEnvelope,
    FederatedArtifactPayload,
    ArtifactSignature,
    FederationTrace,
    NodeCredentials,
    NodeTrustProfile,
    InboundTrustDecision,
)
from torq_console.layer12.federation.config import FederationConfig
from torq_console.layer12.federation.errors import (
    UnknownNodeError,
    QuarantineException,
)


# ============================================================================
# FIXTURES (Module-level for use by all test classes)
# ============================================================================

@pytest.fixture
def sample_config() -> FederationConfig:
    """Create a sample federation configuration."""
    return FederationConfig()


@pytest.fixture
def trusted_node_credentials() -> NodeCredentials:
    """Create trusted node credentials."""
    return NodeCredentials(
        node_id="node-trusted-001",
        key_id="key-001",
        public_key="mock-public-key-trusted",
        trust_tier="trusted",
        is_active=True,
    )


@pytest.fixture
def unknown_node_credentials() -> NodeCredentials:
    """Create unknown node credentials."""
    return NodeCredentials(
        node_id="node-unknown-999",
        key_id="key-999",
        public_key="mock-public-key-unknown",
        trust_tier="unknown",
        is_active=True,
    )


@pytest.fixture
def trusted_node_profile() -> NodeTrustProfile:
    """Create a trusted node trust profile."""
    return NodeTrustProfile(
        node_id="node-trusted-001",
        baseline_trust_score=0.85,
        trust_tier="trusted",
        is_trusted=True,
        successful_exchanges=100,
        failed_exchanges=5,
    )


@pytest.fixture
def sample_envelope_trusted() -> FederatedClaimEnvelope:
    """Create a sample envelope from a trusted node."""
    return FederatedClaimEnvelope(
        envelope_id="env-001",
        protocol_version="1.0.0",
        source_node_id="node-trusted-001",
        target_node_id=None,
        sent_at=datetime.utcnow(),
        artifact=FederatedArtifactPayload(
            artifact_id="artifact-001",
            artifact_type="insight",
            title="Test Insight",
            claim_text="This is a test claim",
            confidence=0.9,
            origin_layer="layer4",
            origin_insight_id="insight-001",
        ),
        signature=ArtifactSignature(
            algorithm="ED25519",
            signer_node_id="node-trusted-001",
            signature_value="valid-signature-001-7ae71c0a11521b2b-mock",
            signed_at=datetime.utcnow(),
        ),
        trace=FederationTrace(
            message_id="msg-001",
            hop_count=0,
        ),
    )


@pytest.fixture
def sample_envelope_unknown() -> FederatedClaimEnvelope:
    """Create a sample envelope from an unknown node."""
    return FederatedClaimEnvelope(
        envelope_id="env-002",
        protocol_version="1.0.0",
        source_node_id="node-unknown-999",
        target_node_id=None,
        sent_at=datetime.utcnow(),
        artifact=FederatedArtifactPayload(
            artifact_id="artifact-002",
            artifact_type="insight",
            title="Unknown Node Insight",
            claim_text="This is from an unknown node",
            confidence=0.7,
            origin_layer="layer4",
        ),
        signature=ArtifactSignature(
            algorithm="ED25519",
            signer_node_id="node-unknown-999",
            signature_value="signature-unknown-mock",
            signed_at=datetime.utcnow(),
        ),
        trace=FederationTrace(
            message_id="msg-002",
            hop_count=0,
        ),
    )


@pytest.fixture
def sample_envelope_spoofed() -> FederatedClaimEnvelope:
    """Create a sample envelope with spoofed signature."""
    return FederatedClaimEnvelope(
        envelope_id="env-003",
        protocol_version="1.0.0",
        source_node_id="node-trusted-001",
        target_node_id=None,
        sent_at=datetime.utcnow(),
        artifact=FederatedArtifactPayload(
            artifact_id="artifact-003",
            artifact_type="insight",
            title="Spoofed Insight",
            claim_text="This signature is spoofed",
            confidence=0.8,
            origin_layer="layer4",
        ),
        signature=ArtifactSignature(
            algorithm="ED25519",
            signer_node_id="node-malicious-777",  # Different from source!
            signature_value="spoofed-signature",
            signed_at=datetime.utcnow(),
        ),
        trace=FederationTrace(
            message_id="msg-003",
            hop_count=0,
        ),
    )


@pytest.fixture
def sample_envelope_malformed_signature() -> FederatedClaimEnvelope:
    """Create a sample envelope with malformed signature."""
    return FederatedClaimEnvelope(
        envelope_id="env-004",
        protocol_version="1.0.0",
        source_node_id="node-trusted-001",
        target_node_id=None,
        sent_at=datetime.utcnow(),
        artifact=FederatedArtifactPayload(
            artifact_id="artifact-004",
            artifact_type="insight",
            title="Malformed Signature",
            claim_text="This signature is malformed",
            confidence=0.6,
            origin_layer="layer4",
        ),
        signature=ArtifactSignature(
            algorithm="ED25519",
            signer_node_id="node-trusted-001",
            signature_value="short",  # Too short to be valid
            signed_at=datetime.utcnow(),
        ),
        trace=FederationTrace(
            message_id="msg-004",
            hop_count=0,
        ),
    )


@pytest.fixture
def sample_envelope_old_signature() -> FederatedClaimEnvelope:
    """Create a sample envelope with expired signature timestamp."""
    old_time = datetime.utcnow() - timedelta(seconds=500)  # Older than tolerance
    return FederatedClaimEnvelope(
        envelope_id="env-005",
        protocol_version="1.0.0",
        source_node_id="node-trusted-001",
        target_node_id=None,
        sent_at=datetime.utcnow(),
        artifact=FederatedArtifactPayload(
            artifact_id="artifact-005",
            artifact_type="insight",
            title="Old Signature",
            claim_text="This signature timestamp is too old",
            confidence=0.75,
            origin_layer="layer4",
        ),
        signature=ArtifactSignature(
            algorithm="ED25519",
            signer_node_id="node-trusted-001",
            signature_value="valid-signature-005-93eb7e3ca4be01d9-mock",
            signed_at=old_time,
        ),
        trace=FederationTrace(
            message_id="msg-005",
            hop_count=0,
        ),
    )


@pytest.fixture
def identity_guard(
    sample_config: FederationConfig,
    trusted_node_credentials: NodeCredentials,
    trusted_node_profile: NodeTrustProfile,
) -> FederationIdentityGuard:
    """Create an identity guard with test data."""
    guard = FederationIdentityGuard(config=sample_config)
    guard.register_node(trusted_node_credentials)
    guard.register_trust_profile(trusted_node_profile)
    return guard


# ============================================================================
# TEST CLASSES
# ============================================================================

class TestIdentityValidation:
    """Test identity validation methods."""

    @pytest.mark.asyncio
    async def test_trusted_node_identity_valid(
        self,
        identity_guard: FederationIdentityGuard,
        trusted_node_credentials: NodeCredentials,
    ):
        """Test that a trusted node's identity is validated successfully."""
        result = await identity_guard.validate_node_identity(
            "node-trusted-001",
            trusted_node_credentials,
        )

        assert result.is_valid is True
        assert result.node_id == "node-trusted-001"
        assert result.is_registered is True
        assert result.is_active is True
        assert result.credentials_match is True
        assert len(result.reasons) == 0

    @pytest.mark.asyncio
    async def test_unknown_node_identity_not_registered(
        self,
        sample_config: FederationConfig,
        unknown_node_credentials: NodeCredentials,
    ):
        """Test that an unknown node is not registered."""
        guard = FederationIdentityGuard(config=sample_config)

        result = await guard.validate_node_identity(
            "node-unknown-999",
            unknown_node_credentials,
        )

        # With default config (unknown nodes not allowed)
        assert result.is_valid is False
        assert result.is_registered is False
        assert any("not in the registry" in r for r in result.reasons)

    @pytest.mark.asyncio
    async def test_inactive_node_identity_fails(
        self,
        sample_config: FederationConfig,
    ):
        """Test that an inactive node fails validation."""
        guard = FederationIdentityGuard(config=sample_config)
        inactive_creds = NodeCredentials(
            node_id="node-inactive-002",
            key_id="key-002",
            public_key="mock-key",
            is_active=False,  # Inactive
        )
        guard.register_node(inactive_creds)

        result = await guard.validate_node_identity(
            "node-inactive-002",
            inactive_creds,
        )

        assert result.is_valid is False
        assert result.is_active is False
        assert any("not active" in r for r in result.reasons)

    @pytest.mark.asyncio
    async def test_empty_node_id_fails_validation(self, identity_guard: FederationIdentityGuard):
        """Test that empty node ID fails validation."""
        result = await identity_guard.validate_node_identity(
            "",
            None,  # No credentials needed for empty node_id test
        )

        assert result.is_valid is False
        assert "missing or empty" in result.reasons[0]


class TestSignatureVerification:
    """Test signature verification methods."""

    @pytest.mark.asyncio
    async def test_valid_signature_accepted(
        self,
        identity_guard: FederationIdentityGuard,
        sample_envelope_trusted: FederatedClaimEnvelope,
    ):
        """Test that a valid signature is accepted."""
        result = await identity_guard.verify_artifact_signature(sample_envelope_trusted)

        assert result.is_valid is True
        assert result.algorithm_supported is True
        assert result.signer_matches_source is True
        assert result.timestamp_valid is True
        assert result.payload_hash_matches is True
        assert len(result.reasons) == 0

    @pytest.mark.asyncio
    async def test_spoofed_signature_detected(
        self,
        identity_guard: FederationIdentityGuard,
        sample_envelope_spoofed: FederatedClaimEnvelope,
    ):
        """Test that a spoofed signature is detected."""
        result = await identity_guard.verify_artifact_signature(sample_envelope_spoofed)

        assert result.is_valid is False
        assert result.signer_matches_source is False
        assert any("does not match" in r for r in result.reasons)

    @pytest.mark.asyncio
    async def test_malformed_signature_rejected(
        self,
        identity_guard: FederationIdentityGuard,
        sample_envelope_malformed_signature: FederatedClaimEnvelope,
    ):
        """Test that a malformed signature is rejected."""
        result = await identity_guard.verify_artifact_signature(sample_envelope_malformed_signature)

        assert result.is_valid is False
        assert result.payload_hash_matches is False

    @pytest.mark.asyncio
    async def test_expired_signature_timestamp_rejected(
        self,
        identity_guard: FederationIdentityGuard,
        sample_envelope_old_signature: FederatedClaimEnvelope,
    ):
        """Test that an expired signature timestamp is rejected."""
        result = await identity_guard.verify_artifact_signature(sample_envelope_old_signature)

        assert result.is_valid is False
        assert result.timestamp_valid is False
        assert any("out of range" in r for r in result.reasons)

    @pytest.mark.asyncio
    async def test_unsupported_algorithm_detected(
        self,
        identity_guard: FederationIdentityGuard,
        sample_envelope_trusted: FederatedClaimEnvelope,
    ):
        """Test that an unsupported algorithm is detected."""
        # Modify envelope to use unsupported algorithm
        envelope = sample_envelope_trusted.model_copy(
            deep=True,
            update={
                "signature": sample_envelope_trusted.signature.model_copy(
                    update={"algorithm": "UNSUPPORTED-ALG"}
                )
            },
        )

        result = await identity_guard.verify_artifact_signature(envelope)

        assert result.is_valid is False
        assert result.algorithm_supported is False
        assert any("not supported" in r for r in result.reasons)


class TestTrustBaseline:
    """Test trust baseline methods."""

    @pytest.mark.asyncio
    async def test_get_trusted_node_profile(
        self,
        identity_guard: FederationIdentityGuard,
        trusted_node_profile: NodeTrustProfile,
    ):
        """Test getting a trusted node's profile."""
        profile = await identity_guard.get_node_trust_baseline("node-trusted-001")

        assert profile.node_id == "node-trusted-001"
        assert profile.baseline_trust_score == 0.85
        assert profile.is_trusted is True
        assert profile.trust_tier == "trusted"

    @pytest.mark.asyncio
    async def test_unknown_node_raises_error(self, sample_config: FederationConfig):
        """Test that unknown node raises error when not allowed."""
        from torq_console.layer12.federation.config import NodeRegistryConfig

        guard = FederationIdentityGuard(
            config=sample_config.model_copy(
                update={"node_registry": NodeRegistryConfig(allow_unknown_nodes=False)}
            )
        )

        with pytest.raises(UnknownNodeError):
            await guard.get_node_trust_baseline("node-unknown-999")

    @pytest.mark.asyncio
    async def test_unknown_node_allowed_creates_profile(self, sample_config: FederationConfig):
        """Test that unknown nodes get default profile when allowed."""
        from torq_console.layer12.federation.config import NodeRegistryConfig

        guard = FederationIdentityGuard(
            config=sample_config.model_copy(
                update={"node_registry": NodeRegistryConfig(allow_unknown_nodes=True)}
            )
        )

        profile = await guard.get_node_trust_baseline("node-unknown-999")

        assert profile.node_id == "node-unknown-999"
        assert profile.baseline_trust_score == 0.0
        assert profile.is_trusted is False


class TestInboundTrustDecision:
    """Test unified inbound trust decision methods."""

    @pytest.mark.asyncio
    async def test_trusted_node_with_valid_signature_accepted(
        self,
        identity_guard: FederationIdentityGuard,
        sample_envelope_trusted: FederatedClaimEnvelope,
    ):
        """Test that trusted node with valid signature is accepted."""
        decision = await identity_guard.evaluate_inbound_trust(sample_envelope_trusted)

        assert decision.decision == "accept"
        assert decision.should_proceed is True
        assert decision.identity_valid is True
        assert decision.signature_valid is True
        assert decision.node_trust_score >= 0.75

    @pytest.mark.asyncio
    async def test_unknown_node_quarantined_or_rejected(
        self,
        identity_guard: FederationIdentityGuard,
        sample_envelope_unknown: FederatedClaimEnvelope,
    ):
        """Test that unknown node is quarantined or rejected."""
        decision = await identity_guard.evaluate_inbound_trust(sample_envelope_unknown)

        assert decision.decision in ("quarantine", "reject")
        assert decision.identity_valid is False or decision.node_trust_score < 0.45

    @pytest.mark.asyncio
    async def test_spoofed_signature_reject_and_flagged(
        self,
        identity_guard: FederationIdentityGuard,
        sample_envelope_spoofed: FederatedClaimEnvelope,
    ):
        """Test that spoofed signature triggers reject_and_flag."""
        decision = await identity_guard.evaluate_inbound_trust(sample_envelope_spoofed)

        assert decision.decision == "reject_and_flag"
        assert decision.requires_flagging is True
        assert decision.signature_valid is False

    @pytest.mark.asyncio
    async def test_malformed_signature_rejected(
        self,
        identity_guard: FederationIdentityGuard,
        sample_envelope_malformed_signature: FederatedClaimEnvelope,
    ):
        """Test that malformed signature is rejected."""
        decision = await identity_guard.evaluate_inbound_trust(sample_envelope_malformed_signature)

        assert decision.decision == "reject"
        assert decision.signature_valid is False

    @pytest.mark.asyncio
    async def test_expired_timestamp_rejected(
        self,
        identity_guard: FederationIdentityGuard,
        sample_envelope_old_signature: FederatedClaimEnvelope,
    ):
        """Test that expired timestamp causes rejection."""
        decision = await identity_guard.evaluate_inbound_trust(sample_envelope_old_signature)

        assert decision.decision == "reject"
        assert decision.signature_valid is False

    @pytest.mark.asyncio
    async def test_medium_trust_node_quarantined(
        self,
        sample_config: FederationConfig,
        trusted_node_credentials: NodeCredentials,
        sample_envelope_trusted: FederatedClaimEnvelope,
    ):
        """Test that medium trust node is quarantined."""
        guard = FederationIdentityGuard(config=sample_config)
        guard.register_node(trusted_node_credentials)

        # Register with medium trust score (in quarantine range)
        medium_profile = NodeTrustProfile(
            node_id="node-trusted-001",
            baseline_trust_score=0.6,  # In quarantine range (0.45-0.74)
            trust_tier="verified",
            is_trusted=False,
        )
        guard.register_trust_profile(medium_profile)

        decision = await guard.evaluate_inbound_trust(sample_envelope_trusted)

        assert decision.decision == "quarantine"
        assert decision.requires_quarantine is True

    @pytest.mark.asyncio
    async def test_low_trust_node_rejected(
        self,
        sample_config: FederationConfig,
        trusted_node_credentials: NodeCredentials,
        sample_envelope_trusted: FederatedClaimEnvelope,
    ):
        """Test that low trust node is rejected."""
        guard = FederationIdentityGuard(config=sample_config)
        guard.register_node(trusted_node_credentials)

        # Register with low trust score
        low_profile = NodeTrustProfile(
            node_id="node-trusted-001",
            baseline_trust_score=0.3,  # Below reject threshold (0.45)
            trust_tier="unknown",
            is_trusted=False,
        )
        guard.register_trust_profile(low_profile)

        decision = await guard.evaluate_inbound_trust(sample_envelope_trusted)

        assert decision.decision == "reject"


class TestFactoryFunctions:
    """Test factory functions and utilities."""

    def test_create_identity_guard(self, sample_config: FederationConfig):
        """Test factory function creates guard correctly."""
        guard = create_identity_guard(config=sample_config)

        assert isinstance(guard, FederationIdentityGuard)
        assert guard.config == sample_config

    def test_register_node_updates_registry(
        self,
        identity_guard: FederationIdentityGuard,
        trusted_node_credentials: NodeCredentials,
    ):
        """Test that registering a node updates the registry."""
        node_id = trusted_node_credentials.node_id

        assert node_id in identity_guard._node_registry
        assert identity_guard._node_registry[node_id] == trusted_node_credentials

    def test_register_trust_profile_updates_profiles(
        self,
        identity_guard: FederationIdentityGuard,
        trusted_node_profile: NodeTrustProfile,
    ):
        """Test that registering a profile updates the profiles."""
        node_id = trusted_node_profile.node_id

        assert node_id in identity_guard._trust_profiles
        assert identity_guard._trust_profiles[node_id] == trusted_node_profile


class TestDecisionProperties:
    """Test decision result properties."""

    def test_should_proceed_true_for_accept(self):
        """Test should_proceed is True for accept decision."""
        decision = InboundTrustDecision(
            decision="accept",
            reasons=["All checks passed"],
            node_trust_score=0.85,
            identity_valid=True,
            signature_valid=True,
            node_id="node-001",
            envelope_id="env-001",
        )

        assert decision.should_proceed is True
        assert decision.requires_quarantine is False
        assert decision.is_rejection is False
        assert decision.requires_flagging is False

    def test_requires_quarantine_true_for_quarantine(self):
        """Test requires_quarantine is True for quarantine decision."""
        decision = InboundTrustDecision(
            decision="quarantine",
            reasons=["Unknown node"],
            node_trust_score=0.0,
            identity_valid=False,
            signature_valid=False,
            node_id="node-999",
            envelope_id="env-002",
        )

        assert decision.should_proceed is False
        assert decision.requires_quarantine is True
        assert decision.is_rejection is False
        assert decision.requires_flagging is False

    def test_is_rejection_true_for_reject(self):
        """Test is_rejection is True for reject decision."""
        decision = InboundTrustDecision(
            decision="reject",
            reasons=["Invalid signature"],
            node_trust_score=0.0,
            identity_valid=True,
            signature_valid=False,
            node_id="node-001",
            envelope_id="env-003",
        )

        assert decision.should_proceed is False
        assert decision.requires_quarantine is False
        assert decision.is_rejection is True
        assert decision.requires_flagging is False

    def test_requires_flagging_true_for_reject_and_flag(self):
        """Test requires_flagging is True for reject_and_flag decision."""
        decision = InboundTrustDecision(
            decision="reject_and_flag",
            reasons=["Spoofed signature"],
            node_trust_score=0.0,
            identity_valid=True,
            signature_valid=False,
            node_id="node-001",
            envelope_id="env-004",
        )

        assert decision.should_proceed is False
        assert decision.requires_quarantine is False
        assert decision.is_rejection is True
        assert decision.requires_flagging is True
