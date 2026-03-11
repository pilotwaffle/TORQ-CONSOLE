"""
Adaptation Policy Models

Defines the data structures for converting learning signals into
governed adaptation proposals with risk classification and approval workflows.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ============================================================================
# Adaptation Type Taxonomy
# ============================================================================

class AdaptationType(str, Enum):
    """Categories of adaptations that can be proposed."""
    # Prompt adaptations
    PROMPT_REVISION = "prompt_revision"
    PROMPT_CONTEXT_ENRICHMENT = "prompt_context_enrichment"
    PROMPT_CHECKLIST_ADDITION = "prompt_checklist_addition"
    PROMPT_STRUCTURAL_REWRITE = "prompt_structural_rewrite"
    REASONING_STEP_ENFORCEMENT = "reasoning_step_enforcement"
    RISK_DETECTION_ENHANCEMENT = "risk_detection_prompt_enhancement"

    # Routing adaptations
    ROUTING_PROFILE_ADJUSTMENT = "routing_profile_adjustment"
    ROUTING_WEIGHT_TWEAK = "routing_weight_tweak"
    ROUTING_THRESHOLD_CHANGE = "routing_threshold_change"

    # Tool adaptations
    TOOL_PRIORITY_INCREASE = "tool_priority_increase"
    TOOL_PRIORITY_DECREASE = "tool_priority_decrease"
    TOOL_ENABLE = "tool_enable"
    TOOL_DISABLE = "tool_disable"
    TOOL_ORDERING_PREFERENCE = "tool_ordering_preference"

    # Policy adaptations (highest risk)
    POLICY_CHANGE = "policy_change"
    SAFETY_PROMPT_CHANGE = "safety_prompt_change"
    AUDIT_BEHAVIOR_CHANGE = "audit_behavior_change"
    MEMORY_RULE_CHANGE = "memory_rule_change"


class TargetAssetType(str, Enum):
    """Types of assets that adaptations can target."""
    AGENT_PROMPT = "agent_prompt"
    AGENT_SYSTEM_INSTRUCTIONS = "agent_system_instructions"
    ROUTING_PROFILE = "routing_profile"
    TOOL_PREFERENCES = "tool_preferences"
    WORKFLOW_CONFIG = "workflow_config"
    SAFETY_POLICY = "safety_policy"
    MEMORY_RULES = "memory_rules"


class RiskTier(str, Enum):
    """Risk classification for adaptation proposals."""
    TIER_1_LOW = "tier_1_low"  # Auto-apply possible
    TIER_2_MEDIUM = "tier_2_medium"  # Human review required
    TIER_3_HIGH = "tier_3_high"  # Restricted, manual review only


class ApprovalMode(str, Enum):
    """How proposals are approved."""
    AUTO_LOW_RISK = "auto_low_risk"  # Auto-apply for Tier 1
    HUMAN_REVIEW = "human_review"  # Requires approval for Tier 2
    RESTRICTED = "restricted"  # Manual review only for Tier 3


class ApprovalStatus(str, Enum):
    """Lifecycle status of a proposal."""
    DRAFT = "draft"  # Initial state
    PENDING_REVIEW = "pending_review"  # Awaiting human approval
    APPROVED = "approved"  # Approved, ready to apply
    REJECTED = "rejected"  # Rejected by reviewer
    APPLIED = "applied"  # Change has been made
    ROLLED_BACK = "rolled_back"  # Change was reverted
    EXPIRED = "expired"  # Proposal expired without action


# ============================================================================
# Proposal Models
# ============================================================================

class AdaptationProposalCreate(BaseModel):
    """Create a new adaptation proposal from a learning signal."""
    learning_signal_id: str = Field(..., description="Source learning signal")

    # What this proposal changes
    adaptation_type: AdaptationType
    target_asset_type: TargetAssetType
    target_scope: str = Field(..., description="agent_id, workflow_id, or 'global'")
    target_key: str = Field(..., description="Specific asset identifier (e.g., prompt name)")

    # The proposed change
    proposed_change: Dict[str, Any] = Field(..., description="Structured change description")
    change_description: str = Field(..., description="Human-readable description")

    # Evidence and justification
    evidence_summary: str = Field(..., description="Summary of supporting evidence")
    evidence_count: int = Field(default=1, ge=1)
    supporting_execution_ids: List[str] = Field(default_factory=list)

    # Risk and approval
    risk_tier: RiskTier
    approval_mode: ApprovalMode

    # Version tracking
    current_version: Optional[str] = Field(None, description="Current version of target asset")
    candidate_version: str = Field(..., description="Version identifier if applied")

    # Expected impact
    expected_improvement: Optional[str] = Field(None, description="Expected measurable improvement")
    rollback_plan: Optional[str] = Field(None, description="How to revert if needed")


class AdaptationProposalRead(BaseModel):
    """A proposal read from the database."""
    proposal_id: str
    learning_signal_id: str

    adaptation_type: AdaptationType
    target_asset_type: TargetAssetType
    target_scope: str
    target_key: str

    proposed_change: Dict[str, Any]
    change_description: str

    evidence_summary: str
    evidence_count: int
    supporting_execution_ids: List[str]

    risk_tier: RiskTier
    approval_mode: ApprovalMode
    status: ApprovalStatus

    current_version: Optional[str]
    candidate_version: str

    expected_improvement: Optional[str]
    rollback_plan: Optional[str]

    # Approval tracking
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None

    applied_by: Optional[str] = None
    applied_at: Optional[datetime] = None

    # Rollback tracking
    rolled_back_by: Optional[str] = None
    rolled_back_at: Optional[datetime] = None
    rollback_reason: Optional[str] = None

    # Metrics
    metrics_baseline: Optional[Dict[str, float]] = None
    metrics_after: Optional[Dict[str, float]] = None

    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None


class AdaptationProposalUpdate(BaseModel):
    """Update a proposal (typically for review/apply actions)."""
    status: Optional[ApprovalStatus] = None
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None
    metrics_baseline: Optional[Dict[str, float]] = None


class ProposalApplicationResult(BaseModel):
    """Result of applying a proposal."""
    proposal_id: str
    success: bool
    applied_version: str
    applied_at: datetime
    change_summary: str
    rollback_instructions: Optional[str] = None


# ============================================================================
# Policy Configuration
# ============================================================================

class PolicyConfig(BaseModel):
    """Configuration for adaptation policy engine."""
    # Proposal generation thresholds
    min_confidence_for_proposal: float = Field(default=0.7, ge=0.0, le=1.0)
    min_evidence_count: int = Field(default=3, ge=1)
    min_signal_strength: str = Field(default="moderate")

    # Cooldown and deduplication
    proposal_cooldown_hours: int = Field(default=24, description="Min time between proposals for same target")
    max_open_proposals_per_asset: int = Field(default=3, description="Max pending proposals per target")
    deduplication_similarity_threshold: float = Field(default=0.85, ge=0.0, le=1.0)

    # Approval defaults
    tier_1_auto_apply: bool = Field(default=False, description="Auto-apply Tier 1 proposals")
    tier_2_require_approval: bool = Field(default=True, description="Require approval for Tier 2")
    tier_3_require_manual: bool = Field(default=True, description="Manual-only for Tier 3")

    # Expiration
    proposal_expiry_days: int = Field(default=30, description="Days before proposal expires")

    # Governance
    require_rollback_plan: bool = Field(default=True, description="Require rollback plan for Tier 2+")
    require_evidence_linkage: bool = Field(default=True, description="Require execution linkage")


class PolicyEvaluation(BaseModel):
    """Result of evaluating whether a signal can become a proposal."""
    can_propose: bool
    reason: str
    suggested_risk_tier: Optional[RiskTier] = None
    suggested_approval_mode: Optional[ApprovalMode] = None
    guardrail_violations: List[str] = Field(default_factory=list)


# ============================================================================
# Signal-to-Proposal Mapping
# ============================================================================

class SignalToProposalMapping(BaseModel):
    """Maps a learning signal type to its corresponding adaptation proposal type."""
    signal_type: str
    adaptation_type: AdaptationType
    default_risk_tier: RiskTier
    default_approval_mode: ApprovalMode
    description: str


# Default mappings from learning signals to adaptation proposals
DEFAULT_SIGNAL_MAPPINGS: List[Dict[str, Any]] = [
    # Prompt improvement signals
    {
        "signal_type": "prompt_structure_clarity",
        "adaptation_type": "prompt_revision",
        "default_risk_tier": "tier_2_medium",
        "default_approval_mode": "human_review",
        "description": "Revise prompt structure for clarity"
    },
    {
        "signal_type": "prompt_missing_context",
        "adaptation_type": "prompt_context_enrichment",
        "default_risk_tier": "tier_1_low",
        "default_approval_mode": "auto_low_risk",
        "description": "Add missing context to prompt"
    },
    {
        "signal_type": "prompt_ambiguous_instructions",
        "adaptation_type": "prompt_checklist_addition",
        "default_risk_tier": "tier_1_low",
        "default_approval_mode": "auto_low_risk",
        "description": "Add clarification checklist to prompt"
    },

    # Routing adjustment signals
    {
        "signal_type": "routing_misalignment",
        "adaptation_type": "routing_profile_adjustment",
        "default_risk_tier": "tier_2_medium",
        "default_approval_mode": "human_review",
        "description": "Adjust routing profile to fix misalignment"
    },
    {
        "signal_type": "routing_missing_capability",
        "adaptation_type": "routing_weight_tweak",
        "default_risk_tier": "tier_2_medium",
        "default_approval_mode": "human_review",
        "description": "Add missing capability to routing"
    },
    {
        "signal_type": "routing_overspecialization",
        "adaptation_type": "routing_threshold_change",
        "default_risk_tier": "tier_2_medium",
        "default_approval_mode": "human_review",
        "description": "Adjust routing thresholds for broader coverage"
    },

    # Tool preference signals
    {
        "signal_type": "tool_preference_emergent",
        "adaptation_type": "tool_priority_increase",
        "default_risk_tier": "tier_1_low",
        "default_approval_mode": "auto_low_risk",
        "description": "Increase priority of effective tool"
    },
    {
        "signal_type": "tool_avoidance_pattern",
        "adaptation_type": "tool_priority_decrease",
        "default_risk_tier": "tier_2_medium",
        "default_approval_mode": "human_review",
        "description": "Decrease priority of problematic tool"
    },
    {
        "signal_type": "tool_inefficiency",
        "adaptation_type": "tool_disable",
        "default_risk_tier": "tier_2_medium",
        "default_approval_mode": "human_review",
        "description": "Disable inefficient tool"
    },

    # Reasoning pattern signals
    {
        "signal_type": "repeated_unresolved_questions",
        "adaptation_type": "prompt_checklist_addition",
        "default_risk_tier": "tier_1_low",
        "default_approval_mode": "auto_low_risk",
        "description": "Add planner checklist for question resolution"
    },
    {
        "signal_type": "repeated_contradiction",
        "adaptation_type": "reasoning_step_enforcement",
        "default_risk_tier": "tier_2_medium",
        "default_approval_mode": "human_review",
        "description": "Add reasoning steps to prevent contradictions"
    },
    {
        "signal_type": "risk_pattern_critical",
        "adaptation_type": "risk_detection_prompt_enhancement",
        "default_risk_tier": "tier_2_medium",
        "default_approval_mode": "human_review",
        "description": "Enhance risk detection in prompt"
    },
    {
        "signal_type": "coherence_degradation",
        "adaptation_type": "prompt_structural_rewrite",
        "default_risk_tier": "tier_2_medium",
        "default_approval_mode": "human_review",
        "description": "Rewrite prompt structure to improve coherence"
    },
]


def get_signal_mapping(signal_type: str) -> Optional[Dict[str, Any]]:
    """Get the adaptation proposal mapping for a signal type."""
    for mapping in DEFAULT_SIGNAL_MAPPINGS:
        if mapping["signal_type"] == signal_type:
            return mapping
    return None


def get_adaptation_type(signal_type: str) -> Optional[AdaptationType]:
    """Get the adaptation type for a signal type."""
    mapping = get_signal_mapping(signal_type)
    if mapping:
        try:
            return AdaptationType(mapping["adaptation_type"])
        except ValueError:
            pass
    return None


# ============================================================================
# Guardrail Violations
# ============================================================================

class GuardrailViolation(BaseModel):
    """A guardrail violation detected during proposal evaluation."""
    violation_type: str
    description: str
    severity: str  # "warning", "error"
    affected_field: Optional[str] = None


# Common guardrail violations
GUARDRAIL_MIN_EVIDENCE = "min_evidence_not_met"
GUARDRAIL_COOLDOWN_ACTIVE = "cooldown_active"
GUARDRAIL_MAX_OPEN_PROPOSALS = "max_open_proposals_exceeded"
GUARDRAIL_MISSING_ROLLBACK = "missing_rollback_plan"
GUARDRAIL_HIGH_RISK_AUTO_APPLY = "high_risk_auto_apply_attempt"
GUARDRAIL_DUPLICATE_PROPOSAL = "duplicate_proposal"
GUARDRAIL_EXPIRED_SIGNAL = "signal_expired"
