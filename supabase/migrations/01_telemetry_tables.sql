-- ============================================
-- TORQ Console: Telemetry & Tracing System
-- Migration 1: Telemetry Tables
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- 1. TELEMETRY TRACES
-- Stores trace metadata (group of related spans)
-- ============================================
CREATE TABLE IF NOT EXISTS telemetry_traces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trace_id TEXT NOT NULL UNIQUE,
    session_id TEXT,

    -- Trace metadata
    agent_name TEXT,
    agent_type TEXT,
    workflow_type TEXT,

    -- Timing
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,

    -- Metrics
    total_spans INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    total_cost_usd DECIMAL(10,4) DEFAULT 0,

    -- Status
    status TEXT DEFAULT 'running', -- running, completed, error, cancelled

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_traces_session ON telemetry_traces(session_id);
CREATE INDEX IF NOT EXISTS idx_traces_agent ON telemetry_traces(agent_name);
CREATE INDEX IF NOT EXISTS idx_traces_started ON telemetry_traces(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_traces_status ON telemetry_traces(status);

-- ============================================
-- 2. TELEMETRY SPANS
-- Stores individual spans within traces
-- ============================================
CREATE TABLE IF NOT EXISTS telemetry_spans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    span_id TEXT NOT NULL UNIQUE,
    trace_id TEXT NOT NULL,

    -- References
    parent_span_id TEXT,
    trace_uuid UUID REFERENCES telemetry_traces(id) ON DELETE CASCADE,

    -- Span identification
    span_name TEXT NOT NULL,
    span_type TEXT, -- tool, agent, workflow, etc.

    -- Timing for TTFT calculation
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,

    -- TTFT specific (Time To First Token)
    ttft_ms INTEGER, -- Time to first token/response
    first_token_at TIMESTAMPTZ,

    -- Token usage
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,

    -- Cost tracking
    cost_usd DECIMAL(10,6) DEFAULT 0,

    -- Status
    status TEXT DEFAULT 'running', -- running, completed, error, cancelled
    error_message TEXT,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    input_hash TEXT, -- For deduplication

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_spans_trace ON telemetry_spans(trace_id);
CREATE INDEX IF NOT EXISTS idx_spans_trace_uuid ON telemetry_spans(trace_uuid);
CREATE INDEX IF NOT EXISTS idx_spans_parent ON telemetry_spans(parent_span_id);
CREATE INDEX IF NOT EXISTS idx_spans_type ON telemetry_spans(span_type);
CREATE INDEX IF NOT EXISTS idx_spans_started ON telemetry_spans(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_spans_status ON telemetry_spans(status);

-- ============================================
-- 3. AUTO-UPDATE TIMESTAMP TRIGGER
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to telemetry tables
DROP TRIGGER IF EXISTS update_traces_updated_at ON telemetry_traces;
CREATE TRIGGER update_traces_updated_at
    BEFORE UPDATE ON telemetry_traces
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_spans_updated_at ON telemetry_spans;
CREATE TRIGGER update_spans_updated_at
    BEFORE UPDATE ON telemetry_spans
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- ENABLE ROW LEVEL SECURITY
-- ============================================
ALTER TABLE telemetry_traces ENABLE ROW LEVEL SECURITY;
ALTER TABLE telemetry_spans ENABLE ROW LEVEL SECURITY;

-- Service role can do everything
CREATE POLICY "Service role full access traces" ON telemetry_traces
    FOR ALL TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role full access spans" ON telemetry_spans
    FOR ALL TO service_role
    USING (true)
    WITH CHECK (true);

-- Anon/key auth can read but not write
CREATE POLICY "Read access traces" ON telemetry_traces
    FOR SELECT TO anon, authenticated
    USING (true);

CREATE POLICY "Read access spans" ON telemetry_spans
    FOR SELECT TO anon, authenticated
    USING (true);

-- ============================================
-- COMMENTS
-- ============================================
COMMENT ON TABLE telemetry_traces IS 'Stores trace metadata for TORQ Console telemetry';
COMMENT ON TABLE telemetry_spans IS 'Stores individual spans with TTFT and token tracking';
COMMENT ON COLUMN telemetry_spans.ttft_ms IS 'Time To First Token - critical latency metric';
COMMENT ON COLUMN telemetry_spans.input_hash IS 'Hash of input for deduplication detection';
