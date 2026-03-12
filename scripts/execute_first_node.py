#!/usr/bin/env python3
"""
Execute the first ready node for Phase 5.1 validation.

This simulates the execution of the objective node and captures:
- Node state transitions
- Emitted events
- Generated handoff
- Workstream state changes
- Downstream readiness updates
"""

import os
import sys
import json
from datetime import datetime
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client
from torq_console.settings import get_settings

# Mission ID
MISSION_ID = "5be233f2-632c-4b2c-8a47-cb1c2c69a762"

# First ready node (objective) - get this from snapshot
OBJECTIVE_NODE_ID = "6523441d-89d4-4352-9d1d-7cc10ca216d9"


def get_supabase_client():
    """Get Supabase client."""
    settings = get_settings()
    url = settings.supabase.url
    key = settings.supabase.service_role_key

    if not url or not key:
        raise ValueError("Supabase credentials not configured")

    return create_client(url, key)


def emit_event(client, mission_id, event_type, node_id, event_data):
    """Emit a mission event."""
    event = {
        "id": str(uuid4()),
        "mission_id": mission_id,
        "event_type": event_type,
        "node_id": node_id,
        "event_data": event_data,
        "metadata": {},
        "timestamp": "now()"
    }
    client.table("mission_events").insert(event).execute()
    return event


def create_handoff(client, mission_id, from_node, to_nodes):
    """Create a structured handoff packet."""
    handoff = {
        "id": str(uuid4()),
        "mission_id": mission_id,
        "from_node_id": from_node,
        "to_node_id": to_nodes[0] if to_nodes else None,
        "from_agent_type": "objective_agent",
        "to_agent_type": "task_agent",
        "handoff_summary": {
            "objective_completed": "Market entry assessment objectives defined",
            "output_summary": "Scope, region, and time horizon established",
            "key_findings": [
                "Target market: commercial delivery fleets",
                "Region: Southeast US",
                "Time horizon: 5 years"
            ],
            "recommendations": ["Proceed with market size research"]
        },
        "confidence": 0.85,
        "confidence_basis": "Clear scope and well-defined parameters",
        "unresolved_questions": [],
        "assumptions_made": [],
        "limitations": [],
        "risks": [],
        "severity_indicators": [],
        "artifacts": {
            "scope_defined": True,
            "context_established": True
        },
        "workspace_entries": [],
        "recommended_consumers": ["Market Size Research"],
        "required_next_actions": ["Research total addressable market"],
        "status": "delivered",
        "delivery_attempts": 1
    }
    client.table("mission_handoffs").insert(handoff).execute()
    return handoff


