"""
TORQ Readiness Checker - Hardening Layer

Milestone 5: Production-grade reliability controls.

This module provides:
- TransitionLockManager: Prevent concurrent transitions
- IdempotencyGuard: Ensure duplicate-safe operations
- RegressionDetector: Detect readiness degradation
- ScoringStabilityValidator: Validate scoring consistency
- AuditIntegrityVerifier: Validate audit log consistency
"""

from .transition_lock_manager import (
    TransitionLockManager,
    get_transition_lock_manager,
)

from .idempotency_guard import (
    IdempotencyGuard,
    IdempotencyRecord,
    generate_idempotency_key,
    get_idempotency_guard,
)

from .regression_detector import (
    RegressionDetector,
    RegressionEvent,
    RegressionSeverity,
    get_regression_detector,
)

from .scoring_stability_validator import (
    ScoringStabilityValidator,
    ScoreHistoryEntry,
    StabilityReport,
    get_scoring_stability_validator,
)

from .audit_integrity_verifier import (
    AuditIntegrityVerifier,
    IntegrityViolation,
    IntegrityReport,
    get_audit_integrity_verifier,
)


__all__ = [
    # Transition Lock Manager
    "TransitionLockManager",
    "get_transition_lock_manager",

    # Idempotency Guard
    "IdempotencyGuard",
    "IdempotencyRecord",
    "generate_idempotency_key",
    "get_idempotency_guard",

    # Regression Detector
    "RegressionDetector",
    "RegressionEvent",
    "RegressionSeverity",
    "get_regression_detector",

    # Scoring Stability Validator
    "ScoringStabilityValidator",
    "ScoreHistoryEntry",
    "StabilityReport",
    "get_scoring_stability_validator",

    # Audit Integrity Verifier
    "AuditIntegrityVerifier",
    "IntegrityViolation",
    "IntegrityReport",
    "get_audit_integrity_verifier",
]
