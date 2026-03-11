#!/usr/bin/env python3
"""
Detect failure patterns in Phase 5.1 execution.

Runs queries to detect the 5 common failure patterns.
"""

import os
import sys
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client
from torq_console.settings import get_settings

# Mission ID
MISSION_ID = "5be233f2-632c-4b2c-8a47-cb1c2c69a762"


def get_supabase_client():
    """Get Supabase client."""
    settings = get_settings()
    url = settings.supabase.url
    key = settings.supabase.service_role_key

    if not url or not key:
        raise ValueError("Supabase credentials not configured")

    return create_client(url, key)


def detect_pattern_1_dependency_leakage(client, mission_id):
    """
    Pattern 1: Dependency Leakage
    Nodes running before their dependencies are complete.
    """
    print("\n[PATTERN 1] Dependency Leakage")

    # Get all nodes and edges
    nodes_result = client.table("mission_nodes").select("*").eq("mission_id", mission_id).execute()
    edges_result = client.table("mission_edges").select("*").eq("mission_id", mission_id).execute()

    nodes = {n['id']: n for n in nodes_result.data} if nodes_result.data else {}
    edges = edges_result.data if edges_result.data else []

    # Build dependency map
    dependencies = {}
    for edge in edges:
        if edge['edge_type'] == 'depends_on':
            to_id = edge['to_node_id']
            from_id = edge['from_node_id']
            if to_id not in dependencies:
                dependencies[to_id] = []
            dependencies[to_id].append(from_id)

    # Check for leakage: running nodes whose dependencies aren't complete
    violations = []

    for node_id, deps in dependencies.items():
        if node_id not in nodes:
            continue

        node = nodes[node_id]

        # Check if node is running
        if node['status'] == 'running':
            # Check if all dependencies are complete
            for dep_id in deps:
                if dep_id in nodes:
                    dep_node = nodes[dep_id]
                    if dep_node['status'] not in ['completed', 'skipped']:
                        violations.append({
                            "node": node['title'],
                            "node_status": node['status'],
                            "dependency": dep_node['title'],
                            "dependency_status": dep_node['status']
                        })

    print(f"  Violations: {len(violations)}")
    if violations:
        print("  [FAIL] Dependency leakage detected!")
        for v in violations:
            print(f"    - {v['node']} ({v['node_status']}) depends on {v['dependency']} ({v['dependency_status']})")
    else:
        print("  [PASS] No dependency leakage")

    return {
        "pattern": "Dependency Leakage",
        "violations": len(violations),
        "threshold": "Must be 0",
        "status": "CLEAR" if len(violations) == 0 else "DETECTED",
        "details": violations
    }


def detect_pattern_2_event_duplication(client, mission_id):
    """
    Pattern 2: Event Duplication
    Multiple identical events for the same state change.
    """
    print("\n[PATTERN 2] Event Duplication")

    events_result = client.table("mission_events").select("*").eq("mission_id", mission_id).execute()
    events = events_result.data if events_result.data else []

    # Group by event_type and node_id to find duplicates
    event_groups = {}
    for event in events:
        key = (event['event_type'], event.get('node_id', ''))
        if key not in event_groups:
            event_groups[key] = []
        event_groups[key].append(event)

    # Find groups with more than 1 event
    duplicates = []
    for key, group in event_groups.items():
        if len(group) > 1:
            # Check if they're truly duplicates (similar timestamp)
            if len(group) > 1:
                timestamps = [e['timestamp'] for e in group]
                duplicates.append({
                    "event_type": key[0],
                    "node_id": key[1],
                    "count": len(group),
                    "timestamps": timestamps
                })

    print(f"  Total events: {len(events)}")
    print(f"  Duplicate groups: {len(duplicates)}")

    if duplicates:
        print("  [FAIL] Event duplication detected!")
        for d in duplicates:
            print(f"    - {d['event_type']}: {d['count']} events")
    else:
        print("  [PASS] No event duplication")

    return {
        "pattern": "Event Duplication",
        "violations": len(duplicates),
        "threshold": "Must be 0",
        "status": "CLEAR" if len(duplicates) == 0 else "DETECTED",
        "details": duplicates
    }


