# Phase 5: Mission Graph Planning - Implementation Complete

## Overview

Phase 5 transforms TORQ from "a system that runs agents" into "a system that structures complex missions the way a strong consulting team would."

**The Leap:**

**Before:** Agent runs produce flat task lists
```
1. Research market
2. Analyze risks
3. Summarize findings
4. Recommend actions
```

**After:** Mission graphs with structured dependencies
```
Mission Objective
├── Workstream A (Market Analyst)
│   ├── Task: Estimate market size
│   ├── Task: Analyze competitors
│   └── Decision: Confidence gate
├── Workstream B (Risk Analyst)
│   ├── Task: Regulatory review
│   └── Task: Risk assessment
└── Decision: Go/no-go gate
    └── Deliverable: Executive brief
```

---

## What Was Built

### 1. Mission Graph Data Model

**File:** `torq_console/mission_graph/models.py` (670 lines)

**Five Node Types:**
- **Objective** - Top-level mission goals
- **Task** - Concrete reasoning/execution work
- **Decision** - Branch points with gate logic
- **Evidence** - Required facts/data/artifacts
- **Deliverable** - Expected outputs

**Five Edge Types:**
- **depends_on** - Target waits for source completion
- **informs** - Source improves target but not required
- **blocks** - Source prevents target until resolved
- **branches_to** - Decision activates downstream branch
- **produces** - Task generates evidence/deliverable

**Node States:** pending → ready → running → blocked → completed/failed/skipped

### 2. Mission Graph Builder

**File:** `torq_console/mission_graph/builder.py` (450 lines)

**Features:**
- Templates for common mission types (analysis, planning, evaluation)
- Strategic memory pattern injection during graph creation
- Context-aware node customization
- Graph structure validation (cycle detection, orphan detection)

**Templates:**
- `analysis_template()` - Research, investigation, assessment
- `planning_template()` - Strategy, roadmap, execution plan
- `evaluation_template()` - Risk assessment, audit, review

### 3. Mission Graph Scheduler

**File:** `torq_console/mission_graph/scheduler.py` (550 lines)

**Features:**
- Finds ready nodes (dependencies satisfied)
- Dispatches nodes to appropriate agents
- Evaluates decision gates
- Tracks execution state
- Handles parallel execution where valid

**Decision Gate Logic:**
```python
# Example gate
{
  "gate_type": "confidence_threshold",
  "metric": "market_confidence",
  "operator": ">=",
  "value": 0.75,
  "on_pass": "continue",
  "on_fail": "spawn_validation_subgraph"
}
```

**Gate Types:**
- confidence_threshold
- risk_threshold
- contradiction_threshold
- evidence_completeness
- human_approval
- budget_threshold
- time_threshold

### 4. Database Schema

**File:** `migrations/018_mission_graphs.sql` (330 lines)

**Tables:**
- `missions` - Top-level mission records
- `mission_graphs` - Graph metadata and versioning
- `mission_nodes` - Individual graph nodes
- `mission_edges` - Node relationships
- `mission_node_outputs` - Execution artifacts
- `decision_outcomes` - Gate evaluation results
- `workstreams` - Logical groupings of nodes

**Views:**
- `active_missions_with_graphs` - Current missions with graphs
- `ready_mission_nodes` - Nodes ready for execution
- `mission_progress_summary` - Progress tracking by mission

### 5. REST API

**File:** `torq_console/mission_graph/api.py` (300 lines)