def execute_node(client, mission_id, node_id):
    """
    Execute a node:
    1. Change status to running
    2. Set started_at
    3. Emit node.started event
    4. Simulate work
    5. Change status to completed
    6. Set completed_at and output_data
    7. Emit node.completed event
    8. Create handoff if applicable
    9. Update dependent nodes to ready
    10. Update workstream
    """
    print(f"\n[EXECUTE] Executing node: {node_id[:8]}...")

    # Step 1: Mark as running
    print("  [1/8] Marking node as running...")
    client.table("mission_nodes").update({
        "status": "running",
        "started_at": "now()",
        "updated_at": "now()"
    }).eq("id", node_id).execute()

    emit_event(client, mission_id, "node.started", node_id, {
        "previous_status": "ready",
        "new_status": "running"
    })

    # Step 2: Simulate work (objectives are instant)
    print("  [2/8] Simulating work...")
    import time
    time.sleep(0.1)

    # Step 3: Mark as completed
    print("  [3/8] Marking node as completed...")
    output_data = {
        "scope": {
            "target_market": "commercial delivery fleets",
            "region": "Southeast US",
            "time_horizon": "5 years"
        },
        "success_criteria": ["Market viability assessed", "ROI projected"]
    }

    client.table("mission_nodes").update({
        "status": "completed",
        "completed_at": "now()",
        "output_data": output_data,
        "confidence_score": 0.85,
        "updated_at": "now()"
    }).eq("id", node_id).execute()

    emit_event(client, mission_id, "node.completed", node_id, {
        "previous_status": "running",
        "new_status": "completed",
        "output_produced": True
    })

    # Step 4: Create handoff
    print("  [4/8] Creating handoff...")
    handoff = create_handoff(client, mission_id, node_id, [])

    # Step 5: Find dependent nodes
    print("  [5/8] Finding dependent nodes...")
    edges_result = client.table("mission_edges").select("*").eq("from_node_id", node_id).execute()
    dependent_node_ids = [e['to_node_id'] for e in edges_result.data] if edges_result.data else []

    print(f"  Found {len(dependent_node_ids)} dependent node(s)")

    # Step 6: Update dependent nodes to ready
    print("  [6/8] Updating dependent nodes to ready...")
    for dep_id in dependent_node_ids:
        client.table("mission_nodes").update({
            "status": "ready",
            "updated_at": "now()"
        }).eq("id", dep_id).execute()

        emit_event(client, mission_id, "node.ready", dep_id, {
            "reason": "dependencies_satisfied",
            "dependency_unblocked": node_id
        })

    # Step 7: Update workstream
    print("  [7/8] Updating workstream...")
    # Get the workstream for this node
    node_result = client.table("mission_nodes").select("*").eq("id", node_id).execute()
    if node_result.data:
        ws_id = node_result.data[0].get('workstream_id')
        if ws_id:
            client.table("workstream_states").update({
                "phase": "discovery",
                "status": "running",
                "completed_nodes": 1,
                "progress_percent": 16.67,  # 1/6 completed
                "updated_at": "now()"
            }).eq("workstream_id", ws_id).execute()

    # Step 8: Check if mission should complete
    print("  [8/8] Checking mission status...")
    nodes_result = client.table("mission_nodes").select("*").eq("mission_id", mission_id).execute()
    all_nodes = nodes_result.data if nodes_result.data else []
    completed = sum(1 for n in all_nodes if n['status'] == 'completed')

    if completed == len(all_nodes):
        client.table("missions").update({
            "status": "completed",
            "completed_at": "now()",
            "updated_at": "now()"
        }).eq("id", mission_id).execute()
        emit_event(client, mission_id, "mission.completed", None, {
            "total_nodes": len(all_nodes),
            "nodes_completed": completed
        })
    else:
        emit_event(client, mission_id, "mission.progress", None, {
            "total_nodes": len(all_nodes),
            "nodes_completed": completed,
            "progress_percent": round(completed / len(all_nodes) * 100, 2)
        })

    return {
        "node_id": node_id,
        "dependent_nodes": dependent_node_ids,
        "handoff_id": handoff['id'],
        "events_emitted": 3  # node.started, node.completed, node.ready (per dependent)
    }


def capture_execution_results(client, mission_id):
    """Capture all 4 views after execution."""
    print("\n[CAPTURE] Collecting execution results...")

    mission = client.table("missions").select("*").eq("id", mission_id).execute()
    nodes = client.table("mission_nodes").select("*").eq("mission_id", mission_id).execute()
    events = client.table("mission_events").select("*").eq("mission_id", mission_id).order("timestamp", desc=True).execute()
    handoffs = client.table("mission_handoffs").select("*").eq("mission_id", mission_id).execute()
    workstreams = client.table("workstream_states").select("*").eq("mission_id", mission_id).execute()

    return {
        "mission": mission.data[0] if mission.data else None,
        "nodes": nodes.data if nodes.data else [],
        "events": events.data if events.data else [],
        "handoffs": handoffs.data if handoffs.data else [],
        "workstreams": workstreams.data if workstreams.data else []
    }


