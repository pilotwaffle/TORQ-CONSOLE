"""
Seed Demo Workflows Migration

Creates example workflows for first-time users.
"""

import asyncio
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)


async def seed_demo_workflows(supabase_client, agent_registry=None) -> None:
    """
    Seed the database with demo workflow templates.

    Args:
        supabase_client: Supabase client for database operations
        agent_registry: Optional agent registry for validation
    """
    demo_workflows = [
        {
            "name": "AI Market Research",
            "description": "Research the AI market and generate a strategic summary with competitive insights",
            "nodes": [
                {
                    "node_id": str(uuid4()),
                    "node_key": "market_research",
                    "name": "AI Market Research",
                    "node_type": "agent",
                    "agent_id": "research_agent",
                    "depends_on": [],
                    "parameters": {
                        "query": "AI infrastructure market trends 2025 enterprise adoption",
                        "max_results": 10,
                    },
                    "timeout_seconds": 300,
                    "retry_policy": {
                        "max_retries": 3,
                        "retry_delay_ms": 1000,
                        "failure_strategy": "retry",
                    },
                    "position_x": 100,
                    "position_y": 100,
                },
                {
                    "node_id": str(uuid4()),
                    "node_key": "competitor_analysis",
                    "name": "Competitor Analysis",
                    "node_type": "agent",
                    "agent_id": "workflow_agent",
                    "depends_on": ["market_research"],
                    "parameters": {
                        "task": "Analyze the competitive landscape and identify key differentiators",
                    },
                    "timeout_seconds": 300,
                    "retry_policy": {
                        "max_retries": 3,
                        "retry_delay_ms": 1000,
                        "failure_strategy": "retry",
                    },
                    "position_x": 100,
                    "position_y": 300,
                },
                {
                    "node_id": str(uuid4()),
                    "node_key": "strategic_summary",
                    "name": "Strategic Summary",
                    "node_type": "agent",
                    "agent_id": "torq_prince_flowers",
                    "depends_on": ["competitor_analysis"],
                    "parameters": {
                        "task": "Synthesize research and analysis into a strategic consulting summary",
                    },
                    "timeout_seconds": 300,
                    "retry_policy": {
                        "max_retries": 3,
                        "retry_delay_ms": 1000,
                        "failure_strategy": "retry",
                    },
                    "position_x": 100,
                    "position_y": 500,
                },
            ],
            "edges": [
                {
                    "edge_id": str(uuid4()),
                    "source_node_id": "market_research",
                    "target_node_id": "competitor_analysis",
                },
                {
                    "edge_id": str(uuid4()),
                    "source_node_id": "competitor_analysis",
                    "target_node_id": "strategic_summary",
                },
            ],
            "limits": {
                "max_nodes": 10,
                "max_runtime_seconds": 900,
                "max_parallel_nodes": 3,
            },
        },
        {
            "name": "Competitor Intelligence",
            "description": "Analyze a specific competitor and generate actionable intelligence",
            "nodes": [
                {
                    "node_id": str(uuid4()),
                    "node_key": "company_research",
                    "name": "Company Research",
                    "node_type": "agent",
                    "agent_id": "research_agent",
                    "depends_on": [],
                    "parameters": {
                        "query": "{{competitor_name}} business model products funding",
                    },
                    "timeout_seconds": 300,
                    "retry_policy": {
                        "max_retries": 3,
                        "retry_delay_ms": 1000,
                        "failure_strategy": "retry",
                    },
                    "position_x": 100,
                    "position_y": 100,
                },
                {
                    "node_id": str(uuid4()),
                    "node_key": "product_analysis",
                    "name": "Product Analysis",
                    "node_type": "agent",
                    "agent_id": "workflow_agent",
                    "depends_on": ["company_research"],
                    "parameters": {
                        "task": "Analyze product strengths, weaknesses, and market positioning",
                    },
                    "timeout_seconds": 300,
                    "retry_policy": {
                        "max_retries": 3,
                        "retry_delay_ms": 1000,
                        "failure_strategy": "retry",
                    },
                    "position_x": 100,
                    "position_y": 300,
                },
                {
                    "node_id": str(uuid4()),
                    "node_key": "intelligence_report",
                    "name": "Intelligence Report",
                    "node_type": "agent",
                    "agent_id": "torq_prince_flowers",
                    "depends_on": ["product_analysis"],
                    "parameters": {
                        "task": "Generate actionable competitive intelligence report",
                    },
                    "timeout_seconds": 300,
                    "retry_policy": {
                        "max_retries": 3,
                        "retry_delay_ms": 1000,
                        "failure_strategy": "retry",
                    },
                    "position_x": 100,
                    "position_y": 500,
                },
            ],
            "edges": [
                {
                    "edge_id": str(uuid4()),
                    "source_node_id": "company_research",
                    "target_node_id": "product_analysis",
                },
                {
                    "edge_id": str(uuid4()),
                    "source_node_id": "product_analysis",
                    "target_node_id": "intelligence_report",
                },
            ],
            "limits": {
                "max_nodes": 10,
                "max_runtime_seconds": 900,
                "max_parallel_nodes": 3,
            },
        },
        {
            "name": "Consulting Brief Generator",
            "description": "Research a topic and produce a professional consulting brief",
            "nodes": [
                {
                    "node_id": str(uuid4()),
                    "node_key": "topic_research",
                    "name": "Topic Research",
                    "node_type": "agent",
                    "agent_id": "research_agent",
                    "depends_on": [],
                    "parameters": {
                        "query": "{{topic}} industry trends best practices",
                    },
                    "timeout_seconds": 300,
                    "retry_policy": {
                        "max_retries": 3,
                        "retry_delay_ms": 1000,
                        "failure_strategy": "retry",
                    },
                    "position_x": 100,
                    "position_y": 100,
                },
                {
                    "node_id": str(uuid4()),
                    "node_key": "analysis",
                    "name": "Analysis & Synthesis",
                    "node_type": "agent",
                    "agent_id": "workflow_agent",
                    "depends_on": ["topic_research"],
                    "parameters": {
                        "task": "Analyze findings and identify key insights and recommendations",
                    },
                    "timeout_seconds": 300,
                    "retry_policy": {
                        "max_retries": 3,
                        "retry_delay_ms": 1000,
                        "failure_strategy": "retry",
                    },
                    "position_x": 100,
                    "position_y": 300,
                },
                {
                    "node_id": str(uuid4()),
                    "node_key": "consulting_brief",
                    "name": "Consulting Brief",
                    "node_type": "agent",
                    "agent_id": "torq_prince_flowers",
                    "depends_on": ["analysis"],
                    "parameters": {
                        "task": "Create a professional consulting brief with executive summary and recommendations",
                    },
                    "timeout_seconds": 300,
                    "retry_policy": {
                        "max_retries": 3,
                        "retry_delay_ms": 1000,
                        "failure_strategy": "retry",
                    },
                    "position_x": 100,
                    "position_y": 500,
                },
            ],
            "edges": [
                {
                    "edge_id": str(uuid4()),
                    "source_node_id": "topic_research",
                    "target_node_id": "analysis",
                },
                {
                    "edge_id": str(uuid4()),
                    "source_node_id": "analysis",
                    "target_node_id": "consulting_brief",
                },
            ],
            "limits": {
                "max_nodes": 10,
                "max_runtime_seconds": 900,
                "max_parallel_nodes": 3,
            },
        },
    ]

    if not supabase_client:
        logger.warning("No Supabase client - skipping workflow seeding")
        return

    for workflow in demo_workflows:
        try:
            # Check if workflow already exists
            existing = supabase_client.table("task_graphs").select("graph_id").eq("name", workflow["name"]).execute()

            if existing.data and len(existing.data) > 0:
                logger.info(f"Demo workflow '{workflow['name']}' already exists - skipping")
                continue

            # Insert workflow
            graph_id = str(uuid4())

            # Insert graph
            supabase_client.table("task_graphs").insert({
                "graph_id": graph_id,
                "name": workflow["name"],
                "description": workflow["description"],
                "status": "active",
                "version": 1,
                "limits": workflow["limits"],
            }).execute()

            # Insert nodes
            for node in workflow["nodes"]:
                supabase_client.table("task_graph_nodes").insert({
                    "node_id": node["node_id"],
                    "graph_id": graph_id,
                    "node_key": node["node_key"],
                    "name": node["name"],
                    "node_type": node["node_type"],
                    "agent_id": node["agent_id"],
                    "depends_on": node["depends_on"],
                    "parameters": node["parameters"],
                    "timeout_seconds": node["timeout_seconds"],
                    "retry_policy": node["retry_policy"],
                    "position_x": node["position_x"],
                    "position_y": node["position_y"],
                }).execute()

            # Insert edges
            for edge in workflow["edges"]:
                supabase_client.table("task_graph_edges").insert({
                    "edge_id": edge["edge_id"],
                    "graph_id": graph_id,
                    "source_node_id": edge["source_node_id"],
                    "target_node_id": edge["target_node_id"],
                }).execute()

            logger.info(f"Created demo workflow: {workflow['name']}")

        except Exception as e:
            logger.error(f"Failed to seed demo workflow '{workflow['name']}': {e}")

    logger.info("Demo workflow seeding complete")


# Standalone execution for testing
async def main():
    """Run the seeding script standalone."""
    import os
    from supabase import create_client

    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        return

    client = create_client(supabase_url, supabase_key)
    await seed_demo_workflows(client)
    print("Demo workflows seeded successfully")


if __name__ == "__main__":
    asyncio.run(main())
