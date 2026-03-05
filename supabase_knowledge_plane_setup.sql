-- TORQ Knowledge Plane Supabase Setup
-- Run this in your Supabase SQL Editor to initialize the Knowledge Plane tables

-- Enable pgvector extension for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Create torq_knowledge table
CREATE TABLE IF NOT EXISTS torq_knowledge (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    title TEXT,
    category TEXT DEFAULT 'other',
    tags TEXT[] DEFAULT '{}',
    source TEXT,
    metadata JSONB DEFAULT '{}',
    embedding VECTOR(1536),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_knowledge_category ON torq_knowledge(category);
CREATE INDEX IF NOT EXISTS idx_knowledge_tags ON torq_knowledge USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_knowledge_created ON torq_knowledge(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_knowledge_source ON torq_knowledge(source);

-- Create vector similarity index (for semantic search)
-- Note: This requires at least 100 rows in the table before creating
-- CREATE INDEX IF NOT EXISTS idx_knowledge_embedding
--     ON torq_knowledge USING ivfflat(embedding vector_cosine_ops)
--     WITH (lists = 100);

-- Add comments for documentation
COMMENT ON TABLE torq_knowledge IS 'TORQ Knowledge Plane - semantic knowledge storage for agents';
COMMENT ON COLUMN torq_knowledge.id IS 'Unique identifier (UUID)';
COMMENT ON COLUMN torq_knowledge.content IS 'Knowledge content text';
COMMENT ON COLUMN torq_knowledge.title IS 'Optional title for the knowledge entry';
COMMENT ON COLUMN torq_knowledge.category IS 'Category classification';
COMMENT ON COLUMN torq_knowledge.tags IS 'Tags for organization and filtering';
COMMENT ON COLUMN torq_knowledge.source IS 'Source of the knowledge (agent, user, system)';
COMMENT ON COLUMN torq_knowledge.metadata IS 'Additional metadata as JSONB';
COMMENT ON COLUMN torq_knowledge.embedding IS 'Vector embedding for semantic search (1536 dims for OpenAI)';
COMMENT ON COLUMN torq_knowledge.created_at IS 'Creation timestamp';
COMMENT ON COLUMN torq_knowledge.updated_at IS 'Last update timestamp';

-- Enable Row Level Security
ALTER TABLE torq_knowledge ENABLE ROW LEVEL SECURITY;

-- Create policies
-- Allow service role to do everything
CREATE POLICY "Service role can do anything" ON torq_knowledge
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Allow anon to read knowledge entries (for public knowledge)
CREATE POLICY "Anon can read knowledge" ON torq_knowledge
    FOR SELECT
    TO anon
    USING (true);

-- Create a function for semantic search (match_knowledge)
CREATE OR REPLACE FUNCTION match_knowledge(
    query_embedding VECTOR(1536),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 10
)
RETURNS TABLE(
    id TEXT,
    content TEXT,
    title TEXT,
    category TEXT,
    tags TEXT[],
    source TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        torq_knowledge.id,
        torq_knowledge.content,
        torq_knowledge.title,
        torq_knowledge.category,
        torq_knowledge.tags,
        torq_knowledge.source,
        torq_knowledge.metadata,
        torq_knowledge.created_at,
        torq_knowledge.updated_at,
        1 - (torq_knowledge.embedding <=> query_embedding) AS similarity
    FROM torq_knowledge
    WHERE torq_knowledge.embedding IS NOT NULL
        AND 1 - (torq_knowledge.embedding <=> query_embedding) > match_threshold
    ORDER BY torq_knowledge.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_knowledge_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER knowledge_updated_at
    BEFORE UPDATE ON torq_knowledge
    FOR EACH ROW
    EXECUTE FUNCTION update_knowledge_updated_at();

-- Sample knowledge entries for testing
INSERT INTO torq_knowledge (id, content, title, category, tags, source) VALUES
    ('sample-1', 'FastAPI is a modern, fast web framework for building APIs with Python 3.7+ based on standard Python type hints.', 'FastAPI Overview', 'documentation', ['python', 'fastapi', 'web', 'api'], 'system'),
    ('sample-2', 'Supabase is an open source Firebase alternative. It provides PostgreSQL database, authentication, and storage.', 'Supabase Overview', 'documentation', ['database', 'supabase', 'postgresql'], 'system'),
    ('sample-3', 'Railway is a platform for deploying and managing applications. It supports various languages and frameworks.', 'Railway Deployment', 'documentation', ['deployment', 'railway', 'devops'], 'system')
ON CONFLICT (id) DO NOTHING;

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON torq_knowledge TO service_role;
GRANT SELECT ON torq_knowledge TO anon, authenticated;
GRANT EXECUTE ON FUNCTION match_knowledge TO service_role, authenticated;

-- Verification query
SELECT
    'torq_knowledge table created' as status,
    COUNT(*) as row_count
FROM torq_knowledge;
