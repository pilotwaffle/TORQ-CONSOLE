"""TORQ Layer 14 - Governance Data Models

This module defines the core data structures for constitutional governance,
authority enforcement, and legitimacy evaluation.
"""

from datetime import datetime
from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def datetime_utcnow() -> datetime:
    """Get current UTC datetime.

    This function exists for compatibility and testing purposes.
    """
    return datetime.utcnow()


# =============================================================================
# ENUMERATIONS
# =============================================================================


class AuthorityLevel(str, Enum):
    """Authority level for agents and decisions.

    Defines the scope of authority that can be granted to agents
    within the TORQ system.
    """

    NONE = "none"  # No authority (observer only)
    READ = "read"  # Read-only access to system state
    PROPOSE = "propose"  # Can propose actions/missions
    ADVISE = "advise"  # Can provide recommendations
    EXECUTE = "execute"  # Can execute approved decisions
    APPROVE = "approve"  # Can approve proposals
    GOVERN = "govern"  # Can modify governance rules
    ROOT = "root"  # Full system authority (use sparingly)


class RuleType(str, Enum):
    """Types of constitutional rules.

    Defines the categories of rules that can be enforced
    by the constitutional framework.
    """

    SELF_APPROVAL = "self_approval"  # Agents cannot approve their own proposals
    PLURALITY = "plurality"  # Requires diversity in decision-making
    AUTHORITY_BOUNDARY = "authority_boundary"  # Agents must stay within authority
    BUDGET_LIMIT = "budget_limit"  # Cannot exceed allocated budget
    SEPARATION_OF_POWERS = "separation_of_powers"  # Distinct roles for planning/execution
    TRANSPARENCY = "transparency"  # Decisions must be logged and explainable
    NON_CONTRAVENTION = "non_contradiction"  # Rules cannot contradict each other
    AUDITABILITY = "auditability"  # All decisions must be auditable
    HUMAN_OVERRIDE = "human_override"  # Critical decisions require human approval


# =============================================================================
# CORE GOVERNANCE MODELS
# =============================================================================


class GovernanceViolation(BaseModel):
    """A constitutional rule violation.

    Represents a specific violation of constitutional rules
    detected during governance evaluation.
    """

    violation_id: str = Field(description="Unique violation identifier")
    rule_type: RuleType = Field(description="Type of rule violated")
    violated_rule_id: str = Field(description="ID of the specific rule violated")
    severity: Literal["low", "medium", "high", "critical"] = Field(
        default="medium", description="Severity of the violation"
    )
    description: str = Field(description="Human-readable violation description")
    violating_agent_id: str | None = Field(
        default=None, description="Agent that caused the violation"
    )
    detected_at: datetime = Field(default_factory=datetime_utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class GovernanceDecisionPacket(BaseModel):
    """A decision packet requiring governance evaluation.

    Input to Layer 14 governance from Layer 13 economic prioritization.
    Contains the proposed action, economic evaluation, and metadata
    for legitimacy assessment.
    """

    # Identity
    decision_id: str = Field(description="Unique decision identifier")
    proposal_id: str | None = Field(
        default=None, description="Associated mission/proposal ID"
    )
    proposing_agent_id: str = Field(description="Agent proposing this decision")

    # Economic Context (from Layer 13)
    economic_priority_score: float = Field(
        ge=0.0, description="Priority score from Layer 13"
    )
    estimated_cost: float = Field(gt=0, description="Estimated cost of execution")
    budget_remaining: float = Field(ge=0, description="Remaining budget before execution")

    # Action Details
    action_type: str = Field(description="Type of action being proposed")
    action_description: str = Field(description="Description of the proposed action")
    target_resources: list[str] = Field(
        default_factory=list, description="Resources this action will use"
    )

    # Approval Chain
    approving_agent_id: str | None = Field(
        default=None, description="Agent approving this decision"
    )
    approval_chain: list[str] = Field(
        default_factory=list,
        description="Chain of agent IDs that approved this decision",
    )

    # Governance Flags
    requires_human_approval: bool = Field(
        default=False, description="Whether this requires human approval"
    )
    is_governance_change: bool = Field(
        default=False, description="Whether this changes governance rules"
    )
    is_budget_change: bool = Field(
        default=False, description="Whether this changes budget allocation"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime_utcnow)
    governance_context: dict = Field(
        default_factory=dict, description="Additional governance context"
    )


class GovernanceResult(BaseModel):
    """Result of governance evaluation.

    Output from Layer 14 containing legitimacy assessment,
    rule compliance, and execution authorization.
    """

    # Identity
    decision_id: str = Field(description="Associated decision ID")
    evaluated_at: datetime = Field(default_factory=datetime_utcnow)

    # Legitimacy Assessment
    legitimacy_score: float = Field(
        ge=0.0, le=1.0, description="Overall legitimacy score (0-1)"
    )
    legitimacy_threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Minimum score for execution"
    )

    # Execution Authorization
    execution_authorized: bool = Field(
        default=False, description="Whether execution is authorized"
    )
    blocking_violations: list[GovernanceViolation] = Field(
        default_factory=list, description="Violations that block execution"
    )
    warning_violations: list[GovernanceViolation] = Field(
        default_factory=list, description="Non-blocking violations"
    )

    # Compliance Details
    constitutional_compliant: bool = Field(
        default=True, description="Passed constitutional rule checks"
    )
    authority_compliant: bool = Field(
        default=True, description="Passed authority boundary checks"
    )
    plurality_compliant: bool = Field(
        default=True, description="Passed plurality requirements"
    )

    # Risk Assessment
    authority_risk_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Authority capture risk"
    )
    transparency_score: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Decision transparency score"
    )

    # Audit Trail
    audit_record_id: str | None = Field(
        default=None, description="ID of the audit ledger record"
    )
    evaluation_details: dict = Field(
        default_factory=dict, description="Detailed evaluation breakdown"
    )


