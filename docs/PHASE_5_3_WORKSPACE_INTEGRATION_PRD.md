# PHASE 5.3: AGENT TOOL WORKSPACE INTEGRATION PRD

**TORQ Console**

---

## 1. Executive Summary

Phase 5.3 introduces a workspace artifact bridge that captures tool activity and persists normalized tool outputs into shared workspace context. The objective is to preserve continuity, traceability, and retrieval value across mission execution without changing the frozen Phase 5.2 Agent Teams runtime.

This phase is **additive**. It does not introduce a new runtime, a new team pattern, or a client-facing product layer. Instead, it connects tool execution to the same operational context already used by mission and team execution so artifacts can be inspected, replayed, and retrieved later.

---

## 2. Problem and Rationale

Agent Teams now produces stable, persisted reasoning traces, but tool activity can still become detached from the execution record. When tool output is not written into workspace context, TORQ loses:

- Continuity across execution steps
- Auditability and explainability
- Later memory and retrieval reliability
- Advisor- and client-facing explainability

---

## 3. Scope and Constraints

### In Scope

- Capture tool invocation metadata
- Normalize supported tool outputs into a consistent artifact contract
- Persist workspace-linked artifact records
- Link artifacts to mission, execution, team execution, role, and round context where applicable
- Provide read and inspection capability for later observability, memory, and retrieval use

### Out of Scope

- Changes to `AgentTeamOrchestrator`, `RoleRunner`, `DecisionEngine`, or existing Phase 5.2 behavior
- Client portal work, new end-user surfaces, or autonomous tool-planning changes
- Replacing existing team tables or mixing workspace artifacts with strategic memory logic too early

### Frozen Runtime Boundary

The following components remain **frozen** throughout Phase 5.3:

- `AgentTeamOrchestrator`
- `RoleRunner`
- `DecisionEngine`
- Phase 5.2 team runtime behavior
- Existing 5.2B observability contracts (unless extended in additive read-only way)

---

## 4. Target State Architecture

The target state is a thin artifact bridge between tool execution and shared workspace, allowing every supported tool output to become a first-class execution artifact.

```
Tool Invocation → Tool Output Adapter → Workspace Artifact Writer → Shared Workspace
                                                              ↓
                                              Execution / Team Context References
```

---

## 5. Workspace Scope Hierarchy

Artifacts should be written to the **narrowest relevant workspace scope** and only referenced upward when necessary:

```
workflow_execution:{execution_id}
team_execution:{team_execution_id}
team_round:{team_execution_id}:{round}
node_execution:{mission_id}:{node_id}
```

---

## 6. Data Model

Phase 5.3 adds a single minimal table, `workspace_artifacts`, that **complements** (not replaces) existing team and mission persistence.

### Table: `workspace_artifacts`

| Field | Type | Purpose |
|-------|------|---------|
| `id` | UUID | Primary key |
| `workspace_id` | UUID | Workspace reference |
| `mission_id` | UUID | Mission reference |
| `node_id` | UUID | Node reference |
| `execution_id` | UUID | Workflow execution reference |
| `team_execution_id` | UUID? | Nullable team execution reference |
| `round_number` | int? | Nullable round number |
| `role_name` | string? | Nullable invoking role |
| `tool_name` | string | Tool identifier |
| `artifact_type` | string | Artifact category |
| `title` | string | Human-readable title |
| `summary` | text | Short summary for retrieval and UI |
| `content_json` | jsonb | Structured artifact payload |
| `content_text` | text | Plain text representation |
| `source_ref` | string? | Optional source reference |
| `created_at` | timestamp | Creation time |

---

## 7. Module Layout

Fit inside the existing workspace package:

```
torq_console/workspace/
  artifact_models.py       # Pydantic models
  artifact_persistence.py  # Supabase operations
  artifact_service.py      # Business logic
  artifact_adapter.py      # Tool output normalization
  artifact_api.py          # FastAPI endpoints
```

