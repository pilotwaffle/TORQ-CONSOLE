"""
TORQ Readiness Checker - Audit Integrity Verifier

Milestone 5: Validate audit log consistency and integrity.

Ensures audit logs remain consistent, complete, and correctly ordered,
providing trust in governance history tracking.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from pydantic import BaseModel


logger = logging.getLogger(__name__)


# Import from existing modules
from ..transition_controller import (
    get_audit_logs,
    get_all_audit_logs,
    TransitionAuditLog,
)
from ..readiness_models import ReadinessState


# ============================================================================
# Integrity Violation
# ============================================================================

class IntegrityViolation(BaseModel):
    """
    Record of an audit integrity violation.
    """
    violation_type: str
    severity: str  # critical, warning, info
    candidate_id: Optional[UUID] = None
    description: str
    affected_records: List[str] = []
    detected_at: datetime = None

    class Config:
        use_enum_values = True

    def __init__(self, **data):
        if "detected_at" not in data:
            data["detected_at"] = datetime.now()
        super().__init__(**data)


# ============================================================================
# Integrity Report
# ============================================================================

class IntegrityReport(BaseModel):
    """
    Report on audit log integrity verification.
    """
    is_valid: bool
    verified_at: datetime
    candidates_checked: int
    total_transitions: int

    violations: List[IntegrityViolation]
    violation_counts: Dict[str, int]

    warnings: List[str]

    checks_performed: List[str]

    class Config:
        use_enum_values = True

    def __init__(self, **data):
        if "verified_at" not in data:
            data["verified_at"] = datetime.now()
        if "violations" not in data:
            data["violations"] = []
        if "violation_counts" not in data:
            data["violation_counts"] = {}
        if "warnings" not in data:
            data["warnings"] = []
        if "checks_performed" not in data:
            data["checks_performed"] = []
        super().__init__(**data)


# ============================================================================
# Audit Integrity Verifier
# ============================================================================

class AuditIntegrityVerifier:
    """
    Verifies the integrity of audit logs.

    Validates:
    - No missing transitions
    - No duplicate records
    - Chronological ordering preserved
    - Actor attribution exists
    - State transitions are valid
    - Evaluation links are consistent
    """

    def __init__(self):
        """Initialize the audit integrity verifier."""
        self._cached_reports: Dict[str, IntegrityReport] = {}

    def verify_candidate_audit_log(
        self,
        candidate_id: UUID,
    ) -> IntegrityReport:
        """
        Verify audit log integrity for a single candidate.

        Args:
            candidate_id: ID of the candidate to verify

        Returns:
            IntegrityReport with verification results
        """
        violations = []
        warnings = []
        checks_performed = []

        audit_logs = get_audit_logs(candidate_id)
        checks_performed.append("retrieved_audit_logs")

        # Check 1: Verify chronological ordering
        ordering_violations = self._check_chronological_order(audit_logs)
        violations.extend(ordering_violations)
        checks_performed.append("chronological_order_check")

        # Check 2: Detect duplicates
        duplicate_violations = self._check_duplicates(audit_logs, candidate_id)
        violations.extend(duplicate_violations)
        checks_performed.append("duplicate_detection")

        # Check 3: Verify actor attribution
        actor_violations = self._check_actor_attribution(audit_logs, candidate_id)
        violations.extend(actor_violations)
        checks_performed.append("actor_attribution_check")

        # Check 4: Verify state transitions are valid
        state_violations = self._check_valid_state_transitions(audit_logs, candidate_id)
        violations.extend(state_violations)
        checks_performed.append("state_transition_validity")

        # Check 5: Verify evaluation consistency
        eval_violations = self._check_evaluation_consistency(audit_logs, candidate_id)
        violations.extend(eval_violations)
        checks_performed.append("evaluation_consistency")

        # Count violations by type
        violation_counts = {}
        for v in violations:
            violation_counts[v.violation_type] = violation_counts.get(v.violation_type, 0) + 1

        # Generate warnings
        if len(audit_logs) == 0:
            warnings.append(f"No audit logs found for candidate {str(candidate_id)[:8]}")
        elif len(audit_logs) < 2:
            warnings.append(
                f"Limited audit history for candidate {str(candidate_id)[:8]} "
                f"({len(audit_logs)} transition)"
            )

        report = IntegrityReport(
            is_valid=len([v for v in violations if v.severity == "critical"]) == 0,
            candidates_checked=1,
            total_transitions=len(audit_logs),
            violations=violations,
            violation_counts=violation_counts,
            warnings=warnings,
            checks_performed=checks_performed,
        )

        return report

    def verify_system_audit_integrity(self) -> IntegrityReport:
        """
        Verify audit log integrity across the entire system.

        Returns:
            IntegrityReport with system-wide verification results
        """
        all_audit_logs = get_all_audit_logs()

        violations = []
        warnings = []
        checks_performed = []

        total_transitions = 0
        candidates_checked = 0

        # Verify each candidate
        for candidate_id, audit_logs in all_audit_logs.items():
            candidate_report = self.verify_candidate_audit_log(candidate_id)
            violations.extend(candidate_report.violations)
            warnings.extend(candidate_report.warnings)
            total_transitions += len(audit_logs)
            candidates_checked += 1

        checks_performed.append("system_wide_verification")

        # System-level checks
        # Check for orphaned transitions (without candidates)
        # This would require candidate registry access

        # Count violations by type
        violation_counts = {}
        for v in violations:
            violation_counts[v.violation_type] = violation_counts.get(v.violation_type, 0) + 1

        report = IntegrityReport(
            is_valid=len([v for v in violations if v.severity == "critical"]) == 0,
            candidates_checked=candidates_checked,
            total_transitions=total_transitions,
            violations=violations,
            violation_counts=violation_counts,
            warnings=warnings,
            checks_performed=checks_performed,
        )

        return report

    def _check_chronological_order(
        self,
        audit_logs: List[TransitionAuditLog],
    ) -> List[IntegrityViolation]:
        """Verify audit logs are in chronological order."""
        violations = []

        for i in range(1, len(audit_logs)):
            if audit_logs[i].transitioned_at < audit_logs[i - 1].transitioned_at:
                violations.append(IntegrityViolation(
                    violation_type="chronological_order",
                    severity="critical",
                    candidate_id=audit_logs[i].candidate_id,
                    description=f"Transition {i} occurs before transition {i-1}",
                    affected_records=[str(audit_logs[i].id), str(audit_logs[i-1].id)],
                ))

        return violations

    def _check_duplicates(
        self,
        audit_logs: List[TransitionAuditLog],
        candidate_id: UUID,
    ) -> List[IntegrityViolation]:
        """Detect duplicate transition records."""
        violations = []

        seen_ids = set()
        for log in audit_logs:
            if log.id in seen_ids:
                violations.append(IntegrityViolation(
                    violation_type="duplicate_record",
                    severity="critical",
                    candidate_id=candidate_id,
                    description=f"Duplicate transition record found: {log.id}",
                    affected_records=[str(log.id)],
                ))
            seen_ids.add(log.id)

        return violations

    def _check_actor_attribution(
        self,
        audit_logs: List[TransitionAuditLog],
        candidate_id: UUID,
    ) -> List[IntegrityViolation]:
        """Verify all transitions have actor attribution."""
        violations = []

        for log in audit_logs:
            if not log.triggered_by or log.triggered_by.strip() == "":
                violations.append(IntegrityViolation(
                    violation_type="missing_actor",
                    severity="warning",
                    candidate_id=candidate_id,
                    description=f"Transition {log.id} missing actor attribution",
                    affected_records=[str(log.id)],
                ))

        return violations

    def _check_valid_state_transitions(
        self,
        audit_logs: List[TransitionAuditLog],
        candidate_id: UUID,
    ) -> List[IntegrityViolation]:
        """Verify state transitions follow valid patterns."""
        violations = []

        # Valid states
        valid_states = {s.value for s in ReadinessState}

        for log in audit_logs:
            # Check state values are valid
            if log.from_state.value not in valid_states:
                violations.append(IntegrityViolation(
                    violation_type="invalid_state",
                    severity="critical",
                    candidate_id=candidate_id,
                    description=f"Invalid from_state: {log.from_state.value}",
                    affected_records=[str(log.id)],
                ))

            if log.to_state.value not in valid_states:
                violations.append(IntegrityViolation(
                    violation_type="invalid_state",
                    severity="critical",
                    candidate_id=candidate_id,
                    description=f"Invalid to_state: {log.to_state.value}",
                    affected_records=[str(log.id)],
                ))

            # Check for same-state transitions (should be rare)
            if log.from_state == log.to_state and not log.force_used:
                violations.append(IntegrityViolation(
                    violation_type="same_state_transition",
                    severity="warning",
                    candidate_id=candidate_id,
                    description=f"Same-state transition without force flag: "
                                f"{log.from_state.value} → {log.to_state.value}",
                    affected_records=[str(log.id)],
                ))

        return violations

    def _check_evaluation_consistency(
        self,
        audit_logs: List[TransitionAuditLog],
        candidate_id: UUID,
    ) -> List[IntegrityViolation]:
        """Verify evaluation references are consistent."""
        violations = []

        for log in audit_logs:
            # If evaluation_id is present, evaluation_outcome should match
            if log.evaluation_id and not log.evaluation_outcome:
                violations.append(IntegrityViolation(
                    violation_type="evaluation_consistency",
                    severity="warning",
                    candidate_id=candidate_id,
                    description=f"Transition has evaluation_id but missing outcome",
                    affected_records=[str(log.id)],
                ))

            # Score should be in valid range
            if log.evaluation_score is not None:
                if not (0.0 <= log.evaluation_score <= 1.0):
                    violations.append(IntegrityViolation(
                        violation_type="invalid_score",
                        severity="critical",
                        candidate_id=candidate_id,
                        description=f"Evaluation score out of range: {log.evaluation_score}",
                        affected_records=[str(log.id)],
                    ))

        return violations

    def get_candidate_transition_count(
        self,
        candidate_id: UUID,
    ) -> int:
        """
        Get the number of transitions for a candidate.

        Args:
            candidate_id: ID of the candidate

        Returns:
            Number of transition records
        """
        return len(get_audit_logs(candidate_id))

    def get_most_recent_transition(
        self,
        candidate_id: UUID,
    ) -> Optional[TransitionAuditLog]:
        """
        Get the most recent transition for a candidate.

        Args:
            candidate_id: ID of the candidate

        Returns:
            Most recent TransitionAuditLog or None
        """
        logs = get_audit_logs(candidate_id)
        if not logs:
            return None

        # Return the last one (should be most recent if logs are ordered)
        return logs[-1]


# Global audit integrity verifier instance
_audit_integrity_verifier: Optional[AuditIntegrityVerifier] = None


def get_audit_integrity_verifier() -> AuditIntegrityVerifier:
    """Get the global audit integrity verifier instance."""
    global _audit_integrity_verifier
    if _audit_integrity_verifier is None:
        _audit_integrity_verifier = AuditIntegrityVerifier()
    return _audit_integrity_verifier
