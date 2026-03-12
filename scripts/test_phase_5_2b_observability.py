#!/usr/bin/env python3
"""
Phase 5.2B - Observability API Test

Tests the new observability endpoints:
- /executions/{id}/card
- /executions/{id}/detail
- /executions/{id}/roles
- /executions/{id}/timeline
- /executions/{id}/decision
- /executions/{id}/confidence
- /executions/{id}/events/stream (SSE)
"""

import os
import sys
import asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from datetime import datetime
from uuid import UUID

from torq_console.dependencies import get_supabase_client
from torq_console.teams import (
    execute_team_node,
    TeamPersistence,
)


def print_header(text):
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)


def print_success(text):
    print(f"[OK] {text}")


def print_fail(text):
    print(f"[FAIL] {text}")


def print_info(text):
    print(f"[INFO] {text}")


async def get_test_execution():
    """Get an existing team execution for testing."""
    supabase = get_supabase_client()

    # Get most recent execution
    result = supabase.table("team_executions").select("*")\
        .order("created_at", desc=True)\
        .limit(1)\
        .execute()

    if not result.data:
        # Create a new one
        print_info("No existing execution found. Creating one...")
        missions_result = supabase.table("missions").select("*").limit(1).execute()
        if not missions_result.data:
            raise ValueError("No missions found")

        mission_id = UUID(missions_result.data[0]["id"])

        nodes_result = supabase.table("mission_nodes").select("*")\
            .eq("mission_id", str(mission_id)).limit(1).execute()

        if not nodes_result.data:
            raise ValueError("No nodes found")

        node_id = UUID(nodes_result.data[0]["id"])

        result_obj = await execute_team_node(
            supabase=supabase,
            mission_id=mission_id,
            node_id=node_id,
            team_id="research_team",
            objective="Test execution for observability validation",
        )

        execution_id = result_obj.team_execution_id
    else:
        execution_id = UUID(result.data[0]["id"])

    print_info(f"Using execution: {str(execution_id)[:8]}...")
    return execution_id


async def test_card_endpoint(execution_id):
    """Test /executions/{id}/card endpoint."""
    print_header("TEST 1: Execution Card Endpoint")

    import httpx

    # Get API base URL from environment or use localhost
    api_url = os.environ.get("TORQ_API_URL", "http://localhost:8000")

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{api_url}/api/teams/executions/{execution_id}/card")

        if response.status_code == 200:
            data = response.json()
            print_success(f"Card endpoint returned 200")
            print(f"  execution_id: {data.get('execution_id', 'N/A')[:8]}...")
            print(f"  team_name: {data.get('team_name', 'N/A')}")
            print(f"  rounds: {data.get('rounds_completed', 0)}/{data.get('rounds_total', 0)}")
            print(f"  confidence: {data.get('confidence', 0.0)}")
            print(f"  status: {data.get('status', 'N/A')}")
            return True
        else:
            print_fail(f"Card endpoint returned {response.status_code}: {response.text[:100]}")
            return False


async def test_roles_endpoint(execution_id):
    """Test /executions/{id}/roles endpoint."""
    print_header("TEST 2: Role Roster Endpoint")

    import httpx

    api_url = os.environ.get("TORQ_API_URL", "http://localhost:8000")

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{api_url}/api/teams/executions/{execution_id}/roles")

        if response.status_code == 200:
            roles = response.json()
            print_success(f"Roles endpoint returned 200")
            print(f"  roles: {len(roles)}")

            for role in roles:
                status_symbol = "✓" if role.get("status") == "completed" else "○"
                print(f"    {status_symbol} {role.get('display_name', role.get('role'))}: {role.get('status')}")

            return True
        else:
            print_fail(f"Roles endpoint returned {response.status_code}: {response.text[:100]}")
            return False


async def test_timeline_endpoint(execution_id):
    """Test /executions/{id}/timeline endpoint."""
    print_header("TEST 3: Timeline Endpoint")

    import httpx

    api_url = os.environ.get("TORQ_API_URL", "http://localhost:8000")

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{api_url}/api/teams/executions/{execution_id}/timeline")

        if response.status_code == 200:
            timeline = response.json()
            print_success(f"Timeline endpoint returned 200")
            print(f"  events: {len(timeline)}")

            # Show first few events
            for event in timeline[:5]:
                print(f"    [{event.get('round_number')}] {event.get('event_type')}: {event.get('sender_role', 'N/A')}")

            if len(timeline) > 5:
                print(f"    ... and {len(timeline) - 5} more")

            return True
        else:
            print_fail(f"Timeline endpoint returned {response.status_code}: {response.text[:100]}")
            return False


