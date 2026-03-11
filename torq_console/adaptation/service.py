"""
Adaptation Proposal Service

Orchestrates the conversion of learning signals into governed
adaptation proposals with risk classification and approval workflows.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .models import (
    AdaptationProposalCreate,
    AdaptationProposalRead,
    AdaptationProposalUpdate,
    ApprovalStatus,
    RiskTier,
    ApprovalMode,
    PolicyConfig,
    PolicyEvaluation,
    ProposalApplicationResult,
)
from .policy import AdaptationPolicyEngine
from .mapper import SignalToProposalMapper


logger = logging.getLogger(__name__)


class AdaptationProposalService:
    """
    Service for managing adaptation proposals.

    Flow:
    1. Learning signal received
    2. Policy engine evaluates eligibility
    3. If eligible, mapper converts signal to proposal
    4. Proposal stored with appropriate approval mode
    5. Proposal reviewed (if required)
    6. Proposal applied (creating versioned behavior)
    7. Proposal can be rolled back
    """

    def __init__(self, supabase_client, config: Optional[PolicyConfig] = None):
        self.supabase = supabase
        self.config = config or PolicyConfig()
        self.policy_engine = AdaptationPolicyEngine(self.config)
        self.mapper = SignalToProposalMapper()

    # ========================================================================
    # Proposal Generation
    # ========================================================================

    async def generate_proposal_from_signal(
        self,
        signal: Dict[str, Any],
        target_scope: Optional[str] = None,
        force_create: bool = False
    ) -> Optional[AdaptationProposalRead]:
        """
        Generate an adaptation proposal from a learning signal.

        Args:
            signal: Learning signal data
            target_scope: Override scope for the proposal
            force_create: Bypass policy guardrails (use with caution)

        Returns:
            AdaptationProposalRead if proposal created, None otherwise
        """
        # Fetch existing proposals for policy evaluation
        scope_id = target_scope or signal.get("scope_id", "unknown")
        existing_proposals = await self._get_existing_proposals_for_target(scope_id)

        # Evaluate eligibility
        if not force_create:
            evaluation = self.policy_engine.evaluate_signal_eligibility(
                signal, existing_proposals
            )
            if not evaluation.can_propose:
                logger.info(f"Signal not eligible for proposal: {evaluation.reason}")
                return None

        # Map signal to proposal
        candidate_version = self._generate_candidate_version(signal)

        proposal_create = self.mapper.map_signal_to_proposal(
            signal=signal,
            target_scope=scope_id,
            candidate_version=candidate_version
        )

        if not proposal_create:
            logger.warning(f"Could not map signal to proposal: {signal.get('signal_type')}")
            return None

        # Override risk classification if policy engine suggested different
        if not force_create:
            evaluation = self.policy_engine.evaluate_signal_eligibility(
                signal, existing_proposals
            )
            if evaluation.suggested_risk_tier:
                proposal_create.risk_tier = evaluation.suggested_risk_tier
            if evaluation.suggested_approval_mode:
                proposal_create.approval_mode = evaluation.suggested_approval_mode

        # Set initial status based on approval mode
        if proposal_create.approval_mode == ApprovalMode.AUTO_LOW_RISK and self.config.tier_1_auto_apply:
            proposal_create.status = ApprovalStatus.APPROVED
        else:
            proposal_create.status = ApprovalStatus.PENDING_REVIEW

        # Persist proposal
        proposal_id = await self._persist_proposal(proposal_create)

        # Read back and return
        return await self.get_proposal(proposal_id)

    async def generate_proposals_from_signals(
        self,
        signals: List[Dict[str, Any]],
        force_create: bool = False
    ) -> List[AdaptationProposalRead]:
        """Generate proposals from multiple signals."""
        proposals = []

        for signal in signals:
            try:
                proposal = await self.generate_proposal_from_signal(
                    signal=signal,
                    force_create=force_create
                )
                if proposal:
                    proposals.append(proposal)
            except Exception as e:
                logger.error(f"Error generating proposal from signal: {e}")
                continue

        logger.info(f"Generated {len(proposals)} proposals from {len(signals)} signals")
        return proposals

    # ========================================================================
    # Proposal Review and Approval
    # ========================================================================

    async def review_proposal(
        self,
        proposal_id: str,
        reviewed_by: str,
        approved: bool,
        review_notes: Optional[str] = None,
        metrics_baseline: Optional[Dict[str, float]] = None
    ) -> Optional[AdaptationProposalRead]:
        """
        Review and approve/reject a proposal.

        Args:
            proposal_id: Proposal to review
            reviewed_by: Reviewer identifier
            approved: True to approve, False to reject
            review_notes: Optional review notes
            metrics_baseline: Optional baseline metrics for comparison

        Returns:
            Updated proposal
        """
        proposal = await self.get_proposal(proposal_id)
        if not proposal:
            logger.warning(f"Proposal not found: {proposal_id}")
            return None

        # Cannot review already applied proposals
        if proposal.status in [ApprovalStatus.APPLIED, ApprovalStatus.ROLLED_BACK]:
            logger.warning(f"Proposal {proposal_id} already {proposal.status}")
            return None

        new_status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED

        update = AdaptationProposalUpdate(
            status=new_status,
            reviewed_by=reviewed_by,
            review_notes=review_notes,
            metrics_baseline=metrics_baseline
        )

        return await self.update_proposal(proposal_id, update)

    async def approve_proposal(
        self,
        proposal_id: str,
        reviewed_by: str,
        review_notes: Optional[str] = None
    ) -> Optional[AdaptationProposalRead]:
        """Approve a proposal."""
        return await self.review_proposal(
            proposal_id=proposal_id,
            reviewed_by=reviewed_by,
            approved=True,
            review_notes=review_notes
        )

    async def reject_proposal(
        self,
        proposal_id: str,
        reviewed_by: str,
        review_notes: Optional[str] = None
    ) -> Optional[AdaptationProposalRead]:
        """Reject a proposal."""
        return await self.review_proposal(
            proposal_id=proposal_id,
            reviewed_by=reviewed_by,
            approved=False,
            review_notes=review_notes
        )

    # ========================================================================
    # Proposal Application
    # ========================================================================

    async def apply_proposal(
        self,
        proposal_id: str,
        applied_by: str,
        force_apply: bool = False
    ) -> Optional[ProposalApplicationResult]:
        """
        Apply an approved proposal.

        Creates versioned behavior change. Returns rollback instructions.

        Args:
            proposal_id: Proposal to apply
            applied_by: User/system applying the change
            force_apply: Bypass policy checks

        Returns:
            Application result with rollback instructions
        """
        proposal_dict = await self._get_proposal_raw(proposal_id)
        if not proposal_dict:
            logger.warning(f"Proposal not found: {proposal_id}")
            return None

        # Check if can apply
        if not force_apply:
            evaluation = self.policy_engine.evaluate_proposal_application(
                proposal_dict, self.config
            )
            if not evaluation.can_propose:
                logger.warning(f"Cannot apply proposal: {evaluation.reason}")
                return None

        # Apply the change
        applied_at = datetime.now()
        applied_version = proposal_dict.get("candidate_version", str(uuid.uuid4()))

        # Update proposal status
        await self.supabase.table("adaptation_proposals").update({
            "status": ApprovalStatus.APPLIED.value,
            "applied_by": applied_by,
            "applied_at": applied_at.isoformat(),
            "updated_at": applied_at.isoformat()
        }).eq("proposal_id", proposal_id).execute()

        # Generate rollback instructions
        rollback_instructions = self._generate_rollback_instructions(proposal_dict)

        # Generate change summary
        change_summary = self._generate_change_summary(proposal_dict)

        logger.info(f"Applied proposal {proposal_id}: {change_summary}")

        return ProposalApplicationResult(
            proposal_id=proposal_id,
            success=True,
            applied_version=applied_version,
            applied_at=applied_at,
            change_summary=change_summary,
            rollback_instructions=rollback_instructions
        )

    async def rollback_proposal(
        self,
        proposal_id: str,
        rolled_back_by: str,
        reason: str
    ) -> bool:
        """
        Rollback an applied proposal.

        Restores previous behavior version.

        Args:
            proposal_id: Proposal to rollback
            rolled_back_by: User/system rolling back
            reason: Reason for rollback

        Returns:
            True if rollback succeeded
        """
        proposal = await self.get_proposal(proposal_id)
        if not proposal:
            return False

        if proposal.status != ApprovalStatus.APPLIED:
            logger.warning(f"Cannot rollback proposal in status: {proposal.status}")
            return False

        rolled_back_at = datetime.now()

        await self.supabase.table("adaptation_proposals").update({
            "status": ApprovalStatus.ROLLED_BACK.value,
            "rolled_back_by": rolled_back_by,
            "rolled_back_at": rolled_back_at.isoformat(),
            "rollback_reason": reason,
            "updated_at": rolled_back_at.isoformat()
        }).eq("proposal_id", proposal_id).execute()

        logger.info(f"Rolled back proposal {proposal_id}: {reason}")
        return True

    # ========================================================================
    # Proposal Query
    # ========================================================================

    async def get_proposal(self, proposal_id: str) -> Optional[AdaptationProposalRead]:
        """Get a specific proposal."""
        proposal_dict = await self._get_proposal_raw(proposal_id)
        if not proposal_dict:
            return None

        try:
            return AdaptationProposalRead.model_validate(proposal_dict)
        except Exception as e:
            logger.error(f"Error validating proposal: {e}")
            return None

    async def list_proposals(
        self,
        target_scope: Optional[str] = None,
        risk_tier: Optional[RiskTier] = None,
        status: Optional[ApprovalStatus] = None,
        limit: int = 100
    ) -> List[AdaptationProposalRead]:
        """List proposals with filters."""
        try:
            query = self.supabase.table("adaptation_proposals").select("*")

            if target_scope:
                query = query.eq("target_scope", target_scope)
            if risk_tier:
                query = query.eq("risk_tier", risk_tier.value)
            if status:
                query = query.eq("status", status.value)

            query = query.order("created_at", desc=True)
            query = query.limit(limit)

            result = query.execute()

            proposals = []
            for item in result.data or []:
                try:
                    proposals.append(AdaptationProposalRead.model_validate(item))
                except Exception:
                    continue

            return proposals

        except Exception as e:
            logger.error(f"Error listing proposals: {e}")
            return []

    async def get_pending_proposals(self, limit: int = 100) -> List[AdaptationProposalRead]:
        """Get proposals pending review."""
        return await self.list_proposals(
            status=ApprovalStatus.PENDING_REVIEW,
            limit=limit
        )

    async def get_approved_proposals(self, limit: int = 100) -> List[AdaptationProposalRead]:
        """Get proposals approved but not yet applied."""
        return await self.list_proposals(
            status=ApprovalStatus.APPROVED,
            limit=limit
        )

    # ========================================================================
    # Proposal Update
    # ========================================================================

    async def update_proposal(
        self,
        proposal_id: str,
        update: AdaptationProposalUpdate
    ) -> Optional[AdaptationProposalRead]:
        """Update a proposal."""
        try:
            payload = {k: v for k, v in update.model_dump().items() if v is not None}
            payload["updated_at"] = datetime.now().isoformat()

            if update.status == ApprovalStatus.APPROVED:
                payload["reviewed_at"] = datetime.now().isoformat()

            result = self.supabase.table("adaptation_proposals").update(payload).eq("proposal_id", proposal_id).execute()

            if result.data:
                return AdaptationProposalRead.model_validate(result.data[0])

        except Exception as e:
            logger.error(f"Error updating proposal: {e}")

        return None

    # ========================================================================
    # Helpers
    # ========================================================================

    async def _get_proposal_raw(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """Get raw proposal data from database."""
        try:
            query = self.supabase.table("adaptation_proposals").select("*")
            query = query.eq("proposal_id", proposal_id)
            query = query.limit(1)

            result = query.execute()
            return result.data[0] if result.data else None

        except Exception as e:
            logger.error(f"Error fetching proposal: {e}")
            return None

    async def _get_existing_proposals_for_target(
        self,
        target_scope: str,
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """Get existing proposals for policy evaluation."""
        try:
            cutoff = datetime.now() - timedelta(days=days_back)

            query = self.supabase.table("adaptation_proposals").select("*")
            query = query.eq("target_scope", target_scope)
            query = query.gte("created_at", cutoff.isoformat())

            result = query.execute()
            return result.data or []

        except Exception as e:
            logger.error(f"Error fetching existing proposals: {e}")
            return []

    async def _persist_proposal(self, proposal: AdaptationProposalCreate) -> str:
        """Persist a new proposal to database."""
        try:
            payload = proposal.model_dump()
            payload["proposal_id"] = str(uuid.uuid4())
            payload["created_at"] = datetime.now().isoformat()
            payload["updated_at"] = datetime.now().isoformat()

            # Set expiry
            expiry_days = self.config.proposal_expiry_days
            payload["expires_at"] = (datetime.now() + timedelta(days=expiry_days)).isoformat()

            result = self.supabase.table("adaptation_proposals").insert(payload).execute()

            if result.data:
                return result.data[0].get("proposal_id")

        except Exception as e:
            logger.error(f"Error persisting proposal: {e}")

        return ""

    def _generate_candidate_version(self, signal: Dict[str, Any]) -> str:
        """Generate a candidate version identifier."""
        timestamp = datetime.now().strftime("%Y%m%d")
        signal_type = signal.get("signal_type", "unknown")[:10]
        return f"candidate_{timestamp}_{signal_type}"

    def _generate_rollback_instructions(self, proposal: Dict[str, Any]) -> str:
        """Generate rollback instructions for an applied proposal."""
        current_version = proposal.get("current_version", "unknown")
        rollback_plan = proposal.get("rollback_plan", "No rollback plan available")

        return f"Restore to version {current_version}. {rollback_plan}"

    def _generate_change_summary(self, proposal: Dict[str, Any]) -> str:
        """Generate a summary of the change."""
        adaptation_type = proposal.get("adaptation_type", "unknown")
        target_key = proposal.get("target_key", "unknown")
        description = proposal.get("change_description", "")

        return f"{adaptation_type} on {target_key}: {description}"
