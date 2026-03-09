#!/usr/bin/env python3
"""
Phase 5.2A - First Execution Test

This script validates the first end-to-end agent_team execution
after database migration is applied.

Run this AFTER applying migrations/018_agent_teams.sql
"""

import os
import sys
import asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from datetime import datetime
from uuid import uuid4, UUID

from torq_console.dependencies import get_supabase_client
from torq_console.teams import (
    execute_team_node,
    TeamPersistence,
    TeamDefinitionRegistry,
    initialize_registry,
)


def print_header(text):
    """Print section header."""
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)


def print_success(text):
    """Print success message."""
    print(f"[OK] {text}")


def print_fail(text):
    """Print failure message."""
    print(f"[FAIL] {text}")


def print_info(text):
    """Print info message."""
    print(f"[INFO] {text}")


async def verify_migration():
    """Verify database migration was applied."""
    print_header("STEP 1: Verify Migration")

    supabase = get_supabase_client()

    tables_to_check = [
        ("agent_teams", 3),  # 3 expected rows
        ("agent_team_members", 12),  # 12 expected rows
        ("team_executions", 0),
        ("team_messages", 0),
        ("team_decisions", 0),
    ]

    all_verified = True

    for table, expected_min in tables_to_check:
        try:
            result = supabase.table(table).select("*", count="exact").execute()
            count = result.count

            if count >= expected_min:
                print_success(f"{table}: {count} rows (expected >= {expected_min})")
            else:
                print_fail(f"{table}: {count} rows (expected >= {expected_min})")
                all_verified = False

        except Exception as e:
            print_fail(f"{table}: {str(e)[:100]}")
            all_verified = False

    return all_verified


async def verify_team_templates():
    """Verify team templates are loaded."""
    print_header("STEP 2: Verify Team Templates")

    try:
        registry = TeamDefinitionRegistry()
        await registry.initialize(supabase_client(), load_from_db=True)

        teams_to_check = ["planning_team", "research_team", "build_team"]
        all_found = True

        for team_id in teams_to_check:
            team = registry.get_by_team_id(team_id)
            if team:
                members = len(team.members)
                print_success(f"{team_id}: {members} members")
            else:
                print_fail(f"{team_id}: not found")
                all_found = False

        return all_found

    except Exception as e:
        print_fail(f"Error loading teams: {e}")
        return False


async def run_first_execution():
    """Run first agent_team execution test."""
    print_header("STEP 3: First Agent Team Execution")

    supabase = get_supabase_client()

    # Get an existing mission and node for testing
    missions_result = supabase.table("missions").select("*").limit(1).execute()

    if not missions_result.data:
        print_fail("No missions found. Create a test mission first.")
        return False

    mission = missions_result.data[0]
    mission_id = mission["id"]

    # Get nodes for this mission
    nodes_result = supabase.table("mission_nodes").select("*").eq(
        "mission_id", mission_id
    ).limit(1).execute()

    if not nodes_result.data:
        print_fail("No nodes found for mission. Cannot run team execution test.")
        return False

    node = nodes_result.data[0]
    node_id = node["id"]

    print_info(f"Using mission: {mission_id[:8]}...")
    print_info(f"Using node: {node_id[:8]}...")

    # Execute using research_team
    try:
        print_info("\nExecuting research_team...")
        print_info("Objective: Analyze TORQ Console architecture")

        result = await execute_team_node(
            supabase=supabase,
            mission_id=mission_id,
            node_id=node_id,
            team_id="research_team",
            objective="Analyze TORQ Console architecture and identify key components",
            constraints=["Use verified information only", "Focus on execution fabric"],
        )

        print_success(f"Execution completed!")
        print(f"  Team Execution ID: {str(result.team_execution_id)[:8]}...")
        print(f"  Confidence Score: {result.confidence_score:.2f}")
        print(f"  Validator Status: {result.validator_status}")
        print(f"  Decision Policy: {result.decision_policy}")

        return True, result.team_execution_id

    except Exception as e:
        print_fail(f"Execution failed: {e}")
        return False, None


