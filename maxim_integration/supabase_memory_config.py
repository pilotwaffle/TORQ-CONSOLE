"""
Supabase Memory Configuration for Enhanced Prince Flowers Agent

Setup and configuration for Supabase long-term memory with learning capabilities.
"""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class SupabaseConfig:
    """Supabase configuration for memory system."""
    url: str
    service_role_key: str
    openai_api_key: str
    user_id: str = "prince_flowers_user"
    agent_id: str = "prince_flowers_enhanced"

class SupabaseMemorySetup:
    """Setup and configure Supabase memory for enhanced Prince Flowers."""

    def __init__(self):
        self.logger = logging.getLogger("SupabaseMemorySetup")
        self.config = self._load_config()

    def _load_config(self) -> Optional[SupabaseConfig]:
        """Load Supabase configuration from environment variables."""
        try:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            openai_key = os.getenv("OPENAI_API_KEY")

            if not all([supabase_url, supabase_key, openai_key]):
                self.logger.warning("Missing required Supabase environment variables")
                return None

            return SupabaseConfig(
                url=supabase_url,
                service_role_key=supabase_key,
                openai_api_key=openai_key
            )

        except Exception as e:
            self.logger.error(f"Failed to load Supabase config: {e}")
            return None

    def generate_setup_instructions(self) -> str:
        """Generate setup instructions for Supabase memory."""
        return """
# Supabase Memory Setup Instructions

## 1. Create Supabase Project
1. Go to https://supabase.com
2. Create a new project
3. Note your project URL and service role key

## 2. Set Environment Variables
Add these to your .env file or system environment:

```bash
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
OPENAI_API_KEY=your_openai_api_key

# Optional: Custom user/agent IDs
PRINCE_FLOWERS_USER_ID=prince_flowers_user
PRINCE_FLOWERS_AGENT_ID=prince_flowers_enhanced
```

## 3. Run Database Setup
Execute the SQL schema provided in supabase_schema.sql

## 4. Test Configuration
Run: python test_supabase_memory.py

## 5. Verify Tables
Check that these tables exist:
- enhanced_memory (interaction storage)
- agent_patterns (learning patterns)
- codebase_entities (knowledge graph)
- agent_performance_metrics (performance tracking)
- interaction_embeddings (semantic search)
"""

    def is_configured(self) -> bool:
        """Check if Supabase is properly configured."""
        return self.config is not None

    def get_config(self) -> Optional[SupabaseConfig]:
        """Get Supabase configuration."""
        return self.config

