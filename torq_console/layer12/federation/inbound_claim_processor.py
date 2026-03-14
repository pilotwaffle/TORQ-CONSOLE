"""
Inbound Federated Claim Processor

Phase 1B - Orchestration service for processing inbound federated claims.

This is the authoritative pipeline for all inbound federation claims.
It coordinates validation, replay protection, duplicate suppression,
persistence, qualification, contradiction detection, and audit logging.

The processor follows a strict sequence:
1. Normalize envelope
2. Validate identity
3. Verify signature
4. Check replay protection
5. Check duplicate suppression
6. Persist inbound claim
7. Run LocalQualificationEngine
8. Run ContradictionAndPluralityManager
9. Write audit trail
10. Return processing result
"""

import logging
from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field

from torq_console.layer12.federation.config import FederationConfig, default_config
from torq_console.layer12.federation.types import (
    FederatedClaimEnvelope,
    IdentityValidationResult,
    SignatureVerificationResult,
    InboundTrustDecision,
    NodeTrustProfile,
)
from torq_console.layer12.federation.federation_identity_guard import FederationIdentityGuard
from torq_console.layer12.federation.replay_protection import (
    ReplayProtectionService,
    ReplayProtectionResult,
    create_replay_protection,
)
from torq_console.layer12.federation.duplicate_suppression import (
    DuplicateSuppressionService,
    DuplicateSuppressionResult,
    create_duplicate_suppression,
)
from torq_console.layer12.federation.errors import (
    ReplayAttackError,
    DuplicateSuppressionError,
    FederationError,
)

