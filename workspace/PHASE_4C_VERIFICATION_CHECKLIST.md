# Shared Cognitive Workspace - Phase 4C Verification Checklist

## Status: Implemented, Pending Integration Validation

**Current Assessment**: The foundation is complete. Strategic integration is in progress.

### ✅ Foundation Complete

- [x] Database schema (PostgreSQL migration)
- [x] FastAPI workspace service + routes
- [x] Agent tools (Python functions)
- [x] Frontend types/api/hooks (React/TypeScript)
- [x] Inspector UI component
- [x] Execution page integration (UI layer)

### 🔄 Integration Validation (In Progress)

---

## 1. Route Validation ✅ FIXED

**Critical Issues Fixed:**
- [x] Backend import path: Changed `from workspace.api` → `from torq_console.workspace.api`
- [x] Double `/api` prefix: Changed workspace router from `/api/workspaces` → `/workspaces`

**Expected Live Endpoints:**
```
GET    /api/workspaces/{id}                    - Get workspace by ID
GET    /api/workspaces/{id}/entries            - List entries (grouped)
POST   /api/workspaces                         - Create workspace
POST   /api/workspaces/{id}/entries            - Add entry
PATCH  /api/workspaces/{id}/entries/{memory_id} - Update entry
POST   /api/workspaces/{id}/entries/{memory_id}/resolve - Resolve question
POST   /api/workspaces/{id}/summarize          - Generate LLM summary
```

**Validation Steps:**
- [ ] Start backend server: `python -m torq_console.api.server`
- [ ] Open API docs: `http://localhost:8899/api/docs`
- [ ] Verify all workspace routes are listed under `/api/workspaces`
- [ ] Confirm NO `/api/api/workspaces` route exists
- [ ] Test creating a workspace via API docs
- [ ] Test adding an entry via API docs

---

## 2. Execution-Linked Workspace Creation

**Goal**: When opening execution details, a workspace should auto-create or load.

**Validation Steps:**
- [ ] Navigate to `/executions` page
- [ ] Click on any execution
- [ ] Click the "Workspace" toggle button in header
- [ ] Verify: Workspace panel opens on the left
- [ ] Verify: No 404 errors in browser console
- [ ] Verify: Either shows existing entries OR clean empty state
- [ ] Verify: Toggle button highlights when open (purple background)

**Expected Empty State:**
```
┌─────────────────────────────────────┐
│  Shared Cognitive Workspace        │
│  ┌───────────────────────────────┐  │
│  │ No facts yet.                 │  │
│  │ No hypotheses yet.            │  │
│  │ No questions yet.             │  │
│  │ No decisions yet.             │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

---

## 3. Inspector UI Behavior

**Toggle Functionality:**
- [ ] Click "Workspace" button → panel slides in from left
- [ ] Click "Workspace" button again → panel slides away
- [ ] Click X in panel header → panel closes
- [ ] Panel state persists across navigation

**Empty Sections:**
- [ ] Each section (Facts, Hypotheses, Questions, Decisions, Artifacts, Notes)
- [ ] Shows "No {section} yet." when empty
- [ ] Shows count badge when entries exist

**Entry Display:**
- [ ] Entry card shows: source_agent, status, confidence %
- [ ] JSON content is properly formatted
- [ ] Resolve button shows for unresolved questions
- [ ] Clicking resolve updates the entry status

**Summary Feature:**
- [ ] Click "Summarize" button → summary section appears
- [ ] Click "Generate Summary" → loading state shows
- [ ] Summary displays when complete (or fallback if no LLM)

---

## 4. Agent Write Test

**Goal**: Verify agents can write to workspace during execution.

**Test Case: Simple Research Workflow**
```
Prompt: "Research top 3 AI consulting competitors"
Expected agent writes:
- Research Agent: Adds 3+ facts about competitors
- Analysis Agent: Adds 1-2 hypotheses about market positioning
- Strategy Agent: Adds 1 decision about recommended approach
```

**Validation Steps:**
- [ ] Run the above workflow
- [ ] Open workspace panel during/after execution
- [ ] Verify: Facts section has competitor data
- [ ] Verify: Hypotheses section has analysis
- [ ] Verify: Decisions section has strategic choice
- [ ] Verify: Each entry shows correct source_agent
- [ ] Verify: Confidence scores are appropriate (0.7-1.0)

**Manual API Test (Quick Check):**
```bash
# Create a workspace
curl -X POST http://localhost:8899/api/workspaces \
  -H "Content-Type: application/json" \
  -d '{"scope_type": "workflow_execution", "scope_id": "test_123", "title": "Test Workspace"}'

