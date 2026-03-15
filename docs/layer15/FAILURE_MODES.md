# Layer 15 Failure Modes
## Strategic Foresight Risk Analysis

**Version:** 0.15.0-planning
**Status:** DRAFT
**Author:** Agent 2
**Date:** 2026-03-14

---

## Overview

This document defines failure modes for Layer 15 strategic foresight, including symptoms, mitigation strategies, and detection methods.

**Goal:** Prevent TORQ from making strategically flawed decisions despite passing economic and constitutional filters.

---

## Failure Mode 1: Short-Term Optimization Trap

### Description

The system repeatedly chooses fast local wins that degrade mission durability over time. This is a subtle failure because each decision looks good in isolation, but the pattern is destructive in aggregate.

### Symptoms

- Short-term scores consistently high (> 0.80)
- Long-term scores declining over time
- Strategic regret accumulating
- Optionality decreasing with each decision
- Mission resilience degrading

### Detection

```python
class ShortTermOptimizationDetector:
    def detect_trap(self, history: list[Decision]) -> bool:
        # Check for pattern
        short_term_avg = mean(d.short_term_score for d in history)
        long_term_avg = mean(d.long_term_score for d in history)

        return (
            short_term_avg > 0.80 and
            long_term_avg < 0.50 and
            long_term_avg is decreasing
        )
```

### Mitigation Strategies

#### M1-1: Regret Tracking

```python
# Track cumulative strategic regret
cumulative_regret = sum(
    calculate_regret(decision, alternatives)
    for decision in history
)

if cumulative_regret > REGRET_THRESHOLD:
    trigger_strategic_review()
```

#### M1-2: Horizon Alignment Weighting

```python
# Increase weight of long-term value
if short_term_score > long_term_score + 0.20:
    long_term_weight *= 1.5
    short_term_weight *= 0.5
```

#### M1-3: Optionality Weighting

```python
# Penalize optionality loss more heavily
if optionality_retention < 0.50:
    optionality_weight *= 1.3
```

### Validation Rule

```python
# Scenario 1 validates this
if strategic_regret > 0.20:
    add_warning("Short-term optimization pattern detected")
```

---

## Failure Mode 2: Overprojection

### Description

The system becomes too speculative, generating numerous future scenarios and spending excessive time on analysis instead of execution. This leads to decision paralysis.

### Symptoms

- Analysis time > 30 seconds per decision
- Multiple deep horizons explored for every decision
- Confidence intervals extremely wide
- Decision queue building up
- System appears "stuck"

### Detection

```python
class OverprojectionDetector:
    def detect_overprojection(self) -> bool:
        # Check analysis time
        avg_analysis_time = measure_recent_analysis_time()

        # Check horizon depth
        avg_horizon_depth = measure_horizon_depth()

        # Check confidence spread
        avg_confidence_spread = measure_confidence_variance()

        return (
            avg_analysis_time > 30.0 or
            avg_horizon_depth > 5 or
            avg_confidence_spread > 0.50
        )
```

### Mitigation Strategies

#### M2-1: Impact-Based Horizon Selection

```python
# Only run deep foresight for high-impact decisions
def select_horizons(decision: DecisionPacket) -> list[TimeHorizon]:
    if decision.impact < IMPACT_THRESHOLD:
        return [TimeHorizon.SHORT]  # Only short-term
    else:
        return [TimeHorizon.SHORT, TimeHorizon.MEDIUM, TimeHorizon.LONG]
```

#### M2-2: Confidence Thresholds

```python
# Skip uncertain branches
def should_evaluate_branch(branch: DecisionBranch) -> bool:
    return branch.confidence > MIN_CONFIDENCE_THRESHOLD
```

#### M2-3: Horizon Depth Caps

```python
# Limit analysis depth
MAX_ANALYSIS_DEPTH = 3
MAX_SCENARIOS_PER_DECISION = 10
```

### Validation Rule

```python
# Ensure analysis time is reasonable
assert analysis_time < 30.0  # seconds
assert num_scenarios_generated < 20
```

---

## Failure Mode 3: Lock-In Blindness

### Description

The system ignores future path narrowing, making irreversible decisions without proper consideration. Decisions that eliminate future options are treated as normal.

### Symptoms

- Irreversible decisions not flagged
- Optionality not tracked
- Commitments made without reversibility assessment
- Lock-in risk not calculated
- Future paths increasingly limited

### Detection

```python
class LockInBlindnessDetector:
    def detect_blindness(self, decision: DecisionPacket) -> bool:
        # Check if reversibility was assessed
        if decision.reversibility not assessed:
            return True

        # Check if optionality was calculated
        if decision.optionality_impact not calculated:
            return True

        # Check for irreversibility patterns
        if decision.creates_commitments and not risk_assessed:
            return True

        return False
```

### Mitigation Strategies

#### M3-1: Mandatory Lock-In Risk Analysis

