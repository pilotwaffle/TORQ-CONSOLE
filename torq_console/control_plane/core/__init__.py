"""
TORQ Control Plane - Core

L7-M1: Core functionality for the Operator Control Plane.

Provides:
- State Management
- Routing
- Command Execution
"""

from .state_manager import (
    ControlPlaneState,
    NavigationState,
    UserSession,
    SystemAlert,
    ControlPlaneStateManager,
    get_control_plane_state,
)

from .router import (
    Route,
    RouteMatch,
    ControlPlaneRouter,
    get_control_plane_router,
    CORE_ROUTES,
)

from .commands import (
    CommandStatus,
    OperatorCommand,
    CommandResult,
    CommandHandler,
    CommandExecutor,
    get_command_executor,
)


__all__ = [
    # State Manager
    "ControlPlaneState",
    "NavigationState",
    "UserSession",
    "SystemAlert",
    "ControlPlaneStateManager",
    "get_control_plane_state",

    # Router
    "Route",
    "RouteMatch",
    "ControlPlaneRouter",
    "get_control_plane_router",
    "CORE_ROUTES",

    # Commands
    "CommandStatus",
    "OperatorCommand",
    "CommandResult",
    "CommandHandler",
    "CommandExecutor",
    "get_command_executor",
]
