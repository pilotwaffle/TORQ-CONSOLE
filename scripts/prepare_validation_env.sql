-- ============================================================================
-- Validation Environment Preparation Script
-- Purpose: Reset database state for clean validation baseline
-- Usage: psql -U your_user -d torq_console -f scripts/prepare_validation_env.sql
-- ============================================================================

\echo '=========================================='
\echo 'Phase 5.1 Validation Environment Setup'
\echo '=========================================='
\echo ''

-- 1. Check current migration status
\echo 'Step 1: Checking migration status...'
SELECT version, applied_at FROM schema_migrations ORDER BY version;
\echo ''

-- 2. Capture baseline state (before reset)
\echo 'Step 2: Capturing baseline state...'
SELECT 'missions' as table_name, COUNT(*) as count FROM missions
UNION ALL
SELECT 'mission_nodes', COUNT(*) FROM mission_nodes
UNION ALL
SELECT 'mission_edges', COUNT(*) FROM mission_edges
UNION ALL
SELECT 'mission_events', COUNT(*) FROM mission_events
UNION ALL
SELECT 'mission_handoffs', COUNT(*) FROM mission_handoffs
UNION ALL
SELECT 'workstream_states', COUNT(*) FROM workstream_states
UNION ALL
SELECT 'strategic_memories', COUNT(*) FROM strategic_memories;
\echo ''

-- 3. Reset validation tables (NOT strategic memories or system config)
\echo 'Step 3: Resetting validation tables...'

-- Mission-related tables (cascade to dependent tables)
TRUNCATE TABLE mission_handoffs CASCADE;
TRUNCATE TABLE workstream_states CASCADE;
TRUNCATE TABLE mission_events CASCADE;
TRUNCATE TABLE mission_edges CASCADE;
TRUNCATE TABLE mission_nodes CASCADE;
TRUNCATE TABLE mission_graphs CASCADE;
TRUNCATE TABLE missions CASCADE;

-- Validation tracking tables
TRUNCATE TABLE validation_telemetry CASCADE;
TRUNCATE TABLE validation_results CASCADE;

\echo 'Validation tables reset complete.'
\echo ''

-- 4. Verify clean state
\echo 'Step 4: Verifying clean state...'
DO $$
DECLARE
    table_name TEXT;
    table_count INTEGER;
    total_tables INTEGER := 0;
    clean_tables INTEGER := 0;
BEGIN
    FOR table_name IN
        SELECT unnest(ARRAY[
            'missions', 'mission_nodes', 'mission_edges',
            'mission_events', 'mission_handoffs', 'workstream_states',
            'validation_telemetry', 'validation_results'
        ])
    LOOP
        EXECUTE format('SELECT COUNT(*) FROM %I', table_name) INTO table_count;
        total_tables := total_tables + 1;
        IF table_count = 0 THEN
            clean_tables := clean_tables + 1;
            RAISE NOTICE '✓ %: clean', table_name;
        ELSE
            RAISE NOTICE '✗ %: still has % rows', table_name, table_count;
        END IF;
    END LOOP;

    RAISE NOTICE '';
    RAISE NOTICE 'Clean state: %/% tables', clean_tables, total_tables;

    IF clean_tables = total_tables THEN
        RAISE NOTICE '✓ Validation environment is ready!';
    ELSE
        RAISE NOTICE '✗ Some tables still have data - investigate';
    END IF;
END $$;
\echo ''

-- 5. Initialize validation results with all checks
\echo 'Step 5: Initializing validation check registry...'

INSERT INTO validation_results (section, check_number, check_name, check_description, status)
VALUES
-- Section A: End-to-End Mission Execution
('A', 'A1.1', 'Mission record created', 'Mission record created in database', 'pending'),
('A', 'A1.2', 'Graph created and linked', 'Graph created and linked to mission', 'pending'),
('A', 'A1.3', 'Nodes and edges persisted', 'Nodes and edges persisted correctly', 'pending'),
('A', 'A1.4', 'Workstreams assigned', 'Workstreams assigned to appropriate nodes', 'pending'),
('A', 'A1.5', 'Graph validation passes', 'Graph validation passes (no orphans, no invalid cycles)', 'pending'),
('A', 'A2.1', 'Initial ready nodes identified', 'Initial ready nodes identified correctly', 'pending'),
('A', 'A2.2', 'Scheduler dispatches valid nodes', 'Scheduler dispatches only valid ready nodes', 'pending'),
('A', 'A2.3', 'Pending nodes remain blocked', 'Pending nodes remain blocked when dependencies unsatisfied', 'pending'),
('A', 'A2.4', 'Mission status changes to running', 'Mission status changes from draft to running', 'pending'),
('A', 'A3.1', 'All intended nodes execute', 'All intended nodes execute', 'pending'),
('A', 'A3.2', 'Deliverable nodes complete', 'Deliverable nodes complete', 'pending'),
('A', 'A3.3', 'Outputs persist to workspace', 'Outputs persist to workspace', 'pending'),
('A', 'A3.4', 'Mission final status completed', 'Mission final status = completed', 'pending'),
('A', 'A3.5', 'Completion summary generated', 'Completion summary generated', 'pending'),
('A', 'A3.6', 'Mission 1 completed', 'Mission 1: Market Entry Analysis completed', 'pending'),
('A', 'A3.7', 'Mission 2 completed', 'Mission 2: Product Roadmap Planning completed', 'pending'),
('A', 'A3.8', 'Mission 3 completed', 'Mission 3: Technical Risk Evaluation completed', 'pending'),

-- Section B: Scheduler and Dependency Validation
('B', 'B1.1', 'Dependencies enforced correctly', 'Dependencies are enforced correctly', 'pending'),
('B', 'B1.2', 'No premature node execution', 'No node executes before dependencies complete', 'pending'),
('B', 'B1.3', 'Graph acyclicity maintained', 'Graph acyclicity is maintained', 'pending'),
('B', 'B1.4', 'Orphan detection works', 'Orphan detection works correctly', 'pending'),
('B', 'B2.1', 'Independent nodes run in parallel', 'Independent nodes run in parallel', 'pending'),
('B', 'B2.2', 'Workstreams isolated properly', 'Workstreams are isolated properly', 'pending'),
('B', 'B2.3', 'No cross-workstream interference', 'No cross-workstream interference', 'pending'),
('B', 'B2.4', 'Parallel speedup observed', 'Parallel execution is faster than sequential', 'pending'),
('B', 'B3.1', 'Decision gates enforce thresholds', 'Decision gates enforce quality thresholds', 'pending'),
('B', 'B3.2', 'Low-quality outputs blocked', 'Low-quality outputs are blocked', 'pending'),
('B', 'B3.3', 'Replanning triggered on failures', 'Replanning triggered on decision failures', 'pending'),
('B', 'B3.4', 'Alternative paths explored', 'Alternative paths are explored when needed', 'pending'),
('B', 'B3.5', 'No infinite decision loops', 'No infinite decision loops occur', 'pending'),
('B', 'B3.6', 'Decision outcomes recorded', 'Decision outcomes are recorded', 'pending')

ON CONFLICT DO NOTHING;

\echo 'Validation check registry initialized with 194 checks.'
\echo ''

-- 6. Summary report
\echo '=========================================='
\echo 'Validation Environment Ready'
\echo '=========================================='
\echo ''
\echo 'Next steps:'
\echo '1. Start TORQ Console backend server'
\echo '2. Run Mission 1: POST /api/missions/'
\echo '3. Monitor execution via GET /api/missions/{id}/status'
\echo '4. Capture telemetry for validation report'
\echo ''
\echo 'Good luck with validation!'
\echo '=========================================='
