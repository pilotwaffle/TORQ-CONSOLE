# Layer 13 Validation Approach
## TORQ Economic Intelligence System

**Version:** 0.13.0-planning
**Status:** APPROACH DEFINED
**Author:** Agent 2
**Date:** 2026-03-14

---

## Overview

This document describes the testing strategy for Layer 13 Economic Intelligence. The validation approach ensures that the economic decision-making system produces correct, efficient, and explainable allocations.

---

## Testing Philosophy

### Principles

1. **Scenario-First Validation** - Tests mirror real-world use cases
2. **Quantifiable Success** - Every test has measurable pass/fail criteria
3. **Economic Theory Foundation** - Scenarios grounded in real economic principles
4. **TORQ Context** - Scenarios reflect actual TORQ mission execution
5. **Fast Feedback** - Unit tests run in seconds, integration in minutes

### Testing Pyramid

```
         /\
        /  \     E2E Tests (5%)
       /----\    - Full pipeline validation
      /------\   - Scenario-based tests
     /--------\  - Integration with Layers 8-12
    /----------\
   /------------\
  /--------------\ Unit Tests (70%)
 /                \ - Individual engine tests
/__________________\ - Score calculation tests
                     - Data model validation
```

---

## Unit Testing Strategy

### Scope

Unit tests validate individual components in isolation.

### Coverage Areas

#### 1. Score Calculation (models.py)

```python
class TestEconomicScoreCalculation:
    """Test score calculation through Layers 1-4."""

    def test_base_value_weights(self):
        """Base value uses correct weights."""
        # user_value: 60%, urgency: 30%, strategic_fit: 10%
        proposal = MissionProposal(
            user_value=0.8,
            urgency=0.5,
            strategic_fit=0.7,
        )
        score = engine._calculate_base_value(proposal)
        expected = 0.6*0.8 + 0.3*0.5 + 0.1*0.7  # 0.67
        assert abs(score - expected) < 0.01

    def test_execution_modifier_confidence(self):
        """Execution modifier affected by confidence."""
        # Confidence 0.9 -> modifier > 1.0
        # Confidence 0.3 -> modifier < 1.0
        assert modifier_high_conf > 1.0
        assert modifier_low_conf < 1.0

    def test_efficiency_calculation(self):
        """Efficiency = value / cost."""
        score = EconomicScore(quality_adjusted_value=0.8)
        efficiency = prioritizer._calculate_efficiency(score, 400, constraints)
        assert abs(efficiency - 0.002) < 0.0001
```

#### 2. Feasibility Gate (Layer 1)

```python
class TestFeasibilityGate:
    """Test Layer 1 hard filters."""

    def test_budget_check(self):
        """Reject proposals exceeding budget."""
        proposal = MissionProposal(estimated_cost=1500)
        constraints = ResourceConstraints(budget_remaining=1000)
        eligible, reason = engine._apply_feasibility_gate(proposal, constraints)
        assert eligible == False
        assert "budget" in reason.lower()

    def test_confidence_threshold(self):
        """Reject proposals below confidence threshold."""
        federation = FederationResult(confidence=0.3)
        constraints = ResourceConstraints(min_confidence_threshold=0.5)
        eligible, reason = engine._apply_feasibility_gate(
            proposal, constraints, federation
        )
        assert eligible == False
        assert "confidence" in reason.lower()

    def test_deadline_validation(self):
        """Reject proposals with impossible deadlines."""
        proposal = MissionProposal(
            estimated_duration_seconds=3600,
            deadline=datetime.utcnow() + timedelta(minutes=30)
        )
        eligible, reason = engine._apply_feasibility_gate(proposal, constraints)
        assert eligible == False
        assert "deadline" in reason.lower()
```

#### 3. Allocation Engine (Layer 5)

