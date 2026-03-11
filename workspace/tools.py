"""
Shared Cognitive Workspace - Agent Tools

Tool definitions for agents to interact with workspaces.
These can be exposed to Prince Flowers, Research Agent, etc.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from .service import workspace_service
from .models import WorkspaceEntryType

logger = logging.getLogger(__name__)


# ============================================================================
# Tool Schemas
# ============================================================================

class AddFactSchema(BaseModel):
    """Schema for adding a fact to workspace."""
    workspace_id: str = Field(..., description="Workspace ID")
    claim: str = Field(..., description="Verified fact")
    source: Optional[str] = Field(None, description="Source of the fact")
    confidence: float = Field(0.9, description="Confidence level (0-1)")


class AddHypothesisSchema(BaseModel):
    """Schema for adding a hypothesis to workspace."""
    workspace_id: str = Field(..., description="Workspace ID")
    hypothesis: str = Field(..., description="Proposed hypothesis")
    rationale: Optional[str] = Field(None, description="Reasoning behind hypothesis")
    confidence: float = Field(0.7, description="Confidence level (0-1)")


class AddQuestionSchema(BaseModel):
    """Schema for adding a question to workspace."""
    workspace_id: str = Field(..., description="Workspace ID")
    question: str = Field(..., description="Unresolved question")
    priority: Optional[str] = Field("medium", description="Priority: low, medium, high")


class AddDecisionSchema(BaseModel):
    """Schema for adding a decision to workspace."""
    workspace_id: str = Field(..., description="Workspace ID")
    decision: str = Field(..., description="Decision made")
    reasoning: Optional[str] = Field(None, description="Reasoning behind decision")
    alternatives_considered: Optional[List[str]] = Field(None, description="Alternatives that were considered")


class AddArtifactSchema(BaseModel):
    """Schema for adding an artifact to workspace."""
    workspace_id: str = Field(..., description="Workspace ID")
    artifact_type: str = Field(..., description="Type of artifact (e.g., 'table', 'report', 'code')")
    title: str = Field(..., description="Artifact title")
    data: Dict[str, Any] = Field(..., description="Artifact data")
    source_agent: Optional[str] = Field(None, description="Agent that created this")


# ============================================================================
# Tool Functions
# ============================================================================

async def add_workspace_fact(
    workspace_id: str,
    claim: str,
    source: Optional[str] = None,
    confidence: float = 0.9
) -> Dict[str, Any]:
    """
    Add a verified fact to the workspace.

    Agents should use this for information they have verified.

    Args:
        workspace_id: Workspace UUID
        claim: The fact to add
        source: Optional source of the fact
        confidence: Confidence level (0-1)

    Returns:
        Created entry response
    """
    from .models import WorkspaceEntryCreate

    entry = WorkspaceEntryCreate(
        entry_type=WorkspaceEntryType.FACT,
        content={
            "claim": claim,
            "source": source,
            "timestamp": datetime.now().isoformat()
        },
        source_agent="agent",  # Would be actual agent name in real usage
        confidence=confidence
    )

    result = await workspace_service.add_entry(workspace_id, entry)
    return {
        "success": True,
        "memory_id": result.memory_id,
        "entry_type": "fact",
        "claim": claim
    }


async def add_workspace_hypothesis(
    workspace_id: str,
    hypothesis: str,
    rationale: Optional[str] = None,
    confidence: float = 0.7
) -> Dict[str, Any]:
    """
    Add a hypothesis to the workspace for testing.

    Hypotheses are tentative insights that need validation.

    Args:
        workspace_id: Workspace UUID
        hypothesis: The hypothesis to add
        rationale: Reasoning behind the hypothesis
        confidence: Confidence level (0-1)

    Returns:
        Created entry response
    """
    from .models import WorkspaceEntryCreate
    from datetime import datetime

    entry = WorkspaceEntryCreate(
        entry_type=WorkspaceEntryType.HYPOTHESIS,
        content={
            "hypothesis": hypothesis,
            "rationale": rationale,
            "timestamp": datetime.now().isoformat()
        },
        source_agent="agent",
        confidence=confidence
    )

    result = await workspace_service.add_entry(workspace_id, entry)
    return {
        "success": True,
        "memory_id": result.memory_id,
        "entry_type": "hypothesis",
        "hypothesis": hypothesis
    }


async def add_workspace_question(
    workspace_id: str,
    question: str,
    priority: str = "medium"
) -> Dict[str, Any]:
    """
    Add an unresolved question to the workspace.

    Questions mark areas that need investigation.

    Args:
        workspace_id: Workspace UUID
        question: The question to add
        priority: Priority level (low, medium, high)

    Returns:
        Created entry response
    """
    from .models import WorkspaceEntryCreate
    from datetime import datetime

    entry = WorkspaceEntryCreate(
        entry_type=WorkspaceEntryType.QUESTION,
        content={
            "question": question,
            "priority": priority,
            "timestamp": datetime.now().isoformat()
        },
        source_agent="agent",
        confidence=0.5  # Questions have low confidence until answered
    )

    result = await workspace_service.add_entry(workspace_id, entry)
    return {
        "success": True,
        "memory_id": result.memory_id,
        "entry_type": "question",
        "question": question
    }


async def add_workspace_decision(
    workspace_id: str,
    decision: str,
    reasoning: Optional[str] = None,
    alternatives_considered: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Add a decision to the workspace.

    Decisions record choices made during planning or execution.

    Args:
        workspace_id: Workspace UUID
        decision: The decision made
        reasoning: Rationale behind the decision
        alternatives_considered: Other options that were considered

    Returns:
        Created entry response
    """
    from .models import WorkspaceEntryCreate
    from datetime import datetime

    entry = WorkspaceEntryCreate(
        entry_type=WorkspaceEntryType.DECISION,
        content={
            "decision": decision,
            "reasoning": reasoning,
            "alternatives_considered": alternatives_considered or [],
            "timestamp": datetime.now().isoformat()
        },
        source_agent="agent",
        confidence=1.0  # Decisions are certain
    )

    result = await workspace_service.add_entry(workspace_id, entry)
    return {
        "success": True,
        "memory_id": result.memory_id,
        "entry_type": "decision",
        "decision": decision
    }


