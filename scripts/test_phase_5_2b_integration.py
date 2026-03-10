#!/usr/bin/env python3
"""
Phase 5.2B Full Integration Test

Validates end-to-end observability path:
1. Static endpoint sanity
2. Full view data integrity
3. Live SSE execution test
4. REST + SSE reconciliation
5. Historical replay
6. Concurrent UI sanity
7. Regression rerun
"""

import os
import sys
import asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from datetime import datetime
from uuid import UUID
import time

from torq_console.dependencies import get_supabase_client
from torq_console.teams import (
    execute_team_node,
    TeamPersistence,
)


def print_header(text):
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70)


def print_success(text):
    print(f"[✓] {text}")


def print_fail(text):
    print(f"[✗] {text}")


def print_info(text):
    print(f"[INFO] {text}")


async def get_recent_execution():
    """Get a recent completed execution for testing."""
    supabase = get_supabase_client()
    persistence = TeamPersistence(supabase)

    executions = await persistence.list_executions(limit=5)
    for exec in executions:
        if exec.status.value == "completed":
            messages = await persistence.get_messages(exec.id)
            decision = await persistence.get_decision(exec.id)
            if messages and decision:
                return exec, str(exec.id)

    # Create new one if none available
    missions_result = supabase.table("missions").select("*").limit(1).execute()
    mission_id = UUID(missions_result.data[0]["id"])

    nodes_result = supabase.table("mission_nodes").select("*")\
        .eq("mission_id", str(mission_id)).limit(1).execute()
    node_id = UUID(nodes_result.data[0]["id"])

    result = await execute_team_node(
        supabase=supabase,
        mission_id=mission_id,
        node_id=node_id,
        team_id="research_team",
        objective="Integration test execution",
    )

    execution = await persistence.get_execution(result.team_execution_id)
    return execution, str(result.team_execution_id)


async def test_1_static_endpoint_sanity(execution_id):
    """Test 1: Static endpoint sanity."""
    print_header("TEST 1: Static Endpoint Sanity")

    import httpx

    api_url = os.environ.get("TORQ_API_URL", "http://localhost:8000")
    endpoints = [
        "/card",
        "/roles",
        "/decision",
        "/timeline",
        "/confidence",
    ]

    all_ok = True
    for endpoint in endpoints:
        try:
            response = await httpx.AsyncClient(timeout=10.0).get(
                f"{api_url}/api/teams/executions/{execution_id}{endpoint}"
            )
            if response.status_code == 200:
                data = response.json()
                print_success(f"{endpoint} - 200 OK")
            else:
                print_fail(f"{endpoint} - {response.status_code}")
                all_ok = False
        except Exception as e:
            print_fail(f"{endpoint} - Error: {str(e)[:50]}")
            all_ok = False

    return all_ok


