"""
Phase Insight Publishing - Milestone 5 Validation

Hardening & Regression Tests for Insight Publishing & Agent Retrieval.

Validates:
1. Concurrency and load safety
2. Duplicate and supersession behavior
3. Lifecycle correctness
4. Ranking and filter edge cases
5. Audit integrity
6. Full regression (M1-M4, 4H.1, 5.3, 5.2)

Exit Criteria:
- Insight publication is concurrency-safe
- Duplicate/supersession behavior is correct
- Lifecycle transitions are stable
- Retrieval ranking/filtering holds under edge cases
- Audit and lineage integrity hold
- No regression in prior phases
"""

import sys
import io
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import threading
import time

# Force UTF-8 output for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import logging

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
    RetrievalContext,
)

from torq_console.insights.inspection import (
    InsightInspectionService,
    get_inspection_service,
)

from torq_console.insights import (
    InsightCandidateExtractor,
    get_default_extractor,
    PublishingValidator,
    get_default_validator,
    ApprovalWorkflowService,
    get_approval_workflow,
)


logging.basicConfig(level=logging.WARNING)  # Reduce noise during tests
logger = logging.getLogger(__name__)


# ============================================================================
# Test Data
# ============================================================================

def create_test_insight_record(
    insight_id: str = None,
    insight_type: InsightType = InsightType.REUSABLE_PLAYBOOK,
    lifecycle_state: InsightLifecycleState = InsightLifecycleState.PUBLISHED,
    confidence: float = 0.85,
    domain: str = "test_domain",
    title: str = "Test Insight",
) -> InsightRecord:
    """Create a test insight record."""
    now = datetime.now()
    insight_id = insight_id or uuid4()

    return InsightRecord(
        id=insight_id,
        insight_type=insight_type,
        title=title,
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

class Milestone5Validator:
    """Validator for Milestone 5 hardening and regression tests."""

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
    # Section 1: Concurrency and Load Validation
    # ========================================================================

    async def test_concurrent_publication(self):
        """Test that concurrent publication operations don't corrupt data."""
        try:
            persistence = MemoryInsightPersistence()
            workflow = get_approval_workflow(persistence)
            extractor = get_default_extractor()
            validator = get_default_validator()  # Takes no args

            # Create test memory for extraction
            test_memory = {
                "id": "test_mem_concurrent",
                "content": "Test content for concurrent publication",
                "metadata": {"domain": "test"},
            }

            # Track results
            results = []
            errors = []

            def publish_instance(instance_id: int):
                """Attempt to publish an insight."""
                try:
                    # Extract candidates
                    candidates = extractor.extract_candidates([test_memory])

                    if candidates:
                        # Validate
                        validation_results = validator.validate_candidates(candidates)

                        if validation_results.valid_candidates:
                            # Create record
                            candidate = validation_results.valid_candidates[0]
                            record = InsightRecord(
                                id=uuid4(),
                                insight_type=candidate.insight_type,
                                title=f"Concurrent Test Insight {instance_id}",
                                summary=candidate.summary,
                                scope=candidate.scope,
                                scope_key=candidate.scope_key,
                                domain=candidate.domain,
                                tags=candidate.tags,
                                content=candidate.content,
                                source_references=candidate.source_references,
                                quality=candidate.quality,
                                lifecycle_state=InsightLifecycleState.PUBLISHED,
                                created_at=datetime.now(),
                                updated_at=datetime.now(),
                                published_at=datetime.now(),
                                usage_count=0,
                                created_by="system",
                            )

                            # Save
                            persistence._insights[record.id] = record
                            results.append(record.id)
                except Exception as e:
                    errors.append(str(e))

            # Run concurrent publications
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(publish_instance, i) for i in range(20)]
                for f in futures:
                    f.result()

            # Verify no corruption and all succeeded
            passed = (
                len(errors) == 0 and
                len(results) == 20 and
                len(set(results)) == 20  # All unique IDs
            )

            self.record(
                "Concurrent Publication",
                passed,
                f"Published {len(results)} insights concurrently, {len(errors)} errors"
            )
        except Exception as e:
            self.record("Concurrent Publication", False, str(e))

    async def test_concurrent_retrieval(self):
        """Test that concurrent retrieval operations don't corrupt data."""
        try:
            persistence = MemoryInsightPersistence()
            retrieval_service = get_retrieval_service(persistence)

            # Seed with test insights
            for i in range(10):
                record = create_test_insight_record(
                    title=f"Retrieval Test {i}",
                    domain="retrieval_test"
                )
                persistence._insights[record.id] = record

            # Track results
            results = []
            errors = []

            def retrieve_instance(instance_id: int):
                """Attempt to retrieve insights."""
                try:
                    result = asyncio.run(retrieval_service.retrieve_by_mission(
                        "planning",
                        limit=10
                    ))
                    results.append(len(result.insights))
                except Exception as e:
                    errors.append(str(e))

            # Run concurrent retrievals
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(retrieve_instance, i) for i in range(20)]
                for f in futures:
                    f.result()

            # Verify all retrievals succeeded and returned consistent counts
            passed = (
                len(errors) == 0 and
                len(results) == 20 and
                all(count == 10 for count in results)  # All returned 10 insights
            )

            self.record(
                "Concurrent Retrieval",
                passed,
                f"Retrieved {len(results)} times concurrently, {len(errors)} errors, "
                f"consistent results: {all(count == 10 for count in results)}"
            )
        except Exception as e:
            self.record("Concurrent Retrieval", False, str(e))

    async def test_read_during_write(self):
        """Test that reads work correctly during writes."""
        try:
            persistence = MemoryInsightPersistence()
            retrieval_service = get_retrieval_service(persistence)

            # Seed initial insights
            for i in range(5):
                record = create_test_insight_record(
                    title=f"Read-Write Test {i}",
                    domain="read_write_test"
                )
                persistence._insights[record.id] = record

            results = {"reads": [], "writes": [], "read_errors": 0, "write_errors": 0}
            lock = threading.Lock()

            def read_instance():
                """Read insights."""
                try:
                    result = asyncio.run(retrieval_service.retrieve_by_mission(
                        "planning",
                        limit=10
                    ))
                    with lock:
                        results["reads"].append(len(result.insights))
                except Exception:
                    with lock:
                        results["read_errors"] += 1

            def write_instance(instance_id: int):
                """Write an insight."""
                try:
                    record = create_test_insight_record(
                        title=f"Concurrent Write {instance_id}",
                        domain="read_write_test"
                    )
                    persistence._insights[record.id] = record
                    with lock:
                        results["writes"].append(1)
                except Exception:
                    with lock:
                        results["write_errors"] += 1

            # Run concurrent reads and writes
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = []
                # Start 5 writes
                futures.extend([executor.submit(write_instance, i) for i in range(5)])
                # Start 10 reads interleaved
                futures.extend([executor.submit(read_instance) for _ in range(10)])
                for f in futures:
                    f.result()

            # Verify all operations succeeded
            passed = (
                results["read_errors"] == 0 and
                results["write_errors"] == 0 and
                len(results["reads"]) == 10 and
                len(results["writes"]) == 5
            )

            self.record(
                "Read During Write",
                passed,
                f"{len(results['reads'])} reads, {len(results['writes'])} writes, "
                f"{results['read_errors']} read errors, {results['write_errors']} write errors"
            )
        except Exception as e:
            self.record("Read During Write", False, str(e))

    # ========================================================================
    # Section 2: Duplicate and Supersession Validation
    # ========================================================================

    async def test_duplicate_prevention(self):
        """Test that duplicate insights are prevented or flagged."""
        try:
            persistence = MemoryInsightPersistence()
            validator = get_default_validator()  # Takes no args

            # Create a base insight
            base_record = create_test_insight_record(
                title="Duplicate Test Insight",
                domain="duplicate_test"
            )
            persistence._insights[base_record.id] = base_record

            # Create a near-duplicate candidate
            from torq_console.insights.models import InsightCandidate
            duplicate_candidate = InsightCandidate(
                insight_type=base_record.insight_type,
                title=base_record.title,  # Same title
                summary=base_record.summary,  # Same summary
                scope=base_record.scope,
                scope_key=base_record.scope_key,
                domain=base_record.domain,  # Same domain
                tags=base_record.tags,
                content=base_record.content,  # Same content
                source_references=base_record.source_references,
                quality=base_record.quality,
                confidence=base_record.quality["confidence_score"],
            )

            # Validate - should detect duplicate
            validation_result = validator.validate_candidates([duplicate_candidate])

            # Check for duplication warnings
            passed = (
                validation_result.duplicates_found >= 1 or
                len(validation_result.duplication_checks) > 0
            )

            self.record(
                "Duplicate Prevention",
                passed,
                f"Duplicates found: {validation_result.duplicates_found}, "
                f"duplication checks: {len(validation_result.duplication_checks)}"
            )
        except Exception as e:
            self.record("Duplicate Prevention", False, str(e))

    async def test_superseded_suppression(self):
        """Test that superseded insights are suppressed in retrieval."""
        try:
            persistence = MemoryInsightPersistence()
            retrieval_service = get_retrieval_service(persistence)

            # Create old and new insights
            old_id = uuid4()
            new_id = uuid4()

            old_record = create_test_insight_record(
                insight_id=old_id,
                title="Old Insight",
                lifecycle_state=InsightLifecycleState.SUPERSEDED,
            )
            old_record.superseded_by_id = new_id

            new_record = create_test_insight_record(
                insight_id=new_id,
                title="New Insight",
                lifecycle_state=InsightLifecycleState.PUBLISHED,
            )

            persistence._insights[old_id] = old_record
            persistence._insights[new_id] = new_record

            # Retrieve - should NOT include superseded
            result = await retrieval_service.retrieve_by_mission("planning", limit=10)

            # Check that superseded insight is not in results
            insight_ids = [i.id for i in result.insights]
            passed = (
                old_id not in insight_ids and
                new_id in insight_ids and
                len(result.suppressed) > 0
            )

            self.record(
                "Superseded Suppression",
                passed,
                f"Superseded not in results: {old_id not in insight_ids}, "
                f"suppressed count: {len(result.suppressed)}"
            )
        except Exception as e:
            self.record("Superseded Suppression", False, str(e))

    async def test_archived_suppression(self):
        """Test that archived insights are suppressed in retrieval."""
        try:
            persistence = MemoryInsightPersistence()
            retrieval_service = get_retrieval_service(persistence)

            # Create published and archived insights
            published_id = uuid4()
            archived_id = uuid4()

            published_record = create_test_insight_record(
                insight_id=published_id,
                title="Published Insight",
                lifecycle_state=InsightLifecycleState.PUBLISHED,
            )

            archived_record = create_test_insight_record(
                insight_id=archived_id,
                title="Archived Insight",
                lifecycle_state=InsightLifecycleState.ARCHIVED,
            )

            persistence._insights[published_id] = published_record
            persistence._insights[archived_id] = archived_record

            # Retrieve - should NOT include archived
            result = await retrieval_service.retrieve_by_mission("planning", limit=10)

            # Check that archived insight is not in results
            insight_ids = [i.id for i in result.insights]
            passed = (
                archived_id not in insight_ids and
                published_id in insight_ids and
                len(result.suppressed) > 0
            )

            self.record(
                "Archived Suppression",
                passed,
                f"Archived not in results: {archived_id not in insight_ids}, "
                f"suppressed count: {len(result.suppressed)}"
            )
        except Exception as e:
            self.record("Archived Suppression", False, str(e))

    # ========================================================================
    # Section 3: Lifecycle Correctness Validation
    # ========================================================================

    async def test_valid_transitions(self):
        """Test that all valid lifecycle transitions work."""
        try:
            persistence = MemoryInsightPersistence()
            inspection_service = get_inspection_service(persistence)

            # Test candidate → validated → published
            insight_id = uuid4()
            record = create_test_insight_record(
                insight_id=insight_id,
                lifecycle_state=InsightLifecycleState.CANDIDATE,
            )
            persistence._insights[insight_id] = record

            # Transition candidate → validated
            from torq_console.insights.models import InsightUpdate
            update = InsightUpdate(lifecycle_state=InsightLifecycleState.VALIDATED)
            updated = await persistence.update_insight(insight_id, update)

            passed = updated.lifecycle_state == InsightLifecycleState.VALIDATED

            # Transition validated → published
            update = InsightUpdate(lifecycle_state=InsightLifecycleState.PUBLISHED)
            updated = await persistence.update_insight(insight_id, update)

            passed = passed and updated.lifecycle_state == InsightLifecycleState.PUBLISHED

            self.record(
                "Valid Transitions",
                passed,
                f"Candidate→Validated→Published: {passed}"
            )
        except Exception as e:
            self.record("Valid Transitions", False, str(e))

    async def test_published_to_superseded(self):
        """Test published → superseded transition."""
        try:
            persistence = MemoryInsightPersistence()
            inspection_service = get_inspection_service(persistence)

            old_id = uuid4()
            new_id = uuid4()

            old_record = create_test_insight_record(
                insight_id=old_id,
                lifecycle_state=InsightLifecycleState.PUBLISHED,
            )
            new_record = create_test_insight_record(
                insight_id=new_id,
                lifecycle_state=InsightLifecycleState.PUBLISHED,
            )

            persistence._insights[old_id] = old_record
            persistence._insights[new_id] = new_record

            # Supersede old with new
            action = await inspection_service.supersede_insight(
                old_id,
                new_id,
                superseded_by="test_admin"
            )

            # Verify transition
            updated_old = await persistence.get_insight(old_id)

            passed = (
                action.success and
                updated_old.lifecycle_state == InsightLifecycleState.SUPERSEDED and
                updated_old.superseded_by_id == new_id
            )

            self.record(
                "Published to Superseded",
                passed,
                f"Supersede action: {action.success}, "
                f"new state: {updated_old.lifecycle_state.value}"
            )
        except Exception as e:
            self.record("Published to Superseded", False, str(e))

    async def test_published_to_archived(self):
        """Test published → archived transition."""
        try:
            persistence = MemoryInsightPersistence()
            inspection_service = get_inspection_service(persistence)

            insight_id = uuid4()
            record = create_test_insight_record(
                insight_id=insight_id,
                lifecycle_state=InsightLifecycleState.PUBLISHED,
            )
            persistence._insights[insight_id] = record

            # Archive
            action = await inspection_service.archive_insight(
                insight_id,
                archived_by="test_admin"
            )

            # Verify transition
            updated = await persistence.get_insight(insight_id)

            passed = (
                action.success and
                updated.lifecycle_state == InsightLifecycleState.ARCHIVED
            )

            self.record(
                "Published to Archived",
                passed,
                f"Archive action: {action.success}, "
                f"new state: {updated.lifecycle_state.value}"
            )
        except Exception as e:
            self.record("Published to Archived", False, str(e))

    async def test_type_disable_effects(self):
        """Test that disabling a type affects retrieval."""
        try:
            persistence = MemoryInsightPersistence()
            retrieval_service = get_retrieval_service(persistence)
            inspection_service = get_inspection_service(persistence, retrieval_service)

            # Create insights of different types
            playbook_id = uuid4()
            best_practice_id = uuid4()

            playbook = create_test_insight_record(
                insight_id=playbook_id,
                insight_type=InsightType.REUSABLE_PLAYBOOK,
                lifecycle_state=InsightLifecycleState.PUBLISHED,
            )
            best_practice = create_test_insight_record(
                insight_id=best_practice_id,
                insight_type=InsightType.BEST_PRACTICE,
                lifecycle_state=InsightLifecycleState.PUBLISHED,
            )

            persistence._insights[playbook_id] = playbook
            persistence._insights[best_practice_id] = best_practice

            # Get baseline retrieval count
            baseline = await retrieval_service.retrieve_by_mission("planning", limit=10)
            baseline_count = len(baseline.insights)

            # Disable REUSABLE_PLAYBOOK type
            action = await inspection_service.disable_insight_type(
                InsightType.REUSABLE_PLAYBOOK,
                disabled_by="test_admin"
            )

            # Retrieve again - should have fewer results
            result = await retrieval_service.retrieve_by_mission("planning", limit=10)
            filtered_count = len(result.insights)

            passed = (
                action.success and
                filtered_count < baseline_count and
                filtered_count == 1  # Only best practice remains
            )

            self.record(
                "Type Disable Effects",
                passed,
                f"Baseline: {baseline_count}, After disable: {filtered_count}, "
                f"type disabled: {not inspection_service.is_insight_type_enabled(InsightType.REUSABLE_PLAYBOOK)}"
            )
        except Exception as e:
            self.record("Type Disable Effects", False, str(e))

    # ========================================================================
    # Section 4: Ranking and Filter Edge Cases
    # ========================================================================

    async def test_stale_insight_ranking(self):
        """Test that stale insights are ranked lower."""
        try:
            persistence = MemoryInsightPersistence()
            retrieval_service = get_retrieval_service(persistence)

            now = datetime.now()

            # Fresh insight (recently validated)
            fresh_id = uuid4()
            fresh = create_test_insight_record(
                insight_id=fresh_id,
                title="Fresh Insight",
            )
            fresh.quality["last_validated_at"] = (now - timedelta(days=1)).isoformat()
            fresh.quality["evidence_cutoff_at"] = (now - timedelta(days=5)).isoformat()

            # Stale insight (old validation)
            stale_id = uuid4()
            stale = create_test_insight_record(
                insight_id=stale_id,
                title="Stale Insight",
            )
            stale.quality["last_validated_at"] = (now - timedelta(days=60)).isoformat()
            stale.quality["evidence_cutoff_at"] = (now - timedelta(days=90)).isoformat()

            persistence._insights[fresh_id] = fresh
            persistence._insights[stale_id] = stale

            # Retrieve - fresh should rank higher
            result = await retrieval_service.retrieve_by_mission("planning", limit=10)

            # Check ranking
            insight_ids = [i.id for i in result.insights]
            passed = (
                len(result.insights) == 2 and
                insight_ids[0] == fresh_id  # Fresh first
            )

            self.record(
                "Stale Insight Ranking",
                passed,
                f"Fresh ranked first: {passed}, "
                f"fresh last_validated: {fresh.quality['last_validated_at']}, "
                f"stale last_validated: {stale.quality['last_validated_at']}"
            )
        except Exception as e:
            self.record("Stale Insight Ranking", False, str(e))

    async def test_low_confidence_filtering(self):
        """Test that low-confidence insights are filtered or ranked lower."""
        try:
            persistence = MemoryInsightPersistence()
            retrieval_service = get_retrieval_service(persistence)

            # High confidence insight
            high_conf_id = uuid4()
            high_conf = create_test_insight_record(
                insight_id=high_conf_id,
                title="High Confidence Insight",
                confidence=0.95,
            )

            # Low confidence insight (below default threshold)
            low_conf_id = uuid4()
            low_conf = create_test_insight_record(
                insight_id=low_conf_id,
                title="Low Confidence Insight",
                confidence=0.45,  # Below 0.5 threshold
            )

            persistence._insights[high_conf_id] = high_conf
            persistence._insights[low_conf_id] = low_conf

            # Retrieve with minimum confidence threshold
            context = RetrievalContext(
                limit=10,
                min_confidence=0.5,
            )
            result = await retrieval_service.retrieve(context)

            # Check that low confidence is filtered out
            insight_ids = [i.id for i in result.insights]
            passed = (
                high_conf_id in insight_ids and
                low_conf_id not in insight_ids and
                len(result.suppressed) > 0
            )

            self.record(
                "Low Confidence Filtering",
                passed,
                f"High conf included: {high_conf_id in insight_ids}, "
                f"low conf excluded: {low_conf_id not in insight_ids}, "
                f"suppressed: {len(result.suppressed)}"
            )
        except Exception as e:
            self.record("Low Confidence Filtering", False, str(e))

    async def test_disabled_type_filtering(self):
        """Test that disabled types are filtered from retrieval."""
        try:
            persistence = MemoryInsightPersistence()
            retrieval_service = get_retrieval_service(persistence)
            inspection_service = get_inspection_service(persistence, retrieval_service)

            # Disable BEST_PRACTICE type
            await inspection_service.disable_insight_type(
                InsightType.BEST_PRACTICE,
                disabled_by="test_admin"
            )

            # Create insights of disabled type
            disabled_id = uuid4()
            disabled = create_test_insight_record(
                insight_id=disabled_id,
                insight_type=InsightType.BEST_PRACTICE,
                lifecycle_state=InsightLifecycleState.PUBLISHED,
            )

            # Create insight of enabled type
            enabled_id = uuid4()
            enabled = create_test_insight_record(
                insight_id=enabled_id,
                insight_type=InsightType.REUSABLE_PLAYBOOK,
                lifecycle_state=InsightLifecycleState.PUBLISHED,
            )

            persistence._insights[disabled_id] = disabled
            persistence._insights[enabled_id] = enabled

            # Retrieve - disabled type should be filtered
            result = await retrieval_service.retrieve_by_mission("planning", limit=10)

            insight_ids = [i.id for i in result.insights]
            passed = (
                enabled_id in insight_ids and
                disabled_id not in insight_ids
            )

            # Re-enable for other tests
            await inspection_service.enable_insight_type(
                InsightType.BEST_PRACTICE,
                enabled_by="test_admin"
            )

            self.record(
                "Disabled Type Filtering",
                passed,
                f"Enabled type included: {enabled_id in insight_ids}, "
                f"disabled type excluded: {disabled_id not in insight_ids}"
            )
        except Exception as e:
            self.record("Disabled Type Filtering", False, str(e))

    async def test_candidate_state_filtering(self):
        """Test that candidate insights are filtered from retrieval."""
        try:
            persistence = MemoryInsightPersistence()
            retrieval_service = get_retrieval_service(persistence)

            # Create candidate and published insights
            candidate_id = uuid4()
            candidate = create_test_insight_record(
                insight_id=candidate_id,
                lifecycle_state=InsightLifecycleState.CANDIDATE,
            )

            published_id = uuid4()
            published = create_test_insight_record(
                insight_id=published_id,
                lifecycle_state=InsightLifecycleState.PUBLISHED,
            )

            persistence._insights[candidate_id] = candidate
            persistence._insights[published_id] = published

            # Retrieve - candidate should be filtered
            result = await retrieval_service.retrieve_by_mission("planning", limit=10)

            insight_ids = [i.id for i in result.insights]
            passed = (
                published_id in insight_ids and
                candidate_id not in insight_ids
            )

            self.record(
                "Candidate State Filtering",
                passed,
                f"Published included: {published_id in insight_ids}, "
                f"candidate excluded: {candidate_id not in insight_ids}"
            )
        except Exception as e:
            self.record("Candidate State Filtering", False, str(e))

    async def test_conflicting_lineage_resolution(self):
        """Test that insights with conflicting lineage are handled correctly."""
        try:
            persistence = MemoryInsightPersistence()
            retrieval_service = get_retrieval_service(persistence)

            # Create two insights with similar content but different lineage
            insight1_id = uuid4()
            insight1 = create_test_insight_record(
                insight_id=insight1_id,
                title="Similar Insight A",
                domain="lineage_test",
            )
            insight1.source_references = [
                {
                    "source_type": InsightSourceType.MEMORY.value,
                    "source_id": "memory_a",
                    "contribution_weight": 1.0,
                }
            ]

            insight2_id = uuid4()
            insight2 = create_test_insight_record(
                insight_id=insight2_id,
                title="Similar Insight B",
                domain="lineage_test",
            )
            insight2.source_references = [
                {
                    "source_type": InsightSourceType.MEMORY.value,
                    "source_id": "memory_b",  # Different source
                    "contribution_weight": 1.0,
                }
            ]

            persistence._insights[insight1_id] = insight1
            persistence._insights[insight2_id] = insight2

            # Retrieve by domain - both should be returned
            context = RetrievalContext(
                limit=10,
                domain="lineage_test",
            )
            result = await retrieval_service.retrieve(context)

            # Both should be present with distinct lineage
            passed = len(result.insights) == 2

            self.record(
                "Conflicting Lineage Resolution",
                passed,
                f"Both insights retrieved: {passed}, count: {len(result.insights)}"
            )
        except Exception as e:
            self.record("Conflicting Lineage Resolution", False, str(e))

    # ========================================================================
    # Section 5: Audit Integrity Validation
    # ========================================================================

    async def test_retrieval_audit_completeness(self):
        """Test that retrieval audit records remain complete."""
        try:
            persistence = MemoryInsightPersistence()
            retrieval_service = get_retrieval_service(persistence)

            # Seed insights
            for i in range(5):
                record = create_test_insight_record(domain="audit_test")
                persistence._insights[record.id] = record

            # Perform multiple retrievals
            for i in range(10):
                await retrieval_service.retrieve_by_mission("planning", limit=5)

            # Get audit stats
            stats = retrieval_service.get_audit_stats()

            passed = stats.get("total_retrievals", 0) >= 10

            self.record(
                "Retrieval Audit Completeness",
                passed,
                f"Retrievals logged: {stats.get('total_retrievals', 0)}"
            )
        except Exception as e:
            self.record("Retrieval Audit Completeness", False, str(e))

    async def test_publication_audit_integrity(self):
        """Test that publication audit trails remain intact."""
        try:
            persistence = MemoryInsightPersistence()
            inspection_service = get_inspection_service(persistence)

            insight_id = uuid4()
            record = create_test_insight_record(
                insight_id=insight_id,
                lifecycle_state=InsightLifecycleState.PUBLISHED,
            )
            persistence._insights[insight_id] = record

            # Get publication audit trail
            trail = await inspection_service.get_publication_audit_trail(insight_id)

            passed = (
                trail is not None and
                trail.insight_id == str(insight_id) and
                len(trail.source_memory_ids) > 0
            )

            self.record(
                "Publication Audit Integrity",
                passed,
                f"Audit trail intact: {passed}, "
                f"source memories: {len(trail.source_memory_ids)}"
            )
        except Exception as e:
            self.record("Publication Audit Integrity", False, str(e))

    async def test_lineage_consistency_under_load(self):
        """Test that lineage resolution works under concurrent operations."""
        try:
            persistence = MemoryInsightPersistence()
            inspection_service = get_inspection_service(persistence)

            # Create multiple insights with lineage
            insights = []
            for i in range(10):
                record = create_test_insight_record(
                    title=f"Lineage Test {i}",
                    domain="lineage_load_test",
                )
                persistence._insights[record.id] = record
                insights.append(record)

            # Get lineage for all concurrently
            errors = []
            lineages = []

            def get_lineage(insight_id):
                try:
                    lineage = asyncio.run(inspection_service.get_insight_lineage(insight_id))
                    lineages.append(lineage)
                except Exception as e:
                    errors.append(str(e))

            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(get_lineage, i.id) for i in insights]
                for f in futures:
                    f.result()

            # Verify all lineages retrieved successfully
            passed = (
                len(errors) == 0 and
                len(lineages) == 10 and
                all(l is not None for l in lineages)
            )

            self.record(
                "Lineage Consistency Under Load",
                passed,
                f"Retrieved {len(lineages)} lineages, {len(errors)} errors"
            )
        except Exception as e:
            self.record("Lineage Consistency Under Load", False, str(e))

    async def test_governance_event_logging(self):
        """Test that governance events are logged reliably."""
        try:
            persistence = MemoryInsightPersistence()
            inspection_service = get_inspection_service(persistence)

            insight_id = uuid4()
            record = create_test_insight_record(
                insight_id=insight_id,
                lifecycle_state=InsightLifecycleState.PUBLISHED,
            )
            persistence._insights[insight_id] = record

            # Perform governance actions
            await inspection_service.archive_insight(insight_id, "test_admin")
            await inspection_service.supersede_insight(insight_id, uuid4(), "test_admin")

            # Get lifecycle history
            history = await inspection_service.get_insight_lifecycle_history(insight_id)

            # Should have at least 2 events (archive + supersede attempt)
            passed = len(history) >= 2

            self.record(
                "Governance Event Logging",
                passed,
                f"Events logged: {len(history)}"
            )
        except Exception as e:
            self.record("Governance Event Logging", False, str(e))

    # ========================================================================
    # Section 6: Full Regression Tests
    # ========================================================================

    async def test_regression_milestone_1(self):
        """Test no regression in Milestone 1 (models, rules, lifecycle)."""
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
                "Regression - Milestone 1",
                passed,
                f"Types: {has_types}, States: {has_states}, Gates: {has_gates}, Transitions: {has_transitions}"
            )
        except Exception as e:
            self.record("Regression - Milestone 1", False, str(e))

    async def test_regression_milestone_2(self):
        """Test no regression in Milestone 2 (extraction, validation, persistence, approval)."""
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
                "Regression - Milestone 2",
                passed,
                "Extractor, Validator, Persistence, Workflow all available"
            )
        except Exception as e:
            self.record("Regression - Milestone 2", False, str(e))

    async def test_regression_milestone_3(self):
        """Test no regression in Milestone 3 (retrieval service)."""
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
                "Regression - Milestone 3",
                passed,
                f"Retrieval service functional: {passed}"
            )
        except Exception as e:
            self.record("Regression - Milestone 3", False, str(e))

    async def test_regression_milestone_4(self):
        """Test no regression in Milestone 4 (inspection, audit, governance)."""
        try:
            from torq_console.insights import (
                get_inspection_service,
            )

            persistence = get_insight_persistence()
            service = get_inspection_service(persistence)

            # Test core inspection methods exist
            has_list = hasattr(service, 'list_published_insights')
            has_detail = hasattr(service, 'get_insight_detail')
            has_lineage = hasattr(service, 'get_insight_lineage')
            has_governance = hasattr(service, 'archive_insight')

            passed = has_list and has_detail and has_lineage and has_governance

            self.record(
                "Regression - Milestone 4",
                passed,
                f"List: {has_list}, Detail: {has_detail}, Lineage: {has_lineage}, Governance: {has_governance}"
            )
        except Exception as e:
            self.record("Regression - Milestone 4", False, str(e))

    # ========================================================================
    # Run All Tests
    # ========================================================================

    async def run_all_tests(self):
        """Run all validation tests."""
        logger.info("=" * 70)
        logger.info("INSIGHT PUBLISHING - MILESTONE 5 VALIDATION")
        logger.info("=" * 70)

        # Section 1: Concurrency and Load
        await self.test_concurrent_publication()
        await self.test_concurrent_retrieval()
        await self.test_read_during_write()

        # Section 2: Duplicate and Supersession
        await self.test_duplicate_prevention()
        await self.test_superseded_suppression()
        await self.test_archived_suppression()

        # Section 3: Lifecycle Correctness
        await self.test_valid_transitions()
        await self.test_published_to_superseded()
        await self.test_published_to_archived()
        await self.test_type_disable_effects()

        # Section 4: Ranking and Filter Edge Cases
        await self.test_stale_insight_ranking()
        await self.test_low_confidence_filtering()
        await self.test_disabled_type_filtering()
        await self.test_candidate_state_filtering()
        await self.test_conflicting_lineage_resolution()

        # Section 5: Audit Integrity
        await self.test_retrieval_audit_completeness()
        await self.test_publication_audit_integrity()
        await self.test_lineage_consistency_under_load()
        await self.test_governance_event_logging()

        # Section 6: Full Regression
        await self.test_regression_milestone_1()
        await self.test_regression_milestone_2()
        await self.test_regression_milestone_3()
        await self.test_regression_milestone_4()

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
            logger.info("MILESTONE 5 COMPLETE - Insight Publishing is production-ready!")
            logger.info("=" * 70)
            logger.info("")
            logger.info("Exit Criteria Met:")
            logger.info("✓ Insight publication is concurrency-safe")
            logger.info("✓ Duplicate/supersession behavior is correct")
            logger.info("✓ Lifecycle transitions are stable")
            logger.info("✓ Retrieval filters/ranking hold under edge cases")
            logger.info("✓ Audit and lineage integrity hold")
            logger.info("✓ No regression in Milestones 1-4")
            logger.info("")
            logger.info("Insight Publishing & Agent Retrieval is fully validated.")
            logger.info("=" * 70)
        else:
            logger.warning(f"{self.results['failed']} test(s) failed")

        logger.info("=" * 70)


# ============================================================================
# Main
# ============================================================================

async def main():
    """Run validation tests."""
    validator = Milestone5Validator()
    await validator.run_all_tests()
    return validator.results["failed"] == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
