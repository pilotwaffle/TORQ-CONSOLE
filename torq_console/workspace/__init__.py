"""
Shared Cognitive Workspace - TORQ Console Team Memory Plane

Provides persistent working memory for multi-agent collaboration.

Phase 5.3: Workspace Artifacts for tool output traceability.
"""

from .api import router
from .service import WorkspaceService
from .agent_tools_api import router as agent_tools_router
from .models import *

# Phase 5.3: Workspace Artifacts
from .artifact_models import *
from .artifact_adapter import ToolOutputAdapter, get_tool_output_adapter, adapt_tool_output
from .artifact_persistence import WorkspaceArtifactPersistence
from .artifact_service import WorkspaceArtifactService, capture_tool_output, get_workspace_artifact_service
from .artifact_context_linker import (
    WorkspaceArtifactContextLinker,
    create_context_linker,
    get_context_linker,
)

# Phase 5.3 Milestone 4: Read and Inspection Layer
from .artifact_read_service import WorkspaceArtifactReadService, get_artifact_read_service
from .artifact_view_models import (
    TraceabilityViewModel,
    ArtifactDetailViewModel,
    TraceabilityChainViewModel,
    ArtifactListResponse,
)
from .artifacts_api import router as artifacts_router

__all__ = [
    # Core workspace
    "router",
    "agent_tools_router",
    "WorkspaceService",

    # Workspace models
    "WorkspaceCreate",
    "WorkspaceRead",
    "WorkspaceEntryCreate",
    "WorkspaceEntryRead",
    "WorkspaceGroupedEntries",
    "WorkspaceScopeType",
    "WorkspaceEntryType",
    "WorkspaceEntryStatus",

    # Phase 5.3: Workspace Artifacts
    "ToolOutputAdapter",
    "get_tool_output_adapter",
    "adapt_tool_output",
    "WorkspaceArtifactPersistence",
    "WorkspaceArtifactService",
    "capture_tool_output",
    "get_workspace_artifact_service",

    # Phase 5.3: Context Linking
    "WorkspaceArtifactContextLinker",
    "create_context_linker",
    "get_context_linker",

    # Phase 5.3 Milestone 4: Read and Inspection Layer
    "WorkspaceArtifactReadService",
    "get_artifact_read_service",
    "TraceabilityViewModel",
    "ArtifactDetailViewModel",
    "TraceabilityChainViewModel",
    "ArtifactListResponse",
    "artifacts_router",

    # Artifact models
    "ArtifactType",
    "WorkspaceArtifactScope",
    "ToolExecutionMetadata",
    "NormalizedArtifact",
    "WorkspaceArtifactCreate",
    "WorkspaceArtifactRead",
    "WorkspaceArtifactListParams",
    "ArtifactSummary",
    "ArtifactCollection",
]
