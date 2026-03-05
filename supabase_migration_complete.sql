-- TORQ Console - Complete Supabase Schema Migration
-- Project: npukynbaglmcdvzyklqa
-- This migration adds all tables needed for Multi-Agent Orchestration, Cognitive Loop, and Marvin Agent Memory

-- ============================================================================
-- EXISTING: thoughts table (Knowledge Plane) - Already deployed
-- ============================================================================
-- thoughts table with pgvector already exists with 9 records

-- ============================================================================
-- Marvin Agent Memory System
-- ============================================================================

-- Agent interactions history
CREATE TABLE IF NOT EXISTS agent_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT NOT NULL,
    user_input TEXT NOT NULL,
    agent_response TEXT NOT NULL,
    agent_name TEXT NOT NULL DEFAULT 'torq_prince_flowers',
    interaction_type TEXT NOT NULL DEFAULT 'general_chat',
    success BOOLEAN DEFAULT true,
    confidence FLOAT DEFAULT 0.0,
    execution_time_ms FLOAT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- User preferences for learning
CREATE TABLE IF NOT EXISTS agent_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT DEFAULT 'default',
    preference_key TEXT NOT NULL,
    preference_value JSONB NOT NULL,
    source TEXT DEFAULT 'manual',
    confidence FLOAT DEFAULT 1.0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, preference_key)
);

-- Learned patterns from feedback
CREATE TABLE IF NOT EXISTS agent_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_type TEXT NOT NULL,
    pattern_data JSONB NOT NULL,
    occurrence_count INTEGER DEFAULT 1,
    success_rate FLOAT DEFAULT 0.0,
    last_seen_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Agent feedback for learning
CREATE TABLE IF NOT EXISTS agent_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interaction_id UUID REFERENCES agent_interactions(id) ON DELETE CASCADE,
    score FLOAT CHECK (score >= 0 AND score <= 1),
    feedback_text TEXT,
    helpful_tags TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- Multi-Agent Orchestration System
-- ============================================================================

-- Agent registry for dynamic agent discovery
CREATE TABLE IF NOT EXISTS agents_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id TEXT UNIQUE NOT NULL,
    agent_name TEXT NOT NULL,
    agent_type TEXT NOT NULL,
    capabilities TEXT[] NOT NULL,
    status TEXT DEFAULT 'active',
    config JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    version TEXT DEFAULT '1.0.0',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Orchestration workflow executions
CREATE TABLE IF NOT EXISTS workflow_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id TEXT NOT NULL,
    workflow_name TEXT NOT NULL,
    mode TEXT NOT NULL, -- sequential, parallel, pipeline, dynamic
    status TEXT DEFAULT 'pending', -- pending, running, completed, failed, cancelled
    tasks JSONB NOT NULL, -- Array of task definitions
    results JSONB DEFAULT '{}', -- Task execution results
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    error_message TEXT,
    execution_time_seconds FLOAT,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'
);

-- Agent collaboration events
CREATE TABLE IF NOT EXISTS agent_collaborations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collaboration_id TEXT NOT NULL,
    from_agent_id TEXT NOT NULL,
    to_agent_id TEXT NOT NULL,
    collaboration_type TEXT NOT NULL, -- handoff, parallel, sequential
    context_data JSONB DEFAULT '{}',
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- ============================================================================
-- Cognitive Loop System
-- ============================================================================

-- Cognitive loop execution results
CREATE TABLE IF NOT EXISTS cognitive_loop_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT NOT NULL,
    query TEXT NOT NULL,
    phase TEXT NOT NULL, -- reason, retrieve, plan, act, evaluate, learn
    phase_result JSONB NOT NULL,
    confidence FLOAT DEFAULT 0.0,
    latency_ms FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Cognitive loop telemetry
CREATE TABLE IF NOT EXISTS cognitive_loop_telemetry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT NOT NULL,
    phase TEXT NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    latency_ms FLOAT,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'
);

-- ============================================================================
-- Performance Monitoring & Telemetry
-- ============================================================================

-- API performance metrics
CREATE TABLE IF NOT EXISTS api_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    status_code INTEGER,
    response_time_ms FLOAT,
    user_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agent performance metrics
CREATE TABLE IF NOT EXISTS agent_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value FLOAT NOT NULL,
    metric_unit TEXT DEFAULT 'count',
    recorded_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- ============================================================================
-- Indexes for performance
-- ============================================================================

