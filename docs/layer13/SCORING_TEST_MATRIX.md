# Layer 13 Scoring Test Matrix
## TORQ Economic Intelligence System

**Version:** 0.13.0-planning
**Status:** SAFETY CHECKPOINT
**Governor:** System
**Date:** 2026-03-14

---

## Purpose

This document ensures every scoring rule has a corresponding test case. This prevents hidden scoring bugs that could corrupt economic decisions.

---

## Test Matrix Overview

| Rule | Layer | Test Case | File | Status |
|------|-------|-----------|------|--------|
| Budget check | 1 | test_reject_exceeds_budget | test_feasibility.py | ⏳ Pending |
| Confidence threshold | 1 | test_reject_low_confidence | test_feasibility.py | ⏳ Pending |
| Deadline validation | 1 | test_reject_impossible_deadline | test_feasibility.py | ⏳ Pending |
| Prerequisite check | 1 | test_reject_missing_prerequisites | test_feasibility.py | ⏳ Pending |
| Forbidden type | 1 | test_reject_forbidden_type | test_feasibility.py | ⏳ Pending |
| Base value normalization | 2 | test_base_value_range | test_base_value.py | ⏳ Pending |
| User value weight | 2 | test_user_value_contribution | test_base_value.py | ⏳ Pending |
| Urgency weight | 2 | test_urgency_contribution | test_base_value.py | ⏳ Pending |
| Strategic fit weight | 2 | test_strategic_fit_contribution | test_base_value.py | ⏳ Pending |
| Confidence modifier | 3 | test_confidence_increases_modifier | test_execution_modifier.py | ⏳ Pending |
| Low confidence penalty | 3 | test_low_confidence_decreases_modifier | test_execution_modifier.py | ⏳ Pending |
| Federation participation bonus | 3 | test_multi_node_bonus | test_execution_modifier.py | ⏳ Pending |
| Historical adjustment | 3 | test_historical_performance_adjustment | test_execution_modifier.py | ⏳ Pending |
| Efficiency calculation | 4 | test_efficiency_formula | test_efficiency.py | ⏳ Pending |
| Cost epsilon prevents div zero | 4 | test_zero_cost_handling | test_efficiency.py | ⏳ Pending |
| Higher efficiency wins | 4 | test_efficiency_ranking | test_efficiency.py | ⏳ Pending |
| Strategic bonus | 4 | test_strategic_type_bonus | test_efficiency.py | ⏳ Pending |
| Knapsack selection | 5 | test_knapsack_optimization | test_allocation.py | ⏳ Pending |
| Budget never exceeded | 5 | test_budget_never_exceeded | test_allocation.py | ⏳ Pending |
| Bundle beats single | 5 | test_bundler_preference | test_allocation.py | ⏳ Pending |
| Required types first | 5 | test_required_type_priority | test_allocation.py | ⏳ Pending |
| Opportunity cost calculation | 5 | test_opportunity_cost_positive | test_opportunity_cost.py | ⏳ Pending |
| Best alternative selection | 5 | test_best_alternative_identification | test_opportunity_cost.py | ⏳ Pending |
| Strategic impact levels | 5 | test_strategic_impact_assessment | test_opportunity_cost.py | ⏳ Pending |

**Total Rules:** 24
**Tests Required:** 24
**Coverage Target:** 100%

---

## Layer 1: Feasibility Gate Tests

### Test: `test_reject_exceeds_budget`

**Rule:** Proposals with cost > remaining_budget are rejected.

**Input:**
```python
proposal = MissionProposal(estimated_cost=1500)
constraints = ResourceConstraints(budget_remaining=1000)
```

**Expected:**
```python
eligible == False
reason contains "budget"
```

**File:** `tests/layer13/test_feasibility.py`

---

### Test: `test_reject_low_confidence`

**Rule:** Proposals with confidence < threshold are rejected.

**Input:**
```python
federation = FederationResult(confidence=0.3)
constraints = ResourceConstraints(min_confidence_threshold=0.5)
```

**Expected:**
```python
eligible == False
reason contains "confidence"
```

**File:** `tests/layer13/test_feasibility.py`

---

### Test: `test_reject_impossible_deadline`

**Rule:** Proposals with deadline < execution time are rejected.

