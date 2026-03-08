# Phase 5.1: Execution Fabric

**Status**: Validated Beta
**Version**: v0.9.0-beta
**Last Updated**: March 8, 2026

---

## Overview

The Execution Fabric is the runtime layer that coordinates mission graph execution with idempotency guarantees, event-driven communication, and structured collaboration packets (handoffs).

---

## Components

### 1. Hardened Scheduler

**Location**: `torq_console/mission_graph/scheduler.py`

The `MissionGraphScheduler` is the production scheduler that uses the hardened executor by default.

**Key Features:**
- Dependency-aware node dispatch
- Parallel execution of ready nodes
- Idempotent mission completion
- Zero duplicate events (validated)

**API:**
```python
from torq_console.mission_graph import MissionGraphScheduler

scheduler = MissionGraphScheduler(supabase_client)
result = await scheduler.execute_graph(mission, graph)

# Result:
# {
#     "status": "completed",
#     "completed_nodes": 7,
#     "failed_nodes": 0,
#     "progress_percent": 100
# }
```

---

### 2. MissionNodeExecutor

**Location**: `torq_console/mission_graph/executor.py`

The `MissionNodeExecutor` provides idempotent node execution with duplicate prevention.

**Idempotency Guarantees:**
1. Nodes execute exactly once
2. Safe retry (no duplicate side effects)
3. Terminal state detection
4. Atomic state transitions

**Key Methods:**

#### `execute_node()`
Execute a node with full idempotency guards.

```python
result = executor.execute_node(
    mission_id="mission_123",
    node_id="node_456",
    node_title="Analyze Market",
    node_type="task"
)

# Result:
# {
#     "node_id": "node_456",
#     "status": "completed",  # or "skipped", "failed"
#     "skipped": False,
#     "confidence": 0.91,
#     "handoff_id": "handoff_789",
#     "dependents_activated": 2
# }
```

#### `_try_transition_to_running()`
Atomic transition from `pending`/`ready` to `running`.

```python
# Only updates if status in ["pending", "ready"]
success = executor._try_transition_to_running(node_id, current_status)
# Returns True if transition succeeded, False otherwise
```

#### `_try_transition_to_completed()`
Atomic transition from `running` to `completed`.

```python
# Only updates if status == "running"
success = executor._try_transition_to_completed(node_id, current_status)
```

#### `_emit_event_if_not_exists()`
Idempotent event emission.

```python
# Checks for existing event before emitting
executor._emit_event_if_not_exists(
    mission_id="mission_123",
    node_id="node_456",
    event_type="node.completed",
    payload={"status": "completed", "confidence": 0.91}
)
```

#### `_create_handoff_if_not_exists()`
Idempotent handoff creation.

```python
# Creates handoff only if it doesn't exist
handoff_id = executor._create_handoff_if_not_exists(
    from_node_id="node_456",
    to_node_ids=["node_789", "node_101"],
    handoff_summary={...}
)
```

---

### 3. MissionCompleter

**Location**: `torq_console/mission_graph/executor.py`

The `MissionCompleter` provides idempotent mission completion.

**Key Method:**

#### `complete_mission()`
Mark mission as completed (idempotent).

```python
completer = MissionCompleter(supabase_client)
result = completer.complete_mission(
    mission_id="mission_123",
    overall_score=0.91
)

# Result:
# {
#     "mission_id": "mission_123",
#     "updated": True,
#     "status": "completed",
#     "reason": "Mission marked as completed"
# }
```

**Idempotency:**
- Only transitions if status in `["running", "in_progress", "planned"]`
- Emits exactly one `mission.completed` event
- Safe to retry

---

### 4. Context Bus

**Location**: `torq_console/mission_graph/context_bus.py`

Event-driven coordination system with 20+ event types.

**Event Types:**

| Category | Events |
|----------|--------|
| Mission | `mission.created`, `mission.started`, `mission.completed`, `mission.failed` |
| Node | `node.ready`, `node.started`, `node.completed`, `node.failed`, `node.soft_failed`, `node.skipped` |
| Handoff | `handoff.created`, `handoff.delivered`, `handoff.consumed` |
| Decision | `decision.evaluating`, `decision.branch_taken` |
| Workstream | `workstream.created`, `workstream.updated`, `workstream.healthy`, `workstream.degraded` |

**API:**
```python
from torq_console.mission_graph import ContextBus, MissionEvent

bus = ContextBus(supabase_client)

# Emit event
await bus.emit(MissionEvent(
    mission_id="mission_123",
    event_type=MissionEventType.NODE_COMPLETED,
    node_id="node_456",
    payload={"confidence": 0.91}
))

# Subscribe to events (future)
async for event in bus.subscribe(mission_id="mission_123"):
    print(f"Event: {event.event_type}")
```

---

### 5. Handoff Manager

**Location**: `torq_console/mission_graph/handoffs.py`

Structured collaboration packets between nodes.

**Canonical Rich Format:**

```python
{
    "handoff_summary": {
        "objective_completed": str,
        "output_summary": str,
        "key_findings": List[str],
        "recommendations": List[str]
    },
    "confidence": float,  # 0.0 - 1.0
    "confidence_basis": str,
    "unresolved_questions": List[str],
    "assumptions_made": List[str],
    "limitations": List[str],
    "risks": List[str],
    "artifacts": Dict[str, Any],
    "status": "delivered"
}
```

