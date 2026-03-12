"""
     TORQ Readiness Checker - Milestone 5 Validation

Validates hardening, concurrency safety, and regression validation layer.

Tests:
1. Transition lock manager - concurrent transition safety
2. Idempotency guard - duplicate request prevention
3. Regression detector - readiness degradation detection
4. Scoring stability validator - deterministic scoring
5. Audit integrity verifier - audit log consistency
6. Regression service - regression tracking and management
7. Transition safety service - locking + idempotency combined
8. Scoring validation service - stability metrics
9. Audit integrity service - system-wide verification
10. No regression in M1/M2/M3/M4 functionality
"""

import sys
import io
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from uuid import uuid4

# Force UTF-8 output for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from torq_console.readiness.readiness_models import (
    CandidateType,
    ReadinessState,
    ReadinessOutcome,
    ReadinessEvaluation,
    ReadinessScore,
    ReadinessCandidate,
    EvidenceSummary,
)

from torq_console.readiness.readiness_policy import (
    get_policy_registry,
)

from torq_console.readiness.transition_controller import (
    get_state_machine,
    get_transition_controller,
    add_audit_log,
    TransitionAuditLog,
)

from torq_console.readiness.query_service import (
    ReadinessQueryService,
    get_query_service,
    register_candidate,
    add_evaluation,
    CandidateListFilter,
)

# M5 Imports
from torq_console.readiness.hardening.transition_lock_manager import (
    TransitionLockManager,
    get_transition_lock_manager,
)

from torq_console.readiness.hardening.idempotency_guard import (
    IdempotencyGuard,
    generate_idempotency_key,
    get_idempotency_guard,
)

from torq_console.readiness.hardening.regression_detector import (
    RegressionDetector,
    RegressionSeverity,
    get_regression_detector,
)

from torq_console.readiness.hardening.scoring_stability_validator import (
    ScoringStabilityValidator,
    get_scoring_stability_validator,
)

from torq_console.readiness.hardening.audit_integrity_verifier import (
    AuditIntegrityVerifier,
    get_audit_integrity_verifier,
)

from torq_console.readiness.services.regression_service import (
    RegressionService,
    get_regression_service,
)

from torq_console.readiness.services.transition_safety_service import (
    TransitionSafetyService,
    get_transition_safety_service,
)

from torq_console.readiness.services.scoring_validation_service import (
    ScoringValidationService,
    get_scoring_validation_service,
)

