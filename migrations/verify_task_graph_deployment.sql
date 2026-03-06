-- ============================================================================
-- Task Graph Engine - Post-Deployment Verification Script
-- ============================================================================
-- Run this after executing the migration to verify everything is working.
--
-- Execute in Supabase SQL Editor:
-- https://supabase.com/dashboard/project/npukynbaglmcdvzyklqa/sql/new
-- ============================================================================

-- ============================================================================
-- 1. Verify all tables exist (should return 6 rows)
-- ============================================================================
SELECT 'Tables created:' as check_type;
SELECT table_name
FROM information_schema.tables
WHERE table_schema='public'
AND table_name LIKE 'task_%'
ORDER BY table_name;

-- Expected output:
-- task_edges
-- task_executions
-- task_graphs
-- task_node_results
-- task_nodes
-- task_webhooks

-- ============================================================================
-- 2. Verify critical concurrency indexes exist
-- ============================================================================
SELECT 'Critical concurrency indexes:' as check_type;
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename='task_node_results'
  AND (
    indexname LIKE '%single_runner%'
    OR indexname LIKE '%idempotency%'
  )
ORDER BY indexname;

-- Expected to see:
-- idx_task_node_results_single_runner (WHERE status = 'running')
-- idx_task_node_results_idempotency_completed (WHERE status = 'completed')
-- idx_task_node_results_idempotency_key

-- ============================================================================
-- 3. Verify state machine triggers exist
-- ============================================================================
SELECT 'State machine triggers:' as check_type;
SELECT tgname, pg_get_triggerdef(oid)
FROM pg_trigger
WHERE tgname LIKE '%enforce%'
ORDER BY tgname;

-- Expected to see:
-- enforce_execution_state_transition_trigger (on task_executions)
-- enforce_node_result_state_transition_trigger (on task_node_results)

-- ============================================================================
-- 4. Verify constraints on task_node_results
-- ============================================================================
SELECT 'Task node results constraints:' as check_type;
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'task_node_results'::regclass
ORDER BY conname;

-- Expected to see:
-- attempt_bound (CHECK attempt <= max_attempts)
-- output_size_limit (CHECK output_size_bytes <= 262144)
-- valid_result_status (CHECK status IN (...))

-- ============================================================================
-- 5. Quick smoke test - Insert test graph and node
-- ============================================================================
SELECT 'Smoke test - creating test graph:' as check_type;

-- Create a test graph
INSERT INTO task_graphs (name, description, status)
VALUES ('smoke_test', 'Migration verification test', 'active')
RETURNING graph_id, name, status, created_at;

-- Save the graph_id from above, then run this:
-- INSERT INTO task_nodes (graph_id, node_key, name, node_type)
-- VALUES ('<graph_id_from_above>', 'step1', 'Test Node', 'agent')
-- RETURNING node_id, node_key, name;

-- ============================================================================
-- 6. Verify RLS policies exist
-- ============================================================================
SELECT 'RLS policies:' as check_type;
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual
FROM pg_policies
WHERE tablename LIKE 'task_%'
ORDER BY tablename, policyname;

-- Expected: Multiple policies for tenant isolation on each table

-- ============================================================================
-- 7. Summary report
-- ============================================================================
SELECT 'Summary:' as check_type;
SELECT
    (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE 'task_%') as tables_created,
    (SELECT COUNT(DISTINCT indexname) FROM pg_indexes WHERE tablename LIKE 'task_%') as indexes_created,
    (SELECT COUNT(*) FROM pg_trigger WHERE tgname LIKE '%task%' OR tgname LIKE '%update%') as triggers_created,
    (SELECT COUNT(*) FROM pg_policies WHERE tablename LIKE 'task_%') as rls_policies_created;

-- All counts should be > 0
