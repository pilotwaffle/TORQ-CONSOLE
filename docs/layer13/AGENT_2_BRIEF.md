# Agent 2 Brief: Layer 13 Planning & Validation
## Economic Intelligence PRD and Validation Framework

**Status:** Layer 12 CLOSED at v0.12-final
**Assignment:** Layer 13 Planning and Validation Design
**Priority:** CRITICAL
**Date:** 2026-03-14

---

## Mission Statement

Define **what "good" economic decisions mean** for TORQ and create the validation framework to prove Layer 13 makes them. You are **NOT** to modify Layer 12 code unless a regression is confirmed.

---

## Layer 13 Purpose Validation

Layer 13 must solve these core problems:

1. **Constrained Budget Allocation** - Given $X budget, choose actions that maximize total value
2. **Value vs Urgency Tradeoffs** - When to prioritize urgent but lower-value actions
3. **Opportunity Cost Awareness** - Understand what's sacrificed by choosing A over B
4. **Low-Confidence Rejection** - Avoid high-cost, low-confidence actions even with high expected value

---

## Deliverables

### 1. Layer 13 PRD (`docs/layer13/LAYER13_PRD.md`)

Create comprehensive PRD covering:

#### 1.1 Product Requirements

- **Problem Statement**: Why TORQ needs economic intelligence
- **Success Criteria**: What "good" decisions look like quantitatively
- **User Stories**: When Layer 13 is invoked in TORQ workflows
- **Failure Modes**: What bad decisions Layer 13 must avoid

#### 1.2 Functional Requirements

- **FR-1**: Evaluate actions on cost, value, urgency, confidence
- **FR-2**: Allocate budget across competing actions
- **FR-3**: Calculate opportunity costs for comparisons
- **FR-4**: Recommend execute/defer/reject with explanations
- **FR-5**: Consume outputs from Layers 8-12

#### 1.3 Non-Functional Requirements

- **Performance**: Evaluate 100 actions in <1 second
- **Explainability**: Every recommendation must have a rationale
- **Configurability**: Risk tolerance and budget must be adjustable
- **Testability**: All scoring components must be independently testable

#### 1.4 Data Requirements

Define input/output contracts for:
- EconomicContext (budget, constraints)
- ActionCandidate (from Layer 8)
- EconomicScore (evaluation output)
- AllocationPlan (resource distribution)

#### 1.5 Integration Requirements

- How Layer 13 calls Layers 8-12 for context
- How Layer 13 returns prioritized actions to TORQ executor
- Backward compatibility (TORQ works without Layer 13)

---

### 2. Validation Scenarios

Create test scenarios that prove Layer 13 makes correct economic decisions.

#### Scenario 1: Constrained Budget Allocation

**Setup:**
```
Budget: 100 units
Actions:
  - Action A: Cost 80, Value 100, Urgency 0.5
  - Action B: Cost 50, Value 70, Urgency 0.5
  - Action C: Cost 30, Value 50, Urgency 0.5
```

**Expected Outcome:**
```
Layer 13 should choose Actions B + C (total cost 80, total value 120)
NOT Action A alone (cost 80, value 100)
Reasoning: Higher total value within budget
```

**Validation Point:**
```python
def test_constrained_budget_allocation():
    plan = await allocate(budget=100, actions=[A, B, C])
    assert plan.allocated_actions == ["B", "C"]
    assert plan.expected_total_value == 120
```

#### Scenario 2: High-Value vs High-Urgency Tradeoff

**Setup:**
```
Budget: 50 units
Actions:
  - Action A: Cost 40, Value 90, Urgency 0.3 (high value, low urgency)
  - Action B: Cost 40, Value 60, Urgency 0.9 (lower value, high urgency)
```

**Expected Outcome:**
```
Decision depends on configured urgency_weight:
- If urgency_weight > 0.6: Choose B
- If urgency_weight <= 0.6: Choose A
Layer 13 must EXPLAIN why it chose either
```