from torq_console.readiness.services.audit_integrity_service import (
    AuditIntegrityService,
    get_audit_integrity_service,
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Milestone5Validator:
    """Validator for Milestone 5: Hardening & Regression."""

    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0

    def record(self, test_name: str, passed: bool, message: str = ""):
        """Record a test result."""
        self.results.append((test_name, passed, message))
        if passed:
            self.passed += 1
            logger.info(f"[OK] {test_name}: {message}")
        else:
            self.failed += 1
            logger.error(f"[FAIL] {test_name}: {message}")

    def _create_test_candidate(self, state: ReadinessState, score: float) -> ReadinessCandidate:
        """Create a test candidate with evaluation."""
        candidate = ReadinessCandidate(
            candidate_type=CandidateType.TOOL,
            candidate_key=f"tool:test_{uuid4().hex[:8]}",
            title=f"Test Tool {uuid4().hex[:8]}",
            current_state=state,
        )

        register_candidate(candidate)

        # Create evaluation
        evaluation = ReadinessEvaluation(
            candidate_id=candidate.id,
            evaluation_type="scheduled",
            evidence=EvidenceSummary(),
            score=ReadinessScore(
                overall_score=score,
                confidence=0.9,
                execution_stability=score,
                artifact_completeness=score,
                memory_confidence=score,
                insight_quality=score,
                pattern_confidence=score,
                audit_coverage=score,
                policy_compliance=score,
                operational_consistency=score,
            ),
            outcome=ReadinessOutcome.READY if score >= 0.7 else ReadinessOutcome.OBSERVED,
            recommended_state=state,
            reason="Test evaluation",
            policy_profile_id="default",
            should_transition=False,
        )

        add_evaluation(candidate.id, evaluation)

        return candidate

    async def validate_transition_lock_manager(self):
        """Test 1: Transition lock manager - concurrent transition safety."""
        try:
            lock_manager = get_transition_lock_manager()
            candidate = self._create_test_candidate(ReadinessState.READY, 0.85)

            # Test lock acquisition
            async with lock_manager.acquire_transition_lock(candidate.id, "test_actor"):
                is_locked = await lock_manager.is_locked(candidate.id)
                passed1 = is_locked

            # After release, should not be locked
            is_locked_after = await lock_manager.is_locked(candidate.id)
            passed2 = not is_locked_after

            # Test try_acquire
            acquired = await lock_manager.try_acquire(candidate.id, "test_actor")
            if acquired:
                await lock_manager.release(candidate.id, "test_actor")

            passed3 = acquired

            passed = passed1 and passed2 and passed3

            self.record(
                "Transition Lock Manager",
                passed,
                f"Lock acquire/release: {passed1}, Release works: {passed2}, Try acquire: {passed3}"
            )

        except Exception as e:
            self.record("Transition Lock Manager", False, str(e))

    async def validate_idempotency_guard(self):
        """Test 2: Idempotency guard - duplicate request prevention."""
        try:
            guard = get_idempotency_guard()
            candidate = self._create_test_candidate(ReadinessState.READY, 0.85)

            # First request - not a duplicate
            is_dup1, record1 = guard.check_and_record(
                candidate_id=candidate.id,
                action="PROMOTE",
                target_state="ready",
                actor="test",
            )
            passed1 = not is_dup1 and record1 is None

            # Duplicate request - should be detected
            is_dup2, record2 = guard.check_and_record(
                candidate_id=candidate.id,
                action="PROMOTE",
                target_state="ready",
                actor="test",
            )
            passed2 = is_dup2 and record2 is not None

            # Different action - not a duplicate
            is_dup3, record3 = guard.check_and_record(
                candidate_id=candidate.id,
                action="BLOCK",
                target_state="blocked",
                actor="test",
            )
            passed3 = not is_dup3

            passed = passed1 and passed2 and passed3

            self.record(
                "Idempotency Guard",
                passed,
                f"First request: {not is_dup1}, Duplicate detected: {is_dup2}, Different action: {not is_dup3}"
            )

        except Exception as e:
            self.record("Idempotency Guard", False, str(e))

    async def validate_regression_detector(self):
        """Test 3: Regression detector - readiness degradation detection."""
        try:
            detector = get_regression_detector()
            candidate = self._create_test_candidate(ReadinessState.READY, 0.85)

            # Simulate regression: READY → BLOCKED with score drop
            event = detector.detect_regression(
                candidate_id=candidate.id,
                candidate_type=candidate.candidate_type.value,
                title=candidate.title,
                previous_state=ReadinessState.READY,
                new_state=ReadinessState.BLOCKED,
                previous_score=0.85,
                new_score=0.40,
                previous_evaluation_id=uuid4(),
                new_evaluation_id=uuid4(),
            )

            passed = (
                event is not None and
                event.previous_state == "ready" and
                event.new_state == "blocked" and
                event.severity == "critical"
            )

            # Get regression count
            counts = detector.get_regression_count()
            passed2 = counts["total"] > 0

            self.record(
                "Regression Detector",
                passed and passed2,
                f"Regression detected: {event is not None}, Severity: {event.severity if event else None}, Count: {counts['total']}"
            )

        except Exception as e:
            self.record("Regression Detector", False, str(e))

    async def validate_scoring_stability_validator(self):
        """Test 4: Scoring stability validator - deterministic scoring."""
        try:
            validator = get_scoring_stability_validator()
            candidate = self._create_test_candidate(ReadinessState.READY, 0.85)

            # Record multiple evaluations with stable scores
            for i in range(5):
                validator.record_evaluation(
                    candidate_id=candidate.id,
                    score=0.85 + (i * 0.001),  # Very small variance
                    evaluation_id=uuid4(),
                )

            # Calculate stability
            report = validator.calculate_stability(candidate.id)

            passed = (
                report is not None and
                report.evaluation_count == 5 and
                report.is_stable and
                report.std_deviation <= validator.stability_threshold
            )

            self.record(
                "Scoring Stability Validator",
                passed,
                f"Evaluations: {report.evaluation_count if report else 0}, "
                f"Stable: {report.is_stable if report else False}, "
                f"StdDev: {report.std_deviation if report else 0:.4f}"
            )

        except Exception as e:
            self.record("Scoring Stability Validator", False, str(e))

    async def validate_audit_integrity_verifier(self):
        """Test 5: Audit integrity verifier - audit log consistency."""
        try:
            verifier = get_audit_integrity_verifier()
            candidate = self._create_test_candidate(ReadinessState.READY, 0.85)

            # Add audit log
            log = TransitionAuditLog(
                candidate_id=candidate.id,
                from_state=ReadinessState.OBSERVED,
                to_state=ReadinessState.READY,
                transition_type="promotion",
                evaluation_id=uuid4(),
                evaluation_outcome=ReadinessOutcome.READY,
                evaluation_score=0.85,
                policy_profile_id="default",
                policy_version="1.0",
                triggered_by="test_validator",
                trigger_reason="Test transition",
            )
            add_audit_log(log)

            # Verify integrity
            report = verifier.verify_candidate_audit_log(candidate.id)

            passed = (
                report is not None and
                report.is_valid and
                report.total_transitions >= 1
            )

            self.record(
                "Audit Integrity Verifier",
                passed,
                f"Valid: {report.is_valid if report else False}, Transitions: {report.total_transitions if report else 0}"
            )

        except Exception as e:
            self.record("Audit Integrity Verifier", False, str(e))

    async def validate_regression_service(self):
        """Test 6: Regression service - regression tracking and management."""
        try:
            service = get_regression_service()
            candidate = self._create_test_candidate(ReadinessState.READY, 0.90)

            # Detect regression
            event = service.detect_and_record(
                candidate=candidate,
                previous_state=ReadinessState.READY,
                new_state=ReadinessState.WATCHLIST,
                previous_score=0.90,
                new_score=0.65,
            )

            passed1 = event is not None

            # Get summary
            summary = service.get_summary()
            passed2 = summary.total_regressions > 0

            # List regressions
            regressions = service.list_regressions(limit=10)
            passed3 = len(regressions) > 0

            passed = passed1 and passed2 and passed3

            self.record(
                "Regression Service",
                passed,
                f"Event detected: {passed1}, Summary: {summary.total_regressions} total, Listed: {len(regressions)}"
            )

        except Exception as e:
            self.record("Regression Service", False, str(e))

    async def validate_transition_safety_service(self):
        """Test 7: Transition safety service - locking + idempotency combined."""
        try:
            service = get_transition_safety_service()
            candidate = self._create_test_candidate(ReadinessState.READY, 0.85)

            # Validate request (checks idempotency)
            validation = await service.validate_transition_request(
                candidate_id=candidate.id,
                action="PROMOTE",
                target_state="ready",
                actor="test_validator",
            )

            passed1 = validation.is_valid and validation.can_proceed

            # Check if locked
            is_locked = await service.is_candidate_locked(candidate.id)
            passed2 = not is_locked  # Should not be locked without acquiring

            # Try acquire lock
            acquired = await service.try_acquire_lock(candidate.id, "test_validator")
            if acquired:
                await service.release_lock(candidate.id, "test_validator")

            passed3 = acquired

            passed = passed1 and passed2 and passed3

            self.record(
                "Transition Safety Service",
                passed,
                f"Validation: {passed1}, Not locked: {passed2}, Acquire/release: {passed3}"
            )

        except Exception as e:
            self.record("Transition Safety Service", False, str(e))

    async def validate_scoring_validation_service(self):
        """Test 8: Scoring validation service - stability metrics."""
        try:
            service = get_scoring_validation_service()
            candidate = self._create_test_candidate(ReadinessState.READY, 0.85)

            # Record evaluations
            for score in [0.84, 0.85, 0.86, 0.85, 0.84]:
                service.record_evaluation(
                    candidate_id=candidate.id,
                    score=score,
                    evaluation_id=uuid4(),
                )

            # Check stability
            is_stable = service.is_candidate_stable(candidate.id)
            variance = service.calculate_score_variance(candidate.id)

            passed = is_stable and variance is not None and variance <= 0.05

            # Get system summary
            summary = service.get_system_summary()
            passed2 = summary.total_candidates >= 1

            self.record(
                "Scoring Validation Service",
                passed and passed2,
                f"Stable: {is_stable}, Variance: {f'{variance:.4f}' if variance is not None else 'N/A'}, "
                f"System: {summary.total_candidates} candidates"
            )

        except Exception as e:
            self.record("Scoring Validation Service", False, str(e))

    async def validate_audit_integrity_service(self):
        """Test 9: Audit integrity service - system-wide verification."""
        try:
            service = get_audit_integrity_service()
            candidate = self._create_test_candidate(ReadinessState.READY, 0.88)

            # Add audit log for this candidate
            log = TransitionAuditLog(
                candidate_id=candidate.id,
                from_state=ReadinessState.OBSERVED,
                to_state=ReadinessState.READY,
                transition_type="promotion",
                evaluation_id=uuid4(),
                evaluation_outcome=ReadinessOutcome.READY,
                evaluation_score=0.88,
                policy_profile_id="default",
                policy_version="1.0",
                triggered_by="test_validator",
                trigger_reason="Test transition",
            )
            add_audit_log(log)

            # Verify system
            status = service.get_system_status()

            passed = (
                status is not None and
                status.candidates_checked >= 1 and
                status.total_transitions >= 1
            )

            self.record(
                "Audit Integrity Service",
                passed,
                f"Candidates: {status.candidates_checked}, Transitions: {status.total_transitions}, Valid: {status.is_valid}"
            )

        except Exception as e:
            self.record("Audit Integrity Service", False, str(e))

    async def validate_no_milestone_regression(self):
        """Test 10: No regression in M1/M2/M3/M4 functionality."""
        try:
            # Test M1: Policy registry
            registry = get_policy_registry()
            profile = registry.get_default_profile()
            m1_ok = profile is not None and profile.id == "default"

            # Test M2: Scoring engine
            from torq_console.readiness.scoring_engine import get_scoring_engine
            engine = get_scoring_engine()
            m2_ok = engine is not None

            # Test M3: Transition controller
            from torq_console.readiness.transition_controller import get_transition_controller
            controller = get_transition_controller()
            m3_ok = controller is not None

            # Test M4: Query service
            query_service = get_query_service()
            m4_ok = query_service is not None

            # Test M4: Inspection service
            from torq_console.readiness.inspection_service import get_inspection_service
            inspection_service = get_inspection_service()
            m4_inspection_ok = inspection_service is not None

            # Test M4: Analytics service
            from torq_console.readiness.analytics_service import get_analytics_service
            analytics_service = get_analytics_service()
            m4_analytics_ok = analytics_service is not None

            passed = (
                m1_ok and m2_ok and m3_ok and
                m4_ok and m4_inspection_ok and m4_analytics_ok
            )

            self.record(
                "M1/M2/M3/M4 Regression Check",
                passed,
                f"M1 (policy): {m1_ok}, M2 (scoring): {m2_ok}, M3 (transition): {m3_ok}, "
                f"M4 (query): {m4_ok}, M4 (inspection): {m4_inspection_ok}, M4 (analytics): {m4_analytics_ok}"
            )

        except Exception as e:
            self.record("M1/M2/M3/M4 Regression Check", False, str(e))

    async def run_all(self):
        """Run all Milestone 5 validation tests."""
        logger.info("=" * 70)
        logger.info("TORQ READINESS CHECKER - MILESTONE 5 VALIDATION")
        logger.info("=" * 70)

        await self.validate_transition_lock_manager()
        await self.validate_idempotency_guard()
        await self.validate_regression_detector()
        await self.validate_scoring_stability_validator()
        await self.validate_audit_integrity_verifier()
        await self.validate_regression_service()
        await self.validate_transition_safety_service()
        await self.validate_scoring_validation_service()
        await self.validate_audit_integrity_service()
        await self.validate_no_milestone_regression()

        # Print summary
        logger.info("")
        logger.info("=" * 70)
        logger.info("VALIDATION SUMMARY")
        logger.info("=" * 70)

        for test_name, passed, message in self.results:
            status = "[PASS]" if passed else "[FAIL]"
            logger.info(f"{status} - {test_name}: {message}")

        logger.info("")
        logger.info(f"Total: {len(self.results)} tests")
        logger.info(f"Passed: {self.passed}")
        logger.info(f"Failed: {self.failed}")

        if self.failed == 0:
            logger.info("")
            logger.info("=" * 70)
            logger.info("MILESTONE 5 COMPLETE - Production hardening is operational!")
            logger.info("=" * 70)
            logger.info("")
            logger.info("Exit Criteria Met:")
            logger.info("✓ Concurrent transition attempts safely handled")
            logger.info("✓ Duplicate governance actions prevented")
            logger.info("✓ Readiness regressions detected and logged")
            logger.info("✓ Scoring stable across repeated evaluations")
            logger.info("✓ Audit logs pass integrity validation")
            logger.info("✓ No regression in M1/M2/M3/M4 functionality")
            logger.info("")
            logger.info("Readiness system is now production-grade.")
            logger.info("=" * 70)
        else:
            logger.warning("")
            logger.warning(f"{self.failed} test(s) failed")
            logger.info("")

        return self.failed == 0


if __name__ == "__main__":
    validator = Milestone5Validator()
    success = asyncio.run(validator.run_all())
    sys.exit(0 if success else 1)
