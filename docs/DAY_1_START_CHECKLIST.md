# Phase 5.1 Validation — Day 1 Start Checklist

**Date:** 2026-03-07
**Status:** Infrastructure Complete, Awaiting Migration Setup

---

## ✅ Completed Infrastructure (Ready)

| Item | Status | File/Location |
|------|--------|---------------|
| Validation Checklist (194 checks) | ✅ Complete | `PHASE_5_1_VALIDATION_CHECKLIST.md` |
| Architecture Documentation | ✅ Complete | `ARCHITECTURE_INDEX.md` |
| Architecture Diagram | ✅ Complete | `docs/ARCHITECTURE_DIAGRAM.md` |
| GitHub Audit | ✅ Complete | `GITHUB_SYNC_AUDIT.md` |
| GitHub Sync Summary | ✅ Complete | `GITHUB_SYNC_SUMMARY.md` |
| README v0.9.0-beta | ✅ Complete | `README.md` |
| .gitignore updated | ✅ Complete | `.gitignore` |
| Validation Log Template | ✅ Complete | `docs/phase_5_1_validation_log.md` |
| Migration 020 (telemetry) | ✅ Created | `migrations/020_validation_telemetry.sql` |
| Environment Reset Script | ✅ Created | `scripts/prepare_validation_env.sql` |
| Validation Helper Script | ✅ Created | `scripts/run_validation.py` |
| Test Mission Definitions | ✅ Created | `scripts/test_missions.json` |
| Migration Setup Script | ✅ Created | `scripts/apply_all_migrations.sh` |
| Quick Reference Guide | ✅ Created | `scripts/VALIDATION_QUICK_REFERENCE.md` |
| Migration Setup Guide | ✅ Created | `docs/MIGRATION_SETUP_GUIDE.md` |

---

## 🔴 Blocking Issue: Database Migrations Not Applied

**Current State:** Remote Supabase database lacks Phase 5.1 tables.

**Tables Missing:**
```
- missions
- mission_nodes
- mission_edges
- mission_events
- mission_handoffs
- workstream_states
- validation_telemetry
- validation_results
```

---

## 📋 Step-by-Step: Starting Validation

### Step 1: Choose Database Environment

**Option A: Local PostgreSQL (Recommended for initial validation)**
- Fast, safe, isolated
- No production risk
- Easy to reset

**Option B: Remote Supabase (For final validation)**
- Production-like environment
- Use after local validation passes

### Step 2: Apply Migrations

**For local PostgreSQL:**
```bash
# Install PostgreSQL if needed
# Windows: https://www.postgresql.org/download/

# Create database
psql -U postgres -c "CREATE DATABASE torq_console;"

# Set connection string
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/torq_console"

# Apply migrations
bash scripts/apply_all_migrations.sh
```

**For remote Supabase:**
```bash
# Get connection string from Supabase dashboard
# Project Settings > Database > Connection String (URI format)

# Set connection string
export DATABASE_URL="postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres"

# Apply migrations
bash scripts/apply_all_migrations.sh
```

### Step 3: Verify Migration Success

```bash
# Check migration table
psql $DATABASE_URL -c "SELECT version FROM schema_migrations ORDER BY version;"

# Expected output includes:
# 001
# 002
# ...
# 018_mission_graphs
# 019_execution_fabric
# 020_validation_telemetry

# Verify tables exist
psql $DATABASE_URL -c "
SELECT table_name
FROM information_schema.tables
WHERE table_name IN ('missions', 'mission_nodes', 'mission_edges',
                    'mission_events', 'mission_handoffs', 'workstream_states',
                    'validation_telemetry', 'validation_results')
ORDER BY table_name;
"
```

### Step 4: Prepare Validation Environment

```bash
# Reset validation tables
psql $DATABASE_URL -f scripts/prepare_validation_env.sql

# Or use Python
python scripts/run_validation.py reset
```

### Step 5: Start Backend Server

```bash
# Terminal 1
cd E:\TORQ-CONSOLE
python -m torq_console.cli server

# Server starts at http://localhost:8000
```

### Step 6: Create Mission 1

```bash
# Using Python helper
python scripts/run_validation.py create \
  --title "Market Entry Analysis" \
  --type "analysis" \
  --objective "Assess market opportunity for electric delivery vehicles in Southeast US" \
  --context '{"target_market": "commercial delivery fleets", "region": "Southeast US"}'

# Save the returned mission_id
```

### Step 7: Start Mission Execution

```bash
# Using curl
curl -X POST http://localhost:8000/api/missions/{mission_id}/start

# Monitor status
curl http://localhost:8000/api/missions/{mission_id}/status
```

---

## 🎯 Day 1-2 Success Criteria

By end of Day 2, you should have:

- [ ] All migrations applied (004-020)
- [ ] Database reset and clean baseline captured
- [ ] Mission 1 created successfully
- [ ] Mission 1 started
- [ ] Mission 1 completed
- [ ] Section A checks (17) verified
- [ ] Section B checks (14) verified
- [ ] Telemetry captured for Mission 1
- [ ] Baseline metrics recorded

---

## 📊 Expected Telemetry Ranges (Mission 1)

| Metric | Min | Max | Target |
|--------|-----|-----|--------|
| node_count | 5 | 15 | 8-10 |
| execution_time_seconds | 60 | 300 | 120-180 |
| handoff_count | 5 | 20 | 8-12 |
| event_count | 20 | 100 | 40-60 |
| checkpoint_count | 3 | 10 | 5-7 |
| workstream_count | 2 | 4 | 3 |
| evaluation_score | 0.6 | 1.0 | >0.75 |

---

## 🚨 Common Issues and Fixes

### Issue: "table not found"
**Cause:** Migrations not applied
**Fix:** Run `bash scripts/apply_all_migrations.sh`

### Issue: "connection refused"
**Cause:** Database not running or wrong connection string
**Fix:** Verify `DATABASE_URL` and database is running

### Issue: Mission stuck in "draft" status
**Cause:** Graph not generated or scheduler not started
**Fix:** Check logs for `MissionGraphBuilder` errors

### Issue: Nodes not executing
**Cause:** Dependencies not satisfied or executor not configured
**Fix:** Verify graph edges and node dependencies

---

## 📝 Daily Progress Template

**Day 1 - Date:** ___________

- [ ] Migrations applied
- [ ] Environment reset
- [ ] Mission 1 created
- [ ] Mission 1 started
- [ ] Section A1 checks passed (5)
- [ ] Section A2 checks passed (4)

**Notes:**
_______________
_______________

**Day 2 - Date:** ___________

- [ ] Mission 1 completed
- [ ] Section A3 checks passed (8)
- [ ] Section B1 checks passed (4)
- [ ] Section B2 checks passed (4)
- [ ] Section B3 checks passed (6)
- [ ] Telemetry captured

**Notes:**
_______________
_______________

---

## ✅ Ready to Proceed

Once migrations are applied, you can immediately begin validation execution.

**Files to reference during execution:**
- `scripts/VALIDATION_QUICK_REFERENCE.md` — Command reference
- `PHASE_5_1_VALIDATION_CHECKLIST.md` — Full checklist
- `docs/phase_5_1_validation_log.md` — Progress tracking

**Good luck with validation!**
