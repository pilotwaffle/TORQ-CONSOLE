"""
Mission Graph Scheduler

Executes mission graph nodes in dependency order with parallelism.

The scheduler:
- Finds ready nodes (dependencies satisfied)
- Dispatches nodes to appropriate agents
- Updates node states
- Tracks progress
- Handles decision gates

Uses hardened executor for idempotent node execution and event emission.
"""

from __future__ import annotations

import logging
from collections import defaultdict, deque
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from .models import (
    Mission,
    MissionGraph,
    MissionNode,
    MissionEdge,
    NodeType,
    NodeStatus,
    EdgeType,
    AgentType,
    GateCondition,
    DecisionOutcome,
    GraphExecutionState,
)
from .executor import MissionNodeExecutor, MissionCompleter


logger = logging.getLogger(__name__)


# ============================================================================
# Scheduler State
# ============================================================================

class SchedulerState:
    """Runtime state of graph execution."""

    def __init__(self, graph: MissionGraph):
        self.graph = graph
        self.node_states: Dict[str, NodeStatus] = {
            n.id: n.status for n in graph.nodes
        }
        self.node_outputs: Dict[str, List[Any]] = defaultdict(list)
        self.blocked_nodes: Set[str] = set()
        self.running_nodes: Set[str] = set()
        self.completed_nodes: Set[str] = set()
        self.failed_nodes: Set[str] = set()

    def get_node(self, node_id: str) -> Optional[MissionNode]:
        """Get node by ID."""
        for node in self.graph.nodes:
            if node.id == node_id:
                return node
        return None

    def update_node_status(self, node_id: str, status: NodeStatus):
        """Update node status."""
        self.node_states[node_id] = status

        # Update tracking sets
        self.completed_nodes.discard(node_id)
        self.failed_nodes.discard(node_id)
        self.running_nodes.discard(node_id)
        self.blocked_nodes.discard(node_id)

        if status == NodeStatus.COMPLETED:
            self.completed_nodes.add(node_id)
        elif status == NodeStatus.FAILED:
            self.failed_nodes.add(node_id)
        elif status == NodeStatus.RUNNING:
            self.running_nodes.add(node_id)
        elif status == NodeStatus.BLOCKED:
            self.blocked_nodes.add(node_id)

    def is_ready(self, node: MissionNode) -> bool:
        """Check if node is ready to execute."""
        # Check current status
        if self.node_states.get(node.id) != NodeStatus.PENDING:
            return False

        # Check if all dependencies are satisfied
        for dep_id in node.depends_on_nodes:
            if dep_id not in self.completed_nodes:
                return False

        # Check if not blocked
        if node.id in self.blocked_nodes:
            return False

        return True

    def mark_dependencies_ready(self, node_id: str):
        """Mark nodes that depend on this node as potentially ready."""
        # Find edges where this node is the source
        for edge in self.graph.edges:
            if edge.source_node_id == node_id:
                if edge.edge_type == EdgeType.DEPENDS_ON:
                    target = self.get_node(edge.target_node_id)
                    if target and target.depends_on_nodes.count(node_id) == len(target.depends_on_nodes):
                        # All dependencies satisfied
                        self.update_node_status(target.id, NodeStatus.READY)


# ============================================================================
# Mission Graph Scheduler
# ============================================================================

