# Phase 5.1 Validation — Quick Reference

## Day 1-2 Commands

### 1. Environment Setup

```bash
# Navigate to project
cd E:\TORQ-CONSOLE

# Activate environment (if needed)
# conda activate torq || source venv/bin/activate

# Check database connection
python -c "from torq_console.dependencies import get_supabase_client; print('OK')"
```

### 2. Reset Validation Database

```bash
# Using psql (preferred)
psql -h localhost -U postgres -d torq_console -f scripts/prepare_validation_env.sql

# Or using the Python script
python scripts/run_validation.py reset
```

### 3. Start Backend Server

```bash
# Terminal 1: Start backend
cd E:\TORQ-CONSOLE
python -m torq_console.cli server

# Server will be available at http://localhost:8000
```

### 4. Create Mission 1

```bash
# Using curl
curl -X POST http://localhost:8000/api/missions/ \
  -H "Content-Type: application/json" \
  -d @scripts/mission_1_request.json

# Or using Python
python scripts/run_validation.py create \
  --title "Market Entry Analysis" \
  --type "analysis" \
  --objective "Assess market opportunity for electric delivery vehicles in Southeast US" \
  --context '{"target_market": "commercial delivery fleets", "region": "Southeast US"}'
```

### 5. Start Mission Execution

```bash
# Replace {mission_id} with actual UUID from creation response
curl -X POST http://localhost:8000/api/missions/{mission_id}/start
```

### 6. Monitor Mission Status

```bash
# Get overall status
curl http://localhost:8000/api/missions/{mission_id}/status

# Get ready nodes
curl http://localhost:8000/api/missions/{mission_id}/nodes/ready

# Get node states
curl http://localhost:8000/api/missions/{mission_id}/nodes

# Get events
curl http://localhost:8000/api/missions/{mission_id}/events
```

### 7. Using Python Validation Helper

```bash
# Get mission status
python scripts/run_validation.py status --mission-id {uuid}

# Capture telemetry
python scripts/run_validation.py telemetry --mission-id {uuid} --section A

# Record check result
python scripts/run_validation.py check \
  --section A \
  --number A1.1 \
  --name "Mission record created" \
  --status passed \
  --notes "Mission created successfully with ID {uuid}"

# Get validation summary
python scripts/run_validation.py summary
```

## SQL Queries for Manual Verification

### Verify Mission Creation (Section A1)

```sql
-- Check mission
SELECT * FROM missions WHERE title = 'Market Entry Analysis';

-- Check graph
SELECT COUNT(*) FROM mission_nodes WHERE mission_id = '{uuid}';
SELECT COUNT(*) FROM mission_edges WHERE mission_id = '{uuid}';

-- Verify node types
SELECT node_type, COUNT(*)
FROM mission_nodes
WHERE mission_id = '{uuid}'
GROUP BY node_type;
```

### Verify Dependency Enforcement (Section B1)

```sql
-- Check for running nodes with pending dependencies
SELECT mn.id, mn.status, mn.node_type
FROM mission_nodes mn
WHERE mn.mission_id = '{uuid}'
  AND mn.status = 'running'
  AND EXISTS (
    SELECT 1 FROM mission_edges me
    WHERE me.to_node_id = mn.id
      AND me.edge_type = 'depends_on'
      AND NOT EXISTS (
        SELECT 1 FROM mission_nodes from_node
        WHERE from_node.id = me.from_node_id
          AND from_node.status IN ('completed', 'skipped')
      )
  );

-- Should return 0 rows if dependencies are enforced correctly
```

### Verify Context Bus Events (Section C)

```sql
-- Count events by type
SELECT event_type, COUNT(*)
FROM mission_events
WHERE mission_id = '{uuid}'
GROUP BY event_type
ORDER BY COUNT(*) DESC;

-- Expected event types:
-- - node.started
-- - node.completed
-- - artifact.produced
-- - evidence.added
-- - decision.required
```