def main():
    """Execute first node and validate results."""
    print("=" * 70)
    print("Phase 5.1 Validation: First Node Execution")
    print("=" * 70)
    print(f"Mission ID: {MISSION_ID}")
    print(f"Node to Execute: {OBJECTIVE_NODE_ID} (objective)")
    print(f"Time: {datetime.now().isoformat()}")

    client = get_supabase_client()

    # Capture before state
    print("\n[BEFORE] Current state:")
    before_nodes = client.table("mission_nodes").select("*").eq("mission_id", MISSION_ID).execute()
    for node in before_nodes.data:
        print(f"  {node['status']:10} | {node['node_type']:12} | {node['title']}")

    # Execute the node
    result = execute_node(client, MISSION_ID, OBJECTIVE_NODE_ID)

    # Capture after state
    print("\n[AFTER] Execution results:")
    after = capture_execution_results(client, MISSION_ID)

    # Save snapshot
    snapshot_dir = "E:\\TORQ-CONSOLE\\logs\\validation_snapshots"
    os.makedirs(snapshot_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{snapshot_dir}\\mission_{MISSION_ID[:8]}_post_execution_{timestamp}.json"

    with open(filename, "w") as f:
        json.dump(after, f, indent=2, default=str)

    print(f"\n[OK] Snapshot saved: {filename}")

    # Validation checks
    print(f"\n{'='*70}")
    print("VALIDATION RESULTS")
    print(f"{'='*70}")

    # B1: Dependency enforcement
    print("\n[B1] Dependency Enforcement:")
    completed_node = next((n for n in after['nodes'] if n['id'] == OBJECTIVE_NODE_ID), None)
    ready_after = [n for n in after['nodes'] if n['status'] == 'ready']
    still_pending = [n for n in after['nodes'] if n['status'] == 'pending']

    print(f"  - Completed node: {completed_node['title'] if completed_node else 'NOT FOUND'}")
    print(f"  - Nodes ready (should be 1): {len(ready_after)}")
    print(f"  - Nodes still pending (should be 4): {len(still_pending)}")

    b1_pass = (
        completed_node and completed_node['status'] == 'completed' and
        len(ready_after) == 1 and
        len(still_pending) == 4
    )
    print(f"  B1 Result: {'PASS' if b1_pass else 'FAIL'}")

    # C1/C2: Event generation
    print("\n[C1/C2] Event Generation:")
    print(f"  - Total events: {len(after['events'])}")
    event_types = [e['event_type'] for e in after['events']]
    print(f"  - Event types: {event_types}")

    c1_pass = (
        'node.started' in event_types and
        'node.completed' in event_types and
        len(after['events']) >= 3
    )
    print(f"  C1/C2 Result: {'PASS' if c1_pass else 'FAIL'}")

    # D1/D2: Handoff completeness
    print("\n[D1/D2] Handoff Completeness:")
    print(f"  - Total handoffs: {len(after['handoffs'])}")

    if after['handoffs']:
        h = after['handoffs'][0]
        print(f"  - Handoff from: {h['from_node_id'][:8]}...")
        print(f"  - Confidence: {h['confidence']}")
        print(f"  - Has summary: {bool(h.get('handoff_summary'))}")
        print(f"  - Has artifacts: {bool(h.get('artifacts'))}")

        d1_pass = (
            h.get('confidence', 0) > 0 and
            h.get('handoff_summary') and
            h.get('artifacts')
        )
        print(f"  D1/D2 Result: {'PASS' if d1_pass else 'FAIL'}")
    else:
        d1_pass = False
        print(f"  D1/D2 Result: FAIL (no handoffs created)")

    # Workstream update
    print("\n[WS] Workstream State:")
    ws_updated = [w for w in after['workstreams'] if w['phase'] != 'initializing']
    if ws_updated:
        ws = ws_updated[0]
        print(f"  - Workstream phase: {ws['phase']}")
        print(f"  - Completed nodes: {ws['completed_nodes']}")
        print(f"  - Progress: {ws['progress_percent']}%")
    else:
        print(f"  No workstreams updated")

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"B1 Dependency Enforcement: {'PASS' if b1_pass else 'FAIL'}")
    print(f"C1/C2 Event Generation:   {'PASS' if c1_pass else 'FAIL'}")
    print(f"D1/D2 Handoff Completeness: {'PASS' if d1_pass else 'FAIL'}")

    all_pass = b1_pass and c1_pass and d1_pass
    print(f"\nOverall: {'ALL CHECKS PASSED' if all_pass else 'SOME CHECKS FAILED'}")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
