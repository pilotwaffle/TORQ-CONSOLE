"""
Node Runner for Task Graph Engine.

Handles execution of individual nodes.
"""

import logging
import time
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from uuid import UUID

from .models import (
    NodeDefinition,
    NodeType,
    NodeStatus,
    RetryPolicy,
    FailureStrategy,
)

logger = logging.getLogger(__name__)


class NodeRunner:
    """
    Executes individual task nodes.

    Supports:
    - Agent nodes
    - Tool nodes
    - API call nodes
    - Analysis nodes
    - Retry logic
    """

    def __init__(self, agent_registry=None):
        """
        Initialize the node runner.

        Args:
            agent_registry: Agent registry for executing agent nodes
        """
        self.agent_registry = agent_registry

    async def execute_node(
        self,
        node: NodeDefinition,
        input_data: Dict[str, Any],
        trace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a single node.

        Args:
            node: Node definition
            input_data: Input data from previous nodes
            trace_id: Trace ID for telemetry

        Returns:
            Node execution result with:
            - status: completed/failed/skipped
            - output: Node output
            - error: Error message if failed
            - duration_ms: Execution time
            - retry_count: Number of retries performed
        """
        started_at = time.time()
        retry_count = 0
        max_retries = (node.retry_policy or RetryPolicy()).max_retries
        last_error = None

        while retry_count <= max_retries:
            try:
                if node.node_type == NodeType.AGENT:
                    output = await self._execute_agent_node(node, input_data, trace_id)
                elif node.node_type == NodeType.TOOL:
                    output = await self._execute_tool_node(node, input_data, trace_id)
                elif node.node_type == NodeType.API_CALL:
                    output = await self._execute_api_node(node, input_data, trace_id)
                elif node.node_type == NodeType.ANALYSIS:
                    output = await self._execute_analysis_node(node, input_data, trace_id)
                elif node.node_type == NodeType.CONDITION:
                    output = await self._execute_condition_node(node, input_data, trace_id)
                elif node.node_type == NodeType.PARALLEL:
                    output = await self._execute_parallel_node(node, input_data, trace_id)
                elif node.node_type == NodeType.SEQUENTIAL:
                    output = await self._execute_sequential_node(node, input_data, trace_id)
                else:
                    raise ValueError(f"Unknown node type: {node.node_type}")

                duration_ms = int((time.time() - started_at) * 1000)

                return {
                    "status": "completed",
                    "output": output,
                    "error": None,
                    "duration_ms": duration_ms,
                    "retry_count": retry_count,
                }

            except Exception as e:
                last_error = str(e)
                logger.warning(f"Node {node.name} execution failed (attempt {retry_count + 1}): {e}")

                retry_count += 1
                if retry_count > max_retries:
                    break

                # Check failure strategy
                failure_strategy = (node.retry_policy or RetryPolicy()).failure_strategy

                if failure_strategy == FailureStrategy.SKIP:
                    logger.info(f"Skipping node {node.name} after failure")
                    duration_ms = int((time.time() - started_at) * 1000)
                    return {
                        "status": "skipped",
                        "output": {},
                        "error": last_error,
                        "duration_ms": duration_ms,
                        "retry_count": retry_count - 1,
                    }

                elif failure_strategy == FailureStrategy.FAIL:
                    raise

                # Wait before retry (with exponential backoff)
                retry_policy = node.retry_policy or RetryPolicy()
                delay = retry_policy.retry_delay_ms * (
                    retry_policy.backoff_multiplier ** (retry_count - 1)
                )
                await asyncio.sleep(delay / 1000)

        # All retries exhausted
        duration_ms = int((time.time() - started_at) * 1000)
        return {
            "status": "failed",
            "output": {},
            "error": last_error,
            "duration_ms": duration_ms,
            "retry_count": retry_count - 1,
        }

    async def _execute_agent_node(
        self,
        node: NodeDefinition,
        input_data: Dict[str, Any],
        trace_id: Optional[str],
    ) -> Dict[str, Any]:
        """Execute an agent node."""
        if not self.agent_registry:
            raise RuntimeError("Agent registry not configured")

        if not node.agent_id:
            raise ValueError("Agent node requires agent_id")

        # Call the agent
        # TODO: Integrate with actual agent registry
        return {
            "text": f"Agent {node.agent_id} executed with input: {input_data}",
            "agent_id": node.agent_id,
        }

    async def _execute_tool_node(
        self,
        node: NodeDefinition,
        input_data: Dict[str, Any],
        trace_id: Optional[str],
    ) -> Dict[str, Any]:
        """Execute a tool node."""
        tool_name = node.tool_name or node.parameters.get("tool")
        if not tool_name:
            raise ValueError("Tool node requires tool_name or tool parameter")

        # TODO: Implement tool execution
        return {
            "tool": tool_name,
            "result": f"Tool {tool_name} executed",
        }

    async def _execute_api_node(
        self,
        node: NodeDefinition,
        input_data: Dict[str, Any],
        trace_id: Optional[str],
    ) -> Dict[str, Any]:
        """Execute an API call node."""
        url = node.parameters.get("url")
        method = node.parameters.get("method", "GET")
        headers = node.parameters.get("headers", {})
        body = node.parameters.get("body")

        # TODO: Implement actual API call
        return {
            "url": url,
            "method": method,
            "result": "API call executed",
        }

    async def _execute_analysis_node(
        self,
        node: NodeDefinition,
        input_data: Dict[str, Any],
        trace_id: Optional[str],
    ) -> Dict[str, Any]:
        """Execute an analysis node."""
        analysis_type = node.parameters.get("analysis_type", "summary")

        return {
            "analysis_type": analysis_type,
            "input": input_data,
            "result": f"Analysis complete: {analysis_type}",
        }

    async def _execute_condition_node(
        self,
        node: NodeDefinition,
        input_data: Dict[str, Any],
        trace_id: Optional[str],
    ) -> Dict[str, Any]:
        """Execute a condition node."""
        condition = node.parameters.get("condition")
        if not condition:
            raise ValueError("Condition node requires condition parameter")

        # Simple condition evaluation
        # TODO: Implement proper condition parsing
        result = bool(input_data.get(condition.get("field"), False))

        return {
            "condition": condition,
            "result": result,
            "branch": "true" if result else "false",
        }

    async def _execute_parallel_node(
        self,
        node: NodeDefinition,
        input_data: Dict[str, Any],
        trace_id: Optional[str],
    ) -> Dict[str, Any]:
        """Execute child nodes in parallel."""
        # Parallel execution is handled by the executor
        # This node type is a marker for the executor
        return {
            "node_type": "parallel",
            "result": "Parallel execution coordinated by executor",
        }

    async def _execute_sequential_node(
        self,
        node: NodeDefinition,
        input_data: Dict[str, Any],
        trace_id: Optional[str],
    ) -> Dict[str, Any]:
        """Execute child nodes sequentially."""
        # Sequential execution is handled by the executor
        # This node type is a marker for the executor
        return {
            "node_type": "sequential",
            "result": "Sequential execution coordinated by executor",
        }