```python
class TestAllocationEngine:
    """Test Layer 5 budget allocation."""

    def test_knapsack_selection(self):
        """Select optimal mission set under budget."""
        # Should pick highest efficiency missions
        result = await engine.allocate_budget(proposals, constraints, costs)
        assert result.funded_total_cost <= constraints.total_budget

    def test_no_budget_exceed(self):
        """Never allocate more than budget."""
        for _ in range(100):  # Test with random data
            result = await engine.allocate_budget(random_proposals(), constraints, costs)
            assert result.funded_total_cost <= constraints.total_budget

    def test_budget_utilization(self):
        """Budget should be efficiently utilized."""
        result = await engine.allocate_budget(proposals, constraints, costs)
        assert result.budget_utilization >= 0.85  # At least 85% used
```

#### 4. Opportunity Cost Model

```python
class TestOpportunityCostModel:
    """Test opportunity cost calculation."""

    def test_opportunity_cost_positive(self):
        """Opportunity cost is non-negative."""
        costs = await model.calculate_opportunity_costs(accepted, rejected, budget, costs)
        for cost in costs.values():
            assert cost.opportunity_cost >= 0

    def test_best_alternative_selected(self):
        """Best alternative is closest in value."""
        costs = await model.calculate_opportunity_costs(accepted, rejected, budget, costs)
        # Verify best accepted is closest to rejected
        assert result.best_accepted_alternative_id is not None

    def test_strategic_impact_levels(self):
        """Strategic impact correctly assessed."""
        # High cost ratio -> high impact
        # Low cost ratio -> low impact
        assert high_cost_result.strategic_impact in ["medium", "high"]
        assert low_cost_result.strategic_impact == "low"
```

---

## Integration Testing Strategy

### Scope

Integration tests validate interaction between components and with Layers 8-12.

### Test Areas

#### 1. Full Pipeline Integration

```python
class TestFullPipeline:
    """Test complete Layers 1-5 pipeline."""

    async def test_end_to_end_allocation(self):
        """Run full pipeline from proposals to allocation."""
        # Input: Mission proposals
        proposals = [
            MissionProposal(mission_id="m1", user_value=0.8, estimated_cost=200),
            MissionProposal(mission_id="m2", user_value=0.6, estimated_cost=300),
        ]

        # Layer 1-3: Evaluation
        evaluation_engine = create_evaluation_engine()
        scores = [
            await evaluation_engine.evaluate_proposal(p, constraints, federation)
            for p in proposals
        ]

        # Layer 4: Prioritization
        prioritization_engine = create_prioritization_engine()
        ranked = await prioritization_engine.rank_by_efficiency(scores, constraints, costs)

        # Layer 5: Allocation
        allocation_engine = create_allocation_engine()
        result = await allocation_engine.allocate_budget(ranked, constraints, costs)

        # Opportunity Cost
        opportunity_model = create_opportunity_cost_model()
        costs_map = await opportunity_model.calculate_opportunity_costs(
            [s for s in ranked if s.candidate_id in result.funded_mission_ids],
            [s for s in ranked if s.candidate_id not in result.funded_mission_ids],
            constraints.total_budget,
            costs
        )

        # Validate
        assert result.funded_total_cost <= constraints.total_budget
        assert result.budget_utilization >= 0.85
```

#### 2. Layer 12 Integration

```python
class TestLayer12Integration:
    """Test integration with Layer 12 federation."""

    async def test_federation_confidence_used(self):
        """Federation confidence affects evaluation."""
        proposal = MissionProposal(requires_validation=True)

        # High confidence
        federation_high = FederationResult(confidence=0.9)
        score_high = await engine.evaluate_proposal(proposal, constraints, federation_high)

        # Low confidence
        federation_low = FederationResult(confidence=0.4)
        score_low = await engine.evaluate_proposal(proposal, constraints, federation_low)

        # High confidence should have higher quality-adjusted value
        assert score_high.quality_adjusted_value > score_low.quality_adjusted_value
```

---

## Scenario-Based Testing

### Scenario Test Structure

Each scenario test follows this structure:

