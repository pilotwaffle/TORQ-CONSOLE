"""
Phase 4G: Pattern Aggregation - Aggregation Rules Module

Defines rules for aggregating observations into patterns, quality thresholds,
and lifecycle transitions for patterns.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


# Import from pattern_models
from .pattern_models import (
    PatternType,
    PatternLifecycleState,
    PatternSourceType,
    PatternCreate,
    PatternUpdate,
    Pattern,
    PatternSourceReference,
    PatternQualityMetrics,
    PatternObservation,
    AggregationEligibilityRule,
    PatternLineageRequirement,
    AggregationCriteria,
)


# ============================================================================
# Aggregation Eligibility Rules by Pattern Type
# ============================================================================

class PatternTypeEligibility(BaseModel):
    """
    Eligibility requirements specific to each pattern type.
    """

    pattern_type: PatternType

    # Minimum observations
    min_observations: int = Field(default=3, ge=2, description="Minimum observations required")
    min_unique_executions: int = Field(default=2, ge=2, description="Minimum distinct executions")
    min_time_span_days: int = Field(default=7, ge=1, description="Minimum observation time span")

    # Source diversity
    require_multiple_sources: bool = Field(default=True, description="Need multiple source types")
    min_source_types: int = Field(default=2, ge=1, description="Minimum source types")

    # Quality thresholds
    min_confidence: float = Field(default=0.60, ge=0.0, le=1.0)
    min_stability: float = Field(default=0.70, ge=0.0, le=1.0)
    min_consistency: float = Field(default=0.65, ge=0.0, le=1.0)


# Default eligibility rules for each pattern type
DEFAULT_ELIGIBILITY_RULES: Dict[PatternType, PatternTypeEligibility] = {
    PatternType.EXECUTION_PATTERN: PatternTypeEligibility(
        pattern_type=PatternType.EXECUTION_PATTERN,
        min_observations=3,
        min_unique_executions=2,
        min_time_span_days=7,
        min_confidence=0.60,
        min_stability=0.70,
    ),

    PatternType.FAILURE_PATTERN: PatternTypeEligibility(
        pattern_type=PatternType.FAILURE_PATTERN,
        min_observations=2,
        min_unique_executions=2,
        min_time_span_days=14,
        min_confidence=0.70,
        min_stability=0.75,
    ),

    PatternType.RECOVERY_PATTERN: PatternTypeEligibility(
        pattern_type=PatternType.RECOVERY_PATTERN,
        min_observations=2,
        min_unique_executions=2,
        min_time_span_days=7,
        min_confidence=0.65,
        min_stability=0.70,
    ),

    PatternType.COLLABORATION_PATTERN: PatternTypeEligibility(
        pattern_type=PatternType.COLLABORATION_PATTERN,
        min_observations=4,
        min_unique_executions=3,
        min_time_span_days=14,
        min_confidence=0.65,
        min_stability=0.70,
        min_consistency=0.70,
    ),

    PatternType.DECISION_PATTERN: PatternTypeEligibility(
        pattern_type=PatternType.DECISION_PATTERN,
        min_observations=5,
        min_unique_executions=3,
        min_time_span_days=14,
        min_confidence=0.70,
        min_stability=0.75,
        min_consistency=0.70,
    ),

    PatternType.RETRIEVAL_PATTERN: PatternTypeEligibility(
        pattern_type=PatternType.RETRIEVAL_PATTERN,
        min_observations=3,
        min_unique_executions=2,
        min_time_span_days=7,
        min_confidence=0.60,
        min_stability=0.70,
    ),

    PatternType.QUALITY_PATTERN: PatternTypeEligibility(
        pattern_type=PatternType.QUALITY_PATTERN,
        min_observations=4,
        min_unique_executions=3,
        min_time_span_days=14,
        min_confidence=0.70,
        min_stability=0.75,
    ),

    PatternType.RISK_PATTERN: PatternTypeEligibility(
        pattern_type=PatternType.RISK_PATTERN,
        min_observations=2,
        min_unique_executions=2,
        min_time_span_days=21,
        min_confidence=0.70,
        min_stability=0.70,
    ),

    PatternType.DOMAIN_PATTERN: PatternTypeEligibility(
        pattern_type=PatternType.DOMAIN_PATTERN,
        min_observations=3,
        min_unique_executions=2,
        min_time_span_days=14,
        min_confidence=0.65,
        min_stability=0.70,
    ),

    PatternType.TEMPORAL_PATTERN: PatternTypeEligibility(
        pattern_type=PatternType.TEMPORAL_PATTERN,
        min_observations=3,
        min_unique_executions=2,
        min_time_span_days=30,
        min_confidence=0.70,
        min_stability=0.80,
    ),

    PatternType.RESOURCE_PATTERN: PatternTypeEligibility(
        pattern_type=PatternType.RESOURCE_PATTERN,
        min_observations=3,
        min_unique_executions=2,
        min_time_span_days=14,
        min_confidence=0.65,
        min_stability=0.70,
    ),
}


def get_eligibility_rules(pattern_type: PatternType) -> PatternTypeEligibility:
    """Get eligibility rules for a pattern type."""
    return DEFAULT_ELIGIBILITY_RULES.get(
        pattern_type,
        PatternTypeEligibility(pattern_type=pattern_type)  # Default
    )


# ============================================================================
# Quality Thresholds
# ============================================================================

class PatternQualityThresholds(BaseModel):
    """
    Quality thresholds for pattern lifecycle transitions.
    """

    # Candidate → Observed
    candidate_to_observed_min_confidence: float = Field(default=0.50, ge=0.0, le=1.0)
    candidate_to_observed_min_observations: int = Field(default=2, ge=1)

    # Observed → Validated
    observed_to_validated_min_confidence: float = Field(default=0.70, ge=0.0, le=1.0)
    observed_to_validated_min_stability: float = Field(default=0.70, ge=0.0, le=1.0)
    observed_to_validated_min_observations: int = Field(default=3, ge=2)

    # Validated → Active
    validated_to_active_min_confidence: float = Field(default=0.75, ge=0.0, le=1.0)
    validated_to_active_recent_observation_days: int = Field(default=30, ge=1)

    # Active → Superseded
    active_to_superseded_replaced_by_better: bool = True
    active_to_superseded_min_improvement: float = Field(default=0.10, ge=0.0, le=1.0)

    # Expiration
    candidate_max_age_days: int = Field(default=30, ge=1)
    observed_max_age_days: int = Field(default=60, ge=1)
    validated_max_age_days: int = Field(default=90, ge=1)
    active_max_age_days: int = Field(default=120, ge=1)


# Default thresholds
DEFAULT_QUALITY_THRESHOLDS = PatternQualityThresholds()


# ============================================================================
# Lifecycle Transition Rules
# ============================================================================

class PatternLifecycleTransition(BaseModel):
    """
    Valid lifecycle transition for patterns.
    """

    from_state: PatternLifecycleState
    to_state: PatternLifecycleState
    requires_approval: bool = False

    # Requirements
    min_confidence: Optional[float] = None
    min_observations: Optional[int] = None
    min_days_in_state: Optional[int] = None

    # Conditions
    allowed_reasons: List[str] = Field(default_factory=list)
    requires_recent_observation: bool = False


# Valid lifecycle transitions
LIFECYCLE_TRANSITIONS: List[PatternLifecycleTransition] = [
    # Candidate transitions (sequential: candidate → observed → validated → active)
    PatternLifecycleTransition(
        from_state=PatternLifecycleState.CANDIDATE,
        to_state=PatternLifecycleState.OBSERVED,
        min_observations=2,
        min_confidence=0.50,
    ),
    PatternLifecycleTransition(
        from_state=PatternLifecycleState.CANDIDATE,
        to_state=PatternLifecycleState.ARCHIVED,
        allowed_reasons=["insufficient_observations", "low_quality", "expired"],
    ),

    # Observed transitions
    PatternLifecycleTransition(
        from_state=PatternLifecycleState.OBSERVED,
        to_state=PatternLifecycleState.VALIDATED,
        min_observations=3,
        min_confidence=0.70,
    ),
    PatternLifecycleTransition(
        from_state=PatternLifecycleState.OBSERVED,
        to_state=PatternLifecycleState.ARCHIVED,
        allowed_reasons=["insufficient_observations", "stale"],
    ),

    # Validated transitions
    PatternLifecycleTransition(
        from_state=PatternLifecycleState.VALIDATED,
        to_state=PatternLifecycleState.ACTIVE,
        min_confidence=0.75,
        requires_recent_observation=True,
    ),
    PatternLifecycleTransition(
        from_state=PatternLifecycleState.VALIDATED,
        to_state=PatternLifecycleState.SUPERSEDED,
        requires_approval=True,
    ),
    PatternLifecycleTransition(
        from_state=PatternLifecycleState.VALIDATED,
        to_state=PatternLifecycleState.ARCHIVED,
        allowed_reasons=["stale", "superseded"],
    ),

    # Active transitions
    PatternLifecycleTransition(
        from_state=PatternLifecycleState.ACTIVE,
        to_state=PatternLifecycleState.SUPERSEDED,
        requires_approval=True,
    ),
    PatternLifecycleTransition(
        from_state=PatternLifecycleState.ACTIVE,
        to_state=PatternLifecycleState.ARCHIVED,
        allowed_reasons=["stale", "deprecated"],
    ),

    # Superseded transitions
    PatternLifecycleTransition(
        from_state=PatternLifecycleState.SUPERSEDED,
        to_state=PatternLifecycleState.ARCHIVED,
        allowed_reasons=["expired"],
    ),
]


def is_transition_valid(
    from_state: PatternLifecycleState,
    to_state: PatternLifecycleState
) -> bool:
    """Check if a lifecycle transition is valid."""
    for transition in LIFECYCLE_TRANSITIONS:
        if transition.from_state == from_state and transition.to_state == to_state:
            return True
    return False


def get_valid_transitions(from_state: PatternLifecycleState) -> List[PatternLifecycleState]:
    """Get all valid target states for a given source state."""
    return [
        t.to_state
        for t in LIFECYCLE_TRANSITIONS
        if t.from_state == from_state
    ]


# ============================================================================
# Aggregation Eligibility Checker
# ============================================================================

class AggregationEligibilityChecker:
    """
    Checks if observations meet criteria for pattern aggregation.
    """

    def __init__(
        self,
        eligibility_rules: Optional[Dict[PatternType, PatternTypeEligibility]] = None,
        quality_thresholds: Optional[PatternQualityThresholds] = None
    ):
        """Initialize the checker."""
        self.eligibility_rules = eligibility_rules or DEFAULT_ELIGIBILITY_RULES
        self.quality_thresholds = quality_thresholds or DEFAULT_QUALITY_THRESHOLDS

    def check_eligibility(
        self,
        pattern_type: PatternType,
        observations: List[PatternObservation]
    ) -> Dict[str, Any]:
        """
        Check if observations meet aggregation criteria.

        Returns:
            Dictionary with eligibility results and reasons
        """
        rules = self.eligibility_rules.get(pattern_type)

        results = {
            "is_eligible": True,
            "failed_criteria": [],
            "scores": {},
            "recommendations": [],
        }

        # Check observation count
        observation_count = len(observations)
        results["scores"]["observation_count"] = observation_count

        if observation_count < rules.min_observations:
            results["is_eligible"] = False
            results["failed_criteria"].append(
                f"Insufficient observations: {observation_count} < {rules.min_observations}"
            )

        # Check unique execution count
        unique_executions = len(set(obs.execution_id for obs in observations if obs.execution_id))
        results["scores"]["unique_executions"] = unique_executions

        if unique_executions < rules.min_unique_executions:
            results["is_eligible"] = False
            results["failed_criteria"].append(
                f"Insufficient unique executions: {unique_executions} < {rules.min_unique_executions}"
            )

        # Check time span
        if observations:
            times = [obs.observed_at for obs in observations]
            time_span = (max(times) - min(times)).days
            results["scores"]["time_span_days"] = time_span

            if time_span < rules.min_time_span_days:
                results["is_eligible"] = False
                results["failed_criteria"].append(
                    f"Insufficient time span: {time_span} < {rules.min_time_span_days} days"
                )

        # Check source diversity
        source_types = set(obs.source_type for obs in observations)
        results["scores"]["source_type_count"] = len(source_types)

        if rules.require_multiple_sources:
            if len(source_types) < rules.min_source_types:
                results["is_eligible"] = False
                results["failed_criteria"].append(
                    f"Insufficient source diversity: {len(source_types)} types < {rules.min_source_types}"
                )

        # Check confidence
        avg_confidence = sum(obs.observation_confidence for obs in observations) / len(observations)
        results["scores"]["avg_confidence"] = avg_confidence

        if avg_confidence < rules.min_confidence:
            results["is_eligible"] = False
            results["failed_criteria"].append(
                f"Insufficient confidence: {avg_confidence:.2f} < {rules.min_confidence}"
            )

        # Add recommendations
        if results["is_eligible"]:
            results["recommendations"].append("Pattern meets all eligibility criteria")
        else:
            if observation_count < rules.min_observations:
                results["recommendations"].append(
                    f"Collect {rules.min_observations - observation_count} more observations"
                )
            if unique_executions < rules.min_unique_executions:
                results["recommendations"].append(
                    f"Observe pattern in {rules.min_unique_executions - unique_executions} more executions"
                )

        return results


# ============================================================================
# Lifecycle Transition Validator
# ============================================================================

class PatternLifecycleValidator:
    """
    Validates lifecycle transitions for patterns.
    """

    def __init__(
        self,
        quality_thresholds: Optional[PatternQualityThresholds] = None
    ):
        """Initialize the validator."""
        self.quality_thresholds = quality_thresholds or DEFAULT_QUALITY_THRESHOLDS

    def validate_transition(
        self,
        pattern: Pattern,
        target_state: PatternLifecycleState,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a lifecycle transition for a pattern.

        Returns:
            Tuple of (is_valid, error_message)
        """
        from_state = pattern.lifecycle_state

        # Check if transition is allowed
        if not is_transition_valid(from_state, target_state):
            return False, f"Invalid transition from {from_state.value} to {target_state.value}"

        # Find the transition rule
        transition = next(
            (t for t in LIFECYCLE_TRANSITIONS
             if t.from_state == from_state and t.to_state == target_state),
            None
        )

        if transition is None:
            return False, "No transition rule found"

        # Check observation requirement
        if transition.min_observations:
            if pattern.quality.observation_count < transition.min_observations:
                return False, (
                    f"Insufficient observations: "
                    f"{pattern.quality.observation_count} < {transition.min_observations}"
                )

        # Check confidence requirement
        if transition.min_confidence:
            if pattern.quality.confidence_score < transition.min_confidence:
                return False, (
                    f"Insufficient confidence: "
                    f"{pattern.quality.confidence_score:.2f} < {transition.min_confidence}"
                )

        # Check recent observation for active state
        if transition.requires_recent_observation:
            days_since_observed = (datetime.now() - pattern.quality.last_observed_at).days
            threshold = self.quality_thresholds.validated_to_active_recent_observation_days

            if days_since_observed > threshold:
                return False, f"Pattern not recently observed: {days_since_observed}d > {threshold}d"

        return True, None

    def can_promote_to_state(
        self,
        pattern: Pattern,
        target_state: PatternLifecycleState
    ) -> Tuple[bool, Optional[str], List[str]]:
        """
        Check if pattern can be promoted to target state.

        Returns:
            Tuple of (can_promote, error_message, requirements)
        """
        requirements = []
        errors = []

        # Get eligibility rules for this pattern type
        rules = get_eligibility_rules(pattern.pattern_type)

        if target_state == PatternLifecycleState.OBSERVED:
            requirements.append(f"At least {rules.min_observations} observations")
            requirements.append(f"Confidence >= {rules.min_confidence}")

            if pattern.quality.observation_count < rules.min_observations:
                errors.append(f"Need {rules.min_observations - pattern.quality.observation_count} more observations")

            if pattern.quality.confidence_score < rules.min_confidence:
                errors.append(f"Confidence too low: {pattern.quality.confidence_score:.2f} < {rules.min_confidence}")

        elif target_state == PatternLifecycleState.VALIDATED:
            requirements.append(f"At least {rules.min_observations} observations")
            requirements.append(f"Confidence >= {rules.min_confidence}")
            requirements.append(f"Stability >= {rules.min_stability}")

            if pattern.quality.observation_count < rules.min_observations:
                errors.append(f"Need {rules.min_observations - pattern.quality.observation_count} more observations")

            if pattern.quality.confidence_score < rules.min_confidence:
                errors.append(f"Confidence too low: {pattern.quality.confidence_score:.2f} < {rules.min_confidence}")

            if pattern.quality.stability_score < rules.min_stability:
                errors.append(f"Stability too low: {pattern.quality.stability_score:.2f} < {rules.min_stability}")

        elif target_state == PatternLifecycleState.ACTIVE:
            requirements.append(f"Confidence >= {self.quality_thresholds.validated_to_active_min_confidence}")
            requirements.append(f"Observed within {self.quality_thresholds.validated_to_active_recent_observation_days} days")

            if pattern.quality.confidence_score < self.quality_thresholds.validated_to_active_min_confidence:
                errors.append(f"Confidence too low for active: {pattern.quality.confidence_score:.2f}")

            days_since_observed = (datetime.now() - pattern.quality.last_observed_at).days
            if days_since_observed > self.quality_thresholds.validated_to_active_recent_observation_days:
                errors.append(f"Last observed {days_since_observed} days ago, too stale for active")

        is_valid = len(errors) == 0

        return is_valid, None if is_valid else "; ".join(errors), requirements


# ============================================================================
# Convenience Functions
# ============================================================================

def get_default_eligibility_checker() -> AggregationEligibilityChecker:
    """Get the default eligibility checker."""
    return AggregationEligibilityChecker()


def get_default_lifecycle_validator() -> PatternLifecycleValidator:
    """Get the default lifecycle validator."""
    return PatternLifecycleValidator()


def check_pattern_eligibility(
    pattern_type: PatternType,
    observations: List[PatternObservation]
) -> Dict[str, Any]:
    """Check if observations are eligible for pattern aggregation."""
    checker = get_default_eligibility_checker()
    return checker.check_eligibility(pattern_type, observations)


def validate_pattern_transition(
    pattern: Pattern,
    target_state: PatternLifecycleState
) -> Tuple[bool, Optional[str]]:
    """Validate a pattern lifecycle transition."""
    validator = get_default_lifecycle_validator()
    return validator.validate_transition(pattern, target_state)
