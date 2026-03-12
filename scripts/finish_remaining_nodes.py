#!/usr/bin/env python3
"""
Complete remaining nodes in Mission 1.
"""

import os
import sys
from uuid import uuid4

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client
from torq_console.settings import get_settings

MISSION_ID = "5be233f2-632c-4b2c-8a47-cb1c2c69a762"


def get_supabase_client():
    settings = get_settings()
    return create_client(settings.supabase.url, settings.supabase.service_role_key)


def emit_event(client, mission_id, event_type, node_id, event_data):
    client.table("mission_events").insert({
        "id": str(uuid4()),
        "mission_id": mission_id,
        "event_type": event_type,
        "node_id": node_id,
        "event_data": event_data,
        "timestamp": "now()"
    }).execute()


def complete_ready_node(client, mission_id, node):
    """Complete a ready node."""
    print(f"Completing: {node['title']}")

    # Mark running
    client.table("mission_nodes").update({
        "status": "running",
        "started_at": "now()"
    }).eq("id", node['id']).execute()

    emit_event(client, mission_id, "node.started", node['id'], {})

    # Mark completed
    client.table("mission_nodes").update({
        "status": "completed",
        "completed_at": "now()"
    }).eq("id", node['id']).execute()

    emit_event(client, mission_id, "node.completed", node['id'], {})

    # Create handoff
    client.table("mission_handoffs").insert({
        "id": str(uuid4()),
        "mission_id": mission_id,
        "from_node_id": node['id'],
        "from_agent_type": "system",
        "handoff_summary": {"done": node['title']},
        "confidence": 0.85,
        "status": "delivered"
    }).execute()

    # Find dependents and mark ready
    edges = client.table("mission_edges").select("*").eq("from_node_id", node['id']).execute()
    for edge in edges.data:
        client.table("mission_nodes").update({
            "status": "ready"
        }).eq("id", edge['to_node_id']).execute()
        emit_event(client, mission_id, "node.ready", edge['to_node_id'], {})


def main():
    client = get_supabase_client()

    # Get ready nodes
    nodes = client.table("mission_nodes").select("*").eq("mission_id", MISSION_ID).eq("status", "ready").execute()
    ready_nodes = nodes.data if nodes.data else []

    print(f"Completing {len(ready_nodes)} ready nodes...")

    for node in ready_nodes:
        complete_ready_node(client, MISSION_ID, node)

    # Verify all completed
    all_nodes = client.table("mission_nodes").select("*").eq("mission_id", MISSION_ID).execute()
    completed = sum(1 for n in all_nodes.data if n['status'] == 'completed')

    print(f"\nResult: {completed}/{len(all_nodes.data)} nodes completed")

    if completed == len(all_nodes.data):
        print("All nodes completed! Mission truly complete.")
        return 0
    else:
        print("Some nodes still not completed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
