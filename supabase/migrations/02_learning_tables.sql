-- ============================================
-- TORQ Console: Learning & Audit System
-- Migration 2: Learning & Policy Tables
-- ============================================

-- ============================================
-- 1. LEARNING EVENTS
-- Stores events from which the system learns
-- ============================================
CREATE TABLE IF NOT EXISTS learning_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id TEXT NOT NULL UNIQUE,

    -- Event classification
    event_type TEXT NOT NULL, -- success, failure, improvement, pattern, drift
    category TEXT, -- performance, security, ux, reliability, cost

    -- Source
    source_agent TEXT,
    source_tool TEXT,
    source_trace_id TEXT,

    -- Event data
    event_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    before_state JSONB,
    after_state JSONB,

    -- Metrics
    impact_score DECIMAL(3,2), -- -1.0 to 1.0 (negative to positive impact)
    confidence DECIMAL(3,2), -- 0.0 to 1.0

    -- Status
    status TEXT DEFAULT 'pending', -- pending, reviewed, applied, rejected, archived
    reviewed_by TEXT,
    reviewed_at TIMESTAMPTZ,

    -- Relationships
    related_event_id UUID REFERENCES learning_events(id) ON DELETE SET NULL,

    -- Timestamps
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================
-- 2. POLICY VERSIONS
-- Stores version history of policies/prompts
-- ============================================
CREATE TABLE IF NOT EXISTS policy_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    policy_id TEXT NOT NULL,
    version INTEGER NOT NULL,

    -- Policy identification
    policy_name TEXT NOT NULL,
    policy_type TEXT NOT NULL, -- agent_prompt, tool_prompt, system_rule, workflow

    -- Content
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,

    -- Version metadata
    previous_version_id UUID REFERENCES policy_versions(id) ON DELETE SET NULL,
    change_summary TEXT,
    change_reason TEXT,

    -- Metrics
    performance_score DECIMAL(5,2), -- 0-100
    usage_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2), -- 0-100

    -- Approval
    created_by TEXT,
    approved_by TEXT,
    approved_at TIMESTAMPTZ,

    -- Status
    status TEXT DEFAULT 'draft', -- draft, active, archived, deprecated
    effective_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(policy_id, version)
);

-- ============================================
-- 3. POLICY ACTIVE
-- Points to currently active policy versions
-- ============================================
CREATE TABLE IF NOT EXISTS policy_active (
    policy_id TEXT PRIMARY KEY,

    -- References
    active_version_id UUID REFERENCES policy_versions(id) ON DELETE RESTRICT,
    active_version INTEGER NOT NULL,

    -- Activation tracking
    activated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    activated_by TEXT,

    -- Metrics since activation
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMPTZ,

    -- Health
    health_score DECIMAL(5,2), -- 0-100
    drift_score DECIMAL(5,2), -- 0-100 (higher = more drift)

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================
-- 4. ADVISORY AUDIT LOG
-- Tracks all advisory system interactions
-- ============================================
CREATE TABLE IF NOT EXISTS advisory_audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Request
    session_id TEXT NOT NULL,
    trace_id TEXT,
    user_query TEXT NOT NULL,

    -- Advisory response
    advisory_decision TEXT, -- approve, reject, modify, defer
    reasoning TEXT,
    confidence DECIMAL(3,2),

    -- Context
    context_data JSONB DEFAULT '{}'::jsonb,
    policy_ids TEXT[] DEFAULT ARRAY[]::TEXT[],
    policy_versions INTEGER[],

    -- Outcome
    final_decision TEXT,
    outcome TEXT, -- success, failure, partial
    feedback TEXT,

    -- Timing
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================
-- 5. DRIFT METRICS
-- Daily metrics for drift detection
-- ============================================
CREATE TABLE IF NOT EXISTS drift_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Time period
    metric_date DATE NOT NULL,
    metric_hour INTEGER, -- If doing hourly, otherwise NULL

    -- Policy drift
    policy_id TEXT NOT NULL,
    policy_version INTEGER NOT NULL,

    -- Drift indicators
    drift_score DECIMAL(5,2) DEFAULT 0, -- 0-100
    baseline_distance DECIMAL(10,4),

    -- Performance changes
    success_rate_baseline DECIMAL(5,2),
    success_rate_current DECIMAL(5,2),
    success_rate_delta DECIMAL(5,2),

    -- Usage patterns
    usage_count INTEGER DEFAULT 0,
    avg_confidence DECIMAL(5,2),
    avg_response_time_ms INTEGER,

    -- Anomalies
    anomaly_detected BOOLEAN DEFAULT false,
    anomaly_details JSONB,

    -- Context
    total_comparisons INTEGER DEFAULT 0,
    sample_size INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(policy_id, metric_date, metric_hour)
);

