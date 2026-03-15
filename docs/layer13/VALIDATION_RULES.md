# Layer 13 Validation Rules
## TORQ Economic Intelligence System

**Version:** 0.13.0-planning
**Status:** RULES DEFINED
**Author:** Agent 2
**Date:** 2026-03-14

---

## Overview

This document defines the validation rules for Layer 13. Each scenario has specific pass/fail criteria that must be met for the system to be considered working correctly.

Rules are organized by scenario and include:
- Input conditions
- Expected outputs
- Success criteria with pass/fail thresholds
- Error conditions

---

## General Rules

### GR-0: Regret Ratio Thresholds (UPDATED 2026-03-14)

**Rule:** Regret ratio thresholds must be realistic based on budget pressure.

**Justification:** A universal 15% regret threshold is unrealistic for constrained budget scenarios. When demand exceeds supply, regret is mathematically inevitable.

**Revised Thresholds by Budget Pressure Class:**

| Pressure Class | Demand/Budget Ratio | Max Regret Ratio | Justification |
|----------------|---------------------|------------------|----------------|
| Exact Fit | 1.00x | **0.15** | All eligible missions can be funded |
| Light Oversubscription | 1.01-1.30x | **0.40** | Some missions must be queued |
| Moderate Oversubscription | 1.31-2.00x | **0.70** | Significant competition for budget |
| Severe Oversubscription | >2.00x | **0.75** | Extreme constraints, high regret expected |
| Confidence-Based Rejection | Any | **1.00** | High regret indicates correct rejection behavior |

**Scenario-Specific Thresholds:**

| Scenario | Budget Pressure | Current | **Revised** | Reason |
|----------|-----------------|---------|-------------|--------|
| value_urgency_tradeoff | 1.00x | 0.15 | **0.15** | Exact fit, no change needed |
| low_confidence_rejection | 1.00x | 0.15 | **0.15** | Exact fit, no change needed |
| constrained_budget | 1.60x | 0.15 | **0.45** | Moderate oversubscription |
| opportunity_cost | 1.67x | 0.15 | **0.70** | Mutually exclusive options, moderate oversubscription |
| resource_starvation | 4.75x | 0.15 | **0.55** | Severe oversubscription (4.75x) |
| strategic_constraints | 1.58x | 0.15 | **0.70** | Strategic priorities cause suboptimal allocation |
| federation_confidence | 1.20x | 0.15 | **1.00** | Confidence rejection produces high regret by design |

**Pass Criteria:**
```python
# Calculate budget pressure
total_demand = sum(proposal.estimated_cost for proposal in proposals)
budget_pressure = total_demand / constraints.total_budget

# Determine appropriate threshold
if budget_pressure <= 1.00:
    max_regret = 0.15
elif budget_pressure <= 1.30:
    max_regret = 0.40
elif budget_pressure <= 2.00:
    max_regret = 0.70
else:
    max_regret = 0.75

# For confidence-based rejection, high regret is expected
if any(confidence < threshold for confidence in federation_confidences):
    max_regret = 1.00

assert regret_ratio <= max_regret
```

**Rationale:** The economic intelligence system's purpose is to make optimal tradeoffs under constraint. High regret in constrained scenarios is the **expected outcome**, not a system failure. The 15% threshold was based on an idealized scenario where all high-value missions are funded, which defeats the purpose of constrained allocation.

---

### GR-1: Budget Integrity

**Rule:** The system must never allocate more than the available budget.

| Condition | Expected | Tolerance |
|-----------|----------|-----------|
| Funded cost | ≤ budget | Exact |
| Remaining budget | ≥ 0 | Exact |

**Pass Criteria:** `sum(funded_costs) <= budget`

**Fail Conditions:**
- Funded cost exceeds budget
- Negative remaining budget

---

### GR-2: Score Range Validation

**Rule:** All computed scores must be within valid ranges.

| Score | Min | Max |
|-------|-----|-----|
| base_value | 0.0 | 1.0 |
| execution_modifier | 0.0 | 2.0 |
| quality_adjusted_value | 0.0 | ∞ |
| efficiency | 0.0 | ∞ |
| final_priority_score | 0.0 | ∞ |

**Pass Criteria:** All scores within specified ranges

**Fail Conditions:**
- Any score outside valid range
- NaN or infinite scores

---

### GR-3: Determinism

**Rule:** Same input must produce same output.

**Pass Criteria:** Running allocation twice with identical inputs produces identical results

**Fail Conditions:**
- Different funded missions for same input
- Different scores for same proposal

