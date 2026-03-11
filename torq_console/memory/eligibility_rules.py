"""
Eligibility Rules Engine - Phase 4H.1 Milestone 1

Implements the validation logic for determining whether
artifacts are eligible to become governed memory.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .memory_models import (
    ConfidenceLevel,
    EligibilityRule,
    EligibilityRuleset,
    MemoryCandidate,
    MemoryProvenance,
    MemoryType,
    RejectionReason,
    ValidationDecision,
    DEFAULT_ELIGIBILITY_RULESET,
    FRESHNESS_RULES,
    get_freshness_window,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Artifact Type Eligibility
# ============================================================================

# Artifact types that are eligible for memory
ELIGIBLE_ARTIFACT_TYPES = {
    "web_search",
    "code_execution",
    "analysis",
    "decision",
    "plan",
    "team_output",
    "api_call",
    "documentation",
    "pattern_recognition",
}

# Artifact types that are never eligible
INELIGIBLE_ARTIFACT_TYPES = {
    "raw_output",
    "error",
    "debug_output",
    "internal_log",
}


# ============================================================================
# Confidence Requirements by Memory Type
# ============================================================================

CONFIDENCE_REQUIREMENTS: Dict[MemoryType, float] = {
    MemoryType.KNOWLEDGE: 0.7,
    MemoryType.PATTERN: 0.75,
    MemoryType.DECISION: 0.7,
    MemoryType.CODE_PATTERN: 0.8,
    MemoryType.ARCHITECTURE_DECISION: 0.75,
    MemoryType.TEAM_INSIGHT: 0.7,
    MemoryType.API_KNOWLEDGE: 0.8,
    MemoryType.BEST_PRACTICE: 0.75,
}


# ============================================================================
# Completeness Requirements by Memory Type
# ============================================================================

COMPLETENESS_REQUIREMENTS: Dict[MemoryType, float] = {
    MemoryType.KNOWLEDGE: 0.6,
    MemoryType.PATTERN: 0.7,
    MemoryType.DECISION: 0.8,  # Decisions need rationale
    MemoryType.CODE_PATTERN: 0.7,
    MemoryType.ARCHITECTURE_DECISION: 0.8,
    MemoryType.TEAM_INSIGHT: 0.6,
    MemoryType.API_KNOWLEDGE: 0.8,  # API info needs to be complete
    MemoryType.BEST_PRACTICE: 0.7,
}


# ============================================================================
# Required Fields by Memory Type
# ============================================================================

REQUIRED_FIELDS: Dict[MemoryType, List[str]] = {
    MemoryType.DECISION: ["rationale", "decision_point"],
    MemoryType.ARCHITECTURE_DECISION: [
        "rationale",
        "alternatives_considered",
        "decision_point",
    ],
    MemoryType.API_KNOWLEDGE: ["endpoint", "method", "parameters"],
    MemoryType.CODE_PATTERN: ["pattern_description", "code_example"],
    MemoryType.PATTERN: ["pattern_description", "occurrences"],
}


# ============================================================================
# Eligibility Engine
# ============================================================================

class EligibilityEngine:
    """
    Engine for determining memory eligibility.

    This implements the validation logic that decides whether
    an artifact-derived candidate should become governed memory.
    """

    def __init__(
        self,
        ruleset: Optional[EligibilityRuleset] = None,
        strict_mode: bool = False,
    ):
        """
        Initialize the eligibility engine.

        Args:
            ruleset: Optional custom ruleset (uses default if None)
            strict_mode: If True, reject borderline cases
        """
        self.ruleset = ruleset or DEFAULT_ELIGIBILITY_RULESET
        self.strict_mode = strict_mode
        self._rejection_counts: Dict[str, int] = {}

    def check_candidate(
        self,
        candidate: MemoryCandidate,
    ) -> Tuple[ValidationDecision, Optional[RejectionReason], Optional[str]]:
        """
        Check if a candidate is eligible for memory.

        Args:
            candidate: Memory candidate to validate

        Returns:
            (decision, rejection_reason, message)
        """
        # 1. Check artifact type eligibility
        type_check = self._check_artifact_type(candidate.artifact_type)
        if type_check[0] != ValidationDecision.ACCEPT:
            self._track_rejection(type_check[1])
            return type_check

        # 2. Check provenance
        provenance_check = self._check_provenance(candidate.provenance)
        if provenance_check[0] != ValidationDecision.ACCEPT:
            self._track_rejection(provenance_check[1])
            return provenance_check

        # 3. Check confidence threshold
        confidence_check = self._check_confidence(candidate)
        if confidence_check[0] != ValidationDecision.ACCEPT:
            self._track_rejection(confidence_check[1])
            return confidence_check

        # 4. Check completeness
        completeness_check = self._check_completeness(candidate)
        if completeness_check[0] != ValidationDecision.ACCEPT:
            self._track_rejection(completeness_check[1])
            return completeness_check

        # 5. Check required fields
        fields_check = self._check_required_fields(candidate)
        if fields_check[0] != ValidationDecision.ACCEPT:
            self._track_rejection(fields_check[1])
            return fields_check

        # 6. Check freshness
        freshness_check = self._check_freshness(candidate)
        if freshness_check[0] != ValidationDecision.ACCEPT:
            self._track_rejection(freshness_check[1])
            return freshness_check

        # 7. Apply ruleset
        is_eligible, reason, rule = self.ruleset.check_candidate(candidate)
        if not is_eligible:
            self._track_rejection(reason or "unknown")
            return ValidationDecision.REJECT, reason, f"Rejected by ruleset: {rule.rule_name if rule else 'default'}"

        # 8. Final decision based on confidence level
        level = candidate.confidence_level
        if level == ConfidenceLevel.VERIFIED:
            return ValidationDecision.ACCEPT, None, "Auto-accepted: Verified confidence"
        elif level == ConfidenceLevel.HIGH:
            return ValidationDecision.ACCEPT, None, "Accepted: High confidence"
        elif level == ConfidenceLevel.MEDIUM:
            if self.strict_mode:
                return ValidationDecision.REVIEW, None, "Review required: Medium confidence (strict mode)"
            return ValidationDecision.ACCEPT, None, "Accepted: Medium confidence"
        else:
            return ValidationDecision.REJECT, RejectionReason.LOW_CONFIDENCE, "Rejected: Low confidence"

    def _check_artifact_type(
        self,
        artifact_type: str,
    ) -> Tuple[ValidationDecision, Optional[RejectionReason], Optional[str]]:
        """Check if artifact type is eligible."""
        artifact_type_lower = artifact_type.lower()

        # Check explicit ineligible types
        if artifact_type_lower in INELIGIBLE_ARTIFACT_TYPES:
            return (
                ValidationDecision.REJECT,
                RejectionReason.INVALID_SOURCE_TYPE,
                f"Ineligible artifact type: {artifact_type}",
            )

        # Check if in eligible types (or allow if not explicitly blocked)
        if ELIGIBLE_ARTIFACT_TYPES and artifact_type_lower not in ELIGIBLE_ARTIFACT_TYPES:
            # Not explicitly eligible, but not explicitly blocked either
            # Allow it to pass through to other checks
            pass

        return (ValidationDecision.ACCEPT, None, None)

    def _check_provenance(
        self,
        provenance: MemoryProvenance,
    ) -> Tuple[ValidationDecision, Optional[RejectionReason], Optional[str]]:
        """Check if candidate has valid provenance."""
        if not provenance.artifact_id:
            return (
                ValidationDecision.REJECT,
                RejectionReason.NO_PROVENANCE,
                "No artifact ID in provenance",
            )

        if not provenance.workspace_id:
            return (
                ValidationDecision.REJECT,
                RejectionReason.NO_PROVENANCE,
                "No workspace ID in provenance",
            )

        return (ValidationDecision.ACCEPT, None, None)

    def _check_confidence(
        self,
        candidate: MemoryCandidate,
    ) -> Tuple[ValidationDecision, Optional[RejectionReason], Optional[str]]:
        """Check if candidate meets confidence threshold."""
        memory_type = candidate.proposed_memory_type
        min_confidence = CONFIDENCE_REQUIREMENTS.get(
            memory_type,
            self.ruleset.default_min_confidence,
        )

        if candidate.confidence_score < min_confidence:
            return (
                ValidationDecision.REJECT,
                RejectionReason.LOW_CONFIDENCE,
                f"Confidence {candidate.confidence_score:.2f} below threshold {min_confidence:.2f} for {memory_type.value}",
            )

        return (ValidationDecision.ACCEPT, None, None)

    def _check_completeness(
        self,
        candidate: MemoryCandidate,
    ) -> Tuple[ValidationDecision, Optional[RejectionReason], Optional[str]]:
        """Check if candidate meets completeness threshold."""
        memory_type = candidate.proposed_memory_type
        min_completeness = COMPLETENESS_REQUIREMENTS.get(
            memory_type,
            self.ruleset.default_min_completeness,
        )

        if candidate.completeness_score < min_completeness:
            return (
                ValidationDecision.REJECT,
                RejectionReason.INCOMPLETE,
                f"Completeness {candidate.completeness_score:.2f} below threshold {min_completeness:.2f} for {memory_type.value}",
            )

        return (ValidationDecision.ACCEPT, None, None)

    def _check_required_fields(
        self,
        candidate: MemoryCandidate,
    ) -> Tuple[ValidationDecision, Optional[RejectionReason], Optional[str]]:
        """Check if candidate has all required fields."""
        memory_type = candidate.proposed_memory_type
        required = REQUIRED_FIELDS.get(memory_type, [])

        if not required:
            return (ValidationDecision.ACCEPT, None, None)

        # Check both top-level fields and content_json fields
        content_dict = candidate.content.model_dump()
        content_json = content_dict.get("content_json", {})

        missing = []
        for field in required:
            # Check top level first
            if field in content_dict and content_dict[field] is not None and content_dict[field] != "":
                continue
            # Check content_json
            if field in content_json and content_json[field] is not None and content_json[field] != "":
                continue
            missing.append(field)

        if missing:
            return (
                ValidationDecision.REJECT,
                RejectionReason.MISSING_FIELDS,
                f"Missing required fields for {memory_type.value}: {', '.join(missing)}",
            )

        return (ValidationDecision.ACCEPT, None, None)

    def _check_freshness(
        self,
        candidate: MemoryCandidate,
    ) -> Tuple[ValidationDecision, Optional[RejectionReason], Optional[str]]:
        """Check if source artifact is still fresh."""
        memory_type = candidate.proposed_memory_type
        freshness_days = get_freshness_window(memory_type)

        # Check age of source artifact
        age_days = (datetime.now() - candidate.provenance.artifact_created_at).days

        if age_days > freshness_days:
            return (
                ValidationDecision.REJECT,
                RejectionReason.STALE_SOURCE,
                f"Source artifact {age_days} days old, freshness window is {freshness_days} days for {memory_type.value}",
            )

        return (ValidationDecision.ACCEPT, None, None)

    def _track_rejection(self, reason) -> None:
        """Track rejection reasons for analytics."""
        # Convert RejectionReason enum to string if needed
        if isinstance(reason, RejectionReason):
            reason_str = reason.value
        else:
            reason_str = str(reason) if reason else "unknown"
        self._rejection_counts[reason_str] = self._rejection_counts.get(reason_str, 0) + 1

    def get_rejection_stats(self) -> Dict[str, int]:
        """Get rejection statistics."""
        return self._rejection_counts.copy()

    def reset_stats(self) -> None:
        """Reset rejection statistics."""
        self._rejection_counts.clear()


# ============================================================================
# Conflict Detection
# ============================================================================

class ConflictDetector:
    """
    Detects conflicts between memory candidates and existing memory.

    This prevents contradictory memory from being stored.
    """

    def __init__(self, strict_conflict_detection: bool = False):
        """
        Initialize the conflict detector.

        Args:
            strict_conflict_detection: If True, reject on any potential conflict
        """
        self.strict_mode = strict_conflict_detection

    def check_conflict(
        self,
        candidate: MemoryCandidate,
        existing_memories: List[Any],  # List[ValidatedMemory]
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if candidate conflicts with existing memories.

        Args:
            candidate: New memory candidate
            existing_memories: List of existing validated memories

        Returns:
            (has_conflict, conflict_description)
        """
        # Group existing memories by type
        by_type: Dict[MemoryType, List[Any]] = {}
        for mem in existing_memories:
            mem_type = mem.metadata.memory_type
            if mem_type not in by_type:
                by_type[mem_type] = []
            by_type[mem_type].append(mem)

        candidate_type = candidate.proposed_memory_type

        # Check for conflicts within the same type
        if candidate_type in by_type:
            for existing in by_type[candidate_type]:
                # Check for direct contradiction in content
                if self._is_contradictory(candidate, existing):
                    return (
                        True,
                        f"Contradicts existing memory {existing.id}: {existing.content.title}",
                    )

                # Check for supersession (newer version of same thing)
                if self._is_superseding(candidate, existing):
                    # Not a conflict, but should supersede
                    # This is handled elsewhere
                    pass

        return (False, None)

    def _is_contradictory(self, candidate: MemoryCandidate, existing: Any) -> bool:
        """Check if candidate contradicts existing memory."""
        # Simple heuristic: same title/pattern but different key assertions
        cand_content = candidate.content.content_text.lower()
        existing_content = existing.content.content_text.lower()

        # Check for negation patterns
        contradictions = [
            ("should", "should not"),
            ("must", "must not"),
            ("do", "do not"),
            ("use", "avoid"),
            ("enable", "disable"),
            ("true", "false"),
            ("yes", "no"),
        ]

        for pos, neg in contradictions:
            if pos in cand_content and neg in existing_content:
                return True
            if neg in cand_content and pos in existing_content:
                return True

        return False

    def _is_superseding(self, candidate: MemoryCandidate, existing: Any) -> bool:
        """Check if candidate is a newer version of existing memory."""
        # Same title/topic, but candidate is newer
        if (
            candidate.content.title.lower() == existing.content.title.lower()
            and candidate.provenance.artifact_created_at
            > existing.provenance.artifact_created_at
        ):
            return True

        return False


# ============================================================================
# Factory Functions
# ============================================================================

def get_eligibility_engine(
    ruleset: Optional[EligibilityRuleset] = None,
    strict_mode: bool = False,
) -> EligibilityEngine:
    """
    Get an eligibility engine.

    Args:
        ruleset: Optional custom ruleset
        strict_mode: Whether to use strict validation

    Returns:
        Configured eligibility engine
    """
    return EligibilityEngine(ruleset=ruleset, strict_mode=strict_mode)


def get_conflict_detector(strict_mode: bool = False) -> ConflictDetector:
    """
    Get a conflict detector.

    Args:
        strict_mode: Whether to use strict conflict detection

    Returns:
        Configured conflict detector
    """
    return ConflictDetector(strict_conflict_detection=strict_mode)
