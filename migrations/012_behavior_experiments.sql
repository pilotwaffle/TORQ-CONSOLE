-- Migration 012: Behavior Experiment & Versioning Layer
-- Purpose: Complete the adaptive cognition loop with controlled experimentation
-- Created: 2026-03-07

-- ============================================================================
-- Behavior Versions (canonical registry)
-- ============================================================================

CREATE TABLE IF NOT EXISTS behavior_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Asset identification
    asset_type TEXT NOT NULL CHECK (
        asset_type IN (
            'agent_prompt',
            'agent_system_instructions',
            'routing_profile',
            'tool_preferences',
            'synthesis_prompt',
            'evaluation_profile'
        )
    ),
    asset_key TEXT NOT NULL,  -- e.g., 'planner', 'financial_analysis_router'
    version TEXT NOT NULL,     -- e.g., 'v1', 'v2', '2026-03-07-a'

    -- Version content
    content JSONB NOT NULL,     -- Actual behavior configuration

    -- Lineage
    created_from_proposal_id UUID REFERENCES adaptation_proposals(proposal_id) ON DELETE SET NULL,
    parent_version_id UUID REFERENCES behavior_versions(id) ON DELETE SET NULL,

    -- Status
    status TEXT NOT NULL DEFAULT 'draft' CHECK (
        status IN ('draft', 'active', 'candidate', 'archived', 'rolled_back')
    ),

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Unique constraint: one version per type/key/version
    UNIQUE (asset_type, asset_key, version)
);

-- Indexes for looking up active/candidate versions
CREATE INDEX idx_behavior_versions_asset ON behavior_versions(asset_type, asset_key, status);
CREATE INDEX idx_behavior_versions_proposal ON behavior_versions(created_from_proposal_id);
CREATE INDEX idx_behavior_versions_parent ON behavior_versions(parent_version_id);

-- Ensure only one active version per asset
CREATE UNIQUE INDEX idx_behavior_versions_active ON behavior_versions(asset_type, asset_key)
WHERE status = 'active';

COMMENT ON TABLE behavior_versions IS 'Canonical registry of versioned behavior assets. All behavior changes flow through this table for version control and traceability.';
COMMENT ON COLUMN behavior_versions.content IS 'The actual behavior configuration (prompt, routing rules, tool preferences, etc.)';
COMMENT ON COLUMN behavior_versions.created_from_proposal_id IS 'Links behavior version to the adaptation proposal that created it, completing the audit trail.';

-- ============================================================================
-- Behavior Experiments
-- ============================================================================

CREATE TABLE IF NOT EXISTS behavior_experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Link to proposal
    proposal_id UUID NOT NULL REFERENCES adaptation_proposals(proposal_id) ON DELETE CASCADE,

    -- Asset under experiment
    asset_type TEXT NOT NULL,
    asset_key TEXT NOT NULL,

    -- Variants
    control_version_id UUID NOT NULL REFERENCES behavior_versions(id) ON DELETE CASCADE,
    candidate_version_id UUID NOT NULL REFERENCES behavior_versions(id) ON DELETE CASCADE,

    -- Experiment configuration
    hypothesis TEXT NOT NULL,
    assignment_mode TEXT NOT NULL CHECK (
        assignment_mode IN ('percentage_hash', 'workflow_type', 'tenant_scope')
    ),
    assignment_config JSONB NOT NULL,

    -- Success criteria
    success_metrics JSONB NOT NULL,
    minimum_sample_size INTEGER NOT NULL DEFAULT 30,

    -- Status
    status TEXT NOT NULL DEFAULT 'draft' CHECK (
        status IN ('draft', 'running', 'paused', 'completed', 'promoted', 'rolled_back')
    ),

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    promoted_at TIMESTAMPTZ,
    rolled_back_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX idx_behavior_experiments_proposal ON behavior_experiments(proposal_id);
CREATE INDEX idx_behavior_experiments_asset ON behavior_experiments(asset_type, asset_key, status);
CREATE INDEX idx_behavior_experiments_status ON behavior_experiments(status, created_at DESC);
CREATE INDEX idx_behavior_experiments_running ON behavior_experiments(status, asset_key)
WHERE status = 'running';

COMMENT ON TABLE behavior_experiments IS 'A/B experiments testing candidate behavior versions against control. All adaptations must run as experiments before promotion.';

-- ============================================================================
-- Experiment Assignments (traceability)
-- ============================================================================

CREATE TABLE IF NOT EXISTS experiment_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Links
    experiment_id UUID NOT NULL REFERENCES behavior_experiments(id) ON DELETE CASCADE,
    execution_id UUID NOT NULL REFERENCES task_executions(id) ON DELETE CASCADE,

    -- Assignment decision
    assigned_variant TEXT NOT NULL CHECK (assigned_variant IN ('control', 'candidate')),
    behavior_version_id UUID NOT NULL REFERENCES behavior_versions(id) ON DELETE CASCADE,

    -- Explainability
    assignment_reason TEXT,

    -- Timestamp
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Ensure one assignment per execution per experiment
    UNIQUE (experiment_id, execution_id)
);

-- Indexes
CREATE INDEX idx_experiment_assignments_experiment ON experiment_assignments(experiment_id, created_at DESC);
CREATE INDEX idx_experiment_assignments_execution ON experiment_assignments(execution_id);
CREATE INDEX idx_experiment_assignments_variant ON experiment_assignments(experiment_id, assigned_variant);

COMMENT ON TABLE experiment_assignments IS 'Records which executions received which behavior variant. Essential for traceability and impact analysis.';

-- ============================================================================
-- Adaptation Impacts (measured outcomes)
-- ============================================================================

