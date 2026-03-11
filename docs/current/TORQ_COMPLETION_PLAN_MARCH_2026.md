# TORQ Completion Plan - March 2026

**Goal**: Finish the kernel and intelligence substrate, not the final end-user platform.

**By month-end, the win is**:
- Agent Teams complete (✅ 5.2A done, 5.2B remaining)
- Observability complete
- Workspace continuity complete
- Governed memory complete
- Reusable insights complete
- Pattern intelligence underway or complete

---

## Execution Order (Locked)

### 1️⃣ Phase 5.2A — Agent Teams Runtime ✅ COMPLETE

**Status**: PRODUCTION-READY, COMMITTED
**Commit**: `294258fc`
**Validation**:
- Initial activation: 5/5 checks passed
- Production readiness: 5/5 executions, σ=0.005
- Concurrent stress test: 20/20 simultaneous, zero failures

**Runtime Freeze**: The following components are FROZEN:
- `AgentTeamOrchestrator`
- `RoleRunner`
- `DecisionEngine`
- `TeamPersistence` (schema and code)
- `TeamContextManager`

**Next**: Phase 5.2B builds observability ONLY around these frozen components.

---

### 2️⃣ Phase 5.2B — Agent Teams Observability + UI

**Status**: 🔜 START NEXT
**Scope**: ONLY observability—no runtime changes

#### Features

**Feature 1 — SSE Event Streaming**
- Endpoint: `/api/teams/executions/{id}/events/stream`
- Events:
  - `TEAM_EXECUTION_STARTED`
  - `TEAM_ROUND_STARTED`
  - `ROLE_EXECUTED`
  - `CRITIQUE_SUBMITTED`
  - `VALIDATOR_DECISION`
  - `TEAM_DECISION_FINALIZED`

**Feature 2 — Round Visualization**
- Round-by-round progress display
- Role interaction timeline

**Feature 3 — Per-Role Confidence**
- Internal confidence weights exposed
- Lead, Researcher, Critic, Validator breakdown

**Feature 4 — Team Timeline**
- Timestamped event sequence
- 00:00 team created → 00:07 final synthesis

**Feature 5 — Control Surface Card**
- Team execution status panel
- Role completion checkboxes
- Final confidence display

#### Success Criteria
- [ ] SSE events stream correctly for live executions
- [ ] Control surface shows team execution card
- [ ] Round-by-round progress visible
- [ ] Per-role confidence exposed
- [ ] Timeline visible and accurate
- [ ] Event telemetry recorded

#### Regression Test
- [ ] All 5.2A tests still pass
- [ ] Concurrent stress test still passes
- [ ] No runtime behavior changes

#### Commit Target
```
feat(agent-teams): add phase 5.2b observability and control surface ui
```

---

### 3️⃣ Agent Tool Workspace Integration

**Status**: ⏳ PENDING
**Why this comes next**: Strengthens continuity, traceability, and shared context without forcing a redesign.

#### Scope
- [ ] Connect tools into shared workspace scopes
- [ ] Ensure tool outputs persist alongside agent outputs
- [ ] Make workspace linkage first-class
- [ ] Preserve auditability

#### Success Criteria
- [ ] Tool invocation can write to workspace
- [ ] Team executions can reference tool artifacts
- [ ] Workspace history is queryable and stable
- [ ] No breakage to frozen agent-team runtime

#### Commit Target
```
feat(workspace): integrate agent tool outputs into shared workspace context
```

---

### 4️⃣ Phase 4H.1 — Strategic Memory Validation & Control

**Status**: ⏳ PENDING
**Why this comes before insight publishing**: You want memory to be governed before you amplify it.

#### Scope
- [ ] Memory validation rules
- [ ] Retrieval confidence controls
- [ ] Stale/invalid memory rejection
- [ ] Memory auditability
- [ ] Policy guardrails on carry-forward use

#### Success Criteria
- [ ] Memory retrieval is controlled and explainable
- [ ] Low-quality or stale memory can be filtered
- [ ] Memory writes and reads are inspectable

#### Commit Target
```
feat(memory): add strategic memory validation and control layer
```

---

### 5️⃣ Insight Publishing & Agent Retrieval

**Status**: ⏳ PENDING
**Why this comes after workspace + memory**: Works best after continuity and controls are in place.

