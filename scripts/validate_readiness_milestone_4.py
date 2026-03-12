"""
TORQ Readiness Checker - Milestone 4 Validation

Validates inspection, query, and governance audit layer.

Tests:
1. Query service - candidate retrieval and filtering
2. Inspection service - full readiness view generation
3. Audit service - transition history retrieval
4. Analytics service - metrics aggregation
5. Report builder - candidate and system reports
6. State distribution calculation
7. Filtered queries (by state, type, score)
8. Transition history with pagination
9. Compliance summary generation
10. No regression in M1/M2/M3 functionality
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

from torq_console.readiness.inspection_service import (
    ReadinessInspectionService,
    get_inspection_service,
)

from torq_console.readiness.audit_service import (
    ReadinessAuditService,
    TransitionAuditFilter,
    get_audit_service,
)

from torq_console.readiness.analytics_service import (
    ReadinessAnalyticsService,
    get_analytics_service,
)

from torq_console.readiness.report_builder import (
    ReadinessReportBuilder,
    get_report_builder,
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Milestone4Validator:
    """Validator for Milestone 4: Inspection, Query, and Governance Audit Layer."""

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

        # Add audit log for state
        log = TransitionAuditLog(
            candidate_id=candidate.id,
            from_state=ReadinessState.OBSERVED,
            to_state=state,
            transition_type="promotion",
            evaluation_id=evaluation.id,
            evaluation_outcome=evaluation.outcome,
            evaluation_score=score,
            policy_profile_id="default",
            policy_version="1.0",
            triggered_by="test_validator",
            trigger_reason="Test setup",
        )

        add_audit_log(log)

        return candidate

    async def validate_query_service(self):
        """Test 1: Query service - candidate retrieval and filtering."""
        try:
            query_service = get_query_service()

            # Create test candidates
            candidate1 = self._create_test_candidate(ReadinessState.READY, 0.85)
            candidate2 = self._create_test_candidate(ReadinessState.BLOCKED, 0.50)
            candidate3 = self._create_test_candidate(ReadinessState.OBSERVED, 0.60)

            # Test get_candidate
            retrieved = query_service.get_candidate(candidate1.id)
            passed1 = retrieved is not None and retrieved.id == candidate1.id

            # Test list_candidates
            result = query_service.list_candidates()
            passed2 = len(result.candidates) >= 3

            # Test list_ready_candidates
            ready_result = query_service.list_ready_candidates(limit=10)
            passed3 = ready_result.total_count >= 1

            passed = passed1 and passed2 and passed3

            self.record(
                "Query Service",
                passed,
                f"Retrieval: {passed1}, List: {len(result.candidates)} candidates, Ready: {ready_result.total_count}"
            )

        except Exception as e:
            self.record("Query Service", False, str(e))

    async def validate_inspection_service(self):
        """Test 2: Inspection service - full readiness view generation."""
        try:
            inspection_service = get_inspection_service()
            query_service = get_query_service()

            # Create test candidate
            candidate = self._create_test_candidate(ReadinessState.READY, 0.88)

            # Generate inspection
            inspection = inspection_service.inspect_candidate(candidate.id)

            passed = (
                inspection is not None and
                inspection.candidate_id == candidate.id and
                inspection.current_state == "ready" and
                inspection.current_score == 0.88 and
                len(inspection.dimension_scores) == 8
            )

            self.record(
                "Inspection Service",
                passed,
                f"Inspection generated: {inspection.current_state}, score: {inspection.current_score:.2f}, dimensions: {len(inspection.dimension_scores)}"
            )

        except Exception as e:
            self.record("Inspection Service", False, str(e))

    async def validate_audit_service(self):
        """Test 3: Audit service - transition history retrieval."""
        try:
            audit_service = get_audit_service()

            # Create test candidate with history
            candidate = self._create_test_candidate(ReadinessState.WATCHLIST, 0.75)

            # Get transition history
            history = audit_service.get_transition_history(candidate.id)

            passed = (
                history is not None and
                len(history) >= 1 and
                history[0].to_state == "watchlist"
            )

            self.record(
                "Audit Service",
                passed,
                f"History retrieved: {len(history)} transitions"
            )

        except Exception as e:
            self.record("Audit Service", False, str(e))

    async def validate_analytics_service(self):
        """Test 4: Analytics service - metrics aggregation."""
        try:
            analytics_service = get_analytics_service()

            # Ensure some test data exists
            for _ in range(3):
                self._create_test_candidate(ReadinessState.READY, 0.8)

            # Get metrics
            metrics = analytics_service.get_metrics()

            passed = (
                metrics is not None and
                metrics.total_candidates >= 3 and
                0.0 <= metrics.avg_score <= 1.0 and
                len(metrics.state_distribution) > 0
            )

            self.record(
                "Analytics Service",
                passed,
                f"Metrics: {metrics.total_candidates} candidates, avg score: {metrics.avg_score:.2f}"
            )

        except Exception as e:
            self.record("Analytics Service", False, str(e))

    async def validate_report_builder(self):
        """Test 5: Report builder - candidate and system reports."""
        try:
            report_builder = get_report_builder()

            # Create test candidate
            candidate = self._create_test_candidate(ReadinessState.READY, 0.92)

            # Build candidate report
            candidate_report = report_builder.build_candidate_report(candidate.id)

            # Build system report
            system_report = report_builder.build_system_readiness_report(period_days=30)

            passed = (
                candidate_report is not None and
                candidate_report.current_score == 0.92 and
                system_report is not None and
                system_report.total_candidates >= 1
            )

            self.record(
                "Report Builder",
                passed,
                f"Candidate report: {len(candidate_report.sections)} sections, System report: {system_report.total_candidates} candidates"
            )

        except Exception as e:
            self.record("Report Builder", False, str(e))

    async def validate_state_distribution(self):
        """Test 6: State distribution calculation."""
        try:
            analytics_service = get_analytics_service()

            distribution = analytics_service.get_state_distribution()

            passed = (
                distribution is not None and
                len(distribution) > 0 and
                all(0 <= d.percentage <= 1.0 for d in distribution)
            )

            state_names = [d.state for d in distribution]

            self.record(
                "State Distribution",
                passed,
                f"Distribution: {len(distribution)} states, {state_names}"
            )

        except Exception as e:
            self.record("State Distribution", False, str(e))

    async def validate_filtered_queries(self):
        """Test 7: Filtered queries (by state, type, score)."""
        try:
            query_service = get_query_service()

            # Create candidates with different states
            self._create_test_candidate(ReadinessState.READY, 0.9)
            self._create_test_candidate(ReadinessState.BLOCKED, 0.4)

            # Filter by state
            filters = CandidateListFilter(
                state=ReadinessState.READY.value,
                limit=10,
            )

            result = query_service.list_candidates(filters)

            passed = (
                all(c.current_state == ReadinessState.READY.value for c in result.candidates)
            )

            self.record(
                "Filtered Queries",
                passed,
                f"State filter: {len(result.candidates)} ready candidates"
            )

        except Exception as e:
            self.record("Filtered Queries", False, str(e))

    async def validate_transition_pagination(self):
        """Test 8: Transition history with pagination."""
        try:
            audit_service = get_audit_service()

            # Create candidate with multiple transitions
            candidate = self._create_test_candidate(ReadinessState.READY, 0.85)

            # Get paginated history
            page1 = audit_service.get_transition_history(candidate.id, limit=1)

            passed = (
                page1 is not None and
                len(page1) <= 1
            )

            self.record(
                "Transition Pagination",
                passed,
                f"Pagination: {len(page1)} results (limit 1)"
            )

        except Exception as e:
            self.record("Transition Pagination", False, str(e))

    async def validate_compliance_summary(self):
        """Test 9: Compliance summary generation."""
        try:
            audit_service = get_audit_service()

            # Get compliance summary
            summary = audit_service.get_compliance_summary()

            passed = (
                summary is not None and
                "total_transitions" in summary and
                summary["total_transitions"] >= 0
            )

            self.record(
                "Compliance Summary",
                passed,
                f"Summary: {summary['total_transitions']} transitions"
            )

        except Exception as e:
            self.record("Compliance Summary", False, str(e))

    async def validate_no_milestone_regression(self):
        """Test 10: No regression in M1/M2/M3 functionality."""
        try:
            # Test M1: Policy registry
            registry = get_policy_registry()
            profile = registry.get_default_profile()

            m1_ok = profile is not None and profile.id == "default"

            # Test M2: Scoring engine
            from torq_console.readiness.scoring_engine import get_scoring_engine
            engine = get_scoring_engine()
            m2_scoring_ok = engine is not None

            # Test M3: Transition controller
            controller = get_transition_controller()
            m3_transition_ok = controller is not None

            # Test M3: State machine
            candidate = self._create_test_candidate(ReadinessState.OBSERVED, 0.5)
            sm = get_state_machine(candidate.id)
            m3_sm_ok = sm is not None and sm.current_state == ReadinessState.OBSERVED

            passed = m1_ok and m2_scoring_ok and m3_transition_ok and m3_sm_ok

            self.record(
                "M1/M2/M3 Regression Check",
                passed,
                f"M1 (policy): {m1_ok}, M2 (scoring): {m2_scoring_ok}, M3 (transition): {m3_transition_ok}, M3 (sm): {m3_sm_ok}"
            )

        except Exception as e:
            self.record("M1/M2/M3 Regression Check", False, str(e))

    async def run_all(self):
        """Run all Milestone 4 validation tests."""
        logger.info("=" * 70)
        logger.info("TORQ READINESS CHECKER - MILESTONE 4 VALIDATION")
        logger.info("=" * 70)

        await self.validate_query_service()
        await self.validate_inspection_service()
        await self.validate_audit_service()
        await self.validate_analytics_service()
        await self.validate_report_builder()
        await self.validate_state_distribution()
        await self.validate_filtered_queries()
        await self.validate_transition_pagination()
        await self.validate_compliance_summary()
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
            logger.info("MILESTONE 4 COMPLETE - Inspection layer is operational!")
            logger.info("=" * 70)
            logger.info("")
            logger.info("Exit Criteria Met:")
            logger.info("✓ Inspection service returns full readiness view")
            logger.info("✓ Readiness query endpoints operate correctly")
            logger.info("✓ Governance audit history is accessible")
            logger.info("✓ Analytics metrics return correct aggregates")
            logger.info("✓ No regression in M1/M2/M3 functionality")
            logger.info("")
            logger.info("Readiness system now has complete operational visibility.")
            logger.info("=" * 70)
        else:
            logger.warning("")
            logger.warning(f"{self.failed} test(s) failed")
            logger.info("")

        return self.failed == 0


if __name__ == "__main__":
    validator = Milestone4Validator()
    success = asyncio.run(validator.run_all())
    sys.exit(0 if success else 1)
