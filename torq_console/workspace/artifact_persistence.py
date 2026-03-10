"""
Workspace Artifact Persistence - Phase 5.3 Milestone 2

Supabase persistence operations for workspace artifacts.

This module provides the WorkspaceArtifactPersistence class which handles
all database operations for creating and retrieving workspace artifacts.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from .artifact_models import (
    WorkspaceArtifactCreate,
    WorkspaceArtifactListParams,
    WorkspaceArtifactRead,
    ArtifactType,
)


class WorkspaceArtifactPersistence:
    """
    Persistence layer for workspace artifacts.

    Handles all Supabase operations for workspace artifacts including
    creating, reading, and querying artifacts.
    """

    def __init__(self, supabase_client: Any):
        """
        Initialize the persistence layer.

        Args:
            supabase_client: Supabase client instance
        """
        self.supabase = supabase_client
        self.table_name = "workspace_artifacts"

    async def create_artifact(
        self,
        workspace_id: Union[str, UUID],
        artifact: WorkspaceArtifactCreate,
    ) -> WorkspaceArtifactRead:
        """
        Create a new workspace artifact.

        Args:
            workspace_id: Target workspace ID
            artifact: Artifact creation data

        Returns:
            Created artifact read model
        """
        payload = artifact.model_dump()
        # Convert workspace_id to UUID string if needed
        payload["workspace_id"] = str(workspace_id) if isinstance(workspace_id, UUID) else workspace_id

        # Convert UUIDs to strings for JSON serialization
        if payload.get("mission_id"):
            payload["mission_id"] = str(payload["mission_id"])
        if payload.get("node_id"):
            payload["node_id"] = str(payload["node_id"])
        if payload.get("team_execution_id"):
            payload["team_execution_id"] = str(payload["team_execution_id"])
        if payload.get("artifact_type"):
            payload["artifact_type"] = payload["artifact_type"].value if isinstance(payload["artifact_type"], ArtifactType) else payload["artifact_type"]

        # Build execution metadata if not provided
        if "execution_metadata" not in payload or not payload["execution_metadata"]:
            payload["execution_metadata"] = {
                "tool_name": artifact.tool_name,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

        result = self.supabase.table(self.table_name).insert(payload).execute()

        if not result.data:
            raise RuntimeError("Failed to create artifact - no data returned")

        return self._to_read_model(result.data[0])

    async def get_artifact(self, artifact_id: UUID) -> Optional[WorkspaceArtifactRead]:
        """
        Get an artifact by ID.

        Args:
            artifact_id: Artifact UUID

        Returns:
            Artifact read model or None if not found
        """
        result = (
            self.supabase.table(self.table_name)
            .select("*")
            .eq("id", str(artifact_id))
            .limit(1)
            .execute()
        )

        if not result.data:
            return None

        return self._to_read_model(result.data[0])

    async def list_artifacts(
        self,
        params: WorkspaceArtifactListParams,
    ) -> List[WorkspaceArtifactRead]:
        """
        List artifacts with optional filtering.

        Args:
            params: Query parameters for filtering and pagination

        Returns:
            List of artifact read models
        """
        query = self.supabase.table(self.table_name).select("*")

        # Apply filters
        if params.workspace_id:
            query = query.eq("workspace_id", params.workspace_id)

        if params.execution_id:
            query = query.eq("execution_id", params.execution_id)

        if params.team_execution_id:
            query = query.eq("team_execution_id", str(params.team_execution_id))

        if params.mission_id:
            query = query.eq("mission_id", str(params.mission_id))

        if params.artifact_type:
            artifact_type_value = params.artifact_type.value if isinstance(params.artifact_type, ArtifactType) else params.artifact_type
            query = query.eq("artifact_type", artifact_type_value)

        if params.tool_name:
            query = query.eq("tool_name", params.tool_name)

        # Apply ordering
        order_column = params.order_by
        if order_column == "created_at":
            order_column = "created_at"
        query = query.order(order_column, desc=params.order_desc)

        # Apply pagination
        query = query.range(params.offset, params.offset + params.limit - 1)

        result = query.execute()

        return [self._to_read_model(row) for row in result.data]

    async def list_workspace_artifacts(
        self,
        workspace_id: Union[str, UUID],
        artifact_type: Optional[ArtifactType] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[WorkspaceArtifactRead]:
        """
        List artifacts for a specific workspace.

        Args:
            workspace_id: Workspace ID
            artifact_type: Optional artifact type filter
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of artifact read models
        """
        # Convert UUID to string for query
        workspace_id_str = str(workspace_id) if isinstance(workspace_id, UUID) else workspace_id
        params = WorkspaceArtifactListParams(
            workspace_id=workspace_id_str,
            artifact_type=artifact_type,
            limit=limit,
            offset=offset,
        )
        return await self.list_artifacts(params)

    async def list_team_execution_artifacts(
        self,
        team_execution_id: UUID,
        round_number: Optional[int] = None,
    ) -> List[WorkspaceArtifactRead]:
        """
        List artifacts for a team execution.

        Args:
            team_execution_id: Team execution UUID
            round_number: Optional round number filter

        Returns:
            List of artifact read models
        """
        query = (
            self.supabase.table(self.table_name)
            .select("*")
            .eq("team_execution_id", str(team_execution_id))
        )

        if round_number is not None:
            query = query.eq("round_number", round_number)

        query = query.order("created_at", desc=False)

        result = query.execute()

        return [self._to_read_model(row) for row in result.data]

    async def list_execution_artifacts(
        self,
        execution_id: str,
    ) -> List[WorkspaceArtifactRead]:
        """
        List artifacts for a workflow execution.

        Args:
            execution_id: Workflow execution ID

        Returns:
            List of artifact read models
        """
        result = (
            self.supabase.table(self.table_name)
            .select("*")
            .eq("execution_id", execution_id)
            .order("created_at", desc=False)
            .execute()
        )

        return [self._to_read_model(row) for row in result.data]

    async def count_artifacts(
        self,
        workspace_id: Optional[Union[str, UUID]] = None,
        artifact_type: Optional[ArtifactType] = None,
        tool_name: Optional[str] = None,
    ) -> int:
        """
        Count artifacts matching the given filters.

        Args:
            workspace_id: Optional workspace filter
            artifact_type: Optional artifact type filter
            tool_name: Optional tool name filter

        Returns:
            Count of matching artifacts
        """
        query = self.supabase.table(self.table_name).select("*", count="exact")

        if workspace_id:
            workspace_id_str = str(workspace_id) if isinstance(workspace_id, UUID) else workspace_id
            query = query.eq("workspace_id", workspace_id_str)

        if artifact_type:
            artifact_type_value = artifact_type.value if isinstance(artifact_type, ArtifactType) else artifact_type
            query = query.eq("artifact_type", artifact_type_value)

        if tool_name:
            query = query.eq("tool_name", tool_name)

        result = query.execute()

        return result.count if hasattr(result, "count") else len(result.data)

    async def delete_artifact(self, artifact_id: UUID) -> bool:
        """
        Delete an artifact by ID.

        Args:
            artifact_id: Artifact UUID

        Returns:
            True if deleted, False if not found
        """
        result = (
            self.supabase.table(self.table_name)
            .delete()
            .eq("id", str(artifact_id))
            .execute()
        )

        return len(result.data) > 0

    async def delete_workspace_artifacts(
        self,
        workspace_id: Union[str, UUID],
        artifact_type: Optional[ArtifactType] = None,
    ) -> int:
        """
        Delete all artifacts for a workspace.

        Args:
            workspace_id: Workspace ID
            artifact_type: Optional artifact type filter

        Returns:
            Number of artifacts deleted
        """
        workspace_id_str = str(workspace_id) if isinstance(workspace_id, UUID) else workspace_id
        query = self.supabase.table(self.table_name).delete().eq("workspace_id", workspace_id_str)

        if artifact_type:
            artifact_type_value = artifact_type.value if isinstance(artifact_type, ArtifactType) else artifact_type
            query = query.eq("artifact_type", artifact_type_value)

        result = query.execute()

        return len(result.data)

    def _to_read_model(self, row: Dict[str, Any]) -> WorkspaceArtifactRead:
        """
        Convert database row to read model.

        Args:
            row: Database row

        Returns:
            WorkspaceArtifactRead instance
        """
        # Parse UUIDs
        row_id = UUID(row["id"]) if row.get("id") else None
        mission_id = UUID(row["mission_id"]) if row.get("mission_id") else None
        node_id = UUID(row["node_id"]) if row.get("node_id") else None
        team_execution_id = UUID(row["team_execution_id"]) if row.get("team_execution_id") else None

        # Parse artifact type
        artifact_type = row.get("artifact_type", "generic_artifact")
        try:
            artifact_type = ArtifactType(artifact_type)
        except ValueError:
            artifact_type = ArtifactType.GENERIC_ARTIFACT

        return WorkspaceArtifactRead(
            id=row_id,
            workspace_id=UUID(row.get("workspace_id")) if row.get("workspace_id") else None,
            mission_id=mission_id,
            node_id=node_id,
            execution_id=row.get("execution_id"),
            team_execution_id=team_execution_id,
            round_number=row.get("round_number"),
            role_name=row.get("role_name"),
            tool_name=row.get("tool_name", ""),
            artifact_type=artifact_type,
            title=row.get("title", ""),
            summary=row.get("summary", ""),
            content_json=row.get("content_json", {}),
            content_text=row.get("content_text", ""),
            source_ref=row.get("source_ref"),
            execution_metadata=row.get("execution_metadata"),
            created_at=row.get("created_at", datetime.now(timezone.utc)),
        )


# ============================================================================
# Helper functions for common queries
# ============================================================================

async def get_team_execution_artifacts_db(
    supabase_client: Any,
    team_execution_id: UUID,
    round_number: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Get artifacts for a team execution using the database function.

    This calls the PostgreSQL function `get_team_execution_artifacts`
    which is more efficient than a raw query.

    Args:
        supabase_client: Supabase client
        team_execution_id: Team execution UUID
        round_number: Optional round number filter

    Returns:
        List of artifact dictionaries
    """
    # Call the database function
    result = supabase_client.rpc(
        "get_team_execution_artifacts",
        params={
            "p_team_execution_id": str(team_execution_id),
            "p_round_number": round_number,
        }
    ).execute()

    return result.data if result.data else []


