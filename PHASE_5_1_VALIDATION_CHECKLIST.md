# Phase 5.1 Validation Checklist

**Validation Objective:** Confirm that TORQ can run a mission end-to-end with dependency-aware execution, shared mission coordination, structured handoffs, workstream health tracking, controlled replanning, and checkpoint recovery.

**Exit Criteria:** All required items in sections A-L must pass before GitHub/README refresh.

---

## A. End-to-End Mission Execution

### A1. Mission Creation

Validate that a mission can be created successfully from a realistic objective.

**Checks:**
- [ ] Mission record created in database
- [ ] Graph created and linked to mission
- [ ] Nodes and edges persisted correctly
- [ ] Workstreams assigned to appropriate nodes
- [ ] Graph validation passes (no orphans, no invalid cycles)

**Pass Criteria:**
- Mission initializes without manual database fixes
- Graph summary is correct and queryable

**Test Command:**
```bash
# Create a market analysis mission
POST /api/missions/
{
    "title": "Market Entry Analysis",
    "mission_type": "analysis",
    "objective": "Assess market opportunity for X in Y region",
    "context": {...}
}
```

**Status:** _____ / 5 passed

---

### A2. Mission Start

Validate mission startup flow.

**Checks:**
- [ ] Initial ready nodes identified correctly
- [ ] Scheduler dispatches only valid ready nodes
- [ ] Pending nodes remain blocked when dependencies unsatisfied
- [ ] Mission status changes from `draft` → `running`

**Pass Criteria:**
- No blocked node starts early
- At least one valid mission can start with no manual intervention

**Test Command:**
```bash
POST /api/missions/{mission_id}/start
GET /api/missions/{mission_id}/nodes/ready
```

**Status:** _____ / 4 passed

---

### A3. Full Mission Completion

Run at least 3 realistic missions through to completion.

**Recommended Mix:**
1. Analysis mission (market research)
2. Planning mission (roadmap creation)
3. Evaluation mission (risk assessment)

**Checks:**
- [ ] All intended nodes execute
- [ ] Deliverable nodes complete
- [ ] Outputs persist to workspace
- [ ] Mission final status = `completed`
- [ ] Completion summary generated

**Pass Criteria:**
- All 3 missions complete successfully
- No hidden deadlocks
- No dangling ready/running nodes at completion

**Test Missions:**
- [ ] Mission 1: Market Entry Analysis
- [ ] Mission 2: Product Roadmap Planning
- [ ] Mission 3: Technical Risk Evaluation

**Status:** _____ / 8 passed

---

## B. Scheduler and Dependency Validation

### B1. Dependency Enforcement

Create a graph with clear dependencies.

**Checks:**
- [ ] Child nodes do not run before required parents
- [ ] `depends_on` edges are enforced
- [ ] `blocks` edges stop execution until resolved
- [ ] `informs` edges do not hard-block execution

**Pass Criteria:**
- Scheduler respects edge semantics 100%

**Test Graph:**
```
A (research) ──depends_on──> B (analysis) ──depends_on──> C (synthesis)
D (parallel research) ─────────────────────────────────�─┬──> C
E (optional) ──informs──> B
```

**Status:** _____ / 4 passed

---

### B2. Parallel Execution

Create a mission with parallelizable branches.

**Checks:**
- [ ] Independent nodes become ready simultaneously
- [ ] Scheduler can dispatch multiple ready nodes
- [ ] Shared state remains coherent under parallel progress

**Pass Criteria:**
- Parallel branches execute without duplication or state corruption

**Status:** _____ / 3 passed

---

### B3. Decision Gates

Create missions with pass/fail branch logic.

**Checks:**
- [ ] Decision nodes evaluate conditions correctly
- [ ] Downstream branches activate correctly
- [ ] Invalid branches remain inactive
- [ ] Decision outcomes persisted to `decision_outcomes` table

**Pass Criteria:**
- Branch routing is deterministic and explainable

