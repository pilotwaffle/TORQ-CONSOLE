# Layer 13 Economic Intelligence - Agent 2 Task Brief

## Mission

Design the validation framework and scenarios for TORQ's economic intelligence layer, ensuring the system makes high-quality resource allocation decisions under various constraints.

## Context

**Layer 12 Status:** CLOSED (v0.12-final)
**Layer 13 Status:** NEW - PRD & Validation Design Phase

Layer 13 will enable TORQ to make economically intelligent decisions about resource allocation. Your job is to define:
- What "good" economic decisions mean in TORQ
- How to validate prioritization quality
- How to measure allocation efficiency and regret
- How to stress-test budget-aware choices

## Your Responsibilities

### Product Requirements Document (PRD)

Create comprehensive PRD for Layer 13 Economic Intelligence.

**Sections:**
1. **Executive Summary** - Why economic intelligence matters for TORQ
2. **Problem Statement** - Current resource allocation limitations
3. **Objectives** - What Layer 13 should achieve
4. **Functional Requirements** - Core capabilities needed
5. **Non-Functional Requirements** - Performance, reliability, constraints
6. **Success Metrics** - How to measure Layer 13 effectiveness

**Deliverable:** `docs/layer13/LAYER13_PRD.md`

### Validation Scenarios

Define test scenarios that exercise economic decision-making quality:

1. **Constrained Budget Allocation**
   - Fixed budget across competing high-value missions
   - Validate: optimal allocation, budget exhaustion

2. **High-Value vs High-Urgency Tradeoffs**
   - Conflicts between important but not urgent vs urgent but not important
   - Validate: correct prioritization, time-sensitive decisions

3. **Opportunity Cost Comparisons**
   - Choose between mutually exclusive high-value options
   - Validate: cost of foregone alternative is calculated

4. **Low-Confidence / High-Cost Rejection**
   - Risky expensive proposals should be rejected
   - Validate: high-cost/low-CONF proposals are filtered

5. **Resource Starvation Stress**
   - Minimal resources across many missions
   - Validate: graceful degradation, mission queueing

**Deliverable:** `docs/layer13/VALIDATION_SCENARIOS.md`

### Expected Outcome Rules

Define what "correct" economic decisions look like for each scenario type:

| Scenario | Input | Expected Output | Success Criteria |
|----------|-------|----------------|------------------|
| Budget Constrained | $1000 budget, 5 missions ($200-$800 each) | Top 1-2 missions funded, remainder queued | Budget exhausted efficiently |
| Value vs Urgency | High-value/low-urgency + Low-value/high-urgency | Urgent action taken, valuable action queued | Time sensitivity respected |
| Opportunity Cost | Option A ($500, value 0.8) vs Option B ($300, value 0.7) | Higher value/weight chosen | Regret minimized |
| Risk Rejection | $800 proposal, 40% confidence | Rejected or quarantined | Risk threshold enforced |
| Resource Starvation | 10 missions, $200 total | Most efficient 1-2 missions funded | Maximizes total value |

**Deliverable:** `docs/layer13/VALIDATION_RULES.md`

### Validation Harness Design

Design how to test Layer 13 economic decision quality:

**Metrics to Track:**
- Allocation efficiency (value achieved per dollar)
- Budget utilization (% used vs wasted)
- Regret (value of foregone optimal choices)
- Response time (economic decisions should be fast)
- Stability (consistent decisions under similar inputs)

**Validation Approach:**
- Unit tests for scoring functions
- Scenario-based integration tests
- Comparison against baseline allocation strategies
- Regression tests for economic formulas

**Deliverable:** `docs/layer13/VALIDATION_APPROACH.md`

### CLI Specification

Define CLI for running Layer 13 simulations:

```bash
# Run economic prioritization
python -m torq_console.layer13.economic.run_prioritization \
    --budget 1000 \
    --missions missions.json \
    --constraints constraints.json

# Run validation suite
python -m torq_console.layer13.economic.run_validation \
    --scenarios budget_constrained,value_urgency_tradeoff

# Compare allocation strategies
python -m torq_console.layer13.economic.run_analysis \
    --baseline equal_allocation \
    --test_layer13
```

**Deliverable:** `docs/layer13/CLI_SPEC.md`

## Technical Approach

1. **Scenario-First Design:** Define scenarios before implementation to validate architecture
2. **Quantifiable Success Criteria:** Every test must have measurable pass/fail criteria
3. **Economic Theory Foundation:** Ground scenarios in real economic principles (opportunity cost, sunk cost fallacy, etc.)
4. **TORQ Context:** Ensure scenarios reflect actual TORQ use cases (missions, claims, federation)

## Best First Milestone

**Deliverable:** Layer 13 PRD + validation scenario pack

**Definition of Done:**
- PRD covers all 6 sections with stakeholder-appropriate detail
- 5 validation scenarios fully specified with inputs/outputs
- Expected outcome rules documented for all scenario types
- CLI spec defined with example commands
- Validation approach documented with success metrics

## Constraints

- DO NOT implement Layer 13 engines (that's Agent 1's job)
- DO NOT modify Layer 12 code
- Coordinate with Agent 1 on shared model definitions
- Ensure scenarios are testable with defined pass/fail criteria

## Success Criteria

- PRD clearly communicates Layer 13 value proposition
- Scenarios cover real-world TORQ economic decision situations
- Validation rules are objective and measurable
- CLI spec enables hands-on testing
- Agent 1 can implement engines directly from your specifications

## Commands

Create PRD directory:
```
mkdir -p docs/layer13
# Create LAYER13_PRD.md
```

Create validation documents:
```
# Create VALIDATION_SCENARIOS.md
# Create VALIDATION_RULES.md
# Create VALIDATION_APPROACH.md
# Create CLI_SPEC.md
```

## Timeline

- Week 1: PRD + scenario definitions
- Week 2: Expected outcome rules + validation approach
- Week 3: CLI spec + review checkpoint

## Coordination with Agent 1

**Before Starting Implementation:**
1. Review Agent 1's architecture document
2. Ensure your scenarios align with their engine interfaces
3. Agree on shared model definitions
4. Lock integration points

**During Implementation:**
1. Provide test cases for Agent 1's engine implementations
2. Validate engines against expected outcomes
3. Report any architecture-scenario mismatches

---

**Start after Layer 13 architecture is approved. Do not define scenarios that the architecture cannot support.**
