"""
Memory Models - Phase 4H.1 Milestone 1

Defines the data models for governed memory in TORQ.
Memory is derived from validated workspace artifacts with
explicit eligibility rules and confidence thresholds.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Enums
# ============================================================================

class MemoryType(str, Enum):
    """Types of memory entries."""

    # Knowledge from verified sources
    KNOWLEDGE = "knowledge"

    # Patterns observed across executions
    PATTERN = "pattern"

    # Decisions made and their rationale
    DECISION = "decision"

    # Verified code patterns
    CODE_PATTERN = "code_pattern"

    # Architecture decisions
    ARCHITECTURE_DECISION = "architecture_decision"

    # Team performance insights
    TEAM_INSIGHT = "team_insight"

    # API endpoint knowledge
    API_KNOWLEDGE = "api_knowledge"

    # Best practices
    BEST_PRACTICE = "best_practice"


class ConfidenceLevel(str, Enum):
    """Confidence levels for memory validation."""

    VERIFIED = "verified"  # 0.9 - 1.0: Auto-accept
    HIGH = "high"  # 0.7 - 0.9: Accept with log
    MEDIUM = "medium"  # 0.5 - 0.7: Review required
    LOW = "low"  # 0.0 - 0.5: Reject


class MemoryStatus(str, Enum):
    """Status of a memory entry."""

    ACTIVE = "active"
    STALE = "stale"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"


class ValidationDecision(str, Enum):
    """Decision from validation gate."""

    ACCEPT = "accept"
    REJECT = "reject"
    REVIEW = "review"


class RejectionReason(str, Enum):
    """Reasons for rejecting memory candidates."""

    LOW_CONFIDENCE = "low_confidence"
    INCOMPLETE = "incomplete"
    NO_PROVENANCE = "no_provenance"
    STALE_SOURCE = "stale_source"
    CONFLICTING = "conflicting"
    INVALID_SOURCE_TYPE = "invalid_source_type"
    MISSING_FIELDS = "missing_fields"
    STORAGE_ERROR = "storage_error"


# ============================================================================
# Core Models
# ============================================================================

class MemoryProvenance(BaseModel):
    """Provenance information for memory entries."""

    # Source artifact
    artifact_id: UUID
    artifact_type: str
    workspace_id: UUID

    # Execution context
    mission_id: Optional[UUID] = None
    node_id: Optional[UUID] = None
    execution_id: Optional[str] = None
    team_execution_id: Optional[UUID] = None

    # Team context
    role_name: Optional[str] = None
    round_number: Optional[int] = None

    # Tool that generated the artifact
    tool_name: Optional[str] = None

    # When the artifact was created
    artifact_created_at: datetime

    # Traceability chain
    traceability_chain: Dict[str, Any] = Field(default_factory=dict)


class MemoryMetadata(BaseModel):
    """Metadata for memory entries."""

    # Memory classification
    memory_type: MemoryType
    confidence_level: ConfidenceLevel

    # Status
    status: MemoryStatus = Field(default=MemoryStatus.ACTIVE)

    # Quality metrics
    confidence_score: float = Field(ge=0.0, le=1.0)
    completeness_score: float = Field(ge=0.0, le=1.0)

    # Temporal information
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed_at: Optional[datetime] = None
    access_count: int = Field(default=0)

    # Freshness
    freshness_window_days: int = Field(default=30)
    expires_at: Optional[datetime] = None

    # Validation status
    validation_decision: Optional[ValidationDecision] = None
    rejection_reason: Optional[RejectionReason] = None

    # Versioning
    version: int = Field(default=1)
    supersedes_memory_id: Optional[UUID] = None
    superseded_by_memory_id: Optional[UUID] = None


class MemoryContent(BaseModel):
    """Content of a memory entry."""

    # Core content
    title: str
    summary: str

    # Detailed content
    content_json: Dict[str, Any] = Field(default_factory=dict)
    content_text: str = ""

    # Tags for categorization
    tags: List[str] = Field(default_factory=list)

    # Related entities
    related_concepts: List[str] = Field(default_factory=list)
    related_artifacts: List[UUID] = Field(default_factory=list)


class MemoryCandidate(BaseModel):
    """
    A candidate for becoming a validated memory entry.

    This represents an artifact that has been extracted
    but not yet validated by the memory gate.
    """

    # Source artifact reference
    artifact_id: UUID
    artifact_type: str

    # Extracted content
    content: MemoryContent

    # Provenance
    provenance: MemoryProvenance

    # Validation data
    confidence_score: float = Field(ge=0.0, le=1.0)
    completeness_score: float = Field(ge=0.0, le=1.0)
    proposed_memory_type: MemoryType

    # Validation state (to be filled by gate)
    validation_decision: Optional[ValidationDecision] = None
    rejection_reason: Optional[RejectionReason] = None
    validation_message: Optional[str] = None

    @field_validator("confidence_score")
    @classmethod
    def confidence_must_be_valid(cls, v: float) -> float:
        """Validate confidence score is in range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        return v

    @field_validator("completeness_score")
    @classmethod
    def completeness_must_be_valid(cls, v: float) -> float:
        """Validate completeness score is in range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Completeness score must be between 0.0 and 1.0")
        return v

    @property
    def confidence_level(self) -> ConfidenceLevel:
        """Get confidence level from score."""
        if self.confidence_score >= 0.9:
            return ConfidenceLevel.VERIFIED
        elif self.confidence_score >= 0.7:
            return ConfidenceLevel.HIGH
        elif self.confidence_score >= 0.5:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW

    @property
    def is_eligible(self) -> bool:
        """Check if candidate meets basic eligibility."""
        # Must have minimum confidence
        if self.confidence_score < 0.5:
            return False

        # Must have minimum completeness
        if self.completeness_score < 0.6:
            return False

        # Must have provenance
        if not self.provenance.artifact_id:
            return False

        # Must have content
        if not self.content.title or not self.content.summary:
            return False

        return True


class ValidatedMemory(BaseModel):
    """
    A validated, persisted memory entry.

    This represents memory that has passed the validation gate
    and been approved for storage and retrieval.
    """

    # Memory identification
    id: UUID
    memory_id: str  # Human-readable identifier

    # Content and metadata
    content: MemoryContent
    metadata: MemoryMetadata
    provenance: MemoryProvenance

    # Validation info
    validated_at: datetime
    validated_by: str = "system"  # system, reviewer, etc.

    @property
    def is_stale(self) -> bool:
        """Check if memory is stale based on freshness window."""
        if self.metadata.expires_at:
            return datetime.utcnow() > self.metadata.expires_at

        window = timedelta(days=self.metadata.freshness_window_days)
        return datetime.utcnow() > self.metadata.created_at + window

    @property
    def is_active(self) -> bool:
        """Check if memory is active (not stale or superseded)."""
        return (
            self.metadata.status == MemoryStatus.ACTIVE
            and not self.is_stale
        )


# ============================================================================
# Validation Rules
# ============================================================================

class EligibilityRule(BaseModel):
    """A rule for determining memory eligibility."""

    rule_name: str
    description: str
    artifact_types: List[str] = Field(default_factory=list)
    min_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    min_completeness: float = Field(default=0.6, ge=0.0, le=1.0)
    required_fields: List[str] = Field(default_factory=list)
    freshness_days: Optional[int] = None
    memory_types: List[MemoryType] = Field(default_factory=list)

    def check_eligibility(self, candidate: MemoryCandidate) -> tuple[bool, Optional[str]]:
        """
        Check if a candidate meets this rule.

        Returns:
            (is_eligible, rejection_reason)
        """
        # Check artifact type
        if self.artifact_types and candidate.artifact_type not in self.artifact_types:
            return False, RejectionReason.INVALID_SOURCE_TYPE

        # Check confidence
        if candidate.confidence_score < self.min_confidence:
            return False, RejectionReason.LOW_CONFIDENCE

        # Check completeness
        if candidate.completeness_score < self.min_completeness:
            return False, RejectionReason.INCOMPLETE

        # Check required fields
        content_dict = candidate.content.model_dump()
        for field in self.required_fields:
            if field not in content_dict or not content_dict[field]:
                return False, RejectionReason.MISSING_FIELDS

        # Check freshness
        if self.freshness_days:
            age = datetime.utcnow() - candidate.provenance.artifact_created_at
            if age.days > self.freshness_days:
                return False, RejectionReason.STALE_SOURCE

        # Check memory type match
        if self.memory_types and candidate.proposed_memory_type not in self.memory_types:
            return False, RejectionReason.INVALID_SOURCE_TYPE

        return True, None


class EligibilityRuleset(BaseModel):
    """A collection of eligibility rules."""

    name: str
    description: str
    rules: List[EligibilityRule] = Field(default_factory=list)
    default_min_confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    default_min_completeness: float = Field(default=0.6, ge=0.0, le=1.0)

    def check_candidate(self, candidate: MemoryCandidate) -> tuple[bool, Optional[str], Optional[EligibilityRule]]:
        """
        Check if a candidate meets any rule in the ruleset.

        Returns:
            (is_eligible, rejection_reason, matching_rule)
        """
        # First try specific rules
        for rule in self.rules:
            is_eligible, reason = rule.check_eligibility(candidate)
            if is_eligible:
                return True, None, rule

        # If no specific rule matched, check default thresholds
        if candidate.confidence_score >= self.default_min_confidence:
            if candidate.completeness_score >= self.default_min_completeness:
                return True, None, None

        # Default rejection
        if candidate.confidence_score < self.default_min_confidence:
            return False, RejectionReason.LOW_CONFIDENCE, None
        else:
            return False, RejectionReason.INCOMPLETE, None


# ============================================================================
# Predefined Rulesets
# ============================================================================

DEFAULT_ELIGIBILITY_RULESET = EligibilityRuleset(
    name="default",
    description="Default eligibility rules for memory candidates",
    default_min_confidence=0.7,
    default_min_completeness=0.6,
    rules=[
        # High-confidence knowledge - auto-accept
        EligibilityRule(
            rule_name="verified_knowledge",
            description="Verified knowledge from code execution",
            artifact_types=["code_execution", "verified_output"],
            min_confidence=0.9,
            min_completeness=0.8,
            memory_types=[MemoryType.KNOWLEDGE, MemoryType.CODE_PATTERN],
        ),
        # Web search - conditional
        EligibilityRule(
            rule_name="web_search_knowledge",
            description="Knowledge from web search requires higher confidence",
            artifact_types=["web_search", "web_fetch"],
            min_confidence=0.75,
            min_completeness=0.7,
            freshness_days=7,  # Web data stales quickly
            memory_types=[MemoryType.KNOWLEDGE],
        ),
        # Decisions - moderate threshold
        EligibilityRule(
            rule_name="decision_memory",
            description="Decisions made during execution",
            artifact_types=["decision", "team_decision"],
            min_confidence=0.7,
            min_completeness=0.8,
            required_fields=["rationale", "alternatives_considered"],
            freshness_days=90,  # Decisions are stable
            memory_types=[MemoryType.DECISION, MemoryType.ARCHITECTURE_DECISION],
        ),
        # Patterns - requires observation
        EligibilityRule(
            rule_name="pattern_memory",
            description="Patterns observed across executions",
            artifact_types=["analysis", "pattern_recognition"],
            min_confidence=0.75,
            min_completeness=0.7,
            memory_types=[MemoryType.PATTERN],
        ),
        # Team insights
        EligibilityRule(
            rule_name="team_insight",
            description="Insights about team performance",
            artifact_types=["team_output", "team_evaluation"],
            min_confidence=0.7,
            min_completeness=0.6,
            freshness_days=14,  # Team dynamics change
            memory_types=[MemoryType.TEAM_INSIGHT],
        ),
        # API knowledge - short freshness
        EligibilityRule(
            rule_name="api_knowledge",
            description="Knowledge about API endpoints",
            artifact_types=["api_call", "api_documentation"],
            min_confidence=0.8,
            min_completeness=0.8,
            required_fields=["endpoint", "method", "parameters"],
            freshness_days=7,  # APIs change frequently
            memory_types=[MemoryType.API_KNOWLEDGE],
        ),
        # Best practices
        EligibilityRule(
            rule_name="best_practice",
            description="Best practices and conventions",
            artifact_types=["documentation", "guideline", "standard"],
            min_confidence=0.75,
            min_completeness=0.7,
            freshness_days=30,
            memory_types=[MemoryType.BEST_PRACTICE],
        ),
    ],
)


# ============================================================================
# Freshness Rules by Domain
# ============================================================================

FRESHNESS_RULES: Dict[str, int] = {
    # High volatility
    "api_knowledge": 7,
    "web_search": 7,
    "external_data": 1,

    # Medium volatility
    "team_insight": 14,
    "team_performance": 14,

    # Low volatility
    "code_pattern": 30,
    "best_practice": 30,
    "pattern": 30,

    # Very stable
    "architecture_decision": 90,
    "decision": 90,
}


def get_freshness_window(memory_type: Union[str, MemoryType]) -> int:
    """Get freshness window for a memory type."""
    if isinstance(memory_type, MemoryType):
        type_str = memory_type.value
    else:
        type_str = str(memory_type)

    return FRESHNESS_RULES.get(type_str, 30)  # Default 30 days


# ============================================================================
# Confidence Threshold Helpers
# ============================================================================

def confidence_to_level(score: float) -> ConfidenceLevel:
    """Convert confidence score to level."""
    if score >= 0.9:
        return ConfidenceLevel.VERIFIED
    elif score >= 0.7:
        return ConfidenceLevel.HIGH
    elif score >= 0.5:
        return ConfidenceLevel.MEDIUM
    else:
        return ConfidenceLevel.LOW


def level_to_min_score(level: ConfidenceLevel) -> float:
    """Get minimum score for a confidence level."""
    level_scores = {
        ConfidenceLevel.VERIFIED: 0.9,
        ConfidenceLevel.HIGH: 0.7,
        ConfidenceLevel.MEDIUM: 0.5,
        ConfidenceLevel.LOW: 0.0,
    }
    return level_scores.get(level, 0.0)