**Example:**
```python
from torq_console.mission_graph import HandoffManager

manager = HandoffManager(supabase_client)
handoff = manager.create_handoff(
    from_node_id="node_456",
    to_node_ids=["node_789"],
    handoff_summary={
        "objective_completed": "Competitor analysis completed",
        "output_summary": "Identified 5 key competitors with market share data",
        "key_findings": [
            "Competitor A has 35% market share",
            "Competitor B has 25% market share"
        ],
        "recommendations": [
            "Focus on differentiation in quality",
            "Consider partnership with smaller competitors"
        ]
    },
    confidence=0.91,
    confidence_basis="Complete competitor coverage, verified data sources"
)
```

---

### 6. Workstream State Manager

**Location**: `torq_console/mission_graph/workstream_state.py`

Health tracking across parallel work streams.

**Workstream Phases:**
- `created` — Workstream initialized
- `active` — Work in progress
- `waiting` — Blocked on dependency
- `completed` — All work done
- `failed` — Workstream failed

**Health Levels:**
- `healthy` — All nodes progressing
- `degraded` — Some nodes slow/retried
- `critical` — Nodes failing, intervention needed

**API:**
```python
from torq_console.mission_graph import WorkstreamStateManager

manager = WorkstreamStateManager(supabase_client)

# Create workstream
workstream = manager.create_workstream(
    mission_id="mission_123",
    workstream_id="ws_analysis",
    phase="active",
    health="healthy"
)

# Update health
manager.update_health(
    workstream_id="ws_analysis",
    health="degraded",
    reason="Some nodes experiencing delays"
)
```

---

## Execution Flow

### Hardened Runtime Path

```
MissionGraphScheduler
    │
    ├── 1. Identify ready nodes (dependencies satisfied)
    │
    ├── 2. For each ready node:
    │       │
    │       └── MissionNodeExecutor.execute_node()
    │           │
    │           ├── Check terminal state (skip if already completed)
    │           │
    │           ├── _try_transition_to_running() [atomic]
    │           │   └── Only if status in [pending, ready]
    │           │
    │           ├── _emit_event_if_not_exists(node.started)
    │           │
    │           ├── Execute work (call agent/specialist)
    │           │
    │           ├── _try_transition_to_completed() [atomic]
    │           │   └── Only if status == running
    │           │
    │           ├── _emit_event_if_not_exists(node.completed)
    │           │
    │           └── _create_handoff_if_not_exists()
    │
    ├── 3. Activate dependent nodes
    │
    ├── 4. Repeat until all nodes complete
    │
    └── 5. MissionCompleter.complete_mission()
        └── Atomic transition to completed
```

### Event Flow

```
Node Ready → Node Started → Node Completed → Handoff Created → Dependents Ready
     ↓              ↓                ↓                ↓                   ↓
  node.ready    node.started    node.completed   handoff.created    node.ready (next)
```

---

## Validation

### Validation Results (v0.9.0-beta)

| Mission | Nodes | Duplicate Events | Rich Handoffs | Status |
|---------|-------|------------------|---------------|--------|
| Mission 1 (Baseline) | 6 | 33 | 9/14 (64%) | Identified issues |
| Mission 2 (Hardened) | 5 | 0 | 5/5 (100%) | Passed |
| Mission 3 (Scheduler) | 7 | 0 | 7/7 (100%) | Passed |

**Key Improvements:**
- Duplicate events: 33 → 0
- Rich handoff adoption: 64% → 100%
- Mission completion events: 2 → 1 (exactly one)

### What Was Proven

1. **Idempotent Node Execution**
   - Safe retry with no side effects
   - Terminal state detection working
   - Atomic transitions preventing race conditions

2. **Duplicate Event Prevention**
   - No duplicate `node.started` events
   - No duplicate `node.completed` events
   - No duplicate `mission.completed` events

3. **Handoff Standardization**
   - All handoffs use canonical rich format
   - Minimal format eliminated
   - Consistent structure across nodes

4. **Cross-Mission Generalization**
   - Fixes work across linear missions
   - Fixes work with decision gates
   - Fixes work with different reasoning strategies

---

## Maturity: Validated Beta

**Implemented:**
- All execution fabric components
- Hardened scheduler as default path
- Event-driven coordination
- Rich handoff standardization

**Validated:**
- Idempotent execution (0 duplicates)
- Handoff consistency (100% rich)
- Cross-mission generalization

**Next:**
- Broader production testing
- Operator control surface refinement
- Additional mission type validation

---

## API Reference

### Imports

```python
from torq_console.mission_graph import (
    # Scheduler
    MissionGraphScheduler,

    # Executor
    MissionNodeExecutor,
    MissionCompleter,

    # Context Bus
    ContextBus,
    MissionEvent,
    MissionEventType,

    # Handoffs
    HandoffManager,
    Handoff,

    # Workstream State
    WorkstreamStateManager,
    WorkstreamState,
    WorkstreamPhase,
    WorkstreamHealth,

    # Exceptions
    NodeExecutionError,
    IdempotencyViolationError,
)
```

### Quick Start

```python
from torq_console.mission_graph import MissionGraphScheduler
from torq_console.dependencies import get_supabase_client

# Initialize
supabase = get_supabase_client()
scheduler = MissionGraphScheduler(supabase)

# Execute mission graph
result = await scheduler.execute_graph(mission, graph)

print(f"Status: {result['status']}")
print(f"Completed: {result['completed_nodes']}/{result['total_nodes']}")
print(f"Progress: {result['progress_percent']}%")
```

---

## See Also

- [Phase 5 Mission Graph Planning](PHASE_5_MISSION_GRAPH_PLANNING.md) — Graph structure
- [Phase 4H Strategic Memory](PHASE_4H_STRATEGIC_MEMORY.md) — Memory system
- [Architecture Index](ARCHITECTURE_INDEX.md) — System overview
- [Phase 5.1 Validation Report](PHASE_5_1_VALIDATION_REPORT.md) — Validation evidence
