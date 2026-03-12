"""
Workspace Artifact Service - Phase 5.3 Milestone 2

Business logic for workspace artifact operations.

This module provides the WorkspaceArtifactService class which combines
the adapter and persistence layers to provide a complete artifact
management interface.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from .artifact_adapter import (
    ToolOutputAdapter,
    adapt_tool_output,
    get_tool_output_adapter,
)
from .artifact_models import (
    NormalizedArtifact,
    ToolExecutionMetadata,
    WorkspaceArtifactCreate,
    WorkspaceArtifactRead,
    WorkspaceArtifactListParams,
    ArtifactType,
)
from .artifact_persistence import WorkspaceArtifactPersistence


class WorkspaceArtifactService:
    """
    Service for managing workspace artifacts.

    This service provides the complete interface for:
    - Adapting tool outputs into normalized artifacts
    - Persisting artifacts to the workspace
    - Retrieving artifacts by various criteria

    The service is designed to be additive - it does not modify
    existing tool execution flows, only captures outputs.
    """

    def __init__(
        self,
        supabase_client: Any,
        adapter: Optional[ToolOutputAdapter] = None,
    ):
        """
        Initialize the artifact service.

        Args:
            supabase_client: Supabase client instance
            adapter: Optional tool output adapter (creates default if not provided)
        """
        self.supabase = supabase_client
        self.persistence = WorkspaceArtifactPersistence(supabase_client)
        self.adapter = adapter or get_tool_output_adapter()

    async def capture_tool_output(
        self,
        workspace_id: Union[str, UUID],
        tool_name: str,
        tool_output: Any,
        execution_context: Optional[Dict[str, Any]] = None,
    ) -> WorkspaceArtifactRead:
        """
        Capture a tool output as a workspace artifact.

        This is the primary entry point for the artifact system.
        It adapts the tool output and persists it to the workspace.

        Args:
            workspace_id: Target workspace ID
            tool_name: Name of the tool
            tool_output: Raw output from the tool
            execution_context: Optional execution context

        Returns:
            Persisted artifact read model
        """
        # Build execution metadata
        metadata = self._build_execution_metadata(
            tool_name=tool_name,
            execution_context=execution_context or {},
        )

        # Adapt the tool output
        normalized = self.adapter.adapt_tool_output(
            tool_name=tool_name,
            tool_output=tool_output,
            execution_metadata=metadata,
        )

        # Create the artifact create model
        create_model = WorkspaceArtifactCreate(
            workspace_id=workspace_id,
            mission_id=normalized.execution_metadata.mission_id,
            node_id=normalized.execution_metadata.node_id,
            execution_id=normalized.execution_metadata.execution_id,
            team_execution_id=normalized.execution_metadata.team_execution_id,
            round_number=normalized.execution_metadata.round_number,
            role_name=normalized.execution_metadata.role_name,
            tool_name=tool_name,
            artifact_type=normalized.artifact_type,
            title=normalized.title,
            summary=normalized.summary,
            content_json=normalized.content_json,
            content_text=normalized.content_text,
            source_ref=normalized.source_ref,
        )

        # Persist to database
        return await self.persistence.create_artifact(
            workspace_id=workspace_id,
            artifact=create_model,
        )

    async def capture_claude_tool_use(
        self,
        workspace_id: Union[str, UUID],
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_result: str,
        execution_context: Optional[Dict[str, Any]] = None,
    ) -> WorkspaceArtifactRead:
        """
        Capture a Claude Tool Use API result as a workspace artifact.

        This handles the specific format from Anthropic's Tool Use API.

        Args:
            workspace_id: Target workspace ID
            tool_name: Tool name (e.g., 'web_search', 'news_search')
            tool_input: Input parameters passed to the tool
            tool_result: Text result from the tool
            execution_context: Optional execution context

        Returns:
            Persisted artifact read model
        """
        # Adapt using the Claude tool use adapter
        normalized = self.adapter.adapt_claude_tool_use(
            tool_name=tool_name,
            tool_input=tool_input,
            tool_result=tool_result,
            execution_context=execution_context,
        )

        # Build execution metadata with completion time
        if not normalized.execution_metadata.completed_at:
            normalized.execution_metadata.completed_at = datetime.now(timezone.utc)

        # Create and persist
        create_model = WorkspaceArtifactCreate(
            workspace_id=workspace_id,
            mission_id=normalized.execution_metadata.mission_id,
            node_id=normalized.execution_metadata.node_id,
            execution_id=normalized.execution_metadata.execution_id,
            team_execution_id=normalized.execution_metadata.team_execution_id,
            round_number=normalized.execution_metadata.round_number,
            role_name=normalized.execution_metadata.role_name,
            tool_name=tool_name,
            artifact_type=normalized.artifact_type,
            title=normalized.title,
            summary=normalized.summary,
            content_json=normalized.content_json,
            content_text=normalized.content_text,
            source_ref=normalized.source_ref,
        )

        return await self.persistence.create_artifact(
            workspace_id=workspace_id,
            artifact=create_model,
        )

    async def capture_role_output(
        self,
        workspace_id: Union[str, UUID],
        role_name: str,
        task_output: Dict[str, Any],
        execution_context: Dict[str, Any],
    ) -> WorkspaceArtifactRead:
        """
        Capture a role task output as a workspace artifact.

        This integrates with Phase 5.2 Agent Teams.

        Args:
            workspace_id: Target workspace ID
            role_name: Name of the role (e.g., 'lead', 'researcher')
            task_output: Output from the role task
            execution_context: Team execution context

        Returns:
            Persisted artifact read model
        """
        # Adapt using the role task adapter
        normalized = self.adapter.adapt_role_task_output(
            role_name=role_name,
            task_output=task_output,
            execution_context=execution_context,
        )

        # Create and persist
        create_model = WorkspaceArtifactCreate(
            workspace_id=workspace_id,
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

        return await self.persistence.create_artifact(
            workspace_id=workspace_id,
            artifact=create_model,
        )

    async def get_artifact(self, artifact_id: UUID) -> Optional[WorkspaceArtifactRead]:
        """Get an artifact by ID."""
        return await self.persistence.get_artifact(artifact_id)

    async def list_workspace_artifacts(
        self,
        workspace_id: Union[str, UUID],
        artifact_type: Optional[ArtifactType] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[WorkspaceArtifactRead]:
        """List artifacts for a workspace."""
        return await self.persistence.list_workspace_artifacts(
            workspace_id=workspace_id,
            artifact_type=artifact_type,
            limit=limit,
            offset=offset,
        )

    async def list_team_execution_artifacts(
        self,
        team_execution_id: UUID,
        round_number: Optional[int] = None,
    ) -> List[WorkspaceArtifactRead]:
        """List artifacts for a team execution."""
        return await self.persistence.list_team_execution_artifacts(
            team_execution_id=team_execution_id,
            round_number=round_number,
        )

    async def list_execution_artifacts(
        self,
        execution_id: str,
    ) -> List[WorkspaceArtifactRead]:
        """List artifacts for a workflow execution."""
        return await self.persistence.list_execution_artifacts(
            execution_id=execution_id,
        )

    async def list_artifacts(self, params: WorkspaceArtifactListParams) -> List[WorkspaceArtifactRead]:
        """List artifacts with custom parameters."""
        return await self.persistence.list_artifacts(params)

    async def count_artifacts(
        self,
        workspace_id: Optional[str] = None,
        artifact_type: Optional[ArtifactType] = None,
        tool_name: Optional[str] = None,
    ) -> int:
        """Count artifacts matching filters."""
        return await self.persistence.count_artifacts(
            workspace_id=workspace_id,
            artifact_type=artifact_type,
            tool_name=tool_name,
        )

    def _build_execution_metadata(
        self,
        tool_name: str,
        execution_context: Dict[str, Any],
    ) -> ToolExecutionMetadata:
        """
        Build execution metadata from context.

        Args:
            tool_name: Name of the tool
            execution_context: Execution context dictionary

        Returns:
            ToolExecutionMetadata instance
        """
        return ToolExecutionMetadata(
            tool_name=tool_name,
            mission_id=execution_context.get("mission_id"),
            node_id=execution_context.get("node_id"),
            execution_id=execution_context.get("execution_id"),
            team_execution_id=execution_context.get("team_execution_id"),
            round_number=execution_context.get("round_number"),
            role_name=execution_context.get("role_name"),
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            success=execution_context.get("success", True),
            error_message=execution_context.get("error_message"),
            cached=execution_context.get("cached", False),
            metadata=execution_context.get("metadata", {}),
        )


# ============================================================================
# Convenience functions
# ============================================================================

async def capture_tool_output(
    supabase_client: Any,
    workspace_id: str,
    tool_name: str,
    tool_output: Any,
    execution_context: Optional[Dict[str, Any]] = None,
) -> WorkspaceArtifactRead:
    """
    Convenience function to capture a tool output as an artifact.

    Args:
        supabase_client: Supabase client
        workspace_id: Target workspace ID
        tool_name: Name of the tool
        tool_output: Raw output from the tool
        execution_context: Optional execution context

    Returns:
        Persisted artifact read model
    """
    service = WorkspaceArtifactService(supabase_client)
    return await service.capture_tool_output(
        workspace_id=workspace_id,
        tool_name=tool_name,
        tool_output=tool_output,
        execution_context=execution_context,
    )


async def get_workspace_artifact_service(
    supabase_client: Any,
) -> WorkspaceArtifactService:
    """
    Get or create a workspace artifact service.

    Args:
        supabase_client: Supabase client

    Returns:
        WorkspaceArtifactService instance
    """
    return WorkspaceArtifactService(supabase_client)
