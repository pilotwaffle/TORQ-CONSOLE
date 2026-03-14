"""
Duplicate Suppression for Federation Layer

Phase 1B - Detect and suppress duplicate federated claims.

Duplicate suppression prevents the same artifact claim from being
processed multiple times. This is different from replay protection:
- Replay protection: exact same envelope re-submitted
- Duplicate suppression: same claim content submitted in different envelopes

For example, two different nodes might submit the same insight.
We want to process it once and track that it came from multiple sources.
"""

import hashlib
import logging
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel, Field

from torq_console.layer12.federation.types import FederatedClaimEnvelope, FederatedArtifactPayload
from torq_console.layer12.federation.errors import DuplicateSuppressionError

logger = logging.getLogger(__name__)


class DuplicateSuppressionResult(BaseModel):
    """Result of a duplicate suppression check."""

    is_duplicate: bool = Field(..., description="Whether the claim was detected as a duplicate")
    claim_id: str = Field(..., description="The claim ID that was checked")
    envelope_id: str = Field(..., description="The envelope ID that was checked")
    existing_envelope_id: str | None = Field(None, description="The existing envelope ID if duplicate")
    first_seen: datetime | None = Field(None, description="When this claim was first seen")
    source_count: int = Field(0, description="Number of sources for this claim")
    sources: list[str] = Field(default_factory=list, description="List of source node IDs")


class ClaimRecord:
    """Record of a processed claim."""

    def __init__(
        self,
        claim_id: str,
        first_envelope_id: str,
        first_source_node: str,
        first_seen: datetime,
        artifact_payload: FederatedArtifactPayload,
    ):
        self.claim_id = claim_id
        self.first_envelope_id = first_envelope_id
        self.first_source_node = first_source_node
        self.first_seen = first_seen
        self.artifact_payload = artifact_payload
        self.source_nodes: dict[str, datetime] = {first_source_node: first_seen}
        self.envelope_ids: list[str] = [first_envelope_id]
        self.processing_count = 1

    def add_source(self, envelope_id: str, source_node: str, seen_at: datetime) -> None:
        """Add a new source for this claim."""
        if source_node not in self.source_nodes:
            self.source_nodes[source_node] = seen_at
        if envelope_id not in self.envelope_ids:
            self.envelope_ids.append(envelope_id)
        self.processing_count += 1

    def to_summary(self) -> dict[str, Any]:
        """Get a summary of the claim record."""
        return {
            "claimId": self.claim_id,
            "firstEnvelopeId": self.first_envelope_id,
            "firstSourceNode": self.first_source_node,
            "firstSeen": self.first_seen.isoformat(),
            "sourceCount": len(self.source_nodes),
            "sources": list(self.source_nodes.keys()),
            "processingCount": self.processing_count,
            "artifactType": self.artifact_payload.artifact_type,
            "title": self.artifact_payload.title,
        }


class DuplicateSuppressionConfig:
    """Configuration for duplicate suppression."""

    def __init__(
        self,
        max_tracked_claims: int = 50000,
        claim_ttl_seconds: int = 604800,  # 7 days
        enable_content_hash: bool = True,
        enable_semantic_hash: bool = False,  # Future: use embeddings
        include_context_in_hash: bool = False,
        include_tags_in_hash: bool = True,
    ):
        """
        Initialize duplicate suppression configuration.

        Args:
            max_tracked_claims: Maximum number of claims to track
            claim_ttl_seconds: Time before claim records expire
            enable_content_hash: Whether to use content-based hashing
            enable_semantic_hash: Whether to use semantic similarity
            include_context_in_hash: Whether to include context in hash
            include_tags_in_hash: Whether to include tags in hash
        """
        self.max_tracked_claims = max_tracked_claims
        self.claim_ttl_seconds = claim_ttl_seconds
        self.enable_content_hash = enable_content_hash
        self.enable_semantic_hash = enable_semantic_hash
        self.include_context_in_hash = include_context_in_hash
        self.include_tags_in_hash = include_tags_in_hash


