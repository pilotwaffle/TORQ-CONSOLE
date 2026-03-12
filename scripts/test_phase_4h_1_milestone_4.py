"""
Phase 4H.1 Milestone 4: Audit, Inspection, and Control Layer Validation Tests

Acceptance criteria:
- Accepted and rejected memory decisions are inspectable
- Retrieval events are auditable
- Memory traceability is visible end to end
- Control actions work without changing foundations
- No regression in Milestones 1-3 or Phases 5.2/5.3
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

from torq_console.strategic_memory.inspection_service import (
    MemoryInspectionService,
    GovernanceAction,
    GovernanceActionResult,
    get_memory_inspection_service,
)

from torq_console.strategic_memory.query_service import (
    MemoryQueryService,
    MemoryQuery,
    get_memory_query_service,
)

from torq_console.strategic_memory.models import (
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

def create_test_memory_dict(
    memory_type: MemoryType,
    title: str,
    status: MemoryStatus = MemoryStatus.ACTIVE,
    confidence: float = 0.8,
) -> dict:
    """Create a test memory dict."""
    now = datetime.now()
    return {
        "id": str(uuid4()),
        "memory_type": memory_type.value,
        "title": title,
        "domain": "test_domain",
        "scope": MemoryScope.GLOBAL.value,
        "scope_key": None,
        "confidence": confidence,
        "durability_score": 0.7,
        "memory_content": {"description": f"Test: {title}"},
        "source_pattern_ids": [],
        "source_insight_ids": [],
        "source_experiment_ids": [],
        "status": status.value,
        "created_at": now.isoformat(),
        "reviewed_at": now.isoformat(),
        "expires_at": (now + timedelta(days=90)).isoformat(),
        "last_validated_at": now.isoformat(),
        "usage_count": 0,
        "last_used_at": None,
    }


# ============================================================================
# Validation Tests
# ============================================================================

class Milestone4Validator:
    """Validator for Phase 4H.1 Milestone 4."""

    def __init__(self, supabase_client=None):
        self.supabase = supabase_client
        self.inspection_service = get_memory_inspection_service(supabase_client=supabase_client) if supabase_client else None
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
            logger.info(f"[OK] {test_name}: {message}")
        else:
            self.results["failed"] += 1
            logger.error(f"[FAIL] {test_name}: {message}")

    async def setup_test_data(self):
        """Create test data including control states."""
        if not self.supabase:
            logger.warning("No Supabase client - skipping test data setup")
            return

        logger.info("Setting up Milestone 4 test data...")

        # Create test memories
        test_memories = [
            create_test_memory_dict(MemoryType.HEURISTIC, "Test Heuristic for Control"),
            create_test_memory_dict(MemoryType.PLAYBOOK, "Test Playbook for Supersession"),
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
            # Clean up control states
            self.supabase.table("memory_control_state").delete().in_(
                "memory_id", self.test_memory_ids
            ).execute()

            # Clean up memories
            self.supabase.table("strategic_memories").delete().in_(
                "id", self.test_memory_ids
            ).execute()

            logger.info("Test data cleaned up")
        except Exception as e:
            logger.warning(f"Failed to clean up test data: {e}")

    # ========================================================================
    # Tests
    # ========================================================================

    async def test_inspection_service_exists(self):
        """Test that the inspection service can be instantiated."""
        try:
            service = get_memory_inspection_service(supabase_client=self.supabase)
            passed = service is not None
            self.record_result(
                "Inspection Service Instantiation",
                passed,
                "Service created successfully" if passed else "Service is None"
            )
        except Exception as e:
            self.record_result("Inspection Service Instantiation", False, str(e))

    async def test_get_memory_detail(self):
        """Test getting detailed memory record."""
        if not self.inspection_service or not self.test_memory_ids:
            self.record_result("Get Memory Detail", False, "Service or test data not available")
            return

        try:
            memory_uuid = self.test_memory_ids[0]
            detail = await self.inspection_service.get_memory_detail(UUID(memory_uuid))

            passed = detail is not None and detail.memory is not None
            self.record_result(
                "Get Memory Detail",
                passed,
                f"Retrieved detail for: {detail.memory.title if detail else 'None'}"
            )
        except Exception as e:
            self.record_result("Get Memory Detail", False, str(e))

    async def test_get_traceability(self):
        """Test getting memory traceability."""
        if not self.inspection_service or not self.test_memory_ids:
            self.record_result("Get Traceability", False, "Service or test data not available")
            return

        try:
            memory_uuid = self.test_memory_ids[0]
            traceability = await self.inspection_service.get_traceability(UUID(memory_uuid))

            passed = traceability is not None
            self.record_result(
                "Get Traceability",
                passed,
                f"Retrieved traceability: {traceability.memory_title if traceability else 'None'}"
            )
        except Exception as e:
            self.record_result("Get Traceability", False, str(e))

    async def test_get_validation_decisions(self):
        """Test getting validation decision reports."""
        if not self.inspection_service:
            self.record_result("Get Validation Decisions", False, "Service not available")
            return

        try:
            decisions = await self.inspection_service.get_validation_decisions(limit=10)
            passed = decisions is not None
            self.record_result(
                "Get Validation Decisions",
                passed,
                f"Retrieved {len(decisions)} validation events"
            )
        except Exception as e:
            self.record_result("Get Validation Decisions", False, str(e))

    async def test_get_rejection_logs(self):
        """Test getting rejection log entries."""
        if not self.inspection_service:
            self.record_result("Get Rejection Logs", False, "Service not available")
            return

        try:
            logs = await self.inspection_service.get_rejection_logs(limit=10)
            passed = logs is not None
            self.record_result(
                "Get Rejection Logs",
                passed,
                f"Retrieved {len(logs)} rejection log entries"
            )
        except Exception as e:
            self.record_result("Get Rejection Logs", False, str(e))

    async def test_get_retrieval_audit(self):
        """Test getting retrieval audit records."""
        if not self.inspection_service or not self.test_memory_ids:
            self.record_result("Get Retrieval Audit", False, "Service or test data not available")
            return

        try:
            memory_uuid = self.test_memory_ids[0]
            audit = await self.inspection_service.get_retrieval_audit(memory_uuid, limit=10)
            passed = audit is not None
            self.record_result(
                "Get Retrieval Audit",
                passed,
                f"Retrieved {len(audit)} audit records"
            )
        except Exception as e:
            self.record_result("Get Retrieval Audit", False, str(e))

    async def test_get_retrieval_summary(self):
        """Test getting retrieval summary."""
        if not self.inspection_service or not self.test_memory_ids:
            self.record_result("Get Retrieval Summary", False, "Service or test data not available")
            return

        try:
            memory_uuid = self.test_memory_ids[0]
            summary = await self.inspection_service.get_retrieval_summary(memory_uuid)
            passed = summary is not None
            self.record_result(
                "Get Retrieval Summary",
                passed,
                f"Retrieved summary with {summary.total_access_count if summary else 0} accesses"
            )
        except Exception as e:
            self.record_result("Get Retrieval Summary", False, str(e))

    async def test_get_governance_statistics(self):
        """Test getting governance statistics."""
        if not self.inspection_service:
            self.record_result("Get Governance Statistics", False, "Service not available")
            return

        try:
            stats = await self.inspection_service.get_governance_statistics()
            passed = stats is not None
            self.record_result(
                "Get Governance Statistics",
                passed,
                f"Statistics: {stats.get('total_memories', 'N/A')} total memories"
            )
        except Exception as e:
            self.record_result("Get Governance Statistics", False, str(e))

    async def test_disable_memory_action(self):
        """Test disable memory governance action."""
        if not self.inspection_service or not self.test_memory_ids:
            self.record_result("Disable Memory Action", False, "Service or test data not available")
            return

        try:
            memory_uuid = self.test_memory_ids[0]

            # Disable the memory
            action = GovernanceAction(
                action_type="disable",
                memory_id=UUID(memory_uuid),
                reason="Test disable action",
                performed_by="test_validator",
            )

            result = await self.inspection_service.execute_governance_action(action)

            passed = result.success
            self.record_result(
                "Disable Memory Action",
                passed,
                f"Disable action {'succeeded' if passed else 'failed'}: {result.error or result.message}"
            )

            # Re-enable for cleanup
            if result.success:
                enable_action = GovernanceAction(
                    action_type="enable",
                    memory_id=UUID(memory_uuid),
                    reason="Re-enable after test",
                    performed_by="test_validator",
                )
                await self.inspection_service.execute_governance_action(enable_action)

        except Exception as e:
            self.record_result("Disable Memory Action", False, str(e))

    async def test_expire_memory_action(self):
        """Test expire memory governance action."""
        if not self.inspection_service or not self.test_memory_ids:
            self.record_result("Expire Memory Action", False, "Service or test data not available")
            return

        try:
            memory_uuid = self.test_memory_ids[1]  # Use second test memory

            # Expire the memory
            action = GovernanceAction(
                action_type="expire",
                memory_id=UUID(memory_uuid),
                reason="Test expire action",
                performed_by="test_validator",
            )

            result = await self.inspection_service.execute_governance_action(action)

            passed = result.success
            self.record_result(
                "Expire Memory Action",
                passed,
                f"Expire action {'succeeded' if passed else 'failed'}: {result.error or result.message}"
            )

        except Exception as e:
            self.record_result("Expire Memory Action", False, str(e))

    async def test_no_regression_query_service(self):
        """Test that query service still works (Milestone 3 regression check)."""
        if not self.query_service:
            self.record_result("No Regression - Query Service", False, "Query service not available")
            return

        try:
            query = MemoryQuery(limit=1)
            result = await self.query_service.query(query)
            passed = result is not None
            self.record_result(
                "No Regression - Query Service",
                passed,
                "Query service (Milestone 3) still functional"
            )
        except Exception as e:
            self.record_result("No Regression - Query Service", False, str(e))

    async def test_no_regression_write_pipeline(self):
        """Test that write pipeline still works (Milestone 2 regression check)."""
        from torq_console.memory.memory_persistence import MemoryPersistenceService

        try:
            persistence = MemoryPersistenceService(supabase_client=self.supabase)
            passed = persistence is not None
            self.record_result(
                "No Regression - Write Pipeline",
                passed,
                "Write pipeline (Milestone 2) still functional"
            )
        except Exception as e:
            self.record_result("No Regression - Write Pipeline", False, str(e))

    async def test_no_regression_eligibility_rules(self):
        """Test that eligibility rules still work (Milestone 1 regression check)."""
        from torq_console.memory.eligibility_rules import get_eligibility_engine

        try:
            engine = get_eligibility_engine()
            passed = engine is not None
            self.record_result(
                "No Regression - Eligibility Rules",
                passed,
                "Eligibility rules (Milestone 1) still functional"
            )
        except Exception as e:
            self.record_result("No Regression - Eligibility Rules", False, str(e))

    # ========================================================================
    # Run All Tests
    # ========================================================================

    async def run_all_tests(self):
        """Run all validation tests."""
        logger.info("=" * 70)
        logger.info("Phase 4H.1 Milestone 4: Audit, Inspection, and Control Layer")
        logger.info("=" * 70)

        # Setup
        await self.setup_test_data()

        # Tests
        await self.test_inspection_service_exists()
        await self.test_get_memory_detail()
        await self.test_get_traceability()
        await self.test_get_validation_decisions()
        await self.test_get_rejection_logs()
        await self.test_get_retrieval_audit()
        await self.test_get_retrieval_summary()
        await self.test_get_governance_statistics()
        await self.test_disable_memory_action()
        await self.test_expire_memory_action()
        await self.test_no_regression_query_service()
        await self.test_no_regression_write_pipeline()
        await self.test_no_regression_eligibility_rules()

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
            icon = "[OK]" if test["status"] == "PASS" else "[FAIL]"
            logger.info(f"{icon} {test['name']}: {test['message']}")

        logger.info("")
        logger.info(f"Total: {self.results['passed'] + self.results['failed']} tests")
        logger.info(f"Passed: {self.results['passed']}")
        logger.info(f"Failed: {self.results['failed']}")
        logger.info(f"Skipped: {self.results['skipped']}")

        if self.results["failed"] == 0:
            logger.info("")
            logger.info("ALL TESTS PASSED - Milestone 4 Complete!")
        else:
            logger.warning(f"{self.results['failed']} test(s) failed")

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

    validator = Milestone4Validator(supabase_client=supabase_client)
    await validator.run_all_tests()

    return validator.results["failed"] == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
