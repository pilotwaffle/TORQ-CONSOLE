# Workflow Builder UI v1 - QA Test Plan

## Overview
This document outlines the recommended QA tests for the Workflow Builder UI v1 implementation. These tests should be executed against a running Task Graph Engine backend.

## Prerequisites
- Frontend dev server running on `http://localhost:3000`
- Task Graph Engine backend running on `http://localhost:8899`
- Supabase backend configured and connected

---

## Test 1: Workflow Creation

### Goal
Create a workflow from template and verify persistence.

### Steps
1. Navigate to `/workflows/new`
2. Select a template (e.g., "Research Agent" template)
3. Verify template loads with:
   - Template name and description
   - Number of nodes and edges
4. Click to select template

### Expected Results
- Should redirect to workflow editor
- Pre-populated nodes should display
- Node configuration panel should show template values

### Verification Commands
```sql
-- Check workflow was saved
SELECT graph_id, name, status, version
FROM task_graphs
ORDER BY created_at DESC
LIMIT 1;

-- Verify nodes
SELECT node_id, node_key, name, node_type, agent_id
FROM task_graph_nodes
WHERE graph_id = (SELECT graph_id FROM task_graphs ORDER BY created_at DESC LIMIT 1)
ORDER BY position_y;

-- Verify edges
SELECT source_node_id, target_node_id
FROM task_graph_edges
WHERE graph_id = (SELECT graph_id FROM task_graphs ORDER BY created_at DESC LIMIT 1);
```

### Success Criteria
- ✅ Workflow created with correct `status`
- ✅ All nodes saved with correct `position_x`, `position_y`
- ✅ All edges saved with correct `source_node_id`, `target_node_id`
- ✅ Graph loads correctly in visualization view

---

## Test 2: Graph Execution

### Goal
Execute a workflow and verify sequential node execution.

### Steps
1. From workflows list, click "Execute" on an active workflow
2. Monitor the redirect to execution details page
3. Watch for status changes:
   - `pending` → `running` → `completed`
   - Or `pending` → `running` → `failed`

### Expected Results
- Execution record created in `task_executions`
- Nodes execute in dependency order
- Final execution status reflects overall result

### Verification Commands
```sql
-- Check execution record
SELECT execution_id, graph_id, status, started_at, completed_at,
       nodes_completed, nodes_failed
FROM task_executions
ORDER BY created_at DESC
LIMIT 1;

-- Check node execution results
SELECT node_id, node_key, name, status, duration_ms,
       attempt, error_message
FROM task_node_results
WHERE execution_id = (SELECT execution_id FROM task_executions ORDER BY created_at DESC LIMIT 1)
ORDER BY started_at;

-- Verify sequential execution
-- Nodes should have started_at in dependency order
-- A node's started_at should be AFTER its dependencies' completed_at
```

### Success Criteria
- ✅ Execution status transitions: `pending` → `running` → `completed`
- ✅ `task_executions` record created
- ✅ `task_node_results` records created for each node
- ✅ Nodes execute sequentially respecting dependencies
- ✅ Duration recorded for each node

---

## Test 3: Execution Visualization

### Goal
Verify real-time visualization updates during execution.

### Steps
1. Navigate to `/executions/{execution_id}` for a running execution
2. Observe the ExecutionGraphOverlay
3. Watch for color changes on nodes

### Expected Node Color Transitions
| Status | Color | Icon |
|--------|-------|------|
| pending | gray | Clock |
| running | blue | Spinning Loader |
| completed | green | CheckCircle |
| failed | red | AlertCircle |

### Verification
- The graph should auto-refresh every 3 seconds while execution is running
- Node colors should update as execution progresses
- Progress bar should show completion percentage

### Success Criteria
- ✅ Node colors change: gray → blue → green (or red for failures)
- ✅ Graph updates correctly with live status
- ✅ Progress bar reflects actual completion
- ✅ Auto-refresh stops when execution completes

---

## Test 4: Node Output

### Goal
Verify node details panel shows complete execution information.

### Steps
1. From execution details page, click on a completed node
2. Verify NodeDetailsPanel opens on right side
3. Check displayed information

### Expected Panel Contents
- **Node ID**: Unique identifier
- **Agent**: Agent ID used (if applicable)
- **Status**: Final status (completed/failed)
- **Duration**: Execution time in ms/s format
- **Retries**: Number of retry attempts
- **Output**: JSON output from node execution
- **Errors**: Error message if failed

### Verification Commands
```sql
-- Compare with actual database records
SELECT result_id, node_id, status, duration_ms,
       attempt, error_message
FROM task_node_results
WHERE execution_id = '<current_execution_id>'
  AND node_id = '<clicked_node_id>';
```

