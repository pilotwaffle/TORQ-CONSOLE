# ✅ Validation Environment — READY

**Date:** 2026-03-07 23:10
**Status:** Local PostgreSQL running, migrations applied, ready for Mission 1

---

## Environment Status

| Component | Status | Details |
|-----------|--------|---------|
| Docker | ✅ Running | torq_validation_db container active |
| PostgreSQL | ✅ Ready | localhost:5433, accepting connections |
| Database | ✅ Created | torq_validation |
| Schema | ✅ Applied | 14 tables created |
| Validation Checks | ✅ Initialized | 194 checks ready |
| Baseline | ✅ Captured | All tables at 0 rows |

---

## Database Tables

```
missions               ✓ (0 rows)
mission_graphs         ✓ (0 rows)
mission_nodes          ✓ (0 rows)
mission_edges          ✓ (0 rows)
mission_events         ✓ (0 rows)
mission_handoffs       ✓ (0 rows)
workstream_states      ✓ (0 rows)
validation_telemetry   ✓ (0 rows)
validation_results     ✓ (194 rows - check registry)
workspaces             ✓ (supporting table)
workspace_syntheses    ✓ (supporting table)
working_memory_entries ✓ (supporting table)
```

---

## Connection Details

**Primary Database:**
```
Host: localhost
Port: 5433
Database: torq_validation
User: postgres
Password: postgres
```

**Connection String:**
```
postgresql://postgres:postgres@localhost:5433/torq_validation
```

**pgAdmin:**
```
URL: http://localhost:5050
Email: admin@torq.local
Password: admin
```

---

## Next Steps: Day 1-2 Execution

### Step 1: Configure Environment

```bash
# Set DATABASE_URL for validation session
export DATABASE_URL="postgresql://postgres:postgres@localhost:5433/torq_validation"

# Or update .env.validation and source it
```

### Step 2: Start Backend Server

```bash
cd E:\TORQ-CONSOLE
python -m torq_console.cli server
```

### Step 3: Create Mission 1

```bash
curl -X POST http://localhost:8000/api/missions/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Market Entry Analysis",
    "mission_type": "analysis",
    "objective": "Assess market opportunity for electric delivery vehicles in Southeast US",
    "context": {
      "target_market": "commercial delivery fleets",
      "region": "Southeast US",
      "time_horizon": "5 years"
    }
  }'
```

### Step 4: Start Mission Execution

```bash
# Replace {mission_id} with returned UUID
curl -X POST http://localhost:8000/api/missions/{mission_id}/start
```

### Step 5: Monitor and Capture Telemetry

```bash
# Monitor status
curl http://localhost:8000/api/missions/{mission_id}/status

# Get ready nodes
curl http://localhost:8000/api/missions/{mission_id}/nodes/ready

# Check events
curl http://localhost:8000/api/missions/{mission_id}/events
```

---

## Validation Check Registry

| Section | Checks | Status |
|---------|--------|--------|
| A - End-to-End Execution | 17 | Ready |
| B - Scheduler & Dependencies | 14 | Ready |
| C - Context Bus & Events | 19 | Ready |
| D - Structured Handoffs | 18 | Ready |
| E - Workstream State | 13 | Ready |
| F - Replanning Engine | 15 | Ready |
| G - Checkpoint & Recovery | 16 | Ready |
| H - Integration Integrity | 15 | Ready |
| I - Observability | 12 | Ready |
| J - Performance & Stability | 11 | Ready |
| K - Maturity Classification | 6 | Ready |
| N - Output Quality | 9 | Ready |
| O - Telemetry Capture | 13 | Ready |
| P - Memory Sanity | 13 | Ready |
| **TOTAL** | **194** | **All Ready** |

---

## Quick SQL Queries

### Check Mission Status
```sql
SELECT id, title, status, created_at
FROM missions
ORDER BY created_at DESC;
```

### Check Node Status
```sql
SELECT mn.node_type, mn.status, COUNT(*)
FROM mission_nodes mn
WHERE mn.mission_id = '{mission_id}'
GROUP BY mn.node_type, mn.status;
```

### Check Events by Type
```sql
SELECT event_type, COUNT(*)
FROM mission_events
WHERE mission_id = '{mission_id}'
GROUP BY event_type
ORDER BY COUNT(*) DESC;
```

### Check Handoffs
```sql
SELECT id, from_node_id, confidence, status
FROM mission_handoffs
WHERE mission_id = '{mission_id}'
ORDER BY created_at;
```

### Check Workstreams
```sql
SELECT workstream_id, phase, health, status, progress_percent
FROM workstream_states
WHERE mission_id = '{mission_id}'
ORDER BY created_at;
```

---

## Failure Pattern Detection

After each mission, run:

```sql
-- Pattern 1: Dependency Leakage
SELECT COUNT(*) as dependency_leakage
FROM mission_nodes mn
JOIN mission_edges me ON me.to_node_id = mn.id
LEFT JOIN mission_nodes dep ON dep.id = me.from_node_id
WHERE mn.status = 'running'
  AND me.edge_type = 'depends_on'
  AND (dep.status IS NULL OR dep.status NOT IN ('completed', 'skipped'));

-- Pattern 2: Event Duplication
SELECT COUNT(*) as duplicate_events
FROM (
    SELECT node_id, event_type, COUNT(*) as cnt
    FROM mission_events
    WHERE mission_id = '{mission_id}'
    GROUP BY node_id, event_type
    HAVING COUNT(*) > 1
) dup
WHERE event_type NOT IN ('artifact.produced', 'evidence.added');

-- Pattern 3: Handoff Incompleteness
SELECT COUNT(*) as incomplete_handoffs
FROM mission_handoffs
WHERE mission_id = '{mission_id}'
  AND (confidence IS NULL OR handoff_summary = '{}'::jsonb);
```

**Expected Results:** All queries should return 0

---

## Documentation

- `scripts/VALIDATION_QUICK_REFERENCE.md` — Command reference
- `docs/5_FAILURE_PATTERNS.md` — Common issues and detection
- `docs/phase_5_1_validation_log.md` — Progress tracking
- `PHASE_5_1_VALIDATION_CHECKLIST.md` — Full checklist

---

## Environment Management

### Stop Validation Database
```bash
docker-compose -f docker/docker-compose.validation.yml down
```

### Reset Validation Database
```bash
docker exec -i torq_validation_db psql -U postgres -d torq_validation << 'SQL'
TRUNCATE mission_handoffs CASCADE;
TRUNCATE workstream_states CASCADE;
TRUNCATE mission_events CASCADE;
TRUNCATE mission_edges CASCADE;
TRUNCATE mission_nodes CASCADE;
TRUNCATE mission_graphs CASCADE;
TRUNCATE missions CASCADE;
TRUNCATE validation_telemetry CASCADE;
SQL
```

### View Logs
```bash
docker logs torq_validation_db --tail 50 -f
```

---

**✅ READY TO BEGIN VALIDATION EXECUTION**
