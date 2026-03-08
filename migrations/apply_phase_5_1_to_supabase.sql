-- ============================================================================
-- Phase 5.1 Schema for Supabase - Combined Migration
-- Copy this entire script into Supabase SQL Editor
-- URL: https://supabase.com/dashboard/project/npukynbaglmcdvzyklqa/sql
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- Migration 018: Mission Graph Planning
-- ============================================================================

-- Missions table
CREATE TABLE IF NOT EXISTS missions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    mission_type TEXT NOT NULL CHECK (mission_type IN ('analysis', 'planning', 'evaluation', 'design', 'transformation')),
    objective TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'planned', 'scheduled', 'running', 'paused', 'completed', 'failed', 'cancelled')),
    scope JSONB DEFAULT '{}',
    context JSONB DEFAULT '{}',
    constraints JSONB DEFAULT '{}',
    injected_memory_ids UUID[] DEFAULT '{}',
    reasoning_strategy TEXT CHECK (reasoning_strategy IN ('decomposition_first', 'risk_first', 'evidence_weighted', 'checklist_driven', 'contradiction_first', 'hypothesis_driven')),
    overall_score NUMERIC,
    deliverables TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_missions_status ON missions(status);
CREATE INDEX IF NOT EXISTS idx_missions_type ON missions(mission_type);

-- Mission graphs table
CREATE TABLE IF NOT EXISTS mission_graphs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    version TEXT NOT NULL DEFAULT '1.0',
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'validating', 'validated', 'active', 'archived')),
    graph_metadata JSONB DEFAULT '{}',
    validation_errors TEXT[] DEFAULT '{}',
    validation_warnings TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mission_graphs_mission ON mission_graphs(mission_id);

-- Mission nodes table
CREATE TABLE IF NOT EXISTS mission_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    graph_id UUID NOT NULL REFERENCES mission_graphs(id) ON DELETE CASCADE,
    node_type TEXT NOT NULL CHECK (node_type IN ('objective', 'task', 'decision', 'evidence', 'deliverable')),
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'ready', 'running', 'completed', 'skipped', 'failed', 'blocked')),
    depends_on UUID[] DEFAULT '{}',
    blocks UUID[] DEFAULT '{}',
    workstream_id UUID,
    agent_type TEXT,
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    confidence_score NUMERIC CHECK (confidence_score >= 0 AND confidence_score <= 1),
    evaluation_score NUMERIC CHECK (evaluation_score >= 0 AND evaluation_score <= 1),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mission_nodes_mission ON mission_nodes(mission_id);
CREATE INDEX IF NOT EXISTS idx_mission_nodes_graph ON mission_nodes(graph_id);
CREATE INDEX IF NOT EXISTS idx_mission_nodes_status ON mission_nodes(status);
CREATE INDEX IF NOT EXISTS idx_mission_nodes_workstream ON mission_nodes(workstream_id);

-- Mission edges table
CREATE TABLE IF NOT EXISTS mission_edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    graph_id UUID NOT NULL REFERENCES mission_graphs(id) ON DELETE CASCADE,
    from_node_id UUID NOT NULL REFERENCES mission_nodes(id) ON DELETE CASCADE,
    to_node_id UUID NOT NULL REFERENCES mission_nodes(id) ON DELETE CASCADE,
    edge_type TEXT NOT NULL CHECK (edge_type IN ('depends_on', 'informs', 'blocks', 'branches_to', 'produces')),
    weight NUMERIC DEFAULT 1.0,
    condition JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mission_edges_mission ON mission_edges(mission_id);
CREATE INDEX IF NOT EXISTS idx_mission_edges_from ON mission_edges(from_node_id);
CREATE INDEX IF NOT EXISTS idx_mission_edges_to ON mission_edges(to_node_id);

-- Mission events table
CREATE TABLE IF NOT EXISTS mission_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    node_id UUID REFERENCES mission_nodes(id) ON DELETE CASCADE,
    workstream_id UUID,
    event_data JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mission_events_mission ON mission_events(mission_id);
CREATE INDEX IF NOT EXISTS idx_mission_events_node ON mission_events(node_id);
CREATE INDEX IF NOT EXISTS idx_mission_events_type ON mission_events(event_type);

