"""
TORQ Readiness Checker - Services Layer

Milestone 5: Production-grade services for readiness governance.

This module provides high-level service interfaces for:
- Regression detection and management
- Transition safety (locking + idempotency)
- Scoring stability validation
- Audit integrity verification
"""

from .regression_service import (
    RegressionService,
    RegressionSummary,
    get_regression_service,
)

from .transition_safety_service import (
    TransitionSafetyService,
    TransitionValidationResult,
    get_transition_safety_service,
)

from .scoring_validation_service import (
    ScoringValidationService,
    SystemStabilitySummary,
    get_scoring_validation_service,
)

from .audit_integrity_service import (
    AuditIntegrityService,
    SystemIntegrityStatus,
    get_audit_integrity_service,
)


__all__ = [
    # Regression Service
    "RegressionService",
    "RegressionSummary",
    "get_regression_service",

    # Transition Safety Service
    "TransitionSafetyService",
    "TransitionValidationResult",
    "get_transition_safety_service",

    # Scoring Validation Service
    "ScoringValidationService",
    "SystemStabilitySummary",
    "get_scoring_validation_service",

    # Audit Integrity Service
    "AuditIntegrityService",
    "SystemIntegrityStatus",
    "get_audit_integrity_service",
]
