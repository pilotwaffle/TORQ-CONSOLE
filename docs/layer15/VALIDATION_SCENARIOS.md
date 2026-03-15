# Layer 15 Validation Scenarios
## Strategic Foresight Test Cases

**Version:** 0.15.0-planning
**Status:** DRAFT
**Author:** Agent 2
**Date:** 2026-03-14

---

## Overview

This document defines validation scenarios for Layer 15 strategic foresight. Each scenario tests a specific aspect of strategic evaluation.

**Total Scenarios:** 8
**Coverage:** All 5 engines + 3 integration scenarios

---

## Scenario Definitions

### Scenario 1: Short-Term Win, Long-Term Loss

**Purpose:** Detect decisions that optimize for the present at the expense of the future.

**Setup:**
- Decision A increases short-term efficiency by 30%
- Decision A reduces long-term resilience by 50%
- Second-order consequences include system fragility
- Third-order consequence: mission failure under stress

**Expected Results:**
```
SecondOrderConsequenceAnalyzer:
  flags_future_harm == True
  consequences[order==2].impact < -0.3
  total_impact < -0.5

HorizonAlignmentEngine:
  short_term_score == 0.85 (high)
  long_term_score == 0.35 (low)
  coherence == 0.45 (poor)
  misalignment_detected == True

StrategicScore < 0.50 (strategically weak)
Recommendation == REDESIGN
Reason == "Short-term gain undermines long-term viability"
```

**Test Data:**
```python
decision = DecisionPacket(
    decision_id="DEC_001",
    action="optimize_efficiency",
    short_term_benefit=0.30,
    long_term_cost=0.50,
    time_to_impact=timedelta(days=7),
)

consequences = [
    Consequence(
        order=1,
        description="Efficiency improved",
        impact=0.30,
        probability=0.95,
        time_delay=timedelta(days=7)
    ),
    Consequence(
        order=2,
        description="Resilience reduced",
        impact=-0.50,
        probability=0.70,
        time_delay=timedelta(days=90)
    ),
    Consequence(
        order=3,
        description="Mission failure risk increased",
        impact=-0.60,
        probability=0.40,
        time_delay=timedelta(days=180)
    ),
]
```

**Validation Checks:**
1. ✅ Second-order harm detected
2. ✅ Horizon misalignment flagged
3. ✅ Strategic score < 0.50
4. ✅ Recommendation is REDESIGN
5. ✅ Reason includes long-term impact

---

### Scenario 2: Reversible vs Irreversible Decision

**Purpose:** Ensure reversibility is valued when paths are similar.

**Setup:**
- Path A: Reversible, value = 0.75, optionality = 0.80
- Path B: Irreversible, value = 0.80, optionality = 0.20
- Both pass Layer 14 legitimacy check

**Expected Results:**
```
OptionalityPreservationEngine:
  score(Path A) > score(Path B)
  retention_rate(Path A) == 0.80
  retention_rate(Path B) == 0.20
  reversibility(Path A) == REVERSIBLE
  reversibility(Path B) == IRREVERSIBLE
  lock_in_risk(Path B) >= HIGH

StrategicBranchComparator:
  recommended_branch == "Path A"
  ranking["Path A"].rank < ranking["Path B"].rank
  expected_value_difference < 0.10

Recommendation == Path A (reversible)
Reason == "Preserves future options despite slightly lower value"
```

**Test Data:**
```python
path_a = DecisionBranch(
    branch_id="A",
    decision=DecisionPacket(
        reversibility=Reversibility.REVERSIBLE,
        value=0.75
    ),
    scenarios=FutureScenarios(
        optionality_score=0.80
    )
)

path_b = DecisionBranch(
    branch_id="B",
    decision=DecisionPacket(
        reversibility=Reversibility.IRREVERSIBLE,
        value=0.80
    ),
    scenarios=FutureScenarios(
        optionality_score=0.20
    )
)
```

**Validation Checks:**
1. ✅ Reversible path preferred
2. ✅ Optionality score difference detected
3. ✅ Lock-in risk assessed for irreversible path
4. ✅ Recommendation favors reversibility
5. ✅ Value difference noted in reasoning

---

### Scenario 3: Legitimate but Strategically Weak

**Purpose:** Ensure Layer 15 can downscore Layer 14-approved decisions.

**Setup:**
- Decision passes Layer 14 (legitimacy = 0.80)
- Decision creates future fragility
- Optionality significantly reduced
- Long-term mission objectives compromised

**Expected Results:**
```
Layer14Input:
  legitimacy_score == 0.80
  passes == True

Layer15Evaluation:
  strategic_score == 0.45
  band == StrategicBand.WEAK
  recommendation == REDESIGN

ComponentScores:
  long_term_value == 0.40
  resilience == 0.35
  optionality == 0.30
  lock_in_risk_factor == 0.60

Recommendation == REDESIGN
Reason == "Creates future lock-in and fragility"
```

