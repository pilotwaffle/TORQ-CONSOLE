-- ============================================================================
-- Task Graph Engine Migration Verification Script
-- ============================================================================
-- Run this after executing the migration to verify all components were created
-- ============================================================================

-- 1. Verify all tables exist
SELECT
    'tables' as component_type,
    table_name,
    CASE
        WHEN table_name IN ('task_graphs', 'task_nodes', 'task_edges', 'task_executions', 'task_node_results', 'task_webhooks')
        THEN 'EXPECTED'
        ELSE 'UNEXPECTED'
    END as status
FROM information_schema.tables
WHERE table_schema = 'public'
    AND table_name LIKE 'task_%'
ORDER BY table_name;

-- 2. Verify all indexes exist
SELECT
    'indexes' as component_type,
    indexname,
    tablename
FROM pg_indexes
WHERE schemaname = 'public'
    AND tablename LIKE 'task_%'
ORDER BY tablename, indexname;

-- 3. Verify all triggers exist
SELECT
    'triggers' as component_type,
    trigger_name,
    event_object_table
FROM information_schema.triggers
WHERE event_object_schema = 'public'
    AND event_object_table LIKE 'task_%'
ORDER BY event_object_table, trigger_name;

-- 4. Verify all functions exist
SELECT
    'functions' as component_type,
    routine_name,
    routine_type
FROM information_schema.routines
WHERE routine_schema = 'public'
    AND (routine_name LIKE '%task%' OR routine_name LIKE '%update_%' OR routine_name LIKE '%enforce_%' OR routine_name LIKE '%generate_%')
ORDER BY routine_name;

-- 5. Verify RLS is enabled on all tables
SELECT
    'rls_status' as component_type,
    tablename,
    rowsecurity as rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
    AND tablename LIKE 'task_%'
ORDER BY tablename;

-- 6. Verify RLS policies exist
SELECT
    'rls_policies' as component_type,
    schemaname || '.' || tablename as table_name,
    policyname,
    permissive,
    roles,
    cmd,
    qual
FROM pg_policies
WHERE schemaname = 'public'
    AND tablename LIKE 'task_%'
ORDER BY tablename, policyname;

-- 7. Verify view exists
SELECT
    'views' as component_type,
    table_name as view_name,
    view_definition
FROM information_schema.views
WHERE table_schema = 'public'
    AND table_name = 'execution_summary_view';

-- 8. Test queries for each table
DO $$
DECLARE
    table_count INTEGER;
    index_count INTEGER;
    trigger_count INTEGER;
    function_count INTEGER;
    policy_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name IN ('task_graphs', 'task_nodes', 'task_edges', 'task_executions', 'task_node_results', 'task_webhooks');

    SELECT COUNT(DISTINCT indexname) INTO index_count
    FROM pg_indexes
    WHERE schemaname = 'public' AND tablename LIKE 'task_%';

    SELECT COUNT(*) INTO trigger_count
    FROM information_schema.triggers
    WHERE event_object_schema = 'public' AND event_object_table LIKE 'task_%';

    SELECT COUNT(*) INTO function_count
    FROM information_schema.routines
    WHERE routine_schema = 'public' AND routine_name IN ('update_updated_at_column', 'enforce_execution_state_transition', 'enforce_node_result_state_transition', 'generate_idempotency_key');

    SELECT COUNT(*) INTO policy_count
    FROM pg_policies
    WHERE schemaname = 'public' AND tablename LIKE 'task_%';

    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'TASK GRAPH ENGINE MIGRATION VERIFICATION';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Tables Created: % / 6', table_count;
    RAISE NOTICE 'Indexes Created: %', index_count;
    RAISE NOTICE 'Triggers Created: % / 6', trigger_count;
    RAISE NOTICE 'Functions Created: % / 4', function_count;
    RAISE NOTICE 'RLS Policies Created: %', policy_count;
    RAISE NOTICE '========================================';

    IF table_count = 6 THEN
        RAISE NOTICE 'SUCCESS: All tables created!';
    ELSE
        RAISE NOTICE 'WARNING: Expected 6 tables, found %', table_count;
    END IF;

    IF index_count >= 20 THEN
        RAISE NOTICE 'SUCCESS: All indexes created!';
    ELSE
        RAISE NOTICE 'WARNING: Expected at least 20 indexes, found %', index_count;
    END IF;

    IF trigger_count = 6 THEN
        RAISE NOTICE 'SUCCESS: All triggers created!';
    ELSE
        RAISE NOTICE 'WARNING: Expected 6 triggers, found %', trigger_count;
    END IF;

    IF function_count = 4 THEN
        RAISE NOTICE 'SUCCESS: All functions created!';
    ELSE
        RAISE NOTICE 'WARNING: Expected 4 functions, found %', function_count;
    END IF;
END $$;
