# Layer 17 Migration Execution Summary

**Date:** 2026-03-15
**Agent Task:** Execute Layer 17 migration and re-run Cycle 001 with database persistence
**Status:** MIGRATION PENDING MANUAL APPLICATION

---

## Executive Summary

The Layer 17 migration creates the database schema for Agent Genome Evolution. The migration SQL has been prepared and validated, but requires manual application to Supabase since the REST API does not support DDL statements.

---

## Migration Status

| Component | Status | Notes |
|-----------|--------|-------|
| Migration SQL File | READY | `E:\TORQ-CONSOLE\migrations\017_layer17_agent_genome_evolution.sql` |
| Table: agent_genomes | NOT CREATED | Requires manual application |
| Table: l16_ecosystem_signals | NOT CREATED | Requires manual application |
| Table: benchmark_evaluations | NOT CREATED | Requires manual application |
| Cycle Execution Script | READY | `experiment_results/run_layer17_cycle_with_db.py` |

---

## How to Apply the Migration

### Method 1: Supabase Dashboard SQL Editor (Recommended)

1. Navigate to:
   ```
   https://supabase.com/dashboard/project/npukynbaglmcdvzyklqa/sql/new
   ```

2. Copy the SQL from:
   ```
   E:\TORQ-CONSOLE\migrations\017_layer17_agent_genome_evolution.sql
   ```

3. Paste into SQL Editor and click "Run"

4. Verify tables created in Table Editor

### Method 2: With Database Password

1. Get database password from:
   ```
   https://supabase.com/dashboard/project/npukynbaglmcdvzyklqa/settings/database
   ```

2. Add to `.env`:
   ```
   SUPABASE_DB_PASSWORD=your_password_here
   ```

3. Run migration script:
   ```bash
   python experiment_results/apply_layer17_migration_rest.py
   ```

### Method 3: Using psql

```bash
psql -h db.npukynbaglmcdvzyklqa.supabase.co -U postgres -d postgres \
     -f E:\TORQ-CONSOLE\migrations\017_layer17_agent_genome_evolution.sql
```

---

## Migration Details

### Table: agent_genomes
Stores evolved agent genomes with toolsets and performance metrics.

| Column | Type | Description |
|--------|------|-------------|
| genome_id | TEXT (PK) | Unique genome identifier |
| parent_genome_id | TEXT (FK) | Parent genome for lineage tracking |
| generation | INTEGER | Evolution generation number |
| status | TEXT | experimental, production, or retired |
| toolset | JSONB | Array of tool names |
| llm_model | TEXT | LLM model used |
| llm_temperature | NUMERIC | LLM temperature setting |
| fitness_score | NUMERIC | Composite fitness (0.0-1.0) |
| benchmark_passed | BOOLEAN | Whether benchmarks passed |
| created_at | TIMESTAMPTZ | Creation timestamp |
| updated_at | TIMESTAMPTZ | Last update timestamp |

### Table: l16_ecosystem_signals
Stores signals from Layer 16 Economic Coordination System.

| Column | Type | Description |
|--------|------|-------------|
| signal_id | TEXT (PK) | Unique signal identifier |
| collected_at | TIMESTAMPTZ | When signal was collected |
| total_agents | INTEGER | Total agents in market |
| active_agents | INTEGER | Active agents |
| market_health | NUMERIC | Market health score (0.0-1.0) |
| resource_supply | JSONB | Supply per resource type |
| resource_demand | JSONB | Demand per resource type |
| allocation_success_rate | NUMERIC | Mission allocation success rate |
| market_stable | BOOLEAN | Whether market is stable |
| evolved_genome_id | TEXT (FK) | Genome using this signal |

### Table: benchmark_evaluations
Stores benchmark evaluation results for genomes.

