"""
TORQ Readiness Checker - Transition Lock Manager

Milestone 5: Prevent concurrent transitions on the same candidate.

Ensures state machine safety by enforcing exclusive transition operations
per candidate using asyncio locks.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, Optional
from uuid import UUID
from contextlib import asynccontextmanager


logger = logging.getLogger(__name__)


# ============================================================================
# Transition Lock Manager
# ============================================================================

class TransitionLockManager:
    """
    Manages exclusive locks for candidate transitions.

    Guarantees that only one transition can occur for a given candidate
    at a time, preventing race conditions and state machine conflicts.
    """

    # Class-level lock storage (shared across all instances)
    _locks: Dict[str, asyncio.Lock] = {}
    _lock_metadata: Dict[str, Dict] = {}

    def __init__(self, lock_timeout: float = 30.0):
        """
        Initialize the lock manager.

        Args:
            lock_timeout: Maximum seconds to wait for lock acquisition
        """
        self.lock_timeout = lock_timeout

    @asynccontextmanager
    async def acquire_transition_lock(
        self,
        candidate_id: UUID,
        actor: Optional[str] = None,
    ):
        """
        Acquire an exclusive lock for a candidate transition.

        Args:
            candidate_id: ID of the candidate to lock
            actor: Optional actor identifier for audit logging

        Yields:
            True if lock was successfully acquired

        Raises:
            TimeoutError: If lock cannot be acquired within timeout
        """
        candidate_key = str(candidate_id)

        # Ensure lock exists for this candidate
        if candidate_key not in self._locks:
            self._locks[candidate_key] = asyncio.Lock()
            self._lock_metadata[candidate_key] = {
                "acquired_count": 0,
                "last_actor": None,
                "created_at": asyncio.get_event_loop().time(),
            }

        lock = self._locks[candidate_key]

        # Update metadata
        self._lock_metadata[candidate_key]["last_actor"] = actor
        self._lock_metadata[candidate_key]["acquired_count"] += 1

        logger.info(
            f"[TransitionLock] Acquiring lock for candidate {candidate_key[:8]} "
            f"by {actor or 'unknown'}"
        )

        try:
            # Attempt to acquire lock with timeout
            acquired = await asyncio.wait_for(
                lock.acquire(),
                timeout=self.lock_timeout,
            )

            if acquired:
                logger.info(
                    f"[TransitionLock] Lock acquired for candidate {candidate_key[:8]}"
                )
                self._lock_metadata[candidate_key]["locked_at"] = asyncio.get_event_loop().time()
                self._lock_metadata[candidate_key]["locked_by"] = actor

            yield acquired

        except asyncio.TimeoutError:
            logger.warning(
                f"[TransitionLock] Timeout waiting for lock on candidate {candidate_key[:8]}"
            )
            raise TimeoutError(
                f"Could not acquire transition lock for candidate {candidate_id} "
                f"within {self.lock_timeout}s"
            )

        finally:
            # Always release the lock
            if lock.locked():
                lock.release()
                logger.info(
                    f"[TransitionLock] Lock released for candidate {candidate_key[:8]}"
                )
                self._lock_metadata[candidate_key]["released_at"] = asyncio.get_event_loop().time()
                self._lock_metadata[candidate_key]["released_by"] = actor

    async def is_locked(self, candidate_id: UUID) -> bool:
        """
        Check if a candidate is currently locked.

        Args:
            candidate_id: ID of the candidate to check

        Returns:
            True if candidate currently has an active lock
        """
        candidate_key = str(candidate_id)

        if candidate_key not in self._locks:
            return False

        return self._locks[candidate_key].locked()

    async def try_acquire(
        self,
        candidate_id: UUID,
        actor: Optional[str] = None,
    ) -> bool:
        """
        Attempt to acquire a lock without blocking.

        Args:
            candidate_id: ID of the candidate to lock
            actor: Optional actor identifier

        Returns:
            True if lock was acquired, False otherwise
        """
        candidate_key = str(candidate_id)

        if candidate_key not in self._locks:
            self._locks[candidate_key] = asyncio.Lock()
            self._lock_metadata[candidate_key] = {
                "acquired_count": 0,
                "last_actor": None,
                "created_at": asyncio.get_event_loop().time(),
            }

        lock = self._locks[candidate_key]

        # Try to acquire without blocking
        # asyncio.Lock doesn't have a non-blocking acquire, so we check locked first
        # This is a race condition but acceptable for a "try" operation
        if not lock.locked():
            # Acquire the lock properly
            # We need to use a task to acquire it without blocking
            try:
                # Try to acquire with a very short timeout
                await asyncio.wait_for(lock.acquire(), timeout=0.001)
                self._lock_metadata[candidate_key]["locked_at"] = asyncio.get_event_loop().time()
                self._lock_metadata[candidate_key]["locked_by"] = actor
                self._lock_metadata[candidate_key]["acquired_count"] += 1
                logger.info(
                    f"[TransitionLock] Quick lock acquired for candidate {candidate_key[:8]}"
                )
                return True
            except asyncio.TimeoutError:
                return False

        return False

    async def release(self, candidate_id: UUID, actor: Optional[str] = None):
        """
        Manually release a lock for a candidate.

        Args:
            candidate_id: ID of the candidate to unlock
            actor: Optional actor identifier for audit logging
        """
        candidate_key = str(candidate_id)

        if candidate_key in self._locks and self._locks[candidate_key].locked():
            self._locks[candidate_key].release()
            self._lock_metadata[candidate_key]["released_at"] = asyncio.get_event_loop().time()
            self._lock_metadata[candidate_key]["released_by"] = actor
            logger.info(
                f"[TransitionLock] Manual release for candidate {candidate_key[:8]} by {actor or 'unknown'}"
            )

    def get_lock_info(self, candidate_id: UUID) -> Optional[Dict]:
        """
        Get metadata about a candidate's lock.

        Args:
            candidate_id: ID of the candidate

        Returns:
            Lock metadata dictionary or None if not found
        """
        candidate_key = str(candidate_id)

        if candidate_key not in self._lock_metadata:
            return None

        metadata = self._lock_metadata[candidate_key].copy()
        metadata["is_locked"] = self._locks[candidate_key].locked()
        return metadata

    @classmethod
    def cleanup_lock(cls, candidate_id: UUID):
        """
        Remove lock data for a candidate (use when candidate is deleted).

        Args:
            candidate_id: ID of the candidate to cleanup
        """
        candidate_key = str(candidate_id)

        if candidate_key in cls._locks:
            del cls._locks[candidate_key]

        if candidate_key in cls._lock_metadata:
            del cls._lock_metadata[candidate_key]

        logger.debug(f"[TransitionLock] Cleaned up lock for candidate {candidate_key[:8]}")


# Global lock manager instance
_lock_manager: Optional[TransitionLockManager] = None


def get_transition_lock_manager() -> TransitionLockManager:
    """Get the global transition lock manager instance."""
    global _lock_manager
    if _lock_manager is None:
        _lock_manager = TransitionLockManager()
    return _lock_manager
