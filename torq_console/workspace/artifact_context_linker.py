"""
Workspace Artifact Context Linker - Phase 5.3 Milestone 3

Links tool execution artifacts to their execution context.

This module provides the integration layer that captures tool outputs
during execution and persists them as workspace artifacts with proper
context linking to missions, nodes, executions, teams, and roles.

The implementation is ADDITIVE - it does not modify frozen components
(AgentTeamOrchestrator, RoleRunner, DecisionEngine) but wraps around
them to capture artifacts.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from .artifact_models import (
    ArtifactType,
    ToolExecutionMetadata,
)
from .artifact_service import WorkspaceArtifactService

logger = logging.getLogger(__name__)


class WorkspaceArtifactContextLinker:
    """
    Links tool outputs to workspace artifacts with full execution context.

    This service provides a thin wrapper around tool execution that:
    1. Captures the tool input/output
    2. Records execution metadata
    3. Persists as a workspace artifact
    4. Links to mission/node/execution/team/round context

    The design is additive - it wraps existing execution without modifying
    the frozen runtime components.
    """

    def __init__(
        self,
        artifact_service: WorkspaceArtifactService,
        enabled: bool = True,
    ):
        """
        Initialize the context linker.

        Args:
            artifact_service: Workspace artifact service for persistence
            enabled: Whether artifact capture is enabled
        """
        self.artifact_service = artifact_service
        self.enabled = enabled
        self._artifact_counts: Dict[str, int] = {}

    async def capture_node_tool_execution(
        self,
        workspace_id: Union[str, UUID],
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_output: Any,
        execution_context: Dict[str, Any],
    ) -> Optional[Any]:
        """
        Capture a tool execution during node processing.

        This is called during workflow node execution to capture tool outputs
        as workspace artifacts linked to the node and execution.

        Args:
            workspace_id: Target workspace ID
            tool_name: Name of the tool executed
            tool_input: Input parameters passed to the tool
            tool_output: Output from the tool
            execution_context: Execution context (mission_id, node_id, execution_id, etc.)

        Returns:
            The original tool_output (pass-through for non-blocking behavior)
        """
        if not self.enabled:
            return tool_output

        try:
            # Build execution metadata
            metadata = ToolExecutionMetadata(
                tool_name=tool_name,
                mission_id=execution_context.get("mission_id"),
                node_id=execution_context.get("node_id"),
                execution_id=execution_context.get("execution_id"),
                team_execution_id=None,  # Node execution doesn't have team context
                round_number=None,
                role_name=None,
                started_at=execution_context.get("started_at", datetime.now(timezone.utc)),
                completed_at=datetime.now(timezone.utc),
                success=execution_context.get("success", True),
                error_message=execution_context.get("error_message"),
                cached=execution_context.get("cached", False),
                metadata={
                    "tool_input": tool_input,
                    "trace_id": execution_context.get("trace_id"),
                },
            )

            # Normalize and persist the artifact
            artifact = self.artifact_service.adapter.adapt_tool_output(
                tool_name=tool_name,
                tool_output=tool_output,
                execution_metadata=metadata,
            )

            # Convert to workspace artifact create model
            from .artifact_models import WorkspaceArtifactCreate

            create_model = WorkspaceArtifactCreate(
                workspace_id=UUID(str(workspace_id)) if isinstance(workspace_id, str) else workspace_id,
                mission_id=metadata.mission_id,
                node_id=metadata.node_id,
                execution_id=metadata.execution_id,
                team_execution_id=None,
                round_number=None,
                role_name=None,
                tool_name=tool_name,
                artifact_type=artifact.artifact_type,
                title=artifact.title,
                summary=artifact.summary,
                content_json=artifact.content_json,
                content_text=artifact.content_text,
                source_ref=artifact.source_ref,
            )

            await self.artifact_service.persistence.create_artifact(
                workspace_id=str(workspace_id) if isinstance(workspace_id, UUID) else workspace_id,
                artifact=create_model,
            )

            self._increment_count("node")

            logger.debug(
                f"[ArtifactLinker] Captured node tool artifact: {tool_name} "
                f"for execution: {execution_context.get('execution_id')}"
            )

        except Exception as e:
            # Don't fail execution on artifact capture errors
            logger.warning(f"[ArtifactLinker] Failed to capture artifact: {e}")

        # Always return original output (non-blocking)
        return tool_output

    async def capture_role_output(
        self,
        workspace_id: Union[str, UUID],
        role_name: str,
        task_output: Dict[str, Any],
        team_execution_context: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Capture a role task output during team execution.

        This is called during team execution to capture role outputs
        as workspace artifacts linked to the team, round, and role.

        Args:
            workspace_id: Target workspace ID
            role_name: Name of the role (lead, researcher, critic, validator)
            task_output: Output dictionary from the role task
            team_execution_context: Team execution context

        Returns:
            The original task_output (pass-through)
        """
        if not self.enabled:
            return task_output

        try:
            # Use the adapter's role output method
            normalized = self.artifact_service.adapter.adapt_role_task_output(
                role_name=role_name,
                task_output=task_output,
                execution_context=team_execution_context,
            )

            # Create and persist
            from .artifact_models import WorkspaceArtifactCreate

            create_model = WorkspaceArtifactCreate(
                workspace_id=UUID(str(workspace_id)) if isinstance(workspace_id, str) else workspace_id,
                mission_id=normalized.execution_metadata.mission_id,
                node_id=normalized.execution_metadata.node_id,
                execution_id=normalized.execution_metadata.execution_id,
                team_execution_id=normalized.execution_metadata.team_execution_id,
                round_number=normalized.execution_metadata.round_number,
                role_name=normalized.execution_metadata.role_name,
                tool_name=normalized.execution_metadata.tool_name,
                artifact_type=normalized.artifact_type,
                title=normalized.title,
                summary=normalized.summary,
                content_json=normalized.content_json,
                content_text=normalized.content_text,
                source_ref=normalized.source_ref,
            )

            await self.artifact_service.persistence.create_artifact(
                workspace_id=str(workspace_id) if isinstance(workspace_id, UUID) else workspace_id,
                artifact=create_model,
            )

            self._increment_count("role")

            logger.debug(
                f"[ArtifactLinker] Captured role artifact: {role_name} "
                f"round: {team_execution_context.get('round_number')}, "
                f"team: {team_execution_context.get('team_execution_id')}"
            )

        except Exception as e:
            logger.warning(f"[ArtifactLinker] Failed to capture role artifact: {e}")

        return task_output

    async def capture_team_decision(
        self,
        workspace_id: Union[str, UUID],
        decision_data: Dict[str, Any],
        team_execution_context: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Capture a team decision as a workspace artifact.

        Args:
            workspace_id: Target workspace ID
            decision_data: Decision output from DecisionEngine
            team_execution_context: Team execution context

        Returns:
            The original decision_data (pass-through)
        """
        if not self.enabled:
            return decision_data

        try:
            # Build metadata
            metadata = ToolExecutionMetadata(
                tool_name="team_decision",
                mission_id=team_execution_context.get("mission_id"),
                node_id=team_execution_context.get("node_id"),
                execution_id=team_execution_context.get("execution_id"),
                team_execution_id=team_execution_context.get("team_execution_id"),
                round_number=team_execution_context.get("round_number"),
                role_name=None,  # Decision is team-level, not role-specific
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                success=True,
                metadata={
                    "decision_policy": decision_data.get("decision_policy"),
                    "confidence_score": decision_data.get("confidence_score"),
                },
            )

            # Build content
            content_json = {
                "decision_outcome": str(decision_data.get("decision_outcome")) if decision_data.get("decision_outcome") else None,
                "confidence_score": decision_data.get("confidence_score", 0.0),
                "confidence_breakdown": decision_data.get("confidence_breakdown", {}),
                "approval_summary": decision_data.get("approval_summary", {}),
                "validator_status": str(decision_data.get("validator_status")) if decision_data.get("validator_status") else None,
            }

            # Create title and summary
            outcome = decision_data.get("decision_outcome", "unknown")
            title = f"Team Decision: {outcome.replace('_', ' ').title()}"
            summary = f"Team decision with {decision_data.get('confidence_score', 0):.2%} confidence"

            # Persist
            from .artifact_models import WorkspaceArtifactCreate, ArtifactType

            create_model = WorkspaceArtifactCreate(
                workspace_id=UUID(str(workspace_id)) if isinstance(workspace_id, str) else workspace_id,
                mission_id=metadata.mission_id,
                node_id=metadata.node_id,
                execution_id=metadata.execution_id,
                team_execution_id=metadata.team_execution_id,
                round_number=metadata.round_number,
                role_name=metadata.role_name,
                tool_name="team_decision",
                artifact_type=ArtifactType.TEAM_DECISION,
                title=title,
                summary=summary,
                content_json=content_json,
                content_text=str(decision_data),
                source_ref=None,
            )

            await self.artifact_service.persistence.create_artifact(
                workspace_id=str(workspace_id) if isinstance(workspace_id, UUID) else workspace_id,
                artifact=create_model,
            )

            self._increment_count("decision")

            logger.debug(
                f"[ArtifactLinker] Captured team decision artifact: {outcome} "
                f"for team: {team_execution_context.get('team_execution_id')}"
            )

        except Exception as e:
            logger.warning(f"[ArtifactLinker] Failed to capture decision artifact: {e}")

        return decision_data

    def _increment_count(self, artifact_type: str):
        """Increment artifact capture counter."""
        self._artifact_counts[artifact_type] = self._artifact_counts.get(artifact_type, 0) + 1

    def get_capture_stats(self) -> Dict[str, int]:
        """Get artifact capture statistics."""
        return self._artifact_counts.copy()

    def enable(self):
        """Enable artifact capture."""
        self.enabled = True

    def disable(self):
        """Disable artifact capture."""
        self.enabled = False


# ============================================================================
# Factory Functions
# ============================================================================

async def create_context_linker(
    supabase_client,
    enabled: bool = True,
) -> WorkspaceArtifactContextLinker:
    """
    Create a workspace artifact context linker.

    Args:
        supabase_client: Supabase client
        enabled: Whether artifact capture is enabled

    Returns:
        Configured context linker instance
    """
    from .artifact_service import WorkspaceArtifactService

    artifact_service = WorkspaceArtifactService(supabase_client)

    return WorkspaceArtifactContextLinker(
        artifact_service=artifact_service,
        enabled=enabled,
    )


# Singleton instance for convenience
_default_linker: Optional[WorkspaceArtifactContextLinker] = None


async def get_context_linker(
    supabase_client,
) -> WorkspaceArtifactContextLinker:
    """
    Get the default context linker instance.

    Args:
        supabase_client: Supabase client

    Returns:
        Context linker instance
    """
    global _default_linker
    if _default_linker is None:
        _default_linker = await create_context_linker(supabase_client)
    return _default_linker