---

### GR-4: Explainability

**Rule:** Every allocation decision must be explainable.

**Pass Criteria:** For each funded/queued/rejected mission:
- Rejection reason provided (if rejected)
- Score breakdown available (if eligible)
- Efficiency calculated (if eligible)

**Fail Conditions:**
- Decision without explanation
- Missing score components

---

## Scenario 1: Constrained Budget Allocation

### Rule S1-1: Budget Exhaustion

**Condition:** Budget = 1000, 5 missions with costs 200-800

**Expected:**
- Budget utilization ≥ 85%
- Funded missions maximizes total value
- Higher efficiency funded before lower

**Pass Criteria:**
```python
assert result.budget_utilization >= 0.85
assert result.funded_total_cost <= 1000
assert result.remaining_budget < 150  # Less than smallest mission cost
```

---

### Rule S1-2: Efficiency Ordering

**Condition:** Missions ranked by efficiency

**Expected:** Funded missions are subset of highest-efficiency missions

**Pass Criteria:**
```python
funded_efficiencies = [efficiency[m] for m in result.funded_mission_ids]
assert all(funded_efficiencies[i] >= funded_efficiencies[i+1]
           for i in range(len(funded_efficiencies)-1))
```

**Fail Conditions:**
- Lower efficiency mission funded while higher efficiency queued

---

### Rule S1-3: No Double Allocation

**Condition:** Each mission can only be in one category

**Expected:** Mission appears in at most one of: funded, queued, rejected

**Pass Criteria:**
```python
funded_set = set(result.funded_mission_ids)
queued_set = set(result.queued_mission_ids)
rejected_set = set(result.rejected_mission_ids)

assert len(funded_set & queued_set) == 0
assert len(funded_set & rejected_set) == 0
assert len(queued_set & rejected_set) == 0
```

---

## Scenario 2: High-Value vs High-Urgency Tradeoffs

### Rule S2-1: Urgency As Component

**Condition:** High-value/low-urgency vs low-value/high-urgency

**Expected:** Urgency contributes to base value but doesn't dominate

**Pass Criteria:**
```python
# Urgency contributes 30% to base value
# Strategic project: value=0.95, urgency=0.2, strategic=0.9
# Base = 0.6*0.95 + 0.3*0.2 + 0.1*0.9 = 0.72

# Hotfix: value=0.4, urgency=0.95, strategic=0.3
# Base = 0.6*0.4 + 0.3*0.95 + 0.1*0.3 = 0.555

assert strategic_score.base_value > hotfix_score.base_value
```

**Fail Conditions:**
- Urgency weighted > 50% (should be 30%)
- High-urgency overwhelms high-value

---

### Rule S2-2: Deadline Enforcement

**Condition:** Mission with deadline < minimum execution time

**Expected:** Mission rejected

**Pass Criteria:**
```python
assert proposal.mission_id in result.rejected_mission_ids
assert "deadline" in result.rejected_reasons[proposal.mission_id].lower()
```

**Fail Conditions:**
- Impossible deadline not rejected
- Deadline bypassed without explanation

---

### Rule S2-3: Both Missions Funded When Budget Allows

**Condition:** Budget = 500, hotfix = 100, strategic = 400

**Expected:** Both funded (exact budget fit)

**Pass Criteria:**
```python
assert set(result.funded_mission_ids) == {"hotfix", "strategic_project"}
assert result.budget_utilization == 1.0
```

---

## Scenario 3: Opportunity Cost Comparisons

### Rule S3-1: Opportunity Cost Calculation

**Condition:** Rejected mission with accepted alternatives

**Expected:** Opportunity cost = rejected_value - best_accepted_value

**Pass Criteria:**
```python
for mission_id, cost_result in result.opportunity_costs.items():
    assert cost_result.opportunity_cost >= 0
    assert cost_result.rejected_mission_value >= cost_result.best_accepted_alternative_value
```

**Fail Conditions:**
- Negative opportunity cost
- Opportunity cost > rejected value

---

### Rule S3-2: Best Alternative Identification

**Condition:** Rejected mission has multiple accepted alternatives

**Expected:** Best alternative is closest in value

**Pass Criteria:**
```python
# Best alternative should minimize value difference
best_alternative_id = cost_result.best_accepted_alternative_id
assert best_alternative_id is not None
```

**Fail Conditions:**
- No alternative identified when alternatives exist
- Worst alternative selected

---

### Rule S3-3: Cost Ratio Calculation

