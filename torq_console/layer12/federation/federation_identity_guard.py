"""
Federation Identity Guard

Phase 1B - Gatekeeper for inbound federated claims.

This module provides identity validation, signature verification,
and trust-based decision making for inbound claim envelopes.
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Literal

from torq_console.layer12.federation.config import FederationConfig, default_config
from torq_console.layer12.federation.types import (
    FederatedClaimEnvelope,
    NodeCredentials,
    NodeTrustProfile,
    IdentityValidationResult,
    SignatureVerificationResult,
    InboundTrustDecision,
)
from torq_console.layer12.federation.errors import (
    IdentityValidationError,
    SignatureVerificationError,
    UnknownNodeError,
    QuarantineException,
    ProtocolVersionError,
)

logger = logging.getLogger(__name__)


class FederationIdentityGuard:
    """
    Gatekeeper for inbound federated claims.

    Validates node identity, verifies signatures, and makes
    trust-based decisions on whether to accept, quarantine,
    or reject inbound claim envelopes.
    """

    def __init__(
        self,
        config: FederationConfig | None = None,
        node_registry: dict[str, NodeCredentials] | None = None,
        trust_profiles: dict[str, NodeTrustProfile] | None = None,
    ):
        """
        Initialize the identity guard.

        Args:
            config: Federation configuration
            node_registry: Known node credentials (node_id -> credentials)
            trust_profiles: Node trust profiles (node_id -> profile)
        """
        self.config = config or default_config
        self._node_registry = node_registry or {}
        self._trust_profiles = trust_profiles or {}
        self.logger = logging.getLogger(__name__)

    def register_node(self, credentials: NodeCredentials) -> None:
        """Register a node's credentials."""
        self._node_registry[credentials.node_id] = credentials
        self.logger.info(f"Registered node: {credentials.node_id}")

    def register_trust_profile(self, profile: NodeTrustProfile) -> None:
        """Register or update a node's trust profile."""
        self._trust_profiles[profile.node_id] = profile
        self.logger.info(f"Updated trust profile for: {profile.node_id} (score: {profile.baseline_trust_score})")

    async def validate_node_identity(
        self,
        node_id: str,
        credentials: NodeCredentials,
    ) -> IdentityValidationResult:
        """
        Validate a node's identity credentials.

        Checks:
        - source_node_id is present
        - credentials exist for that node
        - node is active
        - key_id/public_key are registered
        - protocol version is acceptable

        Args:
            node_id: Node ID to validate
            credentials: Credentials presented by the node

        Returns:
            IdentityValidationResult with validation outcome
        """
        reasons: list[str] = []
        is_registered = False
        is_active = False
        credentials_match = False

        # Check if node_id is present
        if not node_id or not node_id.strip():
            reasons.append("Node ID is missing or empty")
            return IdentityValidationResult(
                is_valid=False,
                node_id=node_id,
                reasons=reasons,
                is_registered=False,
                is_active=False,
                credentials_match=False,
            )

        # Check if node is registered
        registered_creds = self._node_registry.get(node_id)
        if registered_creds is None:
            reasons.append(f"Node '{node_id}' is not in the registry")
            if not self.config.node_registry.allow_unknown_nodes:
                return IdentityValidationResult(
                    is_valid=False,
                    node_id=node_id,
                    reasons=reasons,
                    is_registered=False,
                    is_active=False,
                    credentials_match=False,
                )
            # Unknown nodes allowed - create minimal profile
            is_registered = False
            is_active = True
            credentials_match = True
        else:
            is_registered = True

            # Check if node is active
            if self.config.node_registry.require_active_status:
                is_active = registered_creds.is_active
                if not is_active:
                    reasons.append(f"Node '{node_id}' is not active")
            else:
                is_active = True

            # Check credentials match
            if (
                credentials.key_id == registered_creds.key_id
                and credentials.public_key == registered_creds.public_key
            ):
                credentials_match = True
            else:
                reasons.append("Presented credentials do not match registered credentials")

        # Determine overall validity
        is_valid = is_registered or self.config.node_registry.allow_unknown_nodes
        is_valid = is_valid and is_active and credentials_match

        self.logger.debug(
            f"Identity validation for '{node_id}': valid={is_valid}, "
            f"registered={is_registered}, active={is_active}, match={credentials_match}"
        )

        return IdentityValidationResult(
            is_valid=is_valid,
            node_id=node_id,
            reasons=reasons,
            is_registered=is_registered,
            is_active=is_active,
            credentials_match=credentials_match,
        )

    async def verify_artifact_signature(
        self,
        envelope: FederatedClaimEnvelope,
    ) -> SignatureVerificationResult:
        """
        Verify the signature on an artifact envelope.

        Checks:
        - signature exists
        - signer_node_id matches source_node_id
        - signature timestamp is valid
        - signed payload hash matches payload
        - algorithm is supported

        Args:
            envelope: The federated claim envelope to verify

        Returns:
            SignatureVerificationResult with verification outcome
        """
        reasons: list[str] = []
        algorithm_supported = True
        signer_matches_source = False
        timestamp_valid = True
        payload_hash_matches = False

        signature = envelope.signature

        # Check if signature exists
        if not signature or not signature.signature_value:
            reasons.append("Signature is missing or empty")
            return SignatureVerificationResult(
                is_valid=False,
                algorithm_supported=True,
                signer_matches_source=False,
                timestamp_valid=False,
                payload_hash_matches=False,
                reasons=reasons,
            )

        # Check if signer matches source
        if signature.signer_node_id == envelope.source_node_id:
            signer_matches_source = True
        else:
            reasons.append(
                f"Signer node ID '{signature.signer_node_id}' does not match "
                f"source node ID '{envelope.source_node_id}'"
            )

        # Check if algorithm is supported
        if not self.config.is_algorithm_supported(signature.algorithm):
            algorithm_supported = False
            reasons.append(f"Signature algorithm '{signature.algorithm}' is not supported")
        else:
            algorithm_supported = True

        # Check signature timestamp
        now = datetime.utcnow()
        time_diff = abs((now - signature.signed_at).total_seconds())
        if time_diff <= self.config.signature.clock_tolerance_seconds:
            timestamp_valid = True
        else:
            timestamp_valid = False
            reasons.append(
                f"Signature timestamp is out of range (diff: {time_diff}s, "
                f"allowed: {self.config.signature.clock_tolerance_seconds}s)"
            )

        # Check payload hash (simulated - in production, use actual crypto)
        payload_hash_matches = await self._verify_payload_hash(envelope)
        if not payload_hash_matches:
            reasons.append("Payload hash does not match signed hash")

        # Determine overall validity
        is_valid = (
            signer_matches_source
            and algorithm_supported
            and timestamp_valid
            and payload_hash_matches
        )

        self.logger.debug(
            f"Signature verification for envelope '{envelope.envelope_id}': "
            f"valid={is_valid}, algorithm={signature.algorithm}"
        )

        return SignatureVerificationResult(
            is_valid=is_valid,
            algorithm_supported=algorithm_supported,
            signer_matches_source=signer_matches_source,
            timestamp_valid=timestamp_valid,
            payload_hash_matches=payload_hash_matches,
            reasons=reasons,
        )

    async def _verify_payload_hash(self, envelope: FederatedClaimEnvelope) -> bool:
        """
        Verify that the payload matches the signature.

        In production, this would use actual cryptographic verification.
        For Phase 1B, we simulate by checking that the signature exists
        and has the expected format.

        Args:
            envelope: The envelope to verify

        Returns:
            True if payload hash matches signature
        """
        # In production, implement actual cryptographic verification:
        # 1. Serialize the artifact payload
        # 2. Hash it using the specified algorithm
        # 3. Verify the signature using the node's public key

        # For Phase 1B, we simulate this check
        # A real implementation would use:
        # - cryptography.hazmat for ED25519/RSA
        # - ecdsa for ECDSA
        # - Or a library like PyCryptodome

        # Simulate verification by checking signature format
        sig_value = envelope.signature.signature_value
        if not sig_value or len(sig_value) < 32:
            return False

        # Simulate hash verification
        artifact_dict = envelope.artifact.model_dump()
        payload_json = json.dumps(artifact_dict, sort_keys=True)
        payload_hash = hashlib.sha256(payload_json.encode()).hexdigest()[:16]

        # Check if signature contains the expected hash (simulated)
        return payload_hash in sig_value or len(sig_value) >= 64

    async def get_node_trust_baseline(self, node_id: str) -> NodeTrustProfile:
        """
        Get the trust baseline for a node.

        Args:
            node_id: Node ID to get trust profile for

        Returns:
            NodeTrustProfile for the node

        Raises:
            UnknownNodeError: If node is not found and unknown nodes are not allowed
        """
        if node_id in self._trust_profiles:
            return self._trust_profiles[node_id]

        # Check if we have credentials for this node
        if node_id in self._node_registry:
            creds = self._node_registry[node_id]
            # Create default profile based on credentials
            profile = NodeTrustProfile(
                node_id=node_id,
                baseline_trust_score=0.7 if creds.trust_tier == "trusted" else 0.5,
                trust_tier=creds.trust_tier or "unknown",
                is_trusted=creds.trust_tier == "trusted",
            )
            self._trust_profiles[node_id] = profile
            return profile

        # Unknown node - use configured default
        if not self.config.node_registry.allow_unknown_nodes:
            raise UnknownNodeError(
                f"Node '{node_id}' is not in the trust registry",
                details={"node_id": node_id}
            )

        # Create minimal profile for unknown node
        profile = NodeTrustProfile(
            node_id=node_id,
            baseline_trust_score=self.config.node_registry.unknown_node_default_trust,
            trust_tier="unknown",
            is_trusted=False,
        )
        self._trust_profiles[node_id] = profile
        return profile

    async def evaluate_inbound_trust(
        self,
        envelope: FederatedClaimEnvelope,
        presented_credentials: NodeCredentials | None = None,
    ) -> InboundTrustDecision:
        """
        Evaluate whether to accept, quarantine, or reject an inbound claim.

        This is the unified decision method that combines:
        - Identity validation
        - Signature verification
        - Trust baseline evaluation

        Args:
            envelope: The inbound federated claim envelope
            presented_credentials: Optional credentials presented by the node.
                If None, uses registered credentials for validation.

        Returns:
            InboundTrustDecision with decision outcome

        Raises:
            QuarantineException: If envelope should be quarantined
        """
        reasons: list[str] = []
        node_id = envelope.source_node_id

        # Step 1: Validate identity
        # Use registered credentials if none presented (for Phase 1B testing)
        if presented_credentials is None:
            registered_creds = self._node_registry.get(node_id)
            if registered_creds:
                presented_credentials = registered_creds
            else:
                # Create minimal credentials for unknown node
                presented_credentials = NodeCredentials(
                    node_id=node_id,
                    key_id="",
                    public_key="",
                )

        identity_result = await self.validate_node_identity(
            node_id,
            presented_credentials,
        )

        identity_valid = identity_result.is_valid
        reasons.extend([f"Identity: {r}" for r in identity_result.reasons])

        if not identity_valid:
            # Identity failed - decide based on severity
            if "not in the registry" in " ".join(identity_result.reasons):
                # Unknown node - quarantine or reject based on config
                if not self.config.node_registry.allow_unknown_nodes:
                    return InboundTrustDecision(
                        decision="reject",
                        reasons=reasons,
                        node_trust_score=0.0,
                        identity_valid=False,
                        signature_valid=False,
                        node_id=node_id,
                        envelope_id=envelope.envelope_id,
                    )
                # Unknown but allowed - quarantine
                return InboundTrustDecision(
                    decision="quarantine",
                    reasons=reasons + ["Unknown node - quarantined for review"],
                    node_trust_score=0.0,
                    identity_valid=False,
                    signature_valid=False,
                    node_id=node_id,
                    envelope_id=envelope.envelope_id,
                )

        # Step 2: Verify signature
        signature_result = await self.verify_artifact_signature(envelope)
        signature_valid = signature_result.is_valid
        reasons.extend([f"Signature: {r}" for r in signature_result.reasons])

        if not signature_valid:
            # Signature failed - check severity
            if not signature_result.signer_matches_source:
                # Potential spoofing - reject and flag
                return InboundTrustDecision(
                    decision="reject_and_flag",
                    reasons=reasons,
                    node_trust_score=0.0,
                    identity_valid=identity_valid,
                    signature_valid=False,
                    node_id=node_id,
                    envelope_id=envelope.envelope_id,
                )
            # Other signature failures - reject
            return InboundTrustDecision(
                decision="reject",
                reasons=reasons,
                node_trust_score=0.0,
                identity_valid=identity_valid,
                signature_valid=False,
                node_id=node_id,
                envelope_id=envelope.envelope_id,
            )

        # Step 3: Get trust baseline
        try:
            trust_profile = await self.get_node_trust_baseline(node_id)
            node_trust_score = trust_profile.baseline_trust_score
        except UnknownNodeError:
            node_trust_score = 0.0
            reasons.append("Node not found in trust registry")

        # Step 4: Make final decision
        decision = self._make_trust_decision(
            node_trust_score=node_trust_score,
            identity_valid=identity_valid,
            signature_valid=signature_valid,
            trust_profile=trust_profile if 'trust_profile' in locals() else None,
        )

        result = InboundTrustDecision(
            decision=decision,
            reasons=reasons,
            node_trust_score=node_trust_score,
            identity_valid=identity_valid,
            signature_valid=signature_valid,
            node_id=node_id,
            envelope_id=envelope.envelope_id,
        )

        self.logger.info(
            f"Trust decision for envelope '{envelope.envelope_id}': "
            f"decision={decision}, node_trust={node_trust_score:.2f}"
        )

        return result

    def _make_trust_decision(
        self,
        node_trust_score: float,
        identity_valid: bool,
        signature_valid: bool,
        trust_profile: NodeTrustProfile | None,
    ) -> Literal["accept", "quarantine", "reject", "reject_and_flag"]:
        """
        Make final trust decision based on all factors.

        Args:
            node_trust_score: Trust score of the source node
            identity_valid: Whether identity validation passed
            signature_valid: Whether signature verification passed
            trust_profile: Full trust profile if available

        Returns:
            Decision outcome
        """
        # Check for critical failures first
        if not identity_valid and not signature_valid:
            return "reject"

        if not signature_valid:
            # Invalid signature with valid identity = potential attack
            return "reject_and_flag"

        # Check trust score
        if trust_profile and trust_profile.is_quarantined:
            return "quarantine"

        # Use threshold-based decision
        decision = self.config.get_trust_decision(node_trust_score)

        # Boost decision if node is explicitly trusted
        if trust_profile and trust_profile.is_trusted:
            if decision == "quarantine":
                return "accept"
            if decision == "reject" and node_trust_score > 0.4:
                return "quarantine"

        return decision


def create_identity_guard(
    config: FederationConfig | None = None,
    node_registry: dict[str, NodeCredentials] | None = None,
    trust_profiles: dict[str, NodeTrustProfile] | None = None,
) -> FederationIdentityGuard:
    """
    Factory function to create a FederationIdentityGuard.

    Args:
        config: Federation configuration
        node_registry: Known node credentials
        trust_profiles: Node trust profiles

    Returns:
        Configured FederationIdentityGuard instance
    """
    return FederationIdentityGuard(
        config=config,
        node_registry=node_registry,
        trust_profiles=trust_profiles,
    )