class DuplicateSuppressionService:
    """
    Service to detect and suppress duplicate claim processing.

    Uses content-based hashing to identify duplicate claims even when
    they come from different nodes in different envelopes.

    Tracks:
    - Content hashes of processed claims
    - Source nodes that submitted each claim
    - Processing statistics
    """

    def __init__(self, config: DuplicateSuppressionConfig | None = None):
        """
        Initialize the duplicate suppression service.

        Args:
            config: Configuration for duplicate suppression behavior
        """
        self.config = config or DuplicateSuppressionConfig()
        self.logger = logging.getLogger(__name__)

        # Track claim_id -> ClaimRecord
        self._claims: OrderedDict[str, ClaimRecord] = OrderedDict()

        # Track content_hash -> claim_id (for reverse lookup)
        self._content_hashes: dict[str, str] = {}

        # Statistics
        self._total_checked = 0
        self._duplicates_detected = 0
        self._unique_claims_processed = 0
        self._service_started_at = datetime.utcnow()

    def _compute_content_hash(self, artifact: FederatedArtifactPayload) -> str:
        """
        Compute a content-based hash for duplicate detection.

        The hash includes:
        - claim_text (the core assertion)
        - artifact_type (type categorization)
        - origin_layer (source layer)
        - tags (if enabled)
        - context (if enabled)

        This allows us to detect the same claim even if:
        - It comes from a different node
        - It has a different artifact_id
        - It has slightly different metadata

        Args:
            artifact: The artifact payload to hash

        Returns:
            Hex string hash of the content
        """
        hash_parts = [
            artifact.claim_text.strip().lower(),
            artifact.artifact_type.lower(),
            artifact.origin_layer.lower(),
        ]

        if self.config.include_tags_in_hash and artifact.tags:
            # Sort tags for consistent hashing
            hash_parts.append(",".join(sorted(artifact.tags)))

        if self.config.include_context_in_hash and artifact.context:
            # Use sorted keys for consistent hashing
            context_str = ",".join(f"{k}:{v}" for k, v in sorted(artifact.context.items()))
            hash_parts.append(context_str)

        hash_input = "|".join(hash_parts)
        return hashlib.sha256(hash_input.encode()).hexdigest()

    def _generate_claim_id(self, artifact: FederatedArtifactPayload, content_hash: str) -> str:
        """
        Generate a stable claim ID for an artifact.

        The claim ID is derived from the content hash, ensuring that
        the same claim always gets the same ID.

        Args:
            artifact: The artifact payload
            content_hash: Pre-computed content hash

        Returns:
            Stable claim ID
        """
        # Use first 12 characters of content hash as claim ID
        return f"claim_{content_hash[:12]}"

    def _cleanup_expired_entries(self) -> None:
        """Remove expired claim records."""
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.config.claim_ttl_seconds)

        # Find expired claims
        expired_claims = [
            claim_id for claim_id, record in self._claims.items()
            if record.first_seen < cutoff
        ]

        # Remove expired claims
        for claim_id in expired_claims:
            record = self._claims.pop(claim_id, None)
            if record:
                # Also remove content hash mapping
                content_hash = self._compute_content_hash(record.artifact_payload)
                self._content_hashes.pop(content_hash, None)

        # Enforce LRU limit
        while len(self._claims) > self.config.max_tracked_claims:
            self._claims.popitem(last=False)

    async def check_claim(
        self,
        envelope: FederatedClaimEnvelope,
    ) -> DuplicateSuppressionResult:
        """
        Check if a claim is a duplicate.

        Args:
            envelope: The envelope containing the claim to check

        Returns:
            DuplicateSuppressionResult indicating if this is a duplicate

        Raises:
            DuplicateSuppressionError: If processing should be blocked
                (note: we may want to allow tracking duplicates from
                multiple sources rather than blocking them)
        """
        self._total_checked += 1

        # Clean up expired entries
        self._cleanup_expired_entries()

        # Compute content hash
        content_hash = self._compute_content_hash(envelope.artifact)
        claim_id = self._generate_claim_id(envelope.artifact, content_hash)

        # Check if we've seen this claim before
        existing_record = self._claims.get(claim_id)

        if existing_record is None:
            # New claim
            return DuplicateSuppressionResult(
                is_duplicate=False,
                claim_id=claim_id,
                envelope_id=envelope.envelope_id,
                source_count=1,
                sources=[envelope.source_node_id],
            )

        # Existing claim found
        self._duplicates_detected += 1

        # Add this as a new source
        existing_record.add_source(
            envelope_id=envelope.envelope_id,
            source_node=envelope.source_node_id,
            seen_at=datetime.utcnow(),
        )

        # Update LRU
        self._claims.move_to_end(claim_id)

        self.logger.info(
            f"Duplicate claim detected: {claim_id} "
            f"from {envelope.source_node_id} "
            f"(sources: {len(existing_record.source_nodes)})"
        )

        # Return result - we don't raise an error because we want to
        # track claims from multiple sources
        return DuplicateSuppressionResult(
            is_duplicate=True,
            claim_id=claim_id,
            envelope_id=envelope.envelope_id,
            existing_envelope_id=existing_record.first_envelope_id,
            first_seen=existing_record.first_seen,
            source_count=len(existing_record.source_nodes),
            sources=list(existing_record.source_nodes.keys()),
        )

    def register_claim(
        self,
        envelope: FederatedClaimEnvelope,
        claim_id: str | None = None,
    ) -> str:
        """
        Register a new claim as processed.

        Call this after the claim has passed validation and is being
        integrated into the system.

        Args:
            envelope: The envelope containing the claim
            claim_id: Optional pre-computed claim ID

        Returns:
            The claim ID for this claim
        """
        now = datetime.utcnow()

        # Compute content hash and claim ID
        content_hash = self._compute_content_hash(envelope.artifact)
        if claim_id is None:
            claim_id = self._generate_claim_id(envelope.artifact, content_hash)

        # Check if already exists
        if claim_id in self._claims:
            # Update existing record
            record = self._claims[claim_id]
            record.add_source(
                envelope_id=envelope.envelope_id,
                source_node=envelope.source_node_id,
                seen_at=now,
            )
            self._claims.move_to_end(claim_id)
            self.logger.debug(f"Updated existing claim record: {claim_id}")
        else:
            # Create new record
            record = ClaimRecord(
                claim_id=claim_id,
                first_envelope_id=envelope.envelope_id,
                first_source_node=envelope.source_node_id,
                first_seen=now,
                artifact_payload=envelope.artifact,
            )
            self._claims[claim_id] = record
            self._content_hashes[content_hash] = claim_id
            self._unique_claims_processed += 1
            self.logger.info(f"Registered new claim: {claim_id}")

        return claim_id

    def get_claim_record(self, claim_id: str) -> ClaimRecord | None:
        """
        Get the record for a claim.

        Args:
            claim_id: The claim ID to look up

        Returns:
            ClaimRecord if found, None otherwise
        """
        return self._claims.get(claim_id)

    def get_statistics(self) -> dict:
        """
        Get duplicate suppression statistics.

        Returns:
            Dictionary with duplicate suppression metrics
        """
        uptime = (datetime.utcnow() - self._service_started_at).total_seconds()

        return {
            "totalChecked": self._total_checked,
            "duplicatesDetected": self._duplicates_detected,
            "uniqueClaimsProcessed": self._unique_claims_processed,
            "duplicateRate": self._duplicates_detected / max(self._total_checked, 1),
            "trackedClaims": len(self._claims),
            "trackedContentHashes": len(self._content_hashes),
            "uptimeSeconds": uptime,
            "serviceStartedAt": self._service_started_at.isoformat(),
        }

    def reset_statistics(self) -> None:
        """Reset duplicate suppression statistics."""
        self._total_checked = 0
        self._duplicates_detected = 0

    def clear_tracking(self) -> None:
        """Clear all tracking data (use with caution)."""
        self._claims.clear()
        self._content_hashes.clear()
        self.logger.warning("Cleared all duplicate suppression tracking data")

    def get_recent_claims(self, limit: int = 100) -> list[dict]:
        """
        Get recently processed claims.

        Args:
            limit: Maximum number of claims to return

        Returns:
            List of claim summaries
        """
        recent = list(reversed(list(self._claims.values())))[:limit]
        return [record.to_summary() for record in recent]


def create_duplicate_suppression(
    config: DuplicateSuppressionConfig | None = None,
) -> DuplicateSuppressionService:
    """
    Factory function to create a DuplicateSuppressionService.

    Args:
        config: Configuration for duplicate suppression

    Returns:
        Configured DuplicateSuppressionService instance
    """
    return DuplicateSuppressionService(config=config)
