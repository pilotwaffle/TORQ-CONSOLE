# Phase 4H.1: Strategic Memory Validation & Control

**Date:** 2026-03-10
**Status:** Implementation
**Prerequisites:** Phase 5.2 (Team Execution), Phase 5.3 (Workspace Artifacts) — COMPLETE

---

## Executive Summary

Phase 4H.1 builds **governed memory** on top of TORQ's validated execution and artifact foundation. Instead of fuzzy, uncontrolled memory, we implement:

- **Explicit eligibility rules** — What can become memory
- **Validation gates** — What passes quality thresholds
- **Retrieval controls** — What agents can access
- **Full auditability** — Why every decision was made
- **Drift prevention** — No stale or contradictory carry-forward

---

## Why This Phase Now

### Prerequisites Finally Met

With Phase 5.2 and 5.3 complete, memory now has **reliable source material**:

| Foundation | Status | What It Enables |
|------------|--------|-----------------|
| Structured team execution | ✅ Complete | Validated team outputs |
| Persisted artifacts | ✅ Complete | Inspectable history |
| Context linking | ✅ Complete | Reliable execution trace |
| Read/inspection layer | ✅ Complete | Queryable artifacts |

**Without 5.2 and 5.3**, memory would be weak — operating on isolated outputs without provenance.

**With 5.2 and 5.3**, memory becomes **governed** — operating on validated, traceable artifacts.

---

## The Traceability Foundation

```
workspace → mission → node → execution → team → role/round → artifact
                                                       ↓
                                                 [Memory Gate]
                                                       ↓
                                              [Validated Memory]
```

Every memory decision can trace back to:
- Which workspace generated it
- Which mission it served
- Which node created it
- Which execution produced it
- Which team/role was responsible
- Which artifact holds the source

---

## Phase Goals

### Primary Objective

**Decide what TORQ should remember, trust, retrieve, and reject.**

### Key Outcomes

1. **Memory Quality Rules** — Explicit eligibility, not implicit accumulation
2. **Memory Validation Layer** — Gates before writes, filters before reads
3. **Retrieval Control** — Scoped, ranked, context-aware access
4. **Auditability** — Every decision explainable
5. **Drift Prevention** — No low-confidence or stale carry-forward

---

## Implementation Plan: 5 Milestones

### Milestone 1: Memory Eligibility Rules and Validation Schema

**Goal:** Define what can become memory.

**Deliverables:**
- Memory eligibility model (what artifact types, confidence levels, provenance)
- Validation schema for memory candidates
- Confidence threshold definitions
- Freshness and staleness rules
- Conflict and supersession rules

**Acceptance Criteria:**
- [ ] MemoryCandidateModel with validation rules
- [ ] Eligibility rules documented and enforced
- [ ] Confidence thresholds defined (0.0-1.0 scale)
- [ ] Provenance requirements explicit
- [ ] Artifact type whitelist/blacklist

---

### Milestone 2: Memory Write Pipeline with Validation Gate

**Goal:** Build artifact → memory extraction with validation.

**Deliverables:**
- Memory candidate extraction from artifacts
- Validation engine (confidence, completeness, provenance checks)
- Accept/reject decision logging
- Memory persistence for approved items only
- Rejection reasons captured

**Acceptance Criteria:**
- [ ] Artifact → candidate extraction works
- [ ] Validation engine accepts valid, rejects invalid
- [ ] Every decision logged with rationale
- [ ] Approved memory persisted correctly
- [ ] Rejected candidates tracked with reasons
- [ ] No regression in 5.2 or 5.3

---

### Milestone 3: Memory Retrieval Controls and Ranking Filters

**Goal:** Control what agents can retrieve, not blind access.

**Deliverables:**
- Retrieval query model with scope controls
- Ranking by confidence, recency, relevance
- Stale memory suppression
- Context-aware filtering
- Scoped retrieval (by workspace, mission, team)

**Acceptance Criteria:**
- [ ] Retrieval respects confidence floors
- [ ] Stale memory filtered out
- [ ] Results ranked by relevance
- [ ] Scoped queries work correctly
- [ ] No blind "pull everything" access

---

### Milestone 4: Audit and Inspection Layer

**Goal:** Every memory decision explainable.

**Deliverables:**
- Memory decision log (writes and retrievals)
- Inspection API for memory history
- Traceability from memory to source artifact
- Decision rationale export

**Acceptance Criteria:**
- [ ] Every write logged with artifact source
- [ ] Every retrieval logged with query context
- [ ] Can trace any memory back to origin
- [ ] Decision export available
- [ ] Audit query API works

---

### Milestone 5: Hardening, Drift Tests, and Regression Validation

**Goal:** Prove the system is production-ready.

**Deliverables:**
- Drift prevention tests (no stale carry-forward)
- Contradiction detection tests
- Concurrency tests (parallel writes/reads)
- Full regression suite (5.2, 5.3, 4H.1 M1-M4)
- Performance validation

**Acceptance Criteria:**
- [ ] Drift prevention validated
- [ ] Contradictions detected and handled
- [ ] Concurrency safe
- [ ] No regression in 5.2 or 5.3
- [ ] All validation tests pass
- [ ] Phase 4H.1 declared complete

---

## Architecture: Additive and Non-Blocking