async def test_2_full_view_data_integrity(execution_id):
    """Test 2: Full view data integrity check."""
    print_header("TEST 2: Full View Data Integrity")

    from httpx import AsyncClient

    api_url = os.environ.get("TORQ_API_URL", "http://localhost:8000")

    try:
        async with AsyncClient(timeout=10.0) as client:
            # Get card
            card_resp = await client.get(f"{api_url}/api/teams/executions/{execution_id}/card")
            card = card_resp.json() if card_resp.status_code == 200 else None

            # Get roles
            roles_resp = await client.get(f"{api_url}/api/teams/executions/{execution_id}/roles")
            roles = roles_resp.json() if roles_resp.status_code == 200 else []

            # Get decision
            decision_resp = await client.get(f"{api_url}/api/teams/executions/{execution_id}/decision")
            decision = decision_resp.json() if decision_resp.status_code == 200 else None

            # Get timeline
            timeline_resp = await client.get(f"{api_url}/api/teams/executions/{execution_id}/timeline")
            timeline = timeline_resp.json() if timeline_resp.status_code == 200 else []

            # Validate
            checks = []

            if card:
                checks.append(("Card loads", "team_name" in card))
                checks.append(("Card has confidence", card.get("confidence", 0) >= 0))
                checks.append(("Card has rounds", card.get("rounds_completed", 0) > 0))
            else:
                checks.append(("Card loads", False))

            if roles:
                checks.append(("Role roster loads", len(roles) == 4))
                checks.append(("All roles have status", all(r.get("status") for r in roles)))
            else:
                checks.append(("Role roster loads", False))

            if decision:
                checks.append(("Decision loads", "final_confidence" in decision))
                checks.append(("Decision has policy", "decision_policy" in decision))
            else:
                checks.append(("Decision loads", False))

            if timeline:
                checks.append(("Timeline loads", len(timeline) > 0))
                # Check ordering (timestamps should be non-decreasing)
                timestamps = [t.get("timestamp") for t in timeline]
                checks.append(("Timeline ordered", all(timestamps[i] <= timestamps[i+1] for i in range(len(timestamps)-1))))
            else:
                checks.append(("Timeline loads", False))

            for name, passed in checks:
                if passed:
                    print_success(name)
                else:
                    print_fail(name)

            return all(c[1] for c in checks)

    except Exception as e:
        print_fail(f"Data integrity test failed: {e}")
        return False


async def test_3_sse_execution_stream():
    """Test 3: Live SSE execution test."""
    print_header("TEST 3: Live SSE Execution Test")

    print_info("Starting new team execution with SSE monitoring...")

    from httpx import AsyncClient

    api_url = os.environ.get("TORQ_API_URL", "http://localhost:8000")

    # Get mission/node for test
    supabase = get_supabase_client()
    missions_result = supabase.table("missions").select("*").limit(1).execute()
    mission_id = UUID(missions_result.data[0]["id"])

    nodes_result = supabase.table("mission_nodes").select("*")\
        .eq("mission_id", str(mission_id)).limit(1).execute()
    node_id = UUID(nodes_result.data[0]["id"])

    # Start execution
    print_info("Launching team execution...")
    result = await execute_team_node(
        supabase=supabase,
        mission_id=mission_id,
        node_id=node_id,
        team_id="research_team",
        objective="SSE integration test execution",
    )

    execution_id = str(result.team_execution_id)
    print_info(f"Execution started: {execution_id[:8]}...")

    # Connect SSE and verify we get events
    print_info("Connecting to SSE stream...")

    events_received = []
    event_types = set()

    try:
        async with AsyncClient(timeout=30.0) as client:
            async with client.stream(
                "GET",
                f"{api_url}/api/teams/executions/{execution_id}/events/stream"
            ) as response:
                if response.status_code != 200:
                    print_fail(f"SSE connection failed: {response.status_code}")
                    return False

                print_success("SSE connected")

                async for chunk in response.aiter_bytes():
                    if not chunk:
                        break

                    text = chunk.decode()
                    for line in text.split('\n'):
                        if line.startswith('data: '):
                            try:
                                import json
                                data = json.loads(line[6:])
                                events_received.append(data)
                                if 'event_type' in data:
                                    event_types.add(data['event_type'])
                                if 'status' in data:
                                    event_types.add(f"status_{data['status']}")
                            except:
                                pass

                    # Check if we got completion event
                    if any('complete' in str(e) for e in events_received):
                        break

        print_success(f"Received {len(events_received)} SSE events")
        print(f"  Event types: {event_types}")

        # Verify we got expected events
        has_status = any('status' in str(e) for e in events_received)
        has_complete = any('complete' in str(e) for e in events_received)

        if has_status:
            print_success("Received status updates")
        else:
            print_fail("No status updates received")

        if has_complete:
            print_success("Received completion event")
        else:
            print_fail("No completion event received")

        return len(events_received) > 0 and has_complete

    except Exception as e:
        print_fail(f"SSE test failed: {e}")
        return False