#### Scope
- [ ] Publish insights as reusable artifacts
- [ ] Make insights retrievable by agents
- [ ] Connect reports/findings to mission history
- [ ] Build retrieval paths for prior outputs

#### Success Criteria
- [ ] Agents can retrieve prior published insights
- [ ] Published outputs improve future runs
- [ ] Retrieval stays governed by memory controls

#### Commit Target
```
feat(insights): add insight publishing and agent retrieval pipeline
```

---

### 6️⃣ Phase 4G — Pattern Aggregation

**Status**: ⏳ PENDING
**Why this comes last**: Works best after you have enough stabilized history, memory controls, and published insight artifacts.

#### Scope
- [ ] Recurring execution pattern detection
- [ ] Successful reasoning path recognition
- [ ] Reusable workflow templates
- [ ] Failure pattern detection

#### Success Criteria
- [ ] TORQ can identify repeatable high-value patterns
- [ ] Successful execution structures can be reused
- [ ] Recurring failure modes become visible

#### Commit Target
```
feat(patterns): add phase 4g pattern aggregation and reusable execution insights
```

---

### 7️⃣ Observation Mode Readiness Checker

**Status**: ⏳ PENDING (lower priority)
**Why this is less urgent**: Only needed before expanding automation authority.

#### Scope
- [ ] Readiness criteria definition
- [ ] Observation → active transition checks
- [ ] Governance thresholds
- [ ] Safety and validation gates

#### Commit Target
```
feat(governance): add observation mode readiness checker
```

---

## GitHub Milestone Pushes

**Do NOT do one giant push. Push milestone slices in order.**

1. ✅ `feat(agent-teams): complete phase 5.2a runtime activation` — DONE
2. 🔜 `feat(agent-teams): add phase 5.2b observability and control surface ui`
3. ⏳ `feat(workspace): integrate agent tool outputs into shared workspace context`
4. ⏳ `feat(memory): add strategic memory validation and control layer`
5. ⏳ `feat(insights): add insight publishing and agent retrieval pipeline`
6. ⏳ `feat(patterns): add phase 4g pattern aggregation and reusable execution insights`
7. ⏳ `feat(governance): add observation mode readiness checker`

**This gives you clean rollback points and clean release notes.**

---

## What NOT To Do Right Now

**Do NOT start**:
- Phase 6 architecture implementation
- Client portal
- Document intelligence pipeline
- Dynamic team creation
- New team patterns
- Advisor/client UX expansion beyond current 5.2B observability scope

**Those are important, but they come after this sequence is closed.**

---

## Current Task Queue

1. 🔜 Phase 5.2B — Observability + UI
2. ⏳ Agent Tool Workspace Integration
3. ⏳ Phase 4H.1 — Strategic Memory Validation & Control
4. ⏳ Insight Publishing & Agent Retrieval
5. ⏳ Phase 4G — Pattern Aggregation
6. ⏳ Observation Mode Readiness Checker

---

## Telemetry to Track (Starting 5.2B)

```python
team_round_count              # Confirmed stable at 3
team_confidence_score         # Confirmed stable at ~0.83
validator_block_rate          # Currently 0%
team_execution_duration       # Confirmed stable ~11-12s
team_message_count            # Confirmed stable at 15
critique_modification_rate    # NEW - measures critique effectiveness
```

These metrics will enable Phase 5.3's adaptive team composition.

---

## Month-End Goal

**By end of March, TORQ will have**:

✅ Agent Teams complete (5.2A + 5.2B)
✅ Observability complete
✅ Workspace continuity complete
✅ Governed memory complete
✅ Reusable insights complete
✅ Pattern intelligence underway or complete

**That creates the right foundation for building the better end-user experience.**

---

## Status Summary

| Milestone | Status | Commit |
|-----------|--------|--------|
| Phase 5.2A Runtime | ✅ COMPLETE | `294258fc` |
| Phase 5.2B Observability | 🔜 NEXT | — |
| Workspace Integration | ⏳ PENDING | — |
| Memory Validation | ⏳ PENDING | — |
| Insight Publishing | ⏳ PENDING | — |
| Pattern Aggregation | ⏳ PENDING | — |
| Readiness Checker | ⏳ PENDING | — |
