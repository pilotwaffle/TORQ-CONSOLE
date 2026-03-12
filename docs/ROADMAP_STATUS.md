# TORQ Roadmap Status

**Date:** 2026-03-09
**Current Phase:** 5.3 - Workspace Integration (Ready)

---

## Completed Phases

### ✅ Phase 5.2: Agent Teams (COMPLETE)
- **Runtime:** Governed multi-agent execution with 4 roles (Lead, Researcher, Critic, Validator)
- **Persistence:** Supabase-backed (20+ executions, 300+ messages, 20+ decisions)
- **Observability:** Live SSE streaming, historical replay, control surface UI
- **Validation:** 7/7 integration tests passing
- **Tag:** `v0.5.2b-agent-teams-observability`
- **Docs:** `PHASE_5_2_COMPLETE.md`

**Frozen Components (DO NOT CHANGE):**
- `AgentTeamOrchestrator`
- `RoleRunner`
- `DecisionEngine`
- Team persistence schema
- 5.2B observability contracts (except additive read-only)

---

## Active Phase

### 📋 Phase 5.3: Agent Tool Workspace Integration (READY)
- **Goal:** Make tool outputs first-class workspace artifacts
- **Type:** Additive traceability layer (NOT a new runtime)
- **PRD:** `PHASE_5_3_WORKSPACE_INTEGRATION_PRD.md`

**Implementation Milestones:**

1. **Tool Output Contract**
   - Normalize tool results into consistent structure
   - Define artifact typing rules
   - Include execution/workspace linkage metadata

2. **Workspace Artifact Persistence**
   - Create `workspace_artifacts` table
   - Build persistence service
   - Preserve write ordering

3. **Execution/Team Context Linking**
   - Link artifacts to mission/node/team/round context
   - Context-aware scope selection
   - No changes to frozen 5.2 runtime

4. **Read/Inspection Layer**
   - Query artifacts by workspace/execution/team
   - API endpoints for artifact retrieval

5. **Validation & Hardening**
   - No regression in 5.2A / 5.2B
   - Concurrent write safety
   - Duplicate prevention

**Acceptance Criteria:**
- Tool outputs persist to shared workspace
- Artifacts link to execution/team context
- Ordering preserved
- Readable reliably
- No 5.2 regression

---

## Future Phases (Defined, Not Started)

### 📝 Phase 5.4: Strategic Memory Validation & Control
- **PRD:** Complete (not yet implemented)

---

## Architectural Progression

```
structured team execution (5.2)
        ↓
workspace-linked artifact continuity (5.3)
        ↓
memory / retrieval / insight compounding (5.4+)
```

---

## Quick Access Docs

- [Phase 5.2 Complete Status](PHASE_5_2_COMPLETE.md)
- [Phase 5.3 Workspace Integration PRD](PHASE_5_3_WORKSPACE_INTEGRATION_PRD.md)

---

## Next Action

**Implement Milestones 1 & 2 of Phase 5.3:**
- Normalized artifact contract
- `workspace_artifacts` migration
- Persistence against real execution context

**Constraint:** Do NOT touch frozen 5.2 runtime components.

---

*TORQ is on track for the end goal: true consulting operating system with traceable reasoning, persistent artifacts, and compounded knowledge.*