| Column | Type | Description |
|--------|------|-------------|
| evaluation_id | UUID (PK) | Unique evaluation identifier |
| genome_id | TEXT (FK) | Genome being evaluated |
| benchmark_count | INTEGER | Number of benchmarks run |
| completion_score | NUMERIC | Completion score (0.0-1.0) |
| latency_score | NUMERIC | Latency score (0.0-1.0) |
| consistency_score | NUMERIC | Consistency score (0.0-1.0) |
| overall_score | NUMERIC | Overall score (0.0-1.0) |
| passed | BOOLEAN | Whether evaluation passed |
| evaluated_at | TIMESTAMPTZ | When evaluation occurred |

---

## After Migration: Run Cycle 001

Once migration is applied, run:

```bash
python experiment_results/run_layer17_cycle_with_db.py
```

### Expected Output

When Cycle 001 runs successfully, you should see:

```
======================================================================
CYCLE 001 COMPLETE WITH DATABASE PERSISTENCE
======================================================================
Result: [PROMOTE TO PRODUCTION or RETIRE]
Score: [0.0-1.0]
Report: E:\TORQ-CONSOLE\experiment_results\layer17_cycle_001.md

Database Records Created:
  - agent_genomes: 2 rows
  - l16_ecosystem_signals: 1 row
  - benchmark_evaluations: 1 row
======================================================================
```

### Expected Row IDs

| Table | Expected IDs |
|-------|--------------|
| agent_genomes | genome_founder_001, genome_[generated_child_id] |
| l16_ecosystem_signals | signal_[generated_id] |
| benchmark_evaluations | [uuid] |

---

## Script Reference

| Script | Purpose | Location |
|--------|---------|----------|
| execute_layer17_migration.py | Verify migration status | experiment_results/ |
| apply_layer17_migration_rest.py | Apply migration with DB password | experiment_results/ |
| run_layer17_cycle_with_db.py | Run Cycle 001 with persistence | experiment_results/ |
| run_layer17_cycle.py | Original cycle (in-memory) | experiment_results/ |

---

## Files Created

1. `E:\TORQ-CONSOLE\experiment_results\execute_layer17_migration.py`
   - Migration verification script
   - Checks if tables exist via REST API

2. `E:\TORQ-CONSOLE\experiment_results\apply_layer17_migration_rest.py`
   - Migration application script (requires DB password)
   - Falls back to manual instructions

3. `E:\TORQ-CONSOLE\experiment_results\run_layer17_cycle_with_db.py`
   - Updated cycle runner with Supabase persistence
   - Tracks inserted row IDs
   - Generates detailed report

4. `E:\TORQ-CONSOLE\experiment_results\MIGRATION_STATUS.md`
   - Migration status and instructions

5. `E:\TORQ-CONSOLE\experiment_results\LAYER17_MIGRATION_SUMMARY.md`
   - This document

---

## Environment Variables Required

```bash
# From .env (already configured)
SUPABASE_URL=https://npukynbaglmcdvzyklqa.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci... (service role key)
SUPABASE_ANON_KEY=eyJhbGci... (anon key)

# Optional: for direct DB connection
SUPABASE_DB_PASSWORD=your_database_password
```

---

## Troubleshooting

### Error: "Could not find the table 'public.agent_genomes'"
**Cause:** Migration not applied
**Fix:** Apply migration via Supabase Dashboard SQL Editor

### Error: "Permission denied" or 401
**Cause:** Using anon key instead of service role key
**Fix:** Ensure SUPABASE_SERVICE_ROLE_KEY is set

### Error: "Connection refused"
**Cause:** Supabase project paused
**Fix:** Resume project in Supabase Dashboard

---

## Next Steps

1. [ ] Apply Layer 17 migration via Supabase Dashboard
2. [ ] Verify tables created: `python experiment_results/execute_layer17_migration.py`
3. [ ] Run Cycle 001: `python experiment_results/run_layer17_cycle_with_db.py`
4. [ ] Check report: `cat experiment_results/layer17_cycle_001.md`
5. [ ] Verify row IDs in report

---

**Migration File:** `E:\TORQ-CONSOLE\migrations\017_layer17_agent_genome_evolution.sql`
**Project Ref:** npukynbaglmcdvzyklqa
**Dashboard:** https://supabase.com/dashboard/project/npukynbaglmcdvzyklqa
