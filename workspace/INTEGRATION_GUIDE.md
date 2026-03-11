# Shared Cognitive Workspace - Integration Guide

## Overview

The Shared Cognitive Workspace is TORQ's strategic differentiator for multi-agent collaboration. It provides a persistent working memory layer where agents can store and retrieve facts, hypotheses, questions, decisions, and artifacts.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     TORQ Console Frontend                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ Chat Window  │  │ Workspace    │  │ Execution Details    │ │
│  │              │  │ Inspector    │  │ (w/ Workspace Panel) │ │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘ │
│         │                  │                     │              │
│         └──────────────────┴─────────────────────┘              │
│                            │                                    │
└────────────────────────────┼────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     TORQ API Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ Chat API     │  │ Workspace    │  │ Workflow Execution   │ │
│  │              │  │ API          │  │ API                  │ │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘ │
└─────────┼──────────────────┼─────────────────────┼──────────────┘
          │                  │                     │
          └──────────────────┴─────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   PostgreSQL Database                            │
│  ┌──────────────────┐        ┌─────────────────────────────┐   │
│  │ workspaces       │        │ working_memory_entries      │   │
│  │ - workspace_id   │◄───────│ - memory_id                 │   │
│  │ - scope_type     │        │ - workspace_id (FK)         │   │
│  │ - scope_id       │        │ - entry_type                │   │
│  │ - title          │        │ - content (JSONB)           │   │
│  └──────────────────┘        │ - source_agent              │   │
│                              │ - confidence                 │   │
│                              └─────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Database Schema

### Workspaces Table
```sql
CREATE TABLE workspaces (
    workspace_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scope_type TEXT NOT NULL,  -- 'session', 'workflow_execution', 'agent_team'
    scope_id TEXT NOT NULL,
    title TEXT,
    description TEXT,
    created_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (scope_type, scope_id)
);
```

### Working Memory Entries Table
```sql
CREATE TABLE working_memory_entries (
    memory_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(workspace_id),
    entry_type TEXT NOT NULL,  -- 'fact', 'hypothesis', 'question', 'decision', 'artifact', 'note'
    content JSONB NOT NULL,
    source_agent TEXT,
    confidence FLOAT DEFAULT 0.8,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);
```

## API Endpoints

### Workspace Operations
- `POST /api/workspaces` - Create a new workspace
- `GET /api/workspaces/{workspace_id}` - Get workspace by ID
- `GET /api/workspaces/scope/{scope_type}/{scope_id}` - Get or create by scope

### Entry Operations
- `POST /api/workspaces/{workspace_id}/entries` - Add an entry
- `GET /api/workspaces/{workspace_id}/entries` - List all entries (grouped by type)
- `GET /api/workspaces/{workspace_id}/entries/{memory_id}` - Get specific entry
- `PATCH /api/workspaces/{workspace_id}/entries/{memory_id}` - Update entry
- `POST /api/workspaces/{workspace_id}/entries/{memory_id}/resolve` - Resolve a question
- `DELETE /api/workspaces/{workspace_id}/entries/{memory_id}` - Soft delete entry

### Summary
- `POST /api/workspaces/{workspace_id}/summarize` - Generate LLM summary

## Frontend Components

### WorkspaceInspector
```tsx
import { WorkspaceInspector } from '@/features/workspace';

<WorkspaceInspector
  scopeType="workflow_execution"
  scopeId={executionId}
  onClose={() => setShowWorkspace(false)}
/>
```

### React Query Hooks
```tsx
import {
  useWorkspace,
  useWorkspaceEntries,
  useAddFactMutation,
  useAddHypothesisMutation,
  useAddQuestionMutation,
  useAddDecisionMutation,
  useResolveQuestion,
} from '@/features/workspace';

// Get or create workspace
const { data: workspace } = useWorkspace('workflow_execution', executionId);

// Get entries
const { data: entries } = useWorkspaceEntries(workspace?.workspace_id);

// Add a fact
const addFact = useAddFactMutation();
await addFact.mutateAsync({
  workspaceId: workspace.workspace_id,
  claim: 'User authentication works',
  source: 'testing',
});
```

## Agent Integration

### Python Agent Tools
```python
from workspace.tools import (
    add_workspace_fact,
    add_workspace_hypothesis,
    add_workspace_question,
    add_workspace_decision,
    get_workspace_context_prompt,
)

# Add a fact
await add_workspace_fact(
    workspace_id="...",
    claim="OpenAI consulting projects range from $25k to $120k",
    source="industry_analysis",
    confidence=0.92
)

# Add a hypothesis
await add_workspace_hypothesis(
    workspace_id="...",
    hypothesis="Enterprise clients prefer fixed-price contracts",
    rationale="Based on initial sales calls",
    confidence=0.7
)

# Get context for agent prompt
context = await get_workspace_context_prompt(
    workspace_id="...",
    include_types=["fact", "hypothesis", "question"]
)
```

