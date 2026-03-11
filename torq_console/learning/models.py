"""
Learning Signal Models

Defines the data structures for the Learning Signal Engine.
Signals are extracted from evaluations, workspace entries, and syntheses
to drive adaptive improvements in agent behavior.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ============================================================================
# Signal Type Taxonomy
# ============================================================================

class LearningSignalType(str, Enum):
    """Categories of learning signals extracted from execution data."""

    # Prompt improvement signals
    PROMPT_STRUCTURE_CLARITY = "prompt_structure_clarity"
    PROMPT_MISSING_CONTEXT = "prompt_missing_context"
    PROMPT_AMBIGUOUS_INSTRUCTIONS = "prompt_ambiguous_instructions"

    # Routing adjustment signals
    ROUTING_MISALIGNMENT = "routing_misalignment"
    ROUTING_MISSING_CAPABILITY = "routing_missing_capability"
    ROUTING_Overspecialization = "routing_overspecialization"

    # Tool preference signals
    TOOL_PREFERENCE_EMERGENT = "tool_preference_emergent"
    TOOL_AVOIDANCE_PATTERN = "tool_avoidance_pattern"
    TOOL_INEFFICIENCY = "tool_inefficiency"

    # Reasoning pattern signals
    REPEATED_UNRESOLVED_QUESTIONS = "repeated_unresolved_questions"
    REPEATED_CONTRADICTION = "repeated_contradiction"
    RISK_PATTERN_CRITICAL = "risk_pattern_critical"
    COHERENCE_DEGRADATION = "coherence_degradation"


class SignalStrength(str, Enum):
    """Confidence level in the learning signal."""
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    CONCLUSIVE = "conclusive"


class SignalSource(str, Enum):
    """Primary source of the learning signal."""
    EVALUATION_METRIC = "evaluation_metric"
    WORKSPACE_ENTRY = "workspace_entry"
    SYNTHESIS_OUTPUT = "synthesis_output"
    EXECUTION_OUTCOME = "execution_outcome"
    CROSS_EXECUTION_PATTERN = "cross_execution_pattern"


# ============================================================================
# Signal Creation Models
# ============================================================================

class LearningSignalCreate(BaseModel):
    """Create a new learning signal."""
    signal_type: LearningSignalType
    strength: SignalStrength
    source: SignalSource
    scope_type: str  # "agent", "workflow", "routing", "tool"
    scope_id: str  # Specific agent ID, workflow ID, etc.

    # Evidence tracking
    evidence_count: int = Field(default=1, ge=1, description="Number of observations")
    supporting_execution_ids: List[str] = Field(default_factory=list, description="Executions that support this signal")
    conflicting_execution_ids: List[str] = Field(default_factory=list, description="Executions that contradict this signal")

    # Signal content
    title: str = Field(..., description="Human-readable signal title")
    description: str = Field(..., description="Detailed description of the signal")
    proposed_action: Optional[str] = Field(None, description="Suggested adaptation action")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Salience (derived from source entry importance)
    salience: str = Field(default="medium", description="low|medium|high|critical")


class LearningSignalRead(BaseModel):
    """A learning signal read from the database."""
    signal_id: str
    signal_type: LearningSignalType
    strength: SignalStrength
    source: SignalSource
    scope_type: str
    scope_id: str

    evidence_count: int
    supporting_execution_ids: List[str]
    conflicting_execution_ids: List[str]

    title: str
    description: str
    proposed_action: Optional[str]
    metadata: Dict[str, Any]

    salience: str
    status: str  # "pending", "acknowledged", "incorporated", "rejected"

    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None


class LearningSignalUpdate(BaseModel):
    """Update a learning signal."""
    strength: Optional[SignalStrength] = None
    evidence_count: Optional[int] = None
    supporting_execution_ids: Optional[List[str]] = None
    conflicting_execution_ids: Optional[List[str]] = None
    proposed_action: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# ============================================================================
# Signal Extraction Models
# ============================================================================

class ExtractionRule(BaseModel):
    """A rule for extracting a learning signal from data."""
    signal_type: LearningSignalType
    name: str
    description: str

    # Determination criteria
    min_evidence_count: int = Field(default=3, ge=1, description="Minimum observations needed")
    min_importance: str = Field(default="high", description="Minimum entry importance")
    allowed_source_types: List[str] = Field(default_factory=lambda: ["tool", "system", "agent"])

    # Threshold conditions
    metric_thresholds: Dict[str, float] = Field(default_factory=dict, description="Evaluation metric thresholds")
    pattern_conditions: Dict[str, Any] = Field(default_factory=dict, description="Pattern matching conditions")

    # Weighting
    provenance_weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "tool": 1.0,
            "system": 1.0,
            "agent": 0.7,
            "synthesis": 0.6,
            "user": 0.5
        },
        description="Weight multipliers by source type"
    )
    importance_weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "critical": 1.5,
            "high": 1.2,
            "medium": 1.0,
            "low": 0.5
        },
        description="Weight multipliers by importance"
    )


class ExtractionContext(BaseModel):
    """Context provided to the signal extraction process."""
    execution_id: Optional[str] = None
    agent_id: Optional[str] = None
    workflow_id: Optional[str] = None
    time_window_hours: int = Field(default=168, description="Lookback window (default 1 week)")
    min_execution_count: int = Field(default=3, description="Minimum executions for pattern detection")


class ExtractionResult(BaseModel):
    """Result of signal extraction."""
    signals_detected: List[LearningSignalCreate]
    execution_analyzed: int
    entries_analyzed: int
    evaluations_analyzed: int
    extraction_duration_ms: int


# ============================================================================
# Signal Aggregation Models
# ============================================================================

class AggregatedSignal(BaseModel):
    """An aggregated signal from multiple observations."""
    signal_type: LearningSignalType
    scope_type: str
    scope_id: str

    total_evidence: int
    unique_executions: int
    strength: SignalStrength

    first_observed: datetime
    last_observed: datetime

    representative_signals: List[str]  # IDs of underlying signals

    aggregated_metadata: Dict[str, Any] = Field(default_factory=dict)


class SignalCluster(BaseModel):
    """A cluster of related signals."""
    cluster_id: str
    theme: str  # e.g., "planning_failures", "tool_inefficiencies"
    signals: List[LearningSignalRead]

    # Cluster-level insights
    summary: str
    proposed_adaptations: List[str]
    priority_score: float  # 0-100


# ============================================================================
# Weighting Model
# ============================================================================

class SignalWeightCalculator(BaseModel):
    """Calculate signal weight based on provenance and salience."""

    @staticmethod
    def calculate_weight(
        importance: str,
        source_type: str,
        evidence_count: int,
        recency_hours: int
    ) -> float:
        """
        Calculate a signal weight (0.0 to 1.0+).

        Weight formula:
        base = (importance_weight * provenance_weight)
        adjusted = base * min(evidence_count / min_evidence, 2.0)
        recency_bonus = 1.0 + (1.0 - recency_hours / 168) * 0.3  # Up to +30% for recent signals
        final = adjusted * recency_bonus
        """
        importance_weights = {
            "critical": 1.5,
            "high": 1.2,
            "medium": 1.0,
            "low": 0.5
        }

        provenance_weights = {
            "tool": 1.0,
            "system": 1.0,
            "agent": 0.7,
            "synthesis": 0.6,
            "user": 0.5
        }

        imp_weight = importance_weights.get(importance, 1.0)
        prov_weight = provenance_weights.get(source_type, 0.7)

        base = imp_weight * prov_weight

        # Evidence bonus (caps at 2x)
        evidence_bonus = min(evidence_count / 3.0, 2.0)

        # Recency bonus (up to +30% for signals within 24 hours)
        recency_bonus = 1.0 + max(0, (168 - recency_hours) / 168) * 0.3

        return base * evidence_bonus * recency_bonus
