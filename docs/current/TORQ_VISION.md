# TORQ Vision

**Version**: v0.9.0-beta
**Last Updated**: March 8, 2026

---

## What TORQ Is

TORQ Console is an **adaptive multi-agent reasoning platform** — a cognitive operating system for AI-powered consulting.

Unlike other AI systems that execute tasks and forget, TORQ:

1. **Structures missions** the way a consulting firm would
2. **Coordinates execution** with idempotent guarantees
3. **Accumulates learning** across sessions
4. **Collaborates specialists** on complex problems

**The big idea**: Build a digital consulting firm, not just a better prompt wrapper.

---

## Why Mission Graphs Matter

### The Problem with Prompt Chaining

Most AI systems work like this:

```
User Request → Prompt 1 → Prompt 2 → Prompt 3 → Response
```

This is fragile. If Prompt 2 fails, you're stuck. There's no visibility into what's happening. You can't replay or debug.

### The Mission Graph Approach

TORQ structures requests as **mission graphs**:

```
Objective (Market Entry Assessment)
    │
    ├── Task (Competitor Analysis) ──┐
    │                               │
    ├── Task (Market Sizing)         ├── Decision Gate
    │                               │
    ├── Evidence (Regulatory Data) ──┤
    │                               │
    └── Decision (Go/No-Go) ─────────┘
                │
                ▼
        Deliverable (Entry Strategy)
```

### Why This Matters

| Benefit | What It Enables |
|---------|-----------------|
| **Dependency Awareness** | Tasks execute in correct order, automatically |
| **Decision Gates** | Branch based on actual conditions, not assumptions |
| **Visibility** | See exactly what's running, what's blocked, what's complete |
| **Replayability** | Debug failed missions by retracing the graph |
| **Parallel Execution** | Independent tasks run simultaneously |

### Real Example

**User Request**: "Assess whether we should enter the European market"

**TORQ Generates**:

```
Objective: European Market Entry Assessment
│
├── Task: Competitive Landscape Analysis
├── Task: Market Sizing & Forecasting
├── Task: Regulatory Requirements Assessment
├── Evidence: GDPR Compliance Analysis
├── Decision: Risk Threshold Gate (proceed if risk < 0.7)
│   ├── True → Standard Market Entry Plan
│   └── False → Enhanced Risk Mitigation Plan
└── Deliverable: Market Entry Recommendation Document
```

Each node has:
- Clear objective
- Dependencies (what must complete first)
- Handoff format (what gets passed to next node)
- Success criteria (when is this node done?)

---

## Why Execution Fabric Matters

### The Problem: Mission Execution is Fragile

In most systems, if something goes wrong mid-mission:
- You don't know what executed
- You can't safely retry (might duplicate work)
- You can't see where things failed
- You lose the mission state

### The TORQ Execution Fabric

TORQ's execution fabric provides **stateful collaboration infrastructure** for AI agents — equivalent to Slack + Jira + Git + Notion, but for agents.

#### Four Key Components

**1. Hardened Scheduler**
- Ensures nodes execute exactly once
- Safe retry (no duplicate side effects)
- Atomic state transitions
- Zero duplicate events (validated: 33 → 0 duplicates)

**2. Context Bus**
- Event-driven coordination
- 20+ event types (node.ready, node.started, node.completed, handoff.created, etc.)
- Full mission traceability
- Debugging via event log

**3. Handoff Manager**
- Structured collaboration packets between nodes
- Rich format: findings, recommendations, confidence, artifacts, risks, assumptions
- No lost context between specialists
- Traceable information flow

**4. Workstream State Manager**
- Health tracking across parallel work
- Detects blocked or degraded nodes
- Enables intervention before failures

### Why This Matters

| Problem | Execution Fabric Solution |
|---------|---------------------------|
| Duplicate execution on retry | Idempotent node execution |
| Lost context between agents | Rich handoff format |
| Can't debug failures | Complete event log |
| No visibility into parallel work | Workstream health tracking |
| Mission state lost on error | Checkpoint manager |

### Real Example

**Node Handoff** from "Competitor Analysis" to "Market Sizing":

