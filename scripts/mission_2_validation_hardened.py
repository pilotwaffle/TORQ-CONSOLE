#!/usr/bin/env python3
"""
Mission 2 Validation - Hardened Execution with Idempotency Guards

Tests Phase 5.1 execution fabric with:
- Idempotency guards (no duplicate events)
- Rich handoff format only
- Decision gate structure
- Mission completion idempotency
"""

import os
import sys
import json
from datetime import datetime
from uuid import uuid4

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client
from torq_console.settings import get_settings
from torq_console.mission_graph.executor import MissionNodeExecutor, MissionCompleter


def get_supabase_client():
    """Get Supabase client."""
    settings = get_settings()
    return create_client(settings.supabase.url, settings.supabase.service_role_key)


def create_mission_2_hardware():
    """Create Mission 2 with decision gate structure."""
    mission_id = str(uuid4())
    graph_id = str(uuid4())

    print(f"\n[CREATE] Mission 2: Idempotency & Handoff Validation")
    print(f"Mission ID: {mission_id}")
    print(f"Graph ID: {graph_id}")

    client = get_supabase_client()

    # Create mission
    mission_data = {
        "id": mission_id,
        "title": "Idempotency & Handoff Validation",
        "mission_type": "analysis",
        "objective": "Validate hardened execution with idempotency guards",
        "status": "draft"
    }

    client.table("missions").insert(mission_data).execute()

    # Create graph
    graph_data = {
        "id": graph_id,
        "mission_id": mission_id,
        "version": "1.0",
        "status": "draft"
    }

    client.table("mission_graphs").insert(graph_data).execute()

    # Create nodes (simplified linear flow for testing)
    obj_id = str(uuid4())
    task1_id = str(uuid4())
    task2_id = str(uuid4())
    evidence_id = str(uuid4())
    deliverable_id = str(uuid4())

    nodes = [
        {
            "id": obj_id,
            "mission_id": mission_id,
            "graph_id": graph_id,
            "node_type": "objective",
            "title": "Validate Idempotency Guards",
            "description": "Test that nodes execute exactly once",
            "status": "pending",
            "depends_on": [],
            "workstream_id": str(uuid4())
        },
        {
            "id": task1_id,
            "mission_id": mission_id,
            "graph_id": graph_id,
            "node_type": "task",
            "title": "Test Node Execution",
            "description": "Execute node and verify idempotency",
            "status": "pending",
            "depends_on": [obj_id],
            "workstream_id": str(uuid4())
        },
        {
            "id": task2_id,
            "mission_id": mission_id,
            "graph_id": graph_id,
            "node_type": "task",
            "title": "Test Event Emission",
            "description": "Verify events emitted exactly once",
            "status": "pending",
            "depends_on": [task1_id],
            "workstream_id": str(uuid4())
        },
        {
            "id": evidence_id,
            "mission_id": mission_id,
            "graph_id": graph_id,
            "node_type": "evidence",
            "title": "Evidence Synthesis",
            "description": "Synthesize validation results",
            "status": "pending",
            "depends_on": [task2_id],
            "workstream_id": str(uuid4())
        },
        {
            "id": deliverable_id,
            "mission_id": mission_id,
            "graph_id": graph_id,
            "node_type": "deliverable",
            "title": "Validation Report",
            "description": "Generate validation report",
            "status": "pending",
            "depends_on": [evidence_id],
            "workstream_id": str(uuid4())
        },
    ]

    for node in nodes:
        client.table("mission_nodes").insert(node).execute()

    # Create edges
    edges = [
        {
            "id": str(uuid4()),
            "mission_id": mission_id,
            "graph_id": graph_id,
            "from_node_id": obj_id,
            "to_node_id": task1_id,
            "edge_type": "depends_on",
        },
        {
            "id": str(uuid4()),
            "mission_id": mission_id,
            "graph_id": graph_id,
            "from_node_id": task1_id,
            "to_node_id": task2_id,
            "edge_type": "depends_on",
        },
        {
            "id": str(uuid4()),
            "mission_id": mission_id,
            "graph_id": graph_id,
            "from_node_id": task2_id,
            "to_node_id": evidence_id,
            "edge_type": "depends_on",
        },
        {
            "id": str(uuid4()),
            "mission_id": mission_id,
            "graph_id": graph_id,
            "from_node_id": evidence_id,
            "to_node_id": deliverable_id,
            "edge_type": "depends_on",
        },
    ]

    for edge in edges:
        client.table("mission_edges").insert(edge).execute()

    # Create workstream state
    client.table("workstream_states").insert({
        "workstream_id": str(uuid4()),
        "mission_id": mission_id,
        "phase": "initializing",
        "status": "running",
        "health": "healthy",
        "progress_percent": 0.0,
    }).execute()

    print(f"Created {len(nodes)} nodes, {len(edges)} edges")

    return mission_id, {
        "obj_id": obj_id,
        "task1_id": task1_id,
        "task2_id": task2_id,
        "evidence_id": evidence_id,
        "deliverable_id": deliverable_id,
    }


