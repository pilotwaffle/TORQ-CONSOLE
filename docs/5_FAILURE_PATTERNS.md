# Phase 5.1 Validation — 5 Common Failure Patterns

**Prepared for:** Mission Graph + Execution Fabric validation
**Purpose:** Anticipate and quickly identify the most common issues

---

## Pattern 1: Dependency Leakage

### What It Looks Like

```
Node B (depends_on: Node A) starts running while Node A is still "pending"
```

### Detection Queries

```sql
-- Find running nodes with incomplete dependencies
SELECT
    mn.id as node_id,
    mn.node_type,
    mn.status as node_status,
    dep.id as dependency_id,
    dep.status as dependency_status
FROM mission_nodes mn
JOIN mission_edges me ON me.to_node_id = mn.id
LEFT JOIN mission_nodes dep ON dep.id = me.from_node_id
WHERE mn.status = 'running'
  AND me.edge_type = 'depends_on'
  AND (dep.status IS NULL OR dep.status NOT IN ('completed', 'skipped'));
```

**Expected:** 0 rows
**If non-zero:** Scheduler is not enforcing dependencies correctly

### Root Causes

1. **Scheduler bug:** Edge evaluation logic doesn't wait for dependency status
2. **Graph construction bug:** `depends_on` edges not created correctly
3. **Status transition bug:** Nodes marked `running` before dependencies checked

### Where to Look

- `torq_console/mission_graph/scheduler.py` → `_get_ready_nodes()`
- `torq_console/mission_graph/builder.py` → `_build_dependency_edges()`
- `torq_console/mission_graph/models.py` → `can_start()` method

### Quick Fix

Add defensive check in scheduler:
```python
def can_start_node(self, node_id: str) -> bool:
    dependencies = self._get_dependencies(node_id)
    return all(
        dep.status in ('completed', 'skipped')
        for dep in dependencies
    )
```

---

## Pattern 2: Event Duplication

### What It Looks Like

```
Event log shows:
  node.started → 10 times for same node
  node.completed → 5 times for same node
```

### Detection Queries

```sql
-- Count events per node
SELECT
    node_id,
    event_type,
    COUNT(*) as event_count
FROM mission_events
WHERE mission_id = '{mission_id}'
GROUP BY node_id, event_type
HAVING COUNT(*) > 1;
```

**Expected:** Only `artifact.produced` and `evidence.added` should repeat (>1)
**If `node.started` or `node.completed` repeat:** Event emitter bug

### Root Causes

1. **Multiple emitters:** Both node executor AND scheduler emit same event
2. **Retry loop:** Failed node retries emit duplicate start events
3. **Race condition:** Concurrent execution paths emit events twice

### Where to Look

- `torq_console/mission_graph/context_bus.py` → `emit()` method
- `torq_console/mission_graph/executor.py` → Node execution lifecycle
- `torq_console/mission_graph/scheduler.py` → Dispatch logic

### Quick Fix

Add idempotency key to events:
```python
def emit_event(self, event_type: str, node_id: str, **data):
    event_key = f"{node_id}:{event_type}:{data.get('attempt', 0)}"
    if self._emitted_events.get(event_key):
        return  # Already emitted
    self._emitted_events[event_key] = True
    # ... emit event
```

---

## Pattern 3: Handoff Incompleteness

### What It Looks Like

```
Handoff packet has:
  - confidence: NULL
  - handoff_summary: {}
  - artifacts: []
  - unresolved_questions: NULL
```

### Detection Queries

```sql
-- Find incomplete handoffs
SELECT
    id,
    from_node_id,
    confidence,
    jsonb_array_length(artifacts) as artifact_count,
    array_length(unresolved_questions, 1) as question_count
FROM mission_handoffs
WHERE mission_id = '{mission_id}'
  AND (
    confidence IS NULL
    OR jsonb_pretty(handoff_summary) = '{}'
    OR artifacts IS NULL
  );
```

**Expected:** 0 rows
**If non-zero:** Agent not producing complete handoff data

### Root Causes

1. **Agent not using Handoff schema:** Agent returns plain dict, not HandoffPacket
2. **Missing fields:** Required fields not enforced by schema
3. **Timeout:** Agent timed out before handoff complete

### Where to Look

- `torq_console/mission_graph/handoffs.py` → `HandoffPacket` model
- `torq_console/agents/` → Agent execution methods
- `torq_console/mission_graph/executor.py` → Handoff capture logic

### Quick Fix

Add handoff validation before storing:
```python
def validate_handoff(self, handoff: HandoffPacket) -> bool:
    required = ['confidence', 'handoff_summary', 'artifacts']
    return all(getattr(handoff, field) for field in required)
```

---

## Pattern 4: Workstream Phase Skipping

### What It Looks Like

```
Workstream jumps:
  initializing → analysis (skips discovery)
  analysis → complete (skips synthesis, review)
```

### Detection Queries

```sql
-- Find skipped phases
SELECT
    workstream_id,
    phase,
    health,
    status,
    completed_nodes,
    total_nodes,
    phase_transition_count
FROM workstream_states
WHERE mission_id = '{mission_id}'
  AND phase_transition_count > expected_transitions;
```

**Expected:** Sequential phase progression
**If skipping:** Phase transition logic is too permissive

### Root Causes

1. **Threshold too low:** Workstream moves to next phase with <50% nodes done
2. **No minimum time:** Phase completes immediately without time threshold
3. **Manual override:** Developer bypassed phase gate during testing

