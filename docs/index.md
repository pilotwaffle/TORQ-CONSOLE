# TORQ Console Documentation

**Version**: v0.9.0-beta
**Last Updated**: March 8, 2026

---

## Quick Start

- **[Current Status](current/IMPLEMENTATION_STATUS.md)** — What's implemented and validated today
- **[System Overview](current/TORQ_SYSTEM_OVERVIEW.md)** — Complete request-to-response walkthrough
- **[Architecture Index](architecture/ARCHITECTURE_INDEX.md)** — Canonical system architecture
- **[Architecture Roadmap](architecture/ARCHITECTURE_ROADMAP.md)** — Release timeline and future phases

---

## Documentation Structure

```
docs/
├── index.md                    # This file
├── current/                    # Verified system (Level 1)
│   ├── IMPLEMENTATION_STATUS.md        # What exists and has evidence
│   ├── PHASE_5_1_VALIDATION_REPORT.md  # Validation evidence
│   ├── PHASES_4_7_IMPLEMENTATION_AUDIT.md  # Complete audit
│   ├── TORQ_SYSTEM_OVERVIEW.md         # Request-to-response flow
│   └── TORQ_VISION.md                   # What TORQ is
│
├── architecture/               # System explanation (Level 2)
│   ├── ARCHITECTURE_INDEX.md            # Component catalog
│   ├── ARCHITECTURE_ROADMAP.md          # Version roadmap
│   ├── PHASE_5_MISSION_GRAPH_PLANNING.md  # Mission graphs
│   ├── PHASE_5_1_EXECUTION_FABRIC.md     # Execution fabric
│   └── PHASE_4H_STRATEGIC_MEMORY.md       # Memory system
│
└── prd/                         # Future design (Level 3)
    ├── PHASE_5_2_AGENT_TEAMS_PRD.md          # Specialist teams
    ├── PHASE_5_3_ORGANIZATIONAL_LEARNING_PRD.md  # Org learning
    └── PHASE_7_FIRM_OPERATING_LAYER_PRD.md   # Firm-scale operations
```

---

## Three Levels of Truth

### Level 1: Verified System

What exists **and has validation evidence**.

- ✅ Mission Graph Planning (implemented)
- ✅ Hardened Execution Fabric (validated — 0 duplicate events)
- ✅ Idempotent lifecycle handling
- ✅ Rich handoff generation (validated — 100% rich format)

### Level 2: Implemented Architecture

Real components that exist but are still evolving.

- ✅ Strategic Memory (implemented)
- ✅ Reasoning Synthesis (implemented)
- ✅ Adaptive Cognition Loop (partial implementation)

### Level 3: Designed Future

Well-specified systems that are **not implemented yet**.

- 📋 Agent Teams on Mission Graphs (Phase 5.2 — PRD complete)
- 📋 Organizational Learning Loop (Phase 5.3 — PRD complete)
- 📋 Firm Operating Layer (Phase 7 — PRD complete)

---

## Current Status: v0.9.0-beta

**Validated Beta Architecture** — Mission Graph Planning + Hardened Execution Fabric

### What Ships Today

| Component | Status | Validation |
|-----------|--------|------------|
| Mission Graph Planning | Beta | Functional |
| Hardened Execution Fabric | **Validated** | 3 missions, 0 duplicate events |
| Strategic Memory | Beta | Functional |
| Reasoning Synthesis | Beta | Functional |

### What's Next

| Version | Focus | Target |
|---------|-------|--------|
| v0.10.0 | Agent Teams | Q2 2026 |
| v0.11.0 | Organizational Learning | Q3 2026 |
| v0.12.0 | Firm Operating Layer | Q3 2026 |
| v1.0.0 | Production Release | Q4 2026 |

---

## Key Documents

### For Understanding TORQ

1. [TORQ Vision](current/TORQ_VISION.md) — What TORQ is and why it matters
2. [System Overview](current/TORQ_SYSTEM_OVERVIEW.md) — How TORQ processes requests
3. [Architecture Index](architecture/ARCHITECTURE_INDEX.md) — Complete component catalog

### For Validation Evidence

4. [Implementation Status](current/IMPLEMENTATION_STATUS.md) — What's implemented vs planned
5. [Phase 5.1 Validation Report](current/PHASE_5_1_VALIDATION_REPORT.md) — Hardened execution validation
6. [Implementation Audit](current/PHASES_4_7_IMPLEMENTATION_AUDIT.md) — Complete audit findings

### For Architecture

7. [Architecture Roadmap](architecture/ARCHITECTURE_ROADMAP.md) — Release timeline
8. [Mission Graph Planning](architecture/PHASE_5_MISSION_GRAPH_PLANNING.md) — Dependency execution
9. [Execution Fabric](architecture/PHASE_5_1_EXECUTION_FABRIC.md) — Hardened runtime
10. [Strategic Memory](architecture/PHASE_4H_STRATEGIC_MEMORY.md) — Memory system

### For Future Roadmap

11. [Agent Teams PRD](prd/PHASE_5_2_AGENT_TEAMS_PRD.md) — Specialist teams on nodes
12. [Organizational Learning PRD](prd/PHASE_5_3_ORGANIZATIONAL_LEARNING_PRD.md) — Self-improving organization
13. [Firm Operating Layer PRD](prd/PHASE_7_FIRM_OPERATING_LAYER_PRD.md) — Multi-mission scale

---

## Honest Positioning

TORQ v0.9.0-beta provides a validated architecture for mission-structured multi-agent reasoning, featuring Mission Graph Planning and a hardened Execution Fabric with idempotent coordination. It also includes implemented strategic memory and synthesis layers.

Additional capabilities such as Agent Teams, Organizational Learning, and Firm-Scale Operations are defined in the roadmap and PRDs but are **not yet implemented**.

---

## Support

- **Issues**: https://github.com/pilotwaffle/TORQ-CONSOLE/issues
- **Discussions**: https://github.com/pilotwaffle/TORQ-CONSOLE/discussions
- **Documentation**: This index

---

*For detailed changes in each release, see the [CHANGELOG.md](../CHANGELOG.md) in the repository root.*