def start_mission(client, mission_id):
    """Start mission."""
    client.table("missions").update({
        "status": "running",
        "started_at": "now()"
    }).eq("id", mission_id).execute()

    client.table("mission_events").insert({
        "id": str(uuid4()),
        "mission_id": mission_id,
        "event_type": "mission.started",
        "node_id": None,
        "event_data": {},
        "timestamp": "now()"
    }).execute()


def get_node_info(client, node_id):
    """Get node info."""
    result = client.table("mission_nodes").select("*").eq("id", node_id).execute()
    if result.data:
        n = result.data[0]
        return n["title"], n["node_type"]
    return "Unknown", "task"


def execute_node_idempotent(executor, mission_id, node_id):
    """Execute node with idempotency check."""
    title, node_type = get_node_info(executor.supabase, node_id)

    result = executor.execute_node(
        mission_id=mission_id,
        node_id=node_id,
        node_title=title,
        node_type=node_type
    )

    if result.get("skipped"):
        print(f"  [SKIP] {title}: {result.get('reason')}")
        return False

    print(f"  [EXEC] {title} -> {result['status'].upper()}")
    print(f"         Confidence: {result['confidence']:.2f}, Dependents activated: {result['dependents_activated']}")
    return True


def test_idempotency(executor, mission_id, node_id):
    """Test that second execution is idempotent (skipped)."""
    title, node_type = get_node_info(executor.supabase, node_id)

    # First execution
    result1 = executor.execute_node(
        mission_id=mission_id,
        node_id=node_id,
        node_title=title,
        node_type=node_type
    )
    was_executed = not result1.get("skipped")

    # Try again immediately
    result2 = executor.execute_node(
        mission_id=mission_id,
        node_id=node_id,
        node_title=title,
        node_type=node_type
    )
    was_skipped = result2.get("skipped")

    if was_executed and was_skipped:
        print(f"  [PASS] Idempotency: second execution correctly skipped")
        return True
    else:
        print(f"  [FAIL] Idempotency: executed={was_executed}, skipped={was_skipped}")
        return False


def validate_no_duplicate_events(client, mission_id):
    """Check that there are no duplicate events."""
    events = client.table("mission_events").select("*").eq("mission_id", mission_id).execute()

    event_signatures = {}
    duplicates = []

    for event in events.data:
        sig = (event["node_id"], event["event_type"])
        if sig in event_signatures:
            duplicates.append((sig, event_signatures[sig], event.get("timestamp")))
        event_signatures[sig] = event.get("timestamp")

    return len(duplicates) == 0, duplicates, len(events.data), event_signatures


def validate_handoff_consistency(client, mission_id):
    """Check that all handoffs are rich format."""
    handoffs = client.table("mission_handoffs").select("*").eq("mission_id", mission_id).execute()

    minimal_count = 0
    rich_count = 0

    for handoff in handoffs.data:
        summary = handoff.get("handoff_summary", {})
        if isinstance(summary, dict):
            keys = list(summary.keys())
            if len(keys) <= 2 and "done" in keys:
                minimal_count += 1
                print(f"  [WARN] Minimal handoff found: {keys}")
            else:
                rich_count += 1

    return minimal_count == 0, rich_count, minimal_count, len(handoffs.data)


