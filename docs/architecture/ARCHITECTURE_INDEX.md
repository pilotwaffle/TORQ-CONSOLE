# TORQ Console Architecture Index

**Version**: v0.9.0-beta
**Last Updated**: March 8, 2026

This document is the canonical map of the TORQ Console platform.

---

## Platform Overview

TORQ Console is an **adaptive multi-agent reasoning platform** that combines:
- Mission graph planning for dependency-aware execution
- Execution fabric with idempotent coordination
- Institutional memory for cross-session learning
- Adaptive cognition for continuous improvement

---

## Four-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    EXECUTION LAYER                          │
│  Mission Graph Planning (Phase 5) │ Execution Fabric (5.1)  │
│  - Dependency graphs               - Context Bus              │
│  - Decision gates                  - Handoff Manager           │
│  - Template missions               - Workstream State         │
│                                    - Hardened Scheduler ★      │
├─────────────────────────────────────────────────────────────┤
│                  INTELLIGENCE LAYER                         │
│     Adaptive Cognition (4F)  │  Strategic Memory (4H)         │
│     - Learning loop            - Memory injection           │
│     - Signal collection        - Cross-session learning     │
│     - A/B testing              - Quality scoring            │
├─────────────────────────────────────────────────────────────┤
│                   REASONING LAYER                            │
│                   Multi-Agent Orchestration (3)              │
│                   - Agent selection & routing               │
│                   - Specialist agents                       │
│                   - Collaboration protocols                   │
├─────────────────────────────────────────────────────────────┤
│                    FOUNDATION LAYER                          │
│              Core Infrastructure (1-2)                        │
│              - Supabase persistence                        │
│              - Claude API integration                       │
│              - Configuration management                     │
└─────────────────────────────────────────────────────────────┘

★ = Hardened executor — default runtime path, validated for idempotency
```

---

## Component Directory

### Execution Layer

#### Phase 5: Mission Graph Planning
**Status**: Validated Beta
**Location**: `torq_console/mission_graph/`

| Component | File | Purpose |
|-----------|------|---------|
| Mission Graph | `models.py` | Core graph and node definitions |
| Scheduler | `scheduler.py` | Hardened execution scheduler |
| Node Executor | `executor.py` | Idempotent node execution |
| Context Bus | `context_bus.py` | Event-driven coordination |
| Handoff Manager | `handoffs.py` | Structured collaboration packets |
| Workstream State | `workstream_state.py` | Parallel work tracking |
| Replanning Engine | `replanning.py` | Dynamic graph mutation |
| Checkpoint Manager | `checkpoints.py` | Rollback and recovery |

#### Node Types
| Type | Purpose | Maturity |
|------|---------|----------|
| Objective | Top-level goal | Validated Beta |
| Task | Concrete work item | Validated Beta |
| Decision | Branch point with gate | Validated Beta |
| Evidence | Required data/artifacts | Validated Beta |
| Deliverable | Expected output | Validated Beta |

#### Edge Types
| Type | Purpose |
|------|---------|
| `depends_on` | Dependency (must complete before) |
| `informs` | Information flow (non-blocking) |
| `blocks` | Blocks execution until condition |
| `branches_to` | Conditional branch |
| `produces` | Output artifact |

---

### Intelligence Layer

#### Phase 4F: Adaptive Cognition Loop
**Status**: Beta
**Location**: `torq_console/adaptive_cognition/`

| Component | Purpose |
|-----------|---------|
| Signal Engine | Collect outcome signals |
| Evaluation Engine | Assess quality |
| Adaptation Policy | Manage improvements |
| Experiment & Versioning | A/B testing |

#### Phase 4H: Strategic Memory
**Status**: Beta
**Location**: `torq_console/strategic_memory/`

| Component | Purpose |
|-----------|---------|
| Memory Store | Persistent memory |
| Memory Router | Retrieval by context |
| Memory Synthesizer | Combine related memories |

---

### Reasoning Layer

#### Phase 3: Multi-Agent Orchestration
**Status**: Production
**Location**: `torq_console/agents/`

| Component | Purpose |
|-----------|---------|
| Agent Router | Select agent for task |
| Specialist Agents | Domain experts |
| Collaboration Protocols | Agent communication |

---

### Foundation Layer

#### Phases 1-2: Core Infrastructure
**Status**: Production
**Location**: `torq_console/core/`, `torq_console/config/`

| Component | Purpose |
|-----------|---------|
| Database | Supabase PostgreSQL |
| Configuration | Environment-based config |
| API Integration | Claude, Ollama |

---

## Hardened Runtime Path

The default execution path uses idempotent coordination:

```
MissionGraphScheduler
    │
    ├── MissionNodeExecutor
    │   │
    │   ├── _try_transition_to_running()
    │   │   └── Atomic: only if status in [pending, ready]
    │   │
    │   ├── _execute_node_work()
    │   │   └── Call agent or specialist
    │   │
    │   ├── _try_transition_to_completed()
    │   │   └── Atomic: only if status == running
    │   │
    │   ├── _emit_event_if_not_exists()
    │   │   └── Idempotent: check before emit
    │   │
    │   └── _create_handoff_if_not_exists()
    │       └── Idempotent: check before create
    │
    └── MissionCompleter
        └── complete_mission()
            └── Atomic: only if status in [running, in_progress, planned]
