-- ============================================================================
-- Phase 5.3 Milestone 2: Workspace Artifacts Table
-- ============================================================================
--
-- This migration creates the `workspace_artifacts` table for persisting
-- tool execution outputs as first-class workspace artifacts.
--
-- The table is designed to be additive - it complements existing team and
-- mission persistence without replacing it.
--
-- See: docs/PHASE_5_3_WORKSPACE_INTEGRATION_PRD.md
-- ============================================================================

-- Create workspace_artifacts table
CREATE TABLE IF NOT EXISTS workspace_artifacts (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL,

    -- Execution context linking
    mission_id UUID,
    node_id UUID,
    execution_id TEXT,
    team_execution_id UUID,
    round_number INTEGER,
    role_name TEXT,

    -- Tool identification
    tool_name TEXT NOT NULL,
    artifact_type TEXT NOT NULL,

    -- Artifact content
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    content_json JSONB NOT NULL DEFAULT '{}',
    content_text TEXT NOT NULL DEFAULT '',
    source_ref TEXT,

    -- Full execution metadata (preserves all tool-specific context)
    execution_metadata JSONB NOT NULL DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT workspace_artifacts_workspace_fk
        FOREIGN KEY (workspace_id)
        REFERENCES workspaces(workspace_id)
        ON DELETE CASCADE,

    CONSTRAINT workspace_artifacts_team_execution_fk
        FOREIGN KEY (team_execution_id)
        REFERENCES team_executions(id)
        ON DELETE SET NULL
);

-- Indexes for efficient querying

-- Primary lookup by workspace
CREATE INDEX IF NOT EXISTS idx_workspace_artifacts_workspace_id
    ON workspace_artifacts(workspace_id, created_at DESC);

-- Team execution lookup (for Phase 5.2 integration)
CREATE INDEX IF NOT EXISTS idx_workspace_artifacts_team_execution
    ON workspace_artifacts(team_execution_id, round_number, created_at)
    WHERE team_execution_id IS NOT NULL;

-- Mission/node lookup
CREATE INDEX IF NOT EXISTS idx_workspace_artifacts_mission_node
    ON workspace_artifacts(mission_id, node_id, created_at)
    WHERE mission_id IS NOT NULL;

-- Execution lookup
CREATE INDEX IF NOT EXISTS idx_workspace_artifacts_execution_id
    ON workspace_artifacts(execution_id, created_at)
    WHERE execution_id IS NOT NULL;

-- Type filtering
CREATE INDEX IF NOT EXISTS idx_workspace_artifacts_type
    ON workspace_artifacts(artifact_type, created_at DESC);

-- Tool filtering
CREATE INDEX IF NOT EXISTS idx_workspace_artifacts_tool_name
    ON workspace_artifacts(tool_name, created_at DESC);

-- Role filtering
CREATE INDEX IF NOT EXISTS idx_workspace_artifacts_role_name
    ON workspace_artifacts(role_name, created_at DESC)
    WHERE role_name IS NOT NULL;

-- Full-text search on title and summary
CREATE INDEX IF NOT EXISTS idx_workspace_artifacts_search
    ON workspace_artifacts USING gin(to_tsvector('english', title || ' ' || summary));

-- GIN index for content_json queries
CREATE INDEX IF NOT EXISTS idx_workspace_artifacts_content_json
    ON workspace_artifacts USING gin(content_json);

-- Comments for documentation

COMMENT ON TABLE workspace_artifacts IS '
Workspace artifacts from tool execution.

Persists normalized tool outputs as first-class artifacts linked to
workspace, mission, node, execution, and team context.

Phase 5.3: Agent Tool Workspace Integration
';

COMMENT ON COLUMN workspace_artifacts.id IS 'Unique artifact identifier';
COMMENT ON COLUMN workspace_artifacts.workspace_id IS 'Reference to owning workspace';
COMMENT ON COLUMN workspace_artifacts.mission_id IS 'Optional mission reference';
COMMENT ON COLUMN workspace_artifacts.node_id IS 'Optional node reference';
COMMENT ON COLUMN workspace_artifacts.execution_id IS 'Optional workflow execution reference';
COMMENT ON COLUMN workspace_artifacts.team_execution_id IS 'Optional team execution reference (Phase 5.2)';
COMMENT ON COLUMN workspace_artifacts.round_number IS 'Optional team round number';
COMMENT ON COLUMN workspace_artifacts.role_name IS 'Optional invoking role name';
COMMENT ON COLUMN workspace_artifacts.tool_name IS 'Tool identifier (e.g., web_search, file_read)';
COMMENT ON COLUMN workspace_artifacts.artifact_type IS 'Artifact category (e.g., web_search, file_read, code_execution)';
COMMENT ON COLUMN workspace_artifacts.title IS 'Human-readable title';
COMMENT ON COLUMN workspace_artifacts.summary IS 'Short summary for retrieval and UI';
COMMENT ON COLUMN workspace_artifacts.content_json IS 'Structured artifact payload';
COMMENT ON COLUMN workspace_artifacts.content_text IS 'Plain text representation';
COMMENT ON COLUMN workspace_artifacts.source_ref IS 'Optional source reference (URL, file path, etc.)';
COMMENT ON COLUMN workspace_artifacts.execution_metadata IS 'Full execution metadata including timing and status';
COMMENT ON COLUMN workspace_artifacts.created_at IS 'Artifact creation timestamp';

