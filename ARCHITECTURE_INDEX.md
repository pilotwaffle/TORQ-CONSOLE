# TORQ Console - Architecture Index

**Purpose:** Single source of truth for TORQ architecture — what exists, what is complete, what is in validation, and what is planned next.

**Status:** Phase 5.1 (Execution Fabric) implementation complete. Validation pending.

---

## Quick Reference

| Phase | Component | Status | Maturity |
|-------|-----------|--------|----------|
| Phase 4E | Reasoning Synthesis Engine | ✅ Complete | Production-ready |
| Phase 4F | Adaptive Cognition Loop | ✅ Complete | Guarded/Beta |
| Phase 4G | Pattern Aggregation | ⚠️ Partial | Experimental |
| Phase 4H | Strategic Memory | ✅ Complete | Guarded/Beta |
| Phase 4H.1 | Memory Validation & Control | ✅ Complete | Guarded/Beta |
| Phase 5 | Mission Graph Planning | ✅ Complete | Guarded/Beta |
| Phase 5.1 | Execution Fabric | ✅ Complete | Guarded/Beta |

---

## Architecture Overview

TORQ is an **AI Consulting Operating System** that structures complex missions the way a strong consulting team would.

### Core Value Proposition

**Before:** AI agents run flat task lists in isolation.

**After:** TORQ structures missions with:
- **Dependency-aware execution** — Tasks run in correct order, parallel where valid
- **Multi-agent coordination** — Specialist teams collaborate via structured handoffs
- **Institutional memory** — Strategic knowledge shapes future reasoning
- **Adaptive improvement** — System learns what works and self-corrects

### System Layers

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Mission & Execution Layer                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   Mission    │  │  Execution   │  │   Agent      │             │
│  │   Graph      │  │   Fabric     │  │   Teams      │             │
│  │  (Phase 5)   │  │ (Phase 5.1)  │  │              │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
├─────────────────────────────────────────────────────────────────────┤
│                        Intelligence & Memory Layer                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  Strategic   │  │  Adaptive    │  │  Pattern     │             │
│  │  Memory      │  │  Loop        │  │  Aggregation │             │
│  │  (Phase 4H)  │  │  (Phase 4F)  │  │  (Phase 4G)  │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
├─────────────────────────────────────────────────────────────────────┤
│                        Analysis & Synthesis Layer                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  Evaluation  │  │  Synthesis    │  │  Workspace   │             │
│  │  Engine      │  │  Engine      │  │  Memory      │             │
│  │              │  │ (Phase 4E)   │  │              │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
├─────────────────────────────────────────────────────────────────────┤
│                        Core Infrastructure                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   Marvin    │  │   MCP        │  │  Supabase    │             │
│  │  3.0        │  │  Servers     │  │  Database    │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Catalog

### Phase 4E: Reasoning Synthesis Engine

**Purpose:** Combine multiple agent outputs into coherent summaries.

**Files:** `torq_console/synthesis/`

**Key Classes:**
- `SynthesisEngine` - Orchestrates multi-output synthesis
- `SynthesisStrategy` - Different synthesis approaches (summary, debate, integration)
- `SynthesisRequest` - Input schema
- `SynthesisResult` - Output schema

**Database:** `migrations/008_synthesis_engine.sql`

**Maturity:** **Production-ready**

**What Works:**
- Multi-output synthesis from different agents
- Configurable synthesis strategies
- Conflict detection and resolution
- Workspace integration

**Known Limitations:**
- Limited to text-based outputs
- No multi-modal synthesis yet

---

### Phase 4F: Adaptive Cognition Loop

**Purpose:** Learn what works and self-improve over time.

**Files:** `torq_console/learning/`, `torq_console/adaptation/`, `torq_console/experiments/`

**Key Classes:**
- `LearningSignalEngine` - Collect feedback signals
- `AdaptationPolicyEngine` - Generate adaptation proposals
- `BehaviorExperimentVersioning` - A/B testing framework
- `AdaptiveTelemetryCollector` - Track system behavior

**Database:** `migrations/009-013_adaptive_loop.sql`

**Maturity:** **Guarded/Beta**

**What Works:**
- Signal collection from evaluations
- Experiment assignment (deterministic)
- Adaptation proposal generation
- Readiness checker for exiting observation mode

**What's Guarded:**
- Auto-promotion of adaptations (requires operator approval)
- Experiment reliability thresholds
- Signal stability verification

**Validation Status:** Observation mode validated. Auto-promotion pending.

---

### Phase 4G: Pattern Aggregation

**Purpose:** Discover recurring patterns across workspaces for strategic memory.

**Files:** `torq_console/knowledge_plane/`

**Maturity:** **Experimental**

**Status:** Partially implemented. Pattern detection exists but consolidation into strategic memory is manual.

