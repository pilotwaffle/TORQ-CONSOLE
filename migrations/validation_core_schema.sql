-- ============================================================================
-- Validation Core Schema
-- Simplified schema for Phase 5.1 validation
-- This creates the minimum tables needed to run validation missions
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- Missions Table
-- ============================================================================
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

-- ============================================================================
-- Mission Graphs Table
-- ============================================================================
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

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_mission_graphs_mission ON mission_graphs(mission_id);

-- ============================================================================
-- Mission Nodes Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS mission_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    graph_id UUID NOT NULL REFERENCES mission_graphs(id) ON DELETE CASCADE,

    -- Node identification
    node_type TEXT NOT NULL CHECK (node_type IN ('objective', 'task', 'decision', 'evidence', 'deliverable')),
    title TEXT NOT NULL,
    description TEXT,

    -- Execution state
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'ready', 'running', 'completed', 'skipped', 'failed', 'blocked')),

    -- Dependencies
    depends_on UUID[] DEFAULT '{}',
    blocks UUID[] DEFAULT '{}',

    -- Assignment
    workstream_id UUID,
    agent_type TEXT,

    -- Content
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',

    -- Quality metrics
    confidence_score NUMERIC CHECK (confidence_score >= 0 AND confidence_score <= 1),
    evaluation_score NUMERIC CHECK (evaluation_score >= 0 AND evaluation_score <= 1),

    -- Timing
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_mission_nodes_mission ON mission_nodes(mission_id);
CREATE INDEX idx_mission_nodes_graph ON mission_nodes(graph_id);
CREATE INDEX idx_mission_nodes_status ON mission_nodes(status);
CREATE INDEX idx_mission_nodes_workstream ON mission_nodes(workstream_id);

-- ============================================================================
-- Mission Edges Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS mission_edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    graph_id UUID NOT NULL REFERENCES mission_graphs(id) ON DELETE CASCADE,

    -- Edge identification
    from_node_id UUID NOT NULL REFERENCES mission_nodes(id) ON DELETE CASCADE,
    to_node_id UUID NOT NULL REFERENCES mission_nodes(id) ON DELETE CASCADE,
    edge_type TEXT NOT NULL CHECK (edge_type IN ('depends_on', 'informs', 'blocks', 'branches_to', 'produces')),

    -- Edge metadata
    weight NUMERIC DEFAULT 1.0,
    condition JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_mission_edges_mission ON mission_edges(mission_id);
CREATE INDEX idx_mission_edges_graph ON mission_edges(graph_id);
CREATE INDEX idx_mission_edges_from ON mission_edges(from_node_id);
CREATE INDEX idx_mission_edges_to ON mission_edges(to_node_id);

-- ============================================================================
-- Mission Events Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS mission_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL REFERENCES missions(id) ON DELETE CASCADE,

    -- Event identification
    event_type TEXT NOT NULL,
    node_id UUID REFERENCES mission_nodes(id) ON DELETE CASCADE,
    workstream_id UUID,

    -- Event data
    event_data JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',

    -- Timing
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_mission_events_mission ON mission_events(mission_id);
CREATE INDEX idx_mission_events_node ON mission_events(node_id);
CREATE INDEX idx_mission_events_type ON mission_events(event_type);
CREATE INDEX idx_mission_events_timestamp ON mission_events(timestamp);

-- ============================================================================
-- Mission Handoffs Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS mission_handoffs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL REFERENCES missions(id) ON DELETE CASCADE,

    -- Source information
    from_node_id UUID NOT NULL REFERENCES mission_nodes(id) ON DELETE CASCADE,
    to_node_id UUID REFERENCES mission_nodes(id) ON DELETE SET NULL,
    from_agent_type TEXT NOT NULL,
    to_agent_type TEXT,

    -- Handoff summary
    handoff_summary JSONB NOT NULL DEFAULT '{}',

    -- Quality metrics
    confidence NUMERIC NOT NULL DEFAULT 0.5 CHECK (confidence >= 0 AND confidence <= 1),
    confidence_basis TEXT,

    -- Unresolved items
    unresolved_questions TEXT[] DEFAULT '{}',
    assumptions_made TEXT[] DEFAULT '{}',
    limitations TEXT[] DEFAULT '{}',

    -- Risk flags
    risks TEXT[] DEFAULT '{}',
    severity_indicators TEXT[] DEFAULT '{}',

    -- Artifacts
    artifacts JSONB DEFAULT '{}',
    workspace_entries TEXT[] DEFAULT '{}',

    -- Routing
    recommended_consumers TEXT[] DEFAULT '{}',
    required_next_actions TEXT[] DEFAULT '{}',

    -- Delivery tracking
    status TEXT NOT NULL DEFAULT 'created' CHECK (status IN ('created', 'in_transit', 'delivered', 'acknowledged', 'failed')),
    delivery_attempts INTEGER DEFAULT 0,
    delivered_to TEXT[] DEFAULT '{}',
    acknowledged_by TEXT[] DEFAULT '{}',

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_mission_handoffs_mission ON mission_handoffs(mission_id);
CREATE INDEX idx_mission_handoffs_from_node ON mission_handoffs(from_node_id);
CREATE INDEX idx_mission_handoffs_to_node ON mission_handoffs(to_node_id) WHERE to_node_id IS NOT NULL;
CREATE INDEX idx_mission_handoffs_status ON mission_handoffs(status);

