# Phase 5: Mission Graph Planning

**Status**: Validated Beta
**Version**: v0.9.0-beta
**Last Updated**: March 8, 2026

---

## Overview

Mission Graph Planning is a dependency-aware execution system that structures complex missions as directed acyclic graphs (DAGs). Each mission is composed of typed nodes connected by edges that define dependencies, information flow, and output relationships.

---

## Node Types

### 1. Objective (Root Node)
The top-level goal or primary outcome of the mission.

**Properties:**
- Must be exactly one per mission
- No incoming `depends_on` edges
- Represents the final deliverable

**Example:**
```python
Objective(
    id="obj_1",
    title="Market Entry Assessment",
    description="Determine viability of entering European market"
)
```

### 2. Task
Concrete work items that produce tangible outputs.

**Properties:**
- Can have multiple dependencies
- Executed by agents or specialists
- Produce handoffs for downstream nodes

**Example:**
```python
Task(
    id="task_1",
    title="Analyze Competitive Landscape",
    description="Identify and analyze top 5 competitors"
)
```

### 3. Decision
Branch points with gate evaluation that determine execution flow.

**Properties:**
- Has a `gate_condition` attribute
- Evaluates to true/false at runtime
- Can branch to different downstream nodes

**Example:**
```python
Decision(
    id="dec_1",
    title="Risk Threshold Gate",
    description="Proceed if risk score < 0.7",
    gate_condition="risk_assessment.score < 0.7"
)
```

### 4. Evidence
Required data or artifacts that must be collected before proceeding.

**Properties:**
- Represents external data dependencies
- Can be API calls, file reads, or user input
- Often a dependency of Decision nodes

**Example:**
```python
Evidence(
    id="evi_1",
    title="Market Size Data",
    description="Total addressable market for European region"
)
```

### 5. Deliverable
Expected outputs that constitute mission completion criteria.

**Properties:**
- Represents final artifacts
- Often merged back into Objective
- Can be documents, code, or decisions

**Example:**
```python
Deliverable(
    id="del_1",
    title="Market Entry Report",
    description="Comprehensive analysis with recommendation"
)
```

---

## Edge Types

### depends_on
**Dependency relationship** — The target node must complete before the source node can start.

**Usage:**
```python
# Task B depends on Task A
Edge(from_node="task_a", to_node="task_b", edge_type="depends_on")
```

### informs
**Information flow** — Non-blocking relationship where results from target inform source.

**Usage:**
```python
# Decision A informs Decision B (doesn't block)
Edge(from_node="decision_a", to_node="decision_b", edge_type="informs")
```

### blocks
**Blocking condition** — Source node waits until a condition is satisfied.

**Usage:**
```python
# Task A blocks Task B until approval
Edge(from_node="task_a", to_node="task_b", edge_type="blocks")
```

### branches_to
**Conditional branching** — Used with Decision nodes for conditional execution.

**Usage:**
```python
# Risk gate branches to mitigation plans
Edge(from_node="risk_gate", to_node="standard_plan", edge_type="branches_to")
Edge(from_node="risk_gate", to_node="enhanced_plan", edge_type="branches_to")
```

### produces
**Output relationship** — Source node produces an artifact used by target.

**Usage:**
```python
# Analysis produces report for deliverable
Edge(from_node="analysis", to_node="report", edge_type="produces")
```

---

## Graph Construction

### Example: Linear Mission

```
[Objective: Market Entry]
    |
    v
[Task: Competitor Analysis] --depends_on--> [Task: Pricing Strategy]
    |
    v
[Deliverable: Entry Report]
```

### Example: Decision Gate Mission

```
                 [Decision: Risk Gate]
                            |
        +-------------------+-------------------+
        | branches_to                   | branches_to
        v                               v
[Task: Standard Plan]          [Task: Enhanced Plan]
        |                               |
        +---------------+---------------+
                        |
                        v
              [Deliverable: Final Report]
```

### Python API Example

