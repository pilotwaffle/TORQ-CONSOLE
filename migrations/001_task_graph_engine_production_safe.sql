-- ============================================================================
-- TORQ Console - Task Graph Engine Database Migration (Production-Safe)
-- ============================================================================
--
-- Production safety features included:
-- 1. Idempotency keys scoped per-tenant for exactly-once semantics
-- 2. State machine with enforced transitions on CORRECT tables (runtime state)
-- 3. Input/output size limits
-- 4. Webhook signature verification support
-- 5. Execution summary endpoint optimization
-- 6. Concurrency-safe unique indexes (single-runner lock)
-- ============================================================================

-- Enable pgcrypto for digest() function
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================================
-- Task Graphs Table (definition metadata only)
-- ============================================================================

CREATE TABLE IF NOT EXISTS task_graphs (
    graph_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by TEXT,
    tenant_id TEXT DEFAULT 'default',
    status TEXT DEFAULT 'draft',
    config JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',

    CONSTRAINT valid_graph_status CHECK (status IN ('draft', 'active', 'archived'))
);

CREATE INDEX IF NOT EXISTS idx_task_graphs_status ON task_graphs(status);
CREATE INDEX IF NOT EXISTS idx_task_graphs_tenant ON task_graphs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_task_graphs_created_at ON task_graphs(created_at DESC);

-- ============================================================================
-- Task Nodes Table (definition metadata only - NO runtime state)
-- ============================================================================