**Test Decision:**
```python
{
    "gate_type": "confidence_threshold",
    "metric": "market_confidence",
    "operator": ">=",
    "value": 0.75,
    "on_pass": "continue_to_synthesis",
    "on_fail": "spawn_validation_subgraph"
}
```

**Status:** _____ / 4 passed

---

## C. Context Bus Validation

### C1. Event Generation

Verify context bus emits mission events for key transitions.

**Minimum Events to Verify:**
- [ ] `node.started`
- [ ] `node.completed`
- [ ] `evidence.added`
- [ ] `risk.escalated`
- [ ] `decision.required`
- [ ] `workstream.blocked`
- [ ] `artifact.produced`
- [ ] `mission.replanning`

**Pass Criteria:**
- Each event is emitted once per actual occurrence
- No silent state transitions

**Test Query:**
```sql
SELECT event_type, COUNT(*)
FROM mission_events
WHERE mission_id = $1
GROUP BY event_type;
```

**Status:** _____ / 8 passed

---

### C2. Event Persistence

**Checks:**
- [ ] Events stored correctly in `mission_events` table
- [ ] Mission-scoped event history can be replayed
- [ ] Event payloads complete enough for debugging

**Pass Criteria:**
- Operator can reconstruct mission flow from persisted events

**Status:** _____ / 3 passed

---

### C3. Subscription Behavior

Test filtered subscriptions.

**Checks:**
- [ ] Subscribers receive only relevant events
- [ ] No cross-mission leakage
- [ ] Filters by event type work correctly
- [ ] Filters by mission/node work correctly

**Pass Criteria:**
- Subscription routing is correct and isolated

**Status:** _____ / 4 passed

---

## D. Structured Handoff Validation

### D1. Handoff Packet Completeness

For each important node completion, validate handoff packet structure.

**Required Fields:**
- [ ] `objective_completed`
- [ ] `output_summary`
- [ ] `confidence_level`
- [ ] `confidence_basis`
- [ ] `unresolved_questions`
- [ ] `known_risks`
- [ ] `artifacts_produced`
- [ ] `recommended_next_consumers`

**Pass Criteria:**
- Handoffs are collaboration-ready, not raw output dumps

**Status:** _____ / 8 passed

---

### D2. Handoff Delivery Tracking

**Checks:**
- [ ] Handoffs created and routed to consumers
- [ ] Acknowledgments persist
- [ ] Downstream consumers can reference upstream handoffs
- [ ] Delivery status updates correctly

**Pass Criteria:**
- Handoff lifecycle is traceable end-to-end

**Status:** _____ / 4 passed

---

### D3. Handoff Quality

Review at least 10 real handoffs manually.

**Checks:**
- [ ] No missing context
- [ ] No overly vague summaries
- [ ] No omitted risks
- [ ] Unresolved questions captured

**Pass Criteria:**
- At least 80% of handoffs are usable without rereading full upstream outputs

**Handoffs Reviewed:** _____ / 10

**Quality Score:** _____ %

**Status:** _____ / 4 passed

---

## E. Workstream State Validation

### E1. Workstream Phase Progression

Validate phase transitions.

**Phases to Test:**
- [ ] `initializing` → `discovery`
- [ ] `discovery` → `analysis`
- [ ] `analysis` → `synthesis`
- [ ] `synthesis` → `review`
- [ ] `review` → `finalizing`
- [ ] `finalizing` → `complete`
- [ ] Any phase → `blocked` (on blocker)
- [ ] `blocked` → previous phase (on resolution)

**Pass Criteria:**
- Phase progression reflects actual mission state

**Status:** _____ / 8 passed

---

### E2. Health State Updates

Validate health classification.

**Checks:**
- [ ] Blockers affect health (→ `at_risk` or `critical`)
- [ ] Repeated failures downgrade health
- [ ] Successful recovery updates state upward
- [ ] Stalled workstreams marked correctly

**Pass Criteria:**
- Workstream health matches observed execution reality

**Status:** _____ / 4 passed

