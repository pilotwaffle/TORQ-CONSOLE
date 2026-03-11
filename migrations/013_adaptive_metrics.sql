-- Migration 013: Adaptive System Metrics Storage
-- Purpose: Store baseline metrics and telemetry for adaptive loop calibration
-- Created: 2026-03-07

-- Adaptive metrics table for time-series data
CREATE TABLE IF NOT EXISTS adaptive_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name TEXT NOT NULL,
    metric_value NUMERIC NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for metric queries
CREATE INDEX idx_adaptive_metrics_name ON adaptive_metrics(metric_name, created_at DESC);
CREATE INDEX idx_adaptive_metrics_created ON adaptive_metrics(created_at DESC);

-- System health snapshots (daily aggregated state)
CREATE TABLE IF NOT EXISTS system_health_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Health scores
    health_score NUMERIC,  -- 0.0 to 1.0
    signal_quality TEXT CHECK (signal_quality IN ('good', 'needs_attention', 'poor')),
    proposal_quality TEXT CHECK (proposal_quality IN ('good', 'volatile', 'poor')),
    experiment_quality TEXT CHECK (experiment_quality IN ('good', 'unstable', 'poor')),

    -- Metrics snapshots
    signal_volume JSONB,
    proposal_flow JSONB,
    experiment_outcomes JSONB,

    -- Issues
    noisy_assets TEXT[],
    recommendations TEXT[],

    -- Period covered
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    period_days INTEGER NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for health snapshots
CREATE INDEX idx_system_health_snapshots_period ON system_health_snapshots(period_start DESC);

COMMENT ON TABLE adaptive_metrics IS 'Time-series metrics for adaptive system observability and calibration.';
COMMENT ON TABLE system_health_snapshots IS 'Daily aggregated system health state for tracking adaptive loop stability over time.';

-- View: Latest health status
CREATE OR REPLACE VIEW latest_system_health AS
SELECT
    health_score,
    signal_quality,
    proposal_quality,
    experiment_quality,
    noisy_assets,
    recommendations,
    period_end AS last_updated,
    period_days
FROM system_health_snapshots
ORDER BY period_end DESC
LIMIT 1;

COMMENT ON VIEW latest_system_health IS 'Current system health status for quick monitoring.';
