-- TORQ Layer 17 - Agent Genomes Table
-- Migration: layer17_agent_genomes
-- Version: 0.17.0
-- Date: 2026-03-15

-- Enable UUID extension if not available
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create agent_genomes table
CREATE TABLE IF NOT EXISTS agent_genomes (
    -- Primary Key
    genome_id TEXT PRIMARY KEY,

    -- Lineage
    parent_genome_id TEXT,
    generation INTEGER NOT NULL DEFAULT 0,

    -- Status
    status TEXT NOT NULL DEFAULT 'experimental' CHECK (status IN ('experimental', 'production', 'retired')),

    -- Toolset (evolvable)
    toolset JSONB NOT NULL DEFAULT '[]',
    min_toolset_size INTEGER NOT NULL DEFAULT 3 CHECK (min_toolset_size >= 1),
    max_toolset_size INTEGER NOT NULL DEFAULT 15 CHECK (max_toolset_size >= 1),

    -- LLM Configuration
    llm_model TEXT NOT NULL DEFAULT 'claude-sonnet-4-6',
    llm_temperature REAL NOT NULL DEFAULT 0.7 CHECK (llm_temperature >= 0.0 AND llm_temperature <= 1.0),
    llm_max_tokens INTEGER NOT NULL DEFAULT 4096 CHECK (llm_max_tokens >= 1),

    -- Performance Metrics
    missions_completed INTEGER NOT NULL DEFAULT 0 CHECK (missions_completed >= 0),
    missions_attempted INTEGER NOT NULL DEFAULT 0 CHECK (missions_attempted >= 0),
    total_value_generated REAL NOT NULL DEFAULT 0.0 CHECK (total_value_generated >= 0),
    total_cost_incurred REAL NOT NULL DEFAULT 0.0 CHECK (total_cost_incurred >= 0),

    -- Fitness Scores
    fitness_score REAL CHECK (fitness_score IS NULL OR (fitness_score >= 0.0 AND fitness_score <= 1.0)),
    completion_rate REAL NOT NULL DEFAULT 0.0 CHECK (completion_rate >= 0.0 AND completion_rate <= 1.0),
    efficiency_score REAL NOT NULL DEFAULT 0.0 CHECK (efficiency_score >= 0.0 AND efficiency_score <= 1.0),
    reliability_score REAL NOT NULL DEFAULT 0.5 CHECK (reliability_score >= 0.0 AND reliability_score <= 1.0),

    -- Benchmark Results
    benchmark_completion_score REAL CHECK (benchmark_completion_score IS NULL OR (benchmark_completion_score >= 0.0 AND benchmark_completion_score <= 1.0)),
    benchmark_latency_score REAL CHECK (benchmark_latency_score IS NULL OR (benchmark_latency_score >= 0.0 AND benchmark_latency_score <= 1.0)),
    benchmark_consistency_score REAL CHECK (benchmark_consistency_score IS NULL OR (benchmark_consistency_score >= 0.0 AND benchmark_consistency_score <= 1.0)),
    benchmark_overall_score REAL CHECK (benchmark_overall_score IS NULL OR (benchmark_overall_score >= 0.0 AND benchmark_overall_score <= 1.0)),
    benchmark_passed BOOLEAN NOT NULL DEFAULT FALSE,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    retired_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT genome_id_valid CHECK (genome_id ~ '^genome_[a-z0-9]{12,}$')
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_agent_genomes_status ON agent_genomes(status);
CREATE INDEX IF NOT EXISTS idx_agent_genomes_generation ON agent_genomes(generation);
CREATE INDEX IF NOT EXISTS idx_agent_genomes_fitness ON agent_genomes(fitness_score) WHERE fitness_score IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_agent_genomes_created_at ON agent_genomes(created_at DESC);

-- Create index for parent genome lookups
CREATE INDEX IF NOT EXISTS idx_agent_genomes_parent ON agent_genomes(parent_genome_id) WHERE parent_genome_id IS NOT NULL;

-- Add RLS (Row Level Security) - disabled by default for now
ALTER TABLE agent_genomes ENABLE ROW LEVEL SECURITY;

-- Policy: Service users have full access
CREATE POLICY "service_full_access" ON agent_genomes
    FOR ALL
    USING (true);

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON agent_genomes TO service_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO service_role;

-- Add comments
COMMENT ON TABLE agent_genomes IS 'TORQ Layer 17: Agent genomes for genetic evolution';
COMMENT ON COLUMN agent_genomes.genome_id IS 'Unique identifier for this genome';
COMMENT ON COLUMN agent_genomes.parent_genome_id IS 'Parent genome if this was created by mutation';
COMMENT ON COLUMN agent_genomes.generation IS 'How many generations from founder (0 = founder)';
COMMENT ON COLUMN agent_genomes.status IS 'experimental, production, or retired';
COMMENT ON COLUMN agent_genomes.toolset IS 'JSON array of available tool names';
COMMENT ON COLUMN agent_genomes.fitness_score IS 'Overall ecosystem fitness (0-1)';
COMMENT ON COLUMN agent_genomes.benchmark_passed IS 'Whether genome passed benchmark threshold';
