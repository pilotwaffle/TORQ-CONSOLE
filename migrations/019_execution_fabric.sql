-- Migration 019: Execution Fabric
-- Purpose: Support coordinated, stateful team execution with shared context
-- Phase 5.1: Execution Fabric
-- Created: 2026-03-07

-- ============================================================================
-- Mission Handoffs Table
-- Stores structured handoff packets between mission nodes
-- ============================================================================
CREATE TABLE IF NOT EXISTS mission_handoffs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL REFERENCES missions(id) ON DELETE CASCADE,

    -- Source information
    from_node_id UUID NOT NULL REFERENCES mission_nodes(id) ON DELETE CASCADE,
    to_node_id UUID REFERENCES mission_nodes(id) ON DELETE SET NULL,
    from_agent_type TEXT NOT NULL,
    to_agent_type TEXT,

    -- Handoff summary (collaboration-centric)
    handoff_summary JSONB NOT NULL DEFAULT '{}',
    -- Contains: objective_completed, output_summary, key_findings, recommendations

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
CREATE INDEX idx_mission_handoffs_consumers ON mission_handoffs USING GIN(recommended_consumers);

-- ============================================================================
-- Workstream States Table
-- Tracks health, progress, and state for each workstream
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

    -- Blockers (stored as JSONB array)
    blockers JSONB DEFAULT '[]',
    -- Each blocker: {id, node_id, description, severity, blocked_at, resolution_plan, resolved_at, resolving_node_id}

    -- Risks and questions
    known_risks TEXT[] DEFAULT '{}',
    open_questions TEXT[] DEFAULT '{}',

    -- Dependencies
    depends_on_workstreams UUID[] DEFAULT '{}',
    waiting_for_dependencies BOOLEAN DEFAULT FALSE,
    dependencies_satisfied_at TIMESTAMPTZ,

    -- Coordination
    needs_input_from TEXT[] DEFAULT '{}',
    provides_input_to TEXT[] DEFAULT '{}',
    pending_handoffs INTEGER DEFAULT 0,
    completed_handoffs INTEGER DEFAULT 0,

    -- Timing
    started_at TIMESTAMPTZ,
    phase_started_at TIMESTAMPTZ,
    estimated_completion TIMESTAMPTZ,
    last_activity TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Agent assignment
    lead_agent_type TEXT,
    active_agents TEXT[] DEFAULT '{}',

    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_workstream_states_mission ON workstream_states(mission_id);
CREATE INDEX idx_workstream_states_phase ON workstream_states(phase);
CREATE INDEX idx_workstream_states_health ON workstream_states(health);
CREATE INDEX idx_workstream_states_status ON workstream_states(status);

-- ============================================================================
-- Mission Events Table (if not exists in previous migrations)
-- Stores events from the context bus for mission coordination
-- ============================================================================
CREATE TABLE IF NOT EXISTS mission_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL REFERENCES missions(id) ON DELETE CASCADE,

    -- Event information
    event_type TEXT NOT NULL,
    event_payload JSONB DEFAULT '{}',

    -- Source information
    source_node_id UUID REFERENCES mission_nodes(id) ON DELETE SET NULL,
    source_agent_type TEXT,
    source_workstream_id UUID,

    -- Processing
    processed_by TEXT[] DEFAULT '{}',  -- Agent IDs that processed this
    acknowledged BOOLEAN DEFAULT FALSE,

    -- Metadata
    priority TEXT DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'critical')),
    correlation_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_mission_events_mission ON mission_events(mission_id);
CREATE INDEX idx_mission_events_type ON mission_events(event_type);
CREATE INDEX idx_mission_events_source_node ON mission_events(source_node_id) WHERE source_node_id IS NOT NULL;
CREATE INDEX idx_mission_events_created_at ON mission_events(created_at DESC);

