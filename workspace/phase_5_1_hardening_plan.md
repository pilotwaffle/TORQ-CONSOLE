# Phase 5.1 Hardening Plan

**Status**: Guarded/Beta - Core Flow Proven, Hardening Required
**Date**: 2026-03-07
**Validation Artifact**: `mission_1_final_report_20260307_234754.json`

---

## Executive Summary

Mission 1 end-to-end validation **passed**. All 6 nodes completed, mission closed with score 0.88, and full event/handoff trails were captured.

However, the validation revealed **duplication and consistency issues** that must be addressed before Phase 5.1 can be marked "production-ready."

**Current Classification**: Guarded/Beta with proven core flow

---

## What's Proven ✅

| Component | Evidence | Status |
|-----------|----------|--------|
| Mission Graph Planning | 6 nodes created with 5 edges | ✅ Operational |
| Node Execution Lifecycle | All nodes completed with outputs | ✅ Operational |
| Dependency Enforcement | Nodes unblocked in correct order | ✅ Operational |
| Event Persistence | 52 events captured | ✅ Operational |
| Handoff Generation | 14 handoffs created | ✅ Operational |
| Workstream Progression | Phases: initializing → analysis → synthesis → finalizing | ✅ Operational |
| Mission Completion | Status: completed, score: 0.88 | ✅ Operational |

---

## What Needs Hardening ⚠️

### Issue 1: Event Duplication (CRITICAL)

**Severity**: High
**Evidence**: 33 duplicate events out of 52 total (63% duplication rate)

| Node | Expected Events | Actual Events | Duplicates |
|------|----------------|---------------|------------|
| Market Entry Report | 3 (ready, started, completed) | 11 | 8 |
| Evidence Synthesis | 3 | 11 | 8 |
| Financial Projections | 3 | 8 | 5 |
| Competitor Analysis | 3 | 4 | 1 |
| Mission | 1 (completed) | 12 | 11 |

**Root Cause Hypotheses** (in priority order):

1. **Missing idempotency guards** in scheduler - Node execution may be triggered multiple times without checking if already running/completed
2. **Retry logic re-emitting** - If failures occur and nodes are re-executed, lifecycle events are emitted again without deduplication
3. **Multiple execution paths** - `complete_mission_1.py` and `finish_remaining_nodes.py` may have both executed some nodes

**Fix Strategy**:
```python
# Add to scheduler / node executor
def execute_node_if_not_already(node_id):
    # Check current state
    node = get_node(node_id)
    if node.status in ['running', 'completed']:
        logger.info(f"Node {node_id} already {node.status}, skipping")
        return None

    # Mark as running atomically
    updated = mark_node_running(node_id)
    if not updated:
        return None  # Another process claimed it

    # Execute...
```

---

### Issue 2: Handoff Inconsistency (MEDIUM)

**Severity**: Medium
**Evidence**: Mixed RICH and MINIMAL handoffs for same nodes

| Node | Rich Handoffs | Minimal Handoffs | Issue |
|------|---------------|------------------|-------|
| Market Entry Report | 2 | 2 | Duplicates of both types |
| Evidence Synthesis | 2 | 1 | Extra minimal |
| Financial Projections | 2 | 1 | Extra minimal |
| Competitor Analysis | 2 | 0 | Rich only |
| Market Size Research | 1 | 0 | Rich only |

**Root Cause**: Two different code paths creating handoffs:
1. `complete_mission_1.py` - Creates RICH agent handoffs
2. `finish_remaining_nodes.py` - Creates MINIMAL system handoffs

**Fix Strategy**:
```python
# Standardize on one handoff format per node completion
HANDOFF_TEMPLATE = {
    "objective_completed": str,
    "output_summary": str,
    "key_findings": List[str],
    "recommendations": List[str],
    "artifacts": Dict,
    "confidence": float,
    "unresolved_questions": List[str],
    "assumptions_made": List[str],
}

# Always use this, never {"done": "..."} only
```

---

### Issue 3: Mission Completion Idempotency (MEDIUM)

**Severity**: Medium
**Evidence**: `mission.completed` event fired twice

**Expected**: Mission should complete exactly once
**Actual**: 2 completion events

