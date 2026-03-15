# TORQ Layer 15 - Strategic Foresight Architecture

**Version:** 0.15.0-planning
**Status:** DRAFT
**Depends On:** Layer 14 (Constitutional Governance) - v0.14.0
**Author:** Agent 2
**Date:** 2026-03-14

---

## Architecture Overview

Layer 15 provides **strategic foresight** for the TORQ system, evaluating the long-term consequences of present decisions before execution.

### The Third Gate

Layer 15 adds the final evaluation gate before execution:

```
Layer 13 (Economic Intelligence)
    → Is this worth doing?
Layer 14 (Constitutional Governance)
    → Is this allowed?
Layer 15 (Strategic Foresight) ← NEW
    → Is this smart over time?
    → EXECUTE
```

### Key Question

> **"What future does this decision create?"**

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        LAYER 15                                 │
│                    Strategic Foresight                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────┐    ┌────────────────┐    ┌──────────────┐ │
│  │   Scenario     │    │    Strategic   │    │  Second-     │ │
│  │  Projection    │───→│     Branch     │───→│  Order       │ │
│  │    Engine      │    │   Comparator   │    │  Consequence │ │
│  └────────────────┘    └────────────────┘    └──────────────┘ │
│                                                                  │
│  ┌────────────────┐    ┌────────────────┐    ┌──────────────┐ │
│  │    Optionality │    │    Horizon     │    │ Calibration  │ │
│  │ Preservation  │───→│    Alignment   │───→│     Loop      │ │
│  │     Engine     │    │     Engine     │    │              │ │
│  └────────────────┘    └────────────────┘    └──────────────┘ │
│                            ↓                                   │
│                   ┌────────────────┐                            │
│                   │ StrategicScore │                            │
│                   │    Calculator  │                            │
│                   └────────────────┘                            │
│                            ↓                                   │
│              ┌────────────────────────┐                        │
│              │ StrategicForesightService │                       │
│              │      (Orchestrator)     │                       │
│              └────────────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
           │
           ↓
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 6-11 (Execution)                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. ScenarioProjectionEngine

**Purpose:** Generate future scenarios from present state and decisions.

**Responsibilities:**
- Project future system states
- Generate multiple scenario branches (optimistic, baseline, pessimistic)
- Estimate probability distributions
- Track projection confidence

**Key Methods:**
```python
class ScenarioProjectionEngine:
    async def project_future(
        self,
        current_state: SystemState,
        decision: DecisionPacket,
        time_horizons: list[TimeHorizon]
    ) -> FutureScenarios:
        """Generate future scenarios based on decision."""

    async def project_branch(
        self,
        branch_id: str,
        decision: DecisionPacket
    ) -> BranchProjection:
        """Project a specific decision branch."""

    def calculate_confidence(
        self,
        projection: ScenarioProjection
    ) -> float:
        """Calculate confidence in projection."""
```

**Models:**
```python
class SystemState(BaseModel):
    timestamp: datetime
    active_missions: list[str]
    resource_allocation: dict[str, float]
    performance_metrics: dict[str, float]
    environmental_factors: dict[str, float]

class ScenarioProjection(BaseModel):
    scenario_id: str
    horizon: TimeHorizon
    timestamp: datetime
    probability: float
    expected_state: SystemState
    confidence: float
    key_assumptions: list[str]
    risk_factors: list[str]

class FutureScenarios(BaseModel):
    projection_id: str
    base_decision: str
    scenarios: list[ScenarioProjection]
    aggregate_confidence: float
```

---

### 2. StrategicBranchComparator

**Purpose:** Compare decision branches by long-term value.

**Responsibilities:**
- Evaluate multiple decision paths
- Calculate expected value per branch
- Risk-adjust comparison
- Rank by strategic quality
- Calculate regret metrics

**Key Methods:**
```python
class StrategicBranchComparator:
    async def compare_branches(
        self,
        branches: list[DecisionBranch]
    ) -> BranchComparison:
        """Compare branches by long-term value."""

    def calculate_expected_value(
        self,
        branch: DecisionBranch
    ) -> float:
        """Calculate risk-adjusted expected value."""

    def calculate_regret(
        self,
        chosen_branch: str,
        alternative_branches: list[str]
    ) -> float:
        """Calculate strategic regret."""
```

**Models:**
```python
class DecisionBranch(BaseModel):
    branch_id: str
    decision: DecisionPacket
    scenarios: FutureScenarios
    expected_value: float
    risk_level: RiskLevel

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
    short_term_score: float
    rank: int

class RegretAnalysis(BaseModel):
    strategic_regret: float
    best_alternative: str
    chosen_path_value: float
    best_path_value: float
```

---

### 3. SecondOrderConsequenceAnalyzer

**Purpose:** Estimate cascading consequences (second- and third-order effects).

**Responsibilities:**
- Trace consequence chains
- Identify delayed effects
- Map unintended outcomes
- Calculate cumulative impact

