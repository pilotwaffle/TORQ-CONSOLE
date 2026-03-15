# Layer 15 PRD - Strategic Foresight Engine
## Product Requirements Document

**Version:** 0.15.0-planning
**Status:** DRAFT
**Author:** Agent 2
**Date:** 2026-03-14

---

## Executive Summary

Layer 15 introduces **strategic foresight** to the TORQ system, providing the ability to evaluate how present decisions shape future mission outcomes across short, medium, and long time horizons.

### The Core Question

**"What future does this decision create?"**

### Purpose

To prevent TORQ from making decisions that:
- Optimize for the present at the expense of the future
- Create irreversible lock-in to suboptimal paths
- Eliminate valuable future options
- Undermine long-term mission objectives

### Position in Architecture

```
L1-L11:  Execution Fabric
L12:     Collective Intelligence Exchange
L13:     Economic Intelligence
L14:     Constitutional Governance
L15:     Strategic Foresight ← NEW
```

**Decision Flow:**
```
Layer 13: Economic Prioritization
         ↓
Layer 14: Legitimacy Check
         ↓
Layer 15: Strategic Evaluation ← NEW GATE
         ↓
Layer 6-11: Execution (if strategically sound)
```

---

## Product Definition

**Product Name:** Strategic Foresight Engine

**Purpose:** Provide structured evaluation of how present decisions shape future mission outcomes across short, medium, and long horizons.

**Functional Responsibilities:**

1. **Generate future scenarios** from present state
2. **Compare strategic branches** by long-term value
3. **Estimate second- and third-order consequences**
4. **Detect lock-in and optionality loss**
5. **Evaluate horizon alignment**
6. **Produce strategic recommendation** for execution

---

## Core Evaluation Metrics

### 1. Foresight Accuracy

**Definition:** How well projected branches match real outcomes over time.

```python
foresight_accuracy = matched_projections / total_projections
```

**Measurement:**
- Track predictions made at decision time
- Compare against actual outcomes at future points
- Calculate matching rate across all projections

**Target:** > 0.75 (75% of projections should align with reality)

### 2. Strategic Regret ⭐

**Definition:** Value lost by choosing a path that was acceptable now but inferior over time.

```python
strategic_regret = best_alternative_long_term_value - chosen_path_long_term_value
```

**Why It Matters:** This is the most important Layer 15 metric. It tells TORQ when it picked a path that looked good in the short term but created worse outcomes in the long term.

**Target:** Minimize strategic regret (aim for < 0.20)

### 3. Optionality Retention

**Definition:** How many future paths remain viable after a decision.

```python
optionality_retention = remaining_viable_paths / initial_viable_paths
```

**Why It Matters:** Preserves freedom of action for future decisions.

**Target:** > 0.70 (retain at least 70% of future options)

### 4. Horizon Coherence

**Definition:** Consistency of alignment across time horizons.

```python
horizon_coherence = alignment_consistency_across_time
```

**Why It Matters:** Prevents short-term wins from undermining long-term goals.

**Target:** > 0.80 (consistent alignment across horizons)

### 5. Projection Confidence Calibration

**Definition:** Whether confidence scores match prediction accuracy.

**Measurement:**
- Track confidence vs accuracy correlation
- Detect overconfidence or underconfidence
- Adjust confidence scoring accordingly

**Target:** Calibration error < 0.10

---

## Component Architecture

### C1: ScenarioProjectionEngine

**Purpose:** Generate future scenarios from present state.

**Responsibilities:**
- Project future states based on current decision
- Generate multiple plausible futures (optimistic, baseline, pessimistic)
- Estimate probability distributions for key variables
- Track projection confidence over time

**Interface:**
```python
class ScenarioProjectionEngine:
    async def project_future(
        self,
        current_state: SystemState,
        decision: DecisionPacket,
        time_horizons: list[TimeHorizon]
    ) -> FutureScenarios:
        """Generate future scenarios based on decision."""
        pass
```

**Output Model:**
```python
class FutureScenarios(BaseModel):
    scenario_id: str
    projections: list[ScenarioProjection]
    confidence: float
    time_horizons: list[TimeHorizon]

class ScenarioProjection(BaseModel):
    scenario_id: str
    horizon: TimeHorizon  # SHORT, MEDIUM, LONG
    probability: float
    expected_outcome: SystemState
    key_risks: list[str]
```