async def resolve_workspace_question(
    workspace_id: str,
    memory_id: str,
    resolution: str
) -> Dict[str, Any]:
    """
    Resolve a question with an answer.

    Args:
        workspace_id: Workspace UUID
        memory_id: Question entry UUID
        resolution: The answer or resolution

    Returns:
        Updated entry response
    """
    result = await workspace_service.resolve_question(
        workspace_id,
        memory_id,
        {"resolution": resolution, "resolved_at": datetime.now().isoformat()}
    )

    return {
        "success": True,
        "memory_id": result.memory_id,
        "status": result.status
    }


async def list_workspace_entries(
    workspace_id: str,
    entry_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    List all entries in a workspace.

    Useful for agents to understand current context before acting.

    Args:
        workspace_id: Workspace UUID
        entry_type: Optional filter by entry type

    Returns:
        Grouped entries by type
    """
    entries = await workspace_service.list_entries(
        workspace_id,
        WorkspaceEntryType(entry_type) if entry_type else None
    )

    return {
        "workspace_id": workspace_id,
        "facts": [e.content for e in entries.facts],
        "hypotheses": [e.content for e in entries.hypotheses],
        "questions": [e.content for e in entries.questions],
        "decisions": [e.content for e in entries.decisions],
        "artifacts": [e.content for e in entries.artifacts],
        "notes": [e.content for e in entries.notes],
        "total": entries.total
    }


async def get_workspace_context_prompt(
    workspace_id: str,
    include_types: Optional[List[str]] = None
) -> str:
    """
    Generate a context prompt for agents based on workspace state.

    This is the key function that injects workspace reasoning into agent prompts.

    Args:
        workspace_id: Workspace UUID
        include_types: Which entry types to include (default: all)

    Returns:
        Formatted context string for agent prompts
    """
    entries = await workspace_service.list_entries(workspace_id)

    context_parts = []

    if include_types is None or "fact" in include_types:
        if entries.facts:
            context_parts.append("Workspace Facts:")
            for entry in entries.facts[:10]:  # Limit to prevent huge prompts
                claim = entry.content.get("claim", str(entry.content))
                source = entry.content.get("source", "")
                context_parts.append(f"  - {claim}" + (f" (source: {source})" if source else ""))

    if include_types is None or "hypothesis" in include_types:
        if entries.hypotheses:
            context_parts.append("Working Hypotheses:")
            for entry in entries.hypotheses[:5]:
                hypothesis = entry.content.get("hypothesis", str(entry.content))
                confidence = int(entry.confidence * 100)
                context_parts.append(f"  - {hypothesis} (confidence: {confidence}%)")

    if include_types is None or "question" in include_types:
        if entries.questions:
            context_parts.append("Open Questions:")
            for entry in entries.questions[:5]:
                question = entry.content.get("question", str(entry.content))
                priority = entry.content.get("priority", "medium")
                context_parts.append(f"  - {question} (priority: {priority})")

    if include_types is None or "decision" in include_types:
        if entries.decisions:
            context_parts.append("Recent Decisions:")
            for entry in entries.decisions[:5]:
                decision = entry.content.get("decision", str(entry.content))
                context_parts.append(f"  - {decision}")

    if context_parts:
        return "\n".join(context_parts)
    else:
        return "Workspace is empty. No prior context available."


# ============================================================================
# Tool Registry (for agent framework integration)
# ============================================================================

WORKSPACE_TOOLS = {
    "add_workspace_fact": {
        "description": "Add a verified fact to the shared workspace",
        "parameters": AddFactSchema
    },
    "add_workspace_hypothesis": {
        "description": "Add a hypothesis to the workspace for validation",
        "parameters": AddHypothesisSchema
    },
    "add_workspace_question": {
        "description": "Add an unresolved question to the workspace",
        "parameters": AddQuestionSchema
    },
    "add_workspace_decision": {
        "description": "Record a decision made during planning",
        "parameters": AddDecisionSchema
    },
    "resolve_workspace_question": {
        "description": "Resolve an open question with an answer",
        "parameters": {
            "workspace_id": str,
            "memory_id": str,
            "resolution": str
        }
    },
    "list_workspace_entries": {
        "description": "List all entries in the workspace",
        "parameters": {
            "workspace_id": str,
            "entry_type": str
        }
    },
    "get_workspace_context": {
        "description": "Get workspace context as formatted prompt",
        "parameters": {
            "workspace_id": str,
            "include_types": List[str]
        }
    },
}


async def call_workspace_tool(
    tool_name: str,
    **kwargs
) -> Any:
    """
    Call a workspace tool by name.

    This is the main entry point for agents to interact with workspaces.

    Args:
        tool_name: Name of the tool to call
        **kwargs: Tool parameters

    Returns:
        Tool result
    """
    tool_map = {
        "add_workspace_fact": add_workspace_fact,
        "add_workspace_hypothesis": add_workspace_hypothesis,
        "add_workspace_question": add_workspace_question,
        "add_workspace_decision": add_workspace_decision,
        "resolve_workspace_question": resolve_workspace_question,
        "list_workspace_entries": list_workspace_entries,
        "get_workspace_context": get_workspace_context_prompt,
    }

    if tool_name not in tool_map:
        raise ValueError(f"Unknown workspace tool: {tool_name}")

    return await tool_map[tool_name](**kwargs)
