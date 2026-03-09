# TORQ Console System Overview

**Version**: v0.9.0-beta
**Last Updated**: March 8, 2026

---

## What is TORQ Console?

TORQ Console is an **adaptive multi-agent reasoning platform** that structures complex missions the way a strong consulting team would. It combines institutional memory, mission graph planning, and hardened execution fabric for coordinated AI teamwork.

---

## The Big Picture: Request to Response Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER REQUEST                                    │
│                         "Assess market entry for X"                          │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         1. MISSION GRAPH PLANNING                           │
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │  Objective   │───▶│    Tasks     │───▶│ Deliverables │                   │
│  │              │    │              │    │              │                   │
│  │ "Market      │    │ • Competitor │    │ • Entry      │                   │
│  │  Entry       │    │   Analysis   │    │   Report     │                   │
│  │  Assessment" │    │ • Risk Assess│    │              │                   │
│  └──────────────┘    └──────────────┘    └──────────────┘                   │
│                                                                             │
│  Dependency graph ensures tasks execute in correct order                    │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      2. STRATEGIC MEMORY INJECTION                          │
│                                                                             │
│  "From 3 similar past missions:"                                           │
│  • Regulatory approval takes 6-8 months                                     │
│  • Local partnerships are essential                                         │
│  • GDPR compliance is critical"                                             │
│                                                                             │
│  Past experiences shape current mission planning                             │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         3. EXECUTION FABRIC                                  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                    HARDENED SCHEDULER                            │       │
│  │                                                                  │       │
│  │  For each node:                                                  │       │
│  │  1. Check if already completed (idempotency)                    │       │
│  │  2. Atomic transition to RUNNING                                │       │
│  │  3. Emit node.started event (exactly once)                      │       │
│  │  4. Execute work (call agent/specialist)                        │       │
│  │  5. Atomic transition to COMPLETED                              │       │
│  │  6. Emit node.completed event (exactly once)                    │       │
│  │  7. Create handoff for next node (exactly once)                 │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                             │
│  Guarantees: No duplicate events, safe retry, race-condition-free          │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        4. MULTI-AGENT ORCHESTRATION                         │
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │   Analyst   │  │  Researcher │  │ Synthesizer │  │ Evaluator  │       │
│  │             │  │             │  │             │  │             │       │
│  │ Market data │  │ Competitor  │  │ Combine     │  │ Quality    │       │
│  │ analysis    │  │ intel       │  │ findings    │  │ scoring    │       │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │
│                                                                             │
│  Agent router selects right specialist for each node                        │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         5. HANDOFF PROPAGATION                              │
│                                                                             │
│  Rich handoff format ensures context flows between nodes:                   │
│                                                                             │
│  {                                                                         │
│    "handoff_summary": {                                                    │
│      "objective_completed": "Competitor analysis completed",                │
│      "output_summary": "Identified 5 key competitors",                      │
│      "key_findings": ["Competitor A has 35% share", ...],                  │
│      "recommendations": ["Focus on quality", ...]                           │
│    },                                                                      │
│    "confidence": 0.91,                                                     │
│    "artifacts": {"competitor_table": ...},                                  │
│    "risks": ["Data from Q3 only"],                                         │
│    "assumptions": ["Public filings accurate"]                              │
│  }                                                                         │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        6. WORKSPACE MEMORY                                  │
│                                                                             │
│  Working memory for current mission:                                       │
│  • Node execution states                                                   │
│  • Intermediate artifacts                                                 │
│  • Collaboration context                                                   │
│  • Progress tracking                                                       │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         7. REASONING SYNTHESIS                              │
│                                                                             │
│  Combine outputs from multiple nodes into coherent insights:                │
│                                                                             │
│  "Market entry analysis completed. Key findings:                            │
│   • Addressable market: $2.3B                                              │
│   • Competition: Fragmented, top player has 15% share                      │
│   • Barriers: Regulatory (6-8 months), partnership required                │
│   • Recommendation: Proceed with phased entry, partner with local firm"    │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          8. EVALUATION                                      │
│                                                                             │
│  Quality assessment across dimensions:                                     │
│  • Clarity: 0.92 (findings well-articulated)                               │
│  • Completeness: 0.88 (all required analysis done)                         │
│  • Feasibility: 0.85 (recommendations actionable)                           │
│  • Overall Score: 0.91                                                     │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       9. MISSION COMPLETION                                 │
│                                                                             │
│  Mission marked as completed:                                               │
│  • Status: completed                                                        │
│  • Overall Score: 0.91                                                     │
│  • Completed Nodes: 7/7                                                    │
│  • Failed Nodes: 0                                                         │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       10. ADAPTIVE COGNITION LOOP                           │
│                                                                             │
│  Learning from this mission for future missions:                            │
│  • What worked: Multi-agent approach effective                              │
│  • What didn't: Risk assessment needed more data                           │
│  • Signals collected: Quality score 0.91, risk-first strategy worked        │
│  • Adaptation proposal: Increase data collection for risk nodes            │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      11. STRATEGIC MEMORY STORAGE                           │
│                                                                             │
│  Store learning for future missions:                                        │
│  • "European market entry requires 6-8 month regulatory timeline"           │
│  • "Local partnerships essential for market access"                        │
│  • "Risk-first strategy effective for regulated markets"                    │
│                                                                             │
│  Future missions will retrieve and use this context                         │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            12. RESPONSE                                     │
│                                                                             │
│  Mission complete. Summary delivered to user.                              │
│  Insights stored in strategic memory for next time.                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Layer-by-Layer Breakdown

