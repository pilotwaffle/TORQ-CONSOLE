# Test 3: Execution Detail Panel - Validation Protocol

## Test Objective

Validate that the Workspace Inspector panel integrates correctly with the Execution Details page using the get-or-create-by-scope endpoint.

## Preconditions

1. Backend server must be running on port 8899
2. Frontend must be built (dist folder exists)
3. Supabase migration must be applied (workspaces tables exist)
4. Environment variables configured (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

## Validation Steps

### Step 1: Verify Backend Routes

```bash
# Check if workspace routes are registered
curl http://localhost:8899/api/docs | grep -i workspace

# Expected output should include:
# - /api/workspaces (POST)
# - /api/workspaces/get-or-create (POST)
# - /api/workspaces/by-scope (GET)
```

**Pass Criteria:** Workspace routes appear in OpenAPI docs

---

### Step 2: Test Get-or-Create Endpoint Directly

```bash
# First call - should create new workspace
curl -X POST http://localhost:8899/api/workspaces/get-or-create \
  -H "Content-Type: application/json" \
  -d '{
    "scope_type": "workflow_execution",
    "scope_id": "test_validation_123",
    "title": "Test Execution Workspace"
  }' | jq '.'

# Save the workspace_id from response
# Second call with same scope - should return same workspace (not create new)
curl -X POST http://localhost:8899/api/workspaces/get-or-create \
  -H "Content-Type: application/json" \
  -d '{
    "scope_type": "workflow_execution",
    "scope_id": "test_validation_123",
    "title": "Test Execution Workspace"
  }' | jq '.'

# Compare workspace_id - should be identical
```

**Pass Criteria:**
- First call returns workspace with `workspace_id`
- Second call returns SAME `workspace_id` (idempotency)
- Both calls return HTTP 200

---

### Step 3: Navigate to Execution Details Page

1. Start frontend: `npm run dev` or open built frontend
2. Navigate to: `/executions`
3. Click on any execution to go to `/executions/:executionId`

**Pass Criteria:** Page loads without JavaScript errors

---

### Step 4: Toggle Workspace Panel

1. Locate the "Workspace" button in the execution detail header
2. Click to open the panel

**Expected Behaviors:**
- [ ] Panel slides in from left
- [ ] Button highlights (purple background)
- [ ] No 404 errors in browser console
- [ ] Network tab shows ONE call to `/api/workspaces/get-or-create`

**Pass Criteria:** All expected behaviors met

---

### Step 5: Verify Workspace State

After panel opens, check one of two states:

**State A: Empty Workspace (First Time)**
```
Expected UI:
┌─────────────────────────────────┐
│ Shared Workspace                │
│ ┌───────────────────────────┐  │
│ │ No facts yet.              │  │
│ │ No hypotheses yet.         │  │
│ │ No questions yet.          │  │
│ │ No decisions yet.          │  │
│ │ No artifacts yet.          │  │
│ └───────────────────────────┘  │
└─────────────────────────────────┘
```

**State B: Existing Workspace (Subsequent Visit)**
```
Expected UI: Shows existing entries
```

**Pass Criteria:** Shows clean empty state OR existing entries (no error states)

---

### Step 6: Verify No Request Loops

Open browser DevTools → Network tab

1. Filter by "workspaces"
2. Count the number of `/api/workspaces/get-or-create` calls

**Pass Criteria:**
- Exactly ONE call when panel first opens
- No repeated calls on re-render
- No request loops

---

### Step 7: Verify React Query Caching

1. Close workspace panel
2. Re-open workspace panel

**Pass Criteria:**
- Second open should use cached data (instant)
- No new network call to get-or-create (unless cache expired)

---

### Step 8: Verify Database State

```bash
# Connect to Supabase/PostgreSQL and check:
SELECT workspace_id, scope_type, scope_id, title, created_at
FROM workspaces
WHERE scope_type = 'workflow_execution'
ORDER BY created_at DESC
LIMIT 5;

# Should show the workspace that was created
```

**Pass Criteria:** Workspace row exists for the execution scope

---

## Success Criteria Summary

| # | Criterion | Pass/Fail |
|---|-----------|------------|
| 1 | Backend routes registered in OpenAPI docs | ⏳ |
| 2 | Get-or-create endpoint is idempotent | ⏳ |
| 3 | Execution details page loads | ⏳ |
| 4 | Workspace toggle button works | ⏳ |
| 5 | Panel opens without 404 errors | ⏳ |
| 6 | Shows empty state or real entries | ⏳ |
| 7 | No request loops (single get-or-create call) | ⏳ |
| 8 | React Query cache works on re-open | ⏳ |
| 9 | Workspace row created in database | ⏳ |
| 10 | No console errors | ⏳ |

## Common Issues and Fixes

### Issue: 404 on `/api/workspaces/get-or-create`

**Cause:** Workspace router not included in FastAPI app

**Fix:**
```python
# In torq_console/api/server.py
if WORKSPACE_AVAILABLE and workspace_router:
    app.include_router(workspace_router, prefix="/api")
```

### Issue: Double `/api/api/workspaces`

**Cause:** Router has `/api/workspaces` prefix but included with `/api` prefix

**Fix:** Router prefix should be `/workspaces` only (done)

### Issue: Workspace panel shows error state

**Cause:** Supabase not configured or tables don't exist

**Fix:**
```bash
# Run migration
psql -U postgres -d torq_console -f migrations/004_shared_cognitive_workspace.sql
```

### Issue: Multiple workspaces created for same execution

**Cause:** get-or-create not checking existing properly

**Fix:** Verify unique constraint on `(tenant_id, scope_type, scope_id)`

## Test Execution Log

*Fill in during actual testing*

| Timestamp | Action | Result | Notes |
|-----------|--------|--------|-------|
| - | Started server | ✅ | - |
| - | Checked routes | ⏳ | - |
| - | Tested get-or-create | ⏳ | - |
| - | Opened execution page | ⏳ | - |
| - | Toggled workspace panel | ⏳ | - |
| - | Verified UI state | ⏳ | - |
| - | Checked network calls | ⏳ | - |

## Next Steps After Test 3 Passes

1. **Auto-create workspace on execution start**
   - Modify `torq_console/tasks/executor.py` to call `get_or_create_workspace` when execution starts

2. **Planning Copilot integration**
   - Add workspace writes during planning phase

3. **Agent tool integration**
   - Add `add_workspace_fact`, `add_workspace_decision` calls during agent execution
