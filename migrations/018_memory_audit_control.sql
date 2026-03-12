-- Migration 018: Memory Audit & Control Layer
-- Purpose: Complete audit infrastructure for Phase 4H.1 Milestone 4
-- Phase 4H.1: Audit, Inspection, and Control Layer
-- Created: 2026-03-10

-- ============================================================================
-- Missing Rejection Log Table (referenced in code but not created)
-- ============================================================================

CREATE TABLE IF NOT EXISTS memory_rejection_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Candidate identification
    artifact_id UUID NOT NULL,
    artifact_type TEXT NOT NULL,
    workspace_id UUID NOT NULL,

    -- What was rejected
    proposed_memory_type TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,

    -- Why it was rejected
    rejection_reason TEXT NOT NULL,
    rejection_message TEXT,
    failing_rule TEXT,

    -- Scores at time of rejection
    confidence_score NUMERIC(5,2) NOT NULL,
    completeness_score NUMERIC(5,2) NOT NULL,

    -- Temporal
    rejected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Validator info
    validator_version TEXT DEFAULT '1.0.0',

    -- Review tracking
    reviewed BOOLEAN DEFAULT FALSE,
    reviewed_by TEXT,
    reviewed_at TIMESTAMPTZ,
    review_notes TEXT
);

-- Indexes for rejection log queries
CREATE INDEX idx_memory_rejection_log_workspace ON memory_rejection_log(workspace_id, rejected_at DESC);
CREATE INDEX idx_memory_rejection_log_artifact ON memory_rejection_log(artifact_id);
CREATE INDEX idx_memory_rejection_log_reason ON memory_rejection_log(rejection_reason, rejected_at DESC);
CREATE INDEX idx_memory_rejection_log_unreviewed ON memory_rejection_log(reviewed) WHERE reviewed = FALSE;

-- ============================================================================
-- Memory Access Log (persistent audit trail)
-- ============================================================================

CREATE TABLE IF NOT EXISTS memory_access_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- What was accessed
    memory_id UUID NOT NULL,
    memory_uuid UUID NOT NULL,

    -- Access context
    access_type TEXT NOT NULL,  -- query, injection, inspection
    accessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Who accessed
    user_id TEXT,
    session_id TEXT,

    -- Query details (JSONB for flexibility)
    query_filters JSONB DEFAULT '{}',
    results_count INTEGER DEFAULT 0,

    -- Performance
    query_runtime_ms NUMERIC(10,2) DEFAULT 0,

    -- Context
    workflow_type TEXT,
    domain TEXT,
    execution_id UUID
);

-- Indexes for access log queries
CREATE INDEX idx_memory_access_log_memory ON memory_access_log(memory_id, accessed_at DESC);
CREATE INDEX idx_memory_access_log_type ON memory_access_log(access_type, accessed_at DESC);
CREATE INDEX idx_memory_access_log_user ON memory_access_log(user_id, accessed_at DESC) WHERE user_id IS NOT NULL;
CREATE INDEX idx_memory_access_log_execution ON memory_access_log(execution_id);

-- ============================================================================
-- Memory Validation Events (decision tracking)
-- ============================================================================

CREATE TABLE IF NOT EXISTS memory_validation_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- What was validated
    memory_id UUID,  -- NULL if rejected before storage
    candidate_artifact_id UUID NOT NULL,

    -- Decision
    decision TEXT NOT NULL,  -- ACCEPT, REJECT, REVIEW
    decision_reason TEXT,

    -- Validation details
    confidence_score NUMERIC(5,2),
    completeness_score NUMERIC(5,2),
    durability_score NUMERIC(5,2),

    -- Rule evaluation
    eligibility_rules_checked TEXT[] DEFAULT '{}',
    rules_passed TEXT[] DEFAULT '{}',
    rules_failed TEXT[] DEFAULT '{}',

    -- Conflict detection
    conflicts_detected BOOLEAN DEFAULT FALSE,
    conflict_details JSONB DEFAULT '{}',

    -- Temporal
    validated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    validator_version TEXT DEFAULT '1.0.0',

    -- Validator info
    validator_type TEXT DEFAULT 'automated',  -- automated, human, hybrid
    validator_id TEXT
);

