# Layer 15 Scoring Rules
## Strategic Foresight Evaluation Policy

**Version:** 0.15.0-planning
**Status:** DRAFT
**Author:** Agent 2
**Date:** 2026-03-14

---

## Overview

This document defines the scoring policy for Layer 15 strategic foresight. Scores determine whether decisions are strategically sound and should proceed to execution.

**Core Principle:** > "Is this smart over time?"

---

## Strategic Score Formula

### Primary Formula

```python
strategic_score = base_score - penalties

where:
    base_score = (
        long_term_value * 0.35 +
        resilience * 0.25 +
        optionality * 0.20 +
        horizon_alignment * 0.15 +
        systemic_safety * 0.05
    )

    penalties = (
        lock_in_risk * 0.30 +
        systemic_risk * 0.20
    )
```

### Component Definitions

#### Long-Term Value (0.35 weight)

**Definition:** Expected mission value over 180+ days.

**Calculation:**
```python
long_term_value = weighted_sum(
    scenario.long_term_outcome for scenario in scenarios
)
```

**Range:** [0.0, 1.0]

#### Resilience (0.25 weight)

**Definition:** System ability to maintain function under stress.

**Calculation:**
```python
resilience = 1.0 - stress_vulnerability
where:
    stress_vulnerability = probability_of_failure_under_stress
```

**Range:** [0.0, 1.0]

#### Optionality (0.20 weight)

**Definition:** Future freedom of action preserved.

**Calculation:**
```python
optionality = remaining_viable_paths / initial_viable_paths
```

**Range:** [0.0, 1.0]

#### Horizon Alignment (0.15 weight)

**Definition:** Consistency of alignment across time horizons.

**Calculation:**
```python
horizon_alignment = 1.0 - variance(
    [short_term_score, medium_term_score, long_term_score]
)
```

**Range:** [0.0, 1.0]

#### Systemic Safety (0.05 weight)

**Definition:** Absence of catastrophic risk.

**Calculation:**
```python
systemic_safety = 1.0 - max_catastrophic_risk_probability
```

**Range:** [0.0, 1.0]

#### Lock-In Risk (0.30 penalty)

**Definition:** Risk of being trapped in a suboptimal path.

**Calculation:**
```python
lock_in_risk = 1.0 - optionality_retention
if reversibility == IRREVERSIBLE:
    lock_in_risk *= 1.5  # Increased risk
```

**Range:** [0.0, 1.0]

#### Systemic Risk (0.20 penalty)

**Definition:** Risk of cascading failures.

**Calculation:**
```python
systemic_risk = calculate_systemic_risk(
    decision_interconnectedness,
    potential_cascade_size,
    recovery_difficulty
)
```

**Range:** [0.0, 1.0]

---

## Rating Bands

### Band Definitions

| Score Range | Band | Meaning | Action |
|-------------|------|---------|--------|
| 0.85 - 1.00 | **STRONG** | Strong strategic recommendation | Execute with confidence |
| 0.70 - 0.84 | **ACCEPTABLE** | Strategically acceptable | Execute |
| 0.50 - 0.69 | **CAUTION** | Conditional / concerning | Redesign or defer if possible |
| 0.25 - 0.49 | **WEAK** | Strategically weak | Reject or redesign required |
| 0.00 - 0.24 | **CRITICAL** | Fundamentally flawed | Reject |

### Decision Thresholds

```python
def recommend(strategic_score: StrategicEvaluation) -> StrategicRecommendation:
    if strategic_score.band == StrategicBand.STRONG:
        return StrategicRecommendation.EXECUTE
    elif strategic_score.band == StrategicBand.ACCEPTABLE:
        return StrategicRecommendation.EXECUTE
    elif strategic_score.band == StrategicBand.CAUTION:
        return StrategicRecommendation.DEFER
    else:  # WEAK or CRITICAL
        return StrategicRecommendation.REDESIGN
```

---

## Complete Decision Policy

### The TORQ Three-Layer Filter

```
┌─────────────────────────────────────────────────────────────────┐
│                    DECISION PROPOSED                             │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  LAYER 13: Economic Intelligence                 │
│                                                                  │
│  Question: "Is this worth doing?"                                │
│                                                                  │
│  IF NOT economically viable:                                      │
│      → REJECT                                                      │
│  ELSE:                                                            │
│      → CONTINUE TO LAYER 14                                       │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│               LAYER 14: Constitutional Governance                 │
│                                                                  │
│  Question: "Is this allowed?"                                   │
│                                                                  │
│  IF NOT legitimate:                                              │
│      → REJECT                                                      │
│  ELSE:                                                            │
│      → CONTINUE TO LAYER 15                                       │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                LAYER 15: Strategic Foresight                       │
│                                                                  │
│  Question: "Is this smart over time?"                            │
│                                                                  │
│  IF NOT strategically sound:                                       │
│      → REDESIGN / DEFER                                           │
│  ELSE:                                                            │
│      → EXECUTE (Layers 6-11)                                      │
└─────────────────────────────────────────────────────────────────┘
```