-- ============================================
-- AUTO-UPDATE TIMESTAMP TRIGGERS
-- ============================================
DROP TRIGGER IF EXISTS update_learning_events_updated_at ON learning_events;
CREATE TRIGGER update_learning_events_updated_at
    BEFORE UPDATE ON learning_events
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_policy_active_updated_at ON policy_active;
CREATE TRIGGER update_policy_active_updated_at
    BEFORE UPDATE ON policy_active
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- ENABLE ROW LEVEL SECURITY
-- ============================================
ALTER TABLE learning_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE policy_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE policy_active ENABLE ROW LEVEL SECURITY;
ALTER TABLE advisory_audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE drift_metrics ENABLE ROW LEVEL SECURITY;

-- Service role can do everything
CREATE POLICY "Service role full access learning_events" ON learning_events
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service role full access policy_versions" ON policy_versions
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service role full access policy_active" ON policy_active
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service role full access advisory_audit_log" ON advisory_audit_log
    FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE POLICY "Service role full access drift_metrics" ON drift_metrics
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Anon/authenticated can read learning data
CREATE POLICY "Read access learning_events" ON learning_events
    FOR SELECT TO anon, authenticated USING (true);

CREATE POLICY "Read access policy_versions" ON policy_versions
    FOR SELECT TO anon, authenticated USING (true);

CREATE POLICY "Read access policy_active" ON policy_active
    FOR SELECT TO anon, authenticated USING (true);

-- Audit log and drift are service-role write only
CREATE POLICY "Read access advisory_audit_log" ON advisory_audit_log
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "Read access drift_metrics" ON drift_metrics
    FOR SELECT TO anon, authenticated USING (true);

-- ============================================
-- USEFUL INDEXES
-- ============================================
CREATE INDEX IF NOT EXISTS idx_learning_events_type ON learning_events(event_type);
CREATE INDEX IF NOT EXISTS idx_learning_events_status ON learning_events(status);
CREATE INDEX IF NOT EXISTS idx_learning_events_occurred ON learning_events(occurred_at DESC);

CREATE INDEX IF NOT EXISTS idx_policy_versions_name ON policy_versions(policy_name);
CREATE INDEX IF NOT EXISTS idx_policy_versions_status ON policy_versions(status);
CREATE INDEX IF NOT EXISTS idx_policy_versions_type ON policy_versions(policy_type);

CREATE INDEX IF NOT EXISTS idx_drift_metrics_date ON drift_metrics(metric_date DESC);
CREATE INDEX IF NOT EXISTS idx_drift_metrics_policy ON drift_metrics(policy_id);

CREATE INDEX IF NOT EXISTS idx_advisor_session ON advisory_audit_log(session_id);
CREATE INDEX IF NOT EXISTS idx_advisor_created ON advisory_audit_log(created_at DESC);

-- ============================================
-- HELPER FUNCTIONS
-- ============================================

-- Get current active policy for a policy_id
CREATE OR REPLACE FUNCTION get_active_policy(p_policy_id TEXT)
RETURNS TABLE (
    policy_id TEXT,
    version INTEGER,
    content TEXT,
    activated_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        pa.policy_id,
        pa.active_version,
        pv.content,
        pa.activated_at
    FROM policy_active pa
    JOIN policy_versions pv ON pa.active_version_id = pv.id
    WHERE pa.policy_id = p_policy_id
    AND pv.status = 'active';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- COMMENTS
-- ============================================
COMMENT ON TABLE learning_events IS 'Stores learning events for TORQ Console AI system';
COMMENT ON TABLE policy_versions IS 'Version history for policies, prompts, and rules';
COMMENT ON TABLE policy_active IS 'Currently active policy versions';
COMMENT ON TABLE advisory_audit_log IS 'Audit log for all advisory system decisions';
COMMENT ON TABLE drift_metrics IS 'Daily metrics for detecting policy and behavior drift';
