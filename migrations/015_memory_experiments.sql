-- Migration 015: Memory Injection Experiments
-- Purpose: Track and analyze memory injection effectiveness
-- Phase 4H.1 Milestone 1: Prove strategic memory improves reasoning
-- Created: 2026-03-07

-- Add memory_ids to experiment_assignments
ALTER TABLE experiment_assignments
ADD COLUMN IF NOT EXISTS memory_ids UUID[] DEFAULT '{}';

-- Create index for memory injection experiments lookup
CREATE INDEX IF NOT EXISTS idx_experiment_assignments_memory_ids
ON experiment_assignments USING GIN(memory_ids);

-- Memory injection experiments table
CREATE TABLE IF NOT EXISTS memory_injection_experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id TEXT NOT NULL UNIQUE,

    -- Experiment metadata
    name TEXT NOT NULL,
    description TEXT,
    experiment_type TEXT NOT NULL CHECK (experiment_type IN ('memory_vs_none', 'sparse_vs_dense')),

    -- Sample targets
    sample_size_target INTEGER NOT NULL DEFAULT 50,
    min_sample_size INTEGER NOT NULL DEFAULT 20,

    -- Group configurations
    control_config JSONB NOT NULL DEFAULT '{}',
    candidate_config JSONB NOT NULL DEFAULT '{}',

    -- Status tracking
    status TEXT NOT NULL DEFAULT 'planning' CHECK (status IN ('planning', 'running', 'completed', 'cancelled')),
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,

    -- Analysis results
    analysis_result JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_memory_injection_experiments_status ON memory_injection_experiments(status);

-- Memory injection results table
CREATE TABLE IF NOT EXISTS memory_injection_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id TEXT NOT NULL,
    execution_id UUID NOT NULL,

    -- Group assignment
    group_assignment TEXT NOT NULL CHECK (group_assignment IN ('control', 'candidate')),
    memory_ids UUID[] DEFAULT '{}',

    -- Evaluation metrics
    overall_score NUMERIC,
    reasoning_score NUMERIC,
    coherence_score NUMERIC,
    actionability_score NUMERIC,
    contradiction_count INTEGER,

    -- Performance metrics
    latency_seconds NUMERIC,
    token_count INTEGER,

    -- Context
    workflow_type TEXT,
    domain TEXT,

    -- Metadata
    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(execution_id, experiment_id)
);

CREATE INDEX idx_memory_injection_results_experiment ON memory_injection_results(experiment_id);
CREATE INDEX idx_memory_injection_results_execution ON memory_injection_results(execution_id);
CREATE INDEX idx_memory_injection_results_group ON memory_injection_results(experiment_id, group_assignment);

-- Update memory_usage to include experiment tracking
ALTER TABLE memory_usage
ADD COLUMN IF NOT EXISTS experiment_id TEXT,
ADD COLUMN IF NOT EXISTS injection_config JSONB DEFAULT '{}';

CREATE INDEX idx_memory_usage_experiment ON memory_usage(experiment_id) WHERE experiment_id IS NOT NULL;

-- View: Experiment summary by group
CREATE OR REPLACE VIEW experiment_group_summary AS
SELECT
    experiment_id,
    group_assignment,
    COUNT(*) as sample_count,
    AVG(overall_score) as avg_overall_score,
    AVG(coherence_score) as avg_coherence_score,
    AVG(actionability_score) as avg_actionability_score,
    AVG(contradiction_count) as avg_contradiction_count,
    AVG(latency_seconds) as avg_latency_seconds,
    AVG(token_count) as avg_token_count,
    STDDEV(overall_score) as stddev_overall_score
FROM memory_injection_results
GROUP BY experiment_id, group_assignment;

-- View: Experiment comparison (control vs candidate)
CREATE OR REPLACE VIEW experiment_comparison AS
SELECT
    r.experiment_id,
    e.name as experiment_name,
    e.experiment_type,

    -- Control metrics
    c.sample_count as control_count,
    c.avg_overall_score as control_overall_score,
    c.avg_coherence_score as control_coherence_score,
    c.avg_actionability_score as control_actionability_score,
    c.avg_latency_seconds as control_latency_seconds,

    -- Candidate metrics
    x.sample_count as candidate_count,
    x.avg_overall_score as candidate_overall_score,
    x.avg_coherence_score as candidate_coherence_score,
    x.avg_actionability_score as candidate_actionability_score,
    x.avg_latency_seconds as candidate_latency_seconds,

    -- Deltas
    (x.avg_overall_score - c.avg_overall_score) / NULLIF(c.avg_overall_score, 0) as overall_score_delta,
    (x.avg_coherence_score - c.avg_coherence_score) / NULLIF(c.avg_coherence_score, 0) as coherence_delta,
    (x.avg_actionability_score - c.avg_actionability_score) / NULLIF(c.avg_actionability_score, 0) as actionability_delta,
    (x.avg_latency_seconds - c.avg_latency_seconds) / NULLIF(c.avg_latency_seconds, 0) as latency_delta,

    -- Significance indicator
    CASE
        WHEN (x.avg_overall_score - c.avg_overall_score) / NULLIF(c.avg_overall_score, 0) >= 0.03 THEN 'significant_improvement'
        WHEN (x.avg_overall_score - c.avg_overall_score) / NULLIF(c.avg_overall_score, 0) > 0 THEN 'moderate_improvement'
        WHEN (x.avg_overall_score - c.avg_overall_score) / NULLIF(c.avg_overall_score, 0) < -0.03 THEN 'significant_degradation'
        WHEN (x.avg_overall_score - c.avg_overall_score) / NULLIF(c.avg_overall_score, 0) < 0 THEN 'moderate_degradation'
        ELSE 'neutral'
    END as significance_indicator

FROM memory_injection_results r
JOIN memory_injection_experiments e ON r.experiment_id = e.experiment_id
LEFT JOIN experiment_group_summary c ON c.experiment_id = r.experiment_id AND c.group_assignment = 'control'
LEFT JOIN experiment_group_summary x ON x.experiment_id = r.experiment_id AND x.group_assignment = 'candidate'
WHERE c.group_assignment = 'control' AND x.group_assignment = 'candidate';

COMMENT ON TABLE memory_injection_experiments IS 'Controlled experiments for testing memory injection effectiveness.';
COMMENT ON TABLE memory_injection_results IS 'Individual execution results grouped by control/candidate assignment.';
COMMENT ON VIEW experiment_group_summary IS 'Summary statistics for each group in an experiment.';
COMMENT ON VIEW experiment_comparison IS 'Side-by-side comparison of control vs candidate groups with significance testing.';

COMMENT ON COLUMN experiment_assignments.memory_ids IS 'Strategic memory IDs injected into this execution.';
COMMENT ON COLUMN memory_usage.experiment_id IS 'Link to experiment if this injection was part of a controlled experiment.';
COMMENT ON COLUMN memory_usage.injection_config IS 'Configuration used for memory injection (max_memories, types included, etc.)';
