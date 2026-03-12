"""
Shared Cognitive Workspace - Data Models

Pydantic models for workspace API requests and responses.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Enums
# ============================================================================

class WorkspaceScopeType(str, Enum):
    """Types of workspace scopes."""
    SESSION = "session"
    WORKFLOW_EXECUTION = "workflow_execution"
    AGENT_TEAM = "agent_team"


class WorkspaceEntryType(str, Enum):
    """Types of workspace entries."""
    FACT = "fact"
    HYPOTHESIS = "hypothesis"
    QUESTION = "question"
    DECISION = "decision"
    ARTIFACT = "artifact"
    NOTE = "note"


class WorkspaceEntryStatus(str, Enum):
    """Lifecycle status of workspace entries."""
    ACTIVE = "active"
    RESOLVED = "resolved"
    REVISED = "revised"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


# ============================================================================
# Request Models
# ============================================================================

class WorkspaceCreate(BaseModel):
    """Request to create a new workspace."""
    scope_type: WorkspaceScopeType
    scope_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    created_by: Optional[str] = "system"

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "scope_type": "workflow_execution",
            "scope_id": "exec_123",
            "title": "AI Competitor Research",
            "description": "Researching AI consulting market competitors"
        }
    })


class WorkspaceEntryCreate(BaseModel):
    """Request to add an entry to a workspace."""
    entry_type: WorkspaceEntryType
    content: Dict[str, Any] = Field(..., description="Structured content based on entry_type")
    source_agent: Optional[str] = None
    confidence: Optional[float] = Field(default=0.8, ge=0.0, le=1.0)

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "entry_type": "fact",
            "content": {
                "claim": "OpenAI consulting projects range from $25k to $120k",
                "source": "industry_analysis"
            },
            "source_agent": "research_agent",
            "confidence": 0.92
        }
    })


class WorkspaceEntryUpdate(BaseModel):
    """Request to update a workspace entry."""
    content: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    status: Optional[WorkspaceEntryStatus] = None


class WorkspaceResolveRequest(BaseModel):
    """Request to resolve a question entry."""
    resolution: Dict[str, Any] = Field(..., description="Resolution or answer to the question")


# ============================================================================
# Response Models
# ============================================================================

class WorkspaceResponse(BaseModel):
    """Workspace response."""
    workspace_id: str
    scope_type: str
    scope_id: str
    title: Optional[str]
    description: Optional[str]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    entry_count: int = 0


class WorkspaceEntryResponse(BaseModel):
    """Workspace entry response."""
    memory_id: str
    workspace_id: str
    entry_type: str
    content: Dict[str, Any]
    source_agent: Optional[str]
    confidence: float
    status: str
    created_at: datetime
    updated_at: datetime


class WorkspaceListResponse(BaseModel):
    """Paginated list of workspaces."""
    workspaces: List[WorkspaceResponse]
    total: int


class WorkspaceEntriesResponse(BaseModel):
    """Entries in a workspace, grouped by type."""
    workspace_id: str
    facts: List[WorkspaceEntryResponse] = []
    hypotheses: List[WorkspaceEntryResponse] = []
    questions: List[WorkspaceEntryResponse] = []
    decisions: List[WorkspaceEntryResponse] = []
    artifacts: List[WorkspaceEntryResponse] = []
    notes: List[WorkspaceEntryResponse] = []
    total: int = 0


class WorkspaceSummaryResponse(BaseModel):
    """LLM-generated summary of workspace state."""
    workspace_id: str
    summary: str
    current_understanding: str
    unresolved_questions: List[str]
    key_decisions: List[str]
    generated_at: datetime


# ============================================================================
# Internal Models
# ============================================================================

class WorkspaceDB(BaseModel):
    """Internal workspace representation from database."""
    workspace_id: str
    scope_type: str
    scope_id: str
    title: Optional[str]
    description: Optional[str]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime


class WorkspaceEntryDB(BaseModel):
    """Internal entry representation from database."""
    memory_id: str
    workspace_id: str
    entry_type: str
    content: Dict[str, Any]
    source_agent: Optional[str]
    confidence: float
    status: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
