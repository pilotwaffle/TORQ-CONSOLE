#!/usr/bin/env python3
"""
Create Mission 1 for Phase 5.1 validation using local PostgreSQL.
"""

import os
import sys
from datetime import datetime
from uuid import uuid4
import psycopg2

# Connection to local validation database
DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "torq_validation",
    "user": "postgres",
    "password": "postgres"
}

def create_mission_1():
    """Create Mission 1: Market Entry Analysis."""

    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()

    # Generate IDs
    mission_id = str(uuid4())
    graph_id = str(uuid4())

    print(f"Creating Mission 1: {mission_id}")

    # 1. Create mission
    cur.execute("""
        INSERT INTO missions (id, title, mission_type, objective, context, status)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, title, status
    """, (
        mission_id,
        "Market Entry Analysis",
        "analysis",
        "Assess market opportunity for electric delivery vehicles in Southeast US",
        '{"target_market": "commercial delivery fleets", "region": "Southeast US", "time_horizon": "5 years"}',
        "draft"
    ))

    result = cur.fetchone()
    print(f"✓ Mission created: {result[1]} (status: {result[2]})")

    # 2. Create mission graph
    cur.execute("""
        INSERT INTO mission_graphs (id, mission_id, version, status)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (graph_id, mission_id, "1.0", "active"))

    graph_result = cur.fetchone()
    print(f"✓ Graph created: {graph_result[0]}")

    # 3. Create nodes (8 nodes for analysis mission)
    nodes = [
        # Root objective node
        {
            "id": str(uuid4()),
            "node_type": "objective",
            "title": "Define Market Entry Objectives",
            "description": "Define scope and objectives for electric delivery vehicle market entry",
            "depends_on": [],
            "agent_type": "strategic_planner"
        },
        # Research branches (parallel)
        {
            "id": str(uuid4()),
            "node_type": "task",
            "title": "Market Size Analysis",
            "description": "Analyze total addressable market for commercial EV delivery fleets",
            "depends_on": [],  # Can start in parallel with objective
            "agent_type": "market_researcher"
        },
        {
            "id": str(uuid4()),
            "node_type": "task",
            "title": "Competitive Landscape",
            "description": "Identify key competitors and their market positions",
            "depends_on": [],
            "agent_type": "competitive_analyst"
        },
        {
            "id": str(uuid4()),
            "node_type": "task",
            "title": "Regulatory Analysis",
            "description": "Analyze regulatory requirements and barriers",
            "depends_on": [],
            "agent_type": "policy_analyst"
        },
        # Synthesis nodes
        {
            "id": str(uuid4()),
            "node_type": "task",
            "title": "Infrastructure Requirements",
            "description": "Assess charging infrastructure and grid capacity needs",
            "depends_on": [],
            "agent_type": "infrastructure_analyst"
        },
        # Decision node
        {
            "id": str(uuid4()),
            "node_type": "decision",
            "title": "Feasibility Assessment",
            "description": "Determine if market entry is viable based on research",
            "depends_on": [],
            "agent_type": "evaluator"
        },
        # Evidence node
        {
            "id": str(uuid4()),
            "node_type": "evidence",
            "title": "Evidence Compilation",
            "description": "Compile all evidence supporting the feasibility decision",
            "depends_on": [],
            "agent_type": "synthesizer"
        },
        # Deliverable node
        {
            "id": str(uuid4()),
            "node_type": "deliverable",
            "title": "Market Entry Report",
            "description": "Final report with recommendations and go/no-go decision",
            "depends_on": [],
            "agent_type": "report_writer"
        }
    ]

    # For simplicity, let's create a simpler linear graph first
    # Root -> Research -> Competitor -> Regulatory -> Decision -> Evidence -> Deliverable

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
            "depends_on": [],  # Will be linked after node creation
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

        cur.execute("""
            INSERT INTO mission_nodes (id, mission_id, graph_id, node_type, title, description, status, depends_on, workstream_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, node_type, status
        """, (
            node_id, mission_id, graph_id, node["node_type"], node["title"],
            node["description"], "pending", [], node["workstream_id"]
        ))

        result = cur.fetchone()
        print(f"✓ Node created: {result[1]} - {node['title']}")

    # 4. Create edges (simple linear flow)
    # Objective -> Market Size
    cur.execute("""
        INSERT INTO mission_edges (id, mission_id, graph_id, from_node_id, to_node_id, edge_type)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (str(uuid4()), mission_id, graph_id, node_ids[0], node_ids[1], "depends_on"))
    print("✓ Edge: Objective -> Market Size")

    # Market Size -> Competitor
    cur.execute("""
        INSERT INTO mission_edges (id, mission_id, graph_id, from_node_id, to_node_id, edge_type)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (str(uuid4()), mission_id, graph_id, node_ids[1], node_ids[2], "depends_on"))
    print("✓ Edge: Market Size -> Competitor")

    # Competitor -> Financial
    cur.execute("""
        INSERT INTO mission_edges (id, mission_id, graph_id, from_node_id, to_node_id, edge_type)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (str(uuid4()), mission_id, graph_id, node_ids[2], node_ids[3], "depends_on"))
    print("✓ Edge: Competitor -> Financial")

    # Financial -> Evidence
    cur.execute("""
        INSERT INTO mission_edges (id, mission_id, graph_id, from_node_id, to_node_id, edge_type)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (str(uuid4()), mission_id, graph_id, node_ids[3], node_ids[4], "depends_on"))
    print("✓ Edge: Financial -> Evidence")

    # Evidence -> Deliverable
    cur.execute("""
        INSERT INTO mission_edges (id, mission_id, graph_id, from_node_id, to_node_id, edge_type)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (str(uuid4()), mission_id, graph_id, node_ids[4], node_ids[5], "depends_on"))
    print("✓ Edge: Evidence -> Deliverable")

    # 5. Create workstream states
    for i, node in enumerate(simple_nodes):
        cur.execute("""
            INSERT INTO workstream_states (workstream_id, mission_id, phase, status, total_nodes, completed_nodes)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (node["workstream_id"], mission_id, "initializing", "pending", 1, 0))

    print(f"✓ Created {len(simple_nodes)} workstream states")

    # 6. Update mission status to planned
    cur.execute("""
        UPDATE missions SET status = 'planned', updated_at = NOW()
        WHERE id = %s
    """, (mission_id,))

    print(f"\n✓ Mission status updated to: planned")

    # Summary
    cur.execute("SELECT COUNT(*) FROM mission_nodes WHERE mission_id = %s", (mission_id,))
    node_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM mission_edges WHERE mission_id = %s", (mission_id,))
    edge_count = cur.fetchone()[0]

    print(f"\n{'='*50}")
    print(f"Mission 1 Created Successfully")
    print(f"{'='*50}")
    print(f"Mission ID: {mission_id}")
    print(f"Title: Market Entry Analysis")
    print(f"Type: analysis")
    print(f"Nodes: {node_count}")
    print(f"Edges: {edge_count}")
    print(f"Status: planned")
    print(f"{'='*50}")

    cur.close()
    conn.close()

    return mission_id

if __name__ == "__main__":
    try:
        mission_id = create_mission_1()
        print(f"\nMission ID for next steps: {mission_id}")
        print("\nNext:")
        print("1. Start the scheduler")
        print("2. Run failure pattern detection queries")
        print("3. Monitor node execution")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