---

### E3. Confidence and Completeness Metrics

**Checks:**
- [ ] Confidence updates with node outcomes
- [ ] Completeness increases as tasks finish
- [ ] Metrics do not exceed bounds (0-1)
- [ ] No irrational metric drift

**Pass Criteria:**
- Planner can trust workstream metrics for oversight

**Status:** _____ / 4 passed

---

## F. Replanning Validation

### F1. Trigger Detection

Test each implemented trigger type.

**Triggers to Test:**
- [ ] `evidence_drop` (confidence below threshold)
- [ ] `contradiction_spike` (count exceeds threshold)
- [ ] `node_failure` (too many failures)
- [ ] `blocker_unresolved` (stuck too long)
- [ ] `confidence_low` (average below threshold)

**Pass Criteria:**
- Replanning triggers are not silent and not overly noisy

**Status:** _____ / 5 passed

---

### F2. Replanning Proposal Quality

Review generated proposals.

**Checks:**
- [ ] Risk/benefit analysis exists
- [ ] Scope level appropriate
- [ ] Affected nodes/workstreams identified
- [ ] Proposal is understandable by operator

**Pass Criteria:**
- Proposals are operationally actionable

**Proposals Reviewed:** _____ / 5

**Status:** _____ / 4 passed

---

### F3. Replanning Execution

Approve and apply replans.

**Checks:**
- [ ] Graph mutates safely
- [ ] New nodes/edges valid
- [ ] Superseded paths handled correctly
- [ ] Mission continues cleanly

**Pass Criteria:**
- Replanning improves mission continuity instead of destabilizing it

**Replans Executed:** _____ / 3

**Status:** _____ / 4 passed

---

## G. Checkpoint and Recovery Validation

### G1. Checkpoint Creation

Verify all checkpoint types can be created.

**Checkpoint Types:**
- [ ] `automatic` (periodic)
- [ ] `manual` (user-initiated)
- [ ] `pre_phase` (before phase transition)
- [ ] `post_phase` (after phase completion)
- [ ] `critical` (before risky operation)
- [ ] `recovery` (during recovery)

**Pass Criteria:**
- Checkpoint snapshots are complete and queryable

**Status:** _____ / 6 passed

---

### G2. Restore Integrity

Restore checkpoints from different mission stages.

**Checks:**
- [ ] Graph state restored
- [ ] Node states restored
- [ ] Workstream states restored
- [ ] Recent handoffs restored or re-linked
- [ ] Mission can resume

**Pass Criteria:**
- Restored missions can continue without corruption

**Restores Tested:** _____ / 3

**Status:** _____ / 5 passed

---

### G3. Retention Policy

**Checks:**
- [ ] Old checkpoints expire correctly
- [ ] Max-checkpoint retention enforced (50)
- [ ] No accidental deletion of recent critical checkpoints

**Pass Criteria:**
- Retention policy works as intended

**Status:** _____ / 3 passed

---

## H. Integration with Existing TORQ Layers

### H1. Workspace Integration

**Checks:**
- [ ] Mission nodes write to workspace correctly
- [ ] Reasoning artifacts stay linked to mission context
- [ ] Node outputs attributable to mission

**Pass Criteria:**
- Workspace memory reflects mission execution accurately

**Status:** _____ / 3 passed

---

### H2. Synthesis Integration

**Checks:**
- [ ] Synthesis can operate on mission-produced workspace data
- [ ] Outputs remain coherent across workstreams

**Pass Criteria:**
- Synthesis still produces useful summaries after mission-driven execution

**Status:** _____ / 2 passed

---

### H3. Evaluation Integration

**Checks:**
- [ ] Mission-driven executions can still be evaluated
- [ ] Evaluation scores persist correctly
- [ ] Experiment pipeline works downstream

**Pass Criteria:**
- 5.1 does not break the adaptive loop

**Status:** _____ / 3 passed

---

### H4. Strategic Memory Integration

