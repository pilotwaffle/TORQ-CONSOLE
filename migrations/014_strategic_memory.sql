-- Migration 014: Strategic Memory Store
-- Purpose: Persistent strategic knowledge that shapes future reasoning
-- Phase 4H: Institutional strategic memory layer
-- Created: 2026-03-07

-- Core strategic memories table
CREATE TABLE IF NOT EXISTS strategic_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Classification
    memory_type TEXT NOT NULL CHECK (memory_type IN ('heuristic', 'playbook', 'warning', 'assumption', 'adaptation_lesson')),
    title TEXT NOT NULL,
    domain TEXT,
    scope TEXT NOT NULL CHECK (scope IN ('global', 'workflow_type', 'agent_type', 'tenant', 'domain')),
    scope_key TEXT,  -- e.g., workflow_type name or agent_type identifier

    -- Scoring
    confidence NUMERIC(5,2) NOT NULL DEFAULT 0.70,  -- 0.00 to 1.00
    durability_score NUMERIC(5,2) NOT NULL DEFAULT 0.50,  -- 0.00 to 1.00
    effectiveness_score NUMERIC(5,2),  -- Updated from feedback

    -- Content (flexible schema for different memory types)
    memory_content JSONB NOT NULL DEFAULT '{}',

    -- Source lineage
    source_pattern_ids UUID[] DEFAULT '{}',
    source_insight_ids UUID[] DEFAULT '{}',
    source_experiment_ids UUID[] DEFAULT '{}',

    -- Lifecycle
    status TEXT NOT NULL DEFAULT 'candidate' CHECK (status IN ('candidate', 'active', 'deprecated', 'archived', 'supplanted')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    last_validated_at TIMESTAMPTZ,

    -- Governance
    invalidated_by_pattern_id UUID,
    supplanted_by_memory_id UUID REFERENCES strategic_memories(id) ON DELETE SET NULL,

    -- Usage tracking
    usage_count INTEGER NOT NULL DEFAULT 0,
    last_used_at TIMESTAMPTZ
);

-- Indexes for common queries
CREATE INDEX idx_strategic_memories_type ON strategic_memories(memory_type);
CREATE INDEX idx_strategic_memories_status ON strategic_memories(status);
CREATE INDEX idx_strategic_memories_scope ON strategic_memories(scope, scope_key);
CREATE INDEX idx_strategic_memories_domain ON strategic_memories(domain);
CREATE INDEX idx_strategic_memories_confidence ON strategic_memories(confidence DESC);
CREATE INDEX idx_strategic_memories_expires ON strategic_memories(expires_at) WHERE expires_at IS NOT NULL;

-- GIN index for JSONB content searches
CREATE INDEX idx_strategic_memories_content ON strategic_memories USING GIN(memory_content);

-- GIN index for array searches (patterns, insights, experiments)
CREATE INDEX idx_strategic_memories_patterns ON strategic_memories USING GIN(source_pattern_ids);
CREATE INDEX idx_strategic_memories_insights ON strategic_memories USING GIN(source_insight_ids);

-- Memory supersession tracking (lineage)
CREATE TABLE IF NOT EXISTS memory_supersessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    old_memory_id UUID NOT NULL REFERENCES strategic_memories(id) ON DELETE CASCADE,
    new_memory_id UUID NOT NULL REFERENCES strategic_memories(id) ON DELETE CASCADE,
    reason TEXT NOT NULL,
    superseded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_memory_supersessions_old ON memory_supersessions(old_memory_id);
CREATE INDEX idx_memory_supersessions_new ON memory_supersessions(new_memory_id);

-- Memory challenges (contradicting evidence)
CREATE TABLE IF NOT EXISTS memory_challenges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id UUID NOT NULL REFERENCES strategic_memories(id) ON DELETE CASCADE,
    challenging_pattern_id UUID NOT NULL,
    challenge_description TEXT NOT NULL,
    evidence_summary JSONB DEFAULT '{}',
    challenged_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved BOOLEAN DEFAULT FALSE,
    resolution_notes TEXT
);

CREATE INDEX idx_memory_challenges_memory ON memory_challenges(memory_id);
CREATE INDEX idx_memory_challenges_unresolved ON memory_challenges(memory_id) WHERE resolved = FALSE;

-- Memory usage tracking (for effectiveness analytics)
CREATE TABLE IF NOT EXISTS memory_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id UUID NOT NULL REFERENCES strategic_memories(id) ON DELETE CASCADE,
    execution_id UUID,
    workflow_type TEXT,
    domain TEXT,
    used_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    outcome_score NUMERIC(5,2),  -- Optional: track execution outcome
    was_helpful BOOLEAN  -- Optional: feedback
);

