# Layer 13 Product Requirements Document (PRD)
## TORQ Economic Intelligence System

**Version:** 0.13.0-planning
**Status:** PRD DRAFT
**Author:** Agent 2
**Date:** 2026-03-14

---

## Executive Summary

Layer 13 brings economic intelligence to TORQ, enabling the system to make resource-aware decisions about what actions deserve investment. Currently, TORQ can validate claims through federation (Layer 12) but lacks the ability to prioritize competing missions under budget constraints.

### Problem Statement

TORQ faces three critical resource allocation challenges:

1. **Unbounded Mission Queue** - Missions accumulate without prioritization, wasting compute on low-value work
2. **Blind Budget Allocation** - No mechanism to allocate constrained resources across competing priorities
3. **Value Invisibility** - Stakeholders cannot see the economic rationale behind execution decisions

### Solution

Layer 13 introduces a five-layer economic evaluation pipeline that:
- Filters infeasible proposals before resource expenditure
- Calculates intrinsic value independent of execution confidence
- Adjusts value based on multi-node federation validation
- Measures efficiency as value per unit cost
- Selects optimal mission sets under budget constraints

---

## Objectives

### Primary Objectives

| ID | Objective | Success Metric | Priority |
|----|-----------|----------------|----------|
| O1 | Enable resource-aware mission prioritization | 90%+ of allocated budget achieves target value | P0 |
| O2 | Provide transparent economic decision rationale | Every allocation decision is explainable in 3 steps | P0 |
| O3 | Minimize opportunity cost of rejected missions | Regret score < 15% of total allocated value | P1 |
| O4 | Support real-time budget-constrained allocation | Allocation decisions < 100ms for 100 proposals | P1 |

### Secondary Objectives

| ID | Objective | Success Metric | Priority |
|----|-----------|----------------|----------|
| O5 | Learn from historical mission outcomes | Allocation efficiency improves 10% over 100 cycles | P2 |
| O6 | Support strategic mission type prioritization | Required mission types funded 95%+ of time | P2 |
| O7 | Handle graceful degradation under resource starvation | System functions with 10% of normal budget | P2 |

---

## Functional Requirements

### FR1: Feasibility Gate (Layer 1)

**ID:** FR-1.1
**Title:** Hard Filter Evaluation
**Description:** System must apply hard filters before any scoring to prevent waste on infeasible proposals.

**Acceptance Criteria:**
- [ ] Reject proposals with cost exceeding remaining budget
- [ ] Reject proposals requiring unavailable capabilities
- [ ] Reject proposals with impossible deadlines
- [ ] Reject proposals missing required federation validation
- [ ] Reject proposals below minimum confidence threshold
- [ ] Reject proposals of forbidden mission types
- [ ] Provide clear rejection reason for each filter failure

**Priority:** P0

---

**ID:** FR-1.2
**Title:** Prerequisite Validation
**Description:** System must verify that all prerequisite missions are complete before allowing a proposal to proceed.

**Acceptance Criteria:**
- [ ] Accept proposal only if all prerequisite mission IDs are in completed state
- [ ] Queue proposal if prerequisites are in progress
- [ ] Reject proposal if any prerequisite failed
- [ ] Support circular dependency detection

**Priority:** P1

---

### FR2: Base Value Calculation (Layer 2)

**ID:** FR-2.1
**Title:** Intrinsic Value Scoring
**Description:** System must calculate intrinsic mission value independent of execution confidence or cost.

**Acceptance Criteria:**
- [ ] Combine user value, urgency, and strategic fit using weighted sum
- [ ] Normalize result to [0.0, 1.0] range
- [ ] Support configurable weights for each component
- [ ] Provide breakdown of contribution from each factor

**Priority:** P0

---

**ID:** FR-2.2
**Title:** Urgency Decay
**Description:** System must apply time-based decay to urgency scores to ensure time-sensitive missions are prioritized appropriately.

**Acceptance Criteria:**
- [ ] Urgency decays as deadline approaches
- [ ] Missions past deadline are automatically rejected
- [ ] Support configurable decay curves (linear, exponential)

**Priority:** P2

---

### FR3: Execution Quality Modification (Layer 3)

**ID:** FR-3.1
**Title:** Confidence-Based Adjustment
**Description:** System must adjust base value based on federation validation confidence.

**Acceptance Criteria:**
- [ ] Multiplier in range [0.5, 1.5] based on confidence
- [ ] Confidence 0.5 = neutral multiplier (1.0)
- [ ] Confidence > 0.5 increases multiplier
- [ ] Confidence < 0.5 decreases multiplier
- [ ] Federation participation bonus (diminishing returns)

**Priority:** P0

---

