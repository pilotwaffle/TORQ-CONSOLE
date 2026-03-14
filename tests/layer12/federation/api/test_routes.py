"""
Test Suite for Federation API Routes

Phase 1B - Tests for FastAPI endpoints matching shared TypeScript contracts.
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from torq_console.layer12.federation.api.routes import router, get_guard
from torq_console.layer12.federation.federation_identity_guard import FederationIdentityGuard
from torq_console.layer12.federation.types import (
    NodeCredentials,
    NodeTrustProfile,
)
from torq_console.layer12.federation.config import FederationConfig


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def test_config() -> FederationConfig:
    """Create test configuration."""
    return FederationConfig()


@pytest.fixture
def test_guard(test_config: FederationConfig) -> FederationIdentityGuard:
    """Create test identity guard."""
    from torq_console.layer12.federation.api import routes

    guard = FederationIdentityGuard(config=test_config)

    # Register test nodes
    trusted_creds = NodeCredentials(
        node_id="node-test-trusted",
        key_id="key-test-001",
        public_key="test-public-key-trusted",
        trust_tier="trusted",
        is_active=True,
    )
    guard.register_node(trusted_creds)

    trusted_profile = NodeTrustProfile(
        node_id="node-test-trusted",
        baseline_trust_score=0.85,
        trust_tier="trusted",
        is_trusted=True,
        successful_exchanges=100,
        failed_exchanges=5,
    )
    guard.register_trust_profile(trusted_profile)

    # Set as global guard
    routes._guard = guard

    return guard


@pytest.fixture
def client(test_guard: FederationIdentityGuard) -> TestClient:
    """Create test client."""
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@pytest.fixture
def sample_envelope_dict() -> dict:
    """Create a sample envelope for API requests."""
    now = datetime.utcnow()
    old_time = now - timedelta(seconds=200)

    return {
        "envelopeId": "env-test-001",
        "protocolVersion": "1.0.0",
        "sourceNodeId": "node-test-trusted",
        "targetNodeId": None,
        "sentAt": now.isoformat() + "Z",
        "artifact": {
            "artifactId": "artifact-test-001",
            "artifactType": "insight",
            "title": "Test Insight",
            "claimText": "This is a test claim",
            "confidence": 0.9,
            "originLayer": "layer4",
            "context": {},
            "limitations": [],
            "tags": ["test"],
        },
        "signature": {
            "algorithm": "ED25519",
            "signerNodeId": "node-test-trusted",
            "signatureValue": "valid-signature-001-7ae71c0a11521b2b-mock",
            "signedAt": old_time.isoformat() + "Z",
        },
        "trace": {
            "messageId": "msg-test-001",
            "hopCount": 0,
            "priorNodeIds": [],
            "correlationId": None,
        },
    }


# ============================================================================
# Tests: POST /api/l12/federation/validate-identity
# ============================================================================

class TestValidateIdentityEndpoint:
    """Tests for validate-identity endpoint."""

    def test_trusted_node_validation_succeeds(
        self,
        client: TestClient,
    ):
        """Test that validating a trusted node succeeds."""
        response = client.post(
            "/api/l12/federation/validate-identity",
            json={
                "nodeId": "node-test-trusted",
                "credentials": {
                    "keyId": "key-test-001",
                    "publicKey": "test-public-key-trusted",
                },
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert data["data"]["isValid"] is True
        assert data["data"]["nodeId"] == "node-test-trusted"
        assert data["data"]["isRegistered"] is True
        assert data["data"]["isActive"] is True
        assert data["data"]["credentialsMatch"] is True

    def test_unknown_node_fails_validation(
        self,
        client: TestClient,
    ):
        """Test that an unknown node fails validation."""
        response = client.post(
            "/api/l12/federation/validate-identity",
            json={
                "nodeId": "node-test-unknown",
                "credentials": {
                    "keyId": "key-unknown",
                    "publicKey": "unknown-key",
                },
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert data["data"]["isValid"] is False
        assert data["data"]["isRegistered"] is False

    def test_empty_node_id_fails(self, client: TestClient):
        """Test that empty node ID fails validation."""
        response = client.post(
            "/api/l12/federation/validate-identity",
            json={
                "nodeId": "",
                "credentials": {
                    "keyId": "key-test",
                    "publicKey": "test-key",
                },
            },
        )

        assert response.status_code == 422  # Validation error


# ============================================================================
# Tests: POST /api/l12/federation/verify-signature
# ============================================================================

class TestVerifySignatureEndpoint:
    """Tests for verify-signature endpoint."""

    def test_valid_signature_accepted(
        self,
        client: TestClient,
        sample_envelope_dict: dict,
    ):
        """Test that a valid signature is accepted."""
        response = client.post(
            "/api/l12/federation/verify-signature",
            json={"envelope": sample_envelope_dict},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert data["data"]["isValid"] is True
        assert data["data"]["signerMatchesSource"] is True
        assert data["data"]["timestampValid"] is True

    def test_spoofed_signature_rejected(
        self,
        client: TestClient,
        sample_envelope_dict: dict,
    ):
        """Test that a spoofed signature is rejected."""
        # Spoof the signature
        sample_envelope_dict["signature"]["signerNodeId"] = "node-malicious"

        response = client.post(
            "/api/l12/federation/verify-signature",
            json={"envelope": sample_envelope_dict},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["data"]["isValid"] is False
        assert data["data"]["signerMatchesSource"] is False

    def test_malformed_signature_rejected(
        self,
        client: TestClient,
        sample_envelope_dict: dict,
    ):
        """Test that a malformed signature is rejected."""
        sample_envelope_dict["signature"]["signatureValue"] = "short"

        response = client.post(
            "/api/l12/federation/verify-signature",
            json={"envelope": sample_envelope_dict},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["data"]["isValid"] is False
        assert data["data"]["payloadHashMatches"] is False


# ============================================================================
# Tests: POST /api/l12/federation/evaluate-inbound-trust
# ============================================================================

class TestEvaluateInboundTrustEndpoint:
    """Tests for evaluate-inbound-trust endpoint."""

    def test_trusted_node_accepted(
        self,
        client: TestClient,
        sample_envelope_dict: dict,
    ):
        """Test that a trusted node with valid signature is accepted."""
        response = client.post(
            "/api/l12/federation/evaluate-inbound-trust",
            json={"envelope": sample_envelope_dict},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert data["data"]["decision"] == "accept"
        assert data["data"]["shouldProceed"] is True
        assert data["data"]["identityValid"] is True
        assert data["data"]["signatureValid"] is True

    def test_unknown_node_quarantined_or_rejected(
        self,
        client: TestClient,
        sample_envelope_dict: dict,
    ):
        """Test that an unknown node is quarantined or rejected."""
        sample_envelope_dict["sourceNodeId"] = "node-unknown-999"
        sample_envelope_dict["signature"]["signerNodeId"] = "node-unknown-999"

        response = client.post(
            "/api/l12/federation/evaluate-inbound-trust",
            json={"envelope": sample_envelope_dict},
        )

        assert response.status_code == 200
        data = response.json()

        decision = data["data"]["decision"]
        assert decision in ("quarantine", "reject")

    def test_reject_and_flag_for_spoofed(
        self,
        client: TestClient,
        sample_envelope_dict: dict,
    ):
        """Test that spoofed signature triggers reject_and_flag."""
        sample_envelope_dict["signature"]["signerNodeId"] = "node-malicious"

        response = client.post(
            "/api/l12/federation/evaluate-inbound-trust",
            json={"envelope": sample_envelope_dict},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["data"]["decision"] == "reject_and_flag"
        assert data["data"]["requiresFlagging"] is True


# ============================================================================
# Tests: Node Management Endpoints
# ============================================================================

class TestNodeManagementEndpoints:
    """Tests for node management endpoints."""

    def test_register_node_succeeds(self, client: TestClient):
        """Test that registering a new node succeeds."""
        response = client.post(
            "/api/l12/federation/nodes/register",
            json={
                "credentials": {
                    "nodeId": "node-test-new",
                    "keyId": "key-new-001",
                    "publicKey": "new-public-key",
                },
                "trustTier": "verified",
                "isActive": True,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert data["data"]["success"] is True
        assert data["data"]["nodeId"] == "node-test-new"

    def test_get_node_trust_profile(
        self,
        client: TestClient,
    ):
        """Test getting a node's trust profile."""
        response = client.get(
            "/api/l12/federation/nodes/node-test-trusted/trust-profile",
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert data["data"]["nodeId"] == "node-test-trusted"
        assert data["data"]["baselineTrustScore"] == 0.85
        assert data["data"]["isTrusted"] is True

    def test_get_unknown_node_returns_404(
        self,
        client: TestClient,
    ):
        """Test that getting an unknown node returns 404."""
        response = client.get(
            "/api/l12/federation/nodes/node-unknown-999/trust-profile",
        )

        assert response.status_code == 404

    def test_list_nodes(
        self,
        client: TestClient,
    ):
        """Test listing registered nodes."""
        response = client.get("/api/l12/federation/nodes")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "nodes" in data["data"]
        assert "total" in data["data"]
        assert data["data"]["total"] >= 1


# ============================================================================
# Tests: GET /api/l12/federation/status
# ============================================================================

class TestFederationStatusEndpoint:
    """Tests for federation status endpoint."""

    def test_status_returns_current_state(
        self,
        client: TestClient,
    ):
        """Test that status endpoint returns current federation state."""
        response = client.get("/api/l12/federation/status")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "protocolVersion" in data["data"]
        assert "activeConnections" in data["data"]
        assert data["data"]["protocolVersion"] == "1.0.0"
