"""
Federation Eligibility Filter

Phase 1B Hardening - Prevent insight flood and low-quality content.

This filter validates claims BEFORE they are federated, ensuring:
- Claim quality meets minimum thresholds
- Sender is not flooding the network
- Content is relevant to federation scope
- Spam and abuse patterns are blocked

Without this safeguard, the federation layer could be overwhelmed
by low-quality or malicious content, degrading the value of collective intelligence.
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Literal
from pydantic import BaseModel, Field

from torq_console.layer12.federation.types import FederatedArtifactPayload, FederatedClaimEnvelope

logger = logging.getLogger(__name__)


# ============================================================================
# Eligibility Criteria
# ============================================================================

class EligibilityCriteria(BaseModel):
    """Criteria for federation eligibility."""

    # Content quality thresholds
    min_confidence: float = Field(0.3, ge=0.0, le=1.0, description="Minimum confidence score")
    min_claim_length: int = Field(20, ge=0, description="Minimum claim text length")
    max_claim_length: int = Field(5000, ge=0, description="Maximum claim text length")
    require_provenance: bool = Field(True, description="Require provenance score")

    # Relevance thresholds
    required_tags: list[str] = Field(
        default_factory=list,
        description="Required tags (empty = no tag requirement)"
    )
    allowed_artifact_types: list[str] = Field(
        default_factory=lambda: ["insight", "pattern", "strategy"],
        description="Allowed artifact types"
    )

    # Anti-spam thresholds
    max_claims_per_minute: int = Field(10, ge=1, description="Rate limit per node")
    max_similarity_score: float = Field(
        0.95, ge=0.0, le=1.0,
        description="Max similarity to existing claims (prevent duplicates)"
    )
    spam_keywords: list[str] = Field(
        default_factory=lambda: [
            "buy now", "click here", "free money", "urgent act",
            "limited time", "subscribe now", "winner notification"
        ],
        description="Keywords that indicate spam"
    )


class EligibilityResult(BaseModel):
    """Result of an eligibility check."""

    is_eligible: bool = Field(..., description="Whether the claim is eligible for federation")
    claim_id: str = Field(..., description="Artifact ID")
    envelope_id: str = Field(..., description="Envelope ID")
    source_node_id: str = Field(..., description="Source node ID")
    checked_at: datetime = Field(default_factory=datetime.utcnow, description="When checked")

    # Rejection reasons
    rejection_reasons: list[str] = Field(
        default_factory=list,
        description="Why the claim was rejected"
    )

    # Score breakdown
    confidence_score: float | None = None
    claim_length_score: float | None = None
    provenance_score: float | None = None
    spam_score: float | None = None
    overall_score: float | None = None

    # Rate limit info
    rate_limit_status: str | None = None  # "ok", "warning", "blocked"
    remaining_quota: int | None = None


# ============================================================================
# Rate Limiting
# ============================================================================

class NodeRateTracker:
    """Track claim submission rates per node."""

    def __init__(
        self,
        max_claims_per_minute: int = 10,
        window_seconds: int = 60,
    ):
        self.max_claims_per_minute = max_claims_per_minute
        self.window_seconds = window_seconds
        self._node_submissions: dict[str, list[datetime]] = defaultdict(list)

    def is_rate_limited(self, node_id: str) -> tuple[bool, int]:
        """
        Check if a node is rate limited.

        Returns:
            Tuple of (is_limited, remaining_quota)
        """
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window_seconds)

        # Clean old submissions
        self._node_submissions[node_id] = [
            ts for ts in self._node_submissions[node_id]
            if ts > window_start
        ]

        # Check quota
        submission_count = len(self._node_submissions[node_id])
        remaining = max(0, self.max_claims_per_minute - submission_count)

        if submission_count >= self.max_claims_per_minute:
            return True, 0

        return False, remaining

    def record_submission(self, node_id: str) -> None:
        """Record a claim submission from a node."""
        self._node_submissions[node_id].append(datetime.utcnow())

    def get_statistics(self) -> dict[str, int]:
        """Get rate limiting statistics."""
        return {
            "tracked_nodes": len(self._node_submissions),
            "total_submissions": sum(len(v) for v in self._node_submissions.values()),
        }


# ============================================================================
# Eligibility Filter Service
# ============================================================================

class FederationEligibilityFilter:
    """
    Filters federation claims to prevent insight flood and low-quality content.

    This is the FIRST safeguard in the inbound pipeline.
    Claims must pass this filter BEFORE trust evaluation.
    """

    def __init__(
        self,
        criteria: EligibilityCriteria | None = None,
    ):
        """
        Initialize the eligibility filter.

        Args:
            criteria: Eligibility criteria
        """
        self.criteria = criteria or EligibilityCriteria()
        self.logger = logging.getLogger(__name__)

        # Rate limiter
        self._rate_tracker = NodeRateTracker(
            max_claims_per_minute=self.criteria.max_claims_per_minute,
        )

        # Similarity tracking (prevent near-duplicates)
        self._claim_hashes: dict[str, datetime] = {}

        # Statistics
        self._total_checked = 0
        self._total_passed = 0
        self._total_blocked = 0

    def check_claim_eligibility(
        self,
        artifact: FederatedArtifactPayload,
        envelope_id: str,
        source_node_id: str,
    ) -> EligibilityResult:
        """
        Check if a claim is eligible for federation.

        Args:
            artifact: The artifact payload to check
            envelope_id: Envelope ID
            source_node_id: Source node ID

        Returns:
            EligibilityResult with eligibility status
        """
        self._total_checked += 1

        reasons: list[str] = []
        scores: dict[str, float] = {}

        # 1. Check content quality
        confidence_score = self._check_confidence(artifact, reasons, scores)
        claim_length_score = self._check_claim_length(artifact, reasons, scores)
        provenance_score = self._check_provenance(artifact, reasons, scores)

        # 2. Check relevance
        self._check_artifact_type(artifact, reasons)
        self._check_required_tags(artifact, reasons)

        # 3. Check spam patterns
        spam_score = self._check_spam_patterns(artifact, reasons, scores)

        # 4. Check rate limiting
        is_rate_limited, remaining_quota = self._rate_tracker.is_rate_limited(source_node_id)
        if is_rate_limited:
            reasons.append(f"Rate limit exceeded: {self.criteria.max_claims_per_minute} claims per minute")
        scores["rate_limit_remaining"] = float(remaining_quota)

        # 5. Check similarity (near-duplicate prevention)
        similarity_score = self._check_similarity(artifact, envelope_id, reasons, scores)

        # Calculate overall score
        overall_score = self._calculate_overall_score(scores)

        # Determine eligibility
        is_eligible = (
            len(reasons) == 0 and
            not is_rate_limited and
            overall_score >= 0.5
        )

        # Record statistics
        if is_eligible:
            self._total_passed += 1
            self._rate_tracker.record_submission(source_node_id)
        else:
            self._total_blocked += 1

        # Build result
        result = EligibilityResult(
            is_eligible=is_eligible,
            claim_id=artifact.artifact_id,
            envelope_id=envelope_id,
            source_node_id=source_node_id,
            rejection_reasons=reasons,
            confidence_score=confidence_score,
            claim_length_score=claim_length_score,
            provenance_score=provenance_score,
            spam_score=spam_score,
            overall_score=overall_score,
            rate_limit_status="blocked" if is_rate_limited else "ok",
            remaining_quota=remaining_quota,
        )

        self.logger.info(
            f"Eligibility check for {artifact.artifact_id}: "
            f"eligible={is_eligible}, score={overall_score:.2f}"
        )

        return result

    def _check_confidence(
        self,
        artifact: FederatedArtifactPayload,
        reasons: list[str],
        scores: dict[str, float],
    ) -> float:
        """Check confidence threshold."""
        if artifact.confidence < self.criteria.min_confidence:
            reasons.append(
                f"Confidence {artifact.confidence:.2f} below minimum {self.criteria.min_confidence}"
            )
        scores["confidence"] = artifact.confidence
        return artifact.confidence

    def _check_claim_length(
        self,
        artifact: FederatedArtifactPayload,
        reasons: list[str],
        scores: dict[str, float],
    ) -> float:
        """Check claim length is within bounds."""
        length = len(artifact.claim_text)
        score = 1.0

        if length < self.criteria.min_claim_length:
            reasons.append(f"Claim too short: {length} < {self.criteria.min_claim_length}")
            score = 0.0
        elif length > self.criteria.max_claim_length:
            reasons.append(f"Claim too long: {length} > {self.criteria.max_claim_length}")
            score = 0.5
        elif length > 2000:
            # Prefer concise claims
            score = 0.8

        scores["claim_length"] = score
        return score

    def _check_provenance(
        self,
        artifact: FederatedArtifactPayload,
        reasons: list[str],
        scores: dict[str, float],
    ) -> float:
        """Check provenance score."""
        if self.criteria.require_provenance:
            if artifact.provenance_score is None:
                reasons.append("Missing provenance score")
                scores["provenance"] = 0.0
                return 0.0

            if artifact.provenance_score < 0.5:
                reasons.append(f"Low provenance score: {artifact.provenance_score:.2f}")
                scores["provenance"] = artifact.provenance_score
                return artifact.provenance_score

        scores["provenance"] = artifact.provenance_score or 0.0
        return scores["provenance"]

    def _check_artifact_type(
        self,
        artifact: FederatedArtifactPayload,
        reasons: list[str],
    ) -> None:
        """Check artifact type is allowed."""
        if artifact.artifact_type not in self.criteria.allowed_artifact_types:
            reasons.append(
                f"Artifact type '{artifact.artifact_type}' not allowed. "
                f"Allowed: {', '.join(self.criteria.allowed_artifact_types)}"
            )

    def _check_required_tags(
        self,
        artifact: FederatedArtifactPayload,
        reasons: list[str],
    ) -> None:
        """Check required tags are present."""
        if self.criteria.required_tags:
            missing_tags = set(self.criteria.required_tags) - set(artifact.tags)
            if missing_tags:
                reasons.append(f"Missing required tags: {', '.join(missing_tags)}")

    def _check_spam_patterns(
        self,
        artifact: FederatedArtifactPayload,
        reasons: list[str],
        scores: dict[str, float],
    ) -> float:
        """Check for spam patterns."""
        spam_score = 0.0
        claim_lower = artifact.claim_text.lower()
        title_lower = artifact.title.lower()

        for keyword in self.criteria.spam_keywords:
            if keyword in claim_lower or keyword in title_lower:
                spam_score += 0.2

        # Check for excessive capitalization
        if sum(1 for c in artifact.title if c.isupper()) / len(artifact.title) > 0.5:
            spam_score += 0.1

        # Check for excessive punctuation
        punctuation_count = sum(1 for c in artifact.claim_text if c in '!?.*')
        if punctuation_count / len(artifact.claim_text) > 0.1:
            spam_score += 0.1

        if spam_score > 0.3:
            reasons.append(f"Spam patterns detected (score: {spam_score:.2f})")

        scores["spam"] = 1.0 - spam_score
        return spam_score

    def _check_similarity(
        self,
        artifact: FederatedArtifactPayload,
        envelope_id: str,
        reasons: list[str],
        scores: dict[str, float],
    ) -> float:
        """Check for similarity to existing claims."""
        import hashlib

        # Create content hash
        content = f"{artifact.claim_text.lower().strip()}|{artifact.artifact_type}"
        claim_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        # Clean old hashes
        cutoff = datetime.utcnow() - timedelta(hours=24)
        self._claim_hashes = {
            k: v for k, v in self._claim_hashes.items()
            if v > cutoff
        }

        # Check for near-duplicate
        if claim_hash in self._claim_hashes:
            reasons.append(f"Very similar to recently published claim")
            scores["similarity"] = 0.0
            return 0.0

        self._claim_hashes[claim_hash] = datetime.utcnow()
        scores["similarity"] = 1.0
        return 1.0

    def _calculate_overall_score(self, scores: dict[str, float]) -> float:
        """Calculate overall eligibility score."""
        weights = {
            "confidence": 0.3,
            "claim_length": 0.2,
            "provenance": 0.2,
            "spam": 0.2,
            "similarity": 0.1,
        }

        weighted_sum = sum(
            scores.get(key, 0.0) * weight
            for key, weight in weights.items()
        )

        return weighted_sum

    def get_statistics(self) -> dict:
        """Get filter statistics."""
        return {
            "totalChecked": self._total_checked,
            "totalPassed": self._total_passed,
            "totalBlocked": self._total_blocked,
            "passRate": self._total_passed / max(self._total_checked, 1),
            "rateLimitStats": self._rate_tracker.get_statistics(),
        }


def create_eligibility_filter(
    criteria: EligibilityCriteria | None = None,
) -> FederationEligibilityFilter:
    """
    Factory function to create a FederationEligibilityFilter.

    Args:
        criteria: Eligibility criteria

    Returns:
        Configured FederationEligibilityFilter instance
    """
    return FederationEligibilityFilter(criteria=criteria)
