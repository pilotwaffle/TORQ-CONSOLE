"""
TORQ Readiness Checker - Idempotency Guard

Milestone 5: Ensure duplicate requests don't produce duplicate actions.

Detects and prevents duplicate governance actions, ensuring safe retries
and idempotent transition operations.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from uuid import UUID, uuid4


logger = logging.getLogger(__name__)


# ============================================================================
# Idempotency Key Generator
# ============================================================================

def generate_idempotency_key(
    candidate_id: UUID,
    action: str,
    target_state: Optional[str] = None,
    actor: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate a unique idempotency key for a transition request.

    The key uniquely identifies a transition request based on its parameters,
    allowing duplicate detection across retries.

    Args:
        candidate_id: ID of the candidate
        action: Governance action type
        target_state: Optional target state
        actor: Optional actor identifier
        params: Optional additional parameters

    Returns:
        SHA256 hash representing the unique idempotency key
    """
    # Build key components
    components = [
        str(candidate_id),
        action,
        target_state or "",
        actor or "",
    ]

    # Add sorted params for deterministic hashing
    if params:
        sorted_params = sorted(params.items())
        components.extend(f"{k}={v}" for k, v in sorted_params)

    # Join and hash
    key_string = "|".join(components)
    return hashlib.sha256(key_string.encode()).hexdigest()


# ============================================================================
# Idempotency Record
# ============================================================================

class IdempotencyRecord:
    """
    Record of a processed idempotency key.

    Tracks when an action was processed to prevent duplicates.
    """

    def __init__(
        self,
        key: str,
        candidate_id: UUID,
        action: str,
        target_state: Optional[str],
        result_state: str,
        processed_at: datetime,
        expires_at: datetime,
    ):
        self.key = key
        self.candidate_id = candidate_id
        self.action = action
        self.target_state = target_state
        self.result_state = result_state
        self.processed_at = processed_at
        self.expires_at = expires_at

    def is_expired(self) -> bool:
        """Check if this idempotency record has expired."""
        return datetime.now() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "key": self.key,
            "candidate_id": str(self.candidate_id),
            "action": self.action,
            "target_state": self.target_state,
            "result_state": self.result_state,
            "processed_at": self.processed_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
        }


# ============================================================================
# Idempotency Guard
# ============================================================================