### Success Criteria
- ✅ NodeDetailsPanel displays all required information
- ✅ Agent ID shown if agent was used
- ✅ Runtime duration formatted correctly
- ✅ Output JSON displayed (or "No output" message)
- ✅ Errors shown in red for failed nodes
- ✅ Retry count displayed

---

## Test 5: Failure Recovery

### Goal
Verify proper handling of execution failures.

### Steps
1. Create a workflow with an invalid configuration (e.g., invalid tool name)
2. Execute the workflow
3. Verify failure is captured correctly

### Example Failure Scenarios
```json
// Invalid tool name
{
  "node_type": "tool",
  "tool_name": "nonexistent_tool_xyz"
}

// Missing required parameter
{
  "node_type": "api_call",
  "parameters": {
    "url": ""  // Empty URL
  }
}
```

### Expected Results
- Node status should be `failed`
- Execution status should be `failed`
- Error message should be descriptive
- Dead letter entry should be created

### Verification Commands
```sql
-- Check failed execution
SELECT execution_id, status, nodes_completed, nodes_failed
FROM task_executions
WHERE status = 'failed'
ORDER BY created_at DESC
LIMIT 1;

-- Check failed node result
SELECT node_id, status, error_message, attempt
FROM task_node_results
WHERE execution_id = '<failed_execution_id>'
  AND status = 'failed';

-- Check dead letter queue
SELECT * FROM task_dead_letters
WHERE execution_id = '<failed_execution_id>';
```

### Success Criteria
- ✅ Failed node status: `failed`
- ✅ Failed execution status: `failed`
- ✅ Error message is descriptive and helpful
- ✅ `task_dead_letters` entry created with failure context
- ✅ UI shows failure in red with error message

---

## Test 6: Live Output Streaming (Bonus)

### Goal
Verify LiveOutputPanel shows streaming output during execution.

### Steps
1. Start execution of a long-running workflow
2. Click on a running node
3. Open LiveOutputPanel
4. Watch for streaming output

### Expected Results
- Panel shows "Streaming" indicator
- Output updates in real-time
- Auto-scrolls to bottom
- Pause/Resume buttons work

### Success Criteria
- ✅ "Streaming" badge visible during execution
- ✅ Output appears as it's generated
- ✅ Panel auto-scrolls to show latest output
- ✅ Copy button copies full output
- ✅ Download button saves output to file

---

## Test 7: Template Gallery (Bonus)

### Goal
Verify template gallery loads and filters correctly.

### Steps
1. Navigate to `/workflows/new`
2. Browse available templates
3. Use search box
4. Click category pills

### Expected Results
- All templates display with name, description, node count
- Search filters templates by name/description
- Category pills filter by type
- "Start from Scratch" option available

### Success Criteria
- ✅ Templates load from `/api/tasks/examples`
- ✅ Search filters in real-time
- ✅ Category filtering works
- ✅ Clicking template opens editor with pre-filled data

---

## API Endpoints Tested

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/tasks/graphs` | GET | List workflows |
| `/api/tasks/graphs` | POST | Create workflow |
| `/api/tasks/graphs/{id}` | GET | Get workflow details |
| `/api/tasks/graphs/{id}/execute` | POST | Execute workflow |
| `/api/tasks/executions` | GET | List executions |
| `/api/tasks/executions/{id}` | GET | Get execution |
| `/api/tasks/executions/{id}/graph` | GET | Get execution graph |
| `/api/tasks/examples` | GET | Get templates |

---

## Known Limitations (To Address in Future Phases)

1. **Drag-and-Drop Editor** - Current editor is form-based, not visual drag-and-drop
2. **Real-time WebSocket Updates** - Using polling; could upgrade to WebSocket for true real-time
3. **Workflow Scheduling UI** - API exists but no UI yet
4. **Dead Letter Queue UI** - API exists but no dedicated UI page

---

## Sign-Off Checklist

After completing these tests:

- [ ] All 5 core tests pass
- [ ] Additional bonus tests pass (if attempted)
- [ ] No console errors during normal operations
- [ ] API proxy working correctly to backend
- [ ] Database queries match UI state

---

## Next Steps After QA Pass

1. **Commit changes** with comprehensive test report
2. **Create GitHub PR** with test evidence screenshots
3. **Tag release** as v0.81.0 (Workflow Builder UI v1)
4. **Begin Phase 5**: Workflow Scheduling UI
5. **Begin Phase 6**: Dead Letter Queue UI
