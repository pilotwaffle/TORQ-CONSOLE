-- Migration 016: Memory Effectiveness Tracking
-- Purpose: Track whether strategic memories actually improve outcomes
-- Phase 4H.1 Milestone 3: Memory Effectiveness Scoring
-- Created: 2026-03-07

-- Update memory_usage with effectiveness tracking fields
ALTER TABLE memory_usage
ADD COLUMN IF NOT EXISTS outcome_score NUMERIC,
ADD COLUMN IF NOT EXISTS evaluation_delta NUMERIC,
ADD COLUMN IF NOT EXISTS contradiction_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS led_to_proposal BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS proposal_id UUID,
ADD COLUMN IF NOT EXISTS proposal_succeeded BOOLEAN,
ADD COLUMN IF NOT EXISTS helpful BOOLEAN DEFAULT FALSE;

-- Create indexes for effectiveness queries
CREATE INDEX IF NOT EXISTS idx_memory_usage_outcome_score ON memory_usage(outcome_score) WHERE outcome_score IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_memory_usage_helpful ON memory_usage(memory_id, helpful) WHERE helpful IS NOT NULL;

-- Memory effectiveness summary table (cached calculations)
CREATE TABLE IF NOT EXISTS memory_effectiveness (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id UUID NOT NULL REFERENCES strategic_memories(id) ON DELETE CASCADE,

    -- Component scores
    evaluation_delta_impact NUMERIC CHECK (evaluation_delta_impact BETWEEN -1 AND 1),
    experiment_success_rate NUMERIC CHECK (experiment_success_rate BETWEEN 0 AND 1),
    workflow_performance_boost NUMERIC CHECK (workflow_performance_boost BETWEEN -1 AND 1),
    contradiction_reduction NUMERIC CHECK (contradiction_reduction BETWEEN 0 AND 1),

    -- Overall effectiveness
    effectiveness_score NUMERIC CHECK (effectiveness_score BETWEEN 0 AND 1),

    -- Trend tracking
    score_trend TEXT CHECK (score_trend IN ('improving', 'stable', 'declining')),
    trend_window_days INTEGER DEFAULT 30,

    -- Metadata
    usage_count INTEGER NOT NULL DEFAULT 0,
    period_days INTEGER NOT NULL DEFAULT 90,
    last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(memory_id)
);

CREATE INDEX idx_memory_effectiveness_score ON memory_effectiveness(effectiveness_score DESC);
CREATE INDEX idx_memory_effectiveness_trend ON memory_effectiveness(score_trend);

-- View: Top performing memories
CREATE OR REPLACE VIEW top_performing_memories AS
SELECT
    m.id,
    m.memory_type,
    m.title,
    m.domain,
    m.scope,
    m.usage_count,
    e.effectiveness_score,
    e.score_trend,
    e.usage_count as tracked_usage_count,
    e.last_updated as effectiveness_calculated_at
FROM strategic_memories m
LEFT JOIN memory_effectiveness e ON m.id = e.memory_id
WHERE m.status = 'active'
  AND e.effectiveness_score IS NOT NULL
ORDER BY e.effectiveness_score DESC NULLS LAST, m.usage_count DESC
LIMIT 50;

-- View: Memories needing attention (low effectiveness)
CREATE OR REPLACE VIEW low_effectiveness_memories AS
SELECT
    m.id,
    m.memory_type,
    m.title,
    m.domain,
    m.usage_count,
    e.effectiveness_score,
    e.score_trend,
    e.evaluation_delta_impact,
    e.experiment_success_rate
FROM strategic_memories m
LEFT JOIN memory_effectiveness e ON m.id = e.memory_id
WHERE m.status = 'active'
  AND (
    e.effectiveness_score < 0.3
    OR e.score_trend = 'declining'
  )
ORDER BY e.effectiveness_score ASC NULLS LAST;

-- View: Memory effectiveness by type
CREATE OR REPLACE VIEW memory_effectiveness_by_type AS
SELECT
    m.memory_type,
    COUNT(*) as memory_count,
    AVG(e.effectiveness_score) as avg_effectiveness,
    AVG(e.evaluation_delta_impact) as avg_delta_impact,
    AVG(e.experiment_success_rate) as avg_success_rate,
    AVG(e.contradiction_reduction) as avg_contradiction_reduction,
    SUM(CASE WHEN e.score_trend = 'improving' THEN 1 ELSE 0 END) as improving_count,
    SUM(CASE WHEN e.score_trend = 'declining' THEN 1 ELSE 0 END) as declining_count
FROM strategic_memories m
LEFT JOIN memory_effectiveness e ON m.id = e.memory_id
WHERE m.status = 'active'
GROUP BY m.memory_type
ORDER BY avg_effectiveness DESC;