---

## 8. Implementation Milestones

### Milestone 1 - Tool Output Contract

**Build:** `artifact_adapter.py`, normalized artifact schema, artifact typing rules

**Acceptance:** Tool output from supported tools can be normalized into one structure carrying execution and workspace linkage metadata.

### Milestone 2 - Workspace Artifact Persistence

**Build:** `workspace_artifacts` migration, persistence service, additive repository methods

**Acceptance:** Tool outputs persist successfully, write ordering is preserved, artifacts associated with correct workspace scope.

### Milestone 3 - Execution and Team Context Linking

**Build:** Lightweight integration points around tool execution, context-aware scope selection

**Acceptance:** Team execution produces workspace-linked artifacts traceable to mission, node, role, and round without changing frozen runtime behavior.

### Milestone 4 - Read and Inspection Layer

**Build:** Artifact list and detail access for workspace, execution, and team execution contexts

**Acceptance:** Artifacts can be queried reliably and reused later by observability, retrieval, and memory layers.

### Milestone 5 - Validation and Hardening

**Build:** Ordering, deduplication, replay, concurrency behavior, and regression safety tests

**Acceptance:** No regression in 5.2A or 5.2B, no duplicate artifacts, correct scope assignment, stable concurrent writes, historical replay works.

---

## 9. Test Plan

| Test Type | Checks | Expected Result |
|-----------|--------|------------------|
| Functional | Single tool output persists; team-linked output persists; round-linked artifact persists to correct scope | Correct artifact records written with complete linkage metadata |
| Integration | Mission execution with tool usage writes workspace artifacts; team execution with tool usage writes artifacts without runtime drift | Artifacts linked to execution context, no runtime changes |
| Concurrency | Multiple simultaneous tool outputs do not duplicate; ordering remains correct under concurrent writes | No orphaned artifacts, ordering preserved |
| Regression | Rerun 5.2A; rerun 5.2B; run workspace artifact integration suite | No regression in frozen components |

---

## 10. GitHub Checkpoint Strategy

```
feat(workspace): add tool output artifact contract
feat(workspace): persist tool outputs into shared workspace
feat(workspace): link tool artifacts to execution and team context
feat(workspace): add workspace artifact inspection endpoints
test(workspace): validate artifact persistence ordering and regression safety
```

---

## 11. Risks and Guardrails

- ❌ Do not allow raw, tool-specific payloads to write directly into workspace without normalization
- ❌ Do not couple workspace artifacts too tightly to a single tool type or provider
- ❌ Do not modify frozen team runtime to "support" this phase; integration must remain additive
- ❌ Do not mix workspace artifact storage with memory logic before validation is complete
- ❌ Do not expose unfinished artifacts to UI before persistence and ordering are proven

---

## 12. Definition of Done

Phase 5.3 is complete when:

- ✅ `workspace_artifacts` exists in Supabase and is writing correctly
- ✅ Supported tool outputs normalize into a single artifact shape
- ✅ Artifacts link correctly to mission, node, execution, team execution, role, and round context where applicable
- ✅ Artifact ordering is preserved and duplicate writes are prevented
- ✅ Read and inspection capability works reliably
- ✅ Phase 5.2A and 5.2B regressions remain green

---

## Appendix A: Architectural Progression

```
structured team execution (5.2) ✅
        ↓
workspace-linked artifact continuity (5.3) 📋
        ↓
memory / retrieval / insight compounding (5.4+) 📝
```

---

## Appendix B: Source Baseline

| Previous Phase | Phase 5.2 Agent Teams |
|---|---|
| **Goal** | Make tool outputs first-class workspace artifacts without changing the validated runtime |
| **Primary Deliverables** | Artifact contract, workspace_artifacts migration, persistence, context linking, inspection APIs |
| **Outcome** | Traceable, retrievable tool outputs linked to mission, node, team, and round context |
