"""
Agent Teams - View Models for UI

Phase 5.2B: Observability + UI

Thin presentation layer for exposing team execution data to the frontend.
DOES NOT modify runtime behavior - read-only transformation for display.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .models import (
    TeamExecution,
    TeamMessage,
    TeamExecutionResult,
    TeamExecutionStatus,
    TeamRole,
    MessageType,
    ValidatorStatus,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Team Execution Card (Control Surface)
# ============================================================================

class TeamExecutionCard(BaseModel):
    """Team execution summary for control surface card."""

    execution_id: str = Field(..., description="Execution identifier")
    team_id: str = Field(..., description="Team identifier")
    team_name: str = Field(..., description="Team display name")
    pattern: str = Field(..., description="Collaboration pattern")
    rounds_total: int = Field(..., description="Total rounds configured")
    rounds_completed: int = Field(..., description="Rounds completed")
    status: str = Field(..., description="Current status")
    confidence: float = Field(..., description="Final confidence score", ge=0.0, le=1.0)
    started_at: Optional[str] = Field(None, description="Start timestamp")
    completed_at: Optional[str] = Field(None, description="Completion timestamp")

    @classmethod
    def from_execution(cls, execution: TeamExecution, team_name: str = "") -> "TeamExecutionCard":
        """Create from TeamExecution model."""
        return cls(
            execution_id=str(execution.id),
            team_id=str(execution.team_id),
            team_name=team_name,
            pattern="deliberative_review",  # MVP has single pattern
            rounds_total=execution.max_rounds,
            rounds_completed=execution.current_round,
            status=execution.status.value,
            confidence=execution.final_confidence or 0.0,
            started_at=execution.started_at.isoformat() if execution.started_at else None,
            completed_at=execution.completed_at.isoformat() if execution.completed_at else None,
        )


# ============================================================================
# Role Roster Item
# ============================================================================

class RoleRosterItem(BaseModel):
    """Individual role status for roster display."""

    role: str = Field(..., description="Role name")
    display_name: str = Field(..., description="Display name")
    status: str = Field(..., description="Current state: pending, active, completed")
    last_action: Optional[str] = Field(None, description="Last action taken")
    last_action_round: Optional[int] = Field(None, description="Round of last action")
    confidence: Optional[float] = Field(None, description="Last confidence score", ge=0.0, le=1.0)

    @classmethod
    def create(cls, role: TeamRole, messages: List[TeamMessage]) -> "RoleRosterItem":
        """Create role roster item from messages."""
        # Filter messages for this role
        role_messages = [m for m in messages if m.sender_role == role]

        # Determine status
        status = "pending"
        last_action = None
        last_round = None
        confidence = None

        if role_messages:
            status = "completed"
            last_msg = role_messages[-1]
            last_round = last_msg.round_number
            confidence = last_msg.confidence

            # Generate action description
            if last_msg.message_type == MessageType.ROLE_TO_ROLE:
                last_action = f"Sent to {last_msg.receiver_role.value}"
            elif last_msg.message_type == MessageType.VALIDATION_PASS:
                last_action = "Validation passed"
            elif last_msg.message_type == MessageType.VALIDATION_BLOCK:
                last_action = "Validation blocked"

        display_names = {
            TeamRole.LEAD: "Lead",
            TeamRole.RESEARCHER: "Researcher",
            TeamRole.CRITIC: "Critic",
            TeamRole.VALIDATOR: "Validator",
        }

        return cls(
            role=role.value,
            display_name=display_names.get(role, role.value),
            status=status,
            last_action=last_action,
            last_action_round=last_round,
            confidence=confidence,
        )


# ============================================================================
# Round Timeline Event
# ============================================================================

class RoundTimelineEvent(BaseModel):
    """Single event in round timeline."""

    id: str = Field(..., description="Event identifier")
    round_number: int = Field(..., description="Round number")
    event_type: str = Field(..., description="Event type")
    sender_role: Optional[str] = Field(None, description="Role that sent this event")
    receiver_role: Optional[str] = Field(None, description="Role that received this event")
    content_preview: Optional[str] = Field(None, description="Content preview (truncated)")
    confidence: Optional[float] = Field(None, description="Confidence if applicable")
    timestamp: str = Field(..., description="Event timestamp")

    @classmethod
    def from_message(cls, message: TeamMessage) -> "RoundTimelineEvent":
        """Create from TeamMessage model."""
        # Truncate content for preview
        content_preview = None
        if message.text_content:
            content_preview = message.text_content[:100] + "..." if len(message.text_content) > 100 else message.text_content
        elif message.content:
            # Extract text from content dict
            content_preview = str(message.content)[:100] + "..." if len(str(message.content)) > 100 else str(message.content)

        return cls(
            id=str(message.id),
            round_number=message.round_number,
            event_type=message.message_type.value,
            sender_role=message.sender_role.value if message.sender_role else None,
            receiver_role=message.receiver_role.value if message.receiver_role else None,
            content_preview=content_preview,
            confidence=message.confidence,
            timestamp=message.created_at.isoformat() if message.created_at else datetime.utcnow().isoformat(),
        )


# ============================================================================
# Decision Summary
# ============================================================================

class DecisionSummary(BaseModel):
    """Final decision summary for display."""

    execution_id: str = Field(..., description="Execution identifier")
    decision_policy: str = Field(..., description="Policy used for decision")
    final_confidence: float = Field(..., description="Final confidence score", ge=0.0, le=1.0)
    validator_status: str = Field(..., description="Final validator status")
    validator_notes: Optional[str] = Field(None, description="Validator notes")
    has_dissent: bool = Field(..., description="Whether dissent occurred")
    dissenting_roles: List[str] = Field(default_factory=list, description="Roles that dissented")
    revision_count: int = Field(..., description="Number of revisions")
    escalation_count: int = Field(..., description="Number of escalations")
    confidence_breakdown: Dict[str, float] = Field(default_factory=dict, description="Per-role confidence")

    @classmethod
    def from_result(cls, result: TeamExecutionResult, messages: List[TeamMessage]) -> "DecisionSummary":
        """Create from TeamExecutionResult and messages."""
        # Build confidence breakdown
        confidence_breakdown = {}
        for msg in messages:
            if msg.confidence and msg.confidence > 0:
                role = msg.sender_role.value
                if role not in confidence_breakdown:
                    confidence_breakdown[role] = msg.confidence
                # Average if multiple
                else:
                    confidence_breakdown[role] = (confidence_breakdown[role] + msg.confidence) / 2

        # Get dissenting roles
        dissenting_roles = []
        if result.dissent_summary:
            dissenting_roles = result.dissent_summary.get("dissenting_roles", [])

        return cls(
            execution_id=str(result.team_execution_id),
            decision_policy=result.decision_policy,
            final_confidence=result.confidence_score,
            validator_status=result.validator_status.value,
            validator_notes=result.validator_notes,
            has_dissent=result.dissent_summary.get("has_dissent", False) if result.dissent_summary else False,
            dissenting_roles=dissenting_roles,
            revision_count=result.revision_count,
            escalation_count=result.escalation_count,
            confidence_breakdown=confidence_breakdown,
        )


# ============================================================================
# Historical Execution View
# ============================================================================

class HistoricalExecutionView(BaseModel):
    """Complete view of a historical team execution."""

    card: TeamExecutionCard = Field(..., description="Execution summary card")
    role_roster: List[RoleRosterItem] = Field(..., description="Role roster")
    timeline: List[RoundTimelineEvent] = Field(..., description="Full event timeline")
    decision: DecisionSummary = Field(..., description="Final decision summary")

    @classmethod
    async def create(
        cls,
        execution: TeamExecution,
        messages: List[TeamMessage],
        result: Optional[TeamExecutionResult],
        team_name: str = "",
    ) -> "HistoricalExecutionView":
        """Create complete historical view."""
        # Build card
        card = TeamExecutionCard.from_execution(execution, team_name)

        # Build role roster
        all_roles = [TeamRole.LEAD, TeamRole.RESEARCHER, TeamRole.CRITIC, TeamRole.VALIDATOR]
        role_roster = [
            RoleRosterItem.create(role, messages)
            for role in all_roles
        ]

        # Build timeline
        timeline = [
            RoundTimelineEvent.from_message(msg)
            for msg in messages
        ]
        timeline.sort(key=lambda e: e.timestamp)

        # Build decision
        if result:
            decision = DecisionSummary.from_result(result, messages)
        else:
            # Fallback decision from execution data
            decision = DecisionSummary(
                execution_id=str(execution.id),
                decision_policy="weighted_consensus",
                final_confidence=execution.final_confidence or 0.0,
                validator_status="pending",
                has_dissent=False,
                revision_count=0,
                escalation_count=0,
            )

        return cls(
            card=card,
            role_roster=role_roster,
            timeline=timeline,
            decision=decision,
        )


# ============================================================================
# Per-Role Confidence Display
# ============================================================================

class PerRoleConfidence(BaseModel):
    """Per-role confidence display component."""

    role: str = Field(..., description="Role name")
    display_name: str = Field(..., description="Display name")
    confidence: float = Field(..., description="Confidence score", ge=0.0, le=1.0)
    contribution_count: int = Field(..., description="Number of contributions")

    @classmethod
    def from_messages(cls, role: TeamRole, messages: List[TeamMessage]) -> "PerRoleConfidence":
        """Calculate per-role confidence from messages."""
        role_messages = [m for m in messages if m.sender_role == role and m.confidence]

        # Average confidence
        confidence = 0.0
        if role_messages:
            confidence = sum(m.confidence for m in role_messages) / len(role_messages)

        display_names = {
            TeamRole.LEAD: "Lead",
            TeamRole.RESEARCHER: "Researcher",
            TeamRole.CRITIC: "Critic",
            TeamRole.VALIDATOR: "Validator",
        }

        return cls(
            role=role.value,
            display_name=display_names.get(role, role.value),
            confidence=round(confidence, 3),
            contribution_count=len(role_messages),
        )


# ============================================================================
# Team Execution Detail Response
# ============================================================================

class TeamExecutionDetailResponse(BaseModel):
    """Complete team execution detail for UI."""

    execution: TeamExecutionCard
    roles: List[RoleRosterItem]
    timeline: List[RoundTimelineEvent]
    decision: DecisionSummary
    confidence_breakdown: List[PerRoleConfidence]
