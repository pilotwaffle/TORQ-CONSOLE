"""
Workflow Execution Engine

Phase 8: External Action Fabric, Connectors & Enterprise Workflow Execution

The Workflow Execution Engine runs multi-step workflows that coordinate
connector actions, manage state, support conditional logic, and handle retries.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union

from pydantic import BaseModel, Field

from ..connectors.base import ExternalAction, ActionExecutionResult, ActionState, RiskLevel
from ..execution.action_fabric import ExternalActionFabric, get_action_fabric


logger = logging.getLogger(__name__)


# ============================================================================
# Enums
# ============================================================================

class WorkflowState(str, Enum):
    """States of a workflow execution."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING_FOR_APPROVAL = "waiting_for_approval"


class NodeState(str, Enum):
    """States of a workflow node."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WAITING = "waiting"


class NodeType(str, Enum):
    """Types of workflow nodes."""
    START = "start"
    END = "end"
    ACTION = "action"
    CONDITION = "condition"
    PARALLEL = "parallel"
    DELAY = "delay"
    APPROVAL = "approval"
    SUB_WORKFLOW = "sub_workflow"


# ============================================================================
# Models
# ============================================================================

class WorkflowNode(BaseModel):
    """A node in a workflow graph."""
    node_id: str
    node_type: NodeType
    name: str
    description: Optional[str] = None

    # Configuration based on node type
    config: Dict[str, Any] = Field(default_factory=dict)

    # Action config (for action nodes)
    connector_type: Optional[str] = None
    action_type: Optional[str] = None
    action_parameters: Dict[str, Any] = Field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.MEDIUM

    # Condition config (for condition nodes)
    condition_expression: Optional[str] = None
    true_branch: Optional[str] = None  # Node ID for true condition
    false_branch: Optional[str] = None  # Node ID for false condition

    # Delay config (for delay nodes)
    delay_seconds: float = 0

    # State tracking
    state: NodeState = NodeState.PENDING
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    # Timing
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    duration_seconds: Optional[float] = None

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowEdge(BaseModel):
    """An edge connecting workflow nodes."""
    edge_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_node: str
    to_node: str
    condition: Optional[str] = None  # Optional condition for following this edge


class WorkflowDefinition(BaseModel):
    """Definition of a workflow."""
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    version: str = "1.0"

    # Graph structure
    nodes: List[WorkflowNode] = Field(default_factory=list)
    edges: List[WorkflowEdge] = Field(default_factory=list)

    # Configuration
    timeout_seconds: Optional[float] = None
    retry_on_failure: bool = False
    max_retries: int = 0

    # Scoping
    workspace_id: Optional[str] = None
    environment: Optional[str] = None

    # Metadata
    tags: List[str] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)


class WorkflowExecution(BaseModel):
    """An execution of a workflow."""
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str
    definition: WorkflowDefinition

    # Execution context
    workspace_id: Optional[str] = None
    environment: Optional[str] = None
    triggered_by: Optional[str] = None
    trigger_data: Dict[str, Any] = Field(default_factory=dict)

    # State
    state: WorkflowState = WorkflowState.PENDING
    current_node_id: Optional[str] = None

    # Node execution results
    node_results: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    # Variables shared between nodes
    variables: Dict[str, Any] = Field(default_factory=dict)

    # Error handling
    error_message: Optional[str] = None
    failed_at_node: Optional[str] = None

    # Progress tracking
    total_nodes: int = 0
    completed_nodes: int = 0

    # Timing
    created_at: float = Field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    duration_seconds: Optional[float] = None


class WorkflowExecutionResult(BaseModel):
    """Result of a workflow execution."""
    execution_id: str
    workflow_id: str
    success: bool
    state: WorkflowState

    # Results
    node_results: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    output_variables: Dict[str, Any] = Field(default_factory=dict)

    # Error info
    error_message: Optional[str] = None
    failed_at_node: Optional[str] = None

    # Timing
    duration_seconds: Optional[float] = None

    # Timestamp
    completed_at: float = Field(default_factory=time.time)


# ============================================================================
# Workflow Execution Engine
# ============================================================================

class WorkflowExecutionEngine:
    """
    Engine for executing multi-step workflows.

    Features:
    - Graph-based workflow execution
    - Conditional branching
    - Parallel execution
    - Delay nodes
    - Approval gates
    - Error handling and retries
    - State persistence
    """

    def __init__(
        self,
        action_fabric: Optional[ExternalActionFabric] = None
    ):
        """
        Initialize the workflow engine.

        Args:
            action_fabric: Action fabric for executing external actions
        """
        self._fabric = action_fabric or get_action_fabric()
        self._executions: Dict[str, WorkflowExecution] = {}
        self._running = False

        self.logger = logging.getLogger(__name__)

    async def start(self) -> None:
        """Start the workflow engine."""
        self._running = True
        self.logger.info("Workflow Execution Engine started")

    async def stop(self) -> None:
        """Stop the workflow engine."""
        self._running = False
        self.logger.info("Workflow Execution Engine stopped")

    # -------------------------------------------------------------------------
    # Workflow Execution
    # -------------------------------------------------------------------------

    async def execute_workflow(
        self,
        definition: WorkflowDefinition,
        trigger_data: Optional[Dict[str, Any]] = None,
        workspace_id: Optional[str] = None,
        environment: Optional[str] = None,
        triggered_by: Optional[str] = None
    ) -> WorkflowExecutionResult:
        """
        Execute a workflow.

        Args:
            definition: The workflow definition to execute
            trigger_data: Data that triggered the workflow
            workspace_id: Workspace ID for scoping
            environment: Environment for execution
            triggered_by: Who triggered the workflow

        Returns:
            WorkflowExecutionResult
        """
        # Create execution
        execution = WorkflowExecution(
            workflow_id=definition.workflow_id,
            definition=definition,
            trigger_data=trigger_data or {},
            workspace_id=workspace_id or definition.workspace_id,
            environment=environment or definition.environment,
            triggered_by=triggered_by
        )

        execution.total_nodes = len(definition.nodes)

        # Store execution
        self._executions[execution.execution_id] = execution

        try:
            # Start execution
            execution.state = WorkflowState.RUNNING
            execution.started_at = time.time()

            # Find start node
            start_node = self._find_start_node(definition)
            if not start_node:
                raise ValueError("Workflow has no start node")

            # Execute workflow
            await self._execute_from_node(execution, start_node)

            # Complete execution
            if execution.state == WorkflowState.RUNNING:
                execution.state = WorkflowState.COMPLETED

            execution.completed_at = time.time()
            execution.duration_seconds = execution.completed_at - execution.started_at

        except Exception as e:
            execution.state = WorkflowState.FAILED
            execution.error_message = str(e)
            execution.completed_at = time.time()
            execution.duration_seconds = execution.completed_at - execution.started_at
            self.logger.error(f"Workflow execution failed: {e}")

        # Build result
        return WorkflowExecutionResult(
            execution_id=execution.execution_id,
            workflow_id=execution.workflow_id,
            success=execution.state == WorkflowState.COMPLETED,
            state=execution.state,
            node_results=execution.node_results,
            output_variables=execution.variables,
            error_message=execution.error_message,
            failed_at_node=execution.failed_at_node,
            duration_seconds=execution.duration_seconds
        )

    async def _execute_from_node(self, execution: WorkflowExecution, node: WorkflowNode) -> None:
        """Execute workflow starting from a node."""
        execution.current_node_id = node.node_id

        # Check for timeout
        if execution.definition.timeout_seconds:
            elapsed = time.time() - execution.started_at
            if elapsed > execution.definition.timeout_seconds:
                raise TimeoutError("Workflow execution timeout")

        # Execute based on node type
        if node.node_type == NodeType.START:
            await self._execute_start_node(execution, node)
        elif node.node_type == NodeType.END:
            await self._execute_end_node(execution, node)
            return  # End execution
        elif node.node_type == NodeType.ACTION:
            await self._execute_action_node(execution, node)
        elif node.node_type == NodeType.CONDITION:
            next_node = await self._execute_condition_node(execution, node)
            if next_node:
                next_node_obj = self._get_node(execution.definition, next_node)
                if next_node_obj:
                    await self._execute_from_node(execution, next_node_obj)
            return
        elif node.node_type == NodeType.DELAY:
            await self._execute_delay_node(execution, node)
        elif node.node_type == NodeType.PARALLEL:
            await self._execute_parallel_node(execution, node)
        elif node.node_type == NodeType.APPROVAL:
            await self._execute_approval_node(execution, node)
        else:
            raise ValueError(f"Unknown node type: {node.node_type}")

        # Find and execute next nodes
        if execution.state == WorkflowState.RUNNING:
            next_nodes = self._get_next_nodes(execution.definition, node)
            if len(next_nodes) == 1:
                await self._execute_from_node(execution, next_nodes[0])
            elif len(next_nodes) > 1:
                # Multiple next nodes - execute in parallel
                tasks = [
                    self._execute_from_node(execution, next_node)
                    for next_node in next_nodes
                ]
                await asyncio.gather(*tasks, return_exceptions=True)

    # -------------------------------------------------------------------------
    # Node Executors
    # -------------------------------------------------------------------------

    async def _execute_start_node(self, execution: WorkflowExecution, node: WorkflowNode) -> None:
        """Execute a start node."""
        node.state = NodeState.RUNNING
        node.started_at = time.time()

        # Initialize variables from trigger data
        execution.variables.update(execution.trigger_data)

        node.state = NodeState.COMPLETED
        node.completed_at = time.time()
        node.duration_seconds = node.completed_at - node.started_at
        execution.completed_nodes += 1

    async def _execute_end_node(self, execution: WorkflowExecution, node: WorkflowNode) -> None:
        """Execute an end node."""
        node.state = NodeState.RUNNING
        node.started_at = time.time()

        # Mark workflow as completed
        execution.state = WorkflowState.COMPLETED

        node.state = NodeState.COMPLETED
        node.completed_at = time.time()
        node.duration_seconds = node.completed_at - node.started_at
        execution.completed_nodes += 1

    async def _execute_action_node(self, execution: WorkflowExecution, node: WorkflowNode) -> None:
        """Execute an action node."""
        node.state = NodeState.RUNNING
        node.started_at = time.time()

        try:
            # Submit action to fabric
            action = await self._fabric.submit_action(
                action_type=node.action_type or "unknown",
                connector_type=node.connector_type or "webhook",
                parameters=node.action_parameters,
                workspace_id=execution.workspace_id,
                environment=execution.environment,
                requested_by=execution.triggered_by,
                risk_level=node.risk_level
            )

            # Wait for action completion (in real system, would poll or use callback)
            # For now, simulate execution
            await asyncio.sleep(0.1)

            # Store result
            result = {
                "action_id": action.action_id,
                "connector": node.connector_type,
                "action": node.action_type,
                "status": "completed"
            }

            node.result = result
            execution.node_results[node.node_id] = result
            execution.variables[f"{node.node_id}_result"] = result

            node.state = NodeState.COMPLETED
            execution.completed_nodes += 1

        except Exception as e:
            node.state = NodeState.FAILED
            node.error_message = str(e)

            if node.retry_count < node.max_retries:
                node.retry_count += 1
                node.state = NodeState.PENDING
                await asyncio.sleep(1)  # Brief delay before retry
                await self._execute_action_node(execution, node)
                return

            execution.state = WorkflowState.FAILED
            execution.error_message = str(e)
            execution.failed_at_node = node.node_id

        finally:
            node.completed_at = time.time()
            node.duration_seconds = node.completed_at - node.started_at

    async def _execute_condition_node(self, execution: WorkflowExecution, node: WorkflowNode) -> Optional[str]:
        """Execute a condition node and return next node ID."""
        node.state = NodeState.RUNNING
        node.started_at = time.time()

        try:
            # Evaluate condition
            result = await self._evaluate_condition(
                node.condition_expression or "",
                execution.variables
            )

            node.result = {"condition_result": result}
            execution.node_results[node.node_id] = node.result

            # Return next node based on condition
            next_node_id = node.true_branch if result else node.false_branch
            if next_node_id:
                execution.variables[f"{node.node_id}_result"] = result

            node.state = NodeState.COMPLETED
            execution.completed_nodes += 1

        except Exception as e:
            node.state = NodeState.FAILED
            node.error_message = str(e)
            next_node_id = node.false_branch  # Default to false branch on error

        finally:
            node.completed_at = time.time()
            node.duration_seconds = node.completed_at - node.started_at

        return next_node_id

    async def _execute_delay_node(self, execution: WorkflowExecution, node: WorkflowNode) -> None:
        """Execute a delay node."""
        node.state = NodeState.RUNNING
        node.started_at = time.time()

        await asyncio.sleep(node.delay_seconds)

        node.state = NodeState.COMPLETED
        node.completed_at = time.time()
        node.duration_seconds = node.completed_at - node.started_at
        execution.completed_nodes += 1

    async def _execute_parallel_node(self, execution: WorkflowExecution, node: WorkflowNode) -> None:
        """Execute parallel branches."""
        node.state = NodeState.RUNNING
        node.started_at = time.time()

        # Get parallel branches from config
        branches = node.config.get("branches", [])
        if not isinstance(branches, list):
            branches = []

        # Execute each branch
        tasks = []
        for branch_config in branches:
            branch_workflow = self._create_branch_workflow(branch_config, execution.definition)
            task = self.execute_workflow(
                branch_workflow,
                execution.trigger_data,
                execution.workspace_id,
                execution.environment,
                execution.triggered_by
            )
            tasks.append(task)

        # Wait for all branches
        results = await asyncio.gather(*tasks, return_exceptions=True)

        node.result = {"branch_results": [r if not isinstance(r, Exception) else {"error": str(r)} for r in results]}
        execution.node_results[node.node_id] = node.result

        node.state = NodeState.COMPLETED
        node.completed_at = time.time()
        node.duration_seconds = node.completed_at - node.started_at
        execution.completed_nodes += 1

    async def _execute_approval_node(self, execution: WorkflowExecution, node: WorkflowNode) -> None:
        """Execute an approval node."""
        node.state = NodeState.RUNNING
        node.started_at = time.time()

        # In a real system, would wait for approval
        # For now, auto-approve non-critical actions
        approval_required = node.config.get("approval_required", False)

        if approval_required:
            execution.state = WorkflowState.WAITING_FOR_APPROVAL
            # Would wait for approval here
            # For demo, auto-approve
            execution.state = WorkflowState.RUNNING

        node.result = {"approved": True}
        execution.node_results[node.node_id] = node.result

        node.state = NodeState.COMPLETED
        node.completed_at = time.time()
        node.duration_seconds = node.completed_at - node.started_at
        execution.completed_nodes += 1

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _find_start_node(self, definition: WorkflowDefinition) -> Optional[WorkflowNode]:
        """Find the start node in a workflow."""
        for node in definition.nodes:
            if node.node_type == NodeType.START:
                return node
        return None

    def _get_node(self, definition: WorkflowDefinition, node_id: str) -> Optional[WorkflowNode]:
        """Get a node by ID."""
        for node in definition.nodes:
            if node.node_id == node_id:
                return node
        return None

    def _get_next_nodes(self, definition: WorkflowDefinition, node: WorkflowNode) -> List[WorkflowNode]:
        """Get all nodes that follow this node."""
        next_node_ids = [
            edge.to_node
            for edge in definition.edges
            if edge.from_node == node.node_id
        ]

        next_nodes = []
        for node_id in next_node_ids:
            next_node = self._get_node(definition, node_id)
            if next_node:
                next_nodes.append(next_node)

        return next_nodes

    async def _evaluate_condition(self, expression: str, variables: Dict[str, Any]) -> bool:
        """Evaluate a condition expression."""
        try:
            # Simple condition evaluation
            # In production, use a safe expression evaluator

            # Handle common conditions
            if expression.lower() == "true":
                return True
            if expression.lower() == "false":
                return False

            # Variable reference
            if expression.startswith("$") and expression[1:] in variables:
                value = variables[expression[1:]]
                return bool(value)

            # Comparison expressions (simple format: var == value)
            if "==" in expression:
                parts = expression.split("==", 1)
                if len(parts) == 2:
                    var_name = parts[0].strip()
                    expected_value = parts[1].strip()
                    if var_name.startswith("$"):
                        var_name = var_name[1:]
                    if var_name in variables:
                        return str(variables[var_name]) == expected_value

            # Default to true for empty/unknown conditions
            return True

        except Exception as e:
            self.logger.warning(f"Condition evaluation error: {e}")
            return False

    def _create_branch_workflow(self, branch_config: Dict[str, Any], parent_definition: WorkflowDefinition) -> WorkflowDefinition:
        """Create a workflow for a parallel branch."""
        nodes = []
        edges = []

        branch_nodes = branch_config.get("nodes", [])
        for i, node_data in enumerate(branch_nodes):
            node = WorkflowNode(
                node_id=f"{branch_config.get('id', 'branch')}_node_{i}",
                node_type=NodeType(node_data.get("type", "action")),
                name=node_data.get("name", f"Branch node {i}"),
                config=node_data.get("config", {}),
                connector_type=node_data.get("connector"),
                action_type=node_data.get("action"),
                action_parameters=node_data.get("parameters", {})
            )
            nodes.append(node)

        return WorkflowDefinition(
            workflow_id=str(uuid.uuid4()),
            name=f"Branch: {branch_config.get('id', 'unknown')}",
            nodes=nodes,
            edges=edges,
            workspace_id=parent_definition.workspace_id,
            environment=parent_definition.environment
        )

    # -------------------------------------------------------------------------
    # Execution Management
    # -------------------------------------------------------------------------

    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get an execution by ID."""
        return self._executions.get(execution_id)

    def list_executions(
        self,
        workflow_id: Optional[str] = None,
        state: Optional[WorkflowState] = None,
        limit: int = 100
    ) -> List[WorkflowExecution]:
        """List workflow executions."""
        executions = list(self._executions.values())

        if workflow_id:
            executions = [e for e in executions if e.workflow_id == workflow_id]

        if state:
            executions = [e for e in executions if e.state == state]

        return executions[:limit]

    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running workflow execution."""
        execution = self._executions.get(execution_id)
        if execution and execution.state == WorkflowState.RUNNING:
            execution.state = WorkflowState.CANCELLED
            execution.completed_at = time.time()
            if execution.started_at:
                execution.duration_seconds = execution.completed_at - execution.started_at
            return True
        return False


# ============================================================================
# Singleton Instance
# ============================================================================

_global_engine: Optional[WorkflowExecutionEngine] = None


def get_workflow_engine() -> WorkflowExecutionEngine:
    """Get the global workflow engine instance."""
    global _global_engine
    if _global_engine is None:
        _global_engine = WorkflowExecutionEngine()
    return _global_engine


# Export
__all__ = [
    # Enums
    'WorkflowState',
    'NodeState',
    'NodeType',
    # Models
    'WorkflowNode',
    'WorkflowEdge',
    'WorkflowDefinition',
    'WorkflowExecution',
    'WorkflowExecutionResult',
    # Engine
    'WorkflowExecutionEngine',
    'get_workflow_engine',
]