**Key Methods:**
```python
class SecondOrderConsequenceAnalyzer:
    async def analyze_consequences(
        self,
        decision: DecisionPacket,
        depth: int = 3
    ) -> ConsequenceAnalysis:
        """Analyze consequences up to N orders deep."""

    async def trace_consequence_chain(
        self,
        decision: DecisionPacket
    ) -> list[ConsequenceChain]:
        """Trace full consequence chains."""

    def detect_delayed_consequences(
        self,
        analysis: ConsequenceAnalysis
    ) -> list[Consequence]:
        """Find consequences with significant time delay."""
```

**Models:**
```python
class ConsequenceAnalysis(BaseModel):
    decision_id: str
    consequences: list[Consequence]
    chains: list[ConsequenceChain]
    total_impact: float
    risk_factors: list[str]
    delayed_consequences: list[Consequence]

class Consequence(BaseModel):
    order: int  # 1st, 2nd, 3rd
    consequence_id: str
    description: str
    impact: float  # -1.0 (harm) to 1.0 (benefit)
    probability: float
    time_delay: timedelta
    affected_components: list[str]
    assumptions: list[str]

class ConsequenceChain(BaseModel):
    chain_id: str
    steps: list[Consequence]
    cumulative_impact: float
    critical_path: bool
```

---

### 4. OptionalityPreservationEngine

**Purpose:** Evaluate how decisions affect future options.

**Responsibilities:**
- Count viable paths before/after decision
- Calculate optionality retention
- Detect lock-in situations
- Assess reversibility

**Key Methods:**
```python
class OptionalityPreservationEngine:
    async def evaluate_optionality(
        self,
        decision: DecisionPacket,
        current_paths: list[FuturePath]
    ) -> OptionalityAnalysis:
        """Evaluate optionality impact."""

    def calculate_lock_in_risk(
        self,
        decision: DecisionPacket
    ) -> LockInRisk:
        """Assess lock-in risk level."""

    def assess_reversibility(
        self,
        decision: DecisionPacket
    ) -> Reversibility:
        """Assess decision reversibility."""
```

**Models:**
```python
class OptionalityAnalysis(BaseModel):
    decision_id: str
    initial_paths: int
    remaining_paths: int
    retention_rate: float
    lost_paths: list[FuturePath]
    lock_in_risk: LockInRisk
    reversibility: Reversibility
    optionality_score: float

class FuturePath(BaseModel):
    path_id: str
    description: str
    requirements: list[str]
    feasibility: float
    value_potential: float

class LockInRisk(Enum):
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"

class Reversibility(Enum):
    REVERSIBLE = "reversible"
    DIFFICULT = "difficult"  # Possible with cost
    IRREVERSIBLE = "irreversible"
```

---

### 5. HorizonAlignmentEngine

**Purpose:** Ensure consistency across short, medium, long time horizons.

**Responsibilities:**
- Calculate per-horizon scores
- Detect misalignment
- Flag horizon sacrifices
- Ensure mission consistency

**Key Methods:**
```python
class HorizonAlignmentEngine:
    async def evaluate_alignment(
        self,
        decision: DecisionPacket,
        scenarios: FutureScenarios
    ) -> AlignmentAnalysis:
        """Evaluate alignment across time horizons."""

    def calculate_horizon_score(
        self,
        scenario: ScenarioProjection,
        horizon: TimeHorizon
    ) -> float:
        """Calculate score for specific horizon."""

    def detect_misalignment(
        self,
        scores: dict[TimeHorizon, float]
    ) -> list[MisalignmentIssue]:
        """Detect horizon misalignment."""
```

**Models:**
```python
class AlignmentAnalysis(BaseModel):
    decision_id: str
    short_term_score: float
    medium_term_score: float
    long_term_score: float
    coherence: float
    misalignment_detected: bool
    flagged_issues: list[MisalignmentIssue]
    strategic_alignment: StrategicAlignment

class TimeHorizon(Enum):
    SHORT = "short"   # 0-30 days
    MEDIUM = "medium" # 30-180 days
    LONG = "long"     # 180+ days

class StrategicAlignment(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    MIXED = "mixed"
    POOR = "poor"
    CRITICAL = "critical"

class MisalignmentIssue(BaseModel):
    issue_type: str
    description: str
    severity: str
    affected_horizons: list[TimeHorizon]
```

---

## Service Integration

### StrategicForesightService

**Purpose:** Orchestrate all Layer 15 engines.