class IdempotencyGuard:
    """
    Guards against duplicate governance action requests.

    Tracks processed requests by idempotency key and prevents
    duplicate execution of the same action.
    """

    # Default TTL for idempotency records (24 hours)
    DEFAULT_TTL = timedelta(hours=24)

    def __init__(self, ttl: timedelta = DEFAULT_TTL):
        """
        Initialize the idempotency guard.

        Args:
            ttl: Time-to-live for idempotency records
        """
        self.ttl = ttl
        # In-memory storage (production would use Redis or database)
        self._records: Dict[str, IdempotencyRecord] = {}

    def check_and_record(
        self,
        candidate_id: UUID,
        action: str,
        target_state: Optional[str] = None,
        actor: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> tuple[bool, Optional[IdempotencyRecord]]:
        """
        Check if a request is a duplicate and record if not.

        Args:
            candidate_id: ID of the candidate
            action: Governance action type
            target_state: Optional target state
            actor: Optional actor identifier
            params: Optional additional parameters

        Returns:
            (is_duplicate, existing_record) tuple
            - is_duplicate: True if this request was already processed
            - existing_record: The previous record if duplicate, None otherwise
        """
        key = generate_idempotency_key(
            candidate_id=candidate_id,
            action=action,
            target_state=target_state,
            actor=actor,
            params=params,
        )

        # Clean up expired records first
        self._cleanup_expired()

        # Check for existing record
        if key in self._records:
            existing = self._records[key]
            if not existing.is_expired():
                logger.info(
                    f"[IdempotencyGuard] Duplicate request detected: {action} "
                    f"for candidate {str(candidate_id)[:8]} "
                    f"(originally processed at {existing.processed_at})"
                )
                return True, existing
            else:
                # Remove expired record
                del self._records[key]

        # Record this request as processed (with placeholder result)
        # Caller will update with actual result
        record = IdempotencyRecord(
            key=key,
            candidate_id=candidate_id,
            action=action,
            target_state=target_state,
            result_state="pending",
            processed_at=datetime.now(),
            expires_at=datetime.now() + self.ttl,
        )
        self._records[key] = record

        logger.debug(
            f"[IdempotencyGuard] Recording new request: {action} "
            f"for candidate {str(candidate_id)[:8]}"
        )

        return False, None

    def update_result(
        self,
        candidate_id: UUID,
        action: str,
        result_state: str,
        target_state: Optional[str] = None,
        actor: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ):
        """
        Update the result state for a recorded request.

        Args:
            candidate_id: ID of the candidate
            action: Governance action type
            result_state: The actual state after transition
            target_state: Optional target state
            actor: Optional actor identifier
            params: Optional additional parameters
        """
        key = generate_idempotency_key(
            candidate_id=candidate_id,
            action=action,
            target_state=target_state,
            actor=actor,
            params=params,
        )

        if key in self._records:
            self._records[key].result_state = result_state
            logger.debug(
                f"[IdempotencyGuard] Updated result for {action} "
                f"on candidate {str(candidate_id)[:8]}: {result_state}"
            )

    def get_record(
        self,
        candidate_id: UUID,
        action: str,
        target_state: Optional[str] = None,
        actor: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[IdempotencyRecord]:
        """
        Get the record for a specific request.

        Args:
            candidate_id: ID of the candidate
            action: Governance action type
            target_state: Optional target state
            actor: Optional actor identifier
            params: Optional additional parameters

        Returns:
            IdempotencyRecord if found, None otherwise
        """
        key = generate_idempotency_key(
            candidate_id=candidate_id,
            action=action,
            target_state=target_state,
            actor=actor,
            params=params,
        )

        record = self._records.get(key)
        if record and not record.is_expired():
            return record

        return None

    def invalidate(
        self,
        candidate_id: UUID,
        action: str,
        target_state: Optional[str] = None,
        actor: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ):
        """
        Invalidate an idempotency record.

        Useful for testing or manual override scenarios.

        Args:
            candidate_id: ID of the candidate
            action: Governance action type
            target_state: Optional target state
            actor: Optional actor identifier
            params: Optional additional parameters
        """
        key = generate_idempotency_key(
            candidate_id=candidate_id,
            action=action,
            target_state=target_state,
            actor=actor,
            params=params,
        )

        if key in self._records:
            del self._records[key]
            logger.info(
                f"[IdempotencyGuard] Invalidated record for {action} "
                f"on candidate {str(candidate_id)[:8]}"
            )

    def _cleanup_expired(self):
        """Remove expired idempotency records."""
        now = datetime.now()
        expired_keys = [
            key for key, record in self._records.items()
            if record.is_expired()
        ]

        for key in expired_keys:
            del self._records[key]

        if expired_keys:
            logger.debug(f"[IdempotencyGuard] Cleaned up {len(expired_keys)} expired records")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about idempotency guard state.

        Returns:
            Dictionary with stats
        """
        self._cleanup_expired()

        return {
            "total_records": len(self._records),
            "ttl_seconds": int(self.ttl.total_seconds()),
            "records_by_action": self._count_by_action(),
        }

    def _count_by_action(self) -> Dict[str, int]:
        """Count records by action type."""
        counts: Dict[str, int] = {}
        for record in self._records.values():
            counts[record.action] = counts.get(record.action, 0) + 1
        return counts


# Global idempotency guard instance
_idempotency_guard: Optional[IdempotencyGuard] = None


def get_idempotency_guard() -> IdempotencyGuard:
    """Get the global idempotency guard instance."""
    global _idempotency_guard
    if _idempotency_guard is None:
        _idempotency_guard = IdempotencyGuard()
    return _idempotency_guard
