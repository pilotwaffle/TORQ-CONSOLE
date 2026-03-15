# Layer 15 Calibration Plan
## Strategic Foresight Calibration Framework

**Version:** 0.15.0-planning
**Status:** DRAFT
**Author:** Agent 2
**Date:** 2026-03-14

---

## Overview

This document defines the calibration framework for Layer 15 strategic foresight. Calibration ensures that projections remain accurate and confidence scores are well-calibrated over time.

**Goal:** Maintain and improve the accuracy of strategic foresight projections through continuous learning.

---

## Calibration Metrics

### CM-1: Foresight Accuracy

**Definition:** Percentage of projections that match actual outcomes.

```python
foresight_accuracy = matched_projections / total_projections

where:
    matched_projection = abs(predicted_value - actual_value) < tolerance
```

**Target:** > 0.75 (75% accuracy)

### CM-2: Confidence Calibration Error

**Definition:** Difference between predicted probability and observed frequency.

```python
calibration_error = abs(confidence - observed_frequency)

# Group by confidence level
for bin in [0.0-0.2, 0.2-0.4, 0.4-0.6, 0.6-0.8, 0.8-1.0]:
    predictions_in_bin = [p for p in projections if p.confidence in bin]
    observed_frequency = sum(1 for p in predictions_in_bin if p.matched) / len(predictions_in_bin)
    calibration_error += abs(bin_mid - observed_frequency)
```

**Target:** < 0.10 (Brier score)

### CM-3: Regret Accumulation Rate

**Definition:** Rate of strategic regret accumulation over time.

```python
regret_accumulation_rate = (
    current_cumulative_regret - previous_cumulative_regret
) / time_period
```

**Target:** < 0.05 per week

### CM-4: Projection Distribution

**Definition:** Distribution of projections by accuracy and confidence.

```python
projection_distribution = {
    "high_confidence_high_accuracy": count(p) where p.confidence > 0.7 and p.matched,
    "high_confidence_low_accuracy": count(p) where p.confidence > 0.7 and not p.matched,
    "low_confidence_high_accuracy": count(p) where p.confidence < 0.3 and p.matched,
    "low_confidence_low_accuracy": count(p) where p.confidence < 0.3 and not p.matched,
}
```

**Target:** High confidence implies high accuracy

---

## Calibration Data Collection

### Data Points Per Projection

```python
class ProjectionRecord(BaseModel):
    projection_id: str
    decision_id: str
    timestamp: datetime
    predicted_outcome: SystemState
    confidence: float
    time_horizons: list[TimeHorizon]
    key_assumptions: list[str]
    actual_outcome: SystemState | None  # Filled later
    matched: bool | None  # Filled later
    calibration_error: float | None  # Filled later
```

### Data Collection Process

```python
async def collect_projection_outcomes(time_window: timedelta):
    """Collect actual outcomes for projections made during time window."""

    # Get projections made during window
    projections = await projection_db.get_projections(
        created_after=datetime.utcnow() - time_window
    )

    results = []
    for projection in projections:
        # Get actual outcome
        actual_outcome = await get_actual_outcome(
            projection.decision_id,
            projection.time_horizons[-1]  # Latest horizon
        )

        # Calculate match
        matched = calculate_match(projection.predicted_outcome, actual_outcome)
        calibration_error = calculate_calibration_error(projection, actual_outcome)

        results.append(ProjectionRecord(
            projection_id=projection.id,
            decision_id=projection.decision_id,
            predicted_outcome=projection.predicted_outcome,
            actual_outcome=actual_outcome,
            confidence=projection.confidence,
            matched=matched,
            calibration_error=calibration_error
        ))

    return results
```

---

## Calibration Loop

