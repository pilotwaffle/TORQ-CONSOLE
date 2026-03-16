# Layer 17 Migration Status and Execution Guide

**Date:** 2026-03-15
**Migration ID:** 017_layer17_agent_genome_evolution
**Status:** PENDING MANUAL APPLICATION

---

## Summary

The Layer 17 migration creates three new tables in Supabase for storing:
1. **agent_genomes** - Evolved agent genomes with toolsets and performance metrics
2. **l16_ecosystem_signals** - Signals collected from Layer 16 economic coordination
3. **benchmark_evaluations** - Benchmark evaluation results for genomes

---

## Current Status

### Tables Created
- `agent_genomes`: NOT FOUND
- `l16_ecosystem_signals`: NOT FOUND
- `benchmark_evaluations`: NOT FOUND

### Verification
Run the verification script:
```bash
python experiment_results/execute_layer17_migration.py
```

---

## How to Apply the Migration

Since Supabase REST API does NOT support DDL statements (CREATE TABLE), you must apply the migration using one of these methods:

### Method 1: Supabase Dashboard (Recommended - Easiest)

1. Open your Supabase project SQL Editor:
   ```
   https://supabase.com/dashboard/project/npukynbaglmcdvzyklqa/sql/new
   ```

2. Copy the SQL from:
   ```
   E:\TORQ-CONSOLE\migrations\017_layer17_agent_genome_evolution.sql
   ```

3. Paste into the SQL Editor and click "Run"

4. Verify the tables were created by checking the Table Editor

### Method 2: psql Command Line

If you have your database password:

```bash
psql -h db.npukynbaglmcdvzyklqa.supabase.co -U postgres -d postgres -f E:\TORQ-CONSOLE\migrations\017_layer17_agent_genome_evolution.sql
```

### Method 3: Using Python Script (Requires DB Password)

1. Add your database password to `.env`:
   ```
   SUPABASE_DB_PASSWORD=your_actual_password
   ```

2. Run:
   ```bash
   python experiment_results/execute_layer17_migration.py
   ```

---

## Migration SQL Details

The migration creates:

### Table: agent_genomes
- Stores evolved agent genomes
- Fields: genome_id, parent_genome_id, generation, status, toolset, llm_model, fitness scores, benchmark results
- Indexes: status, generation, fitness_score, benchmark_passed, created_at
- Triggers: Auto-updates updated_at timestamp

### Table: l16_ecosystem_signals
- Stores L16 economic coordination signals
- Fields: signal_id, collected_at, market_health, resource_supply/demand, equilibrium prices
- Indexes: collected_at, market_health, evolved_genome_id

### Table: benchmark_evaluations
- Stores benchmark evaluation results
- Fields: evaluation_id, genome_id, scores (completion, latency, consistency), passed
- Indexes: genome_id, passed, overall_score, evaluated_at

### Views
- `production_genomes` - Production-ready genomes meeting criteria
- `recent_l16_signals` - L16 signals from last 7 days

---

## After Migration is Applied

Once the migration is successfully applied:

1. Verify tables exist:
   ```bash
   python experiment_results/execute_layer17_migration.py
   ```

2. Run Cycle 001 with database persistence:
   ```bash
   python experiment_results/run_layer17_cycle_with_db.py
   ```

3. Check the results in the experiment report:
   ```bash
   cat experiment_results/layer17_cycle_001.md
   ```

---

## Expected Row IDs After Cycle 001

When Cycle 001 runs successfully, you should see:

| Table | Expected Rows | IDs |
|-------|---------------|-----|
| agent_genomes | 2 | genome_founder_001, genome_[child_id] |
| l16_ecosystem_signals | 1 | signal_[id] |
| benchmark_evaluations | 1 | [uuid] |

---

## Troubleshooting

### Error: "Could not find the table 'public.agent_genomes'"
**Cause:** Migration not applied
**Fix:** Apply migration using Method 1, 2, or 3 above

### Error: "Permission denied"
**Cause:** Using anon key instead of service role key
**Fix:** Ensure `SUPABASE_SERVICE_ROLE_KEY` is set in `.env`

### Error: "Connection refused"
**Cause:** Database not accessible
**Fix:** Check Supabase project is active and database is paused/unpaused

---

## Next Steps

1. Apply the migration (see methods above)
2. Run verification: `python experiment_results/execute_layer17_migration.py`
3. Run Cycle 001: `python experiment_results/run_layer17_cycle_with_db.py`
4. Review results: `cat experiment_results/layer17_cycle_001.md`

---

**Migration File:** `E:\TORQ-CONSOLE\migrations\017_layer17_agent_genome_evolution.sql`
**Project Ref:** npukynbaglmcdvzyklqa
**Supabase URL:** https://npukynbaglmcdvzyklqa.supabase.co