**Endpoints:**

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/missions/` | Create new mission with graph |
| GET | `/api/missions/` | List missions with filters |
| GET | `/api/missions/{id}` | Get mission with graph/nodes/edges |
| POST | `/api/missions/{id}/start` | Execute mission graph |
| POST | `/api/missions/{id}/graph` | Create new graph version |
| GET | `/api/missions/{id}/graph/validate` | Validate graph structure |
| GET | `/api/missions/{id}/nodes/ready` | Get ready nodes |
| POST | `/api/missions/{id}/nodes/{node_id}/execute` | Execute specific node |
| GET | `/api/missions/{id}/progress` | Get execution progress |
| GET | `/api/missions/{id}/workstreams` | Get workstreams |

---

## Agent Team Structure

The scheduler assigns nodes to appropriate agent types:

| Agent Type | Role |
|------------|------|
| **Strategic Planner** | Builds/monitors graph, handles decisions |
| **Domain Leads** | Own workstreams (finance, operations, market, compliance) |
| **Specialist Agents** | Execute specific task nodes |
| **Synthesizer** | Combines outputs into deliverables |
| **Risk/QA Agent** | Reviews contradictions, risks, quality |
| **Executive** | Final review and approval |

---

## Strategic Memory Integration

Strategic memory shapes mission execution in three ways:

1. **During graph generation** - Memory suggests graph patterns
   - "financial analysis missions should include regulatory review"
   - "complex planning needs contradiction check node"

2. **During node execution** - Per-node memory injection
   - Compliance task gets compliance warnings
   - Planner node gets planning playbooks
   - Synthesis node gets evidence-weighting heuristics

3. **During decision gates** - Memories influence branch logic
   - "if similar missions historically failed with evidence < 0.7, escalate"

---

## Reasoning Strategies

Instead of vague prompt enrichment, TORQ attaches explicit reasoning strategies:

| Strategy | Use Case |
|----------|----------|
| `decomposition_first` | Break down problem before solving |
| `risk_first` | Identify risks early in process |
| `evidence_weighted` | Weight decisions by evidence strength |
| `checklist_driven` | Follow explicit checklist for quality |
| `contradiction_first` | Surface conflicts early for resolution |
| `hypothesis_driven` | Test hypotheses sequentially |

---

## Example Mission Graph

```python
MissionGraph(
    nodes=[
        MissionNode(id="n1", type=OBJECTIVE, "Assess market opportunity"),
        MissionNode(id="n2", type=TASK, "Estimate market size",
                  agent=SPECIALIST, strategy=EVIDENCE_WEIGHTED),
        MissionNode(id="n3", type=TASK, "Evaluate regulatory exposure",
                  agent=DOMAIN_LEAD, strategy=RISK_FIRST),
        MissionNode(id="n4", type=DECISION, "Go/no-go gate",
                  condition={"market_confidence_min": 0.75, "regulatory_risk_max": 0.40}),
        MissionNode(id="n5", type=DELIVERABLE, "Executive brief")
    ],
    edges=[
        MissionEdge(source="n2", target="n4", type=DEPENDS_ON),
        MissionEdge(source="n3", target="n4", type=DEPENDS_ON),
        MissionEdge(source="n4", target="n5", type=DEPENDS_ON)
    ]
)
```

---

## Why This Matters

### Problems Solved

1. **Duplicated work** - Explicit dependencies prevent parallel same work
2. **Weak dependency handling** - Clear depends_on edges
3. **Poor escalation logic** - Decision gates with conditions
4. **Shallow synthesis** - Deliverable nodes aggregate upstream outputs

### What TORQ Can Now Do

- **Decompose objectives** into structured work
- **Assign specialists** to appropriate workstreams
- **Gather evidence** with clear dependencies
- **Challenge assumptions** via decision gates
- **Synthesize outputs** into deliverables
- **Revise plans** when new evidence arrives

---

## Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `mission_graph/models.py` | 670 | Data models for missions, graphs, nodes, edges |
| `mission_graph/builder.py` | 450 | Graph creation from objectives + memory |
| `mission_graph/scheduler.py` | 550 | Dependency-aware execution engine |
| `mission_graph/api.py` | 300 | REST API for mission operations |
| `mission_graph/__init__.py` | 100 | Package exports |
| `migrations/018_mission_graphs.sql` | 330 | Database schema |

**Total: ~2,400 lines of production code**

---

## What This Enables

With Mission Graph Planning, TORQ now has:

**Adaptive execution** (Phase 4F)
**+**
**Institutional memory** (Phase 4H)
**+**
**Governed improvement** (4H.1)
**+**
**Operational oversight** (4H.1)
**+**
**Structured mission planning** (Phase 5)

Equals: **AI consulting operating system**

---

## Next Steps

1. **Complete 4H.1 experiments** - Prove memory injection works
2. **Build Mission Control UI** - Graph visualization, workstream status
3. **Implement agent team coordination** - Nodes → Agents → Results
4. **Add decision gate automation** - Branch activation, escalation

---

**Phase 5 Foundation Complete.** TORQ can now structure missions like a consulting firm.