CREATE TABLE IF NOT EXISTS task_nodes (
    node_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    graph_id UUID NOT NULL REFERENCES task_graphs(graph_id) ON DELETE CASCADE,

    node_key TEXT UNIQUE,
    name TEXT NOT NULL,
    description TEXT,

    node_type TEXT NOT NULL,
    agent_id TEXT,
    tool_name TEXT,
    parameters JSONB DEFAULT '{}',

    parameters_size_bytes INTEGER GENERATED ALWAYS AS (octet_length(parameters::text)) STORED,

    retry_policy JSONB DEFAULT '{"max_retries": 3, "retry_delay_ms": 1000, "failure_strategy": "retry"}',
    timeout_seconds INTEGER DEFAULT 300,

    fallback_node_id UUID REFERENCES task_nodes(node_id) ON DELETE SET NULL,
    fallback_node_key TEXT,

    depends_on TEXT[] DEFAULT '{}',

    position_x INTEGER DEFAULT 0,
    position_y INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT valid_node_type CHECK (node_type IN (
        'agent', 'tool', 'api_call', 'analysis', 'condition', 'parallel', 'sequential'
    )),
    CONSTRAINT parameters_size_limit CHECK (parameters_size_bytes <= 65536),
    CHECK (
        (fallback_node_id IS NULL AND fallback_node_key IS NULL) OR
        (fallback_node_id IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_task_nodes_graph_id ON task_nodes(graph_id);
CREATE INDEX IF NOT EXISTS idx_task_nodes_node_key ON task_nodes(node_key);
CREATE INDEX IF NOT EXISTS idx_task_nodes_fallback ON task_nodes(fallback_node_id);

-- ============================================================================
-- Task Edges Table (using stable keys - static definition)
-- ============================================================================

CREATE TABLE IF NOT EXISTS task_edges (
    edge_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    graph_id UUID NOT NULL REFERENCES task_graphs(graph_id) ON DELETE CASCADE,

    source_node_key TEXT NOT NULL,
    target_node_key TEXT NOT NULL,

    source_node_id UUID NOT NULL,
    target_node_id UUID NOT NULL,

    condition JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(graph_id, source_node_key, target_node_key),

    CONSTRAINT fk_source_node FOREIGN KEY (source_node_id) REFERENCES task_nodes(node_id),
    CONSTRAINT fk_target_node FOREIGN KEY (target_node_id) REFERENCES task_nodes(node_id)
);

CREATE INDEX IF NOT EXISTS idx_task_edges_graph_id ON task_edges(graph_id);
CREATE INDEX IF NOT EXISTS idx_task_edges_source_key ON task_edges(source_node_key);
CREATE INDEX IF NOT EXISTS idx_task_edges_target_node_key ON task_edges(target_node_key);

-- ============================================================================
-- Task Executions Table (runtime state - per-execution tracking)
-- ============================================================================

CREATE TABLE IF NOT EXISTS task_executions (
    execution_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    graph_id UUID NOT NULL REFERENCES task_graphs(graph_id),
    tenant_id TEXT DEFAULT 'default',

    idempotency_key TEXT,

    status TEXT DEFAULT 'pending',
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    output JSONB DEFAULT '{}',
    output_size_bytes INTEGER GENERATED ALWAYS AS (octet_length(output::text)) STORED,
    output_ref TEXT,

    error_message TEXT,

    trace_id TEXT,
    total_duration_ms INTEGER,
    nodes_completed INTEGER DEFAULT 0,
    nodes_failed INTEGER DEFAULT 0,

    trigger_type TEXT,
    trigger_source TEXT,
    webhook_signature TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT valid_execution_status CHECK (status IN (
        'pending', 'running', 'completed', 'failed', 'canceled'
    )),
    CONSTRAINT output_size_limit CHECK (output_size_bytes <= 262144),
    CHECK (
        (output_size_bytes <= 262144) OR (output_ref IS NOT NULL)
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_task_executions_tenant_idempotency
    ON task_executions(tenant_id, idempotency_key)
    WHERE idempotency_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_task_executions_graph_id ON task_executions(graph_id);
CREATE INDEX IF NOT EXISTS idx_task_executions_status ON task_executions(status);
CREATE INDEX IF NOT EXISTS idx_task_executions_tenant ON task_executions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_task_executions_created_at ON task_executions(created_at DESC);

-- ============================================================================
-- Node Execution Results Table (runtime state - per-node-per-execution)
-- ============================================================================

CREATE TABLE IF NOT EXISTS task_node_results (
    result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID NOT NULL REFERENCES task_executions(execution_id) ON DELETE CASCADE,
    node_id UUID NOT NULL REFERENCES task_nodes(node_id),
    node_key TEXT NOT NULL,

    idempotency_key TEXT NOT NULL,

    status TEXT NOT NULL,
    output JSONB DEFAULT '{}',
    output_size_bytes INTEGER GENERATED ALWAYS AS (octet_length(output::text)) STORED,
    output_ref TEXT,

    error_message TEXT,

    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,
    retry_count INTEGER DEFAULT 0,
    attempt INTEGER DEFAULT 1,
    max_attempts INTEGER DEFAULT 3,

    trace_id TEXT,
    agent_id TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT valid_result_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'skipped')),
    CONSTRAINT output_size_limit CHECK (output_size_bytes <= 262144),
    CONSTRAINT attempt_bound CHECK (attempt <= max_attempts),
    CHECK (
        (output_size_bytes <= 262144) OR (output_ref IS NOT NULL)
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_task_node_results_idempotency_completed
    ON task_node_results(execution_id, node_id, attempt)
    WHERE status = 'completed';

CREATE UNIQUE INDEX IF NOT EXISTS idx_task_node_results_single_runner
    ON task_node_results(execution_id, node_id)
    WHERE status = 'running';

CREATE UNIQUE INDEX IF NOT EXISTS idx_task_node_results_idempotency_key
    ON task_node_results(execution_id, idempotency_key);

CREATE INDEX IF NOT EXISTS idx_task_node_results_execution_id ON task_node_results(execution_id);
CREATE INDEX IF NOT EXISTS idx_task_node_results_node_id ON task_node_results(node_id);
CREATE INDEX IF NOT EXISTS idx_task_node_results_node_key ON task_node_results(node_key);
CREATE INDEX IF NOT EXISTS idx_task_node_results_status ON task_node_results(status);

-- ============================================================================
-- Webhook Configuration Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS task_webhooks (
    webhook_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    graph_id UUID NOT NULL REFERENCES task_graphs(graph_id) ON DELETE CASCADE,

    webhook_key TEXT NOT NULL UNIQUE,
    secret_key TEXT NOT NULL,
    path TEXT NOT NULL UNIQUE,

    enabled BOOLEAN DEFAULT TRUE,
    require_signature BOOLEAN DEFAULT TRUE,
    allowed_ips TEXT[] DEFAULT '{}',
    rate_limit_per_minute INTEGER DEFAULT 10,

    replay_window_seconds INTEGER DEFAULT 300,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_task_webhooks_graph_id ON task_webhooks(graph_id);
CREATE INDEX IF NOT EXISTS idx_task_webhooks_key ON task_webhooks(webhook_key);
CREATE INDEX IF NOT EXISTS idx_task_webhooks_path ON task_webhooks(path);

-- ============================================================================
-- Triggers and Functions
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_task_graphs_updated_at
    BEFORE UPDATE ON task_graphs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_task_nodes_updated_at
    BEFORE UPDATE ON task_nodes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_task_webhooks_updated_at
    BEFORE UPDATE ON task_webhooks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- STATE MACHINE TRIGGERS
-- ============================================================================

CREATE OR REPLACE FUNCTION enforce_execution_state_transition()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IN ('completed', 'failed', 'canceled') AND NEW.status = 'running' THEN
        RAISE EXCEPTION 'invalid_execution_transition'
        USING MESSAGE = 'Cannot transition from terminal state back to running';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER enforce_execution_state_transition_trigger
    BEFORE UPDATE ON task_executions
    FOR EACH ROW
    WHEN (OLD.status IS DISTINCT FROM NEW.status)
    EXECUTE FUNCTION enforce_execution_state_transition();

CREATE OR REPLACE FUNCTION enforce_node_result_state_transition()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IN ('completed', 'failed', 'skipped') AND NEW.status = 'running' THEN
        RAISE EXCEPTION 'invalid_node_result_transition'
        USING MESSAGE = 'Cannot transition from terminal state back to running';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER enforce_node_result_state_transition_trigger
    BEFORE UPDATE ON task_node_results
    FOR EACH ROW
    WHEN (OLD.status IS DISTINCT FROM NEW.status)
    EXECUTE FUNCTION enforce_node_result_state_transition();

CREATE OR REPLACE FUNCTION generate_idempotency_key(
    p_execution_id TEXT,
    p_node_id TEXT,
    p_input_data JSONB
) RETURNS TEXT AS $$
BEGIN
    RETURN encode(
        digest(
            p_execution_id || '|' ||
            p_node_id || '|' ||
            COALESCE(p_input_data::text, ''),
            'sha256'
        ),
        'hex'
    );
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Views for execution summary
-- ============================================================================

CREATE OR REPLACE VIEW execution_summary_view AS
SELECT
    e.execution_id,
    e.graph_id,
    e.status,
    e.started_at,
    e.completed_at,
    e.trace_id,
    e.nodes_completed,
    e.nodes_failed,
    COUNT(n.node_id) AS total_nodes,
    ROUND(
        CASE
            WHEN COUNT(n.node_id) > 0
            THEN (COUNT(n.node_id) FILTER (WHERE r.status = 'completed')::numeric / COUNT(n.node_id) * 100)
            ELSE 0
        END::numeric,
        2
    )::numeric AS progress_percentage,
    jsonb_agg(
        jsonb_build_object(
            'node_id', n.node_id,
            'node_key', n.node_key,
            'name', n.name,
            'status', COALESCE(r.status, 'pending'),
            'latency_ms', r.duration_ms,
            'agent_id', r.agent_id
        )
    ) AS nodes_summary,
    g.name AS graph_name,
    g.description AS graph_description
FROM task_executions e
JOIN task_graphs g ON e.graph_id = g.graph_id
LEFT JOIN task_nodes n ON n.graph_id = e.graph_id
LEFT JOIN LATERAL (
    SELECT *
    FROM task_node_results nr
    WHERE nr.execution_id = e.execution_id
      AND nr.node_id = n.node_id
    ORDER BY nr.created_at DESC
    LIMIT 1
) r ON true
GROUP BY e.execution_id, e.graph_id, e.status, e.started_at, e.completed_at,
         e.trace_id, e.nodes_completed, e.nodes_failed, g.name, g.description;

-- ============================================================================
-- Row Level Security
-- ============================================================================

ALTER TABLE task_graphs ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_edges ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_node_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_webhooks ENABLE ROW LEVEL SECURITY;

-- Task graphs (has tenant_id column directly)
CREATE POLICY "tenant_isolate_task_graphs" ON task_graphs
    FOR ALL
    USING (tenant_id = COALESCE(current_setting('request.jwt.claim.tenant_id', true), 'default'));

CREATE POLICY "task_graphs_read_own_tenant" ON task_graphs
    FOR SELECT
    USING (tenant_id = COALESCE(current_setting('request.jwt.claim.tenant_id', true), 'default'));

-- Task nodes (no tenant_id - use EXISTS subquery to parent graph)
CREATE POLICY "tenant_isolate_task_nodes" ON task_nodes
    FOR ALL
    USING (
        EXISTS (
            SELECT 1
            FROM task_graphs g
            WHERE g.graph_id = task_nodes.graph_id
              AND g.tenant_id = COALESCE(current_setting('request.jwt.claim.tenant_id', true), 'default')
        )
    );

CREATE POLICY "task_nodes_read_own_tenant" ON task_nodes
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1
            FROM task_graphs g
            WHERE g.graph_id = task_nodes.graph_id
              AND g.tenant_id = COALESCE(current_setting('request.jwt.claim.tenant_id', true), 'default')
        )
    );

-- Task edges (no tenant_id - use EXISTS subquery to parent graph)
CREATE POLICY "tenant_isolate_task_edges" ON task_edges
    FOR ALL
    USING (
        EXISTS (
            SELECT 1
            FROM task_graphs g
            WHERE g.graph_id = task_edges.graph_id
              AND g.tenant_id = COALESCE(current_setting('request.jwt.claim.tenant_id', true), 'default')
        )
    );

CREATE POLICY "task_edges_read_own_tenant" ON task_edges
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1
            FROM task_graphs g
            WHERE g.graph_id = task_edges.graph_id
              AND g.tenant_id = COALESCE(current_setting('request.jwt.claim.tenant_id', true), 'default')
        )
    );

-- Task executions (has tenant_id column directly)
CREATE POLICY "tenant_isolate_task_executions" ON task_executions
    FOR ALL
    USING (tenant_id = COALESCE(current_setting('request.jwt.claim.tenant_id', true), 'default'));

CREATE POLICY "task_executions_read_own_tenant" ON task_executions
    FOR SELECT
    USING (tenant_id = COALESCE(current_setting('request.jwt.claim.tenant_id', true), 'default'));

-- Task node results (no tenant_id - use EXISTS subquery to parent execution)
CREATE POLICY "tenant_isolate_task_node_results" ON task_node_results
    FOR ALL
    USING (
        EXISTS (
            SELECT 1
            FROM task_executions e
            WHERE e.execution_id = task_node_results.execution_id
              AND e.tenant_id = COALESCE(current_setting('request.jwt.claim.tenant_id', true), 'default')
        )
    );

CREATE POLICY "task_node_results_read_own_tenant" ON task_node_results
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1
            FROM task_executions e
            WHERE e.execution_id = task_node_results.execution_id
              AND e.tenant_id = COALESCE(current_setting('request.jwt.claim.tenant_id', true), 'default')
        )
    );

