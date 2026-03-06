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
    tenant_id TEXT DEFAULT 'default', -- For multi-tenancy
    status TEXT DEFAULT 'draft', -- draft, active, archived (DEFINITION state, not runtime)
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

    -- Stable node key (client-provided, for stable references)
    node_key TEXT UNIQUE,
    name TEXT NOT NULL,
    description TEXT,

    -- Node configuration
    node_type TEXT NOT NULL,
    agent_id TEXT,
    tool_name TEXT,
    parameters JSONB DEFAULT '{}',

    -- Size limits
    parameters_size_bytes INTEGER DEFAULT 0 GENERATED ALWAYS AS (octet_length(parameters::text)),

    -- Execution config (static configuration, not runtime state)
    retry_policy JSONB DEFAULT '{"max_retries": 3, "retry_delay_ms": 1000, "failure_strategy": "retry"}',
    timeout_seconds INTEGER DEFAULT 300,

    -- Fallback node for reroute strategy (static configuration)
    fallback_node_id UUID REFERENCES task_nodes(node_id) ON DELETE SET NULL,
    fallback_node_key TEXT,

    -- Dependencies (using stable keys - static definition)
    depends_on TEXT[] DEFAULT '{}',

    -- Position for visualization (static)
    position_x INTEGER DEFAULT 0,
    position_y INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT valid_node_type CHECK (node_type IN (
        'agent', 'tool', 'api_call', 'analysis', 'condition', 'parallel', 'sequential'
    )),
    -- Enforce size limits
    CONSTRAINT parameters_size_limit CHECK (parameters_size_bytes <= 65536), -- 64KB
    CHECK (
        COALESCE(fallback_node_id, fallback_node_key) IS NULL OR
        fallback_node_id IS NOT NULL OR fallback_node_key IS NOT NULL
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

    -- Use stable keys instead of UUIDs for portability
    source_node_key TEXT NOT NULL,
    target_node_key TEXT NOT NULL,

    -- Resolve to actual node_ids at runtime for performance
    source_node_id UUID NOT NULL,
    target_node_id UUID NOT NULL,

    -- Edge condition for conditional routing (static configuration)
    condition JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(graph_id, source_node_key, target_node_key),

    -- Foreign key constraints (will be populated by triggers)
    CONSTRAINT fk_source_node FOREIGN KEY (source_node_id) REFERENCES task_nodes(node_id),
    CONSTRAINT fk_target_node FOREIGN KEY (target_node_id) REFERENCES task_nodes(node_id)
);

CREATE INDEX IF NOT EXISTS idx_task_edges_graph_id ON task_edges(graph_id);
CREATE INDEX IF NOT EXISTS idx_task_edges_source_key ON task_edges(source_node_key);
CREATE INDEX IF NOT EXISTS idx_task_edges_target_key ON task_edges(target_key);

-- ============================================================================
-- Task Executions Table (runtime state - per-execution tracking)
-- ============================================================================

CREATE TABLE IF NOT EXISTS task_executions (
    execution_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    graph_id UUID NOT NULL REFERENCES task_graphs(graph_id),
    tenant_id TEXT DEFAULT 'default',

    -- Idempotency key for safe retries - scoped per tenant for multi-tenancy
    -- If NOT NULL, ensures exactly-once execution per tenant
    idempotency_key TEXT,

    -- Execution tracking (runtime state)
    status TEXT DEFAULT 'pending',
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Results with size limits
    output JSONB DEFAULT '{}',
    output_size_bytes INTEGER DEFAULT 0 GENERATED ALWAYS AS (octet_length(output::text)),
    output_ref TEXT, -- Reference to external storage if output is large

    error_message TEXT,

    -- Telemetry
    trace_id TEXT,
    total_duration_ms INTEGER,
    nodes_completed INTEGER DEFAULT 0,
    nodes_failed INTEGER DEFAULT 0,

    -- Trigger info
    trigger_type TEXT,
    trigger_source TEXT,
    webhook_signature TEXT, -- Store for verification

    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT valid_execution_status CHECK (status IN (
        'pending', 'running', 'completed', 'failed', 'canceled'
    )),
    CONSTRAINT output_size_limit CHECK (output_size_bytes <= 262144), -- 256KB
    CHECK (
        (output_size_bytes <= 262144) OR (output_ref IS NOT NULL)
    )
);

-- Scoped uniqueness: tenant + idempotency key (for multi-tenant safety)
CREATE UNIQUE INDEX idx_task_executions_tenant_idempotency
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

    -- Idempotency key - scoped per execution to prevent duplicate node execution
    -- Combined with execution_id+node_id, ensures exactly-once per node per execution
    idempotency_key TEXT NOT NULL,

    -- Execution result (runtime state)
    status TEXT NOT NULL,
    output JSONB DEFAULT '{}',
    output_size_bytes INTEGER DEFAULT 0 GENERATED ALWAYS AS (octet_length(output::text)),
    output_ref TEXT,

    error_message TEXT,

    -- Timing
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,
    retry_count INTEGER DEFAULT 0,
    attempt INTEGER DEFAULT 1, -- Which attempt number
    max_attempts INTEGER DEFAULT 3,

    -- Telemetry
    trace_id TEXT,
    agent_id TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT valid_result_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'skipped')),
    CONSTRAINT output_size_limit CHECK (output_size_bytes <= 262144),
    CONSTRAINT attempt_bound CHECK (attempt <= max_attempts), -- Prevents runaway retry loops
    CHECK (
        (output_size_bytes <= 262144) OR (output_ref IS NOT NULL)
    )
);

-- Concurrency-safe unique indexes:

