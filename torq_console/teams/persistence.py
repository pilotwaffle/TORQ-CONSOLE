"""
Agent Teams - Persistence Layer

Phase 5.2: Agent Teams as a governed execution primitive.

This module handles database persistence for team executions,
messages, and decisions.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from .models import (
    TeamExecution,
    TeamExecutionStatus,
    TeamMessage,
    TeamExecutionResult,
    DecisionOutcome,
    ValidatorStatus,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Team Persistence
# ============================================================================

class TeamPersistence:
    """
    Handles database persistence for agent teams.

    Provides CRUD operations for team executions, messages,
    and decisions with proper error handling and logging.
    """

    def __init__(self, supabase):
        """
        Initialize persistence layer.

        Args:
            supabase: Supabase client
        """
        self.supabase = supabase

    # =========================================================================
    # Team Executions
    # =========================================================================

    async def create_execution(self, execution: TeamExecution) -> TeamExecution:
        """
        Create a new team execution record.

        Args:
            execution: Team execution to create

        Returns:
            Created execution with database ID
        """
        data = {
            "mission_id": str(execution.mission_id),
            "node_id": str(execution.node_id),
            "execution_id": execution.execution_id,
            "team_id": str(execution.team_id),
            "workspace_id": execution.workspace_id,
            "status": execution.status.value,
            "current_round": execution.current_round,
            "max_rounds": execution.max_rounds,
            "objective": execution.objective,
            "constraints": execution.constraints,
            "telemetry": execution.telemetry,
        }

        result = self.supabase.table("team_executions").insert(data).execute()

        if result.data:
            execution.id = UUID(result.data[0]["id"])
            logger.debug(f"Created team execution: {execution.id}")

        return execution

    async def update_execution(self, execution: TeamExecution) -> TeamExecution:
        """
        Update a team execution record.

        Args:
            execution: Team execution to update

        Returns:
            Updated execution
        """
        data = {
            "status": execution.status.value,
            "current_round": execution.current_round,
            "final_confidence": execution.final_confidence,
            "decision_outcome": execution.decision_outcome.value if execution.decision_outcome else None,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
        }

        result = self.supabase.table("team_executions").update(data).eq(
            "id", str(execution.id)
        ).execute()

        logger.debug(f"Updated team execution: {execution.id}")
        return execution

    async def get_execution(self, execution_id: UUID) -> Optional[TeamExecution]:
        """
        Get a team execution by ID.

        Args:
            execution_id: Execution identifier

        Returns:
            Team execution or None
        """
        result = self.supabase.table("team_executions").select("*").eq(
            "id", str(execution_id)
        ).execute()

        if result.data:
            return self._parse_execution(result.data[0])
        return None

    async def get_execution_by_mission_node(
        self, mission_id: UUID, node_id: UUID
    ) -> List[TeamExecution]:
        """
        Get team executions for a mission node.

        Args:
            mission_id: Mission identifier
            node_id: Node identifier

        Returns:
            List of team executions
        """
        result = self.supabase.table("team_executions").select("*").eq(
            "mission_id", str(mission_id)
        ).eq("node_id", str(node_id)).execute()

        return [self._parse_execution(row) for row in result.data]

    async def list_executions(
        self,
        mission_id: Optional[UUID] = None,
        status: Optional[TeamExecutionStatus] = None,
        limit: int = 50,
    ) -> List[TeamExecution]:
        """
        List team executions with optional filters.

        Args:
            mission_id: Filter by mission
            status: Filter by status
            limit: Max results

        Returns:
            List of team executions
        """
        query = self.supabase.table("team_executions").select("*")

        if mission_id:
            query = query.eq("mission_id", str(mission_id))
        if status:
            query = query.eq("status", status.value)

        query = query.order("created_at", desc=True).limit(limit)
        result = query.execute()

        return [self._parse_execution(row) for row in result.data]

    # =========================================================================
    # Team Messages
    # =========================================================================

    async def create_message(self, message: TeamMessage) -> TeamMessage:
        """
        Create a team message.

        Args:
            message: Message to create

        Returns:
            Created message
        """
        data = {
            "team_execution_id": str(message.team_execution_id),
            "round_number": message.round_number,
            "sender_role": message.sender_role.value,
            "receiver_role": message.receiver_role.value,
            "message_type": message.message_type.value,
            "content": message.content,
            "text_content": message.text_content,
            "confidence": message.confidence,
            "token_count": message.token_count,
        }

        result = self.supabase.table("team_messages").insert(data).execute()

        if result.data:
            message.id = UUID(result.data[0]["id"])

        return message

    async def get_messages(
        self,
        team_execution_id: UUID,
        round_number: Optional[int] = None,
    ) -> List[TeamMessage]:
        """
        Get messages for a team execution.

        Args:
            team_execution_id: Execution identifier
            round_number: Optional round filter

        Returns:
            List of messages
        """
        query = self.supabase.table("team_messages").select("*").eq(
            "team_execution_id", str(team_execution_id)
        )

        if round_number:
            query = query.eq("round_number", round_number)

        query = query.order("created_at", nullsfirst=True)
        result = query.execute()

        return [self._parse_message(row) for row in result.data]

    # =========================================================================
    # Team Decisions
    # =========================================================================

    async def create_decision(self, result: TeamExecutionResult) -> TeamExecutionResult:
        """
        Create a team decision record.

        Args:
            result: Team execution result

        Returns:
            Created result
        """
        data = {
            "team_execution_id": str(result.team_execution_id),
            "final_output": result.final_output,
            "text_output": result.text_output,
            "decision_policy": result.decision_policy,
            "approval_summary": result.approval_summary,
            "dissent_summary": result.dissent_summary,
            "validator_status": result.validator_status.value,
            "validator_notes": result.validator_notes,
            "confidence_score": result.confidence_score,
            "confidence_breakdown": result.confidence_breakdown,
            "revision_count": result.revision_count,
            "escalation_count": result.escalation_count,
        }

        self.supabase.table("team_decisions").insert(data).execute()

        logger.debug(f"Created team decision: {result.team_execution_id}")
        return result

    async def get_decision(self, team_execution_id: UUID) -> Optional[TeamExecutionResult]:
        """
        Get a team decision by execution ID.

        Args:
            team_execution_id: Execution identifier

        Returns:
            Team result or None
        """
        result = self.supabase.table("team_decisions").select("*").eq(
            "team_execution_id", str(team_execution_id)
        ).execute()

        if result.data:
            return self._parse_decision(result.data[0])
        return None

    # =========================================================================
    # Parsers
    # =========================================================================

    def _parse_execution(self, data: Dict[str, Any]) -> TeamExecution:
        """Parse database row to TeamExecution."""
        return TeamExecution(
            id=UUID(data["id"]),
            mission_id=UUID(data["mission_id"]),
            node_id=UUID(data["node_id"]),
            execution_id=data["execution_id"],
            team_id=UUID(data["team_id"]),
            workspace_id=data.get("workspace_id"),
            status=TeamExecutionStatus(data["status"]),
            current_round=data.get("current_round", 0),
            max_rounds=data.get("max_rounds", 3),
            final_confidence=data.get("final_confidence"),
            decision_outcome=DecisionOutcome(data["decision_outcome"]) if data.get("decision_outcome") else None,
            started_at=self._parse_datetime(data.get("started_at")),
            completed_at=self._parse_datetime(data.get("completed_at")),
            objective=data.get("objective", ""),
            constraints=data.get("constraints", []),
            telemetry=data.get("telemetry", {}),
            created_at=self._parse_datetime(data["created_at"]),
            updated_at=self._parse_datetime(data["updated_at"]),
        )

    def _parse_message(self, data: Dict[str, Any]) -> TeamMessage:
        """Parse database row to TeamMessage."""
        from .models import TeamRole, MessageType

        return TeamMessage(
            id=UUID(data["id"]),
            team_execution_id=UUID(data["team_execution_id"]),
            round_number=data.get("round_number", 1),
            sender_role=TeamRole(data["sender_role"]),
            receiver_role=TeamRole(data["receiver_role"]),
            message_type=MessageType(data["message_type"]),
            content=data.get("content", {}),
            text_content=data.get("text_content", ""),
            confidence=data.get("confidence", 0.0),
            token_count=data.get("token_count", 0),
            created_at=self._parse_datetime(data["created_at"]),
        )

    def _parse_decision(self, data: Dict[str, Any]) -> TeamExecutionResult:
        """Parse database row to TeamExecutionResult."""
        from .models import ValidatorStatus

        return TeamExecutionResult(
            id=UUID(data["id"]),
            team_execution_id=UUID(data["team_execution_id"]),
            final_output=data.get("final_output", {}),
            text_output=data.get("text_output", ""),
            decision_policy=data["decision_policy"],
            approval_summary=data.get("approval_summary", {}),
            dissent_summary=data.get("dissent_summary", {}),
            validator_status=ValidatorStatus(data.get("validator_status", "pending")),
            validator_notes=data.get("validator_notes", ""),
            confidence_score=data.get("confidence_score", 0.0),
            confidence_breakdown=data.get("confidence_breakdown", {}),
            revision_count=data.get("revision_count", 0),
            escalation_count=data.get("escalation_count", 0),
            created_at=self._parse_datetime(data["created_at"]),
        )

    @staticmethod
    def _parse_datetime(value: Any) -> Optional[datetime]:
        """Parse datetime from database value."""
        if value:
            if isinstance(value, str):
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            return value
        return None
