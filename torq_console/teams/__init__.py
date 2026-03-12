"""
Agent Teams Module

Phase 5.2: Agent Teams as a governed execution primitive.
Phase 5.2B: Observability + UI (read-only)

This module provides multi-agent team collaboration capabilities
for TORQ Console mission execution.

Exports:
    - execute_team_node: Main entry point for team execution
    - AgentTeamOrchestrator: Team orchestration engine
    - TeamDefinitionRegistry: Team definition management
    - TeamPersistence: Database persistence layer
    - View models: UI presentation layer (Phase 5.2B)
"""

from .models import (
    # Enums
    TeamPattern,
    DecisionPolicy,
    TeamExecutionStatus,
    DecisionOutcome,
    TeamRole,
    MessageType,
    ValidatorStatus,
    RoleTaskState,
    # Models
    TeamDefinition,
    TeamMemberRole,
    TeamExecutionContext,
    TeamExecution,
    TeamMessage,
    TeamExecutionResult,
    RoleTask,
    # Response Models
    TeamDefinitionResponse,
    TeamExecutionResponse,
    TeamMessageResponse,
    TeamDecisionResponse,
    CreateTeamRequest,
    ExecuteTeamNodeRequest,
)

from .registry import (
    TeamDefinitionRegistry,
    get_registry,
    initialize_registry,
)

from .orchestrator import (
    AgentTeamOrchestrator,
    execute_team_node,
)

from .role_runner import (
    RoleRunner,
    execute_role_task,
)

from .decision_engine import (
    DecisionEngine,
    DecisionResult,
)

from .persistence import (
    TeamPersistence,
)

from .context import (
    TeamContextManager,
)

__all__ = [
    # Enums
    "TeamPattern",
    "DecisionPolicy",
    "TeamExecutionStatus",
    "DecisionOutcome",
    "TeamRole",
    "MessageType",
    "ValidatorStatus",
    "RoleTaskState",
    # Models
    "TeamDefinition",
    "TeamMemberRole",
    "TeamExecutionContext",
    "TeamExecution",
    "TeamMessage",
    "TeamExecutionResult",
    "RoleTask",
    # Response Models
    "TeamDefinitionResponse",
    "TeamExecutionResponse",
    "TeamMessageResponse",
    "TeamDecisionResponse",
    "CreateTeamRequest",
    "ExecuteTeamNodeRequest",
    # Registry
    "TeamDefinitionRegistry",
    "get_registry",
    "initialize_registry",
    # Core
    "AgentTeamOrchestrator",
    "execute_team_node",
    "RoleRunner",
    "execute_role_task",
    "DecisionEngine",
    "DecisionResult",
    "TeamPersistence",
    "TeamContextManager",
]


# Version info
__version__ = "0.1.0"
__phase__ = "5.2"
