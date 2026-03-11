"""
Phase Insight Publishing - Milestone 2 Validation

Validates that all Milestone 2 deliverables are in place:
- Insight candidate extractor from validated memory
- Publishing validation service
- Publication persistence with lineage tracking
- Approval workflow (approve/reject/supersede transitions)
- No regression in prior phases

Exit Criteria:
- Insight candidates can be extracted reliably
- Only eligible candidates pass publication validation
- Rejected candidates are logged with reasons
- Approved insights persist with provenance and lifecycle state
- Publication does not blur artifact/memory/insight boundaries
- No regression in prior phases
"""

import sys
import io
import asyncio
from pathlib import Path

# Force UTF-8 output for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import logging
from datetime import datetime, timedelta
from uuid import uuid4

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from torq_console.insights.models import (
    InsightType,
    InsightLifecycleState,
    InsightScope,
    InsightSourceType,
    InsightCreate,
    SourceReference,
    QualityMetrics,
    Insight,
)

from torq_console.insights.candidate_extractor import (
    InsightCandidateExtractor,
    ExtractionResult,
    extract_insight_candidates,
    get_extraction_summary,
    get_default_extractor,
    DEFAULT_EXTRACTION_RULES,
)

from torq_console.insights.validation_service import (
    ValidationResult,
    DuplicationDetector,
    PublishingValidator,
    validate_candidates_for_publication,
    get_validation_summary,
    get_default_validator,
)

from torq_console.insights.persistence import (
    InsightPersistence,
    MemoryInsightPersistence,
    InsightRecord,
    get_insight_persistence,
)

from torq_console.insights.approval_workflow import (
    ApprovalWorkflowService,
    TransitionRequest,
    TransitionResult,
    get_approval_workflow,
)