### Detailed Policy Logic

```python
async def evaluate_decision(decision: DecisionPacket) -> FinalRecommendation:
    # Layer 13: Economic Intelligence
    economic_result = await layer13_engine.evaluate(decision)
    if not economic_result.viable:
        return FinalRecommendation(
            approved=False,
            reason="Not economically viable",
            layer="L13"
        )

    # Layer 14: Constitutional Governance
    governance_result = await layer14_engine.evaluate(decision)
    if not governance_result.passes:
        return FinalRecommendation(
            approved=False,
            reason=f"Constitutional violation: {governance_result.violations}",
            layer="L14"
        )

    # Layer 15: Strategic Foresight
    strategic_result = await layer15_engine.evaluate(decision)
    if strategic_result.recommendation in [StrategicRecommendation.REDESIGN, StrategicRecommendation.REJECT]:
        return FinalRecommendation(
            approved=False,
            reason=f"Strategically weak: {strategic_result.warnings}",
            layer="L15"
        )

    # All layers passed
    return FinalRecommendation(
        approved=True,
        reason="Economically viable, legitimate, and strategically sound",
        strategic_score=strategic_result.score,
        layer="L15"
    )
```

---

## Component Scoring Rules

### CR-1: Long-Term Value Scoring

**Rule:** Calculate expected value over long-term horizon.

**Pass Criteria:**
```python
long_term_value = weighted_average(
    [scenario.value for scenario in scenarios],
    weights=[scenario.probability for scenario in scenarios]
)

assert 0.0 <= long_term_value <= 1.0
```

### CR-2: Resilience Scoring

**Rule:** Assess stress tolerance.

**Pass Criteria:**
```python
resilience = 1.0 - stress_failure_probability

if decision.creates_single_point_of_failure:
    resilience *= 0.5

assert 0.0 <= resilience <= 1.0
```

### CR-3: Optionality Scoring

**Rule:** Calculate future path preservation.

**Pass Criteria:**
```python
optionality = remaining_paths / initial_paths

if decision.reversibility == IRREVERSIBLE:
    optionality *= 0.7  # Penalty for irreversible

assert 0.0 <= optionality <= 1.0
```

### CR-4: Horizon Alignment Scoring

**Rule:** Assess temporal consistency.

**Pass Criteria:**
```python
alignment = 1.0 - std_deviation(
    [short_score, medium_score, long_score]
) / sqrt(3)

if long_score < short_score - 0.2:
    alignment *= 0.7  # Penalty for horizon sacrifice

assert 0.0 <= alignment <= 1.0
```

### CR-5: Lock-In Risk Scoring

**Rule:** Assess path dependency risk.

**Pass Criteria:**
```python
lock_in_risk = 1.0 - optionality

if decision.reversibility == Reversibility.IRREVERSIBLE:
    lock_in_risk = min(1.0, lock_in_risk * 1.5)

assert 0.0 <= lock_in_risk <= 1.0
```

### CR-6: Systemic Risk Scoring

**Rule:** Assess cascade potential.

**Pass Criteria:**
```python
systemic_risk = calculate_interconnectedness_risk(
    decision.depends_on_components,
    decision.creates_dependencies
)

if decision.creates_critical_dependency:
    systemic_risk = min(1.0, systemic_risk * 1.2)

assert 0.0 <= systemic_risk <= 1.0
```

---

## Score Composition Rules

### Rule SCR-1: Score Range Validation

**Requirement:** All scores in [0.0, 1.0].

```python
assert 0.0 <= strategic_score <= 1.0
assert all(0.0 <= component <= 1.0 for component in base_components)
assert all(0.0 <= penalty <= 1.0 for penalty in penalties)
```

### Rule SCR-2: Weight Sum Validation

**Requirement:** Base weights sum to 1.0.

```python
BASE_WEIGHTS = {
    "long_term_value": 0.35,
    "resilience": 0.25,
    "optionality": 0.20,
    "horizon_alignment": 0.15,
    "systemic_safety": 0.05,
}

assert abs(sum(BASE_WEIGHTS.values()) - 1.0) < 0.001
```

### Rule SCR-3: Penalty Cap

**Requirement:** Total penalties cannot exceed 0.50.

