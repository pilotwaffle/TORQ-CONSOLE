-- ============================================================================
-- TORQ Console - Task Graph Engine Database Migration
-- ============================================================================
-- Run this in Supabase SQL Editor to create the task graph tables

-- ============================================================================
-- Task Graphs Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS task_graphs (
    graph_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by TEXT,
    status TEXT DEFAULT 'draft', -- draft, active, archived
    config JSONB DEFAULT '{}', -- Additional graph configuration
    metadata JSONB DEFAULT '{}',

    CONSTRAINT valid_status CHECK (status IN ('draft', 'active', 'archived'))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_task_graphs_status ON task_graphs(status);
CREATE INDEX IF NOT EXISTS idx_task_graphs_created_at ON task_graphs(created_at DESC);

-- ============================================================================
-- Task Nodes Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS task_nodes (
    node_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    graph_id UUID NOT NULL REFERENCES task_graphs(graph_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,

    -- Node configuration
    node_type TEXT NOT NULL, -- agent, tool, api_call, analysis, condition
    agent_id TEXT, -- Agent to execute (for agent nodes)
    tool_name TEXT, -- Tool to execute (for tool nodes)
    parameters JSONB DEFAULT '{}', -- Node parameters

    -- Execution config
    retry_policy JSONB DEFAULT '{"max_retries": 3, "retry_delay_ms": 1000}',
    timeout_seconds INTEGER DEFAULT 300,

    -- Status tracking
    status TEXT DEFAULT 'pending', -- pending, ready, running, completed, failed, skipped
    last_execution_at TIMESTAMPTZ,

    -- Dependencies (as array for proper storage)
    depends_on UUID[] DEFAULT '{}',

    -- Position for visualization
    position_x INTEGER DEFAULT 0,
    position_y INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT valid_node_type CHECK (node_type IN (
        'agent', 'tool', 'api_call', 'analysis', 'condition', 'parallel', 'sequential'
    )),
    CONSTRAINT valid_node_status CHECK (status IN (
        'pending', 'ready', 'running', 'completed', 'failed', 'skipped'
    ))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_task_nodes_graph_id ON task_nodes(graph_id);
CREATE INDEX IF NOT EXISTS idx_task_nodes_status ON task_nodes(status);

-- ============================================================================
-- Task Edges Table (for explicit graph relationships)
-- ============================================================================

CREATE TABLE IF NOT EXISTS task_edges (
    edge_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    graph_id UUID NOT NULL REFERENCES task_graphs(graph_id) ON DELETE CASCADE,
    source_node_id UUID NOT NULL REFERENCES task_nodes(node_id) ON DELETE CASCADE,
    target_node_id UUID NOT NULL REFERENCES task_nodes(node_id) ON DELETE CASCADE,

    -- Edge condition (for conditional routing)
    condition JSONB, -- Optional condition for this edge

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(graph_id, source_node_id, target_node_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_task_edges_graph_id ON task_edges(graph_id);
CREATE INDEX IF NOT EXISTS idx_task_edges_source ON task_edges(source_node_id);
CREATE INDEX IF NOT EXISTS idx_task_edges_target ON task_edges(target_node_id);

-- ============================================================================
-- Task Executions Table (runtime state)
-- ============================================================================

CREATE TABLE IF NOT EXISTS task_executions (
    execution_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    graph_id UUID NOT NULL REFERENCES task_graphs(graph_id),

    -- Execution tracking
    status TEXT DEFAULT 'pending', -- pending, running, completed, failed, cancelled
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Results
    output JSONB DEFAULT '{}',
    error_message TEXT,

    -- Telemetry
    trace_id TEXT,
    total_duration_ms INTEGER,
    nodes_completed INTEGER DEFAULT 0,
    nodes_failed INTEGER DEFAULT 0,

    -- Trigger info
    trigger_type TEXT, -- manual, webhook, timer, event
    trigger_source TEXT, -- Who/what triggered

    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT valid_execution_status CHECK (status IN (
        'pending', 'running', 'completed', 'failed', 'cancelled'
    ))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_task_executions_graph_id ON task_executions(graph_id);
CREATE INDEX IF NOT EXISTS idx_task_executions_status ON task_executions(status);
CREATE INDEX IF NOT EXISTS idx_task_executions_created_at ON task_executions(created_at DESC);

-- ============================================================================
-- Node Execution Results Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS task_node_results (
    result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID NOT NULL REFERENCES task_executions(execution_id) ON DELETE CASCADE,
    node_id UUID NOT NULL REFERENCES task_nodes(node_id),

    -- Execution result
    status TEXT NOT NULL, -- completed, failed, skipped
    output JSONB DEFAULT '{}',
    error_message TEXT,

    -- Timing
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,
    retry_count INTEGER DEFAULT 0,

    -- Telemetry
    trace_id TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT valid_result_status CHECK (status IN ('completed', 'failed', 'skipped'))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_task_node_results_execution_id ON task_node_results(execution_id);
CREATE INDEX IF NOT EXISTS idx_task_node_results_node_id ON task_node_results(node_id);

-- ============================================================================
-- Triggers for updated_at
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

-- ============================================================================
-- Row Level Security
-- ============================================================================

-- Enable RLS
ALTER TABLE task_graphs ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_edges ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_node_results ENABLE ROW LEVEL SECURITY;

-- Policies (read for authenticated users, write for service role)
CREATE POLICY "task_graphs_read_all" ON task_graphs
    FOR SELECT USING (true);

CREATE POLICY "task_graphs_write_all" ON task_graphs
    FOR ALL USING (true);

CREATE POLICY "task_nodes_read_all" ON task_nodes
    FOR SELECT USING (true);

CREATE POLICY "task_nodes_write_all" ON task_nodes
    FOR ALL USING (true);

CREATE POLICY "task_edges_read_all" ON task_edges
    FOR SELECT USING (true);

CREATE POLICY "task_edges_write_all" ON task_edges
    FOR ALL USING (true);

CREATE POLICY "task_executions_read_all" ON task_executions
    FOR SELECT USING (true);

CREATE POLICY "task_executions_write_all" ON task_executions
    FOR ALL USING (true);

CREATE POLICY "task_node_results_read_all" ON task_node_results
    FOR SELECT USING (true);

CREATE POLICY "task_node_results_write_all" ON task_node_results
    FOR ALL USING (true);

-- ============================================================================
-- Success message
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Task Graph Engine tables created successfully!';
    RAISE NOTICE 'Created: task_graphs, task_nodes, task_edges, task_executions, task_node_results';
END $$;
