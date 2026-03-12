"""
Workspace Artifact Models - Phase 5.3 Milestone 1

Normalized artifact contract for tool outputs.

This module defines the Pydantic models for workspace artifacts,
providing a consistent structure for tool outputs that can be
persisted to the shared workspace and linked to execution context.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ============================================================================
# Artifact Type Enumeration
# ============================================================================

class ArtifactType(str, Enum):
    """Categories of workspace artifacts from tool execution."""

    # Web/Research artifacts
    WEB_SEARCH = "web_search"
    NEWS_SEARCH = "news_search"
    RESEARCH_SYNTHESIS = "research_synthesis"

    # File operations
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"

    # Database operations
    DATABASE_QUERY = "database_query"

    # Code execution
    CODE_EXECUTION = "code_execution"

    # API calls
    API_CALL = "api_call"

    # Document generation
    DOCUMENT_GENERATION = "document_generation"

    # Data operations
    DATA_ANALYSIS = "data_analysis"
    DATA_VISUALIZATION = "data_visualization"

    # Knowledge operations
    KNOWLEDGE_QUERY = "knowledge_query"
    VALIDATION = "validation"
    SYNTHESIS = "synthesis"

    # Team artifacts
    TEAM_DECISION = "team_decision"
    TEAM_MESSAGE = "team_message"
    ROLE_OUTPUT = "role_output"

    # Generic
    GENERIC_ARTIFACT = "generic_artifact"


# ============================================================================
# Workspace Scope Hierarchy (from PRD)
# ============================================================================

class WorkspaceArtifactScope(str, Enum):
    """
    Narrowest relevant workspace scope for an artifact.

    Artifacts should be written to the narrowest relevant scope
    and only referenced upward when necessary.
    """

    WORKFLOW_EXECUTION = "workflow_execution"
    TEAM_EXECUTION = "team_execution"
    TEAM_ROUND = "team_round"
    NODE_EXECUTION = "node_execution"


# ============================================================================
# Core Artifact Models
# ============================================================================

class ToolExecutionMetadata(BaseModel):
    """
    Metadata captured during tool execution.

    This includes timing, status, and execution context
    without exposing raw tool-specific payloads.
    """

    tool_name: str = Field(..., description="Tool identifier (e.g., 'web_search', 'file_read')")
    tool_version: Optional[str] = Field(None, description="Tool version if available")
    execution_id: Optional[str] = Field(None, description="Workflow execution ID")
    team_execution_id: Optional[UUID] = Field(None, description="Team execution ID")
    round_number: Optional[int] = Field(None, description="Team round number")
    role_name: Optional[str] = Field(None, description="Invoking role (e.g., 'lead', 'researcher')")
    node_id: Optional[UUID] = Field(None, description="Mission graph node ID")
    mission_id: Optional[UUID] = Field(None, description="Mission ID")

    # Execution metrics
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(None)
    duration_seconds: Optional[float] = Field(None, description="Execution duration")
    success: bool = Field(True, description="Whether tool execution succeeded")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    cached: bool = Field(False, description="Whether result was from cache")

    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional tool-specific metadata")


class NormalizedArtifact(BaseModel):
    """
    Normalized artifact structure.

    This is the output format from ToolOutputAdapter - a consistent
    structure representing tool execution results.
    """

    # Core identification
    artifact_type: ArtifactType = Field(..., description="Category of artifact")
    title: str = Field(..., description="Human-readable title")
    summary: str = Field(..., description="Short summary for retrieval and UI")

    # Content (normalized)
    content_json: Dict[str, Any] = Field(default_factory=dict, description="Structured artifact payload")
    content_text: str = Field("", description="Plain text representation")

    # Source tracking
    source_ref: Optional[str] = Field(None, description="Optional source reference (URL, file path, etc.)")

    # Execution context
    execution_metadata: ToolExecutionMetadata = Field(..., description="Tool execution metadata")

    # Workspace linking (filled by persistence layer)
    workspace_id: Optional[str] = Field(None, description="Workspace ID (assigned on persist)")
    artifact_id: Optional[UUID] = Field(None, description="Artifact ID (assigned on persist)")

    def to_persist_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Supabase persistence."""
        return {
            "artifact_type": self.artifact_type.value,
            "title": self.title,
            "summary": self.summary,
            "content_json": self.content_json,
            "content_text": self.content_text,
            "source_ref": self.source_ref,
            # Execution context fields from metadata
            "mission_id": str(self.execution_metadata.mission_id) if self.execution_metadata.mission_id else None,
            "node_id": str(self.execution_metadata.node_id) if self.execution_metadata.node_id else None,
            "execution_id": self.execution_metadata.execution_id,
            "team_execution_id": str(self.execution_metadata.team_execution_id) if self.execution_metadata.team_execution_id else None,
            "round_number": self.execution_metadata.round_number,
            "role_name": self.execution_metadata.role_name,
            "tool_name": self.execution_metadata.tool_name,
            # Additional metadata stored as JSON
            "execution_metadata": self.execution_metadata.model_dump(),
        }


