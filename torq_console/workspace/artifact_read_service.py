"""
Workspace Artifact Read Service - Phase 5.3 Milestone 4

Provides read operations for workspace artifacts with filtering,
pagination, and traceability view models.

This service is additive - it does not modify capture behavior.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from .artifact_models import (
    ArtifactSummary,
    ArtifactType,
    ToolExecutionMetadata,
    WorkspaceArtifactListParams,
    WorkspaceArtifactRead,
)
from .artifact_persistence import WorkspaceArtifactPersistence
from .artifact_view_models import (
    ArtifactDetailViewModel,
    TraceabilityChainViewModel,
    TraceabilityViewModel,
)

logger = logging.getLogger(__name__)


class WorkspaceArtifactReadService:
    """
    Read service for workspace artifacts.

    Provides querying, filtering, and inspection capabilities
    for persisted workspace artifacts.
    """

    def __init__(self, persistence: WorkspaceArtifactPersistence):
        """
        Initialize the read service.

        Args:
            persistence: Artifact persistence layer
        """
        self.persistence = persistence

    async def list_artifacts(
        self,
        params: WorkspaceArtifactListParams,
    ) -> List[TraceabilityViewModel]:
        """
        List artifacts with filtering and pagination.

        Args:
            params: Query parameters for filtering and pagination

        Returns:
            List of traceability view models
        """
        # Query artifacts from persistence
        artifacts = await self.persistence.list_artifacts(params)

        # Convert to traceability view models
        return [
            self._to_traceability_view(artifact)
            for artifact in artifacts
        ]

    async def list_artifacts_paginated(
        self,
        params: WorkspaceArtifactListParams,
    ) -> Dict[str, Any]:
        """
        List artifacts with pagination metadata.

        Args:
            params: Query parameters for filtering and pagination

        Returns:
            Dict with artifacts, total_count, limit, offset
        """
        # Get artifacts
        artifacts = await self.list_artifacts(params)

        # Get total count
        total_count = await self.count_artifacts(params)

        return {
            "artifacts": artifacts,
            "total_count": total_count,
            "limit": params.limit,
            "offset": params.offset,
        }

    async def get_artifact_detail(
        self,
        artifact_id: UUID,
    ) -> Optional[ArtifactDetailViewModel]:
        """
        Get full artifact detail including traceability chain.

        Args:
            artifact_id: Artifact ID

        Returns:
            Artifact detail view model with traceability chain, or None if not found
        """
        artifact = await self.persistence.get_artifact(artifact_id)
        if not artifact:
            return None

        # Build traceability chain
        traceability_chain = await self._build_traceability_chain(artifact)

        return ArtifactDetailViewModel(
            artifact=self._to_traceability_view(artifact),
            content_json=artifact.content_json or {},
            content_text=artifact.content_text or "",
            execution_metadata=self._parse_execution_metadata(artifact).model_dump(),
            source_ref=artifact.source_ref,
            traceability=traceability_chain,
        )

    async def count_artifacts(
        self,
        params: WorkspaceArtifactListParams,
    ) -> int:
        """
        Count artifacts matching the given filters.

        Args:
            params: Query parameters for filtering

        Returns:
            Count of matching artifacts
        """
        return await self.persistence.count_artifacts(params)

    async def list_by_workspace(
        self,
        workspace_id: Union[str, UUID],
        limit: int = 50,
        offset: int = 0,
        artifact_type: Optional[ArtifactType] = None,
    ) -> List[TraceabilityViewModel]:
        """
        List artifacts for a specific workspace.

        Args:
            workspace_id: Workspace ID
            limit: Maximum results
            offset: Offset for pagination
            artifact_type: Optional artifact type filter

        Returns:
            List of traceability view models
        """
        params = WorkspaceArtifactListParams(
            workspace_id=str(workspace_id) if isinstance(workspace_id, UUID) else workspace_id,
            limit=limit,
            offset=offset,
            artifact_type=artifact_type,
        )
        return await self.list_artifacts(params)

    async def list_by_execution(
        self,
        execution_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[TraceabilityViewModel]:
        """
        List artifacts for a specific execution.

        Args:
            execution_id: Execution ID
            limit: Maximum results
            offset: Offset for pagination

        Returns:
            List of traceability view models
        """
        params = WorkspaceArtifactListParams(
            execution_id=execution_id,
            limit=limit,
            offset=offset,
        )
        return await self.list_artifacts(params)

    async def list_by_mission(
        self,
        mission_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> List[TraceabilityViewModel]:
        """
        List artifacts for a specific mission.

        Args:
            mission_id: Mission ID
            limit: Maximum results
            offset: Offset for pagination

        Returns:
            List of traceability view models
        """
        params = WorkspaceArtifactListParams(
            mission_id=mission_id,
            limit=limit,
            offset=offset,
        )
        return await self.list_artifacts(params)

    async def list_by_node(
        self,
        node_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> List[TraceabilityViewModel]:
        """
        List artifacts for a specific node.

        Args:
            node_id: Node ID
            limit: Maximum results
            offset: Offset for pagination

        Returns:
            List of traceability view models
        """
        params = WorkspaceArtifactListParams(
            node_id=node_id,
            limit=limit,
            offset=offset,
        )
        return await self.list_artifacts(params)

    async def list_by_team_execution(
        self,
        team_execution_id: UUID,
        limit: int = 50,
        offset: int = 0,
        round_number: Optional[int] = None,
    ) -> List[TraceabilityViewModel]:
        """
        List artifacts for a specific team execution.

        Args:
            team_execution_id: Team execution ID
            limit: Maximum results
            offset: Offset for pagination
            round_number: Optional round number filter

        Returns:
            List of traceability view models
        """
        params = WorkspaceArtifactListParams(
            team_execution_id=team_execution_id,
            limit=limit,
            offset=offset,
        )
        artifacts = await self.list_artifacts(params)

        # Filter by round_number if specified
        if round_number is not None:
            artifacts = [a for a in artifacts if a.round_number == round_number]

        return artifacts

    async def list_by_type(
        self,
        artifact_type: ArtifactType,
        workspace_id: Optional[Union[str, UUID]] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[TraceabilityViewModel]:
        """
        List artifacts by type.

        Args:
            artifact_type: Artifact type to filter by
            workspace_id: Optional workspace ID filter
            limit: Maximum results
            offset: Offset for pagination

        Returns:
            List of traceability view models
        """
        params = WorkspaceArtifactListParams(
            workspace_id=str(workspace_id) if isinstance(workspace_id, UUID) else workspace_id,
            artifact_type=artifact_type,
            limit=limit,
            offset=offset,
        )
        return await self.list_artifacts(params)

    def _to_traceability_view(
        self,
        artifact: WorkspaceArtifactRead,
    ) -> TraceabilityViewModel:
        """Convert artifact to traceability view model."""
        # Determine content type
        has_json = bool(artifact.content_json)
        has_text = bool(artifact.content_text)
        if has_json and has_text:
            content_type = "mixed"
        elif has_json:
            content_type = "json"
        else:
            content_type = "text"

        return TraceabilityViewModel(
            id=artifact.id,
            artifact_type=artifact.artifact_type.value,
            title=artifact.title,
            summary=artifact.summary,
            created_at=artifact.created_at,
            workspace_id=artifact.workspace_id,
            mission_id=artifact.mission_id,
            node_id=artifact.node_id,
            execution_id=artifact.execution_id,
            team_execution_id=artifact.team_execution_id,
            round_number=artifact.round_number,
            role_name=artifact.role_name,
            tool_name=artifact.tool_name,
            has_content=has_json or has_text,
            content_type=content_type,
        )

    def _parse_execution_metadata(
        self,
        artifact: WorkspaceArtifactRead,
    ) -> ToolExecutionMetadata:
        """Parse execution metadata from artifact."""
        if artifact.execution_metadata:
            return ToolExecutionMetadata(**artifact.execution_metadata)

        # Build from artifact fields if execution_metadata is not populated
        return ToolExecutionMetadata(
            tool_name=artifact.tool_name,
            mission_id=artifact.mission_id,
            node_id=artifact.node_id,
            execution_id=artifact.execution_id,
            team_execution_id=artifact.team_execution_id,
            round_number=artifact.round_number,
            role_name=artifact.role_name,
            started_at=artifact.created_at,
            success=True,
        )

    async def _build_traceability_chain(
        self,
        artifact: WorkspaceArtifactRead,
    ) -> TraceabilityChainViewModel:
        """Build traceability chain view model for an artifact."""
        # For now, build a basic chain
        # Future enhancement: fetch related entities for full chain

        return TraceabilityChainViewModel(
            workspace={
                "id": str(artifact.workspace_id),
                "type": "workspace",
            },
            mission=(
                {
                    "id": str(artifact.mission_id),
                    "type": "mission",
                }
                if artifact.mission_id
                else None
            ),
            node=(
                {
                    "id": str(artifact.node_id),
                    "type": "node",
                }
                if artifact.node_id
                else None
            ),
            execution=(
                {
                    "id": artifact.execution_id,
                    "type": "execution",
                }
                if artifact.execution_id
                else None
            ),
            team=(
                {
                    "id": str(artifact.team_execution_id),
                    "type": "team",
                    "round_number": artifact.round_number,
                }
                if artifact.team_execution_id
                else None
            ),
            role=(
                {
                    "name": artifact.role_name,
                    "type": "role",
                }
                if artifact.role_name
                else None
            ),
            artifact={
                "id": str(artifact.id),
                "type": "artifact",
                "artifact_type": artifact.artifact_type.value,
                "title": artifact.title,
            },
        )


# ============================================================================
# Factory Functions
# ============================================================================

def get_artifact_read_service(persistence: WorkspaceArtifactPersistence) -> WorkspaceArtifactReadService:
    """
    Get an artifact read service.

    Args:
        persistence: Artifact persistence layer

    Returns:
        Configured read service instance
    """
    return WorkspaceArtifactReadService(persistence)
