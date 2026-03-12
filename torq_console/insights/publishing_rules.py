"""
Insight Publishing Rules - Phase Insight Publishing & Agent Retrieval

Defines the quality gates and publication criteria for insights.

This module answers the key questions for insight publication:
- What source types are allowed?
- What confidence threshold is required?
- What provenance is required?
- What freshness window applies?
- What quality checks must pass?
- What conflicts block publication?
- When should an existing insight be superseded?
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .models import (
    InsightType,
    InsightLifecycleState,
    InsightSourceType,
    QualityGateResult,
    Insight,
    InsightCreate,
    PublishingRule,
    PublishingCriteria,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Quality Gate Definitions
# ============================================================================

class QualityGateConfig(BaseModel):
    """
    Configuration for a single quality gate.
    """

    name: str
    description: str

    # Thresholds
    min_confidence: float = 0.7
    min_validation_score: float = 0.7
    min_applicability: float = 0.6

    # Evidence requirements
    min_source_count: int = 1
    min_execution_count: int = 0
    require_success_rate: bool = False
    min_success_rate: float = 0.6

    # Freshness
    max_evidence_age_days: Optional[int] = None
    require_recent_validation: bool = False
    validation_window_days: int = 30


# Built-in quality gates for each insight type
QUALITY_GATES: Dict[InsightType, QualityGateConfig] = {
    InsightType.STRATEGIC_INSIGHT: QualityGateConfig(
        name="strategic_insight_gate",
        description="Quality gate for strategic insights",
        min_confidence=0.75,
        min_validation_score=0.70,
        min_applicability=0.70,
        min_source_count=2,
        min_execution_count=5,
        max_evidence_age_days=90,
    ),

    InsightType.REUSABLE_PLAYBOOK: QualityGateConfig(
        name="reusable_playbook_gate",
        description="Quality gate for reusable playbooks",
        min_confidence=0.80,
        min_validation_score=0.75,
        min_applicability=0.60,
        min_source_count=1,
        min_execution_count=3,
        require_success_rate=True,
        min_success_rate=0.70,
    ),

    InsightType.VALIDATED_FINDING: QualityGateConfig(
        name="validated_finding_gate",
        description="Quality gate for validated findings",
        min_confidence=0.85,
        min_validation_score=0.80,
        min_applicability=0.50,
        min_source_count=1,
        min_execution_count=10,
        require_success_rate=True,
        min_success_rate=0.75,
    ),

    InsightType.ARCHITECTURE_DECISION: QualityGateConfig(
        name="architecture_decision_gate",
        description="Quality gate for architecture decisions",
        min_confidence=0.70,
        min_validation_score=0.65,
        min_applicability=0.60,
        min_source_count=1,
        min_execution_count=0,
    ),

    InsightType.BEST_PRACTICE: QualityGateConfig(
        name="best_practice_gate",
        description="Quality gate for best practices",
        min_confidence=0.75,
        min_validation_score=0.70,
        min_applicability=0.70,
        min_source_count=2,
        min_execution_count=5,
        max_evidence_age_days=180,
    ),

    InsightType.RISK_PATTERN: QualityGateConfig(
        name="risk_pattern_gate",
        description="Quality gate for risk patterns",
        min_confidence=0.70,
        min_validation_score=0.70,
        min_applicability=0.50,
        min_source_count=1,
        min_execution_count=3,
    ),

    InsightType.EXECUTION_LESSON: QualityGateConfig(
        name="execution_lesson_gate",
        description="Quality gate for execution lessons",
        min_confidence=0.70,
        min_validation_score=0.65,
        min_applicability=0.60,
        min_source_count=1,
        min_execution_count=1,
    ),

    InsightType.RESEARCH_SUMMARY: QualityGateConfig(
        name="research_summary_gate",
        description="Quality gate for research summaries",
        min_confidence=0.75,
        min_validation_score=0.70,
        min_applicability=0.60,
        min_source_count=1,
        min_execution_count=0,
        max_evidence_age_days=120,
    ),
}


# ============================================================================
# Publication Rules by Insight Type
# ============================================================================

def get_default_publishing_rules() -> List[PublishingRule]:
    """
    Get the default publishing rules for all insight types.
    """
    return [
        PublishingRule(
            name="strategic_insight_publication",
            description="Publication rules for strategic insights",
            applies_to_types=[InsightType.STRATEGIC_INSIGHT],
            min_confidence=0.75,
            min_validation_score=0.70,
            min_applicability=0.70,
            min_source_count=2,
            min_execution_count=5,
            allowed_source_types=[
                InsightSourceType.ARTIFACT,
                InsightSourceType.MEMORY,
                InsightSourceType.AGENT_GENERATED,
            ],
            supersede_on_conflict=True,
        ),

        PublishingRule(
            name="reusable_playbook_publication",
            description="Publication rules for reusable playbooks",
            applies_to_types=[InsightType.REUSABLE_PLAYBOOK],
            min_confidence=0.80,
            min_validation_score=0.75,
            min_applicability=0.60,
            min_source_count=1,
            min_execution_count=3,
            require_success_rate=True,
            min_success_rate=0.70,
            allowed_source_types=[
                InsightSourceType.ARTIFACT,
                InsightSourceType.MEMORY,
                InsightSourceType.MANUAL,
            ],
            supersede_on_conflict=True,
        ),

        PublishingRule(
            name="validated_finding_publication",
            description="Publication rules for validated findings",
            applies_to_types=[InsightType.VALIDATED_FINDING],
            min_confidence=0.85,
            min_validation_score=0.80,
            min_applicability=0.50,
            min_source_count=1,
            min_execution_count=10,
            require_success_rate=True,
            min_success_rate=0.75,
            allowed_source_types=[
                InsightSourceType.ARTIFACT,
                InsightSourceType.AGENT_GENERATED,
            ],
            supersede_on_conflict=True,
        ),

        PublishingRule(
            name="architecture_decision_publication",
            description="Publication rules for architecture decisions",
            applies_to_types=[InsightType.ARCHITECTURE_DECISION],
            min_confidence=0.70,
            min_validation_score=0.65,
            min_applicability=0.60,
            min_source_count=1,
            allowed_source_types=[
                InsightSourceType.MANUAL,
                InsightSourceType.AGENT_GENERATED,
            ],
            requires_manual_approval=True,
        ),

        PublishingRule(
            name="best_practice_publication",
            description="Publication rules for best practices",
            applies_to_types=[InsightType.BEST_PRACTICE],
            min_confidence=0.75,
            min_validation_score=0.70,
            min_applicability=0.70,
            min_source_count=2,
            min_execution_count=5,
            allowed_source_types=[
                InsightSourceType.ARTIFACT,
                InsightSourceType.MEMORY,
                InsightSourceType.MANUAL,
            ],
            supersede_on_conflict=True,
        ),

        PublishingRule(
            name="risk_pattern_publication",
            description="Publication rules for risk patterns",
            applies_to_types=[InsightType.RISK_PATTERN],
            min_confidence=0.70,
            min_validation_score=0.70,
            min_applicability=0.50,
            min_source_count=1,
            min_execution_count=3,
            allowed_source_types=[
                InsightSourceType.ARTIFACT,
                InsightSourceType.MEMORY,
            ],
            supersede_on_conflict=False,  # Don't supersede risk warnings
        ),

        PublishingRule(
            name="execution_lesson_publication",
            description="Publication rules for execution lessons",
            applies_to_types=[InsightType.EXECUTION_LESSON],
            min_confidence=0.70,
            min_validation_score=0.65,
            min_applicability=0.60,
            min_source_count=1,
            min_execution_count=1,
            allowed_source_types=[
                InsightSourceType.ARTIFACT,
                InsightSourceType.MEMORY,
            ],
            supersede_on_conflict=False,
        ),

        PublishingRule(
            name="research_summary_publication",
            description="Publication rules for research summaries",
            applies_to_types=[InsightType.RESEARCH_SUMMARY],
            min_confidence=0.75,
            min_validation_score=0.70,
            min_applicability=0.60,
            min_source_count=1,
            allowed_source_types=[
                InsightSourceType.ARTIFACT,
                InsightSourceType.AGENT_GENERATED,
            ],
            supersede_on_conflict=True,
        ),
    ]


# ============================================================================
# Quality Gate Evaluation
# ============================================================================

class PublicationEligibilityChecker:
    """
    Evaluates whether an insight meets publication criteria.
    """

    def __init__(
        self,
        quality_gates: Optional[Dict[InsightType, QualityGateConfig]] = None,
        publishing_rules: Optional[List[PublishingRule]] = None
    ):
        """
        Initialize the checker with custom rules if provided.
        """
        self.quality_gates = quality_gates or QUALITY_GATES
        self.publishing_rules = publishing_rules or get_default_publishing_rules()

    def check_eligibility(
        self,
        insight_create: InsightCreate,
        as_of_date: Optional[datetime] = None
    ) -> List[QualityGateResult]:
        """
        Check if an insight meets all quality gates for publication.

        Returns a list of gate results. All must pass for publication.
        """
        as_of_date = as_of_date or datetime.now()
        results = []

        # Get the applicable quality gate for this insight type
        gate_config = self.quality_gates.get(
            insight_create.insight_type,
            QUALITY_GATES[InsightType.STRATEGIC_INSIGHT]  # Default
        )

        # Check confidence threshold
        results.append(self._check_confidence(
            insight_create.quality.confidence_score,
            gate_config.min_confidence
        ))

        # Check validation score
        results.append(self._check_validation_score(
            insight_create.quality.validation_score,
            gate_config.min_validation_score
        ))

        # Check applicability
        results.append(self._check_applicability(
            insight_create.quality.applicability_score,
            gate_config.min_applicability
        ))

        # Check source count
        results.append(self._check_source_count(
            insight_create.quality.source_count,
            gate_config.min_source_count
        ))

        # Check execution count
        results.append(self._check_execution_count(
            insight_create.quality.execution_count,
            gate_config.min_execution_count
        ))

        # Check success rate if required
        if gate_config.require_success_rate:
            results.append(self._check_success_rate(
                insight_create.quality.success_rate,
                gate_config.min_success_rate
            ))

        # Check evidence freshness
        if gate_config.max_evidence_age_days:
            results.append(self._check_evidence_freshness(
                insight_create.quality.evidence_cutoff_at,
                gate_config.max_evidence_age_days,
                as_of_date
            ))

        # Check recent validation if required
        if gate_config.require_recent_validation:
            results.append(self._check_recent_validation(
                insight_create.quality.last_validated_at,
                gate_config.validation_window_days,
                as_of_date
            ))

        return results

    def _check_confidence(
        self,
        actual: float,
        threshold: float
    ) -> QualityGateResult:
        """Check confidence threshold."""
        passed = actual >= threshold
        return QualityGateResult(
            gate_name="confidence_threshold",
            passed=passed,
            score=actual,
            threshold=threshold,
            reason=f"Confidence {actual:.2f} >= {threshold:.2f}"
                if passed else f"Confidence {actual:.2f} < {threshold:.2f}"
        )

    def _check_validation_score(
        self,
        actual: float,
        threshold: float
    ) -> QualityGateResult:
        """Check validation score threshold."""
        passed = actual >= threshold
        return QualityGateResult(
            gate_name="validation_score_threshold",
            passed=passed,
            score=actual,
            threshold=threshold,
            reason=f"Validation score {actual:.2f} >= {threshold:.2f}"
                if passed else f"Validation score {actual:.2f} < {threshold:.2f}"
        )

    def _check_applicability(
        self,
        actual: float,
        threshold: float
    ) -> QualityGateResult:
        """Check applicability threshold."""
        passed = actual >= threshold
        return QualityGateResult(
            gate_name="applicability_threshold",
            passed=passed,
            score=actual,
            threshold=threshold,
            reason=f"Applicability {actual:.2f} >= {threshold:.2f}"
                if passed else f"Applicability {actual:.2f} < {threshold:.2f}"
        )

    def _check_source_count(
        self,
        actual: int,
        threshold: int
    ) -> QualityGateResult:
        """Check source count threshold."""
        passed = actual >= threshold
        return QualityGateResult(
            gate_name="source_count_threshold",
            passed=passed,
            score=float(actual),
            threshold=float(threshold),
            reason=f"Source count {actual} >= {threshold}"
                if passed else f"Source count {actual} < {threshold}"
        )

    def _check_execution_count(
        self,
        actual: int,
        threshold: int
    ) -> QualityGateResult:
        """Check execution count threshold."""
        passed = actual >= threshold
        return QualityGateResult(
            gate_name="execution_count_threshold",
            passed=passed,
            score=float(actual),
            threshold=float(threshold),
            reason=f"Execution count {actual} >= {threshold}"
                if passed else f"Execution count {actual} < {threshold}"
        )

    def _check_success_rate(
        self,
        actual: Optional[float],
        threshold: float
    ) -> QualityGateResult:
        """Check success rate threshold."""
        if actual is None:
            return QualityGateResult(
                gate_name="success_rate_threshold",
                passed=False,
                score=None,
                threshold=threshold,
                reason="Success rate not provided"
            )

        passed = actual >= threshold
        return QualityGateResult(
            gate_name="success_rate_threshold",
            passed=passed,
            score=actual,
            threshold=threshold,
            reason=f"Success rate {actual:.2f} >= {threshold:.2f}"
                if passed else f"Success rate {actual:.2f} < {threshold:.2f}"
        )

    def _check_evidence_freshness(
        self,
        evidence_cutoff: Optional[datetime],
        max_age_days: int,
        as_of_date: datetime
    ) -> QualityGateResult:
        """Check evidence freshness."""
        if evidence_cutoff is None:
            return QualityGateResult(
                gate_name="evidence_freshness",
                passed=False,
                score=None,
                threshold=float(max_age_days),
                reason="Evidence cutoff date not provided"
            )

        age_days = (as_of_date - evidence_cutoff).days
        passed = age_days <= max_age_days
        return QualityGateResult(
            gate_name="evidence_freshness",
            passed=passed,
            score=float(age_days),
            threshold=float(max_age_days),
            reason=f"Evidence age {age_days} days <= {max_age_days} days"
                if passed else f"Evidence age {age_days} days > {max_age_days} days"
        )

    def _check_recent_validation(
        self,
        last_validated: Optional[datetime],
        window_days: int,
        as_of_date: datetime
    ) -> QualityGateResult:
        """Check recent validation."""
        if last_validated is None:
            return QualityGateResult(
                gate_name="recent_validation",
                passed=False,
                score=None,
                threshold=float(window_days),
                reason="No validation date provided"
            )

        days_since_validation = (as_of_date - last_validated).days
        passed = days_since_validation <= window_days
        return QualityGateResult(
            gate_name="recent_validation",
            passed=passed,
            score=float(days_since_validation),
            threshold=float(window_days),
            reason=f"Validated {days_since_validation} days ago <= {window_days} days"
                if passed else f"Validated {days_since_validation} days ago > {window_days} days"
        )

    def passes_all_gates(
        self,
        gate_results: List[QualityGateResult]
    ) -> bool:
        """Check if all quality gates passed."""
        return all(result.passed for result in gate_results)

    def get_failed_gates(
        self,
        gate_results: List[QualityGateResult]
    ) -> List[QualityGateResult]:
        """Get list of failed quality gates."""
        return [result for result in gate_results if not result.passed]


# ============================================================================
# Publication Criteria Configuration
# ============================================================================

def get_default_publishing_criteria() -> PublishingCriteria:
    """
    Get the default publishing criteria configuration.
    """
    return PublishingCriteria(
        rules=get_default_publishing_rules(),
        default_lifecycle_path=[
            InsightLifecycleState.DRAFT,
            InsightLifecycleState.CANDIDATE,
            InsightLifecycleState.VALIDATED,
            InsightLifecycleState.PUBLISHED,
        ],
        enable_conflict_detection=True,
        conflict_similarity_threshold=0.85,
        auto_supersede_threshold=0.90,
    )


# ============================================================================
# Lifecycle Transition Rules
# ============================================================================

class LifecycleTransition(BaseModel):
    """
    A valid transition between lifecycle states.
    """

    from_state: InsightLifecycleState
    to_state: InsightLifecycleState
    requires_approval: bool = False
    requires_quality_check: bool = False
    auto_transition: bool = False


# Valid lifecycle transitions
LIFECYCLE_TRANSITIONS: List[LifecycleTransition] = [
    # Draft to Candidate (submission for review)
    LifecycleTransition(
        from_state=InsightLifecycleState.DRAFT,
        to_state=InsightLifecycleState.CANDIDATE,
        requires_quality_check=True,
    ),

    # Candidate to Validated (passed quality gates)
    LifecycleTransition(
        from_state=InsightLifecycleState.CANDIDATE,
        to_state=InsightLifecycleState.VALIDATED,
        requires_quality_check=True,
    ),

    # Validated to Published (release for agent retrieval)
    LifecycleTransition(
        from_state=InsightLifecycleState.VALIDATED,
        to_state=InsightLifecycleState.PUBLISHED,
        requires_approval=False,  # Auto-approved if validated
        auto_transition=True,
    ),

    # Draft to Published (fast-track for high-confidence insights)
    LifecycleTransition(
        from_state=InsightLifecycleState.DRAFT,
        to_state=InsightLifecycleState.PUBLISHED,
        requires_quality_check=True,
        requires_approval=False,
    ),

    # Published to Superseded (replaced by newer version)
    LifecycleTransition(
        from_state=InsightLifecycleState.PUBLISHED,
        to_state=InsightLifecycleState.SUPERSEDED,
        auto_transition=True,
    ),

    # Published to Archived (no longer relevant)
    LifecycleTransition(
        from_state=InsightLifecycleState.PUBLISHED,
        to_state=InsightLifecycleState.ARCHIVED,
        requires_approval=True,
    ),

    # Superseded to Archived
    LifecycleTransition(
        from_state=InsightLifecycleState.SUPERSEDED,
        to_state=InsightLifecycleState.ARCHIVED,
        auto_transition=True,
    ),

    # Any state to Archived (deprecated)
    LifecycleTransition(
        from_state=InsightLifecycleState.DRAFT,
        to_state=InsightLifecycleState.ARCHIVED,
        auto_transition=True,
    ),
    LifecycleTransition(
        from_state=InsightLifecycleState.CANDIDATE,
        to_state=InsightLifecycleState.ARCHIVED,
        auto_transition=True,
    ),
    LifecycleTransition(
        from_state=InsightLifecycleState.VALIDATED,
        to_state=InsightLifecycleState.ARCHIVED,
        requires_approval=True,
    ),
]


def get_valid_transitions(
    from_state: InsightLifecycleState
) -> List[LifecycleTransition]:
    """
    Get valid transitions from a given state.
    """
    return [
        transition for transition in LIFECYCLE_TRANSITIONS
        if transition.from_state == from_state
    ]


def is_transition_valid(
    from_state: InsightLifecycleState,
    to_state: InsightLifecycleState
) -> bool:
    """
    Check if a transition between states is valid.
    """
    return any(
        transition.from_state == from_state and transition.to_state == to_state
        for transition in LIFECYCLE_TRANSITIONS
    )


def get_transition(
    from_state: InsightLifecycleState,
    to_state: InsightLifecycleState
) -> Optional[LifecycleTransition]:
    """
    Get the transition rule between two states.
    """
    for transition in LIFECYCLE_TRANSITIONS:
        if transition.from_state == from_state and transition.to_state == to_state:
            return transition
    return None