async def get_execution_artifacts_db(
    supabase_client: Any,
    execution_id: str,
) -> List[Dict[str, Any]]:
    """
    Get artifacts for a workflow execution using the database function.

    Args:
        supabase_client: Supabase client
        execution_id: Workflow execution ID

    Returns:
        List of artifact dictionaries
    """
    result = supabase_client.rpc(
        "get_execution_artifacts",
        params={"p_execution_id": execution_id}
    ).execute()

    return result.data if result.data else []


async def get_workspace_artifacts_paginated_db(
    supabase_client: Any,
    workspace_id: str,
    limit: int = 100,
    offset: int = 0,
    artifact_type: Optional[str] = None,
) -> tuple[List[Dict[str, Any]], int]:
    """
    Get paginated artifacts for a workspace using the database function.

    Returns both the artifacts and the total count.

    Args:
        supabase_client: Supabase client
        workspace_id: Workspace ID
        limit: Maximum results
        offset: Pagination offset
        artifact_type: Optional artifact type filter

    Returns:
        Tuple of (artifacts list, total count)
    """
    result = supabase_client.rpc(
        "get_workspace_artifacts_paginated",
        params={
            "p_workspace_id": workspace_id,
            "p_limit": limit,
            "p_offset": offset,
            "p_artifact_type": artifact_type,
        }
    ).execute()

    if not result.data:
        return [], 0

    # Extract total count from first row
    total_count = result.data[0].get("total_count", 0) if result.data else 0

    return result.data, total_count
