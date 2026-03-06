"""
API Router for Task Graph Engine.

Provides REST endpoints for task graph management and execution.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel

from .models import (
    TaskGraphCreate,
    TaskGraphResponse,
    ExecutionCreate,
    ExecutionResponse,
    GraphStatus,
    TriggerType,
)
from .graph_engine import TaskGraphEngine, TaskGraph
from .executor import ExecutionEngine
from .scheduler import Scheduler

logger = logging.getLogger(__name__)


def create_task_router(
    supabase_client=None,
    agent_registry=None,
) -> APIRouter:
    """
    Create the task graph API router.

    Args:
        supabase_client: Supabase client for persistence
        agent_registry: Agent registry for agent execution

    Returns:
        FastAPI router with task graph endpoints
    """

    router = APIRouter(prefix="/api/tasks", tags=["tasks"])

    # Initialize engines
    graph_engine = TaskGraphEngine(supabase_client)
    execution_engine = ExecutionEngine(supabase_client, agent_registry)
    scheduler = Scheduler(supabase_client, execution_engine)

    # ========================================================================
    # Graph Management
    # ========================================================================

    @router.post("/graphs", response_model=TaskGraphResponse)
    async def create_graph(request: TaskGraphCreate) -> TaskGraphResponse:
        """
        Create a new task graph.

        Validates the graph structure and persists it to the database.
        """
        try:
            return await graph_engine.create_graph(request)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Failed to create graph: {e}")
            raise HTTPException(status_code=500, detail="Failed to create graph")

    @router.get("/graphs", response_model=List[TaskGraphResponse])
    async def list_graphs(
        status: Optional[GraphStatus] = None,
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
    ) -> List[TaskGraphResponse]:
        """
        List task graphs.

        Can be filtered by status.
        """
        return await graph_engine.list_graphs(status=status, limit=limit, offset=offset)

    @router.get("/graphs/{graph_id}", response_model=TaskGraphResponse)
    async def get_graph(graph_id: UUID) -> TaskGraphResponse:
        """
        Get a specific task graph.

        Returns the graph with all nodes and edges.
        """
        graph = await graph_engine.get_graph(graph_id)
        if not graph:
            raise HTTPException(status_code=404, detail="Graph not found")
        return graph

    @router.delete("/graphs/{graph_id}")
    async def delete_graph(graph_id: UUID) -> Dict[str, bool]:
        """
        Delete a task graph.

        Also deletes all associated executions.
        """
        success = await graph_engine.delete_graph(graph_id)
        if not success:
            raise HTTPException(status_code=404, detail="Graph not found")
        return {"deleted": True}

    @router.post("/graphs/{graph_id}/activate")
    async def activate_graph(graph_id: UUID) -> Dict[str, bool]:
        """
        Activate a task graph.

        Allows the graph to be executed.
        """
        success = await graph_engine.update_graph_status(graph_id, GraphStatus.ACTIVE)
        if not success:
            raise HTTPException(status_code=404, detail="Graph not found")
        return {"activated": True}

    @router.post("/graphs/{graph_id}/archive")
    async def archive_graph(graph_id: UUID) -> Dict[str, bool]:
        """
        Archive a task graph.

        Prevents new executions but keeps history.
        """
        success = await graph_engine.update_graph_status(graph_id, GraphStatus.ARCHIVED)
        if not success:
            raise HTTPException(status_code=404, detail="Graph not found")
        return {"archived": True}

    # ========================================================================
    # Execution
    # ========================================================================

    @router.post("/graphs/{graph_id}/execute", response_model=ExecutionResponse)
    async def execute_graph(
        graph_id: UUID,
        request: ExecutionCreate,
        background_tasks: BackgroundTasks,
    ) -> ExecutionResponse:
        """
        Execute a task graph.

        Resolves dependencies and executes nodes in order.
        Can run synchronously (wait for result) or asynchronously.
        """
        graph = await graph_engine.get_graph(graph_id)
        if not graph:
            raise HTTPException(status_code=404, detail="Graph not found")

        if graph.status != GraphStatus.ACTIVE:
            raise HTTPException(status_code=400, detail=f"Graph is {graph.status.value}, cannot execute")

        # Execute graph
        try:
            return await execution_engine.execute_graph(graph, request)
        except Exception as e:
            logger.error(f"Graph execution failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/executions", response_model=List[ExecutionResponse])
    async def list_executions(
        graph_id: Optional[UUID] = None,
        status: Optional[str] = None,
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
    ) -> List[ExecutionResponse]:
        """
        List task executions.

        Can be filtered by graph and status.
        """
        if not supabase_client:
            return []

        query = supabase_client.table("task_executions").select("*")

        if graph_id:
            query = query.eq("graph_id", str(graph_id))

        if status:
            query = query.eq("status", status)

        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
        result = query.execute()

        return [
            ExecutionResponse(
                execution_id=UUID(e["execution_id"]),
                graph_id=UUID(e["graph_id"]),
                status=e["status"],
                started_at=datetime.fromisoformat(e["started_at"].replace("Z", "+00:00")) if e.get("started_at") else None,
                completed_at=datetime.fromisoformat(e["completed_at"].replace("Z", "+00:00")) if e.get("completed_at") else None,
                output=e.get("output", {}),
                error_message=e.get("error_message"),
                total_duration_ms=e.get("total_duration_ms"),
                nodes_completed=e.get("nodes_completed", 0),
                nodes_failed=e.get("nodes_failed", 0),
                trace_id=e.get("trace_id"),
            )
            for e in result.data
        ]

    @router.get("/executions/{execution_id}", response_model=ExecutionResponse)
    async def get_execution(execution_id: UUID) -> ExecutionResponse:
        """
        Get execution details.

        Returns status and results of an execution.
        """
        execution = await execution_engine.get_execution_status(execution_id)
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
        return execution

    @router.post("/executions/{execution_id}/cancel")
    async def cancel_execution(execution_id: UUID) -> Dict[str, bool]:
        """
        Cancel a running execution.

        Attempts to gracefully stop the execution.
        """
        success = await execution_engine.cancel_execution(execution_id)
        if not success:
            raise HTTPException(status_code=404, detail="Execution not found or cannot be cancelled")
        return {"cancelled": True}

    # ========================================================================
    # Scheduling
    # ========================================================================

    @router.post("/graphs/{graph_id}/schedule")
    async def schedule_graph(
        graph_id: UUID,
        trigger_type: TriggerType,
        schedule: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, UUID]:
        """
        Schedule a graph for automatic execution.

        Creates a trigger based on the specified type.
        """
        trigger_id = await scheduler.register_trigger(
            graph_id=graph_id,
            trigger_type=trigger_type,
            schedule=schedule,
        )

        return {"trigger_id": trigger_id}

    @router.get("/triggers")
    async def list_triggers() -> Dict[str, List[Dict[str, Any]]]:
        """
        List all scheduled triggers.

        Returns active triggers with their next run time.
        """
        return {"triggers": scheduler.get_scheduled_triggers()}

    @router.post("/webhooks/{graph_id}")
    async def webhook_trigger(
        graph_id: UUID,
        payload: Dict[str, Any],
    ) -> ExecutionResponse:
        """
        Webhook endpoint for triggering graphs.

        Can be called by external systems to start workflows.
        """
        try:
            execution_id = await scheduler.handle_webhook(graph_id, payload)

            # Wait a bit for execution to start
            await asyncio.sleep(0.5)

            execution = await execution_engine.get_execution_status(execution_id)
            if execution:
                return execution
            else:
                raise HTTPException(status_code=500, detail="Execution not found")

        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"Webhook execution failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ========================================================================
    # Telemetry
    # ========================================================================

    @router.get("/executions/{execution_id}/nodes")
    async def get_execution_nodes(execution_id: UUID) -> List[Dict[str, Any]]:
        """
        Get node results for an execution.

        Returns detailed results for each node execution.
        """
        if not supabase_client:
            raise HTTPException(status_code=501, detail="Not implemented")

        result = supabase_client.table("task_node_results").select("*").eq(
            "execution_id", str(execution_id)
        ).order("created_at", desc=True).execute()

        return result.data

    # ========================================================================
    # Examples & Templates
    # ========================================================================

    @router.get("/examples")
    async def list_examples() -> Dict[str, Any]:
        """
        List example task graph templates.

        Returns predefined graph templates for common workflows.
        """
        return {
            "examples": [
                {
                    "name": "Research Report",
                    "description": "Automated research report generation",
                    "template": {
                        "name": "Research Report",
                        "description": "Generate a research report on a given topic",
                        "nodes": [
                            {
                                "name": "Search",
                                "node_type": "tool",
                                "tool_name": "web_search",
                                "parameters": {"query": "{{topic}}"},
                            },
                            {
                                "name": "Analyze",
                                "node_type": "agent",
                                "agent_id": "research_agent",
                                "depends_on": ["{{Search.node_id}}"],
                            },
                            {
                                "name": "Write Report",
                                "node_type": "agent",
                                "agent_id": "workflow_agent",
                                "depends_on": ["{{Analyze.node_id}}"],
                            },
                        ],
                        "edges": [],
                    },
                },
                {
                    "name": "Financial Analysis",
                    "description": "Multi-step financial data analysis",
                    "template": {
                        "name": "Financial Analysis",
                        "description": "Analyze financial data and generate insights",
                        "nodes": [
                            {
                                "name": "Fetch Data",
                                "node_type": "api_call",
                                "parameters": {"url": "https://api.finance.example/{{symbol}}"},
                            },
                            {
                                "name": "Calculate Metrics",
                                "node_type": "analysis",
                                "depends_on": ["{{Fetch Data.node_id}}"],
                            },
                            {
                                "name": "Generate Report",
                                "node_type": "agent",
                                "agent_id": "workflow_agent",
                                "depends_on": ["{{Calculate Metrics.node_id}}"],
                            },
                        ],
                        "edges": [],
                    },
                },
            ]
        }

    return router
