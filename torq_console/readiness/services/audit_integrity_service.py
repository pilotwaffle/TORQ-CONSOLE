"""
TORQ Readiness Checker - Audit Integrity Service

Milestone 5: Service for audit log integrity verification.

Provides interface for validating audit log consistency
and completeness across the readiness system.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


logger = logging.getLogger(__name__)


# Import from hardening layer
from ..hardening.audit_integrity_verifier import (
    AuditIntegrityVerifier,
    IntegrityReport,
    IntegrityViolation,
    get_audit_integrity_verifier,
)


# ============================================================================
# System Integrity Status
# ============================================================================

class SystemIntegrityStatus(BaseModel):
    """
    High-level system integrity status.
    """
    is_valid: bool
    candidates_checked: int
    total_transitions: int

    critical_violations: int
    warning_violations: int
    total_violations: int

    violation_types: Dict[str, int]

    has_chronological_issues: bool
    has_duplicate_records: bool
    has_missing_actors: bool
    has_invalid_states: bool


# ============================================================================
# Audit Integrity Service
# ============================================================================

class AuditIntegrityService:
    """
    Service for audit log integrity verification.

    Validates audit logs for consistency, completeness,
    and correctness of governance history.
    """

    def __init__(self):
        """Initialize the audit integrity service."""
        self.verifier = get_audit_integrity_verifier()

    def verify_candidate(
        self,
        candidate_id: UUID,
    ) -> IntegrityReport:
        """
        Verify audit log integrity for a candidate.

        Args:
            candidate_id: ID of the candidate to verify

        Returns:
            IntegrityReport with verification results
        """
        return self.verifier.verify_candidate_audit_log(candidate_id)

    def verify_system(self) -> IntegrityReport:
        """
        Verify audit log integrity across the entire system.

        Returns:
            IntegrityReport with system-wide results
        """
        return self.verifier.verify_system_audit_integrity()

    def get_system_status(self) -> SystemIntegrityStatus:
        """
        Get high-level system integrity status.

        Returns:
            SystemIntegrityStatus with summary information
        """
        report = self.verify_system()

        critical_count = sum(
            1 for v in report.violations
            if v.severity == "critical"
        )
        warning_count = sum(
            1 for v in report.violations
            if v.severity == "warning"
        )

        # Check for specific issue types
        has_chronological = any(
            v.violation_type == "chronological_order"
            for v in report.violations
        )
        has_duplicates = any(
            v.violation_type == "duplicate_record"
            for v in report.violations
        )
        has_missing_actors = any(
            v.violation_type == "missing_actor"
            for v in report.violations
        )
        has_invalid_states = any(
            v.violation_type == "invalid_state"
            for v in report.violations
        )

        return SystemIntegrityStatus(
            is_valid=report.is_valid,
            candidates_checked=report.candidates_checked,
            total_transitions=report.total_transitions,
            critical_violations=critical_count,
            warning_violations=warning_count,
            total_violations=len(report.violations),
            violation_types=report.violation_counts,
            has_chronological_issues=has_chronological,
            has_duplicate_records=has_duplicates,
            has_missing_actors=has_missing_actors,
            has_invalid_states=has_invalid_states,
        )

    def get_transition_count(
        self,
        candidate_id: UUID,
    ) -> int:
        """
        Get number of transitions for a candidate.

        Args:
            candidate_id: ID of the candidate

        Returns:
            Number of transition records
        """
        return self.verifier.get_candidate_transition_count(candidate_id)

    def get_most_recent_transition(
        self,
        candidate_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        """
        Get most recent transition for a candidate.

        Args:
            candidate_id: ID of the candidate

        Returns:
            Dictionary with transition data or None
        """
        log = self.verifier.get_most_recent_transition(candidate_id)
        if log:
            return {
                "id": str(log.id),
                "from_state": log.from_state.value,
                "to_state": log.to_state.value,
                "transitioned_at": log.transitioned_at.isoformat(),
                "triggered_by": log.triggered_by,
                "force_used": log.force_used,
            }
        return None

    def get_violations_by_type(
        self,
        violation_type: str,
        limit: int = 100,
    ) -> List[IntegrityViolation]:
        """
        Get violations of a specific type.

        Args:
            violation_type: Type of violation to filter
            limit: Maximum number of violations

        Returns:
            List of matching violations
        """
        report = self.verify_system()
        matching = [
            v for v in report.violations
            if v.violation_type == violation_type
        ]
        return matching[:limit]

    def get_candidate_violations(
        self,
        candidate_id: UUID,
    ) -> List[IntegrityViolation]:
        """
        Get violations for a specific candidate.

        Args:
            candidate_id: ID of the candidate

        Returns:
            List of violations for the candidate
        """
        report = self.verify_candidate(candidate_id)
        return report.violations


# Global audit integrity service instance
_audit_integrity_service: Optional[AuditIntegrityService] = None


def get_audit_integrity_service() -> AuditIntegrityService:
    """Get the global audit integrity service instance."""
    global _audit_integrity_service
    if _audit_integrity_service is None:
        _audit_integrity_service = AuditIntegrityService()
    return _audit_integrity_service