def detect_pattern_3_handoff_incompleteness(client, mission_id):
    """
    Pattern 3: Handoff Incompleteness
    Handoffs missing confidence, summary, or artifacts.
    """
    print("\n[PATTERN 3] Handoff Incompleteness")

    handoffs_result = client.table("mission_handoffs").select("*").eq("mission_id", mission_id).execute()
    handoffs = handoffs_result.data if handoffs_result.data else []

    violations = []

    for handoff in handoffs:
        issues = []

        # Check confidence
        if handoff.get('confidence') is None or handoff['confidence'] < 0 or handoff['confidence'] > 1:
            issues.append("missing/invalid confidence")

        # Check handoff_summary
        summary = handoff.get('handoff_summary', {})
        if not summary or summary == {}:
            issues.append("missing handoff_summary")

        # Check for key fields in summary
        if summary:
            if not any(k in summary for k in ['objective_completed', 'output_summary', 'key_findings']):
                issues.append("incomplete handoff_summary")

        # Check artifacts
        artifacts = handoff.get('artifacts', {})
        if not artifacts or artifacts == {}:
            issues.append("missing artifacts")

        if issues:
            violations.append({
                "handoff_id": handoff['id'],
                "from_node": handoff.get('from_node_id'),
                "issues": issues
            })

    print(f"  Total handoffs: {len(handoffs)}")
    print(f"  Incomplete handoffs: {len(violations)}")

    if violations:
        print("  [FAIL] Incomplete handoffs detected!")
        for v in violations:
            print(f"    - Handoff {v['handoff_id'][:8]}...: {', '.join(v['issues'])}")
    else:
        print("  [PASS] All handoffs complete")

    return {
        "pattern": "Handoff Incompleteness",
        "violations": len(violations),
        "threshold": "Must be 0",
        "status": "CLEAR" if len(violations) == 0 else "DETECTED",
        "details": violations
    }


def detect_pattern_4_phase_skipping(client, mission_id):
    """
    Pattern 4: Workstream Phase Skipping
    Workstreams jumping phases without completing intermediate phases.
    """
    print("\n[PATTERN 4] Workstream Phase Skipping")

    workstreams_result = client.table("workstream_states").select("*").eq("mission_id", mission_id).execute()
    workstreams = workstreams_result.data if workstreams_result.data else []

    violations = []

    valid_phases = [
        'initializing', 'discovery', 'analysis', 'synthesis',
        'review', 'finalizing', 'blocked', 'complete'
    ]

    for ws in workstreams:
        phase = ws.get('phase')
        status = ws.get('status')

        # Check for invalid phase transitions
        # If status is 'running' but phase is still 'initializing', that's OK
        # But if phase is 'synthesis' with no completed nodes, that's suspicious

        if phase not in valid_phases:
            violations.append({
                "workstream_id": ws['workstream_id'],
                "issue": f"invalid phase: {phase}",
                "status": status
            })

        # Check if workstream is in a later phase with zero completed nodes
        if phase in ['synthesis', 'review', 'finalizing', 'complete']:
            if ws.get('completed_nodes', 0) == 0:
                violations.append({
                    "workstream_id": ws['workstream_id'],
                    "issue": f"phase '{phase}' with 0 completed nodes",
                    "status": status
                })

    print(f"  Total workstreams: {len(workstreams)}")
    print(f"  Phase violations: {len(violations)}")

    if violations:
        print("  [FAIL] Phase skipping detected!")
        for v in violations:
            print(f"    - {v['workstream_id'][:8]}...: {v['issue']}")
    else:
        print("  [PASS] No phase skipping")

    return {
        "pattern": "Workstream Phase Skipping",
        "violations": len(violations),
        "threshold": "Must be 0",
        "status": "CLEAR" if len(violations) == 0 else "DETECTED",
        "details": violations
    }


