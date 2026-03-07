"""
Execution Planner - Converts triggers into execution plans.

The Execution Planner is responsible for:
- Converting triggers into execution plans
- Choosing specialist agents
- Defining tool policy
- Setting approval stage
- Deciding observe vs prepare vs execute
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from .models import (
    AutonomousTask, ExecutionMode, TriggerEvent,
    MonitorType, PolicyDecision
)


logger = logging.getLogger(__name__)


@dataclass
class ExecutionPlan:
    """
    A plan for executing an autonomous task.

    Defines how a trigger should be handled, including:
    - Which agents to use
    - What tools to invoke
    - Whether approval is needed
    - What the expected outcome is
    """
    task_type: str
    execution_mode: ExecutionMode
    agents: List[str]
    tool_policy: str  # required, preferred, optional
    approval_required: bool
    reason: str
    prompt_template: Optional[str] = None
    estimated_duration_seconds: int = 60
    risk_level: str = "low"


class ExecutionPlanner:
    """
    Planner for autonomous task execution.

    Responsibilities:
    - Analyze trigger events
    - Determine appropriate execution mode
    - Select specialist agents
    - Set tool requirements
    - Identify approval requirements
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def plan_from_trigger(
        self,
        event: TriggerEvent,
        monitor_config: Optional[Dict[str, Any]] = None
    ) -> ExecutionPlan:
        """
        Create an execution plan from a trigger event.

        Args:
            event: The trigger event
            monitor_config: Optional monitor configuration

        Returns:
            ExecutionPlan for handling the trigger
        """
        monitor_config = monitor_config or {}
        monitor_type = monitor_config.get("type", MonitorType.THRESHOLD)

        # Determine execution mode based on monitor config
        execution_mode = ExecutionMode(monitor_config.get(
            "execution_mode",
            "observe"  # Default to observe for safety
        ))

        # Select agents based on event type
        agents = self._select_agents_for_event(event, monitor_type)

        # Determine tool policy
        tool_policy = self._determine_tool_policy(event, monitor_type)

        # Check if approval is needed (basic check, refined by policy engine)
        approval_required = execution_mode == ExecutionMode.EXECUTE

        # Generate reason
        reason = self._generate_reason(event, monitor_type)

        # Create prompt template
        prompt_template = self._generate_prompt_template(event, monitor_type)

        return ExecutionPlan(
            task_type=f"{event.event_type.value}_handling",
            execution_mode=execution_mode,
            agents=agents,
            tool_policy=tool_policy,
            approval_required=approval_required,
            reason=reason,
            prompt_template=prompt_template,
            estimated_duration_seconds=self._estimate_duration(event, monitor_type),
            risk_level=self._assess_risk(event, execution_mode)
        )

    def _select_agents_for_event(
        self,
        event: TriggerEvent,
        monitor_type: MonitorType
    ) -> List[str]:
        """Select appropriate specialist agents for the event."""
        # Default agent assignments by event type
        agent_map = {
            MonitorType.HEALTH_CHECK: ["research_agent"],
            MonitorType.THRESHOLD: ["research_agent"],
            MonitorType.STATUS_CHANGE: ["orchestration_agent"],
            MonitorType.ABSENCE: ["orchestration_agent"],
            MonitorType.TOPIC: ["research_agent"],
            MonitorType.WORKFLOW_FAILURE: ["workflow_agent", "orchestration_agent"],
            MonitorType.POLICY_VIOLATION: ["orchestration_agent"],
        }

        return agent_map.get(monitor_type, ["research_agent"])

    def _determine_tool_policy(
        self,
        event: TriggerEvent,
        monitor_type: MonitorType
    ) -> str:
        """Determine if tools are required."""
        # Health checks and threshold monitoring require tools
        if monitor_type in [MonitorType.HEALTH_CHECK, MonitorType.THRESHOLD]:
            return "required"

        # Topic searches require tools
        if monitor_type == MonitorType.TOPIC:
            return "required"

        return "optional"

    def _generate_reason(
        self,
        event: TriggerEvent,
        monitor_type: MonitorType
    ) -> str:
        """Generate a human-readable reason for the execution."""
        return f"{monitor_type.value}_triggered: {event.event_type.value}"

    def _generate_prompt_template(
        self,
        event: TriggerEvent,
        monitor_type: MonitorType
    ) -> str:
        """Generate the prompt template for the task."""
        templates = {
            MonitorType.HEALTH_CHECK: (
                "Analyze the following health check event and provide a summary:\n"
                "Event: {event_type}\n"
                "Details: {payload}\n\n"
                "Provide:\n"
                "1. What happened\n"
                "2. Current status\n"
                "3. Recommended actions (if any)"
            ),
            MonitorType.THRESHOLD: (
                "A threshold has been crossed. Analyze and report:\n"
                "Threshold: {operator} {value}\n"
                "Current value: {current}\n"
                "Severity: {severity}\n\n"
                "Provide:\n"
                "1. Analysis of the threshold breach\n"
                "2. Potential impact\n"
                "3. Recommended next steps"
            ),
            MonitorType.STATUS_CHANGE: (
                "Status change detected. Analyze and report:\n"
                "Previous: {previous}\n"
                "Current: {current}\n\n"
                "Provide:\n"
                "1. What changed and why it matters\n"
                "2. Context and potential causes\n"
                "3. Suggested actions"
            ),
            MonitorType.TOPIC: (
                "Topic of interest detected. Provide a brief summary:\n"
                "Topic: {topic}\n"
                "Context: {context}\n\n"
                "Provide:\n"
                "1. Key information about this topic\n"
                "2. Why it might be relevant\n"
                "3. Suggested follow-up actions"
            ),
            MonitorType.WORKFLOW_FAILURE: (
                "Workflow execution failed. Analyze and recommend:\n"
                "Failure details: {details}\n\n"
                "Provide:\n"
                "1. Root cause analysis\n"
                "2. Potential fixes\n"
                "3. Prevention strategies"
            ),
        }

        # Get template and format with event data
        template = templates.get(
            monitor_type,
            "Analyze the following event and provide a summary: {payload}"
        )

        # Format template with event payload
        try:
            return template.format(**event.payload, event_type=event.event_type.value)
        except (KeyError, TypeError):
            # Fallback if template variables don't match
            return f"Analyze this event: {event.payload}"

    def _estimate_duration(
        self,
        event: TriggerEvent,
        monitor_type: MonitorType
    ) -> int:
        """Estimate execution duration in seconds."""
        duration_map = {
            MonitorType.HEALTH_CHECK: 30,
            MonitorType.THRESHOLD: 45,
            MonitorType.STATUS_CHANGE: 60,
            MonitorType.ABSENCE: 45,
            MonitorType.TOPIC: 90,
            MonitorType.WORKFLOW_FAILURE: 120,
            MonitorType.POLICY_VIOLATION: 60,
        }
        return duration_map.get(monitor_type, 60)

    def _assess_risk(self, event: TriggerEvent, execution_mode: ExecutionMode) -> str:
        """Assess the risk level of this execution."""
        # Risk is based on execution mode and event severity
        mode_risk = {
            ExecutionMode.OBSERVE: "low",
            ExecutionMode.PREPARE: "low",
            ExecutionMode.EXECUTE: "medium"
        }

        severity_risk = {
            "low": "low",
            "medium": "medium",
            "high": "high",
            "critical": "critical"
        }

        # Take the higher of mode and severity risk
        mode_r = mode_risk.get(execution_mode.value, "low")
        severity_r = severity_risk.get(event.severity, "low")

        if severity_r == "critical":
            return "critical"
        if severity_r == "high" or mode_r == "medium":
            return "high"
        if severity_r == "medium" or mode_r == "low":
            return "medium"
        return "low"

    async def plan_from_task_request(
        self,
        name: str,
        prompt: str,
        execution_mode: ExecutionMode,
        context: Dict[str, Any]
    ) -> ExecutionPlan:
        """
        Create an execution plan from a direct task request.

        Args:
            name: Task name
            prompt: User-provided prompt
            execution_mode: Requested execution mode
            context: Additional context

        Returns:
            ExecutionPlan for the task
        """
        # Select agents based on request content
        agents = self._select_agents_from_prompt(prompt, context)

        # Determine tool policy
        tool_policy = context.get("tool_policy", "optional")

        # Generate prompt template
        prompt_template = self._generate_prompt_from_request(name, prompt, context)

        return ExecutionPlan(
            task_type="user_requested_task",
            execution_mode=execution_mode,
            agents=agents,
            tool_policy=tool_policy,
            approval_required=execution_mode == ExecutionMode.EXECUTE,
            reason=f"User requested: {name}",
            prompt_template=prompt_template,
            estimated_duration_seconds=context.get("estimated_duration", 60),
            risk_level=context.get("risk_level", "low")
        )

    def _select_agents_from_prompt(
        self,
        prompt: str,
        context: Dict[str, Any]
    ) -> List[str]:
        """Select agents based on prompt content."""
        prompt_lower = prompt.lower()

        # Check for workflow indicators
        workflow_keywords = ["workflow", "automate", "pipeline", "process"]
        if any(kw in prompt_lower for kw in workflow_keywords):
            return ["workflow_agent"]

        # Check for complex planning indicators
        planning_keywords = ["plan", "strategy", "analyze from multiple"]
        if any(kw in prompt_lower for kw in planning_keywords):
            return ["orchestration_agent"]

        # Default to research agent
        return ["research_agent"]

    def _generate_prompt_from_request(
        self,
        name: str,
        prompt: str,
        context: Dict[str, Any]
    ) -> str:
        """Generate prompt template from user request."""
        return (
            f"Task: {name}\n"
            f"Request: {prompt}\n\n"
            f"Context: {context.get('additional_context', 'N/A')}\n\n"
            "Please execute this task and provide a comprehensive response."
        )


# Singleton instance
_execution_planner: Optional[ExecutionPlanner] = None


def get_execution_planner() -> ExecutionPlanner:
    """Get the singleton execution planner instance."""
    global _execution_planner
    if _execution_planner is None:
        _execution_planner = ExecutionPlanner()
    return _execution_planner
