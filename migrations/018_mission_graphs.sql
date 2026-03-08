-- Migration 018: Mission Graph Planning
-- Purpose: Support structured mission execution with dependency graphs
-- Phase 5: Mission Graph Planning
-- Created: 2026-03-07

-- Missions table
CREATE TABLE IF NOT EXISTS missions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    mission_type TEXT NOT NULL CHECK (mission_type IN ('analysis', 'planning', 'evaluation', 'design', 'transformation')),
    objective TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'planned', 'scheduled', 'running', 'paused', 'completed', 'failed', 'cancelled')),

    -- Scope and context
    scope JSONB DEFAULT '{}',
    context JSONB DEFAULT '{}',
    constraints JSONB DEFAULT '{}',

    -- Strategic memory integration
    injected_memory_ids UUID[] DEFAULT '{}',
    reasoning_strategy TEXT CHECK (reasoning_strategy IN ('decomposition_first', 'risk_first', 'evidence_weighted', 'checklist_driven', 'contradiction_first', 'hypothesis_driven')),

    -- Results
    overall_score NUMERIC,
    deliverables TEXT[] DEFAULT '{}',

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_missions_status ON missions(status);
CREATE INDEX idx_missions_type ON missions(mission_type);

-- Mission graphs table
CREATE TABLE IF NOT EXISTS mission_graphs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    version TEXT NOT NULL DEFAULT '1.0',
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'validating', 'validated', 'active', 'archived')),

    -- Graph metadata
    graph_metadata JSONB DEFAULT '{}',

    -- Validation
    validation_errors TEXT[] DEFAULT '{}',
    validation_warnings TEXT[] DEFAULT '{}',

    -- Statistics
    node_count INTEGER DEFAULT 0,
    edge_count INTEGER DEFAULT 0,
    estimated_duration_seconds INTEGER,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(mission_id, version)
);

CREATE INDEX idx_mission_graphs_mission ON mission_graphs(mission_id);
CREATE INDEX idx_mission_graphs_status ON mission_graphs(status);

-- Mission nodes table
CREATE TABLE IF NOT EXISTS mission_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    graph_id UUID NOT NULL REFERENCES mission_graphs(id) ON DELETE CASCADE,
    mission_id UUID NOT NULL REFERENCES missions(id) ON DELETE CASCADE,

    -- Node classification
    node_type TEXT NOT NULL CHECK (node_type IN ('objective', 'task', 'decision', 'evidence', 'deliverable')),
    title TEXT NOT NULL,
    description TEXT,

    -- Execution
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'ready', 'running', 'blocked', 'completed', 'failed', 'skipped')),
    priority TEXT DEFAULT 'medium' CHECK (priority IN ('critical', 'high', 'medium', 'low')),

    -- Agent assignment
    agent_type TEXT CHECK (agent_type IN ('strategic_planner', 'domain_lead', 'specialist', 'synthesizer', 'risk_qa', 'executive')),
    reasoning_strategy TEXT CHECK (reasoning_strategy IN ('decomposition_first', 'risk_first', 'evidence_weighted', 'checklist_driven', 'contradiction_first', 'hypothesis_driven')),

    -- Requirements
    input_requirements JSONB DEFAULT '{}',
    output_schema JSONB DEFAULT '{}',

    -- Dependencies (denormalized for fast access)
    depends_on_nodes UUID[] DEFAULT '{}',
    blocked_by_nodes UUID[] DEFAULT '{}',
    informs_nodes UUID[] DEFAULT '{}',

    -- Decision-specific
    decision_condition JSONB,
    decision_outcome TEXT,  -- Which branch was taken

    -- Evidence-specific
    evidence_type TEXT,
    required_by_nodes UUID[] DEFAULT '{}',

    -- Deliverable-specific
    deliverable_type TEXT,
    format_spec JSONB,

    -- Workspace linkage
    workspace_id UUID REFERENCES workspaces(id) ON DELETE SET NULL,

    -- Strategic memory
    injected_memory_ids UUID[] DEFAULT '{}',

    -- Timing
    estimated_duration_seconds INTEGER,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Results
    output_count INTEGER DEFAULT 0,
    error_message TEXT
);