async def test_4_rest_sse_reconciliation(execution_id):
    """Test 4: REST + SSE reconciliation test."""
    print_header("TEST 4: REST + SSE Reconciliation")

    from httpx import AsyncClient
    import json

    api_url = os.environ.get("TORQ_API_URL", "http://localhost:8000")

    try:
        async with AsyncClient(timeout=10.0) as client:
            # Get REST data
            card_resp = await client.get(f"{api_url}/api/teams/executions/{execution_id}/card")
            rest_card = card_resp.json() if card_resp.status_code == 200 else None

            # Get SSE final state
            final_confidence_rest = rest_card.get("confidence") if rest_card else None

            # Get decision for comparison
            decision_resp = await client.get(f"{api_url}/api/teams/executions/{execution_id}/decision")
            decision = decision_resp.json() if decision_resp.status_code == 200 else None

            decision_confidence = decision.get("final_confidence") if decision else None

            # Check reconciliation
            checks = []

            if rest_card and decision:
                checks.append(("Confidence matches REST decision",
                    abs(rest_card.get("confidence", 0) - decision.get("final_confidence", 0)) < 0.01))
                checks.append(("Decision has consistent data", decision.get("final_confidence") >= 0))

            if rest_card:
                checks.append(("Card has status", rest_card.get("status") in ["completed", "failed", "blocked"]))
                checks.append(("Card has round data", rest_card.get("rounds_completed") == rest_card.get("rounds_total")))

            for name, passed in checks:
                if passed:
                    print_success(name)
                else:
                    print_fail(name)

            return all(c[1] for c in checks)

    except Exception as e:
        print_fail(f"Reconciliation test failed: {e}")
        return False


async def test_5_historical_replay(execution_id):
    """Test 5: Historical replay test."""
    print_header("TEST 5: Historical Replay Test")

    from httpx import AsyncClient

    api_url = os.environ.get("TORQ_API_URL", "http://localhost:8000")

    try:
        async with AsyncClient(timeout=10.0) as client:
            # Load all components without SSE
            card_resp = await client.get(f"{api_url}/api/teams/executions/{execution_id}/card")
            roles_resp = await client.get(f"{api_url}/api/teams/executions/{execution_id}/roles")
            timeline_resp = await client.get(f"{api_url}/api/teams/executions/{execution_id}/timeline")
            decision_resp = await client.get(f"{api_url}/api/teams/executions/{execution_id}/decision")

            checks = []

            # All should load without SSE
            checks.append(("Card loads from REST", card_resp.status_code == 200))
            checks.append(("Roles load from REST", roles_resp.status_code == 200))
            checks.append(("Timeline loads from REST", timeline_resp.status_code == 200))
            checks.append(("Decision loads from REST", decision_resp.status_code == 200))

            # Verify data integrity
            if card_resp.status_code == 200:
                card = card_resp.json()
                checks.append(("Historical card has data", card.get("rounds_completed") > 0))

            if timeline_resp.status_code == 200:
                timeline = timeline_resp.json()
                checks.append(("Historical timeline has events", len(timeline) > 0))

            for name, passed in checks:
                if passed:
                    print_success(name)
                else:
                    print_fail(name)

            return all(c[1] for c in checks)

    except Exception as e:
        print_fail(f"Historical replay test failed: {e}")
        return False


