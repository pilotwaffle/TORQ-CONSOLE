"""
TORQ Console - Shared Cognitive Workspace (Team Memory Plane)

Persistent structured working memory layer for multi-agent collaboration.
Enables agents, workflows, and users to share reasoning artifacts.

Entry Types:
    - fact: Verified information
    - hypothesis: Proposed interpretation or insight
    - question: Unresolved investigation topic
    - decision: Workflow or planning choice
    - artifact: Intermediate data or outputs
    - note: General notes
"""

from .models import (
    WorkspaceScopeType,
    WorkspaceEntryType,
    WorkspaceEntryStatus,
    WorkspaceCreate,
    WorkspaceEntryCreate,
    WorkspaceEntryUpdate,
    WorkspaceResponse,
    WorkspaceEntryResponse,
    WorkspaceListResponse,
    WorkspaceSummaryResponse,
)
from .service import WorkspaceService

__all__ = [
    "WorkspaceScopeType",
    "WorkspaceEntryType",
    "WorkspaceEntryStatus",
    "WorkspaceCreate",
    "WorkspaceEntryCreate",
    "WorkspaceEntryUpdate",
    "WorkspaceResponse",
    "WorkspaceEntryResponse",
    "WorkspaceSummaryResponse",
    "WorkspaceService",
]
