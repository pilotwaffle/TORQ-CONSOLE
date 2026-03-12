# Next Build Session: Phase 5.3 Milestones 1 & 2

**Date:** 2026-03-09
**Status:** Ready to start

---

## Opening Prompt

> Implement Phase 5.3 Milestones 1 and 2 only.
>
> **Scope:**
> - Normalized artifact contract
> - workspace_artifacts migration
> - Persistence against real execution context
>
> **Constraints:**
> - Do NOT modify AgentTeamOrchestrator
> - Do NOT modify RoleRunner
> - Do NOT modify DecisionEngine
> - Do NOT modify existing 5.2 persistence schema except additive workspace integration
> - Keep all changes additive and testable
>
> **Acceptance:**
> - Tool outputs normalize into a single artifact shape
> - Artifacts persist into the correct workspace scope
> - Artifacts link to mission/execution/team context where applicable
> - No regression in 5.2A or 5.2B

---

## Frozen Components (DO NOT CHANGE)

```
torq_console/teams/
├── orchestrator.py      # LOCKED
├── role_runner.py       # LOCKED
├── decision.py          # LOCKED
└── models.py            # LOCKED
```

---

## Target Checkpoint

Milestones 1 & 2 complete when:

- ✅ Migration created and applied
- ✅ `workspace_artifacts` table live in Supabase
- ✅ Artifact adapter normalizing outputs successfully
- ✅ Persistence layer writing artifacts correctly
- ✅ At least one real execution writing a workspace artifact
- ✅ No regression in Agent Teams runtime
- ✅ Clean commit for Milestones 1 and 2

---

## Implementation Order

1. **Milestone 1: Tool Output Contract**
   - Create `artifact_models.py` - Pydantic models for normalized artifacts
   - Create `artifact_adapter.py` - Tool output normalization
   - Define `WorkspaceArtifact` schema
   - Test: Tool outputs normalize into single shape

2. **Milestone 2: Workspace Artifact Persistence**
   - Create migration for `workspace_artifacts` table
   - Create `artifact_persistence.py` - Supabase operations
   - Create `artifact_service.py` - Business logic
   - Test: Artifacts persist, link to context, no regression

3. **DO NOT PROCEED TO** Milestone 3, 4, or 5 in this session
   - Keep scope narrow
   - Get artifacts flowing first
   - Read/inspection comes later

---

## What "Good" Looks Like

End of session checkpoint:

```
✅ workspace_artifacts migration applied to Supabase
✅ WorkspaceArtifact model defined
✅ ToolOutputAdapter normalizes Claude/tool outputs
✅ WorkspaceArtifactPersistence writes to database
✅ At least 1 execution produces artifact
✅ 5.2A regression passes
✅ 5.2B integration test passes
✅ Clean commit: "feat(workspace): milestones 1-2 artifact contract and persistence"
```

---

## Files to Create

```
torq_console/workspace/
  artifact_models.py       # Pydantic models (WorkspaceArtifact, ArtifactType, etc.)
  artifact_adapter.py      # Tool output normalization (ToolOutputAdapter)
  artifact_persistence.py  # Supabase operations (WorkspaceArtifactPersistence)
  artifact_service.py      # Business logic (WorkspaceArtifactService)
```

---

## Files to Modify

```
migrations/
  0XX_workspace_artifacts.sql  # New migration

torq_console/workspace/__init__.py  # Export new classes
```

---

## Files NOT to Modify

```
torq_console/teams/orchestrator.py  # LOCKED
torq_console/teams/role_runner.py    # LOCKED
torq_console/teams/decision.py       # LOCKED
torq_console/teams/persistence.py    # LOCKED (additive only)
```

---

## First Implementation Pass

**Keep it narrow:** Focus on artifact contract + persistence only.

**Do NOT add in this session:**
- Read endpoints
- API routes
- UI components
- Memory integration

Those come in Milestones 3 & 4.

---

## Regression Safety

Before committing, run:

```bash
# 5.2A regression
python scripts/test_phase_5_2_activation.py

# 5.2B integration
TORQ_API_URL=http://localhost:8900 python scripts/test_phase_5_2b_integration.py
```

Both must pass.

---

## Reference Docs

- `docs/PHASE_5_3_WORKSPACE_INTEGRATION_PRD.md` - Full PRD
- `docs/PHASE_5_2_COMPLETE.md` - Frozen baseline documentation
- `docs/ROADMAP_STATUS.md` - Overall roadmap

---

*Discipline preserves value. Narrow scope, validate, then extend.*