**ID:** FR-3.2
**Title:** Historical Performance Adjustment
**Description:** System must incorporate historical mission success rates for similar mission types.

**Acceptance Criteria:**
- [ ] Track historical value achieved by mission type
- [ ] Apply small adjustment (±10%) based on historical performance
- [ ] Handle new mission types with no history (neutral adjustment)

**Priority:** P2

---

### FR4: Economic Efficiency Calculation (Layer 4)

**ID:** FR-4.1
**Title:** Value-Per-Cost Efficiency
**Description:** System must calculate economic efficiency as value achieved per unit of resource spent.

**Acceptance Criteria:**
- [ ] Efficiency = quality_adjusted_value / (cost + epsilon)
- [ ] Epsilon prevents division by zero
- [ ] Higher efficiency = better return on investment
- [ ] Sort missions by efficiency for allocation

**Priority:** P0

---

**ID:** FR-4.2
**Title:** Strategic Mission Type Bonus
**Description:** System must apply bonus to critical mission types to ensure strategic priorities are met.

**Acceptance Criteria:**
- [ ] Configurable list of required mission types
- [ ] Apply capped bonus to efficiency score
- [ ] Bonus recorded separately for transparency
- [ ] Strategic missions prioritized even with lower raw efficiency

**Priority:** P1

---

### FR5: Portfolio Allocation (Layer 5)

**ID:** FR-5.1
**Title:** Budget-Constrained Selection
**Description:** System must select optimal mission set given budget constraints using knapsack-style optimization.

**Acceptance Criteria:**
- [ ] Fund missions by efficiency ranking until budget exhaustion
- [ ] Queue valid missions that don't fit in remaining budget
- [ ] Reject ineligible missions with clear reasons
- [ ] Support strategic constraint mode (required types funded first)
- [ ] Calculate budget utilization percentage

**Priority:** P0

---

**ID:** FR-5.2
**Title:** Opportunity Cost Calculation
**Description:** System must calculate opportunity cost for each rejected mission to inform future allocation decisions.

**Acceptance Criteria:**
- [ ] Identify best accepted alternative for each rejection
- [ ] Calculate value difference (rejected - best accepted)
- [ ] Compute cost ratio relative to total budget
- [ ] Assess strategic impact (low/medium/high)
- [ ] Aggregate to portfolio-level regret score

**Priority:** P1

---

### FR6: Metrics and Monitoring

**ID:** FR-6.1
**Title:** Allocation Metrics
**Description:** System must provide metrics to evaluate allocation quality.

**Acceptance Criteria:**
- [ ] Allocation efficiency (total value per dollar spent)
- [ ] Budget utilization (percentage of budget used)
- [ ] Regret score (value of best foregone alternative)
- [ ] Opportunity cost by mission
- [ ] Strategic impact assessment

**Priority:** P1

---

**ID:** FR-6.2
**Title:** Decision Explainability
**Description:** System must provide explanation for every allocation decision.

**Acceptance Criteria:**
- [ ] Show score breakdown by layer (1-5)
- [ ] Show rejection reason for ineligible proposals
- [ ] Show why one mission was funded over another
- [ ] Show opportunity cost for each rejection

**Priority:** P0

---

## Non-Functional Requirements

### NFR1: Performance

| ID | Requirement | Metric | Priority |
|----|-------------|--------|----------|
| NFR-1.1 | Evaluation latency | < 10ms per proposal (Layers 1-3) | P0 |
| NFR-1.2 | Prioritization latency | < 50ms for 100 proposals (Layer 4) | P0 |
| NFR-1.3 | Allocation latency | < 100ms for 100 proposals (Layer 5) | P0 |
| NFR-1.4 | Opportunity cost latency | < 200ms for full allocation | P1 |

### NFR2: Scalability

| ID | Requirement | Metric | Priority |
|----|-------------|--------|----------|
| NFR-2.1 | Proposal throughput | Support 1000 proposals per allocation cycle | P1 |
| NFR-2.2 | Concurrent evaluation | Support parallel evaluation of independent proposals | P2 |
| NFR-2.3 | Memory efficiency | < 100MB for 1000 proposals | P2 |

### NFR3: Reliability

| ID | Requirement | Metric | Priority |
|----|-------------|--------|----------|
| NFR-3.1 | Allocation determinism | Same input produces same output | P0 |
| NFR-3.2 | Budget integrity | Never allocate more than available budget | P0 |
| NFR-3.3 | Graceful degradation | Function with 10% of normal budget | P1 |
| NFR-3.4 | Error handling | All errors produce clear messages | P1 |

### NFR4: Usability