```

**Guarantees**:
1. Nodes execute exactly once
2. Events emit exactly once per transition
3. Handoffs create exactly once per completion
4. Retry is safe (no duplicate side effects)
5. Race conditions prevented

---

## Event Flow

```
Node Ready → Node Started → Node Completed → Handoff Created → Dependents Ready
     ↓              ↓                ↓                ↓                   ↓
  node.ready    node.started    node.completed   handoff.created    node.ready (next)
```

All events are persisted to `mission_events` table for full observability.

---

## Handoff Structure

Canonical rich handoff format:

```python
{
    "handoff_summary": {
        "objective_completed": str,
        "output_summary": str,
        "key_findings": List[str],
        "recommendations": List[str]
    },
    "confidence": float,
    "confidence_basis": str,
    "unresolved_questions": List[str],
    "assumptions_made": List[str],
    "limitations": List[str],
    "risks": List[str],
    "artifacts": Dict,
    "status": "delivered"
}
```

---

## Data Model

### Core Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `missions` | Mission metadata | id, title, status, reasoning_strategy |
| `mission_graphs` | Graph versions | id, mission_id, version |
| `mission_nodes` | Graph nodes | id, node_type, status, depends_on |
| `mission_edges` | Graph edges | id, from_node_id, to_node_id, edge_type |
| `mission_events` | Event log | id, mission_id, event_type, node_id |
| `mission_handoffs` | Handoff packets | id, from_node_id, handoff_summary |
| `workstream_states` | Parallel work tracking | workstream_id, phase, health |
| `strategic_memories` | Long-term memory | id, content, quality_score |
| `adaptation_signals` | Learning signals | id, source, signal_type |

---

## API Reference

### Mission Graph Scheduler

```python
from torq_console.mission_graph import MissionGraphScheduler

scheduler = MissionGraphScheduler(supabase_client)

# Execute a mission graph
result = await scheduler.execute_graph(mission, graph)

# Result contains:
# - status: final mission status
# - completed_nodes: count of completed nodes
# - failed_nodes: count of failed nodes
# - progress_percent: completion percentage
```

### Hardened Node Executor

```python
from torq_console.mission_graph import MissionNodeExecutor

executor = MissionNodeExecutor(supabase_client)

# Execute a node (idempotent)
result = executor.execute_node(
    mission_id=mission_id,
    node_id=node_id,
    node_title="Analyze Market",
    node_type="task"
)

# Result contains:
# - status: completed, skipped, or failed
# - skipped: True if already executed
# - confidence: quality score
# - handoff_id: created handoff
# - dependents_activated: count of downstream nodes ready
```

### Mission Completer

```python
from torq_console.mission_graph import MissionCompleter

completer = MissionCompleter(supabase_client)

# Complete mission (idempotent)
result = completer.complete_mission(
    mission_id=mission_id,
    overall_score=0.91
)

# Result contains:
# - updated: True if mission was marked completed
# - status: final mission status
# - reason: why updated or not updated
```

---

## Validation Summary

**v0.9.0-beta** — March 8, 2026

| Check | Result | Details |
|-------|--------|---------|
| Duplicate event prevention | ✅ Pass | 0 duplicates across 3 missions |
| Idempotent node execution | ✅ Pass | Safe retry verified |
| Idempotent mission completion | ✅ Pass | Single event verified |
| Rich handoff standardization | ✅ Pass | 100% rich format |
| Cross-mission generalization | ✅ Pass | 3 mission shapes validated |

See [PHASE_5_1_VALIDATION_REPORT.md](PHASE_5_1_VALIDATION_REPORT.md) for full details.

---

## Maturity Labels

| Label | Meaning | Components |
|-------|---------|------------|
| **Production** | Field-tested, reliable | Foundation, Reasoning, Agent Router |
| **Validated Beta** | Implemented and validated | Mission Graph, Execution Fabric, Handoffs |
| **Beta** | Implemented, needs broader testing | Context Bus, Workstreams, Memory, Cognition |
| **Experimental** | Framework exists, needs implementation | Replanning, Checkpoints |

---

## Migration Notes

When upgrading from older versions:

1. **v0.8 → v0.9.0**: Hardened scheduler is now default
   - Old execution path deprecated
   - Duplicate events eliminated
   - Handoff format standardized
   - Mission completion idempotent

2. Database migrations required:
   ```bash
   python -m torq_console.cli migrate
   ```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Code style guidelines
- Pull request process
- Testing requirements
- Documentation standards

---

## License

MIT License — see [LICENSE](../LICENSE)
