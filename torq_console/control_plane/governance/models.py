"""
TORQ Control Plane - Governance Models

L7-M1: Data models for governance actions and approvals.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from enum import Enum

from pydantic import BaseModel, Field


# ============================================================================
# Governance Action Models
# ============================================================================

class ActionStatus(str, Enum):
    """Status of a governance action."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class ActionType(str, Enum):
    """Types of governance actions."""
    PROMOTE = "promote"
    BLOCK = "block"
    DEMOTE = "demote"
    FORCE_TRANSITION = "force_transition"
    OVERRIDE_POLICY = "override_policy"
    VALIDATE_PATTERN = "validate_pattern"
    START_MISSION = "start_mission"
    STOP_MISSION = "stop_mission"


class GovernanceActionRequest(BaseModel):
    """
    A request for a governance action.
    """
    id: UUID = Field(default_factory=uuid4)
    action_type: ActionType
    target_type: str  # candidate, pattern, mission, etc.
    target_id: str
    title: str
    description: Optional[str] = None

    # Request details
    parameters: Dict[str, Any] = Field(default_factory=dict)
    requested_by: str
    requested_at: datetime = Field(default_factory=datetime.now)

    # Approval workflow
    requires_approval: bool = True
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    # Execution
    status: ActionStatus = ActionStatus.PENDING
    executed_at: Optional[datetime] = None
    execution_result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    # Priority
    priority: str = "normal"  # low, normal, high, urgent
    due_at: Optional[datetime] = None

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class GovernanceActionQueue(BaseModel):
    """
    Queue of pending governance actions.
    """
    queue_id: str = "default"
    actions: List[GovernanceActionRequest] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.now)

    # Queue settings
    auto_approve_threshold: Optional[str] = None  # Actions below this level auto-approve
    require_quorum_for: List[str] = Field(default_factory=lambda: ["force_transition", "override_policy"])

    def get_pending_actions(self) -> List[GovernanceActionRequest]:
        """Get all pending actions sorted by priority."""
        pending = [a for a in self.actions if a.status == ActionStatus.PENDING]
        priority_order = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
        pending.sort(key=lambda a: priority_order.get(a.priority, 2))
        return pending

    def get_actions_by_status(self, status: ActionStatus) -> List[GovernanceActionRequest]:
        """Get actions by status."""
        return [a for a in self.actions if a.status == status]

    def add_action(self, action: GovernanceActionRequest) -> bool:
        """Add an action to the queue."""
        self.actions.append(action)
        self.last_updated = datetime.now()
        return True

    def get_action(self, action_id: UUID) -> Optional[GovernanceActionRequest]:
        """Get an action by ID."""
        for action in self.actions:
            if action.id == action_id:
                return action
        return None


class GovernanceOverride(BaseModel):
    """
    Record of a governance override action.
    """
    id: UUID = Field(default_factory=uuid4)
    target_type: str
    target_id: str
    original_decision: str
    override_decision: str
    override_reason: str
    overridden_by: str
    overridden_at: datetime = Field(default_factory=datetime.now)

    # Review
    reviewed: bool = False
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None

    # Impact tracking
    impact_assessment: Optional[str] = None
    resolved: bool = False

    class Config:
        use_enum_values = True


class ApprovalPolicy(BaseModel):
    """
    Policy for approving governance actions.
    """
    id: str
    name: str
    description: Optional[str] = None

    # Approval rules
    action_types: List[str] = Field(default_factory=list)
    auto_approve: bool = False
    required_approvers: int = 1
    approver_roles: List[str] = Field(default_factory=list)

    # Conditions
    max_value_threshold: Optional[float] = None
    require_quorum_for: List[str] = Field(default_factory=list)

    # Time limits
    approval_timeout_hours: int = 24

    class Config:
        use_enum_values = True


# ============================================================================
# Readiness Governance Models
# ============================================================================

class PromotionRequest(BaseModel):
    """
    Request to promote a candidate to ready.
    """
    id: UUID = Field(default_factory=uuid4)
    candidate_id: UUID
    candidate_type: str
    candidate_title: str

    # Current state
    current_state: str
    current_score: float

    # Promotion details
    requested_state: str = "ready"
    confidence_score: float
    supporting_evidence: List[str] = Field(default_factory=list)

    # Request info
    requested_by: str
    requested_at: datetime = Field(default_factory=datetime.now)

    # Approval
    requires_approval: bool = True
    approved: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

    # Execution
    executed: bool = False
    execution_result: Optional[Dict[str, Any]] = None

    class Config:
        use_enum_values = True


class ReadinessGovernanceView(BaseModel):
    """
    Aggregated view of readiness governance status.
    """
    # Promotion queue
    pending_promotions: List[PromotionRequest] = Field(default_factory=list)
    recent_promotions: List[PromotionRequest] = Field(default_factory=list)

    # Override history
    recent_overrides: List[GovernanceOverride] = Field(default_factory=list)

    # Statistics
    total_candidates: int = 0
    ready_candidates: int = 0
    blocked_candidates: int = 0
    pending_actions: int = 0

    # Policy status
    active_policies: List[str] = Field(default_factory=list)
    quorum_required: bool = False

    last_updated: datetime = Field(default_factory=datetime.now)

    class Config:
        use_enum_values = True


# ============================================================================
# Helper Functions
# ============================================================================

def create_promotion_request(
    candidate_id: UUID,
    candidate_type: str,
    candidate_title: str,
    current_state: str,
    current_score: float,
    confidence_score: float,
    requested_by: str,
    supporting_evidence: Optional[List[str]] = None,
) -> PromotionRequest:
    """
    Create a new promotion request.

    Args:
        candidate_id: ID of candidate
        candidate_type: Type of candidate
        candidate_title: Title of candidate
        current_state: Current readiness state
        current_score: Current readiness score
        confidence_score: Confidence in promotion
        requested_by: User requesting promotion
        supporting_evidence: Optional evidence supporting promotion

    Returns:
        PromotionRequest
    """
    return PromotionRequest(
        candidate_id=candidate_id,
        candidate_type=candidate_type,
        candidate_title=candidate_title,
        current_state=current_state,
        current_score=current_score,
        confidence_score=confidence_score,
        supporting_evidence=supporting_evidence or [],
        requested_by=requested_by,
    )