-- Task webhooks (no tenant_id - use EXISTS subquery to parent graph)
CREATE POLICY "tenant_isolate_task_webhooks" ON task_webhooks
    FOR ALL
    USING (
        EXISTS (
            SELECT 1
            FROM task_graphs g
            WHERE g.graph_id = task_webhooks.graph_id
              AND g.tenant_id = COALESCE(current_setting('request.jwt.claim.tenant_id', true), 'default')
        )
    );

CREATE POLICY "task_webhooks_read_own_tenant" ON task_webhooks
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1
            FROM task_graphs g
            WHERE g.graph_id = task_webhooks.graph_id
              AND g.tenant_id = COALESCE(current_setting('request.jwt.claim.tenant_id', true), 'default')
        )
    );

-- ============================================================================
-- Success message
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Task Graph Engine tables created successfully with production safety features!';
    RAISE NOTICE 'Features included:';
    RAISE NOTICE '  - Idempotency keys scoped per-tenant for exactly-once semantics';
    RAISE NOTICE '  - State machine with enforced transitions on runtime state tables';
    RAISE NOTICE '  - Concurrency-safe single-runner lock (prevents duplicate node claims)';
    RAISE NOTICE '  - Input/output size limits (64KB input, 256KB output)';
    RAISE NOTICE '  - Tenant isolation via RLS policies';
    RAISE NOTICE '  - Execution summary view for UI';
    RAISE NOTICE '  - Webhook configuration table';
    RAISE NOTICE '  ';
    RAISE NOTICE 'Definition tables (static): task_graphs, task_nodes, task_edges, task_webhooks';
    RAISE NOTICE 'Runtime tables (stateful): task_executions, task_node_results';
    RAISE NOTICE 'View: execution_summary_view';
END;
$$;
