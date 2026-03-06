-- ============================================================================
-- TORQ Console - Task Graph Engine v2 Enhancements
-- ============================================================================
--
-- This migration adds:
-- 1. Graph versioning support
-- 2. Dead letter queue for failed executions
-- 3. Execution telemetry tables
-- 4. Security limits (max nodes, runtime, output size)
-- ============================================================================

-- ============================================================================
-- Add Versioning to task_graphs
-- ============================================================================

ALTER TABLE task_graphs
ADD COLUMN IF NOT EXISTS version INT DEFAULT 1,
ADD COLUMN IF NOT EXISTS parent_graph_id UUID REFERENCES task_graphs(graph_id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_task_graphs_parent ON task_graphs(parent_graph_id);
CREATE INDEX IF NOT EXISTS idx_task_graphs_version ON task_graphs(graph_id, version DESC);

-- ============================================================================
-- Dead Letter Queue for Failed Executions
-- ============================================================================

CREATE TABLE IF NOT EXISTS task_dead_letters (
    dead_letter_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID NOT NULL,
    graph_id UUID NOT NULL REFERENCES task_graphs(graph_id),
    tenant_id TEXT DEFAULT 'default',

    -- Original execution info
    original_status TEXT NOT NULL,
    failure_reason TEXT NOT NULL,
    node_id UUID REFERENCES task_nodes(node_id),

    -- Recovery info
    retry_count INTEGER DEFAULT 0,
    last_attempt_at TIMESTAMPTZ,
    next_retry_at TIMESTAMPTZ,

    -- Status
    status TEXT DEFAULT 'pending', -- pending, retrying, recovered, permanently_failed

    -- Diagnostic
    error_details JSONB DEFAULT '{}',
    execution_snapshot JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT valid_dl_status CHECK (status IN (
        'pending', 'retrying', 'recovered', 'permanently_failed'
    ))
);

CREATE INDEX IF NOT EXISTS idx_task_dead_letters_execution ON task_dead_letters(execution_id);
CREATE INDEX IF NOT EXISTS idx_task_dead_letters_graph ON task_dead_letters(graph_id);
CREATE INDEX IF NOT EXISTS idx_task_dead_letters_status ON task_dead_letters(status);
CREATE INDEX IF NOT EXISTS idx_task_dead_letters_tenant ON task_dead_letters(tenant_id);

-- ============================================================================
-- Execution Telemetry
-- ============================================================================

CREATE TABLE IF NOT EXISTS task_telemetry_spans (
    span_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trace_id TEXT NOT NULL,
    execution_id UUID REFERENCES task_executions(execution_id) ON DELETE CASCADE,
    node_id UUID REFERENCES task_nodes(node_id),

    parent_span_id UUID,

    -- Span timing
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,

    -- Span metadata
    span_type TEXT NOT NULL, -- node, graph, retry, wait
    status TEXT NOT NULL, -- started, completed, failed

    -- Telemetry data
    metadata JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',

    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT valid_span_status CHECK (status IN (
        'started', 'completed', 'failed'
    ))
);

CREATE INDEX IF NOT EXISTS idx_task_telemetry_spans_trace ON task_telemetry_spans(trace_id);
CREATE INDEX IF NOT EXISTS idx_task_telemetry_spans_execution ON task_telemetry_spans(execution_id);
CREATE INDEX IF NOT EXISTS idx_task_telemetry_spans_node ON task_telemetry_spans(node_id);
CREATE INDEX IF NOT EXISTS idx_task_telemetry_spans_parent ON task_telemetry_spans(parent_span_id);
CREATE INDEX IF NOT EXISTS idx_task_telemetry_spans_started_at ON task_telemetry_spans(started_at DESC);

-- ============================================================================
-- Security Limits
-- ============================================================================

-- Add limits column to task_graphs for production safety
ALTER TABLE task_graphs
ADD COLUMN IF NOT EXISTS limits JSONB DEFAULT '{
    "max_nodes_per_graph": 100,
    "max_runtime_seconds": 3600,
    "max_parallel_nodes": 10,
    "max_output_size_bytes": 1048576
}'::jsonb;

-- ============================================================================
-- Trigger for updated_at on dead_letters
-- ============================================================================

CREATE TRIGGER update_task_dead_letters_updated_at
    BEFORE UPDATE ON task_dead_letters
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- RLS for new tables
-- ============================================================================

ALTER TABLE task_dead_letters ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_telemetry_spans ENABLE ROW LEVEL SECURITY;

CREATE POLICY "tenant_isolate_task_dead_letters" ON task_dead_letters
    FOR ALL
    USING (tenant_id = COALESCE(current_setting('request.jwt.claim.tenant_id', true), 'default'));

CREATE POLICY "task_dead_letters_read_own_tenant" ON task_dead_letters
    FOR SELECT
    USING (tenant_id = COALESCE(current_setting('request.jwt.claim.tenant_id', true), 'default'));

CREATE POLICY "tenant_isolate_task_telemetry_spans" ON task_telemetry_spans
    FOR ALL
    USING (
        EXISTS (
            SELECT 1
            FROM task_executions e
            WHERE e.execution_id = task_telemetry_spans.execution_id
              AND e.tenant_id = COALESCE(current_setting('request.jwt.claim.tenant_id', true), 'default')
        )
    );

CREATE POLICY "task_telemetry_spans_read_own_tenant" ON task_telemetry_spans
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1
            FROM task_executions e
            WHERE e.execution_id = task_telemetry_spans.execution_id
              AND e.tenant_id = COALESCE(current_setting('request.jwt.claim.tenant_id', true), 'default')
        )
    );