**Input:**
```python
proposal = MissionProposal(
    estimated_duration_seconds=3600,
    deadline=datetime.utcnow() + timedelta(minutes=30)
)
```

**Expected:**
```python
eligible == False
reason contains "deadline"
```

**File:** `tests/layer13/test_feasibility.py`

---

### Test: `test_reject_missing_prerequisites`

**Rule:** Proposals with incomplete prerequisites are queued.

**Input:**
```python
proposal = MissionProposal(
    prerequisites=["mission_incomplete"]
)
```

**Expected:**
```python
eligible == False
reason contains "prerequisite"
```

**File:** `tests/layer13/test_feasibility.py`

---

### Test: `test_reject_forbidden_type`

**Rule:** Proposals of forbidden types are rejected.

**Input:**
```python
proposal = MissionProposal(mission_type="forbidden_type")
constraints = ResourceConstraints(
    forbidden_mission_types=["forbidden_type"]
)
```

**Expected:**
```python
eligible == False
reason contains "forbidden"
```

**File:** `tests/layer13/test_feasibility.py`

---

## Layer 2: Base Value Tests

### Test: `test_base_value_range`

**Rule:** Base value must be in [0.0, 1.0].

**Input:**
```python
proposal = MissionProposal(
    user_value=0.8,
    urgency=0.5,
    strategic_fit=0.7
)
```

**Expected:**
```python
0.0 <= base_value <= 1.0
```

**File:** `tests/layer13/test_base_value.py`

---

### Test: `test_user_value_contribution`

**Rule:** User value contributes 60% to base value.

**Input:**
```python
# Vary user_value, keep others constant
p1 = MissionProposal(user_value=1.0, urgency=0.5, strategic_fit=0.5)
p2 = MissionProposal(user_value=0.0, urgency=0.5, strategic_fit=0.5)
```

**Expected:**
```python
base_value(p1) - base_value(p2) ≈ 0.6
```

**File:** `tests/layer13/test_base_value.py`

---

### Test: `test_urgency_contribution`

**Rule:** Urgency contributes 30% to base value.

**Input:**
```python
p1 = MissionProposal(user_value=0.5, urgency=1.0, strategic_fit=0.5)
p2 = MissionProposal(user_value=0.5, urgency=0.0, strategic_fit=0.5)
```

**Expected:**
```python
base_value(p1) - base_value(p2) ≈ 0.3
```

**File:** `tests/layer13/test_base_value.py`

---

### Test: `test_strategic_fit_contribution`

**Rule:** Strategic fit contributes 10% to base value.

**Input:**
```python
p1 = MissionProposal(user_value=0.5, urgency=0.5, strategic_fit=1.0)
p2 = MissionProposal(user_value=0.5, urgency=0.5, strategic_fit=0.0)
```

**Expected:**
```python
base_value(p1) - base_value(p2) ≈ 0.1
```

**File:** `tests/layer13/test_base_value.py`

---

## Layer 3: Execution Modifier Tests

### Test: `test_confidence_increases_modifier`

**Rule:** Higher confidence increases execution modifier.

**Input:**
```python
federation_high = FederationResult(confidence=0.9)
federation_low = FederationResult(confidence=0.6)
```

**Expected:**
```python
modifier(high_confidence) > modifier(low_confidence)
modifier > 1.0
```

**File:** `tests/layer13/test_execution_modifier.py`

---

### Test: `test_low_confidence_decreases_modifier`

**Rule:** Low confidence decreases execution modifier.

**Input:**
```python
federation = FederationResult(confidence=0.3)
```

**Expected:**
```python
modifier < 1.0
modifier >= 0.5
```

**File:** `tests/layer13/test_execution_modifier.py`

---

### Test: `test_multi_node_bonus`

**Rule:** More participating nodes increases modifier.

**Input:**
```python
f1 = FederationResult(confidence=0.8, participating_nodes=5)
f2 = FederationResult(confidence=0.8, participating_nodes=15)
```

**Expected:**
```python
modifier(f2) > modifier(f1)
```

**File:** `tests/layer13/test_execution_modifier.py`

---

### Test: `test_historical_performance_adjustment`

**Rule:** Good historical performance increases modifier.

**Input:**
```python
context = EvaluationContext(
    historical_outcomes={"test_type": 0.8}
)
```

