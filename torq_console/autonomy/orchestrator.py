"""
Autonomous Orchestrator - Integration layer for autonomous operations.

This module ties together Phase 4's executive controller with Phase 5's
autonomous task engine, trigger engine, and policy engine.

Prince Flowers becomes the executive controller for autonomous operations.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable

from .models import (
    Monitor, TriggerEvent, AutonomousTask,
    ExecutionMode, TaskState, PolicyDecision
)
from .task_engine import TaskEngine, get_task_engine
from .trigger_engine import TriggerEngine, get_trigger_engine
from .policy_engine import PolicyEngine, get_policy_engine
from .approval_manager import ApprovalManager, get_approval_manager
from .execution_planner import ExecutionPlanner, get_execution_planner
from .state_store import StateStore, get_state_store

# Integration with Phase 4
from ..agents.orchestration.executive_controller import (
    ExecutiveController, ExecutiveDecision
)
from ..agents.orchestration.execution_plan import (
    AgentRole, PlanTemplates
)


logger = logging.getLogger(__name__)


class AutonomousOrchestrator:
    """
    Orchestrator for autonomous operations in TORQ Console.

    This is the main integration point that:
    - Connects trigger events to task creation
    - Applies policy engine decisions
    - Routes tasks through approval workflow
    - Executes tasks via specialist agents
    - Maintains audit trail

    Prince Flowers (via ExecutiveController) uses this orchestrator
    to manage autonomous operations.
    """

    def __init__(
        self,
        state_store: Optional[StateStore] = None,
        executive_controller: Optional[ExecutiveController] = None
    ):
        # Initialize components
        self.state_store = state_store or get_state_store()
        self.task_engine = get_task_engine(self.state_store)
        self.trigger_engine = get_trigger_engine(self.state_store)
        self.policy_engine = get_policy_engine()
        self.approval_manager = get_approval_manager(self.state_store)
        self.execution_planner = get_execution_planner()
        self.executive = executive_controller

        self.logger = logging.getLogger(__name__)

        # Wire up trigger engine to task creation
        self.trigger_engine.add_event_handler(self._on_trigger_event)

    async def start(self):
        """Start all autonomous components."""
        await self.task_engine.start()
        await self.trigger_engine.start()
        await self.approval_manager.start()
        self.logger.info("Autonomous orchestrator started")

    async def stop(self):
        """Stop all autonomous components."""
        await self.task_engine.stop()
        await self.trigger_engine.stop()
        await self.approval_manager.stop()
        self.logger.info("Autonomous orchestrator stopped")

    async def register_monitor(self, monitor: Monitor) -> bool:
        """Register a new autonomous monitor."""
        return self.trigger_engine.register_monitor(monitor)

    async def unregister_monitor(self, monitor_id: str) -> bool:
        """Unregister a monitor."""
        return self.trigger_engine.unregister_monitor(monitor_id)

    def list_monitors(
        self,
        workspace_id: Optional[str] = None
    ) -> List[Monitor]:
        """List all monitors."""
        return self.trigger_engine.list_monitors(workspace_id)

    async def _on_trigger_event(self, event: TriggerEvent):
        """
        Handle a trigger event by creating an autonomous task.

        This is the main integration point between triggers and tasks.
        """
        self.logger.info(f"Handling trigger event: {event.event_id}")

        try:
            # Load monitor configuration
            monitor = self.trigger_engine.get_monitor(event.monitor_id)
            if not monitor:
                self.logger.error(f"Monitor not found: {event.monitor_id}")
                return

            # Create execution plan
            plan = await self.execution_planner.plan_from_trigger(
                event,
                {
                    "type": monitor.type,
                    "execution_mode": monitor.execution_mode,
                    "action_policy": monitor.action_policy
                }
            )

            # Create task from plan
            task = await self.task_engine.create_task(
                name=f"{plan.task_type}_{event.monitor_id}",
                execution_mode=plan.execution_mode,
                trigger_event=event,
                monitor_id=event.monitor_id,
                agents=plan.agents,
                prompt_template=plan.prompt_template,
                parameters={
                    "plan": plan.__dict__,
                    "monitor_config": monitor.model_dump()
                },
                workspace_id=event.workspace_id or monitor.workspace_id,
                environment=event.environment or monitor.environment
            )

            # Evaluate policy
            context = {
                "workspace_id": task.workspace_id,
                "environment": task.environment
            }

            policy_decision = self.policy_engine.evaluate(task, context)
            task.policy_decision = policy_decision

            # Handle approval requirement
            if policy_decision.requires_approval:
                approval = await self.approval_manager.create_approval_request(
                    task,
                    policy_decision
                )

                if approval:
                    task.approval_id = approval.approval_id
                    task.state = TaskState.WAITING_FOR_APPROVAL

                    self.logger.info(
                        f"Task {task.task_id} requires approval: {approval.approval_id}"
                    )
            else:
                # Task can proceed
                self.logger.info(
                    f"Task {task.task_id} approved by policy: {policy_decision.reason}"
                )

        except Exception as e:
            self.logger.error(f"Error handling trigger event: {e}")

    async def execute_task_via_specialists(
        self,
        task: AutonomousTask
    ) -> Dict[str, Any]:
        """
        Execute a task via specialist agents.

        This integrates with Phase 4's executive controller and agent coordinator.
        """
        self.logger.info(f"Executing task {task.task_id} via specialists")

        try:
            # Determine agent role
            agent_roles = {
                "research_agent": AgentRole.RESEARCHER,
                "workflow_agent": AgentRole.WORKFLOW,
                "orchestration_agent": AgentRole.ORCHESTRATOR,
                "conversational_agent": AgentRole.CONVERSATIONAL
            }

            # Create Phase 4 execution plan
            if len(task.agents) == 1:
                # Single agent plan
                agent_id = task.agents[0]
                agent_role = agent_roles.get(agent_id, AgentRole.RESEARCHER)
                plan = PlanTemplates.research_plan(
                    task.prompt_template or task.name,
                    agent_id
                )
            else:
                # Multi-agent plan
                plan = PlanTemplates.parallel_analysis(
                    task.prompt_template or task.name,
                    task.agents
                )

            # Execute via agent coordinator (would use real agents in production)
            # For Phase 5A, return a mock result
            result = {
                "success": True,
                "content": f"Task {task.name} executed successfully by {', '.join(task.agents)}",
                "data": {
                    "agents_used": task.agents,
                    "execution_mode": task.execution_mode.value
                },
                "agent_results": [
                    {
                        "agent_id": agent_id,
                        "content": f"Processed by {agent_id}",
                        "success": True
                    }
                    for agent_id in task.agents
                ]
            }

            return result

        except Exception as e:
            self.logger.error(f"Error executing task {task.task_id}: {e}")
            raise

    async def get_autonomous_summary(self) -> Dict[str, Any]:
        """Get a summary of autonomous operations."""
        return {
            "monitors": {
                "total": len(self.list_monitors()),
                "active": len([m for m in self.list_monitors() if m.enabled])
            },
            "tasks": self.task_engine.get_metrics(),
            "approvals": {
                "pending": len(await self.approval_manager.inbox.get_pending_approvals()),
                "total": len(await self.approval_manager.list_approvals())
            },
            "is_running": all([
                self.task_engine._running,
                self.trigger_engine._running,
                self.approval_manager._running
            ])
        }


# Singleton instance
_autonomous_orchestrator: Optional[AutonomousOrchestrator] = None


def get_autonomous_orchestrator(
    state_store: Optional[StateStore] = None,
    executive_controller: Optional[ExecutiveController] = None
) -> AutonomousOrchestrator:
    """Get the singleton autonomous orchestrator instance."""
    global _autonomous_orchestrator
    if _autonomous_orchestrator is None:
        _autonomous_orchestrator = AutonomousOrchestrator(
            state_store=state_store,
            executive_controller=executive_controller
        )
    return _autonomous_orchestrator