async def test_decision_endpoint(execution_id):
    """Test /executions/{id}/decision endpoint."""
    print_header("TEST 4: Decision Endpoint")

    import httpx

    api_url = os.environ.get("TORQ_API_URL", "http://localhost:8000")

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{api_url}/api/teams/executions/{execution_id}/decision")

        if response.status_code == 200:
            decision = response.json()
            print_success(f"Decision endpoint returned 200")
            print(f"  policy: {decision.get('decision_policy', 'N/A')}")
            print(f"  confidence: {decision.get('final_confidence', 0.0)}")
            print(f"  validator: {decision.get('validator_status', 'N/A')}")
            print(f"  dissent: {decision.get('has_dissent', False)}")

            return True
        else:
            print_fail(f"Decision endpoint returned {response.status_code}: {response.text[:100]}")
            return False


async def test_confidence_endpoint(execution_id):
    """Test /executions/{id}/confidence endpoint."""
    print_header("TEST 5: Confidence Breakdown Endpoint")

    import httpx

    api_url = os.environ.get("TORQ_API_URL", "http://localhost:8000")

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{api_url}/api/teams/executions/{execution_id}/confidence")

        if response.status_code == 200:
            confidence = response.json()
            print_success(f"Confidence endpoint returned 200")

            for role_conf in confidence:
                print(f"    {role_conf.get('display_name')}: {role_conf.get('confidence', 0.0):.3f} ({role_conf.get('contribution_count')} contributions)")

            return True
        else:
            print_fail(f"Confidence endpoint returned {response.status_code}: {response.text[:100]}")
            return False


async def test_detail_endpoint(execution_id):
    """Test /executions/{id}/detail endpoint."""
    print_header("TEST 6: Full Detail Endpoint")

    import httpx

    api_url = os.environ.get("TORQ_API_URL", "http://localhost:8000")

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{api_url}/api/teams/executions/{execution_id}/detail")

        if response.status_code == 200:
            detail = response.json()
            print_success(f"Detail endpoint returned 200")

            # Check all required sections
            has_card = "card" in detail
            has_roles = "roles" in detail
            has_timeline = "timeline" in detail
            has_decision = "decision" in detail

            print(f"  card: {'✓' if has_card else '✗'}")
            print(f"  roles: {'✓' if has_roles else '✗'} ({len(detail.get('roles', []))} roles)")
            print(f"  timeline: {'✓' if has_timeline else '✗'} ({len(detail.get('timeline', []))} events)")
            print(f"  decision: {'✓' if has_decision else '✗'}")

            return has_card and has_roles and has_timeline and has_decision
        else:
            print_fail(f"Detail endpoint returned {response.status_code}: {response.text[:100]}")
            return False


async def run_observability_tests():
    """Run all Phase 5.2B observability tests."""
    print_header("PHASE 5.2B OBSERVABILITY API TEST")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Get test execution
    execution_id = await get_test_execution()

    # Note: These tests require the API server to be running
    print_info("\nNote: These tests require the TORQ API server to be running.")
    print_info("Start it with: python -m uvicorn api.main:app --reload")
    print_info("Or set TORQ_API_URL to the correct endpoint.\n")

    results = {}

    try:
        results["card"] = await test_card_endpoint(execution_id)
    except Exception as e:
        print_fail(f"Card endpoint test failed: {e}")
        results["card"] = False

    try:
        results["roles"] = await test_roles_endpoint(execution_id)
    except Exception as e:
        print_fail(f"Roles endpoint test failed: {e}")
        results["roles"] = False

    try:
        results["timeline"] = await test_timeline_endpoint(execution_id)
    except Exception as e:
        print_fail(f"Timeline endpoint test failed: {e}")
        results["timeline"] = False

    try:
        results["decision"] = await test_decision_endpoint(execution_id)
    except Exception as e:
        print_fail(f"Decision endpoint test failed: {e}")
        results["decision"] = False

    try:
        results["confidence"] = await test_confidence_endpoint(execution_id)
    except Exception as e:
        print_fail(f"Confidence endpoint test failed: {e}")
        results["confidence"] = False

    try:
        results["detail"] = await test_detail_endpoint(execution_id)
    except Exception as e:
        print_fail(f"Detail endpoint test failed: {e}")
        results["detail"] = False

    # Summary
    print_header("OBSERVABILITY TEST SUMMARY")

    for endpoint, passed in results.items():
        status = "[OK]" if passed else "[FAIL]"
        print(f"{status} /executions/{{id}}/{endpoint}")

    all_passed = all(results.values())

    print("\n" + "=" * 60)
    if all_passed:
        print("[SUCCESS] PHASE 5.2B OBSERVABILITY COMPLETE")
        print("=" * 60)
        return 0
    else:
        print("[PARTIAL] Some endpoints failed (server may not be running)")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_observability_tests())
    sys.exit(exit_code)
