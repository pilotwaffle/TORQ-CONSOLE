"""
Execution Plan - Multi-Agent Orchestration Contract

Defines the structure for coordinated multi-agent execution plans
that Prince Flowers creates and manages.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import (
    Any, Dict, List, Optional, Set,
    Callable, Awaitable, Union
)

from pydantic import BaseModel, Field


class ExecutionMode(str, Enum):
    """Execution mode for multi-agent operations."""
    SINGLE_AGENT = "single"           # One agent handles entire request
    SEQUENTIAL = "sequential"         # Agents work in sequence, output passes to next
    PARALLEL = "parallel"             # Agents work simultaneously, results combined
    HIERARCHICAL = "hierarchical"     # Lead agent delegates to sub-agents
    CONSENSUS = "consensus"          # Multiple agents collaborate, results voted/aggregated
    AUTO = "auto"                     # System chooses best mode


class TaskPriority(str, Enum):
    """Priority levels for autonomous tasks."""
    CRITICAL = "critical"    # Immediate execution required
    HIGH = "high"           # Execute soon
    NORMAL = "normal"       # Standard queue position
    LOW = "low"           # Can be deferred


class AgentRole(str, Enum):
    """Standard roles for agents in multi-agent execution."""
    EXECUTIVE = "executive"       # Prince Flowers - coordinates and decides
    RESEARCHER = "researcher"     # Research Agent - information gathering
    WORKFLOW = "workflow"        # Workflow Agent - execution/automation
    CONVERSATIONAL = "conversational"  # Conversational Agent - drafting/chat
    ORCHESTRATOR = "orchestrator"    # Orchestration Agent - complex coordination


@dataclass
class AgentTask:
    """
    A single task assigned to an agent.

    Attributes:
        task_id: Unique identifier for this task
        agent_id: Which agent should handle this task
        agent_role: The role this agent plays in the execution
        prompt: The specific prompt/request for this agent
        dependencies: IDs of tasks that must complete first
        output_key: Key to store this task's output for other agents
        timeout_seconds: Maximum time to allow for this task
        retries: Number of retries allowed on failure
    """
    task_id: str
    agent_id: str
    agent_role: AgentRole
    prompt: str
    dependencies: List[str] = field(default_factory=list)
    output_key: Optional[str] = None
    timeout_seconds: int = 120
    retries: int = 2
    status: str = "pending"  # pending, running, completed, failed, skipped
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

    def is_ready(self, completed_tasks: Set[str]) -> bool:
        """Check if this task's dependencies are satisfied."""
        return all(dep in completed_tasks for dep in self.dependencies)

    @property
    def execution_time(self) -> Optional[float]:
        """Get task execution time if completed."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None


@dataclass
class ExecutionPlan:
    """
    A complete execution plan for multi-agent coordination.

    Prince Flowers creates these plans to coordinate specialist agents.
    The plan defines what agents to use, in what order, and how to combine results.

    Attributes:
        plan_id: Unique identifier for this plan
        mode: How agents should work together
        priority: How urgent this plan is
        tasks: List of agent tasks to execute
        final_synthesis: How to combine agent outputs into final response
        created_at: When this plan was created
        estimated_duration: Estimated total execution time
    """
    plan_id: str
    mode: ExecutionMode
    priority: TaskPriority
    tasks: List[AgentTask]
    final_synthesis: str
    created_at: float
    estimated_duration: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    routing_reason: str = ""
    tools_required: List[str] = field(default_factory=list)
    approval_required: bool = False

    # Execution state
    status: str = "created"  # created, running, completed, failed, cancelled
    current_task_index: int = 0
    completed_tasks: Set[str] = field(default_factory=set)
    failed_tasks: Set[str] = field(default_factory=set)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

    @property
    def is_complete(self) -> bool:
        """Check if all tasks are complete."""
        return len(self.completed_tasks) == len(self.tasks)

    @property
    def is_failed(self) -> bool:
        """Check if any critical task has failed."""
        return len(self.failed_tasks) > 0

    @property
    def execution_time(self) -> Optional[float]:
        """Get total execution time if completed."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None

    @property
    def progress(self) -> float:
        """Get progress as percentage (0.0 - 1.0)."""
        if not self.tasks:
            return 1.0
        return len(self.completed_tasks) / len(self.tasks)

    def get_ready_tasks(self) -> List[AgentTask]:
        """Get tasks whose dependencies are satisfied and are pending."""
        return [
            task for task in self.tasks
            if task.status == "pending"
            and task.is_ready(self.completed_tasks)
        ]

    def get_task_by_id(self, task_id: str) -> Optional[AgentTask]:
        """Find a task by its ID."""
        for task in self.tasks:
            if task.task_id == task_id:
                return task
        return None

    def mark_task_started(self, task_id: str) -> None:
        """Mark a task as started."""
        task = self.get_task_by_id(task_id)
        if task:
            task.status = "running"
            task.started_at = time.time()

    def mark_task_completed(self, task_id: str, result: Dict[str, Any]) -> None:
        """Mark a task as completed with its result."""
        task = self.get_task_by_id(task_id)
        if task:
            task.status = "completed"
            task.completed_at = time.time()
            task.result = result
            self.completed_tasks.add(task_id)

    def mark_task_failed(self, task_id: str, error: str) -> None:
        """Mark a task as failed."""
        task = self.get_task_by_id(task_id)
        if task:
            task.status = "failed"
            task.completed_at = time.time()
            task.error = error
            self.failed_tasks.add(task_id)

    def to_dict(self) -> Dict[str, Any]:
        """Convert plan to dictionary for serialization."""
        return {
            "plan_id": self.plan_id,
            "mode": self.mode.value,
            "priority": self.priority.value,
            "status": self.status,
            "tasks": [
                {
                    "task_id": t.task_id,
                    "agent_id": t.agent_id,
                    "agent_role": t.agent_role.value,
                    "prompt": t.prompt[:200] + "..." if len(t.prompt) > 200 else t.prompt,
                    "dependencies": t.dependencies,
                    "status": t.status,
                }
                for t in self.tasks
            ],
            "final_synthesis": self.final_synthesis,
            "created_at": self.created_at,
            "estimated_duration": self.estimated_duration,
            "progress": self.progress,
            "routing_reason": self.routing_reason,
            "tools_required": self.tools_required,
            "approval_required": self.approval_required,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ExecutionPlan:
        """Create plan from dictionary (for deserialization)."""
        tasks = [
            AgentTask(
                task_id=t["task_id"],
                agent_id=t["agent_id"],
                agent_role=AgentRole(t["agent_role"]),
                prompt=t["prompt"],
                dependencies=t.get("dependencies", []),
                status=t.get("status", "pending"),
            )
            for t in data.get("tasks", [])
        ]

        plan = cls(
            plan_id=data["plan_id"],
            mode=ExecutionMode(data["mode"]),
            priority=TaskPriority(data["priority"]),
            tasks=tasks,
            final_synthesis=data["final_synthesis"],
            created_at=data["created_at"],
            estimated_duration=data["estimated_duration"],
            metadata=data.get("metadata", {}),
            routing_reason=data.get("routing_reason", ""),
            tools_required=data.get("tools_required", []),
            approval_required=data.get("approval_required", False),
        )

        # Restore state
        plan.status = data.get("status", "created")
        plan.completed_tasks = set(data.get("completed_tasks", []))
        plan.failed_tasks = set(data.get("failed_tasks", []))

        return plan


# ============================================================================
# Plan Builder
# ============================================================================

class ExecutionPlanBuilder:
    """
    Builder for creating execution plans.

    Provides a fluent interface for constructing multi-agent plans.
    """

    def __init__(self):
        self.reset()

    def reset(self) -> None:
        """Reset builder for new plan."""
        self.plan_id: Optional[str] = None
        self.mode: ExecutionMode = ExecutionMode.SINGLE_AGENT
        self.priority: TaskPriority = TaskPriority.NORMAL
        self.tasks: List[AgentTask] = []
        self.synthesis: str = "Combine all agent responses into a coherent answer."
        self.routing_reason: str = ""
        self.tools_required: List[str] = []
        self.approval_required: bool = False
        self.metadata: Dict[str, Any] = {}

    def with_id(self, plan_id: str) -> ExecutionPlanBuilder:
        """Set plan ID."""
        self.plan_id = plan_id
        return self

    def with_mode(self, mode: ExecutionMode) -> ExecutionPlanBuilder:
        """Set execution mode."""
        self.mode = mode
        return self

    def with_priority(self, priority: TaskPriority) -> ExecutionPlanBuilder:
        """Set priority."""
        self.priority = priority
        return self

    def with_synthesis(self, synthesis: str) -> ExecutionPlanBuilder:
        """Set final synthesis instructions."""
        self.synthesis = synthesis
        return self

    def with_routing_reason(self, reason: str) -> ExecutionPlanBuilder:
        """Set routing reason."""
        self.routing_reason = reason
        return self

    def require_tools(self, tools: List[str]) -> ExecutionPlanBuilder:
        """Specify required tools."""
        self.tools_required = tools
        return self

    def require_approval(self, required: bool = True) -> ExecutionPlanBuilder:
        """Set whether approval is required."""
        self.approval_required = required
        return self

    def with_metadata(self, **kwargs) -> ExecutionPlanBuilder:
        """Add metadata."""
        self.metadata.update(kwargs)
        return self

    def add_task(
        self,
        agent_id: str,
        agent_role: AgentRole,
        prompt: str,
        dependencies: Optional[List[str]] = None,
        output_key: Optional[str] = None,
        timeout: int = 120
    ) -> ExecutionPlanBuilder:
        """Add a task to the plan."""
        task = AgentTask(
            task_id=f"{self.plan_id or 'plan'}_task_{len(self.tasks)}",
            agent_id=agent_id,
            agent_role=agent_role,
            prompt=prompt,
            dependencies=dependencies or [],
            output_key=output_key,
            timeout_seconds=timeout
        )
        self.tasks.append(task)
        return self

    def build(self) -> ExecutionPlan:
        """Build the execution plan."""
        if not self.plan_id:
            self.plan_id = f"plan_{uuid.uuid4().hex[:8]}"

        # Calculate estimated duration
        total_duration = sum(task.timeout_seconds for task in self.tasks)
        if self.mode == ExecutionMode.PARALLEL:
            total_duration = max((task.timeout_seconds for task in self.tasks), default=60)

        return ExecutionPlan(
            plan_id=self.plan_id,
            mode=self.mode,
            priority=self.priority,
            tasks=self.tasks,
            final_synthesis=self.synthesis,
            created_at=time.time(),
            estimated_duration=total_duration,
            metadata=self.metadata,
            routing_reason=self.routing_reason,
            tools_required=self.tools_required,
            approval_required=self.approval_required
        )


# ============================================================================
# Predefined Plan Templates
# ============================================================================

class PlanTemplates:
    """Predefined execution plan templates for common patterns."""

    @staticmethod
    def research_plan(query: str, agent_id: str = "research_agent") -> ExecutionPlan:
        """Create a research-focused single-agent plan."""
        return (ExecutionPlanBuilder()
                .with_id(f"research_{uuid.uuid4().hex[:8]}")
                .with_mode(ExecutionMode.SINGLE_AGENT)
                .with_priority(TaskPriority.NORMAL)
                .with_synthesis("Present the research findings clearly and comprehensively.")
                .with_routing_reason("research_query")
                .require_tools(["web_search"])
                .add_task(
                    agent_id=agent_id,
                    agent_role=AgentRole.RESEARCHER,
                    prompt=query,
                    timeout=60
                )
                .build())

    @staticmethod
    def research_then_synthesis(
        query: str,
        research_agent: str = "research_agent",
        synthesis_agent: str = "torq_prince_flowers"
    ) -> ExecutionPlan:
        """Create a plan that researches then synthesizes results."""
        plan_id = f"synthesis_{uuid.uuid4().hex[:8]}"
        return (ExecutionPlanBuilder()
                .with_id(plan_id)
                .with_mode(ExecutionMode.SEQUENTIAL)
                .with_priority(TaskPriority.NORMAL)
                .with_synthesis("Create a comprehensive response based on the research findings.")
                .with_routing_reason("research_then_synthesis")
                .require_tools(["web_search"])
                .add_task(
                    agent_id=research_agent,
                    agent_role=AgentRole.RESEARCHER,
                    prompt=f"Research this query: {query}",
                    output_key="research_findings",
                    timeout=60
                )
                .add_task(
                    agent_id=synthesis_agent,
                    agent_role=AgentRole.EXECUTIVE,
                    prompt=f"Synthesize the research findings into a clear, comprehensive response to: {query}",
                    dependencies=[f"{plan_id}_task_0"],
                    timeout=60
                )
                .build())

    @staticmethod
    def parallel_analysis(
        query: str,
        agents: List[str],
        synthesis_agent: str = "torq_prince_flowers"
    ) -> ExecutionPlan:
        """Create a plan where multiple agents analyze in parallel."""
        plan_id = f"parallel_{uuid.uuid4().hex[:8]}"
        builder = (ExecutionPlanBuilder()
                  .with_id(plan_id)
                  .with_mode(ExecutionMode.PARALLEL)
                  .with_priority(TaskPriority.NORMAL)
                  .with_synthesis("Combine insights from all specialist agents into a unified response."))

        # Add parallel analysis tasks
        for i, agent in enumerate(agents):
            builder.add_task(
                agent_id=agent,
                agent_role=AgentRole.WORKFLOW,
                prompt=f"Analyze this query from your perspective: {query}",
                output_key=f"analysis_{i}",
                timeout=60
            )

        # Add synthesis task
        builder.add_task(
            agent_id=synthesis_agent,
            agent_role=AgentRole.EXECUTIVE,
            prompt=f"Synthesize all analyses into a comprehensive response to: {query}",
            dependencies=[f"{plan_id}_task_{i}" for i in range(len(agents))],
            timeout=90
        )

        return builder.build()

    @staticmethod
    def workflow_with_research(
        goal: str,
        research_agent: str = "research_agent",
        workflow_agent: str = "workflow_agent",
        synthesis_agent: str = "torq_prince_flowers"
    ) -> ExecutionPlan:
        """Create a plan that researches then builds a workflow."""
        plan_id = f"workflow_{uuid.uuid4().hex[:8]}"
        return (ExecutionPlanBuilder()
                .with_id(plan_id)
                .with_mode(ExecutionMode.SEQUENTIAL)
                .with_priority(TaskPriority.HIGH)
                .with_synthesis("Present the research findings and the proposed workflow.")
                .with_routing_reason("workflow_with_research")
                .require_tools(["web_search"])
                .add_task(
                    agent_id=research_agent,
                    agent_role=AgentRole.RESEARCHER,
                    prompt=f"Research current best practices for: {goal}",
                    output_key="best_practices",
                    timeout=90
                )
                .add_task(
                    agent_id=workflow_agent,
                    agent_role=AgentRole.WORKFLOW,
                    prompt=f"Based on the research, design a workflow for: {goal}",
                    dependencies=[f"{plan_id}_task_0"],
                    output_key="workflow_design",
                    timeout=120
                )
                .add_task(
                    agent_id=synthesis_agent,
                    agent_role=AgentRole.EXECUTIVE,
                    prompt=f"Present the research and workflow design for: {goal}",
                    dependencies=[f"{plan_id}_task_0", f"{plan_id}_task_1"],
                    timeout=60
                )
                .build())