```python
total_penalties = lock_in_risk * 0.30 + systemic_risk * 0.20
assert total_penalties <= 0.50
```

---

## Threshold Rules

### TR-1: Execution Threshold

**Requirement:** Only execute if all three layers pass.

```python
def can_execute(econ, gov, strat) -> bool:
    return (
        econ.viable and
        gov.passes and
        strat.recommendation in [StrategicRecommendation.EXECUTE]
    )
```

### TR-2: Deferral Threshold

**Requirement:** Defer if strategic score in CAUTION band.

```python
if 0.50 <= strategic_score < 0.70:
    return StrategicRecommendation.DEFER
```

### TR-3: Redesign Threshold

**Requirement:** Require redesign if score < 0.50.

```python
if strategic_score < 0.50:
    return StrategicRecommendation.REDESIGN
```

---

## Calibration Rules

### Calibration Rule CAL-1: Accuracy Tracking

**Requirement:** Track projection vs actual accuracy.

```python
calibration_data = {
    "projections_made": 100,
    "projections_matched": 75,
    "foresight_accuracy": 0.75
}
```

### Calibration Rule CAL-2: Confidence Adjustment

**Requirement:** Adjust confidence based on calibration.

```python
if projection.confidence > actual_accuracy + 0.10:
    confidence = max(0.30, confidence * 0.9)  # Reduce

elif projection.confidence < actual_accuracy - 0.10:
    confidence = min(0.95, confidence * 1.1)  # Increase
```

### Calibration Rule CAL-3: Assumption Reliability

**Requirement:** Track and adjust assumption weights.

```python
for assumption in projection.assumptions:
    if assumption.historical_accuracy < 0.50:
        assumption.weight *= 0.8  # Reduce influence
```

---

## Validation Rules

### VR-1: Scenario 1 (Short-Term Win)

**Requirement:** Long-term loss detected and flagged.

```python
assert long_term_score < short_term_score
assert strategic_score < 0.50
assert recommendation == REDESIGN
```

### VR-2: Scenario 2 (Reversibility)

**Requirement:** Reversible path favored when similar value.

```python
assert optionality_score(A) > optionality_score(B)
assert recommended_branch == A
assert reversibility(A) == REVERSIBLE
```

### VR-3: Scenario 3 (Legitimate but Weak)

**Requirement:** Layer 15 can override Layer 14.

```python
assert layer14.passes == True
assert layer15.score < 0.50
assert final_recommendation == REDESIGN
```

### VR-4: Scenario 4 (Uncertainty)

**Requirement:** Uncertainty acknowledged in recommendation.

```python
assert confidence_intervals_provided
assert risk_adjusted_value_used
assert recommendation.acknowledges_uncertainty == True
```

### VR-5: Scenario 5 (Calibration)

**Requirement:** Calibration loop executes.

```python
assert foresight_accuracy_calculated
assert confidence_updated if needed
assert assumption_reliability_tracked
```

### VR-6: Scenario 6 (Optionality)

**Requirement:** Optionality loss penalized.

```python
assert optionality_retention < 0.50
assert lock_in_risk >= HIGH
assert strategic_score reflects penalty
```

### VR-7: Scenario 7 (Horizon Coherence)

**Requirement:** Misalignment detected and penalized.

```python
assert coherence < 0.50
assert misalignment_detected == True
assert strategic_score < short_term_score
```

### VR-8: Scenario 8 (Regret)

**Requirement:** Regret calculated and tracked.

```python
assert strategic_regret > 0
assert best_alternative_identified
assert regret_accumulation_updated
```

---

## Test Matrix

| Scenario | Rules | Priority |
|----------|-------|----------|
| S1: Short-Term Win | SCR-1, SCR-3, TR-2, VR-1 | P0 |
| S2: Reversibility | CR-3, CR-5, VR-2 | P0 |
| S3: Legitimate but Weak | TR-1, TR-3, VR-3 | P0 |
| S4: Uncertainty | CR-1, VR-4 | P1 |
| S5: Calibration | CAL-1, CAL-2, CAL-3, VR-5 | P1 |
| S6: Optionality | CR-3, CR-5, VR-6 | P0 |
| S7: Horizon Coherence | CR-4, VR-7 | P0 |
| S8: Regret | CR-1, VR-8 | P1 |

---

## Success Criteria

Layer 15 scoring is complete when:

1. ✅ Formula defined with weights
2. ✅ Rating bands established
3. ✅ Complete decision policy specified
4. ✅ All validation rules mapped
5. ✅ Calibration rules defined
6. ✅ Integration with Layer 13-14 specified

---

**Document Status:** DRAFT
**Next:** FAILURE_MODES.md
