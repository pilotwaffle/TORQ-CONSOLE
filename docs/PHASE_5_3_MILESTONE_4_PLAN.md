# Phase 5.3 Milestone 4: Read and Inspection Layer

**Date:** 2026-03-10
**Status:** COMPLETE - VALIDATED (15/15 tests passing)

---

## Goal

Expose persisted workspace artifacts through a read and inspection layer so TORQ can inspect, filter, and trace execution artifacts before full hardening.

---

## Context

Milestone 4 builds on:
- **Milestone 1**: Tool output normalization into artifact contract
- **Milestone 2**: Workspace artifact persistence
- **Milestone 3**: Execution and team context linking

Now that artifacts are being captured and persisted with full context, we need the ability to **query, inspect, and verify** those artifacts cleanly.

---

## Scope

### In Scope

- Artifact retrieval API with multiple query paths
- Traceability view model for clean inspection
- Minimal inspection UI
- Historical inspection support
- No changes to capture behavior

### Out of Scope

- Full polished artifact explorer (deferred to future)
- Modifying frozen 5.2 components
- Changing capture behavior unless required for read correctness

---

## Implementation Plan

### 1. Artifact Retrieval API

**File:** `workspace/artifact_read_service.py`

Add read endpoints for the most useful inspection paths:

**By:** `workspace_id`, `execution_id`, `mission_id`, `node_id`, `team_execution_id`, `artifact_type`

**Features:**
- Pagination (`limit`, `offset`)
- Sort by `created_at` (desc/asc)
- Optional filters for `role_name` and `round_number`

### 2. Artifact Detail Endpoint

One endpoint that returns the full artifact record:

- Metadata
- Summary
- Content payload (`content_json`, `content_text`)
- Traceability fields
- Timestamps
- Source tool info

### 3. Traceability View Model

**File:** `workspace/artifact_view_models.py`

Do not expose raw persistence objects directly. Create a thin read model:

```
workspace → mission → node → execution → team → role/round → artifact
```

This makes both debugging and future UI cleaner.

### 4. Minimal Inspection UI

**Files:** `frontend/src/features/workspace/components/`

Keep it light for now:

- `ArtifactListPanel.tsx` - Artifact list panel
- `ArtifactDetailDrawer.tsx` - Artifact detail drawer
- `ArtifactFilterControls.tsx` - Filter controls
- `TraceabilitySummary.tsx` - Traceability summary block

### 5. Historical Inspection Support

Make sure the read layer works for completed executions, not only live ones.

This matters because this layer is a bridge to:
- Memory validation
- Insight publishing
- Pattern aggregation

---

## Data Flow

```
User Request
    ↓
[ArtifactReadService.list_artifacts()]
    ↓
[Build query from params]
    ↓
[Supabase query with filters]
    ↓
[Map to TraceabilityViewModel]
    ↓
[Return paginated results]
```

---

## API Endpoints

### List Artifacts

```python
GET /api/workspace/artifacts

Query params:
- workspace_id: UUID (required)
- execution_id?: str
- mission_id?: UUID
- node_id?: UUID
- team_execution_id?: UUID
- artifact_type?: str
- role_name?: str
- round_number?: int
- limit?: int (default 50, max 100)
- offset?: int (default 0)
- sort?: "created_at:desc" | "created_at:asc" (default desc)

Response:
{
  "artifacts": TraceabilityViewModel[],
  "total_count": int,
  "limit": int,
  "offset": int
}
```

### Get Artifact Detail

```python
GET /api/workspace/artifacts/{artifact_id}

Response:
{
  "artifact": ArtifactDetailViewModel,
  "traceability": TraceabilityChainViewModel
}
```

---

## View Models

### TraceabilityViewModel

```python
class TraceabilityViewModel(BaseModel):
    """Clean read model for artifact inspection."""

    # Identification
    id: UUID
    artifact_type: str
    title: str
    summary: str
    created_at: datetime

    # Traceability chain
    workspace_id: UUID
    mission_id: Optional[UUID]
    node_id: Optional[UUID]
    execution_id: Optional[str]
    team_execution_id: Optional[UUID]
    round_number: Optional[int]
    role_name: Optional[str]

    # Tool info
    tool_name: str

    # Quick stats
    has_content: bool
    content_type: str  # "json", "text", "mixed"
```

