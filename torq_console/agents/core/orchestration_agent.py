"""
Orchestration Agent - High-level agent coordination and orchestration.

Consolidates orchestration, routing, and coordination functionality into
a single agent that manages other agents and workflows.
"""

import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum

from .base_agent import BaseAgent, AgentCapability, AgentContext, AgentResult
from .interfaces import IOrchestrationAgent
from ..registry import get_agent_registry


class OrchestrationMode(str, Enum):
    """Orchestration execution modes."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    PIPELINE = "pipeline"
    DYNAMIC = "dynamic"
    COLLABORATIVE = "collaborative"


class OrchestrationStatus(str, Enum):
    """Orchestration execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentTask:
    """Individual task within an orchestration workflow."""
    task_id: str
    agent_id: str
    task_type: str
    parameters: Dict[str, Any]
    dependencies: List[str] = None
    timeout: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class OrchestrationPlan:
    """Plan for orchestration execution."""
    plan_id: str
    name: str
    description: str
    mode: OrchestrationMode
    tasks: List[AgentTask]
    timeout: Optional[float] = None
    metadata: Dict[str, Any] = None


@dataclass
class OrchestrationResult:
    """Result from orchestration execution."""
    plan_id: str
    status: OrchestrationStatus
    task_results: Dict[str, AgentResult]
    execution_time: float
    success_count: int
    failure_count: int
    metadata: Dict[str, Any] = None


