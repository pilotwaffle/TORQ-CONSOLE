"""
Workspace Artifact View Models - Phase 5.3 Milestone 4

Clean read models for artifact inspection and API responses.

These models provide a thin abstraction over raw persistence objects,
making both debugging and future UI much cleaner.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# Traceability View Model
# ============================================================================

class TraceabilityViewModel(BaseModel):
    """
    Clean read model for artifact inspection.

    Shows the complete traceability chain from workspace to artifact.
    """

    # Identification
    id: UUID = Field(..., description="Artifact ID")
    artifact_type: str = Field(..., description="Artifact category")
    title: str = Field(..., description="Human-readable title")
    summary: str = Field(..., description="Short summary")
    created_at: datetime = Field(..., description="Creation timestamp")

    # Traceability chain (workspace -> mission -> node -> execution -> team -> role)
    workspace_id: UUID = Field(..., description="Workspace ID")
    mission_id: Optional[UUID] = Field(None, description="Mission ID")
    node_id: Optional[UUID] = Field(None, description="Node ID")
    execution_id: Optional[str] = Field(None, description="Execution ID")
    team_execution_id: Optional[UUID] = Field(None, description="Team execution ID")
    round_number: Optional[int] = Field(None, description="Team round number")
    role_name: Optional[str] = Field(None, description="Role name")

    # Tool info
    tool_name: str = Field(..., description="Tool that created this artifact")

    # Quick stats
    has_content: bool = Field(..., description="Whether artifact has content")
    content_type: str = Field(..., description="Content type: json, text, or mixed")

    class Config:
        from_attributes = True


# ============================================================================
# Artifact Detail View Model
# ============================================================================

class ArtifactDetailViewModel(BaseModel):
    """
    Full artifact detail for inspection.

    Includes complete content and traceability information.
    """

    # Traceability summary
    artifact: TraceabilityViewModel = Field(..., description="Artifact traceability")

    # Content
    content_json: Dict[str, Any] = Field(..., description="Structured content")
    content_text: str = Field(..., description="Plain text content")

    # Execution metadata
    execution_metadata: Dict[str, Any] = Field(..., description="Full execution metadata")

    # Source reference
    source_ref: Optional[str] = Field(None, description="Source reference (URL, file path, etc.)")

    # Full traceability chain
    traceability: TraceabilityChainViewModel = Field(..., description="Traceability chain")

    class Config:
        from_attributes = True


# ============================================================================
# Traceability Chain View Model
# ============================================================================

class TraceabilityChainViewModel(BaseModel):
    """
    Shows the full chain from workspace to artifact.

    Format: workspace -> mission -> node -> execution -> team -> role -> artifact
    """

    workspace: Dict[str, str] = Field(..., description="Workspace reference")
    mission: Optional[Dict[str, str]] = Field(None, description="Mission reference")
    node: Optional[Dict[str, str]] = Field(None, description="Node reference")
    execution: Optional[Dict[str, str]] = Field(None, description="Execution reference")
    team: Optional[Dict[str, Any]] = Field(None, description="Team reference")
    role: Optional[Dict[str, str]] = Field(None, description="Role reference")
    artifact: Dict[str, str] = Field(..., description="Artifact reference")

    def to_display_string(self) -> str:
        """
        Convert traceability chain to human-readable string.

        Returns:
            Human-readable traceability chain
        """
        parts = ["workspace"]

        if self.mission:
            parts.append("mission")
        if self.node:
            parts.append("node")
        if self.execution:
            parts.append("execution")
        if self.team:
            parts.append(f"team (round {self.team.get('round_number', '?')})")
        if self.role:
            parts.append(f"role: {self.role.get('name', '?')}")

        parts.append(f"artifact: {self.artifact.get('artifact_type', '?')}")

        return " -> ".join(parts)


# ============================================================================
# List Response Models
# ============================================================================

class ArtifactListResponse(BaseModel):
    """
    Response model for artifact list endpoint.
    """

    artifacts: List[TraceabilityViewModel] = Field(..., description="Artifacts")
    total_count: int = Field(..., description="Total count matching filters")
    limit: int = Field(..., description="Page size")
    offset: int = Field(..., description="Page offset")
    has_more: bool = Field(..., description="Whether more results exist")

    @classmethod
    def create(
        cls,
        artifacts: List[TraceabilityViewModel],
        total_count: int,
        limit: int,
        offset: int,
    ) -> "ArtifactListResponse":
        """
        Create list response with computed has_more flag.

        Args:
            artifacts: List of artifacts
            total_count: Total count
            limit: Page size
            offset: Page offset

        Returns:
            ArtifactListResponse instance
        """
        return cls(
            artifacts=artifacts,
            total_count=total_count,
            limit=limit,
            offset=offset,
            has_more=offset + len(artifacts) < total_count,
        )


# ============================================================================
# Artifact Summary by Context
# ============================================================================

class ArtifactSummaryByContext(BaseModel):
    """
    Summary of artifacts grouped by context.

    Useful for showing artifact counts per execution, mission, or team.
    """

    context_type: str = Field(..., description="Type of context (execution, mission, team)")
    context_id: str = Field(..., description="Context identifier")
    artifact_count: int = Field(..., description="Number of artifacts")
    artifact_types: Dict[str, int] = Field(..., description="Count by artifact type")
    earliest: Optional[datetime] = Field(None, description="Earliest artifact timestamp")
    latest: Optional[datetime] = Field(None, description="Latest artifact timestamp")


class ArtifactSummaryCollection(BaseModel):
    """
    Collection of artifact summaries by context.
    """

    summaries: List[ArtifactSummaryByContext] = Field(..., description="Summary items")
    total_artifacts: int = Field(..., description="Total artifacts across all contexts")
    total_contexts: int = Field(..., description="Number of contexts")