```python
class TestScenario1_BudgetConstrained:
    """Scenario 1: Constrained Budget Allocation."""

    @pytest.fixture
    def scenario_data(self):
        """Load scenario test data."""
        return load_test_data("scenario1_budget_constrained.json")

    @pytest.fixture
    def expected_output(self):
        """Load expected outputs."""
        return load_expected_output("scenario1_expected.json")

    def test_budget_not_exceeded(self, scenario_data, expected_output):
        """Budget is never exceeded."""
        result = run_allocation(scenario_data)
        assert result.funded_total_cost <= scenario_data["budget"]

    def test_high_efficiency_funded(self, scenario_data):
        """Higher efficiency missions funded first."""
        result = run_allocation(scenario_data)
        funded_efficiencies = get_efficiencies(result.funded_mission_ids)
        assert is_sorted_descending(funded_efficiencies)

    def test_budget_utilization(self, scenario_data):
        """Budget efficiently utilized."""
        result = run_allocation(scenario_data)
        assert result.budget_utilization >= 0.85
```

---

## Performance Testing

### Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Single proposal evaluation | < 10ms | Time per evaluation |
| 100 proposals prioritization | < 50ms | Total prioritization time |
| 100 proposals allocation | < 100ms | Total allocation time |
| Opportunity cost calculation | < 200ms | Full calculation time |

### Performance Tests

```python
class TestPerformance:
    """Performance regression tests."""

    @pytest.mark.performance
    def test_evaluation_latency(self, benchmark):
        """Single proposal evaluation is fast."""
        proposal = create_test_proposal()
        result = benchmark(
            engine.evaluate_proposal,
            proposal, constraints, federation
        )
        assert result is not None

    @pytest.mark.performance
    def test_prioritization_latency(self):
        """100 proposals prioritization is fast."""
        proposals = [create_test_proposal() for _ in range(100)]
        start = time.time()
        result = await prioritizer.rank_by_efficiency(proposals, constraints, costs)
        elapsed = time.time() - start
        assert elapsed < 0.05

    @pytest.mark.performance
    def test_allocation_latency(self):
        """100 proposals allocation is fast."""
        proposals = [create_test_proposal() for _ in range(100)]
        start = time.time()
        result = await allocator.allocate_budget(proposals, constraints, costs)
        elapsed = time.time() - start
        assert elapsed < 0.10
```

---

## Regression Testing

### Automated Regression Suite

Every commit triggers:

```yaml
# .github/workflows/layer13-tests.yml
name: Layer 13 Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run unit tests
        run: pytest tests/layer13/unit/ -v --coverage
      - name: Run integration tests
        run: pytest tests/layer13/integration/ -v
      - name: Run scenario tests
        run: pytest tests/layer13/scenarios/ -v
      - name: Run performance tests
        run: pytest tests/layer13/performance/ -v -m performance
      - name: Check coverage
        run: |
          coverage report --fail-under=80
```

### Regression Prevention

Each scenario has expected outputs stored as fixtures:

```python
# tests/layer13/fixtures/scenario1_expected.json
{
    "funded_mission_ids": ["m5", "m1", "m4"],
    "funded_total_cost": 750.0,
    "budget_utilization": 0.75,
    "queued_mission_ids": ["m3", "m2"]
}
```

Tests compare actual output to expected:

```python
def test_regression_scenario1(scenario_data):
    result = run_allocation(scenario_data)
    expected = load_fixture("scenario1_expected.json")

    assert result.funded_mission_ids == expected["funded_mission_ids"]
    assert abs(result.funded_total_cost - expected["funded_total_cost"]) < 1.0
```

---

## Validation Metrics

### Quality Metrics

| Metric | Target | Formula |
|--------|--------|---------|
| Test Coverage | ≥ 80% | lines_covered / total_lines |
| Pass Rate | 100% | tests_passed / tests_run |
| Performance Budget | 100% | tests_within_threshold / performance_tests |
| Regression Rate | 0% | new_failures / total_runs |

