"""
TORQ Console - Layer 7: Operator Control Plane

This module provides the human-facing governance layer that allows operators to:

- Observe system intelligence
- Inspect readiness decisions
- Manage governance actions
- Monitor agent execution
- Promote operational capabilities safely

Layer 7 Architecture:
    Intelligence Producers (Layers 1-6)
                    │
                    ▼
        ┌───────────────────────────┐
        │   Control Plane Core     │
        │  (State Management)      │
        └───────────────────────────┘
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
    ┌─────────┐ ┌─────────┐ ┌──────────┐
    │Readiness│ │Mission  │ │Pattern   │
    │Governance│ │Command  │ │Intelligence│
    │   UI    │ │ Center  │ │ Monitor  │
    └─────────┘ └─────────┘ └──────────┘
        │           │           │
        └───────────┼───────────┘
                    ▼
          ┌─────────────────┐
          │ Operator Action │
          │    Interface    │
          └─────────────────┘

Phase Milestones:
    L7-M1: Control Plane Core + Routing ✅ (starting)
    L7-M2: Readiness Governance UI
    L7-M3: Mission Command Center
    L7-M4: Pattern Intelligence Monitor
    L7-M5: Operational Intelligence Dashboard
"""

from .core.state_manager import (
    ControlPlaneState,
    get_control_plane_state,
)

from .core.router import (
    ControlPlaneRouter,
    Route,
    get_control_plane_router,
)

from .core.commands import (
    OperatorCommand,
    CommandResult,
    CommandExecutor,
    get_command_executor,
)

from .dashboards.models import (
    DashboardWidget,
    DashboardLayout,
    DashboardConfig,
)

from .dashboards.monitoring import (
    SystemMonitor,
    SystemMetrics,
    get_system_monitor,
)

from .governance.models import (
    GovernanceActionRequest,
    GovernanceActionQueue,
    GovernanceOverride,
)

from .governance.controller import (
    GovernanceController,
    get_governance_controller,
)

from .intelligence.models import (
    IntelligenceView,
    IntelligenceLayer,
    LayerStatus,
)

from .intelligence.aggregator import (
    IntelligenceAggregator,
    get_intelligence_aggregator,
)


__all__ = [
    # Core
    "ControlPlaneState",
    "get_control_plane_state",
    "ControlPlaneRouter",
    "Route",
    "get_control_plane_router",
    "OperatorCommand",
    "CommandResult",
    "CommandExecutor",
    "get_command_executor",

    # Dashboards
    "DashboardWidget",
    "DashboardLayout",
    "DashboardConfig",
    "SystemMonitor",
    "SystemMetrics",
    "get_system_monitor",

    # Governance
    "GovernanceActionRequest",
    "GovernanceActionQueue",
    "GovernanceOverride",
    "GovernanceController",
    "get_governance_controller",

    # Intelligence
    "IntelligenceView",
    "IntelligenceLayer",
    "LayerStatus",
    "IntelligenceAggregator",
    "get_intelligence_aggregator",
]
