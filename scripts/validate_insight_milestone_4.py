"""
Phase Insight Publishing - Milestone 4 Validation

Validates that all Milestone 4 deliverables are in place:
- Insight inspection endpoints (list, detail, lineage, lifecycle, usage)
- Retrieval audit visibility (queries, audit log, ranking explanations)
- Publication audit visibility (trail, sources, validation path)
- Governance controls (archive, supersede, disable type)
- No regression in Milestones 1-3 or prior phases

Exit Criteria:
- Published insights are inspectable
- Lineage from insight → memory/artifact is visible
- Retrieval behavior is auditable
- Governance actions work
- No regression in Milestones 1-3
"""

import sys
import io
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

# Force UTF-8 output for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import logging
from uuid import uuid4

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from torq_console.insights.models import (
    InsightType,
    InsightLifecycleState,
    InsightScope,
    InsightSourceType,
)

from torq_console.insights.persistence import (
    InsightRecord,
    MemoryInsightPersistence,
    get_insight_persistence,
)

from torq_console.insights.retrieval import (
    InsightRetrievalService,
    get_retrieval_service,
)

from torq_console.insights.inspection import (
    InsightLineage,
    LifecycleEvent,
    UsageRecord,
    InsightDetail,
    RetrievalAuditSummary,
    PublicationAuditTrail,
    GovernanceAction,
    InsightTypeConfig,
    InsightInspectionService,
    get_inspection_service,
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Test Data
# ============================================================================

def create_test_insight_record(
    insight_type: InsightType = InsightType.REUSABLE_PLAYBOOK,
    lifecycle_state: InsightLifecycleState = InsightLifecycleState.PUBLISHED,
    confidence: float = 0.85,
    domain: str = "test_domain",
) -> InsightRecord:
    """Create a test insight record."""
    now = datetime.now()

    return InsightRecord(
        id=uuid4(),
        insight_type=insight_type,
        title=f"Test {insight_type.value}",
        summary="A test insight for validation",
        scope=InsightScope.WORKFLOW_TYPE,
        scope_key="planning",
        domain=domain,
        tags=["test", "validation"],
        content={
            "objective": "Test objective",
            "steps": ["step1", "step2"],
        },
        source_references=[
            {
                "source_type": InsightSourceType.MEMORY.value,
                "source_id": "test_memory_123",
                "contribution_weight": 1.0,
                "extraction_method": "test_extraction",
            }
        ],
        quality={
            "confidence_score": confidence,
            "validation_score": 0.80,
            "applicability_score": 0.75,
            "source_count": 2,
            "execution_count": 10,
            "success_rate": 0.80,
            "last_validated_at": (now - timedelta(days=5)).isoformat(),
            "evidence_cutoff_at": (now - timedelta(days=15)).isoformat(),
        },
        lifecycle_state=lifecycle_state,
        created_at=now - timedelta(days=10),
        updated_at=now - timedelta(days=5),
        published_at=now - timedelta(days=5) if lifecycle_state == InsightLifecycleState.PUBLISHED else None,
        usage_count=10,
        effectiveness_score=0.8,
        created_by="system",
    )


# ============================================================================
# Validators
# ============================================================================

class Milestone4Validator:
    """Validator for Milestone 4 deliverables."""

    def __init__(self):
        self.results = {
            "passed": 0,
            "failed": 0,
            "tests": [],
        }

    def record(self, test_name: str, passed: bool, message: str = ""):
        """Record a test result."""
        status = "PASS" if passed else "FAIL"
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

    async def test_inspection_service_exists(self):
        """Test that inspection service can be instantiated."""
        try:
            persistence = MemoryInsightPersistence()
            service = get_inspection_service(persistence)
            passed = service is not None

            self.record(
                "Inspection Service Instantiation",
                passed,
                "Service created successfully" if passed else "Service is None"
            )
        except Exception as e:
            self.record("Inspection Service Instantiation", False, str(e))

    async def test_list_published_insights(self):
        """Test listing published insights."""
        try:
            persistence = MemoryInsightPersistence()
            service = get_inspection_service(persistence)

            # Create test insights
            for domain in ["financial", "technical"]:
                record = create_test_insight_record(domain=domain)
                persistence._insights[record.id] = record

            # List published
            insights = await service.list_published_insights(limit=10)

            passed = len(insights) == 2

            self.record(
                "List Published Insights",
                passed,
                f"Listed {len(insights)} published insights"
            )
        except Exception as e:
            self.record("List Published Insights", False, str(e))

    async def test_get_insight_detail(self):
        """Test getting complete insight detail."""
        try:
            persistence = MemoryInsightPersistence()
            service = get_inspection_service(persistence)

            # Create test insight
            record = create_test_insight_record()
            persistence._insights[record.id] = record

            # Get detail
            detail = await service.get_insight_detail(record.id)

            passed = (
                detail is not None and
                detail.id == str(record.id) and
                detail.lineage is not None and
                detail.lifecycle_state == "published"
            )

            self.record(
                "Get Insight Detail",
                passed,
                f"Retrieved detail with {len(detail.lineage.source_memories)} source memories"
            )
        except Exception as e:
            self.record("Get Insight Detail", False, str(e))

    async def test_get_insight_lineage(self):
        """Test getting insight lineage."""
        try:
            persistence = MemoryInsightPersistence()
            service = get_inspection_service(persistence)

            # Create test insight
            record = create_test_insight_record()
            persistence._insights[record.id] = record

            # Get lineage
            lineage = await service.get_insight_lineage(record.id)

            passed = (
                lineage is not None and
                len(lineage.source_memories) == 1 and
                lineage.source_memories[0].memory_id == "test_memory_123"
            )

            self.record(
                "Get Insight Lineage",
                passed,
                f"Lineage has {len(lineage.source_memories)} memory sources"
            )
        except Exception as e:
            self.record("Get Insight Lineage", False, str(e))

    async def test_get_lifecycle_history(self):
        """Test getting lifecycle history."""
        try:
            persistence = MemoryInsightPersistence()
            service = get_inspection_service(persistence)

            # Create test insight
            record = create_test_insight_record()
            persistence._insights[record.id] = record

            # Log a lifecycle event
            service._log_lifecycle_event(
                str(record.id),
                "test_event",
                None,
                "published",
                "test_validator",
                "Test event"
            )

            # Get history
            history = await service.get_insight_lifecycle_history(record.id)

            passed = len(history) >= 1 and history[0].event_type == "test_event"

            self.record(
                "Get Lifecycle History",
                passed,
                f"History has {len(history)} events"
            )
        except Exception as e:
            self.record("Get Lifecycle History", False, str(e))

    async def test_get_usage_history(self):
        """Test getting usage history."""
        try:
            persistence = MemoryInsightPersistence()
            service = get_inspection_service(persistence)

            # Create test insight
            record = create_test_insight_record()
            persistence._insights[record.id] = record

            # Log some usage
            service.log_usage(
                insight_id=str(record.id),
                agent_id="test_agent",
                agent_type="planner",
                mission_type="planning",
            )
            service.log_usage(
                insight_id=str(record.id),
                agent_id="test_agent_2",
                agent_type="executor",
            )

            # Get usage history
            usage = await service.get_insight_usage_history(record.id)

            passed = len(usage) == 2

            self.record(
                "Get Usage History",
                passed,
                f"Found {len(usage)} usage records"
            )
        except Exception as e:
            self.record("Get Usage History", False, str(e))

    async def test_get_retrieval_audit_log(self):
        """Test getting retrieval audit log."""
        try:
            persistence = MemoryInsightPersistence()
            retrieval_service = get_retrieval_service(persistence)
            service = get_inspection_service(persistence, retrieval_service)

            # Perform some retrievals to populate audit log
            await retrieval_service.retrieve_by_mission("planning", limit=5)
            await retrieval_service.retrieve_by_domain("technical", limit=5)

            # Get audit log
            audit_log = await service.get_retrieval_audit_log(limit=10)

            passed = len(audit_log) >= 2

            self.record(
                "Get Retrieval Audit Log",
                passed,
                f"Audit log has {len(audit_log)} entries"
            )
        except Exception as e:
            self.record("Get Retrieval Audit Log", False, str(e))

    async def test_get_retrieval_audit_summary(self):
        """Test getting retrieval audit summary."""
        try:
            persistence = MemoryInsightPersistence()
            retrieval_service = get_retrieval_service(persistence)
            service = get_inspection_service(persistence, retrieval_service)

            # Perform some retrievals
            await retrieval_service.retrieve_by_mission("planning", limit=5)

            # Get summary
            summary = await service.get_retrieval_audit_summary(period_days=7)

            passed = (
                summary.total_retrievals >= 1 and
                summary.period_start is not None and
                summary.period_end is not None
            )

            self.record(
                "Get Retrieval Audit Summary",
                passed,
                f"Summary: {summary.total_retrievals} retrievals, "
                f"{summary.unique_insights_retrieved} unique insights"
            )
        except Exception as e:
            self.record("Get Retrieval Audit Summary", False, str(e))

    async def test_get_publication_audit_trail(self):
        """Test getting publication audit trail."""
        try:
            persistence = MemoryInsightPersistence()
            service = get_inspection_service(persistence)

            # Create test insight
            record = create_test_insight_record()
            persistence._insights[record.id] = record

            # Get audit trail
            trail = await service.get_publication_audit_trail(record.id)

            passed = (
                trail is not None and
                trail.insight_id == str(record.id) and
                len(trail.source_memory_ids) == 1
            )

            self.record(
                "Get Publication Audit Trail",
                passed,
                f"Audit trail has {len(trail.source_memory_ids)} memory sources"
            )
        except Exception as e:
            self.record("Get Publication Audit Trail", False, str(e))

    async def test_governance_archive(self):
        """Test archiving an insight."""
        try:
            persistence = MemoryInsightPersistence()
            service = get_inspection_service(persistence)

            # Create test insight
            record = create_test_insight_record()
            persistence._insights[record.id] = record

            # Archive it
            action = await service.archive_insight(
                record.id,
                archived_by="test_admin",
                reason="No longer relevant"
            )

            passed = (
                action.success and
                action.new_state == "archived" and
                action.action == "archive"
            )

            self.record(
                "Governance - Archive Insight",
                passed,
                f"Archive action: {action.message}"
            )
        except Exception as e:
            self.record("Governance - Archive Insight", False, str(e))

    async def test_governance_supersede(self):
        """Test superseding an insight."""
        try:
            persistence = MemoryInsightPersistence()
            service = get_inspection_service(persistence)

            # Create test insights
            old_record = create_test_insight_record()
            new_record = create_test_insight_record()
            persistence._insights[old_record.id] = old_record
            persistence._insights[new_record.id] = new_record

            # Supersede old with new
            action = await service.supersede_insight(
                old_record.id,
                new_record.id,
                superseded_by="test_admin",
                reason="Improved version available"
            )

            passed = (
                action.success and
                action.action == "supersede" and
                action.new_state == "superseded"
            )

            self.record(
                "Governance - Supersede Insight",
                passed,
                f"Supersede action: {action.message}"
            )
        except Exception as e:
            self.record("Governance - Supersede Insight", False, str(e))

    async def test_governance_disable_type(self):
        """Test disabling an insight type."""
        try:
            persistence = MemoryInsightPersistence()
            service = get_inspection_service(persistence)

            # Disable a type
            action = await service.disable_insight_type(
                InsightType.REUSABLE_PLAYBOOK,
                disabled_by="test_admin",
                reason="Under review"
            )

            passed = (
                action.success and
                action.action == "disable_type"
            )

            # Check it's disabled
            is_disabled = not service.is_insight_type_enabled(InsightType.REUSABLE_PLAYBOOK)

            passed = passed and is_disabled

            self.record(
                "Governance - Disable Insight Type",
                passed,
                f"Disable action: {action.message}, type disabled: {is_disabled}"
            )
        except Exception as e:
            self.record("Governance - Disable Insight Type", False, str(e))

    async def test_governance_enable_type(self):
        """Test re-enabling an insight type."""
        try:
            persistence = MemoryInsightPersistence()
            service = get_inspection_service(persistence)

            # First disable
            await service.disable_insight_type(
                InsightType.BEST_PRACTICE,
                disabled_by="test_admin",
            )

            # Then enable
            action = await service.enable_insight_type(
                InsightType.BEST_PRACTICE,
                enabled_by="test_admin"
            )

            passed = (
                action.success and
                action.action == "enable_type"
            )

            # Check it's enabled
            is_enabled = service.is_insight_type_enabled(InsightType.BEST_PRACTICE)

            passed = passed and is_enabled

            self.record(
                "Governance - Enable Insight Type",
                passed,
                f"Enable action: {action.message}, type enabled: {is_enabled}"
            )
        except Exception as e:
            self.record("Governance - Enable Insight Type", False, str(e))

    async def test_no_regression_milestone_1(self):
        """Test no regression in Milestone 1."""
        try:
            from torq_console.insights import (
                InsightType,
                InsightLifecycleState,
                QUALITY_GATES,
                LIFECYCLE_TRANSITIONS,
            )

            has_types = len(InsightType) >= 8
            has_states = len(InsightLifecycleState) >= 6
            has_gates = len(QUALITY_GATES) >= 8
            has_transitions = len(LIFECYCLE_TRANSITIONS) >= 7

            passed = has_types and has_states and has_gates and has_transitions

            self.record(
                "No Regression - Milestone 1",
                passed,
                f"Types: {has_types}, States: {has_states}, Gates: {has_gates}, Transitions: {has_transitions}"
            )
        except Exception as e:
            self.record("No Regression - Milestone 1", False, str(e))

    async def test_no_regression_milestone_2(self):
        """Test no regression in Milestone 2."""
        try:
            from torq_console.insights import (
                get_default_extractor,
                get_default_validator,
                get_insight_persistence,
                get_approval_workflow,
            )

            extractor = get_default_extractor()
            validator = get_default_validator()
            persistence = get_insight_persistence()
            workflow = get_approval_workflow(persistence)

            passed = all([
                extractor is not None,
                validator is not None,
                persistence is not None,
                workflow is not None,
            ])

            self.record(
                "No Regression - Milestone 2",
                passed,
                "Extractor, Validator, Persistence, Workflow all available"
            )
        except Exception as e:
            self.record("No Regression - Milestone 2", False, str(e))

    async def test_no_regression_milestone_3(self):
        """Test no regression in Milestone 3."""
        try:
            from torq_console.insights import (
                get_retrieval_service,
                RetrievalContext,
            )

            persistence = get_insight_persistence()
            service = get_retrieval_service(persistence)

            # Test retrieval still works
            context = RetrievalContext(limit=10)
            result = await service.retrieve(context)

            passed = result is not None

            self.record(
                "No Regression - Milestone 3",
                passed,
                f"Retrieval service functional: {passed}"
            )
        except Exception as e:
            self.record("No Regression - Milestone 3", False, str(e))

    # ========================================================================
    # Run All Tests
    # ========================================================================

    async def run_all_tests(self):
        """Run all validation tests."""
        logger.info("=" * 70)
        logger.info("INSIGHT PUBLISHING - MILESTONE 4 VALIDATION")
        logger.info("=" * 70)

        # Tests
        await self.test_inspection_service_exists()
        await self.test_list_published_insights()
        await self.test_get_insight_detail()
        await self.test_get_insight_lineage()
        await self.test_get_lifecycle_history()
        await self.test_get_usage_history()
        await self.test_get_retrieval_audit_log()
        await self.test_get_retrieval_audit_summary()
        await self.test_get_publication_audit_trail()
        await self.test_governance_archive()
        await self.test_governance_supersede()
        await self.test_governance_disable_type()
        await self.test_governance_enable_type()
        await self.test_no_regression_milestone_1()
        await self.test_no_regression_milestone_2()
        await self.test_no_regression_milestone_3()

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary."""
        logger.info("")
        logger.info("=" * 70)
        logger.info("VALIDATION SUMMARY")
        logger.info("=" * 70)

        for test in self.results["tests"]:
            status = "PASS" if test["status"] == "PASS" else "FAIL"
            logger.info(f"[{status}] - {test['name']}: {test['message']}")

        logger.info("")
        logger.info(f"Total: {self.results['passed'] + self.results['failed']} tests")
        logger.info(f"Passed: {self.results['passed']}")
        logger.info(f"Failed: {self.results['failed']}")

        if self.results["failed"] == 0:
            logger.info("")
            logger.info("=" * 70)
            logger.info("MILESTONE 4 COMPLETE - All deliverables verified!")
            logger.info("=" * 70)
            logger.info("")
            logger.info("Exit Criteria Met:")
            logger.info("Published insights are inspectable")
            logger.info("Lineage from insight → memory/artifact is visible")
            logger.info("Retrieval behavior is auditable")
            logger.info("Governance actions work")
            logger.info("No regression in Milestones 1-3")
        else:
            logger.warning(f"{self.results['failed']} test(s) failed")

        logger.info("=" * 70)


# ============================================================================
# Main
# ============================================================================

async def main():
    """Run validation tests."""
    validator = Milestone4Validator()
    await validator.run_all_tests()
    return validator.results["failed"] == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
