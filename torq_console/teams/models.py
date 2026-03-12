"""
Agent Teams - Data Models

Phase 5.2: Agent Teams as a governed execution primitive.

This module defines the core data models for agent team execution,
including team definitions, execution context, roles, and decisions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ============================================================================
# Enums
# ============================================================================

class TeamPattern(str, Enum):
    """Collaboration patterns for agent teams."""
    DELIBERATIVE_REVIEW = "deliberative_review"
    PARALLEL_SYNTHESIS = "parallel_synthesis"
    SUPERVISOR_WORKERS = "supervisor_workers"


class DecisionPolicy(str, Enum):
    """Decision policies for team consensus."""
    WEIGHTED_CONSENSUS = "weighted_consensus"
    UNANIMOUS = "unanimous"
    MAJORITY = "majority"
    VALIDATOR_GATE = "validator_gate"


class TeamExecutionStatus(str, Enum):
    """Status of a team execution."""
    CREATED = "created"
    INITIALIZED = "initialized"
    RUNNING = "running"
    AWAITING_VALIDATION = "awaiting_validation"
    REVISING = "revising"
    APPROVED = "approved"
    BLOCKED = "blocked"
    FAILED = "failed"
    COMPLETED = "completed"


class DecisionOutcome(str, Enum):
    """Possible outcomes of team decision."""
    APPROVED = "approved"
    APPROVED_WITH_DISSENT = "approved_with_dissent"
    REVISION_REQUIRED = "revision_required"
    BLOCKED = "blocked"
    ESCALATED = "escalated"
    FAILED = "failed"


class TeamRole(str, Enum):
    """Standard role names in agent teams."""
    LEAD = "lead"
    RESEARCHER = "researcher"
    STRATEGIST = "strategist"
    BUILDER = "builder"
    CRITIC = "critic"
    REVIEWER = "reviewer"
    VALIDATOR = "validator"


class MessageType(str, Enum):
    """Types of messages within team collaboration."""
    ROLE_TO_ROLE = "role_to_role"
    CRITIQUE = "critique"
    VALIDATION_BLOCK = "validation_block"
    VALIDATION_PASS = "validation_pass"
    ROUND_SUMMARY = "round_summary"
    SYNTHESIS = "synthesis"
    ESCALATION = "escalation"
    REVISION_REQUEST = "revision_request"


class ValidatorStatus(str, Enum):
    """Status of validator review."""
    PENDING = "pending"
    APPROVED = "approved"
    BLOCKED = "blocked"
    ESCALATED = "escalated"


# ============================================================================
# Team Definition Models
# ============================================================================

@dataclass
class TeamMemberRole:
    """Defines a role within a team."""
    role_name: TeamRole
    agent_type: str
    confidence_weight: float = 1.0
    execution_order: int = 0
    is_required: bool = True
    capabilities: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    agent_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TeamDefinition:
    """Defines a reusable agent team."""
    id: UUID = field(default_factory=uuid4)
    team_id: str = ""
    name: str = ""
    description: str = ""
    pattern: TeamPattern = TeamPattern.DELIBERATIVE_REVIEW
    decision_policy: DecisionPolicy = DecisionPolicy.WEIGHTED_CONSENSUS
    max_rounds: int = 3
    output_schema: Optional[str] = None
    escalation_policy: str = "retry_with_fallback"
    is_active: bool = True
    members: List[TeamMemberRole] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


# ============================================================================
# Team Execution Models
# ============================================================================

@dataclass
class TeamExecutionContext:
    """Shared runtime context for team execution."""
    mission_id: UUID
    node_id: UUID
    execution_id: str
    workspace_id: Optional[str] = None
    team_id: Optional[UUID] = None
    objective: str = ""
    constraints: List[str] = field(default_factory=list)
    prior_outputs: Dict[str, Any] = field(default_factory=dict)
    policy_context: Dict[str, Any] = field(default_factory=dict)
    shared_state: Dict[str, Any] = field(default_factory=dict)
    max_rounds: int = 3
    current_round: int = 0


@dataclass
class TeamMessage:
    """A message within team collaboration."""
    id: UUID = field(default_factory=uuid4)
    team_execution_id: UUID = field(default_factory=uuid4)
    round_number: int = 1
    sender_role: TeamRole = TeamRole.LEAD
    receiver_role: TeamRole = TeamRole.LEAD
    message_type: MessageType = MessageType.ROLE_TO_ROLE
    content: Dict[str, Any] = field(default_factory=dict)
    text_content: str = ""
    confidence: float = 0.0
    token_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TeamExecutionResult:
    """Final result of a team execution."""
    id: UUID = field(default_factory=uuid4)
    team_execution_id: UUID = field(default_factory=uuid4)
    final_output: Dict[str, Any] = field(default_factory=dict)
    text_output: str = ""
    decision_policy: DecisionPolicy = DecisionPolicy.WEIGHTED_CONSENSUS
    approval_summary: Dict[str, Any] = field(default_factory=dict)
    dissent_summary: Dict[str, Any] = field(default_factory=dict)
    validator_status: ValidatorStatus = ValidatorStatus.PENDING
    validator_notes: str = ""
    confidence_score: float = 0.0
    confidence_breakdown: Dict[str, float] = field(default_factory=dict)
    revision_count: int = 0
    escalation_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TeamExecution:
    """A complete team execution record."""
    id: UUID = field(default_factory=uuid4)
    mission_id: UUID = field(default_factory=uuid4)
    node_id: UUID = field(default_factory=uuid4)
    execution_id: str = ""
    team_id: UUID = field(default_factory=uuid4)
    workspace_id: Optional[str] = None
    status: TeamExecutionStatus = TeamExecutionStatus.CREATED
    current_round: int = 0
    max_rounds: int = 3
    final_confidence: Optional[float] = None
    decision_outcome: Optional[DecisionOutcome] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_duration_seconds: Optional[int] = None
    objective: str = ""
    constraints: List[str] = field(default_factory=list)
    telemetry: Dict[str, Any] = field(default_factory=dict)
    messages: List[TeamMessage] = field(default_factory=list)
    result: Optional[TeamExecutionResult] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


# ============================================================================
# API Request/Response Models
# ============================================================================

class TeamMemberResponse(BaseModel):
    """Team member in API response."""
    role_name: str
    agent_type: str
    confidence_weight: float
    execution_order: int
    is_required: bool


class TeamDefinitionResponse(BaseModel):
    """Team definition in API response."""
    id: str
    team_id: str
    name: str
    description: str
    pattern: str
    decision_policy: str
    max_rounds: int
    members: List[TeamMemberResponse]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TeamExecutionResponse(BaseModel):
    """Team execution in API response."""
    id: str
    mission_id: str
    node_id: str
    execution_id: str
    team_id: str
    status: str
    current_round: int
    max_rounds: int
    final_confidence: Optional[float]
    decision_outcome: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    message_count: int
    duration_seconds: Optional[float]


class TeamMessageResponse(BaseModel):
    """Team message in API response."""
    id: str
    team_execution_id: str
    round_number: int
    sender_role: str
    receiver_role: str
    message_type: str
    content: Dict[str, Any]
    text_content: str
    confidence: Optional[float]
    created_at: datetime


class TeamDecisionResponse(BaseModel):
    """Team decision in API response."""
    id: str
    team_execution_id: str
    final_output: Dict[str, Any]
    text_output: str
    decision_policy: str
    approval_summary: Dict[str, Any]
    dissent_summary: Dict[str, Any]
    validator_status: str
    validator_notes: str
    confidence_score: float
    confidence_breakdown: Dict[str, float]
    revision_count: int
    escalation_count: int
    created_at: datetime


class CreateTeamRequest(BaseModel):
    """Request to create a new team."""
    team_id: str
    name: str
    description: str = ""
    pattern: TeamPattern = TeamPattern.DELIBERATIVE_REVIEW
    decision_policy: DecisionPolicy = DecisionPolicy.WEIGHTED_CONSENSUS
    max_rounds: int = 3
    members: List[TeamMemberResponse]


class ExecuteTeamNodeRequest(BaseModel):
    """Request to execute a node as a team."""
    team_id: str
    objective: str
    constraints: List[str] = Field(default_factory=list)
    prior_outputs: Dict[str, Any] = Field(default_factory=dict)
    policy_context: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Role Task Models
# ============================================================================

@dataclass
class RoleTask:
    """A task assigned to a specific role."""
    id: UUID = field(default_factory=uuid4)
    team_execution_id: UUID = field(default_factory=uuid4)
    role: TeamRole = TeamRole.LEAD
    objective: str = ""
    input_data: Dict[str, Any] = field(default_factory=dict)
    expected_output_format: str = ""
    status: TeamExecutionStatus = TeamExecutionStatus.CREATED
    output: Optional[Dict[str, Any]] = None
    confidence: float = 0.0
    error_message: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class RoleTaskState(str, Enum):
    """State of a role task."""
    IDLE = "idle"
    ASSIGNED = "assigned"
    WORKING = "working"
    SUBMITTED = "submitted"
    CHALLENGED = "challenged"
    APPROVED = "approved"
    REWORK_REQUIRED = "rework_required"
    FAILED = "failed"


# ============================================================================
# Decision Breakdown
# ============================================================================

@dataclass
class ConfidenceBreakdown:
    """Breakdown of confidence by role."""
    lead: float = 0.0
    researcher: float = 0.0
    strategist: float = 0.0
    builder: float = 0.0
    critic: float = 0.0
    reviewer: float = 0.0
    validator: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary, excluding zero values."""
        return {
            k: v for k, v in [
                ("lead", self.lead),
                ("researcher", self.researcher),
                ("strategist", self.strategist),
                ("builder", self.builder),
                ("critic", self.critic),
                ("reviewer", self.reviewer),
                ("validator", self.validator),
            ] if v > 0
        }


@dataclass
class ApprovalSummary:
    """Summary of approvals within the team."""
    total_votes: int = 0
    approve_votes: int = 0
    dissent_votes: int = 0
    abstain_votes: int = 0
    voters: List[str] = field(default_factory=list)


@dataclass
class DissentSummary:
    """Summary of dissent within the team."""
    has_dissent: bool = False
    dissenting_roles: List[str] = field(default_factory=list)
    dissent_reasons: List[str] = field(default_factory=list)
    severity: str = "low"  # low, medium, high
