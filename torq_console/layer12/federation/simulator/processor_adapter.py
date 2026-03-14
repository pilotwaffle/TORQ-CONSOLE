"""
Processor Adapter for Federation Simulator

Layer 12 Phase 2A — Federation Stability Validation Harness

Adapter layer that converts simulated claims into real federation processor
requests and normalizes responses back into simulator-friendly results.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

import hashlib
import json

from .models import (
    Domain,
    SimulatedClaim,
    SimulatedNode,
    Stance,
)
from ..inbound_claim_processor import InboundFederatedClaimProcessor
from ..types import (
    ArtifactSignature,
    FederatedArtifactPayload,
    FederatedClaimEnvelope,
    FederationTrace,
    NodeCredentials,
    NodeTrustProfile,
)
from ..federation_identity_guard import FederationIdentityGuard


logger = logging.getLogger(__name__)


class ProcessedSimulationClaimResult:
    """Normalized result from processing a simulated claim."""

    def __init__(
        self,
        claim: SimulatedClaim,
        accepted: bool,
        status: str,
        rejection_reason: Optional[str] = None,
        eligibility_decision: Optional[Dict[str, Any]] = None,
        similarity_risk: Optional[Dict[str, Any]] = None,
        plurality_flags: Optional[Dict[str, Any]] = None,
        allocative_flags: Optional[Dict[str, Any]] = None,
        trust_adjustment: float = 0.0,
        effective_trust: float = 0.5,
        contradiction_detected: bool = False,
        processing_latency_ms: float = 0.0,
        safeguard_events: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ):
        self.claim = claim
        self.accepted = accepted
        self.status = status  # "accepted", "quarantined", "rejected"
        self.rejection_reason = rejection_reason
        self.eligibility_decision = eligibility_decision
        self.similarity_risk = similarity_risk
        self.plurality_flags = plurality_flags
        self.allocative_flags = allocative_flags
        self.trust_adjustment = trust_adjustment
        self.effective_trust = effective_trust
        self.contradiction_detected = contradiction_detected
        self.processing_latency_ms = processing_latency_ms
        self.safeguard_events = safeguard_events or {}
        self.error = error


class ProcessorAdapter:
    """
    Adapter between simulator models and real federation processor.

    Responsibilities:
    - Convert SimulatedClaim → FederatedClaimEnvelope
    - Call async InboundFederatedClaimProcessor.process_claim()
    - Normalize ClaimProcessingResult → ProcessedSimulationClaimResult
    """

    def __init__(
        self,
        processor: InboundFederatedClaimProcessor,
        identity_guard: FederationIdentityGuard,
    ):
        """
        Initialize the processor adapter.

        Args:
            processor: The real inbound claim processor
            identity_guard: Identity guard for node validation
        """
        self.processor = processor
        self.identity_guard = identity_guard
        self.logger = logging.getLogger(__name__)

        # Ensure simulator nodes are registered in identity guard
        self._register_simulator_nodes()

    def _register_simulator_nodes(self):
        """Register simulator nodes with the identity guard."""
        # This will be called during scenario setup
        # Nodes will be registered as they are created
        pass

    def register_node(self, node: SimulatedNode) -> None:
        """
        Register a simulator node with the identity guard.

        Args:
            node: The simulated node to register
        """
        try:
            # Create NodeCredentials object
            credentials = NodeCredentials(
                node_id=node.node_id,
                key_id=f"key_{node.node_id}",
                public_key=f"simulated_key_{node.node_id}",
                trust_tier="trusted" if node.state.current_trust > 0.7 else "verified",
                is_active=True,
            )
            self.identity_guard.register_node(credentials)

            # Also register trust profile for trust evaluation
            trust_profile = NodeTrustProfile(
                node_id=node.node_id,
                baseline_trust_score=node.state.current_trust,
                trust_tier="trusted" if node.state.current_trust > 0.7 else "verified",
                is_trusted=node.state.current_trust > 0.8,
                is_quarantined=False,
            )
            self.identity_guard.register_trust_profile(trust_profile)

            self.logger.debug(f"Registered node {node.node_id} with identity guard (trust={node.state.current_trust:.2f})")
        except Exception as e:
            # Node might already be registered
            self.logger.debug(f"Node {node.node_id} already registered or registration failed: {e}")

    async def process_simulated_claim(
        self,
        sim_claim: SimulatedClaim,
        origin_node: SimulatedNode,
        round_context: Optional[Dict[str, Any]] = None,
    ) -> ProcessedSimulationClaimResult:
        """
        Process a simulated claim through the real federation processor.

        Args:
            sim_claim: The simulated claim to process
            origin_node: The node that generated the claim
            round_context: Optional round/simulation context

        Returns:
            ProcessedSimulationClaimResult with normalized outcome
        """
        round_num = round_context.get("round_num", 0) if round_context else 0
        scenario_name = round_context.get("scenario_name", "unknown") if round_context else "unknown"

        started_at = datetime.utcnow()

        try:
            # Convert SimulatedClaim to FederatedClaimEnvelope
            envelope = self._build_processor_request(
                sim_claim=sim_claim,
                origin_node=origin_node,
                round_num=round_num,
                scenario_name=scenario_name,
            )

            self.logger.debug(
                f"Processing claim {sim_claim.claim_id} from {origin_node.node_id} "
                f"(round {round_num}, stance {sim_claim.stance})"
            )

            # Call the real async processor
            processing_result = await self.processor.process_claim(
                envelope=envelope,
                skip_replay_check=False,
                skip_duplicate_check=False,
                force_accept=False,
            )

            # Calculate latency
            latency_ms = (
                processing_result.processing_completed_at -
                processing_result.processing_started_at
            ).total_seconds() * 1000

            # Extract safeguard results
            safeguard_events = self._extract_safeguard_events(processing_result)

            # Build normalized result
            result = ProcessedSimulationClaimResult(
                claim=sim_claim,
                accepted=(processing_result.status == "accepted"),
                status=processing_result.status,
                rejection_reason=self._extract_rejection_reason(processing_result),
                eligibility_decision=self._extract_eligibility_decision(processing_result),
                similarity_risk=self._extract_similarity_risk(processing_result),
                plurality_flags=self._extract_plurality_flags(processing_result),
                allocative_flags=self._extract_allocative_flags(processing_result),
                trust_adjustment=self._extract_trust_adjustment(processing_result),
                effective_trust=self._extract_effective_trust(processing_result, origin_node),
                contradiction_detected=self._extract_contradiction_detected(processing_result),
                processing_latency_ms=latency_ms,
                safeguard_events=safeguard_events,
            )

            self.logger.debug(
                f"Claim {sim_claim.claim_id} processed: {result.status} "
                f"(latency: {latency_ms:.2f}ms)"
            )

            return result

        except Exception as e:
            self.logger.error(
                f"Error processing claim {sim_claim.claim_id}: {e}",
                exc_info=True
            )
            return ProcessedSimulationClaimResult(
                claim=sim_claim,
                accepted=False,
                status="error",
                rejection_reason=f"Processing error: {str(e)}",
                processing_latency_ms=(
                    datetime.utcnow() - started_at
                ).total_seconds() * 1000,
                error=str(e),
            )

    def _build_processor_request(
        self,
        sim_claim: SimulatedClaim,
        origin_node: SimulatedNode,
        round_num: int,
        scenario_name: str,
    ) -> FederatedClaimEnvelope:
        """
        Build a FederatedClaimEnvelope from a SimulatedClaim.

        Args:
            sim_claim: The simulated claim
            origin_node: The node that generated it
            round_num: Current simulation round
            scenario_name: Current scenario name

        Returns:
            FederatedClaimEnvelope ready for the processor
        """
        # Map simulator enums to string values
        domain_str = self._map_domain_to_string(sim_claim.domain)
        stance_str = self._map_stance_to_string(sim_claim.stance)

        # Create artifact payload
        artifact = FederatedArtifactPayload(
            artifact_id=sim_claim.claim_id,
            artifact_type="insight",
            title=getattr(sim_claim, 'title', None) or f"Claim from {origin_node.node_id}",
            claim_text=sim_claim.content,
            summary=getattr(sim_claim, 'summary', None),
            confidence=sim_claim.confidence,
            provenance_score=sim_claim.provenance_quality,
            origin_layer="layer12_simulation",
            origin_insight_id=sim_claim.claim_id,
            context={
                "domain": domain_str,
                "stance": stance_str,
                "round": round_num,
                "scenario": scenario_name,
                "adversarial_mode": origin_node.profile.adversarial_mode or "none",
                "quality_level": getattr(sim_claim, 'quality_level', 'medium'),
            },
            tags=[domain_str, stance_str, scenario_name],
        )

        # Create signature (simulated with proper hash)
        # Generate a simulated hash that will pass verification
        artifact_dict = artifact.model_dump()
        payload_json = json.dumps(artifact_dict, sort_keys=True)
        payload_hash = hashlib.sha256(payload_json.encode()).hexdigest()[:16]
        # Create a 64-char signature value that includes the hash
        signature_value = f"simulated_sig_{payload_hash}_{origin_node.node_id}_{'0' * 32}"

        signature = ArtifactSignature(
            algorithm="SIMULATED",
            signer_node_id=origin_node.node_id,
            signature_value=signature_value,
            signed_at=sim_claim.timestamp,
        )

        # Create trace
        trace = FederationTrace(
            message_id=f"msg_{sim_claim.claim_id[:16]}",
            hop_count=0,
            prior_node_ids=[],
            correlation_id=f"{scenario_name}_round{round_num}",
        )

        # Create envelope
        envelope = FederatedClaimEnvelope(
            envelope_id=f"env_{sim_claim.claim_id[:32]}",
            protocol_version="1.0",
            source_node_id=origin_node.node_id,
            target_node_id=None,  # Broadcast
            sent_at=sim_claim.timestamp,
            artifact=artifact,
            signature=signature,
            trace=trace,
        )

        return envelope

    def _extract_safeguard_events(
        self,
        processing_result: Any,
    ) -> Dict[str, Any]:
        """Extract safeguard trigger events from processing result."""
        events = {
            "eligibility_triggered": False,
            "similarity_triggered": False,
            "plurality_triggered": False,
            "allocative_triggered": False,
            "trust_decay_triggered": False,
        }

        # Safeguard results are stored in the processing result
        # The exact structure depends on ClaimProcessingResult implementation

        if hasattr(processing_result, 'safeguard_results'):
            for safeguard_name, result in processing_result.safeguard_results.items():
                if hasattr(result, 'triggered') and result.triggered:
                    event_key = f"{safeguard_name}_triggered"
                    if event_key in events:
                        events[event_key] = True

        return events

    def _extract_rejection_reason(self, processing_result: Any) -> Optional[str]:
        """Extract rejection reason from processing result."""
        if hasattr(processing_result, 'quarantine_reason') and processing_result.quarantine_reason:
            return processing_result.quarantine_reason
        if hasattr(processing_result, 'rejection_reason') and processing_result.rejection_reason:
            return processing_result.rejection_reason
        return None

    def _extract_eligibility_decision(self, processing_result: Any) -> Optional[Dict[str, Any]]:
        """Extract eligibility filter decision."""
        if hasattr(processing_result, 'eligibility_result') and processing_result.eligibility_result:
            result = processing_result.eligibility_result
            return {
                "is_eligible": getattr(result, 'is_eligible', True),
                "quality_score": getattr(result, 'quality_score', 0.5),
                "confidence": getattr(result, 'confidence', 0.5),
            }
        return None

    def _extract_similarity_risk(self, processing_result: Any) -> Optional[Dict[str, Any]]:
        """Extract context similarity risk assessment."""
        if hasattr(processing_result, 'similarity_result') and processing_result.similarity_result:
            result = processing_result.similarity_result
            return {
                "should_throttle": getattr(result, 'should_throttle', False),
                "risk_level": getattr(result, 'risk_level', 'low'),
                "cluster_id": getattr(result, 'cluster_id', None),
            }
        return None

    def _extract_plurality_flags(self, processing_result: Any) -> Optional[Dict[str, Any]]:
        """Extract plurality preservation flags."""
        if hasattr(processing_result, 'plurality_result') and processing_result.plurality_result:
            result = processing_result.plurality_result
            assessment = getattr(result, 'assessment', None)
            return {
                "plurality_level": getattr(assessment, 'plurality_level', 'healthy') if assessment else 'healthy',
                "is_minority_preserved": getattr(assessment, 'is_minority_preserved', True) if assessment else True,
            }
        return None

    def _extract_allocative_flags(self, processing_result: Any) -> Optional[Dict[str, Any]]:
        """Extract allocative boundary flags."""
        if hasattr(processing_result, 'allocative_result') and processing_result.allocative_result:
            result = processing_result.allocative_result
            return {
                "is_allowed": getattr(result, 'is_allowed', True),
                "dominant_node_detected": getattr(result, 'dominant_node_detected', False),
            }
        return None

    def _extract_trust_adjustment(self, processing_result: Any) -> float:
        """Extract trust adjustment from processing."""
        if hasattr(processing_result, 'trust_decision') and processing_result.trust_decision:
            decision = processing_result.trust_decision
            return getattr(decision, 'trust_adjustment', 0.0)
        return 0.0

    def _extract_effective_trust(self, processing_result: Any, node: SimulatedNode) -> float:
        """Extract effective trust used for the decision."""
        if hasattr(processing_result, 'trust_decision') and processing_result.trust_decision:
            decision = processing_result.trust_decision
            effective_trust = getattr(decision, 'effective_trust', None)
            if effective_trust is not None:
                return effective_trust
        return node.state.current_trust

    def _extract_contradiction_detected(self, processing_result: Any) -> bool:
        """Extract whether contradiction was detected."""
        if hasattr(processing_result, 'contradiction_result') and processing_result.contradiction_result:
            return getattr(processing_result.contradiction_result, 'has_contradiction', False)
        return False

    def _map_domain_to_string(self, domain: Domain) -> str:
        """Map Domain enum to string for processor."""
        return domain.value if isinstance(domain, Domain) else str(domain)

    def _map_stance_to_string(self, stance: Stance) -> str:
        """Map Stance enum to string for processor."""
        return stance.value if isinstance(stance, Stance) else str(stance)


async def process_claims_batch(
    adapter: ProcessorAdapter,
    claims: List[tuple[SimulatedClaim, SimulatedNode]],
    round_context: Optional[Dict[str, Any]] = None,
) -> List[ProcessedSimulationClaimResult]:
    """
    Process a batch of claims concurrently.

    Args:
        adapter: The processor adapter
        claims: List of (claim, node) tuples
        round_context: Optional round context

    Returns:
        List of processed results in same order as input
    """
    tasks = [
        adapter.process_simulated_claim(claim, node, round_context)
        for claim, node in claims
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle any exceptions that occurred
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            claim, node = claims[i]
            processed_results.append(
                ProcessedSimulationClaimResult(
                    claim=claim,
                    accepted=False,
                    status="error",
                    rejection_reason=f"Exception during processing: {str(result)}",
                    error=str(result),
                )
            )
        else:
            processed_results.append(result)

    return processed_results
