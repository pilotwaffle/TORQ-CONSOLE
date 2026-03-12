"""
Request and response models for Workflow Planning Copilot.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


# Allowed agent IDs in TORQ Console
AllowedAgentId = Literal[
    "conversational_agent",
    "workflow_agent",
    "research_agent",
    "orchestration_agent",
    "torq_prince_flowers",
]

# Allowed node types for v1
AllowedNodeType = Literal["agent"]


class WorkflowPlannerRequest(BaseModel):
    """Request to generate a workflow draft from a prompt."""

    prompt: str = Field(..., min_length=10, max_length=4000, description="User's natural language workflow description")
    session_id: Optional[str] = Field(default=None, max_length=200, description="Optional session ID for context")
    tenant_id: Optional[str] = Field(default="default", max_length=200, description="Tenant identifier")
    workspace_id: Optional[str] = Field(default=None, max_length=200, description="Optional workspace ID to write reasoning entries")
    write_reasoning: bool = Field(default=True, description="Whether to write reasoning entries to workspace")


class DraftNode(BaseModel):
    """A single node in a generated workflow draft."""

    node_key: str = Field(..., min_length=1, max_length=100, description="Unique identifier for this node")
    name: str = Field(..., min_length=1, max_length=200, description="Human-readable node name")
    node_type: AllowedNodeType = Field(default="agent", description="Type of node (agent for v1)")
    agent_id: AllowedAgentId = Field(..., description="Which agent to use for this node")
    depends_on: List[str] = Field(default_factory=list, description="List of node_keys this node depends on")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters to pass to the agent")
    timeout_seconds: int = Field(default=300, ge=10, le=1800, description="Max runtime for this node")
    retry_policy: Dict[str, Any] = Field(
        default_factory=lambda: {
            "max_retries": 3,
            "retry_delay_ms": 1000,
            "failure_strategy": "retry",
        }
    )

    @field_validator("node_key")
    @classmethod
    def normalize_node_key(cls, v: str) -> str:
        """Normalize node_key to lowercase with underscores."""
        return v.strip().lower().replace(" ", "_").replace("-", "_")


class DraftEdge(BaseModel):
    """A directed edge between two nodes."""

    source_node_key: str = Field(..., description="Source node key")
    target_node_key: str = Field(..., description="Target node key")


class WorkflowDraft(BaseModel):
    """A complete generated workflow draft."""

    name: str = Field(..., min_length=1, max_length=200, description="Workflow name")
    description: str = Field(..., min_length=1, max_length=1000, description="Workflow description")
    rationale: Optional[str] = Field(default=None, max_length=2000, description="Why this workflow was designed this way")
    nodes: List[DraftNode] = Field(..., min_length=1, max_length=10, description="Nodes in the workflow")
    edges: List[DraftEdge] = Field(default_factory=list, description="Edges between nodes")
    limits: Dict[str, Any] = Field(
        default_factory=lambda: {
            "max_nodes": 10,
            "max_runtime_seconds": 900,
            "max_parallel_nodes": 3,
        }
    )


class WorkflowPlannerResponse(BaseModel):
    """Response from workflow draft generation."""

    success: bool = Field(..., description="Whether generation succeeded")
    draft: Optional[WorkflowDraft] = Field(None, description="Generated workflow draft if successful")
    error_code: Optional[str] = Field(None, description="Error code if failed")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    generation_time_ms: Optional[int] = Field(None, description="Time taken to generate in milliseconds")
