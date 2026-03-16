-- Migration: Layer 17 - Agent Genome Evolution Tables
-- Purpose: Store agent genomes, L16 ecosystem signals, and benchmark results
-- Date: 2026-03-15
-- Phase: Layer 17 Implementation
-- Depends On: Layer 16 (Multi-Agent Economic Coordination)

-- =============================================================================
-- AGENT GENOMES TABLE
-- -----------------------------------------------------------------------------

-- Stores evolved agent genomes with toolsets and performance metrics
CREATE TABLE IF NOT EXISTS agent_genomes (
    -- Primary identity
    genome_id TEXT PRIMARY KEY,
    parent_genome_id TEXT,
    generation INTEGER NOT NULL DEFAULT 0,

    -- Status
    status TEXT NOT NULL DEFAULT 'experimental' CHECK (status IN ('experimental', 'production', 'retired')),

    -- Toolset (evolvable)
    toolset JSONB NOT NULL DEFAULT '[]'::jsonb,
    min_toolset_size INTEGER NOT NULL DEFAULT 3,
    max_toolset_size INTEGER NOT NULL DEFAULT 15,

    -- LLM Configuration
    llm_model TEXT NOT NULL DEFAULT 'claude-sonnet-4-6',
    llm_temperature NUMERIC(3,2) NOT NULL DEFAULT 0.7 CHECK (llm_temperature >= 0.0 AND llm_temperature <= 1.0),
    llm_max_tokens INTEGER NOT NULL DEFAULT 4096,

    -- Performance Metrics (from L16 ecosystem interaction)
    missions_completed INTEGER NOT NULL DEFAULT 0,
    missions_attempted INTEGER NOT NULL DEFAULT 0,
    total_value_generated NUMERIC(15,2) NOT NULL DEFAULT 0.0,
    total_cost_incurred NUMERIC(15,2) NOT NULL DEFAULT 0.0,

    -- Fitness Scores
    fitness_score NUMERIC(3,2) CHECK (fitness_score >= 0.0 AND fitness_score <= 1.0),
    completion_rate NUMERIC(3,2) NOT NULL DEFAULT 0.0 CHECK (completion_rate >= 0.0 AND completion_rate <= 1.0),
    efficiency_score NUMERIC(3,2) NOT NULL DEFAULT 0.0 CHECK (efficiency_score >= 0.0 AND efficiency_score <= 1.0),
    reliability_score NUMERIC(3,2) NOT NULL DEFAULT 0.5 CHECK (reliability_score >= 0.0 AND reliability_score <= 1.0),

    -- Benchmark Results
    benchmark_completion_score NUMERIC(3,2) CHECK (benchmark_completion_score >= 0.0 AND benchmark_completion_score <= 1.0),
    benchmark_latency_score NUMERIC(3,2) CHECK (benchmark_latency_score >= 0.0 AND benchmark_latency_score <= 1.0),
    benchmark_consistency_score NUMERIC(3,2) CHECK (benchmark_consistency_score >= 0.0 AND benchmark_consistency_score <= 1.0),
    benchmark_overall_score NUMERIC(3,2) CHECK (benchmark_overall_score >= 0.0 AND benchmark_overall_score <= 1.0),
    benchmark_passed BOOLEAN NOT NULL DEFAULT FALSE,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    retired_at TIMESTAMPTZ,

    -- Foreign key to parent genome
    CONSTRAINT fk_parent_genome FOREIGN KEY (parent_genome_id) REFERENCES agent_genomes(genome_id) ON DELETE SET NULL
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_agent_genomes_status ON agent_genomes(status);
CREATE INDEX IF NOT EXISTS idx_agent_genomes_generation ON agent_genomes(generation);
CREATE INDEX IF NOT EXISTS idx_agent_genomes_fitness ON agent_genomes(fitness_score DESC) WHERE fitness_score IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_agent_genomes_benchmark_passed ON agent_genomes(benchmark_passed);
CREATE INDEX IF NOT EXISTS idx_agent_genomes_created_at ON agent_genomes(created_at DESC);

-- Comments
COMMENT ON TABLE agent_genomes IS 'Evolved agent genomes with toolsets, performance metrics, and benchmark results';
COMMENT ON COLUMN agent_genomes.toolset IS 'Array of tool names available to this agent';
COMMENT ON COLUMN agent_genomes.fitness_score IS 'Composite fitness score from ecosystem interaction';
COMMENT ON COLUMN agent_genomes.benchmark_passed IS 'Whether genome passed benchmark threshold';

-- =============================================================================
-- L16 ECOSYSTEM SIGNALS TABLE
-- -----------------------------------------------------------------------------

-- Stores signals collected from Layer 16 economic coordination system
CREATE TABLE IF NOT EXISTS l16_ecosystem_signals (
    -- Primary identity
    signal_id TEXT PRIMARY KEY,
    collected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Market State (verified from L16 AgentMarketState)
    total_agents INTEGER NOT NULL DEFAULT 0,
    active_agents INTEGER NOT NULL DEFAULT 0,
    market_health NUMERIC(3,2) NOT NULL DEFAULT 0.8 CHECK (market_health >= 0.0 AND market_health <= 1.0),

    -- Resource Supply/Demand (verified from L16)
    resource_supply JSONB NOT NULL DEFAULT '{}'::jsonb,
    resource_demand JSONB NOT NULL DEFAULT '{}'::jsonb,
    supply_demand_gap NUMERIC(15,2) NOT NULL DEFAULT 0.0,

    -- Mission Allocation Data (verified from L16 CoordinationResult)
    total_missions_processed INTEGER NOT NULL DEFAULT 0,
    total_missions_allocated INTEGER NOT NULL DEFAULT 0,
    allocation_success_rate NUMERIC(3,2) NOT NULL DEFAULT 0.0 CHECK (allocation_success_rate >= 0.0 AND allocation_success_rate <= 1.0),

    -- Recent Winning Allocations (verified from L16)
    recent_allocations JSONB NOT NULL DEFAULT '[]'::jsonb,

    -- Price Information (verified from L16 ResourcePrice)
    equilibrium_prices JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- Equilibrium State (verified from L16 MarketEquilibrium)
    market_stable BOOLEAN NOT NULL DEFAULT FALSE,
    equilibrium_confidence NUMERIC(3,2) NOT NULL DEFAULT 0.5 CHECK (equilibrium_confidence >= 0.0 AND equilibrium_confidence <= 1.0),

    -- Incentive Data (verified from L16)
    active_adjustments INTEGER NOT NULL DEFAULT 0,

    -- Optional: Link to genome that used this signal for evolution
    evolved_genome_id TEXT,

    CONSTRAINT fk_evolved_genome FOREIGN KEY (evolved_genome_id) REFERENCES agent_genomes(genome_id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_l16_signals_collected_at ON l16_ecosystem_signals(collected_at DESC);
CREATE INDEX IF NOT EXISTS idx_l16_signals_market_health ON l16_ecosystem_signals(market_health);
CREATE INDEX IF NOT EXISTS idx_l16_signals_evolved_genome ON l16_ecosystem_signals(evolved_genome_id);

-- Comments
COMMENT ON TABLE l16_ecosystem_signals IS 'Signals collected from Layer 16 economic coordination system';
COMMENT ON COLUMN l16_ecosystem_signals.resource_supply IS 'Supply per resource type (cpu, memory, etc.)';
COMMENT ON COLUMN l16_ecosystem_signals.equilibrium_prices IS 'Market equilibrium prices per resource';

-- =============================================================================
-- BENCHMARK EVALUATIONS TABLE
-- -----------------------------------------------------------------------------

-- Stores benchmark evaluation results for genomes
CREATE TABLE IF NOT EXISTS benchmark_evaluations (
    -- Primary identity
    evaluation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    genome_id TEXT NOT NULL,

    -- Evaluation metadata
    benchmark_count INTEGER NOT NULL DEFAULT 0,
    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    evaluation_duration_ms NUMERIC(10,2) NOT NULL DEFAULT 0.0,

    -- Individual Scores
    completion_score NUMERIC(3,2) NOT NULL DEFAULT 0.0 CHECK (completion_score >= 0.0 AND completion_score <= 1.0),
    latency_score NUMERIC(3,2) NOT NULL DEFAULT 0.0 CHECK (latency_score >= 0.0 AND latency_score <= 1.0),
    consistency_score NUMERIC(3,2) NOT NULL DEFAULT 0.0 CHECK (consistency_score >= 0.0 AND consistency_score <= 1.0),

    -- Overall
    overall_score NUMERIC(3,2) NOT NULL DEFAULT 0.0 CHECK (overall_score >= 0.0 AND overall_score <= 1.0),
    passed BOOLEAN NOT NULL DEFAULT FALSE,

    -- Per-Benchmark Details
    benchmark_details JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- Foreign key to genome
    CONSTRAINT fk_benchmark_genome FOREIGN KEY (genome_id) REFERENCES agent_genomes(genome_id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_benchmark_evaluations_genome_id ON benchmark_evaluations(genome_id);
CREATE INDEX IF NOT EXISTS idx_benchmark_evaluations_passed ON benchmark_evaluations(passed);
CREATE INDEX IF NOT EXISTS idx_benchmark_evaluations_overall_score ON benchmark_evaluations(overall_score DESC);
CREATE INDEX IF NOT EXISTS idx_benchmark_evaluations_evaluated_at ON benchmark_evaluations(evaluated_at DESC);

-- Comments
COMMENT ON TABLE benchmark_evaluations IS 'Benchmark evaluation results for agent genomes';
COMMENT ON COLUMN benchmark_evaluations.benchmark_details IS 'Individual benchmark results with scores and durations';

-- =============================================================================
-- TRIGGER: UPDATE UPDATED_AT
-- -----------------------------------------------------------------------------

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_agent_genomes_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update updated_at
CREATE TRIGGER trigger_update_agent_genomes_updated_at
    BEFORE UPDATE ON agent_genomes
    FOR EACH ROW
    EXECUTE FUNCTION update_agent_genomes_updated_at();

-- =============================================================================
-- VIEWS
-- -----------------------------------------------------------------------------

-- View: Production-ready genomes
CREATE OR REPLACE VIEW production_genomes AS
SELECT
    genome_id,
    generation,
    toolset,
    llm_model,
    fitness_score,
    completion_rate,
    benchmark_overall_score,
    created_at
FROM agent_genomes
WHERE status = 'production'
  AND benchmark_passed = TRUE
  AND completion_rate >= 0.8
ORDER BY fitness_score DESC;

COMMENT ON VIEW production_genomes IS 'Genomes that meet production readiness criteria';

-- View: Recent L16 signals
CREATE OR REPLACE VIEW recent_l16_signals AS
SELECT
    signal_id,
    collected_at,
    total_agents,
    market_health,
    allocation_success_rate,
    equilibrium_confidence,
    market_stable
FROM l16_ecosystem_signals
WHERE collected_at > NOW() - INTERVAL '7 days'
ORDER BY collected_at DESC;

COMMENT ON VIEW recent_l16_signals IS 'L16 ecosystem signals from the last 7 days';

-- =============================================================================
-- MIGRATION COMPLETE
-- =============================================================================

-- This migration creates the foundation for Layer 17 (Agent Genome Evolution)
-- to integrate with Layer 16 (Multi-Agent Economic Coordination).
--
-- Next: Import verified model fields from VERIFIED_L16_MODELS.md