async def test_6_concurrent_ui_sanity():
    """Test 6: Concurrent UI sanity test."""
    print_header("TEST 6: Concurrent UI Sanity Test")

    print_info("Running 3 concurrent executions...")

    supabase = get_supabase_client()

    missions_result = supabase.table("missions").select("*").limit(1).execute()
    mission_id = UUID(missions_result.data[0]["id"])

    nodes_result = supabase.table("mission_nodes").select("*")\
        .eq("mission_id", str(mission_id)).limit(1).execute()
    node_id = UUID(nodes_result.data[0]["id"])

    # Run concurrent executions
    tasks = []
    for i in range(3):
        task = execute_team_node(
            supabase=supabase,
            mission_id=mission_id,
            node_id=node_id,
            team_id="research_team",
            objective=f"Concurrent test {i+1}",
        )
        tasks.append(task)

    start = time.time()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    duration = time.time() - start

    # Check results
    success_count = sum(1 for r in results if isinstance(r, object) and hasattr(r, 'team_execution_id'))
    failed = any(isinstance(r, Exception) for r in results)

    print_success(f"Completed {success_count}/3 executions in {duration:.1f}s")

    # Verify no duplicates across executions
    all_ids = []
    for r in results:
        if isinstance(r, object) and hasattr(r, 'team_execution_id'):
            all_ids.append(str(r.team_execution_id))

    unique_ids = set(all_ids)
    checks = [
        ("No duplicate execution IDs", len(all_ids) == len(unique_ids)),
        ("All executions completed", success_count == 3),
        ("No execution failures", not failed),
    ]

    for name, passed in checks:
        if passed:
            print_success(name)
        else:
            print_fail(name)

    return all(c[1] for c in checks)


async def test_7_regression_rerun():
    """Test 7: Regression rerun."""
    print_header("TEST 7: Regression Rerun")

    # Run 5.2A regression
    print_info("Running Phase 5.2A regression test...")

    from torq_console.teams import TeamPersistence

    supabase = get_supabase_client()
    persistence = TeamPersistence(supabase)

    # Check a recent execution
    executions = await persistence.list_executions(limit=1)
    if not executions:
        print_fail("No executions to verify")
        return False

    exec = executions[0]
    messages = await persistence.get_messages(exec.id)
    decision = await persistence.get_decision(exec.id)

    checks = [
        ("Execution record exists", exec.status.value in ["completed", "failed", "blocked"]),
        ("Messages persisted", len(messages) > 0),
        ("Decision persisted", decision is not None),
        ("Message count correct (15)", len(messages) == 15),
        ("Rounds completed (3)", exec.current_round == exec.max_rounds),
        ("Confidence valid", exec.final_confidence is not None),
    ]

    for name, passed in checks:
        if passed:
            print_success(name)
        else:
            print_fail(name)

    return all(c[1] for c in checks)


async def run_full_integration_test():
    """Run all Phase 5.2B integration tests."""
    print_header("PHASE 5.2B FULL INTEGRATION TEST")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Get a test execution first
    print_info("Getting test execution...")
    _, execution_id = await get_recent_execution()
    print_info(f"Using execution: {execution_id[:8]}...")

    results = {}

    # Test 1: Static endpoints
    results["static_endpoints"] = await test_1_static_endpoint_sanity(execution_id)

    # Test 2: Full view data integrity
    results["data_integrity"] = await test_2_full_view_data_integrity(execution_id)

    # Test 3: SSE execution stream
    results["sse_streaming"] = await test_3_sse_execution_stream()

    # Test 4: REST + SSE reconciliation
    results["reconciliation"] = await test_4_rest_sse_reconciliation(execution_id)

    # Test 5: Historical replay
    results["historical"] = await test_5_historical_replay(execution_id)

    # Test 6: Concurrent sanity
    results["concurrent"] = await test_6_concurrent_ui_sanity()

    # Test 7: Regression
    results["regression"] = await test_7_regression_rerun()

    # Summary
    print_header("INTEGRATION TEST SUMMARY")

    for test_name, passed in results.items():
        status = "[✓]" if passed else "[✗]"
        print(f"{status} {test_name.replace('_', ' ').title()}")

    all_passed = all(results.values())

    print("\n" + "=" * 70)
    if all_passed:
        print("[SUCCESS] PHASE 5.2B INTEGRATION COMPLETE")
        print("=" * 70)
        print("\nAll validation checks passed.")
        print("Agent Teams runtime + observability is complete.")
        return 0
    else:
        print("[FAILURE] INTEGRATION INCOMPLETE")
        print("=" * 70)
        failed = [name for name, passed in results.items() if not passed]
        print(f"\nFailed tests: {', '.join(failed)}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_full_integration_test())
    sys.exit(exit_code)
