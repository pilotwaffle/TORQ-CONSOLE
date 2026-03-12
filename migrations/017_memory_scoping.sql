-- Migration 017: Memory Scoping Rules
-- Purpose: Define scope hierarchy and limits for memory retrieval
-- Phase 4H.1 Milestone 4: Strategic Memory Scoping Rules
-- Created: 2026-03-07

-- Memory scope rules table
CREATE TABLE IF NOT EXISTS memory_scope_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Scope definition
    scope TEXT NOT NULL UNIQUE CHECK (scope IN ('tenant', 'workflow_type', 'domain', 'agent_type', 'global')),
    precedence INTEGER NOT NULL UNIQUE, -- 1=highest (tenant), 5=lowest (global)
    max_memories INTEGER NOT NULL DEFAULT 5,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    -- Configuration
    require_scope_key BOOLEAN DEFAULT FALSE, -- Whether this scope requires a scope_key match
    description TEXT,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Insert default scope rules
INSERT INTO memory_scope_rules (scope, precedence, max_memories, description) VALUES
    ('tenant', 1, 10, 'Tenant-specific memories (highest precedence)'),
    ('workflow_type', 2, 5, 'Workflow-type specific memories'),
    ('domain', 3, 5, 'Domain-specific memories'),
    ('agent_type', 4, 3, 'Agent-type specific memories'),
    ('global', 5, 3, 'Global memories (lowest precedence)')
ON CONFLICT (scope) DO NOTHING;

-- Create index for lookups
CREATE INDEX IF NOT EXISTS idx_memory_scope_rules_precedence ON memory_scope_rules(precedence);

-- View: Active scope configuration
CREATE OR REPLACE VIEW active_scope_configuration AS
SELECT
    scope,
    precedence,
    max_memories,
    enabled,
    description
FROM memory_scope_rules
WHERE enabled = TRUE
ORDER BY precedence ASC;

-- Function: Get scope precedence
CREATE OR REPLACE FUNCTION get_scope_precedence(p_scope TEXT)
RETURNS INTEGER AS $$
BEGIN
    RETURN (
        SELECT precedence
        FROM memory_scope_rules
        WHERE scope = p_scope
          AND enabled = TRUE
        LIMIT 1
    );
END;
$$ LANGUAGE plpgsql;

-- Function: Get max memories for scope
CREATE OR REPLACE FUNCTION get_scope_max_memories(p_scope TEXT)
RETURNS INTEGER AS $$
BEGIN
    RETURN (
        SELECT max_memories
        FROM memory_scope_rules
        WHERE scope = p_scope
          AND enabled = TRUE
        LIMIT 1
    );
END;
$$ LANGUAGE plpgsql;

-- Add scope_key index to strategic_memories if not exists
CREATE INDEX IF NOT EXISTS idx_strategic_memories_scope_key
ON strategic_memories(scope, scope_key)
WHERE status = 'active';

COMMENT ON TABLE memory_scope_rules IS 'Configuration for memory scope hierarchy and retrieval limits.';
COMMENT ON COLUMN memory_scope_rules.precedence IS 'Lower number = higher precedence. Tenant=1, Global=5';
COMMENT ON COLUMN memory_scope_rules.max_memories IS 'Maximum memories to retrieve from this scope';
COMMENT ON VIEW active_scope_configuration IS 'Current active scope configuration ordered by precedence';

COMMENT ON FUNCTION get_scope_precedence IS 'Get precedence level for a scope (lower = higher priority)';
COMMENT ON FUNCTION get_scope_max_memories IS 'Get maximum number of memories to retrieve from a scope';
