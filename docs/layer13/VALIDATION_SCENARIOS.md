# Layer 13 Validation Scenarios
## TORQ Economic Intelligence System

**Version:** 0.13.0-planning
**Status:** SCENARIOS DEFINED
**Author:** Agent 2
**Date:** 2026-03-14

---

## Overview

This document defines the validation scenarios for Layer 13 Economic Intelligence. Each scenario represents a real-world use case that the system must handle correctly.

Scenarios are designed to validate:
- Correct economic decision-making under various constraints
- Robustness against edge cases
- Proper handling of tradeoffs
- Graceful degradation under stress

---

## Scenario 1: Constrained Budget Allocation

### Description

A fixed budget must be allocated across multiple high-value missions. The system should select missions that maximize total value while staying within budget.

### Input

```python
budget = 1000.0

missions = [
    MissionProposal(
        mission_id="m1",
        mission_type="data_ingestion",
        user_value=0.8,
        urgency=0.5,
        strategic_fit=0.7,
        estimated_cost=200.0,
    ),
    MissionProposal(
        mission_id="m2",
        mission_type="model_training",
        user_value=0.9,
        urgency=0.4,
        strategic_fit=0.8,
        estimated_cost=500.0,
    ),
    MissionProposal(
        mission_id="m3",
        mission_type="feature_export",
        user_value=0.7,
        urgency=0.6,
        strategic_fit=0.6,
        estimated_cost=350.0,
    ),
    MissionProposal(
        mission_id="m4",
        mission_type="api_deployment",
        user_value=0.85,
        urgency=0.7,
        strategic_fit=0.75,
        estimated_cost=400.0,
    ),
    MissionProposal(
        mission_id="m5",
        mission_type="monitoring_setup",
        user_value=0.6,
        urgency=0.3,
        strategic_fit=0.5,
        estimated_cost=150.0,
    ),
]
```

### Expected Output

| Metric | Expected Value | Tolerance |
|--------|----------------|-----------|
| Funded Missions | 3-4 missions | Exact |
| Budget Utilization | 85-100% | ±5% |
| Total Value | Maximized | N/A |

### Expected Allocation

By efficiency (value/cost):
- m5: 0.6/150 = 0.0040
- m1: 0.67/200 = 0.00335
- m4: 0.73/400 = 0.001825
- m2: 0.7/500 = 0.0014
- m3: 0.63/350 = 0.0018

**Funded:** m5 (150), m1 (200), m4 (400) = 750 total
**Remaining:** 250
**Next best:** m3 (350) - doesn't fit, m2 (500) - doesn't fit
**Queued:** m3, m2

### Success Criteria

- [ ] Budget never exceeded (funded cost ≤ 1000)
- [ ] Maximum possible value achieved
- [ ] Higher efficiency missions funded before lower efficiency
- [ ] Budget utilization ≥ 85%
- [ ] Opportunity costs calculated for queued missions

---

## Scenario 2: High-Value vs High-Urgency Tradeoffs

### Description

A conflict exists between a high-value/low-urgency mission and a low-value/high-urgency mission. The system must correctly prioritize based on the staged evaluation.

### Input

```python
budget = 500.0

missions = [
    MissionProposal(
        mission_id="strategic_project",
        mission_type="infrastructure",
        user_value=0.95,      # Very high value
        urgency=0.2,          # Not time-sensitive
        strategic_fit=0.9,    # High strategic fit
        estimated_cost=400.0,
        deadline=None,        # No deadline
    ),
    MissionProposal(
        mission_id="hotfix",
        mission_type="bugfix",
        user_value=0.4,       # Low value
        urgency=0.95,         # Extremely urgent
        strategic_fit=0.3,    # Low strategic fit
        estimated_cost=100.0,
        deadline=datetime.utcnow() + timedelta(hours=2),  # Soon
    ),
]
```

### Analysis

**Strategic Project:**
- Base value = 0.6*0.95 + 0.3*0.2 + 0.1*0.9 = 0.57 + 0.06 + 0.09 = 0.72
- Quality adjusted (assuming neutral modifier) = 0.72
- Efficiency = 0.72 / 400 = 0.0018