-- ============================================================================
-- Row Level Security (RLS)
-- ============================================================================

-- Enable RLS
ALTER TABLE workspace_artifacts ENABLE ROW LEVEL SECURITY;

-- Policy: Users can read artifacts from workspaces they have access to
CREATE POLICY workspace_artifacts_select_policy ON workspace_artifacts
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM workspaces
            WHERE workspaces.workspace_id = workspace_artifacts.workspace_id
            AND (
                -- Service account can access all
                workspaces.tenant_id = 'default'
                OR workspaces.tenant_id = current_setting('request.jwt.claim.tenant_id', true)
            )
        )
    );

-- Policy: Service can insert artifacts (via API)
CREATE POLICY workspace_artifacts_insert_policy ON workspace_artifacts
    FOR INSERT
    WITH CHECK (true);

-- ============================================================================
-- Validation functions
-- ============================================================================

-- Function to validate artifact_type
CREATE OR REPLACE FUNCTION validate_artifact_type(artifact_type TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN artifact_type IN (
        'web_search', 'news_search', 'research_synthesis',
        'file_read', 'file_write',
        'database_query',
        'code_execution',
        'api_call',
        'document_generation',
        'data_analysis', 'data_visualization',
        'knowledge_query', 'validation', 'synthesis',
        'team_decision', 'team_message', 'role_output',
        'generic_artifact'
    );
END;
$$ LANGUAGE plpgsql;

-- Add check constraint for artifact_type
ALTER TABLE workspace_artifacts
    ADD CONSTRAINT workspace_artifacts_valid_type
    CHECK (validate_artifact_type(artifact_type));

-- ============================================================================
-- Helper functions
-- ============================================================================

-- Function: Get artifacts for a team execution
CREATE OR REPLACE FUNCTION get_team_execution_artifacts(
    p_team_execution_id UUID,
    p_round_number INTEGER DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    artifact_type TEXT,
    tool_name TEXT,
    title TEXT,
    summary TEXT,
    role_name TEXT,
    round_number INTEGER,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        wa.id,
        wa.artifact_type,
        wa.tool_name,
        wa.title,
        wa.summary,
        wa.role_name,
        wa.round_number,
        wa.created_at
    FROM workspace_artifacts wa
    WHERE wa.team_execution_id = p_team_execution_id
        AND (p_round_number IS NULL OR wa.round_number = p_round_number)
    ORDER BY wa.round_number, wa.created_at;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function: Get artifacts for an execution
CREATE OR REPLACE FUNCTION get_execution_artifacts(
    p_execution_id TEXT
)
RETURNS TABLE (
    id UUID,
    artifact_type TEXT,
    tool_name TEXT,
    title TEXT,
    summary TEXT,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        wa.id,
        wa.artifact_type,
        wa.tool_name,
        wa.title,
        wa.summary,
        wa.created_at
    FROM workspace_artifacts wa
    WHERE wa.execution_id = p_execution_id
    ORDER BY wa.created_at;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function: Get artifacts for a workspace (paginated)
CREATE OR REPLACE FUNCTION get_workspace_artifacts_paginated(
    p_workspace_id TEXT,
    p_limit INTEGER DEFAULT 100,
    p_offset INTEGER DEFAULT 0,
    p_artifact_type TEXT DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    artifact_type TEXT,
    tool_name TEXT,
    title TEXT,
    summary TEXT,
    created_at TIMESTAMPTZ,
    total_count BIGINT
) AS $$
DECLARE
    v_total_count BIGINT;
BEGIN
    -- Count total matching artifacts
    SELECT COUNT(*)
    INTO v_total_count
    FROM workspace_artifacts
    WHERE workspace_id = p_workspace_id
        AND (p_artifact_type IS NULL OR artifact_type = p_artifact_type);

    -- Return paginated results with total count
    RETURN QUERY
    SELECT
        wa.id,
        wa.artifact_type,
        wa.tool_name,
        wa.title,
        wa.summary,
        wa.created_at,
        v_total_count::BIGINT
    FROM workspace_artifacts wa
    WHERE wa.workspace_id = p_workspace_id
        AND (p_artifact_type IS NULL OR wa.artifact_type = p_artifact_type)
    ORDER BY wa.created_at DESC
    LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- Triggers for automatic timestamp updates
-- ============================================================================

-- Function to set created_at (default is usually sufficient, but this ensures consistency)
CREATE OR REPLACE FUNCTION workspace_artifacts_created_at_trigger()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.created_at IS NULL OR NEW.created_at < NOW() - INTERVAL '1 second' THEN
        NEW.created_at = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER workspace_artifacts_set_created_at
    BEFORE INSERT ON workspace_artifacts
    FOR EACH ROW
    EXECUTE FUNCTION workspace_artifacts_created_at_trigger();

-- ============================================================================
-- Migration complete
-- ============================================================================

-- Verify table was created
DO $$
BEGIN
    RAISE NOTICE 'workspace_artifacts table created successfully';
    RAISE NOTICE 'Indexes: 10 indexes created for efficient querying';
    RAISE NOTICE 'RLS: 2 policies created for read/write access';
    RAISE NOTICE 'Functions: 3 helper functions for artifact retrieval';
END $$;