**What Works:**
- Workspace pattern extraction
- Simple clustering

**What's Missing:**
- Automatic pattern consolidation
- Pattern lifecycle management
- Pattern validation

---

### Phase 4H: Strategic Memory

**Purpose:** Persistent strategic knowledge that shapes future reasoning.

**Files:** `torq_console/strategic_memory/`

**Key Classes:**
- `StrategicMemoryStore` - Core memory operations
- `MemoryConsolidationEngine` - Pattern → Memory conversion
- `MemoryRetrievalEngine` - Search and ranking
- `MemoryGovernance` - Lifecycle and challenges

**Database:** `migrations/014_strategic_memory.sql`

**Maturity:** **Guarded/Beta**

**What Works:**
- Memory types: heuristics, playbooks, warnings, assumptions, lessons
- Confidence and durability scoring
- Scope-based retrieval (tenant > workflow > domain > agent > global)
- Memory governance (approve, reject, supersede)

**What's Guarded:**
- Memory injection is experimental (Phase 4H.1 validates this)
- Automatic consolidation thresholds
- Confidence decay over time

---

### Phase 4H.1: Strategic Memory Validation & Control

**Purpose:** Prove memory works before expanding its influence.

**Files:** `torq_console/strategic_memory/experiments.py`, `effectiveness.py`, `scoping.py`

**Key Classes:**
- `MemoryInjectionExperiment` - A/B testing for memory impact
- `MemoryEffectivenessTracker` - Score memory performance
- `MemoryScopingManager` - Enforce scope limits

**Database:** `migrations/015-017_memory_validation.sql`

**Maturity:** **Guarded/Beta**

**What Works:**
- Deterministic experiment assignment
- Effectiveness scoring (delta, experiments, workflow, contradictions)
- Scope precedence rules
- Per-scope memory limits

**Validation Status:** Infrastructure complete. 7-10 day experiment pending.

---

### Phase 5: Mission Graph Planning

**Purpose:** Structure complex missions with dependency graphs.

**Files:** `torq_console/mission_graph/models.py`, `builder.py`, `scheduler.py`, `api.py`

**Key Classes:**
- `MissionGraph` - Graph with nodes and edges
- `MissionNode` - 5 types: objective, task, decision, evidence, deliverable
- `MissionEdge` - 5 types: depends_on, informs, blocks, branches_to, produces
- `MissionGraphBuilder` - Create graphs from objectives
- `MissionGraphScheduler` - Execute dependency-aware missions

**Database:** `migrations/018_mission_graphs.sql`

**Maturity:** **Guarded/Beta**

**What Works:**
- Graph creation from objectives
- Templates for analysis, planning, evaluation missions
- Dependency-aware scheduling
- Decision gate evaluation
- Strategic memory integration during graph building

**What's Guarded:**
- End-to-end execution pending validation
- Agent team integration not yet implemented

---

### Phase 5.1: Execution Fabric

**Purpose:** Coordinated, stateful team execution with shared context.

**Files:** `torq_console/mission_graph/context_bus.py`, `handoffs.py`, `workstream_state.py`, `replanning.py`, `checkpoints.py`

**Key Classes:**
- `MissionContextBus` - Event-driven coordination
- `HandoffManager` - Structured collaboration packets
- `WorkstreamStateManager` - Health and progress tracking
- `ReplanningEngine` - Dynamic graph mutation
- `CheckpointManager` - Rollback and recovery

**Database:** `migrations/019_execution_fabric.sql`

**Maturity:** **Guarded/Beta**

**What Works:**
- Event emission and subscription
- Handoff creation and routing
- Workstream state tracking (8 phases, 5 health levels)
- Replanning triggers and proposals
- Checkpoint creation and restoration

**What's Guarded:**
- End-to-end execution pending validation
- Replanning execution not production-tested
- Checkpoint recovery not stress-tested

**Validation Status:** Implementation complete. End-to-end validation pending (see `PHASE_5_1_VALIDATION_CHECKLIST.md`).

---

## Maturity Classifications

### Production-ready

Safe to use in production with normal operational monitoring.

- ✅ **Workspace Memory** - Core storage and retrieval
- ✅ **Synthesis Engine** - Multi-output combination
- ✅ **Evaluation Engine** - Quality assessment

### Guarded/Beta

Working but needs operational caution or additional validation.

- ⚠️ **Adaptive Cognition Loop** - Observation mode validated, auto-promotion guarded
- ⚠️ **Strategic Memory** - Infrastructure complete, injection experiments pending
- ⚠️ **Memory Validation & Control** - Ready for experiments, awaiting results
- ⚠️ **Mission Graph Planning** - Graph creation works, execution pending validation
- ⚠️ **Execution Fabric** - All subsystems implemented, end-to-end validation pending

### Experimental

Proof of concept. Not for production use.