**Hotfix:**
- Base value = 0.6*0.4 + 0.3*0.95 + 0.1*0.3 = 0.24 + 0.285 + 0.03 = 0.555
- Quality adjusted = 0.555
- Efficiency = 0.555 / 100 = 0.00555

### Expected Output

**Both should be funded:** Hotfix (100) + Strategic (400) = 500

If budget only allows one (budget = 450):
- Hotfix funded first (higher efficiency: 0.00555 > 0.0018)
- Strategic project queued (doesn't fit in remaining 350)

### Success Criteria

- [ ] Both missions funded when budget allows
- [ ] Hotfix funded first when budget constrained (higher efficiency)
- [ ] Urgency correctly weighted as component, not override
- [ ] Strategic project not penalized for low urgency
- [ ] Deadline properly enforced for hotfix

### Edge Case: Budget = 300

With only 300 budget:
- Hotfix funded (100)
- Strategic project doesn't fit (400 > 200 remaining)
- System should queue strategic project, not reject it

---

## Scenario 3: Opportunity Cost Comparisons

### Description

Choose between mutually exclusive high-value options to validate opportunity cost calculation.

### Input

```python
budget = 600.0

missions = [
    MissionProposal(
        mission_id="option_a",
        mission_type="feature_a",
        user_value=0.8,
        urgency=0.5,
        strategic_fit=0.7,
        estimated_cost=500.0,
    ),
    MissionProposal(
        mission_id="option_b",
        mission_type="feature_b",
        user_value=0.7,
        urgency=0.6,
        strategic_fit=0.65,
        estimated_cost=300.0,
    ),
    MissionProposal(
        mission_id="option_c",
        mission_type="feature_c",
        user_value=0.6,
        urgency=0.4,
        strategic_fit=0.5,
        estimated_cost=200.0,
    ),
]
```

### Analysis

**Option A:** Base = 0.6*0.8 + 0.3*0.5 + 0.1*0.7 = 0.48 + 0.15 + 0.07 = 0.70
- Efficiency = 0.70 / 500 = 0.0014

**Option B:** Base = 0.6*0.7 + 0.3*0.6 + 0.1*0.65 = 0.42 + 0.18 + 0.065 = 0.665
- Efficiency = 0.665 / 300 = 0.00222

**Option C:** Base = 0.6*0.6 + 0.3*0.4 + 0.1*0.5 = 0.36 + 0.12 + 0.05 = 0.53
- Efficiency = 0.53 / 200 = 0.00265

### Expected Allocation

By efficiency: C (0.00265) > B (0.00222) > A (0.0014)

Budget 600:
1. Fund C (200), remaining 400
2. Fund B (300), remaining 100
3. A doesn't fit (500 > 100), queued

### Expected Opportunity Costs

For rejected A:
- Best accepted alternative: C (highest value among accepted)
- Opportunity cost = 0.70 - 0.665 = 0.035
- Or compare to B if same type

### Success Criteria

- [ ] Higher efficiency missions funded first
- [ ] Opportunity cost calculated for rejected mission
- [ ] Best accepted alternative correctly identified
- [ ] Cost ratio computed (500/600 = 0.833)
- [ ] Strategic impact assessed (high given cost ratio)

---

## Scenario 4: Low-Confidence / High-Cost Rejection

### Description

Risky expensive proposals should be rejected or flagged, not funded just because they have high nominal value.

### Input

```python
budget = 1000.0

missions = [
    MissionProposal(
        mission_id="risky_bet",
        mission_type="experimental",
        user_value=0.9,
        urgency=0.5,
        strategic_fit=0.8,
        estimated_cost=800.0,
        requires_validation=True,
    ),
    MissionProposal(
        mission_id="safe_bet",
        mission_type="standard",
        user_value=0.7,
        urgency=0.5,
        strategic_fit=0.6,
        estimated_cost=200.0,
        requires_validation=True,
    ),
]

# Federation results
federation_risky = FederationResult(
    claim_id="risky_claim",
    acceptance_rate=0.4,    # Low acceptance
    confidence=0.35,        # Low confidence - below threshold
    participating_nodes=12,
)

federation_safe = FederationResult(
    claim_id="safe_claim",
    acceptance_rate=0.92,   # High acceptance
    confidence=0.88,        # High confidence
    participating_nodes=12,
)
```

### Analysis

**Risky Bet:**
- Base value = 0.6*0.9 + 0.3*0.5 + 0.1*0.8 = 0.54 + 0.15 + 0.08 = 0.77
- With low confidence (0.35 < 0.5 threshold):
  - Execution modifier = 1.0 + (0.35 - 0.5) * 0.5 = 1.0 - 0.075 = 0.925
  - Quality adjusted = 0.77 * 0.925 = 0.712
- If confidence threshold = 0.5: REJECTED at feasibility gate
- If allow_risky_proposals = True:
  - Efficiency = 0.712 / 800 = 0.00089

**Safe Bet:**
- Base value = 0.6*0.7 + 0.3*0.5 + 0.1*0.6 = 0.42 + 0.15 + 0.06 = 0.63
- With high confidence (0.88):
  - Execution modifier = 1.0 + (0.88 - 0.5) * 0.5 = 1.0 + 0.19 = 1.19
  - Quality adjusted = 0.63 * 1.19 = 0.75
- Efficiency = 0.75 / 200 = 0.00375

### Expected Output

**With strict confidence threshold (0.5):**
- Risky Bet: REJECTED (confidence below threshold)
- Safe Bet: FUNDED

**With allow_risky_proposals = True:**
- Safe Bet: FUNDED (efficiency 0.00375)
- Risky Bet: QUEUED or REJECTED (efficiency 0.00089, 40% of safe)

### Success Criteria

- [ ] Low confidence proposals filtered when threshold enforced
- [ ] Confidence threshold configurable
- [ ] High-cost low-confidence proposals rejected
- [ ] Rejection reason clearly communicated
- [ ] Safe alternatives prioritized

---

## Scenario 5: Resource Starvation Stress

### Description

Minimal resources across many missions. System should maximize value within severe constraints.

### Input

```python
budget = 200.0  # Very low budget

missions = [
    MissionProposal(
        mission_id=f"mission_{i}",
        mission_type="standard",
        user_value=0.5 + (i * 0.05),
        urgency=0.5,
        strategic_fit=0.5 + (i * 0.03),
        estimated_cost=50.0 + (i * 10),
    )
    for i in range(10)  # 10 missions
]
```

### Mission Details

| ID | Value | Cost | Efficiency |
|----|-------|------|------------|
| m0 | 0.50 | 50 | 0.0100 |
| m1 | 0.55 | 60 | 0.00917 |
| m2 | 0.60 | 70 | 0.00857 |
| m3 | 0.65 | 80 | 0.00813 |
| m4 | 0.70 | 90 | 0.00778 |
| m5 | 0.75 | 100 | 0.0075 |
| m6 | 0.80 | 110 | 0.00727 |
| m7 | 0.85 | 120 | 0.00708 |
| m8 | 0.90 | 130 | 0.00692 |
| m9 | 0.95 | 140 | 0.00679 |

### Expected Allocation

Budget 200:
1. Fund m0 (50), remaining 150
2. Fund m1 (60), remaining 90
3. Fund m2 (70), remaining 20
4. m3 (80) doesn't fit

**Funded:** m0, m1, m2 (total 180)
**Remaining:** 20
**Queued:** m3-m9

### Success Criteria

- [ ] Maximum number of missions funded within budget
- [ ] Budget efficiently utilized (≥ 85%)
- [ ] Higher efficiency missions prioritized
- [ ] Graceful handling of severe constraints
- [ ] No crashes or errors with zero remaining budget

### Edge Case: Budget = 30

With only 30 budget (smaller than cheapest mission):
- No missions funded
- All missions queued
- System doesn't crash

---

## Scenario 6: Strategic Mission Type Constraints

### Description

Required mission types must be funded even if they have lower raw efficiency.

### Input

```python
budget = 600.0
required_mission_types = ["security", "compliance"]

missions = [
    MissionProposal(
        mission_id="security_audit",
        mission_type="security",
        user_value=0.6,
        urgency=0.7,
        strategic_fit=0.8,
        estimated_cost=300.0,
    ),
    MissionProposal(
        mission_id="compliance_check",
        mission_type="compliance",
        user_value=0.5,
        urgency=0.8,
        strategic_fit=0.7,
        estimated_cost=250.0,
    ),
    MissionProposal(
        mission_id="feature_development",
        mission_type="feature",
        user_value=0.9,
        urgency=0.4,
        strategic_fit=0.6,
        estimated_cost=400.0,
    ),
]
```

### Analysis

**Security Audit:** Base = 0.6*0.6 + 0.3*0.7 + 0.1*0.8 = 0.36 + 0.21 + 0.08 = 0.65
- Efficiency = 0.65 / 300 = 0.00217

**Compliance Check:** Base = 0.6*0.5 + 0.3*0.8 + 0.1*0.7 = 0.30 + 0.24 + 0.07 = 0.61
- Efficiency = 0.61 / 250 = 0.00244

**Feature Development:** Base = 0.6*0.9 + 0.3*0.4 + 0.1*0.6 = 0.54 + 0.12 + 0.06 = 0.72
- Efficiency = 0.72 / 400 = 0.0018

### Expected Allocation

**Standard allocation (by efficiency):**
1. Compliance (250), remaining 350
2. Security (300), remaining 50
3. Feature doesn't fit (400 > 50), queued

**Strategic allocation (required types first):**
Same result in this case, but required types get priority even if lower efficiency.

### Success Criteria

- [ ] Required mission types funded first
- [ ] Strategic bonus applied and recorded
- [ ] Remaining budget used for optional missions
- [ ] Tradeoffs documented

---

## Scenario 7: Federation Confidence Impact

### Description

Validate that federation confidence correctly adjusts scores.

### Input

```python
budget = 500.0

missions = [
    MissionProposal(
        mission_id="high_conf",
        mission_type="standard",
        user_value=0.7,
        urgency=0.5,
        strategic_fit=0.6,
        estimated_cost=300.0,
    ),
    MissionProposal(
        mission_id="low_conf",
        mission_type="standard",
        user_value=0.8,  # Higher value
        urgency=0.5,
        strategic_fit=0.6,
        estimated_cost=300.0,
    ),
]

federation_high = FederationResult(
    claim_id="high_conf_claim",
    acceptance_rate=0.95,
    confidence=0.92,
    participating_nodes=15,
)

federation_low = FederationResult(
    claim_id="low_conf_claim",
    acceptance_rate=0.6,
    confidence=0.55,
    participating_nodes=8,
)
```

### Analysis

**High Confidence:**
- Base = 0.6*0.7 + 0.3*0.5 + 0.1*0.6 = 0.42 + 0.15 + 0.06 = 0.63
- Modifier = 1.0 + (0.92 - 0.5) * 0.5 = 1.21
- Quality adjusted = 0.63 * 1.21 = 0.762
- Efficiency = 0.762 / 300 = 0.00254

**Low Confidence:**
- Base = 0.6*0.8 + 0.3*0.5 + 0.1*0.6 = 0.48 + 0.15 + 0.06 = 0.69
- Modifier = 1.0 + (0.55 - 0.5) * 0.5 = 1.025
- Quality adjusted = 0.69 * 1.025 = 0.707
- Efficiency = 0.707 / 300 = 0.00236

### Expected Output

High confidence funded first (0.00254 > 0.00236) despite lower base value.

### Success Criteria

- [ ] Confidence correctly modifies score
- [ ] High confidence can overcome lower base value
- [ ] Federation participation bonus applied
- [ ] Federation validation recorded in score

---

## Execution Order

Run scenarios in order:
1. Scenario 1 (Basic allocation)
2. Scenario 3 (Opportunity cost)
3. Scenario 2 (Value vs urgency)
4. Scenario 4 (Confidence filtering)
5. Scenario 5 (Resource starvation)
6. Scenario 6 (Strategic constraints)
7. Scenario 7 (Federation impact)

---

## Test Data

Sample mission data and expected outputs are provided in `tests/layer13/test_data/`:

```
tests/layer13/test_data/
├── scenario1_budget_constrained.json
├── scenario2_value_urgency_tradeoff.json
├── scenario3_opportunity_cost.json
├── scenario4_low_confidence_rejection.json
├── scenario5_resource_starvation.json
├── scenario6_strategic_constraints.json
└── scenario7_federation_confidence.json
```

---

**Document Status:** COMPLETE
**Next:** Create validation rules document