-- Indexes for validation event queries
CREATE INDEX idx_memory_validation_events_memory ON memory_validation_events(memory_id, validated_at DESC);
CREATE INDEX idx_memory_validation_events_artifact ON memory_validation_events(candidate_artifact_id);
CREATE INDEX idx_memory_validation_events_decision ON memory_validation_events(decision, validated_at DESC);
CREATE INDEX idx_memory_validation_events_unreviewed ON memory_validation_events(decision) WHERE decision = 'REVIEW';

-- ============================================================================
-- Memory Control State (for governance actions)
-- ============================================================================

CREATE TABLE IF NOT EXISTS memory_control_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Target memory
    memory_id UUID NOT NULL UNIQUE,

    -- Control flags
    disabled BOOLEAN DEFAULT FALSE,
    disabled_at TIMESTAMPTZ,
    disabled_by TEXT,
    disabled_reason TEXT,

    -- Forced freshness
    force_expiration BOOLEAN DEFAULT FALSE,
    forced_expires_at TIMESTAMPTZ,
    expiration_reason TEXT,

    -- Supersession control
    marked_for_supersession BOOLEAN DEFAULT FALSE,
    superseded_by UUID REFERENCES strategic_memories(id) ON DELETE SET NULL,
    supersession_reason TEXT,

    -- Quality gate
    quality_gate_locked BOOLEAN DEFAULT FALSE,
    quality_gate_version TEXT,

    -- Metadata
    controlled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    controlled_by TEXT NOT NULL,
    control_notes TEXT,

    -- Audit trail for state changes
    state_history JSONB DEFAULT '[]'
);

-- Indexes for control state queries
CREATE INDEX idx_memory_control_state_disabled ON memory_control_state(disabled) WHERE disabled = TRUE;
CREATE INDEX idx_memory_control_state_supersession ON memory_control_state(marked_for_supersession) WHERE marked_for_supersession = TRUE;
CREATE INDEX idx_memory_control_state_expiration ON memory_control_state(force_expiration, forced_expires_at);

-- ============================================================================
-- Memory Provenance View (traceability)
-- ============================================================================

CREATE OR REPLACE VIEW memory_provenance_view AS
SELECT
    sm.id as memory_id,
    sm.memory_type,
    sm.title,
    sm.status,
    sm.confidence,
    sm.durability_score,
    sm.created_at,

    -- Source lineage
    sm.source_pattern_ids,
    sm.source_insight_ids,
    sm.source_experiment_ids,

    -- Usage tracking
    sm.usage_count,
    sm.last_used_at,

    -- Control state
    COALESCE(mcs.disabled, FALSE) as is_disabled,
    COALESCE(mcs.force_expiration, FALSE) as has_forced_expiration,
    COALESCE(mcs.marked_for_supersession, FALSE) as is_marked_for_supersession,

    -- Validation summary
    (SELECT COUNT(*) FROM memory_validation_events mve WHERE mve.memory_id = sm.id) as validation_event_count,
    (SELECT COUNT(*) FILTER (WHERE decision = 'REJECT') FROM memory_validation_events mve WHERE mve.candidate_artifact_id IN (
        SELECT unnest(source_pattern_ids) UNION SELECT unnest(source_insight_ids)
    )) as related_rejection_count,

    -- Access summary
    (SELECT COUNT(*) FROM memory_access_log mal WHERE mal.memory_id = sm.id) as access_count,
    (SELECT MAX(accessed_at) FROM memory_access_log mal WHERE mal.memory_id = sm.id) as last_accessed_at,

    -- Challenge status
    EXISTS(SELECT 1 FROM memory_challenges mc WHERE mc.memory_id = sm.id AND NOT mc.resolved) as has_unresolved_challenges