### C2: StrategicBranchComparator

**Purpose:** Compare strategic branches by long-term value.

**Responsibilities:**
- Evaluate multiple decision paths
- Calculate expected value for each path
- Risk-adjust comparison
- Rank paths by strategic quality

**Interface:**
```python
class StrategicBranchComparator:
    async def compare_branches(
        self,
        branches: list[DecisionBranch]
    ) -> BranchComparison:
        """Compare decision branches by long-term value."""
        pass
```

**Output Model:**
```python
class BranchComparison(BaseModel):
    recommended_branch: str
    rankings: list[BranchRank]
    regret_analysis: RegretAnalysis
    confidence_intervals: dict[str, tuple[float, float]]

class BranchRank(BaseModel):
    branch_id: str
    expected_value: float
    risk_adjusted_value: float
    long_term_score: float
    rank: int
```

### C3: SecondOrderConsequenceAnalyzer

**Purpose:** Estimate second- and third-order consequences.

**Responsibilities:**
- Trace cascading effects of decisions
- Identify delayed consequences
- Detect unintended outcomes
- Map consequence chains

**Interface:**
```python
class SecondOrderConsequenceAnalyzer:
    async def analyze_consequences(
        self,
        decision: DecisionPacket,
        depth: int = 3
    ) -> ConsequenceAnalysis:
        """Analyze consequences up to N orders deep."""
        pass
```

**Output Model:**
```python
class ConsequenceAnalysis(BaseModel):
    decision_id: str
    consequences: list[Consequence]
    total_impact: float
    risk_factors: list[str]

class Consequence(BaseModel):
    order: int  # 1st, 2nd, 3rd
    description: str
    impact: float  # -1.0 to 1.0
    probability: float
    time_delay: timedelta
```

### C4: OptionalityPreservationEngine

**Purpose:** Detect lock-in and optionality loss.

**Responsibilities:**
- Count viable future paths before decision
- Count viable future paths after decision
- Calculate optionality retention
- Flag irreversible commitments

**Interface:**
```python
class OptionalityPreservationEngine:
    async def evaluate_optionality(
        self,
        decision: DecisionPacket,
        current_paths: list[FuturePath]
    ) -> OptionalityAnalysis:
        """Evaluate how decision affects future options."""
        pass
```

**Output Model:**
```python
class OptionalityAnalysis(BaseModel):
    decision_id: str
    initial_paths: int
    remaining_paths: int
    retention_rate: float
    lost_paths: list[FuturePath]
    lock_in_risk: LockInRisk
    reversibility: Reversibility

class LockInRisk(Enum):
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"

class Reversibility(Enum):
    REVERSIBLE = "reversible"
    DIFFICULT = "difficult"
    IRREVERSIBLE = "irreversible"
```

### C5: HorizonAlignmentEngine

**Purpose:** Evaluate horizon coherence and alignment.

**Responsibilities:**
- Calculate short-term, medium-term, long-term scores
- Detect misalignment across horizons
- Flag decisions that sacrifice long-term for short-term
- Ensure consistency with mission objectives

**Interface:**
```python
class HorizonAlignmentEngine:
    async def evaluate_alignment(
        self,
        decision: DecisionPacket,
        scenarios: FutureScenarios
    ) -> AlignmentAnalysis:
        """Evaluate alignment across time horizons."""
        pass
```

**Output Model:**
```python
class AlignmentAnalysis(BaseModel):
    decision_id: str
    short_term_score: float
    medium_term_score: float
    long_term_score: float
    coherence: float
    misalignment_detected: bool
    flagged_issues: list[str]

class TimeHorizon(Enum):
    SHORT = "short"   # 0-30 days
    MEDIUM = "medium" # 30-180 days
    LONG = "long"     # 180+ days
```

---

## Strategic Scoring Formula

### Strategic Score Calculation

```python
strategic_score = (
    long_term_value * 0.35 +
    resilience * 0.25 +
    optionality * 0.20 +
    horizon_alignment * 0.15 +
    systemic_safety * 0.05
) - (
    lock_in_risk * 0.30 +
    systemic_risk * 0.20
)
```