**Fix Strategy**:
```python
def complete_mission(mission_id):
    mission = get_mission(mission_id)
    if mission.status == 'completed':
        logger.info(f"Mission {mission_id} already completed")
        return

    # Atomic update with status check
    updated = update_mission_status(
        mission_id,
        to='completed',
        from=['running', 'in_progress']
    )

    if updated:
        emit_event('mission.completed', ...)
```

---

## Hardening Tasks (Priority Order)

### Priority 1: Fix Duplicate Execution Behavior
- [ ] Add idempotency guard to node execution
- [ ] Check node status before marking as running
- [ ] Add database constraints or unique indexes for event deduplication
- [ ] Review retry logic for event re-emission

**Success Criteria**: Running Mission 1 again produces exactly 19 events (no duplicates)

### Priority 2: Normalize Handoff Generation
- [ ] Define canonical handoff schema
- [ ] Consolidate handoff creation into single function
- [ ] Remove `finish_remaining_nodes.py` minimal handoff path
- [ ] Add handoff validation (reject non-compliant handoffs)

**Success Criteria**: All handoffs are RICH format, count equals nodes completed

### Priority 3: Mission Completion Idempotency
- [ ] Add status check before mission completion
- [ ] Use conditional database update (only if not already completed)
- [ ] Add unit test for double-completion attempt

**Success Criteria**: Mission completes exactly once regardless of how many times completion is triggered

---

## Validation Plan After Fixes

### Mission 2 Design
Create a new mission with different characteristics to test fixes:

```python
Mission 2: Technical Decision with Gate

Nodes:
1. Objective: "Evaluate Database Migration Strategy"
2. Task: "Analyze Current Schema"
3. Decision: "Choose: Replatform vs Rewrite" [DECISION GATE]
4. Task A (if Replatform): "Plan Migration Steps"
5. Task B (if Rewrite): "Design New Schema"
6. Deliverable: "Migration Plan Document"

Edges:
- Objective → Task 1
- Task 1 → Decision
- Decision → Task A (condition: choice == 'replatform')
- Decision → Task B (condition: choice == 'rewrite')
- Task A → Deliverable
- Task B → Deliverable
```

**Why This Mission**:
- Tests decision gate execution (conditional edges)
- Heavy sequential dependency (no parallel branches)
- Different from Mission 1's linear flow

### Success Criteria for Mission 2
- [ ] All 6 nodes complete exactly once
- [ ] Event count = N nodes × 3 (ready, started, completed) + 1 mission event
- [ ] Exactly 6 handoffs, all RICH format
- [ ] Mission completes exactly once
- [ ] Decision gate correctly routes to one branch only

---

## GitHub Refresh Readiness Checklist

**Do NOT refresh until**:
- [ ] Mission 2 runs clean (zero duplicate events)
- [ ] All handoffs use consistent format
- [ ] Idempotency guards proven in production
- [ ] Documentation updated with hardening findings

**Then classify Phase 5.1 as**:
- From: "Guarded/Beta with proven core flow"
- To: "Production Ready with proven execution fabric"

---

## Files to Modify

| File | Change |
|------|--------|
| `torq_console/mission_graph/scheduler.py` | Add idempotency guards |
| `torq_console/mission_graph/executor.py` | Consolidate handoff creation |
| `scripts/finish_remaining_nodes.py` | Remove or consolidate |
| `scripts/complete_mission_1.py` | Add to shared executor library |

---

## Open Questions

1. Should event deduplication happen at:
   - Application level (check before emit)?
   - Database level (unique constraint on event signature)?
   - Both?

2. Should handoffs be:
   - Exactly 1 per node completion?
   - Or 1 rich + multiple lightweight system events?

3. Should Mission 2 test:
   - Just the fixes from this hardening?
   - Or also include new features (decision gates, retries)?

---

## Timeline Estimate

| Task | Estimate |
|------|----------|
| Priority 1: Idempotency guards | 2-3 hours |
| Priority 2: Handoff normalization | 1-2 hours |
| Priority 3: Mission completion | 1 hour |
| Mission 2 creation & execution | 1 hour |
| Documentation & validation | 1 hour |
| **Total** | **6-8 hours** |
