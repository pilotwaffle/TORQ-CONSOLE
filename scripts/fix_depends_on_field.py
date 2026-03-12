#!/usr/bin/env python3
"""
Fix the depends_on field in mission_nodes to match mission_edges.

This script populates the denormalized depends_on field from the
edges table for self-documenting snapshots.
"""

import os
import sys

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


def fix_depends_on(client, mission_id):
    """Populate depends_on field from mission_edges."""
    print(f"[INFO] Fixing depends_on field for mission: {mission_id}")

    # Get all edges
    edges_result = client.table("mission_edges").select("*").eq("mission_id", mission_id).execute()
    edges = edges_result.data if edges_result.data else []

    # Build dependency map: target_node_id -> [source_node_ids]
    dependency_map = {}
    for edge in edges:
        if edge['edge_type'] == 'depends_on':
            target = edge['to_node_id']
            source = edge['from_node_id']
            if target not in dependency_map:
                dependency_map[target] = []
            dependency_map[target].append(source)

    print(f"[INFO] Found {len(dependency_map)} nodes with dependencies")

    # Get all nodes
    nodes_result = client.table("mission_nodes").select("*").eq("mission_id", mission_id).execute()
    nodes = nodes_result.data if nodes_result.data else []

    print(f"[INFO] Updating {len(nodes)} nodes")

    # Update each node's depends_on field
    updated = 0
    for node in nodes:
        node_id = node['id']
        deps = dependency_map.get(node_id, [])

        # Update the node
        client.table("mission_nodes").update({
            "depends_on": deps,
            "updated_at": "now()"
        }).eq("id", node_id).execute()

        if deps:
            print(f"  [OK] {node['title']}: depends on {len(deps)} node(s)")
        else:
            print(f"  [OK] {node['title']}: no dependencies")
        updated += 1

    print(f"\n[OK] Updated {updated} nodes")


def verify_fix(client, mission_id):
    """Verify that depends_on is now populated."""
    print("\n[VERIFY] Checking fix...")

    nodes_result = client.table("mission_nodes").select("*").eq("mission_id", mission_id).execute()
    nodes = nodes_result.data if nodes_result.data else []

    for node in nodes:
        deps = node.get('depends_on', [])
        if deps:
            print(f"  {node['title']}: depends_on = {len(deps)} node(s)")
        else:
            print(f"  {node['title']}: depends_on = []")


def main():
    """Fix depends_on field."""
    print("=" * 60)
    print("Fixing depends_on field from edges")
    print("=" * 60)

    client = get_supabase_client()

    fix_depends_on(client, MISSION_ID)
    verify_fix(client, MISSION_ID)

    print("\n" + "=" * 60)
    print("Fix complete!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] Fix failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
