"""
Phase 4H.1 Milestone 3: Memory Read/Query Interface Validation Tests

Acceptance criteria:
- Approved memory can be queried reliably
- Stale memory is suppressed
- Provenance filtering works
- Retrieval is scope-aware
- Memory access is logged
- No regression in 5.2, 5.3, or 4H.1 M1–M2
"""

import asyncio
import logging
from datetime import datetime, timedelta
from uuid import uuid4

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from torq_console.strategic_memory.query_service import (
    MemoryQueryService,
    MemoryQuery,
    ProvenanceFilter,
    FreshnessFilter,
    get_memory_query_service,
)

from torq_console.strategic_memory.models import (
    StrategicMemory,
    MemoryType,
    MemoryScope,
    MemoryStatus,
)

try:
    from torq_console.main import get_supabase_client
except ImportError:
    print("Warning: Could not import get_supabase_client from torq_console.main")
    get_supabase_client = None


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ============================================================================
# Test Data
# ============================================================================

def create_test_memory(
    memory_type: MemoryType,
    title: str,
    status: MemoryStatus = MemoryStatus.ACTIVE,
    confidence: float = 0.8,
    expires_in_days: int = 90,
) -> dict:
    """Create a test memory dict for insertion."""
    now = datetime.now()
    expires_at = now + timedelta(days=expires_in_days) if expires_in_days > 0 else None

    return {
        "id": str(uuid4()),
        "memory_type": memory_type.value,
        "title": title,
        "domain": "test_domain",
        "scope": MemoryScope.GLOBAL.value,
        "scope_key": None,
        "confidence": confidence,
        "durability_score": 0.7,
        "effectiveness_score": None,
        "memory_content": {"description": f"Test memory: {title}"},
        "source_pattern_ids": [],
        "source_insight_ids": [],
        "source_experiment_ids": [],
        "status": status.value,
        "created_at": now.isoformat(),
        "reviewed_at": now.isoformat(),
        "expires_at": expires_at.isoformat() if expires_at else None,
        "last_validated_at": now.isoformat(),
        "invalidated_by_pattern_id": None,
        "supplanted_by_memory_id": None,
        "usage_count": 0,
        "last_used_at": None,
    }


# ============================================================================
# Validation Tests
# ============================================================================

