# Phase 5.1 Supabase Setup Instructions

**Date:** 2026-03-07
**Status:** Ready for execution
**Mission ID:** TBD (after schema application)

---

## Current State

- ✅ Local PostgreSQL validation environment created (port 5433)
- ✅ Local Mission 1 created and Section A1 validated (6 nodes, 5 edges)
- ⏸️ Backend cannot start due to Supabase coupling
- ⚠️ **BLOCKER:** Phase 5.1 tables don't exist in Supabase

---

## The Blocker

The TORQ codebase is tightly coupled to Supabase's REST API client. When we attempt to use local PostgreSQL, the code fails because:
1. `get_supabase_client()` returns a Supabase REST API client
2. This client requires a Supabase URL (like `https://npukynbaglmcdvzyklqa.supabase.co`)
3. Cannot connect to raw PostgreSQL via connection string

---

## Resolution Path

Apply Phase 5.1 schema to Supabase, then use Supabase for validation.

### Step 1: Apply Schema to Supabase (REQUIRED)

1. Open Supabase SQL Editor:
   ```
   https://supabase.com/dashboard/project/npukynbaglmcdvzyklqa/sql
   ```

2. Copy and paste the contents of:
   ```
   E:\TORQ-CONSOLE\migrations\apply_phase_5_1_to_supabase.sql
   ```

3. Click "Run" to execute the schema creation

4. Verify tables were created:
   - missions
   - mission_graphs
   - mission_nodes
   - mission_edges
   - mission_events
   - mission_handoffs
   - workstream_states
   - validation_telemetry
   - validation_results

### Step 2: Create Validation Mission

Once schema is applied, run:
```bash
python scripts/create_validation_mission_supabase.py
```

This will create Mission 1 with:
- 6 nodes (objective → 3 tasks → evidence → deliverable)
- 5 dependency edges (linear chain)
- 6 workstream states
- Status: `planned`

### Step 3: Start Backend and Execute

```bash
# Start TORQ backend
python -m torq_console.cli serve

# In another terminal, start the mission via API
curl -X POST http://localhost:8000/api/missions/<mission_id>/start
```

---

## Validation Plan After Setup

### Section A2: Mission Start
- Verify only valid ready nodes start (node 1 has no dependencies)
- Verify blocked nodes remain blocked
- Verify mission status changes to `running`

### Section B: Scheduler Validation
- B1: Dependency enforcement during execution
- B2: Parallel execution (if applicable)
- B3: Decision gate evaluation

### Section C: Context Bus Events
- C1: Event emission on state changes
- C2: Event persistence and correlation
- C3: No event duplication

### Section D: Structured Handoffs
- D1: Handoff creation on node completion
- D2: Handoff completeness (confidence, summary, artifacts)
- D3: Handoff delivery to dependent nodes

---

## Failure Pattern Detection

After each execution step, run detection queries:
1. **Pattern 1: Dependency Leakage** - Nodes running before dependencies complete
2. **Pattern 2: Event Duplication** - Multiple identical events
3. **Pattern 3: Handoff Incompleteness** - Missing confidence/summary/artifacts
4. **Pattern 4: Workstream Phase Skipping** - Jumping phases
5. **Pattern 5: Memory Injection Overload** - Too many memories per node

See `docs/5_FAILURE_PATTERNS.md` for detection queries.

---

## Files Reference

| File | Purpose |
|------|---------|
| `migrations/apply_phase_5_1_to_supabase.sql` | Combined schema for Supabase SQL Editor |
| `scripts/create_validation_mission_supabase.py` | Create Mission 1 in Supabase |
| `scripts/apply_migrations_to_supabase.py` | Alternative: Apply via Python script |
| `docs/5_FAILURE_PATTERNS.md` | Failure patterns and detection queries |
| `docs/validation_report_day_1.md` | Day 1 local validation report |

---

## Next Steps (Once Schema Applied)

1. Run `python scripts/create_validation_mission_supabase.py`
2. Capture mission ID from output
3. Start backend: `python -m torq_console.cli serve`
4. Start mission via API
5. Capture 4 views after first execution step:
   - Mission status
   - Node states
   - Events emitted
   - Handoffs created

---

**Prepared by:** TORQ Console Validation System
**Project Reference:** Phase 5.1 Execution Fabric Validation
