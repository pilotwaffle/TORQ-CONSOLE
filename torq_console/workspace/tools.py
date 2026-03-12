"""
Agent Workspace Tools

Provides tool definitions for agents to interact with Shared Cognitive Workspace.
Agents can:
- Write reasoning entries (facts, hypotheses, decisions, questions, notes)
- Attach artifacts
- Read workspace context
- Get summaries

This enables agents to contribute to the shared cognitive workspace during execution.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class WorkspaceToolScope(str, Enum):
    """Scope for workspace operations."""
    SESSION = "session"
    WORKFLOW_EXECUTION = "workflow_execution"
    AGENT_TEAM = "agent_team"


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


class WorkspaceWriteFactRequest(BaseModel):
    """Request to write a fact to workspace."""
    workspace_id: str = Field(..., description="Workspace ID")
    fact: str = Field(..., description="Fact statement")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Confidence level")
    source: Optional[str] = Field(None, description="Source of the fact")
    importance: EntryImportance = Field(default=EntryImportance.MEDIUM, description="Entry importance")
    source_type: EntrySourceType = Field(default=EntrySourceType.AGENT, description="Entry source type")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class WorkspaceWriteHypothesisRequest(BaseModel):
    """Request to write a hypothesis to workspace."""
    workspace_id: str = Field(..., description="Workspace ID")
    hypothesis: str = Field(..., description="Hypothesis statement")
    confidence: float = Field(default=0.7, ge=0.0, le=1.0, description="Confidence level")
    reasoning: Optional[str] = Field(None, description="Reasoning behind hypothesis")
    importance: EntryImportance = Field(default=EntryImportance.MEDIUM, description="Entry importance")
    source_type: EntrySourceType = Field(default=EntrySourceType.AGENT, description="Entry source type")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class WorkspaceWriteQuestionRequest(BaseModel):
    """Request to write a question to workspace."""
    workspace_id: str = Field(..., description="Workspace ID")
    question: str = Field(..., description="Question text")
    priority: str = Field(default="medium", description="Priority: low, medium, high")
    context: Optional[str] = Field(None, description="Context for the question")
    importance: EntryImportance = Field(default=EntryImportance.MEDIUM, description="Entry importance")
    source_type: EntrySourceType = Field(default=EntrySourceType.AGENT, description="Entry source type")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class WorkspaceWriteDecisionRequest(BaseModel):
    """Request to write a decision to workspace."""
    workspace_id: str = Field(..., description="Workspace ID")
    decision: str = Field(..., description="Decision statement")
    rationale: str = Field(..., description="Rationale for the decision")
    alternatives: List[str] = Field(default_factory=list, description="Alternatives considered")
    importance: EntryImportance = Field(default=EntryImportance.HIGH, description="Entry importance")
    source_type: EntrySourceType = Field(default=EntrySourceType.AGENT, description="Entry source type")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class WorkspaceWriteNoteRequest(BaseModel):
    """Request to write a note to workspace."""
    workspace_id: str = Field(..., description="Workspace ID")
    note: str = Field(..., description="Note content")
    category: Optional[str] = Field(None, description="Category for organization")
    importance: EntryImportance = Field(default=EntryImportance.LOW, description="Entry importance")
    source_type: EntrySourceType = Field(default=EntrySourceType.AGENT, description="Entry source type")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class WorkspaceAttachArtifactRequest(BaseModel):
    """Request to attach an artifact to workspace."""
    workspace_id: str = Field(..., description="Workspace ID")
    artifact_type: str = Field(..., description="Type of artifact (e.g., 'chart', 'document', 'data')")
    title: str = Field(..., description="Artifact title")
    content: Any = Field(..., description="Artifact content (can be any JSON-serializable data)")
    importance: EntryImportance = Field(default=EntryImportance.MEDIUM, description="Entry importance")
    source_type: EntrySourceType = Field(default=EntrySourceType.AGENT, description="Entry source type")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class WorkspaceReadContextRequest(BaseModel):
    """Request to read workspace context."""
    workspace_id: str = Field(..., description="Workspace ID")
    entry_types: Optional[List[str]] = Field(None, description="Filter by entry types")
    limit: int = Field(default=100, ge=1, le=1000, description="Max entries to return")
    min_importance: Optional[EntryImportance] = Field(None, description="Filter by minimum importance")


class WorkspaceGetSummaryRequest(BaseModel):
    """Request to get workspace summary."""
    workspace_id: str = Field(..., description="Workspace ID")
    include_counts: bool = Field(default=True, description="Include entry counts")


# ============================================================================
# Agent Tool Registry
# ============================================================================

AGENT_WORKSPACE_TOOLS = {
    "workspace_write_fact": {
        "name": "Write Fact to Workspace",
        "description": "Record a verified fact to the shared cognitive workspace",
        "parameters": "workspace_id, fact, confidence, source",
        "request_model": WorkspaceWriteFactRequest,
    },
    "workspace_write_hypothesis": {
        "name": "Write Hypothesis to Workspace",
        "description": "Record a hypothesis or theory to the shared cognitive workspace",
        "parameters": "workspace_id, hypothesis, confidence, reasoning",
        "request_model": WorkspaceWriteHypothesisRequest,
    },
    "workspace_write_question": {
        "name": "Write Question to Workspace",
        "description": "Record an open question to the shared cognitive workspace",
        "parameters": "workspace_id, question, priority, context",
        "request_model": WorkspaceWriteQuestionRequest,
    },
    "workspace_write_decision": {
        "name": "Write Decision to Workspace",
        "description": "Record a decision with rationale to the shared cognitive workspace",
        "parameters": "workspace_id, decision, rationale, alternatives",
        "request_model": WorkspaceWriteDecisionRequest,
    },
    "workspace_write_note": {
        "name": "Write Note to Workspace",
        "description": "Record a note or observation to the shared cognitive workspace",
        "parameters": "workspace_id, note, category",
        "request_model": WorkspaceWriteNoteRequest,
    },
    "workspace_attach_artifact": {
        "name": "Attach Artifact to Workspace",
        "description": "Attach an artifact (chart, document, data) to the workspace",
        "parameters": "workspace_id, artifact_type, title, content",
        "request_model": WorkspaceAttachArtifactRequest,
    },
    "workspace_read_context": {
        "name": "Read Workspace Context",
        "description": "Read entries from the workspace for context",
        "parameters": "workspace_id, entry_types, limit",
        "request_model": WorkspaceReadContextRequest,
    },
    "workspace_get_summary": {
        "name": "Get Workspace Summary",
        "description": "Get a summary of the workspace state",
        "parameters": "workspace_id, include_counts",
        "request_model": WorkspaceGetSummaryRequest,
    },
}


def get_agent_tools() -> Dict[str, Dict[str, Any]]:
    """Get available agent workspace tools."""
    return AGENT_WORKSPACE_TOOLS


def get_tool_schema(tool_name: str) -> Optional[Dict[str, Any]]:
    """Get schema for a specific tool."""
    return AGENT_WORKSPACE_TOOLS.get(tool_name)


def list_available_tools() -> List[str]:
    """List all available workspace tools for agents."""
    return list(AGENT_WORKSPACE_TOOLS.keys())