def main():
    """Run Mission 2 validation."""
    print("=" * 70)
    print("Mission 2: Hardened Execution with Idempotency Guards")
    print("=" * 70)

    client = get_supabase_client()
    executor = MissionNodeExecutor(client)
    completer = MissionCompleter(client)

    # Create mission
    mission_id, node_ids = create_mission_2_hardware()

    # Start mission
    print(f"\n[START] Mission {mission_id[:8]}...")
    start_mission(client, mission_id)

    # Execute all nodes
    print(f"\n[EXECUTE] Mission nodes...")

    results = {
        "nodes_executed": 0,
        "idempotency_passes": 0,
        "idempotency_fails": 0,
    }

    # Execute each node and test idempotency
    for key, node_id in node_ids.items():
        print(f"\n[{key.upper()}] {get_node_info(client, node_id)[0]}")

        executed = execute_node_idempotent(executor, mission_id, node_id)
        if executed:
            results["nodes_executed"] += 1
            if test_idempotency(executor, mission_id, node_id):
                results["idempotency_passes"] += 1
            else:
                results["idempotency_fails"] += 1

    # Complete mission (twice - to test idempotency)
    print(f"\n[COMPLETE] Mission")
    result1 = completer.complete_mission(mission_id, overall_score=0.92)
    print(f"  First attempt: updated={result1['updated']}, reason={result1['reason']}")

    result2 = completer.complete_mission(mission_id, overall_score=0.92)
    print(f"  Second attempt: updated={result2['updated']}, reason={result2['reason']}")

    mission_complete_idempotent = result1['updated'] and not result2['updated']

    # Validations
    print(f"\n{'='*70}")
    print("VALIDATION RESULTS")
    print(f"{'='*70}")

    # Check for duplicate events
    no_duplicates, duplicates, event_count, event_sigs = validate_no_duplicate_events(client, mission_id)
    print(f"\n[EVENTS]")
    print(f"  Total events: {event_count}")
    print(f"  Duplicate events: {len(duplicates)}")
    if duplicates:
        print(f"  Duplicates:")
        for sig, first, second in duplicates[:5]:  # Show first 5
            print(f"    {sig}: first={first}, second={second}")

    # Expected: 5 nodes × 3 (ready/started/completed) + 2 (mission events) = 17
    expected_events = (results["nodes_executed"] * 3) + 2
    print(f"  Expected events: ~{expected_events}")

    # Check handoff consistency
    all_rich, rich_count, minimal_count, handoff_count = validate_handoff_consistency(client, mission_id)
    print(f"\n[HANDOFFS]")
    print(f"  Total handoffs: {handoff_count}")
    print(f"  Rich format: {rich_count}")
    print(f"  Minimal format: {minimal_count}")

    # Final node states
    nodes_final = client.table("mission_nodes").select("*").eq("mission_id", mission_id).execute()
    print(f"\n[NODES]")
    for node in nodes_final.data:
        print(f"  {node['status']:12} | {node['title']}")

    # Summary
    print(f"\n{'='*70}")
    print("VALIDATION CHECKS")
    print(f"{'='*70}")

    checks = {
        "No duplicate events": no_duplicates,
        "All handoffs are rich format": all_rich,
        "Mission completion idempotent": mission_complete_idempotent,
        f"Node idempotency ({results['idempotency_passes']}/5 tested)": results['idempotency_passes'] == 5,
        f"Nodes executed ({results['nodes_executed']}/5 expected)": results['nodes_executed'] == 5,
        "Event count reasonable": abs(event_count - expected_events) <= 2,  # Allow small variance
    }

    for check, passed in checks.items():
        icon = "[PASS]" if passed else "[FAIL]"
        print(f"  {icon} {check}")

    all_passed = all(checks.values())
    print(f"\n{'='*70}")
    print(f"Overall: {'ALL CHECKS PASSED 🎉' if all_passed else 'SOME CHECKS FAILED'}")
    print(f"{'='*70}")

    # Save report
    report = {
        "mission_id": mission_id,
        "timestamp": datetime.now().isoformat(),
        "results": results,
        "event_count": event_count,
        "duplicate_events": len(duplicates),
        "handoff_count": handoff_count,
        "rich_handoffs": rich_count,
        "minimal_handoffs": minimal_count,
        "mission_complete_idempotent": mission_complete_idempotent,
        "checks": checks,
        "all_passed": all_passed
    }

    report_dir = "E:\\TORQ-CONSOLE\\logs\\validation_snapshots"
    os.makedirs(report_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{report_dir}\\mission_2_hardened_{timestamp}.json"

    with open(filename, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\n[OK] Report saved: {filename}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
