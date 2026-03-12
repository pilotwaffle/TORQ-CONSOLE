# Insight Publishing & Agent Retrieval - Phase Overview

**Status**: 🟡 Ready to Start
**Dependencies**: Phase 4H.1 ✅ COMPLETE | Phase 5.3 ✅ COMPLETE | Phase 5.2 ✅ COMPLETE

---

## The Shift: From Stored History to Compounding Intelligence

**What TORQ now has:**
- ✅ Structured team execution (5.2)
- ✅ Workspace artifact continuity (5.3)
- ✅ Governed strategic memory (4H.1)
- ✅ Console stability restored

**What TORQ is good at:**
- Executing
- Persisting
- Validating
- Remembering
- Auditing

**What's next:**
Making that intelligence **reusable on purpose**

---

## Clean Model Distinction

```
┌─────────────────────────────────────────────────────────────────┐
│                    Artifact Layer                               │
│  Raw persisted execution output                                  │
│  - Execution traces, reasoning chains, outputs                  │
│  - Stored in workspace                                         │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼ (validation gate)
┌─────────────────────────────────────────────────────────────────┐
│                     Memory Layer                                 │
│  Validated carry-forward knowledge                                │
│  - Heuristics, playbooks, warnings, lessons                      │
│  - Governed by eligibility rules                                 │
│  - Queryable with freshness/provenance filters                   │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼ (curation & publication)
┌─────────────────────────────────────────────────────────────────┐
│                    Insight Layer                                 │
│  Curated, publishable intelligence objects                      │
│  - Designed for reuse                                           │
│  - Agent-retrievable                                            │
│  - Scoped by mission type, domain, freshness                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Proposed Milestones

### Milestone 1: Insight Object Model + Publishing Rules

**Goal:** Define what an "insight" is and how it differs from memory/artifacts

**Deliverables:**
- Insight type definitions (strategic, playbook, finding, decision, practice, research)
- Insight object model (Pydantic schemas)
- Publishing criteria (when does memory become insight?)
- Quality gates (minimum confidence, effectiveness thresholds)
- Lifecycle states (draft, validated, published, superseded, archived)

**Exit Criteria:**
- Insight types explicitly defined
- Publishing rules explicit and testable
- Quality gates exist
- Lifecycle model exists
- Insight candidates distinguishable from ordinary memory

---

### Milestone 2: Publishing Pipeline

**Goal:** Turn validated memory/artifacts into curated intelligence

**Deliverables:**
- Insight extraction service (from memory/artifacts)
- Insight validation workflow
- Publication approval process
- Insight persistence layer
- Supersession detection for insights

---

### Milestone 3: Retrieval Service for Agents

**Goal:** Make published insights retrievable by agents during execution

**Deliverables:**
- Insight retrieval service
- Scope-aware retrieval (by mission type, domain, agent)
- Artifact lineage tracking
- Freshness and confidence filtering
- Agent integration (injection into execution context)

---

### Milestone 4: Inspection/Audit

**Goal:** Trust, governance, and tuning for published insights

**Deliverables:**
- Insight provenance tracking
- Usage analytics (which insights are used, how effectively)
- Governance controls (deprecate, unpublish, supersede)
- Impact measurement (did insight X improve execution Y?)

---

### Milestone 5: Hardening and Regression

**Goal:** Architecture discipline and stability

**Deliverables:**
- Concurrency checks (no duplicate publishing)
- Drift/conflict detection (insight vs memory consistency)
- Full regression suite
- Performance benchmarks

---

## Insight Types (Proposed)

| Type | Description | Example |
|------|-------------|---------|
| **Strategic Insight** | High-level strategic observation | "Teams that plan before executing outperform those that don't" |
| **Playbook** | Step-by-step execution guidance | "How to handle regulatory exposure in financial analysis" |
| **Validated Finding** | Empirically validated result | "Checklist additions outperform prompt rewrites for planning" |
| **Architecture Decision** | Technical decision record | "Use PostgreSQL for workspace storage, not MongoDB" |
| **Best Practice** | Procedural recommendation | "Always validate workspace schema before publishing artifacts" |
| **Research Summary** | Synthesized research output | "Multi-agent coordination improves quality for complex tasks" |

---

## Key Constraints

**DO:**
- Keep artifact, memory, and insight layers distinct
- Build additively on 5.2, 5.3, 4H.1
- Maintain validation and governance discipline
- Focus on reusability for agents

**DO NOT:**
- Blur the lines between artifacts, memory, and insights
- Redesign existing foundations
- Skip quality gates for "speed"
- Create intelligence without provenance

---

## Success Metrics

At phase completion, TORQ should be able to:

1. **Publish** high-value outputs as reusable insights
2. **Retrieve** insights by scope, mission type, domain
3. **Inject** insights into agent execution context
4. **Track** insight usage and effectiveness
5. **Govern** the insight lifecycle (publish, deprecate, unpublish)

---

## Ready to Start

**Dependencies:** All satisfied
**First Milestone:** M1 - Insight object model + publishing rules
**Constraint:** Additive architecture, maintain layer separation

**Next session:** Implement Milestone 1 only. Keep the milestone discipline.
