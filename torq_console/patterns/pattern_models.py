"""
Phase 4G: Pattern Aggregation - Pattern Object Model

This module defines the Pattern layer which sits above Artifacts, Memory, and Insights.

Layer Architecture:
- Artifact = Raw execution output (Phase 5.3)
- Memory = Validated carry-forward knowledge (Phase 4H.1)
- Insight = Curated reusable intelligence (Insight Publishing M1-M4)
- Pattern = Recurring, cross-execution structure or signal (This Phase - 4G)

Key Design Principles:
1. Patterns are DETECTED across executions, not created directly
2. Patterns require RECURRENCE across multiple artifacts/memory/insights
3. Patterns have CONFIDENCE based on observation frequency
4. Patterns have LINEAGE back to source artifacts/memory/insights
5. Patterns are DISTINCT from insights (insights = reusable knowledge, patterns = recurring structure)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Set
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


# ============================================================================
# Pattern Type Enumeration
# ============================================================================

class PatternType(str, Enum):
    """
    Categories of patterns that can be detected across executions.

    Each pattern type represents a distinct kind of recurring structure
    that can be identified by analyzing artifacts, memory, and insights.
    """

    # Execution patterns - recurring structures in how work is done
    EXECUTION_PATTERN = "execution_pattern"
    """Recurring sequence of steps, decisions, or workflows."""

    FAILURE_PATTERN = "failure_pattern"
    """Recurring failure modes, error sequences, or breakdown points."""

    RECOVERY_PATTERN = "recovery_pattern"
    """Recurring recovery actions, mitigations, or bounce-back patterns."""

    # Collaboration patterns - recurring team behaviors
    COLLABORATION_PATTERN = "collaboration_pattern"
    """Recurring team interaction patterns, role coordination, or handoff modes."""

    # Decision patterns - recurring choice tendencies
    DECISION_PATTERN = "decision_pattern"
    """Recurring decision points, choice tendencies, or selection patterns."""

    # Retrieval patterns - recurring knowledge access
    RETRIEVAL_PATTERN = "retrieval_pattern"
    """Recurring patterns in how agents retrieve and use information."""

    # Quality patterns - recurring success/failure indicators
    QUALITY_PATTERN = "quality_pattern"
    """Recurring indicators of output quality, effectiveness, or excellence."""

    # Risk patterns - recurring threat or hazard patterns
    RISK_PATTERN = "risk_pattern"
    """Recurring risk scenarios, threat patterns, or hazard precursors."""

    # Domain-specific patterns
    DOMAIN_PATTERN = "domain_pattern"
    """Patterns specific to a domain (e.g., financial, legal, technical)."""

    # Temporal patterns - timing-based recurrence
    TEMPORAL_PATTERN = "temporal_pattern"
    """Patterns based on timing, sequences, or periodic occurrences."""

    # Resource patterns - recurring resource usage
    RESOURCE_PATTERN = "resource_pattern"
    """Recurring patterns in resource allocation, usage, or constraints."""


# ============================================================================
# Pattern Lifecycle States
# ============================================================================

class PatternLifecycleState(str, Enum):
    """
    Lifecycle states for a detected pattern.

    The aggregation pipeline flows through these states:
    candidate → observed → validated → active → superseded → archived
    """

    CANDIDATE = "candidate"
    """
    Initially detected pattern that meets minimum recurrence threshold.
    Not yet validated as a stable pattern.
    """

    OBSERVED = "observed"
    """
    Pattern has been observed multiple times but not yet validated.
    Accumulating evidence for stability.
    """

    VALIDATED = "validated"
    """
    Pattern has been validated as stable and recurring.
    Ready for use in agent execution and decision-making.
    """

    ACTIVE = "active"
    """
    Validated pattern that is currently being detected in recent executions.
    Indicates the pattern is still relevant and recurring.
    """

    SUPERSEDED = "superseded"
    """
    Pattern has been replaced by a newer, more accurate version.
    Kept for historical analysis but not used in execution.
    """

    ARCHIVED = "archived"
    """
    Pattern is no longer relevant or hasn't been observed in a long time.
    Kept for historical analysis but not used in execution.
    """


# ============================================================================
# Pattern Source Enumeration
# ============================================================================

class PatternSourceType(str, Enum):
    """
    Types of sources that can contribute to pattern detection.
    """

    ARTIFACT = "artifact"
    """Pattern detected across workspace artifacts."""

    MEMORY = "memory"
    """Pattern detected across validated strategic memories."""

    INSIGHT = "insight"
    """Pattern detected across published insights."""

    EXECUTION_TRACE = "execution_trace"
    """Pattern detected in execution traces or logs."""

    TEAM_EVENT = "team_event"
    """Pattern detected in team coordination events."""

    AGENT_BEHAVIOR = "agent_behavior"
    """Pattern detected in agent behavior or choices."""


# ============================================================================
# Core Pattern Models
# ============================================================================

class PatternSourceReference(BaseModel):
    """
    Reference to a source that contributed to pattern detection.
    """
    source_type: PatternSourceType = Field(..., description="Type of the source")
    source_id: str = Field(..., description="Identifier of the source")
    contribution_weight: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="How much this source contributed to pattern detection"
    )
    extraction_method: Optional[str] = Field(
        None,
        description="Method used to extract pattern from this source"
    )

    # Optional metadata
    source_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the source"
    )

    # Timestamp
    observed_at: datetime = Field(
        default_factory=datetime.now,
        description="When this source was observed"
    )


class PatternQualityMetrics(BaseModel):
    """
    Quality and confidence metrics for a detected pattern.
    """

    # Confidence in pattern validity
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="How confident are we that this is a real pattern?"
    )

    # Stability metrics
    stability_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="How stable is the pattern across observations?"
    )

    consistency_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="How consistent is the pattern in its manifestation?"
    )

    # Observation metrics
    observation_count: int = Field(
        default=1,
        ge=1,
        description="Number of times this pattern has been observed"
    )

    unique_execution_count: int = Field(
        default=1,
        ge=1,
        description="Number of distinct executions showing this pattern"
    )

    distinct_source_count: int = Field(
        default=1,
        ge=1,
        description="Number of distinct sources contributing to detection"
    )

    # Temporal metrics
    first_observed_at: datetime = Field(
        ...,
        description="When this pattern was first observed"
    )

    last_observed_at: datetime = Field(
        default_factory=datetime.now,
        description="When this pattern was most recently observed"
    )

    observation_span_days: int = Field(
        default=0,
        ge=0,
        description="Days between first and last observation"
    )

    # Frequency metrics
    avg_frequency_days: Optional[float] = Field(
        None,
        description="Average days between observations"
    )

    # Effectiveness metrics (for applicable patterns)
    effectiveness_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="When followed/used, how effective is this pattern?"
    )

    negative_outcome_rate: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Rate of negative outcomes when pattern occurs"
    )


class PatternCreate(BaseModel):
    """
    Request model for creating a new detected pattern.
    """

    # Core identification
    pattern_type: PatternType = Field(..., description="Type of pattern")
    name: str = Field(..., min_length=1, max_length=500, description="Pattern name")
    description: str = Field(..., min_length=1, max_length=2000, description="Pattern description")

    # Domain/scope
    domain: Optional[str] = Field(
        None,
        description="Domain classification (e.g., 'financial', 'technical')"
    )

    scope: Optional[str] = Field(
        None,
        description="Scope (e.g., 'planning', 'execution', 'review')"
    )

    # Pattern structure
    structure: Dict[str, Any] = Field(
        ...,
        description="The detected structure (sequence, cluster, tendency, etc.)"
    )

    # Characteristics
    characteristics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Identifying characteristics of this pattern"
    )

    # Tags for categorization
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for search and categorization"
    )

    # Lineage - what sources contributed
    source_references: List[PatternSourceReference] = Field(
        ...,
        min_length=1,
        description="Sources this pattern was detected from"
    )

    # Quality metrics
    quality: PatternQualityMetrics = Field(
        ...,
        description="Quality and confidence assessment"
    )

    # Initial lifecycle state
    initial_state: PatternLifecycleState = Field(
        default=PatternLifecycleState.CANDIDATE,
        description="Initial lifecycle state"
    )

    # Optional expiration
    expires_in_days: Optional[int] = Field(
        None,
        ge=1,
        description="Days until this pattern expires if not re-observed"
    )


class PatternUpdate(BaseModel):
    """
    Request model for updating an existing pattern.
    """

    # Content updates
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, min_length=1, max_length=2000)
    structure: Optional[Dict[str, Any]] = None
    characteristics: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None

    # Quality updates
    quality: Optional[PatternQualityMetrics] = None

    # Lifecycle updates
    lifecycle_state: Optional[PatternLifecycleState] = None

    # Expiration
    expires_at: Optional[datetime] = None


class Pattern(BaseModel):
    """
    A detected recurring pattern across executions.

    Patterns are discovered by analyzing artifacts, memory, and insights
    to find recurring structures, sequences, or tendencies.
    """

    # Core identification
    id: UUID = Field(default_factory=uuid4, description="Unique pattern identifier")
    pattern_type: PatternType = Field(..., description="Type of pattern")
    name: str = Field(..., description="Pattern name")
    description: str = Field(..., description="Pattern description")

    # Domain/scope
    domain: Optional[str] = Field(None, description="Domain classification")
    scope: Optional[str] = Field(None, description="Scope")

    # Pattern structure
    structure: Dict[str, Any] = Field(..., description="Detected structure")
    characteristics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Identifying characteristics"
    )
    tags: List[str] = Field(default_factory=list, description="Categorization tags")

    # Lineage
    source_references: List[PatternSourceReference] = Field(
        ...,
        description="Sources this pattern was detected from"
    )

    # Quality
    quality: PatternQualityMetrics = Field(..., description="Quality metrics")

    # Lifecycle
    lifecycle_state: PatternLifecycleState = Field(
        ...,
        description="Current lifecycle state"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now, description="Creation time")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update time")
    created_by: str = Field(default="pattern_detector", description="What created this pattern")

    # Supersession
    superseded_by_id: Optional[UUID] = Field(None, description="If superseded, which pattern replaced it")
    superseded_at: Optional[datetime] = Field(None, description="When this pattern was superseded")

    # Expiration
    expires_at: Optional[datetime] = Field(None, description="When this pattern expires")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ============================================================================
# Aggregation Rule Models
# ============================================================================

class AggregationEligibilityRule(BaseModel):
    """
    Rule defining what qualifies as pattern-worthy aggregation.
    """

    name: str = Field(..., description="Rule name")

    # Source requirements
    min_source_count: int = Field(
        default=3,
        ge=2,
        description="Minimum number of sources required"
    )

    min_unique_executions: int = Field(
        default=2,
        ge=2,
        description="Minimum distinct executions showing this pattern"
    )

    min_observation_span_days: int = Field(
        default=7,
        ge=1,
        description="Minimum time span over which observations must occur"
    )

    # Pattern type specific requirements
    pattern_type_requirements: Dict[PatternType, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Type-specific requirements"
    )

    # Quality thresholds
    min_confidence_threshold: float = Field(
        default=0.60,
        ge=0.0,
        le=1.0,
        description="Minimum confidence to promote from candidate"
    )

    min_stability_threshold: float = Field(
        default=0.70,
        ge=0.0,
        le=1.0,
        description="Minimum stability to validate pattern"
    )


class PatternLineageRequirement(BaseModel):
    """
    Requirements for pattern lineage back to sources.
    """

    # Source diversity
    require_multiple_source_types: bool = Field(
        default=True,
        description="Must have patterns from multiple source types"
    )

    min_source_types: int = Field(
        default=2,
        ge=1,
        description="Minimum number of different source types required"
    )

    # Traceability
    require_execution_traceability: bool = Field(
        default=True,
        description="Must be traceable back to specific executions"
    )

    require_artifact_lineage: bool = Field(
        default=False,
        description="Must have artifact-level lineage"
    )

    require_memory_lineage: bool = Field(
        default=True,
        description="Must have memory-level lineage"
    )

    require_insight_lineage: bool = Field(
        default=False,
        description="Must have insight-level lineage"
    )


class AggregationCriteria(BaseModel):
    """
    Criteria for aggregating observations into a pattern.
    """

    pattern_type: PatternType = Field(..., description="Type of pattern being aggregated")

    # Similarity threshold
    similarity_threshold: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Minimum similarity to group observations"
    )

    # Temporal clustering
    max_cluster_time_span_days: int = Field(
        default=30,
        ge=1,
        description="Maximum time span for observations in a cluster"
    )

    # Source requirements
    eligibility_rules: AggregationEligibilityRule = Field(
        default_factory=AggregationEligibilityRule,
        description="Eligibility rules for aggregation"
    )

    # Lineage requirements
    lineage_requirements: PatternLineageRequirement = Field(
        default_factory=PatternLineageRequirement,
        description="Lineage requirements"
    )


# ============================================================================
# Pattern Detection Result Models
# ============================================================================

class PatternObservation(BaseModel):
    """
    A single observation that contributes to pattern detection.
    """

    id: UUID = Field(default_factory=uuid4)

    # What was observed
    pattern_type: PatternType
    observed_structure: Dict[str, Any]

    # Where it was observed
    source_type: PatternSourceType
    source_id: str
    execution_id: Optional[str] = None
    agent_id: Optional[str] = None

    # When and how
    observed_at: datetime = Field(default_factory=datetime.now)
    detection_method: str

    # Confidence in this single observation
    observation_confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class PatternDetectionResult(BaseModel):
    """
    Result of a pattern detection run.
    """

    pattern_type: PatternType
    observations: List[PatternObservation]

    # Aggregated pattern (if eligibility met)
    aggregated_pattern: Optional[Pattern] = None

    # Detection metadata
    detection_method: str
    confidence_score: float
    eligibility_check: Dict[str, Any] = Field(default_factory=dict)

    # Timestamp
    detected_at: datetime = Field(default_factory=datetime.now)


# ============================================================================
# Pattern Templates
# ============================================================================

class PatternTemplates:
    """
    Templates for creating patterns of different types.
    """

    @staticmethod
    def execution_pattern_template(
        name: str,
        steps: List[str],
        frequency: str,
        contexts: List[str]
    ) -> Dict[str, Any]:
        """Template for execution patterns (recurring step sequences)."""
        return {
            "pattern_type": PatternType.EXECUTION_PATTERN,
            "structure": {
                "type": "sequence",
                "steps": steps,
                "expected_duration": None,
            },
            "characteristics": {
                "frequency": frequency,
                "common_contexts": contexts,
            }
        }

    @staticmethod
    def failure_pattern_template(
        name: str,
        failure_mode: str,
        precursor_signals: List[str],
        common_contexts: List[str]
    ) -> Dict[str, Any]:
        """Template for failure patterns (recurring failure modes)."""
        return {
            "pattern_type": PatternType.FAILURE_PATTERN,
            "structure": {
                "type": "failure_mode",
                "failure_type": failure_mode,
                "precursor_signals": precursor_signals,
            },
            "characteristics": {
                "common_contexts": common_contexts,
                "severity": None,
            }
        }

    @staticmethod
    def collaboration_pattern_template(
        name: str,
        roles_involved: List[str],
        interaction_pattern: str,
        frequency: str
    ) -> Dict[str, Any]:
        """Template for collaboration patterns (team interaction patterns)."""
        return {
            "pattern_type": PatternType.COLLABORATION_PATTERN,
            "structure": {
                "type": "team_interaction",
                "roles": roles_involved,
                "interaction_pattern": interaction_pattern,
            },
            "characteristics": {
                "frequency": frequency,
            }
        }

    @staticmethod
    def retrieval_pattern_template(
        name: str,
        information_type: str,
        retrieval_sources: List[str],
        timing: str
    ) -> Dict[str, Any]:
        """Template for retrieval patterns (how agents access information)."""
        return {
            "pattern_type": PatternType.RETRIEVAL_PATTERN,
            "structure": {
                "type": "information_access",
                "information_type": information_type,
                "sources": retrieval_sources,
            },
            "characteristics": {
                "timing": timing,
            }
        }


# ============================================================================
# Example Patterns (for documentation)
# ============================================================================

EXAMPLE_PATTERNS: Dict[str, Dict[str, Any]] = {
    "planning_heuristic_pattern": {
        "pattern_type": PatternType.EXECUTION_PATTERN,
        "name": "Planning Quality Improves Execution Outcomes",
        "description": "Teams that create structured plans before execution produce better outcomes",
        "domain": "execution",
        "scope": "planning",
        "structure": {
            "type": "sequence",
            "steps": ["analyze_requirements", "create_plan", "validate_plan", "execute"],
        },
        "characteristics": {
            "frequency": "high",
            "contexts": ["mission_start", "complex_tasks"],
        }
    },

    "error_recovery_pattern": {
        "pattern_type": PatternType.RECOVERY_PATTERN,
        "name": "API Error Recovery with Retry",
        "description": "Pattern of retrying API calls with exponential backoff",
        "domain": "technical",
        "scope": "api_interaction",
        "structure": {
            "type": "recovery_sequence",
            "recovery_actions": ["detect_error", "calculate_backoff", "retry", "log"],
        },
        "characteristics": {
            "frequency": "high",
            "success_rate": 0.85,
        }
    },
}