```python
# Require lock-in risk for high-commitment decisions
if decision.creates_commitments:
    lock_in_risk = calculate_lock_in_risk(decision)

    if lock_in_risk >= LockInRisk.HIGH:
        require_human_review()
        add_blocking_warning("High lock-in risk")
```

#### M3-2: Reversibility Requirement

```python
# Require reversibility assessment for uncertain decisions
if decision.uncertainty > UNCERTAINTY_THRESHOLD:
    if decision.reversibility != Reversibility.REVERSIBLE:
        block_decision(
            reason="Irreversible decision requires higher certainty"
        )
```

#### M3-3: Optionality Impact Statement

```python
# Require optionality impact documentation
if optionality_retention < 0.50:
    require_optionality_impact_statement(
        decision,
        explanation="This decision eliminates 50% of future paths"
    )
```

### Validation Rule

```python
# Scenario 6 validates this
if optionality_retention < 0.50:
    assert lock_in_risk >= LockInRisk.HIGH
    assert reversibility_assessed == True
```

---

## Failure Mode 4: Strategic Hallucination

### Description

Bad assumptions or incorrect models produce false future projections. The system confidently predicts futures that don't materialize, leading to poor strategic decisions.

### Symptoms

- Projections consistently wrong vs actual outcomes
- Confidence poorly calibrated
- Key assumptions violated
- Models fail in predictable ways
- "Hallucinated" scenarios treated as real

### Detection

```python
class StrategicHallucinationDetector:
    def detect_hallucination(self) -> bool:
        # Check calibration
        accuracy = self.calculate_projection_accuracy()

        # Check confidence calibration
        calibration_error = self.calculate_calibration_error()

        # Check assumption violations
        violated_assumptions = self.check_assumptions()

        return (
            accuracy < 0.60 or
            calibration_error > 0.20 or
            len(violated_assumptions) > 3
        )
```

### Mitigation Strategies

#### M4-1: Assumption Traceability

```python
# Require assumption traceability
for projection in projections:
    for assumption in projection.assumptions:
        assumption.trace_id = generate_trace()
        assumption.source = "documented"  # Not "hallucinated"
```

#### M4-2: Calibration Feedback Loop

```python
# Continuously calibrate based on outcomes
async def calibration_loop():
    while True:
        # Compare predictions vs outcomes
        calibration_data = await collect_outcomes()

        # Update confidence scores
        for projection in projections:
            new_confidence = recalibrate(
                projection.confidence,
                projection.actual_outcome,
                calibration_data
            )
            projection.confidence = new_confidence

        await sleep(timedelta(days=7))
```

#### M4-3: Post-Outcome Review

```python
# Require review when projections fail significantly
for decision in decisions:
    actual_outcome = await get_actual_outcome(decision.id)
    predicted_outcome = decision.projected_outcome

    error = abs(predicted_outcome - actual_outcome)
    if error > ERROR_THRESHOLD:
        require_review(
            decision=decision,
            reason=f"Projection error {error} exceeds threshold"
        )
```

### Validation Rule

```python
# Scenario 5 validates this
assert foresight_accuracy_calculated == True
assert confidence_updated_if_needed == True
```

---

## Failure Mode 5: Horizon Sacrifice

### Description

The system consistently sacrifices long-term goals for short-term gains. This is similar to FM-1 but focuses specifically on the temporal tradeoff.

### Symptoms

- Short-term: High scores
- Medium-term: Declining scores
- Long-term: Poor scores
- Mission objectives drift over time
- Strategic alignment degrades

### Detection

```python
class HorizonSacrificeDetector:
    def detect_sacrifice(self, decisions: list[Decision]) -> bool:
        # Check for temporal pattern
        for i in range(1, len(decisions) - 1):
            if decisions[i].long_term_score < decisions[i-1].long_term_score:
                # Long-term declining
                if decisions[i].short_term_score > decisions[i-1].short_term_score:
                    # But short-term improving
                    return True

        return False
```

### Mitigation Strategies

#### M5-1: Horizon Coherence Requirement

```python
# Require minimum coherence across horizons
coherence = calculate_horizon_coherence(scores)

if coherence < COHERENCE_THRESHOLD:
    reject_or_modify_decision(
        reason="Insufficient horizon coherence"
    )
```

#### M5-2: Mission Objective Alignment

```python
# Ensure long-term objectives preserved
if decision.conflicts_with_mission_objectives(horizon=TimeHorizon.LONG):
    require_explanation(
        decision,
        "How does this align with long-term mission objectives?"
    )
```

#### M5-3: Progressive Validation

```python
# Re-evaluate at each horizon
for horizon in [TimeHorizon.SHORT, MEDIUM, LONG]:
    if not passes_horizon_evaluation(decision, horizon):
        return False  # Stop before execution
```

### Validation Rule

```python
# Scenario 7 validates this
assert coherence < 0.50 triggers misalignment_detected
assert strategic_score < short_term_score when misaligned
```

---

## Failure Mode 6: Decision Paralysis

### Description

The system becomes so concerned with strategic risks that it refuses to make any decision, leading to complete inaction.