```json
{
  "handoff_summary": {
    "objective_completed": "Competitive landscape analysis",
    "output_summary": "Identified 5 key competitors with market share and positioning",
    "key_findings": [
      "Competitor A: 35% market share, premium positioning",
      "Competitor B: 25% market share, value positioning",
      "Market fragmented: Top 3 players hold <70% combined"
    ],
    "recommendations": [
      "Focus on quality differentiation (market gap)",
      "Consider partnership with smaller players"
    ]
  },
  "confidence": 0.91,
  "confidence_basis": "Public filings verified, analyst reports cross-checked",
  "artifacts": {
    "competitor_table": {...},
    "positioning_map": {...}
  },
  "risks": [
    "Data from Q3 only, market may have shifted"
  ],
  "assumptions": [
    "Public filings accurate",
    "Analyst reports unbiased"
  ]
}
```

The next node receives ALL of this context — not just "competitors analyzed, done."

---

## Why Institutional Memory Matters

### The Problem: Every Mission Starts from Scratch

Most AI systems:

```
Mission 1: Assess market entry → produce answer → forget
Mission 2: Assess market entry → produce answer → forget (same work!)
Mission 3: Assess market entry → produce answer → forget (same work!)
```

Each mission learns nothing from previous missions.

### The TORQ Strategic Memory

TORQ accumulates **doctrine** — learned patterns that shape future missions.

```
Mission 1: Learn
    ↓
Strategic Memory Store
    ↓
Mission 2: Apply Learning + Learn More
    ↓
Strategic Memory Store (richer)
    ↓
Mission 3: Apply All Learning + Learn More
```

### What Gets Stored

| Memory Type | Example |
|-------------|---------|
| **Outcome Pattern** | "Markets with GDPR-like regulations have 40% longer entry timelines" |
| **Strategy Effectiveness** | "Risk-first strategy works best for acquisition assessments" |
| **Team Composition** | "Financial nodes need evidence-weighted synthesis" |
| **Failure Pattern** | "Nodes with >3 dependencies have 30% failure rate" |

### Real Example

**Mission 1** learns:
- "European market entry requires 6-8 month regulatory approval"
- "Local partnerships essential for distribution"
- "GDPR compliance is critical blocker"

**Mission 2** (new market entry assessment) receives:
```
Strategic Context Injection:
"From 3 similar European market entry missions:
- Regulatory approval takes 6-8 months (factor into timeline)
- Local partnerships essential (identify partners early)
- GDPR compliance critical (assess early in mission)"
```

Mission 2 starts smarter, not from zero.

---

## What Agent Teams Will Enable

### Current State (Phase 5.1)

One specialist per node:

```
Node: "Assess acquisition viability"
    ↓
One Financial Analyst
    ↓
Output
```

This produces coherent but shallow output. A single financial analyst can't deeply assess legal, operational, and strategic dimensions.

### Future State (Phase 5.2)

Specialist teams per node:

```
Node: "Assess acquisition viability"
    ↓
Team Collaboration:
    ├── Financial Analyst
    ├── Legal Specialist
    ├── Operations Strategist
    └── Synthesizer
    ↓
Integrated Recommendation
```

### Why This Matters

| Before (Solo Specialist) | After (Specialist Team) |
|--------------------------|-------------------------|
| Single domain perspective | Multi-domain perspective |
| Assumptions unchallenged | Assumptions stress-tested |
| Limited evidence coverage | Comprehensive evidence |
| Coherent but shallow | Coherent and deep |

### Real Example

**Node**: "Assess whether to acquire Target Corp ($50M SaaS, EU-based)"

**Specialist Team Execution**:

1. **Financial Analyst**: "Financials strong. Revenue growing 40% YoY. Recommendation: Proceed."
   - Confidence: 0.91

2. **Legal Specialist**: "GDPR compliance uncertain. Data localization requirements may increase integration cost by $2M."
   - Flags: Material risk not in financial model

3. **Operations Strategist**: "Integration complex. Team distributed across EU. Cultural alignment uncertain."
   - Flags: Execution risk