**Checks:**
- [ ] Relevant memories inject during mission planning
- [ ] Memory injection scoped correctly
- [ ] No obvious context flooding

**Pass Criteria:**
- Strategic memory assists mission execution without overwhelming it

**Status:** _____ / 3 passed

---

## I. Operational Observability

### I1. Mission Traceability

For a completed mission, verify traceability.

**Can Trace:**
- [ ] Mission → Graph
- [ ] Graph → Nodes
- [ ] Nodes → Handoffs
- [ ] Mission → Events
- [ ] Mission → Checkpoints
- [ ] Nodes → Workspace entries
- [ ] Workspace → Syntheses
- [ ] Syntheses → Evaluations

**Pass Criteria:**
- Full lineage is reconstructable

**Status:** _____ / 8 passed

---

### I2. Failure Visibility

Force controlled failures.

**Checks:**
- [ ] Failed nodes visible
- [ ] Blocked workstreams visible
- [ ] Replanning need visible
- [ ] Checkpoint recovery path visible

**Pass Criteria:**
- Operators can see and understand failures quickly

**Status:** _____ / 4 passed

---

### I3. Mission Health Summary

Validate aggregated mission health output.

**Includes:**
- [ ] Active blockers
- [ ] Risk level
- [ ] Stalled workstreams
- [ ] Incomplete deliverables
- [ ] Pending decisions

**Pass Criteria:**
- Summary is accurate enough for operator dashboard

**Test Query:**
```sql
SELECT * FROM get_mission_health_summary($mission_id);
```

**Status:** _____ / 5 passed

---

## J. Performance and Stability

### J1. Parallel Mission Stability

Run multiple missions concurrently.

**Checks:**
- [ ] No cross-mission event leakage
- [ ] No handoff contamination
- [ ] No scheduler collision
- [ ] Bus instances isolated per mission

**Pass Criteria:**
- Missions remain isolated under concurrency

**Concurrent Missions Tested:** _____ / 3

**Status:** _____ / 4 passed

---

### J2. Event Volume Sanity

Measure runtime overhead.

**Metrics:**
- [ ] Events per mission: _____ (expected: 20-100)
- [ ] Handoffs per mission: _____ (expected: 5-20)
- [ ] Checkpoints per mission: _____ (expected: 3-10)

**Pass Criteria:**
- Runtime overhead is reasonable

**Status:** _____ / 3 passed

---

### J3. Recovery Under Interruption

Interrupt a mission mid-run.

**Checks:**
- [ ] Mission does not become unrecoverable
- [ ] Checkpoint can restore
- [ ] Scheduler resumes safely

**Pass Criteria:**
- Interruption does not require manual DB surgery

**Status:** _____ / 3 passed

---

## K. Subsystem Maturity Classification

Before GitHub update, classify each 5.1 subsystem.

**Classification Labels:**
- `production-ready` - Validated, stable, recommended for use
- `guarded/beta` - Working but needs operational caution
- `experimental` - Proof of concept, not for production

**Classifications:**

| Subsystem | Classification | Notes |
|-----------|----------------|-------|
| Context Bus | _____ | |
| Structured Handoffs | _____ | |
| Workstream State Tracking | _____ | |
| Replanning Engine | _____ | |
| Checkpoint/Recovery | _____ | |
| Mission Graph Scheduling | _____ | |

**Required:** All subsystems must be classified before repo update.

---

## N. Output Quality Validation

**Objective:** Prove that Mission Graph execution actually improves reasoning quality compared to flat single-agent execution.

### N1. Comparative Mission Execution

Run the same mission in two modes:

**Mode A: Mission Graph Execution**
- Full dependency graph
- Parallel workstreams
- Structured handoffs
- Strategic memory injection

**Mode B: Flat Single-Agent Execution**
- Sequential task list
- Single agent processes entire objective
- No structured handoffs
- No memory injection

**Test Mission:** Use a realistic consulting objective (e.g., "Assess market entry for SaaS product in EU")

### N2. Quality Metrics Comparison