# Phase 1B Hardening: Safeguards
from torq_console.layer12.federation.safeguards import (
    FederationEligibilityFilter,
    ContextSimilarityEngine,
    PluralityPreservationRules,
    AllocativeBoundaryGuard,
    TrustDecayModel,
    EligibilityCriteria,
    SimilarityEngineConfig,
    PluralityPreservationConfig,
    AllocativeBoundaryConfig,
    TrustDecayConfig,
    EligibilityResult,
    SimilarityAnalysisResult,
    PluralityAnalysisResult,
    AllocativeDecision,
    TrustDecayAssessment,
    create_eligibility_filter,
    create_context_similarity_engine,
    create_plurality_preservation_rules,
    create_allocative_boundary_guard,
    create_trust_decay_model,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Processing Result Types
# ============================================================================

class ClaimProcessingResult(BaseModel):
    """Complete result of processing an inbound claim."""

    # Processing status
    status: Literal["accepted", "quarantined", "rejected"] = Field(
        ...,
        description="Final disposition of the claim"
    )

    # Envelope info
    envelope_id: str = Field(..., description="Processed envelope ID")
    claim_id: str | None = Field(None, description="Internal claim ID if assigned")
    source_node_id: str = Field(..., description="Source node ID")

    # Validation results
    identity_validation: IdentityValidationResult | None = Field(
        None,
        description="Identity validation result"
    )
    signature_verification: SignatureVerificationResult | None = Field(
        None,
        description="Signature verification result"
    )
    trust_decision: InboundTrustDecision | None = Field(
        None,
        description="Trust evaluation decision"
    )

    # Protection results
    replay_protection: ReplayProtectionResult | None = Field(
        None,
        description="Replay protection check result"
    )
    duplicate_suppression: DuplicateSuppressionResult | None = Field(
        None,
        description="Duplicate suppression check result"
    )

    # Phase 1B Hardening: Safeguard results
    eligibility_result: EligibilityResult | None = Field(
        None,
        description="Eligibility filter result"
    )
    similarity_result: SimilarityAnalysisResult | None = Field(
        None,
        description="Context similarity analysis result"
    )
    plurality_result: PluralityAnalysisResult | None = Field(
        None,
        description="Plurality preservation analysis result"
    )
    allocative_result: AllocativeDecision | None = Field(
        None,
        description="Allocative boundary guard decision"
    )
    trust_decay_result: TrustDecayAssessment | None = Field(
        None,
        description="Trust decay assessment result"
    )

    # Processing results (placeholder for Phase 1B completion)
    persisted_claim_id: str | None = Field(
        None,
        description="ID of persisted claim record"
    )
    qualification_score: float | None = Field(
        None,
        description="Qualification score from LocalQualificationEngine"
    )
    contradiction_count: int = Field(
        default=0,
        description="Number of contradictions detected"
    )
    plurality_status: str | None = Field(
        None,
        description="Plurality status after processing"
    )

    # Audit
    audit_event_ids: list[str] = Field(
        default_factory=list,
        description="IDs of audit events written"
    )

    # Processing metadata
    processing_started_at: datetime = Field(
        ...,
        description="When processing started"
    )
    processing_completed_at: datetime = Field(
        ...,
        description="When processing completed"
    )
    processing_duration_ms: float = Field(
        ...,
        description="Processing duration in milliseconds"
    )

    # Rejection info
    rejection_reason: str | None = Field(
        None,
        description="Reason for rejection if rejected"
    )
    quarantine_reasons: list[str] = Field(
        default_factory=list,
        description="Reasons for quarantine if quarantined"
    )

    # Error info
    error_code: str | None = Field(
        None,
        description="Error code if processing failed"
    )
    error_message: str | None = Field(
        None,
        description="Error message if processing failed"
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "status": self.status,
            "envelopeId": self.envelope_id,
            "claimId": self.claim_id,
            "sourceNodeId": self.source_node_id,
            "identityValidation": self.identity_validation.model_dump() if self.identity_validation else None,
            "signatureVerification": self.signature_verification.model_dump() if self.signature_verification else None,
            "trustDecision": self.trust_decision.model_dump() if self.trust_decision else None,
            "replayProtection": self.replay_protection.model_dump() if self.replay_protection else None,
            "duplicateSuppression": self.duplicate_suppression.model_dump() if self.duplicate_suppression else None,
            # Phase 1B Hardening: Safeguard results
            "eligibilityResult": self.eligibility_result.model_dump() if self.eligibility_result else None,
            "similarityResult": self.similarity_result.model_dump() if self.similarity_result else None,
            "pluralityResult": self.plurality_result.model_dump() if self.plurality_result else None,
            "allocativeResult": self.allocative_result.model_dump() if self.allocative_result else None,
            "trustDecayResult": self.trust_decay_result.model_dump() if self.trust_decay_result else None,
            "persistedClaimId": self.persisted_claim_id,
            "qualificationScore": self.qualification_score,
            "contradictionCount": self.contradiction_count,
            "pluralityStatus": self.plurality_status,
            "auditEventIds": self.audit_event_ids,
            "processingStartedAt": self.processing_started_at.isoformat(),
            "processingCompletedAt": self.processing_completed_at.isoformat(),
            "processingDurationMs": self.processing_duration_ms,
            "rejectionReason": self.rejection_reason,
            "quarantineReasons": self.quarantine_reasons,
            "errorCode": self.error_code,
            "errorMessage": self.error_message,
        }


class ProcessorConfig(BaseModel):
    """Configuration for the inbound claim processor."""

    enable_replay_protection: bool = Field(
        default=True,
        description="Whether to enable replay protection"
    )
    enable_duplicate_suppression: bool = Field(
        default=True,
        description="Whether to enable duplicate suppression"
    )
    enable_qualification: bool = Field(
        default=False,  # Phase 1B: will enable when LocalQualificationEngine is ready
        description="Whether to run qualification engine"
    )
    enable_contradiction_check: bool = Field(
        default=False,  # Phase 1B: will enable when ContradictionAndPluralityManager is ready
        description="Whether to run contradiction detection"
    )
    enable_persistence: bool = Field(
        default=False,  # Phase 1B: will enable when persistence layer is ready
        description="Whether to persist claims"
    )
    enable_audit_logging: bool = Field(
        default=True,
        description="Whether to write audit logs"
    )
    quarantine_duplicates: bool = Field(
        default=False,  # Track but don't quarantine duplicates from other nodes
        description="Whether to quarantine duplicate claims"
    )
    block_replays: bool = Field(
        default=True,
        description="Whether to block replayed envelopes"
    )

    # Phase 1B Hardening: Safeguards
    enable_eligibility_filter: bool = Field(
        default=True,
        description="Whether to enable eligibility filtering (quality gate)"
    )
    enable_context_similarity: bool = Field(
        default=True,
        description="Whether to enable context similarity engine"
    )
    enable_plurality_preservation: bool = Field(
        default=True,
        description="Whether to enable plurality preservation rules"
    )
    enable_allocative_boundaries: bool = Field(
        default=True,
        description="Whether to enable allocative boundary guard"
    )
    enable_trust_decay: bool = Field(
        default=True,
        description="Whether to enable trust decay modeling"
    )

    # Safeguard configurations
    eligibility_criteria: EligibilityCriteria | None = Field(
        default=None,
        description="Custom eligibility criteria (uses defaults if None)"
    )
    similarity_config: SimilarityEngineConfig | None = Field(
        default=None,
        description="Custom similarity engine config (uses defaults if None)"
    )
    plurality_config: PluralityPreservationConfig | None = Field(
        default=None,
        description="Custom plurality preservation config (uses defaults if None)"
    )
    allocative_config: AllocativeBoundaryConfig | None = Field(
        default=None,
        description="Custom allocative boundary config (uses defaults if None)"
    )
    trust_decay_config: TrustDecayConfig | None = Field(
        default=None,
        description="Custom trust decay config (uses defaults if None)"
    )


# ============================================================================
# Main Processor
# ============================================================================

class InboundFederatedClaimProcessor:
    """
    Authoritative pipeline for processing inbound federated claims.

    This service is the single orchestration point for all inbound
    federation handling. It coordinates validation, protection,
    persistence, and epistemic integration.

    Do not scatter this logic across routes or UI components.
    All inbound claims should flow through this processor.
    """

    def __init__(
        self,
        identity_guard: FederationIdentityGuard,
        replay_protection: ReplayProtectionService | None = None,
        duplicate_suppression: DuplicateSuppressionService | None = None,
        config: ProcessorConfig | None = None,
        federation_config: FederationConfig | None = None,
        # Phase 1B Hardening: Safeguards
        eligibility_filter: FederationEligibilityFilter | None = None,
        similarity_engine: ContextSimilarityEngine | None = None,
        plurality_rules: PluralityPreservationRules | None = None,
        allocative_guard: AllocativeBoundaryGuard | None = None,
        trust_decay: TrustDecayModel | None = None,
    ):
        """
        Initialize the inbound claim processor.

        Args:
            identity_guard: Identity validation and trust evaluation service
            replay_protection: Replay protection service
            duplicate_suppression: Duplicate suppression service
            config: Processor configuration
            federation_config: Federation layer configuration
            eligibility_filter: Eligibility filter safeguard
            similarity_engine: Context similarity engine safeguard
            plurality_rules: Plurality preservation rules safeguard
            allocative_guard: Allocative boundary guard safeguard
            trust_decay: Trust decay model safeguard
        """
        self.identity_guard = identity_guard
        self.replay_protection = replay_protection or create_replay_protection()
        self.duplicate_suppression = duplicate_suppression or create_duplicate_suppression()
        self.config = config or ProcessorConfig()
        self.federation_config = federation_config or default_config
        self.logger = logging.getLogger(__name__)

        # Phase 1B Hardening: Initialize safeguards
        self.eligibility_filter = eligibility_filter
        self.similarity_engine = similarity_engine
        self.plurality_rules = plurality_rules
        self.allocative_guard = allocative_guard
        self.trust_decay = trust_decay

        # Create safeguards on-demand if not provided and enabled
        if self.config.enable_eligibility_filter and not self.eligibility_filter:
            self.eligibility_filter = create_eligibility_filter(
                criteria=self.config.eligibility_criteria
            )
        if self.config.enable_context_similarity and not self.similarity_engine:
            self.similarity_engine = create_context_similarity_engine(
                config=self.config.similarity_config
            )
        if self.config.enable_plurality_preservation and not self.plurality_rules:
            self.plurality_rules = create_plurality_preservation_rules(
                config=self.config.plurality_config
            )
        if self.config.enable_allocative_boundaries and not self.allocative_guard:
            self.allocative_guard = create_allocative_boundary_guard(
                config=self.config.allocative_config
            )
        if self.config.enable_trust_decay and not self.trust_decay:
            self.trust_decay = create_trust_decay_model(
                config=self.config.trust_decay_config
            )

        # Statistics
        self._total_processed = 0
        self._accepted_count = 0
        self._quarantined_count = 0
        self._rejected_count = 0
        self._processor_started_at = datetime.utcnow()

    async def process_claim(
        self,
        envelope: FederatedClaimEnvelope,
        skip_replay_check: bool = False,
        skip_duplicate_check: bool = False,
        force_accept: bool = False,  # For testing only
    ) -> ClaimProcessingResult:
        """
        Process an inbound federated claim through the full pipeline.

        Pipeline:
        1. Normalize envelope
        2. Validate identity
        3. Verify signature
        4. Check replay protection
        5. Check duplicate suppression
        6. Persist inbound claim (if enabled)
        7. Run LocalQualificationEngine (if enabled)
        8. Run ContradictionAndPluralityManager (if enabled)
        9. Write audit trail
        10. Return processing result

        Args:
            envelope: The inbound claim envelope to process
            skip_replay_check: Skip replay protection check (testing)
            skip_duplicate_check: Skip duplicate check (testing)
            force_accept: Force acceptance regardless of validation (testing)

        Returns:
            ClaimProcessingResult with complete processing outcome
        """
        started_at = datetime.utcnow()
        envelope_id = envelope.envelope_id
        source_node = envelope.source_node_id

        self.logger.info(f"Processing inbound claim: {envelope_id} from {source_node}")

        # Initialize result
        result = ClaimProcessingResult(
            status="accepted",  # Will be updated by pipeline
            envelope_id=envelope_id,
            source_node_id=source_node,
            processing_started_at=started_at,
            processing_completed_at=started_at,
            processing_duration_ms=0.0,
        )

        try:
            # Step 1: Normalize envelope (validate structure)
            self._normalize_envelope(envelope)

            # Step 2: Validate identity
            identity_result = await self.identity_guard.validate_node_identity(
                node_id=envelope.source_node_id,
                credentials=self.identity_guard._node_registry.get(envelope.source_node_id),
            )
            result.identity_validation = identity_result

            # Step 3: Verify signature
            signature_result = await self.identity_guard.verify_artifact_signature(envelope)
            result.signature_verification = signature_result

            # Early rejection checks
            if not force_accept and not identity_result.is_valid:
                return self._reject_result(
                    result,
                    reason=f"Identity validation failed: {', '.join(identity_result.reasons)}"
                )

            if not force_accept and not signature_result.is_valid:
                return self._reject_result(
                    result,
                    reason=f"Signature verification failed: {', '.join(signature_result.reasons)}"
                )

            # Phase 1B Hardening: Run safeguards BEFORE trust evaluation
            # These provide early quality/context filtering

            # Safeguard 1: Eligibility Filter (quality gate)
            if self.config.enable_eligibility_filter and self.eligibility_filter:
                eligibility_result = self.eligibility_filter.check_claim_eligibility(
                    envelope.artifact,
                    envelope_id,
                    source_node,
                )
                result.eligibility_result = eligibility_result

                if not force_accept and not eligibility_result.is_eligible:
                    return self._reject_result(
                        result,
                        reason=f"Eligibility check failed: {', '.join(eligibility_result.rejection_reasons)}",
                        error_code="ELIGIBILITY_FAILED",
                    )

            # Safeguard 2: Context Similarity Engine (prevent context collapse)
            if self.config.enable_context_similarity and self.similarity_engine:
                similarity_result = self.similarity_engine.analyze_claim(
                    envelope.artifact,
                    envelope_id,
                    source_node,
                )
                result.similarity_result = similarity_result

                if not force_accept and similarity_result.should_throttle:
                    return self._quarantine_result(
                        result,
                        reasons=[
                            f"Context monoculture risk detected in {similarity_result.risk_profile.risk_level} state",
                            f"Diversity score: {similarity_result.risk_profile.diversity_score:.2f}",
                        ] + similarity_result.risk_profile.recommendations,
                    )

            # Safeguard 3: Plurality Preservation (prevent knowledge monoculture)
            if self.config.enable_plurality_preservation and self.plurality_rules:
                plurality_result = self.plurality_rules.analyze_claim(
                    envelope.artifact,
                    envelope_id,
                    source_node,
                )
                result.plurality_result = plurality_result

                if not force_accept and plurality_result.assessment.plurality_level == "monoculture":
                    return self._quarantine_result(
                        result,
                        reasons=[
                            f"Knowledge monoculture detected in {plurality_result.topic_domain} domain",
                        ] + plurality_result.assessment.recommendations,
                    )

            # Step 4: Replay protection
            if self.config.enable_replay_protection and not skip_replay_check:
                try:
                    replay_result = await self.replay_protection.check_envelope(envelope)
                    result.replay_protection = replay_result
                except ReplayAttackError as e:
                    result.replay_protection = ReplayProtectionResult(
                        is_replay=True,
                        envelope_id=envelope_id,
                        check_type="unknown",
                        blocked_reason=str(e),
                    )
                    if self.config.block_replays:
                        return self._reject_result(
                            result,
                            reason=f"Replay attack detected: {e.message}",
                            error_code="REPLAY_ATTACK",
                        )

            # Step 5: Duplicate suppression
            duplicate_result = None
            if self.config.enable_duplicate_suppression and not skip_duplicate_check:
                duplicate_result = await self.duplicate_suppression.check_claim(envelope)
                result.duplicate_suppression = duplicate_result

                if duplicate_result.is_duplicate and self.config.quarantine_duplicates:
                    return self._quarantine_result(
                        result,
                        reasons=[
                            f"Duplicate of claim {duplicate_result.existing_envelope_id}",
                            f"Previously seen at {duplicate_result.first_seen}",
                        ]
                    )

            # Step 6: Trust evaluation
            trust_decision = await self.identity_guard.evaluate_inbound_trust(envelope)
            result.trust_decision = trust_decision

            if not force_accept:
                if trust_decision.decision == "reject" or trust_decision.decision == "reject_and_flag":
                    return self._reject_result(
                        result,
                        reason=f"Trust evaluation rejected: {trust_decision.decision}",
                    )
                if trust_decision.decision == "quarantine":
                    return self._quarantine_result(
                        result,
                        reasons=trust_decision.reasons,
                    )

            # Phase 1B Hardening: Post-trust safeguards
            # These use trust score to make allocative and decay decisions

            # Safeguard 4: Allocative Boundary Guard (prevent authority concentration)
            if self.config.enable_allocative_boundaries and self.allocative_guard:
                allocative_result = self.allocative_guard.evaluate_claim(
                    envelope.artifact,
                    envelope_id,
                    source_node,
                    trust_score=trust_decision.effective_trust,
                )
                result.allocative_result = allocative_result

                if not force_accept and not allocative_result.is_allowed:
                    return self._reject_result(
                        result,
                        reason=f"Allocative boundary exceeded: {', '.join(allocative_result.reasons)}",
                        error_code="ALLOCATIVE_BOUNDARY_EXCEEDED",
                    )

                # Apply throttle if recommended
                if not force_accept and allocative_result.throttle_factor < 1.0:
                    # Adjust trust based on allocative throttle
                    trust_decision.effective_trust *= allocative_result.throttle_factor
                    self.logger.info(
                        f"Applied allocative throttle: {allocative_result.throttle_factor:.2f} "
                        f"to node {source_node}"
                    )

            # Safeguard 5: Trust Decay Model (detect trust drift)
            if self.config.enable_trust_decay and self.trust_decay:
                trust_decay_result = self.trust_decay.assess_trust_decay(
                    envelope.artifact,
                    envelope_id,
                    source_node,
                    current_trust=trust_decision.effective_trust,
                    claim_accepted=(result.status != "rejected"),
                )
                result.trust_decay_result = trust_decay_result

                if not force_accept and trust_decay_result.recommendation == "reject":
                    return self._reject_result(
                        result,
                        reason=f"Trust decay assessment rejected: {', '.join(trust_decay_result.reasons)}",
                        error_code="TRUST_DECAY_REJECTED",
                    )

                # Use adjusted trust from decay model
                if not force_accept and trust_decay_result.adjusted_trust != trust_decay_result.current_trust:
                    trust_decision.effective_trust = trust_decay_result.adjusted_trust
                    self.logger.info(
                        f"Applied trust decay adjustment: "
                        f"{trust_decay_result.current_trust:.2f} -> {trust_decay_result.adjusted_trust:.2f} "
                        f"for node {source_node}"
                    )

            # Steps 7-8: Qualification and contradiction (placeholders for Phase 1B)
            if self.config.enable_qualification:
                result.qualification_score = await self._run_qualification(envelope)

            if self.config.enable_contradiction_check:
                contradiction_result = await self._run_contradiction_check(envelope)
                result.contradiction_count = contradiction_result.get("count", 0)
                result.plurality_status = contradiction_result.get("status")

            # Step 9: Persistence (placeholder for Phase 1B)
            if self.config.enable_persistence:
                result.persisted_claim_id = await self._persist_claim(envelope, result)

            # Register as seen (after all validations pass)
            if self.config.enable_replay_protection:
                self.replay_protection.mark_envelope_seen(envelope)

            if self.config.enable_duplicate_suppression:
                claim_id = self.duplicate_suppression.register_claim(envelope)
                result.claim_id = claim_id

            # Step 10: Audit logging
            if self.config.enable_audit_logging:
                audit_ids = await self._write_audit_trail(envelope, result)
                result.audit_event_ids = audit_ids

            # Success - claim accepted
            result.status = "accepted"
            self._accepted_count += 1

        except FederationError as e:
            self.logger.error(f"Federation error processing claim {envelope_id}: {e}")
            result.error_code = e.__class__.__name__
            result.error_message = e.message
            result.status = "rejected"
            self._rejected_count += 1

        except Exception as e:
            self.logger.exception(f"Unexpected error processing claim {envelope_id}: {e}")
            result.error_code = "PROCESSING_ERROR"
            result.error_message = str(e)
            result.status = "rejected"
            self._rejected_count += 1

        finally:
            # Finalize result
            result.processing_completed_at = datetime.utcnow()
            result.processing_duration_ms = (
                result.processing_completed_at - result.processing_started_at
            ).total_seconds() * 1000

            self._total_processed += 1

            self.logger.info(
                f"Completed processing claim {envelope_id}: "
                f"status={result.status}, duration={result.processing_duration_ms:.2f}ms"
            )

        return result

    def _normalize_envelope(self, envelope: FederatedClaimEnvelope) -> None:
        """
        Normalize and validate envelope structure.

        Args:
            envelope: The envelope to normalize

        Raises:
            ValueError: If envelope structure is invalid
        """
        # Pydantic validation happens on model construction
        # This is a hook for additional normalization if needed
        pass

    def _reject_result(
        self,
        result: ClaimProcessingResult,
        reason: str,
        error_code: str | None = None,
    ) -> ClaimProcessingResult:
        """
        Update result to indicate rejection.

        Args:
            result: The result to update
            reason: Rejection reason
            error_code: Optional error code

        Returns:
            Updated result with rejection status
        """
        result.status = "rejected"
        result.rejection_reason = reason
        result.error_code = error_code
        self._rejected_count += 1
        return result

    def _quarantine_result(
        self,
        result: ClaimProcessingResult,
        reasons: list[str],
    ) -> ClaimProcessingResult:
        """
        Update result to indicate quarantine.

        Args:
            result: The result to update
            reasons: List of quarantine reasons

        Returns:
            Updated result with quarantine status
        """
        result.status = "quarantined"
        result.quarantine_reasons = reasons
        self._quarantined_count += 1
        return result

    async def _run_qualification(self, envelope: FederatedClaimEnvelope) -> float:
        """
        Run LocalQualificationEngine on the claim.

        Phase 1B: Placeholder - will integrate with actual engine.

        Args:
            envelope: The envelope to qualify

        Returns:
            Qualification score (0.0 - 1.0)
        """
        # Phase 1B: Return a default qualification score
        # Phase 1C: Integrate with LocalQualificationEngine
        return envelope.artifact.confidence

    async def _run_contradiction_check(self, envelope: FederatedClaimEnvelope) -> dict[str, Any]:
        """
        Run ContradictionAndPluralityManager on the claim.

        Phase 1B: Placeholder - will integrate with actual manager.

        Args:
            envelope: The envelope to check

        Returns:
            Dictionary with contradiction check results
        """
        # Phase 1B: Return default results
        # Phase 1C: Integrate with ContradictionAndPluralityManager
        return {
            "count": 0,
            "status": "no_contradictions",
        }

    async def _persist_claim(
        self,
        envelope: FederatedClaimEnvelope,
        result: ClaimProcessingResult,
    ) -> str:
        """
        Persist the claim to storage.

        Phase 1B: Placeholder - will integrate with actual persistence.

        Args:
            envelope: The envelope to persist
            result: Processing result

        Returns:
            ID of persisted claim record
        """
        # Phase 1B: Return a placeholder ID
        # Phase 1C: Integrate with persistence layer
        return f"persisted_{envelope.envelope_id}"

    async def _write_audit_trail(
        self,
        envelope: FederatedClaimEnvelope,
        result: ClaimProcessingResult,
    ) -> list[str]:
        """
        Write audit trail entries for the processing.

        Args:
            envelope: The processed envelope
            result: Processing result

        Returns:
            List of audit event IDs
        """
        # Phase 1B: Log to logger
        # Phase 1C: Integrate with audit service
        event_id = f"audit_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{envelope.envelope_id[:8]}"
        self.logger.info(
            f"Audit: {event_id} - envelope={envelope.envelope_id}, "
            f"status={result.status}, source={envelope.source_node_id}"
        )
        return [event_id]

    def get_statistics(self) -> dict[str, Any]:
        """
        Get processor statistics.

        Returns:
            Dictionary with processor metrics
        """
        uptime = (datetime.utcnow() - self._processor_started_at).total_seconds()

        stats = {
            "totalProcessed": self._total_processed,
            "acceptedCount": self._accepted_count,
            "quarantinedCount": self._quarantined_count,
            "rejectedCount": self._rejected_count,
            "acceptRate": self._accepted_count / max(self._total_processed, 1),
            "uptimeSeconds": uptime,
            "processorStartedAt": self._processor_started_at.isoformat(),
            "replayProtection": self.replay_protection.get_statistics() if self.config.enable_replay_protection else None,
            "duplicateSuppression": self.duplicate_suppression.get_statistics() if self.config.enable_duplicate_suppression else None,
            # Phase 1B Hardening: Safeguard statistics
            "eligibilityFilter": self.eligibility_filter.get_statistics() if self.eligibility_filter else None,
            "similarityEngine": self.similarity_engine.get_statistics() if self.similarity_engine else None,
            "pluralityRules": self.plurality_rules.get_statistics() if self.plurality_rules else None,
            "allocativeGuard": self.allocative_guard.get_statistics() if self.allocative_guard else None,
            "trustDecay": self.trust_decay.get_statistics() if self.trust_decay else None,
        }

        return stats


def create_inbound_claim_processor(
    identity_guard: FederationIdentityGuard | None = None,
    replay_protection: ReplayProtectionService | None = None,
    duplicate_suppression: DuplicateSuppressionService | None = None,
    config: ProcessorConfig | None = None,
    federation_config: FederationConfig | None = None,
    # Phase 1B Hardening: Safeguard parameters
    eligibility_filter: FederationEligibilityFilter | None = None,
    similarity_engine: ContextSimilarityEngine | None = None,
    plurality_rules: PluralityPreservationRules | None = None,
    allocative_guard: AllocativeBoundaryGuard | None = None,
    trust_decay: TrustDecayModel | None = None,
) -> InboundFederatedClaimProcessor:
    """
    Factory function to create an InboundFederatedClaimProcessor.

    Args:
        identity_guard: Identity validation service (created if None)
        replay_protection: Replay protection service (created if None)
        duplicate_suppression: Duplicate suppression service (created if None)
        config: Processor configuration
        federation_config: Federation layer configuration
        eligibility_filter: Eligibility filter safeguard (created if None and enabled)
        similarity_engine: Context similarity engine safeguard (created if None and enabled)
        plurality_rules: Plurality preservation rules safeguard (created if None and enabled)
        allocative_guard: Allocative boundary guard safeguard (created if None and enabled)
        trust_decay: Trust decay model safeguard (created if None and enabled)

    Returns:
        Configured InboundFederatedClaimProcessor instance
    """
    from torq_console.layer12.federation.federation_identity_guard import create_identity_guard

    if identity_guard is None:
        identity_guard = create_identity_guard(config=federation_config)

    return InboundFederatedClaimProcessor(
        identity_guard=identity_guard,
        replay_protection=replay_protection,
        duplicate_suppression=duplicate_suppression,
        config=config,
        federation_config=federation_config,
        eligibility_filter=eligibility_filter,
        similarity_engine=similarity_engine,
        plurality_rules=plurality_rules,
        allocative_guard=allocative_guard,
        trust_decay=trust_decay,
    )