**Validation Point:**
```python
def test_urgency_value_tradeoff():
    score_a = await evaluate(A, alternatives=[B])
    score_b = await evaluate(B, alternatives=[A])

    # Scores should reflect urgency_weight
    # Recommendation must have rationale
    assert score_a.recommendation in ["execute", "defer"]
    assert len(score_a.rationale) > 0
```

#### Scenario 3: Opportunity Cost Comparison

**Setup:**
```
Budget: 100 units (allows multiple actions)
Actions:
  - Action A: Cost 100, Value 150
  - Action B: Cost 50, Value 90
  - Action C: Cost 50, Value 90
```

**Expected Outcome:**
```
Layer 13 should recognize:
- Choosing A has opportunity cost = 180 (value of B+C) - 150 = 30
- Choosing B+C has total value 180
Recommendation: Choose B+C, defer A
Reasoning: Higher total value, lower opportunity cost
```

**Validation Point:**
```python
def test_opportunity_cost_recognition():
    score_a = await evaluate(A, alternatives=[B, C], budget=100)
    assert score_a.opportunity_cost == 30  # 180 - 150
    assert score_a.recommendation == "defer"
```

#### Scenario 4: Low-Confidence Rejection

**Setup:**
```
Actions:
  - Action A: Cost 80, Value 200, Confidence 0.2 (high value, low confidence)
  - Action B: Cost 30, Value 50, Confidence 0.9 (lower value, high confidence)
```

**Expected Outcome:**
```
Layer 13 should reject Action A despite high expected value:
- Risk-adjusted value = 200 × 0.2 = 40
- Risk-adjusted value of B = 50 × 0.9 = 45
Recommendation: Execute B, reject A
Reasoning: Low confidence kills high-value action
```

**Validation Point:**
```python
def test_low_confidence_rejection():
    score_a = await evaluate(A, alternatives=[B])
    assert score_a.risk_adjusted_value < score_b.risk_adjusted_value
    assert score_a.recommendation == "reject"
```

#### Scenario 5: Budget Exhaustion Edge Case

**Setup:**
```
Budget: 100 units
Actions:
  - Action A: Cost 95, Value 150
  - Action B: Cost 10, Value 20
```

**Expected Outcome:**
```
Layer 13 should choose A only (budget nearly exhausted, but A dominates)
NOT choose B (wastes budget capacity)
Recommendation: Execute A, defer B
```

#### Scenario 6: Regret Minimization

**Setup:**
```
Budget: 100 units
Actions with probabilistic outcomes:
  - Action A: Cost 50, Value 100, p(success) = 0.5
  - Action B: Cost 50, Value 60, p(success) = 0.9
```

**Expected Outcome:**
```
Expected values:
- A: 100 × 0.5 = 50
- B: 60 × 0.9 = 54
Layer 13 should choose B (higher expected value)
Expected regret if A chosen: 54 - 50 = 4
```

---

### 3. Validation Definitions

Define quantitative metrics for economic decision quality:

#### 3.1 Allocation Efficiency

```
Efficiency = (Actual Total Value / Maximum Possible Value)
Target: Efficiency > 0.8 for greedy allocation
Target: Efficiency > 0.9 for optimal allocation
```

#### 3.2 Regret Minimization

```
Regret = Value of best excluded action - Value of worst included action
Target: Regret < 10% of total budget
```

#### 3.3 Confidence Calibration

```
Calibration Error = |Predicted Success Rate - Actual Success Rate|
Target: Calibration Error < 0.1
```

#### 3.4 Recommendation Consistency

```
Consistency = (Same recommendation on repeated runs) / (Total runs)
Target: Consistency > 0.95 for same inputs
```

---

### 4. CLI Specification

Define command-line interface for Layer 13 simulations:

```bash
# Run economic evaluation on action set
torq-economic evaluate \
  --budget 100 \
  --urgency-weight 0.5 \
  --risk-tolerance 0.7 \
  --actions actions.json

# Run allocation optimization
torq-economic allocate \
  --budget 100 \
  --strategy greedy \
  --actions actions.json

# Run validation scenarios
torq-economic validate \
  --scenario constrained_budget \
  --expected-outcome outcomes/constrained_budget.json

# Compare scoring configurations
torq-economic compare \
  --actions actions.json \
  --configs config_a.yaml config_b.yaml
```