```
┌─────────────────────────────────────────────────────────────┐
│                    FROZEN LAYER                              │
│  Phase 5.2: Team Runtime (unchanged)                        │
│  Phase 5.3: Artifact System (source-of-truth input)         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                 Phase 4H.1: Memory Layer (ADDITIVE)         │
│                                                              │
│  ┌──────────────┐    ┌─────────────┐    ┌──────────────┐  │
│  │  Extraction  │ → │ Validation  │ → │   Write/Log   │  │
│  │              │    │    Gate     │    │              │  │
│  └──────────────┘    └─────────────┘    └──────────────┘  │
│         ↑                                       ↓           │
│         │                            ┌──────────────┐      │
│         └────────────────────────────│ Retrieval    │      │
│              (validated memory)      │  Controls    │      │
│                                      └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Additive Only** — No modifications to frozen 5.2 or 5.3
2. **Read-First** — Artifact system is source-of-truth, memory is derived
3. **Gate-Heavy** — Validate on write, filter on read
4. **Audit-Everything** — Every decision logged
5. **Fail-Closed** — When uncertain, reject, don't accept

---

## Memory Quality Rules

### Eligibility Criteria

A memory candidate MUST satisfy:

| Criterion | Requirement | Rationale |
|-----------|-------------|-----------|
| **Source Type** | Validated artifact only | No unstructured inputs |
| **Confidence** | ≥ threshold (default 0.7) | Low-confidence not reusable |
| **Completeness** | All required fields present | Partial memory is misleading |
| **Provenance** | Traceable to execution | Untraceable = untrustworthy |
| **Freshness** | Not stale per domain rules | Old memory can be harmful |
| **Consistency** | No conflicts with newer data | Contradictions confuse agents |

### Artifact Type Eligibility

| Artifact Type | Eligible | Notes |
|---------------|----------|-------|
| WEB_SEARCH | Conditional | High confidence only |
| CODE_EXECUTION | Yes | Verified by execution |
| ANALYSIS | Conditional | Must have conclusion |
| DECISION | Yes | Explicit decision points |
| PLAN | Yes | Structured plans |
| TEAM_OUTPUT | Yes | Validated team results |
| RAW_OUTPUT | No | Too unstructured |
| ERROR | Conditional | Only if resolved |

### Confidence Thresholds

| Range | Action | Example |
|-------|--------|---------|
| 0.9 - 1.0 | Auto-accept | Verified code execution |
| 0.7 - 0.9 | Accept with log | High-confidence analysis |
| 0.5 - 0.7 | Review required | Medium-confidence outputs |
| 0.0 - 0.5 | Reject | Low-confidence, unverified |

---

## Drift Prevention

### What We Prevent

| Drift Type | Prevention Mechanism |
|------------|---------------------|
| **Low-confidence carry-forward** | Confidence floor on retrieval |
| **Stale recommendations** | Freshness validation on write/read |
| **Contradictory reuse** | Conflict detection before write |
| **Noisy pollution** | Source type filtering |
| **Orphaned memory** | Provenance requirement |

### Staleness Rules (by Domain)

| Domain | Freshness Window | Rationale |
|--------|------------------|-----------|
| API Endpoints | 7 days | APIs change frequently |
| Code Patterns | 30 days | Patterns evolve slower |
| Architecture Decisions | 90 days | Stable but can evolve |
| Team Performance | 14 days | Team dynamics change |
| External Data | 1 day | Highly volatile |

---

## Files to Create

| File | Purpose | Milestone |
|------|---------|-----------|
| `torq_console/memory/memory_models.py` | Memory candidate and validation models | M1 |
| `torq_console/memory/eligibility_rules.py` | Eligibility rule engine | M1 |
| `torq_console/memory/memory_extractor.py` | Extract candidates from artifacts | M2 |
| `torq_console/memory/validation_gate.py` | Validation engine | M2 |
| `torq_console/memory/memory_writer.py` | Validated memory persistence | M2 |
| `torq_console/memory/memory_retrieval.py` | Controlled retrieval | M3 |
| `torq_console/memory/memory_audit.py` | Audit and inspection | M4 |
| `scripts/test_phase_4h_1_milestone_1.py` | M1 validation tests | M1 |
| `scripts/test_phase_4h_1_milestone_2.py` | M2 validation tests | M2 |
| `scripts/test_phase_4h_1_milestone_3.py` | M3 validation tests | M3 |
| `scripts/test_phase_4h_1_milestone_4.py` | M4 validation tests | M4 |
| `scripts/test_phase_4h_1_milestone_5.py` | M5 hardening tests | M5 |

---

## Definition of Done

Phase 4H.1 is complete when:

- [ ] M1: Memory eligibility rules explicit and enforced
- [ ] M2: Write pipeline with validation gate working
- [ ] M3: Retrieval controls prevent blind access
- [ ] M4: All decisions auditable and explainable
- [ ] M5: Drift prevention validated, no regression
- [ ] All validation tests pass
- [ ] Code committed
- [ ] Phase 4H.1 declared complete

---

## Success Metrics

### Before Phase 4H.1

- Memory: Fuzzy, unvalidated, no provenance
- Retrieval: Blind "pull everything"
- Quality: Unknown, inconsistent
- Drift: Uncontrolled
- Audit: Impossible

### After Phase 4H.1

- Memory: Governed, validated, full provenance
- Retrieval: Scoped, ranked, filtered
- Quality: Explicit thresholds, enforced
- Drift: Prevented by design
- Audit: Complete, explainable

---

## Current Status

**Starting Phase 4H.1 Milestones 1 and 2:**

- Task #129: Milestone 1 — Memory eligibility rules and validation schema
- Task #130: Milestone 2 — Memory write pipeline with validation gate

**Constraint Checklist:**

- ✅ Frozen 5.2 runtime remains unchanged
- ✅ 5.3 artifact system as source-of-truth
- ✅ Additive architecture only
- ✅ Read-first design (memory derived from artifacts)

---

## Next Step

Begin Milestone 1 implementation:
1. Define memory candidate models
2. Implement eligibility rule engine
3. Create validation schema
4. Build confidence threshold system