class OrchestrationAgent(BaseAgent, IOrchestrationAgent):
    """
    Unified orchestration agent that coordinates other agents and workflows.

    Replaces multiple scattered orchestration systems:
    - Agent orchestration engines
    - Workflow coordination systems
    - Task planning and execution
    - Multi-agent coordination
    - Policy-driven routing systems

    Features:
    - Multiple orchestration modes (sequential, parallel, pipeline, dynamic)
    - Agent discovery and routing
    - Task dependency management
    - Error handling and retry logic
    - Performance monitoring and optimization
    - Real-time orchestration status tracking
    """

    def __init__(
        self,
        llm_provider=None,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize orchestration agent."""
        super().__init__(
            agent_id="orchestration_agent",
            agent_name="Orchestration Agent",
            capabilities=[
                AgentCapability.ORCHESTRATION,
                AgentCapability.WORKFLOW_AUTOMATION,
                AgentCapability.LEARNING
            ],
            llm_provider=llm_provider,
            config=config
        )

        # Agent registry reference
        self._agent_registry = get_agent_registry()

        # Orchestration state
        self._active_plans: Dict[str, OrchestrationPlan] = {}
        self._execution_history: List[OrchestrationResult] = []
        self._max_history_size = self.config.get("max_history_size", 100)

        # Orchestration settings
        self._default_timeout = self.config.get("default_timeout", 300)  # 5 minutes
        self._max_concurrent_tasks = self.config.get("max_concurrent_tasks", 10)
        self._task_semaphore = asyncio.Semaphore(self._max_concurrent_tasks)

        # Performance tracking
        self._performance_metrics = {
            "total_plans": 0,
            "successful_plans": 0,
            "failed_plans": 0,
            "average_execution_time": 0.0,
            "agent_usage": {}
        }

        self.logger.info("OrchestrationAgent initialized with agent coordination capabilities")

    async def _execute_request(
        self,
        request: str,
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Execute orchestration request."""
        # Try to parse as orchestration plan
        try:
            # This is a simplified implementation
            # In a real system, this would use AI to understand orchestration requests

            plan = await self._parse_orchestration_request(request, context)
            if plan:
                result = await self.execute_orchestration_plan(plan, context)
                return AgentResult(
                    success=result.status == OrchestrationStatus.COMPLETED,
                    content=self._format_orchestration_result(result),
                    confidence=0.9,
                    execution_time=result.execution_time,
                    metadata={
                        "plan_id": result.plan_id,
                        "status": result.status,
                        "task_count": len(result.task_results),
                        "success_rate": result.success_count / (result.success_count + result.failure_count) if (result.success_count + result.failure_count) > 0 else 0
                    }
                )
            else:
                return AgentResult(
                    success=False,
                    content="Could not parse orchestration request. Please specify agents, tasks, and execution mode.",
                    error="Invalid orchestration request"
                )

        except Exception as e:
            self.logger.error(f"Orchestration request failed: {e}")
            return AgentResult(
                success=False,
                content="Orchestration request failed to execute.",
                error=str(e)
            )

    async def orchestrate_agents(
        self,
        agents: List[str],
        workflow: Dict[str, Any],
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Orchestrate multiple agents in a workflow."""
        try:
            # Create orchestration plan
            plan_id = str(uuid.uuid4())
            mode = OrchestrationMode(workflow.get("mode", "sequential"))

            tasks = []
            for i, agent_id in enumerate(agents):
                task = AgentTask(
                    task_id=f"task_{i}",
                    agent_id=agent_id,
                    task_type=workflow.get("task_type", "general"),
                    parameters=workflow.get("parameters", {}),
                    timeout=workflow.get("timeout")
                )
                tasks.append(task)

            plan = OrchestrationPlan(
                plan_id=plan_id,
                name=workflow.get("name", "Agent Orchestration"),
                description=workflow.get("description", "Orchestrate multiple agents"),
                mode=mode,
                tasks=tasks,
                timeout=workflow.get("timeout"),
                metadata={"workflow": workflow, "context": context}
            )

            # Execute orchestration
            result = await self.execute_orchestration_plan(plan, context)

            return AgentResult(
                success=result.status == OrchestrationStatus.COMPLETED,
                content=self._format_orchestration_result(result),
                execution_time=result.execution_time,
                metadata={
                    "orchestration_id": plan_id,
                    "mode": mode,
                    "agents": agents
                }
            )

        except Exception as e:
            self.logger.error(f"Agent orchestration failed: {e}")
            return AgentResult(
                success=False,
                content="Failed to orchestrate agents.",
                error=str(e)
            )

    async def coordinate_workflow(
        self,
        workflow_definition: Dict[str, Any],
        context: Optional[AgentContext] = None
    ) -> AgentResult:
        """Coordinate a complex workflow."""
        try:
            # Parse workflow definition
            plan = await self._parse_workflow_definition(workflow_definition)
            if not plan:
                return AgentResult(
                    success=False,
                    content="Invalid workflow definition.",
                    error="Cannot parse workflow"
                )

            # Execute workflow
            result = await self.execute_orchestration_plan(plan, context)

            return AgentResult(
                success=result.status == OrchestrationStatus.COMPLETED,
                content=self._format_orchestration_result(result),
                execution_time=result.execution_time,
                metadata={
                    "workflow_id": result.plan_id,
                    "workflow_name": plan.name,
                    "step_count": len(plan.tasks)
                }
            )

        except Exception as e:
            self.logger.error(f"Workflow coordination failed: {e}")
            return AgentResult(
                success=False,
                content="Failed to coordinate workflow.",
                error=str(e)
            )

    async def execute_orchestration_plan(
        self,
        plan: OrchestrationPlan,
        context: Optional[AgentContext] = None
    ) -> OrchestrationResult:
        """Execute an orchestration plan."""
        start_time = asyncio.get_event_loop().time()

        # Register plan
        self._active_plans[plan.plan_id] = plan
        self._performance_metrics["total_plans"] += 1

        try:
            self.logger.info(f"Executing orchestration plan {plan.plan_id} with mode {plan.mode}")

            # Execute based on mode
            if plan.mode == OrchestrationMode.SEQUENTIAL:
                task_results = await self._execute_sequential(plan.tasks, context)
            elif plan.mode == OrchestrationMode.PARALLEL:
                task_results = await self._execute_parallel(plan.tasks, context)
            elif plan.mode == OrchestrationMode.PIPELINE:
                task_results = await self._execute_pipeline(plan.tasks, context)
            elif plan.mode == OrchestrationMode.DYNAMIC:
                task_results = await self._execute_dynamic(plan.tasks, context)
            else:
                raise ValueError(f"Unsupported orchestration mode: {plan.mode}")

            execution_time = asyncio.get_event_loop().time() - start_time

            # Determine overall status
            success_count = sum(1 for result in task_results.values() if result.success)
            failure_count = len(task_results) - success_count

            status = (
                OrchestrationStatus.COMPLETED if failure_count == 0
                else OrchestrationStatus.FAILED if success_count == 0
                else OrchestrationStatus.COMPLETED  # Partial success counts as completed
            )

            # Create result
            result = OrchestrationResult(
                plan_id=plan.plan_id,
                status=status,
                task_results=task_results,
                execution_time=execution_time,
                success_count=success_count,
                failure_count=failure_count,
                metadata={
                    "mode": plan.mode,
                    "context": context.metadata if context else {}
                }
            )

            # Update metrics
            if status == OrchestrationStatus.COMPLETED:
                self._performance_metrics["successful_plans"] += 1
            else:
                self._performance_metrics["failed_plans"] += 1

            self._update_performance_metrics(result)
            self._add_to_history(result)

            self.logger.info(
                f"Orchestration plan {plan.plan_id} completed: "
                f"{success_count} success, {failure_count} failures in {execution_time:.2f}s"
            )

            return result

        except Exception as e:
            self.logger.error(f"Orchestration plan {plan.plan_id} failed: {e}")

            execution_time = asyncio.get_event_loop().time() - start_time
            result = OrchestrationResult(
                plan_id=plan.plan_id,
                status=OrchestrationStatus.FAILED,
                task_results={},
                execution_time=execution_time,
                success_count=0,
                failure_count=len(plan.tasks),
                metadata={"error": str(e)}
            )

            self._performance_metrics["failed_plans"] += 1
            self._add_to_history(result)

            return result

        finally:
            # Clean up active plan
            self._active_plans.pop(plan.plan_id, None)

    async def _execute_sequential(
        self,
        tasks: List[AgentTask],
        context: Optional[AgentContext]
    ) -> Dict[str, AgentResult]:
        """Execute tasks sequentially."""
        results = {}

        for task in tasks:
            try:
                result = await self._execute_task(task, context)
                results[task.task_id] = result

                # Stop on first failure if strict mode
                if not result.success and self.config.get("strict_sequential", False):
                    self.logger.warning(f"Sequential execution stopped due to task {task.task_id} failure")
                    break

            except Exception as e:
                self.logger.error(f"Task {task.task_id} failed: {e}")
                results[task.task_id] = AgentResult(
                    success=False,
                    content=f"Task execution failed: {str(e)}",
                    error=str(e)
                )

                if self.config.get("strict_sequential", False):
                    break

        return results

    async def _execute_parallel(
        self,
        tasks: List[AgentTask],
        context: Optional[AgentContext]
    ) -> Dict[str, AgentResult]:
        """Execute tasks in parallel."""
        async def execute_single_task(task: AgentTask) -> Tuple[str, AgentResult]:
            try:
                result = await self._execute_task(task, context)
                return task.task_id, result
            except Exception as e:
                self.logger.error(f"Parallel task {task.task_id} failed: {e}")
                return task.task_id, AgentResult(
                    success=False,
                    content=f"Task execution failed: {str(e)}",
                    error=str(e)
                )

        # Execute all tasks concurrently
        coroutines = [execute_single_task(task) for task in tasks]
        results_list = await asyncio.gather(*coroutines, return_exceptions=True)

        # Convert to dict
        results = {}
        for item in results_list:
            if isinstance(item, Exception):
                self.logger.error(f"Parallel execution error: {item}")
                continue
            task_id, result = item
            results[task_id] = result

        return results

    async def _execute_pipeline(
        self,
        tasks: List[AgentTask],
        context: Optional[AgentContext]
    ) -> Dict[str, AgentResult]:
        """Execute tasks as a pipeline (output of one becomes input to next)."""
        results = {}
        pipeline_context = context

        for i, task in enumerate(tasks):
            try:
                # Add previous results to task parameters for pipeline flow
                if i > 0:
                    task.parameters["pipeline_input"] = results.get(tasks[i-1].task_id, AgentResult(success=False, content="")).content

                result = await self._execute_task(task, pipeline_context)
                results[task.task_id] = result

                # Update pipeline context with task result
                if result.success:
                    if not pipeline_context:
                        pipeline_context = AgentContext(
                            session_id=f"pipeline_{task.task_id}",
                            metadata={"pipeline_results": {}}
                        )
                    pipeline_context.metadata["pipeline_results"][task.task_id] = result

            except Exception as e:
                self.logger.error(f"Pipeline task {task.task_id} failed: {e}")
                results[task.task_id] = AgentResult(
                    success=False,
                    content=f"Pipeline task failed: {str(e)}",
                    error=str(e)
                )
                break  # Stop pipeline on failure

        return results

    async def _execute_dynamic(
        self,
        tasks: List[AgentTask],
        context: Optional[AgentContext]
    ) -> Dict[str, Any]:
        """Execute tasks dynamically with adaptive routing and optimization."""
        # Simplified dynamic execution - would use AI for optimization in real system
        self.logger.info("Executing tasks with dynamic orchestration")

        # For now, fall back to parallel execution
        return await self._execute_parallel(tasks, context)

    async def _execute_task(
        self,
        task: AgentTask,
        context: Optional[AgentContext]
    ) -> AgentResult:
        """Execute a single task."""
        async with self._task_semaphore:
            self.logger.debug(f"Executing task {task.task_id} on agent {task.agent_id}")

            # Get agent instance
            agent = await self._agent_registry.get_agent_instance(task.agent_id)
            if not agent:
                return AgentResult(
                    success=False,
                    content=f"Agent {task.agent_id} not available",
                    error="Agent not found"
                )

            # Execute task with timeout
            timeout = task.timeout or self._default_timeout

            try:
                result = await asyncio.wait_for(
                    agent.process_request(
                        str(task.parameters),
                        context
                    ),
                    timeout=timeout
                )

                # Update agent usage metrics
                if task.agent_id not in self._performance_metrics["agent_usage"]:
                    self._performance_metrics["agent_usage"][task.agent_id] = 0
                self._performance_metrics["agent_usage"][task.agent_id] += 1

                return result

            except asyncio.TimeoutError:
                return AgentResult(
                    success=False,
                    content=f"Task {task.task_id} timed out after {timeout}s",
                    error="Timeout"
                )

            except Exception as e:
                # Retry logic
                if task.retry_count < task.max_retries:
                    self.logger.warning(f"Task {task.task_id} failed, retrying ({task.retry_count + 1}/{task.max_retries})")
                    task.retry_count += 1
                    await asyncio.sleep(1)  # Brief delay before retry
                    return await self._execute_task(task, context)
                else:
                    return AgentResult(
                        success=False,
                        content=f"Task {task.task_id} failed after {task.max_retries} retries: {str(e)}",
                        error=str(e)
                    )

    async def _parse_orchestration_request(
        self,
        request: str,
        context: Optional[AgentContext]
    ) -> Optional[OrchestrationPlan]:
        """Parse orchestration request from natural language."""
        # This is a simplified implementation
        # In a real system, this would use LLM or AI to parse complex requests

        request_lower = request.lower()

        # Simple pattern matching
        if "coordinate" in request_lower or "orchestrate" in request_lower:
            # Try to extract agent names from request
            agents = []
            if "conversational" in request_lower:
                agents.append("conversational_agent")
            if "workflow" in request_lower:
                agents.append("workflow_agent")
            if "research" in request_lower:
                agents.append("research_agent")

            if agents:
                mode = OrchestrationMode.PARALLEL if "parallel" in request_lower else OrchestrationMode.SEQUENTIAL

                tasks = [
                    AgentTask(
                        task_id=f"task_{i}",
                        agent_id=agent_id,
                        task_type="orchestration",
                        parameters={"request": request}
                    )
                    for i, agent_id in enumerate(agents)
                ]

                return OrchestrationPlan(
                    plan_id=str(uuid.uuid4()),
                    name="Parsed Orchestration",
                    description="Orchestration plan parsed from request",
                    mode=mode,
                    tasks=tasks
                )

        return None

    async def _parse_workflow_definition(
        self,
        workflow_definition: Dict[str, Any]
    ) -> Optional[OrchestrationPlan]:
        """Parse workflow definition into orchestration plan."""
        try:
            plan_id = workflow_definition.get("id", str(uuid.uuid4()))
            name = workflow_definition.get("name", "Workflow")
            description = workflow_definition.get("description", "")
            mode = OrchestrationMode(workflow_definition.get("mode", "sequential"))

            tasks = []
            for i, step in enumerate(workflow_definition.get("steps", [])):
                task = AgentTask(
                    task_id=step.get("id", f"step_{i}"),
                    agent_id=step.get("agent", "workflow_agent"),
                    task_type=step.get("type", "general"),
                    parameters=step.get("parameters", {}),
                    timeout=step.get("timeout"),
                    dependencies=step.get("dependencies", [])
                )
                tasks.append(task)

            return OrchestrationPlan(
                plan_id=plan_id,
                name=name,
                description=description,
                mode=mode,
                tasks=tasks,
                timeout=workflow_definition.get("timeout")
            )

        except Exception as e:
            self.logger.error(f"Failed to parse workflow definition: {e}")
            return None

    def _format_orchestration_result(self, result: OrchestrationResult) -> str:
        """Format orchestration result for display."""
        lines = [
            f"## Orchestration Result ({result.plan_id})",
            f"**Status:** {result.status}",
            f"**Execution Time:** {result.execution_time:.2f}s",
            f"**Tasks:** {result.success_count + result.failure_count} total, {result.success_count} successful, {result.failure_count} failed",
            ""
        ]

        for task_id, task_result in result.task_results.items():
            status = "✅ Success" if task_result.success else "❌ Failed"
            lines.append(f"### Task {task_id}: {status}")

            if task_result.content:
                lines.append(f"**Output:** {task_result.content[:200]}{'...' if len(task_result.content) > 200 else ''}")

            if task_result.error:
                lines.append(f"**Error:** {task_result.error}")

            lines.append("")

        return "\n".join(lines)

    def _update_performance_metrics(self, result: OrchestrationResult) -> None:
        """Update performance metrics."""
        # Update average execution time
        total_time = (
            self._performance_metrics["average_execution_time"] * (self._performance_metrics["total_plans"] - 1) +
            result.execution_time
        )
        self._performance_metrics["average_execution_time"] = total_time / self._performance_metrics["total_plans"]

    def _add_to_history(self, result: OrchestrationResult) -> None:
        """Add result to execution history."""
        self._execution_history.append(result)

        # Maintain history size limit
        if len(self._execution_history) > self._max_history_size:
            self._execution_history = self._execution_history[-self._max_history_size:]

    def get_active_plans(self) -> List[Dict[str, Any]]:
        """Get list of active orchestration plans."""
        active_plans = []
        for plan in self._active_plans.values():
            plan_info = {
                "plan_id": plan.plan_id,
                "name": plan.name,
                "mode": plan.mode,
                "task_count": len(plan.tasks),
                "description": plan.description
            }
            active_plans.append(plan_info)
        return active_plans

    def get_execution_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get orchestration execution history."""
        history = []
        for result in self._execution_history:
            result_info = {
                "plan_id": result.plan_id,
                "status": result.status,
                "execution_time": result.execution_time,
                "task_count": len(result.task_results),
                "success_count": result.success_count,
                "failure_count": result.failure_count
            }
            history.append(result_info)

        if limit:
            return history[-limit:]
        return history

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get orchestration performance metrics."""
        return self._performance_metrics.copy()

    async def _health_check_impl(self) -> bool:
        """Agent-specific health check."""
        try:
            # Check agent registry connectivity
            stats = self._agent_registry.get_registry_stats()
            return stats["total_agents"] >= 0  # Basic connectivity check

        except Exception as e:
            self.logger.error(f"Orchestration agent health check failed: {e}")
            return False

    async def _reset_impl(self) -> None:
        """Reset agent-specific state."""
        # Cancel active plans
        self._active_plans.clear()

        # Clear history
        self._execution_history.clear()

    def get_agent_info(self) -> Dict[str, Any]:
        """Get detailed agent information."""
        base_info = super().get_agent_info() if hasattr(super(), 'get_agent_info') else {}

        orchestration_info = {
            "active_plans": len(self._active_plans),
            "execution_history_size": len(self._execution_history),
            "performance_metrics": self.get_performance_metrics(),
            "max_concurrent_tasks": self._max_concurrent_tasks,
            "default_timeout": self._default_timeout
        }

        if base_info:
            base_info.update(orchestration_info)
            return base_info

        return orchestration_info


# Register the agent
register_agent(
    OrchestrationAgent,
    "orchestration_agent",
    "Orchestration Agent",
    [
        AgentCapability.ORCHESTRATION,
        AgentCapability.WORKFLOW_AUTOMATION,
        AgentCapability.LEARNING
    ],
    config={
        "max_concurrent_tasks": 10,
        "default_timeout": 300,
        "max_history_size": 100,
        "strict_sequential": False
    },
    metadata={
        "description": "Unified orchestration agent that coordinates other agents and workflows",
        "replaces": [
            "marvin_orchestrator",
            "agent_system_enhancements",
            "policy_driven_router",
            "handoff_optimizer",
            "coordination_benchmark"
        ],
        "features": [
            "Multiple orchestration modes",
            "Agent discovery and routing",
            "Task dependency management",
            "Performance monitoring",
            "Error handling and retries"
        ]
    }
)