-- Function: Recalculate effectiveness for a single memory
CREATE OR REPLACE FUNCTION recalculate_memory_effectiveness(
    p_memory_id UUID,
    p_days_back INTEGER DEFAULT 90
)
RETURNS TABLE (
    effectiveness_score NUMERIC,
    evaluation_delta_impact NUMERIC,
    experiment_success_rate NUMERIC,
    workflow_performance_boost NUMERIC,
    contradiction_reduction NUMERIC,
    score_trend TEXT,
    usage_count BIGINT
) AS $$
DECLARE
    v_usage_count INTEGER;
    v_avg_delta NUMERIC;
    v_success_rate NUMERIC;
    v_contradiction_reduction NUMERIC;
    v_effectiveness_score NUMERIC;
    v_recent_score NUMERIC;
    v_older_score NUMERIC;
    v_score_trend TEXT;
BEGIN
    -- Count usage in period
    SELECT COUNT(*) INTO v_usage_count
    FROM memory_usage
    WHERE memory_id = p_memory_id
      AND used_at >= NOW() - (p_days_back || ' days')::INTERVAL;

    -- Calculate average evaluation delta
    SELECT COALESCE(AVG(evaluation_delta), 0) INTO v_avg_delta
    FROM memory_usage
    WHERE memory_id = p_memory_id
      AND evaluation_delta IS NOT NULL
      AND used_at >= NOW() - (p_days_back || ' days')::INTERVAL;

    -- Calculate experiment success rate
    SELECT COALESCE(
        COUNT(*) FILTER (WHERE proposal_succeeded = TRUE)::NUMERIC /
        NULLIF(COUNT(*) FILTER (WHERE led_to_proposal = TRUE), 0),
        0
    ) INTO v_success_rate
    FROM memory_usage
    WHERE memory_id = p_memory_id
      AND used_at >= NOW() - (p_days_back || ' days')::INTERVAL;

    -- Calculate contradiction reduction (0 contradictions = 1.0, 5+ = 0.0)
    SELECT COALESCE(
        1.0 - (AVG(contradiction_count) / 5.0),
        0
    ) INTO v_contradiction_reduction
    FROM memory_usage
    WHERE memory_id = p_memory_id
      AND contradiction_count IS NOT NULL
      AND used_at >= NOW() - (p_days_back || ' days')::INTERVAL;

    -- Normalize delta to -1 to 1 range
    v_avg_delta := LEAST(GREATEST(v_avg_delta * 5, -1), 1);

    -- Calculate overall effectiveness score
    v_effectiveness_score := (
        (v_avg_delta + 1) * 0.30 / 2 +  -- Normalized delta: 30% weight
        v_success_rate * 0.25 +           -- Success rate: 25% weight
        0.5 * 0.25 +                      -- Workflow boost: 25% weight (placeholder)
        v_contradiction_reduction * 0.20  -- Contradiction reduction: 20% weight
    );

    -- Determine trend (simplified - would compare two periods in production)
    IF v_effectiveness_score > 0.6 THEN
        v_score_trend := 'stable';  -- High scores considered stable
    ELSIF v_effectiveness_score < 0.4 THEN
        v_score_trend := 'declining';
    ELSE
        v_score_trend := 'stable';
    END IF;

    -- Update memory_effectiveness table
    INSERT INTO memory_effectiveness (
        memory_id,
        evaluation_delta_impact,
        experiment_success_rate,
        workflow_performance_boost,
        contradiction_reduction,
        effectiveness_score,
        score_trend,
        usage_count,
        period_days
    ) VALUES (
        p_memory_id,
        v_avg_delta,
        v_success_rate,
        0,  -- Workflow boost placeholder
        v_contradiction_reduction,
        v_effectiveness_score,
        v_score_trend,
        v_usage_count,
        p_days_back
    )
    ON CONFLICT (memory_id) DO UPDATE SET
        evaluation_delta_impact = EXCLUDED.evaluation_delta_impact,
        experiment_success_rate = EXCLUDED.experiment_success_rate,
        workflow_performance_boost = EXCLUDED.workflow_performance_boost,
        contradiction_reduction = EXCLUDED.contradiction_reduction,
        effectiveness_score = EXCLUDED.effectiveness_score,
        score_trend = EXCLUDED.score_trend,
        usage_count = EXCLUDED.usage_count,
        period_days = EXCLUDED.period_days,
        last_updated = NOW();

    -- Update strategic_memories table
    UPDATE strategic_memories
    SET effectiveness_score = v_effectiveness_score
    WHERE id = p_memory_id;

    RETURN QUERY SELECT
        v_effectiveness_score,
        v_avg_delta,
        v_success_rate,
        0::NUMERIC,  -- Workflow boost placeholder
        v_contradiction_reduction,
        v_score_trend,
        v_usage_count::BIGINT;
END;
$$ LANGUAGE plpgsql;

-- Comment objects
COMMENT ON TABLE memory_effectiveness IS 'Cached effectiveness calculations for strategic memories.';
COMMENT ON FUNCTION recalculate_memory_effectiveness IS 'Recalculate effectiveness score for a single memory based on recent usage data.';

COMMENT ON VIEW top_performing_memories IS 'Strategic memories ranked by effectiveness score.';
COMMENT ON VIEW low_effectiveness_memories IS 'Active memories with low effectiveness scores or declining trends.';
COMMENT ON VIEW memory_effectiveness_by_type IS 'Effectiveness statistics aggregated by memory type.';