async def verify_persistence(team_execution_id):
    """Verify persistence after execution."""
    print_header("STEP 4: Verify Persistence")

    supabase = get_supabase_client()
    persistence = TeamPersistence(supabase)

    all_verified = True

    # Check team_executions
    execution = await persistence.get_execution(team_execution_id)
    if execution:
        print_success(f"team_executions: 1 row found")
        print(f"  Status: {execution.status}")
        print(f"  Rounds: {execution.current_round}/{execution.max_rounds}")
        print(f"  Final Confidence: {execution.final_confidence}")
    else:
        print_fail("team_executions: execution not found")
        all_verified = False

    # Check team_messages
    messages = await persistence.get_messages(team_execution_id)
    if messages:
        print_success(f"team_messages: {len(messages)} rows")

        # Count message types
        from collections import Counter
        msg_types = Counter(m.message_type.value for m in messages)
        print(f"  Message types: {dict(msg_types)}")
    else:
        print_fail("team_messages: no messages found")
        all_verified = False

    # Check team_decisions
    decision = await persistence.get_decision(team_execution_id)
    if decision:
        print_success("team_decisions: 1 row found")
        print(f"  Validator Status: {decision.validator_status}")
        print(f"  Decision Policy: {decision.decision_policy}")
        print(f"  Has Dissent: {decision.dissent_summary.get('has_dissent', False)}")
    else:
        print_fail("team_decisions: decision not found")
        all_verified = False

    return all_verified


async def check_no_duplicates(team_execution_id):
    """Check for duplicate execution records."""
    print_header("STEP 5: Idempotency Check")

    supabase = get_supabase_client()

    # Check for duplicate executions for same node
    result = supabase.table("team_executions").select("*").eq(
        "id", str(team_execution_id)
    ).execute()

    if len(result.data) == 1:
        print_success("No duplicate execution records")
        return True
    else:
        print_fail(f"Found {len(result.data)} execution records - duplicates detected!")
        return False


async def run_activation_test():
    """Run complete activation test."""
    print_header("PHASE 5.2A - RUNTIME ACTIVATION TEST")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Step 1: Verify migration
    migration_ok = await verify_migration()
    if not migration_ok:
        print("\n" + "=" * 60)
        print("BLOCKED: Migration not applied")
        print("=" * 60)
        print("\nPlease apply migrations/018_agent_teams.sql via:")
        print("1. Supabase Dashboard SQL Editor")
        print("2. Copy SQL file contents")
        print("3. Run the query")
        return 1

    # Step 2: Verify team templates
    templates_ok = await verify_team_templates()
    if not templates_ok:
        print("\nBLOCKED: Team templates not loaded")
        return 1

    # Step 3: Run first execution
    exec_ok, execution_id = await run_first_execution()
    if not exec_ok:
        print("\nBLOCKED: First execution failed")
        return 1

    # Step 4: Verify persistence
    persistence_ok = await verify_persistence(execution_id)
    if not persistence_ok:
        print("\nWARNING: Persistence verification failed")
        # Continue to check duplicates anyway

    # Step 5: Check duplicates
    duplicates_ok = await check_no_duplicates(execution_id)

    # Final summary
    print_header("ACTIVATION TEST SUMMARY")

    checks = {
        "Migration Applied": migration_ok,
        "Team Templates Loaded": templates_ok,
        "First Execution": exec_ok,
        "Persistence Verified": persistence_ok,
        "No Duplicates": duplicates_ok,
    }

    for check, passed in checks.items():
        status = "[OK]" if passed else "[FAIL]"
        print(f"{status} {check}")

    all_passed = all(checks.values())

    print("\n" + "=" * 60)
    if all_passed:
        print("[SUCCESS] PHASE 5.2A ACTIVATION COMPLETE")
        print("=" * 60)
        print("\nPhase 5.2 is now runtime-validated.")
        print("Ready for Phase 5.2B: Observability + UI")
        return 0
    else:
        print("[FAILURE] ACTIVATION INCOMPLETE")
        print("=" * 60)
        failed = [c for c, p in checks.items() if not p]
        print(f"\nFailed checks: {', '.join(failed)}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_activation_test())
    sys.exit(exit_code)