def detect_pattern_5_memory_overload(client, mission_id):
    """
    Pattern 5: Memory Injection Overload
    Too many memories injected into a single mission/node.
    """
    print("\n[PATTERN 5] Memory Injection Overload")

    # Check mission-level memory injection
    mission_result = client.table("missions").select("*").eq("id", mission_id).execute()
    mission = mission_result.data[0] if mission_result.data else {}

    memory_ids = mission.get('injected_memory_ids', [])
    mission_memory_count = len(memory_ids)

    # Also check nodes
    nodes_result = client.table("mission_nodes").select("*").eq("mission_id", mission_id).execute()
    nodes = nodes_result.data if nodes_result.data else []

    violations = []

    # Threshold: more than 10 memories per mission/node is overload
    THRESHOLD = 10

    if mission_memory_count > THRESHOLD:
        violations.append({
            "scope": "mission",
            "count": mission_memory_count,
            "threshold": THRESHOLD
        })

    for node in nodes:
        # Check if node has injected_memory_ids field
        node_memories = node.get('injected_memory_ids', [])
        if isinstance(node_memories, list) and len(node_memories) > THRESHOLD:
            violations.append({
                "scope": "node",
                "node_id": node['id'],
                "node_title": node['title'],
                "count": len(node_memories),
                "threshold": THRESHOLD
            })

    print(f"  Mission memories: {mission_memory_count}")
    print(f"  Threshold: {THRESHOLD}")
    print(f"  Violations: {len(violations)}")

    if violations:
        print("  [FAIL] Memory overload detected!")
        for v in violations:
            if v['scope'] == 'mission':
                print(f"    - Mission: {v['count']} memories (threshold: {v['threshold']})")
            else:
                print(f"    - Node '{v['node_title']}': {v['count']} memories (threshold: {v['threshold']})")
    else:
        print("  [PASS] No memory overload")

    return {
        "pattern": "Memory Injection Overload",
        "violations": len(violations),
        "threshold": f"Must be <={THRESHOLD}",
        "status": "CLEAR" if len(violations) == 0 else "DETECTED",
        "details": violations
    }


def main():
    """Run all failure pattern detection."""
    print("=" * 60)
    print("Phase 5.1 Failure Pattern Detection")
    print("=" * 60)
    print(f"Mission ID: {MISSION_ID}")
    print(f"Time: {datetime.now().isoformat()}")

    client = get_supabase_client()

    # Run all pattern detections
    results = []

    results.append(detect_pattern_1_dependency_leakage(client, MISSION_ID))
    results.append(detect_pattern_2_event_duplication(client, MISSION_ID))
    results.append(detect_pattern_3_handoff_incompleteness(client, MISSION_ID))
    results.append(detect_pattern_4_phase_skipping(client, MISSION_ID))
    results.append(detect_pattern_5_memory_overload(client, MISSION_ID))

    # Summary
    print(f"\n{'='*60}")
    print("FAILURE PATTERN SUMMARY")
    print(f"{'='*60}")

    total_violations = sum(r['violations'] for r in results)

    print(f"\n| Pattern | Status | Violations | Threshold |")
    print(f"|---------|--------|------------|-----------|")
    for r in results:
        status_icon = "[PASS]" if r['status'] == "CLEAR" else "[FAIL]"
        print(f"| {r['pattern']} | {status_icon} {r['status']} | {r['violations']} | {r['threshold']} |")

    print(f"\nTotal violations: {total_violations}")

    # Save results
    snapshot_dir = "E:\\TORQ-CONSOLE\\logs\\validation_snapshots"
    os.makedirs(snapshot_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{snapshot_dir}\\failure_patterns_{MISSION_ID[:8]}_{timestamp}.json"

    with open(filename, "w") as f:
        json.dump({
            "mission_id": MISSION_ID,
            "timestamp": datetime.now().isoformat(),
            "total_violations": total_violations,
            "patterns": results
        }, f, indent=2)

    print(f"\nResults saved: {filename}")

    if total_violations == 0:
        print("\n[OK] All failure patterns CLEAR")
        return 0
    else:
        print(f"\n[WARN] {total_violations} failure pattern(s) DETECTED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
