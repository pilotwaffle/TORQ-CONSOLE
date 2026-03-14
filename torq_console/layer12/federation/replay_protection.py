"""
Replay Protection for Federation Layer

Phase 1B - Detect and block replayed federated envelopes.

Replay attacks occur when a malicious actor resends a previously
valid envelope to trick the system into re-processing it. This
module tracks seen envelopes and signatures to prevent such attacks.
"""

import hashlib
import logging
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Literal

from pydantic import BaseModel, Field

from torq_console.layer12.federation.types import FederatedClaimEnvelope
from torq_console.layer12.federation.errors import ReplayAttackError

logger = logging.getLogger(__name__)


class ReplayProtectionResult(BaseModel):
    """Result of a replay protection check."""

    is_replay: bool = Field(..., description="Whether the envelope was detected as a replay")
    envelope_id: str = Field(..., description="The envelope ID that was checked")
    check_type: Literal["envelope_id", "signature_hash", "timestamp"] = Field(
        ..., description="Type of replay check performed"
    )
    first_seen: datetime | None = Field(None, description="When this envelope was first seen")
    blocked_reason: str | None = Field(None, description="Reason why the envelope was blocked")


class ReplayProtectionConfig:
    """Configuration for replay protection."""

    def __init__(
        self,
        max_tracked_envelopes: int = 10000,
        envelope_ttl_seconds: int = 86400,  # 24 hours
        signature_ttl_seconds: int = 86400,  # 24 hours
        enable_timestamp_check: bool = True,
        max_timestamp_skew_seconds: int = 300,  # 5 minutes
        enable_envelope_id_tracking: bool = True,
        enable_signature_hash_tracking: bool = True,
    ):
        """
        Initialize replay protection configuration.

        Args:
            max_tracked_envelopes: Maximum number of envelopes to track
            envelope_ttl_seconds: Time before envelope IDs expire from tracking
            signature_ttl_seconds: Time before signature hashes expire
            enable_timestamp_check: Whether to check envelope timestamps
            max_timestamp_skew_seconds: Maximum allowed timestamp skew
            enable_envelope_id_tracking: Whether to track envelope IDs
            enable_signature_hash_tracking: Whether to track signature hashes
        """
        self.max_tracked_envelopes = max_tracked_envelopes
        self.envelope_ttl_seconds = envelope_ttl_seconds
        self.signature_ttl_seconds = signature_ttl_seconds
        self.enable_timestamp_check = enable_timestamp_check
        self.max_timestamp_skew_seconds = max_timestamp_skew_seconds
        self.enable_envelope_id_tracking = enable_envelope_id_tracking
        self.enable_signature_hash_tracking = enable_signature_hash_tracking


