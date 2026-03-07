"""
Agent Coordinator - Multi-Agent Execution Engine

Executes multi-agent plans by coordinating specialist agents
in the correct order with proper dependency management.
"""

from __future__ import annotations

import asyncio
import time
import logging
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field

from .execution_plan import (
    ExecutionPlan, AgentTask, ExecutionMode,
    AgentRole, TaskPriority
)
from .delegation import DelegationRequest, DelegationResult, DelegationEngine
from ..core.base_agent import BaseAgent, AgentContext, AgentResult


logger = logging.getLogger(__name__)


@dataclass
class ExecutionSummary:
    """
    Summary of a multi-agent execution.

    Collects results from all agents and provides final synthesis.
    """
    plan_id: str
    mode: ExecutionMode
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    total_time: float
    agent_results: List[Dict[str, Any]] = field(default_factory=list)
    final_response: str = ""
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_tasks == 0:
            return 1.0
        return self.completed_tasks / self.total_tasks

    @property
    def is_successful(self) -> bool:
        """Check if execution was successful."""
        # Consider successful if no critical tasks failed
        return self.failed_tasks == 0 or self.success_rate >= 0.5


class AgentCoordinator:
    """
    Coordinates multi-agent execution.

    Responsibilities:
    - Execute plans in the correct mode (sequential, parallel, etc.)
    - Manage task dependencies
    - Handle agent communication
    - Collect and aggregate results
    - Implement retry logic
    """

    def __init__(self, agent_registry=None):
        self.agent_registry = agent_registry
        self.delegation_engine = DelegationEngine()
        self.logger = logging.getLogger(__name__)

        # Execution tracking
        self._active_plans: Dict[str, ExecutionPlan] = {}
        self._plan_history: List[ExecutionSummary] = []

    async def execute_plan(
        self,
        plan: ExecutionPlan,
        context: Dict[str, Any],
        agent_getter: callable
    ) -> ExecutionSummary:
        """
        Execute a multi-agent plan.

        Args:
            plan: The execution plan to run
            context: Execution context
            agent_getter: Async callable to get agent by ID

        Returns:
            ExecutionSummary with all results
        """
        start_time = time.time()

        self.logger.info(
            f"Executing plan {plan.plan_id} in {plan.mode.value} mode "
            f"with {len(plan.tasks)} tasks"
        )

        plan.status = "running"
        plan.started_at = start_time
        self._active_plans[plan.plan_id] = plan

        try:
            # Execute based on mode
            if plan.mode == ExecutionMode.SEQUENTIAL:
                summary = await self._execute_sequential(plan, context, agent_getter)
            elif plan.mode == ExecutionMode.PARALLEL:
                summary = await self._execute_parallel(plan, context, agent_getter)
            elif plan.mode == ExecutionMode.HIERARCHICAL:
                summary = await self._execute_hierarchical(plan, context, agent_getter)
            elif plan.mode == ExecutionMode.SINGLE_AGENT:
                summary = await self._execute_single_agent(plan, context, agent_getter)
            else:
                # Default to sequential
                summary = await self._execute_sequential(plan, context, agent_getter)

            # Finalize summary
            summary.total_time = time.time() - start_time
            plan.completed_at = time.time()

            if summary.is_successful:
                plan.status = "completed"
            else:
                plan.status = "failed"

            self._plan_history.append(summary)
            return summary

        except Exception as e:
            self.logger.error(f"Plan {plan.plan_id} execution failed: {e}")
            plan.status = "failed"
            plan.completed_at = time.time()

            return ExecutionSummary(
                plan_id=plan.plan_id,
                mode=plan.mode,
                total_tasks=len(plan.tasks),
                completed_tasks=len(plan.completed_tasks),
                failed_tasks=len(plan.failed_tasks),
                total_time=time.time() - start_time,
                errors=[str(e)],
                metadata={"exception": str(e)}
            )

    async def _execute_sequential(
        self,
        plan: ExecutionPlan,
        context: Dict[str, Any],
        agent_getter: callable
    ) -> ExecutionSummary:
        """Execute tasks in sequence (output of one feeds into next)."""
        agent_results = []

        for task in plan.tasks:
            if not task.is_ready(plan.completed_tasks):
                break

            self.logger.info(f"Sequential: executing task {task.task_id}")

            # Mark task started
            plan.mark_task_started(task.task_id)

            # Execute task
            result = await self._execute_task(task, context, agent_getter, plan)

            # Update plan state
            if result.success or task.error:  # Even if failed, move to next if no retry
                plan.mark_task_completed(task.task_id, {
                    "content": result.content,
                    "data": result.data,
                    "success": result.success
                })
                agent_results.append({
                    "task_id": task.task_id,
                    "agent_id": result.agent_id,
                    "role": result.agent_role.value,
                    "content": result.content,
                    "success": result.success
                })

            # If task failed and was critical, stop
            if not result.success and self._is_critical_task(task):
                plan.mark_task_failed(task.task_id, result.error or "Task failed")
                break

        return self._build_summary(plan, agent_results)

    async def _execute_parallel(
        self,
        plan: ExecutionPlan,
        context: Dict[str, Any],
        agent_getter: callable
    ) -> ExecutionSummary:
        """Execute independent tasks in parallel."""
        # Find tasks with no dependencies
        ready_tasks = [t for t in plan.tasks if t.is_ready(plan.completed_tasks)]

        agent_results = []
        futures = []

        # Launch all ready tasks in parallel
        for task in ready_tasks:
            plan.mark_task_started(task.task_id)

            # Create async task
            async def execute_and_record(task):
                result = await self._execute_task(task, context, agent_getter, plan)
                plan.mark_task_completed(task.task_id, {
                    "content": result.content,
                    "data": result.data,
                    "success": result.success
                })
                return {
                    "task_id": task.task_id,
                    "agent_id": result.agent_id,
                    "role": result.agent_role.value,
                    "content": result.content,
                    "success": result.success
                }

            futures.append(execute_and_record(task))

        # Wait for all to complete
        results = await asyncio.gather(*futures, return_exceptions=True)

        # Process results
        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"Parallel task failed: {result}")
            else:
                agent_results.append(result)

        return self._build_summary(plan, agent_results)

    async def _execute_hierarchical(
        self,
        plan: ExecutionPlan,
        context: Dict[str, Any],
        agent_getter: callable
    ) -> ExecutionSummary:
        """Execute with lead agent delegating to sub-agents."""
        # Find the lead/orchestrator task (usually first)
        lead_tasks = [t for t in plan.tasks if t.agent_role == AgentRole.ORCHESTRATOR]

        if not lead_tasks:
            # No orchestrator, fall back to sequential
            return await self._execute_sequential(plan, context, agent_getter)

        # Execute orchestrator first
        lead_task = lead_tasks[0]
        plan.mark_task_started(lead_task.task_id)

        orchestrator_context = AgentContext(
            session_id=context.get("session_id", ""),
            metadata={
                **context,
                "subordinate_tasks": [
                    t.task_id for t in plan.tasks if t != lead_task
                ]
            }
        )

        lead_result = await self._execute_task(
            lead_task,
            orchestrator_context,
            agent_getter,
            plan
        )

        plan.mark_task_completed(lead_task.task_id, {
            "content": lead_result.content,
            "data": lead_result.data,
            "success": lead_result.success
        })

        # Continue with remaining tasks
        return await self._execute_sequential(plan, context, agent_getter)

    async def _execute_single_agent(
        self,
        plan: ExecutionPlan,
        context: Dict[str, Any],
        agent_getter: callable
    ) -> ExecutionSummary:
        """Execute with single agent (all tasks go to same agent)."""
        if not plan.tasks:
            return ExecutionSummary(
                plan_id=plan.plan_id,
                mode=plan.mode,
                total_tasks=0,
                completed_tasks=0,
                failed_tasks=0,
                total_time=0,
                final_response="No tasks to execute"
            )

        # Execute first task
        task = plan.tasks[0]
        plan.mark_task_started(task.task_id)

        result = await self._execute_task(task, context, agent_getter, plan)

        plan.mark_task_completed(task.task_id, {
            "content": result.content,
            "data": result.data,
            "success": result.success
        })

        return ExecutionSummary(
            plan_id=plan.plan_id,
            mode=plan.mode,
            total_tasks=len(plan.tasks),
            completed_tasks=1 if result.success else 0,
            failed_tasks=0 if result.success else 1,
            total_time=result.execution_time,
            agent_results=[{
                "task_id": task.task_id,
                "agent_id": result.agent_id,
                "role": result.agent_role.value,
                "content": result.content,
                "success": result.success
            }],
            final_response=result.content,
            metadata=result.metadata
        )

    async def _execute_task(
        self,
        task: AgentTask,
        context: Dict[str, Any],
        agent_getter: callable,
        plan: ExecutionPlan
    ) -> DelegationResult:
        """Execute a single agent task."""
        self.logger.info(f"Executing task {task.task_id} with agent {task.agent_id}")

        # Get agent
        agent = await agent_getter(task.agent_id)
        if not agent:
            return DelegationResult(
                request_id=task.task_id,
                success=False,
                agent_id=task.agent_id,
                agent_role=task.agent_role,
                content="",
                error=f"Agent {task.agent_id} not found"
            )

        # Prepare context with previous task outputs
        task_context = AgentContext(
            session_id=context.get("session_id", ""),
            metadata={
                **context,
                "task_outputs": {
                    t.task_id: t.result
                    for t in plan.tasks
                    if t.task_id in plan.completed_tasks and t.result
                }
            }
        )

        # Execute
        agent_result = await agent.process_request(task.prompt, task_context)

        return DelegationResult(
            request_id=task.task_id,
            success=agent_result.success,
            agent_id=task.agent_id,
            agent_role=task.agent_role,
            content=agent_result.content,
            data=agent_result.metadata,
            execution_time=agent_result.execution_time,
            error=agent_result.error,
            metadata={
                "confidence": agent_result.confidence,
                "tokens_used": agent_result.tokens_used
            }
        )

    def _build_summary(
        self,
        plan: ExecutionPlan,
        agent_results: List[Dict[str, Any]]
    ) -> ExecutionSummary:
        """Build execution summary from plan and results."""
        completed = len(plan.completed_tasks)
        failed = len(plan.failed_tasks)

        # Collect errors
        errors = []
        for result in agent_results:
            if not result.get("success", True):
                task = plan.get_task_by_id(result.get("task_id", ""))
                error_msg = result.get("error") or task.error if task else "Unknown error"
                errors.append(f"{task.task_id if task else 'unknown'}: {error_msg}")

        # Combine responses
        if len(agent_results) == 1:
            final_response = agent_results[0].get("content", "")
        else:
            # Multiple agents - combine their responses
            responses = [r.get("content", "") for r in agent_results if r.get("success")]
            final_response = "\n\n".join(responses)

        return ExecutionSummary(
            plan_id=plan.plan_id,
            mode=plan.mode,
            total_tasks=len(plan.tasks),
            completed_tasks=completed,
            failed_tasks=failed,
            total_time=time.time() - plan.started_at if plan.started_at else 0,
            agent_results=agent_results,
            final_response=final_response,
            errors=errors,
            metadata={
                "progress": plan.progress,
                "routing_reason": plan.routing_reason
            }
        )

    def _is_critical_task(self, task: AgentTask) -> bool:
        """Check if a task is critical (failure should stop execution)."""
        # Tasks with no retry are considered critical
        return task.retries == 0


# ============================================================================
# Agent Registry Integration
# ============================================================================

class AgentGetter:
    """Wrapper for getting agents from various sources."""

    def __init__(self, registry=None, fallback_agents=None):
        self.registry = registry
        self.fallback_agents = fallback_agents or {}

    async def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get agent instance by ID."""
        # Try registry first
        if self.registry:
            agent = await self.registry.get_agent(agent_id)
            if agent:
                # Extract the actual agent instance if wrapped
                return agent

        # Try fallback
        return self.fallback_agents.get(agent_id)
