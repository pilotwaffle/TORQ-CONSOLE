# Agent Tool Workspace Integration — Implementation Plan

**Phase:** 5.3 - Workspace Integration
**Previous:** Phase 5.2 Agent Teams (COMPLETE)
**Goal:** Route tool outputs into shared workspace context for traceability

---

## Executive Summary

Make tool outputs first-class workspace artifacts without changing the validated Agent Teams runtime.

**Problem:** Tool usage is not consistently written into workspace context, losing continuity and traceability.

**Solution:** Add an additive workspace artifact bridge between tool execution and shared workspace.

**Outcome:** Tool outputs are persisted, linked to execution context, and retrievable for later inspection.

---

## Goal

Route tool activity and tool outputs into the shared workspace context so missions, teams, and later memory/retrieval layers can reference the same execution artifacts.

This is not a new runtime. It is a traceability and continuity layer added around the existing system.

---

## Why This Is The Right Next Step

Now that Agent Teams is complete, the next bottleneck is that reasoning and tool usage can become separated.

If tool outputs are not consistently written into workspace context, you lose:
- Continuity across execution steps
- Artifact traceability
- Clean audit history
- Later retrieval value
- Stronger advisor/client-facing explainability

---

## Scope

### In Scope
- Capture tool invocation metadata
- Persist tool outputs into workspace-linked records
- Link tool artifacts to mission execution and team execution context
- Expose workspace-linked tool artifacts for later retrieval and inspection
- Preserve ordering and traceability

### Out of Scope
- Changing AgentTeamOrchestrator logic
- Changing RoleRunner decision behavior
- Changing DecisionEngine
- Changing team persistence schema unless additive and isolated
- Client portal or new end-user surfaces
- Autonomous tool planning changes

---

## Constraints

**Frozen components remain frozen:**
- `AgentTeamOrchestrator`
- `RoleRunner`
- `DecisionEngine`
- Phase 5.2 team runtime behavior
- Existing 5.2B observability contracts (unless extended read-only later)

This integration must be **additive, not invasive**.

---

## Desired Outcome

```
Mission / Team Execution
        ↓
Agent reasons
        ↓
Tool invoked
        ↓
Tool output persisted to workspace
        ↓
Workspace artifact linked to execution context
        ↓
Future steps can inspect, cite, or retrieve artifact
```

---

## Architecture

### Core Idea

Introduce a workspace artifact bridge between tool execution and shared workspace.

```
Tool Invocation
      ↓
Tool Output Adapter
      ↓
Workspace Artifact Writer
      ↓
Shared Workspace
      ↓
Execution / Team Context References
```

### New Responsibilities

**Tool Output Adapter**
Normalizes tool results into a consistent shape:
- `tool_name`
- `invocation_id`
- `execution_id` / `mission_id` / `node_id`
- `team_execution_id` (if present)
- `role_name` (if present)
- `artifact_type`
- `summary`
- `raw_output` reference
- `created_at`

**Workspace Artifact Writer**
Writes normalized tool artifacts into the proper workspace scope.

**Workspace Context Linker**
Associates artifacts to:
- Workflow execution
- Team execution
- Team round (if applicable)
- Node execution

---

## Workspace Scope Hierarchy

Use the existing pattern and extend carefully:

```
workflow_execution:{execution_id}
team_execution:{team_execution_id}
team_round:{team_execution_id}:{round}
node_execution:{mission_id}:{node_id}
```

Tool outputs should be written to the **narrowest relevant scope** and optionally referenced upward.

---

## Data Model Additions

### New Table: `workspace_artifacts`

Keep minimal and additive.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `workspace_id` | UUID | Workspace reference |
| `mission_id` | UUID | Mission reference |
| `node_id` | UUID | Node reference |
| `execution_id` | UUID | Workflow execution reference |
| `team_execution_id` | UUID | Team execution reference (nullable) |
| `round_number` | int | Round number (nullable) |
| `role_name` | string | Role that invoked tool (nullable) |
| `tool_name` | string | Tool identifier |
| `artifact_type` | string | Type of artifact |
| `title` | string | Artifact title |
| `summary` | text | Short summary |
| `content_json` | jsonb | Structured content |
| `content_text` | text | Plain text content |
| `source_ref` | string | Reference to source (nullable) |
| `created_at` | timestamp | Creation time |

**Note:** This complements, not replaces, existing team tables.

---

## Implementation Milestones

