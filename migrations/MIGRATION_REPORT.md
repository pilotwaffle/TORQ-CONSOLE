# Task Graph Engine Migration Report

## Migration Details

**File**: `migrations/001_task_graph_engine_production_safe.sql`
**Project**: npukynbaglmcdvzyklqa
**Size**: 19,817 characters
**Date**: 2026-03-05

## Objects to be Created

### Tables (6)
1. `task_graphs` - Graph definition metadata
2. `task_nodes` - Node definition metadata
3. `task_edges` - Edge definitions with stable keys
4. `task_executions` - Runtime execution tracking
5. `task_node_results` - Per-node execution results
6. `task_webhooks` - Webhook configuration

### Functions (4)
1. `update_updated_at_column` - Auto-update timestamps
2. `enforce_execution_state_transition` - State machine guard for executions
3. `enforce_node_result_state_transition` - State machine guard for node results
4. `generate_idempotency_key` - Generate idempotency hashes

### Triggers (6)
1. `update_task_graphs_updated_at` - Auto-update task_graphs.updated_at
2. `update_task_nodes_updated_at` - Auto-update task_nodes.updated_at
3. `update_task_webhooks_updated_at` - Auto-update task_webhooks.updated_at
4. `enforce_execution_state_transition_trigger` - Enforce execution state transitions
5. `enforce_node_result_state_transition_trigger` - Enforce node result state transitions

### Views (1)
1. `execution_summary_view` - Aggregated execution summary with progress

### Indexes (20+)
- Status indexes on task_graphs, task_executions, task_node_results
- Tenant isolation indexes
- Foreign key indexes
- Unique constraints for idempotency
- Partial indexes for single-runner lock

## Production Safety Features

1. **Idempotency Keys**: Scoped per-tenant for exactly-once semantics
2. **State Machine Enforcement**: Prevents invalid state transitions
3. **Size Limits**: 64KB input, 256KB output limits with external storage refs
4. **Concurrency Control**: Single-runner lock prevents duplicate node execution
5. **Tenant Isolation**: RLS policies for multi-tenancy
6. **Webhook Security**: HMAC signature verification support

## Execution Status

**Status**: NOT EXECUTED - Requires manual execution

The migration could not be executed automatically because:
- Direct PostgreSQL connection requires database password (not available via service role key)
- Supabase Management API requires personal access token
- REST API does not support DDL statements

## How to Execute

### Option 1: Supabase Dashboard (Recommended)

1. Go to: https://supabase.com/dashboard/project/npukynbaglmcdvzyklqa/sql/new
2. Open the file: `E:\TORQ-CONSOLE\migrations\001_task_graph_engine_production_safe.sql`
3. Copy the entire SQL content
4. Paste into the SQL Editor
5. Click "Run" or press Ctrl+Enter

### Option 2: Supabase CLI

1. Generate access token at: https://supabase.com/dashboard/account/tokens
2. Set environment variable:
   ```bash
   export SUPABASE_ACCESS_TOKEN=your_access_token_here
   ```
3. Execute:
   ```bash
   npx supabase db execute --project-ref npukynbaglmcdvzyklqa --file migrations/001_task_graph_engine_production_safe.sql
   ```

### Option 3: psql with Database Password

1. Get database password from: https://supabase.com/dashboard/project/npukynbaglmcdvzyklqa/settings/database
2. Connect and execute:
   ```bash
   psql -h db.npukynbaglmcdvzyklqa.supabase.co -U postgres -d postgres
   # Paste the SQL content
   ```

## Verification Queries

After execution, verify the objects were created:

```sql
-- Verify tables
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name LIKE 'task_%'
ORDER BY table_name;
-- Expected: task_edges, task_executions, task_graphs, task_node_results, task_nodes, task_webhooks

-- Verify indexes on task_node_results
SELECT indexname
FROM pg_indexes
WHERE tablename = 'task_node_results'
ORDER BY indexname;
-- Expected: idx_task_node_results_execution_id, idx_task_node_results_idempotency_completed,
--           idx_task_node_results_idempotency_key, idx_task_node_results_node_id,
--           idx_task_node_results_node_key, idx_task_node_results_single_runner,
--           idx_task_node_results_status

-- Verify triggers
SELECT tgname
FROM pg_trigger
WHERE tgname LIKE '%task%'
OR tgname LIKE '%update%'
OR tgname LIKE '%enforce%'
ORDER BY tgname;
-- Expected: enforce_execution_state_transition_trigger, enforce_node_result_state_transition_trigger,
--           update_task_graphs_updated_at, update_task_nodes_updated_at, update_task_webhooks_updated_at

-- Verify functions
SELECT proname
FROM pg_proc
WHERE proname LIKE '%task%'
OR proname LIKE '%generate%'
OR proname LIKE '%update%'
ORDER BY proname;
-- Expected: enforce_execution_state_transition, enforce_node_result_state_transition,
--           generate_idempotency_key, update_updated_at_column

-- Verify view
SELECT viewname
FROM pg_views
WHERE viewname LIKE '%execution%';
-- Expected: execution_summary_view
```

## Next Steps After Migration

1. Run the verification queries above
2. Create a test graph and execution to verify functionality
3. Test the state machine transitions
4. Verify RLS policies are working correctly
5. Test webhook endpoint if using webhooks

## Files Created

- `E:\TORQ-CONSOLE\migration_to_execute.sql` - Copy-paste ready SQL
- `E:\TORQ-CONSOLE\migrations\001_task_graph_engine_production_safe.sql` - Original migration file
