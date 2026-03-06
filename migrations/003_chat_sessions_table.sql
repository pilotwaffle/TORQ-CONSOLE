-- ============================================================================
-- TORQ Console - Chat Sessions Table for Session Persistence
-- ============================================================================
--
-- This migration adds the chat_sessions table for conversation memory.
-- Stores message history with support for soft-delete and multi-turn context.
-- ============================================================================

CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id TEXT PRIMARY KEY,
    tenant_id TEXT DEFAULT 'default',

    -- Messages array with full conversation history
    messages JSONB DEFAULT '[]',

    -- Session metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Optional session metadata
    title TEXT,
    agent_id TEXT,
    metadata JSONB DEFAULT '{}'
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_chat_sessions_tenant ON chat_sessions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_created_at ON chat_sessions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_agent_id ON chat_sessions(agent_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_updated_at ON chat_sessions(updated_at DESC);

-- ============================================================================
-- Row Level Security
-- ============================================================================

ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access sessions in their tenant
CREATE POLICY "tenant_isolate_chat_sessions" ON chat_sessions
    FOR ALL
    USING (tenant_id = COALESCE(current_setting('request.jwt.claim.tenant_id', true), 'default'));

CREATE POLICY "chat_sessions_read_own_tenant" ON chat_sessions
    FOR SELECT
    USING (tenant_id = COALESCE(current_setting('request.jwt.claim.tenant_id', true), 'default'));

CREATE POLICY "chat_sessions_insert_own_tenant" ON chat_sessions
    FOR INSERT
    WITH CHECK (tenant_id = COALESCE(current_setting('request.jwt.claim.tenant_id', true), 'default'));

CREATE POLICY "chat_sessions_update_own_tenant" ON chat_sessions
    FOR UPDATE
    USING (tenant_id = COALESCE(current_setting('request.jwt.claim.tenant_id', true), 'default'));

CREATE POLICY "chat_sessions_delete_own_tenant" ON chat_sessions
    FOR DELETE
    USING (tenant_id = COALESCE(current_setting('request.jwt.claim.tenant_id', true), 'default'));

-- ============================================================================
-- Triggers
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE TRIGGER update_chat_sessions_updated_at
    BEFORE UPDATE ON chat_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Helper function for message cleanup
-- ============================================================================

-- Function to remove soft-deleted messages and trim to max messages
CREATE OR REPLACE FUNCTION cleanup_session_messages(p_session_id TEXT, p_max_messages INT DEFAULT 100)
RETURNS VOID AS $$
BEGIN
    UPDATE chat_sessions
    SET messages = (
        SELECT jsonb_agg(msg)
        FROM (
            SELECT msg
            FROM jsonb_array_elements(messages) AS msg
            WHERE NOT (msg->>'deleted' = 'true')
            ORDER BY (msg->>'timestamp')::timestamptz DESC
            LIMIT p_max_messages
        ) AS trimmed
    )
    WHERE session_id = p_session_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON TABLE chat_sessions IS 'Stores conversation history for chat session persistence';
COMMENT ON COLUMN chat_sessions.session_id IS 'Unique session identifier (client-generated)';
COMMENT ON COLUMN chat_sessions.tenant_id IS 'Tenant for multi-tenancy isolation';
COMMENT ON COLUMN chat_sessions.messages IS 'Array of message objects with role, content, timestamp, agent_id, deleted flag';
COMMENT ON COLUMN chat_sessions.title IS 'Optional session title for UI display';
COMMENT ON COLUMN chat_sessions.agent_id IS 'Default agent for this session (if any)';
COMMENT ON COLUMN chat_sessions.metadata IS 'Additional session metadata (user preferences, context, etc.)';
