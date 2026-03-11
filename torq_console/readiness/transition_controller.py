"""
TORQ Readiness Checker - Transition Controller

Milestone 3: Manage readiness state transitions and governance actions.

Implements the state machine that controls when capabilities move from
observation mode through testing into active production use.

Core Components:
- ReadinessTransitionController: Orchestrates state transitions
- GovernanceActionEngine: Executes governance actions
- TransitionPolicyValidator: Validates transitions against policy
- ReadinessStateMachine: Tracks state and prevents invalid transitions
- TransitionAuditLog: Records all state changes
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from .readiness_models import (
    CandidateType,
    ReadinessCandidate,
    ReadinessEvaluation,
    ReadinessState,
    ReadinessOutcome,
    TransitionRequest,
    TransitionResult,
    TransitionEvent,
    validate_candidate_type_transition,
)
from .readiness_policy import (
    ReadinessPolicyRegistry,
    get_policy_registry,
    HardBlockEvaluator,
    get_hard_block_evaluator,
)
from .scoring_engine import (
    ReadinessScoringEngine,
    ScoringContext,
    get_scoring_engine,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Transition Audit Log
# ============================================================================

class TransitionAuditLog(BaseModel):
    """
    Persistent audit log of all readiness state transitions.

    Maintains complete history of all state changes for compliance
    and operational visibility.
    """
    id: UUID = Field(default_factory=uuid4)
    candidate_id: UUID

    # Transition details
    from_state: ReadinessState
    to_state: ReadinessState
    transition_type: str  # promotion, demotion, regression, reassessment, forced

    # Evaluation that triggered this
    evaluation_id: UUID
    evaluation_outcome: ReadinessOutcome
    evaluation_score: float

    # Policy
    policy_profile_id: str
    policy_version: str

    # Trigger
    triggered_by: str  # system, user_id, policy_id
    trigger_reason: str
    force_used: bool = False

    # Governance
    approved_by: Optional[str] = None
    approval_reason: Optional[str] = None
    governance_override: bool = False

    # Timing
    transitioned_at: datetime = Field(default_factory=datetime.now)
    transition_duration_ms: int = 0

    # Previous state for rollback
    previous_state_locked: bool = False
    rollback_until: Optional[datetime] = None

    # Additional context
    metadata: Dict[str, Any] = Field(default_factory=dict)


# In-memory audit log storage (would be database in production)
_audit_logs: Dict[UUID, List[TransitionAuditLog]] = {}


def get_audit_logs(candidate_id: UUID) -> List[TransitionAuditLog]:
    """Get all audit logs for a candidate."""
    return _audit_logs.get(candidate_id, []).copy()


def add_audit_log(log: TransitionAuditLog) -> None:
    """Add an audit log entry."""
    candidate_id = log.candidate_id
    if candidate_id not in _audit_logs:
        _audit_logs[candidate_id] = []
    _audit_logs[candidate_id].append(log)
    logger.info(f"Recorded transition audit: {log.from_state.value} -> {log.to_state.value} for candidate {candidate_id}")


def get_all_audit_logs() -> Dict[UUID, List[TransitionAuditLog]]:
    """Get all audit logs (for audit service)."""
    return _audit_logs.copy()


# ============================================================================
# Transition Policy Validator
# ============================================================================

class TransitionPolicyValidator:
    """
    Validates transition requests against policy constraints.

    Ensures that all transitions comply with:
    - State machine rules
    - Policy profile requirements
    - Evidence sufficiency
    - Hard block rules
    """

    def __init__(
        self,
        policy_registry=None,
        block_evaluator=None,
    ):
        self.policy_registry = policy_registry or get_policy_registry()
        self.block_evaluator = block_evaluator or get_hard_block_evaluator()

    def validate_transition_request(
        self,
        request: TransitionRequest,
        current_state: ReadinessState,
        evaluation: Optional[ReadinessEvaluation] = None,
    ) -> Tuple[bool, List[str]]:
        """
        Validate a transition request.

        Args:
            request: The transition request to validate
            current_state: Current state of the candidate
            evaluation: Optional evaluation supporting the request

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # 1. Check if transition is allowed by state machine
        if not request.force:
            is_allowed, state_error = validate_candidate_type_transition(
                current_state,
                request.target_state,
                force=False
            )
            if not is_allowed:
                errors.append(state_error or "Invalid state transition")

        # 2. If evaluation provided, validate it supports the transition
        if evaluation:
            profile = self.policy_registry.get_profile(evaluation.policy_profile_id)

            # Check hard blocks
            if evaluation.score.hard_blocks:
                if request.target_state == ReadinessState.READY and not request.force:
                    errors.append(f"Cannot transition to READY with hard blocks: {evaluation.score.hard_blocks}")

            # Check score thresholds
            if request.target_state == ReadinessState.READY:
                min_score = profile.thresholds.ready_min
                if evaluation.score.overall_score < min_score and not request.force:
                    errors.append(f"Score {evaluation.score.overall_score:.2f} below READY threshold {min_score}")

            # Check for regression
            if current_state == ReadinessState.READY and request.target_state == ReadinessState.REGRESSED:
                if not evaluation.is_regression and not request.force:
                    errors.append("Cannot transition to REGRESSED without regression signal")

        # 3. Validate evaluation_id if provided
        if request.evaluation_id and not evaluation:
            errors.append("Evaluation ID provided but no evaluation data")

        return len(errors) == 0, errors

    def validate_forced_transition(
        self,
        request: TransitionRequest,
        current_state: ReadinessState,
    ) -> Tuple[bool, List[str]]:
        """
        Validate a forced transition request.

        Forced transitions bypass normal checks but still require:
        - Valid target state
        - Proper authorization
        - Audit trail justification

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Must have force=True
        if not request.force:
            errors.append("Forced transition validation requires force=True")

        # Must have reason
        if not request.reason:
            errors.append("Forced transitions require a reason")

        # Target state must be valid ReadinessState
        valid_states = {s.value for s in ReadinessState}
        if request.target_state.value not in valid_states:
            errors.append(f"Invalid target state: {request.target_state}")

        return len(errors) == 0, errors


# ============================================================================
# Readiness State Machine
# ============================================================================

class ReadinessStateMachine:
    """
    Manages readiness state transitions and history.

    Tracks the complete lifecycle of a candidate through all
    observation mode states with full history preservation.
    """

    def __init__(self, candidate_id: UUID, initial_state: ReadinessState = ReadinessState.OBSERVED):
        self.candidate_id = candidate_id
        self.current_state = initial_state
        self.state_history: List[Tuple[ReadinessState, datetime]] = [
            (initial_state, datetime.now())
        ]
        self.state_since: datetime = datetime.now()
        self.transition_count: int = 0
        self.forced_transition_count: int = 0

    def can_transition_to(self, target_state: ReadinessState, force: bool = False) -> bool:
        """Check if transition to target state is allowed."""
        if force:
            return True

        valid, _ = validate_candidate_type_transition(
            self.current_state,
            target_state,
            force=False
        )
        return valid

    def transition_to(
        self,
        target_state: ReadinessState,
        transition_type: str,
        forced: bool = False,
    ) -> TransitionEvent:
        """
        Execute a state transition.

        Args:
            target_state: The state to transition to
            transition_type: Type of transition (promotion, demotion, etc.)
            forced: Whether this was a forced transition

        Returns:
            TransitionEvent record of the transition
        """
        from_state = self.current_state
        now = datetime.now()

        # Update state
        self.current_state = target_state
        self.state_since = now
        self.state_history.append((target_state, now))
        self.transition_count += 1

        if forced:
            self.forced_transition_count += 1

        # Create transition event
        event = TransitionEvent(
            id=uuid4(),
            candidate_id=self.candidate_id,
            from_state=from_state,
            to_state=target_state,
            transition_type=transition_type,
            triggered_by="system" if not forced else "forced_override",
            trigger_reason=f"State transition: {from_state.value} -> {target_state.value}",
            evaluation_id=uuid4(),  # Will be updated by caller
            policy_profile_id="default",
            policy_version="1.0",
            transitioned_at=now,
            previous_state_locked=forced,  # Forced transitions are locked
        )

        logger.info(
            f"Transitioned candidate {self.candidate_id}: "
            f"{from_state.value} -> {target_state.value} "
            f"({'forced' if forced else 'normal'})"
        )

        return event

    def get_state_duration(self) -> timedelta:
        """Get time spent in current state."""
        from datetime import timedelta
        return datetime.now() - self.state_since

    def get_state_history_summary(self) -> List[Dict[str, Any]]:
        """Get summary of state history."""
        return [
            {
                "state": state.value,
                "entered_at": entered_at.isoformat(),
            }
            for state, entered_at in self.state_history
        ]


# In-memory state machine storage (would be database in production)
_state_machines: Dict[UUID, ReadinessStateMachine] = {}


def get_state_machine(candidate_id: UUID, initial_state: ReadinessState = ReadinessState.OBSERVED) -> ReadinessStateMachine:
    """Get or create state machine for a candidate."""
    if candidate_id not in _state_machines:
        _state_machines[candidate_id] = ReadinessStateMachine(candidate_id, initial_state)
    return _state_machines[candidate_id]


# ============================================================================
# Governance Action Engine
# ============================================================================

class GovernanceActionType(str, Enum):
    """Types of governance actions that can be executed."""

    PROMOTE = "promote"
    """Promote candidate to a higher state."""

    DEMOTE = "demote"
    """Demote candidate to a lower state."""

    BLOCK = "block"
    """Block candidate from activation."""

    UNBLOCK = "unblock"
    """Remove block from candidate."""

    FORCE_TRANSITION = "force_transition"
    """Force a transition bypassing normal checks."""

    REQUEST_EVALUATION = "request_evaluation"
    """Request a new readiness evaluation."""

    SET_WATCHLIST = "set_watchlist"
    """Place candidate on watchlist."""

    CLEAR_WATCHLIST = "clear_watchlist"
    """Remove candidate from watchlist."""

    ARCHIVE = "archive"
    """Archive a candidate."""


class GovernanceAction(BaseModel):
    """A governance action to be executed."""

    id: UUID = Field(default_factory=uuid4)
    action_type: GovernanceActionType
    candidate_id: UUID

    # Action parameters
    target_state: Optional[ReadinessState] = None
    reason: Optional[str] = None
    requested_by: str = "system"
    force: bool = False
    evaluation_id: Optional[UUID] = None

    # Execution metadata
    created_at: datetime = Field(default_factory=datetime.now)
    executed_at: Optional[datetime] = None
    execution_duration_ms: int = 0
    success: bool = False
    error_message: Optional[str] = None

    # Result
    transition_event_id: Optional[UUID] = None


class GovernanceActionEngine:
    """
    Executes governance actions on readiness candidates.

    Governance actions are the operational commands that change
    the state or treatment of readiness candidates.
    """

    def __init__(
        self,
        state_machine_factory=get_state_machine,
        audit_log_adder=add_audit_log,
    ):
        self.state_machine_factory = state_machine_factory
        self.add_audit_log = audit_log_adder

    async def execute_action(
        self,
        action: GovernanceAction,
        current_state: ReadinessState,
        evaluation: Optional[ReadinessEvaluation] = None,
    ) -> GovernanceAction:
        """
        Execute a governance action.

        Args:
            action: The governance action to execute
            current_state: Current state of the candidate
            evaluation: Optional evaluation supporting the action

        Returns:
            Updated action with execution results
        """
        start_time = datetime.now()

        try:
            if action.action_type == GovernanceActionType.PROMOTE:
                success = await self._execute_promote(action, current_state, evaluation)

            elif action.action_type == GovernanceActionType.DEMOTE:
                success = await self._execute_demote(action, current_state)

            elif action.action_type == GovernanceActionType.BLOCK:
                success = await self._execute_block(action, current_state)

            elif action.action_type == GovernanceActionType.UNBLOCK:
                success = await self._execute_unblock(action, current_state)

            elif action.action_type == GovernanceActionType.FORCE_TRANSITION:
                success = await self._execute_force_transition(action, current_state)

            elif action.action_type == GovernanceActionType.SET_WATCHLIST:
                success = await self._execute_set_watchlist(action, current_state)

            elif action.action_type == GovernanceActionType.CLEAR_WATCHLIST:
                success = await self._execute_clear_watchlist(action, current_state)

            else:
                action.error_message = f"Unknown action type: {action.action_type}"
                success = False

            action.success = success

        except Exception as e:
            action.success = False
            action.error_message = str(e)
            logger.error(f"Error executing governance action: {e}")

        action.executed_at = datetime.now()
        action.execution_duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        return action

    async def _execute_promote(
        self,
        action: GovernanceAction,
        current_state: ReadinessState,
        evaluation: Optional[ReadinessEvaluation],
    ) -> bool:
        """Execute promote action."""
        if not action.target_state:
            action.error_message = "Promote action requires target_state"
            return False

        # Get state machine
        state_machine = self.state_machine_factory(action.candidate_id, current_state)

        # Check if transition is allowed
        if not action.force and not state_machine.can_transition_to(action.target_state):
            action.error_message = f"Cannot promote from {current_state.value} to {action.target_state.value}"
            return False

        # If evaluation provided, validate score
        if evaluation and not action.force:
            if evaluation.score.overall_score < 0.7:  # Default threshold
                action.error_message = f"Score {evaluation.score.overall_score:.2f} too low for promotion"
                return False

        # Execute transition
        event = state_machine.transition_to(
            action.target_state,
            transition_type="promotion",
            forced=action.force,
        )

        # Create audit log
        if evaluation:
            audit_log = TransitionAuditLog(
                candidate_id=action.candidate_id,
                from_state=current_state,
                to_state=action.target_state,
                transition_type="promotion",
                evaluation_id=evaluation.id,
                evaluation_outcome=evaluation.outcome,
                evaluation_score=evaluation.score.overall_score,
                policy_profile_id=evaluation.policy_profile_id,
                policy_version=evaluation.policy_version,
                triggered_by=action.requested_by,
                trigger_reason=action.reason or "Promotion action",
                force_used=action.force,
            )
            self.add_audit_log(audit_log)

        action.transition_event_id = event.id
        return True

    async def _execute_demote(
        self,
        action: GovernanceAction,
        current_state: ReadinessState,
    ) -> bool:
        """Execute demote action."""
        if not action.target_state:
            # Default to OBSERVED for demotion
            action.target_state = ReadinessState.OBSERVED

        state_machine = self.state_machine_factory(action.candidate_id, current_state)

        event = state_machine.transition_to(
            action.target_state,
            transition_type="demotion",
            forced=action.force,
        )

        audit_log = TransitionAuditLog(
            candidate_id=action.candidate_id,
            from_state=current_state,
            to_state=action.target_state,
            transition_type="demotion",
            evaluation_id=uuid4(),
            evaluation_outcome=ReadinessOutcome.OBSERVED,
            evaluation_score=0.0,
            policy_profile_id="default",
            policy_version="1.0",
            triggered_by=action.requested_by,
            trigger_reason=action.reason or "Demotion action",
            force_used=action.force,
        )
        self.add_audit_log(audit_log)

        action.transition_event_id = event.id
        return True

    async def _execute_block(
        self,
        action: GovernanceAction,
        current_state: ReadinessState,
    ) -> bool:
        """Execute block action."""
        state_machine = self.state_machine_factory(action.candidate_id, current_state)

        event = state_machine.transition_to(
            ReadinessState.BLOCKED,
            transition_type="block",
            forced=True,  # Blocks are always forced
        )

        audit_log = TransitionAuditLog(
            candidate_id=action.candidate_id,
            from_state=current_state,
            to_state=ReadinessState.BLOCKED,
            transition_type="block",
            evaluation_id=uuid4(),
            evaluation_outcome=ReadinessOutcome.BLOCKED,
            evaluation_score=0.0,
            policy_profile_id="default",
            policy_version="1.0",
            triggered_by=action.requested_by,
            trigger_reason=action.reason or "Block action",
            force_used=True,
        )
        self.add_audit_log(audit_log)

        action.transition_event_id = event.id
        return True

    async def _execute_unblock(
        self,
        action: GovernanceAction,
        current_state: ReadinessState,
    ) -> bool:
        """Execute unblock action."""
        if current_state != ReadinessState.BLOCKED:
            action.error_message = "Cannot unblock a candidate that is not blocked"
            return False

        state_machine = self.state_machine_factory(action.candidate_id, current_state)

        # Move to OBSERVED when unblocking
        event = state_machine.transition_to(
            ReadinessState.OBSERVED,
            transition_type="unblock",
            forced=True,
        )

        audit_log = TransitionAuditLog(
            candidate_id=action.candidate_id,
            from_state=current_state,
            to_state=ReadinessState.OBSERVED,
            transition_type="unblock",
            evaluation_id=uuid4(),
            evaluation_outcome=ReadinessOutcome.OBSERVED,
            evaluation_score=0.0,
            policy_profile_id="default",
            policy_version="1.0",
            triggered_by=action.requested_by,
            trigger_reason=action.reason or "Unblock action",
            force_used=True,
        )
        self.add_audit_log(audit_log)

        action.transition_event_id = event.id
        return True

    async def _execute_force_transition(
        self,
        action: GovernanceAction,
        current_state: ReadinessState,
    ) -> bool:
        """Execute force transition action."""
        if not action.target_state:
            action.error_message = "Force transition action requires target_state"
            return False

        state_machine = self.state_machine_factory(action.candidate_id, current_state)

        event = state_machine.transition_to(
            action.target_state,
            transition_type="forced",
            forced=True,
        )

        audit_log = TransitionAuditLog(
            candidate_id=action.candidate_id,
            from_state=current_state,
            to_state=action.target_state,
            transition_type="forced",
            evaluation_id=uuid4(),
            evaluation_outcome=ReadinessOutcome.REEVALUATE,
            evaluation_score=0.0,
            policy_profile_id="default",
            policy_version="1.0",
            triggered_by=action.requested_by,
            trigger_reason=action.reason or "Forced transition",
            force_used=True,
            governance_override=True,
        )
        self.add_audit_log(audit_log)

        action.transition_event_id = event.id
        return True

    async def _execute_set_watchlist(
        self,
        action: GovernanceAction,
        current_state: ReadinessState,
    ) -> bool:
        """Execute set watchlist action."""
        state_machine = self.state_machine_factory(action.candidate_id, current_state)

        # Can only move to watchlist from OBSERVED
        if current_state != ReadinessState.OBSERVED and not action.force:
            action.error_message = "Can only set watchlist from OBSERVED state"
            return False

        event = state_machine.transition_to(
            ReadinessState.WATCHLIST,
            transition_type="watchlist_promotion",
            forced=action.force,
        )

        audit_log = TransitionAuditLog(
            candidate_id=action.candidate_id,
            from_state=current_state,
            to_state=ReadinessState.WATCHLIST,
            transition_type="watchlist_promotion",
            evaluation_id=uuid4(),
            evaluation_outcome=ReadinessOutcome.WATCHLIST,
            evaluation_score=0.0,
            policy_profile_id="default",
            policy_version="1.0",
            triggered_by=action.requested_by,
            trigger_reason=action.reason or "Added to watchlist",
            force_used=action.force,
        )
        self.add_audit_log(audit_log)

        action.transition_event_id = event.id
        return True

    async def _execute_clear_watchlist(
        self,
        action: GovernanceAction,
        current_state: ReadinessState,
    ) -> bool:
        """Execute clear watchlist action."""
        if current_state != ReadinessState.WATCHLIST:
            action.error_message = "Cannot clear watchlist for a non-watchlisted candidate"
            return False

        state_machine = self.state_machine_factory(action.candidate_id, current_state)

        # Move back to OBSERVED when clearing watchlist
        event = state_machine.transition_to(
            ReadinessState.OBSERVED,
            transition_type="watchlist_clear",
            forced=False,
        )

        audit_log = TransitionAuditLog(
            candidate_id=action.candidate_id,
            from_state=current_state,
            to_state=ReadinessState.OBSERVED,
            transition_type="watchlist_clear",
            evaluation_id=uuid4(),
            evaluation_outcome=ReadinessOutcome.OBSERVED,
            evaluation_score=0.0,
            policy_profile_id="default",
            policy_version="1.0",
            triggered_by=action.requested_by,
            trigger_reason=action.reason or "Removed from watchlist",
            force_used=False,
        )
        self.add_audit_log(audit_log)

        action.transition_event_id = event.id
        return True


def get_governance_engine() -> GovernanceActionEngine:
    """Get the global governance engine instance."""
    return GovernanceActionEngine()


# ============================================================================
# Readiness Transition Controller
# ============================================================================

class ReadinessTransitionController:
    """
    Main controller for readiness state transitions.

    Orchestrates the complete transition workflow:
    1. Validate transition request
    2. Check policy compliance
    3. Execute transition
    4. Record audit trail
    5. Notify stakeholders
    """

    def __init__(
        self,
        policy_validator=None,
        governance_engine=None,
        scoring_engine=None,
    ):
        self.policy_validator = policy_validator or TransitionPolicyValidator()
        self.governance_engine = governance_engine or get_governance_engine()
        self.scoring_engine = scoring_engine or get_scoring_engine()

    async def request_transition(
        self,
        request: TransitionRequest,
        current_state: ReadinessState,
        evaluation: Optional[ReadinessEvaluation] = None,
    ) -> TransitionResult:
        """
        Process a transition request.

        Args:
            request: The transition request
            current_state: Current state of the candidate
            evaluation: Optional evaluation supporting the request

        Returns:
            TransitionResult with outcome
        """
        # Step 1: Validate request
        is_valid, errors = self.policy_validator.validate_transition_request(
            request,
            current_state,
            evaluation,
        )

        if not is_valid and not request.force:
            return TransitionResult(
                success=False,
                candidate_id=request.candidate_id,
                from_state=current_state,
                to_state=request.target_state,
                reason="Validation failed: " + "; ".join(errors),
                errors=errors,
            )

        # Step 2: For forced transitions, validate force requirements
        if request.force:
            is_valid, force_errors = self.policy_validator.validate_forced_transition(
                request,
                current_state,
            )
            if not is_valid:
                return TransitionResult(
                    success=False,
                    candidate_id=request.candidate_id,
                    from_state=current_state,
                    to_state=request.target_state,
                    reason="Force validation failed: " + "; ".join(force_errors),
                    errors=force_errors,
                )

        # Step 3: Execute governance action
        action = GovernanceAction(
            action_type=GovernanceActionType.FORCE_TRANSITION if request.force else GovernanceActionType.PROMOTE,
            candidate_id=request.candidate_id,
            target_state=request.target_state,
            reason=request.reason,
            requested_by=request.requested_by,
            force=request.force,
            evaluation_id=request.evaluation_id,
        )

        executed_action = await self.governance_engine.execute_action(
            action,
            current_state,
            evaluation,
        )

        if not executed_action.success:
            return TransitionResult(
                success=False,
                candidate_id=request.candidate_id,
                from_state=current_state,
                to_state=request.target_state,
                reason="Action execution failed: " + (executed_action.error_message or "Unknown error"),
                errors=[executed_action.error_message] if executed_action.error_message else [],
            )

        # Step 4: Return success result
        return TransitionResult(
            success=True,
            candidate_id=request.candidate_id,
            from_state=current_state,
            to_state=request.target_state,
            reason=request.reason or "Transition completed successfully",
            transition_event_id=executed_action.transition_event_id,
        )

    async def auto_transition_from_evaluation(
        self,
        evaluation: ReadinessEvaluation,
        current_state: ReadinessState,
    ) -> Optional[TransitionResult]:
        """
        Automatically determine and execute transition based on evaluation.

        Args:
            evaluation: The evaluation result
            current_state: Current state of the candidate

        Returns:
            TransitionResult if transition was executed, None if no change
        """
        # Don't auto-transition if evaluation says not to
        if not evaluation.should_transition:
            return None

        # Determine target state from evaluation
        target_state = evaluation.recommended_state

        # Skip if already in target state
        if target_state == current_state:
            return None

        # Create transition request
        request = TransitionRequest(
            candidate_id=evaluation.candidate_id,
            target_state=target_state,
            requested_by="system",
            reason=evaluation.reason,
            force=False,
            evaluation_id=evaluation.id,
        )

        # Process transition
        return await self.request_transition(request, current_state, evaluation)

    async def force_state(
        self,
        candidate_id: UUID,
        target_state: ReadinessState,
        requested_by: str,
        reason: str,
        current_state: ReadinessState,
    ) -> TransitionResult:
        """
        Force a candidate to a specific state.

        This bypasses normal validation and should only be used
        for operational overrides.

        Args:
            candidate_id: ID of the candidate
            target_state: State to force to
            requested_by: Who is requesting this
            reason: Reason for the forced transition
            current_state: Current state of the candidate

        Returns:
            TransitionResult with outcome
        """
        request = TransitionRequest(
            candidate_id=candidate_id,
            target_state=target_state,
            requested_by=requested_by,
            reason=reason,
            force=True,
        )

        return await self.request_transition(request, current_state)

    def get_transition_history(
        self,
        candidate_id: UUID,
    ) -> List[TransitionAuditLog]:
        """Get transition history for a candidate."""
        return get_audit_logs(candidate_id)


# Global transition controller instance
_transition_controller: Optional[ReadinessTransitionController] = None


def get_transition_controller() -> ReadinessTransitionController:
    """Get the global transition controller instance."""
    global _transition_controller
    if _transition_controller is None:
        _transition_controller = ReadinessTransitionController()
    return _transition_controller