CREATE INDEX idx_memory_usage_memory ON memory_usage(memory_id, used_at DESC);
CREATE INDEX idx_memory_usage_execution ON memory_usage(execution_id);

-- Views for governance

-- Candidate memories awaiting review
CREATE OR REPLACE VIEW candidate_memories AS
SELECT
    id,
    memory_type,
    title,
    domain,
    scope,
    confidence,
    durability_score,
    array_length(source_pattern_ids, 1) as pattern_count,
    array_length(source_insight_ids, 1) as insight_count,
    created_at
FROM strategic_memories
WHERE status = 'candidate'
ORDER BY confidence DESC, created_at DESC;

-- Active strategic memories
CREATE OR REPLACE VIEW active_strategic_memories AS
SELECT
    id,
    memory_type,
    title,
    domain,
    scope,
    scope_key,
    confidence,
    durability_score,
    usage_count,
    last_used_at,
    expires_at,
    last_validated_at
FROM strategic_memories
WHERE status = 'active'
  AND (expires_at IS NULL OR expires_at > NOW())
ORDER BY
  CASE scope
    WHEN 'global' THEN 1
    WHEN 'domain' THEN 2
    WHEN 'workflow_type' THEN 3
    ELSE 4
  END,
  confidence DESC;

-- Memories needing attention
CREATE OR REPLACE VIEW memories_needing_attention AS
SELECT
    id,
    memory_type,
    title,
    status,
    confidence,
    expires_at,
    last_validated_at,
    CASE
        WHEN expires_at IS NOT NULL AND expires_at < NOW() THEN 'expired'
        WHEN last_validated_at IS NULL THEN 'never_validated'
        WHEN confidence < 0.5 THEN 'low_confidence'
        WHEN expires_at IS NOT NULL AND expires_at < NOW() + INTERVAL '7 days' THEN 'expiring_soon'
        ELSE 'review_needed'
    END as attention_reason
FROM strategic_memories
WHERE status = 'active'
  AND (
    expires_at IS NOT NULL AND expires_at < NOW()
    OR last_validated_at IS NULL
    OR confidence < 0.5
    OR (expires_at IS NOT NULL AND expires_at < NOW() + INTERVAL '7 days')
  )
ORDER BY expires_at NULLS LAST, confidence ASC;

-- Memory effectiveness summary
CREATE OR REPLACE VIEW memory_effectiveness_summary AS
SELECT
    sm.id,
    sm.memory_type,
    sm.title,
    sm.usage_count,
    sm.last_used_at,
    COUNT(mu.id) as tracked_usage_count,
    AVG(mu.outcome_score) as avg_outcome_score,
    SUM(CASE WHEN mu.was_helpful = TRUE THEN 1 ELSE 0 END)::FLOAT / NULLIF(COUNT(*) FILTER (WHERE mu.was_helpful IS NOT NULL), 0) as helpful_ratio
FROM strategic_memories sm
LEFT JOIN memory_usage mu ON sm.id = mu.memory_id
WHERE sm.status = 'active'
GROUP BY sm.id, sm.memory_type, sm.title, sm.usage_count, sm.last_used_at
ORDER BY sm.usage_count DESC;

-- Comments
COMMENT ON TABLE strategic_memories IS 'Persistent strategic knowledge that shapes future agent reasoning.';
COMMENT ON COLUMN strategic_memories.memory_type IS 'Type: heuristic (shortcuts), playbook (guidance), warning (risks), assumption (priors), adaptation_lesson (validated learnings).';
COMMENT ON COLUMN strategic_memories.confidence IS 'How reliable is this memory? Updated from validation.';
COMMENT ON COLUMN strategic_memories.durability_score IS 'How long should this persist? High durability = long-lived institutional knowledge.';
COMMENT ON COLUMN strategic_memories.effectiveness_score IS 'Real-world effectiveness feedback from usage.';
COMMENT ON COLUMN strategic_memories.status IS 'Lifecycle: candidate (pending review), active (in use), deprecated (outdated), supplanted (replaced), archived (removed).';

COMMENT ON TABLE memory_supersessions IS 'Tracks memory evolution when newer memories replace older ones.';
COMMENT ON TABLE memory_challenges IS 'Records when new evidence contradicts an existing memory.';
COMMENT ON TABLE memory_usage IS 'Tracks memory injection and outcomes for effectiveness analytics.';

COMMENT ON VIEW candidate_memories IS 'Memories pending governance review before activation.';
COMMENT ON VIEW active_strategic_memories IS 'Currently active memories available for agent injection.';
COMMENT ON VIEW memories_needing_attention IS 'Memories requiring governance action: expired, low confidence, or never validated.';
COMMENT ON VIEW memory_effectiveness_summary IS 'Usage statistics and effectiveness scores for active memories.';
