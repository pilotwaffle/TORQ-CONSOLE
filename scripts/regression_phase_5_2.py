#!/usr/bin/env python3
"""
Phase 5.2 Agent Teams - Regression Test Suite

Tests all components of the Agent Teams system including:
- Team definitions and registry
- Team execution orchestrator
- Role runner
- Decision engine
- Database persistence
"""

import os
import sys
import asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from uuid import UUID, uuid4

from torq_console.dependencies import get_supabase_client
from torq_console.teams import (
    TeamDefinition,
    TeamMemberRole,
    TeamPattern,
    DecisionPolicy,
    TeamRole,
    TeamExecutionContext,
    TeamDefinitionRegistry,
    TeamPersistence,
    DecisionEngine,
    initialize_registry,
)
from torq_console.teams.models import TeamExecution, TeamExecutionStatus


# ============================================================================
# Test Results
# ============================================================================

class TestResults:
    def __init__(self):
        self.results = {}
        self.start_time = datetime.now()

    def add(self, name: str, passed: bool, details: str = ""):
        self.results[name] = {"passed": passed, "details": details}

    def print_summary(self):
        duration = (datetime.now() - self.start_time).total_seconds()

        print("\n" + "="*60)
        print("PHASE 5.2 REGRESSION SUMMARY")
        print("="*60)

        for name, result in self.results.items():
            status = "[OK]   " if result["passed"] else "[FAIL] "
            print(f"{status}{name}")
            if result["details"]:
                print(f"       {result['details']}")

        passed = sum(1 for r in self.results.values() if r["passed"])
        total = len(self.results)

        print(f"\nTotal: {passed}/{total} tests passed")
        print(f"Duration: {duration:.1f} seconds")

        if passed == total:
            print("\n[SUCCESS] ALL TESTS PASSED")
            return 0
        else:
            print(f"\n[FAILURE] {total - passed} TESTS FAILED")
            return 1


results = TestResults()


# ============================================================================
# Test Functions
# ============================================================================

async def test_database_schema(supabase):
    """Test that all team tables exist and are accessible."""
    print("\n[TEST 1] Database Schema")

    tables = [
        "agent_teams",
        "agent_team_members",
        "team_executions",
        "team_messages",
        "team_decisions",
    ]

    for table in tables:
        try:
            result = supabase.table(table).select("*", count="exact").limit(1).execute()
            print(f"  ✓ {table}: accessible ({result.count} rows)")
        except Exception as e:
            print(f"  ✗ {table}: {e}")
            results.add("database_schema", False, f"{table}: {e}")
            return

    results.add("database_schema", True, f"All {len(tables)} tables accessible")


async def test_team_registry(supabase):
    """Test team definition registry."""
    print("\n[TEST 2] Team Registry")

    try:
        # Initialize registry
        registry = TeamDefinitionRegistry()
        await registry.initialize(supabase)

        # Check default teams
        planning_team = registry.get_by_team_id("planning_team")
        research_team = registry.get_by_team_id("research_team")
        build_team = registry.get_by_team_id("build_team")

        assert planning_team is not None, "Planning team not found"
        assert research_team is not None, "Research team not found"
        assert build_team is not None, "Build team not found"

        print(f"  ✓ Planning team: {len(planning_team.members)} members")
        print(f"  ✓ Research team: {len(research_team.members)} members")
        print(f"  ✓ Build team: {len(build_team.members)} members")

        # Test role ordering
        roles = registry.get_roles_in_order("planning_team")
        assert len(roles) == 4, f"Expected 4 roles, got {len(roles)}"
        print(f"  ✓ Role ordering: {[r.role_name.value for r in roles]}")

        results.add("team_registry", True, "All default teams loaded")

    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.add("team_registry", False, str(e))


async def test_team_persistence(supabase):
    """Test team persistence layer."""
    print("\n[TEST 3] Team Persistence")

    try:
        persistence = TeamPersistence(supabase)

        # Create test execution
        execution = TeamExecution(
            mission_id=uuid4(),
            node_id=uuid4(),
            execution_id=f"test_{uuid4().hex[:8]}",
            team_id=uuid4(),
            status=TeamExecutionStatus.CREATED,
            objective="Test objective",
            max_rounds=2,
        )

        # Create execution
        created = await persistence.create_execution(execution)
        assert created.id is not None, "Failed to create execution"
        print(f"  ✓ Created execution: {created.id}")

        # Update execution
        created.status = TeamExecutionStatus.RUNNING
        updated = await persistence.update_execution(created)
        assert updated.status == TeamExecutionStatus.RUNNING
        print(f"  ✓ Updated execution status")

        # Retrieve execution
        retrieved = await persistence.get_execution(created.id)
        assert retrieved is not None, "Failed to retrieve execution"
        assert retrieved.status == TeamExecutionStatus.RUNNING
        print(f"  ✓ Retrieved execution")

        results.add("team_persistence", True, "CRUD operations working")

    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.add("team_persistence", False, str(e))


