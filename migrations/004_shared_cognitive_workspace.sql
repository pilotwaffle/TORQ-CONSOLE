-- Shared Cognitive Workspace migration
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS workspaces (
    workspace_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scope_type TEXT NOT NULL,
    scope_id TEXT NOT NULL,
    tenant_id TEXT NOT NULL DEFAULT 'default',
    title TEXT,
    description TEXT,
    created_by TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT valid_workspace_scope_type CHECK (
        scope_type IN ('session', 'workflow_execution', 'agent_team')
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_workspaces_scope_unique
ON workspaces(tenant_id, scope_type, scope_id);

CREATE INDEX IF NOT EXISTS idx_workspaces_scope
ON workspaces(scope_type, scope_id);

CREATE INDEX IF NOT EXISTS idx_workspaces_tenant
ON workspaces(tenant_id);

CREATE TABLE IF NOT EXISTS working_memory_entries (
    memory_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(workspace_id) ON DELETE CASCADE,
    tenant_id TEXT NOT NULL DEFAULT 'default',
    entry_type TEXT NOT NULL,
    content JSONB NOT NULL DEFAULT '{}',
    source_agent TEXT,
    confidence DOUBLE PRECISION NOT NULL DEFAULT 0.8,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT valid_entry_type CHECK (
        entry_type IN ('fact', 'hypothesis', 'question', 'decision', 'artifact', 'note')
    ),
    CONSTRAINT valid_entry_status CHECK (
        status IN ('active', 'resolved', 'revised', 'deprecated')
    ),
    CONSTRAINT valid_confidence CHECK (confidence >= 0.0 AND confidence <= 1.0)
);

CREATE INDEX IF NOT EXISTS idx_working_memory_workspace
ON working_memory_entries(workspace_id);

CREATE INDEX IF NOT EXISTS idx_working_memory_workspace_type
ON working_memory_entries(workspace_id, entry_type);

CREATE INDEX IF NOT EXISTS idx_working_memory_status
ON working_memory_entries(status);

CREATE INDEX IF NOT EXISTS idx_working_memory_tenant
ON working_memory_entries(tenant_id);

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_workspaces_updated_at ON workspaces;
CREATE TRIGGER trg_workspaces_updated_at
BEFORE UPDATE ON workspaces
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_working_memory_entries_updated_at ON working_memory_entries;
CREATE TRIGGER trg_working_memory_entries_updated_at
BEFORE UPDATE ON working_memory_entries
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