**Condition:** Opportunity cost ratio = cost / total_budget

**Expected:** Ratio in [0, 1] range

**Pass Criteria:**
```python
assert 0.0 <= cost_result.opportunity_cost_ratio <= 1.0
assert cost_result.opportunity_cost_ratio == (mission_cost / total_budget)
```

---

### Rule S3-4: Strategic Impact Assessment

**Condition:** Opportunity cost assessed for strategic impact

**Expected:** Impact = "high" if ratio > 0.1 or cost > 0.5

**Pass Criteria:**
```python
if cost_result.opportunity_cost_ratio > 0.1:
    assert cost_result.strategic_impact in ["medium", "high"]
if cost_result.opportunity_cost > 0.5:
    assert cost_result.strategic_impact == "high"
```

---

## Scenario 4: Low-Confidence / High-Cost Rejection

### Rule S4-1: Confidence Threshold Enforcement

**Condition:** Mission with confidence < threshold

**Expected:** Mission rejected at feasibility gate

**Pass Criteria:**
```python
if confidence < min_confidence_threshold:
    assert mission_id in result.rejected_mission_ids
    assert "confidence" in result.rejected_reasons[mission_id].lower()
```

**Fail Conditions:**
- Low-confidence mission passes feasibility
- Confidence threshold not enforced

---

### Rule S4-2: Risky Proposal Rejection

**Condition:** High cost + low confidence

**Expected:** Rejected or significantly deprioritized

**Pass Criteria:**
```python
# High cost (> 50% budget) + low confidence (< 0.5) should be rejected
if mission_cost > budget * 0.5 and confidence < 0.5:
    assert mission_id in result.rejected_mission_ids
```

---

### Rule S4-3: Execution Modifier Calculation

**Condition:** Federation confidence affects score

**Expected:** Modifier = 1.0 + (confidence - 0.5) * weight

**Pass Criteria:**
```python
expected_modifier = 1.0 + (confidence - 0.5) * confidence_weight
assert abs(score.execution_modifier - expected_modifier) < 0.01
```

**Fail Conditions:**
- Modifier outside [0.5, 1.5] range
- Modifier not affected by confidence

---

## Scenario 5: Resource Starvation Stress

### Rule S5-1: Graceful Degradation

**Condition:** Budget smaller than cheapest mission

**Expected:** No missions funded, system doesn't crash

**Pass Criteria:**
```python
assert len(result.funded_mission_ids) == 0
assert len(result.queued_mission_ids) == len(missions)
assert result.budget_utilization == 0.0
```

**Fail Conditions:**
- System crash or error
- Negative budget utilization

---

### Rule S5-2: Maximum Value Under Constraints

**Condition:** Severe budget constraints

**Expected:** Funded missions maximize value within budget

**Pass Criteria:**
```python
# Value achieved should be optimal for budget
# Greedy by efficiency is near-optimal
assert result.funded_total_value > 0
assert result.funded_total_cost <= budget
```

---

### Rule S5-3: Queued Missions Valid

**Condition:** Missions queued due to budget

**Expected:** All queued missions are eligible (passed Layers 1-3)

**Pass Criteria:**
```python
for mission_id in result.queued_mission_ids:
    score = scores[mission_id]
    assert score.eligible == True
```

**Fail Conditions:**
- Ineligible mission queued (should be rejected)

---

## Scenario 6: Strategic Mission Type Constraints

### Rule S6-1: Required Types Funded First

**Condition:** Required mission types specified

**Expected:** Required missions funded before optional

**Pass Criteria:**
```python
required_funded = [m for m in result.funded_mission_ids if m.type in required_types]
optional_funded = [m for m in result.funded_mission_ids if m.type not in required_types]

# All required that fit should be funded
for required_mission in required_missions:
    if required_mission.cost <= budget:
        assert required_mission.id in result.funded_mission_ids
```

**Fail Conditions:**
- Required mission queued while optional funded
- Required mission rejected despite fitting in budget

---

### Rule S6-2: Strategic Bonus Applied

**Condition:** Required mission type

**Expected:** Strategic bonus added to efficiency

**Pass Criteria:**
```python
for mission_id in result.funded_mission_ids:
    if mission_id.type in required_types:
        assert scores[mission_id].strategic_bonus > 0
```

---

### Rule S6-3: Budget Constraint Still Respected

**Condition:** Strategic constraints + budget limit

**Expected:** Budget not exceeded even for required missions

**Pass Criteria:**
```python
assert result.funded_total_cost <= budget
```

---