```python
from torq_console.mission_graph import MissionGraph, Objective, Task, Decision

# Create nodes
objective = Objective(
    id="obj_1",
    title="Market Entry Assessment",
    description="Assess viability of European market entry"
)

task_1 = Task(
    id="task_1",
    title="Competitor Analysis",
    description="Identify and analyze top 5 competitors"
)

task_2 = Task(
    id="task_2",
    title="Pricing Strategy",
    description="Develop pricing for European market"
)

decision = Decision(
    id="dec_1",
    title="Risk Threshold Gate",
    description="Proceed if risk score < 0.7",
    gate_condition="risk_score < 0.7"
)

# Create graph
graph = MissionGraph(
    id="graph_1",
    nodes=[objective, task_1, task_2, decision],
    edges=[
        Edge(from_node="obj_1", to_node="task_1", edge_type="depends_on"),
        Edge(from_node="task_1", to_node="decision", edge_type="depends_on"),
        Edge(from_node="decision", to_node="task_2", edge_type="branches_to"),
    ]
)
```

---

## Execution Model

### Dependency Resolution

1. **Ready Set Identification**: Nodes with all `depends_on` edges satisfied are marked `ready`
2. **Parallel Execution**: All ready nodes are dispatched concurrently
3. **Completion Propagation**: When a node completes, dependent nodes are evaluated for readiness
4. **Decision Evaluation**: Decision nodes evaluate gate conditions and activate appropriate branches

### Status Transitions

```
pending -> ready -> running -> completed
                    |
                    v
                 failed/soft_failed/skipped
```

### Handoff Flow

When a node completes, it creates a handoff containing:
- `objective_completed`: What was accomplished
- `output_summary`: Concise summary of results
- `key_findings`: Important discoveries
- `recommendations`: Actionable recommendations
- `confidence`: Quality score (0.0–1.0)
- `artifacts`: Produced artifacts
- `risks`: Identified risks
- `assumptions`: Assumptions made

---

## Template Missions

### Market Entry Template

```python
template = MissionGraph(
    id="market_entry_template",
    name="Market Entry Assessment",
    nodes=[
        Objective("Market Entry Viability"),
        Task("Competitor Analysis"),
        Task("Market Sizing"),
        Evidence("Regulatory Requirements"),
        Decision("Go/No-Go Gate"),
        Deliverable("Entry Strategy Document"),
    ],
    edges=[
        # Define template structure
    ]
)
```

### Risk Assessment Template

```python
template = MissionGraph(
    id="risk_assessment_template",
    name="Risk Assessment with Mitigation",
    nodes=[
        Objective("Risk Assessment"),
        Task("Technical Risk Analysis"),
        Task("Business Risk Analysis"),
        Decision("Risk Threshold Gate"),
        Task("Standard Mitigation"),
        Task("Enhanced Mitigation"),
        Deliverable("Risk Report"),
    ],
    edges=[
        # Risk threshold gate branches to different mitigation paths
    ]
)
```

---

## Validation

Mission graphs are validated before execution:

1. **Acyclic Check**: Graph must be a DAG (no cycles)
2. **Single Objective**: Exactly one objective node required
3. **Connected**: All nodes must be reachable from objective
4. **Valid Edges**: Edge references must point to existing nodes
5. **Decision Gates**: Decision nodes must have at least one `branches_to` edge

---

## Integration with Execution Fabric

Mission Graph Planning integrates with Phase 5.1 Execution Fabric:

- **Context Bus**: Events for node lifecycle (`node.ready`, `node.started`, `node.completed`)
- **Handoff Manager**: Structured handoffs between nodes
- **Workstream State**: Health tracking across parallel work
- **Hardened Scheduler**: Idempotent node execution

---

## API Reference

### Creating a Mission with Graph

```python
from torq_console.mission_graph import create_mission_with_graph

mission = await create_mission_with_graph(
    objective="Assess market opportunity",
    reasoning_strategy="analytical",
    graph=market_entry_template
)
```

### Executing a Mission Graph

```python
from torq_console.mission_graph import MissionGraphScheduler

scheduler = MissionGraphScheduler(supabase_client)
result = await scheduler.execute_graph(mission, mission.graph)

# Result contains:
# - status: final mission status
# - completed_nodes: count of completed nodes
# - failed_nodes: count of failed nodes
# - progress_percent: completion percentage
```

---

## Maturity: Validated Beta

**Validated:**
- Dependency resolution across linear missions
- Decision gate branching
- Parallel execution of ready nodes
- Integration with hardened scheduler

**Next:**
- Additional mission shape validation
- Template library expansion
- Replanning integration

---

## See Also

- [Phase 5.1 Execution Fabric](PHASE_5_1_EXECUTION_FABRIC.md) — Execution runtime
- [Phase 4H Strategic Memory](PHASE_4H_STRATEGIC_MEMORY.md) — Memory system
- [Architecture Index](ARCHITECTURE_INDEX.md) — System overview