-- Agent interactions indexes
CREATE INDEX IF NOT EXISTS idx_agent_interactions_session ON agent_interactions(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_interactions_agent ON agent_interactions(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_interactions_created ON agent_interactions(created_at DESC);

-- Preferences indexes
CREATE INDEX IF NOT EXISTS idx_agent_preferences_user ON agent_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_preferences_key ON agent_preferences(preference_key);

-- Patterns indexes
CREATE INDEX IF NOT EXISTS idx_agent_patterns_type ON agent_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_agent_patterns_success ON agent_patterns(success_rate DESC);

-- Workflow executions indexes
CREATE INDEX IF NOT EXISTS idx_workflow_executions_id ON workflow_executions(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_status ON workflow_executions(status);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_created ON workflow_executions(created_at DESC);

-- Cognitive loop indexes
CREATE INDEX IF NOT EXISTS idx_cognitive_results_session ON cognitive_loop_results(session_id);
CREATE INDEX IF NOT EXISTS idx_cognitive_results_phase ON cognitive_loop_results(phase);
CREATE INDEX IF NOT EXISTS idx_cognitive_telemetry_session ON cognitive_loop_telemetry(session_id);

-- Metrics indexes
CREATE INDEX IF NOT EXISTS idx_api_metrics_endpoint ON api_metrics(endpoint);
CREATE INDEX IF NOT EXISTS idx_api_metrics_created ON api_metrics(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_metrics_agent ON agent_metrics(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_metrics_name ON agent_metrics(metric_name);

-- ============================================================================
-- RLS Policies (Simplified - adjust for production security)
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE agent_interactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_patterns ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE agents_registry ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_collaborations ENABLE ROW LEVEL SECURITY;
ALTER TABLE cognitive_loop_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE cognitive_loop_telemetry ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_metrics ENABLE ROW LEVEL SECURITY;

-- Grant service role full access (for Railway backend)
CREATE POLICY "Service role full access on agent_interactions" ON agent_interactions
    FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Service role full access on agent_preferences" ON agent_preferences
    FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Service role full access on agent_patterns" ON agent_patterns
    FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Service role full access on agent_feedback" ON agent_feedback
    FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Service role full access on agents_registry" ON agents_registry
    FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Service role full access on workflow_executions" ON workflow_executions
    FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Service role full access on agent_collaborations" ON agent_collaborations
    FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Service role full access on cognitive_loop_results" ON cognitive_loop_results
    FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Service role full access on cognitive_loop_telemetry" ON cognitive_loop_telemetry
    FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Service role full access on api_metrics" ON api_metrics
    FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Service role full access on agent_metrics" ON agent_metrics
    FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');

-- ============================================================================
-- Seed Default Agents in Registry
-- ============================================================================

INSERT INTO agents_registry (agent_id, agent_name, agent_type, capabilities, status, metadata) VALUES
    ('conversational_agent', 'Conversational Agent', 'core', ARRAY['conversation', 'memory_management', 'learning'], 'active', '{"description": "Multi-turn conversation with context"}'),
    ('workflow_agent', 'Workflow Agent', 'core', ARRAY['code_generation', 'debugging', 'documentation', 'testing', 'architecture'], 'active', '{"description": "Workflow execution for coding tasks"}'),
    ('research_agent', 'Research Agent', 'core', ARRAY['research', 'web_search', 'data_analysis'], 'active', '{"description": "Research and information gathering"}'),
    ('orchestration_agent', 'Orchestration Agent', 'core', ARRAY['orchestration', 'workflow_automation', 'learning'], 'active', '{"description": "Coordinates multi-agent workflows"}'),
    ('torq_prince_flowers', 'TORQ Prince Flowers', 'enhanced', ARRAY['conversation', 'web_search', 'file_ops', 'reasoning'], 'active', '{"description": "Enhanced TORQ agent with full capabilities"}')
ON CONFLICT (agent_id) DO NOTHING;

-- ============================================================================
-- Grant public/anon access for specific read operations (adjust as needed)
-- ============================================================================

-- Allow anonymous read access to agents registry (for agent discovery)
CREATE POLICY "Public read agents registry" ON agents_registry
    FOR SELECT USING (auth.role() = 'anon');

-- ============================================================================
-- Functions for automatic timestamp updates
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
DROP TRIGGER IF EXISTS update_agent_interactions_updated_at ON agent_interactions;
CREATE TRIGGER update_agent_interactions_updated_at
    BEFORE UPDATE ON agent_interactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_agent_preferences_updated_at ON agent_preferences;
CREATE TRIGGER update_agent_preferences_updated_at
    BEFORE UPDATE ON agent_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_agents_registry_updated_at ON agents_registry;
CREATE TRIGGER update_agents_registry_updated_at
    BEFORE UPDATE ON agents_registry
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Verification Query
-- ============================================================================

-- Run this to verify all tables were created successfully
SELECT
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name AND table_schema = 'public') as column_count
FROM information_schema.tables t
WHERE table_schema = 'public'
    AND table_name IN (
        'thoughts',
        'agent_interactions',
        'agent_preferences',
        'agent_patterns',
        'agent_feedback',
        'agents_registry',
        'workflow_executions',
        'agent_collaborations',
        'cognitive_loop_results',
        'cognitive_loop_telemetry',
        'api_metrics',
        'agent_metrics'
    )
ORDER BY table_name;