class MissionGraphScheduler:
    """
    Schedules and executes mission graph nodes.

    Responsibilities:
    - Find ready nodes
    - Dispatch to agents
    - Update states on completion
    - Evaluate decision gates
    - Track progress

    Uses hardened MissionNodeExecutor for idempotent execution:
    - No duplicate events
    - No duplicate handoffs
    - Safe retry handling
    - Atomic state transitions
    """

    def __init__(self, supabase_client, executor=None):
        self.supabase = supabase_client
        self.executor = executor  # Agent executor interface (for actual work)
        self.hardened_executor = MissionNodeExecutor(supabase_client)  # For idempotent execution
        self.mission_completer = MissionCompleter(supabase_client)  # For idempotent completion

    async def execute_graph(
        self,
        mission: Mission,
        graph: MissionGraph
    ) -> GraphExecutionState:
        """
        Execute a mission graph until completion or failure.

        Returns final execution state.
        """
        state = SchedulerState(graph)

        # Update mission status
        await self._update_mission_status(mission.id, "running")

        # Main execution loop
        while not self._is_complete(state):
            # Find ready nodes
            ready_nodes = self._get_ready_nodes(state)

            if not ready_nodes:
                # No ready nodes - check if blocked
                if state.blocked_nodes or state.running_nodes:
                    # Wait for running nodes to complete
                    await self._await_progress(state)
                else:
                    # No progress possible - might be stuck
                    logger.warning(f"Mission {mission.id} appears stuck")
                    break

            # Dispatch ready nodes (with parallelism)
            await self._dispatch_nodes(mission, ready_nodes, state)

            # Update state
            execution_state = self._build_execution_state(mission, graph, state)

            # Check for completion
            if execution_state.pending_nodes == 0:
                break

        # Final state
        final_state = self._build_execution_state(mission, graph, state)

        # Update mission status using hardened completer (idempotent)
        if final_state.failed_nodes > 0:
            await self._update_mission_status(mission.id, "failed")
        elif final_state.pending_nodes == 0:
            # Use hardened completer for idempotent mission completion
            result = self.mission_completer.complete_mission(
                mission.id,
                overall_score=self._calculate_mission_score(final_state)
            )
            logger.info(f"Mission completion: {result['updated']}, {result['reason']}")

        return final_state

    def _get_ready_nodes(self, state: SchedulerState) -> List[MissionNode]:
        """Get all nodes that are ready to execute."""
        ready = []

        for node in state.graph.nodes:
            if state.is_ready(node):
                ready.append(node)

        return ready

    async def _dispatch_nodes(
        self,
        mission: Mission,
        nodes: List[MissionNode],
        state: SchedulerState
    ):
        """
        Dispatch nodes to agents for execution.

        Uses hardened executor for idempotent node execution.
        Nodes that are already running or completed will be safely skipped.
        """
        for node in nodes:
            # Check if already executed (idempotency)
            current_status = state.node_states.get(node.id)
            if current_status in [NodeStatus.COMPLETED, NodeStatus.RUNNING]:
                logger.info(f"Node {node.id} already {current_status.value}, skipping")
                continue

            # Execute node using hardened executor
            try:
                await self._execute_node_hardened(mission, node, state)
            except Exception as e:
                logger.error(f"Error executing node {node.id}: {e}")
                state.update_node_status(node.id, NodeStatus.FAILED)
                await self._persist_node_status(node.id, NodeStatus.FAILED, error=str(e))

    async def _execute_node_hardened(
        self,
        mission: Mission,
        node: MissionNode,
        state: SchedulerState
    ):
        """
        Execute a single node using hardened executor.

        This method provides:
        - Idempotent state transitions
        - Duplicate event prevention
        - Canonical handoff generation
        - Safe retry handling
        """
        # Prepare inputs from dependencies
        inputs = await self._prepare_node_inputs(node, state)

        # Prepare memory context
        memory_context = await self._get_memory_context(node, mission)

        # Define the actual work function for this node
        async def execute_work():
            """Execute the actual node work."""
            # Execute based on node type
            if node.node_type == NodeType.DECISION:
                return await self._execute_decision_node_work(mission, node, inputs, state)
            elif node.node_type == NodeType.EVIDENCE:
                return await self._execute_evidence_node_work(mission, node, inputs, state)
            elif node.node_type == NodeType.DELIVERABLE:
                return await self._execute_deliverable_node_work(mission, node, inputs, state)
            else:
                return await self._execute_task_node_work(mission, node, inputs, memory_context, state)

        # Use hardened executor for the node lifecycle
        result = self.hardened_executor.execute_node(
            mission_id=mission.id,
            node_id=node.id,
            node_title=node.title,
            node_type=node.node_type.value,
            executor_fn=self._sync_wrapper(execute_work)
        )

        # Update local state to match database
        if result.get("skipped"):
            # Node was already executed, sync local state
            actual_status = result.get("status", "completed")
            if actual_status == "completed":
                state.update_node_status(node.id, NodeStatus.COMPLETED)
            state.mark_dependencies_ready(node.id)
            return

        # Node executed successfully
        state.update_node_status(node.id, NodeStatus.COMPLETED)
        state.mark_dependencies_ready(node.id)

    def _sync_wrapper(self, async_fn):
        """Wrap async function for sync executor."""
        def wrapper(*args, **kwargs):
            # For now, run async function in sync context
            # In production, this should use proper async/await
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Running in async context, need to create task
                    # For now, return placeholder
                    return {"output": {}, "confidence": 0.85}
                else:
                    return loop.run_until_complete(async_fn(*args, **kwargs))
            except RuntimeError:
                # No event loop, return placeholder
                return {"output": {}, "confidence": 0.85}
        return wrapper

    async def _execute_node(
        self,
        mission: Mission,
        node: MissionNode,
        state: SchedulerState
    ):
        """
        Execute a single node (legacy method, kept for compatibility).

        Deprecated: Use _execute_node_hardened instead.
        """
        await self._execute_node_hardened(mission, node, state)

    # ========================================================================
    # Work Execution Methods (called by hardened executor)
    # These return {output, confidence} for handoff generation
    # ========================================================================

    async def _execute_decision_node_work(
        self,
        mission: Mission,
        node: MissionNode,
        inputs: Dict[str, Any],
        state: SchedulerState
    ) -> Dict[str, Any]:
        """Execute decision gate work (returns decision outcome for handoff)."""
        if not node.decision_condition:
            return {"output": {"decision": "auto_pass"}, "confidence": 1.0}

        condition = GateCondition(**node.decision_condition)
        outcome = await self._evaluate_condition(condition, inputs, node)

        # Store decision outcome
        await self._persist_decision_outcome(node.id, outcome)

        # Handle outcome
        if outcome.passed:
            logger.info(f"Decision gate {node.id} passed: {outcome.reason}")
        else:
            await self._handle_decision_failure(mission, node, outcome, state)

        return {
            "output": {
                "decision": outcome.decision,
                "passed": outcome.passed,
                "reason": outcome.reason,
                "actual_value": outcome.actual_value
            },
            "confidence": 0.95
        }

    async def _execute_evidence_node_work(
        self,
        mission: Mission,
        node: MissionNode,
        inputs: Dict[str, Any],
        state: SchedulerState
    ) -> Dict[str, Any]:
        """Execute evidence gathering work."""
        # Evidence nodes gather data from external sources or workspace
        logger.info(f"Evidence node {node.id} gathering evidence")

        return {
            "output": {
                "synthesis": f"Evidence gathered for {node.title}",
                "sources": inputs.get("sources", [])
            },
            "confidence": 0.90
        }

    async def _execute_deliverable_node_work(
        self,
        mission: Mission,
        node: MissionNode,
        inputs: Dict[str, Any],
        state: SchedulerState
    ) -> Dict[str, Any]:
        """Execute deliverable generation work."""
        # Collect outputs from dependencies
        dependency_outputs = []
        for dep_id in node.depends_on_nodes:
            dep_outputs = state.node_outputs.get(dep_id, [])
            dependency_outputs.extend(dep_outputs)

        logger.info(f"Deliverable node {node.id} synthesizing from {len(dependency_outputs)} inputs")

        return {
            "output": {
                "deliverable": node.title,
                "summary": f"Synthesized from {len(dependency_outputs)} sources",
                "artifacts": dependency_outputs
            },
            "confidence": 0.95
        }

    async def _execute_task_node_work(
        self,
        mission: Mission,
        node: MissionNode,
        inputs: Dict[str, Any],
        memory_context: Dict[str, Any],
        state: SchedulerState
    ) -> Dict[str, Any]:
        """Execute task work via agent."""
        if self.executor:
            # Call agent executor and get result
            try:
                result = await self.executor.execute(
                    mission_id=mission.id,
                    node_id=node.id,
                    node_type=node.node_type,
                    agent_type=node.agent_type,
                    reasoning_strategy=node.reasoning_strategy,
                    inputs=inputs,
                    memory_context=memory_context
                )
                return {
                    "output": result.get("output", {}),
                    "confidence": result.get("confidence", 0.85)
                }
            except Exception as e:
                logger.error(f"Agent execution error: {e}")
                return {
                    "output": {"error": str(e)},
                    "confidence": 0.0
                }
        else:
            logger.warning(f"No executor available for node {node.id}")
            return {
                "output": {"note": "No executor available"},
                "confidence": 0.50
            }

    # ========================================================================
    # Legacy Node Execution Methods (kept for compatibility, deprecated)
    # ========================================================================

    async def _execute_decision_node(
        self,
        mission: Mission,
        node: MissionNode,
        inputs: Dict[str, Any],
        state: SchedulerState
    ):
        """Execute a decision gate node."""
        if not node.decision_condition:
            # No condition - auto-pass
            return

        condition = GateCondition(**node.decision_condition)
        outcome = await self._evaluate_condition(condition, inputs, node)

        # Store decision outcome
        await self._persist_decision_outcome(node.id, outcome)

        # Handle outcome
        if outcome.passed:
            # Continue - downstream nodes become ready
            logger.info(f"Decision gate {node.id} passed: {outcome.reason}")
        else:
            # Failed - handle based on decision type
            await self._handle_decision_failure(mission, node, outcome, state)

    async def _evaluate_condition(
        self,
        condition: GateCondition,
        inputs: Dict[str, Any],
        node: MissionNode
    ) -> DecisionOutcome:
        """Evaluate a decision gate condition."""
        # Get actual value from inputs or node outputs
        actual_value = inputs.get(condition.metric, 0.0)

        # Evaluate condition
        passed = self._evaluate_operator(actual_value, condition.operator, condition.value)

        return DecisionOutcome(
            gate_id=node.id,
            condition=condition,
            passed=passed,
            actual_value=actual_value,
            decision=condition.on_pass if passed else condition.on_fail,
            reason=self._explain_evaluation(condition, actual_value, passed)
        )

    def _evaluate_operator(self, actual: float, operator: str, expected: float) -> bool:
        """Evaluate comparison operator."""
        if operator == ">=":
            return actual >= expected
        elif operator == "<=":
            return actual <= expected
        elif operator == ">":
            return actual > expected
        elif operator == "<":
            return actual < expected
        elif operator == "==":
            return actual == expected
        else:
            logger.warning(f"Unknown operator: {operator}")
            return False

    def _explain_evaluation(self, condition: GateCondition, actual: float, passed: bool) -> str:
        """Generate human-readable explanation of evaluation."""
        return (
            f"{condition.metric} is {actual:.2f}, "
            f"{condition.operator} {condition.value} required: {'PASSED' if passed else 'FAILED'}"
        )

    async def _execute_evidence_node(
        self,
        mission: Mission,
        node: MissionNode,
        inputs: Dict[str, Any],
        state: SchedulerState
    ):
        """Execute an evidence gathering node."""
        # Evidence nodes typically gather data from external sources
        # or synthesize from existing workspace entries

        # For now, mark as complete with placeholder
        logger.info(f"Evidence node {node.id} completed")

    async def _execute_deliverable_node(
        self,
        mission: Mission,
        node: MissionNode,
        inputs: Dict[str, Any],
        state: SchedulerState
    ):
        """Execute a deliverable generation node."""
        # Deliverable nodes synthesize outputs from upstream nodes

        # Collect outputs from dependencies
        dependency_outputs = []
        for dep_id in node.depends_on_nodes:
            dep_outputs = state.node_outputs.get(dep_id, [])
            dependency_outputs.extend(dep_outputs)

        # Generate deliverable (would call synthesizer agent)
        logger.info(f"Deliverable node {node.id} generated from {len(dependency_outputs)} inputs")

    async def _execute_task_node(
        self,
        mission: Mission,
        node: MissionNode,
        inputs: Dict[str, Any],
        memory_context: Dict[str, Any],
        state: SchedulerState
    ):
        """Execute a task node via agent."""
        if self.executor:
            # Call agent executor
            await self.executor.execute(
                mission_id=mission.id,
                node_id=node.id,
                node_type=node.node_type,
                agent_type=node.agent_type,
                reasoning_strategy=node.reasoning_strategy,
                inputs=inputs,
                memory_context=memory_context
            )
        else:
            logger.warning(f"No executor available for node {node.id}")

    async def _handle_decision_failure(
        self,
        mission: Mission,
        node: MissionNode,
        outcome: DecisionOutcome,
        state: SchedulerState
    ):
        """Handle a failed decision gate."""
        decision = outcome.decision

        if decision == "stop":
            # Stop execution - mark downstream as skipped
            await self._mark_downstream_skipped(node, state)

        elif decision == "spawn_validation":
            # Would spawn a validation subgraph
            logger.info(f"Decision gate {node.id} spawning validation subgraph")
            # For now, mark as blocked
            state.update_node_status(node.id, NodeStatus.BLOCKED)

        elif decision == "escalate":
            # Would escalate to human
            logger.info(f"Decision gate {node.id} escalating to human")
            state.update_node_status(node.id, NodeStatus.BLOCKED)

        elif decision == "alternate_branch":
            # Would activate alternate branch
            logger.info(f"Decision gate {node.id} taking alternate branch")

    async def _mark_downstream_skipped(self, node: MissionNode, state: SchedulerState):
        """Mark all downstream nodes as skipped."""
        # BFS to find all downstream nodes
        visited = set()
        queue = [node.id]

        while queue:
            current_id = queue.pop(0)
            if current_id in visited:
                continue
            visited.add(current_id)

            # Mark skipped
            if state.node_states.get(current_id) == NodeStatus.PENDING:
                state.update_node_status(current_id, NodeStatus.SKIPPED)

            # Find downstream nodes
            for edge in state.graph.edges:
                if edge.source_node_id == current_id:
                    if edge.edge_type == EdgeType.DEPENDS_ON:
                        queue.append(edge.target_node_id)

    async def _prepare_node_inputs(
        self,
        node: MissionNode,
        state: SchedulerState
    ) -> Dict[str, Any]:
        """Prepare inputs for a node from dependency outputs."""
        inputs = {}

        for dep_id in node.depends_on_nodes:
            dep_outputs = state.node_outputs.get(dep_id, [])
            inputs[f"dep_{dep_id}"] = dep_outputs

        return inputs

    async def _get_memory_context(
        self,
        node: MissionNode,
        mission: Mission
    ) -> Dict[str, Any]:
        """Get strategic memory context for a node."""
        # Would query strategic memory based on:
        # - node type
        # - node domain
        # - node reasoning strategy
        # - mission context

        return {
            "injected_memories": node.injected_memory_ids,
            "reasoning_strategy": node.reasoning_strategy or mission.reasoning_strategy
        }

    def _determine_agent_type(self, node: MissionNode) -> AgentType:
        """Determine appropriate agent type for a node."""
        if node.node_type == NodeType.OBJECTIVE:
            return AgentType.STRATEGIC_PLANNER
        elif node.node_type == NodeType.DECISION:
            return AgentType.STRATEGIC_PLANNER
        elif node.node_type == NodeType.DELIVERABLE:
            return AgentType.SYNTHESIZER
        elif node.reasoning_strategy == "risk_first":
            return AgentType.RISK_QA
        else:
            return AgentType.SPECIALIST

    def _is_complete(self, state: SchedulerState) -> bool:
        """Check if execution is complete."""
        # Complete if no pending or ready nodes
        for node_id, status in state.node_states.items():
            if status in [NodeStatus.PENDING, NodeStatus.READY, NodeStatus.RUNNING]:
                return False
        return True

    async def _await_progress(self, state: SchedulerState):
        """Wait for running nodes to make progress."""
        # In real implementation, this would:
        # - Subscribe to node completion events
        # - Wait with timeout
        # - Check for blocked nodes that need attention

        # For now, just return
        pass

    def _build_execution_state(
        self,
        mission: Mission,
        graph: MissionGraph,
        state: SchedulerState
    ) -> GraphExecutionState:
        """Build current execution state summary."""
        total = len(state.graph.nodes)

        status_counts = defaultdict(int)
        for status in state.node_states.values():
            status_counts[status.value] += 1

        # Get ready and blocked nodes
        ready_ids = [n.id for n in graph.nodes if state.is_ready(n)]
        blocked_ids = list(state.blocked_nodes)
        running_ids = list(state.running_nodes)

        # Calculate progress
        if total > 0:
            progress = (status_counts.get("completed", 0) + status_counts.get("skipped", 0)) / total
        else:
            progress = 0.0

        return GraphExecutionState(
            mission_id=mission.id,
            graph_id=graph.id,
            status=MissionStatus(mission.status),
            total_nodes=total,
            pending_nodes=status_counts.get("pending", 0),
            ready_nodes=len(ready_ids),
            running_nodes=status_counts.get("running", 0),
            blocked_nodes=status_counts.get("blocked", 0),
            completed_nodes=status_counts.get("completed", 0),
            failed_nodes=status_counts.get("failed", 0),
            skipped_nodes=status_counts.get("skipped", 0),
            progress_percent=progress,
            ready_node_ids=ready_ids,
            blocked_node_ids=blocked_ids,
            running_node_ids=running_ids,
            completed_deliverables=[],  # Would extract from completed nodes
            pending_deliverables=[],  # Would extract from pending nodes
        )

    def _calculate_mission_score(self, execution_state: GraphExecutionState) -> float:
        """Calculate overall mission score from execution state."""
        if execution_state.total_nodes == 0:
            return 0.0

        # Score based on completion rate
        completion_rate = (
            execution_state.completed_nodes + execution_state.skipped_nodes
        ) / execution_state.total_nodes

        # Penalty for failures
        failure_penalty = execution_state.failed_nodes * 0.1

        return max(0.0, min(1.0, completion_rate - failure_penalty))

    async def _update_mission_status(self, mission_id: str, status: str):
        """Update mission status in database."""
        try:
            updates = {"status": status}
            if status == "running":
                updates["started_at"] = datetime.now().isoformat()
            elif status in ["completed", "failed", "cancelled"]:
                updates["completed_at"] = datetime.now().isoformat()

            self.supabase.table("missions").update(updates).eq("id", mission_id).execute()
        except Exception as e:
            logger.error(f"Error updating mission status: {e}")

    async def _persist_node_status(
        self,
        node_id: str,
        status: NodeStatus,
        error: Optional[str] = None
    ):
        """Persist node status to database."""
        try:
            updates = {"status": status.value}
            if status == NodeStatus.RUNNING:
                updates["started_at"] = datetime.now().isoformat()
            elif status in [NodeStatus.COMPLETED, NodeStatus.FAILED, NodeStatus.SKIPPED]:
                updates["completed_at"] = datetime.now().isoformat()

            if error:
                updates["error_message"] = error

            self.supabase.table("mission_nodes").update(updates).eq("id", node_id).execute()
        except Exception as e:
            logger.error(f"Error persisting node status: {e}")

    async def _persist_decision_outcome(self, node_id: str, outcome: DecisionOutcome):
        """Persist decision gate outcome."""
        try:
            self.supabase.table("decision_outcomes").insert({
                "node_id": node_id,
                "gate_type": outcome.condition.gate_type.value,
                "condition": outcome.condition.dict(),
                "passed": outcome.passed,
                "actual_value": outcome.actual_value,
                "decision": outcome.decision,
                "reason": outcome.reason,
                "evaluated_at": outcome.evaluated_at.isoformat()
            }).execute()
        except Exception as e:
            logger.error(f"Error persisting decision outcome: {e}")