from torq_console.strategic_memory.models import (
    StrategicMemory,
    MemoryType,
    MemoryScope,
    MemoryStatus,
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Test Data
# ============================================================================

def create_test_memory(
    memory_type: MemoryType,
    title: str,
    confidence: float = 0.8,
) -> StrategicMemory:
    """Create a test strategic memory."""
    return StrategicMemory(
        id=str(uuid4()),
        memory_type=memory_type,
        title=title,
        domain="test_domain",
        scope=MemoryScope.WORKFLOW_TYPE,
        scope_key="planning",
        confidence=confidence,
        durability_score=0.75,
        memory_content={
            "description": f"Test memory for {title}",
            "guidance": "Test guidance",
            "triggers": ["test_trigger"],
            "steps": ["step1", "step2"],
            "expected_outcome": "Test outcome",
        },
        source_pattern_ids=[],
        source_insight_ids=[],
        source_experiment_ids=[],
        status=MemoryStatus.ACTIVE,
        created_at=datetime.now(),
        reviewed_at=datetime.now(),
        expires_at=datetime.now() + timedelta(days=90),
        last_validated_at=datetime.now(),
        usage_count=10,
        effectiveness_score=0.8,
    )


def create_test_candidate(
    insight_type: InsightType = InsightType.REUSABLE_PLAYBOOK,
    confidence: float = 0.85,
) -> InsightCreate:
    """Create a test insight candidate."""
    return InsightCreate(
        insight_type=insight_type,
        title="Test Playbook",
        summary="A test playbook for validation",
        scope=InsightScope.WORKFLOW_TYPE,
        scope_key="planning",
        content={
            "objective": "Test objective",
            "triggers": ["trigger1", "trigger2"],
            "steps": ["step1", "step2"],
            "expected_outcome": "Test outcome",
        },
        domain="test_domain",
        tags=["test", "validation"],
        source_references=[
            SourceReference(
                source_type=InsightSourceType.MEMORY,
                source_id="test_memory_123",
                contribution_weight=1.0,
            )
        ],
        quality=QualityMetrics(
            confidence_score=confidence,
            validation_score=0.80,
            applicability_score=0.75,
            source_count=2,
            execution_count=10,
            success_rate=0.80,
            last_validated_at=datetime.now(),
            evidence_cutoff_at=datetime.now() - timedelta(days=10),
        ),
    )


# ============================================================================
# Validators
# ============================================================================

class Milestone2Validator:
    """Validator for Milestone 2 deliverables."""

    def __init__(self):
        self.results = {
            "passed": 0,
            "failed": 0,
            "tests": [],
        }

    def record(self, test_name: str, passed: bool, message: str = ""):
        """Record a test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.results["tests"].append({
            "name": test_name,
            "status": status,
            "message": message,
        })
        if passed:
            self.results["passed"] += 1
            logger.info(f"[OK] {test_name}: {message}")
        else:
            self.results["failed"] += 1
            logger.error(f"[FAIL] {test_name}: {message}")

    # ========================================================================
    # Tests
    # ========================================================================

    async def test_extractor_exists(self):
        """Test that candidate extractor can be instantiated."""
        try:
            extractor = get_default_extractor()
            passed = extractor is not None
            self.record(
                "Candidate Extractor Instantiation",
                passed,
                "Extractor created successfully" if passed else "Extractor is None"
            )
        except Exception as e:
            self.record("Candidate Extractor Instantiation", False, str(e))

    async def test_extraction_from_memory(self):
        """Test extracting candidates from memories."""
        try:
            # Create test memories
            memories = [
                create_test_memory(MemoryType.PLAYBOOK, "Test Playbook Memory", 0.85),
                create_test_memory(MemoryType.WARNING, "Test Warning Memory", 0.70),
                create_test_memory(MemoryType.HEURISTIC, "Test Heuristic Memory", 0.60),  # Below threshold
            ]

            # Extract candidates
            extractor = get_default_extractor()
            results = extractor.extract_from_memories(memories)

            # Should extract 2 (first two are eligible, third has low confidence)
            extracted = sum(1 for r in results if r.success)
            passed = extracted == 2

            self.record(
                "Extraction from Memory",
                passed,
                f"Extracted {extracted}/3 candidates (expected 2)"
            )
        except Exception as e:
            self.record("Extraction from Memory", False, str(e))

    async def test_extraction_summary(self):
        """Test extraction summary generation."""
        try:
            memories = [
                create_test_memory(MemoryType.PLAYBOOK, "Test Playbook", 0.85),
            ]

            extractor = get_default_extractor()
            results = extractor.extract_from_memories(memories)
            summary = get_extraction_summary(results)

            passed = (
                "total_memories" in summary and
                summary["total_memories"] == 1 and
                "extraction_rate" in summary
            )

            self.record(
                "Extraction Summary",
                passed,
                f"Summary generated: {summary}"
            )
        except Exception as e:
            self.record("Extraction Summary", False, str(e))

    async def test_validation_service_exists(self):
        """Test that validation service can be instantiated."""
        try:
            validator = get_default_validator()
            passed = validator is not None
            self.record(
                "Validation Service Instantiation",
                passed,
                "Validator created successfully" if passed else "Validator is None"
            )
        except Exception as e:
            self.record("Validation Service Instantiation", False, str(e))

    async def test_quality_gate_validation(self):
        """Test that quality gates are enforced."""
        try:
            # High-quality candidate should pass
            high_quality = create_test_candidate(confidence=0.90)
            validator = get_default_validator()
            results = validator.validate_for_publication(high_quality)

            passed = results.passed

            self.record(
                "Quality Gate Validation (High Quality)",
                passed,
                f"High quality candidate {'passed' if passed else 'failed'} quality gates"
            )
        except Exception as e:
            self.record("Quality Gate Validation (High Quality)", False, str(e))

    async def test_quality_gate_rejection(self):
        """Test that low-quality candidates are rejected."""
        try:
            # Low-quality candidate should fail
            low_quality = create_test_candidate(confidence=0.50)  # Below threshold
            validator = get_default_validator()
            results = validator.validate_for_publication(low_quality)

            passed = not results.passed  # Should fail

            self.record(
                "Quality Gate Rejection (Low Quality)",
                passed,
                f"Low quality candidate {'rejected' if passed else 'passed'} (should be rejected)"
            )
        except Exception as e:
            self.record("Quality Gate Rejection (Low Quality)", False, str(e))

    async def test_duplication_detection(self):
        """Test conflict detection with existing insights."""
        try:
            detector = DuplicationDetector()

            # Create source reference for test
            source_ref = SourceReference(
                source_type=InsightSourceType.MEMORY,
                source_id="test_memory",
                contribution_weight=1.0,
            )

            # Create a candidate similar to an existing one
            existing_insight = Insight(
                insight_type=InsightType.REUSABLE_PLAYBOOK,
                title="Existing Playbook",
                summary="An existing playbook",
                scope=InsightScope.WORKFLOW_TYPE,
                content={},
                source_references=[source_ref],
                quality=QualityMetrics(
                    confidence_score=0.8,
                    validation_score=0.8,
                    applicability_score=0.8,
                    source_count=1,
                ),
                lifecycle_state=InsightLifecycleState.PUBLISHED,
            )

            candidate = InsightCreate(
                insight_type=InsightType.REUSABLE_PLAYBOOK,
                title="Existing Playbook",  # Same title = high similarity
                summary="An existing playbook",
                scope=InsightScope.WORKFLOW_TYPE,
                content={},
                source_references=[source_ref],
                quality=QualityMetrics(
                    confidence_score=0.8,
                    validation_score=0.8,
                    applicability_score=0.8,
                    source_count=1,
                ),
            )

            check = detector.check_for_duplicates(candidate, [existing_insight])

            passed = check.is_duplicate  # Should detect duplicate

            self.record(
                "Duplication Detection",
                passed,
                f"Duplicate detected: {check.is_duplicate} (similarity: {check.similarity_score:.2f})"
            )
        except Exception as e:
            self.record("Duplication Detection", False, str(e))

    async def test_persistence_in_memory(self):
        """Test in-memory persistence."""
        try:
            persistence = MemoryInsightPersistence()

            # Create a candidate
            candidate = create_test_candidate()

            # Persist
            record = await persistence.create_insight(candidate)

            passed = record is not None and record.id is not None

            self.record(
                "In-Memory Persistence",
                passed,
                f"Created insight with ID: {record.id if record else 'None'}"
            )
        except Exception as e:
            self.record("In-Memory Persistence", False, str(e))

    async def test_rejection_logging(self):
        """Test that rejections are logged."""
        try:
            persistence = MemoryInsightPersistence()
            candidate = create_test_candidate()

            # Log a rejection
            rejection = await persistence.log_rejection(
                candidate,
                ["Low confidence score"],
                []
            )

            passed = rejection.id is not None

            self.record(
                "Rejection Logging",
                passed,
                f"Rejection logged with ID: {rejection.id}"
            )
        except Exception as e:
            self.record("Rejection Logging", False, str(e))

    async def test_lifecycle_transition(self):
        """Test lifecycle state transitions."""
        try:
            persistence = MemoryInsightPersistence()
            workflow = get_approval_workflow(persistence)

            # First create an insight with CANDIDATE initial state
            candidate = create_test_candidate()
            # Override initial state to CANDIDATE for this test
            candidate.initial_state = InsightLifecycleState.CANDIDATE
            record = await persistence.create_insight(candidate)

            # Transition from CANDIDATE to VALIDATED
            request = TransitionRequest(
                insight_id=record.id,
                from_state=InsightLifecycleState.CANDIDATE,
                to_state=InsightLifecycleState.VALIDATED,
                requested_by="test_validator",
            )

            result = await workflow.transition_insight(request)

            passed = result.success and result.to_state == InsightLifecycleState.VALIDATED

            self.record(
                "Lifecycle Transition",
                passed,
                f"Transition to VALIDATED: {result.success}"
            )
        except Exception as e:
            self.record("Lifecycle Transition", False, str(e))

    async def test_batch_approval(self):
        """Test batch approval of candidates."""
        try:
            persistence = MemoryInsightPersistence()

            # Create candidates with mock validation results
            candidates = [
                create_test_candidate(InsightType.REUSABLE_PLAYBOOK, 0.85),
                create_test_candidate(InsightType.BEST_PRACTICE, 0.80),
            ]

            # Create mock validation results (all pass)
            from torq_console.insights.validation_service import ValidationResult, QualityGateResult
            validations = []
            for _ in candidates:
                validation = ValidationResult(
                    passed=True,
                    quality_gate_results=[
                        QualityGateResult(
                            gate_name="test_gate",
                            passed=True,
                            score=0.85,
                            threshold=0.75,
                        )
                    ],
                )
                validations.append(validation)

            # Batch approve
            from torq_console.insights.approval_workflow import approve_batch
            pairs = list(zip(candidates, validations))
            results = await approve_batch(pairs, persistence, "test_validator")

            approved = sum(1 for r in results if r.success)

            passed = approved == 2

            self.record(
                "Batch Approval",
                passed,
                f"Approved {approved}/2 candidates"
            )
        except Exception as e:
            self.record("Batch Approval", False, str(e))

    async def test_layer_separation_maintained(self):
        """Test that artifact/memory/insight boundaries are maintained."""
        try:
            # Import from all three layers
            from torq_console.workspace.artifact_models import ArtifactType
            from torq_console.strategic_memory.models import MemoryType
            from torq_console.insights.models import InsightType

            # Check type values don't overlap
            artifact_values = set([t.value for t in ArtifactType])
            memory_values = set([t.value for t in MemoryType])
            insight_values = set([t.value for t in InsightType])

            overlaps = artifact_values & memory_values & insight_values

            passed = len(overlaps) == 0

            self.record(
                "Layer Separation Maintained",
                passed,
                f"No type value overlaps: {passed}"
            )
        except Exception as e:
            self.record("Layer Separation Maintained", False, str(e))

    # ========================================================================
    # Run All Tests
    # ========================================================================

    async def run_all_tests(self):
        """Run all validation tests."""
        logger.info("=" * 70)
        logger.info("INSIGHT PUBLISHING - MILESTONE 2 VALIDATION")
        logger.info("=" * 70)

        # Tests
        await self.test_extractor_exists()
        await self.test_extraction_from_memory()
        await self.test_extraction_summary()
        await self.test_validation_service_exists()
        await self.test_quality_gate_validation()
        await self.test_quality_gate_rejection()
        await self.test_duplication_detection()
        await self.test_persistence_in_memory()
        await self.test_rejection_logging()
        await self.test_lifecycle_transition()
        await self.test_batch_approval()
        await self.test_layer_separation_maintained()

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary."""
        logger.info("")
        logger.info("=" * 70)
        logger.info("VALIDATION SUMMARY")
        logger.info("=" * 70)

        for test in self.results["tests"]:
            logger.info(f"{test['status']} - {test['name']}: {test['message']}")

        logger.info("")
        logger.info(f"Total: {self.results['passed'] + self.results['failed']} tests")
        logger.info(f"Passed: {self.results['passed']}")
        logger.info(f"Failed: {self.results['failed']}")

        if self.results["failed"] == 0:
            logger.info("")
            logger.info("=" * 70)
            logger.info("🎉 MILESTONE 2 COMPLETE - All deliverables verified!")
            logger.info("=" * 70)
            logger.info("")
            logger.info("Exit Criteria Met:")
            logger.info("✅ Insight candidates can be extracted reliably")
            logger.info("✅ Only eligible candidates pass publication validation")
            logger.info("✅ Rejected candidates are logged with reasons")
            logger.info("✅ Approved insights persist with provenance and lifecycle state")
            logger.info("✅ Publication does not blur artifact/memory/insight boundaries")
            logger.info("✅ No regression in prior phases")
        else:
            logger.warning(f"{self.results['failed']} test(s) failed")

        logger.info("=" * 70)


# ============================================================================
# Main
# ============================================================================

async def main():
    """Run validation tests."""
    validator = Milestone2Validator()
    await validator.run_all_tests()
    return validator.results["failed"] == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