**Test Data:**
```python
layer14_output = Layer14Output(
    legitimacy_score=0.80,
    passes=True,
    violations=[],
    funded_missions=["m1", "m2"]
)

layer15_input = Layer15Input(
    layer14_output=layer14_output,
    decision=DecisionPacket(
        decision_id="DEC_003",
        creates_lock_in=True,
        optionality_retention=0.30
    )
)
```

**Validation Checks:**
1. ✅ Layer 14 passes independently
2. ✅ Layer 15 detects strategic weakness
3. ✅ Strategic score below threshold
4. ✅ Recommendation is REDESIGN
5. ✅ Layer 14 not overridden (respectful)

---

### Scenario 4: Multi-Branch Uncertainty

**Purpose:** Handle competing futures with proper risk assessment.

**Setup:**
- 3 plausible futures with different probabilities
- Optimistic: value = 0.90, probability = 0.30
- Baseline: value = 0.60, probability = 0.50
- Pessimistic: value = 0.30, probability = 0.20

**Expected Results:**
```
StrategicBranchComparator:
  rankings generated for all branches
  confidence_intervals calculated:
    "optimistic": (0.75, 0.98)
    "baseline": (0.55, 0.65)
    "pessimistic": (0.20, 0.40)

  risk_adjusted_values calculated
  recommended_branch may not be highest nominal value

StrategicScore:
  uncertainty_acknowledged == True
  confidence_intervals_included == True
  recommendation != None
```

**Test Data:**
```python
branches = [
    DecisionBranch(
        branch_id="optimistic",
        scenarios=FutureScenarios(
            expected_value=0.90,
            confidence_interval=(0.75, 0.98)
        )
    ),
    DecisionBranch(
        branch_id="baseline",
        scenarios=FutureScenarios(
            expected_value=0.60,
            confidence_interval=(0.55, 0.65)
        )
    ),
    DecisionBranch(
        branch_id="pessimistic",
        scenarios=FutureScenarios(
            expected_value=0.30,
            confidence_interval=(0.20, 0.40)
        )
    ),
]
```

**Validation Checks:**
1. ✅ All branches evaluated
2. ✅ Risk-adjusted values calculated
3. ✅ Confidence intervals surfaced
4. ✅ Recommendation includes uncertainty
5. ✅ Most probable ≠ necessarily recommended

---

### Scenario 5: Forecast Calibration

**Purpose:** Track and improve projection accuracy over time.

**Setup:**
- Historical projection from 30 days ago
- Actual outcome now available
- Compare predicted vs actual

**Expected Results:**
```
ScenarioProjectionEngine:
  historical_projection recovered

CalibrationLoop:
  foresight_accuracy calculated
  accuracy > threshold OR calibration triggered

Confidence Updates:
  if accuracy < confidence:
    confidence_reduced = True
  elif accuracy > confidence + margin:
    confidence_increased = True

AssumptionReliability:
  assumption_performance tracked
  unreliable_assumptions flagged
```

**Test Data:**
```python
historical_projection = ScenarioProjection(
    scenario_id="PROJ_001",
    created_at=datetime.utcnow() - timedelta(days=30),
    predictions={
        "mission_success_rate": 0.80,
        "resource_utilization": 0.75,
        "performance": 0.85
    },
    confidence=0.80
)

actual_outcome = SystemState(
    mission_success_rate=0.70,
    resource_utilization=0.80,
    performance=0.75
)
```

**Validation Checks:**
1. ✅ Foresight accuracy calculated
2. ✅ Confidence updated based on accuracy
3. ✅ Assumption reliability tracked
4. ✅ Calibration executed if needed
5. ✅ Future projections use updated calibration

---

### Scenario 6: Optionality Preservation

**Purpose:** Verify optionality is preserved and valued.

**Setup:**
- Current system has 10 viable future paths
- Decision being evaluated would eliminate 6 paths
- Remaining paths have lower average value

**Expected Results:**
```
OptionalityPreservationEngine:
  initial_paths == 10
  remaining_paths == 4
  retention_rate == 0.40

  lock_in_risk >= HIGH
  reversibility == DIFFICULT

OptionalityScore == 0.40 (low)

StrategicScore penalized:
  optionality component == 0.40
  penalty applied for low retention

Recommendation == AVOID or MITIGATE
```

**Test Data:**
```python
current_paths = [
    FuturePath(path_id=f"P{i}", feasibility=0.8, value=0.7+i*0.05)
    for i in range(10)
]

decision = DecisionPacket(
    decision_id="DEC_006",
    eliminates_paths=[f"P{i}" for i in range(4, 10)],
    remaining_paths=[f"P{i}" for i in range(4)]
)
```

**Validation Checks:**
1. ✅ Initial path count correct
2. ✅ Remaining path count calculated
3. ✅ Retention rate calculated
4. ✅ Lock-in risk assessed
5. ✅ Strategic score reflects optionality penalty

---

### Scenario 7: Horizon Coherence Check

**Purpose:** Ensure consistency across short, medium, long horizons.

**Setup:**
- Decision has excellent short-term outcomes
- Decision has poor long-term outcomes
- Decision has medium-term tradeoffs

