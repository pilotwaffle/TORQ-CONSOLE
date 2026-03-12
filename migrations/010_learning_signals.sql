-- Migration 010: Learning Signals Storage
-- Purpose: Store learning signals extracted from evaluations and workspace data
-- Created: 2026-03-07

-- Main learning signals table
CREATE TABLE IF NOT EXISTS learning_signals (
    signal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Signal classification
    signal_type TEXT NOT NULL CHECK (
        signal_type IN (
            'prompt_structure_clarity',
            'prompt_missing_context',
            'prompt_ambiguous_instructions',
            'routing_misalignment',
            'routing_missing_capability',
            'routing_overspecialization',
            'tool_preference_emergent',
            'tool_avoidance_pattern',
            'tool_inefficiency',
            'repeated_unresolved_questions',
            'repeated_contradiction',
            'risk_pattern_critical',
            'coherence_degradation'
        )
    ),

    -- Signal strength and source
    strength TEXT NOT NULL CHECK (strength IN ('weak', 'moderate', 'strong', 'conclusive')),
    source TEXT NOT NULL CHECK (source IN (
        'evaluation_metric',
        'workspace_entry',
        'synthesis_output',
        'execution_outcome',
        'cross_execution_pattern'
    )),

    -- Scope (what this signal applies to)
    scope_type TEXT NOT NULL CHECK (scope_type IN ('agent', 'workflow', 'routing', 'tool')),
    scope_id TEXT NOT NULL,

    -- Evidence tracking
    evidence_count INTEGER NOT NULL DEFAULT 1,
    supporting_execution_ids TEXT[] DEFAULT '{}',
    conflicting_execution_ids TEXT[] DEFAULT '{}',

    -- Signal content
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    proposed_action TEXT,

    -- Additional structured data
    metadata JSONB DEFAULT '{}',

    -- Salience and status
    salience TEXT NOT NULL DEFAULT 'medium' CHECK (salience IN ('low', 'medium', 'high', 'critical')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'acknowledged', 'incorporated', 'rejected')),

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ  -- Optional expiration for transient signals
);

-- Indexes for common queries
CREATE INDEX idx_learning_signals_scope ON learning_signals(scope_type, scope_id);
CREATE INDEX idx_learning_signals_type_status ON learning_signals(signal_type, status);
CREATE INDEX idx_learning_signals_strength ON learning_signals(strength DESC, created_at DESC);
CREATE INDEX idx_learning_signals_salience ON learning_signals(salience, status);

-- Index for signal aggregation
CREATE INDEX idx_learning_signals_aggregation ON learning_signals(
    signal_type, scope_type, scope_id, status, created_at DESC
);

-- Prevent duplicate pending signals
CREATE UNIQUE INDEX idx_learning_signals_unique_pending ON learning_signals(
    signal_type, scope_type, scope_id
) WHERE status IN ('pending', 'acknowledged');

-- Comments
COMMENT ON TABLE learning_signals IS 'Learning signals extracted from evaluations, workspace entries, and syntheses. Signals drive adaptive improvements in agent behavior.';
COMMENT ON COLUMN learning_signals.signal_type IS 'Type of learning signal. Determines the category of adaptive improvement.';
COMMENT ON COLUMN learning_signals.strength IS 'Confidence in the signal based on evidence count and weight.';
COMMENT ON COLUMN learning_signals.scope_type IS 'What this signal applies to: agent, workflow, routing, or tool.';
COMMENT ON COLUMN learning_signals.evidence_count IS 'Number of observations supporting this signal.';
COMMENT ON COLUMN learning_signals.salience IS 'Importance of this signal for prioritization.';

-- Aggregated signals table (for higher-level patterns)
CREATE TABLE IF NOT EXISTS aggregated_learning_signals (
    aggregation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    signal_type TEXT NOT NULL,
    scope_type TEXT NOT NULL,
    scope_id TEXT NOT NULL,

    total_evidence INTEGER NOT NULL,
    unique_executions INTEGER NOT NULL,
    strength TEXT NOT NULL,

    first_observed TIMESTAMPTZ NOT NULL,
    last_observed TIMESTAMPTZ NOT NULL,

    representative_signal_ids UUID[] NOT NULL,

    aggregated_metadata JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_aggregated_signals_scope ON aggregated_learning_signals(scope_type, scope_id);

COMMENT ON TABLE aggregated_learning_signals IS 'Aggregated learning signals representing higher-level patterns across multiple observations.';

-- Signal events table (for tracking signal lifecycle)
CREATE TABLE IF NOT EXISTS learning_signal_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id UUID NOT NULL REFERENCES learning_signals(signal_id) ON DELETE CASCADE,

    event_type TEXT NOT NULL CHECK (event_type IN ('created', 'acknowledged', 'incorporated', 'rejected', 'expired')),
    event_data JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by TEXT
);

CREATE INDEX idx_learning_signal_events_signal ON learning_signal_events(signal_id, created_at DESC);

COMMENT ON TABLE learning_signal_events IS 'Audit trail of learning signal lifecycle events.';