class ReplayProtectionService:
    """
    Service to detect and prevent replay attacks.

    Tracks:
    - Envelope IDs (globally unique identifiers)
    - Signature hashes (cryptographic signatures)
    - Timestamp bounds (detect envelopes from the far past/future)

    Uses an LRU cache to limit memory usage while maintaining
    effective protection against replay attacks.
    """

    def __init__(self, config: ReplayProtectionConfig | None = None):
        """
        Initialize the replay protection service.

        Args:
            config: Configuration for replay protection behavior
        """
        self.config = config or ReplayProtectionConfig()
        self.logger = logging.getLogger(__name__)

        # Track seen envelope IDs -> first seen timestamp
        self._envelope_ids: OrderedDict[str, datetime] = OrderedDict()

        # Track seen signature hashes -> first seen timestamp
        self._signature_hashes: OrderedDict[str, datetime] = OrderedDict()

        # Statistics
        self._total_checked = 0
        self._replays_detected = 0
        self._service_started_at = datetime.utcnow()

    def _compute_signature_hash(self, envelope: FederatedClaimEnvelope) -> str:
        """
        Compute a hash of the envelope signature for replay detection.

        Args:
            envelope: The envelope to hash

        Returns:
            Hex string hash of the signature
        """
        sig = envelope.signature
        sig_data = f"{sig.signer_node_id}:{sig.algorithm}:{sig.signature_value}:{sig.signed_at.isoformat()}"
        return hashlib.sha256(sig_data.encode()).hexdigest()

    def _cleanup_expired_entries(self) -> None:
        """Remove expired entries from tracking dictionaries."""
        now = datetime.utcnow()
        envelope_cutoff = now - timedelta(seconds=self.config.envelope_ttl_seconds)
        signature_cutoff = now - timedelta(seconds=self.config.signature_ttl_seconds)

        # Clean envelope IDs
        expired_envelopes = [
            env_id for env_id, seen_at in self._envelope_ids.items()
            if seen_at < envelope_cutoff
        ]
        for env_id in expired_envelopes:
            del self._envelope_ids[env_id]

        # Clean signature hashes
        expired_signatures = [
            sig_hash for sig_hash, seen_at in self._signature_hashes.items()
            if seen_at < signature_cutoff
        ]
        for sig_hash in expired_signatures:
            del self._signature_hashes[sig_hash]

        # Enforce LRU limit
        while len(self._envelope_ids) > self.config.max_tracked_envelopes:
            self._envelope_ids.popitem(last=False)

        while len(self._signature_hashes) > self.config.max_tracked_envelopes:
            self._signature_hashes.popitem(last=False)

    def _check_timestamp_bounds(self, envelope: FederatedClaimEnvelope) -> tuple[bool, str | None]:
        """
        Check if envelope timestamp is within acceptable bounds.

        Args:
            envelope: The envelope to check

        Returns:
            Tuple of (is_valid, reason_if_invalid)
        """
        if not self.config.enable_timestamp_check:
            return True, None

        now = datetime.utcnow()
        time_diff = abs((now - envelope.sent_at).total_seconds())

        if time_diff > self.config.max_timestamp_skew_seconds:
            return False, f"Envelope timestamp out of bounds (diff: {time_diff}s, max: {self.config.max_timestamp_skew_seconds}s)"

        return True, None

    async def check_envelope(
        self,
        envelope: FederatedClaimEnvelope,
        skip_timestamp_check: bool = False,
    ) -> ReplayProtectionResult:
        """
        Check if an envelope has been replayed.

        Performs multiple checks:
        1. Timestamp bounds (if enabled)
        2. Envelope ID uniqueness (if enabled)
        3. Signature hash uniqueness (if enabled)

        Args:
            envelope: The envelope to check
            skip_timestamp_check: Skip timestamp validation

        Returns:
            ReplayProtectionResult indicating if this is a replay

        Raises:
            ReplayAttackError: If a replay attack is detected
        """
        self._total_checked += 1

        # Clean up expired entries before checking
        self._cleanup_expired_entries()

        envelope_id = envelope.envelope_id

        # Check 1: Timestamp bounds
        if not skip_timestamp_check and self.config.enable_timestamp_check:
            timestamp_valid, reason = self._check_timestamp_bounds(envelope)
            if not timestamp_valid:
                self._replays_detected += 1
                self.logger.warning(f"Replay detected (timestamp): {envelope_id} - {reason}")
                result = ReplayProtectionResult(
                    is_replay=True,
                    envelope_id=envelope_id,
                    check_type="timestamp",
                    blocked_reason=reason,
                )
                raise ReplayAttackError(
                    f"Replay attack detected: {reason}",
                    details=result.to_dict()
                )

        # Check 2: Envelope ID tracking
        if self.config.enable_envelope_id_tracking:
            if envelope_id in self._envelope_ids:
                first_seen = self._envelope_ids[envelope_id]
                self._replays_detected += 1
                reason = f"Envelope ID previously seen at {first_seen.isoformat()}"
                self.logger.warning(f"Replay detected (envelope_id): {envelope_id} - {reason}")
                result = ReplayProtectionResult(
                    is_replay=True,
                    envelope_id=envelope_id,
                    check_type="envelope_id",
                    first_seen=first_seen,
                    blocked_reason=reason,
                )
                raise ReplayAttackError(
                    f"Replay attack detected: {reason}",
                    details=result.to_dict()
                )

        # Check 3: Signature hash tracking
        if self.config.enable_signature_hash_tracking:
            sig_hash = self._compute_signature_hash(envelope)
            if sig_hash in self._signature_hashes:
                first_seen = self._signature_hashes[sig_hash]
                self._replays_detected += 1
                reason = f"Signature hash previously seen at {first_seen.isoformat()}"
                self.logger.warning(f"Replay detected (signature_hash): {envelope_id} - {reason}")
                result = ReplayProtectionResult(
                    is_replay=True,
                    envelope_id=envelope_id,
                    check_type="signature_hash",
                    first_seen=first_seen,
                    blocked_reason=reason,
                )
                raise ReplayAttackError(
                    f"Replay attack detected: {reason}",
                    details=result.to_dict()
                )

        # All checks passed - this is a new envelope
        return ReplayProtectionResult(
            is_replay=False,
            envelope_id=envelope_id,
            check_type="envelope_id",
        )

    def mark_envelope_seen(self, envelope: FederatedClaimEnvelope) -> None:
        """
        Mark an envelope as seen to prevent future replays.

        Call this after envelope has passed all other validation checks
        and is being processed.

        Args:
            envelope: The envelope to mark as seen
        """
        now = datetime.utcnow()
        envelope_id = envelope.envelope_id

        # Track envelope ID
        if self.config.enable_envelope_id_tracking:
            self._envelope_ids[envelope_id] = now
            # Move to end (most recently used)
            self._envelope_ids.move_to_end(envelope_id)

        # Track signature hash
        if self.config.enable_signature_hash_tracking:
            sig_hash = self._compute_signature_hash(envelope)
            self._signature_hashes[sig_hash] = now
            # Move to end (most recently used)
            self._signature_hashes.move_to_end(sig_hash)

        self.logger.debug(f"Marked envelope as seen: {envelope_id}")

    def get_statistics(self) -> dict:
        """
        Get replay protection statistics.

        Returns:
            Dictionary with replay protection metrics
        """
        uptime = (datetime.utcnow() - self._service_started_at).total_seconds()

        return {
            "totalChecked": self._total_checked,
            "replaysDetected": self._replays_detected,
            "replayRate": self._replays_detected / max(self._total_checked, 1),
            "trackedEnvelopeIds": len(self._envelope_ids),
            "trackedSignatureHashes": len(self._signature_hashes),
            "uptimeSeconds": uptime,
            "serviceStartedAt": self._service_started_at.isoformat(),
        }

    def reset_statistics(self) -> None:
        """Reset replay protection statistics."""
        self._total_checked = 0
        self._replays_detected = 0

    def clear_tracking(self) -> None:
        """Clear all tracking data (use with caution)."""
        self._envelope_ids.clear()
        self._signature_hashes.clear()
        self.logger.warning("Cleared all replay protection tracking data")


def create_replay_protection(
    config: ReplayProtectionConfig | None = None,
) -> ReplayProtectionService:
    """
    Factory function to create a ReplayProtectionService.

    Args:
        config: Configuration for replay protection

    Returns:
        Configured ReplayProtectionService instance
    """
    return ReplayProtectionService(config=config)