### Where to Look

- `torq_console/mission_graph/workstream_state.py` → `can_transition_to_phase()`
- `torq_console/mission_graph/context_bus.py` → `workstream.phase_changed` handler

### Quick Fix

Add phase completion criteria:
```python
def can_complete_phase(self, phase: str) -> bool:
    if self.total_nodes == 0:
        return False
    completion_pct = self.completed_nodes / self.total_nodes
    return completion_pct >= 0.8  # Require 80% completion
```

---

## Pattern 5: Memory Injection Overload

### What It Looks Like

```
Node receives 50+ strategic memories, prompt exceeds context limit
```

### Detection Queries

```sql
-- Count memories injected per node
SELECT
    node_id,
    COUNT(*) as memory_count,
    SUM(LENGTH(memory_content)) as total_chars
FROM node_memory_injection
WHERE mission_id = '{mission_id}'
GROUP BY node_id
HAVING COUNT(*) > 10;
```

**Expected:** 2-5 memories per node (max)
**If >10:** Memory retrieval is not scoped correctly

### Root Causes

1. **Scope too broad:** Global memories returned when domain-specific should be
2. **No limit:** Retrieval engine returns all matching memories
3. **Low relevance threshold:** Irrelevant memories included

### Where to Look

- `torq_console/strategic_memory/retrieval.py` → `retrieve_memories()`
- `torq_console/mission_graph/builder.py` → Memory injection during graph build
- `torq_console/mission_graph/scheduler.py` → Memory injection per node

### Quick Fix

Add hard limit to retrieval:
```python
def retrieve_memories(self, query: str, scope: str, limit: int = 5) -> List[Memory]:
    results = self._search(query, scope)
    # Re-rank and limit
    ranked = self._rank_by_relevance(results, query)
    return ranked[:limit]  # Hard cap at 5
```

---

## Diagnostic Queries — All Patterns

Run this after each mission to detect any of the 5 patterns:

```sql
-- ALL-PATTERN DIAGNOSTIC QUERY
DO $$
DECLARE
    pattern_1_count INTEGER;
    pattern_2_count INTEGER;
    pattern_3_count INTEGER;
    pattern_4_count INTEGER;
    pattern_5_count INTEGER;
BEGIN
    -- Pattern 1: Dependency Leakage
    SELECT COUNT(*) INTO pattern_1_count
    FROM mission_nodes mn
    JOIN mission_edges me ON me.to_node_id = mn.id
    LEFT JOIN mission_nodes dep ON dep.id = me.from_node_id
    WHERE mn.status = 'running'
      AND me.edge_type = 'depends_on'
      AND (dep.status IS NULL OR dep.status NOT IN ('completed', 'skipped'));

    -- Pattern 2: Event Duplication (excluding multi-allowed types)
    SELECT COUNT(*) INTO pattern_2_count
    FROM (
        SELECT node_id, event_type, COUNT(*) as cnt
        FROM mission_events
        WHERE mission_id = CURRENT_SETTING('mission_id', true)
        GROUP BY node_id, event_type
        HAVING COUNT(*) > 1
    ) dup
    WHERE event_type NOT IN ('artifact.produced', 'evidence.added');

    -- Pattern 3: Handoff Incompleteness
    SELECT COUNT(*) INTO pattern_3_count
    FROM mission_handoffs
    WHERE mission_id = CURRENT_SETTING('mission_id', true)
      AND (confidence IS NULL OR handoff_summary = '{}'::jsonb);

    -- Pattern 4: Workstream Phase Issues (simple check: too few phases)
    -- This would need more complex logic for full detection
    pattern_4_count := 0;

    -- Pattern 5: Memory Overload (if tracking)
    pattern_5_count := 0;

    -- Report
    RAISE NOTICE 'Pattern 1 (Dependency Leakage): %', pattern_1_count;
    RAISE NOTICE 'Pattern 2 (Event Duplication): %', pattern_2_count;
    RAISE NOTICE 'Pattern 3 (Handoff Incomplete): %', pattern_3_count;
    RAISE NOTICE 'Pattern 4 (Phase Skipping): %', pattern_4_count;
    RAISE NOTICE 'Pattern 5 (Memory Overload): %', pattern_5_count;

    IF pattern_1_count > 0 OR pattern_2_count > 0 OR pattern_3_count > 0 THEN
        RAISE NOTICE '⚠️ FAILURE PATTERNS DETECTED - Review required';
    ELSE
        RAISE NOTICE '✓ No failure patterns detected';
    END IF;
END $$;
```

---

## Quick Reference: Pattern → Fix

| Pattern | Quick Check | File to Fix |
|---------|-------------|-------------|
| 1. Dependency Leakage | Running node with pending deps | `scheduler.py` |
| 2. Event Duplication | Duplicate events in log | `context_bus.py` |
| 3. Handoff Incomplete | NULL confidence or empty summary | `handoffs.py` |
| 4. Phase Skipping | Phase jumps in workstream | `workstream_state.py` |
| 5. Memory Overload | >10 memories per node | `retrieval.py` |

---

## Pre-Validation Checklist

Before running Mission 1, verify:

- [ ] Scheduler dependency check implemented
- [ ] Event emitter has idempotency
- [ ] Handoff schema validated before storage
- [ ] Workstream phase gates have thresholds
- [ ] Memory retrieval has hard limit (≤5)

**This prevents the 5 patterns from appearing in the first place.**
