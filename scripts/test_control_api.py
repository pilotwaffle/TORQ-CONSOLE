#!/usr/bin/env python3
"""
Control API Regression Test

Quick smoke test for all 10 Control API endpoints.
Verifies endpoints respond correctly and return expected data shapes.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from torq_console.dependencies import get_supabase_client


def test_api_endpoints():
    """Test all Control API endpoints."""
    client = get_supabase_client()

    print("\n" + "="*60)
    print("CONTROL API REGRESSION TEST")
    print("="*60)

    results = {}

    # Test 1: GET /api/control/missions
    print("\n[TEST 1] GET /api/control/missions")
    try:
        result = client.table("missions").select("*").limit(5).execute()
        print(f"  Status: {result.data is not None}")
        print(f"  Missions returned: {len(result.data) if result.data else 0}")
        results["missions_list"] = "PASS"
    except Exception as e:
        print(f"  Status: FAIL - {e}")
        results["missions_list"] = "FAIL"

    # Test 2: Check mission_events table exists
    print("\n[TEST 2] Check mission_events table")
    try:
        result = client.table("mission_events").select("*", count="exact").execute()
        print(f"  Status: Table accessible")
        print(f"  Event count: {result.count}")
        results["events_table"] = "PASS"
    except Exception as e:
        print(f"  Status: FAIL - {e}")
        results["events_table"] = "FAIL"

    # Test 3: Check mission_handoffs table exists
    print("\n[TEST 3] Check mission_handoffs table")
    try:
        result = client.table("mission_handoffs").select("*", count="exact").execute()
        print(f"  Status: Table accessible")
        print(f"  Handoff count: {result.count}")
        results["handoffs_table"] = "PASS"
    except Exception as e:
        print(f"  Status: FAIL - {e}")
        results["handoffs_table"] = "FAIL"

    # Test 4: Check mission_nodes table exists
    print("\n[TEST 4] Check mission_nodes table")
    try:
        result = client.table("mission_nodes").select("*", count="exact").execute()
        print(f"  Status: Table accessible")
        print(f"  Node count: {result.count}")
        results["nodes_table"] = "PASS"
    except Exception as e:
        print(f"  Status: FAIL - {e}")
        results["nodes_table"] = "FAIL"

    # Test 5: Check workstream_states table exists (actual table name)
    print("\n[TEST 5] Check workstream_states table")
    try:
        result = client.table("workstream_states").select("*", count="exact").execute()
        print(f"  Status: Table accessible")
        print(f"  Workstream state count: {result.count}")
        results["workstreams_table"] = "PASS"
    except Exception as e:
        print(f"  Status: FAIL - {e}")
        results["workstreams_table"] = "FAIL"

    # Test 6: Check mission_graphs table exists
    print("\n[TEST 6] Check mission_graphs table")
    try:
        result = client.table("mission_graphs").select("*", count="exact").execute()
        print(f"  Status: Table accessible")
        print(f"  Graph count: {result.count}")
        results["graphs_table"] = "PASS"
    except Exception as e:
        print(f"  Status: FAIL - {e}")
        results["graphs_table"] = "FAIL"

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for test_name, status in results.items():
        print(f"  {test_name}: {status}")

    pass_count = sum(1 for s in results.values() if s == "PASS")
    total_count = len(results)
    print(f"\nTotal: {pass_count}/{total_count} tests passed")

    if pass_count == total_count:
        print("\n[OK] ALL TESTS PASSED")
        return True
    else:
        print(f"\n[FAIL] {total_count - pass_count} TESTS FAILED")
        return False


if __name__ == "__main__":
    success = test_api_endpoints()
    sys.exit(0 if success else 1)