### Loop Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    PROJECTION MADE                                 │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                 RECORD PROJECTION                                   │
│                 • Store predictions                                 │
│                 • Store assumptions                                    │
│                 • Store confidence                                     │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
                        [TIME PASSES]
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                 COLLECT OUTCOMES                                   │
│                 • Compare predicted vs actual                           │
│                 • Calculate match/error                                 │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                 CALIBRATE                                            │
│                 • Update confidence weights                             │
│                 • Adjust assumption reliability                         │
│                 • Trigger alerts if needed                               │
└─────────────────────────────────────────────────────────────────┘
```

### Calibration Algorithms

#### CA-1: Confidence Adjustment

```python
async def adjust_confidence(projection: ScenarioProjection, actual_outcome: SystemState):
    """Adjust confidence based on outcome."""

    # Calculate match
    match = calculate_match(projection.predicted_outcome, actual_outcome)

    # Get current confidence
    old_confidence = projection.confidence

    # Adjust confidence
    if match and old_confidence < 0.90:
        # Was right and wasn't confident enough
        new_confidence = min(0.95, old_confidence * 1.1)
    elif not match and old_confidence > 0.50:
        # Was wrong and was confident
        new_confidence = max(0.30, old_confidence * 0.8)

    # Apply learning rate
    learning_rate = 0.1
    final_confidence = old_confidence + learning_rate * (new_confidence - old_confidence)

    return final_confidence
```

#### CA-2: Assumption Reliability Tracking

```python
class AssumptionReliabilityTracker:
    def __init__(self):
        self.assumption_scores = {}  # assumption_id -> reliability_score

    def record_assumption_performance(
        self,
        assumption_id: str,
        held_valid: bool
    ):
        if assumption_id not in self.assumption_scores:
            self.assumption_scores[assumption_id] = 0.5  # Start neutral

        # Update with exponential moving average
        alpha = 0.2  # Learning rate
        current_score = self.assumption_scores[assumption_id]
        new_score = alpha if held_valid else (1.0 - alpha)

        self.assumption_scores[assumption_id] = (
            current_score * (1 - alpha) + new_score * alpha
        )

    def get_reliability(self, assumption_id: str) -> float:
        return self.assumption_scores.get(assumption_id, 0.5)
```

#### CA-3: Horizon Weight Calibration

```python
def calibrate_horizon_weights(historical_evaluations: list[Evaluation]):
    """Adjust horizon weights based on predictive value."""

    # Calculate predictive value of each horizon
    horizon_values = {}
    for horizon in [TimeHorizon.SHORT, MEDIUM, LONG]:
        # How well did this horizon predict actual outcomes?
        correlations = []
        for eval in historical_evaluations:
            predicted = eval.scores.get(horizon)
            actual = eval.actual_outcome
            correlation = calculate_correlation(predicted, actual)
            correlations.append(correlation)

        # Average correlation for this horizon
        horizon_values[horizon] = mean(correlations)

    # Adjust weights proportionally
    total_value = sum(horizon_values.values())
    calibrated_weights = {
        horizon: value / total_value
        for horizon, value in horizon_values.items()
    }

    return calibrated_weights
```

---

## Calibration Triggers

### Automatic Calibration

**Trigger Conditions:**
- Weekly calibration cycle (scheduled)
- Accuracy drops below 0.70
- Calibration error exceeds 0.15
- Regret accumulation rate exceeds threshold

### Manual Calibration

**Trigger Conditions:**
- Operator requests calibration
- System performance degraded
- Major prediction failure
- Model deployment

---

## Calibration Phases

### Phase 15A: Initial Calibration (First 30 Days)

**Goal:** Establish baseline accuracy and confidence.

**Activities:**
1. Collect all projection records
2. Calculate initial foresight accuracy
3. Calculate initial calibration error
4. Establish confidence baseline
5. Document assumption reliability

**Success Criteria:**
- Baseline accuracy measured
- Baseline calibration error calculated
- Confidence baseline established

### Phase 15B: Active Calibration (Days 31-90)

**Goal:** Improve calibration through feedback.

**Activities:**
1. Weekly calibration cycles
2. Update confidence scores
3. Adjust assumption reliability
4. Refine horizon weights
5. Monitor improvement

**Success Criteria:**
- Foresight accuracy > 0.70
- Calibration error < 0.15
- Confidence properly calibrated

### Phase 15C: Steady-State Calibration (Day 91+)

**Goal:** Maintain accuracy and detect drift.

**Activities:**
1. Monthly deep calibration
2. Continuous monitoring
3. Drift detection
4. Model refinement

**Success Criteria:**
- Accuracy maintained > 0.70
- Drift detected within 7 days
- Accuracy trend stable

---

## Validation of Calibration

### V-1: Calibration Improves Accuracy

**Test:** Compare accuracy before and after calibration.

**Expected:** Accuracy increases by at least 5%.

```python
accuracy_before = calculate_accuracy(projections_before_calibration)
accuracy_after = calculate_accuracy(projections_after_calibration)

