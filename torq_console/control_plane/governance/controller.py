"""
TORQ Control Plane - Governance Controller

L7-M1: Controller for governance actions and approvals.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


# Import from models
from .models import (
    ActionStatus,
    ActionType,
    GovernanceActionRequest,
    GovernanceActionQueue,
    GovernanceOverride,
    ApprovalPolicy,
    PromotionRequest,
    ReadinessGovernanceView,
    create_promotion_request,
)


# ============================================================================
# Approval Result
# ============================================================================

class ApprovalResult(BaseModel):
    """
    Result of an approval decision.
    """
    approved: bool
    approved_by: str
    approved_at: datetime = Field(default_factory=datetime.now)
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None


# ============================================================================
# Governance Controller
# ============================================================================

class GovernanceController:
    """
    Controller for governance actions and approval workflow.

    Manages the queue of governance actions, handles
    approvals, and executes approved actions.
    """

    def __init__(self):
        """Initialize the governance controller."""
        self._queue = GovernanceActionQueue()
        self._overrides: List[GovernanceOverride] = []
        self._policies: Dict[str, ApprovalPolicy] = {}
        self._promotion_requests: List[PromotionRequest] = []

        # Load default policies
        self._load_default_policies()

    def _load_default_policies(self):
        """Load default approval policies."""
        # Default policy: auto-approve low-risk promotions
        self._policies["low_risk_promotion"] = ApprovalPolicy(
            id="low_risk_promotion",
            name="Low Risk Promotion Auto-Approve",
            description="Auto-approve promotions with high confidence scores",
            action_types=["promote"],
            auto_approve=True,
            approvers=0,
            max_value_threshold=0.9,  # Auto-approve if confidence >= 0.9
        )

        # High-risk actions require quorum
        self._policies["high_risk_override"] = ApprovalPolicy(
            id="high_risk_override",
            name="High Risk Override Requires Quorum",
            description="Critical overrides require quorum approval",
            action_types=["force_transition", "override_policy"],
            auto_approve=False,
            required_approvers=2,
            require_quorum_for=["force_transition", "override_policy"],
            approval_timeout_hours=48,
        )

    async def submit_action(
        self,
        action: GovernanceActionRequest,
    ) -> GovernanceActionRequest:
        """
        Submit a governance action for approval.

        Args:
            action: Action to submit

        Returns:
            The submitted action
        """
        # Check if auto-approval applies
        policy = self._get_applicable_policy(action)

        if policy and policy.auto_approve:
            action.status = ActionStatus.APPROVED
            action.approved_by = "system"
            action.approved_at = datetime.now()
            logger.info(
                f"[Governance] Auto-approved action {action.id}: {action.action_type}"
            )

            # Execute the action
            await self._execute_action(action)

        else:
            # Add to queue
            self._queue.add_action(action)
            logger.info(
                f"[Governance] Queued action {action.id}: {action.action_type} "
                f"by {action.requested_by}"
            )

        return action

    async def approve_action(
        self,
        action_id: UUID,
        approver: str,
        notes: Optional[str] = None,
    ) -> GovernanceActionRequest:
        """
        Approve a pending action.

        Args:
            action_id: ID of action to approve
            approver: User approving the action
            notes: Optional approval notes

        Returns:
            The approved action
        """
        action = self._queue.get_action(action_id)

        if not action:
            raise ValueError(f"Action not found: {action_id}")

        if action.status != ActionStatus.PENDING:
            raise ValueError(f"Action not pending: {action.status}")

        # Check if quorum is required
        policy = self._get_applicable_policy(action)
        requires_quorum = (
            policy and action.action_type.value in policy.require_quorum_for
        )

        # Record approval
        action.approved_by = approver
        action.approved_at = datetime.now()
        action.status = ActionStatus.APPROVED

        logger.info(
            f"[Governance] Action {action_id} approved by {approver}"
        )

        # Execute the action
        if not requires_quorum:
            await self._execute_action(action)
        else:
            # Quorum handling - check if we have enough approvals
            # For now, single approval is enough
            await self._execute_action(action)

        return action

    async def reject_action(
        self,
        action_id: UUID,
        rejected_by: str,
        reason: str,
    ) -> GovernanceActionRequest:
        """
        Reject a pending action.

        Args:
            action_id: ID of action to reject
            rejected_by: User rejecting the action
            reason: Rejection reason

        Returns:
            The rejected action
        """
        action = self._queue.get_action(action_id)

        if not action:
            raise ValueError(f"Action not found: {action_id}")

        if action.status != ActionStatus.PENDING:
            raise ValueError(f"Action not pending: {action.status}")

        action.status = ActionStatus.REJECTED
        action.rejection_reason = reason

        logger.info(
            f"[Governance] Action {action_id} rejected by {rejected_by}: {reason}"
        )

        return action

    async def _execute_action(self, action: GovernanceActionRequest):
        """
        Execute an approved action.

        Args:
            action: Action to execute
        """
        action.status = ActionStatus.EXECUTING
        action.executed_at = datetime.now()

        try:
            # Route to appropriate handler
            if action.action_type == ActionType.PROMOTE:
                result = await self._execute_promote(action)
            elif action.action_type == ActionType.BLOCK:
                result = await self._execute_block(action)
            elif action.action_type == ActionType.FORCE_TRANSITION:
                result = await self._execute_force_transition(action)
            elif action.action_type == ActionType.VALIDATE_PATTERN:
                result = await self._execute_validate_pattern(action)
            elif action.action_type == ActionType.START_MISSION:
                result = await self._execute_start_mission(action)
            elif action.action_type == ActionType.STOP_MISSION:
                result = await self._execute_stop_mission(action)
            else:
                raise ValueError(f"Unknown action type: {action.action_type}")

            action.status = ActionStatus.COMPLETED
            action.execution_result = result

            logger.info(
                f"[Governance] Action {action.id} completed successfully"
            )

        except Exception as e:
            action.status = ActionStatus.FAILED
            action.error_message = str(e)
            logger.error(
                f"[Governance] Action {action.id} failed: {e}"
            )

    async def _execute_promote(
        self,
        action: GovernanceActionRequest,
    ) -> Dict[str, Any]:
        """Execute a promotion action."""
        from ...readiness.transition_controller import (
            get_transition_controller,
        )
        from ...readiness.readiness_models import ReadinessState

        controller = get_transition_controller()
        candidate_id = UUID(action.target_id)

        # Get target state
        target_state = action.parameters.get("target_state", "ready")

        result = await controller.request_transition(
            candidate_id=candidate_id,
            target_state=target_state,
            transition_type="promotion",
            requested_by=action.requested_by,
            reason=f"Governance action {action.id}",
        )

        return {
            "candidate_id": str(candidate_id),
            "target_state": target_state,
            "success": result.success,
        }

    async def _execute_block(
        self,
        action: GovernanceActionRequest,
    ) -> Dict[str, Any]:
        """Execute a block action."""
        from ...readiness.transition_controller import (
            get_transition_controller,
        )

        controller = get_transition_controller()
        candidate_id = UUID(action.target_id)

        result = await controller.request_transition(
            candidate_id=candidate_id,
            target_state="blocked",
            transition_type="block",
            requested_by=action.requested_by,
            reason=action.parameters.get("reason", "Blocked by governance"),
        )

        return {
            "candidate_id": str(candidate_id),
            "success": result.success,
        }

    async def _execute_force_transition(
        self,
        action: GovernanceActionRequest,
    ) -> Dict[str, Any]:
        """Execute a force transition action."""
        from ...readiness.transition_controller import (
            get_transition_controller,
        )

        controller = get_transition_controller()
        candidate_id = UUID(action.target_id)
        target_state = action.parameters.get("target_state")

        result = await controller.force_transition(
            candidate_id=candidate_id,
            target_state=target_state,
            requested_by=action.requested_by,
            reason=action.parameters.get("reason", "Governance override"),
        )

        # Record override
        override = GovernanceOverride(
            target_type="candidate",
            target_id=action.target_id,
            original_decision="<previous state>",
            override_decision=target_state,
            override_reason=action.parameters.get("reason", ""),
            overridden_by=action.requested_by,
        )
        self._overrides.append(override)

        return {
            "candidate_id": str(candidate_id),
            "target_state": target_state,
            "success": result.success,
            "override_id": str(override.id),
        }

    async def _execute_validate_pattern(self, action: GovernanceActionRequest) -> Dict[str, Any]:
        """Execute a pattern validation action."""
        # Placeholder - would integrate with pattern system
        return {
            "pattern_id": action.target_id,
            "status": "validated",
        }

    async def _execute_start_mission(self, action: GovernanceActionRequest) -> Dict[str, Any]:
        """Execute a mission start action."""
        # Placeholder - would integrate with mission system
        return {
            "mission_id": action.target_id,
            "status": "started",
        }

    async def _execute_stop_mission(self, action: GovernanceActionRequest) -> Dict[str, Any]:
        """Execute a mission stop action."""
        # Placeholder - would integrate with mission system
        return {
            "mission_id": action.target_id,
            "status": "stopped",
        }

    # ------------------------------------------------------------------------
    # Promotion Management
    # ------------------------------------------------------------------------

    async def request_promotion(
        self,
        request: PromotionRequest,
    ) -> PromotionRequest:
        """
        Request promotion of a candidate.

        Args:
            request: Promotion request

        Returns:
            The promotion request
        """
        # Check if auto-approval applies
        policy = self._policies.get("low_risk_promotion")

        if request.confidence_score >= (policy.max_value_threshold or 0.9):
            # Auto-approve
            request.approved = True
            request.approved_by = "system"
            request.approved_at = datetime.now()

            # Execute promotion
            await self._execute_promotion_request(request)
        else:
            # Add to queue
            self._promotion_requests.append(request)

        return request

    async def _execute_promotion_request(self, request: PromotionRequest):
        """Execute a promotion request."""
        from ...readiness.transition_controller import (
            get_transition_controller,
        )

        controller = get_transition_controller()

        result = await controller.request_transition(
            candidate_id=request.candidate_id,
            target_state=request.requested_state,
            transition_type="promotion",
            requested_by=request.requested_by,
            reason=f"Promotion request {request.id}",
        )

        request.executed = True
        request.execution_result = {
            "success": result.success,
            "previous_state": result.previous_state.value if result.previous_state else None,
            "new_state": result.new_state.value if result.new_state else None,
        }

    # ------------------------------------------------------------------------
    # Query Methods
    # ------------------------------------------------------------------------

    def get_queue(self) -> GovernanceActionQueue:
        """Get the current action queue."""
        return self._queue

    def get_pending_actions(self) -> List[GovernanceActionRequest]:
        """Get all pending actions."""
        return self._queue.get_pending_actions()

    def get_action(self, action_id: UUID) -> Optional[GovernanceActionRequest]:
        """Get an action by ID."""
        return self._queue.get_action(action_id)

    def get_overrides(
        self,
        limit: int = 50,
    ) -> List[GovernanceOverride]:
        """Get recent override history."""
        return sorted(
            self._overrides,
            key=lambda o: o.overridden_at,
            reverse=True,
        )[:limit]

    def get_promotion_requests(
        self,
        status: Optional[str] = None,
    ) -> List[PromotionRequest]:
        """
        Get promotion requests with optional filtering.

        Args:
            status: Optional status filter

        Returns:
            List of promotion requests
        """
        requests = self._promotion_requests

        if status:
            if status == "pending":
                requests = [r for r in requests if not r.executed]
            elif status == "approved":
                requests = [r for r in requests if r.approved]
            elif status == "executed":
                requests = [r for r in requests if r.executed]

        return sorted(
            requests,
            key=lambda r: r.requested_at,
            reverse=True,
        )

    def get_governance_view(self) -> ReadinessGovernanceView:
        """Get aggregated readiness governance view."""
        from ...readiness.query_service import get_query_service

        query_service = get_query_service()

        # Get candidate counts
        all_candidates = query_service.list_candidates()
        ready = query_service.list_ready_candidates(limit=500)
        blocked = query_service.list_blocked_candidates(limit=500)

        return ReadinessGovernanceView(
            pending_promotions=self.get_promotion_requests("pending"),
            recent_promotions=self.get_promotion_requests("executed")[:10],
            recent_overrides=self.get_overrides()[:10],
            total_candidates=all_candidates.total_count,
            ready_candidates=ready.total_count,
            blocked_candidates=blocked.total_count,
            pending_actions=len(self.get_pending_actions()),
            active_policies=list(self._policies.keys()),
        )

    def _get_applicable_policy(
        self,
        action: GovernanceActionRequest,
    ) -> Optional[ApprovalPolicy]:
        """Get the applicable approval policy for an action."""
        for policy in self._policies.values():
            if action.action_type.value in policy.action_types:
                return policy
        return None


# Global governance controller instance
_controller: Optional[GovernanceController] = None


def get_governance_controller() -> GovernanceController:
    """Get the global governance controller instance."""
    global _controller
    if _controller is None:
        _controller = GovernanceController()
    return _controller