### Prompt Integration
```python
# Inject workspace context into agent prompts
system_prompt = f"""You are an AI assistant working on a collaborative task.

{context}

When making decisions or discovering information, record it in the workspace
for other agents to see. Ask questions when you need more information."""
```

## Implementation Status

### Completed ✅
1. **Database Schema** - Migration file created
2. **Backend Models** - Pydantic models for API
3. **Service Layer** - Business logic for workspace operations
4. **API Endpoints** - FastAPI routes for workspace CRUD
5. **Agent Tools** - Python functions for agent interaction
6. **Frontend Types** - TypeScript type definitions
7. **API Client** - HTTP client for workspace API
8. **React Query Hooks** - Data fetching and mutations
9. **WorkspaceInspector Component** - UI for workspace visualization
10. **Execution Details Integration** - Workspace panel in execution view

### In Progress ⏳
1. **LLM Summarization** - Generate intelligent summaries of workspace state
2. **Planning Copilot Integration** - Write decisions during workflow planning

### Planned 📋
1. **Agent Context Injection** - Automatically include workspace in agent prompts
2. **Workflow Engine Integration** - Create workspace for each execution
3. **Session Workspace** - Persistent workspace for chat sessions
4. **Agent Team Workspace** - Shared workspace for multi-agent coordination

## Usage Patterns

### Pattern 1: Workflow Execution Workspace
```python
# When a workflow execution starts
workspace = await workspace_service.get_workspace_by_scope(
    "workflow_execution",
    execution_id
)

# As agents execute, they add entries
await add_workspace_decision(
    workspace.workspace_id,
    decision="Use PostgreSQL for data storage",
    reasoning="Best fit for relational data requirements",
    alternatives_considered=["MongoDB", "Redis"]
)

# Later agents can see this decision
context = await get_workspace_context_prompt(workspace.workspace_id)
```

### Pattern 2: Planning Copilot Integration
```python
# During planning, record decisions
await add_workspace_decision(
    workspace_id,
    decision="Implement feature X before feature Y",
    reasoning="X is a dependency for Y"
)

# Record questions for later investigation
await add_workspace_question(
    workspace_id,
    question="What is the expected data volume?",
    priority="high"
)
```

### Pattern 3: Multi-Agent Collaboration
```python
# Agent A adds a hypothesis
await add_workspace_hypothesis(
    workspace_id,
    hypothesis="This approach will reduce latency by 50%",
    rationale="Based on preliminary benchmarks"
)

# Agent B validates the hypothesis
entries = await list_workspace_entries(workspace_id)
for entry in entries.hypotheses:
    if entry.content["hypothesis"] == "...":
        # Update confidence after testing
        await update_entry(workspace_id, entry.memory_id, {
            "confidence": 0.95  # Confirmed!
        })
```

## Best Practices

1. **Use structured content** - Always provide well-structured content objects
2. **Set appropriate confidence** - Use 0.9+ for facts, 0.7 for hypotheses, 1.0 for decisions
3. **Source everything** - Always indicate the source of information
4. **Resolve questions** - Mark questions as resolved when answered
5. **Keep entries focused** - One clear idea per entry
6. **Use appropriate entry types**:
   - Facts: Verified information
   - Hypotheses: Tentative insights needing validation
   - Questions: Areas needing investigation
   - Decisions: Choices made with reasoning
   - Artifacts: Generated outputs (code, reports, diagrams)
   - Notes: General observations

## Testing

### Backend Tests
```bash
# Test workspace service
python -m pytest tests/test_workspace_service.py

# Test workspace API
python -m pytest tests/test_workspace_api.py
```

### Frontend Tests
```bash
# Test workspace hooks
npm run test -- workspace.test.tsx

# Test WorkspaceInspector component
npm run test -- WorkspaceInspector.test.tsx
```

## Migration

Run the database migration:
```bash
psql -U postgres -d torq_console -f migrations/004_shared_cognitive_workspace.sql
```

## Troubleshooting

### Issue: Workspace not found
**Solution**: Use `get_or_create_workspace` for idempotency

### Issue: Entries not appearing
**Solution**: Check that `deleted_at` is NULL and status is 'active'

### Issue: Frontend shows empty workspace
**Solution**: Verify React Query cache is invalidated after mutations

## References

- PRD: Shared Cognitive Workspace (internal document)
- API Docs: http://localhost:8899/api/docs
- Database Schema: `migrations/004_shared_cognitive_workspace.sql`