4. **Synthesizer**: "Proceed with acquisition, subject to conditions:
   - Confirm GDPR compliance pathway within 30 days
   - Negotiate price to reflect integration risk (≤$45M)
   - Secure key team commitments (EU talent retention critical)
   - Budget +$2M for compliance infrastructure"
   - Confidence: 0.82 (lower due to surfaced risks)

**Result**: More nuanced recommendation, explicit risks, practical conditions — closer to how a real consulting firm works.

---

## The Complete Loop

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER REQUEST                            │
│                  "Assess market entry for X"                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    1. MISSION GRAPH PLANNING                    │
│                 Structure mission as dependency graph            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    2. STRATEGIC MEMORY INJECTION                 │
│           Inject relevant past experiences into mission          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     3. EXECUTION FABRIC                          │
│      Coordinate specialists with idempotent guarantees           │
│                    (Context Bus + Handoffs)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    4. SPECIALIST COLLABORATION                  │
│           (Future Phase 5.2) Teams collaborate per node          │
│                    Synthesis produces node output                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      5. REASONING SYNTHESIS                      │
│            Combine multi-node outputs into coherent insights      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        6. EVALUATION                             │
│                Quality assessment across dimensions              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   7. ADAPTIVE COGNITION LOOP                     │
│              Learn from outcomes to improve future missions       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   8. STRATEGIC MEMORY STORAGE                    │
│              Store learnings for cross-mission retrieval         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Where TORQ Is Heading

### Current (v0.9.0-beta)

| Capability | Status |
|------------|--------|
| Mission graph planning | ✅ Validated |
| Idempotent execution fabric | ✅ Validated |
| Institutional memory | ✅ Beta |
| Multi-agent orchestration | ✅ Production |

### Near Future (v0.10.0 - Phase 5.2)

| Capability | Status |
|------------|--------|
| Specialist teams per node | 🔄 Planned |
| Team collaboration patterns | 🔄 Planned |
| Multi-specialist synthesis | 🔄 Planned |
| Team quality gates | 🔄 Planned |

### Future Vision (v1.0+)

| Capability | Status |
|------------|--------|
| Adaptive replanning | 📋 Planned |
| Human strategic oversight | 📋 Planned |
| Autonomous consulting missions | 📋 Planned |
| Self-improving organization | 📋 Planned |

---

## The Strategic Difference

### Most AI Systems

```
Request → Prompt → Response → Forget
```

### TORQ

```
Request → Mission Graph → Execution Fabric → Collaboration
    ↓                                            ↓
Strategic Memory ←────────── Adaptive Loop ←── Evaluation
```

**Result**: TORQ doesn't just answer questions — it accumulates expertise.

---

## For New Contributors

### Quick Mental Model

Think of TORQ as:

1. **Project Management** (Mission Graph) — What needs to happen, in what order
2. **Operating System** (Execution Fabric) — Coordinating work, handling failures
3. **Consulting Firm** (Agent Teams) — Specialists collaborating on problems
4. **Institutional Knowledge** (Strategic Memory) — Learning from experience

### Where to Start

1. **Understand the flow**: Read `docs/TORQ_SYSTEM_OVERVIEW.md`
2. **See the architecture**: Read `docs/ARCHITECTURE_INDEX.md`
3. **See the validation**: Read `docs/PHASE_5_1_VALIDATION_REPORT.md`
4. **See what's next**: Read `docs/PHASE_5_2_AGENT_TEAMS_PRD.md`

---

## The Real Opportunity

Most AI systems are tools.

TORQ is becoming an **organization**.

An organization that:
- Plans before executing
- Coordinates multiple specialists
- Learns from experience
- Adapts its approach
- Accumulates institutional knowledge

That's what makes TORQ different.

---

## Version

**Current Release**: v0.9.0-beta
**Classification**: Validated Beta Architecture
**Next Milestone**: v0.10.0 (Agent Teams on Mission Graphs)

---

## See Also

- [System Overview](TORQ_SYSTEM_OVERVIEW.md) — Complete request-to-response flow
- [Architecture Index](ARCHITECTURE_INDEX.md) — Canonical component map
- [Phase 5.2 PRD](PHASE_5_2_AGENT_TEAMS_PRD.md) — Next major feature
- [Architecture Roadmap](ARCHITECTURE_ROADMAP.md) — Release timeline