### Milestone 1 — Tool Output Contract

Build a normalized internal contract for tool outputs.

**Deliverables:**
- `artifact_adapter.py` or equivalent
- Normalized artifact schema
- Artifact typing rules

**Acceptance:**
- Tool output from supported tools can be normalized
- Structure includes execution and workspace linkage metadata

### Milestone 2 — Workspace Artifact Persistence

Build the persistence layer that writes artifacts to workspace context.

**Deliverables:**
- `workspace_artifacts` migration
- Persistence service
- Additive repository methods

**Acceptance:**
- Tool outputs persist successfully
- Artifacts associated with correct workspace scope
- Write ordering is preserved

### Milestone 3 — Execution/Team Context Linking

Connect tool artifacts to mission and team context without changing frozen team runtime.

**Deliverables:**
- Lightweight integration points around tool execution
- Context-aware scope selection
- Optional role/round tagging

**Acceptance:**
- Team execution produces workspace-linked artifacts
- Artifacts traceable to mission, node, role, and round

### Milestone 4 — Read/Inspection Layer

Add read APIs to inspect workspace artifacts.

**Deliverables:**
- `GET /workspace/artifacts`
- `GET /workspace/artifacts/{execution_id}`
- `GET /workspace/artifacts/teams/{team_execution_id}`
- `GET /workspace/artifacts/{id}`

**Acceptance:**
- Artifacts can be queried reliably
- Data usable by observability, retrieval, and memory

### Milestone 5 — Validation and Hardening

Test correctness, ordering, and regression safety.

**Acceptance:**
- No regression in 5.2A / 5.2B
- No duplicate artifacts
- Correct scope assignment
- Concurrent writes remain stable
- Historical artifact replay works

---

## Recommended Module Layout

```
torq_console/workspace/
  artifact_models.py       # Pydantic models
  artifact_persistence.py  # Supabase operations
  artifact_service.py      # Business logic
  artifact_adapter.py      # Tool output normalization
  artifact_api.py          # FastAPI endpoints
```

Fit into existing workspace package rather than creating parallel architecture.

---

## Acceptance Criteria

Phase complete when:
- ✅ Tool outputs persist into shared workspace context
- ✅ Artifacts link correctly to execution and team context
- ✅ Artifact ordering is preserved
- ✅ Duplicate artifact writes are prevented
- ✅ Artifacts can be read back reliably
- ✅ 5.2A and 5.2B regressions remain green
- ✅ Concurrency behavior remains stable

---

## Test Plan

### Functional Tests
- Single tool output persists to workspace
- Team-linked tool output persists with team metadata
- Round-linked artifact persists with correct scope

### Integration Tests
- Mission execution with tool usage writes workspace artifacts
- Team execution with tool usage writes artifacts without runtime drift
- Read APIs return expected artifact list and detail

### Concurrency Tests
- Multiple simultaneous tool outputs do not duplicate
- Ordering remains correct under concurrent writes
- No orphaned artifacts

### Regression Tests
- Rerun 5.2A activation test
- Rerun 5.2B integration test
- Run workspace artifact integration suite

---

## GitHub Checkpoint Strategy

```
feat(workspace): add tool output artifact contract
feat(workspace): persist tool outputs into shared workspace
feat(workspace): link tool artifacts to execution and team context
feat(workspace): add workspace artifact inspection endpoints
test(workspace): validate artifact persistence ordering and regression safety
```

---

## Best Build Order

1. Artifact contract
2. Persistence layer
3. Integration hook around tool execution
4. Read/inspection layer
5. Tests
6. Commit and push

---

## Risks To Avoid

- ❌ Letting tools write raw inconsistent payloads directly to workspace
- ❌ Coupling workspace artifacts too tightly to one tool type
- ❌ Modifying team runtime to "support" this when it should stay frozen
- ❌ Mixing artifact storage with memory logic too early
- ❌ Exposing unfinished artifacts to UI before validation

---

## Why This Matters

This phase is a **bridge phase** that strengthens:
- Traceability
- Continuity
- Later memory quality
- Insight publishing quality
- Future advisor/client explainability

Without this, TORQ can execute well but will have weaker knowledge continuity. With it, TORQ starts behaving more like a true consulting operating system.

---

## Bottom Line

**Next disciplined milestone:**

> Agent tool workspace integration = make tool outputs first-class workspace artifacts without changing the validated Agent Teams runtime.

**After this:**
> Strategic Memory Validation & Control
