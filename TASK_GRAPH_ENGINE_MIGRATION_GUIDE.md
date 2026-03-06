# Task Graph Engine Migration - Execution Guide

## Overview

This migration creates a complete Task Graph Engine database schema for TORQ Console with:
- **6 tables**: task_graphs, task_nodes, task_edges, task_executions, task_node_results, task_webhooks
- **26+ indexes** for performance optimization
- **6 triggers** for automatic state management
- **4 functions** for idempotency and state enforcement
- **8 RLS policies** for tenant isolation
- **1 view** for execution summaries

## Production Safety Features

1. **Idempotency keys scoped per-tenant** - Ensures exactly-once execution semantics
2. **State machine triggers** - Enforces valid transitions on runtime state tables
3. **Input/output size limits** - 64KB for parameters, 256KB for outputs
4. **Concurrency-safe indexes** - Single-runner lock prevents duplicate node execution
5. **Tenant isolation** - Row Level Security policies for multi-tenancy

## Execution Instructions

### Option 1: Supabase Dashboard (RECOMMENDED)

1. Go to: https://app.supabase.com/project/npukynbaglmcdvzyklqa/sql/new
2. Open the migration file: `E:\TORQ-CONSOLE\migrations\001_task_graph_engine_production_safe.sql`
3. Copy the entire contents
4. Paste into the SQL Editor
5. Click "Run" to execute

### Option 2: Supabase CLI with Database Password

1. Get your database password from: https://app.supabase.com/project/npukynbaglmcdvzyklqa/settings/database
2. Run:
```bash
psql "postgresql://postgres:[PASSWORD]@db.npukynbaglmcdvzyklqa.supabase.co:5432/postgres" -f migrations/001_task_graph_engine_production_safe.sql
```

### Option 3: Via psql with Pooler Connection

```bash
psql "postgresql://postgres.npukynbaglmcdvzyklqa:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:5432/postgres" -f migrations/001_task_graph_engine_production_safe.sql
```

## Verification

After executing the migration, run the verification script:

**Via Dashboard**: https://app.supabase.com/project/npukynbaglmcdvzyklqa/sql/new
Copy and paste the contents of: `E:\TORQ-CONSOLE\verify_task_graph_migration.sql`

**Expected Results**:
- Tables Created: 6 / 6
- Indexes Created: 26+
- Triggers Created: 6 / 6
- Functions Created: 4 / 4
- RLS Policies Created: 8+

## Schema Overview

### Definition Tables (Static Metadata)

| Table | Purpose |
|-------|---------|
| `task_graphs` | Workflow definitions |
| `task_nodes` | Node definitions (agents, tools, etc.) |
| `task_edges` | Connections between nodes |
| `task_webhooks` | Webhook configurations |

### Runtime Tables (Stateful)

| Table | Purpose |
|-------|---------|
| `task_executions` | Per-execution tracking |
| `task_node_results` | Per-node-per-execution results |

### Key Features

1. **Idempotency**: Each execution can have an idempotency key to prevent duplicate execution
2. **State Machine**: Triggers enforce valid status transitions (e.g., can't go from completed back to running)
3. **Concurrency Control**: Unique indexes prevent multiple workers from claiming the same node
4. **Tenant Isolation**: RLS policies ensure tenants can only see their own data

## Migration File Location

- Primary: `E:\TORQ-CONSOLE\migrations\001_task_graph_engine_production_safe.sql`
- Copy: `E:\TORQ-CONSOLE\task_graph_migration.sql`
- Verification: `E:\TORQ-CONSOLE\verify_task_graph_migration.sql`

## Troubleshooting

### Error: "relation already exists"
The migration uses `IF NOT EXISTS` for all objects, so it should be safe to re-run.

### Error: "function already exists"
Functions use `CREATE OR REPLACE`, so they will be updated if they exist.

### Error: "policy already exists"
Drop existing policies first:
```sql
DROP POLICY IF EXISTS "policy_name" ON "table_name";
```

### Error: Foreign key constraints
Create tables in order:
1. task_graphs
2. task_nodes
3. task_edges
4. task_executions
5. task_node_results
6. task_webhooks

The migration file is already in the correct order.

## Next Steps

After migration:

1. **Test idempotency**: Insert a record with an idempotency key, then try to insert again
2. **Test state transitions**: Update execution status from pending -> running -> completed
3. **Test RLS**: Set `request.jwt.claim.tenant_id` and verify data isolation
4. **Create a test workflow**: Insert a task_graph with nodes and edges
5. **Execute a test run**: Insert a task_execution and related task_node_results

## Support

For issues or questions:
- Check the migration logs in Supabase Dashboard
- Run the verification script to identify missing components
- Review the production safety features section for expected behavior