CREATE TABLE IF NOT EXISTS adaptation_impacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Links
    experiment_id UUID NOT NULL REFERENCES behavior_experiments(id) ON DELETE CASCADE,
    proposal_id UUID NOT NULL REFERENCES adaptation_proposals(proposal_id) ON DELETE CASCADE,

    -- Metric comparison
    metric_name TEXT NOT NULL,
    control_value NUMERIC(10,4) NOT NULL,
    candidate_value NUMERIC(10,4) NOT NULL,
    delta_value NUMERIC(10,4) NOT NULL,

    -- Statistical confidence
    confidence NUMERIC(5,2) NOT NULL,  -- 0.00 to 1.00

    -- Sample sizes
    sample_control INTEGER NOT NULL,
    sample_candidate INTEGER NOT NULL,

    -- Timestamp
    measured_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_adaptation_impacts_experiment ON adaptation_impacts(experiment_id, metric_name);
CREATE INDEX idx_adaptation_impacts_proposal ON adaptation_impacts(proposal_id);

COMMENT ON TABLE adaptation_impacts IS 'Measured impact of experiments on evaluation metrics. Aggregates control vs candidate performance.';
COMMENT ON COLUMN adaptation_impacts.delta_value IS 'Candidate value minus control value. Positive means candidate improved the metric.';

-- ============================================================================
-- View: Active Experiments Summary
-- ============================================================================

CREATE OR REPLACE VIEW active_experiments_summary AS
SELECT
    e.id AS experiment_id,
    e.asset_type,
    e.asset_key,
    e.hypothesis,
    e.minimum_sample_size,
    e.status,
    e.created_at,

    -- Assignment counts
    COALESCE(a_cnt.total_assignments, 0) AS total_assignments,
    COALESCE(a_cnt.control_count, 0) AS control_count,
    COALESCE(a_cnt.candidate_count, 0) AS candidate_count,

    -- Progress
    CASE
        WHEN e.minimum_sample_size > 0 THEN
            ROUND(
                (COALESCE(a_cnt.control_count, 0)::NUMERIC / e.minimum_sample_size) * 100
            , 1)
        ELSE 0
    END AS sample_progress_percent,

    -- Versions
    cv.content AS control_content,
    cv.version AS control_version,
    candv.content AS candidate_content,
    candv.version AS candidate_version,

    -- Proposal linkage
    p.learning_signal_id,
    p.adaptation_type,
    p.change_description,
    p.risk_tier

FROM behavior_experiments e

-- Get assignment counts
LEFT JOIN (
    SELECT experiment_id,
        COUNT(*) AS total_assignments,
        COUNT(*) FILTER (WHERE assigned_variant = 'control') AS control_count,
        COUNT(*) FILTER (WHERE assigned_variant = 'candidate') AS candidate_count
    FROM experiment_assignments
    GROUP BY experiment_id
) a_cnt ON a_cnt.experiment_id = e.id

-- Get version contents
LEFT JOIN behavior_versions cv ON cv.id = e.control_version_id
LEFT JOIN behavior_versions candv ON candv.id = e.candidate_version_id

-- Get proposal info
LEFT JOIN adaptation_proposals p ON p.proposal_id = e.proposal_id

WHERE e.status IN ('draft', 'running', 'paused');

COMMENT ON VIEW active_experiments_summary IS 'Summary of active experiments with assignment counts and progress. Used for monitoring and decision-making.';

-- ============================================================================
-- View: Experiment Impact Analysis
-- ============================================================================

CREATE OR REPLACE VIEW experiment_impact_analysis AS
SELECT
    e.id AS experiment_id,
    e.asset_key,
    e.hypothesis,
    e.status,

    -- Sample sizes
    COALESCE(a_cnt.control_count, 0) AS sample_control,
    COALESCE(a_cnt.candidate_count, 0) AS sample_candidate,

    -- Primary metric
    COALESCE(
        FIRST_VALUE(ai.delta_value) FILTER (
            WHERE ai.metric_name = (
                SELECT JSON_VALUE_PATH(success_metrics, '$.primary_metric')
                FROM behavior_experiments be
                WHERE be.id = e.id
            )
        ) OVER (PARTITION BY e.id ORDER BY ai.measured_at DESC),
        0
    ) AS primary_metric_delta,

    -- Guardrail checks
    COALESCE(
        COUNT(*) FILTER (
            WHERE ai.metric_name IN (
                SELECT JSON_VALUE_PATH(j.value, '$.metric')
                FROM jsonb_array_elements(
                    JSON_VALUE_PATH(success_metrics, '$.guardrails')
                ) j
                WHERE EXISTS (
                    SELECT 1 FROM behavior_experiments be
                    WHERE be.id = e.id
                )
            )
            AND ai.delta_value < 0  -- Regression
        ),
        0
    ) AS guardrail_violations,

    -- Recommendation
    CASE
        WHEN COALESCE(a_cnt.control_count, 0) >= 30
            AND COALESCE(a_cnt.candidate_count, 0) >= 30
            THEN 'ready_for_decision'
        ELSE 'collecting_samples'
    END AS decision_status

FROM behavior_experiments e

-- Assignment counts
LEFT JOIN (
    SELECT experiment_id,
        COUNT(*) FILTER (WHERE assigned_variant = 'control') AS control_count,
        COUNT(*) FILTER (WHERE assigned_variant = 'candidate') AS candidate_count
    FROM experiment_assignments
    GROUP BY experiment_id
) a_cnt ON a_cnt.experiment_id = e.id

-- Impact data
LEFT JOIN adaptation_impacts ai ON ai.experiment_id = e.id;

COMMENT ON VIEW experiment_impact_analysis IS 'Pre-computed analysis of experiment results for quick decision-making.';