**Expected:**
```python
modifier_with_history > modifier_without_history
```

**File:** `tests/layer13/test_execution_modifier.py`

---

## Layer 4: Efficiency Tests

### Test: `test_efficiency_formula`

**Rule:** Efficiency = quality_adjusted_value / (cost + epsilon).

**Input:**
```python
score = EconomicScore(quality_adjusted_value=0.8)
cost = 400.0
```

**Expected:**
```python
efficiency ≈ 0.8 / 400.01
```

**File:** `tests/layer13/test_efficiency.py`

---

### Test: `test_zero_cost_handling`

**Rule:** Cost epsilon prevents division by zero.

**Input:**
```python
score = EconomicScore(quality_adjusted_value=0.5)
cost = 0.0
```

**Expected:**
```python
efficiency is finite
efficiency == 0.5 / epsilon
```

**File:** `tests/layer13/test_efficiency.py`

---

### Test: `test_efficiency_ranking`

**Rule:** Higher efficiency missions ranked first.

**Input:**
```python
m1 = EconomicScore(quality_adjusted_value=0.8, efficiency=0.001)
m2 = EconomicScore(quality_adjusted_value=0.5, efficiency=0.005)
```

**Expected:**
```python
ranked[0] == m2  # Higher efficiency first
```

**File:** `tests/layer13/test_efficiency.py`

---

### Test: `test_strategic_type_bonus`

**Rule:** Required mission types receive efficiency bonus.

**Input:**
```python
required_types = ["security"]
proposal = MissionProposal(mission_type="security")
```

**Expected:**
```python
score_with_bonus.efficiency > score_without_bonus.efficiency
score.strategic_bonus > 0
```

**File:** `tests/layer13/test_efficiency.py`

---

## Layer 5: Allocation Tests

### Test: `test_knapsack_optimization`

**Rule:** Knapsack selects optimal mission set.

**Input:**
```python
budget = 100
missions = [
    (value=50, cost=60),  # efficiency 0.833
    (value=40, cost=40),  # efficiency 1.0
    (value=30, cost=30),  # efficiency 1.0
]
```

**Expected:**
```python
funded == ["m2", "m3"]  # Both efficiency 1.0, fit in budget
total_cost == 70
total_value == 70
```

**File:** `tests/layer13/test_allocation.py`

---

### Test: `test_budget_never_exceeded`

**Rule:** Budget never exceeded (100 runs).

**Input:**
```python
for _ in range(100):
    proposals = generate_random_proposals()
    result = allocate(proposals, budget)
```

**Expected:**
```python
all(result.funded_total_cost <= budget for result in results)
```

**File:** `tests/layer13/test_allocation.py`

---

### Test: `test_bundle_preference`

**Rule:** Bundle of missions beats single high-value mission.

**Input:**
```python
budget = 100
A = MissionProposal(value=80, cost=90)   # efficiency 0.89
B = MissionProposal(value=50, cost=50)   # efficiency 1.0
C = MissionProposal(value=40, cost=40)   # efficiency 1.0
```

**Expected:**
```python
funded == ["B", "C"]  # Bundle beats single
total_value == 90 > 80
```

**File:** `tests/layer13/test_allocation.py`

---

### Test: `test_required_type_priority`

**Rule:** Required mission types funded first.

**Input:**
```python
required_types = ["security"]
security = MissionProposal(type="security", efficiency=0.5, cost=300)
feature = MissionProposal(type="feature", efficiency=0.8, cost=200)
budget = 400
```

**Expected:**
```python
"security" in funded  # Lower efficiency but required
```

**File:** `tests/layer13/test_allocation.py`

---

## Layer 5: Opportunity Cost Tests

### Test: `test_opportunity_cost_positive`

**Rule:** Opportunity cost is always non-negative.

**Input:**
```python
rejected = EconomicScore(quality_adjusted_value=0.8)
accepted = EconomicScore(quality_adjusted_value=0.6)
```

**Expected:**
```python
opportunity_cost >= 0
```

**File:** `tests/layer13/test_opportunity_cost.py`

---

### Test: `test_best_alternative_identification`

**Rule:** Best accepted alternative identified correctly.

