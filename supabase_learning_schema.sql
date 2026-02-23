-- Supabase Learning Events Schema for TORQ Console
--
-- Run this in your Supabase SQL Editor:
-- 1. Go to https://supabase.com/dashboard
-- 2. Select your project (lkaddjvuptwboaytruiz)
-- 3. Go to SQL Editor
-- 4. Paste and run this script

-- Enable pgvector extension for vector similarity search
create extension if not exists vector;

-- Learning Events Table
CREATE TABLE IF NOT EXISTS learning_events (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    event_id TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Query and mode
    query TEXT NOT NULL,
    query_embedding VECTOR(1536),
    mode TEXT NOT NULL,

    -- Outcome
    success BOOLEAN NOT NULL,
    reward DECIMAL(5,4) NOT NULL,
    execution_time DECIMAL(8,3) NOT NULL,
    outcome TEXT NOT NULL,

    -- Tools and metadata
    tools_used TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}'
);

-- Create vector similarity search function
CREATE OR REPLACE FUNCTION match_learning_events(
    query_embedding VECTOR(1536),
    match_threshold DECIMAL DEFAULT 0.7,
    match_count INTEGER DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    event_id TEXT,
    query TEXT,
    mode TEXT,
    success BOOLEAN,
    reward DECIMAL,
    similarity DECIMAL
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        le.id,
        le.event_id,
        le.query,
        le.mode,
        le.success,
        le.reward,
        1 - (le.query_embedding <=> query_embedding) as similarity
    FROM learning_events le
    WHERE le.query_embedding IS NOT NULL
        AND (1 - (le.query_embedding <=> query_embedding)) >= match_threshold
    ORDER BY le.query_embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_learning_events_query_embedding
ON learning_events USING ivfflat (query_embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_learning_events_mode
ON learning_events(mode);

CREATE INDEX IF NOT EXISTS idx_learning_events_success
ON learning_events(success);

CREATE INDEX IF NOT EXISTS idx_learning_events_created_at
ON learning_events(created_at DESC);

-- Enable Row Level Security (optional, can be disabled for single-user)
ALTER TABLE learning_events ENABLE ROW LEVEL SECURITY;

-- Allow service role full access
CREATE POLICY "Service role full access learning_events" ON learning_events
    FOR ALL USING (auth.role() = 'service_role');

-- Verification query - run this to confirm setup
SELECT 'learning_events table exists' as status, COUNT(*) as row_count FROM learning_events;
