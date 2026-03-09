# TORQ Console Architecture Roadmap

**Version**: v0.9.0-beta
**Last Updated**: March 8, 2026

---

## Current State: v0.9.0-beta (Validated Architecture)

| Phase | Component | Status | Maturity |
|-------|-----------|--------|----------|
| 1-2 | Core Infrastructure | Complete | Production |
| 3 | Multi-Agent Orchestration | Complete | Production |
| 4E | Reasoning Synthesis Engine | Complete | Production |
| 4F | Adaptive Cognition Loop | Complete | Beta |
| 4H | Strategic Memory | Complete | Beta |
| 5 | Mission Graph Planning | Complete | Validated Beta |
| 5.1 | Execution Fabric (Hardened) | Complete | Validated Beta |

---

## Roadmap

### v0.10.0: Agent Teams on Mission Graphs (Phase 5.2)

**Status**: PRD Complete
**Target**: Q2 2026

**Key Features**:
- Node Team Builder (determines team composition)
- Team Collaboration Engine (3 patterns: parallel+synthesis, lead+challenger, gatherers+reviewer)
- Node Team Workspace (specialist contributions, conflicts, synthesis)
- Team Synthesizer (integrates specialist outputs)
- Team Quality Gate (prevents low-quality completion)

**Strategic Impact**: TORQ becomes "consulting firm" rather than "task executor"

---

### v0.11.0: Replanning Engine (Phase 5.3)

**Status**: Planned
**Target**: Q3 2026

**Key Features**:
- Deviation detection (expected vs actual mission state)
- Dynamic graph replanning (modify graph mid-execution)
- Work preservation (migrate completed nodes to new plan)
- Rollback capability (revert to previous graph state)

**Strategic Impact**: TORQ adapts to changing conditions mid-mission

---

### v0.12.0: Operator Control Surface (Phase 6)

**Status**: Planned
**Target**: Q3 2026

**Key Features**:
- Mission control dashboard (real-time mission status)
- Node intervention (pause, retry, override nodes)
- Team inspector (view specialist collaboration)
- Handoff viewer (trace information flow)
- Conflict resolver (manual conflict resolution)

**Strategic Impact**: Human operators can monitor and intervene in missions

---

### v1.0.0: Production Release

**Status**: Planned
**Target**: Q4 2026

**Criteria**:
- All validated components promoted to Production
- Comprehensive test coverage (>90%)
- Performance benchmarks met
- Security audit passed
- Documentation complete
- Success stories/ case studies

---

## Component Maturity Progression

```
Experimental → Beta → Validated Beta → Production
     ↓            ↓           ↓                ↓
   Framework   Implemented   Tested      Field-Tested
   exists      & needs      & evidence   & reliable
               testing      backed
```

---

## Priority Matrix

| Phase | Impact | Effort | Priority |
|-------|--------|--------|----------|
| 5.2 Agent Teams | High | Medium | **P0** |
| 5.3 Replanning | High | High | P1 |
| 6 Operator Control | High | Medium | P1 |
| 4G Pattern Aggregation | Medium | Medium | P2 |
| 4I Insight Publishing | Medium | Low | P2 |

---

## Dependencies

```
Phase 5.2 (Agent Teams)
    ├── Requires: Phase 5 (Mission Graph)
    ├── Requires: Phase 5.1 (Execution Fabric)
    ├── Requires: Phase 3 (Multi-Agent Orchestration)
    └── Enables: Phase 5.3 (Replanning)

Phase 5.3 (Replanning)
    ├── Requires: Phase 5.2 (Agent Teams)
    ├── Requires: Phase 4H (Strategic Memory)
    └── Enables: Phase 6 (Operator Control)

Phase 6 (Operator Control)
    ├── Requires: Phase 5.3 (Replanning)
    └── Enables: Production readiness
```

---

## See Also

- [Phase 5.2 PRD](PHASE_5_2_AGENT_TEAMS_PRD.md)
- [Architecture Index](ARCHITECTURE_INDEX.md)
- [System Overview](TORQ_SYSTEM_OVERVIEW.md)