CREATE INDEX idx_mission_nodes_graph ON mission_nodes(graph_id);
CREATE INDEX idx_mission_nodes_mission ON mission_nodes(mission_id);
CREATE INDEX idx_mission_nodes_status ON mission_nodes(status);
CREATE INDEX idx_mission_nodes_type ON mission_nodes(node_type);
CREATE INDEX idx_mission_nodes_agent ON mission_nodes(agent_type);
CREATE INDEX idx_mission_nodes_workspace ON mission_nodes(workspace_id) WHERE workspace_id IS NOT NULL;

-- GIN index for dependency arrays
CREATE INDEX idx_mission_nodes_depends_on ON mission_nodes USING GIN(depends_on_nodes);
CREATE INDEX idx_mission_nodes_blocked_by ON mission_nodes USING GIN(blocked_by_nodes);

-- Mission edges table
CREATE TABLE IF NOT EXISTS mission_edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    graph_id UUID NOT NULL REFERENCES mission_graphs(id) ON DELETE CASCADE,
    mission_id UUID NOT NULL REFERENCES missions(id) ON DELETE CASCADE,

    source_node_id UUID NOT NULL REFERENCES mission_nodes(id) ON DELETE CASCADE,
    target_node_id UUID NOT NULL REFERENCES mission_nodes(id) ON DELETE CASCADE,
    edge_type TEXT NOT NULL CHECK (edge_type IN ('depends_on', 'informs', 'blocks', 'branches_to', 'produces')),

    -- Conditional edges
    condition JSONB,

    -- Tracking
    satisfied BOOLEAN DEFAULT FALSE,
    satisfied_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_mission_edges_graph ON mission_edges(graph_id);
CREATE INDEX idx_mission_edges_source ON mission_edges(source_node_id);
CREATE INDEX idx_mission_edges_target ON mission_edges(target_node_id);
CREATE INDEX idx_mission_edges_type ON mission_edges(edge_type);

-- Mission node outputs table
CREATE TABLE IF NOT EXISTS mission_node_outputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_id UUID NOT NULL REFERENCES mission_nodes(id) ON DELETE CASCADE,
    mission_id UUID NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    workspace_id UUID REFERENCES workspaces(id) ON DELETE SET NULL,

    output_type TEXT NOT NULL,  -- reasoning, evidence, deliverable, decision
    content JSONB NOT NULL DEFAULT '{}',

    -- Quality metrics
    confidence_score NUMERIC,
    contradiction_count INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_mission_node_outputs_node ON mission_node_outputs(node_id);
CREATE INDEX idx_mission_node_outputs_mission ON mission_node_outputs(mission_id);
CREATE INDEX idx_mission_node_outputs_workspace ON mission_node_outputs(workspace_id) WHERE workspace_id IS NOT NULL;

-- Decision outcomes table
CREATE TABLE IF NOT EXISTS decision_outcomes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_id UUID NOT NULL REFERENCES mission_nodes(id) ON DELETE CASCADE,
    mission_id UUID NOT NULL REFERENCES missions(id) ON DELETE CASCADE,

    gate_type TEXT NOT NULL,
    condition JSONB NOT NULL,
    passed BOOLEAN NOT NULL,
    actual_value NUMERIC NOT NULL,
    decision TEXT NOT NULL,  -- continue, stop, spawn_validation, escalate, alternate_branch
    reason TEXT,

    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_decision_outcomes_node ON decision_outcomes(node_id);
CREATE INDEX idx_decision_outcomes_mission ON decision_outcomes(mission_id);

-- Workstreams table
CREATE TABLE IF NOT EXISTS workstreams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    graph_id UUID NOT NULL REFERENCES mission_graphs(id) ON DELETE CASCADE,

    name TEXT NOT NULL,
    domain TEXT NOT NULL,  -- finance, operations, market, compliance, etc.
    lead_agent_type TEXT NOT NULL CHECK (lead_agent_type IN ('strategic_planner', 'domain_lead', 'specialist', 'synthesizer', 'risk_qa', 'executive')),

    -- Nodes in this workstream
    node_ids UUID[] DEFAULT '{}',

    -- Status
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'ready', 'running', 'blocked', 'completed', 'failed')),
    progress_percent NUMERIC DEFAULT 0.0,

    -- Dependencies
    depends_on_workstreams UUID[] DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_workstreams_mission ON workstreams(mission_id);
CREATE INDEX idx_workstreams_domain ON workstreams(domain);
CREATE INDEX idx_workstreams_lead ON workstreams(lead_agent_type);

