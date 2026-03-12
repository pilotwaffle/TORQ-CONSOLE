"""
Strategic Memory Models

Phase 4H: Persistent strategic knowledge that shapes future reasoning.

Memory types:
- heuristic: Reusable reasoning shortcuts
- playbook: Structured action guidance that worked repeatedly
- warning: Known failure patterns to guard against
- assumption: Stable assumptions until contradicted
- adaptation_lesson: Validated learnings from adaptations
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


# ============================================================================
# Memory Types & Scopes
# ============================================================================

class MemoryType(str, Enum):
    """Types of strategic memory."""
    HEURISTIC = "heuristic"  # Reusable reasoning shortcuts
    PLAYBOOK = "playbook"  # Structured action guidance
    WARNING = "warning"  # Known failure patterns
    ASSUMPTION = "assumption"  # Stable operating assumptions
    ADAPTATION_LESSON = "adaptation_lesson"  # Validated adaptation learnings


class MemoryScope(str, Enum):
    """Scope of memory applicability."""
    GLOBAL = "global"  # Applies to all workflows
    WORKFLOW_TYPE = "workflow_type"  # Specific workflow type
    AGENT_TYPE = "agent_type"  # Specific agent type
    TENANT = "tenant"  # Specific organization
    DOMAIN = "domain"  # Specific domain (e.g., financial, legal)


class MemoryStatus(str, Enum):
    """Lifecycle state of a strategic memory."""
    CANDIDATE = "candidate"  # Pending review
    ACTIVE = "active"  # In use, validated
    DEPRECATED = "deprecated"  # Outdated but kept for reference
    ARCHIVED = "archived"  # No longer in use
    SUPPLANTED = "supplanted"  # Replaced by newer memory


# ============================================================================
# Core Models
# ============================================================================

class StrategicMemoryCreate(BaseModel):
    """Create a new strategic memory."""
    memory_type: MemoryType
    title: str
    domain: Optional[str] = None
    scope: MemoryScope
    scope_key: Optional[str] = None  # e.g., workflow_type name
    memory_content: Dict[str, Any]
    source_pattern_ids: List[str] = Field(default_factory=list)
    source_insight_ids: List[str] = Field(default_factory=list)
    source_experiment_ids: List[str] = Field(default_factory=list)
    initial_confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    initial_durability: float = Field(default=0.5, ge=0.0, le=1.0)
    expires_in_days: Optional[int] = Field(default=90, ge=1)


class StrategicMemory(BaseModel):
    """A persistent strategic memory."""
    id: str
    memory_type: MemoryType
    title: str
    domain: Optional[str]
    scope: MemoryScope
    scope_key: Optional[str]
    confidence: float  # 0.0 to 1.0
    durability_score: float  # 0.0 to 1.0
    memory_content: Dict[str, Any]
    source_pattern_ids: List[str] = Field(default_factory=list)
    source_insight_ids: List[str] = Field(default_factory=list)
    source_experiment_ids: List[str] = Field(default_factory=list)
    status: MemoryStatus
    created_at: datetime
    reviewed_at: Optional[datetime]
    expires_at: Optional[datetime]
    last_validated_at: Optional[datetime]
    invalidated_by_pattern_id: Optional[str] = None
    supplanted_by_memory_id: Optional[str] = None

    # Usage tracking
    usage_count: int = 0
    last_used_at: Optional[datetime] = None

    # Effectiveness tracking
    effectiveness_score: Optional[float] = None  # Updated from feedback


class StrategicMemoryUpdate(BaseModel):
    """Update a strategic memory."""
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    durability_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    memory_content: Optional[Dict[str, Any]] = None
    status: Optional[MemoryStatus] = None
    expires_at: Optional[datetime] = None
    effectiveness_score: Optional[float] = Field(None, ge=0.0, le=1.0)


# ============================================================================
# Consolidation Models
# ============================================================================

class MemoryCandidate(BaseModel):
    """A candidate memory derived from patterns/insights."""
    memory_type: MemoryType
    title: str
    proposed_content: Dict[str, Any]
    proposed_scope: MemoryScope
    proposed_scope_key: Optional[str] = None
    domain: Optional[str] = None

    # Validation scores
    confidence_score: float  # How reliable is this memory?
    durability_score: float  # How long should this persist?
    applicability_score: float  # How broadly applicable?

    # Source evidence
    source_patterns: List[str] = Field(default_factory=list)
    source_insights: List[str] = Field(default_factory=list)
    source_experiments: List[str] = Field(default_factory=list)

    # Evidence counts
    workspace_count: int = 0  # How many workspaces show this?
    execution_count: int = 0  # How many executions support this?
    success_count: int = 0  # How many successful outcomes?

    # Metadata
    proposed_at: datetime = Field(default_factory=datetime.now)
    proposer: str = "system"  # "system", "human", or specific agent


class ConsolidationRule(BaseModel):
    """Rule for determining when a pattern becomes a memory candidate."""
    name: str
    description: str

    # Thresholds
    min_workspace_count: int = 3
    min_execution_count: int = 10
    min_success_rate: float = 0.6
    min_confidence: float = 0.7

    # Memory type to create
    memory_type: MemoryType
    default_scope: MemoryScope = MemoryScope.WORKFLOW_TYPE
    default_durability: float = 0.5

    # Template for content generation
    content_template: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Retrieval Models
# ============================================================================

class MemorySearchRequest(BaseModel):
    """Search for relevant strategic memories."""
    query: Optional[str] = None
    workflow_type: Optional[str] = None
    domain: Optional[str] = None
    agent_type: Optional[str] = None
    memory_types: Optional[List[MemoryType]] = None
    scope: Optional[MemoryScope] = None
    max_results: int = Field(default=5, ge=1, le=50)
    min_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    include_deprecated: bool = False


class MemorySearchResult(BaseModel):
    """A single memory search result with relevance scoring."""
    memory: StrategicMemory
    relevance_score: float  # 0.0 to 1.0
    match_reason: str  # Why this memory matched


class MemoryInjectionContext(BaseModel):
    """Context for memory injection into agent reasoning."""
    workflow_type: Optional[str] = None
    domain: Optional[str] = None
    agent_type: Optional[str] = None
    task_description: Optional[str] = None
    execution_id: Optional[str] = None

    # Injection preferences
    max_memories: int = 5
    min_confidence: float = 0.5
    include_warnings: bool = True
    include_playbooks: bool = True
    include_heuristics: bool = True


class MemoryInjection(BaseModel):
    """Memories to inject into agent context."""
    heuristics: List[StrategicMemory] = Field(default_factory=list)
    playbooks: List[StrategicMemory] = Field(default_factory=list)
    warnings: List[StrategicMemory] = Field(default_factory=list)
    assumptions: List[StrategicMemory] = Field(default_factory=list)
    adaptation_lessons: List[StrategicMemory] = Field(default_factory=list)

    # Injection metadata
    total_count: int = 0
    injected_at: datetime = Field(default_factory=datetime.now)

    def get_context_text(self) -> str:
        """Generate formatted context text for agent consumption."""
        sections = []

        if self.warnings:
            sections.append("## STRATEGIC WARNINGS\n" + "\n".join([
                f"- {m.title}: {m.memory_content.get('description', '')}"
                for m in self.warnings
            ]))

        if self.heuristics:
            sections.append("## REASONING HEURISTICS\n" + "\n".join([
                f"- {m.title}: {m.memory_content.get('rule', m.memory_content.get('description', ''))}"
                for m in self.heuristics
            ]))

        if self.playbooks:
            sections.append("## ACTION PLAYBOOKS\n" + "\n".join([
                f"- {m.title}: {m.memory_content.get('guidance', '')}"
                for m in self.playbooks
            ]))

        if self.adaptation_lessons:
            sections.append("## VALIDATED LEARNINGS\n" + "\n".join([
                f"- {m.title}: {m.memory_content.get('lesson', '')}"
                for m in self.adaptation_lessons
            ]))

        return "\n\n".join(sections) if sections else "No relevant strategic memory available."


# ============================================================================
# Governance Models
# ============================================================================

class MemoryValidation(BaseModel):
    """Validation result for a strategic memory."""
    memory_id: str
    is_valid: bool
    confidence_adjustment: Optional[float] = None
    durability_adjustment: Optional[float] = None
    validator: str = "system"
    validated_at: datetime = Field(default_factory=datetime.now)
    notes: Optional[str] = None


class MemorySupersedence(BaseModel):
    """Record of a memory being replaced by a newer one."""
    old_memory_id: str
    new_memory_id: str
    reason: str
    superseded_at: datetime = Field(default_factory=datetime.now)


class MemoryChallenge(BaseModel):
    """A challenge to a memory based on new evidence."""
    memory_id: str
    challenging_pattern_id: str
    challenge_description: str
    evidence_summary: Dict[str, Any]
    challenged_at: datetime = Field(default_factory=datetime.now)


class GovernanceMetrics(BaseModel):
    """Metrics about strategic memory governance health."""
    total_memories: int
    active_memories: int
    candidate_memories: int
    deprecated_memories: int
    expiring_soon: int  # Expires within 7 days
    expired_but_active: int  # Needs governance attention
    low_confidence_active: int  # Active but confidence < 0.5
    never_validated: int  # Active but never revalidated
    average_memory_age_days: float


# ============================================================================
# Preset Memory Templates
# ============================================================================

class MemoryTemplates:
    """Templates for common strategic memory types."""

    @staticmethod
    def playbook_template(
        title: str,
        domain: str,
        guidance: str,
        triggers: List[str],
        workflow_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Template for playbook memories."""
        return {
            "title": title,
            "description": f"Structured action guidance for {domain}",
            "guidance": guidance,
            "triggers": triggers,  # When to apply this playbook
            "workflow_types": workflow_types or [],
            "steps": [],  # Can be populated with specific steps
            "expected_outcome": "",
            "risk_level": "medium"
        }

    @staticmethod
    def warning_template(
        title: str,
        risk_description: str,
        mitigation: str,
        anti_patterns: List[str]
    ) -> Dict[str, Any]:
        """Template for warning memories."""
        return {
            "title": title,
            "risk_description": risk_description,
            "severity": "medium",  # low, medium, high, critical
            "mitigation": mitigation,
            "anti_patterns": anti_patterns,
            "detection_signals": [],
            "first_observed": None,
            "occurrences": 0
        }

    @staticmethod
    def heuristic_template(
        title: str,
        rule: str,
        rationale: str,
        exceptions: List[str]
    ) -> Dict[str, Any]:
        """Template for heuristic memories."""
        return {
            "title": title,
            "rule": rule,
            "rationale": rationale,
            "exceptions": exceptions,
            "confidence_basis": "observed_pattern",
            "applicability": "broad"
        }

    @staticmethod
    def adaptation_lesson_template(
        title: str,
        lesson: str,
        adaptation_type: str,
        impact_summary: Dict[str, float]
    ) -> Dict[str, Any]:
        """Template for adaptation lesson memories."""
        return {
            "title": title,
            "lesson": lesson,
            "adaptation_type": adaptation_type,  # prompt_revision, routing_change, etc.
            "impact_summary": impact_summary,  # {"coherence": +0.15, "actionability": -0.05}
            "workflow_types": [],
            "duration_active": 0,
            "validation_status": "proven"
        }