### Rating Bands

| Score Range | Rating | Meaning |
|------------|--------|---------|
| 0.85 - 1.00 | **Strong Strategic Recommendation** | Execute with confidence |
| 0.70 - 0.84 | **Strategically Acceptable** | Execute |
| 0.50 - 0.69 | **Caution / Conditional** | Redesign or defer if possible |
| 0.00 - 0.49 | **Strategically Weak** | Reject or redesign |

---

## Decision Policy for TORQ

### Complete Recommendation Ladder

```
IF economically weak (Layer 13):
    → REJECT

ELIF economically viable BUT illegitimate (Layer 14):
    → REJECT

ELIF economically viable AND legitimate BUT strategically weak (Layer 15):
    → REDESIGN / DEFER

ELIF economically viable AND legitimate AND strategically sound:
    → EXECUTE
```

This is the real value of Layers 13-15 together:
- **Layer 13:** Is this worth doing?
- **Layer 14:** Is this allowed?
- **Layer 15:** Is this smart over time?

---

## Validation Scenarios

### Scenario 1: Short-Term Win, Long-Term Loss

**Purpose:** Detect decisions that improve efficiency now but degrade resilience later.

**Setup:**
- Decision increases short-term efficiency by 30%
- Decision reduces long-term resilience by 50%
- Second-order consequences include fragility

**Expected Results:**
```
SecondOrderConsequenceAnalyzer.flags_future_harm == True
LongTermScore < ShortTermScore
StrategicScore < 0.50 (strategically weak)
FinalRecommendation == REDESIGN
```

### Scenario 2: Reversible vs Irreversible Decision

**Purpose:** Ensure reversibility is valued when paths are similar.

**Setup:**
- Path A: Reversible, medium value, 0.70 optionality
- Path B: Irreversible, slightly higher value, 0.20 optionality

**Expected Results:**
```
OptionalityPreservationEngine.favors(Path A)
LockInRisk(Path B) == CRITICAL
StrategicScore(Path A) > StrategicScore(Path B)
Recommendation == Path A (reversible)
```

### Scenario 3: Legitimate but Strategically Weak

**Purpose:** Ensure Layer 15 can downscore Layer 14-approved decisions.

**Setup:**
- Decision passes Layer 14 legitimacy check (score 0.75)
- Decision creates future fragility
- Optionality significantly reduced

**Expected Results:**
```
Layer14Score == 0.75 (passes)
Layer15Score < 0.50 (strategically weak)
StrategicRecommendation == REDESIGN
Reason == "Creates future lock-in"
```

### Scenario 4: Multi-Branch Uncertainty

**Purpose:** Handle competing futures with proper risk assessment.

**Setup:**
- 3 plausible futures with different probabilities
- Optimistic: 0.30 prob, high value
- Baseline: 0.50 prob, medium value
- Pessimistic: 0.20 prob, low value

**Expected Results:**
```
StrategicBranchComparator.ranks_by_risk_adjusted_value()
ConfidenceIntervals surfaced for each branch
Recommendation includes uncertainty quantification
MostProbable != Recommended (if risk-adjusted)
```

### Scenario 5: Forecast Calibration

**Purpose:** Track and improve projection accuracy over time.

**Setup:**
- Historical projection from 30 days ago
- Actual outcome now available
- Compare predicted vs actual

**Expected Results:**
```
ForesightAccuracy calculated and recorded
ConfidenceScores updated if calibration error > threshold
AssumptionReliability adjusted
CalibrationLoop.executed()
```

---

## Failure Modes

### FM-1: Short-Term Optimization Trap

**Description:** System repeatedly chooses fast local wins that degrade mission durability.

**Symptoms:**
- Short-term scores consistently high
- Long-term scores declining
- Strategic regret accumulating
- Optionality decreasing over time

**Mitigation:**
```python
if short_term_score > 0.80 and long_term_score < 0.50:
    trigger_warning("short_term_optimization_trap")
    apply_regret_penalty()
    weight_optionality_higher()
```

### FM-2: Overprojection

**Description:** System becomes too speculative and slows execution.

**Symptoms:**
- Analysis time > 30 seconds per decision
- Multiple deep horizons explored
- Confidence intervals too wide
- Decision paralysis