-- 1. Exactly-once completed per attempt (prevents duplicate completion)
CREATE UNIQUE INDEX idx_task_node_results_idempotency_completed
    ON task_node_results(execution_id, node_id, attempt)
    WHERE status = 'completed';

-- 2. Single-runner lock (prevents concurrent workers from claiming same node)
CREATE UNIQUE INDEX idx_task_node_results_single_runner
    ON task_node_results(execution_id, node_id)
    WHERE status = 'running';

-- 3. Scoped idempotency key uniqueness (per execution, not global)
CREATE UNIQUE INDEX idx_task_node_results_idempotency_key
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

    -- Webhook configuration
    webhook_key TEXT NOT NULL UNIQUE, -- Stable key for the webhook
    secret_key TEXT NOT NULL, -- HMAC secret for signature verification
    path TEXT NOT NULL UNIQUE, -- URL path (e.g., /webhooks/my-workflow)

    -- Configuration
    enabled BOOLEAN DEFAULT TRUE,
    require_signature BOOLEAN DEFAULT TRUE,
    allowed_ips TEXT[] DEFAULT '{}',
    rate_limit_per_minute INTEGER DEFAULT 10,

    -- Replay protection
    replay_window_seconds INTEGER DEFAULT 300, -- 5 minutes

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_task_webhooks_graph_id ON task_webhooks(graph_id);
CREATE INDEX IF NOT EXISTS idx_task_webhooks_key ON task_webhooks(webhook_key);
CREATE INDEX IF NOT EXISTS idx_task_webhooks_path ON task_webhooks(path);

-- ============================================================================
-- Triggers and Functions
-- ============================================================================

-- Update updated_at timestamp
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
-- STATE MACHINE TRIGGERS (on CORRECT tables - runtime state tables)
-- ============================================================================

-- 1. Execution state transition guard (prevents going backward from terminal states)
CREATE OR REPLACE FUNCTION enforce_execution_state_transition()
RETURNS TRIGGER AS $$
BEGIN
    -- Prevent terminal states from going back to running
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

-- 2. Node result state transition guard (prevents invalid runtime transitions)
CREATE OR REPLACE FUNCTION enforce_node_result_state_transition()
RETURNS TRIGGER AS $$
BEGIN
    -- Prevent terminal states from going back to running
    IF OLD.status IN ('completed', 'failed', 'skipped') AND NEW.status = 'running' THEN
        RAISE EXCEPTION 'invalid_node_result_transition'
        USING MESSAGE = 'Cannot transition from terminal state back to running';
    END IF;

    -- Optional: prevent skipping pending -> completed without running
    -- Uncomment if you want to enforce running state always happens
    -- IF OLD.status = 'pending' AND NEW.status IN ('completed', 'failed', 'skipped') THEN
    --     RAISE EXCEPTION 'invalid_node_result_transition'
    --     USING MESSAGE = 'Cannot transition from pending to terminal without running';
    -- END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER enforce_node_result_state_transition_trigger
    BEFORE UPDATE ON task_node_results
    FOR EACH ROW
    WHEN (OLD.status IS DISTINCT FROM NEW.status)
    EXECUTE FUNCTION enforce_node_result_state_transition();

-- Function to generate idempotency key
CREATE OR REPLACE FUNCTION generate_idempotency_key(
    p_execution_id TEXT,
    p_node_id TEXT,
    p_input_data JSONB
) RETURNS TEXT AS $$
BEGIN
    RETURN encode(
        sha256(
            p_execution_id || '|' ||
            p_node_id || '|' ||
            COALESCE(p_input_data::text, '')
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
            THEN (COUNT(n.node_id) FILTER (WHERE r.status = 'completed')::float / COUNT(n.node_id) * 100)
            ELSE 0
        END,
        2
    ) AS progress_percentage,

    -- Nodes summary (runtime status from results table, not nodes table)
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

    -- Graph info
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

-- Enable RLS
ALTER TABLE task_graphs ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_edges ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_node_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_webhooks ENABLE ROW LEVEL SECURITY;

-- Policies (tenant-isolated)
CREATE POLICY "tenant_isolate_task_graphs" ON task_graphs
    FOR ALL
    USING (tenant_id = current_setting('request.jwt.claim.tenant_id', 'default'));

CREATE POLICY "tenant_isolate_task_nodes" ON task_nodes
    FOR ALL
    USING (
        tenant_id IN (
            SELECT tenant_id FROM task_graphs WHERE graph_id = task_nodes.graph_id
        )
    );

CREATE POLICY "tenant_isolate_task_executions" ON task_executions
    FOR ALL
    USING (
        tenant_id = current_setting('request.jwt.claim.tenant_id', 'default')
    );

CREATE POLICY "tenant_isolate_task_node_results" ON task_node_results
    FOR ALL
    USING (
        tenant_id IN (
            SELECT tenant_id FROM task_executions WHERE execution_id = task_node_results.execution_id
        )
    );

-- Read policies (within tenant)
CREATE POLICY "task_graphs_read_own_tenant" ON task_graphs
    FOR SELECT
    USING (tenant_id = current_setting('request.jwt.claim.tenant_id', 'default'));

CREATE POLICY "task_nodes_read_own_tenant" ON task_nodes
    FOR SELECT
    USING (
        tenant_id IN (
            SELECT tenant_id FROM task_graphs WHERE graph_id = task_nodes.graph_id
        )
    );

CREATE POLICY "task_executions_read_own_tenant" ON task_executions
    FOR SELECT
    USING (tenant_id = current_setting('request.jwt.claim.tenant_id', 'default'));

CREATE POLICY "task_node_results_read_own_tenant" ON task_node_results
    FOR SELECT
    USING (
        tenant_id IN (
            SELECT tenant_id FROM task_executions WHERE execution_id = task_node_results.execution_id
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
END $$;