FROM strategic_memories sm
LEFT JOIN memory_control_state mcs ON sm.id = mcs.memory_id
WHERE sm.status IN ('active', 'deprecated', 'supplanted');

-- ============================================================================
-- Governance Dashboard Views
-- ============================================================================

-- Memories needing governance attention
CREATE OR REPLACE VIEW memories_needing_governance AS
SELECT
    sm.id,
    sm.memory_type,
    sm.title,
    sm.status,
    sm.confidence,
    sm.expires_at,
    sm.last_validated_at,

    -- Control state
    COALESCE(mcs.disabled, FALSE) as is_disabled,
    COALESCE(mcs.marked_for_supersession, FALSE) as is_marked_for_supersession,

    -- Attention reasons
    CASE
        WHEN COALESCE(mcs.disabled, FALSE) THEN 'disabled'
        WHEN sm.expires_at IS NOT NULL AND sm.expires_at < NOW() THEN 'expired'
        WHEN sm.last_validated_at IS NULL THEN 'never_validated'
        WHEN sm.confidence < 0.5 THEN 'low_confidence'
        WHEN sm.expires_at IS NOT NULL AND sm.expires_at < NOW() + INTERVAL '7 days' THEN 'expiring_soon'
        WHEN COALESCE(mcs.marked_for_supersession, FALSE) THEN 'marked_for_supersession'
        WHEN EXISTS(SELECT 1 FROM memory_challenges mc WHERE mc.memory_id = sm.id AND NOT mc.resolved) THEN 'has_challenges'
        ELSE 'review_needed'
    END as attention_reason,

    -- Related stats
    (SELECT COUNT(*) FROM memory_validation_events mve WHERE mve.memory_id = sm.id) as validation_count,
    (SELECT COUNT(*) FROM memory_access_log mal WHERE mal.memory_id = sm.id) as access_count

FROM strategic_memories sm
LEFT JOIN memory_control_state mcs ON sm.id = mcs.memory_id
WHERE sm.status = 'active'
  AND (
    mcs.disabled = TRUE
    OR mcs.marked_for_supersession = TRUE
    OR sm.expires_at IS NOT NULL AND sm.expires_at < NOW()
    OR sm.last_validated_at IS NULL
    OR sm.confidence < 0.5
    OR (sm.expires_at IS NOT NULL AND sm.expires_at < NOW() + INTERVAL '7 days')
    OR EXISTS(SELECT 1 FROM memory_challenges mc WHERE mc.memory_id = sm.id AND NOT mc.resolved)
  )
ORDER BY
  CASE sm.expires_at
    WHEN NULL THEN 2
    ELSE 1
  END,
  sm.expires_at ASC NULLS LAST,
  sm.confidence ASC;

-- Rejection log summary by workspace
CREATE OR REPLACE VIEW rejection_summary_by_workspace AS
SELECT
    workspace_id,
    COUNT(*) as total_rejections,
    COUNT(*) FILTER (WHERE reviewed = FALSE) as pending_review,
    rejection_reason,
    AVG(confidence_score) as avg_confidence,
    AVG(completeness_score) as avg_completeness,
    MAX(rejected_at) as last_rejection_at
FROM memory_rejection_log
GROUP BY workspace_id, rejection_reason
ORDER BY total_rejections DESC;

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON TABLE memory_rejection_log IS 'Audit log for rejected memory candidates with reason tracking.';
COMMENT ON TABLE memory_access_log IS 'Persistent audit trail of all memory access events.';
COMMENT ON TABLE memory_validation_events IS 'Detailed validation decision tracking for all memory candidates.';
COMMENT ON TABLE memory_control_state IS 'Governance control state for memories (disable, expire, supersede).';

COMMENT ON VIEW memory_provenance_view IS 'Complete provenance and traceability view for all memories.';
COMMENT ON VIEW memories_needing_governance IS 'Memories requiring governance attention with prioritization.';
COMMENT ON VIEW rejection_summary_by_workspace IS 'Summary of rejections by workspace for governance review.';