# =============================================================================
# AUTHORITY PROFILES
# =============================================================================


class AgentAuthority(BaseModel):
    """Authority granted to an agent.

    Defines what actions an agent is authorized to perform
    within the TORQ system.
    """

    agent_id: str = Field(description="Agent identifier")
    authority_level: AuthorityLevel = Field(
        default=AuthorityLevel.PROPOSE, description="Maximum authority level"
    )
    permitted_actions: list[str] = Field(
        default_factory=list, description="Specific actions permitted"
    )
    forbidden_actions: list[str] = Field(
        default_factory=list, description="Specific actions forbidden"
    )
    resource_constraints: list[str] = Field(
        default_factory=list, description="Resource access constraints"
    )
    granted_at: datetime = Field(default_factory=datetime_utcnow)
    granted_by: str | None = Field(
        default=None, description="Agent that granted this authority"
    )
    expires_at: datetime | None = Field(default=None, description="Authority expiration")


class SystemConstitution(BaseModel):
    """The TORQ system constitution.

    Defines the foundational rules that govern all system behavior.
    This is the root source of governance authority.
    """

    constitution_id: str = Field(default="torq-constitution-v1")
    version: str = Field(default="1.0.0")
    ratified_at: datetime = Field(default_factory=datetime_utcnow)

    # Core Principles
    core_principles: list[str] = Field(
        default_factory=list, description="Foundational principles"
    )

    # Constitutional Rules
    rules: list[str] = Field(
        default_factory=list,
        description="Constitutional rule IDs (detailed rules stored separately)",
    )

    # System-wide Constraints
    max_single_agent_authority: AuthorityLevel = Field(
        default=AuthorityLevel.APPROVE,
        description="Maximum authority any single agent can have",
    )
    requires_plurality_for: list[str] = Field(
        default_factory=list,
        description="Action types requiring plural approval",
    )
    human_approval_required_for: list[str] = Field(
        default_factory=list,
        description="Action types requiring human approval",
    )

    # Amendment Process
    amendment_requires_plurality: bool = Field(default=True)
    amendment_requires_human_approval: bool = Field(default=True)
    amendment_quorum_percent: float = Field(default=0.67, ge=0.5, le=1.0)


# =============================================================================
# ALL EXPORTS
# =============================================================================

__all__ = [
    # Enumerations
    "AuthorityLevel",
    "RuleType",
    # Core Models
    "GovernanceViolation",
    "GovernanceDecisionPacket",
    "GovernanceResult",
    # Authority
    "AgentAuthority",
    "SystemConstitution",
    # Utility
    "datetime_utcnow",
]