**Input:**
```python
rejected = EconomicScore(quality_adjusted_value=0.8, mission_type="A")
accepted = [
    EconomicScore(quality_adjusted_value=0.7, mission_type="B"),
    EconomicScore(quality_adjusted_value=0.5, mission_type="A"),  # Same type
]
```

**Expected:**
```python
best_alternative.mission_type == "A"  # Same type preferred
```

**File:** `tests/layer13/test_opportunity_cost.py`

---

### Test: `test_strategic_impact_assessment`

**Rule:** Strategic impact correctly assessed.

**Input:**
```python
high_cost_ratio = 0.3  # > 0.1
low_cost_ratio = 0.05  # < 0.1
high_value_cost = 0.6  # > 0.5
```

**Expected:**
```python
high_cost_ratio.impact in ["medium", "high"]
low_cost_ratio.impact == "low"
high_value_cost.impact == "high"
```

**File:** `tests/layer13/test_opportunity_cost.py`

---

## Critical Bug Prevention Tests

### Bug: Cheap Task Loop

**Test:** `test_cheap_task_loop_prevented`

**Description:** System must not prefer infinite tiny tasks over big valuable missions.

**Input:**
```python
# Tiny task with high efficiency
tiny = MissionProposal(value=20, cost=1)  # efficiency 20

# Big mission with lower efficiency
big = MissionProposal(value=100, cost=50)  # efficiency 2

budget = 60
```

**Expected (correct behavior):**
```python
# Knapsack should fund both if possible
funded == ["tiny", "big"]  # Total cost 51, value 120
# NOT just tiny tasks
```

**Prevention:** Bundle-based allocation prevents this.

**File:** `tests/layer13/test_critical_bugs.py`

---

### Bug: Cost Domination

**Test:** `test_cost_does_not_dominate`

**Description:** Low cost shouldn't be the only factor.

**Input:**
```python
low_value_low_cost = MissionProposal(value=0.3, cost=10)
high_value_high_cost = MissionProposal(value=0.9, cost=100)
budget = 100
```

**Expected:**
```python
# High value should win despite higher cost
funded == ["high_value_high_cost"]
# Because: efficiency 0.009 > 0.03
```

**Prevention:** Value + efficiency combined.

**File:** `tests/layer13/test_critical_bugs.py`

---

### Bug: Urgency Overpowering Value

**Test:** `test_urgency_does_not_overpower_value`

**Description:** High urgency shouldn't overwhelm high value.

**Input:**
```python
high_value_low_urgency = MissionProposal(value=0.9, urgency=0.2)
low_value_high_urgency = MissionProposal(value=0.4, urgency=0.95)
```

**Expected:**
```python
# High value should have higher base value
base_value(high_value_low_urgency) > base_value(low_value_high_urgency)
# Because: 0.9*0.6 + 0.2*0.3 = 0.6 > 0.4*0.6 + 0.95*0.3 = 0.525
```

**Prevention:** Urgency is only 30% of base value.

**File:** `tests/layer13/test_critical_bugs.py`

---

## Coverage Requirements

### Statement Coverage Target: 85%

### Branch Coverage Target: 80%

### Critical Path Coverage: 100%

All scoring rules must have tests. No exceptions.

---

## Test Execution Order

```bash
# 1. Unit tests (fast)
pytest tests/layer13/unit/ -v

# 2. Scoring tests (this matrix)
pytest tests/layer13/scoring/ -v

# 3. Scenario tests
pytest tests/layer13/scenarios/ -v

# 4. Critical bug tests
pytest tests/layer13/critical_bugs/ -v

# 5. Full validation suite
pytest tests/layer13/ -v --coverage
```

---

## Pre-Implementation Checklist

Before implementing engines:

- [ ] Every rule has a test case
- [ ] Tests are written (can fail initially)
- [ ] Test matrix is complete
- [ ] Critical bug tests defined
- [ ] Coverage thresholds defined

---

## Pre-Merge Checklist

Before merging implementation:

- [ ] All tests passing
- [ ] Coverage targets met
- [ ] No critical bugs
- [ ] Performance benchmarks met
- [ ] Documentation updated

---

**Governor Status:** SAFETY CHECKPOINT ESTABLISHED
**Next:** Agent 1 implements engines with tests driving development
**Guardrail:** Architecture models cannot be modified without governor approval
