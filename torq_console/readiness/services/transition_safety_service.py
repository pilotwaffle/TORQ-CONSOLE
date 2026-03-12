"""
TORQ Readiness Checker - Transition Safety Service

Milestone 5: Service for concurrency-safe and idempotent transitions.

Manages transition locks and idempotency validation to ensure
safe concurrent operations on readiness candidates.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Tuple
from uuid import UUID

from pydantic import BaseModel


logger = logging.getLogger(__name__)


# Import from hardening layer
from ..hardening.transition_lock_manager import (
    TransitionLockManager,
    get_transition_lock_manager,
)

from ..hardening.idempotency_guard import (
    IdempotencyGuard,
    generate_idempotency_key,
    get_idempotency_guard,
)

# Import models
from ..readiness_models import ReadinessState


# ============================================================================
# Transition Validation Result
# ============================================================================

class TransitionValidationResult(BaseModel):
    """
    Result of a transition safety validation.
    """
    is_valid: bool
    can_proceed: bool

    rejection_reason: Optional[str] = None
    is_duplicate: bool = False
    duplicate_result_state: Optional[str] = None

    lock_acquired: bool = False
    idempotency_key: Optional[str] = None


# ============================================================================
# Transition Safety Service
# ============================================================================

class TransitionSafetyService:
    """
    Service for ensuring safe, concurrent transitions.

    Combines locking and idempotency mechanisms to guarantee
    state machine safety under concurrent operations.
    """

    def __init__(self):
        """Initialize the transition safety service."""
        self.lock_manager = get_transition_lock_manager()
        self.idempotency_guard = get_idempotency_guard()

    async def validate_transition_request(
        self,
        candidate_id: UUID,
        action: str,
        target_state: Optional[str] = None,
        actor: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> TransitionValidationResult:
        """
        Validate a transition request for safety.

        Checks for duplicates and prepares for lock acquisition.

        Args:
            candidate_id: ID of the candidate
            action: Governance action type
            target_state: Optional target state
            actor: Optional actor identifier
            params: Optional additional parameters

        Returns:
            TransitionValidationResult with validation status
        """
        # Check for duplicate request
        is_duplicate, existing_record = self.idempotency_guard.check_and_record(
            candidate_id=candidate_id,
            action=action,
            target_state=target_state,
            actor=actor,
            params=params,
        )

        idempotency_key = generate_idempotency_key(
            candidate_id=candidate_id,
            action=action,
            target_state=target_state,
            actor=actor,
            params=params,
        )

        if is_duplicate and existing_record:
            logger.info(
                f"[TransitionSafety] Duplicate {action} request "
                f"for candidate {str(candidate_id)[:8]} "
                f"by {actor or 'unknown'}"
            )

            return TransitionValidationResult(
                is_valid=True,
                can_proceed=False,  # Don't proceed, already done
                is_duplicate=True,
                duplicate_result_state=existing_record.result_state,
                idempotency_key=idempotency_key,
            )

        return TransitionValidationResult(
            is_valid=True,
            can_proceed=True,
            lock_acquired=False,
            idempotency_key=idempotency_key,
        )

    async def execute_transition_safely(
        self,
        candidate_id: UUID,
        action: str,
        transition_func,  # Async function to execute under lock
        target_state: Optional[str] = None,
        actor: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Execute a transition with safety guarantees.

        Acquires lock, validates idempotency, executes transition,
        releases lock, and updates idempotency record.

        Args:
            candidate_id: ID of the candidate
            action: Governance action type
            transition_func: Async function to execute
            target_state: Optional target state
            actor: Optional actor identifier
            params: Optional additional parameters

        Returns:
            (success, result_state, error_message) tuple
        """
        # Step 1: Validate request
        validation = await self.validate_transition_request(
            candidate_id=candidate_id,
            action=action,
            target_state=target_state,
            actor=actor,
            params=params,
        )

        if not validation.can_proceed:
            # Duplicate request - return existing result
            return (
                True,
                validation.duplicate_result_state,
                None,
            )

        # Step 2: Acquire lock
        try:
            async with self.lock_manager.acquire_transition_lock(
                candidate_id=candidate_id,
                actor=actor,
            ):
                logger.info(
                    f"[TransitionSafety] Executing {action} "
                    f"for candidate {str(candidate_id)[:8]}"
                )

                # Step 3: Execute transition
                try:
                    result = await transition_func()
                    result_state = result.get("state") if isinstance(result, dict) else str(result)

                    # Step 4: Update idempotency record with result
                    self.idempotency_guard.update_result(
                        candidate_id=candidate_id,
                        action=action,
                        result_state=result_state,
                        target_state=target_state,
                        actor=actor,
                        params=params,
                    )

                    return True, result_state, None

                except Exception as e:
                    error_msg = f"Transition execution failed: {str(e)}"
                    logger.error(f"[TransitionSafety] {error_msg}")
                    return False, None, error_msg

        except TimeoutError as e:
            error_msg = f"Failed to acquire transition lock: {str(e)}"
            logger.error(f"[TransitionSafety] {error_msg}")
            return False, None, error_msg

    async def is_candidate_locked(self, candidate_id: UUID) -> bool:
        """
        Check if a candidate is currently locked.

        Args:
            candidate_id: ID of the candidate

        Returns:
            True if candidate has an active lock
        """
        return await self.lock_manager.is_locked(candidate_id)

    async def try_acquire_lock(
        self,
        candidate_id: UUID,
        actor: Optional[str] = None,
    ) -> bool:
        """
        Attempt to acquire a lock without blocking.

        Args:
            candidate_id: ID of the candidate
            actor: Optional actor identifier

        Returns:
            True if lock was acquired, False otherwise
        """
        return await self.lock_manager.try_acquire(
            candidate_id=candidate_id,
            actor=actor,
        )

    async def release_lock(
        self,
        candidate_id: UUID,
        actor: Optional[str] = None,
    ):
        """
        Manually release a lock.

        Args:
            candidate_id: ID of the candidate
            actor: Optional actor identifier
        """
        await self.lock_manager.release(
            candidate_id=candidate_id,
            actor=actor,
        )

    def get_lock_info(self, candidate_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get information about a candidate's lock.

        Args:
            candidate_id: ID of the candidate

        Returns:
            Lock metadata or None
        """
        return self.lock_manager.get_lock_info(candidate_id)

    def get_idempotency_stats(self) -> Dict[str, Any]:
        """
        Get statistics about idempotency tracking.

        Returns:
            Dictionary with stats
        """
        return self.idempotency_guard.get_stats()

    def invalidate_idempotency(
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
        self.idempotency_guard.invalidate(
            candidate_id=candidate_id,
            action=action,
            target_state=target_state,
            actor=actor,
            params=params,
        )


# Global transition safety service instance
_transition_safety_service: Optional[TransitionSafetyService] = None


def get_transition_safety_service() -> TransitionSafetyService:
    """Get the global transition safety service instance."""
    global _transition_safety_service
    if _transition_safety_service is None:
        _transition_safety_service = TransitionSafetyService()
    return _transition_safety_service
