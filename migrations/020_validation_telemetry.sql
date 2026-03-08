-- Migration 020: Validation Telemetry
-- Purpose: Capture metrics for Phase 5.1 validation
-- Created: 2026-03-07

-- ============================================================================
-- Validation Telemetry Table
-- Captures runtime metrics for validation missions
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
    checkpoint_count INTEGER NOT NULL,

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
    validation_section TEXT, -- Which section this data supports (A-P)
    captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Notes for manual review
    notes TEXT
);

CREATE INDEX idx_validation_telemetry_mission ON validation_telemetry(mission_id);
CREATE INDEX idx_validation_telemetry_type ON validation_telemetry(mission_type);
CREATE INDEX idx_validation_telemetry_section ON validation_telemetry(validation_section);
CREATE INDEX idx_validation_telemetry_captured ON validation_telemetry(captured_at);

-- ============================================================================
-- Validation Results Table
-- Tracks pass/fail status for each validation check
-- ============================================================================
CREATE TABLE IF NOT EXISTS validation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Check identification
    section TEXT NOT NULL, -- A, B, C, etc.
    check_number TEXT NOT NULL, -- A1, A2, etc.
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
CREATE INDEX idx_validation_results_check ON validation_results(section, check_number);

-- ============================================================================
-- Helper View: Validation Summary
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