### Verify Handoffs (Section D)

```sql
-- Check handoff completeness
SELECT
    id,
    from_node_id,
    confidence,
    array_length(unresolved_questions, 1) as question_count,
    array_length(risks, 1) as risk_count,
    jsonb_array_length(artifacts) as artifact_count
FROM mission_handoffs
WHERE mission_id = '{uuid}';

-- Each handoff should have:
-- - confidence score (0-1)
-- - 0+ unresolved questions
-- - 0+ risks
-- - 0+ artifacts
```

### Verify Workstream States (Section E)

```sql
-- Check workstream progression
SELECT
    workstream_id,
    phase,
    health,
    status,
    progress_percent,
    completed_nodes,
    total_nodes
FROM workstream_states
WHERE mission_id = '{uuid}'
ORDER BY created_at;
```

## Common Failure Signals

### 1. Dependency Leakage

**Symptom:** Node starts before dependencies complete

**Detection:**
```sql
-- Running nodes with incomplete dependencies
SELECT mn.id, mn.status
FROM mission_nodes mn
JOIN mission_edges me ON me.to_node_id = mn.id
WHERE mn.status = 'running'
  AND me.edge_type = 'depends_on'
  AND EXISTS (
    SELECT 1 FROM mission_nodes dep
    WHERE dep.id = me.from_node_id
      AND dep.status NOT IN ('completed', 'skipped')
  );
```

**Fix:** Check scheduler edge evaluation logic in `mission_graph/scheduler.py`

### 2. Event Duplication

**Symptom:** Same event appears multiple times

**Detection:**
```sql
-- Check for duplicate events
SELECT event_type, node_id, COUNT(*)
FROM mission_events
WHERE mission_id = '{uuid}'
GROUP BY event_type, node_id
HAVING COUNT(*) > 1;
```

**Fix:** Check event emitter lifecycle hooks in `mission_graph/context_bus.py`

### 3. Handoff Incompleteness

**Symptom:** Handoffs missing required fields

**Detection:**
```sql
-- Find incomplete handoffs
SELECT id, from_node_id
FROM mission_handoffs
WHERE mission_id = '{uuid}'
  AND (
    confidence IS NULL
    OR handoff_summary IS NULL
    OR jsonb_pretty(handoff_summary) = '{}'
  );
```

**Fix:** Check handoff schema enforcement in `mission_graph/handoffs.py`

## Expected Ranges

| Metric | Min | Max | Typical |
|--------|-----|-----|---------|
| nodes per mission | 5 | 15 | 8-10 |
| events per mission | 20 | 100 | 40-60 |
| handoffs per mission | 5 | 20 | 8-12 |
| checkpoints per mission | 3 | 10 | 5-7 |
| workstreams per mission | 2 | 4 | 3 |
| execution time (sec) | 60 | 300 | 120-180 |

## Validation Checklist Progress

Track progress by updating `docs/phase_5_1_validation_log.md`:

```markdown
## Day 1 Progress

- [x] Environment setup
- [x] Database reset
- [x] Mission 1 created
- [x] Mission 1 started
- [ ] Mission 1 completed
- [ ] Section A checks passed
- [ ] Section B checks passed
```

## Getting Help

If validation fails:

1. **Check logs:** `tail -f logs/torq_console.log`
2. **Verify schema:** Run `SELECT version FROM schema_migrations ORDER BY version;`
3. **Query directly:** Use SQL queries above to inspect state
4. **Document findings:** Update `docs/phase_5_1_validation_log.md`

---

**Files Created for Validation:**
- `migrations/020_validation_telemetry.sql` — Telemetry schema
- `scripts/prepare_validation_env.sql` — Database reset script
- `scripts/run_validation.py` — Python validation helper
- `scripts/test_missions.json` — Test mission definitions
- `docs/phase_5_1_validation_log.md` — Validation log template
- `scripts/VALIDATION_QUICK_REFERENCE.md` — This file