### Economic Quality Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| Allocation Efficiency | ≥ 0.8 | Value per dollar spent |
| Budget Utilization | 85-95% | Budget percentage used |
| Regret Ratio | < 15% | Regret / total value |
| Decision Transparency | 100% | Explainable decisions |

---

## Continuous Integration

### CI Pipeline Stages

```
┌─────────────────────────────────────────────────────────────┐
│  1. Unit Tests (30 seconds)                                 │
│     ├─ Score calculation tests                              │
│     ├─ Feasibility gate tests                               │
│     ├─ Allocation engine tests                              │
│     └─ Opportunity cost tests                               │
├─────────────────────────────────────────────────────────────┤
│  2. Integration Tests (60 seconds)                          │
│     ├─ Full pipeline tests                                  │
│     ├─ Layer 12 integration tests                           │
│     └─ Data model validation tests                          │
├─────────────────────────────────────────────────────────────┤
│  3. Scenario Tests (90 seconds)                             │
│     ├─ Scenario 1-7 tests                                   │
│     ├─ Expected output validation                           │
│     └─ Regression checks                                    │
├─────────────────────────────────────────────────────────────┤
│  4. Performance Tests (60 seconds)                          │
│     ├─ Latency benchmarks                                   │
│     ├─ Scalability tests                                    │
│     └─ Memory profiling                                    │
├─────────────────────────────────────────────────────────────┤
│  5. Report Generation (30 seconds)                          │
│     ├─ Coverage report                                      │
│     ├─ Performance report                                   │
│     └─ Quality metrics                                      │
└─────────────────────────────────────────────────────────────┘
```

### Total Runtime: ~5 minutes

---

## Test Data Management

### Fixtures

Test fixtures stored in `tests/layer13/fixtures/`:

```
tests/layer13/fixtures/
├── proposals/
│   ├── scenario1_proposals.json
│   ├── scenario2_proposals.json
│   └── ...
├── federation/
│   ├── high_confidence.json
│   ├── low_confidence.json
│   └── ...
└── expected/
    ├── scenario1_output.json
    ├── scenario2_output.json
    └── ...
```

### Data Generation

Helper functions for generating test data:

```python
def create_test_proposal(**overrides):
    """Create a test proposal with defaults."""
    defaults = {
        "mission_id": "test_mission",
        "mission_type": "test",
        "user_value": 0.5,
        "urgency": 0.5,
        "strategic_fit": 0.5,
        "estimated_cost": 100.0,
    }
    defaults.update(overrides)
    return MissionProposal(**defaults)

def create_test_constraints(**overrides):
    """Create test constraints with defaults."""
    defaults = {
        "total_budget": 1000.0,
        "budget_remaining": 1000.0,
    }
    defaults.update(overrides)
    return ResourceConstraints(**defaults)
```

---

## Debugging Failed Tests

### Common Issues

| Issue | Symptom | Fix |
|-------|---------|-----|
| Budget exceeded | funded_total_cost > budget | Check knapsack logic |
| Wrong efficiency | Incorrect ranking | Check value/cost calculation |
| Missing bonus | Required type not prioritized | Check strategic bonus logic |
| Wrong modifier | Confidence not applied | Check execution modifier formula |

### Debug Mode

Run tests with verbose output:

```bash
# Verbose test output
pytest tests/layer13/ -v -s

# Specific scenario
pytest tests/layer13/scenarios/test_scenario1.py -v

# With coverage
pytest tests/layer13/ --cov=torq_console.layer13 --cov-report=html
```

---

## Acceptance Criteria

Layer 13 is considered validated when:

- [ ] All unit tests passing (≥ 80% coverage)
- [ ] All integration tests passing
- [ ] All 7 scenarios validated
- [ ] All performance benchmarks met
- [ ] Zero regression failures
- [ ] Documentation complete

---

**Document Status:** COMPLETE
**Next:** Create CLI specification document