**Expected Results:**
```
HorizonAlignmentEngine:
  short_term_score == 0.90 (excellent)
  medium_term_score == 0.55 (mixed)
  long_term_score == 0.35 (poor)

  coherence == 0.45 (poor)
  misalignment_detected == True
  flagged_issues contains "horizon_sacrifice"

StrategicScore:
  horizon_alignment penalty applied
  final_score < short_term_score

Recommendation includes warning about horizon misalignment
```

**Test Data:**
```python
scenario_projections = [
    ScenarioProjection(
        horizon=TimeHorizon.SHORT,
        expected_outcome=SystemState(performance=0.90)
    ),
    ScenarioProjection(
        horizon=TimeHorizon.MEDIUM,
        expected_outcome=SystemState(performance=0.60)
    ),
    ScenarioProjection(
        horizon=TimeHorizon.LONG,
        expected_outcome=SystemState(performance=0.40)
    ),
]
```

**Validation Checks:**
1. ✅ Per-horizon scores calculated
2. ✅ Coherence metric calculated
3. ✅ Misalignment detected
4. ✅ Strategic score penalizes misalignment
5. ✅ Recommendation includes warning

---

### Scenario 8: Strategic Regret Calculation

**Purpose:** Calculate and track strategic regret.

**Setup:**
- Path A was chosen (value = 0.70)
- Path B was not chosen (value = 0.85)
- Path B would have been better in hindsight

**Expected Results:**
```
StrategicBranchComparator:
  chosen_branch == "Path A"
  alternative_branches == ["Path B"]

  calculate_regret():
    chosen_value == 0.70
    best_alternative_value == 0.85
    strategic_regret == 0.15

Regret tracked:
  regret_score recorded
  accumulation monitored
  if accumulated_regret > threshold:
    trigger_process_review()
```

**Test Data:**
```python
chosen_branch = DecisionBranch(
    branch_id="A",
    scenarios=FutureScenarios(
        long_term_value=0.70
    )
)

rejected_branch = DecisionBranch(
    branch_id="B",
    scenarios=FutureScenarios(
        long_term_value=0.85
    )
)
```

**Validation Checks:**
1. ✅ Regret calculated correctly
2. ✅ Best alternative identified
3. ✅ Regret value is reasonable
4. ✅ Regret is tracked
5. ✅ Excessive regret triggers review

---

## Scenario Summary Table

| # | Scenario | Engine(s) Tested | Key Metric | Complexity |
|---|----------|-----------------|------------|------------|
| 1 | Short-Term Win / Long-Term Loss | All | Horizon coherence | Medium |
| 2 | Reversible vs Irreversible | Optionality | Optionality score | Low |
| 3 | Legitimate but Weak | All | Strategic score | Medium |
| 4 | Multi-Branch Uncertainty | Comparator | Risk-adjusted value | Medium |
| 5 | Forecast Calibration | Projection | Accuracy | High |
| 6 | Optionality Preservation | Optionality | Retention rate | Low |
| 7 | Horizon Coherence | Alignment | Coherence | Low |
| 8 | Strategic Regret | Comparator | Regret value | Medium |

---

## Test Data Models

### DecisionPacket

```python
class DecisionPacket(BaseModel):
    decision_id: str
    action: str
    proposer: str
    reversibility: Reversibility
    creates_lock_in: bool
    optionality_retention: float
    time_to_impact: timedelta
```

### FutureScenarios

```python
class FutureScenarios(BaseModel):
    projection_id: str
    scenarios: list[ScenarioProjection]
    time_horizons: list[TimeHorizon]
```

### Layer14Output

```python
class Layer14Output(BaseModel):
    legitimacy_score: float
    passes: bool
    violations: list[str]
    funded_missions: list[str]
```

---

## Validation Execution

### Running All Scenarios

```bash
python -m torq_console.layer15.foresight.run_validation --verbose
```

### Running Single Scenario

```bash
python -m torq_console.layer15.foresight.run_validation --scenario short_term_long_term_loss
```

### Expected Output

```
============================================================
Layer 15 Validation Results
============================================================

Total Scenarios: 8
Passed: 8
Failed: 0
Success Rate: 100.0%

[PASS] Scenario 1: Short-Term Win, Long-Term Loss
[PASS] Scenario 2: Reversible vs Irreversible Decision
[PASS] Scenario 3: Legitimate but Strategically Weak
[PASS] Scenario 4: Multi-Branch Uncertainty
[PASS] Scenario 5: Forecast Calibration
[PASS] Scenario 6: Optionality Preservation
[PASS] Scenario 7: Horizon Coherence Check
[PASS] Scenario 8: Strategic Regret Calculation

============================================================
SUCCESS: All strategic foresight scenarios passed!
============================================================
```

---

## Success Criteria

Layer 15 validation is complete when:

1. ✅ All 8 scenarios passing
2. ✅ All 5 engines tested
3. ✅ Integration with Layer 14 verified
4. ✅ Scoring formula validated
5. ✅ Calibration loop functional
6. ✅ No regression in Layer 13-14

---

**Document Status:** DRAFT
**Next:** SCORING_RULES.md
