"""
Two-Node Federation Test Harness

Phase 1B - Local simulation of two-node federation exchange.

This harness enables deterministic testing of federation scenarios:
- Valid claim exchange
- Replay attacks
- Duplicate content
- Contradictions
- Low-trust sender behavior

The harness runs entirely in-memory with simulated transport,
making tests fast, deterministic, and isolated from external dependencies.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Literal
from pydantic import BaseModel, Field

from torq_console.layer12.federation.config import FederationConfig, default_config
from torq_console.layer12.federation.types import (
    FederatedClaimEnvelope,
    NodeCredentials,
    NodeTrustProfile,
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
from torq_console.layer12.federation.outbound_publisher import (
    OutboundClaimPublisher,
    PublisherConfig,
    ArtifactDraft,
    PublishResult,
    create_outbound_publisher,
)
from torq_console.layer12.federation.exchange_tracker import (
    ExchangeTrackerService,
    ExchangeTrace,
    create_exchange_tracker,
    ExchangeEventType,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Test Node Configuration
# ============================================================================

class TestNodeConfig(BaseModel):
    """Configuration for a test node."""

    node_id: str = Field(..., description="Node identifier")
    key_id: str = Field(..., description="Key identifier")
    public_key: str = Field(..., description="Public key")
    trust_tier: str = Field(default="trusted", description="Trust tier")
    baseline_trust_score: float = Field(default=0.8, ge=0.0, le=1.0)
    is_active: bool = Field(default=True, description="Whether node is active")


# ============================================================================
# Test Scenario Configuration
# ============================================================================

class TestScenario(BaseModel):
    """Configuration for a federation test scenario."""

    name: str = Field(..., description="Scenario name")
    description: str = Field(..., description="Scenario description")

    # Node A (sender) configuration
    node_a_config: TestNodeConfig = Field(..., description="Sender node config")

    # Node B (receiver) configuration
    node_b_config: TestNodeConfig = Field(..., description="Receiver node config")

    # Test behavior flags
    enable_replay_test: bool = Field(default=False, description="Test replay resend")
    enable_duplicate_test: bool = Field(default=False, description="Test duplicate content")
    enable_contradiction_test: bool = Field(default=False, description="Test contradiction detection")
    enable_low_trust_test: bool = Field(default=False, description="Test low-trust sender")

    # Expected outcomes
    expected_outcome: Literal["accepted", "quarantined", "rejected"] = Field(
        default="accepted",
        description="Expected final disposition"
    )


# ============================================================================
# Predefined Scenarios
# ============================================================================

class TestScenarios:
    """Predefined test scenarios for federation testing."""

    @staticmethod
    def trusted_exchange() -> TestScenario:
        """Scenario: Trusted node A sends valid claim to trusted node B."""
        return TestScenario(
            name="trusted_exchange",
            description="Trusted node A sends valid claim to trusted node B",
            node_a_config=TestNodeConfig(
                node_id="node_alice",
                key_id="key_alice",
                public_key="pubkey_alice",
                trust_tier="trusted",
                baseline_trust_score=0.9,
            ),
            node_b_config=TestNodeConfig(
                node_id="node_bob",
                key_id="key_bob",
                public_key="pubkey_bob",
                trust_tier="trusted",
                baseline_trust_score=0.9,
            ),
            expected_outcome="accepted",
        )

    @staticmethod
    def low_trust_sender() -> TestScenario:
        """Scenario: Low-trust node sends claim to trusted node."""
        return TestScenario(
            name="low_trust_sender",
            description="Low-trust node sends claim to trusted node",
            node_a_config=TestNodeConfig(
                node_id="node_charlie",
                key_id="key_charlie",
                public_key="pubkey_charlie",
                trust_tier="unknown",
                baseline_trust_score=0.3,
            ),
            node_b_config=TestNodeConfig(
                node_id="node_bob",
                key_id="key_bob",
                public_key="pubkey_bob",
                trust_tier="trusted",
                baseline_trust_score=0.9,
            ),
            enable_low_trust_test=True,
            expected_outcome="quarantined",
        )

    @staticmethod
    def replay_attack() -> TestScenario:
        """Scenario: Replay attack - same envelope resent."""
        return TestScenario(
            name="replay_attack",
            description="Replay attack - same envelope resent",
            node_a_config=TestNodeConfig(
                node_id="node_alice",
                key_id="key_alice",
                public_key="pubkey_alice",
                trust_tier="trusted",
                baseline_trust_score=0.9,
            ),
            node_b_config=TestNodeConfig(
                node_id="node_bob",
                key_id="key_bob",
                public_key="pubkey_bob",
                trust_tier="trusted",
                baseline_trust_score=0.9,
            ),
            enable_replay_test=True,
            expected_outcome="rejected",
        )

    @staticmethod
    def duplicate_content() -> TestScenario:
        """Scenario: Duplicate content sent in different envelope."""
        return TestScenario(
            name="duplicate_content",
            description="Duplicate content sent in different envelope",
            node_a_config=TestNodeConfig(
                node_id="node_alice",
                key_id="key_alice",
                public_key="pubkey_alice",
                trust_tier="trusted",
                baseline_trust_score=0.9,
            ),
            node_b_config=TestNodeConfig(
                node_id="node_bob",
                key_id="key_bob",
                public_key="pubkey_bob",
                trust_tier="trusted",
                baseline_trust_score=0.9,
            ),
            enable_duplicate_test=True,
            expected_outcome="accepted",  # Tracked but not rejected
        )

    @staticmethod
    def contradiction() -> TestScenario:
        """Scenario: Contradictory claim sent to node with opposing claim."""
        return TestScenario(
            name="contradiction",
            description="Contradictory claim sent to node with opposing claim",
            node_a_config=TestNodeConfig(
                node_id="node_alice",
                key_id="key_alice",
                public_key="pubkey_alice",
                trust_tier="trusted",
                baseline_trust_score=0.9,
            ),
            node_b_config=TestNodeConfig(
                node_id="node_bob",
                key_id="key_bob",
                public_key="pubkey_bob",
                trust_tier="trusted",
                baseline_trust_score=0.9,
            ),
            enable_contradiction_test=True,
            expected_outcome="accepted",  # Accepted but contradiction flagged
        )


# ============================================================================
# Two-Node Test Harness
# ============================================================================

class TwoNodeFederationHarness:
    """
    Test harness for two-node federation scenarios.

    This harness creates isolated test environments with:
    - Two configurable nodes (A and B)
    - Separate identity guards for each node
    - Publisher for Node A
    - Processor for Node B
    - Exchange tracker for full visibility
    - Simulated transport (direct function call)
    """

    def __init__(
        self,
        scenario: TestScenario,
        federation_config: FederationConfig | None = None,
    ):
        """
        Initialize the test harness.

        Args:
            scenario: Test scenario configuration
            federation_config: Federation layer configuration
        """
        self.scenario = scenario
        self.federation_config = federation_config or default_config
        self.logger = logging.getLogger(__name__)

        # Create credentials for both nodes
        self.node_a_credentials = NodeCredentials(
            node_id=scenario.node_a_config.node_id,
            key_id=scenario.node_a_config.key_id,
            public_key=scenario.node_a_config.public_key,
            trust_tier=scenario.node_a_config.trust_tier,
            is_active=scenario.node_a_config.is_active,
        )

        self.node_b_credentials = NodeCredentials(
            node_id=scenario.node_b_config.node_id,
            key_id=scenario.node_b_config.key_id,
            public_key=scenario.node_b_config.public_key,
            trust_tier=scenario.node_b_config.trust_tier,
            is_active=scenario.node_b_config.is_active,
        )

        # Create identity guards
        self.node_a_guard = create_identity_guard(config=self.federation_config)
        self.node_b_guard = create_identity_guard(config=self.federation_config)

        # Register nodes with each other's guards
        self.node_a_guard.register_node(self.node_b_credentials)
        self.node_b_guard.register_node(self.node_a_credentials)

        # Set trust profiles
        self.node_a_guard.register_trust_profile(NodeTrustProfile(
            node_id=scenario.node_a_config.node_id,
            baseline_trust_score=scenario.node_a_config.baseline_trust_score,
            trust_tier=scenario.node_a_config.trust_tier,
            is_trusted=scenario.node_a_config.trust_tier == "trusted",
        ))

        self.node_b_guard.register_trust_profile(NodeTrustProfile(
            node_id=scenario.node_b_config.node_id,
            baseline_trust_score=scenario.node_b_config.baseline_trust_score,
            trust_tier=scenario.node_b_config.trust_tier,
            is_trusted=scenario.node_b_config.trust_tier == "trusted",
        ))

        # Create publisher for Node A
        self.node_a_publisher = create_outbound_publisher(
            credentials=self.node_a_credentials,
            config=PublisherConfig(
                local_node_id=scenario.node_a_config.node_id,
                enable_dispatch=False,  # We'll dispatch manually in tests
            ),
            federation_config=self.federation_config,
        )

        # Create processor for Node B
        self.node_b_processor = create_inbound_claim_processor(
            identity_guard=self.node_b_guard,
            config=ProcessorConfig(
                enable_replay_protection=True,
                enable_duplicate_suppression=True,
                enable_persistence=False,  # In-memory for tests
                enable_audit_logging=True,
            ),
            federation_config=self.federation_config,
        )

        # Create exchange tracker
        self.exchange_tracker = create_exchange_tracker()

        # Test results
        self.publish_results: list[PublishResult] = []
        self.process_results: list[ClaimProcessingResult] = []

        self.logger.info(f"Initialized test harness: {scenario.name}")

    async def publish_claim_from_node_a(
        self,
        draft: ArtifactDraft,
    ) -> PublishResult:
        """
        Publish a claim from Node A.

        Args:
            draft: Artifact draft to publish

        Returns:
            PublishResult
        """
        self.logger.info(f"Node A publishing claim: {draft.title}")

        result = await self.node_a_publisher.publish_claim(
            draft=draft,
            target_node_id=self.scenario.node_b_config.node_id,
        )

        self.publish_results.append(result)

        # Track the exchange
        if result.envelope:
            self.exchange_tracker.create_exchange(
                correlation_id=result.correlation_id,
                envelope_id=result.envelope_id,
                source_node_id=self.scenario.node_a_config.node_id,
                target_node_id=self.scenario.node_b_config.node_id,
            )

            self.exchange_tracker.record_event(
                correlation_id=result.correlation_id,
                event_type=ExchangeEventType.PUBLISHED,
                node_id=self.scenario.node_a_config.node_id,
                envelope_id=result.envelope_id,
                source_node_id=self.scenario.node_a_config.node_id,
                target_node_id=self.scenario.node_b_config.node_id,
                status="published",
                details={"title": draft.title},
            )

        return result

    async def process_claim_on_node_b(
        self,
        envelope: FederatedClaimEnvelope,
    ) -> ClaimProcessingResult:
        """
        Process a claim on Node B.

        Args:
            envelope: Envelope to process

        Returns:
            ClaimProcessingResult
        """
        self.logger.info(f"Node B processing claim: {envelope.envelope_id}")

        # Track receive event
        correlation_id = envelope.trace.correlation_id or f"corr_{envelope.envelope_id}"

        self.exchange_tracker.record_event(
            correlation_id=correlation_id,
            event_type=ExchangeEventType.RECEIVED,
            node_id=self.scenario.node_b_config.node_id,
            envelope_id=envelope.envelope_id,
            source_node_id=envelope.source_node_id,
            target_node_id=self.scenario.node_b_config.node_id,
        )

        result = await self.node_b_processor.process_claim(envelope)
        self.process_results.append(result)

        # Track processing events
        self.exchange_tracker.record_event(
            correlation_id=correlation_id,
            event_type=result.status.upper(),  # accepted, quarantined, rejected
            node_id=self.scenario.node_b_config.node_id,
            envelope_id=envelope.envelope_id,
            status=result.status,
            details={
                "processingDurationMs": result.processing_duration_ms,
                "claimId": result.claim_id,
            },
        )

        return result

    async def run_full_exchange(
        self,
        draft: ArtifactDraft,
    ) -> tuple[PublishResult, ClaimProcessingResult]:
        """
        Run a full exchange: Node A publishes, Node B processes.

        Args:
            draft: Artifact draft to exchange

        Returns:
            Tuple of (publish_result, process_result)
        """
        # Publish from Node A
        publish_result = await self.publish_claim_from_node_a(draft)

        if not publish_result.success or not publish_result.envelope:
            raise Exception(f"Publish failed: {publish_result.error_message}")

        # Process on Node B
        process_result = await self.process_claim_on_node_b(publish_result.envelope)

        return publish_result, process_result

    async def run_replay_test(self, draft: ArtifactDraft) -> tuple[PublishResult, ClaimProcessingResult, ClaimProcessingResult]:
        """
        Run a replay attack test: same envelope sent twice.

        Args:
            draft: Artifact draft

        Returns:
            Tuple of (first_publish, first_process, replay_process)
        """
        # First exchange
        pub1, proc1 = await self.run_full_exchange(draft)

        if not pub1.envelope:
            raise Exception("First publish failed")

        # Replay - same envelope
        proc2 = await self.process_claim_on_node_b(pub1.envelope)

        return pub1, proc1, proc2

    async def run_duplicate_test(
        self,
        draft1: ArtifactDraft,
        draft2: ArtifactDraft | None = None,
    ) -> tuple[PublishResult, ClaimProcessingResult, PublishResult, ClaimProcessingResult]:
        """
        Run a duplicate content test: same claim in different envelope.

        Args:
            draft1: First artifact draft
            draft2: Second draft with same content (uses draft1 if None)

        Returns:
            Tuple of (pub1, proc1, pub2, proc2)
        """
        # First exchange
        pub1, proc1 = await self.run_full_exchange(draft1)

        # Second exchange with same content (different envelope)
        if draft2 is None:
            draft2 = ArtifactDraft(
                artifact_id=f"artifact_2_{datetime.now().timestamp()}",
                artifact_type=draft1.artifact_type,
                title=draft1.title,
                claim_text=draft1.claim_text,
                confidence=draft1.confidence,
                origin_layer=draft1.origin_layer,
                tags=draft1.tags,
            )

        pub2, proc2 = await self.run_full_exchange(draft2)

        return pub1, proc1, pub2, proc2

    def get_exchange_trace(self, correlation_id: str) -> ExchangeTrace | None:
        """Get the exchange trace for a correlation ID."""
        return self.exchange_tracker.get_exchange_trace(correlation_id)

    def get_statistics(self) -> dict[str, Any]:
        """Get harness statistics."""
        return {
            "scenario": self.scenario.name,
            "publishCount": len(self.publish_results),
            "processCount": len(self.process_results),
            "nodeAPublisher": self.node_a_publisher.get_statistics(),
            "nodeBProcessor": self.node_b_processor.get_statistics(),
            "exchangeTracker": self.exchange_tracker.get_statistics(),
        }


# ============================================================================
# Harness Factory
# ============================================================================

def create_two_node_harness(
    scenario: TestScenario,
    federation_config: FederationConfig | None = None,
) -> TwoNodeFederationHarness:
    """
    Factory function to create a TwoNodeFederationHarness.

    Args:
        scenario: Test scenario configuration
        federation_config: Federation layer configuration

    Returns:
        Configured TwoNodeFederationHarness instance
    """
    return TwoNodeFederationHarness(
        scenario=scenario,
        federation_config=federation_config,
    )