-- ============================================================================
-- Mission Checkpoints Table
-- Stores recoverable mission snapshots for rollback and recovery
-- ============================================================================
CREATE TABLE IF NOT EXISTS mission_checkpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    graph_id UUID NOT NULL REFERENCES mission_graphs(id) ON DELETE CASCADE,

    -- Type and status
    checkpoint_type TEXT NOT NULL DEFAULT 'automatic' CHECK (checkpoint_type IN (
        'automatic', 'manual', 'pre_phase', 'post_phase', 'critical', 'recovery'
    )),
    status TEXT NOT NULL DEFAULT 'creating' CHECK (status IN ('creating', 'ready', 'corrupted', 'expired', 'deleting')),

    -- Content summary
    node_count INTEGER DEFAULT 0,
    completed_nodes INTEGER DEFAULT 0,
    failed_nodes INTEGER DEFAULT 0,
    workstream_count INTEGER DEFAULT 0,
    artifact_count INTEGER DEFAULT 0,
    handoff_count INTEGER DEFAULT 0,

    -- Size tracking
    estimated_size_bytes BIGINT DEFAULT 0,

    -- Timing
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,

    -- Creator
    created_by TEXT DEFAULT 'system',

    -- Description
    description TEXT,
    tags TEXT[] DEFAULT '{}',

    -- Statistics
    mission_duration_seconds NUMERIC DEFAULT 0.0,
    average_confidence NUMERIC DEFAULT 0.0,
    open_blockers INTEGER DEFAULT 0,
    open_risks INTEGER DEFAULT 0
);

CREATE INDEX idx_mission_checkpoints_mission ON mission_checkpoints(mission_id);
CREATE INDEX idx_mission_checkpoints_type ON mission_checkpoints(checkpoint_type);
CREATE INDEX idx_mission_checkpoints_status ON mission_checkpoints(status);
CREATE INDEX idx_mission_checkpoints_created_at ON mission_checkpoints(created_at DESC);
CREATE INDEX idx_mission_checkpoints_expires_at ON mission_checkpoints(expires_at) WHERE expires_at IS NOT NULL;

