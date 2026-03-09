"""
Agent Teams - Team Orchestrator

Phase 5.2: Agent Teams as a governed execution primitive.

This module manages the execution of agent teams, including round
management, role coordination, and decision synthesis.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from .models import (
    TeamDefinition,
    TeamExecutionContext,
    TeamExecution,
    TeamExecutionResult,
    TeamExecutionStatus,
    TeamMessage,
    TeamRole,
    MessageType,
    DecisionOutcome,
    DecisionPolicy,
    ValidatorStatus,
    ConfidenceBreakdown,
    ApprovalSummary,
    DissentSummary,
    RoleTask,
    RoleTaskState,
)
from .registry import TeamDefinitionRegistry, get_registry
from .role_runner import RoleRunner
from .decision_engine import DecisionEngine
from .persistence import TeamPersistence
from .context import TeamContextManager


logger = logging.getLogger(__name__)


# ============================================================================
# Team Orchestrator
# ============================================================================

class AgentTeamOrchestrator:
    """
    Orchestrates execution of agent teams.

    Responsibilities:
    - Load team definitions
    - Create team execution context
    - Assign roles to agents
    - Manage collaboration rounds
    - Route internal handoffs
    - Invoke decision policy
    - Produce final synthesis
    """

    def __init__(self, supabase, registry: Optional[TeamDefinitionRegistry] = None):
        """
        Initialize the orchestrator.

        Args:
            supabase: Supabase client
            registry: Team definition registry (defaults to global)
        """
        self.supabase = supabase
        self.registry = registry or get_registry()
        self.role_runner = RoleRunner(supabase)
        self.decision_engine = DecisionEngine(supabase)
        self.persistence = TeamPersistence(supabase)
        self.context_manager = TeamContextManager(supabase)

    async def execute_team_node(
        self,
        mission_id: UUID,
        node_id: UUID,
        team_id: str,
        context: TeamExecutionContext,
    ) -> TeamExecutionResult:
        """
        Execute a mission node using an agent team.

        Args:
            mission_id: Mission identifier
            node_id: Node identifier
            team_id: Team identifier
            context: Team execution context

        Returns:
            Final team execution result
        """
        # Load team definition
        definition = self.registry.get_by_team_id(team_id)
        if not definition:
            raise ValueError(f"Team not found: {team_id}")

        # Create execution record
        execution = TeamExecution(
            mission_id=mission_id,
            node_id=node_id,
            execution_id=context.execution_id,
            team_id=definition.id,
            workspace_id=context.workspace_id,
            status=TeamExecutionStatus.CREATED,
            max_rounds=definition.max_rounds,
            objective=context.objective,
            constraints=context.constraints,
        )

        # Persist execution
        execution = await self.persistence.create_execution(execution)
        logger.info(f"Created team execution: {execution.execution_id}")

        # Initialize workspace
        if not context.workspace_id:
            context.workspace_id = await self.context_manager.create_workspace(
                mission_id, node_id, execution.id
            )

        # Update status and start
        execution.status = TeamExecutionStatus.INITIALIZED
        execution.started_at = datetime.utcnow()
        execution = await self.persistence.update_execution(execution)

        try:
            # Run team collaboration
            result = await self._run_collaboration(execution, definition, context)

            # Update execution with result
            execution.status = TeamExecutionStatus.COMPLETED
            execution.completed_at = datetime.utcnow()
            execution.final_confidence = result.confidence_score
            execution.decision_outcome = DecisionOutcome(result.decision_policy.split("_")[0])
            execution.result = result

            await self.persistence.update_execution(execution)
            await self.persistence.create_decision(result)

            logger.info(
                f"Team execution completed: {execution.execution_id} "
                f"with confidence {result.confidence_score:.2f}"
            )

            return result

        except Exception as e:
            logger.error(f"Team execution failed: {execution.execution_id} - {e}")
            execution.status = TeamExecutionStatus.FAILED
            execution.completed_at = datetime.utcnow()
            await self.persistence.update_execution(execution)

            # Return failure result
            return TeamExecutionResult(
                team_execution_id=execution.id,
                final_output={"error": str(e)},
                text_output=f"Team execution failed: {e}",
                decision_policy=definition.decision_policy.value,
                confidence_score=0.0,
                validator_status=ValidatorStatus.ESCALATED,
            )

    async def _run_collaboration(
        self,
        execution: TeamExecution,
        definition: TeamDefinition,
        context: TeamExecutionContext,
    ) -> TeamExecutionResult:
        """
        Run the team collaboration process.

        Args:
            execution: Team execution record
            definition: Team definition
            context: Execution context

        Returns:
            Final team result
        """
        execution.status = TeamExecutionStatus.RUNNING
        execution = await self.persistence.update_execution(execution)

        # Get roles in execution order
        roles = self.registry.get_roles_in_order(definition.team_id)

        for round_num in range(1, definition.max_rounds + 1):
            execution.current_round = round_num
            context.current_round = round_num

            logger.info(
                f"Starting round {round_num}/{definition.max_rounds} "
                f"for execution {execution.execution_id}"
            )

            # Execute round
            round_result = await self._execute_round(
                execution, definition, context, roles, round_num
            )

            # Check if we need another round
            if round_result.get("should_stop", False):
                logger.info(f"Collaboration complete after round {round_num}")
                break

            # Check confidence threshold
            if round_result.get("confidence", 0.0) >= 0.85:
                logger.info(f"High confidence achieved: {round_result['confidence']:.2f}")
                break

        # Synthesize final result
        return await self._synthesize_result(execution, definition, context)

    async def _execute_round(
        self,
        execution: TeamExecution,
        definition: TeamDefinition,
        context: TeamExecutionContext,
        roles: List,
        round_num: int,
    ) -> Dict[str, Any]:
        """
        Execute a single collaboration round.

        Args:
            execution: Team execution record
            definition: Team definition
            context: Execution context
            roles: Ordered list of team roles
            round_num: Current round number

        Returns:
            Round result dictionary
        """
        round_outputs = {}
        round_messages = []
        total_confidence = 0.0
        confidence_count = 0

        # Execute each role in order
        for role_def in roles:
            role = role_def.role_name

            # Prepare role input
            role_input = self._prepare_role_input(
                role, context, round_outputs, round_num
            )

            # Execute role task
            task = await self.role_runner.execute_role(
                execution.id,
                role,
                role_def.agent_type,
                context.objective,
                role_input,
            )

            # Store output
            round_outputs[role.value] = task.output or {}

            # Create handoff message
            message = TeamMessage(
                team_execution_id=execution.id,
                round_number=round_num,
                sender_role=role,
                receiver_role=self._get_next_role(roles, role),
                message_type=MessageType.ROLE_TO_ROLE,
                content=task.output or {},
                text_content=task.output.get("text", ""),
                confidence=task.confidence,
            )
            round_messages.append(message)
            await self.persistence.create_message(message)

            # Track confidence
            if task.confidence > 0:
                total_confidence += task.confidence
                confidence_count += 1

            # Log to workspace
            await self.context_manager.add_role_output(
                context.workspace_id,
                execution.id,
                round_num,
                role.value,
                task.output or {},
            )

        # Run validator if this is the validation round
        if self._is_validation_round(round_num, definition.max_rounds):
            validation_result = await self._run_validation(
                execution, context, round_outputs, round_num
            )
            round_messages.append(validation_result)

            # Check if validator blocked
            if validation_result.content.get("blocked", False):
                return {"should_stop": True, "blocked": True}

        # Calculate average confidence
        avg_confidence = total_confidence / confidence_count if confidence_count > 0 else 0.0

        # Create round summary
        summary = TeamMessage(
            team_execution_id=execution.id,
            round_number=round_num,
            sender_role=TeamRole.LEAD,
            receiver_role=TeamRole.LEAD,
            message_type=MessageType.ROUND_SUMMARY,
            content={
                "round": round_num,
                "outputs": round_outputs,
                "average_confidence": avg_confidence,
                "complete": False,
            },
        )
        await self.persistence.create_message(summary)

        return {
            "outputs": round_outputs,
            "confidence": avg_confidence,
            "should_stop": False,
        }

    async def _run_validation(
        self,
        execution: TeamExecution,
        context: TeamExecutionContext,
        round_outputs: Dict[str, Any],
        round_num: int,
    ) -> TeamMessage:
        """
        Run validator review of round outputs.

        Args:
            execution: Team execution record
            context: Execution context
            round_outputs: Outputs from all roles
            round_num: Current round number

        Returns:
            Validation message
        """
        # Get validator role
        validator = self.registry.get_member_role(
            execution.team_id, TeamRole.VALIDATOR
        )

        # Run validation
        validation_input = {
            "round_outputs": round_outputs,
            "objective": context.objective,
            "constraints": context.constraints,
        }

        task = await self.role_runner.execute_role(
            execution.id,
            TeamRole.VALIDATOR,
            validator.agent_type if validator else "validator_agent",
            "Validate team outputs",
            validation_input,
        )

        # Determine validation status
        is_blocked = task.output.get("validation_passed", True) is False

        return TeamMessage(
            team_execution_id=execution.id,
            round_number=round_num,
            sender_role=TeamRole.VALIDATOR,
            receiver_role=TeamRole.LEAD,
            message_type=MessageType.VALIDATION_BLOCK if is_blocked else MessageType.VALIDATION_PASS,
            content={
                "validation_passed": not is_blocked,
                "notes": task.output.get("validation_notes", ""),
                "blocked": is_blocked,
                "issues": task.output.get("issues", []),
            },
            confidence=task.confidence,
        )

    async def _synthesize_result(
        self,
        execution: TeamExecution,
        definition: TeamDefinition,
        context: TeamExecutionContext,
    ) -> TeamExecutionResult:
        """
        Synthesize final team result using decision policy.

        Args:
            execution: Team execution record
            definition: Team definition
            context: Execution context

        Returns:
            Final team execution result
        """
        # Load all messages
        messages = await self.persistence.get_messages(execution.id)

        # Build confidence breakdown
        confidence_breakdown = ConfidenceBreakdown()
        approval = ApprovalSummary()
        dissent = DissentSummary()

        for message in messages:
            if message.confidence > 0:
                setattr(
                    confidence_breakdown,
                    message.sender_role.value,
                    getattr(confidence_breakdown, message.sender_role.value, 0) + message.confidence
                )

        # Run decision engine
        decision = await self.decision_engine.make_decision(
            execution, messages, definition.decision_policy
        )

        # Update approval/dissent summaries
        approval.total_votes = decision.total_votes
        approval.approve_votes = decision.approve_votes
        approval.dissent_votes = decision.dissent_votes
        approval.voters = decision.voters

        dissent.has_dissent = decision.has_dissent
        dissent.dissenting_roles = decision.dissenting_roles
        dissent.dissent_reasons = decision.dissent_reasons

        # Get final output
        final_output = decision.final_output or {}
        text_output = final_output.get("text", str(final_output))

        return TeamExecutionResult(
            team_execution_id=execution.id,
            final_output=final_output,
            text_output=text_output,
            decision_policy=definition.decision_policy.value,
            approval_summary=approval.__dict__,
            dissent_summary=dissent.__dict__,
            validator_status=decision.validator_status,
            validator_notes=decision.validator_notes,
            confidence_score=decision.confidence_score,
            confidence_breakdown=confidence_breakdown.to_dict(),
            revision_count=decision.revision_count,
            escalation_count=decision.escalation_count,
        )

    def _prepare_role_input(
        self,
        role: TeamRole,
        context: TeamExecutionContext,
        round_outputs: Dict[str, Any],
        round_num: int,
    ) -> Dict[str, Any]:
        """
        Prepare input for a role execution.

        Args:
            role: Role to execute
            context: Execution context
            round_outputs: Outputs from previous roles in this round
            round_num: Current round number

        Returns:
            Role input dictionary
        """
        return {
            "objective": context.objective,
            "constraints": context.constraints,
            "prior_outputs": context.prior_outputs,
            "round_outputs": round_outputs,
            "round_number": round_num,
            "role": role.value,
            "shared_state": context.shared_state,
        }

    def _get_next_role(self, roles: List, current_role: TeamRole) -> TeamRole:
        """Get the next role in execution order."""
        current_idx = next(
            (i for i, r in enumerate(roles) if r.role_name == current_role),
            len(roles) - 1
        )
        next_idx = (current_idx + 1) % len(roles)
        return roles[next_idx].role_name

    def _is_validation_round(self, round_num: int, max_rounds: int) -> bool:
        """Check if this is a validation round."""
        # Validate on final round or middle round
        return round_num == max_rounds or (round_num % 2 == 0)


# ============================================================================
# Convenience Functions
# ============================================================================

async def execute_team_node(
    supabase,
    mission_id: Union[UUID, str],
    node_id: Union[UUID, str],
    team_id: str,
    objective: str,
    constraints: List[str] = None,
    prior_outputs: Dict[str, Any] = None,
    workspace_id: str = None,
) -> TeamExecutionResult:
    """
    Convenience function to execute a team node.

    Args:
        supabase: Supabase client
        mission_id: Mission identifier
        node_id: Node identifier
        team_id: Team identifier (e.g., "planning_team")
        objective: Node objective
        constraints: Optional constraints list
        prior_outputs: Prior node outputs
        workspace_id: Optional workspace ID

    Returns:
        Team execution result
    """
    # Convert string IDs to UUID if needed
    if isinstance(mission_id, str):
        mission_id = UUID(mission_id)
    if isinstance(node_id, str):
        node_id = UUID(node_id)

    # Initialize registry if needed
    registry = get_registry()
    if not registry._loaded_from_db:
        await initialize_registry(supabase)

    # Create execution context
    execution_id = f"team_{uuid4().hex[:12]}"
    context = TeamExecutionContext(
        mission_id=mission_id,
        node_id=node_id,
        execution_id=execution_id,
        workspace_id=workspace_id,
        objective=objective,
        constraints=constraints or [],
        prior_outputs=prior_outputs or {},
    )

    # Execute
    orchestrator = AgentTeamOrchestrator(supabase, registry)
    return await orchestrator.execute_team_node(mission_id, node_id, team_id, context)