class WorkspaceArtifactCreate(BaseModel):
    """
    Request model for creating a workspace artifact.
    """

    workspace_id: UUID = Field(..., description="Target workspace ID")
    mission_id: Optional[UUID] = Field(None, description="Mission reference")
    node_id: Optional[UUID] = Field(None, description="Node reference")
    execution_id: Optional[str] = Field(None, description="Workflow execution reference")
    team_execution_id: Optional[UUID] = Field(None, description="Team execution reference")
    round_number: Optional[int] = Field(None, description="Round number")
    role_name: Optional[str] = Field(None, description="Invoking role")
    tool_name: str = Field(..., description="Tool identifier")
    artifact_type: ArtifactType = Field(..., description="Artifact category")
    title: str = Field(..., description="Human-readable title")
    summary: str = Field(..., description="Short summary for retrieval")
    content_json: Dict[str, Any] = Field(default_factory=dict, description="Structured payload")
    content_text: str = Field("", description="Plain text representation")
    source_ref: Optional[str] = Field(None, description="Source reference")


class WorkspaceArtifactRead(BaseModel):
    """
    Response model for a workspace artifact.
    """

    id: UUID = Field(..., description="Artifact ID")
    workspace_id: UUID = Field(..., description="Workspace reference")
    mission_id: Optional[UUID] = Field(None, description="Mission reference")
    node_id: Optional[UUID] = Field(None, description="Node reference")
    execution_id: Optional[str] = Field(None, description="Execution reference")
    team_execution_id: Optional[UUID] = Field(None, description="Team execution reference")
    round_number: Optional[int] = Field(None, description="Round number")
    role_name: Optional[str] = Field(None, description="Invoking role")
    tool_name: str = Field(..., description="Tool identifier")
    artifact_type: ArtifactType = Field(..., description="Artifact category")
    title: str = Field(..., description="Human-readable title")
    summary: str = Field(..., description="Short summary")
    content_json: Dict[str, Any] = Field(default_factory=dict, description="Structured payload")
    content_text: str = Field("", description="Plain text representation")
    source_ref: Optional[str] = Field(None, description="Source reference")
    execution_metadata: Optional[Dict[str, Any]] = Field(None, description="Full execution metadata")
    created_at: datetime = Field(..., description="Creation timestamp")


class WorkspaceArtifactListParams(BaseModel):
    """
    Query parameters for listing artifacts.
    """

    workspace_id: Optional[Union[str, UUID]] = Field(None, description="Filter by workspace")
    execution_id: Optional[str] = Field(None, description="Filter by execution")
    team_execution_id: Optional[UUID] = Field(None, description="Filter by team execution")
    mission_id: Optional[UUID] = Field(None, description="Filter by mission")
    artifact_type: Optional[ArtifactType] = Field(None, description="Filter by artifact type")
    tool_name: Optional[str] = Field(None, description="Filter by tool name")
    limit: int = Field(100, ge=1, le=1000, description="Maximum results")
    offset: int = Field(0, ge=0, description="Offset for pagination")
    order_by: str = Field("created_at", description="Sort field")
    order_desc: bool = Field(True, description="Sort descending")


# ============================================================================
# Artifact Summary Models
# ============================================================================

class ArtifactSummary(BaseModel):
    """
    Lightweight summary of an artifact for list views.
    """

    id: UUID
    artifact_type: ArtifactType
    tool_name: str
    title: str
    summary: str
    created_at: datetime
    role_name: Optional[str] = None
    team_execution_id: Optional[UUID] = None
    round_number: Optional[int] = None


class ArtifactCollection(BaseModel):
    """
    Collection of artifacts with metadata.
    """

    artifacts: List[ArtifactSummary]
    total_count: int
    filtered_type: Optional[ArtifactType] = None
    filtered_tool: Optional[str] = None