### Layer 1: Foundation (Phase 1-2)

**What it is**: Core infrastructure

**Components**:
- Supabase PostgreSQL database
- Claude API integration
- Configuration management

**Why it matters**: Reliable foundation for everything above

---

### Layer 2: Reasoning (Phase 3)

**What it is**: Multi-agent orchestration

**Components**:
- Agent Router: Selects right agent for each task
- Specialist Agents: Analyst, Researcher, Synthesizer, Evaluator
- Collaboration Protocols: How agents work together

**Why it matters**: Different problems need different specialists

---

### Layer 3: Intelligence (Phase 4)

**What it is**: Learning and memory systems

**Components**:

| Subsystem | Purpose | Status |
|-----------|---------|--------|
| **Strategic Memory (4H)** | Long-term memory across sessions | Beta |
| **Adaptive Cognition (4F)** | Learning from outcomes | Beta |
| **Reasoning Synthesis (4E)** | Combine multi-agent outputs | Production |

**Why it matters**: Platform improves with use

---

### Layer 4: Execution (Phase 5)

**What it is**: Mission planning and execution

**Components**:

| Subsystem | Purpose | Status |
|-----------|---------|--------|
| **Mission Graph Planning (5)** | Dependency-aware execution | Validated Beta |
| **Execution Fabric (5.1)** | Idempotent coordination | Validated Beta |
| **Hardened Scheduler** | Duplicate-safe execution | Validated Beta |

**Why it matters**: Complex missions execute reliably

---

## Key Innovations

### 1. Hardened Execution Path

**Problem**: Mission retry created duplicate events and handoffs

**Solution**: Atomic state transitions + idempotent guards

**Result**: 33 duplicate events → 0 duplicate events

### 2. Rich Handoff Format

**Problem**: Agents lost context between nodes

**Solution**: Structured collaboration packets with findings, recommendations, artifacts

**Result**: 64% rich format → 100% rich format

### 3. Strategic Memory

**Problem**: Each mission started from scratch

**Solution**: Persistent memory injected into relevant missions

**Result**: Cross-session learning

---

## Component Maturity

| Component | Maturity | What It Means |
|-----------|----------|---------------|
| Multi-Agent Orchestration | **Production** | Field-tested, reliable |
| Mission Graph Planning | **Validated Beta** | Implemented and validated |
| Execution Fabric | **Validated Beta** | Idempotency proven |
| Hardened Scheduler | **Validated Beta** | Default runtime path |
| Strategic Memory | **Beta** | Implemented, needs testing |
| Adaptive Cognition | **Beta** | Learning loop operational |
| Replanning Engine | **Experimental** | Framework exists |

---

## Quick Start API

### Execute a Mission

```python
from torq_console.mission_graph import MissionGraphScheduler
from torq_console.dependencies import get_supabase_client

# Initialize
supabase = get_supabase_client()
scheduler = MissionGraphScheduler(supabase)

# Create and execute mission
mission = await create_mission(
    objective="Assess market entry for Product X",
    reasoning_strategy="risk_first",
    context={"market": "Europe", "product": "Product X"}
)

result = await scheduler.execute_graph(mission, mission.graph)

print(f"Status: {result['status']}")
print(f"Progress: {result['progress_percent']}%")
```

### Query Strategic Memory

```python
from torq_console.strategic_memory import MemoryRouter

router = MemoryRouter(supabase_client)

# Get relevant memories
memories = await router.get_relevant_memories(
    mission_context={
        "objective": "Assess market entry",
        "tags": ["market-entry", "europe"]
    },
    limit=10
)

for memory in memories:
    print(f"{memory['summary']} (relevance: {memory['relevance_score']})")
```

---

## What's Next?

### Phase 5.2: Agent Teams on Mission Graphs

**Current**: One specialist per node

**Next**: Coordinated specialist teams per node

**Example**: Risk Assessment node could use:
- Financial Analyst (market sizing)
- Legal Specialist (regulatory analysis)
- Operations Expert (implementation complexity)
- Team synthesizes combined recommendation

---

## Documentation

- [Architecture Index](ARCHITECTURE_INDEX.md) — Complete system overview
- [Phase 5.1 Validation Report](PHASE_5_1_VALIDATION_REPORT.md) — Evidence-backed validation
- [Mission Graph Planning](PHASE_5_MISSION_GRAPH_PLANNING.md) — Dependency execution
- [Execution Fabric](PHASE_5_1_EXECUTION_FABRIC.md) — Hardened runtime
- [Strategic Memory](PHASE_4H_STRATEGIC_MEMORY.md) — Memory system

---

## Status

**Version**: v0.9.0-beta
**Classification**: Validated Beta Architecture
**Release Date**: March 8, 2026

Validated across 3 mission shapes with hardened executor as default runtime path.
