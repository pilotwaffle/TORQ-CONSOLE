#!/usr/bin/env python3
"""
Create Mission 1 for Phase 5.1 validation using Supabase client.

This script creates the validation mission in Supabase, which will then
be used for scheduler execution validation.
"""

import os
import sys
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client
from torq_console.settings import get_settings

def create_validation_mission():
    """Create Mission 1: Market Entry Analysis for validation."""

    settings = get_settings()
    url = settings.supabase.url
    key = settings.supabase.service_role_key

    if not url or not key:
        print("[ERROR] Supabase credentials not configured")
        print("[INFO] Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env")
        sys.exit(1)

    print(f"[INFO] Connecting to Supabase: {url}")

    client = create_client(url, key)

    # Generate IDs
    mission_id = str(uuid4())
    graph_id = str(uuid4())

    print(f"\n{'='*60}")
    print(f"Creating Validation Mission 1")
    print(f"{'='*60}")
    print(f"Mission ID: {mission_id}")
    print(f"Graph ID: {graph_id}")

    # 1. Create mission
    print("\n[STEP 1] Creating mission record...")
    mission_data = {
        "id": mission_id,
        "title": "Market Entry Analysis",
        "mission_type": "analysis",
        "objective": "Assess market opportunity for electric delivery vehicles in Southeast US",
        "context": {
            "target_market": "commercial delivery fleets",
            "region": "Southeast US",
            "time_horizon": "5 years"
        },
        "status": "draft"
    }

    result = client.table("missions").insert(mission_data).execute()

    if len(result.data) == 0:
        print("[ERROR] Failed to create mission")
        sys.exit(1)

    print(f"[OK] Mission created: {result.data[0]['title']}")

    # 2. Create mission graph
    print("\n[STEP 2] Creating mission graph...")
    graph_data = {
        "id": graph_id,
        "mission_id": mission_id,
        "version": "1.0",
        "status": "draft"
    }

    result = client.table("mission_graphs").insert(graph_data).execute()

    if len(result.data) == 0:
        print("[ERROR] Failed to create graph")
        sys.exit(1)

    print(f"[OK] Graph created: {result.data[0]['id']}")

    # 3. Create nodes (6 nodes for linear flow)
    print("\n[STEP 3] Creating mission nodes...")

    simple_nodes = [
        {
            "id": str(uuid4()),
            "node_type": "objective",
            "title": "Market Entry Assessment",
            "description": "Assess market opportunity for electric delivery vehicles",
            "depends_on": [],
            "workstream_id": str(uuid4())
        },
        {
            "id": str(uuid4()),
            "node_type": "task",
            "title": "Market Size Research",
            "description": "Research total addressable market size",
            "depends_on": [],
            "workstream_id": str(uuid4())
        },
        {
            "id": str(uuid4()),
            "node_type": "task",
            "title": "Competitor Analysis",
            "description": "Analyze competitive landscape",
            "depends_on": [],
            "workstream_id": str(uuid4())
        },
        {
            "id": str(uuid4()),
            "node_type": "task",
            "title": "Financial Projections",
            "description": "Create 5-year financial projections",
            "depends_on": [],
            "workstream_id": str(uuid4())
        },
        {
            "id": str(uuid4()),
            "node_type": "evidence",
            "title": "Evidence Synthesis",
            "description": "Synthesize all research findings",
            "depends_on": [],
            "workstream_id": str(uuid4())
        },
        {
            "id": str(uuid4()),
            "node_type": "deliverable",
            "title": "Market Entry Report",
            "description": "Final market entry recommendation report",
            "depends_on": [],
            "workstream_id": str(uuid4())
        }
    ]

    node_ids = {}
    for i, node in enumerate(simple_nodes):
        node_id = node["id"]
        node_ids[i] = node_id

        node_data = {
            "id": node_id,
            "mission_id": mission_id,
            "graph_id": graph_id,
            "node_type": node["node_type"],
            "title": node["title"],
            "description": node["description"],
            "status": "pending",
            "depends_on": [],
            "workstream_id": node["workstream_id"]
        }

        result = client.table("mission_nodes").insert(node_data).execute()

        if len(result.data) == 0:
            print(f"[ERROR] Failed to create node: {node['title']}")
            sys.exit(1)

        print(f"[OK] Node created: {result.data[0]['node_type']} - {node['title']}")

    # 4. Create edges (linear dependency chain)
    print("\n[STEP 4] Creating dependency edges...")

    edges = [
        (0, 1),  # Objective -> Market Size
        (1, 2),  # Market Size -> Competitor
        (2, 3),  # Competitor -> Financial
        (3, 4),  # Financial -> Evidence
        (4, 5),  # Evidence -> Deliverable
    ]

    for from_idx, to_idx in edges:
        edge_data = {
            "id": str(uuid4()),
            "mission_id": mission_id,
            "graph_id": graph_id,
            "from_node_id": node_ids[from_idx],
            "to_node_id": node_ids[to_idx],
            "edge_type": "depends_on"
        }

        result = client.table("mission_edges").insert(edge_data).execute()

        if len(result.data) == 0:
            print(f"[ERROR] Failed to create edge: {from_idx} -> {to_idx}")
            sys.exit(1)

        print(f"[OK] Edge created: node {from_idx} -> node {to_idx}")

    # 5. Create workstream states
    print("\n[STEP 5] Creating workstream states...")

    for node in simple_nodes:
        ws_data = {
            "workstream_id": node["workstream_id"],
            "mission_id": mission_id,
            "phase": "initializing",
            "status": "pending",
            "total_nodes": 1,
            "completed_nodes": 0
        }

        result = client.table("workstream_states").insert(ws_data).execute()

        if len(result.data) == 0:
            print(f"[ERROR] Failed to create workstream state")
            sys.exit(1)

    print(f"[OK] Created {len(simple_nodes)} workstream states")

    # 6. Update mission status to planned
    print("\n[STEP 6] Updating mission status...")

    result = client.table("missions").update({
        "status": "planned",
        "updated_at": "now()"
    }).eq("id", mission_id).execute()

    print(f"[OK] Mission status updated to: planned")

    # Summary
    print(f"\n{'='*60}")
    print(f"Validation Mission 1 Created Successfully")
    print(f"{'='*60}")
    print(f"Mission ID: {mission_id}")
    print(f"Title: Market Entry Analysis")
    print(f"Type: analysis")
    print(f"Nodes: 6")
    print(f"Edges: 5 (linear dependency chain)")
    print(f"Status: planned")
    print(f"{'='*60}")

    print(f"\nNext steps:")
    print(f"1. Start backend: python -m torq_console.cli serve")
    print(f"2. Start mission via API: POST /api/missions/{mission_id}/start")
    print(f"3. Monitor execution and capture telemetry")

    return mission_id


if __name__ == "__main__":
    try:
        mission_id = create_validation_mission()
        print(f"\nMission ID for validation: {mission_id}")

        # Write to file for reference
        ref_file = "E:\\TORQ-CONSOLE\\logs\\validation_mission_id.txt"
        os.makedirs(os.path.dirname(ref_file), exist_ok=True)
        with open(ref_file, "w") as f:
            f.write(mission_id)
        print(f"Mission ID saved to: {ref_file}")

    except Exception as e:
        print(f"\n[ERROR] Mission creation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
