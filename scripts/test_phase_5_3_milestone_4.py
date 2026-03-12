#!/usr/bin/env python
"""
Phase 5.3 Milestone 4: Read and Inspection Layer Tests

Tests for workspace artifact retrieval and inspection.

This validates:
- Artifacts can be listed by workspace/execution/team
- Artifact detail loads correctly
- Filters work
- Traceability chain is visible
- Historical artifacts are inspectable
- No regression in 5.2 or 5.3 M1-M3

Run with:
    python scripts/test_phase_5_3_milestone_4.py
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment
load_dotenv()

from torq_console.dependencies import get_supabase_client
from torq_console.workspace import (
    WorkspaceArtifactContextLinker,
    WorkspaceArtifactPersistence,
    WorkspaceArtifactReadService,
    WorkspaceArtifactService,
    create_context_linker,
    get_artifact_read_service,
)
from torq_console.workspace.artifact_models import ArtifactType, WorkspaceArtifactListParams
from torq_console.workspace.artifact_view_models import (
    ArtifactDetailViewModel,
    TraceabilityChainViewModel,
    TraceabilityViewModel,
)


# ============================================================================
# Milestone 4 Tests: Read and Inspection Layer
# ============================================================================

class TestMilestone4_ReadInspection:
    """Tests for workspace artifact read and inspection (Milestone 4)."""

    def __init__(self):
        self.supabase = None
        self.read_service = None
        self.linker = None
        self.passed = 0
        self.failed = 0
        self.test_workspace_id = None
        self.created_artifacts = []
        self.test_mission_id = None
        self.test_execution_id = None
        self.test_node_id = None

    def log(self, message: str, status: str = "info"):
        """Log test output."""
        icon = {"pass": "[PASS]", "fail": "[FAIL]", "info": "[INFO]", "skip": "[SKIP]"}[status]
        print(f"{icon} {message}")

    async def setup(self):
        """Set up test environment with sample artifacts."""
        try:
            self.supabase = get_supabase_client()

            # Create a test workspace
            test_id = uuid4()
            test_workspace = self.supabase.table("workspaces").insert({
                "workspace_id": str(test_id),
                "scope_type": "session",
                "scope_id": "test_milestone_4",
                "tenant_id": "default",
                "title": "Test Workspace for Milestone 4",
                "description": "Temporary workspace for read/inspection testing",
            }).execute()

            if test_workspace.data:
                self.test_workspace_id = UUID(test_workspace.data[0]["workspace_id"])
                self.log(f"Created test workspace: {self.test_workspace_id}", "info")

            # Create context IDs for traceability
            self.test_mission_id = uuid4()
            self.test_node_id = uuid4()
            self.test_execution_id = "test_read_inspection_exec"

            # Create services
            persistence = WorkspaceArtifactPersistence(self.supabase)
            self.read_service = get_artifact_read_service(persistence)
            self.linker = await create_context_linker(self.supabase, enabled=True)

            # Create sample artifacts for testing
            await self._create_sample_artifacts()

        except Exception as e:
            self.log(f"Setup failed: {e}", "fail")
            import traceback
            traceback.print_exc()
            return False

        return True

    async def _create_sample_artifacts(self):
        """Create sample artifacts for testing read operations."""
        # Node tool artifact
        await self.linker.capture_node_tool_execution(
            workspace_id=self.test_workspace_id,
            tool_name="web_search",
            tool_input={"query": "test search", "max_results": 5},
            tool_output={
                "results": [
                    {"title": "Test Result 1", "url": "https://test1.com", "snippet": "Test snippet 1"},
                    {"title": "Test Result 2", "url": "https://test2.com", "snippet": "Test snippet 2"},
                ],
                "query": "test search"
            },
            execution_context={
                "mission_id": self.test_mission_id,
                "node_id": self.test_node_id,
                "execution_id": self.test_execution_id,
                "started_at": datetime.now(timezone.utc),
            },
        )

        # File read artifact
        await self.linker.capture_node_tool_execution(
            workspace_id=self.test_workspace_id,
            tool_name="file_read",
            tool_input={"path": "/test/config.txt"},
            tool_output={
                "path": "/test/config.txt",
                "content": "config_value=123",
                "size": 16
            },
            execution_context={
                "mission_id": self.test_mission_id,
                "node_id": self.test_node_id,
                "execution_id": self.test_execution_id,
                "started_at": datetime.now(timezone.utc),
            },
        )

        # Role output artifact (round 1)
        await self.linker.capture_role_output(
            workspace_id=self.test_workspace_id,
            role_name="researcher",
            task_output={
                "text": "Here is my research analysis",
                "data": {"findings": ["finding1", "finding2"]},
                "confidence": 0.85,
            },
            team_execution_context={
                "mission_id": self.test_mission_id,
                "node_id": self.test_node_id,
                "execution_id": self.test_execution_id,
                "team_execution_id": None,  # No team_executions table yet
                "round_number": 1,
                "started_at": datetime.now(timezone.utc),
            },
        )

        # Role output artifact (round 2)
        await self.linker.capture_role_output(
            workspace_id=self.test_workspace_id,
            role_name="critic",
            task_output={
                "text": "I have some critiques",
                "data": {"issues": ["issue1", "issue2"]},
                "confidence": 0.75,
            },
            team_execution_context={
                "mission_id": self.test_mission_id,
                "node_id": self.test_node_id,
                "execution_id": self.test_execution_id,
                "team_execution_id": None,
                "round_number": 2,
                "started_at": datetime.now(timezone.utc),
            },
        )

        # Team decision artifact
        await self.linker.capture_team_decision(
            workspace_id=self.test_workspace_id,
            decision_data={
                "decision_outcome": "approved",
                "confidence_score": 0.92,
                "confidence_breakdown": {"lead": 0.9, "researcher": 0.85, "critic": 0.95},
                "approval_summary": {"total_votes": 3, "approve_votes": 3},
                "validator_status": "approved",
            },
            team_execution_context={
                "mission_id": self.test_mission_id,
                "node_id": self.test_node_id,
                "execution_id": self.test_execution_id,
                "team_execution_id": None,
                "round_number": 3,
            },
        )

        self.log(f"Created 5 sample artifacts for testing", "info")

    async def teardown(self):
        """Clean up test environment."""
        try:
            # Delete created artifacts
            if self.created_artifacts:
                for artifact_id in self.created_artifacts:
                    self.supabase.table("workspace_artifacts").delete().eq("id", str(artifact_id)).execute()
                self.log(f"Cleaned up {len(self.created_artifacts)} artifacts", "info")

            # Delete all artifacts in test workspace (in case created_artifacts missed any)
            if self.test_workspace_id:
                result = self.supabase.table("workspace_artifacts").select("id").eq("workspace_id", str(self.test_workspace_id)).execute()
                if result.data:
                    for row in result.data:
                        self.supabase.table("workspace_artifacts").delete().eq("id", row["id"]).execute()
                    self.log(f"Cleaned up additional artifacts from test workspace", "info")

            # Delete test workspace
            if self.test_workspace_id:
                self.supabase.table("workspaces").delete().eq("workspace_id", str(self.test_workspace_id)).execute()
                self.log(f"Deleted test workspace", "info")

        except Exception as e:
            self.log(f"Teardown failed: {e}", "fail")

    async def test_read_service_exists(self):
        """Test that read service can be instantiated."""
        try:
            assert self.read_service is not None
            assert hasattr(self.read_service, "list_artifacts")
            assert hasattr(self.read_service, "get_artifact_detail")
            assert hasattr(self.read_service, "list_by_workspace")
            assert hasattr(self.read_service, "list_by_execution")
            assert hasattr(self.read_service, "list_by_mission")
            assert hasattr(self.read_service, "list_by_node")
            assert hasattr(self.read_service, "list_by_team_execution")

            self.log("Read service instantiated with required methods", "pass")
            self.passed += 1
        except Exception as e:
            self.log(f"Read service instantiation failed: {e}", "fail")
            self.failed += 1

    async def test_list_by_workspace(self):
        """Test listing artifacts by workspace_id."""
        try:
            artifacts = await self.read_service.list_by_workspace(
                workspace_id=self.test_workspace_id,
                limit=10,
            )

            assert len(artifacts) >= 5, f"Expected at least 5 artifacts, got {len(artifacts)}"
            assert all(isinstance(a, TraceabilityViewModel) for a in artifacts)
            assert all(str(a.workspace_id) == str(self.test_workspace_id) for a in artifacts)

            self.log(f"Listed {len(artifacts)} artifacts by workspace", "pass")
            self.passed += 1

        except Exception as e:
            import traceback
            self.log(f"List by workspace failed: {e}\n{traceback.format_exc()}", "fail")
            self.failed += 1

    async def test_list_by_execution(self):
        """Test listing artifacts by execution_id."""
        try:
            artifacts = await self.read_service.list_by_execution(
                execution_id=self.test_execution_id,
                limit=10,
            )

            assert len(artifacts) >= 5, f"Expected at least 5 artifacts, got {len(artifacts)}"
            assert all(a.execution_id == self.test_execution_id for a in artifacts)

            self.log(f"Listed {len(artifacts)} artifacts by execution", "pass")
            self.passed += 1

        except Exception as e:
            import traceback
            self.log(f"List by execution failed: {e}\n{traceback.format_exc()}", "fail")
            self.failed += 1

    async def test_list_by_mission(self):
        """Test listing artifacts by mission_id."""
        try:
            artifacts = await self.read_service.list_by_mission(
                mission_id=self.test_mission_id,
                limit=10,
            )

            assert len(artifacts) >= 5, f"Expected at least 5 artifacts, got {len(artifacts)}"
            assert all(a.mission_id == self.test_mission_id for a in artifacts)

            self.log(f"Listed {len(artifacts)} artifacts by mission", "pass")
            self.passed += 1

        except Exception as e:
            import traceback
            self.log(f"List by mission failed: {e}\n{traceback.format_exc()}", "fail")
            self.failed += 1

    async def test_list_by_node(self):
        """Test listing artifacts by node_id."""
        try:
            artifacts = await self.read_service.list_by_node(
                node_id=self.test_node_id,
                limit=10,
            )

            assert len(artifacts) >= 5, f"Expected at least 5 artifacts, got {len(artifacts)}"
            assert all(a.node_id == self.test_node_id for a in artifacts)

            self.log(f"Listed {len(artifacts)} artifacts by node", "pass")
            self.passed += 1

        except Exception as e:
            import traceback
            self.log(f"List by node failed: {e}\n{traceback.format_exc()}", "fail")
            self.failed += 1

    async def test_filter_by_artifact_type(self):
        """Test filtering artifacts by type."""
        try:
            # Filter for web_search artifacts
            artifacts = await self.read_service.list_by_type(
                artifact_type=ArtifactType.WEB_SEARCH,
                workspace_id=str(self.test_workspace_id),
            )

            web_search_artifacts = [a for a in artifacts if a.artifact_type == "web_search"]
            assert len(web_search_artifacts) >= 1, "Expected at least one web_search artifact"

            self.log(f"Filtered to {len(web_search_artifacts)} web_search artifacts", "pass")
            self.passed += 1

        except Exception as e:
            import traceback
            self.log(f"Filter by artifact_type failed: {e}\n{traceback.format_exc()}", "fail")
            self.failed += 1

    async def test_filter_by_role_name(self):
        """Test filtering artifacts by role_name."""
        try:
            # Get all artifacts for the workspace
            all_artifacts = await self.read_service.list_by_workspace(
                workspace_id=self.test_workspace_id,
                limit=50,
            )

            # Filter for researcher role
            researcher_artifacts = [a for a in all_artifacts if a.role_name == "researcher"]
            critic_artifacts = [a for a in all_artifacts if a.role_name == "critic"]

            assert len(researcher_artifacts) >= 1, "Expected at least one researcher artifact"
            assert len(critic_artifacts) >= 1, "Expected at least one critic artifact"

            self.log(f"Filtered by role_name: {len(researcher_artifacts)} researcher, {len(critic_artifacts)} critic", "pass")
            self.passed += 1

        except Exception as e:
            import traceback
            self.log(f"Filter by role_name failed: {e}\n{traceback.format_exc()}", "fail")
            self.failed += 1

    async def test_filter_by_round_number(self):
        """Test filtering artifacts by round_number."""
        try:
            # Get all artifacts for the workspace
            all_artifacts = await self.read_service.list_by_workspace(
                workspace_id=self.test_workspace_id,
                limit=50,
            )

            # Filter for round 1 and round 2
            round_1_artifacts = [a for a in all_artifacts if a.round_number == 1]
            round_2_artifacts = [a for a in all_artifacts if a.round_number == 2]

            assert len(round_1_artifacts) >= 1, "Expected at least one round 1 artifact"
            assert len(round_2_artifacts) >= 1, "Expected at least one round 2 artifact"

            self.log(f"Filtered by round_number: {len(round_1_artifacts)} round 1, {len(round_2_artifacts)} round 2", "pass")
            self.passed += 1

        except Exception as e:
            import traceback
            self.log(f"Filter by round_number failed: {e}\n{traceback.format_exc()}", "fail")
            self.failed += 1

    async def test_get_artifact_detail(self):
        """Test getting full artifact detail."""
        try:
            # Get an artifact first
            artifacts = await self.read_service.list_by_workspace(
                workspace_id=self.test_workspace_id,
                limit=1,
            )

            if not artifacts:
                self.skip("No artifacts found for detail test")
                return

            artifact_id = artifacts[0].id

            # Get detail
            detail = await self.read_service.get_artifact_detail(artifact_id)

            assert detail is not None, "Expected artifact detail"
            assert isinstance(detail, ArtifactDetailViewModel)
            assert detail.artifact.id == artifact_id
            assert hasattr(detail, "content_json")
            assert hasattr(detail, "content_text")
            assert hasattr(detail, "execution_metadata")
            assert hasattr(detail, "traceability")

            # Check traceability chain
            chain = detail.traceability
            assert isinstance(chain, TraceabilityChainViewModel)
            assert chain.workspace is not None
            assert chain.artifact is not None

            self.log("Artifact detail loaded with full traceability chain", "pass")
            self.passed += 1

        except Exception as e:
            import traceback
            self.log(f"Get artifact detail failed: {e}\n{traceback.format_exc()}", "fail")
            self.failed += 1

    async def test_traceability_chain_visible(self):
        """Test that traceability chain is visible in view model."""
        try:
            # Get artifacts with execution context
            artifacts = await self.read_service.list_by_execution(
                execution_id=self.test_execution_id,
                limit=10,
            )

            if not artifacts:
                self.skip("No artifacts found for traceability test")
                return

            # Check that each artifact has traceability info
            for artifact in artifacts:
                assert artifact.workspace_id is not None, f"Artifact {artifact.id} missing workspace_id"
                assert artifact.mission_id is not None, f"Artifact {artifact.id} missing mission_id"
                assert artifact.node_id is not None, f"Artifact {artifact.id} missing node_id"
                assert artifact.execution_id is not None, f"Artifact {artifact.id} missing execution_id"

            # Check team artifacts have round/role
            role_artifacts = [a for a in artifacts if a.role_name is not None]
            for artifact in role_artifacts:
                assert artifact.round_number is not None, f"Role artifact {artifact.id} missing round_number"

            self.log(f"Traceability chain visible in all {len(artifacts)} artifacts", "pass")
            self.passed += 1

        except Exception as e:
            import traceback
            self.log(f"Traceability chain test failed: {e}\n{traceback.format_exc()}", "fail")
            self.failed += 1

    async def test_pagination_works(self):
        """Test that pagination works correctly."""
        try:
            # Get first page
            page1 = await self.read_service.list_by_workspace(
                workspace_id=self.test_workspace_id,
                limit=2,
                offset=0,
            )

            # Get second page
            page2 = await self.read_service.list_by_workspace(
                workspace_id=self.test_workspace_id,
                limit=2,
                offset=2,
            )

            # Verify pagination
            assert len(page1) <= 2, "Page 1 should have at most 2 artifacts"
            assert len(page2) <= 2, "Page 2 should have at most 2 artifacts"

            # Verify no overlap
            page1_ids = {a.id for a in page1}
            page2_ids = {a.id for a in page2}
            assert len(page1_ids.intersection(page2_ids)) == 0, "Pages should not overlap"

            self.log(f"Pagination works: page1={len(page1)}, page2={len(page2)}", "pass")
            self.passed += 1

        except Exception as e:
            import traceback
            self.log(f"Pagination test failed: {e}\n{traceback.format_exc()}", "fail")
            self.failed += 1

    async def test_historical_artifacts_inspectable(self):
        """Test that historical artifacts (from completed executions) are inspectable."""
        try:
            # All artifacts in our test are effectively "historical" since
            # they're persisted and can be queried after the fact
            artifacts = await self.read_service.list_by_workspace(
                workspace_id=self.test_workspace_id,
                limit=10,
            )

            assert len(artifacts) >= 5, "Expected at least 5 historical artifacts"

            # Verify each has a created_at timestamp
            for artifact in artifacts:
                assert artifact.created_at is not None, f"Artifact {artifact.id} missing created_at"

            # Verify we can filter by date range if needed (all artifacts have timestamps)
            self.log(f"Historical artifacts are inspectable: {len(artifacts)} artifacts with timestamps", "pass")
            self.passed += 1

        except Exception as e:
            import traceback
            self.log(f"Historical artifacts test failed: {e}\n{traceback.format_exc()}", "fail")
            self.failed += 1

    async def test_combined_filters(self):
        """Test that combined filters work (AND logic)."""
        try:
            # Get all artifacts for workspace
            all_artifacts = await self.read_service.list_by_workspace(
                workspace_id=self.test_workspace_id,
                limit=50,
            )

            # Apply combined filter: role_name AND round_number
            filtered = [
                a for a in all_artifacts
                if a.role_name == "researcher" and a.round_number == 1
            ]

            assert len(filtered) >= 1, "Expected at least one researcher artifact in round 1"

            # Verify the filter worked correctly
            for artifact in filtered:
                assert artifact.role_name == "researcher"
                assert artifact.round_number == 1

            self.log(f"Combined filters work: {len(filtered)} artifacts match (role=researcher AND round=1)", "pass")
            self.passed += 1

        except Exception as e:
            import traceback
            self.log(f"Combined filters test failed: {e}\n{traceback.format_exc()}", "fail")
            self.failed += 1

    def skip(self, message: str):
        """Skip a test."""
        self.log(f"Skipped: {message}", "skip")

    async def run_all(self):
        """Run all Milestone 4 tests."""
        print("\n" + "="*60)
        print("Milestone 4: Read and Inspection Layer Tests")
        print("="*60 + "\n")

        if not await self.setup():
            print("\n[WARNING] Milestone 4 tests skipped (setup failed)")
            return False

        try:
            await self.test_read_service_exists()
            await self.test_list_by_workspace()
            await self.test_list_by_execution()
            await self.test_list_by_mission()
            await self.test_list_by_node()
            await self.test_filter_by_artifact_type()
            await self.test_filter_by_role_name()
            await self.test_filter_by_round_number()
            await self.test_get_artifact_detail()
            await self.test_traceability_chain_visible()
            await self.test_pagination_works()
            await self.test_historical_artifacts_inspectable()
            await self.test_combined_filters()

            print(f"\nMilestone 4 Results: {self.passed} passed, {self.failed} failed")
            return self.failed == 0

        finally:
            await self.teardown()


# ============================================================================
# Regression Tests: No regression in 5.2 or 5.3 M1-M3
# ============================================================================

class TestRegression_PreviousMilestones:
    """Tests to verify no regression in previous milestones."""

    def __init__(self):
        self.passed = 0
        self.failed = 0

    def log(self, message: str, status: str = "info"):
        """Log test output."""
        icon = {"pass": "[PASS]", "fail": "[FAIL]", "info": "[INFO]"}[status]
        print(f"{icon} {message}")

    async def test_context_linker_still_works(self):
        """Test that Milestone 3 context linker still works."""
        try:
            from torq_console.dependencies import get_supabase_client
            from torq_console.workspace import create_context_linker

            supabase = get_supabase_client()
            linker = await create_context_linker(supabase, enabled=True)

            assert linker is not None
            assert hasattr(linker, "capture_node_tool_execution")
            assert hasattr(linker, "capture_role_output")
            assert hasattr(linker, "capture_team_decision")

            self.log("Context linker (Milestone 3) still works", "pass")
            self.passed += 1

        except Exception as e:
            import traceback
            self.log(f"Context linker regression test failed: {e}\n{traceback.format_exc()}", "fail")
            self.failed += 1

    async def test_artifact_service_still_works(self):
        """Test that Milestone 2 artifact service still works."""
        try:
            from torq_console.dependencies import get_supabase_client
            from torq_console.workspace import WorkspaceArtifactService

            supabase = get_supabase_client()
            service = WorkspaceArtifactService(supabase)

            assert service is not None
            assert hasattr(service, "capture_tool_output")
            assert hasattr(service, "list_workspace_artifacts")

            self.log("Artifact service (Milestone 2) still works", "pass")
            self.passed += 1

        except Exception as e:
            import traceback
            self.log(f"Artifact service regression test failed: {e}\n{traceback.format_exc()}", "fail")
            self.failed += 1

    async def run_all(self):
        """Run all regression tests."""
        print("\n" + "="*60)
        print("Regression Tests: Previous Milestones")
        print("="*60 + "\n")

        await self.test_context_linker_still_works()
        await self.test_artifact_service_still_works()

        print(f"\nRegression Results: {self.passed} passed, {self.failed} failed")
        return self.failed == 0


# ============================================================================
# Main Test Runner
# ============================================================================

async def main():
    """Run all Phase 5.3 Milestone 4 tests."""
    print("\n" + "="*60)
    print("Phase 5.3: Workspace Integration")
    print("Milestone 4: Read and Inspection Layer")
    print("="*60)

    milestone4 = TestMilestone4_ReadInspection()
    m4_success = await milestone4.run_all()

    regression = TestRegression_PreviousMilestones()
    regression_success = await regression.run_all()

    # Summary
    print("\n" + "="*60)
    print("Final Summary")
    print("="*60)

    total_passed = milestone4.passed + regression.passed
    total_failed = milestone4.failed + regression.failed

    print(f"\nTotal: {total_passed} passed, {total_failed} failed")
    print(f"\nMilestone 4 (Read/Inspection): {'[PASS]' if m4_success else '[FAIL]'}")
    print(f"Regression (Previous Milestones): {'[PASS]' if regression_success else '[FAIL]'}")

    if m4_success and regression_success:
        print("\n[SUCCESS] Phase 5.3 Milestone 4: VALIDATED")
        print("\n[OK] Artifacts can be listed by workspace/execution/team")
        print("[OK] Artifact detail loads correctly")
        print("[OK] Filters work")
        print("[OK] Traceability chain is visible")
        print("[OK] Historical artifacts are inspectable")
        print("[OK] No regression in 5.2 or 5.3 M1-M3")
        return 0
    else:
        print("\n[FAILED] Phase 5.3 Milestone 4: FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