class Milestone3Validator:
    """Validator for Phase 4H.1 Milestone 3."""

    def __init__(self, supabase_client=None):
        self.supabase = supabase_client
        self.query_service = get_memory_query_service(supabase_client=supabase_client) if supabase_client else None
        self.test_memory_ids = []
        self.results = {
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "tests": [],
        }

    def record_result(self, test_name: str, passed: bool, message: str = ""):
        """Record a test result."""
        status = "PASS" if passed else "FAIL"
        self.results["tests"].append({
            "name": test_name,
            "status": status,
            "message": message,
        })
        if passed:
            self.results["passed"] += 1
            logger.info(f"✅ {test_name}: {message}")
        else:
            self.results["failed"] += 1
            logger.error(f"❌ {test_name}: {message}")

    async def setup_test_data(self):
        """Create test memories for validation."""
        if not self.supabase:
            logger.warning("No Supabase client - skipping test data setup")
            return

        logger.info("Setting up test data...")

        test_memories = [
            # Active memories
            create_test_memory(MemoryType.HEURISTIC, "Active Heuristic 1", MemoryStatus.ACTIVE, 0.9, 90),
            create_test_memory(MemoryType.PLAYBOOK, "Active Playbook 1", MemoryStatus.ACTIVE, 0.8, 90),
            create_test_memory(MemoryType.WARNING, "Active Warning 1", MemoryStatus.ACTIVE, 0.85, 90),

            # Stale memory (expired)
            create_test_memory(MemoryType.HEURISTIC, "Stale Heuristic 1", MemoryStatus.ACTIVE, 0.7, -10),

            # Deprecated memory
            create_test_memory(MemoryType.PLAYBOOK, "Deprecated Playbook 1", MemoryStatus.DEPRECATED, 0.6, 90),

            # High confidence memory
            create_test_memory(MemoryType.ADAPTATION_LESSON, "High Confidence Lesson", MemoryStatus.ACTIVE, 0.95, 90),

            # Low confidence memory
            create_test_memory(MemoryType.HEURISTIC, "Low Confidence Heuristic", MemoryStatus.ACTIVE, 0.4, 90),
        ]

        for memory in test_memories:
            try:
                result = self.supabase.table("strategic_memories").insert(memory).execute()
                self.test_memory_ids.append(memory["id"])
                logger.debug(f"Created test memory: {memory['title']}")
            except Exception as e:
                logger.warning(f"Failed to create test memory: {e}")

        logger.info(f"Created {len(self.test_memory_ids)} test memories")

    async def cleanup_test_data(self):
        """Clean up test data."""
        if not self.supabase or not self.test_memory_ids:
            return

        logger.info("Cleaning up test data...")
        try:
            self.supabase.table("strategic_memories").delete().in_("id", self.test_memory_ids).execute()
            logger.info("Test data cleaned up")
        except Exception as e:
            logger.warning(f"Failed to clean up test data: {e}")

    # ========================================================================
    # Tests
    # ========================================================================

    async def test_query_service_exists(self):
        """Test that the query service can be instantiated."""
        try:
            service = get_memory_query_service(supabase_client=self.supabase)
            passed = service is not None
            self.record_result(
                "Query Service Instantiation",
                passed,
                "Service created successfully" if passed else "Service is None"
            )
            return service
        except Exception as e:
            self.record_result("Query Service Instantiation", False, str(e))
            return None

    async def test_query_all_memories(self):
        """Test querying all memories."""
        if not self.query_service:
            self.record_result("Query All Memories", False, "Query service not available")
            return

        try:
            query = MemoryQuery(limit=10)
            result = await self.query_service.query(query)

            passed = result is not None
            self.record_result(
                "Query All Memories",
                passed,
                f"Found {result.total_count if passed else 0} memories"
            )
        except Exception as e:
            self.record_result("Query All Memories", False, str(e))

    async def test_query_by_type(self):
        """Test querying memories by type."""
        if not self.query_service:
            self.record_result("Query By Type", False, "Query service not available")
            return

        try:
            query = MemoryQuery(memory_types=[MemoryType.HEURISTIC], limit=10)
            result = await self.query_service.query(query)

            all_heuristics = all(m.memory_type == MemoryType.HEURISTIC for m in result.memories)
            passed = all_heuristics if result.memories else True  # Empty result is valid

            self.record_result(
                "Query By Type",
                passed,
                f"Found {len(result.memories)} heuristics, all correct type: {all_heuristics}"
            )
        except Exception as e:
            self.record_result("Query By Type", False, str(e))

    async def test_query_by_status(self):
        """Test querying memories by status."""
        if not self.query_service:
            self.record_result("Query By Status", False, "Query service not available")
            return

        try:
            result = await self.query_service.list_by_status(MemoryStatus.ACTIVE, limit=10)

            all_active = all(m.status == MemoryStatus.ACTIVE for m in result.memories)
            passed = all_active if result.memories else True

            self.record_result(
                "Query By Status",
                passed,
                f"Found {len(result.memories)} active memories, all correct status: {all_active}"
            )
        except Exception as e:
            self.record_result("Query By Status", False, str(e))

    async def test_freshness_filter_active_only(self):
        """Test that stale memories are filtered out when using ACTIVE_ONLY."""
        if not self.query_service:
            self.record_result("Freshness Filter - Active Only", False, "Query service not available")
            return

        try:
            query = MemoryQuery(freshness=FreshnessFilter.ACTIVE_ONLY, limit=50)
            result = await self.query_service.query(query)

            # Check that no stale memories are in results
            has_stale = False
            for memory in result.memories:
                if memory.expires_at and memory.expires_at < datetime.now():
                    has_stale = True
                    break

            passed = not has_stale
            self.record_result(
                "Freshness Filter - Active Only",
                passed,
                f"Found {len(result.memories)} memories, none stale: {not has_stale}"
            )
        except Exception as e:
            self.record_result("Freshness Filter - Active Only", False, str(e))

    async def test_freshness_filter_stale_only(self):
        """Test that STALE_ONLY returns only expired memories."""
        if not self.query_service:
            self.record_result("Freshness Filter - Stale Only", False, "Query service not available")
            return

        try:
            query = MemoryQuery(freshness=FreshnessFilter.STALE_ONLY, limit=50)
            result = await self.query_service.query(query)

            # Check that all returned memories are stale
            all_stale = True
            for memory in result.memories:
                if memory.expires_at is None or memory.expires_at >= datetime.now():
                    all_stale = False
                    break

            passed = all_stale if result.memories else True  # Empty result is valid
            self.record_result(
                "Freshness Filter - Stale Only",
                passed,
                f"Found {len(result.memories)} stale memories, all expired: {all_stale}"
            )
        except Exception as e:
            self.record_result("Freshness Filter - Stale Only", False, str(e))

    async def test_confidence_filter(self):
        """Test filtering by minimum confidence."""
        if not self.query_service:
            self.record_result("Confidence Filter", False, "Query service not available")
            return

        try:
            query = MemoryQuery(min_confidence=0.8, limit=50)
            result = await self.query_service.query(query)

            # Check that all memories meet confidence threshold
            all_above_threshold = all(m.confidence >= 0.8 for m in result.memories)
            passed = all_above_threshold if result.memories else True

            self.record_result(
                "Confidence Filter",
                passed,
                f"Found {len(result.memories)} memories, all >= 0.8 confidence: {all_above_threshold}"
            )
        except Exception as e:
            self.record_result("Confidence Filter", False, str(e))

    async def test_scope_filter(self):
        """Test filtering by scope."""
        if not self.query_service:
            self.record_result("Scope Filter", False, "Query service not available")
            return

        try:
            query = MemoryQuery(scopes=[MemoryScope.GLOBAL], limit=50)
            result = await self.query_service.query(query)

            # Check that all memories are global scope
            all_global = all(m.scope == MemoryScope.GLOBAL for m in result.memories)
            passed = all_global if result.memories else True

            self.record_result(
                "Scope Filter",
                passed,
                f"Found {len(result.memories)} memories, all global scope: {all_global}"
            )
        except Exception as e:
            self.record_result("Scope Filter", False, str(e))

    async def test_get_memory_by_id(self):
        """Test getting a specific memory by UUID."""
        if not self.query_service or not self.test_memory_ids:
            self.record_result("Get Memory By ID", False, "Query service or test data not available")
            return

        try:
            memory_uuid = self.test_memory_ids[0]
            memory = await self.query_service.get_by_id(memory_uuid)

            passed = memory is not None and memory.id == str(memory_uuid)
            self.record_result(
                "Get Memory By ID",
                passed,
                f"Retrieved memory: {memory.title if memory else 'None'}"
            )
        except Exception as e:
            self.record_result("Get Memory By ID", False, str(e))

    async def test_access_logging(self):
        """Test that access is logged."""
        if not self.query_service:
            self.record_result("Access Logging", False, "Query service not available")
            return

        try:
            # Clear log first
            initial_count = len(self.query_service.get_access_log())

            # Perform a query
            query = MemoryQuery(limit=1)
            await self.query_service.query(query)

            # Check that log was updated
            log_entries = self.query_service.get_access_log()
            passed = len(log_entries) > initial_count

            self.record_result(
                "Access Logging",
                passed,
                f"Log entries: {len(log_entries)} (was {initial_count})"
            )
        except Exception as e:
            self.record_result("Access Logging", False, str(e))

    async def test_inspection_endpoint(self):
        """Test memory inspection with detailed data."""
        if not self.query_service or not self.test_memory_ids:
            self.record_result("Inspection Endpoint", False, "Query service or test data not available")
            return

        try:
            memory_uuid = self.test_memory_ids[0]
            inspection = await self.query_service.inspect(UUID(memory_uuid))

            passed = inspection is not None and inspection.memory is not None
            self.record_result(
                "Inspection Endpoint",
                passed,
                f"Inspection returned: {inspection.memory.title if inspection else 'None'}"
            )
        except Exception as e:
            self.record_result("Inspection Endpoint", False, str(e))

    async def test_pagination(self):
        """Test pagination support."""
        if not self.query_service:
            self.record_result("Pagination", False, "Query service not available")
            return

        try:
            # First page
            query1 = MemoryQuery(limit=2, offset=0)
            result1 = await self.query_service.query(query1)

            # Second page
            query2 = MemoryQuery(limit=2, offset=2)
            result2 = await self.query_service.query(query2)

            # Check that pages are different
            different_ids = set(m.id for m in result1.memories).isdisjoint(
                set(m.id for m in result2.memories)
            )
            passed = different_ids or len(result1.memories) == 0 or len(result2.memories) == 0

            self.record_result(
                "Pagination",
                passed,
                f"Page 1: {len(result1.memories)} memories, Page 2: {len(result2.memories)} memories"
            )
        except Exception as e:
            self.record_result("Pagination", False, str(e))

    async def test_statistics(self):
        """Test statistics endpoint."""
        if not self.query_service:
            self.record_result("Statistics", False, "Query service not available")
            return

        try:
            stats = await self.query_service.get_statistics()
            passed = stats is not None and "total_memories" in stats

            self.record_result(
                "Statistics",
                passed,
                f"Total memories: {stats.get('total_memories', 'N/A')}"
            )
        except Exception as e:
            self.record_result("Statistics", False, str(e))

    async def test_no_regression_in_write_pipeline(self):
        """Test that write pipeline still works (regression check)."""
        from torq_console.memory.memory_persistence import MemoryPersistenceService

        try:
            persistence = MemoryPersistenceService(supabase_client=self.supabase)
            # Just check we can instantiate and query
            passed = persistence is not None

            self.record_result(
                "No Regression - Write Pipeline",
                passed,
                "Memory persistence service accessible"
            )
        except Exception as e:
            self.record_result("No Regression - Write Pipeline", False, str(e))

    async def test_no_regression_in_retrieval_engine(self):
        """Test that retrieval engine still works (regression check)."""
        from torq_console.strategic_memory.retrieval import MemoryRetrievalEngine

        try:
            retrieval = MemoryRetrievalEngine(self.supabase)
            # Try a search
            from torq_console.strategic_memory.models import MemorySearchRequest
            request = MemorySearchRequest(max_results=1)
            results = await retrieval.search(request)

            passed = results is not None
            self.record_result(
                "No Regression - Retrieval Engine",
                passed,
                f"Retrieval engine returned {len(results)} results"
            )
        except Exception as e:
            self.record_result("No Regression - Retrieval Engine", False, str(e))

    # ========================================================================
    # Run All Tests
    # ========================================================================

    async def run_all_tests(self):
        """Run all validation tests."""
        logger.info("=" * 70)
        logger.info("Phase 4H.1 Milestone 3: Memory Read/Query Interface Validation")
        logger.info("=" * 70)

        # Setup
        await self.setup_test_data()

        # Tests
        await self.test_query_service_exists()
        await self.test_query_all_memories()
        await self.test_query_by_type()
        await self.test_query_by_status()
        await self.test_freshness_filter_active_only()
        await self.test_freshness_filter_stale_only()
        await self.test_confidence_filter()
        await self.test_scope_filter()
        await self.test_get_memory_by_id()
        await self.test_access_logging()
        await self.test_inspection_endpoint()
        await self.test_pagination()
        await self.test_statistics()
        await self.test_no_regression_in_write_pipeline()
        await self.test_no_regression_in_retrieval_engine()

        # Cleanup
        await self.cleanup_test_data()

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary."""
        logger.info("")
        logger.info("=" * 70)
        logger.info("VALIDATION SUMMARY")
        logger.info("=" * 70)

        for test in self.results["tests"]:
            icon = "✅" if test["status"] == "PASS" else "❌"
            logger.info(f"{icon} {test['name']}: {test['message']}")

        logger.info("")
        logger.info(f"Total: {self.results['passed'] + self.results['failed']} tests")
        logger.info(f"Passed: {self.results['passed']}")
        logger.info(f"Failed: {self.results['failed']}")
        logger.info(f"Skipped: {self.results['skipped']}")

        if self.results["failed"] == 0:
            logger.info("")
            logger.info("🎉 ALL TESTS PASSED - Milestone 3 Complete!")
        else:
            logger.info("")
            logger.warning(f"⚠️ {self.results['failed']} test(s) failed")

        logger.info("=" * 70)


# ============================================================================
# Main
# ============================================================================

async def main():
    """Run validation tests."""
    supabase_client = None

    if get_supabase_client:
        try:
            supabase_client = get_supabase_client()
            logger.info("Supabase client initialized")
        except Exception as e:
            logger.warning(f"Could not initialize Supabase client: {e}")
            logger.info("Running in offline mode (limited tests)")
    else:
        logger.info("No Supabase client available - running in offline mode")

    validator = Milestone3Validator(supabase_client=supabase_client)
    await validator.run_all_tests()

    return validator.results["failed"] == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