| ID | Requirement | Metric | Priority |
|----|-------------|--------|----------|
| NFR-4.1 | CLI usability | Single command for common operations | P1 |
| NFR-4.2 | Configuration simplicity | Sensible defaults with optional overrides | P1 |
| NFR-4.3 | Output clarity | Human-readable + machine-parseable formats | P2 |

---

## Success Metrics

### Overall KPIs

| Metric | Target | Measurement |
|--------|--------|-------------|
| Allocation Efficiency | ≥ 0.8 value/dollar | Total value achieved / total cost |
| Budget Utilization | 85-95% | Percentage of budget used |
| Regret Ratio | < 15% | Regret / total allocated value |
| Decision Transparency | 100% | All decisions explainable in ≤3 steps |

### Quality Gates

| Gate | Criteria | Status |
|------|----------|--------|
| Architecture Review | Five-layer pipeline approved | ✅ Complete |
| Validation Scenarios | All 5 scenarios defined | ⏳ Pending |
| Implementation | All engines passing tests | ⏳ Pending |
| Integration | Layers 8-12 integration verified | ⏳ Pending |
| Performance | All NFRs met | ⏳ Pending |

---

## User Stories

### US1: Budget-Constrained Prioritization

**As:** TORQ System Operator
**I want:** To allocate a fixed budget across competing missions
**So that:** I maximize value achieved with limited resources

**Acceptance:**
- System selects optimal mission set within budget
- Budget never exceeded
- Clear explanation of why missions were funded/queued

### US2: Strategic Mission Prioritization

**As:** TORQ Stakeholder
**I want:** To ensure critical-path missions are funded
**So that:** Strategic objectives are met even with lower raw efficiency

**Acceptance:**
- Required mission types receive priority
- Strategic bonus is transparent
- Tradeoffs are documented

### US3: Opportunity Cost Analysis

**As:** TORQ System Operator
**I want:** To understand what I'm giving up when funding decisions are made
**So that:** I can make better future allocation decisions

**Acceptance:**
- Opportunity cost calculated for each rejection
- Best alternative identified
- Strategic impact assessed

### US4: Transparent Decision Rationale

**As:** TORQ Auditor
**I want:** To understand why specific missions were funded
**So that:** I can verify alignment with organizational priorities

**Acceptance:**
- Score breakdown by layer available
- Rejection reasons documented
- Comparisons between funded and unfunded missions

---

## Dependencies

### Upstream (Layers 8-12)

| Layer | Dependency | Status |
|-------|------------|--------|
| Layer 8 | Mission definitions with value/urgency | Available |
| Layer 9 | Capability registry with resource costs | Available |
| Layer 11 | Federation validation results | Available |
| Layer 12 | Multi-node confidence scores | ✅ Closed |

### Downstream

| Layer | Dependency | Status |
|-------|------------|--------|
| Layer 14 | Dashboard metrics | Planned |
| Layer 15 | Execution queue population | Planned |

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Cost domination (low-cost missions always win) | High | Medium | Efficiency score + strategic bonus |
| Urgency overpowering value | Medium | Low | Urgency as component, not multiplier |
| Double-counting factors | High | Low | Clear layer separation |
| Inefficient allocation algorithm | Medium | Low | Greedy knapsack is near-optimal |
| Historical data sparsity | Low | Medium | Neutral adjustment for unknown types |

---

## Open Questions

| ID | Question | Owner | Target Date |
|----|----------|-------|-------------|
| OQ-1 | Should urgency decay be linear or exponential? | Agent 2 | v0.13.1 |
| OQ-2 | What is the minimum viable budget for system operation? | Agent 1 | v0.13.0 |
| OQ-3 | Should partial mission funding be supported? | Stakeholder | v0.13.1 |

---

## Roadmap

### Phase 1: Foundation (Current)
- ✅ Architecture design
- ✅ Engine scaffolds
- ⏳ PRD approval
- ⏳ Validation scenarios

### Phase 2: Implementation
- ⏳ Engine implementation
- ⏳ Integration with Layers 8-12
- ⏳ Unit tests
- ⏳ Integration tests

### Phase 3: Validation
- ⏳ Scenario-based testing
- ⏳ Performance testing
- ⏳ Bug fixes
- ⏳ Documentation

### Phase 4: Production
- ⏳ Layer 14 integration (dashboard)
- ⏳ Layer 15 integration (execution)
- ⏳ Monitoring and alerting
- ⏳ Continuous improvement

---

## Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Architecture Review | Agent 1 | | |
| Product Owner | | | |
| Technical Lead | | | |
| Security Review | | | |

---

**Document Status:** DRAFT - PENDING REVIEW
**Next Steps:** Review with Agent 1 to ensure alignment, then create validation scenarios