**Key Methods:**
```python
class StrategicForesightService:
    def __init__(
        self,
        projection_engine: ScenarioProjectionEngine,
        branch_comparator: StrategicBranchComparator,
        consequence_analyzer: SecondOrderConsequenceAnalyzer,
        optionality_engine: OptionalityPreservationEngine,
        alignment_engine: HorizonAlignmentEngine
    ):

    async def evaluate_decision(
        self,
        decision: DecisionPacket,
        layer14_result: Layer14Output,
        layer13_allocation: AllocationResult
    ) -> StrategicEvaluation:
        """Complete strategic evaluation of a decision."""

    async def generate_strategic_recommendation(
        self,
        evaluation: StrategicEvaluation
    ) -> StrategicRecommendation:
        """Generate final recommendation."""
```

**Models:**
```python
class StrategicEvaluation(BaseModel):
    decision_id: str
    strategic_score: float
    band: StrategicBand
    component_scores: ComponentScores
    recommendation: StrategicRecommendation
    confidence: float
    warnings: list[str]

class ComponentScores(BaseModel):
    long_term_value: float
    resilience: float
    optionality: float
    horizon_alignment: float
    systemic_safety: float
    lock_in_risk: float
    systemic_risk: float

class StrategicBand(Enum):
    STRONG = "strong"           # 0.85-1.00
    ACCEPTABLE = "acceptable"   # 0.70-0.84
    CAUTION = "caution"         # 0.50-0.69
    WEAK = "weak"               # 0.00-0.49

class StrategicRecommendation(Enum):
    EXECUTE = "execute"
    REDESIGN = "redesign"
    DEFER = "defer"
    REJECT = "reject"
```

---

## Data Flow

### Input: Layer 14 Output

```python
class Layer14Output(BaseModel):
    legitimacy_score: float
    passes: bool
    violations: list[str]
    funded_missions: list[str]
    audit_record_id: str
```

### Output: Strategic Evaluation

```python
class StrategicEvaluation(BaseModel):
    decision_id: str
    layer14_compatible: bool
    strategic_score: float
    band: StrategicBand
    recommendation: StrategicRecommendation
    analysis: {
        "projections": FutureScenarios,
        "branches": BranchComparison,
        "consequences": ConsequenceAnalysis,
        "optionality": OptionalityAnalysis,
        "alignment": AlignmentAnalysis
    }
```

---

## Performance Requirements

| Engine | Operation | Target Latency |
|--------|-----------|-----------------|
| ScenarioProjectionEngine | Single projection | <50ms |
| StrategicBranchComparator | Compare 3 branches | <30ms |
| SecondOrderConsequenceAnalyzer | Depth 3 analysis | <100ms |
| OptionalityPreservationEngine | Evaluate optionality | <20ms |
| HorizonAlignmentEngine | Evaluate alignment | <20ms |
| StrategicForesightService | Full evaluation | <200ms |

---

## Storage Requirements

### Scenario Cache
- Store generated scenarios for replay
- TTL: 7 days
- Retention: Configurable

### Calibration Data
- Store prediction vs actual comparisons
- Retention: 1 year minimum
- Used for accuracy tracking

### Projection Registry
- Track all projections made
- Enable outcome comparison
- Support calibration loop

---

## Security Considerations

### SC-1: Gaming Prevention

**Threat:** Agents manipulate decisions to optimize strategic score without genuine strategic merit.

**Mitigation:**
- Multi-component scoring (hard to game all)
- Pattern detection for optimization behavior
- Human oversight for critical decisions

### SC-2: Projection Manipulation

**Threat:** Bad actors inject false assumptions to skew projections.

**Mitigation:**
- Assumption traceability
- Assumption verification against historical data
- Reputation scoring for assumption sources

### SC-3: Calibration Attacks

**Threat:** Manipulating calibration data to influence future projections.

**Mitigation:**
- Calibration data immutability
- Multi-source verification
- Anomaly detection in calibration

---

## Error Handling

### E-1: Projection Failure

**Scenario:** Cannot generate valid projection (insufficient data).

**Fallback:** Use simpler projection model, flag low confidence.

### E-2: Confidence Overflow

**Scenario:** All projections have very low confidence.

**Action:** Block decision, require human review.

### E-3: Conference Explosion

**Scenario:** Consequence chain analysis produces exponential combinations.

**Mitigation:** Depth cap (max 3 orders), pruning of low-probability branches.

---

## Layer Dependencies

```
Layer 15 depends on:
  Layer 13 (Economic Intelligence) - allocation data
  Layer 14 (Constitutional Governance) - legitimacy data
  Layer 12 (Federation) - multiple perspectives

Layer 15 enables:
  Layer 6-11 (Execution) - with strategic pre-filtering
```

---

## Extension Points

### Future Enhancements

1. **Human-in-the-Loop Calibration** - Expert feedback on projections
2. **Monte Carlo Simulation** - Probabilistic scenario generation
3. **Machine Learning Projections** - Learned outcome prediction
4. **Real-Time Horizon Tracking** - Continuous alignment monitoring
5. **Cross-Layer Optimization** - Joint optimization across layers

---

**Document Status:** DRAFT
**Next:** VALIDATION_SCENARIOS.md