For each execution mode, capture:

| Metric | Mission Graph | Single Agent | Pass Criteria |
|--------|--------------|-------------|---------------|
| Evaluation score | _____ | _____ | MG ≥ SA |
| Reasoning coherence (1-10) | _____ | _____ | MG ≥ SA |
| Contradiction rate | _____ | _____ | MG < SA |
| Deliverable completeness (1-10) | _____ | _____ | MG ≥ SA |
| Execution time | _____ | _____ | Reasonable |
| Token usage | _____ | _____ | Efficient |

**Evaluation Method:**
```python
from torq_console.evaluation import EvaluationEngine

# Evaluate outputs from both modes
mg_result = await evaluation_engine.evaluate(mission_graph_output)
sa_result = await evaluation_engine.evaluate(single_agent_output)
```

**Pass Criteria:**
- [ ] Mission graph evaluation score ≥ single agent score
- [ ] Contradiction rate lower in mission graph mode
- [ ] Deliverable completeness higher or equal
- [ ] Execution time within 2x of single agent (acceptable overhead)

**Status:** _____ / 4 passed

### N3. Architecture Value Demonstration

Document specific improvements from mission graph execution:

**Checks:**
- [ ] Parallel branches executed faster than sequential
- [ ] Handoffs prevented information loss between stages
- [ ] Decision gates prevented low-quality outputs
- [ ] Strategic memory provided relevant context
- [ ] Replanning recovered from failures

**Pass Criteria:**
- At least 3 of 5 architectural improvements clearly demonstrated

**Status:** _____ / 5 passed

---

## O. Runtime Telemetry Capture

**Objective:** Capture validation metrics that will support credible claims in the GitHub README.

### O1. Telemetry Schema

Create validation telemetry table or export:

