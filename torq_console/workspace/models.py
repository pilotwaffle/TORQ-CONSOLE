from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class WorkspaceScopeType(str, Enum):
    SESSION = "session"
    WORKFLOW_EXECUTION = "workflow_execution"
    AGENT_TEAM = "agent_team"


class WorkspaceEntryType(str, Enum):
    FACT = "fact"
    HYPOTHESIS = "hypothesis"
    QUESTION = "question"
    DECISION = "decision"
    ARTIFACT = "artifact"
    NOTE = "note"


class WorkspaceEntryStatus(str, Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    REVISED = "revised"
    DEPRECATED = "deprecated"


class WorkspaceCreate(BaseModel):
    scope_type: WorkspaceScopeType
    scope_id: str = Field(..., min_length=1, max_length=255)
    title: Optional[str] = None
    description: Optional[str] = None
    created_by: Optional[str] = None
    tenant_id: str = "default"


class WorkspaceRead(BaseModel):
    workspace_id: str
    scope_type: WorkspaceScopeType
    scope_id: str
    tenant_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class EntryImportance(str, Enum):
    """Importance level for workspace entries."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EntrySourceType(str, Enum):
    """Provenance source for workspace entries."""
    AGENT = "agent"
    TOOL = "tool"
    USER = "user"
    SYSTEM = "system"
    SYNTHESIS = "synthesis"


class WorkspaceEntryCreate(BaseModel):
    entry_type: WorkspaceEntryType
    content: Dict[str, Any]
    source_agent: Optional[str] = None
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    status: WorkspaceEntryStatus = WorkspaceEntryStatus.ACTIVE
    importance: EntryImportance = EntryImportance.MEDIUM
    source_type: EntrySourceType = EntrySourceType.AGENT
    execution_id: Optional[str] = None


class WorkspaceEntryUpdate(BaseModel):
    content: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    status: Optional[WorkspaceEntryStatus] = None
    importance: Optional[EntryImportance] = None


class WorkspaceEntryRead(BaseModel):
    memory_id: str
    workspace_id: str
    tenant_id: str
    entry_type: WorkspaceEntryType
    content: Dict[str, Any]
    source_agent: Optional[str] = None
    confidence: float
    status: WorkspaceEntryStatus
    importance: EntryImportance
    source_type: EntrySourceType
    execution_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class WorkspaceGroupedEntries(BaseModel):
    workspace_id: str
    facts: List[WorkspaceEntryRead] = []
    hypotheses: List[WorkspaceEntryRead] = []
    questions: List[WorkspaceEntryRead] = []
    decisions: List[WorkspaceEntryRead] = []
    artifacts: List[WorkspaceEntryRead] = []
    notes: List[WorkspaceEntryRead] = []


class WorkspaceSummaryRequest(BaseModel):
    model: Optional[str] = None


class WorkspaceSummaryResponse(BaseModel):
    workspace_id: str
    summary: str
    facts_count: int
    hypotheses_count: int
    questions_count: int
    decisions_count: int
    generated_at: datetime
