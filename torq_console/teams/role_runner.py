"""
Agent Teams - Role Runner

Phase 5.2: Agent Teams as a governed execution primitive.

This module executes individual role tasks within a team,
handling agent invocation and output capture.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from .models import (
    TeamRole,
    RoleTask,
    RoleTaskState,
    TeamExecutionStatus,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Agent Type Mapping
# ============================================================================

AGENT_TYPE_MAPPING = {
    # Planning roles
    TeamRole.LEAD: "planner_agent",
    TeamRole.STRATEGIST: "strategist_agent",

    # Research roles
    TeamRole.RESEARCHER: "research_agent",

    # Build roles
    TeamRole.BUILDER: "builder_agent",

    # Review roles
    TeamRole.CRITIC: "critic_agent",
    TeamRole.REVIEWER: "critic_agent",

    # Validation roles
    TeamRole.VALIDATOR: "validator_agent",
}


# ============================================================================
# Role Runner
# ============================================================================

class RoleRunner:
    """
    Executes individual role tasks within a team.

    Responsibilities:
    - Invoke appropriate agent for role
    - Capture role output
    - Track role state and confidence
    - Handle role errors
    """

    def __init__(self, supabase):
        """
        Initialize the role runner.

        Args:
            supabase: Supabase client
        """
        self.supabase = supabase
        self._active_tasks: Dict[UUID, RoleTask] = {}

    async def execute_role(
        self,
        team_execution_id: UUID,
        role: TeamRole,
        agent_type: str,
        objective: str,
        input_data: Dict[str, Any],
        timeout_seconds: int = 300,
    ) -> RoleTask:
        """
        Execute a role task.

        Args:
            team_execution_id: Parent team execution ID
            role: Role to execute
            agent_type: Type of agent to invoke
            objective: Task objective
            input_data: Input data for the role
            timeout_seconds: Execution timeout

        Returns:
            Completed role task
        """
        # Create task
        task = RoleTask(
            id=uuid4(),
            team_execution_id=team_execution_id,
            role=role,
            objective=objective,
            input_data=input_data,
            status=RoleTaskState.ASSIGNED,
        )

        self._active_tasks[task.id] = task
        logger.info(f"Executing role {role.value} for team execution {team_execution_id}")

        try:
            # Update to working
            task.status = RoleTaskState.WORKING
            task.started_at = datetime.utcnow()

            # Execute the role
            output, confidence = await self._invoke_agent(
                agent_type, objective, input_data, timeout_seconds
            )

            # Store results
            task.output = output
            task.confidence = confidence
            task.status = RoleTaskState.APPROVED
            task.completed_at = datetime.utcnow()

            logger.info(
                f"Role {role.value} completed with confidence {confidence:.2f}"
            )

        except asyncio.TimeoutError:
            task.status = RoleTaskState.FAILED
            task.error_message = f"Role execution timed out after {timeout_seconds}s"
            task.completed_at = datetime.utcnow()
            logger.error(f"Role {role.value} timed out")

        except Exception as e:
            task.status = RoleTaskState.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()
            logger.error(f"Role {role.value} failed: {e}")

        finally:
            # Remove from active tasks
            self._active_tasks.pop(task.id, None)

        return task

    async def _invoke_agent(
        self,
        agent_type: str,
        objective: str,
        input_data: Dict[str, Any],
        timeout_seconds: int,
    ) -> tuple[Dict[str, Any], float]:
        """
        Invoke an agent for role execution.

        Args:
            agent_type: Type of agent to invoke
            objective: Task objective
            input_data: Input data
            timeout_seconds: Execution timeout

        Returns:
            Tuple of (output, confidence)
        """
        # For MVP, we'll simulate agent execution with pattern-based responses
        # In production, this would call the actual agent framework

        role = agent_type.replace("_agent", "")

        # Simulate processing time
        await asyncio.sleep(0.5)

        # Generate role-specific output
        output, confidence = self._simulate_role_output(role, objective, input_data)

        return output, confidence

    def _simulate_role_output(
        self,
        role: str,
        objective: str,
        input_data: Dict[str, Any],
    ) -> tuple[Dict[str, Any], float]:
        """
        Simulate role output for MVP testing.

        TODO: Replace with actual agent invocation in production.

        Args:
            role: Role name
            objective: Task objective
            input_data: Input data

        Returns:
            Tuple of (output, confidence)
        """
        base_confidence = 0.85

        if role == "planner":
            output = {
                "text": f"Plan for: {objective}",
                "steps": [
                    "Analyze requirements",
                    "Define scope",
                    "Create timeline",
                    "Identify resources",
                ],
                "recommendations": [
                    "Start with requirements gathering",
                    "Allocate sufficient time for validation",
                ],
                "confidence": base_confidence,
            }

        elif role == "strategist":
            output = {
                "text": f"Strategic analysis for: {objective}",
                "strategic_considerations": [
                    "Market positioning",
                    "Competitive landscape",
                    "Resource allocation",
                ],
                "risks": [
                    "Timeline constraints",
                    "Technical complexity",
                ],
                "opportunities": [
                    "Leverage existing capabilities",
                    "Phase implementation",
                ],
                "confidence": base_confidence - 0.05,
            }

        elif role == "researcher":
            output = {
                "text": f"Research findings for: {objective}",
                "key_findings": [
                    "Finding 1: Market demand is strong",
                    "Finding 2: Technical feasibility confirmed",
                    "Finding 3: Competitive options available",
                ],
                "sources": [
                    "Market analysis report",
                    "Technical documentation",
                    "Industry benchmarks",
                ],
                "confidence": base_confidence + 0.05,
            }

        elif role == "builder":
            output = {
                "text": f"Implementation plan for: {objective}",
                "implementation_steps": [
                    "Set up project structure",
                    "Implement core functionality",
                    "Add error handling",
                    "Write tests",
                ],
                "technologies": [
                    "Python",
                    "FastAPI",
                    "React",
                ],
                "confidence": base_confidence,
            }

        elif role == "critic":
            output = {
                "text": f"Critique of: {objective}",
                "strengths": [
                    "Clear objective",
                    "Well-structured approach",
                ],
                "weaknesses": [
                    "Missing risk analysis",
                    "Limited consideration of alternatives",
                ],
                "suggestions": [
                    "Add contingency plans",
                    "Consider parallel approaches",
                ],
                "confidence": base_confidence - 0.1,
            }

        elif role == "validator":
            # Check prior outputs for validation
            prior_rounds = input_data.get("round_outputs", {})
            has_issues = False
            issues = []

            # Simple validation logic
            if not input_data.get("constraints"):
                issues.append("No constraints specified")

            if len(prior_rounds) < 2:
                issues.append("Insufficient collaboration")

            output = {
                "validation_passed": len(issues) == 0,
                "validation_notes": "Validation complete" if not issues else f"Issues found: {', '.join(issues)}",
                "issues": issues,
                "blocked": len(issues) > 1,
                "confidence": base_confidence - 0.15 if issues else base_confidence,
            }

        else:
            output = {
                "text": f"Response from {role} for: {objective}",
                "confidence": base_confidence,
            }

        confidence = output.get("confidence", base_confidence)
        return output, max(0.0, min(1.0, confidence))

    async def get_task_status(self, task_id: UUID) -> Optional[RoleTask]:
        """
        Get the status of a role task.

        Args:
            task_id: Task identifier

        Returns:
            Role task or None if not found
        """
        return self._active_tasks.get(task_id)

    async def cancel_task(self, task_id: UUID) -> bool:
        """
        Cancel a running role task.

        Args:
            task_id: Task identifier

        Returns:
            True if cancelled, False if not found or already complete
        """
        task = self._active_tasks.get(task_id)
        if task and task.status in (RoleTaskState.ASSIGNED, RoleTaskState.WORKING):
            task.status = RoleTaskState.FAILED
            task.error_message = "Task cancelled"
            task.completed_at = datetime.utcnow()
            return True
        return False

    def get_active_tasks(self) -> List[RoleTask]:
        """Get all currently active tasks."""
        return list(self._active_tasks.values())


# ============================================================================
# Convenience Functions
# ============================================================================

async def execute_role_task(
    supabase,
    team_execution_id: Union[UUID, str],
    role: Union[TeamRole, str],
    agent_type: str,
    objective: str,
    input_data: Dict[str, Any],
) -> RoleTask:
    """
    Convenience function to execute a role task.

    Args:
        supabase: Supabase client
        team_execution_id: Parent team execution ID
        role: Role to execute
        agent_type: Type of agent
        objective: Task objective
        input_data: Input data

    Returns:
        Completed role task
    """
    if isinstance(team_execution_id, str):
        team_execution_id = UUID(team_execution_id)
    if isinstance(role, str):
        role = TeamRole(role)

    runner = RoleRunner(supabase)
    return await runner.execute_role(
        team_execution_id, role, agent_type, objective, input_data
    )