-- Workstream states table
CREATE TABLE IF NOT EXISTS workstream_states (
    workstream_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    phase TEXT NOT NULL DEFAULT 'initializing' CHECK (phase IN (
        'initializing', 'discovery', 'analysis', 'synthesis', 'review', 'finalizing', 'blocked', 'complete'
    )),
    health TEXT NOT NULL DEFAULT 'healthy' CHECK (health IN ('healthy', 'at_risk', 'critical', 'recovering', 'stalled')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'paused', 'completed', 'failed')),
    total_nodes INTEGER DEFAULT 0,
    completed_nodes INTEGER DEFAULT 0,
    failed_nodes INTEGER DEFAULT 0,
    skipped_nodes INTEGER DEFAULT 0,
    progress_percent NUMERIC DEFAULT 0.0 CHECK (progress_percent >= 0 AND progress_percent <= 100),
    confidence_score NUMERIC DEFAULT 0.5 CHECK (confidence_score >= 0 AND confidence_score <= 1),
    quality_score NUMERIC DEFAULT 0.5 CHECK (quality_score >= 0 AND quality_score <= 1),
    contradiction_count INTEGER DEFAULT 0,
    blockers JSONB DEFAULT '[]',
    known_risks TEXT[] DEFAULT '{}',
    open_questions TEXT[] DEFAULT '{}',
    depends_on_workstreams UUID[] DEFAULT '{}',
    waiting_for_dependencies BOOLEAN DEFAULT FALSE,
    dependencies_satisfied_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_workstream_states_mission ON workstream_states(mission_id);
CREATE INDEX IF NOT EXISTS idx_workstream_states_phase ON workstream_states(phase);
CREATE INDEX IF NOT EXISTS idx_workstream_states_health ON workstream_states(health);

-- ============================================================================
-- Migration 019: Execution Fabric (Handoffs)
-- ============================================================================

CREATE TABLE IF NOT EXISTS mission_handoffs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    from_node_id UUID NOT NULL REFERENCES mission_nodes(id) ON DELETE CASCADE,
    to_node_id UUID REFERENCES mission_nodes(id) ON DELETE SET NULL,
    from_agent_type TEXT NOT NULL,
    to_agent_type TEXT,
    handoff_summary JSONB NOT NULL DEFAULT '{}',
    confidence NUMERIC NOT NULL DEFAULT 0.5 CHECK (confidence >= 0 AND confidence <= 1),
    confidence_basis TEXT,
    unresolved_questions TEXT[] DEFAULT '{}',
    assumptions_made TEXT[] DEFAULT '{}',
    limitations TEXT[] DEFAULT '{}',
    risks TEXT[] DEFAULT '{}',
    severity_indicators TEXT[] DEFAULT '{}',
    artifacts JSONB DEFAULT '{}',
    workspace_entries TEXT[] DEFAULT '{}',
    recommended_consumers TEXT[] DEFAULT '{}',
    required_next_actions TEXT[] DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'created' CHECK (status IN ('created', 'in_transit', 'delivered', 'acknowledged', 'failed')),
    delivery_attempts INTEGER DEFAULT 0,
    delivered_to TEXT[] DEFAULT '{}',
    acknowledged_by TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mission_handoffs_mission ON mission_handoffs(mission_id);
CREATE INDEX IF NOT EXISTS idx_mission_handoffs_from_node ON mission_handoffs(from_node_id);
CREATE INDEX IF NOT EXISTS idx_mission_handoffs_to_node ON mission_handoffs(to_node_id) WHERE to_node_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_mission_handoffs_status ON mission_handoffs(status);

-- ============================================================================
-- Migration 020: Validation Telemetry
-- ============================================================================

CREATE TABLE IF NOT EXISTS validation_telemetry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    mission_type TEXT NOT NULL,
    node_count INTEGER NOT NULL,
    execution_time_seconds NUMERIC NOT NULL,
    nodes_completed INTEGER NOT NULL,
    nodes_failed INTEGER DEFAULT 0,
    handoff_count INTEGER NOT NULL,
    event_count INTEGER NOT NULL,
    checkpoint_count INTEGER DEFAULT 0,
    replans_triggered INTEGER DEFAULT 0,
    replans_executed INTEGER DEFAULT 0,
    memories_injected INTEGER DEFAULT 0,
    memory_conflicts INTEGER DEFAULT 0,
    evaluation_score NUMERIC,
    contradiction_count INTEGER DEFAULT 0,
    workstream_count INTEGER NOT NULL,
    workstreams_blocked INTEGER DEFAULT 0,
    validation_section TEXT,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_validation_telemetry_mission ON validation_telemetry(mission_id);
CREATE INDEX IF NOT EXISTS idx_validation_telemetry_section ON validation_telemetry(validation_section);

CREATE TABLE IF NOT EXISTS validation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    section TEXT NOT NULL,
    check_number TEXT NOT NULL,
    check_name TEXT NOT NULL,
    check_description TEXT,
    status TEXT NOT NULL CHECK (status IN ('pending', 'passed', 'failed', 'skipped')),
    result_notes TEXT,
    evidence_query TEXT,
    evidence_result JSONB,
    executed_at TIMESTAMPTZ,
    execution_duration_seconds NUMERIC,
    mission_id UUID REFERENCES missions(id),
    validator TEXT DEFAULT 'system'
);

CREATE INDEX IF NOT EXISTS idx_validation_results_section ON validation_results(section);
CREATE INDEX IF NOT EXISTS idx_validation_results_status ON validation_results(status);

-- ============================================================================
-- Success Message
-- ============================================================================
SELECT 'Phase 5.1 Schema Applied Successfully' as result;