```sql
CREATE TABLE IF NOT EXISTS validation_telemetry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL,
    mission_type TEXT NOT NULL,

    -- Execution metrics
    node_count INTEGER NOT NULL,
    execution_time_seconds NUMERIC NOT NULL,
    nodes_completed INTEGER NOT NULL,
    nodes_failed INTEGER DEFAULT 0,

    -- Coordination metrics
    handoff_count INTEGER NOT NULL,
    event_count INTEGER NOT NULL,
    checkpoint_count INTEGER NOT NULL,

    -- Adaptation metrics
    replans_triggered INTEGER DEFAULT 0,
    replans_executed INTEGER DEFAULT 0,

    -- Memory metrics
    memories_injected INTEGER DEFAULT 0,
    memory_conflicts INTEGER DEFAULT 0,

    -- Quality metrics
    evaluation_score NUMERIC,
    contradiction_count INTEGER DEFAULT 0,

    -- Workstream metrics
    workstream_count INTEGER NOT NULL,
    workstreams_blocked INTEGER DEFAULT 0,

    captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### O2. Required Captures

Capture telemetry for all validation missions:

**For Each Mission (minimum 3):**
- [ ] mission_id, mission_type, node_count
- [ ] execution_time_seconds, nodes_completed, nodes_failed
- [ ] handoff_count, event_count, checkpoint_count
- [ ] replans_triggered, replans_executed
- [ ] memories_injected, memory_conflicts
- [ ] evaluation_score, contradiction_count
- [ ] workstream_count, workstreams_blocked

### O3. Aggregate Statistics for GitHub

After validation, compute aggregates:

| Metric | Value | Source |
|--------|-------|--------|
| Average mission duration | _____ seconds | AVG(execution_time_seconds) |
| Average nodes per mission | _____ | AVG(node_count) |
| Average handoffs per mission | _____ | AVG(handoff_count) |
| Average events per mission | _____ | AVG(event_count) |
| Average checkpoints per mission | _____ | AVG(checkpoint_count) |
| Average evaluation score | _____ | AVG(evaluation_score) |
| Evaluation score improvement | _____ % | vs. baseline |
| Average replan success rate | _____ % | replans_executed / replans_triggered |
| Memory injection rate | _____ per node | AVG(memories_injected) / AVG(node_count) |
| Workstream block rate | _____ % | workstreams_blocked / total workstreams |

**Pass Criteria:**
- All 3 missions have complete telemetry captured
- Aggregate statistics computed accurately
- Results suitable for public README

**Status:** _____ / 13 passed

---

## P. Memory Injection Sanity Check

**Objective:** Ensure strategic memory enhances rather than overwhelms reasoning.

### P1. Injection Volume Limits

**Check:**
- [ ] Average memories injected per node ≤ 5
- [ ] Maximum memories in any single node ≤ 10
- [ ] Total memories per mission ≤ 50

**Rationale:** More than 5 memories per node risks context flooding.

**Status:** _____ / 3 passed

### P2. Memory Effectiveness

**Check:**
- [ ] Memory injection success rate ≥ 80%
  - (memory cited and used / total memories injected)
- [ ] Memory conflict rate ≤ 10%
  - (contradictions caused by memory / total injections)
- [ ] Memory attribution score ≥ 0.6
  - (can trace outcome improvements to specific memories)

**Status:** _____ / 3 passed

### P3. Memory Scope Compliance

**Check:**
- [ ] Global memories only inject when appropriate
- [ ] Tenant-scoped memories respect tenant boundaries
- [ ] Workflow-scoped memories don't leak to other workflows
- [ ] Agent-scoped memories only inject to matching agents

**Status:** _____ / 4 passed

### P4. No Context Flooding

**Check:**
- [ ] Agent token limits respected with memory injection
- [ ] Prompt size remains manageable (≤ 80% of context window)
- [ ] Memory content doesn't duplicate existing context

**Status:** _____ / 3 passed

---

## L. Minimum Exit Criteria Before GitHub Update

**Required (all must be true):**
- [ ] 3 end-to-end missions completed successfully (Section A)
- [ ] Dependency scheduling validated (Section B)
- [ ] Handoffs reviewed and usable (Section D)
- [ ] At least 1 successful replan executed (Section F)
- [ ] At least 3 checkpoint restores tested (Section G)
- [ ] Workspace/synthesis/evaluation integration confirmed (Section H)
- [ ] No major cross-mission concurrency bug found (Section J)
- [ ] Output quality validation passes (Section N) — NEW
- [ ] Runtime telemetry captured (Section O) — NEW
- [ ] Memory injection sanity check passes (Section P) — NEW

**Strongly Preferred:**
- [ ] Mission graph beats single-agent on quality (Section N)
- [ ] Telemetry aggregates computed (Section O)
- [ ] Mission health summary exposed cleanly (Section I)
- [ ] Subsystem maturity labels assigned (Section K)
- [ ] At least one architecture doc written from validated behavior

---

## M. Validation Summary
- [ ] 3 end-to-end missions completed successfully (Section A)
- [ ] Dependency scheduling validated (Section B)
- [ ] Handoffs reviewed and usable (Section D)
- [ ] At least 1 successful replan executed (Section F)
- [ ] At least 3 checkpoint restores tested (Section G)
- [ ] Workspace/synthesis/evaluation integration confirmed (Section H)
- [ ] No major cross-mission concurrency bug found (Section J)

**Strongly Preferred:**
- [ ] Mission health summary exposed cleanly (Section I)
- [ ] Subsystem maturity labels assigned (Section K)
- [ ] At least one architecture doc written from validated behavior

---

## M. Validation Summary

**Date:** _______________

**Validator:** _______________

**Overall Status:** PASS / FAIL

**Total Checks:** _____ / 194

**Updated total includes:**
- Original: 148 checks (Sections A-L)
- Section N (Output Quality): 9 checks
- Section O (Telemetry Capture): 13 checks
- Section P (Memory Sanity): 13 checks
- Section L (Exit Criteria): +3 required, +5 preferred
- Total: 148 + 9 + 13 + 13 = 183 + 11 (K/L updates) = 194

**Critical Failures:** _____

**Bugs Found:**
1.
2.
3.

**Fixes Applied:**
1.
2.
3.

**Known Limitations:**
1.
2.
3.

**Recommendation:**
- [ ] Ready for GitHub/README refresh
- [ ] Not ready — requires: _____

**Next Steps:**
1.
2.
3.

---

## Appendix: Test Mission Definitions

### Mission 1: Market Entry Analysis
**Type:** Analysis
**Objective:** Assess market opportunity for product X in region Y
**Complexity:** Medium
**Parallel Branches:** Yes (research workstreams)
**Decision Gates:** 1 (go/no-go based on confidence)

### Mission 2: Product Roadmap Planning
**Type:** Planning
**Objective:** Create 12-month roadmap for product line Z
**Complexity:** High
**Dependencies:** Heavy (sequential phases)
**Decision Gates:** 2 (budget gate, resource gate)

### Mission 3: Technical Risk Evaluation
**Type:** Evaluation
**Objective:** Assess technical risks for architecture proposal
**Complexity:** Medium
**Triggers:** Replanning likely (contradictions, low confidence)
**Decision Gates:** 1 (risk threshold)

---

### Mission 4: Quality Comparison (for Section N)
**Type:** Comparative Validation
**Objective:** Same objective executed via Mission Graph vs Single Agent
**Purpose:** Prove architecture improves quality, not just adds complexity

**Objective:** "Assess technical feasibility of migrating monolith to microservices"

**Mission Graph Mode:**
- Workstream 1: Analyze current architecture
- Workstream 2: Research microservices patterns
- Workstream 3: Assess migration complexity
- Workstream 4: Evaluate cost/benefit
- Decision gate: Go/no-go based on feasibility confidence
- Synthesis: Comprehensive migration recommendation

**Single Agent Mode:**
- Same objective processed by single agent sequentially

**Success Criteria:** Mission Graph mode scores higher on evaluation while maintaining reasonable execution time.

---

## Appendix: Validation Timeline

### 14-Day Validation Schedule

**Day 1-2 (Mon-Tue): Mission Graph & Scheduler**
- Section A: Mission creation, startup, completion
- Section B: Dependency enforcement, parallel execution, decision gates
- Target: All A-B checks pass

**Day 3-4 (Wed-Thu): Context Bus & Handoffs**
- Section C: Event generation, persistence, subscriptions
- Section D: Handoff completeness, delivery, quality
- Target: All C-D checks pass

**Day 5-6 (Fri-Mon): Workstreams & Replanning**
- Section E: Workstream phases, health, metrics
- Section F: Replan triggers, proposals, execution
- Target: All E-F checks pass

**Day 7 (Tue): Checkpoints & Recovery**
- Section G: Checkpoint creation, restore integrity, retention
- Target: All G checks pass

**Day 8 (Wed): Integration**
- Section H: Workspace, synthesis, evaluation integration
- Target: All H checks pass

**Day 9 (Thu): Observability**
- Section I: Traceability, failure visibility, health summary
- Target: All I checks pass

**Day 10 (Fri): Performance & Stability**
- Section J: Parallel missions, event volume, interruption recovery
- Target: All J checks pass

**Day 11-12 (Mon-Tue): Output Quality & Telemetry**
- Section N: Comparative mission execution
- Section O: Telemetry capture and aggregation
- Section P: Memory injection sanity checks
- Target: All N-O-P checks pass

**Day 13 (Wed): Bug Fixes**
- Address any failures from sections A-P
- Re-test failed checks
- Target: All checks pass

**Day 14 (Thu): Final Classification**
- Section K: Subsystem maturity classification
- Section L: Exit criteria confirmation
- Produce validation report
- Target: Ready for GitHub decision

### Contingency Day

**Day 15 (Fri): Extra validation buffer**
- Address remaining issues
- Final documentation
- Go/no-go decision for GitHub update

---

*This checklist is the source of truth for Phase 5.1 validation readiness.*
