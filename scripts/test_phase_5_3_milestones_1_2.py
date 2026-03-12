#!/usr/bin/env python
"""
Phase 5.3 Milestones 1 & 2 Validation Tests

Tests for workspace artifact contract and persistence.

This validates:
- Milestone 1: Tool output normalization into artifact contract
- Milestone 2: Workspace artifact persistence

Run with:
    python scripts/test_phase_5_3_milestones_1_2.py
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

# Import TORQ modules
from torq_console.workspace import (
    ToolOutputAdapter,
    get_tool_output_adapter,
    adapt_tool_output,
    ArtifactType,
    ToolExecutionMetadata,
    NormalizedArtifact,
    WorkspaceArtifactCreate,
)
from torq_console.dependencies import get_supabase_client


# ============================================================================
# Milestone 1 Tests: Tool Output Contract
# ============================================================================

class TestMilestone1_ToolOutputContract:
    """Tests for normalized artifact contract (Milestone 1)."""

    def __init__(self):
        self.adapter = get_tool_output_adapter()
        self.passed = 0
        self.failed = 0

    def log(self, message: str, status: str = "info"):
        """Log test output."""
        icon = {"pass": "[PASS]", "fail": "[FAIL]", "info": "[INFO]", "skip": "[SKIP]"}[status]
        print(f"{icon} {message}")

    def test_adapter_exists(self):
        """Test that adapter can be instantiated."""
        try:
            assert self.adapter is not None
            assert hasattr(self.adapter, "adapt_tool_output")
            assert hasattr(self.adapter, "adapt_claude_tool_use")
            self.log("ToolOutputAdapter instantiated with required methods", "pass")
            self.passed += 1
        except AssertionError as e:
            self.log(f"Adapter instantiation failed: {e}", "fail")
            self.failed += 1

    def test_web_search_normalization(self):
        """Test web search output normalization."""
        try:
            tool_output = {
                "results": [
                    {"title": "Test Result", "url": "https://example.com", "snippet": "A test result"}
                ],
                "query": "test query"
            }

            artifact = self.adapter.adapt_tool_output(
                tool_name="web_search",
                tool_output=tool_output,
            )

            assert isinstance(artifact, NormalizedArtifact)
            assert artifact.artifact_type == ArtifactType.WEB_SEARCH
            assert artifact.title == "Web Search: test query"
            assert "test query" in artifact.summary
            assert artifact.content_json == tool_output
            assert artifact.execution_metadata.tool_name == "web_search"

            self.log("Web search output normalizes correctly", "pass")
            self.passed += 1
        except Exception as e:
            self.log(f"Web search normalization failed: {e}", "fail")
            self.failed += 1

    def test_file_read_normalization(self):
        """Test file read output normalization."""
        try:
            tool_output = {
                "path": "/path/to/file.txt",
                "content": "file content here",
                "size": 16
            }

            artifact = self.adapter.adapt_tool_output(
                tool_name="file_read",
                tool_output=tool_output,
            )

            assert artifact.artifact_type == ArtifactType.FILE_READ
            assert "file.txt" in artifact.title
            assert "16 bytes" in artifact.summary
            assert artifact.source_ref == "/path/to/file.txt"

            self.log("File read output normalizes correctly", "pass")
            self.passed += 1
        except Exception as e:
            self.log(f"File read normalization failed: {e}", "fail")
            self.failed += 1

    def test_claude_tool_use_normalization(self):
        """Test Claude Tool Use API format normalization."""
        try:
            artifact = self.adapter.adapt_claude_tool_use(
                tool_name="web_search",
                tool_input={"query": "test search", "max_results": 10},
                tool_result="Web search results for 'test search':\n\n1. Test Result\n   https://test.com",
            )

            assert artifact.artifact_type == ArtifactType.WEB_SEARCH
            assert artifact.title == "Web Search: test search"
            assert artifact.content_text != ""
            assert artifact.execution_metadata.tool_name == "web_search"

            self.log("Claude Tool Use format normalizes correctly", "pass")
            self.passed += 1
        except Exception as e:
            self.log(f"Claude Tool Use normalization failed: {e}", "fail")
            self.failed += 1

    def test_role_task_normalization(self):
        """Test role task output normalization."""
        try:
            execution_context = {
                "mission_id": uuid4(),
                "node_id": uuid4(),
                "team_execution_id": uuid4(),
                "round_number": 2,
            }

            artifact = self.adapter.adapt_role_task_output(
                role_name="researcher",
                task_output={
                    "text": "Here is my research output",
                    "data": {"findings": ["finding1", "finding2"]}
                },
                execution_context=execution_context,
            )

            assert artifact.artifact_type == ArtifactType.ROLE_OUTPUT
            assert "researcher" in artifact.title.lower()
            assert execution_context["round_number"] == artifact.execution_metadata.round_number
            assert artifact.execution_metadata.role_name == "researcher"

            self.log("Role task output normalizes correctly", "pass")
            self.passed += 1
        except Exception as e:
            self.log(f"Role task normalization failed: {e}", "fail")
            self.failed += 1

    def test_unknown_tool_fallback(self):
        """Test unknown tool falls back to generic artifact."""
        try:
            artifact = self.adapter.adapt_tool_output(
                tool_name="unknown_custom_tool",
                tool_output={"data": "custom output"},
            )

            assert artifact.artifact_type == ArtifactType.GENERIC_ARTIFACT
            # Title is "Unknown Custom Tool Result" - check for "unknown" and "tool"
            assert "unknown" in artifact.title.lower()
            assert "tool" in artifact.title.lower()

            self.log("Unknown tools fall back to generic artifact type", "pass")
            self.passed += 1
        except Exception as e:
            self.log(f"Unknown tool fallback failed: {e}", "fail")
            self.failed += 1

    def run_all(self):
        """Run all Milestone 1 tests."""
        print("\n" + "="*60)
        print("Milestone 1: Tool Output Contract Tests")
        print("="*60 + "\n")

        self.test_adapter_exists()
        self.test_web_search_normalization()
        self.test_file_read_normalization()
        self.test_claude_tool_use_normalization()
        self.test_role_task_normalization()
        self.test_unknown_tool_fallback()

        print(f"\nMilestone 1 Results: {self.passed} passed, {self.failed} failed")
        return self.failed == 0


# ============================================================================
# Milestone 2 Tests: Workspace Artifact Persistence
# ============================================================================

class TestMilestone2_ArtifactPersistence:
    """Tests for workspace artifact persistence (Milestone 2)."""

    def __init__(self):
        self.supabase = None
        self.passed = 0
        self.failed = 0
        self.test_workspace_id = None
        self.created_artifacts = []

    def log(self, message: str, status: str = "info"):
        """Log test output."""
        icon = {"pass": "[PASS]", "fail": "[FAIL]", "info": "[INFO]", "skip": "[SKIP]"}[status]
        print(f"{icon} {message}")

    async def setup(self):
        """Set up test environment."""
        try:
            self.supabase = get_supabase_client()

            # Use an existing workspace instead of creating a new one
            # Get any existing workspace or create with proper UUID format
            existing = self.supabase.table("workspaces").select("*").limit(1).execute()

            if existing.data:
                # Convert string UUID to UUID object
                from uuid import UUID as UUIDType
                workspace_id_str = existing.data[0]["workspace_id"]
                self.test_workspace_id = UUIDType(workspace_id_str) if isinstance(workspace_id_str, str) else workspace_id_str
                self.log(f"Using existing workspace: {self.test_workspace_id}", "info")
            else:
                # Generate a proper UUID for workspace_id
                import uuid
                test_id = str(uuid.uuid4())
                test_workspace = self.supabase.table("workspaces").insert({
                    "workspace_id": test_id,
                    "scope_type": "session",
                    "scope_id": "test_phase_5_3",
                    "tenant_id": "default",
                    "title": "Test Workspace for Phase 5.3",
                    "description": "Temporary workspace for artifact testing",
                }).execute()

                if test_workspace.data:
                    from uuid import UUID as UUIDType
                    workspace_id_str = test_workspace.data[0]["workspace_id"]
                    self.test_workspace_id = UUIDType(workspace_id_str) if isinstance(workspace_id_str, str) else workspace_id_str
                    self.log(f"Created test workspace: {self.test_workspace_id}", "info")

        except Exception as e:
            self.log(f"Setup failed: {e}", "fail")
            return False

        return True

    async def teardown(self):
        """Clean up test environment."""
        try:
            # Delete created artifacts
            if self.created_artifacts:
                for artifact_id in self.created_artifacts:
                    self.supabase.table("workspace_artifacts").delete().eq("id", str(artifact_id)).execute()
                self.log(f"Cleaned up {len(self.created_artifacts)} artifacts", "info")

            # Delete test workspace
            if self.test_workspace_id:
                self.supabase.table("workspaces").delete().eq("workspace_id", self.test_workspace_id).execute()
                self.log(f"Deleted test workspace", "info")

        except Exception as e:
            self.log(f"Teardown failed: {e}", "fail")

    async def test_table_exists(self):
        """Test that workspace_artifacts table exists."""
        try:
            result = self.supabase.table("workspace_artifacts").select("*").limit(1).execute()
            self.log("workspace_artifacts table exists and is queryable", "pass")
            self.passed += 1
        except Exception as e:
            self.log(f"Table check failed: {e}", "fail")
            self.failed += 1

    async def test_create_artifact(self):
        """Test creating an artifact."""
        try:
            from torq_console.workspace import WorkspaceArtifactService, capture_tool_output

            service = WorkspaceArtifactService(self.supabase)

            artifact = await service.capture_tool_output(
                workspace_id=self.test_workspace_id,
                tool_name="web_search",
                tool_output={
                    "results": [{"title": "Test", "url": "https://test.com"}],
                    "query": "test query"
                },
            )

            assert artifact.id is not None
            # Compare workspace_id as UUID (convert both to string for comparison)
            assert str(artifact.workspace_id) == str(self.test_workspace_id)
            assert artifact.tool_name == "web_search"
            assert artifact.artifact_type == ArtifactType.WEB_SEARCH

            self.created_artifacts.append(artifact.id)

            self.log("Artifact created successfully with all fields", "pass")
            self.passed += 1
        except Exception as e:
            self.log(f"Artifact creation failed: {e}", "fail")
            self.failed += 1

    async def test_list_workspace_artifacts(self):
        """Test listing artifacts for a workspace."""
        try:
            from torq_console.workspace import WorkspaceArtifactService

            service = WorkspaceArtifactService(self.supabase)

            artifacts = await service.list_workspace_artifacts(
                workspace_id=self.test_workspace_id,
                limit=10,
            )

            assert len(artifacts) > 0
            # Compare workspace_id as string (UUID objects may differ)
            assert all(str(a.workspace_id) == str(self.test_workspace_id) for a in artifacts)

            self.log(f"Listed {len(artifacts)} artifacts for workspace", "pass")
            self.passed += 1
        except Exception as e:
            self.log(f"Artifact listing failed: {e}", "fail")
            self.failed += 1

    async def test_filter_by_artifact_type(self):
        """Test filtering artifacts by type."""
        try:
            from torq_console.workspace import WorkspaceArtifactService

            service = WorkspaceArtifactService(self.supabase)

            # Create another artifact of different type
            await service.capture_tool_output(
                workspace_id=self.test_workspace_id,
                tool_name="file_read",
                tool_output={"path": "/test/file.txt", "content": "test content"},
            )

            # Filter by web_search type
            web_search_artifacts = await service.list_workspace_artifacts(
                workspace_id=self.test_workspace_id,
                artifact_type=ArtifactType.WEB_SEARCH,
            )

            assert all(a.artifact_type == ArtifactType.WEB_SEARCH for a in web_search_artifacts)

            self.log(f"Filtered to {len(web_search_artifacts)} web_search artifacts", "pass")
            self.passed += 1
        except Exception as e:
            self.log(f"Artifact type filtering failed: {e}", "fail")
            self.failed += 1

    async def test_count_artifacts(self):
        """Test counting artifacts."""
        try:
            from torq_console.workspace import WorkspaceArtifactService

            service = WorkspaceArtifactService(self.supabase)

            count = await service.count_artifacts(
                workspace_id=self.test_workspace_id,
            )

            assert count >= 1

            self.log(f"Counted {count} artifacts in workspace", "pass")
            self.passed += 1
        except Exception as e:
            self.log(f"Artifact counting failed: {e}", "fail")
            self.failed += 1

    async def run_all(self):
        """Run all Milestone 2 tests."""
        print("\n" + "="*60)
        print("Milestone 2: Workspace Artifact Persistence Tests")
        print("="*60 + "\n")

        if not await self.setup():
            print("\n[WARNING] Milestone 2 tests skipped (setup failed)")
            return False

        try:
            await self.test_table_exists()
            await self.test_create_artifact()
            await self.test_list_workspace_artifacts()
            await self.test_filter_by_artifact_type()
            await self.test_count_artifacts()

            print(f"\nMilestone 2 Results: {self.passed} passed, {self.failed} failed")
            return self.failed == 0
        finally:
            await self.teardown()


# ============================================================================
# Main Test Runner
# ============================================================================

async def main():
    """Run all Phase 5.3 Milestones 1 & 2 tests."""
    print("\n" + "="*60)
    print("Phase 5.3: Workspace Integration")
    print("Milestones 1 & 2 Validation")
    print("="*60)

    # Milestone 1 tests (no database required)
    milestone1 = TestMilestone1_ToolOutputContract()
    m1_success = milestone1.run_all()

    # Milestone 2 tests (database required)
    milestone2 = TestMilestone2_ArtifactPersistence()
    m2_success = await milestone2.run_all()

    # Summary
    print("\n" + "="*60)
    print("Final Summary")
    print("="*60)

    total_passed = milestone1.passed + milestone2.passed
    total_failed = milestone1.failed + milestone2.failed

    print(f"\nTotal: {total_passed} passed, {total_failed} failed")
    print(f"\nMilestone 1 (Tool Output Contract): {'[PASS]' if m1_success else '[FAIL]'}")
    print(f"Milestone 2 (Artifact Persistence): {'[PASS]' if m2_success else '[FAIL]'}")

    if m1_success and m2_success:
        print("\n[SUCCESS] Phase 5.3 Milestones 1 & 2: VALIDATED")
        return 0
    else:
        print("\n[FAILED] Phase 5.3 Milestones 1 & 2: FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
