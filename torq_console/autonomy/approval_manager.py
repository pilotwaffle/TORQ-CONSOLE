"""
Approval Manager - Manages approval workflows for autonomous actions.

The Approval Manager is responsible for:
- Generating approval requests for gated actions
- Managing approval lifecycle (pending, approved, denied)
- Tracking expiration and timeouts
- Notifying approvers
- Recording approval decisions for audit
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from .models import (
    AutonomousTask, ApprovalRequest, ApprovalStatus,
    ActionRisk, PolicyDecision
)
from .state_store import StateStore


logger = logging.getLogger(__name__)


class ApprovalInbox:
    """
    Inbox for managing pending approval requests.

    Provides query and notification capabilities for approvers.
    """

    def __init__(self, state_store: StateStore):
        self.state_store = state_store
        self.logger = logging.getLogger(__name__)

    async def get_pending_approvals(
        self,
        workspace_id: Optional[str] = None,
        risk_level: Optional[ActionRisk] = None
    ) -> List[ApprovalRequest]:
        """Get all pending approval requests."""
        approvals = await self.state_store.list_approvals(
            status="pending",
            workspace_id=workspace_id
        )

        if risk_level:
            approvals = [a for a in approvals if a.risk_level == risk_level]

        # Sort by severity and created time
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        approvals.sort(
            key=lambda a: (
                severity_order.get(a.risk_level.value, 4),
                a.created_at
            )
        )

        return approvals

    async def get_approval_count_by_status(
        self,
        workspace_id: Optional[str] = None
    ) -> Dict[str, int]:
        """Get count of approvals by status."""
        approvals = await self.state_store.list_approvals(workspace_id=workspace_id)

        counts = {"pending": 0, "approved": 0, "denied": 0, "expired": 0}
        for approval in approvals:
            counts[approval.status.value] = counts.get(approval.status.value, 0) + 1

        return counts


class ApprovalManager:
    """
    Manager for approval workflows.

    Responsibilities:
    - Create approval requests from tasks
    - Process approval decisions
    - Handle expiration
    - Track approval history
    - Notify approvers
    """

    def __init__(
        self,
        state_store: StateStore,
        default_approval_timeout: int = 3600  # 1 hour default
    ):
        self.state_store = state_store
        self.default_approval_timeout = default_approval_timeout
        self.logger = logging.getLogger(__name__)
        self.inbox = ApprovalInbox(state_store)

        # Background expiration checker
        self._running = False
        self._expiration_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the approval manager."""
        if self._running:
            return

        self._running = True
        self._expiration_task = asyncio.create_task(self._check_expirations())
        self.logger.info("Approval manager started")

    async def stop(self):
        """Stop the approval manager."""
        self._running = False
        if self._expiration_task:
            self._expiration_task.cancel()
            try:
                await self._expiration_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Approval manager stopped")

    async def _check_expirations(self):
        """Background loop that checks for expired approvals."""
        while self._running:
            try:
                await self._expire_old_approvals()
                await asyncio.sleep(60)  # Check every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error checking expirations: {e}")

    async def _expire_old_approvals(self):
        """Expire approvals that have timed out."""
        now = time.time()
        approvals = await self.state_store.list_approvals(status="pending")

        for approval in approvals:
            if approval.expires_at and approval.expires_at < now:
                await self._update_approval_status(
                    approval.approval_id,
                    ApprovalStatus.EXPIRED
                )
                self.logger.info(f"Approval {approval.approval_id} expired")

    async def create_approval_request(
        self,
        task: AutonomousTask,
        policy_decision: PolicyDecision,
        timeout_seconds: Optional[int] = None
    ) -> Optional[ApprovalRequest]:
        """
        Create an approval request for a task.

        Args:
            task: The task requiring approval
            policy_decision: The policy decision that required approval
            timeout_seconds: Optional custom timeout

        Returns:
            Created ApprovalRequest, or None if not needed
        """
        if not policy_decision.requires_approval:
            return None

        # Calculate expiration
        timeout = timeout_seconds or self.default_approval_timeout
        expires_at = time.time() + timeout

        # Create approval request
        approval = ApprovalRequest(
            task_id=task.task_id,
            requested_action=task.name,
            action_description=task.description or task.prompt_template or "",
            risk_level=policy_decision.risk_level,
            policy_level=policy_decision.policy_level,
            trigger_reason=task.parameters.get("trigger_event", {}).get("event_type", "autonomous_task"),
            workspace_id=task.workspace_id,
            environment=task.environment,
            expires_at=expires_at,
            evidence=task.parameters.get("evidence", [])
        )

        # Save approval
        await self.state_store.save_approval(approval)

        # Update task with approval reference
        task.approval_id = approval.approval_id
        task.approval_required = True

        self.logger.info(
            f"Created approval request {approval.approval_id} "
            f"for task {task.task_id}"
        )

        # Notify approvers (would send to UI/webhook in production)
        await self._notify_approvers(approval)

        return approval

    async def approve(
        self,
        approval_id: str,
        approved_by: str,
        comment: Optional[str] = None
    ) -> bool:
        """
        Approve an approval request.

        Args:
            approval_id: The approval request ID
            approved_by: User ID of the approver
            comment: Optional comment

        Returns:
            True if approval was successful
        """
        approval = await self.state_store.load_approval(approval_id)
        if not approval:
            self.logger.error(f"Approval {approval_id} not found")
            return False

        if approval.status != ApprovalStatus.PENDING:
            self.logger.warning(
                f"Approval {approval_id} is not pending (status: {approval.status})"
            )
            return False

        # Check expiration
        if approval.expires_at and approval.expires_at < time.time():
            self.logger.warning(f"Approval {approval_id} has expired")
            return False

        # Update approval
        await self._update_approval_status(
            approval_id,
            ApprovalStatus.APPROVED,
            approved_by=approved_by,
            approved_at=time.time()
        )

        # Add comment if provided
        if comment:
            await self.state_store.update_approval(
                approval_id,
                {"denied_reason": f"Approved with comment: {comment}"}
            )

        self.logger.info(
            f"Approval {approval_id} approved by {approved_by}"
        )

        return True

    async def deny(
        self,
        approval_id: str,
        denied_by: str,
        reason: str
    ) -> bool:
        """
        Deny an approval request.

        Args:
            approval_id: The approval request ID
            denied_by: User ID of the denier
            reason: Reason for denial

        Returns:
            True if denial was successful
        """
        approval = await self.state_store.load_approval(approval_id)
        if not approval:
            self.logger.error(f"Approval {approval_id} not found")
            return False

        if approval.status != ApprovalStatus.PENDING:
            self.logger.warning(
                f"Approval {approval_id} is not pending (status: {approval.status})"
            )
            return False

        # Update approval
        await self._update_approval_status(
            approval_id,
            ApprovalStatus.DENIED
        )

        await self.state_store.update_approval(
            approval_id,
            {
                "approved_by": denied_by,
                "denied_reason": reason
            }
        )

        self.logger.info(
            f"Approval {approval_id} denied by {denied_by}: {reason}"
        )

        return True

    async def cancel(self, approval_id: str) -> bool:
        """Cancel an approval request."""
        return await self._update_approval_status(
            approval_id,
            ApprovalStatus.CANCELLED
        )

    async def _update_approval_status(
        self,
        approval_id: str,
        status: ApprovalStatus,
        **kwargs
    ) -> bool:
        """Update approval status."""
        updates = {"status": status.value}
        updates.update(kwargs)

        return await self.state_store.update_approval(approval_id, updates)

    async def _notify_approvers(self, approval: ApprovalRequest):
        """Notify approvers of pending approval."""
        # In production, this would send notifications via:
        # - WebSocket to UI
        # - Email
        # - Webhook
        # - Slack/Discord

        self.logger.info(
            f"Notification: Approval {approval.approval_id} pending "
            f"({approval.risk_level.value} risk)"
        )

    async def get_approval(self, approval_id: str) -> Optional[ApprovalRequest]:
        """Get an approval by ID."""
        return await self.state_store.load_approval(approval_id)

    async def list_approvals(
        self,
        status: Optional[str] = None,
        workspace_id: Optional[str] = None,
        limit: int = 100
    ) -> List[ApprovalRequest]:
        """List approvals with filtering."""
        approvals = await self.state_store.list_approvals(status, workspace_id)
        return approvals[:limit]

    async def get_task_approval(self, task_id: str) -> Optional[ApprovalRequest]:
        """Get the approval request for a task."""
        approvals = await self.state_store.list_approvals()
        for approval in approvals:
            if approval.task_id == task_id:
                return approval
        return None

    async def is_approved(self, task_id: str) -> bool:
        """Check if a task has been approved."""
        approval = await self.get_task_approval(task_id)
        return approval is not None and approval.status == ApprovalStatus.APPROVED


# Singleton instance
_approval_manager: Optional[ApprovalManager] = None


def get_approval_manager(state_store: Optional[StateStore] = None) -> ApprovalManager:
    """Get the singleton approval manager instance."""
    global _approval_manager
    if _approval_manager is None:
        _state_store = state_store or get_state_store()
        _approval_manager = ApprovalManager(_state_store)
    return _approval_manager


# Import at end to avoid circular dependency
from .state_store import get_state_store