-- ============================================================================
-- Workstream States Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS workstream_states (
    workstream_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL REFERENCES missions(id) ON DELETE CASCADE,

    -- Basic status
    phase TEXT NOT NULL DEFAULT 'initializing' CHECK (phase IN (
        'initializing', 'discovery', 'analysis', 'synthesis', 'review', 'finalizing', 'blocked', 'complete'
    )),
    health TEXT NOT NULL DEFAULT 'healthy' CHECK (health IN ('healthy', 'at_risk', 'critical', 'recovering', 'stalled')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'paused', 'completed', 'failed')),

    -- Progress tracking
    total_nodes INTEGER DEFAULT 0,
    completed_nodes INTEGER DEFAULT 0,
    failed_nodes INTEGER DEFAULT 0,
    skipped_nodes INTEGER DEFAULT 0,
    progress_percent NUMERIC DEFAULT 0.0 CHECK (progress_percent >= 0 AND progress_percent <= 100),

    -- Confidence and quality
    confidence_score NUMERIC DEFAULT 0.5 CHECK (confidence_score >= 0 AND confidence_score <= 1),
    quality_score NUMERIC DEFAULT 0.5 CHECK (quality_score >= 0 AND quality_score <= 1),
    contradiction_count INTEGER DEFAULT 0,

    -- Blockers
    blockers JSONB DEFAULT '[]',

    -- Risks and questions
    known_risks TEXT[] DEFAULT '{}',
    open_questions TEXT[] DEFAULT '{}',

    -- Dependencies
    depends_on_workstreams UUID[] DEFAULT '{}',
    waiting_for_dependencies BOOLEAN DEFAULT FALSE,
    dependencies_satisfied_at TIMESTAMPTZ,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_workstream_states_mission ON workstream_states(mission_id);
CREATE INDEX idx_workstream_states_phase ON workstream_states(phase);
CREATE INDEX idx_workstream_states_health ON workstream_states(health);

-- ============================================================================
-- Validation Telemetry Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS validation_telemetry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    mission_type TEXT NOT NULL,

    -- Execution metrics
    node_count INTEGER NOT NULL,
    execution_time_seconds NUMERIC NOT NULL,
    nodes_completed INTEGER NOT NULL,
    nodes_failed INTEGER DEFAULT 0,

    -- Coordination metrics
    handoff_count INTEGER NOT NULL,
    event_count INTEGER NOT NULL,
    checkpoint_count INTEGER DEFAULT 0,

    -- Adaptation metrics
    replans_triggered INTEGER DEFAULT 0,
    replans_executed INTEGER DEFAULT 0,

    -- Memory metrics
    memories_injected INTEGER DEFAULT 0,
    memory_conflicts INTEGER DEFAULT 0,

    -- Quality metrics
    evaluation_score NUMERIC,
    contradiction_count INTEGER DEFAULT 0,

    -- Workstream metrics
    workstream_count INTEGER NOT NULL,
    workstreams_blocked INTEGER DEFAULT 0,

    -- Metadata
    validation_section TEXT,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes TEXT
);

CREATE INDEX idx_validation_telemetry_mission ON validation_telemetry(mission_id);
CREATE INDEX idx_validation_telemetry_section ON validation_telemetry(validation_section);

-- ============================================================================
-- Validation Results Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS validation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Check identification
    section TEXT NOT NULL,
    check_number TEXT NOT NULL,
    check_name TEXT NOT NULL,
    check_description TEXT,

    -- Result
    status TEXT NOT NULL CHECK (status IN ('pending', 'passed', 'failed', 'skipped')),
    result_notes TEXT,

    -- Evidence
    evidence_query TEXT,
    evidence_result JSONB,

    -- Timing
    executed_at TIMESTAMPTZ,
    execution_duration_seconds NUMERIC,

    -- Metadata
    mission_id UUID REFERENCES missions(id),
    validator TEXT DEFAULT 'system'
);

CREATE INDEX idx_validation_results_section ON validation_results(section);
CREATE INDEX idx_validation_results_status ON validation_results(status);

-- ============================================================================
-- Schema Migrations Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Record this migration
INSERT INTO schema_migrations (version) VALUES ('validation_core_001')
ON CONFLICT (version) DO NOTHING;

-- ============================================================================
-- Validation Summary View
-- ============================================================================
CREATE OR REPLACE VIEW validation_summary AS
SELECT
    section,
    COUNT(*) FILTER (WHERE status = 'passed') AS passed,
    COUNT(*) FILTER (WHERE status = 'failed') AS failed,
    COUNT(*) FILTER (WHERE status = 'pending') AS pending,
    COUNT(*) FILTER (WHERE status = 'skipped') AS skipped,
    COUNT(*) AS total,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'passed') / NULLIF(COUNT(*), 0), 2) AS pass_rate_percent
FROM validation_results
GROUP BY section
ORDER BY section;
