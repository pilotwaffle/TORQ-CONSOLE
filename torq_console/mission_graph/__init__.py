"""
Mission Graph Planning - Phase 5
Execution Fabric - Phase 5.1

Phase 5 turns TORQ from a system that runs agents into a system that structures
complex missions the way a strong consulting team would.

Phase 5.1 adds the Execution Fabric layer that provides coordinated, stateful
team execution with shared mission context.

Mission Graphs contain:
- Objective nodes (top-level goals)
- Task nodes (concrete work items)
- Decision nodes (branch points with gates)
- Evidence nodes (required data/artifacts)
- Deliverable nodes (expected outputs)

Execution Fabric provides:
- Context Bus for event-driven coordination
- Handoff Manager for collaboration-centric data transfer
- Workstream State Manager for parallel workstream tracking
- Replanning Engine for dynamic graph mutation
- Checkpoint Manager for rollback and recovery

This enables:
- Parallel execution where valid
- Explicit dependency handling
- Decision gates with escalation logic
- Strategic memory injection per node
- Hierarchical agent team coordination
- Shared context across agents and workstreams
- Reactive coordination through events
- Recovery from failures and rollbacks
"""

from .models import (
    # Mission types
    MissionStatus,
    MissionType,

    # Graph types
    GraphStatus,

    # Node types
    NodeType,
    NodeStatus,
    NodePriority,

    # Edge types
    EdgeType,

    # Reasoning strategies
    ReasoningStrategy,

    # Agent types
    AgentType,

    # Core models
    Mission,
    MissionGraph,
    MissionNode,
    MissionEdge,
    MissionNodeOutput,

    # Decision gates
    DecisionGateType,
    GateCondition,
    DecisionOutcome,

    # Requests
    MissionCreateRequest,
    MissionGraphCreateRequest,

    # Execution
    NodeExecutionRequest,
    NodeExecutionResult,
    GraphExecutionState,

    # Workstreams
    Workstream,

    # Templates
    EXAMPLE_MARKET_ENTRY_GRAPH,
)

from .builder import (
    MissionGraphBuilder,
    GraphTemplate,
)

from .scheduler import (
    SchedulerState,
    MissionGraphScheduler,
)

from .executor import (
    MissionNodeExecutor,
    MissionCompleter,
    NodeExecutionError,
    IdempotencyViolationError,
)

# Phase 5.1: Execution Fabric
from .context_bus import (
    MissionEventType,
    MissionEvent,
    MissionContextBus,
    ContextBusManager,
)

from .handoffs import (
    HandoffStatus,
    HandoffPacket,
    HandoffValidation,
    HandoffManager,
)

from .workstream_state import (
    WorkstreamPhase,
    WorkstreamHealth,
    BlockerSeverity,
    Blocker,
    WorkstreamState,
    WorkstreamTransition,
    WorkstreamStateManager,
)

from .replanning import (
    ReplanTriggerType,
    ReplanScope,
    ReplanStatus,
    ReplanTrigger,
    ReplanAction,
    ReplanProposal,
    ReplanConfig,
    ReplanningEngine,
)

from .checkpoints import (
    CheckpointType,
    CheckpointStatus,
    CheckpointMetadata,
    CheckpointData,
    RestoreResult,
    CheckpointManager,
)

__all__ = [
    # Mission types
    "MissionStatus",
    "MissionType",

    # Graph types
    "GraphStatus",

    # Node types
    "NodeType",
    "NodeStatus",
    "NodePriority",

    # Edge types
    "EdgeType",

    # Reasoning strategies
    "ReasoningStrategy",

    # Agent types
    "AgentType",

    # Core models
    "Mission",
    "MissionGraph",
    "MissionNode",
    "MissionEdge",
    "MissionNodeOutput",

    # Decision gates
    "DecisionGateType",
    "GateCondition",
    "DecisionOutcome",

    # Requests
    "MissionCreateRequest",
    "MissionGraphCreateRequest",

    # Execution
    "NodeExecutionRequest",
    "NodeExecutionResult",
    "GraphExecutionState",

    # Hardened Execution (Phase 5.1.1)
    "MissionNodeExecutor",
    "MissionCompleter",
    "NodeExecutionError",
    "IdempotencyViolationError",

    # Workstreams
    "Workstream",

    # Templates
    "EXAMPLE_MARKET_ENTRY_GRAPH",

    # Builder
    "MissionGraphBuilder",
    "GraphTemplate",

    # Scheduler
    "SchedulerState",
    "MissionGraphScheduler",

    # Phase 5.1: Execution Fabric - Context Bus
    "MissionEventType",
    "MissionEvent",
    "MissionContextBus",
    "ContextBusManager",

    # Phase 5.1: Execution Fabric - Handoffs
    "HandoffStatus",
    "HandoffPacket",
    "HandoffValidation",
    "HandoffManager",

    # Phase 5.1: Execution Fabric - Workstream State
    "WorkstreamPhase",
    "WorkstreamHealth",
    "BlockerSeverity",
    "Blocker",
    "WorkstreamState",
    "WorkstreamTransition",
    "WorkstreamStateManager",

    # Phase 5.1: Execution Fabric - Replanning
    "ReplanTriggerType",
    "ReplanScope",
    "ReplanStatus",
    "ReplanTrigger",
    "ReplanAction",
    "ReplanProposal",
    "ReplanConfig",
    "ReplanningEngine",

    # Phase 5.1: Execution Fabric - Checkpoints
    "CheckpointType",
    "CheckpointStatus",
    "CheckpointMetadata",
    "CheckpointData",
    "RestoreResult",
    "CheckpointManager",
]
