"""
Phase 4G Milestone 3: Pattern Validation & Promotion Workflow

This module provides the governed workflow for validating and promoting
pattern candidates through lifecycle states.

Key Components:
- PatternValidationService: Evaluates candidates against validation thresholds
- PatternPromotionWorkflow: Manages lifecycle state transitions
- PatternConflictResolver: Detects and resolves duplicate/conflicting patterns
- PatternSupersessionHandler: Manages pattern supersession and replacement
- PatternAuditLogger: Logs all validation and promotion decisions

Flow:
candidate → validation → (reject/hold/promote) → observed → validated → active
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


# Import from pattern_models
from .pattern_models import (
    PatternType,
    PatternLifecycleState,
    PatternSourceType,
    Pattern,
    PatternCreate,
    PatternUpdate,
    PatternSourceReference,
    PatternQualityMetrics,
    PatternObservation,
    AggregationEligibilityRule,
    PatternLineageRequirement,
    AggregationCriteria,
)

# Import from aggregation_rules
from .aggregation_rules import (
    PatternTypeEligibility,
    DEFAULT_ELIGIBILITY_RULES,
    DEFAULT_QUALITY_THRESHOLDS,
    LIFECYCLE_TRANSITIONS,
    is_transition_valid,
    get_valid_transitions,
    AggregationEligibilityChecker,
    PatternLifecycleValidator,
    check_pattern_eligibility,
    validate_pattern_transition,
)

# Import from extraction
from .extraction import (
    PatternCandidate,
    PatternEvidence,
    RejectionReason,
    PatternRejectionRecord,
    PatternScoringService,
    PatternPersistenceService,
)


# ============================================================================
# Validation Outcome Models
# ============================================================================

class ValidationOutcome(str, Enum):
    """Possible outcomes of pattern validation."""
    PROMOTE = "promote"
    HOLD = "hold"
    REJECT = "reject"
    SUPERSEDED = "superseded"


class ValidationResult(BaseModel):
    """Result of validating a pattern candidate."""
    candidate_id: UUID
    pattern_type: PatternType
    outcome: ValidationOutcome

    # Scores at validation time
    recurrence_score: float
    confidence_score: float
    stability_score: float
    source_diversity_score: float
    temporal_consistency_score: float

    # Thresholds applied
    thresholds_applied: Dict[str, Any] = Field(default_factory=dict)

    # Rules that passed/failed
    passed_rules: List[str] = Field(default_factory=list)
    failed_rules: List[str] = Field(default_factory=list)

    # Decision reasoning
    reasoning: str = ""

    # Target state if promoting
    target_state: Optional[PatternLifecycleState] = None

    # Superseding pattern if applicable
    superseded_by_id: Optional[UUID] = None
    superseded_by_name: Optional[str] = None

    # Hold reason if applicable
    hold_reason: Optional[str] = None
    hold_until: Optional[datetime] = None

    # Rejection reason if applicable
    rejection_reason: Optional[RejectionReason] = None

    # Metadata
    validated_at: datetime = Field(default_factory=datetime.now)
    validator_version: str = "1.0.0"
    validated_by: str = "validation_service"


class PromotionRequest(BaseModel):
    """Request to promote a pattern candidate."""
    candidate_id: UUID
    current_state: PatternLifecycleState
    target_state: PatternLifecycleState

    # Validation context
    require_fresh_review: bool = False
    force_promotion: bool = False
    review_notes: Optional[str] = None

    # Requester
    requested_by: str = "system"
    requested_at: datetime = Field(default_factory=datetime.now)


class PromotionResult(BaseModel):
    """Result of a promotion attempt."""
    request_id: UUID = Field(default_factory=uuid4)
    candidate_id: UUID
    current_state: PatternLifecycleState
    requested_state: PatternLifecycleState
    actual_state: PatternLifecycleState

    # Outcome
    success: bool
    outcome: ValidationOutcome

    # Reasons
    promotion_reasons: List[str] = Field(default_factory=list)
    blocking_issues: List[str] = Field(default_factory=list)

    # Metadata
    promoted_at: datetime = Field(default_factory=datetime.now)
    promoted_by: str = Field(default="validation_workflow")


# ============================================================================
# Validation Thresholds
# ============================================================================

class ValidationThresholds(BaseModel):
    """Thresholds for validating pattern candidates."""
    # Minimum scores
    min_recurrence_score: float = Field(default=0.3, ge=0.0, le=1.0)
    min_confidence_score: float = Field(default=0.6, ge=0.0, le=1.0)
    min_stability_score: float = Field(default=0.6, ge=0.0, le=1.0)
    min_source_diversity_score: float = Field(default=0.3, ge=0.0, le=1.0)
    min_temporal_consistency_score: float = Field(default=0.5, ge=0.0, le=1.0)

    # Minimum evidence
    min_observation_count: int = Field(default=3, ge=2)
    min_unique_executions: int = Field(default=2, ge=2)
    min_distinct_sources: int = Field(default=2, ge=1)

    # Temporal requirements
    min_observation_span_days: int = Field(default=7, ge=1)
    max_days_since_last_observation: int = Field(default=90, ge=1)

    # Conflict detection
    max_similarity_to_existing: float = Field(default=0.85, ge=0.0, le=1.0)

    # Freshness
    max_candidate_age_days: int = Field(default=30, ge=1)


# ============================================================================
# Pattern Validation Service
# ============================================================================

class PatternValidationService:
    """
    Validates pattern candidates against governance thresholds.

    Checks:
    - Minimum recurrence, confidence, stability
    - Source diversity requirements
    - Temporal consistency and freshness
    - Evidence sufficiency
    - Conflict with existing patterns
    """

    def __init__(
        self,
        thresholds: Optional[ValidationThresholds] = None,
        quality_thresholds: Optional[PatternQualityThresholds] = None
    ):
        """Initialize the validation service."""
        self.thresholds = thresholds or ValidationThresholds()
        self.quality_thresholds = quality_thresholds or DEFAULT_QUALITY_THRESHOLDS

    def validate_candidate(
        self,
        candidate: PatternCandidate,
        existing_patterns: Optional[List[Pattern]] = None
    ) -> ValidationResult:
        """
        Validate a pattern candidate against all thresholds.

        Returns:
            ValidationResult with outcome and reasoning
        """
        passed_rules = []
        failed_rules = []

        # 1. Check minimum scores
        if candidate.recurrence_score >= self.thresholds.min_recurrence_score:
            passed_rules.append(f"recurrence_score {candidate.recurrence_score:.2f} >= {self.thresholds.min_recurrence_score}")
        else:
            failed_rules.append(
                f"recurrence_score {candidate.recurrence_score:.2f} < {self.thresholds.min_recurrence_score}"
            )

        if candidate.confidence_score >= self.thresholds.min_confidence_score:
            passed_rules.append(f"confidence_score {candidate.confidence_score:.2f} >= {self.thresholds.min_confidence_score}")
        else:
            failed_rules.append(
                f"confidence_score {candidate.confidence_score:.2f} < {self.thresholds.min_confidence_score}"
            )

        if candidate.stability_score >= self.thresholds.min_stability_score:
            passed_rules.append(f"stability_score {candidate.stability_score:.2f} >= {self.thresholds.min_stability_score}")
        else:
            failed_rules.append(
                f"stability_score {candidate.stability_score:.2f} < {self.thresholds.min_stability_score}"
            )

        if candidate.source_diversity_score >= self.thresholds.min_source_diversity_score:
            passed_rules.append(
                f"source_diversity {candidate.source_diversity_score:.2f} >= {self.thresholds.min_source_diversity_score}"
            )
        else:
            failed_rules.append(
                f"source_diversity {candidate.source_diversity_score:.2f} < {self.thresholds.min_source_diversity_score}"
            )

        # 2. Check evidence requirements
        obs_count = len(candidate.evidence)
        if obs_count >= self.thresholds.min_observation_count:
            passed_rules.append(f"observation_count {obs_count} >= {self.thresholds.min_observation_count}")
        else:
            failed_rules.append(f"observation_count {obs_count} < {self.thresholds.min_observation_count}")

        unique_execs = len(set(ev.execution_id for ev in candidate.evidence if ev.execution_id))
        if unique_execs >= self.thresholds.min_unique_executions:
            passed_rules.append(f"unique_executions {unique_execs} >= {self.thresholds.min_unique_executions}")
        else:
            failed_rules.append(f"unique_executions {unique_execs} < {self.thresholds.min_unique_executions}")

        distinct_sources = len(set(ev.source_type for ev in candidate.evidence))
        if distinct_sources >= self.thresholds.min_distinct_sources:
            passed_rules.append(f"distinct_sources {distinct_sources} >= {self.thresholds.min_distinct_sources}")
        else:
            failed_rules.append(f"distinct_sources {distinct_sources} < {self.thresholds.min_distinct_sources}")

        # 3. Check temporal requirements
        if candidate.quality and candidate.quality.observation_span_days >= self.thresholds.min_observation_span_days:
            passed_rules.append(
                f"observation_span {candidate.quality.observation_span_days}d >= {self.thresholds.min_observation_span_days}d"
            )
        else:
            span = candidate.quality.observation_span_days if candidate.quality else 0
            failed_rules.append(
                f"observation_span {span}d < {self.thresholds.min_observation_span_days}d"
            )

        # 4. Check freshness
        if candidate.quality:
            days_since_observed = (datetime.now() - candidate.quality.last_observed_at).days
            if days_since_observed <= self.thresholds.max_days_since_last_observation:
                passed_rules.append(
                    f"freshness: last_observed {days_since_observed}d ago <= {self.thresholds.max_days_since_last_observation}d"
                )
            else:
                failed_rules.append(
                    f"freshness: last_observed {days_since_observed}d ago > {self.thresholds.max_days_since_last_observation}d"
                )

        # 5. Check for conflicts with existing patterns
        conflict_detected = False
        superseded_by_id = None
        superseded_by_name = None

        if existing_patterns:
            conflict_result = self._check_conflicts(candidate, existing_patterns)
            if conflict_result["has_conflict"]:
                conflict_detected = True
                if conflict_result["superseded_by"]:
                    superseded_by_id = conflict_result["superseded_by"].id
                    superseded_by_name = conflict_result["superseded_by"].name
                    failed_rules.append(
                        f"superseded by existing pattern: {superseded_by_name}"
                    )
                else:
                    failed_rules.append("conflicts with existing pattern")

        # Determine outcome
        if not failed_rules and not conflict_detected:
            outcome = ValidationOutcome.PROMOTE
            reasoning = f"All {len(passed_rules)} validation rules passed. Candidate eligible for promotion."
            target_state = PatternLifecycleState.OBSERVED  # Default first promotion

        elif conflict_detected and superseded_by_id:
            outcome = ValidationOutcome.SUPERSEDED
            reasoning = f"Candidate is superseded by stronger pattern: {superseded_by_name}"
            target_state = None

        elif len(failed_rules) <= 2 and any("freshness" in f for f in failed_rules):
            # Hold for freshness issues only
            outcome = ValidationOutcome.HOLD
            reasoning = f"Held for: {', '.join(failed_rules)}. Accumulate more evidence."
            target_state = None

        else:
            outcome = ValidationOutcome.REJECT
            reasoning = f"Rejected. Failed rules: {', '.join(failed_rules)}"
            target_state = None

        return ValidationResult(
            candidate_id=candidate.id,
            pattern_type=candidate.pattern_type,
            outcome=outcome,
            recurrence_score=candidate.recurrence_score,
            confidence_score=candidate.confidence_score,
            stability_score=candidate.stability_score,
            source_diversity_score=candidate.source_diversity_score,
            temporal_consistency_score=candidate.temporal_consistency_score,
            thresholds_applied=self.thresholds.model_dump(),
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            reasoning=reasoning,
            target_state=target_state,
            superseded_by_id=superseded_by_id,
            superseded_by_name=superseded_by_name,
            hold_reason=failed_rules[0] if outcome == ValidationOutcome.HOLD and failed_rules else None,
            rejection_reason=RejectionReason.LOW_CONFIDENCE if outcome == ValidationOutcome.REJECT else None,
        )

    def _check_conflicts(
        self,
        candidate: PatternCandidate,
        existing_patterns: List[Pattern]
    ) -> Dict[str, Any]:
        """
        Check if candidate conflicts with existing patterns.

        Returns:
            Dict with conflict detection results
        """
        for existing in existing_patterns:
            # Same pattern type and domain
            if existing.pattern_type != candidate.pattern_type:
                continue

            if existing.domain != candidate.domain:
                continue

            # Check similarity
            similarity = self._calculate_pattern_similarity(candidate, existing)

            if similarity >= self.thresholds.max_similarity_to_existing:
                # Existing pattern is stronger (more observations, higher confidence)
                if existing.quality.confidence_score >= candidate.confidence_score:
                    return {
                        "has_conflict": True,
                        "conflicting_pattern": existing,
                        "superseded_by": existing,
                        "similarity": similarity,
                    }
                else:
                    # Candidate is stronger - would supersede existing
                    return {
                        "has_conflict": True,
                        "conflicting_pattern": existing,
                        "superseded_by": None,  # Candidate would supersede
                        "similarity": similarity,
                    }

        return {"has_conflict": False}

    def _calculate_pattern_similarity(
        self,
        candidate: PatternCandidate,
        existing: Pattern
    ) -> float:
        """Calculate similarity between candidate and existing pattern."""
        # Start with type match
        type_score = 1.0 if candidate.pattern_type == existing.pattern_type else 0.0

        # Domain match
        domain_score = 1.0 if candidate.domain == existing.domain else 0.0

        # Structure similarity
        struct_keys = set(candidate.structure.keys()) & set(existing.structure.keys())
        total_keys = set(candidate.structure.keys()) | set(existing.structure.keys())
        structure_score = len(struct_keys) / len(total_keys) if total_keys else 0.0

        # Weighted average
        return type_score * 0.3 + domain_score * 0.3 + structure_score * 0.4


# ============================================================================
# Pattern Promotion Workflow
# ============================================================================

class PatternPromotionWorkflow:
    """
    Manages pattern promotion through lifecycle states.

    Supported transitions (sequential):
    - candidate → observed
    - observed → validated
    - validated → active
    - active → superseded
    - any → archived (for termination)

    Transitions must follow the sequential path unless force=True is used.
    """

    def __init__(
        self,
        validation_service: Optional[PatternValidationService] = None,
        lifecycle_validator: Optional[PatternLifecycleValidator] = None
    ):
        """Initialize the promotion workflow."""
        self.validation_service = validation_service or PatternValidationService()
        self.lifecycle_validator = lifecycle_validator or PatternLifecycleValidator()

    def promote_candidate(
        self,
        candidate: PatternCandidate,
        target_state: Optional[PatternLifecycleState] = None,
        existing_patterns: Optional[List[Pattern]] = None,
        force: bool = False
    ) -> PromotionResult:
        """
        Promote a candidate through the lifecycle.

        Returns:
            PromotionResult with outcome and new state
        """
        # Start validation
        validation = self.validation_service.validate_candidate(candidate, existing_patterns)

        # If superseded, can't promote
        if validation.outcome == ValidationOutcome.SUPERSEDED:
            return PromotionResult(
                candidate_id=candidate.id,
                current_state=candidate.lifecycle_state,
                requested_state=target_state or PatternLifecycleState.OBSERVED,
                actual_state=candidate.lifecycle_state,
                success=False,
                outcome=validation.outcome,
                blocking_issues=[validation.reasoning],
            )

        # If rejected, can't promote unless forced
        if validation.outcome == ValidationOutcome.REJECT and not force:
            return PromotionResult(
                candidate_id=candidate.id,
                current_state=candidate.lifecycle_state,
                requested_state=target_state or PatternLifecycleState.OBSERVED,
                actual_state=candidate.lifecycle_state,
                success=False,
                outcome=validation.outcome,
                blocking_issues=validation.failed_rules,
            )

        # If held, can't promote unless forced
        if validation.outcome == ValidationOutcome.HOLD and not force:
            return PromotionResult(
                candidate_id=candidate.id,
                current_state=candidate.lifecycle_state,
                requested_state=target_state or PatternLifecycleState.OBSERVED,
                actual_state=candidate.lifecycle_state,
                success=False,
                outcome=validation.outcome,
                blocking_issues=[validation.hold_reason],
            )

        # Determine target state
        if target_state is None:
            target_state = validation.target_state or PatternLifecycleState.OBSERVED

        # Check if transition is valid
        # Build a minimal pattern for transition validation
        temp_pattern = Pattern(
            pattern_type=candidate.pattern_type,
            name=candidate.name,
            description=candidate.description or "",
            structure=candidate.structure or {},
            characteristics=candidate.characteristics or {},
            tags=candidate.tags or [],
            source_references=candidate.source_references or [],
            quality=candidate.quality or PatternQualityMetrics(
                confidence_score=candidate.confidence_score,
                stability_score=candidate.stability_score,
                consistency_score=candidate.temporal_consistency_score,
                observation_count=len(candidate.evidence),
                unique_execution_count=len(set(ev.execution_id for ev in candidate.evidence if ev.execution_id)),
                distinct_source_count=len(set(ev.source_type for ev in candidate.evidence)),
                first_observed_at=min((ev.observed_at for ev in candidate.evidence), default=datetime.now()),
                last_observed_at=max((ev.observed_at for ev in candidate.evidence), default=datetime.now()),
            ),
            lifecycle_state=candidate.lifecycle_state,
            domain=candidate.domain,
            scope=candidate.scope,
        )

        is_valid, error_msg = validate_pattern_transition(
            temp_pattern,
            target_state
        )

        if not is_valid and not force:
            return PromotionResult(
                candidate_id=candidate.id,
                current_state=candidate.lifecycle_state,
                requested_state=target_state,
                actual_state=candidate.lifecycle_state,
                success=False,
                outcome=ValidationOutcome.REJECT,
                blocking_issues=[error_msg],
            )

        # Promotion successful
        return PromotionResult(
            candidate_id=candidate.id,
            current_state=candidate.lifecycle_state,
            requested_state=target_state,
            actual_state=target_state,
            success=True,
            outcome=ValidationOutcome.PROMOTE,
            promotion_reasons=[validation.reasoning],
        )

    def promote_to_observed(
        self,
        candidate: PatternCandidate,
        force: bool = False
    ) -> PromotionResult:
        """Promote candidate to OBSERVED state."""
        return self.promote_candidate(
            candidate,
            target_state=PatternLifecycleState.OBSERVED,
            force=force
        )

    def promote_to_validated(
        self,
        candidate: PatternCandidate,
        force: bool = False
    ) -> PromotionResult:
        """Promote candidate to VALIDATED state."""
        return self.promote_candidate(
            candidate,
            target_state=PatternLifecycleState.VALIDATED,
            force=force
        )

    def promote_to_active(
        self,
        candidate: PatternCandidate,
        force: bool = False
    ) -> PromotionResult:
        """Promote candidate to ACTIVE state."""
        return self.promote_candidate(
            candidate,
            target_state=PatternLifecycleState.ACTIVE,
            force=force
        )

    def archive_candidate(
        self,
        candidate: PatternCandidate,
        reason: str
    ) -> PromotionResult:
        """Archive a candidate."""
        return PromotionResult(
            candidate_id=candidate.id,
            current_state=candidate.lifecycle_state,
            requested_state=PatternLifecycleState.ARCHIVED,
            actual_state=PatternLifecycleState.ARCHIVED,
            success=True,
            outcome=ValidationOutcome.REJECT,
            promotion_reasons=[f"Archived: {reason}"],
        )


# ============================================================================
# Conflict and Supersession Handler
# ============================================================================

class PatternSupersessionHandler:
    """
    Handles pattern conflicts and supersession.

    When a stronger pattern emerges:
    - Weaker pattern is marked SUPERSEDED
    - Lineage is preserved
    - Replacement pattern is linked
    """

    def __init__(self):
        """Initialize the supersession handler."""
        self.supersession_history: List[Dict[str, Any]] = []

    def detect_supersession(
        self,
        new_pattern: Pattern,
        existing_patterns: List[Pattern],
        similarity_threshold: float = 0.85
    ) -> List[Dict[str, Any]]:
        """
        Detect existing patterns that should be superseded by new pattern.

        Returns:
            List of supersession records
        """
        supersessions = []

        for existing in existing_patterns:
            # Skip if already superseded
            if existing.lifecycle_state == PatternLifecycleState.SUPERSEDED:
                continue

            # Same type and domain
            if existing.pattern_type != new_pattern.pattern_type:
                continue

            if existing.domain != new_pattern.domain:
                continue

            # Calculate similarity
            similarity = self._calculate_similarity(new_pattern, existing)

            if similarity >= similarity_threshold:
                # Check if new pattern is stronger
                new_is_stronger = (
                    new_pattern.quality.confidence_score > existing.quality.confidence_score and
                    new_pattern.quality.observation_count >= existing.quality.observation_count
                )

                if new_is_stronger:
                    supersession = {
                        "superseded_pattern": existing,
                        "superseded_by": new_pattern,
                        "similarity": similarity,
                        "reason": "new_pattern_stronger",
                        "detected_at": datetime.now(),
                    }
                    supersessions.append(supersession)

                    logger.info(
                        f"Supersession detected: {existing.name} superseded by {new_pattern.name} "
                        f"(similarity: {similarity:.2f})"
                    )

        return supersessions

    def apply_supersession(
        self,
        pattern: Pattern,
        superseded_by: Pattern
    ) -> Pattern:
        """
        Apply supersession to a pattern.

        Returns:
            Updated pattern with SUPERSEDED state
        """
        # Update pattern to superseded
        pattern.lifecycle_state = PatternLifecycleState.SUPERSEDED
        pattern.superseded_by_id = superseded_by.id
        pattern.superseded_at = datetime.now()

        # Log supersession
        self.supersession_history.append({
            "superseded_pattern_id": str(pattern.id),
            "superseded_pattern_name": pattern.name,
            "superseded_by_id": str(superseded_by.id),
            "superseded_by_name": superseded_by.name,
            "superseded_at": pattern.superseded_at.isoformat(),
        })

        logger.info(
            f"Applied supersession: {pattern.name} → SUPERSEDED by {superseded_by.name}"
        )

        return pattern

    def _calculate_similarity(
        self,
        pattern1: Pattern,
        pattern2: Pattern
    ) -> float:
        """Calculate similarity between two patterns."""
        # Type match
        type_score = 1.0 if pattern1.pattern_type == pattern2.pattern_type else 0.0

        # Domain match
        domain_score = 1.0 if pattern1.domain == pattern2.domain else 0.0

        # Scope match
        scope_score = 1.0 if pattern1.scope == pattern2.scope else 0.0

        # Structure overlap
        keys1 = set(pattern1.structure.keys())
        keys2 = set(pattern2.structure.keys())
        struct_score = len(keys1 & keys2) / len(keys1 | keys2) if keys1 | keys2 else 0.0

        # Weighted average
        return type_score * 0.3 + domain_score * 0.3 + scope_score * 0.1 + struct_score * 0.3

    def get_supersession_history(
        self,
        pattern_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Get supersession history, optionally filtered by pattern."""
        if pattern_id:
            return [
                s for s in self.supersession_history
                if s["superseded_pattern_id"] == str(pattern_id) or
                   s["superseded_by_id"] == str(pattern_id)
            ]
        return self.supersession_history