assert accuracy_after > accuracy_before * 1.05
```

### V-2: Confidence Properly Calibrated

**Test:** Check if confidence matches observed frequency.

**Expected:** Calibration error < 0.15.

```python
calibration_error = calculate_calibration_error(calibrated_projections)
assert calibration_error < 0.15
```

### V-3: Assumptions Become More Reliable

**Test:** Track assumption reliability over time.

**Expected:** Mean reliability increases or stays stable.

```python
reliability_trend = get_reliability_trend(assumption_scores)
assert reliability_trend[-1] >= reliability_trend[0] * 0.95  # Not degrading
```

---

## Rollout and Monitoring

### Monitoring Dashboard

```bash
torq foresight calibration status
```

**Output:**
```
Calibration Status (Last 7 Days)
---------------------------------------------------------------------------
Foresight Accuracy: 0.78
Calibration Error: 0.08
Regret Accumulation: 0.03
Confidence Distribution:
  High/High: 45
  High/Low: 5
  Low/High: 12
  Low/Low: 8

Status: WELL CALIBRATED ✓
```

### Alert Thresholds

| Metric | Warning | Critical | Action |
|--------|--------|----------|--------|
| Foresight Accuracy | < 0.70 | < 0.60 | Trigger calibration |
| Calibration Error | > 0.15 | > 0.25 | Trigger recalibration |
| Regret Accumulation | > 0.05 | > 0.10 | Trigger strategic review |
| Confidence Error | > 0.20 | > 0.30 | Trigger confidence audit |

---

## Calibration Report

### Weekly Report Contents

```python
class CalibrationReport(BaseModel):
    report_date: date
    period_start: datetime
    period_end: datetime

    # Metrics
    foresight_accuracy: float
    calibration_error: float
    regret_accumulation: float

    # Distribution
    confidence_distribution: dict[str, int]
    accuracy_distribution: dict[str, int]

    # Assumptions
    most_reliable_assumptions: list[str]
    least_reliable_assumptions: list[str]

    # Trends
    accuracy_trend: list[float]
    error_trend: list[float]

    # Recommendations
    recommendations: list[str]
```

---

## Success Criteria

Layer 15 calibration is complete when:

1. ✅ Baseline metrics established (Phase 15A)
2. ✅ Active calibration improves accuracy (Phase 15B)
3. ✅ Steady-state monitoring functional (Phase 15C)
4. ✅ Calibration loop automated
5. ✅ Monitoring dashboard functional
6. ✅ Alert thresholds defined
7. ✅ No regression in Layer 13-14

---

## Integration with Validation

### Calibration in Validation Scenarios

**Scenario 5: Forecast Calibration** explicitly tests calibration:
- Projections compared against actual outcomes
- Confidence updates applied
- Assumption reliability adjusted

### Validation Uses Calibration Data

```python
# Validation uses calibrated models
calibrated_projections = await calibration_engine.get_calibrated_models()

# Run validation scenarios
for scenario in validation_scenarios:
    result = await scenario.run_with_calibrated_models(calibrated_projections)
```

---

## Open Questions

1. **Calibration Frequency:** Should calibration be adaptive based on need or strictly scheduled?
   - Proposal: Scheduled weekly + trigger-based if accuracy drops

2. **Confidence Bounds:** Should minimum confidence be enforced?
   - Proposal: Minimum 0.30 confidence to accept projection

3. **Assumption Tracking:** How to identify unique assumptions?
   - Proposal: Use semantic similarity clustering

4. **Historical Data:** How much historical data is required?
   - Proposal: Minimum 30 days, optimal 90 days

---

**Document Status:** DRAFT
**Layer 15 Status:** Planning Phase - Complete
