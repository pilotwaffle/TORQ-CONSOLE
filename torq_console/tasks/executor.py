"""
Execution Engine for Task Graph Engine.

Orchestrates the execution of task graphs with dependency resolution.
Integrates with Shared Cognitive Workspace for execution-level working memory.
"""

import logging
import time
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Set
from uuid import UUID, uuid4

from .graph_engine import TaskGraph
from .models import (
    NodeDefinition,
    EdgeDefinition,
    NodeStatus,
    ExecutionStatus,
    ExecutionCreate,
    ExecutionResponse,
    NodeResult,
    TaskGraphNode,
)
from .dependency_resolver import DependencyResolver
from .node_runner import NodeRunner

# Optional workspace integration for Shared Cognitive Workspace
try:
    from torq_console.workspace.service import WorkspaceService
    WORKSPACE_AVAILABLE = True
except ImportError:
    WORKSPACE_AVAILABLE = False
    WorkspaceService = None

logger = logging.getLogger(__name__)


class ExecutionEngine:
    """
    Executes task graphs with dependency resolution.

    Handles:
    - Sequential and parallel execution
    - State persistence
    - Error handling and recovery
    - Telemetry
    """

    def __init__(self, supabase_client=None, agent_registry=None, workspace_service=None):
        """
        Initialize the execution engine.

        Args:
            supabase_client: Supabase client for persistence
            agent_registry: Agent registry for agent execution
            workspace_service: Optional WorkspaceService for Shared Cognitive Workspace
        """
        self.supabase = supabase_client
        self.agent_registry = agent_registry
        self.workspace_service = workspace_service
        self.node_runner = NodeRunner(agent_registry)
        self._running_executions: Dict[UUID, asyncio.Task] = {}

    async def execute_graph(
        self,
        graph: TaskGraph,
        execution_request: ExecutionCreate,
    ) -> ExecutionResponse:
        """
        Execute a task graph.

        Args:
            graph: Task graph to execute
            execution_request: Execution request with trigger info

        Returns:
            Execution response with results
        """
        execution_id = uuid4()
        trace_id = f"exec_{int(time.time() * 1000)}_{execution_id.hex[:8]}"

        # Create Shared Cognitive Workspace for this execution
        workspace_id = None
        if self.workspace_service:
            try:
                workspace = await self.workspace_service.get_or_create_workspace(
                    scope_type="workflow_execution",
                    scope_id=str(execution_id),
                    title=f"Execution: {graph.name or 'Untitled'}",
                    description=f"Workspace for workflow execution {execution_id}",
                )
                workspace_id = str(workspace.workspace_id)
                logger.info(f"[{trace_id}] Created workspace: {workspace_id}")
            except Exception as e:
                logger.warning(f"[{trace_id}] Failed to create workspace: {e}")
                # Continue without workspace - non-blocking

        # Create execution record
        if self.supabase:
            execution_data = {
                "execution_id": str(execution_id),
                "graph_id": str(graph.graph_id),
                "status": "running",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "trigger_type": execution_request.trigger_type.value,
                "trigger_source": execution_request.trigger_source,
                "trace_id": trace_id,
            }
            # Link workspace if created
            if workspace_id:
                execution_data["workspace_id"] = workspace_id

            self.supabase.table("task_executions").insert(execution_data).execute()

        started_at = time.time()
        completed_nodes: Set[UUID] = set()
        failed_nodes: Set[UUID] = set()
        node_results: List[Dict[str, Any]] = []
        output_data = execution_request.input_data.copy()

        try:
            # Build dependency resolver
            graph_nodes = [
                TaskGraphNode(
                    node_id=n.node_id or uuid4(),
                    name=n.name,
                    node_type=n.node_type,
                    agent_id=n.agent_id,
                    tool_name=n.tool_name,
                    parameters=n.parameters,
                    retry_policy=n.retry_policy,
                    timeout_seconds=n.timeout_seconds,
                    depends_on=n.depends_on,
                )
                for n in graph.nodes
            ]

            resolver = DependencyResolver(graph_nodes)

            # Execute in layers (topological order)
            layers = resolver.topological_sort()

            for layer_idx, layer_nodes in enumerate(layers):
                logger.info(f"[{trace_id}] Executing layer {layer_idx + 1}: {len(layer_nodes)} nodes")

                # Check if layer can run in parallel
                can_parallel = resolver.can_execute_parallel(layer_nodes)

                if can_parallel:
                    # Execute layer in parallel
                    layer_results = await asyncio.gather(
                        *[
                            self._execute_single_node(
                                graph,
                                UUID(node_id),
                                resolver.node_map[UUID(node_id)],
                                output_data,
                                execution_id,
                                trace_id,
                            )
                            for node_id in layer_nodes
                        ],
                        return_exceptions=True,
                    )

                    for i, result in enumerate(layer_results):
                        node_id = layer_nodes[i]
                        if isinstance(result, Exception):
                            logger.error(f"[{trace_id}] Node {node_id} failed: {result}")
                            failed_nodes.add(node_id)
                        else:
                            if result["status"] == "completed":
                                completed_nodes.add(node_id)
                                # Merge output into shared data
                                output_data.update(result.get("output", {}))
                            elif result["status"] == "failed":
                                failed_nodes.add(node_id)
                            elif result["status"] == "skipped":
                                completed_nodes.add(node_id)  # Skipped nodes are considered complete

                        node_results.append({
                            "execution_id": str(execution_id),
                            "node_id": str(node_id),
                            **result,
                        })

                else:
                    # Execute layer sequentially
                    for node_id in layer_nodes:
                        result = await self._execute_single_node(
                            graph,
                            node_id,
                            resolver.node_map[node_id],
                            output_data,
                            execution_id,
                            trace_id,
                        )

                        node_results.append({
                            "execution_id": str(execution_id),
                            "node_id": str(node_id),
                            **result,
                        })

                        if result["status"] == "completed":
                            completed_nodes.add(node_id)
                            output_data.update(result.get("output", {}))
                        elif result["status"] == "failed":
                            failed_nodes.add(node_id)
                        elif result["status"] == "skipped":
                            completed_nodes.add(node_id)

                # Stop if too many failures
                if len(failed_nodes) > len(graph.nodes) / 2:
                    raise RuntimeError(f"Too many node failures: {len(failed_nodes)}")

            completed_at = time.time()
            duration_ms = int((completed_at - started_at) * 1000)

            # Update execution record
            final_status = ExecutionStatus.COMPLETED if not failed_nodes else ExecutionStatus.FAILED

            if self.supabase:
                self.supabase.table("task_executions").update({
                    "status": final_status.value,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "output": output_data,
                    "total_duration_ms": duration_ms,
                    "nodes_completed": len(completed_nodes),
                    "nodes_failed": len(failed_nodes),
                }).eq("execution_id", str(execution_id)).execute()

                # Store node results
                if node_results:
                    self.supabase.table("task_node_results").insert(node_results).execute()

            return ExecutionResponse(
                execution_id=execution_id,
                graph_id=graph.graph_id,
                status=final_status,
                started_at=datetime.fromtimestamp(started_at, tz=timezone.utc),
                completed_at=datetime.fromtimestamp(completed_at, tz=timezone.utc),
                output=output_data,
                error_message=None if final_status == ExecutionStatus.COMPLETED else f"{len(failed_nodes)} nodes failed",
                total_duration_ms=duration_ms,
                nodes_completed=len(completed_nodes),
                nodes_failed=len(failed_nodes),
                trace_id=trace_id,
                workspace_id=workspace_id,
            )

        except Exception as e:
            logger.error(f"[{trace_id}] Graph execution failed: {e}")
            completed_at = time.time()
            duration_ms = int((completed_at - started_at) * 1000)

            if self.supabase:
                self.supabase.table("task_executions").update({
                    "status": "failed",
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "error_message": str(e),
                    "total_duration_ms": duration_ms,
                    "nodes_completed": len(completed_nodes),
                    "nodes_failed": len(failed_nodes),
                }).eq("execution_id", str(execution_id)).execute()

            return ExecutionResponse(
                execution_id=execution_id,
                graph_id=graph.graph_id,
                status=ExecutionStatus.FAILED,
                started_at=datetime.fromtimestamp(started_at, tz=timezone.utc),
                completed_at=datetime.fromtimestamp(completed_at, tz=timezone.utc),
                output={},
                error_message=str(e),
                total_duration_ms=duration_ms,
                nodes_completed=len(completed_nodes),
                nodes_failed=len(failed_nodes),
                trace_id=trace_id,
                workspace_id=workspace_id,
            )

    async def _execute_single_node(
        self,
        graph: TaskGraph,
        node_id: UUID,
        graph_node: TaskGraphNode,
        input_data: Dict[str, Any],
        execution_id: UUID,
        trace_id: str,
    ) -> Dict[str, Any]:
        """
        Execute a single node.

        Args:
            graph: Task graph
            node_id: Node ID
            graph_node: Graph node from resolver
            input_data: Input data
            execution_id: Execution ID
            trace_id: Trace ID

        Returns:
            Node result dict
        """
        # Get node definition from graph
        node_def = next((n for n in graph.nodes if n.node_id == node_id), None)
        if not node_def:
            return {
                "status": "failed",
                "output": {},
                "error": f"Node {node_id} not found in graph",
                "duration_ms": 0,
                "retry_count": 0,
            }

        # Update node status to running
        if self.supabase:
            self.supabase.table("task_nodes").update({
                "status": "running",
                "last_execution_at": datetime.now(timezone.utc).isoformat(),
            }).eq("node_id", str(node_id)).execute()

        # Execute the node
        result = await self.node_runner.execute_node(
            node_def,
            input_data,
            trace_id,
        )

        # Update node status
        final_status = NodeStatus.COMPLETED if result["status"] == "completed" else (
            NodeStatus.FAILED if result["status"] == "failed" else NodeStatus.SKIPPED
        )

        if self.supabase:
            self.supabase.table("task_nodes").update({
                "status": final_status.value,
            }).eq("node_id", str(node_id)).execute()

        return result

    async def cancel_execution(self, execution_id: UUID) -> bool:
        """
        Cancel a running execution.

        Args:
            execution_id: Execution ID

        Returns:
            True if cancelled
        """
        task = self._running_executions.get(execution_id)
        if task and not task.done():
            task.cancel()
            del self._running_executions[execution_id]

            if self.supabase:
                self.supabase.table("task_executions").update({
                    "status": "cancelled",
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                }).eq("execution_id", str(execution_id)).execute()

            return True
        return False

    async def get_execution_status(self, execution_id: UUID) -> Optional[ExecutionResponse]:
        """
        Get execution status.

        Args:
            execution_id: Execution ID

        Returns:
            Execution response or None
        """
        if self.supabase:
            result = self.supabase.table("task_executions").select("*").eq("execution_id", str(execution_id)).execute()

            if not result.data:
                return None

            data = result.data[0]
            return ExecutionResponse(
                execution_id=UUID(data["execution_id"]),
                graph_id=UUID(data["graph_id"]),
                status=ExecutionStatus(data["status"]),
                started_at=datetime.fromisoformat(data["started_at"].replace("Z", "+00:00")) if data.get("started_at") else None,
                completed_at=datetime.fromisoformat(data["completed_at"].replace("Z", "+00:00")) if data.get("completed_at") else None,
                output=data.get("output", {}),
                error_message=data.get("error_message"),
                total_duration_ms=data.get("total_duration_ms"),
                nodes_completed=data.get("nodes_completed", 0),
                nodes_failed=data.get("nodes_failed", 0),
                trace_id=data.get("trace_id"),
                workspace_id=data.get("workspace_id"),
            )

        return None
