"""
TORQ Readiness Checker - Milestone 3 Validation

Validates transition controller and governance actions.

Tests:
1. State machine instantiation and state tracking
2. State transitions (observed → watchlist → ready)
3. Invalid transition blocking
4. Governance action execution (promote, demote, block)
5. Forced transitions
6. Transition audit logging
7. Auto-transition from evaluation
8. Transition policy validation
9. Full transition request workflow
10. No regression in M1/M2 functionality
"""

import sys
import io
import asyncio
from pathlib import Path
from datetime import datetime
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
    EvidenceSummary,
    TransitionRequest,
    TransitionResult,
)

from torq_console.readiness.readiness_policy import (
    get_policy_registry,
)

from torq_console.readiness.evidence_collector import (
    get_evidence_orchestrator,
)

from torq_console.readiness.scoring_engine import (
    get_scoring_engine,
    ScoringContext,
)

from torq_console.readiness.transition_controller import (
    # State Machine
    ReadinessStateMachine,
    get_state_machine,

    # Governance Engine
    GovernanceActionEngine,
    GovernanceActionType,
    GovernanceAction,
    get_governance_engine,

    # Policy Validator
    TransitionPolicyValidator,

    # Transition Controller
    ReadinessTransitionController,
    get_transition_controller,

    # Audit Log
    TransitionAuditLog,
    get_audit_logs,
    add_audit_log,
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Milestone3Validator:
    """Validator for Milestone 3: Transition Controller and Governance Actions."""

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

    async def validate_state_machine_instantiation(self):
        """Test 1: State machine instantiation and state tracking."""
        try:
            candidate_id = uuid4()
            sm = get_state_machine(candidate_id)

            passed = (
                sm.candidate_id == candidate_id and
                sm.current_state == ReadinessState.OBSERVED and
                len(sm.state_history) == 1 and
                sm.transition_count == 0
            )

            self.record(
                "State Machine Instantiation",
                passed,
                f"State machine created with initial state OBSERVED, history: {len(sm.state_history)}"
            )

        except Exception as e:
            self.record("State Machine Instantiation", False, str(e))

    async def validate_state_transitions(self):
        """Test 2: State transitions (observed → watchlist → ready)."""
        try:
            candidate_id = uuid4()
            sm = get_state_machine(candidate_id)

            # Test observed → watchlist
            event1 = sm.transition_to(ReadinessState.WATCHLIST, "promotion")
            passed1 = (
                sm.current_state == ReadinessState.WATCHLIST and
                event1.from_state == ReadinessState.OBSERVED and
                event1.to_state == ReadinessState.WATCHLIST
            )

            # Test watchlist → ready
            event2 = sm.transition_to(ReadinessState.READY, "promotion")
            passed2 = (
                sm.current_state == ReadinessState.READY and
                event2.from_state == ReadinessState.WATCHLIST and
                event2.to_state == ReadinessState.READY
            )

            passed = passed1 and passed2

            self.record(
                "State Transitions",
                passed,
                f"OBSERVED → WATCHLIST → READY: {sm.current_state.value}, transitions: {sm.transition_count}"
            )

        except Exception as e:
            self.record("State Transitions", False, str(e))

    async def validate_invalid_transition_blocking(self):
        """Test 3: Invalid transition blocking."""
        try:
            candidate_id = uuid4()
            sm = get_state_machine(candidate_id)

            # Try invalid transition: WATCHLIST → REGRESSED (not allowed)
            can_transition = sm.can_transition_to(ReadinessState.REGRESSED)

            passed = not can_transition  # Should NOT be able to transition

            self.record(
                "Invalid Transition Blocking",
                passed,
                f"Invalid transition correctly blocked: can_transition={can_transition}"
            )

        except Exception as e:
            self.record("Invalid Transition Blocking", False, str(e))

    async def validate_governance_actions(self):
        """Test 4: Governance action execution (promote, demote, block)."""
        try:
            engine = get_governance_engine()
            candidate_id = uuid4()

            # Test promote action
            promote_action = GovernanceAction(
                action_type=GovernanceActionType.PROMOTE,
                candidate_id=candidate_id,
                target_state=ReadinessState.WATCHLIST,
                requested_by="test_validator",
            )
            promote_result = await engine.execute_action(
                promote_action,
                ReadinessState.OBSERVED,
            )

            # Test demote action
            demote_action = GovernanceAction(
                action_type=GovernanceActionType.DEMOTE,
                candidate_id=candidate_id,
                target_state=ReadinessState.OBSERVED,
                requested_by="test_validator",
            )
            demote_result = await engine.execute_action(
                demote_action,
                ReadinessState.WATCHLIST,
            )

            # Test block action
            block_action = GovernanceAction(
                action_type=GovernanceActionType.BLOCK,
                candidate_id=candidate_id,
                requested_by="test_validator",
                reason="Test block",
            )
            block_result = await engine.execute_action(
                block_action,
                ReadinessState.OBSERVED,
            )

            passed = (
                promote_result.success and
                demote_result.success and
                block_result.success
            )

            self.record(
                "Governance Actions",
                passed,
                f"Promote: {promote_result.success}, Demote: {demote_result.success}, Block: {block_result.success}"
            )

        except Exception as e:
            self.record("Governance Actions", False, str(e))

    async def validate_forced_transitions(self):
        """Test 5: Forced transitions."""
        try:
            candidate_id = uuid4()
            sm = get_state_machine(candidate_id)

            # Force an invalid transition
            event = sm.transition_to(
                ReadinessState.BLOCKED,
                "forced",
                forced=True,
            )

            passed = (
                sm.current_state == ReadinessState.BLOCKED and
                sm.forced_transition_count == 1
            )

            self.record(
                "Forced Transitions",
                passed,
                f"Forced transition to BLOCKED: {sm.current_state.value}, forced count: {sm.forced_transition_count}"
            )

        except Exception as e:
            self.record("Forced Transitions", False, str(e))

    async def validate_audit_logging(self):
        """Test 6: Transition audit logging."""
        try:
            candidate_id = uuid4()

            # Create an audit log entry
            log = TransitionAuditLog(
                candidate_id=candidate_id,
                from_state=ReadinessState.OBSERVED,
                to_state=ReadinessState.READY,
                transition_type="promotion",
                evaluation_id=uuid4(),
                evaluation_outcome=ReadinessOutcome.READY,
                evaluation_score=0.85,
                policy_profile_id="default",
                policy_version="1.0",
                triggered_by="test_validator",
                trigger_reason="Test promotion",
            )

            add_audit_log(log)

            # Retrieve audit logs
            logs = get_audit_logs(candidate_id)

            passed = (
                len(logs) == 1 and
                logs[0].from_state == ReadinessState.OBSERVED and
                logs[0].to_state == ReadinessState.READY and
                logs[0].transition_type == "promotion"
            )

            self.record(
                "Audit Logging",
                passed,
                f"Audit log recorded and retrieved: {len(logs)} logs"
            )

        except Exception as e:
            self.record("Audit Logging", False, str(e))

    async def validate_auto_transition_from_evaluation(self):
        """Test 7: Auto-transition from evaluation."""
        try:
            controller = get_transition_controller()
            candidate_id = uuid4()

            # Create a high-scoring evaluation that should trigger promotion
            evaluation = ReadinessEvaluation(
                candidate_id=candidate_id,
                evaluation_type="scheduled",
                evidence=EvidenceSummary(),
                score=ReadinessScore(
                    overall_score=0.85,
                    confidence=0.9,
                ),
                outcome=ReadinessOutcome.READY,
                recommended_state=ReadinessState.READY,
                reason="High score qualifies for READY",
                policy_profile_id="default",
                should_transition=True,
            )

            result = await controller.auto_transition_from_evaluation(
                evaluation,
                ReadinessState.WATCHLIST,
            )

            passed = (
                result is not None and
                result.success and
                result.to_state == ReadinessState.READY
            )

            self.record(
                "Auto-Transition from Evaluation",
                passed,
                f"Auto-transition to READY: {result.to_state.value if result else None}"
            )

        except Exception as e:
            self.record("Auto-Transition from Evaluation", False, str(e))

    async def validate_policy_validation(self):
        """Test 8: Transition policy validation."""
        try:
            validator = TransitionPolicyValidator()
            candidate_id = uuid4()

            # Create valid promotion request
            request = TransitionRequest(
                candidate_id=candidate_id,
                target_state=ReadinessState.WATCHLIST,
                requested_by="test_validator",
                reason="Valid promotion",
            )

            is_valid, errors = validator.validate_transition_request(
                request,
                ReadinessState.OBSERVED,
            )

            passed = is_valid and len(errors) == 0

            self.record(
                "Policy Validation",
                passed,
                f"Valid request passed: {is_valid}, errors: {errors}"
            )

        except Exception as e:
            self.record("Policy Validation", False, str(e))

    async def validate_full_transition_workflow(self):
        """Test 9: Full transition request workflow."""
        try:
            controller = get_transition_controller()
            candidate_id = uuid4()

            # Create transition request
            request = TransitionRequest(
                candidate_id=candidate_id,
                target_state=ReadinessState.READY,
                requested_by="test_validator",
                reason="Meeting readiness threshold",
            )

            # Create supporting evaluation
            evaluation = ReadinessEvaluation(
                candidate_id=candidate_id,
                evaluation_type="scheduled",
                evidence=EvidenceSummary(),
                score=ReadinessScore(
                    overall_score=0.85,
                    confidence=0.9,
                ),
                outcome=ReadinessOutcome.READY,
                recommended_state=ReadinessState.READY,
                reason="Ready for production",
                policy_profile_id="default",
                should_transition=True,
            )

            result = await controller.request_transition(
                request,
                ReadinessState.WATCHLIST,
                evaluation,
            )

            passed = (
                result.success and
                result.to_state == ReadinessState.READY
            )

            self.record(
                "Full Transition Workflow",
                passed,
                f"Transition successful: {result.to_state.value}, event_id: {result.transition_event_id}"
            )

        except Exception as e:
            self.record("Full Transition Workflow", False, str(e))

    async def validate_no_milestone_1_2_regression(self):
        """Test 10: No regression in M1/M2 functionality."""
        try:
            # Test M1: Policy registry
            registry = get_policy_registry()
            profile = registry.get_default_profile()

            m1_ok = (
                profile is not None and
                profile.id == "default" and
                len(registry.list_profiles()) >= 3
            )

            # Test M2: Evidence collection
            orchestrator = get_evidence_orchestrator()
            collectors = list(orchestrator.collectors.keys())

            m2_ok = len(collectors) == 8

            # Test M2: Scoring engine
            engine = get_scoring_engine()

            m2_scoring_ok = engine is not None

            passed = m1_ok and m2_ok and m2_scoring_ok

            self.record(
                "M1/M2 Regression Check",
                passed,
                f"M1 (policy): {m1_ok}, M2 (collectors): {m2_ok}, M2 (scoring): {m2_scoring_ok}"
            )

        except Exception as e:
            self.record("M1/M2 Regression Check", False, str(e))

    async def run_all(self):
        """Run all Milestone 3 validation tests."""
        logger.info("=" * 70)
        logger.info("TORQ READINESS CHECKER - MILESTONE 3 VALIDATION")
        logger.info("=" * 70)

        await self.validate_state_machine_instantiation()
        await self.validate_state_transitions()
        await self.validate_invalid_transition_blocking()
        await self.validate_governance_actions()
        await self.validate_forced_transitions()
        await self.validate_audit_logging()
        await self.validate_auto_transition_from_evaluation()
        await self.validate_policy_validation()
        await self.validate_full_transition_workflow()
        await self.validate_no_milestone_1_2_regression()

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
            logger.info("MILESTONE 3 COMPLETE - Transition controller is operational!")
            logger.info("=" * 70)
            logger.info("")
            logger.info("Exit Criteria Met:")
            logger.info("✓ State transitions work end-to-end")
            logger.info("✓ Governance actions execute correctly")
            logger.info("✓ Invalid transitions are blocked")
            logger.info("✓ Audit trail captures all changes")
            logger.info("✓ No regression in M1/M2 functionality")
            logger.info("")
            logger.info("Readiness candidates can now safely transition through states.")
            logger.info("=" * 70)
        else:
            logger.warning("")
            logger.warning(f"{self.failed} test(s) failed")
            logger.info("")

        return self.failed == 0


if __name__ == "__main__":
    validator = Milestone3Validator()
    success = asyncio.run(validator.run_all())
    sys.exit(0 if success else 1)