# ============================================================================
# Audit Logger
# ============================================================================

class PatternAuditRecord(BaseModel):
    """Audit record for pattern validation/promotion decisions."""
    id: UUID = Field(default_factory=uuid4)

    # What was acted on
    pattern_id: UUID
    pattern_name: str
    pattern_type: PatternType

    # Action taken
    action: str  # "validated", "promoted", "rejected", "held", "superseded", "archived"

    # State transition
    from_state: Optional[PatternLifecycleState] = None
    to_state: Optional[PatternLifecycleState] = None

    # Decision context
    decision_reasoning: str
    scores_at_decision: Dict[str, float] = Field(default_factory=dict)

    # Rules applied
    passed_rules: List[str] = Field(default_factory=list)
    failed_rules: List[str] = Field(default_factory=list)

    # Metadata
    decided_at: datetime = Field(default_factory=datetime.now)
    decided_by: str = "validation_workflow"
    validator_version: str = "1.0.0"

    # Related records
    superseded_by_id: Optional[UUID] = None
    related_pattern_ids: List[UUID] = Field(default_factory=list)


class PatternAuditLogger:
    """
    Logs all validation and promotion decisions for auditability.

    Provides:
    - Complete decision history
    - Rule application tracking
    - Score evolution over time
    - Compliance reporting
    """

    def __init__(self):
        """Initialize the audit logger."""
        self._records: List[PatternAuditRecord] = []

    def log_validation(
        self,
        candidate: PatternCandidate,
        validation: ValidationResult
    ) -> PatternAuditRecord:
        """Log a validation decision."""
        record = PatternAuditRecord(
            pattern_id=candidate.id,
            pattern_name=candidate.name,
            pattern_type=candidate.pattern_type,
            action=f"validated_{validation.outcome.value}",
            from_state=candidate.lifecycle_state,
            to_state=validation.target_state,
            decision_reasoning=validation.reasoning,
            scores_at_decision={
                "recurrence": validation.recurrence_score,
                "confidence": validation.confidence_score,
                "stability": validation.stability_score,
                "source_diversity": validation.source_diversity_score,
                "temporal_consistency": validation.temporal_consistency_score,
            },
            passed_rules=validation.passed_rules,
            failed_rules=validation.failed_rules,
            validator_version=validation.validator_version,
        )

        self._records.append(record)
        logger.info(
            f"Audit: {candidate.name} {validation.outcome.value} - {validation.reasoning}"
        )

        return record

    def log_promotion(
        self,
        result: PromotionResult,
        candidate_name: str,
        pattern_type: PatternType
    ) -> PatternAuditRecord:
        """Log a promotion decision."""
        record = PatternAuditRecord(
            pattern_id=result.candidate_id,
            pattern_name=candidate_name,
            pattern_type=pattern_type,
            action=f"promoted_to_{result.actual_state.value}" if result.success else "promotion_failed",
            from_state=result.current_state,
            to_state=result.actual_state if result.success else None,
            decision_reasoning="; ".join(result.promotion_reasons) if result.promotion_reasons else "; ".join(result.blocking_issues),
            passed_rules=result.promotion_reasons,
            failed_rules=result.blocking_issues,
        )

        self._records.append(record)
        logger.info(
            f"Audit: promotion {result.success and 'success' or 'failed'} - "
            f"{candidate_name} {result.current_state.value} → {result.actual_state.value}"
        )

        return record

    def log_supersession(
        self,
        superseded: Pattern,
        superseded_by: Pattern
    ) -> PatternAuditRecord:
        """Log a supersession decision."""
        record = PatternAuditRecord(
            pattern_id=superseded.id,
            pattern_name=superseded.name,
            pattern_type=superseded.pattern_type,
            action="superseded",
            from_state=superseded.lifecycle_state,
            to_state=PatternLifecycleState.SUPERSEDED,
            decision_reasoning=f"Superseded by stronger pattern: {superseded_by.name}",
            superseded_by_id=superseded_by.id,
            related_pattern_ids=[superseded_by.id],
        )

        self._records.append(record)
        logger.info(
            f"Audit: {superseded.name} SUPERSEDED by {superseded_by.name}"
        )

        return record

    def get_audit_trail(
        self,
        pattern_id: Optional[UUID] = None,
        pattern_type: Optional[PatternType] = None,
        action: Optional[str] = None,
        limit: int = 100
    ) -> List[PatternAuditRecord]:
        """Get audit records with optional filtering."""
        records = self._records

        if pattern_id:
            records = [r for r in records if r.pattern_id == pattern_id]

        if pattern_type:
            records = [r for r in records if r.pattern_type == pattern_type]

        if action:
            records = [r for r in records if r.action == action]

        # Sort by most recent first
        records = sorted(records, key=lambda r: r.decided_at, reverse=True)

        return records[:limit]

    def get_pattern_history(
        self,
        pattern_id: UUID
    ) -> List[PatternAuditRecord]:
        """Get complete history for a specific pattern."""
        return self.get_audit_trail(pattern_id=pattern_id, limit=1000)

    def get_compliance_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Generate compliance report for audit period."""
        records = self._records

        if start_date:
            records = [r for r in records if r.decided_at >= start_date]

        if end_date:
            records = [r for r in records if r.decided_at <= end_date]

        # Group by action
        by_action = defaultdict(int)
        for record in records:
            by_action[record.action] += 1

        # Group by pattern type
        by_type = defaultdict(int)
        for record in records:
            by_type[record.pattern_type.value] += 1

        # Group by outcome
        promoted = len([r for r in records if "promoted" in r.action])
        rejected = len([r for r in records if "rejected" in r.action or "superseded" in r.action])
        held = len([r for r in records if "held" in r.action])

        return {
            "period_start": start_date.isoformat() if start_date else None,
            "period_end": end_date.isoformat() if end_date else None,
            "total_decisions": len(records),
            "decisions_by_action": dict(by_action),
            "decisions_by_type": dict(by_type),
            "promotion_rate": promoted / len(records) if records else 0,
            "rejection_rate": rejected / len(records) if records else 0,
            "hold_rate": held / len(records) if records else 0,
        }


# ============================================================================
# Complete Validation & Promotion Orchestrator
# ============================================================================

class PatternValidationOrchestrator:
    """
    Orchestrates the complete validation and promotion workflow.

    Flow:
    1. Validate candidate against thresholds
    2. Check for conflicts with existing patterns
    3. Handle supersession if applicable
    4. Promote through lifecycle if valid
    5. Log all decisions to audit trail
    """

    def __init__(
        self,
        validation_service: Optional[PatternValidationService] = None,
        promotion_workflow: Optional[PatternPromotionWorkflow] = None,
        supersession_handler: Optional[PatternSupersessionHandler] = None,
        audit_logger: Optional[PatternAuditLogger] = None,
        persistence: Optional[PatternPersistenceService] = None
    ):
        """Initialize the orchestrator."""
        self.validation_service = validation_service or PatternValidationService()
        self.promotion_workflow = promotion_workflow or PatternPromotionWorkflow()
        self.supersession_handler = supersession_handler or PatternSupersessionHandler()
        self.audit_logger = audit_logger or PatternAuditLogger()
        self.persistence = persistence or PatternPersistenceService()

    def process_candidate(
        self,
        candidate: PatternCandidate,
        target_state: Optional[PatternLifecycleState] = None,
        existing_patterns: Optional[List[Pattern]] = None,
        force_promotion: bool = False
    ) -> Dict[str, Any]:
        """
        Process a candidate through validation and promotion.

        Returns:
            Dict with validation result, promotion result, and audit records
        """
        results = {
            "candidate_id": str(candidate.id),
            "candidate_name": candidate.name,
            "validation_outcome": None,
            "promotion_outcome": None,
            "final_state": None,
            "audit_records": [],
        }

        # Get existing patterns if not provided
        if existing_patterns is None:
            existing_patterns = self.persistence.list_patterns()

        # Step 1: Validate candidate
        validation = self.validation_service.validate_candidate(candidate, existing_patterns)
        results["validation_outcome"] = validation.outcome.value

        # Log validation
        audit_record = self.audit_logger.log_validation(candidate, validation)
        results["audit_records"].append(audit_record.id)

        # Step 2: Handle supersession if detected
        if validation.outcome == ValidationOutcome.SUPERSEDED:
            superseded_by = self.persistence.get_pattern(validation.superseded_by_id)
            if superseded_by:
                results["superseded_by"] = {
                    "id": str(superseded_by.id),
                    "name": superseded_by.name,
                }

        # Step 3: Promote if valid
        if validation.outcome == ValidationOutcome.PROMOTE:
            promotion = self.promotion_workflow.promote_candidate(
                candidate,
                target_state=target_state,
                existing_patterns=existing_patterns,
                force=force_promotion
            )
            results["promotion_outcome"] = promotion.outcome.value
            results["final_state"] = promotion.actual_state.value if promotion.success else candidate.lifecycle_state.value

            # Log promotion
            audit_record = self.audit_logger.log_promotion(
                promotion,
                candidate.name,
                candidate.pattern_type
            )
            results["audit_records"].append(audit_record.id)

            # If promotion successful and superseding another pattern, log it
            if promotion.success and existing_patterns:
                # Build a minimal pattern for supersession detection
                # (only fields needed for similarity calculation)
                temp_pattern = Pattern(
                    pattern_type=candidate.pattern_type,
                    name=candidate.name,
                    description=candidate.description or "",
                    structure=candidate.structure or {},
                    characteristics=candidate.characteristics or {},
                    tags=candidate.tags or [],
                    source_references=candidate.source_references or [],
                    quality=candidate.quality or PatternQualityMetrics(
                        confidence_score=candidate.confidence_score,
                        stability_score=candidate.stability_score,
                        consistency_score=candidate.temporal_consistency_score,
                        observation_count=len(candidate.evidence),
                        unique_execution_count=len(set(ev.execution_id for ev in candidate.evidence if ev.execution_id)),
                        distinct_source_count=len(set(ev.source_type for ev in candidate.evidence)),
                        first_observed_at=min((ev.observed_at for ev in candidate.evidence), default=datetime.now()),
                        last_observed_at=max((ev.observed_at for ev in candidate.evidence), default=datetime.now()),
                    ),
                    lifecycle_state=promotion.actual_state,
                    domain=candidate.domain,
                    scope=candidate.scope,
                )

                for supersession in supersessions:
                    updated = self.supersession_handler.apply_supersession(
                        supersession["superseded_pattern"],
                        supersession["superseded_by"]
                    )
                    self.audit_logger.log_supersession(
                        supersession["superseded_pattern"],
                        supersession["superseded_by"]
                    )

        else:
            # Not promoted
            results["final_state"] = candidate.lifecycle_state.value
            results["reason"] = validation.reasoning

        return results

    def batch_process_candidates(
        self,
        candidates: List[PatternCandidate],
        target_state: Optional[PatternLifecycleState] = None
    ) -> Dict[str, Any]:
        """Process multiple candidates in batch."""
        results = {
            "total_candidates": len(candidates),
            "promoted": 0,
            "held": 0,
            "rejected": 0,
            "superseded": 0,
            "candidate_results": [],
        }

        existing_patterns = self.persistence.list_patterns()

        for candidate in candidates:
            result = self.process_candidate(
                candidate,
                target_state=target_state,
                existing_patterns=existing_patterns
            )
            results["candidate_results"].append(result)

            # Count outcomes
            if result["validation_outcome"] == "promote":
                results["promoted"] += 1
            elif result["validation_outcome"] == "hold":
                results["held"] += 1
            elif result["validation_outcome"] == "reject":
                results["rejected"] += 1
            elif result["validation_outcome"] == "superseded":
                results["superseded"] += 1

        logger.info(
            f"Batch processing complete: {results['promoted']} promoted, "
            f"{results['held']} held, {results['rejected']} rejected, "
            f"{results['superseded']} superseded"
        )

        return results


# ============================================================================
# Convenience Functions
# ============================================================================

def validate_pattern_candidate(
    candidate: PatternCandidate,
    thresholds: Optional[ValidationThresholds] = None
) -> ValidationResult:
    """Validate a pattern candidate."""
    service = PatternValidationService(thresholds=thresholds)
    return service.validate_candidate(candidate)


def promote_pattern(
    candidate: PatternCandidate,
    target_state: PatternLifecycleState,
    force: bool = False
) -> PromotionResult:
    """Promote a pattern candidate."""
    workflow = PatternPromotionWorkflow()
    return workflow.promote_candidate(candidate, target_state=target_state, force=force)


def check_pattern_supersession(
    new_pattern: Pattern,
    existing_patterns: List[Pattern],
    similarity_threshold: float = 0.85
) -> List[Dict[str, Any]]:
    """Check for pattern supersession."""
    handler = PatternSupersessionHandler()
    return handler.detect_supersesion(new_pattern, existing_patterns, similarity_threshold)
