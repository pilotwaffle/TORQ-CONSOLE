-- Migration: Workspace Syntheses Table
-- Purpose: Store synthesized reasoning artifacts (summaries, insights, contradictions, etc.)
-- Date: 2026-03-08
-- Phase: 4E - Reasoning Synthesis Engine

CREATE TABLE IF NOT EXISTS workspace_syntheses (
    synthesis_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(workspace_id) ON DELETE CASCADE,
    synthesis_type TEXT NOT NULL CHECK (synthesis_type IN (
        'summary',
        'insights',
        'risks',
        'contradictions',
        'next_actions',
        'executive_brief'
    )),
    content JSONB NOT NULL DEFAULT '{}',
    source_model TEXT,
    generated_by TEXT,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Ensure one version per type per workspace
    CONSTRAINT unique_synthesis_version UNIQUE (workspace_id, synthesis_type, version)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_workspace_syntheses_workspace_id ON workspace_syntheses(workspace_id);
CREATE INDEX IF NOT EXISTS idx_workspace_syntheses_type ON workspace_syntheses(synthesis_type);
CREATE INDEX IF NOT EXISTS idx_workspace_syntheses_workspace_type_version
    ON workspace_syntheses(workspace_id, synthesis_type, version DESC);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_workspace_syntheses_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_workspace_syntheses_updated_at ON workspace_syntheses;
CREATE TRIGGER trigger_workspace_syntheses_updated_at
    BEFORE UPDATE ON workspace_syntheses
    FOR EACH ROW
    EXECUTE FUNCTION update_workspace_syntheses_updated_at();

-- Comments
COMMENT ON TABLE workspace_syntheses IS 'Synthesized reasoning artifacts derived from workspace entries';
COMMENT ON COLUMN workspace_syntheses.synthesis_type IS 'Type of synthesis: summary, insights, risks, contradictions, next_actions, executive_brief';
COMMENT ON COLUMN workspace_syntheses.content IS 'Structured synthesis output (JSONB)';
COMMENT ON COLUMN workspace_syntheses.version IS 'Version number for regeneration support';
COMMENT ON COLUMN workspace_syntheses.source_model IS 'LLM model used (e.g., claude-sonnet-4-6) or "heuristic" for fallback';