-- Views for common queries

-- Active missions with their graphs
CREATE OR REPLACE VIEW active_missions_with_graphs AS
SELECT
    m.id,
    m.title,
    m.mission_type,
    m.objective,
    m.status,
    g.id as graph_id,
    g.version as graph_version,
    g.node_count,
    g.status as graph_status,
    m.started_at,
    m.completed_at
FROM missions m
LEFT JOIN mission_graphs g ON g.id = (
    SELECT id FROM mission_graphs
    WHERE mission_id = m.id
    ORDER BY created_at DESC
    LIMIT 1
)
WHERE m.status IN ('planned', 'scheduled', 'running')
ORDER BY m.created_at DESC;

-- Ready nodes for execution
CREATE OR REPLACE VIEW ready_mission_nodes AS
SELECT
    n.id,
    n.mission_id,
    n.graph_id,
    n.node_type,
    n.title,
    n.agent_type,
    n.priority,
    COUNT(DISTINCT unnest(n.depends_on_nodes)) FILTER (
        WHERE NOT EXISTS (
            SELECT 1 FROM mission_nodes dep
            WHERE dep.id = unnest(n.depends_on_nodes)
            AND dep.status NOT IN ('completed', 'skipped')
        )
    ) as satisfied_dependencies
FROM mission_nodes n
WHERE n.status IN ('pending', 'ready')
  AND (
    -- All dependencies satisfied or no dependencies
    cardinality(n.depends_on_nodes) FILTER (
        WHERE NOT EXISTS (
            SELECT 1 FROM mission_nodes dep
            WHERE dep.id = ANY(n.depends_on_nodes)
            AND dep.status NOT IN ('completed', 'skipped')
        )
    ) = 0
  )
GROUP BY n.id, n.mission_id, n.graph_id, n.node_type, n.title, n.agent_type, n.priority
ORDER BY
  CASE n.priority
    WHEN 'critical' THEN 1
    WHEN 'high' THEN 2
    WHEN 'medium' THEN 3
    WHEN 'low' THEN 4
  END,
  n.node_type;  -- Objectives first, then tasks, decisions

-- Mission progress summary
CREATE OR REPLACE VIEW mission_progress_summary AS
SELECT
    m.id as mission_id,
    m.title,
    m.status,
    COUNT(n.id) as total_nodes,
    SUM(CASE WHEN n.status = 'completed' THEN 1 ELSE 0 END) as completed_nodes,
    SUM(CASE WHEN n.status = 'failed' THEN 1 ELSE 0 END) as failed_nodes,
    SUM(CASE WHEN n.status = 'skipped' THEN 1 ELSE 0 END) as skipped_nodes,
    SUM(CASE WHEN n.status IN ('pending', 'ready', 'running', 'blocked') THEN 1 ELSE 0 END) as pending_nodes,
    ROUND(
        SUM(CASE WHEN n.status IN ('completed', 'skipped') THEN 1 ELSE 0 END)::NUMERIC /
        NULLIF(COUNT(n.id), 0) * 100,
        1
    ) as progress_percent
FROM missions m
LEFT JOIN mission_nodes n ON n.mission_id = m.id
GROUP BY m.id, m.title, m.status
ORDER BY m.created_at DESC;

COMMENT ON TABLE missions IS 'Top-level mission records representing complex consulting work.';
COMMENT ON TABLE mission_graphs IS 'Graph metadata and versioning for mission execution.';
COMMENT ON TABLE mission_nodes IS 'Individual nodes in the mission graph (objectives, tasks, decisions, evidence, deliverables).';
COMMENT ON TABLE mission_edges IS 'Relationships between nodes (dependencies, information flow, blocking, branching).';
COMMENT ON TABLE mission_node_outputs IS 'Artifacts and outputs generated by node execution.';
COMMENT ON TABLE decision_outcomes IS 'Results from decision gate evaluations.';
COMMENT ON TABLE workstreams IS 'Logical groupings of related nodes, owned by domain leads.';

COMMENT ON VIEW active_missions_with_graphs IS 'Missions currently being executed with their active graph versions.';
COMMENT ON VIEW ready_mission_nodes IS 'Nodes ready for immediate execution (dependencies satisfied).';
COMMENT ON VIEW mission_progress_summary IS 'Progress tracking for all missions with node-level breakdown.';
