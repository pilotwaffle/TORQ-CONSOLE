# MIGRATION REQUIRED: chat_sessions Table

## Status
The session memory persistence code is complete, but the database table needs to be created.

## Quick Apply (2 minutes)

1. Go to **Supabase Dashboard**: https://app.supabase.com
2. Select project: **npukynbaglmcdvzyklqa**
3. Click **SQL Editor** in left sidebar
4. Click **New Query**
5. Copy and paste the SQL below
6. Click **Run**

## Migration SQL

```sql
-- ============================================================================
-- TORQ Console - Chat Sessions Table for Session Persistence
-- ============================================================================

CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id TEXT PRIMARY KEY,
    tenant_id TEXT DEFAULT 'default',
    messages JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    title TEXT,
    agent_id TEXT,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_tenant ON chat_sessions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_created_at ON chat_sessions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_agent_id ON chat_sessions(agent_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_updated_at ON chat_sessions(updated_at DESC);

ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;

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

CREATE TRIGGER update_chat_sessions_updated_at
    BEFORE UPDATE ON chat_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

## After Applying Migration

1. **Redeploy Railway** (or wait for auto-deploy if connected to GitHub)
2. **Run validation**:
   ```bash
   RAILWAY_URL=https://your-url.up.railway.app python validate_session_memory.py
   ```

## Verify Table Exists

After applying, you should see the table in Supabase:
- Table Editor > chat_sessions
- Should have columns: session_id, tenant_id, messages, created_at, updated_at, title, agent_id, metadata