**Mitigation:**
```python
# Only run deep foresight for high-impact decisions
if decision.impact < IMPACT_THRESHOLD:
    time_horizons = [TimeHorizon.SHORT]  # Only short-term

# Confidence thresholds
if projection.confidence < 0.30:
    skip_branch()  # Don't evaluate uncertain futures
```

### FM-3: Lock-In Blindness

**Description:** System ignores future path narrowing.

**Symptoms:**
- Irreversible decisions treated as normal
- Optionality not tracked
- Commitments made without reversibility assessment

**Mitigation:**
```python
if decision.reversibility == Reversibility.IRREVERSIBLE:
    require_lock_in_risk_analysis()
    require_optionality_impact_statement()
    if optionality_retention < 0.50:
        block_decision("Excessive lock-in risk")
```

### FM-4: Strategic Hallucination

**Description:** Bad assumptions produce false future models.

**Symptoms:**
- Projections consistently wrong
- Confidence poorly calibrated
- Key assumptions violated

**Mitigation:**
```python
# Assumption traceability
for projection in projections:
    projection.assumptions.traced = True
    projection.assumptions.verify_against_history()

# Calibration feedback loop
if foresight_accuracy < 0.60:
    trigger_calibration_review()
    reduce_confidence_scores()
    require_human Oversight()
```

---

## CLI Specification

### Commands

**1. foresight evaluate** - Evaluate strategic quality of a decision
**2. foresight project** - Generate future scenarios
**3. foresight compare** - Compare multiple decision branches
**4. foresight analyze-consequences** - Analyze second/third-order effects
**5. foresight optionality** - Evaluate optionality retention
**6. foresight alignment** - Check horizon coherence
**7. foresight calibrate** - Update forecast models based on outcomes

```bash
torq foresight evaluate <DECISION_ID> [--explain]
torq foresight project <DECISION_ID> [--horizons SHORT,MEDIUM,LONG]
torq foresight compare <BRANCH_1> <BRANCH_2> ...
torq foresight analyze-consequences <DECISION_ID> [--depth N]
torq foresight optionality <DECISION_ID>
torq foresight alignment <DECISION_ID>
torq foresight calibrate [--window DAYS]
```

---

## Integration with Layer 14

### Decision Flow

```python
# After Layer 14 passes
if layer14_score.passes:
    # Layer 15 strategic evaluation
    strategic_result = await strategic_foresight_service.evaluate(
        decision=decision,
        layer14_result=layer14_result,
        layer13_allocation=allocation
    )

    if strategic_result.score < 0.50:
        return StrategicRecommendation.REDESIGN
    elif strategic_result.score < 0.70:
        return StrategicRecommendation.DEFER
    else:
        return StrategicRecommendation.EXECUTE
```

### Handoff from Layer 14

```python
class Layer14Output(BaseModel):
    legitimacy_score: float
    passes: bool
    violations: list[str]
    funded_missions: list[str]

class Layer15Input(BaseModel):
    layer14_output: Layer14Output
    decision_packet: DecisionPacket
    layer13_allocation: AllocationResult
```

---

## Success Criteria

Layer 15 is complete when:

1. ✅ All 5 engines implemented
2. ✅ Strategic scoring formula defined
3. ✅ All 5 validation scenarios passing
4. ✅ Failure modes documented with mitigation
5. ✅ Calibration plan defined
6. ✅ CLI commands specified
7. ✅ Integration with Layer 14 verified
8. ✅ No regression in Layer 13-14 functionality

---

## Dependencies

### Required Layers

- **Layer 13:** Economic Intelligence (allocation data)
- **Layer 14:** Constitutional Governance (legitimacy data)

### Required Data

- Historical decision outcomes (for calibration)
- Mission objective definitions (for alignment)
- System state models (for projection)

---

## Definition of Done

Agent 2 planning is complete when:

- [x] PRD is written
- [ ] Architecture doc is written (next)
- [ ] Validation scenarios are complete
- [ ] Scoring rules are written
- [ ] Failure modes are documented
- [ ] Calibration plan is documented
- [ ] Success criteria are measurable

---

**Document Status:** DRAFT
**Next:** LAYER15_ARCHITECTURE.md