# ============================================================================
# Examples (for documentation/testing)
# ============================================================================

EXAMPLE_MEMORIES = {
    "financial_regulatory_playbook": {
        "memory_type": MemoryType.PLAYBOOK,
        "title": "Financial Analysis Regulatory Exposure Check",
        "domain": "financial",
        "scope": MemoryScope.WORKFLOW_TYPE,
        "scope_key": "financial_analysis",
        "confidence": 0.92,
        "durability_score": 0.85,
        "memory_content": {
            "guidance": "Before final synthesis, run a dedicated regulatory exposure pass",
            "triggers": ["financial_analysis", "compliance_review"],
            "steps": [
                "Identify all regulatory frameworks applicable to the analysis",
                "Check for assumptions that may not hold under regulation",
                "Flag any conclusions requiring regulatory qualification"
            ],
            "expected_outcome": "Synthesis includes proper regulatory caveats"
        }
    },

    "prompt_actionability_warning": {
        "memory_type": MemoryType.WARNING,
        "title": "Prompt Verbosity vs Actionability Trade-off",
        "domain": "prompt_engineering",
        "scope": MemoryScope.GLOBAL,
        "confidence": 0.88,
        "durability_score": 0.75,
        "memory_content": {
            "risk_description": "Prompt rewrites that increase coherence often reduce actionability",
            "severity": "medium",
            "mitigation": "Preserve checklist structure when revising prompts",
            "anti_patterns": [
                "Removing explicit action items during coherence improvements",
                "Consolidating structured steps into prose"
            ]
        }
    },

    "checklist_lesson": {
        "memory_type": MemoryType.ADAPTATION_LESSON,
        "title": "Checklist Additions Outperform Prompt Rewrites",
        "domain": "planning",
        "scope": MemoryScope.WORKFLOW_TYPE,
        "scope_key": "planning",
        "confidence": 0.85,
        "durability_score": 0.70,
        "memory_content": {
            "lesson": "Adding targeted checklist items to planner prompts improves quality more reliably than broad prompt rewrites",
            "adaptation_type": "prompt_revision",
            "impact_summary": {
                "coherence_improvement": 0.12,
                "actionability_retention": 0.95,
                "planning_quality_delta": 0.18
            },
            "workflow_types": ["planning", "task_decomposition"],
            "validation_status": "proven"
        }
    }
}
