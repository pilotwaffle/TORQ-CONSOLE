"""
Insight Approval Workflow - Phase Insight Publishing Milestone 2

Manages approval/rejection/supersession lifecycle transitions for insights.

This module handles:
- Approving candidates for publication
- Rejecting candidates with reasons
- Superseding existing insights
- Lifecycle state transitions
- Transition validation
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from .models import (
    InsightType,
    InsightLifecycleState,
    Insight,
    InsightCreate,
    InsightUpdate,
)

from .persistence import InsightPersistence, InsightRecord
from .validation_service import ValidationResult, PublishingValidator


logger = logging.getLogger(__name__)


# ============================================================================
# Transition Request Models
# ============================================================================

class TransitionRequest(BaseModel):
    """
    Request to transition an insight to a new lifecycle state.
    """
    insight_id: UUID
    from_state: InsightLifecycleState
    to_state: InsightLifecycleState
    requested_by: str = "system"
    reason: Optional[str] = None
    force: bool = False  # Skip validation if True


class TransitionResult(BaseModel):
    """
    Result of a lifecycle transition.
    """
    success: bool
    insight_id: UUID
    from_state: InsightLifecycleState
    to_state: InsightLifecycleState
    insight_record: Optional[InsightRecord] = None

    # Validation
    validation_errors: List[str] = Field(default_factory=list)
    validation_warnings: List[str] = Field(default_factory=list)

    # Messages
    messages: List[str] = Field(default_factory=list)

    # Metadata
    transitioned_at: datetime = Field(default_factory=datetime.now)
    transitioned_by: str


class ApprovalResult(BaseModel):
    """
    Result of approving an insight candidate for publication.
    """
    success: bool
    insight_id: Optional[UUID] = None
    insight_record: Optional[InsightRecord] = None

    # Supersession info
    superseded_insights: List[UUID] = Field(default_factory=list)

    # Messages
    messages: List[str] = Field(default_factory=list)

    # Metadata
    approved_at: datetime = Field(default_factory=datetime.now)
    approved_by: str


class RejectionResult(BaseModel):
    """
    Result of rejecting an insight candidate.
    """
    success: bool
    candidate_id: Optional[str] = None  # May be UUID or string for candidates

    # Rejection details
    rejection_reasons: List[str] = Field(default_factory=list)

    # Messages
    messages: List[str] = Field(default_factory=list)

    # Metadata
    rejected_at: datetime = Field(default_factory=datetime.now)
    rejected_by: str


# ============================================================================
# Approval Workflow Service
# ============================================================================

class ApprovalWorkflowService:
    """
    Manages the approval workflow for insight candidates.

    Handles state transitions, approval, rejection, and supersession.
    """

    def __init__(
        self,
        persistence: InsightPersistence,
        validator: Optional[PublishingValidator] = None,
    ):
        """
        Initialize the workflow service.

        Args:
            persistence: Insight persistence layer
            validator: Publishing validator (optional, for approval validation)
        """
        self.persistence = persistence
        self.validator = validator

    async def approve_candidate(
        self,
        candidate: InsightCreate,
        validation_result: ValidationResult,
        approved_by: str = "system"
    ) -> ApprovalResult:
        """
        Approve an insight candidate for publication.

        Creates the insight record and transitions it to PUBLISHED state.

        Args:
            candidate: The insight candidate to approve
            validation_result: Result from validation (must be passed)
            approved_by: Who is approving

        Returns:
            ApprovalResult with created insight
        """
        if not validation_result.passed:
            return ApprovalResult(
                success=False,
                messages=["Cannot approve candidate that failed validation"],
                approved_by=approved_by
            )

        # Handle supersession if recommended
        superseded_ids = []
        if validation_result.should_supersede:
            superseded_result = await self._supersede_insight(
                validation_result.should_supersede,
                candidate,
                approved_by
            )
            if superseded_result:
                superseded_ids.append(validation_result.should_supersede)

        # Create the insight with PUBLISHED state
        from .models import Insight

        published_insight = Insight(
            insight_type=candidate.insight_type,
            title=candidate.title,
            summary=candidate.summary,
            scope=candidate.scope,
            scope_key=candidate.scope_key,
            domain=candidate.domain,
            tags=candidate.tags,
            content=candidate.content,
            source_references=candidate.source_references,
            quality=candidate.quality,
            lifecycle_state=InsightLifecycleState.PUBLISHED,
            published_at=datetime.now(),
            created_by=approved_by,
        )

        # Persist
        record = await self.persistence.create_insight(candidate)
        # Update to published state
        update = InsightUpdate(lifecycle_state=InsightLifecycleState.PUBLISHED)
        record = await self.persistence.update_insight(record.id, update)

        logger.info(f"Approved insight {record.id}: {candidate.title}")

        return ApprovalResult(
            success=True,
            insight_id=record.id,
            insight_record=record,
            superseded_insights=superseded_ids,
            messages=[f"Insight approved and published as {record.id}"],
            approved_by=approved_by
        )

    async def reject_candidate(
        self,
        candidate: InsightCreate,
        validation_result: ValidationResult,
        rejected_by: str = "system"
    ) -> RejectionResult:
        """
        Reject an insight candidate.

        Logs the rejection with reasons for future review.

        Args:
            candidate: The candidate to reject
            validation_result: Validation result with rejection reasons
            rejected_by: Who is rejecting

        Returns:
            RejectionResult
        """
        # Collect rejection reasons
        reasons = []
        if validation_result.validation_errors:
            reasons.extend(validation_result.validation_errors)
        if validation_result.provenance_issues:
            reasons.extend(validation_result.provenance_issues)
        if validation_result.freshness_issues:
            reasons.extend(validation_result.freshness_issues)

        # Serialize quality gate results
        quality_results = [
            {
                "gate_name": gr.gate_name,
                "passed": gr.passed,
                "score": gr.score,
                "threshold": gr.threshold,
                "reason": gr.reason,
            }
            for gr in validation_result.quality_gate_results
        ]

        # Log rejection
        rejection_record = await self.persistence.log_rejection(
            candidate,
            reasons,
            quality_results
        )

        logger.info(f"Rejected candidate: {candidate.title} - {', '.join(reasons[:3])}")

        return RejectionResult(
            success=True,
            candidate_id=str(uuid4()),  # Placeholder ID
            rejection_reasons=reasons,
            messages=[f"Candidate rejected: {', '.join(reasons)}"],
            rejected_by=rejected_by
        )

    async def transition_insight(
        self,
        request: TransitionRequest
    ) -> TransitionResult:
        """
        Transition an insight to a new lifecycle state.

        Args:
            request: Transition request with from/to states

        Returns:
            TransitionResult with updated insight
        """
        # Get current insight
        record = await self.persistence.get_insight(request.insight_id)
        if not record:
            return TransitionResult(
                success=False,
                insight_id=request.insight_id,
                from_state=request.from_state,
                to_state=request.to_state,
                validation_errors=["Insight not found"],
                transitioned_by=request.requested_by
            )

        # Validate transition
        errors = self._validate_transition(request, record)
        if errors and not request.force:
            return TransitionResult(
                success=False,
                insight_id=request.insight_id,
                from_state=request.from_state,
                to_state=request.to_state,
                insight_record=record,
                validation_errors=errors,
                transitioned_by=request.requested_by
            )

        # Perform transition
        update = InsightUpdate(
            lifecycle_state=request.to_state,
            expires_at=None  # Clear expiration on certain transitions
        )

        # Set published_at if transitioning to PUBLISHED
        if request.to_state == InsightLifecycleState.PUBLISHED:
            # Note: In real implementation, we'd add this to InsightUpdate
            pass

        updated_record = await self.persistence.update_insight(
            request.insight_id,
            update
        )

        # Handle supersession link if applicable
        if request.to_state == InsightLifecycleState.SUPERSEDED:
            if request.reason and "superseded_by" in request.reason:
                # Parse superseding ID from reason
                try:
                    superseded_by_id = UUID(request.reason.split("superseded_by: ")[1])
                    # Update the original insight to record supersession
                    # (In real implementation, this would be a separate field)
                    pass
                except (IndexError, ValueError):
                    pass

        logger.info(
            f"Transitioned insight {request.insight_id}: "
            f"{request.from_state.value} → {request.to_state.value}"
        )

        return TransitionResult(
            success=True,
            insight_id=request.insight_id,
            from_state=request.from_state,
            to_state=request.to_state,
            insight_record=updated_record,
            messages=[f"Transitioned to {request.to_state.value}"],
            transitioned_by=request.requested_by
        )

    async def _supersede_insight(
        self,
        old_insight_id: UUID,
        new_candidate: InsightCreate,
        superseded_by: str
    ) -> bool:
        """
        Mark an existing insight as superseded by a new one.

        Args:
            old_insight_id: ID of insight to supersede
            new_candidate: The new candidate that supersedes it
            superseded_by: Who is performing the supersession

        Returns:
            True if successful
        """
        # Transition old insight to SUPERSEDED
        request = TransitionRequest(
            insight_id=old_insight_id,
            from_state=InsightLifecycleState.PUBLISHED,
            to_state=InsightLifecycleState.SUPERSEDED,
            reason=f"superseded_by: {new_candidate.title}",
            requested_by=superseded_by
        )

        result = await self.transition_insight(request)
        return result.success

    def _validate_transition(
        self,
        request: TransitionRequest,
        record: InsightRecord
    ) -> List[str]:
        """
        Validate that a transition is allowed.

        Args:
            request: Transition request
            record: Current insight record

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check current state matches expected
        if record.lifecycle_state != request.from_state:
            errors.append(
                f"Current state is {record.lifecycle_state.value}, "
                f"expected {request.from_state.value}"
            )

        # Check if transition is valid per lifecycle rules
        from .publishing_rules import is_transition_valid, LIFECYCLE_TRANSITIONS

        if not is_transition_valid(request.from_state, request.to_state):
            errors.append(
                f"Invalid transition: {request.from_state.value} → {request.to_state.value}"
            )

        # Check if transition requires approval
        for transition in LIFECYCLE_TRANSITIONS:
            if (transition.from_state == request.from_state and
                transition.to_state == request.to_state):
                if transition.requires_approval:
                    # In real implementation, check for actual approval
                    # For now, system requests are auto-approved
                    if request.requested_by == "system":
                        errors.append(
                            f"Transition {request.from_state.value} → {request.to_state.value} "
                            "requires manual approval"
                        )

        return errors


