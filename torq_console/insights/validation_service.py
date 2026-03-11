"""
Insight Publishing Validation Service - Phase Insight Publishing Milestone 2

Validates insight candidates against quality gates and publishing criteria.

This module enforces:
- Type-specific quality gates
- Provenance requirements
- Freshness constraints
- Duplication and supersession detection
- Publication eligibility
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from pydantic import BaseModel, Field

from .models import (
    InsightType,
    InsightScope,
    InsightLifecycleState,
    InsightSourceType,
    InsightCreate,
    Insight,
    QualityMetrics,
    QualityGateResult,
    SourceReference,
)

from .publishing_rules import (
    QUALITY_GATES,
    QualityGateConfig,
    get_default_publishing_rules,
    get_default_publishing_criteria,
    PublishingRule,
    PublishingCriteria,
    PublicationEligibilityChecker,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Validation Result Models
# ============================================================================

class ValidationResult(BaseModel):
    """
    Result of validating an insight candidate.
    """
    passed: bool
    insight_id: Optional[UUID] = None

    # Quality gate results
    quality_gate_results: List[QualityGateResult] = Field(default_factory=list)

    # Validation details
    validation_errors: List[str] = Field(default_factory=list)
    validation_warnings: List[str] = Field(default_factory=list)

    # Conflict detection
    conflicting_insights: List[UUID] = Field(default_factory=list)
    should_supersede: Optional[UUID] = None  # ID of insight to supersede

    # Provenance check
    provenance_valid: bool = True
    provenance_issues: List[str] = Field(default_factory=list)

    # Freshness check
    freshness_valid: bool = True
    freshness_issues: List[str] = Field(default_factory=list)

    # Metadata
    validated_at: datetime = Field(default_factory=datetime.now)
    validator: str = "system"


# ============================================================================
# Duplication Detection
# ============================================================================

class DuplicationCheck(BaseModel):
    """
    Result of checking for duplicate or conflicting insights.
    """
    is_duplicate: bool
    is_supersedable: bool
    similarity_score: float
    existing_insight_id: Optional[UUID] = None
    conflict_reason: Optional[str] = None


class DuplicationDetector:
    """
    Detects duplicate or conflicting insights.

    Uses textual similarity and type matching to identify
    insights that should be merged or superseded.
    """

    def __init__(
        self,
        similarity_threshold: float = 0.85,
        supersede_threshold: float = 0.90
    ):
        """
        Initialize the detector.

        Args:
            similarity_threshold: Score above which insights are considered conflicting
            supersede_threshold: Score above which new insight should supersede existing
        """
        self.similarity_threshold = similarity_threshold
        self.supersede_threshold = supersede_threshold

    def check_for_duplicates(
        self,
        candidate: InsightCreate,
        existing_insights: List[Insight]
    ) -> DuplicationCheck:
        """
        Check if a candidate duplicates or conflicts with existing insights.

        Args:
            candidate: The insight candidate to check
            existing_insights: Published insights to compare against

        Returns:
            DuplicationCheck with conflict information
        """
        # Filter to same type and scope
        same_type = [
            ins for ins in existing_insights
            if ins.insight_type == candidate.insight_type
            and ins.lifecycle_state == InsightLifecycleState.PUBLISHED
        ]

        # Check title and summary similarity
        for existing in same_type:
            similarity = self._compute_similarity(candidate, existing)

            if similarity >= self.supersede_threshold:
                return DuplicationCheck(
                    is_duplicate=True,
                    is_supersedable=True,
                    similarity_score=similarity,
                    existing_insight_id=existing.id,
                    conflict_reason=f"Very similar ({similarity:.2f}) to existing insight"
                )

            if similarity >= self.similarity_threshold:
                return DuplicationCheck(
                    is_duplicate=True,
                    is_supersedable=False,
                    similarity_score=similarity,
                    existing_insight_id=existing.id,
                    conflict_reason=f"Similar ({similarity:.2f}) to existing insight"
                )

        return DuplicationCheck(
            is_duplicate=False,
            is_supersedable=False,
            similarity_score=0.0,
        )

    def _compute_similarity(
        self,
        candidate: InsightCreate,
        existing: Insight
    ) -> float:
        """
        Compute similarity between candidate and existing insight.

        Simple heuristic based on title and summary overlap.
        """
        # Get text from both
        candidate_text = f"{candidate.title} {candidate.summary}".lower()
        existing_text = f"{existing.title} {existing.summary}".lower()

        # Simple word overlap similarity
        candidate_words = set(candidate_text.split())
        existing_words = set(existing_text.split())

        if not candidate_words or not existing_words:
            return 0.0

        intersection = candidate_words & existing_words
        union = candidate_words | existing_words

        # Jaccard similarity
        jaccard = len(intersection) / len(union) if union else 0

        # Boost for exact title match
        title_match = 1.0 if candidate.title.lower() == existing.title.lower() else 0

        # Combined score (70% Jaccard, 30% title)
        similarity = jaccard * 0.7 + title_match * 0.3

        return min(similarity, 1.0)


# ============================================================================
# Publishing Validator
# ============================================================================

class PublishingValidator:
    """
    Validates insight candidates for publication.

    Enforces quality gates, provenance rules, and freshness constraints.
    """

    def __init__(
        self,
        quality_gates: Optional[Dict[InsightType, QualityGateConfig]] = None,
        publishing_rules: Optional[List[PublishingRule]] = None,
        publishing_criteria: Optional[PublishingCriteria] = None,
    ):
        """
        Initialize the validator.

        Args:
            quality_gates: Quality gate configuration by insight type
            publishing_rules: Publishing rules to enforce
            publishing_criteria: Overall publishing criteria
        """
        self.quality_gates = quality_gates or QUALITY_GATES
        self.publishing_rules = publishing_rules or get_default_publishing_rules()
        self.publishing_criteria = publishing_criteria or get_default_publishing_criteria()
        self.eligibility_checker = PublicationEligibilityChecker(
            self.quality_gates,
            self.publishing_rules
        )
        self.duplication_detector = DuplicationDetector(
            self.publishing_criteria.conflict_similarity_threshold,
            self.publishing_criteria.auto_supersede_threshold
        )

    def validate_for_publication(
        self,
        candidate: InsightCreate,
        existing_insights: Optional[List[Insight]] = None,
        as_of_date: Optional[datetime] = None
    ) -> ValidationResult:
        """
        Validate an insight candidate for publication.

        Runs all quality gates, provenance checks, and conflict detection.

        Args:
            candidate: The insight candidate to validate
            existing_insights: Existing published insights (for conflict detection)
            as_of_date: Date for freshness calculations

        Returns:
            ValidationResult with pass/fail and details
        """
        as_of_date = as_of_date or datetime.now()
        existing_insights = existing_insights or []

        result = ValidationResult(passed=True)

        # 1. Run quality gates
        quality_results = self.eligibility_checker.check_eligibility(
            candidate,
            as_of_date
        )
        result.quality_gate_results = quality_results

        if not self.eligibility_checker.passes_all_gates(quality_results):
            result.passed = False
            failed_gates = self.eligibility_checker.get_failed_gates(quality_results)
            result.validation_errors.extend([
                f"Quality gate failed: {fg.gate_name} - {fg.reason}"
                for fg in failed_gates
            ])

        # 2. Check provenance
        provenance_valid, provenance_issues = self._validate_provenance(candidate)
        result.provenance_valid = provenance_valid
        result.provenance_issues = provenance_issues

        if not provenance_valid:
            result.passed = False
            result.validation_errors.extend(provenance_issues)

        # 3. Check freshness
        freshness_valid, freshness_issues = self._validate_freshness(
            candidate,
            as_of_date
        )
        result.freshness_valid = freshness_valid
        result.freshness_issues = freshness_issues

        if not freshness_valid:
            result.passed = False
            result.validation_errors.extend(freshness_issues)

        # 4. Check for conflicts/duplicates
        if self.publishing_criteria.enable_conflict_detection:
            dup_check = self.duplication_detector.check_for_duplicates(
                candidate,
                existing_insights
            )

            if dup_check.is_duplicate:
                result.conflicting_insights = [dup_check.existing_insight_id]

                if dup_check.is_supersedable:
                    result.should_supersede = dup_check.existing_insight_id
                    result.validation_warnings.append(
                        f"Should supersede existing insight: {dup_check.existing_insight_id}"
                    )
                else:
                    result.passed = False
                    result.validation_errors.append(
                        f"Conflicts with existing insight: {dup_check.conflict_reason}"
                    )

        # 5. Check publishing rule-specific requirements
        rule_errors = self._validate_publishing_rules(candidate)
        if rule_errors:
            result.passed = False
            result.validation_errors.extend(rule_errors)

        return result

    def _validate_provenance(
        self,
        candidate: InsightCreate
    ) -> tuple[bool, List[str]]:
        """
        Validate provenance requirements.

        Ensures source references are present and valid.
        """
        issues = []

        # Must have at least one source
        if not candidate.source_references:
            issues.append("No source references provided")
            return False, issues

        # Check source types against allowed types for this insight type
        applicable_rule = self._get_applicable_rule(candidate)
        if applicable_rule:
            allowed_types = set(applicable_rule.allowed_source_types)
            for source_ref in candidate.source_references:
                if source_ref.source_type not in allowed_types:
                    issues.append(
                        f"Source type {source_ref.source_type.value} not allowed "
                        f"for insight type {candidate.insight_type.value}"
                    )

        # Check contribution weights sum to reasonable value
        total_weight = sum(sr.contribution_weight for sr in candidate.source_references)
        if total_weight == 0:
            issues.append("Total contribution weight is zero")

        return len(issues) == 0, issues

    def _validate_freshness(
        self,
        candidate: InsightCreate,
        as_of_date: datetime
    ) -> tuple[bool, List[str]]:
        """
        Validate freshness requirements.

        Ensures evidence is recent enough.
        """
        issues = []
        quality_gate = self.quality_gates.get(
            candidate.insight_type,
            self.quality_gates[InsightType.STRATEGIC_INSIGHT]  # Default
        )

        # Check evidence cutoff date if gate requires it
        if quality_gate.max_evidence_age_days:
            if candidate.quality.evidence_cutoff_at:
                age_days = (as_of_date - candidate.quality.evidence_cutoff_at).days
                if age_days > quality_gate.max_evidence_age_days:
                    issues.append(
                        f"Evidence is {age_days} days old, "
                        f"exceeds maximum of {quality_gate.max_evidence_age_days} days"
                    )
            else:
                issues.append("No evidence cutoff date provided")

        # Check recent validation if required
        if quality_gate.require_recent_validation:
            if candidate.quality.last_validated_at:
                validation_age = (as_of_date - candidate.quality.last_validated_at).days
                if validation_age > quality_gate.validation_window_days:
                    issues.append(
                        f"Validation is {validation_age} days old, "
                        f"exceeds window of {quality_gate.validation_window_days} days"
                    )
            else:
                issues.append("Recent validation required but none provided")

        return len(issues) == 0, issues

    def _get_applicable_rule(
        self,
        candidate: InsightCreate
    ) -> Optional[PublishingRule]:
        """Get the publishing rule that applies to this candidate."""
        for rule in self.publishing_rules:
            if candidate.insight_type in rule.applies_to_types:
                return rule
        return None

    def _validate_publishing_rules(
        self,
        candidate: InsightCreate
    ) -> List[str]:
        """Validate candidate against publishing rule requirements."""
        issues = []
        rule = self._get_applicable_rule(candidate)

        if not rule:
            return [f"No publishing rule found for type {candidate.insight_type.value}"]

        # Check confidence threshold
        if candidate.quality.confidence_score < rule.min_confidence:
            issues.append(
                f"Confidence {candidate.quality.confidence_score} below "
                f"rule threshold {rule.min_confidence}"
            )

        # Check source count if specified
        source_count = len(candidate.source_references)
        if source_count < rule.min_source_count:
            issues.append(
                f"Source count {source_count} below "
                f"rule minimum {rule.min_source_count}"
            )

        # Check execution count if specified
        exec_count = candidate.quality.execution_count
        if exec_count < rule.min_execution_count:
            issues.append(
                f"Execution count {exec_count} below "
                f"rule minimum {rule.min_execution_count}"
            )

        # Check success rate if required
        if rule.require_success_rate:
            success_rate = candidate.quality.success_rate
            if success_rate is None or success_rate < rule.min_success_rate:
                issues.append(
                    f"Success rate not provided or below "
                    f"rule minimum {rule.min_success_rate}"
                )

        return issues


# ============================================================================
# Batch Validation
# ============================================================================

def validate_candidates_for_publication(
    candidates: List[InsightCreate],
    existing_insights: Optional[List[Insight]] = None,
    as_of_date: Optional[datetime] = None
) -> List[ValidationResult]:
    """
    Batch validate multiple insight candidates.

    Args:
        candidates: List of insight candidates to validate
        existing_insights: Existing published insights
        as_of_date: Date for freshness calculations

    Returns:
        List of validation results
    """
    validator = PublishingValidator()
    results = []

    for candidate in candidates:
        result = validator.validate_for_publication(
            candidate,
            existing_insights,
            as_of_date
        )
        results.append(result)

    # Log summary
    passed = sum(1 for r in results if r.passed)
    logger.info(
        f"Batch validation: {passed}/{len(results)} candidates passed"
    )

    return results


def get_validation_summary(
    results: List[ValidationResult]
) -> Dict[str, Any]:
    """
    Get summary statistics for validation results.

    Args:
        results: List of validation results

    Returns:
        Summary dict with counts and breakdowns
    """
    total = len(results)
    passed = sum(1 for r in results if r.passed)

    # Count by failure reason
    failure_reasons: Dict[str, int] = {}
    for result in results:
        if not result.passed:
            for error in result.validation_errors:
                failure_reasons[error] = failure_reasons.get(error, 0) + 1

    # Quality gate pass rates
    gate_pass_rates: Dict[str, Dict[str, int]] = {}
    if results:
        for result in results:
            for gate_result in result.quality_gate_results:
                gate_name = gate_result.gate_name
                if gate_name not in gate_pass_rates:
                    gate_pass_rates[gate_name] = {"pass": 0, "fail": 0}
                if gate_result.passed:
                    gate_pass_rates[gate_name]["pass"] += 1
                else:
                    gate_pass_rates[gate_name]["fail"] += 1

    # Conflict/supersession stats
    conflicts = sum(1 for r in results if r.conflicting_insights)
    supersedes = sum(1 for r in results if r.should_supersede)

    return {
        "total_candidates": total,
        "passed": passed,
        "rejected": total - passed,
        "pass_rate": passed / total if total > 0 else 0,
        "failure_reasons": failure_reasons,
        "quality_gate_pass_rates": gate_pass_rates,
        "conflicts_detected": conflicts,
        "supersedes_recommended": supersedes,
    }


# ============================================================================
# Helper Functions
# ============================================================================

def get_default_validator() -> PublishingValidator:
    """Get the default publishing validator."""
    return PublishingValidator()
