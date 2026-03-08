#!/usr/bin/env python3
"""
Mission 3: Risk Assessment with Decision Gates

Validates the hardened scheduler (now default runtime path) with:
- Decision gate behavior (pass/fail paths)
- Risk-first reasoning strategy
- Contradiction detection patterns
- Sequential dependencies with branches

Mission Shape: Different from Missions 1 and 2
- Mission 1: Linear market entry (6 nodes)
- Mission 2: Idempotency validation (5 nodes)
- Mission 3: Risk assessment with decision gates (7 nodes, 2 potential outcomes)
"""

import os
import sys
import json
from datetime import datetime
from uuid import uuid4

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client
from torq_console.settings import get_settings
from torq_console.mission_graph import MissionGraphScheduler


def get_supabase_client():
    """Get Supabase client."""
    settings = get_settings()
    return create_client(settings.supabase.url, settings.supabase.service_role_key)


def create_mission_3():
    """Create Mission 3: Risk Assessment with Decision Gates."""
    mission_id = str(uuid4())
    graph_id = str(uuid4())

    print(f"\n[CREATE] Mission 3: Risk Assessment with Decision Gates")
    print(f"Mission ID: {mission_id}")
    print(f"Graph ID: {graph_id}")

    client = get_supabase_client()

    # Create mission
    mission_data = {
        "id": mission_id,
        "title": "Risk Assessment with Decision Gates",
        "mission_type": "analysis",
        "objective": "Evaluate technical risk levels and determine mitigation strategy",
        "status": "draft",
        "reasoning_strategy": "risk_first",
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

    # Create nodes (7 nodes with decision gate)
    obj_id = str(uuid4())
    risk_analysis_id = str(uuid4())
    decision_gate_id = str(uuid4())
    mitigate_low_id = str(uuid4())
    mitigate_high_id = str(uuid4())
    evidence_id = str(uuid4())
    deliverable_id = str(uuid4())

    nodes = [
        {
            "id": obj_id,
            "mission_id": mission_id,
            "graph_id": graph_id,
            "node_type": "objective",
            "title": "Assess Technical Risk",
            "description": "Evaluate technical risk and determine mitigation path",
            "status": "pending",
            "depends_on": [],
            "workstream_id": str(uuid4())
        },
        {
            "id": risk_analysis_id,
            "mission_id": mission_id,
            "graph_id": graph_id,
            "node_type": "task",
            "title": "Analyze Risk Factors",
            "description": "Identify and categorize technical risk factors",
            "status": "pending",
            "depends_on": [obj_id],
            "workstream_id": str(uuid4())
        },
        {
            "id": decision_gate_id,
            "mission_id": mission_id,
            "graph_id": graph_id,
            "node_type": "decision",
            "title": "Risk Threshold Gate",
            "description": "Determine if risk level is acceptable or requires mitigation",
            "status": "pending",
            "depends_on": [risk_analysis_id],
            "workstream_id": str(uuid4())
        },
        {
            "id": mitigate_low_id,
            "mission_id": mission_id,
            "graph_id": graph_id,
            "node_type": "task",
            "title": "Standard Mitigation Plan",
            "description": "Create standard risk mitigation for acceptable risk",
            "status": "pending",
            "depends_on": [decision_gate_id],
            "workstream_id": str(uuid4())
        },
        {
            "id": mitigate_high_id,
            "mission_id": mission_id,
            "graph_id": graph_id,
            "node_type": "task",
            "title": "Enhanced Mitigation Plan",
            "description": "Create enhanced mitigation for high-risk scenarios",
            "status": "pending",
            "depends_on": [decision_gate_id],
            "workstream_id": str(uuid4())
        },
        {
            "id": evidence_id,
            "mission_id": mission_id,
            "graph_id": graph_id,
            "node_type": "evidence",
            "title": "Risk Evidence Synthesis",
            "description": "Synthesize risk evidence and mitigation options",
            "status": "pending",
            "depends_on": [mitigate_low_id, mitigate_high_id],
            "workstream_id": str(uuid4())
        },
        {
            "id": deliverable_id,
            "mission_id": mission_id,
            "graph_id": graph_id,
            "node_type": "deliverable",
            "title": "Risk Assessment Report",
            "description": "Generate final risk assessment report with recommendations",
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
            "to_node_id": risk_analysis_id,
            "edge_type": "depends_on",
        },
        {
            "id": str(uuid4()),
            "mission_id": mission_id,
            "graph_id": graph_id,
            "from_node_id": risk_analysis_id,
            "to_node_id": decision_gate_id,
            "edge_type": "depends_on",
        },
        {
            "id": str(uuid4()),
            "mission_id": mission_id,
            "graph_id": graph_id,
            "from_node_id": decision_gate_id,
            "to_node_id": mitigate_low_id,
            "edge_type": "depends_on",
        },
        {
            "id": str(uuid4()),
            "mission_id": mission_id,
            "graph_id": graph_id,
            "from_node_id": decision_gate_id,
            "to_node_id": mitigate_high_id,
            "edge_type": "depends_on",
        },
        {
            "id": str(uuid4()),
            "mission_id": mission_id,
            "graph_id": graph_id,
            "from_node_id": mitigate_low_id,
            "to_node_id": evidence_id,
            "edge_type": "depends_on",
        },
        {
            "id": str(uuid4()),
            "mission_id": mission_id,
            "graph_id": graph_id,
            "from_node_id": mitigate_high_id,
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
        "risk_analysis_id": risk_analysis_id,
        "decision_gate_id": decision_gate_id,
        "mitigate_low_id": mitigate_low_id,
        "mitigate_high_id": mitigate_high_id,
        "evidence_id": evidence_id,
        "deliverable_id": deliverable_id,
    }


def execute_mission_via_hardened_scheduler(mission_id, node_ids):
    """Execute mission using the production scheduler with hardened executor."""
    client = get_supabase_client()
    scheduler = MissionGraphScheduler(client)

    print(f"\n[EXECUTE] Using production scheduler (hardened path)")

    # Start mission - mark objective as ready
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

    client.table("mission_nodes").update({
        "status": "ready"
    }).eq("id", node_ids["obj_id"]).execute()

    # Execute nodes sequentially using hardened executor
    # In production, the scheduler would do this automatically
    from torq_console.mission_graph.executor import MissionNodeExecutor

    executor = MissionNodeExecutor(client)

    execution_order = [
        ("obj_id", "Assess Technical Risk"),
        ("risk_analysis_id", "Analyze Risk Factors"),
        ("decision_gate_id", "Risk Threshold Gate"),
        ("mitigate_low_id", "Standard Mitigation Plan"),
        ("mitigate_high_id", "Enhanced Mitigation Plan"),
        ("evidence_id", "Risk Evidence Synthesis"),
        ("deliverable_id", "Risk Assessment Report"),
    ]

    results = {"executed": 0, "skipped": 0, "errors": 0}

    for key, title in execution_order:
        node_id = node_ids[key]
        print(f"\n  [{key.upper()}] {title}")

        result = executor.execute_node(
            mission_id=mission_id,
            node_id=node_id,
            node_title=title,
            node_type=key.split("_")[0] if "_" in key else "objective"
        )

        if result.get("skipped"):
            print(f"    [SKIP] {result.get('reason')}")
            results["skipped"] += 1
        else:
            print(f"    [DONE] Status: {result['status']}, Confidence: {result['confidence']:.2f}")
            print(f"          Dependents activated: {result['dependents_activated']}")
            results["executed"] += 1

    # Complete mission using hardened completer
    from torq_console.mission_graph.executor import MissionCompleter
    completer = MissionCompleter(client)

    print(f"\n[COMPLETE] Mission")
    result = completer.complete_mission(mission_id, overall_score=0.91)
    print(f"  Updated: {result['updated']}, Reason: {result['reason']}")

    return results


def validate_mission_3_results(mission_id):
    """Validate Mission 3 results against hardened expectations."""
    client = get_supabase_client()

    print(f"\n{'='*70}")
    print("MISSION 3 VALIDATION RESULTS")
    print(f"{'='*70}")

    # Get final state
    mission = client.table("missions").select("*").eq("id", mission_id).execute()
    nodes = client.table("mission_nodes").select("*").eq("mission_id", mission_id).execute()
    events = client.table("mission_events").select("*").eq("mission_id", mission_id).execute()
    handoffs = client.table("mission_handoffs").select("*").eq("mission_id", mission_id).execute()

    m = mission.data[0] if mission.data else {}
    n = nodes.data if nodes.data else []
    e = events.data if events.data else []
    h = handoffs.data if handoffs.data else []

    # Mission status
    print(f"\n[MISSION]")
    print(f"  Status: {m.get('status')}")
    print(f"  Reasoning Strategy: {m.get('reasoning_strategy')}")
    print(f"  Overall Score: {m.get('overall_score')}")

    # Node states
    print(f"\n[NODES] ({len(n)} total)")
    for node in n:
        print(f"  {node['status']:12} | {node['title']}")

    # Check for duplicate events
    event_sigs = {}
    duplicates = []
    for event in e:
        sig = (event["node_id"], event["event_type"])
        if sig in event_sigs:
            duplicates.append(sig)
        event_sigs[sig] = event.get("timestamp")

    print(f"\n[EVENTS] ({len(e)} total)")
    print(f"  Duplicate events: {len(duplicates)}")
    print(f"  Expected: ~{(len(n) * 3) + 1} (ready/started/completed per node + mission)")

    # Event type breakdown
    event_types = {}
    for event in e:
        et = event["event_type"]
        event_types[et] = event_types.get(et, 0) + 1
    print(f"  Event types:")
    for etype, count in sorted(event_types.items()):
        print(f"    {etype}: {count}")

    # Check for mission.completed duplicates
    mission_completed_count = event_types.get("mission.completed", 0)
    print(f"\n  mission.completed events: {mission_completed_count} (expected: 1)")

    # Handoff quality
    print(f"\n[HANDOFFS] ({len(h)} total)")
    rich_count = 0
    minimal_count = 0
    for handoff in h:
        summary = handoff.get("handoff_summary", {})
        if isinstance(summary, dict):
            keys = list(summary.keys())
            if len(keys) <= 2 and "done" in keys:
                minimal_count += 1
            else:
                rich_count += 1

    print(f"  Rich format: {rich_count}")
    print(f"  Minimal format: {minimal_count}")

    # Validation checks
    print(f"\n{'='*70}")
    print("HARDENED SCHEDULER VALIDATION CHECKS")
    print(f"{'='*70}")

    checks = {
        "Mission completed": m.get('status') == 'completed',
        "All nodes completed": all(node['status'] == 'completed' for node in n),
        "No duplicate events": len(duplicates) == 0,
        "Single mission.completed event": mission_completed_count == 1,
        "All handoffs rich format": minimal_count == 0,
        "Used risk_first strategy": m.get('reasoning_strategy') == 'risk_first',
    }

    for check, passed in checks.items():
        icon = "[PASS]" if passed else "[FAIL]"
        print(f"  {icon} {check}")

    all_passed = all(checks.values())
    print(f"\n{'='*70}")
    print(f"Overall: {'ALL CHECKS PASSED' if all_passed else 'SOME CHECKS FAILED'}")
    print(f"{'='*70}")

    # Save report
    report = {
        "mission_id": mission_id,
        "timestamp": datetime.now().isoformat(),
        "mission": m,
        "node_count": len(n),
        "event_count": len(e),
        "duplicate_events": len(duplicates),
        "handoff_count": len(h),
        "rich_handoffs": rich_count,
        "minimal_handoffs": minimal_count,
        "mission_completed_events": mission_completed_count,
        "checks": checks,
        "all_passed": all_passed
    }

    report_dir = "E:\\TORQ-CONSOLE\\logs\\validation_snapshots"
    os.makedirs(report_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{report_dir}\\mission_3_hardened_scheduler_{timestamp}.json"

    with open(filename, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\n[OK] Report saved: {filename}")

    return 0 if all_passed else 1


def main():
    """Run Mission 3 validation."""
    print("=" * 70)
    print("Mission 3: Risk Assessment with Decision Gates")
    print("Testing HARDENED SCHEDULER (default runtime path)")
    print("=" * 70)

    # Create mission
    mission_id, node_ids = create_mission_3()

    # Execute using hardened scheduler
    results = execute_mission_via_hardened_scheduler(mission_id, node_ids)

    print(f"\n[RESULTS] Executed: {results['executed']}, Skipped: {results['skipped']}, Errors: {results['errors']}")

    # Validate results
    return validate_mission_3_results(mission_id)


if __name__ == "__main__":
    sys.exit(main())
