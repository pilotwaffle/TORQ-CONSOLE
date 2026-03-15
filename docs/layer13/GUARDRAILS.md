# Layer 13 Guardrails
## Architecture Lock During Implementation

**Date:** 2026-03-14
**Status:** EFFECTIVE IMMEDIATELY
**Governor:** Integration Governor

---

## Architecture Lock

The Layer 13 architecture models and scoring stages are **LOCKED** during implementation.

### Locked Components

These models **CANNOT** be modified without governor approval:

- `EconomicContext`
- `ActionCandidate`
- `EconomicScore`
- `AllocationPlan`
- `OpportunityCostAnalysis`
- `FeasibilityResult`

### Locked Pipeline Stages

The five-stage evaluation pipeline **CANNOT** be reordered:

1. Feasibility Gate (Stage 1)
2. Base Value (Stage 2)
3. Execution Quality Modifier (Stage 3)
4. Economic Efficiency (Stage 4)
5. Portfolio Allocation (Stage 5)

### Locked Rules

The scoring architecture rules **CANNOT** be violated:

1. Feasibility gate MUST filter before scoring
2. Base value MUST NOT include cost
3. Confidence MUST be used ONCE (Stage 3 only)
4. Efficiency MUST be calculated AFTER value
5. Allocation MUST be bundle-aware (not just top-N)
6. Intermediate values MUST be stored

---

## What CAN Be Modified

### Implementation Details

Formula weights, algorithm choices, and optimization strategies CAN be tuned:

- Scoring weights (value_weight, urgency_weight, etc.)
- Allocation strategy parameters
- Threshold values (execute_threshold, reject_threshold)
- Convergence criteria for optimization

### Additions (Not Modifications)

New components CAN be added without approval:

- New validation scenarios
- New metrics
- New analysis tools
- New CLI features

---

## Change Request Process

If architectural changes are needed:

1. Document the proposed change
2. Explain why current architecture is insufficient
3. Get approval from Integration Governor
4. Update affected agents
5. Verify alignment after change

---

## Violation Consequences

Unauthorized architectural changes will:

1. Break alignment between Agent 1 and Agent 2
2. Invalidate validation scenarios
3. Require re-verification of all components
4. Delay Layer 13 completion

---

## Approval Status

| Component | Locked | Approver |
|-----------|--------|----------|
| Models | ✅ YES | Governor |
| Pipeline Stages | ✅ YES | Governor |
| Scoring Rules | ✅ YES | Governor |
| Formula Weights | ❌ NO | Self-approved |
| Algorithms | ❌ NO | Self-approved |
| Thresholds | ❌ NO | Self-approved |

---

**This lock remains in effect until Layer 13 v0.13.0 is released.**