### Symptoms

- All decisions score in CAUTION band
- Defer count exceeds execute count
- No decision made for extended period
- System appears "stuck"

### Detection

```python
class DecisionParalysisDetector:
    def detect_paralysis(self) -> bool:
        recent_decisions = get_recent_decisions(timedelta(days=7))

        defer_count = sum(1 for d in recent_decisions if d.recommendation == "DEFER")
        execute_count = sum(1 for d in recent_decisions if d.recommendation == "EXECUTE")

        return (
            defer_count > 10 and
            execute_count == 0 and
            len([d for d in recent_decisions if d.score < 0.70]) > len(recent_decisions) * 0.8
        )
```

### Mitigation Strategies

#### M6-1: Minimum Execution Quota

```python
# Require some decisions to proceed
MIN_EXECUTION_RATIO = 0.30  # 30% of decisions must execute

if execution_ratio < MIN_EXECUTION_RATIO:
    lower_strictness_temporarily()
    force_execute_best_scoring_deferred()
```

#### M6-2: Progressive Commitment

```python
# Start with reversible decisions, build confidence
def build_decision_confidence():
    reversible_decisions = [d for d in pending if d.reversibility == Reversibility.REVERSIBLE]

    # Execute reversible decisions first
    for decision in reversible_decisions:
        if decision.score > 0.50:
            execute(decision)
```

#### M6-3: Risk Budget

```path

# Allow some strategic risk to avoid paralysis
RISK_BUDGET = 0.10  # Can accept 10% strategic regret

total_risk_accepted = 0.0
for decision in pending:
    risk = 1.0 - decision.strategic_score
    if total_risk_accepted + risk < RISK_BUDGET:
        execute(decision)
        total_risk_accepted += risk
```

---

## Failure Mode Summary

| # | Failure Mode | Severity | Detection Complexity | Mitigation Complexity |
|---|-------------|----------|---------------------|---------------------|
| 1 | Short-Term Optimization Trap | HIGH | Low | Medium |
| 2 | Overprojection | MEDIUM | Low | Low |
| 3 | Lock-In Blindness | HIGH | Low | Medium |
| 4 | Strategic Hallucination | HIGH | Medium | High |
| 5 | Horizon Sacrifice | MEDIUM | Low | Medium |
| 6 | Decision Paralysis | MEDIUM | Low | Medium |

---

## Detection Integration

### Unified Failure Detector

```python
class StrategicFailureDetector:
    def __init__(self):
        self.detectors = [
            ShortTermOptimizationDetector(),
            OverprojectionDetector(),
            LockInBlindnessDetector(),
            StrategicHallucinationDetector(),
            HorizonSacrificeDetector(),
            DecisionParalysisDetector()
        ]

    async def detect_failures(
        self,
        decision: DecisionPacket,
        history: list[Decision]
    ) -> FailureReport:
        results = {}
        for detector in self.detectors:
            try:
                results[detector.name] = await detector.detect(decision, history)
            except Exception as e:
                results[detector.name] = DetectionError(str(e))

        return FailureReport(
            detections=results,
            critical_failures=[k for k,v in results.items() if v == True],
            warnings=[k for k,v in results.items() if isinstance(v, DetectionWarning)]
        )
```

---

## Recovery Procedures

### Recovery R1: Short-Term Optimization Trap Recovery

1. Trigger strategic review
2. Increase long-term value weight
3. Force optionality preservation for next N decisions
4. Monitor for improvement

### Recovery R2: Overprojection Recovery

1. Reduce horizon depth
2. Increase confidence threshold
3. Limit scenarios per decision
4. Monitor decision latency

### Recovery R3: Lock-In Blindness Recovery

1. Block irreversible decisions temporarily
2. Require optionality impact analysis
3. Rebuild optionality buffer
4. Gradually restore irreversible decision capacity

### Recovery R4: Strategic Hallucination Recovery

1. Trigger calibration review
2. Reduce confidence scores
3. Require assumption documentation
4. Increase human oversight

### Recovery R5: Horizon Sacrifice Recovery

1. Enforce horizon coherence threshold
2. Require long-term objective alignment
3. Progressive validation at each horizon
4. Monitor mission objective drift

### Recovery R6: Decision Paralysis Recovery

1. Lower strictness temporarily
2. Force execution of best deferred decision
3. Build confidence with reversible decisions
4. Restore normal strictness after quota

---

## Prevention Summary

| Failure Mode | Prevention Strategy |
|---------------|-------------------|
| Short-Term Optimization | Regret tracking, horizon weighting |
| Overprojection | Impact-based horizons, confidence thresholds |
| Lock-In Blindness | Mandatory risk analysis, reversibility requirements |
| Strategic Hallucination | Assumption traceability, calibration loop |
| Horizon Sacrifice | Coherence threshold, objective alignment |
| Decision Paralysis | Execution quota, progressive commitment |

---

**Document Status:** DRAFT
**Next:** CALIBRATION_PLAN.md