def create_supabase_schema_sql() -> str:
    """Generate SQL schema for Supabase memory system."""
    return """
-- Enhanced Memory System Schema for Prince Flowers Agent

-- 1. Enhanced Memory Table (long-term storage)
CREATE TABLE IF NOT EXISTS enhanced_memory (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    memory_tier TEXT NOT NULL CHECK (memory_tier IN ('short', 'long')),
    memory_type TEXT NOT NULL CHECK (memory_type IN ('knowledge', 'pattern', 'entity', 'interaction')),
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    importance_score DECIMAL(3,2) DEFAULT 5.0 CHECK (importance_score >= 0 AND importance_score <= 10),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    access_count INTEGER DEFAULT 0
);

-- 2. Agent Patterns Table (learning patterns)
CREATE TABLE IF NOT EXISTS agent_patterns (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    agent_id TEXT NOT NULL,
    pattern_type TEXT NOT NULL,
    pattern_content JSONB NOT NULL,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    success_rate DECIMAL(3,2) GENERATED ALWAYS AS (
        CASE WHEN (success_count + failure_count) > 0
        THEN success_count::DECIMAL / (success_count + failure_count)
        ELSE 0 END
    ) STORED,
    last_used TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Codebase Entities Table (knowledge graph)
CREATE TABLE IF NOT EXISTS codebase_entities (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_name TEXT NOT NULL,
    attributes JSONB NOT NULL,
    relationships JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, entity_type, entity_name)
);

-- 4. Agent Performance Metrics Table
CREATE TABLE IF NOT EXISTS agent_performance_metrics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    agent_id TEXT NOT NULL,
    metric_type TEXT NOT NULL,
    metric_value DECIMAL(5,2) NOT NULL,
    metric_metadata JSONB DEFAULT '{}',
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Interaction Embeddings Table (for semantic search)
CREATE TABLE IF NOT EXISTS interaction_embeddings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    memory_id UUID REFERENCES enhanced_memory(id) ON DELETE CASCADE,
    content_embedding VECTOR(1536), -- OpenAI text-embedding-3-small
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. Query Routing Patterns Table
CREATE TABLE IF NOT EXISTS query_routing_patterns (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    agent_id TEXT NOT NULL,
    query_pattern TEXT NOT NULL,
    intent_classification TEXT NOT NULL,
    routing_decision TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    confidence_score DECIMAL(3,2),
    tools_used JSONB DEFAULT '[]',
    execution_time DECIMAL(8,3),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. Learning Feedback Table
CREATE TABLE IF NOT EXISTS learning_feedback (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    interaction_id UUID,
    feedback_type TEXT NOT NULL CHECK (feedback_type IN ('user_rating', 'correction', 'improvement')),
    feedback_data JSONB NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_enhanced_memory_user_agent ON enhanced_memory(user_id, agent_id);
CREATE INDEX IF NOT EXISTS idx_enhanced_memory_content_hash ON enhanced_memory(content_hash);
CREATE INDEX IF NOT EXISTS idx_enhanced_memory_importance ON enhanced_memory(importance_score DESC);
CREATE INDEX IF NOT EXISTS idx_enhanced_memory_type_tier ON enhanced_memory(memory_type, memory_tier);
CREATE INDEX IF NOT EXISTS idx_agent_patterns_agent_type ON agent_patterns(agent_id, pattern_type);
CREATE INDEX IF NOT EXISTS idx_codebase_entities_user_type ON codebase_entities(user_id, entity_type);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_agent_type ON agent_performance_metrics(agent_id, metric_type);
CREATE INDEX IF NOT EXISTS idx_routing_patterns_agent ON query_routing_patterns(agent_id);
CREATE INDEX IF NOT EXISTS idx_routing_patterns_success ON query_routing_patterns(success, created_at);

-- Vector Index for Semantic Search (pgvector extension required)
CREATE INDEX IF NOT EXISTS idx_interaction_embeddings_vector ON interaction_embeddings
USING ivfflat (content_embedding vector_cosine_ops);

-- Functions for Memory Management
CREATE OR REPLACE FUNCTION update_memory_access(memory_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE enhanced_memory
    SET last_accessed = NOW(), access_count = access_count + 1
    WHERE id = memory_id;
END;
$$ LANGUAGE plpgsql;

-- Function for Pattern Learning
CREATE OR REPLACE FUNCTION update_agent_pattern(
    agent_id_param TEXT,
    pattern_type_param TEXT,
    pattern_content_param JSONB,
    success_param BOOLEAN
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO agent_patterns (agent_id, pattern_type, pattern_content, success_count, failure_count)
    VALUES (agent_id_param, pattern_type_param, pattern_content_param,
            CASE WHEN success_param THEN 1 ELSE 0 END,
            CASE WHEN success_param THEN 0 ELSE 1 END)
    ON CONFLICT (agent_id, pattern_type)
    DO UPDATE SET
        pattern_content = pattern_content_param,
        success_count = agent_patterns.success_count + CASE WHEN success_param THEN 1 ELSE 0 END,
        failure_count = agent_patterns.failure_count + CASE WHEN success_param THEN 0 ELSE 1 END,
        last_used = NOW(),
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- Function for Performance Metrics
CREATE OR REPLACE FUNCTION record_performance_metric(
    agent_id_param TEXT,
    metric_type_param TEXT,
    metric_value_param DECIMAL,
    metric_metadata_param JSONB DEFAULT '{}'
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO agent_performance_metrics (agent_id, metric_type, metric_value, metric_metadata)
    VALUES (agent_id_param, metric_type_param, metric_value_param, metric_metadata_param);
END;
$$ LANGUAGE plpgsql;

-- Semantic Search Function
CREATE OR REPLACE FUNCTION search_similar_memories(
    query_embedding VECTOR(1536),
    match_user_id TEXT DEFAULT NULL,
    match_agent_id TEXT DEFAULT NULL,
    match_threshold DECIMAL DEFAULT 0.78,
    match_count INTEGER DEFAULT 5
)
RETURNS TABLE(
    memory_id UUID,
    similarity DECIMAL,
    content TEXT,
    metadata JSONB,
    importance_score DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        m.id,
        1 - (ie.content_embedding <=> query_embedding) as similarity,
        m.content,
        m.metadata,
        m.importance_score
    FROM enhanced_memory m
    JOIN interaction_embeddings ie ON m.id = ie.memory_id
    WHERE
        (match_user_id IS NULL OR m.user_id = match_user_id) AND
        (match_agent_id IS NULL OR m.agent_id = match_agent_id) AND
        (1 - (ie.content_embedding <=> query_embedding)) >= match_threshold
    ORDER BY similarity DESC, m.importance_score DESC
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Cleanup Function for Expired Memories
CREATE OR REPLACE FUNCTION cleanup_expired_memories()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM enhanced_memory
    WHERE expires_at IS NOT NULL AND expires_at < NOW();

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Row Level Security (RLS) Policies
ALTER TABLE enhanced_memory ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_patterns ENABLE ROW LEVEL SECURITY;
ALTER TABLE codebase_entities ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_performance_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE interaction_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE query_routing_patterns ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_feedback ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view their own memories" ON enhanced_memory
    FOR SELECT USING (user_id = current_setting('app.current_user_id', true));

CREATE POLICY "Users can insert their own memories" ON enhanced_memory
    FOR INSERT WITH CHECK (user_id = current_setting('app.current_user_id', true));

CREATE POLICY "Users can update their own memories" ON enhanced_memory
    FOR UPDATE USING (user_id = current_setting('app.current_user_id', true));

-- Similar policies for other tables...
CREATE POLICY "Agents can manage their patterns" ON agent_patterns
    FOR ALL USING (agent_id = current_setting('app.current_agent_id', true));

CREATE POLICY "Users can manage their entities" ON codebase_entities
    FOR ALL USING (user_id = current_setting('app.current_user_id', true));
"""

# Singleton instance
_supabase_setup = None

def get_supabase_setup() -> SupabaseMemorySetup:
    """Get or create Supabase setup instance."""
    global _supabase_setup
    if _supabase_setup is None:
        _supabase_setup = SupabaseMemorySetup()
    return _supabase_setup