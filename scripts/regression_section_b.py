#!/usr/bin/env python3
"""
Section B: Mission Graph + Execution Fabric Regression

Tests core mission graph and execution fabric components.
"""

import os
import sys
import asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from torq_console.dependencies import get_supabase_client
from torq_console.mission_graph.executor import MissionNodeExecutor
from torq_console.mission_graph.scheduler import MissionGraphScheduler
from torq_console.mission_graph.builder import MissionGraphBuilder
from torq_console.mission_graph.context_bus import MissionContextBus
from torq_console.mission_graph.handoffs import HandoffManager


async def test_execution_fabric():
    """Test execution fabric core components."""

    print("\n" + "="*60)
    print("SECTION B: MISSION GRAPH + EXECUTION FABRIC")
    print("="*60)

    results = {}
    supabase = get_supabase_client()

    # Test B1: MissionNodeExecutor import and initialization
    print("\n[TEST B1] MissionNodeExecutor")
    try:
        executor = MissionNodeExecutor(supabase)
        print(f"  Status: Executor instantiated")
        print(f"  Type: {type(executor).__name__}")
        results["executor_init"] = "PASS"
    except Exception as e:
        print(f"  Status: FAIL - {e}")
        results["executor_init"] = "FAIL"

    # Test B2: MissionGraphScheduler import and initialization
    print("\n[TEST B2] MissionGraphScheduler")
    try:
        scheduler = MissionGraphScheduler(supabase, executor=None)
        print(f"  Status: Scheduler instantiated")
        print(f"  Type: {type(scheduler).__name__}")
        results["scheduler_init"] = "PASS"
    except Exception as e:
        print(f"  Status: FAIL - {e}")
        results["scheduler_init"] = "FAIL"

    # Test B3: MissionGraphBuilder import and initialization
    print("\n[TEST B3] MissionGraphBuilder")
    try:
        from torq_console.strategic_memory.retrieval import MemoryRetrievalEngine
        retrieval = MemoryRetrievalEngine(supabase)
        builder = MissionGraphBuilder(supabase, retrieval)
        print(f"  Status: Builder instantiated")
        print(f"  Type: {type(builder).__name__}")
        results["builder_init"] = "PASS"
    except Exception as e:
        print(f"  Status: FAIL - {e}")
        results["builder_init"] = "FAIL"

    # Test B4: MissionContextBus initialization
    print("\n[TEST B4] MissionContextBus")
    try:
        context_bus = MissionContextBus(supabase)
        print(f"  Status: MissionContextBus instantiated")
        results["context_bus_init"] = "PASS"
    except Exception as e:
        print(f"  Status: FAIL - {e}")
        results["context_bus_init"] = "FAIL"

    # Test B5: HandoffManager initialization
    print("\n[TEST B5] HandoffManager")
    try:
        handoff = HandoffManager(supabase)
        print(f"  Status: HandoffManager instantiated")
        results["handoff_init"] = "PASS"
    except Exception as e:
        print(f"  Status: FAIL - {e}")
        results["handoff_init"] = "FAIL"

    # Test B6: Verify database relationships
    print("\n[TEST B6] Database Relationships")
    try:
        # Check missions have graphs
        missions = supabase.table("missions").select("id").limit(1).execute()
        if missions.data:
            mission_id = missions.data[0]["id"]
            graphs = supabase.table("mission_graphs").select("*").eq("mission_id", mission_id).execute()
            nodes = supabase.table("mission_nodes").select("*").eq("mission_id", mission_id).execute()
            print(f"  Status: Relationships accessible")
            print(f"  Sample mission: {mission_id[:8]}...")
            print(f"  Graphs: {len(graphs.data)}, Nodes: {len(nodes.data)}")
            results["db_relationships"] = "PASS"
        else:
            print(f"  Status: SKIP - No missions found")
            results["db_relationships"] = "SKIP"
    except Exception as e:
        print(f"  Status: FAIL - {e}")
        results["db_relationships"] = "FAIL"

    # Summary
    print("\n" + "="*60)
    print("SECTION B SUMMARY")
    print("="*60)
    for test_name, status in results.items():
        print(f"  {test_name}: {status}")

    pass_count = sum(1 for s in results.values() if s == "PASS")
    total_count = len([s for s in results.values() if s != "SKIP"])
    print(f"\nTotal: {pass_count}/{total_count} tests passed")

    if pass_count == total_count:
        print("\n[OK] SECTION B PASSED")
        return True
    else:
        print(f"\n[FAIL] {total_count - pass_count} TESTS FAILED")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_execution_fabric())
    sys.exit(0 if success else 1)