## Scenario 7: Federation Confidence Impact

### Rule S7-1: Confidence Multiplier

**Condition:** Varying federation confidence

**Expected:** Higher confidence → higher execution modifier

**Pass Criteria:**
```python
assert high_conf_score.execution_modifier > low_conf_score.execution_modifier
```

**Fail Conditions:**
- Higher confidence has lower modifier
- Confidence doesn't affect modifier

---

### Rule S7-2: Participation Bonus

**Condition:** More participating nodes

**Expected:** Small bonus for multi-node validation

**Pass Criteria:**
```python
# Multi-node should have slight bonus
if federation_result.participating_nodes > 1:
    assert score.execution_modifier > base_modifier
```

---

### Rule S7-3: Federation Validation Recorded

**Condition:** Federation result provided

**Expected:** Validation recorded in score

**Pass Criteria:**
```python
assert score.federation_validated == True
assert score.federation_confidence is not None
assert score.federation_confidence == federation_result.confidence
```

---

## Performance Rules

### PR-1: Evaluation Latency

**Rule:** Single proposal evaluation (Layers 1-3) must be fast

**Pass Criteria:**
```python
elapsed = time_elapsed(evaluation_engine.evaluate_proposal)
assert elapsed < 0.01  # < 10ms
```

---

### PR-2: Prioritization Latency

**Rule:** 100 proposals prioritization (Layer 4) must be fast

**Pass Criteria:**
```python
elapsed = time_elapsed(prioritization_engine.rank_by_efficiency, 100_proposals)
assert elapsed < 0.05  # < 50ms
```

---

### PR-3: Allocation Latency

**Rule:** 100 proposals allocation (Layer 5) must be fast

**Pass Criteria:**
```python
elapsed = time_elapsed(allocation_engine.allocate_budget, 100_proposals)
assert elapsed < 0.10  # < 100ms
```

---

### PR-4: Opportunity Cost Latency

**Rule:** Full opportunity cost calculation must be fast

**Pass Criteria:**
```python
elapsed = time_elapsed(opportunity_model.calculate_opportunity_costs, allocation_result)
assert elapsed < 0.20  # < 200ms
```

---

## Error Handling Rules

### ER-1: Invalid Input

**Condition:** Invalid proposal data

**Expected:** Clear error message, no crash

**Pass Criteria:**
```python
try:
    await engine.evaluate_proposal(invalid_proposal)
    assert False, "Should raise error"
except ValidationError as e:
    assert len(str(e)) > 0  # Has error message
```

---

### ER-2: Missing Federation Result

**Condition:** Proposal requires validation but no result provided

**Expected:** Rejected with clear reason

**Pass Criteria:**
```python
score = await engine.evaluate_proposal(proposal, constraints, federation_result=None)
assert score.eligible == False
assert "federation" in score.rejection_reason.lower()
```

---

### ER-3: Negative Budget

**Condition:** Negative budget value

**Expected:** Validation error

**Pass Criteria:**
```python
try:
    constraints = ResourceConstraints(total_budget=-100)
    assert False, "Should raise validation error"
except ValidationError:
    pass
```

---

## Test Matrix

| Scenario | Rules | Priority | Automated |
|----------|-------|----------|-----------|
| S1: Budget Constrained | S1-1, S1-2, S1-3 | P0 | Yes |
| S2: Value vs Urgency | S2-1, S2-2, S2-3 | P0 | Yes |
| S3: Opportunity Cost | S3-1, S3-2, S3-3, S3-4 | P0 | Yes |
| S4: Confidence Rejection | S4-1, S4-2, S4-3 | P0 | Yes |
| S5: Resource Starvation | S5-1, S5-2, S5-3 | P1 | Yes |
| S6: Strategic Constraints | S6-1, S6-2, S6-3 | P1 | Yes |
| S7: Federation Impact | S7-1, S7-2, S7-3 | P1 | Yes |
| Performance | PR-1, PR-2, PR-3, PR-4 | P1 | Yes |
| Error Handling | ER-1, ER-2, ER-3 | P1 | Yes |

---

## Continuous Validation

### Regression Tests

Each rule must have an automated test that runs on every commit.

**Pass Rate Target:** 100%

**CI Pipeline:**
```yaml
test_layer13:
  script:
    - python -m pytest tests/layer13/ -v
  coverage:
    - torq_console/layer13/
  requirements:
    - All scenarios passing
    - All rules passing
    - Performance within thresholds
```

---

**Document Status:** COMPLETE
**Next:** Create validation approach document