async def test_decision_engine(supabase):
    """Test decision engine."""
    print("\n[TEST 4] Decision Engine")

    try:
        engine = DecisionEngine(supabase)

        # Create test execution and messages
        execution = TeamExecution(
            mission_id=uuid4(),
            node_id=uuid4(),
            execution_id=f"test_{uuid4().hex[:8]}",
            team_id=uuid4(),
            status=TeamExecutionStatus.RUNNING,
            max_rounds=2,
        )

        from torq_console.teams.models import TeamMessage, MessageType, TeamRole

        messages = [
            TeamMessage(
                team_execution_id=execution.id,
                round_number=1,
                sender_role=TeamRole.LEAD,
                receiver_role=TeamRole.RESEARCHER,
                message_type=MessageType.ROLE_TO_ROLE,
                content={"text": "Lead output"},
                confidence=0.85,
            ),
            TeamMessage(
                team_execution_id=execution.id,
                round_number=1,
                sender_role=TeamRole.RESEARCHER,
                receiver_role=TeamRole.CRITIC,
                message_type=MessageType.ROLE_TO_ROLE,
                content={"text": "Research output"},
                confidence=0.80,
            ),
            TeamMessage(
                team_execution_id=execution.id,
                round_number=1,
                sender_role=TeamRole.VALIDATOR,
                receiver_role=TeamRole.LEAD,
                message_type=MessageType.VALIDATION_PASS,
                content={"validation_passed": True},
                confidence=0.90,
            ),
        ]

        # Test weighted consensus
        decision = await engine.make_decision(
            execution, messages, DecisionPolicy.WEIGHTED_CONSENSUS
        )

        assert decision is not None, "Decision engine returned None"
        assert decision.confidence_score > 0, "Confidence score is zero"
        assert decision.final_output is not None, "No final output"

        print(f"  ✓ Weighted consensus: confidence={decision.confidence_score:.2f}")
        print(f"  ✓ Final output generated: {bool(decision.final_output)}")

        results.add("decision_engine", True, "Decision policies working")

    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.add("decision_engine", False, str(e))


async def test_team_execution_flow(supabase):
    """Test end-to-end team execution flow (without actual agents)."""
    print("\n[TEST 5] Team Execution Flow")

    try:
        # Initialize registry
        registry = TeamDefinitionRegistry()
        await registry.initialize(supabase)

        # Get planning team
        team_def = registry.get_by_team_id("planning_team")
        assert team_def is not None, "Planning team not found"

        # Create execution context
        context = TeamExecutionContext(
            mission_id=uuid4(),
            node_id=uuid4(),
            execution_id=f"test_{uuid4().hex[:8]}",
            objective="Plan a simple feature",
            constraints=["Must be testable"],
            max_rounds=2,
        )

        # Create workspace
        from torq_console.teams.context import TeamContextManager
        ctx_manager = TeamContextManager(supabase)
        workspace_id = await ctx_manager.create_workspace(
            context.mission_id, context.node_id, uuid4()
        )
        context.workspace_id = workspace_id
        print(f"  ✓ Workspace created: {workspace_id}")

        # Test adding role output
        await ctx_manager.add_role_output(
            workspace_id, uuid4(), 1, "lead",
            {"text": "Lead's plan", "steps": ["Step 1", "Step 2"]}
        )
        print(f"  ✓ Role output added")

        # Retrieve context
        full_context = await ctx_manager.get_full_context(workspace_id)
        assert "rounds" in full_context, "Context missing rounds"
        print(f"  ✓ Context retrieved: {len(full_context['rounds'])} rounds")

        results.add("team_execution_flow", True, "Execution flow validated")

    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.add("team_execution_flow", False, str(e))


async def test_api_integration(supabase):
    """Test API integration with existing systems."""
    print("\n[TEST 6] API Integration")

    try:
        # Test missions table still accessible
        missions = supabase.table("missions").select("*", count="exact").limit(1).execute()
        print(f"  ✓ Missions table accessible")

        # Test mission_nodes table
        nodes = supabase.table("mission_nodes").select("*", count="exact").limit(1).execute()
        print(f"  ✓ Mission nodes table accessible")

        # Test workspace_entries if available
        try:
            workspace = supabase.table("workspace_entries").select("*", count="exact").limit(1).execute()
            print(f"  ✓ Workspace entries table accessible ({workspace.count} rows)")
        except Exception:
            print(f"  ⚠ Workspace entries table not available (optional)")

        results.add("api_integration", True, "All required tables accessible")

    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.add("api_integration", False, str(e))


# ============================================================================
# Main Test Runner
# ============================================================================

async def run_all_tests():
    """Run all Phase 5.2 regression tests."""
    print("\n" + "="*60)
    print("PHASE 5.2 AGENT TEAMS - REGRESSION TEST SUITE")
    print("="*60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    supabase = get_supabase_client()

    # Run tests
    await test_database_schema(supabase)
    await test_team_registry(supabase)
    await test_team_persistence(supabase)
    await test_decision_engine(supabase)
    await test_team_execution_flow(supabase)
    await test_api_integration(supabase)

    # Print summary
    return results.print_summary()


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
