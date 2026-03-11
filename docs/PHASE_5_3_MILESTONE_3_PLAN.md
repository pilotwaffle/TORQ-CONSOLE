# Phase 5.3 Milestone 3: Execution and Team Context Linking

**Date:** 2026-03-10
**Status:** COMPLETE - VALIDATED (8/8 tests passing)

---

## Goal

Link workspace artifacts to their execution context so that tool outputs can be traced from workspace → execution → node → team → role/round.

This is the "continuity layer" that gives artifacts meaning beyond being stored data.

---

## Scope

### In Scope

- Link artifacts to mission execution
- Link artifacts to node execution
- Link artifacts to team execution when present
- Link artifacts to round and role where applicable
- Preserve scope hierarchy cleanly
- Create context linker service for non-blocking artifact capture
- No changes to frozen runtime components

### Out of Scope

- Read/inspection endpoints (Milestone 4)
- Advanced validation and hardening (Milestone 5)
- Modifying AgentTeamOrchestrator, RoleRunner, or DecisionEngine

---

## Implementation Plan

### 1. Create Context Linker Service

**File:** `workspace/artifact_context_linker.py`

The context linker provides:
- `capture_node_tool_execution()` - Capture artifacts during node execution
- `capture_role_output()` - Capture artifacts during team role execution
- `capture_team_decision()` - Capture team decisions as artifacts
- Non-blocking design (errors don't fail execution)
- Enable/disable control for testing

### 2. Integration Points

The context linker will be integrated at:
- **Node execution** - Wrap tool calls in node_runner.py
- **Team execution** - Wrap role calls in orchestrator.py
- **Decision synthesis** - Wrap decision output in decision_engine.py

**Key Design Principle:** All integration is done via **wrapping/decoration**, not modifying frozen core logic.

### 3. Execution Context Structure

The execution context passed to artifact capture includes:

```python
{
    # Mission context
    "mission_id": UUID,
    "node_id": UUID,

    # Execution context
    "execution_id": str,

    # Team context (when present)
    "team_execution_id": UUID,
    "round_number": int,
    "role_name": str,

    # Timing
    "started_at": datetime,
    "success": bool,
    "error_message": str | None,

    # Trace
    "trace_id": str,
}
```

---

## Data Flow

```
Mission Execution
    ↓
[creates workspace]
    ↓
Node Execution (with tool)
    ↓
[ContextLinker.capture_node_tool_execution]
    ↓
[Tool Output → Normalized Artifact → workspace_artifacts table]
    ↓
    ↓ (if team node)
Team Execution
    ↓
[ContextLinker.capture_role_output]
    ↓
[Role Output → Normalized Artifact → workspace_artifacts table]
    ↓
Team Decision
    ↓
[ContextLinker.capture_team_decision]
    ↓
[Decision → Normalized Artifact → workspace_artifacts table]
```

---

## Validation Criteria

After Milestone 3, we must demonstrate:

1. **At least one real mission execution writing workspace artifacts**
   - Run a simple mission through the execution fabric
   - Verify artifacts appear in workspace_artifacts table

2. **At least one team-linked artifact persisted with execution metadata**
   - Execute a team node
   - Verify team_execution_id, round_number, role_name are set

3. **Correct workspace scope assignment**
   - Artifacts in correct workspace
   - No artifacts without workspace_id

4. **Round/role metadata when relevant**
   - Role artifacts have role_name
   - Team artifacts have round_number

5. **No regression in 5.2**
   - Team execution still works
   - Mission execution still works

6. **No artifact duplication**
   - Same tool output not stored twice
   - Idempotent capture logic

---

## Files to Create

| File | Purpose |
|------|---------|
| `workspace/artifact_context_linker.py` | Context linker service |
| `scripts/test_phase_5_3_milestone_3.py` | Validation tests |
| `docs/PHASE_5_3_MILESTONE_3_COMPLETE.md` | Completion status |

---

## Files to Modify

| File | Change Type | Notes |
|------|-------------|-------|
| `workspace/__init__.py` | Add exports | Export context linker |

---

## Testing Strategy

### Unit Tests

1. Context linker captures node artifacts correctly
2. Context linker captures role artifacts correctly
3. Context linker captures team decisions correctly
4. Non-blocking behavior (errors don't stop execution)
5. Enable/disable control works

### Integration Tests

1. Mission execution produces artifacts
2. Team execution produces role artifacts
3. Team decision produces decision artifact
4. Artifact traceability chain works (workspace → execution → node → team → role)

### Regression Tests

1. Phase 5.2A team runtime still works
2. Phase 5.2B observability still works
3. Mission execution still works without workspace

---

## Definition of Done

Milestone 3 is complete when:

- [x] Context linker service created
- [x] At least one mission execution writes workspace artifacts
- [x] Team-linked artifacts persist with execution metadata
- [x] Correct workspace scope assignment
- [x] Round/role metadata preserved when relevant
- [x] No regression in 5.2
- [x] No artifact duplication
- [x] All validation tests pass (8/8 passing)
- [ ] Code committed (pending)

---

## Next: Milestone 4

After Milestone 3, we move to **Read and Inspection Layer**:
- API endpoints for artifact retrieval
- Filtering by workspace, execution, team, type
- Artifact inspection UI components
- Traceability view (showing the full chain)