### ArtifactDetailViewModel

```python
class ArtifactDetailViewModel(BaseModel):
    """Full artifact detail for inspection."""

    # All traceability fields
    traceability: TraceabilityViewModel

    # Content
    content_json: Dict[str, Any]
    content_text: str

    # Execution metadata
    execution_metadata: ToolExecutionMetadata

    # Source reference
    source_ref: Optional[str]
```

### TraceabilityChainViewModel

```python
class TraceabilityChainViewModel(BaseModel):
    """Shows the full chain from workspace to artifact."""

    workspace: Optional[WorkspaceRef]
    mission: Optional[MissionRef]
    node: Optional[NodeRef]
    execution: Optional[ExecutionRef]
    team: Optional[TeamRef]
    artifact: ArtifactRef
```

---

## Validation Criteria

After Milestone 4, we must demonstrate:

1. **Artifacts can be listed by workspace/execution/team**
   - Query by workspace_id returns all artifacts for that workspace
   - Query by execution_id returns all artifacts for that execution
   - Query by team_execution_id returns all artifacts for that team

2. **Artifact detail loads correctly**
   - GET /artifacts/{id} returns full artifact record
   - All fields populated correctly

3. **Filters work**
   - artifact_type filter returns correct subset
   - role_name filter works
   - round_number filter works
   - Combined filters work (AND logic)

4. **Traceability chain is visible**
   - ViewModel shows complete chain
   - Each link in chain has correct IDs

5. **Historical artifacts are inspectable**
   - Can query artifacts from completed executions
   - Pagination works for large result sets

6. **No regression in 5.2 or 5.3 M1-M3**
   - Milestones 1-3 tests still pass
   - Team execution still works
   - Artifact capture still works

---

## Files to Create

| File | Purpose |
|------|---------|
| `workspace/artifact_read_service.py` | Read service for artifact queries |
| `workspace/artifact_view_models.py` | View models for clean API |
| `workspace/api/artifacts.py` | FastAPI router for artifact endpoints |
| `scripts/test_phase_5_3_milestone_4.py` | Validation tests |
| `frontend/src/features/workspace/components/ArtifactListPanel.tsx` | List component |
| `frontend/src/features/workspace/components/ArtifactDetailDrawer.tsx` | Detail component |
| `frontend/src/features/workspace/components/ArtifactFilterControls.tsx` | Filter component |
| `frontend/src/features/workspace/components/TraceabilitySummary.tsx` | Traceability component |

---

## Files to Modify

| File | Change |
|------|--------|
| `workspace/__init__.py` | Add read service exports |
| `workspace/api/__init__.py` | Include artifacts router |
| `frontend/src/features/workspace/api/index.ts` | Export artifact APIs |

---

## Testing Strategy

### Unit Tests

1. Read service queries by each filter
2. Pagination works correctly
3. Sorting works correctly
4. View models serialize correctly

### Integration Tests

1. List artifacts by workspace
2. List artifacts by execution
3. List artifacts by team
4. Get artifact detail
5. Filter combinations work
6. Historical queries work

### Regression Tests

1. Phase 5.3 M1-M3 tests still pass
2. Phase 5.2 team execution still works

---

## Definition of Done

Milestone 4 is complete when:

- [ ] Artifact read service created
- [ ] Traceability view models created
- [ ] List API endpoint works with all filters
- [ ] Detail API endpoint works
- [ ] Pagination and sorting work
- [ ] Minimal UI components created
- [ ] All validation tests pass
- [ ] No regression in 5.2 or 5.3 M1-M3
- [ ] Code committed

---

## Next: Milestone 5

After Milestone 4, move to **Validation and Hardening**:

- Concurrency testing
- Duplicate prevention validation
- Scope correctness validation
- Ordering validation
- Regression reruns
- Failure-path tests
- Non-blocking capture tests under load

That is the point where 5.3 becomes truly complete.