# Add a fact
curl -X POST http://localhost:8899/api/workspaces/{id}/entries \
  -H "Content-Type: application/json" \
  -d '{"entry_type": "fact", "content": {"claim": "Test fact"}, "confidence": 0.9}'

# Get entries
curl http://localhost:8899/api/workspaces/{id}/entries
```

---

## 5. Planner Integration Test

**Goal**: Planning Copilot writes decisions/questions during workflow planning.

**Test Prompt:**
```
"Build a workflow to research AI consulting competitors"
```

**Expected Planner Writes:**
- [ ] At least 1 decision (e.g., "Use web search for competitor research")
- [ ] At least 1 question (e.g., "What defines 'top' competitors?")
- [ ] At least 1 fact (e.g., "Market size is $X billion")

**Validation Steps:**
- [ ] Open workflow planning copilot
- [ ] Enter test prompt
- [ ] Let planner complete
- [ ] Open workspace panel
- [ ] Verify planner's reasoning is captured

---

## Next Implementation Order (Recommended)

### Priority 1: Foundation Validation ✅ (Done)
- [x] Fix router import path
- [x] Fix double /api prefix
- [ ] Verify all routes load correctly

### Priority 2: Auto-Create Workspace on Execution Start
```python
# In torq_console/tasks/executor.py
async def start_execution(graph_id: str, inputs: dict):
    # Create workspace first
    workspace = await workspace_service.get_or_create_workspace(
        scope_type="workflow_execution",
        scope_id=execution_id,
        title=f"Execution: {graph.name}"
    )
    # Pass workspace_id to all agent calls
    ...
```

### Priority 3: Planning Copilot Integration
```python
# In planner agent
async def plan_workflow(user_request: str):
    # Create/get workspace
    workspace = await get_or_create_workspace("planning", session_id)

    # Write decisions as they're made
    await add_workspace_decision(
        workspace.workspace_id,
        decision="Use web search for research",
        reasoning="User needs real-time data"
    )
```

### Priority 4: Agent Read/Write Tools
```python
# In each agent call
async def agent_execute(task: str, workspace_id: str):
    # Read workspace context
    context = await get_workspace_context_prompt(workspace_id)

    # Add context to agent prompt
    prompt = f"{context}\n\nTask: {task}"

    # Write results back to workspace
    result = await agent.run(prompt)
    await add_workspace_fact(workspace_id, claim=result.summary)
```

### Priority 5: LLM Summarization
- [ ] Ensure Anthropic API key is configured
- [ ] Test summarization endpoint
- [ ] Add fallback when LLM unavailable

---

## Success Criteria

The Shared Cognitive Workspace becomes strategically meaningful when:

1. **Every workflow execution** has an auto-created workspace
2. **Planning phase** writes decisions/questions to workspace
3. **Agent execution** reads workspace context before acting
4. **Agent execution** writes facts/hypotheses after acting
5. **Users can inspect** the workspace via the UI panel
6. **Summarization** provides quick overview of workspace state

When these are true, TORQ has a real differentiator vs LangGraph/CrewAI.

---

## Current Status Summary

**Phase 4C**: Shared Cognitive Workspace
- **Foundation**: ✅ Complete
- **Backend API**: ✅ Complete (routes fixed)
- **Frontend UI**: ✅ Complete (integrated)
- **Agent Tools**: ✅ Complete
- **Strategic Integration**: 🔄 In Progress

**Blockers**: None identified
**Next Step**: Run route validation test, then execution-linked workspace creation

**Estimated Completion**: After Priority 2-5 above are implemented