- 🔬 **Pattern Aggregation** - Partial implementation, manual consolidation

---

## Database Schema

| Migration | Component | Tables | Status |
|-----------|-----------|--------|--------|
| 006 | Workspace Memory | workspace_entries, working_memory_entries | ✅ Production |
| 007 | Shared Workspace | workspaces, workspace_entries, invites | ✅ Production |
| 008 | Synthesis Engine | syntheses, synthesis_requests | ✅ Production |
| 009 | Learning Signals | learning_signals, signal_sources | ⚠️ Beta |
| 010 | Adaptation Policies | adaptation_policies, policy_versions | ⚠️ Beta |
| 011 | Behavior Experiments | experiments, experiment_assignments | ⚠️ Beta |
| 012 | Adaptive Telemetry | adaptive_system_metrics, telemetry_reports | ⚠️ Beta |
| 013 | Observation Mode | system_observability_status | ⚠️ Beta |
| 014 | Strategic Memory | strategic_memories, memory_challenges | ⚠️ Beta |
| 015 | Memory Experiments | memory_injection_experiments, results | ⚠️ Beta |
| 016 | Memory Effectiveness | memory_effectiveness | ⚠️ Beta |
| 017 | Memory Scoping | memory_scope_rules | ⚠️ Beta |
| 018 | Mission Graphs | missions, mission_graphs, nodes, edges | ⚠️ Beta |
| 019 | Execution Fabric | mission_handoffs, workstream_states, events, checkpoints | ⚠️ Beta |

---

## API Endpoints

### Mission Graph API

```
POST   /api/missions/                    # Create mission with graph
GET    /api/missions/                    # List missions
GET    /api/missions/{id}                # Get mission with graph
POST   /api/missions/{id}/start          # Execute mission
POST   /api/missions/{id}/graph          # Create new graph version
GET    /api/missions/{id}/graph/validate # Validate graph structure
GET    /api/missions/{id}/nodes/ready    # Get ready nodes
POST   /api/missions/{id}/nodes/{nid}/execute  # Execute node
GET    /api/missions/{id}/progress       # Get progress
GET    /api/missions/{id}/workstreams    # Get workstreams
```

### Strategic Memory API

```
POST   /api/strategic-memory/            # Create memory
GET    /api/strategic-memory/            # Search memories
GET    /api/strategic-memory/{id}        # Get memory
POST   /api/strategic-memory/{id}/approve    # Approve candidate
POST   /api/strategic-memory/{id}/challenge   # Challenge memory
GET    /api/strategic-memory/injection/{workspace_id}  # Get memories for injection
```

### Synthesis API

```
POST   /api/synthesis                    # Synthesize outputs
GET    /api/synthesis/{id}               # Get synthesis result
```

### Evaluation API

```
POST   /api/evaluations                  # Evaluate output
GET    /api/evaluations/{id}             # Get evaluation result
```

---

## Roadmap

### Near-term (Next 1-2 weeks)

1. **Phase 5.1 Validation** - Execute end-to-end validation checklist
2. **GitHub/README Refresh** - Update public documentation
3. **Mission Control UI** - Graph visualization and monitoring

### Medium-term (Next 1-2 months)

1. **Agent Team Integration** - Connect nodes to actual agents
2. **Human Approval Flows** - Decision gates with human input
3. **Mission Templates** - Pre-built graphs for common missions

### Long-term (3-6 months)

1. **Phase 5.2** - Multi-mission orchestration
2. **Phase 6** - Learning from mission outcomes
3. **Phase 7** - Autonomous mission proposal

---

## Documentation

| Document | Purpose | Status |
|----------|---------|--------|
| `README.md` | Public overview | Needs update |
| `CLAUDE.md` | Project-specific context for Claude | Current |
| `PHASE_5_MISSION_GRAPH_PLANNING.md` | Phase 5 overview | ✅ Complete |
| `PHASE_5_1_EXECUTION_FABRIC.md` | Phase 5.1 overview | ✅ Complete |
| `PHASE_5_1_VALIDATION_CHECKLIST.md` | Validation runbook | ✅ Complete |
| `ARCHITECTURE_INDEX.md` | This document | ✅ Complete |

---

## Development Guidelines

### Adding New Features

1. **Check if existing phase covers it** - Don't duplicate architecture
2. **Validate before building** - Prove value of new layers
3. **Document maturity** - Mark as experimental/beta/production
4. **Update this index** - Keep architecture documentation current

### Validation Before GitHub Update

All of these must be true before updating public docs:
- [ ] Phase 5.1 validation checklist complete
- [ ] Subsystem maturity classifications assigned
- [ ] At least 3 end-to-end missions successful
- [ ] No critical bugs in production components

---

**Last Updated:** 2025-03-07

**Current Version:** Phase 5.1 (Execution Fabric) - Implementation Complete, Validation Pending