-- ============================================================================
-- Checkpoint Data Table
-- Stores detailed checkpoint data (separate table for size management)
-- ============================================================================
CREATE TABLE IF NOT EXISTS checkpoint_data (
    checkpoint_id UUID PRIMARY KEY REFERENCES mission_checkpoints(id) ON DELETE CASCADE,

    -- Complete state snapshots
    graph_state JSONB DEFAULT '{}',
    node_states JSONB DEFAULT '{}',
    node_outputs JSONB DEFAULT '{}',
    workstream_states JSONB DEFAULT '{}',
    active_handoffs JSONB DEFAULT '[]',
    blockers JSONB DEFAULT '[]',
    risks JSONB DEFAULT '[]',
    events JSONB DEFAULT '[]',
    decision_outcomes JSONB DEFAULT '[]',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- Replan Proposals Table
-- Stores proposals for mission graph modifications
-- ============================================================================
CREATE TABLE IF NOT EXISTS replan_proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    graph_id UUID NOT NULL REFERENCES mission_graphs(id) ON DELETE CASCADE,

    -- Trigger information
    trigger_type TEXT NOT NULL CHECK (trigger_type IN (
        'evidence_drop', 'contradiction_spike', 'node_failure', 'human_request',
        'external_change', 'blocker_unresolved', 'confidence_low', 'timeout'
    )),
    trigger_description TEXT NOT NULL,
    source_node_id UUID REFERENCES mission_nodes(id) ON DELETE SET NULL,
    source_workstream_id UUID,

    -- Proposed changes
    scope TEXT NOT NULL DEFAULT 'minor' CHECK (scope IN ('minor', 'moderate', 'major', 'full')),
    actions JSONB DEFAULT '[]',
    -- Each action: {action_type, target_id, description, changes, reasoning}
    estimated_impact TEXT,

    -- Analysis
    reasoning TEXT,
    risks TEXT[] DEFAULT '{}',
    benefits TEXT[] DEFAULT '{}',
    alternatives TEXT[] DEFAULT '{}',

    -- Decision
    status TEXT NOT NULL DEFAULT 'proposed' CHECK (status IN (
        'proposed', 'approved', 'rejected', 'in_progress', 'completed', 'failed'
    )),
    approved_by TEXT,
    approved_at TIMESTAMPTZ,
    rejection_reason TEXT,

    -- Execution
    execution_started_at TIMESTAMPTZ,
    execution_completed_at TIMESTAMPTZ,
    new_graph_id UUID REFERENCES mission_graphs(id) ON DELETE SET NULL,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_replan_proposals_mission ON replan_proposals(mission_id);
CREATE INDEX idx_replan_proposals_graph ON replan_proposals(graph_id);
CREATE INDEX idx_replan_proposals_status ON replan_proposals(status);
CREATE INDEX idx_replan_proposals_trigger_type ON replan_proposals(trigger_type);
CREATE INDEX idx_replan_proposals_created_at ON replan_proposals(created_at DESC);

-- ============================================================================
-- Views for Common Queries
-- ============================================================================

-- Active handoffs awaiting delivery
CREATE OR REPLACE VIEW active_handoffs AS
SELECT
    h.id,
    h.mission_id,
    h.from_node_id,
    h.to_node_id,
    h.from_agent_type,
    h.to_agent_type,
    h.handoff_summary,
    h.confidence,
    h.status,
    h.delivery_attempts,
    h.recommended_consumers,
    h.created_at,
    n_from.title as from_node_title,
    n_to.title as to_node_title
FROM mission_handoffs h
LEFT JOIN mission_nodes n_from ON h.from_node_id = n_from.id
LEFT JOIN mission_nodes n_to ON h.to_node_id = n_to.id
WHERE h.status IN ('created', 'in_transit')
ORDER BY h.created_at ASC;

-- Workstreams at risk or critical
CREATE OR REPLACE VIEW workstreams_at_risk AS
SELECT
    ws.workstream_id,
    ws.mission_id,
    ws.phase,
    ws.health,
    ws.status,
    ws.progress_percent,
    ws.confidence_score,
    ws.blockers,
    ws.last_activity,
    ws.lead_agent_type,
    w.name as workstream_name,
    w.domain
FROM workstream_states ws
INNER JOIN workstreams w ON ws.workstream_id = w.id
WHERE ws.health IN ('at_risk', 'critical', 'stalled')
   OR ws.phase = 'blocked'
ORDER BY
  CASE ws.health
    WHEN 'critical' THEN 1
    WHEN 'stalled' THEN 2
    WHEN 'at_risk' THEN 3
    ELSE 4
  END,
  ws.last_activity ASC;

-- Recent mission events (for context bus replay)
CREATE OR REPLACE VIEW recent_mission_events AS
SELECT
    e.id,
    e.mission_id,
    e.event_type,
    e.event_payload,
    e.source_node_id,
    e.source_agent_type,
    e.source_workstream_id,
    e.priority,
    e.processed_by,
    e.acknowledged,
    e.created_at,
    n.title as source_node_title
FROM mission_events e
LEFT JOIN mission_nodes n ON e.source_node_id = n.id
WHERE e.created_at > NOW() - INTERVAL '7 days'
ORDER BY e.created_at DESC;

-- Checkpoints ready for restore
CREATE OR REPLACE VIEW available_checkpoints AS
SELECT
    c.id,
    c.mission_id,
    c.graph_id,
    c.checkpoint_type,
    c.status,
    c.description,
    c.tags,
    c.node_count,
    c.completed_nodes,
    c.progress_percent,
    c.created_at,
    c.expires_at,
    c.created_by,
    c.average_confidence,
    c.open_blockers,
    m.title as mission_title
FROM mission_checkpoints c
INNER JOIN missions m ON c.mission_id = m.id
WHERE c.status = 'ready'
  AND (c.expires_at IS NULL OR c.expires_at > NOW())
ORDER BY c.created_at DESC;

-- Pending replan proposals
CREATE OR REPLACE VIEW pending_replans AS
SELECT
    r.id,
    r.mission_id,
    r.trigger_type,
    r.trigger_description,
    r.scope,
    r.status,
    array_length(r.actions, 1) as action_count,
    r.created_at,
    r.approved_at,
    r.execution_started_at,
    r.execution_completed_at,
    m.title as mission_title
FROM replan_proposals r
INNER JOIN missions m ON r.mission_id = m.id
WHERE r.status IN ('proposed', 'approved', 'in_progress')
ORDER BY
  CASE r.status
    WHEN 'proposed' THEN 1
    WHEN 'approved' THEN 2
    WHEN 'in_progress' THEN 3
  END,
  r.created_at ASC;

-- ============================================================================
-- Functions for Common Operations
-- ============================================================================

-- Get workstreams that need attention (at risk, blocked, or stalled)
CREATE OR REPLACE FUNCTION get_workstreams_needing_attention(p_mission_id UUID)
RETURNS TABLE (
    workstream_id UUID,
    workstream_name TEXT,
    health TEXT,
    phase TEXT,
    blocker_count INTEGER,
    open_risk_count INTEGER,
    last_activity TIMESTAMPTZ,
    attention_reason TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ws.workstream_id,
        w.name,
        ws.health,
        ws.phase,
        COALESCE(array_length(ws.blockers, 1), 0) as blocker_count,
        COALESCE(array_length(ws.known_risks, 1), 0) as open_risk_count,
        ws.last_activity,
        ARRAY[
            CASE WHEN ws.health = 'critical' THEN 'Critical health' END,
            CASE WHEN ws.phase = 'blocked' THEN 'Workstream blocked' END,
            CASE WHEN ws.health = 'stalled' THEN 'Workstream stalled' END,
            CASE WHEN COALESCE(array_length(ws.blockers, 1), 0) > 0 THEN COALESCE(blocker_count::TEXT || ' blockers', '') END
        ] FILTER (WHERE elem IS NOT NULL) as attention_reason
    FROM workstream_states ws
    INNER JOIN workstreams w ON ws.workstream_id = w.id
    WHERE ws.mission_id = p_mission_id
      AND (ws.health IN ('at_risk', 'critical', 'stalled', 'recovering') OR ws.phase = 'blocked')
    ORDER BY
      CASE ws.health
        WHEN 'critical' THEN 1
        WHEN 'stalled' THEN 2
        WHEN 'at_risk' THEN 3
        ELSE 4
      END,
      ws.last_activity ASC;
END;
$$ LANGUAGE plpgsql;

-- Get mission health summary
CREATE OR REPLACE FUNCTION get_mission_health_summary(p_mission_id UUID)
RETURNS TABLE (
    total_workstreams INTEGER,
    healthy_workstreams INTEGER,
    at_risk_workstreams INTEGER,
    critical_workstreams INTEGER,
    stalled_workstreams INTEGER,
    total_blockers INTEGER,
    total_open_risks INTEGER,
    average_confidence NUMERIC,
    overall_status TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*) as total_workstreams,
        SUM(CASE WHEN ws.health = 'healthy' THEN 1 ELSE 0 END) as healthy_workstreams,
        SUM(CASE WHEN ws.health = 'at_risk' THEN 1 ELSE 0 END) as at_risk_workstreams,
        SUM(CASE WHEN ws.health = 'critical' THEN 1 ELSE 0 END) as critical_workstreams,
        SUM(CASE WHEN ws.health = 'stalled' THEN 1 ELSE 0 END) as stalled_workstreams,
        SUM(COALESCE(array_length(ws.blockers, 1), 0)) as total_blockers,
        SUM(COALESCE(array_length(ws.known_risks, 1), 0)) as total_open_risks,
        AVG(ws.confidence_score) as average_confidence,
        CASE
            WHEN SUM(CASE WHEN ws.health = 'critical' THEN 1 ELSE 0 END) > 0 THEN 'critical'
            WHEN SUM(CASE WHEN ws.health IN ('at_risk', 'stalled') THEN 1 ELSE 0 END) > COUNT(*) / 2 THEN 'at_risk'
            WHEN SUM(CASE WHEN ws.health = 'healthy' THEN 1 ELSE 0 END) = COUNT(*) THEN 'healthy'
            ELSE 'degraded'
        END as overall_status
    FROM workstream_states ws
    WHERE ws.mission_id = p_mission_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Comments
-- ============================================================================
COMMENT ON TABLE mission_handoffs IS 'Structured handoff packets between mission nodes for collaboration.';
COMMENT ON TABLE workstream_states IS 'Health, progress, and state tracking for each workstream.';
COMMENT ON TABLE mission_events IS 'Context bus events for mission coordination and replay.';
COMMENT ON TABLE mission_checkpoints IS 'Recoverable mission snapshots for rollback and recovery.';
COMMENT ON TABLE checkpoint_data IS 'Detailed checkpoint data (separated for size management).';
COMMENT ON TABLE replan_proposals IS 'Proposals for dynamic mission graph modification.';

COMMENT ON VIEW active_handoffs IS 'Handoffs currently awaiting delivery.';
COMMENT ON VIEW workstreams_at_risk IS 'Workstreams with health issues requiring attention.';
COMMENT ON VIEW recent_mission_events IS 'Recent context bus events for state replay.';
COMMENT ON VIEW available_checkpoints IS 'Checkpoints ready for restore operations.';
COMMENT ON VIEW pending_replans IS 'Replanning proposals awaiting approval or execution.';

COMMENT ON FUNCTION get_workstreams_needing_attention IS 'Returns workstreams that need human or system attention.';
COMMENT ON FUNCTION get_mission_health_summary IS 'Returns overall health summary for a mission.';