---

### 5. Test Harness Specification

Define validation framework structure:

```python
# tests/layer13/test_economic_validation.py

class EconomicValidationHarness:
    """Test harness for Layer 13 validation."""

    async def run_scenario(
        self,
        scenario: EconomicScenario,
        config: EconomicConfig,
    ) -> ValidationResult:
        """Run a single validation scenario."""
        pass

    async def run_all_scenarios(
        self,
        config: EconomicConfig,
    ) -> List[ValidationResult]:
        """Run all validation scenarios."""
        pass

    def generate_report(
        self,
        results: List[ValidationResult],
    ) -> ValidationReport:
        """Generate validation report."""
        pass

@dataclass
class EconomicScenario:
    """Validation scenario definition."""
    name: str
    description: str
    budget: float
    actions: List[ActionCandidate]
    expected_outcome: ExpectedOutcome
    validation_criteria: List[ValidationCriterion]

@dataclass
class ExpectedOutcome:
    """Expected outcome for validation."""
    selected_actions: List[str]
    deferred_actions: List[str]
    rejected_actions: List[str]
    minimum_total_value: float
    maximum_regret: float
```

---

### 6. Example Input/Output Files

Create example data files:

```
tests/layer13/fixtures/
├── simple_allocation.json
├── urgency_tradeoff.json
├── opportunity_cost.json
├── low_confidence_rejection.json
└── budget_exhaustion.json
```

Each fixture contains:
- Input actions with all required fields
- Budget constraint
- Expected output (for validation)

---

## Design Considerations

### What Makes a "Good" Economic Decision?

1. **Maximizes total value** within budget constraints
2. **Minimizes regret** from excluded alternatives
3. **Accounts for risk** through confidence-based adjustment
4. **Balances urgency** with long-term value
5. **Is explainable** - rationale can be articulated

### Common Failure Modes to Detect

1. **Budget overspend** - Selecting actions that exceed budget
2. **Low-value inclusion** - Including actions with negative net benefit
3. **High-regret exclusion** - Excluding high-value actions for low-value ones
4. **Confidence blindness** - Ignoring low confidence when making high-stakes choices
5. **Urgency tunnel vision** - Prioritizing urgency at expense of all value

---

## Success Criteria

Your planning is complete when:

1. ✅ PRD covers all functional/non-functional requirements
2. ✅ 6+ validation scenarios defined with expected outcomes
3. ✅ Validation metrics quantitatively defined
4. ✅ CLI specification documented
5. ✅ Test harness structure specified
6. ✅ Example fixture files created
7. ✅ No Layer 12 code was modified

---

## Next Steps (After This Brief)

1. Write LAYER13_PRD.md
2. Define all 6 validation scenarios with concrete numbers
3. Create validation metrics formulas
4. Specify CLI commands
5. Create example fixture JSON files
6. Design test harness structure

**DO NOT proceed to implementation** until Agent 1 delivers the architecture scaffold. Your validation must align with their implementation.

---

## Checkpoint

After completing this brief, you will have:

- [ ] PRD document created
- [ ] Validation scenarios defined
- [ ] Expected outcomes specified
- [ ] Validation metrics defined
- [ ] CLI specification written
- [ ] Example fixtures created

At this point, **STOP** and synchronize with Agent 1. Compare PRD against architecture, lock shared models, align scoring formulas, and verify integration points.

---

## Synchronization Meeting Agenda

When both agents complete their briefs, meet to:

1. **Compare PRD vs Architecture** - Ensure requirements match design
2. **Lock Shared Models** - Agree on EconomicContext, ActionCandidate, EconomicScore
3. **Align Scoring Formulas** - Verify PRD scenarios match engine logic
4. **Validate Integration Points** - Confirm Layer 8-12 consumption approach
5. **Sign Off** - Both agents approve combined specification

After synchronization, implementation can proceed in parallel without drift.

---

**Agent 2, you own defining "correct" for Layer 13. Specify it clearly, validate it thoroughly, and the implementation will follow.**
