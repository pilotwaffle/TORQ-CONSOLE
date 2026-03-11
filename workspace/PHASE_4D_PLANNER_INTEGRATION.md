# Phase 4D Milestone 2: Planning Copilot Writes Reasoning

## Status: ✅ COMPLETE

**Date:** 2026-03-08

## Executive Summary

The Planning Copilot now writes structured reasoning entries to the Shared Cognitive Workspace during workflow planning.

## Changes Made

### 1. Workflow Planner Service (`workflow_planner/service.py`)

**Added workspace integration:**
- New parameter: `workspace_service` in `__init__`
- Made `draft_workflow()` async to support workspace writes
- New method: `_write_planning_reasoning()` - async, writes 3 entry types

**Reasoning entries written:**
1. **Fact** (`user_request`): User's original prompt
2. **Decision** (`agent_selection`): Selected agent sequence with rationale
3. **Artifact** (`workflow_draft`): Generated workflow structure

### 2. Workflow Planner Models (`workflow_planner/models.py`)

**Added new request fields:**
```python
class WorkflowPlannerRequest(BaseModel):
    # ... existing fields ...
    workspace_id: Optional[str] = None  # Direct workspace target
    write_reasoning: bool = True  # Enable/disable reasoning writes
```

### 3. Workflow Planner API (`workflow_planner/api.py`)

**Updated for async:**
- Made `generate_workflow_draft()` endpoint async
- Added `set_workspace_service()` for dependency injection
- Wired up workspace_service from railway_app.py

### 4. Task Graph Engine (`tasks/graph_engine.py`)

**Added workspace creation on graph save:**
- New parameter: `workspace_service` in `__init__`
- Workspace created when graph is saved with `scope_type="workflow_graph"`
- Workspace ID persisted to `task_graphs` table

### 5. Task Graph Models (`tasks/models.py`)

**Added workspace_id field:**
```python
class TaskGraphResponse(BaseModel):
    # ... existing fields ...
    workspace_id: Optional[str] = None  # Linked workspace
```

### 6. Database Migration (`migrations/006_add_workspace_id_to_task_graphs.sql`)

**Added workspace_id column to task_graphs table:**
```sql
ALTER TABLE task_graphs ADD COLUMN IF NOT EXISTS workspace_id UUID;
CREATE INDEX idx_task_graphs_workspace_id ON task_graphs(workspace_id);
```

## Entry Types Created

| Entry Type | Category | Content | Purpose |
|------------|----------|---------|---------|
| **Fact** | `user_request` | User's prompt, session_id | Capture what was requested |
| **Decision** | `agent_selection` | Agent sequence, rationale | Explain why agents were chosen |
| **Artifact** | `workflow_draft` | Workflow name, nodes, structure | Capture generated design |

## User Flow

1. **User calls planner** with prompt and optional `session_id`
2. **Planner generates draft** and writes reasoning to session workspace
3. **User saves workflow** → creates graph with `workflow_graph:{graph_id}` workspace
4. **Execution** creates separate `workflow_execution:{execution_id}` workspace

## Scope Types

| Scope Type | Scope ID | Created By | Purpose |
|------------|----------|------------|---------|
| `session` | session_id | Planner API call | Multi-turn planning context |
| `workflow_graph` | graph_id | Graph save | Graph-level reasoning |
| `workflow_execution` | execution_id | Execution start | Runtime working memory |

## API Usage

```bash
# Plan a workflow (writes to session workspace)
POST /api/workflow-planner/draft
{
  "prompt": "Research AI market and create summary",
  "session_id": "user-session-123",
  "write_reasoning": true
}

# Save as graph (creates graph workspace)
POST /api/tasks/graphs
{
  "name": "Market Research",
  ...nodes from planner...
}

# Response includes workspace_id for graph
{
  "graph_id": "...",
  "workspace_id": "...",
  ...
}
```

## Verification Checklist

| Criterion | Status |
|-----------|--------|
| Planner accepts workspace_service | ✅ |
| Planner writes 3 entry types | ✅ |
| Graph creation creates workspace | ✅ |
| workspace_id persisted to database | ✅ |
| Async/await correctly implemented | ✅ |
| Non-blocking if workspace unavailable | ✅ |
| Migration created | ✅ |

## Next Steps (Milestone 3)

**Agent reasoning writes** - Start with two agents:

1. **Research Agent**:
   - Writes `fact` entries for discovered information
   - Writes `artifact` entries for gathered data

2. **Strategy Agent**:
   - Writes `hypothesis` entries for analysis
   - Writes `decision` entries for recommendations

---

**Phase 4D Milestone 2: COMPLETE** ✅

The Planning Copilot now provides instant explainability for workflow design decisions through structured workspace entries.
