"""
Phase Insight Publishing - Milestone 3 Validation

Validates that all Milestone 3 deliverables are in place:
- Retrieval service for agent access
- Context-aware retrieval (mission, domain, agent type)
- Ranking by relevance, freshness, confidence
- Filtering of invalid/stale/superseded insights
- Retrieval audit logging
- Clean agent-facing payloads
- No regression in prior milestones

Exit Criteria:
- Agents can retrieve published insights reliably
- Retrieval is context-aware
- Only valid/published insights are returned
- Freshness and supersession rules are respected
- Retrieval is auditable
- No regression in Milestones 1-2 or prior phases
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
    InsightCreate,
    SourceReference,
    QualityMetrics,
    Insight,
)

from torq_console.insights.persistence import (
    InsightRecord,
    MemoryInsightPersistence,
    get_insight_persistence,
)

from torq_console.insights.retrieval import (
    RetrievalContext,
    RetrievalResult,
    InsightPayload,
    ProvenanceSummary,
    SuppressedInsight,
    RetrievalAuditEntry,
    RankingConfig,
    InsightRetrievalService,
    get_retrieval_service,
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
    scope: InsightScope = InsightScope.WORKFLOW_TYPE,
    scope_key: str = "planning",
    age_days: int = 10,
) -> InsightRecord:
    """Create a test insight record."""
    created_at = datetime.now() - timedelta(days=age_days)

    return InsightRecord(
        id=uuid4(),
        insight_type=insight_type,
        title=f"Test {insight_type.value}",
        summary="A test insight for validation",
        scope=scope,
        scope_key=scope_key,
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
            "last_validated_at": (datetime.now() - timedelta(days=5)).isoformat(),
            "evidence_cutoff_at": (datetime.now() - timedelta(days=15)).isoformat(),
        },
        lifecycle_state=lifecycle_state,
        created_at=created_at,
        updated_at=created_at,
        published_at=created_at if lifecycle_state == InsightLifecycleState.PUBLISHED else None,
        usage_count=10,
        effectiveness_score=0.8,
    )


# ============================================================================
# Validators
# ============================================================================

class Milestone3Validator:
    """Validator for Milestone 3 deliverables."""

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

    async def test_retrieval_service_exists(self):
        """Test that retrieval service can be instantiated."""
        try:
            persistence = MemoryInsightPersistence()
            service = get_retrieval_service(persistence)
            passed = service is not None

            self.record(
                "Retrieval Service Instantiation",
                passed,
                "Service created successfully" if passed else "Service is None"
            )
        except Exception as e:
            self.record("Retrieval Service Instantiation", False, str(e))

    async def test_context_aware_retrieval(self):
        """Test retrieval by context (mission type, domain, agent type)."""
        try:
            persistence = MemoryInsightPersistence()

            # Create test insights with different domains
            for domain in ["financial", "technical", "legal"]:
                record = create_test_insight_record(domain=domain)
                persistence._insights[record.id] = record

            service = get_retrieval_service(persistence)

            # Retrieve by domain
            context = RetrievalContext(
                domain="financial",
                limit=10,
            )

            result = await service.retrieve(context)

            # Should only return financial insights
            passed = (
                len(result.insights) == 1 and
                result.insights[0].domain == "financial"
            )

            self.record(
                "Context-Aware Retrieval (Domain)",
                passed,
                f"Retrieved {len(result.insights)} insights for domain 'financial'"
            )
        except Exception as e:
            self.record("Context-Aware Retrieval (Domain)", False, str(e))

    async def test_mission_type_retrieval(self):
        """Test retrieval by mission type."""
        try:
            persistence = MemoryInsightPersistence()
            service = get_retrieval_service(persistence)

            # Create test insight
            record = create_test_insight_record()
            persistence._insights[record.id] = record

            # Retrieve by mission type
            result = await service.retrieve_by_mission(
                mission_type="planning",
                limit=10,
            )

            passed = len(result.insights) >= 1

            self.record(
                "Mission Type Retrieval",
                passed,
                f"Retrieved {len(result.insights)} insights for mission type 'planning'"
            )
        except Exception as e:
            self.record("Mission Type Retrieval", False, str(e))

    async def test_agent_type_retrieval(self):
        """Test retrieval by agent type."""
        try:
            persistence = MemoryInsightPersistence()
            service = get_retrieval_service(persistence)

            # Create test insight
            record = create_test_insight_record()
            persistence._insights[record.id] = record

            # Retrieve by agent type
            result = await service.retrieve_by_agent_type(
                agent_type="planner",
                limit=10,
            )

            passed = len(result.insights) >= 1

            self.record(
                "Agent Type Retrieval",
                passed,
                f"Retrieved {len(result.insights)} insights for agent type 'planner'"
            )
        except Exception as e:
            self.record("Agent Type Retrieval", False, str(e))

    async def test_insight_type_retrieval(self):
        """Test retrieval by insight type."""
        try:
            persistence = MemoryInsightPersistence()
            service = get_retrieval_service(persistence)

            # Create test insights of different types
            for insight_type in [InsightType.REUSABLE_PLAYBOOK, InsightType.BEST_PRACTICE]:
                record = create_test_insight_record(insight_type=insight_type)
                persistence._insights[record.id] = record

            # Retrieve by insight type
            result = await service.retrieve_by_insight_type(
                insight_type=InsightType.REUSABLE_PLAYBOOK,
                limit=10,
            )

            passed = (
                len(result.insights) == 1 and
                result.insights[0].insight_type == "reusable_playbook"
            )

            self.record(
                "Insight Type Retrieval",
                passed,
                f"Retrieved {len(result.insights)} insights of type 'reusable_playbook'"
            )
        except Exception as e:
            self.record("Insight Type Retrieval", False, str(e))

    async def test_source_lineage_retrieval(self):
        """Test retrieval by source lineage."""
        try:
            persistence = MemoryInsightPersistence()
            service = get_retrieval_service(persistence)

            # Create test insight with known source
            record = create_test_insight_record()
            persistence._insights[record.id] = record

            # Retrieve by source lineage
            result = await service.retrieve_by_source_lineage(
                source_id="test_memory_123",
                limit=10,
            )

            passed = len(result.insights) == 1

            self.record(
                "Source Lineage Retrieval",
                passed,
                f"Retrieved {len(result.insights)} insights from source 'test_memory_123'"
            )
        except Exception as e:
            self.record("Source Lineage Retrieval", False, str(e))

    async def test_filters_invalid_states(self):
        """Test that draft/candidate/superseded insights are filtered out."""
        try:
            persistence = MemoryInsightPersistence()
            service = get_retrieval_service(persistence)

            # Create insights in various states
            for state in [
                InsightLifecycleState.DRAFT,
                InsightLifecycleState.CANDIDATE,
                InsightLifecycleState.PUBLISHED,
                InsightLifecycleState.SUPERSEDED,
                InsightLifecycleState.ARCHIVED,
            ]:
                record = create_test_insight_record(lifecycle_state=state)
                persistence._insights[record.id] = record

            # Retrieve with default context (should only get PUBLISHED)
            context = RetrievalContext(limit=100)
            result = await service.retrieve(context)

            # Should only return PUBLISHED insights
            passed = (
                len(result.insights) == 1 and
                result.insights[0].lifecycle_state == "published"
            )

            self.record(
                "Filters Invalid States",
                passed,
                f"Returned {len(result.insights)} PUBLISHED insights, "
                f"suppressed {len(result.suppressed)} invalid states"
            )
        except Exception as e:
            self.record("Filters Invalid States", False, str(e))

    async def test_filters_by_confidence(self):
        """Test confidence-based filtering."""
        try:
            persistence = MemoryInsightPersistence()
            service = get_retrieval_service(persistence)

            # Create insights with different confidence levels
            for confidence in [0.90, 0.75, 0.50]:
                record = create_test_insight_record(confidence=confidence)
                persistence._insights[record.id] = record

            # Retrieve with minimum confidence
            context = RetrievalContext(
                min_confidence=0.70,
                limit=100,
            )
            result = await service.retrieve(context)

            # Should only return insights with confidence >= 0.70
            all_valid = all(i.confidence >= 0.70 for i in result.insights)
            passed = all_valid and len(result.insights) == 2

            self.record(
                "Filters by Confidence",
                passed,
                f"Retrieved {len(result.insights)} insights with confidence >= 0.70"
            )
        except Exception as e:
            self.record("Filters by Confidence", False, str(e))

    async def test_filters_stale_insights(self):
        """Test freshness filtering."""
        try:
            persistence = MemoryInsightPersistence()
            service = get_retrieval_service(persistence)

            # Create insights of different ages
            for age_days in [5, 30, 100]:
                record = create_test_insight_record(age_days=age_days)
                persistence._insights[record.id] = record

            # Retrieve with max age
            context = RetrievalContext(
                max_age_days=60,
                limit=100,
            )
            result = await service.retrieve(context)

            # Should filter out the 100-day-old insight
            passed = len(result.insights) == 2 and len(result.suppressed) == 1

            self.record(
                "Filters Stale Insights",
                passed,
                f"Retrieved {len(result.insights)} fresh insights, "
                f"suppressed {len(result.suppressed)} stale"
            )
        except Exception as e:
            self.record("Filters Stale Insights", False, str(e))

    async def test_ranking_by_relevance(self):
        """Test that insights are ranked by relevance."""
        try:
            persistence = MemoryInsightPersistence()
            service = get_retrieval_service(persistence)

            # Create insights with different relevance
            # (domain match = higher relevance)
            record1 = create_test_insight_record(domain="financial", confidence=0.70)
            record2 = create_test_insight_record(domain="financial", confidence=0.90)
            record3 = create_test_insight_record(domain="technical", confidence=0.90)

            for r in [record1, record2, record3]:
                persistence._insights[r.id] = r

            # Retrieve for financial domain
            context = RetrievalContext(
                domain="financial",
                limit=10,
            )
            result = await service.retrieve(context)

            # Financial insights should rank higher
            # and within financial, higher confidence should rank higher
            passed = (
                len(result.insights) == 2 and
                all(i.domain == "financial" for i in result.insights) and
                result.insights[0].confidence >= result.insights[1].confidence
            )

            self.record(
                "Ranking by Relevance",
                passed,
                f"Insights ranked correctly: {[i.insight_type for i in result.insights]}"
            )
        except Exception as e:
            self.record("Ranking by Relevance", False, str(e))

    async def test_agent_facing_payload(self):
        """Test that agents get clean payloads, not raw persistence objects."""
        try:
            persistence = MemoryInsightPersistence()
            service = get_retrieval_service(persistence)

            # Create test insight
            record = create_test_insight_record()
            persistence._insights[record.id] = record

            # Retrieve
            context = RetrievalContext(limit=10)
            result = await service.retrieve(context)

            if not result.insights:
                self.record("Agent-Facing Payload", False, "No insights returned")
                return

            payload = result.insights[0]

            # Check payload has required fields
            required_fields = [
                "id", "insight_type", "title", "summary",
                "content", "scope", "confidence", "validation_score",
                "lifecycle_state", "provenance", "relevance_score",
                "match_reasons", "trace_id",
            ]

            has_all = all(hasattr(payload, f) for f in required_fields)
            has_provenance = isinstance(payload.provenance, ProvenanceSummary)

            passed = has_all and has_provenance

            self.record(
                "Agent-Facing Payload",
                passed,
                f"Payload has {len(required_fields)} fields, provenance: {has_provenance}"
            )
        except Exception as e:
            self.record("Agent-Facing Payload", False, str(e))

    async def test_audit_logging(self):
        """Test that retrievals are logged for audit."""
        try:
            persistence = MemoryInsightPersistence()
            service = get_retrieval_service(persistence)

            # Create test insight
            record = create_test_insight_record()
            persistence._insights[record.id] = record

            # Perform retrieval
            context = RetrievalContext(
                agent_id="test_agent",
                agent_type="planner",
                limit=10,
            )
            await service.retrieve(context)

            # Check audit log
            audit_log = service.get_audit_log()

            passed = len(audit_log) > 0

            self.record(
                "Audit Logging",
                passed,
                f"Audit log has {len(audit_log)} entries"
            )
        except Exception as e:
            self.record("Audit Logging", False, str(e))

    async def test_audit_stats(self):
        """Test that audit statistics are available."""
        try:
            persistence = MemoryInsightPersistence()
            service = get_retrieval_service(persistence)

            # Create test insight
            record = create_test_insight_record()
            persistence._insights[record.id] = record

            # Perform multiple retrievals
            for i in range(3):
                await service.retrieve(RetrievalContext(limit=10))

            # Get stats
            stats = service.get_audit_stats()

            passed = (
                stats.get("total_retrievals") == 3 and
                "avg_retrieval_time_ms" in stats and
                "avg_results_per_query" in stats
            )

            self.record(
                "Audit Statistics",
                passed,
                f"Stats: {stats}"
            )
        except Exception as e:
            self.record("Audit Statistics", False, str(e))

    async def test_no_regression_milestone_1(self):
        """Test no regression in Milestone 1 (models and publishing rules)."""
        try:
            from torq_console.insights import (
                InsightType,
                InsightLifecycleState,
                QUALITY_GATES,
                LIFECYCLE_TRANSITIONS,
            )

            # Check models are available
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
        """Test no regression in Milestone 2 (extraction, validation, persistence, workflow)."""
        try:
            from torq_console.insights import (
                get_default_extractor,
                get_default_validator,
                get_insight_persistence,
                get_approval_workflow,
            )

            # Test extractor
            extractor = get_default_extractor()
            has_extractor = extractor is not None

            # Test validator
            validator = get_default_validator()
            has_validator = validator is not None

            # Test persistence
            persistence = get_insight_persistence()
            has_persistence = persistence is not None

            # Test workflow
            workflow = get_approval_workflow(persistence)
            has_workflow = workflow is not None

            passed = has_extractor and has_validator and has_persistence and has_workflow

            self.record(
                "No Regression - Milestone 2",
                passed,
                f"Extractor: {has_extractor}, Validator: {has_validator}, "
                f"Persistence: {has_persistence}, Workflow: {has_workflow}"
            )
        except Exception as e:
            self.record("No Regression - Milestone 2", False, str(e))

    # ========================================================================
    # Run All Tests
    # ========================================================================

    async def run_all_tests(self):
        """Run all validation tests."""
        logger.info("=" * 70)
        logger.info("INSIGHT PUBLISHING - MILESTONE 3 VALIDATION")
        logger.info("=" * 70)

        # Tests
        await self.test_retrieval_service_exists()
        await self.test_context_aware_retrieval()
        await self.test_mission_type_retrieval()
        await self.test_agent_type_retrieval()
        await self.test_insight_type_retrieval()
        await self.test_source_lineage_retrieval()
        await self.test_filters_invalid_states()
        await self.test_filters_by_confidence()
        await self.test_filters_stale_insights()
        await self.test_ranking_by_relevance()
        await self.test_agent_facing_payload()
        await self.test_audit_logging()
        await self.test_audit_stats()
        await self.test_no_regression_milestone_1()
        await self.test_no_regression_milestone_2()

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
            logger.info("MILESTONE 3 COMPLETE - All deliverables verified!")
            logger.info("=" * 70)
            logger.info("")
            logger.info("Exit Criteria Met:")
            logger.info("Agents can retrieve published insights reliably")
            logger.info("Retrieval is context-aware")
            logger.info("Only valid/published insights are returned")
            logger.info("Freshness and supersession rules are respected")
            logger.info("Retrieval is auditable")
            logger.info("No regression in Milestones 1-2 or prior phases")
        else:
            logger.warning(f"{self.results['failed']} test(s) failed")

        logger.info("=" * 70)


# ============================================================================
# Main
# ============================================================================

async def main():
    """Run validation tests."""
    validator = Milestone3Validator()
    await validator.run_all_tests()
    return validator.results["failed"] == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