# ============================================================================
# Batch Operations
# ============================================================================

async def approve_batch(
    candidates_with_validation: List[tuple[InsightCreate, ValidationResult]],
    persistence: InsightPersistence,
    approved_by: str = "system"
) -> List[ApprovalResult]:
    """
    Batch approve multiple candidates.

    Args:
        candidates_with_validation: List of (candidate, validation) tuples
        persistence: Insight persistence layer
        approved_by: Who is approving

    Returns:
        List of approval results
    """
    workflow = ApprovalWorkflowService(persistence)
    results = []

    for candidate, validation in candidates_with_validation:
        if validation.passed:
            result = await workflow.approve_candidate(
                candidate,
                validation,
                approved_by
            )
            results.append(result)
        else:
            results.append(
                ApprovalResult(
                    success=False,
                    messages=["Candidate failed validation, cannot approve"],
                    approved_by=approved_by
                )
            )

    return results


async def reject_batch(
    candidates_with_validation: List[tuple[InsightCreate, ValidationResult]],
    persistence: InsightPersistence,
    rejected_by: str = "system"
) -> List[RejectionResult]:
    """
    Batch reject multiple candidates.

    Args:
        candidates_with_validation: List of (candidate, validation) tuples
        persistence: Insight persistence layer
        rejected_by: Who is rejecting

    Returns:
        List of rejection results
    """
    workflow = ApprovalWorkflowService(persistence)
    results = []

    for candidate, validation in candidates_with_validation:
        result = await workflow.reject_candidate(
            candidate,
            validation,
            rejected_by
        )
        results.append(result)

    return results


# ============================================================================
# Helper Functions
# ============================================================================

def get_approval_workflow(
    persistence: InsightPersistence,
    validator: Optional[PublishingValidator] = None
) -> ApprovalWorkflowService:
    """Get an approval workflow service instance."""
    return ApprovalWorkflowService(persistence, validator)
