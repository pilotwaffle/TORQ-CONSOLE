# Agent 1 Brief: Layer 13 Core Architecture
## Economic Intelligence Engine Scaffolding

**Status:** Layer 12 CLOSED at v0.12-final
**Assignment:** Layer 13 Core Architecture
**Priority:** CRITICAL
**Date:** 2026-03-14

---

## Mission Statement

Build the core architecture for Layer 13 - Economic Intelligence. This layer enables TORQ to decide **what actions deserve resources** by evaluating costs, value, urgency, and opportunity costs.

You are **NOT** to modify Layer 12 code unless a regression is confirmed.

---

## Layer 13 Purpose

Layer 13 sits above Layers 8-12 and consumes their outputs to make economic decisions:

```
Layer 8  (Meta-Control)     → Action candidates
Layer 9  (Execution)        → Execution costs
Layer 10 (Verification)     → Confidence scores
Layer 11 (Learning)         → Success probabilities
Layer 12 (Federation)       → Network-wide consensus

              ↓

Layer 13 (Economic Intelligence)
    → Rank actions by economic value
    → Allocate constrained resources
    → Calculate opportunity costs
    → Prioritize budget-aware choices
```

---

## Deliverables

### 1. File Scaffold + Package Structure

Create `torq_console/layer13/economics/` with:

```
__init__.py                    # Package exports
models.py                      # Core economic models
economic_evaluation_engine.py  # Main evaluation orchestrator
resource_allocation_engine.py  # Resource constraint solver
opportunity_cost_model.py      # Trade-off calculator
budget_aware_prioritization.py # Ranking under constraints
scoring.py                     # Utility scoring functions
integration.py                 # Layer 8-12 consumption layer
```

### 2. Core Models (`models.py`)

Define these Pydantic models:

```python
@dataclass
class EconomicContext:
    """Inputs from Layers 8-12."""
    available_budget: float
    time_horizon: timedelta
    risk_tolerance: float  # 0-1
    confidence_threshold: float  # 0-1

@dataclass
class ActionCandidate:
    """Potential action to evaluate."""
    action_id: str
    description: str
    estimated_cost: ResourceCost
    expected_value: float
    confidence: float  # from Layer 10
    success_probability: float  # from Layer 11
    urgency: float  # 0-1
    time_estimate: timedelta

@dataclass
class ResourceCost:
    """Multi-dimensional resource cost."""
    compute_budget: float
    api_call_budget: int
    time_budget: timedelta
    human_attention_required: bool

@dataclass
class EconomicScore:
    """Output of economic evaluation."""
    action_id: str
    total_score: float
    value_score: float
    cost_score: float
    urgency_score: float
    risk_adjusted_value: float
    opportunity_cost: float
    net_benefit: float
    recommendation: Literal["execute", "defer", "reject"]

@dataclass
class AllocationPlan:
    """Resource allocation across actions."""
    total_budget: float
    allocated_actions: List[AllocatedAction]
    remaining_budget: float
    expected_total_value: float
    expected_regret: float

@dataclass
class AllocatedAction:
    """Single action in allocation plan."""
    action_id: str
    allocated_budget: float
    expected_value: float
    priority_rank: int
```

### 3. EconomicEvaluationEngine (`economic_evaluation_engine.py`)

Main orchestrator class:

```python
class EconomicEvaluationEngine:
    """Evaluates actions on economic dimensions."""

    def __init__(
        self,
        context: EconomicContext,
        scoring_config: Optional[ScoringConfig] = None,
    ):
        self.context = context
        self.scoring_config = scoring_config or ScoringConfig()

    async def evaluate_action(
        self,
        candidate: ActionCandidate,
        alternatives: List[ActionCandidate],
    ) -> EconomicScore:
        """Evaluate a single action economically."""
        # 1. Calculate raw value score
        # 2. Apply cost penalty
        # 3. Apply urgency boost
        # 4. Risk-adjust based on confidence
        # 5. Calculate opportunity cost vs alternatives
        # 6. Determine recommendation
        pass

    async def evaluate_batch(
        self,
        candidates: List[ActionCandidate],
    ) -> List[EconomicScore]:
        """Evaluate multiple actions for comparison."""
        pass

    def get_net_benefit(
        self,
        score: EconomicScore,
    ) -> float:
        """Calculate risk-adjusted net benefit."""
        pass
```

### 4. ResourceAllocationEngine (`resource_allocation_engine.py`)

Constraint solver for resource distribution:

```python
class ResourceAllocationEngine:
    """Allocates constrained resources across actions."""

    def __init__(
        self,
        budget: float,
        allocation_strategy: Literal["greedy", "optimal", "satisfice"],
    ):
        self.budget = budget
        self.strategy = allocation_strategy

    async def allocate(
        self,
        scored_actions: List[EconomicScore],
        candidates: Map[str, ActionCandidate],
    ) -> AllocationPlan:
        """Solve resource allocation problem."""
        # 1. Sort by net benefit
        # 2. Apply knapsack or greedy selection
        # 3. Maximize total value within budget
        # 4. Calculate expected regret
        pass

    def calculate_regret(
        self,
        plan: AllocationPlan,
        excluded_actions: List[EconomicScore],
    ) -> float:
        """Calculate opportunity regret for excluded actions."""
        pass
```

### 5. OpportunityCostModel (`opportunity_cost_model.py`)

Trade-off calculator:

```python
class OpportunityCostModel:
    """Calculates opportunity costs of action choices."""

    async def calculate_opportunity_cost(
        self,
        chosen_action: ActionCandidate,
        alternatives: List[ActionCandidate],
        budget_constraint: float,
    ) -> float:
        """Calculate value sacrificed by choosing this action."""
        # Sum value of best alternatives that could have been chosen
        # Subtract value of chosen action
        # Normalize by budget
        pass

    async def compare_alternatives(
        self,
        actions: List[ActionCandidate],
    ) -> AlternativeComparison:
        """Compare all actions to each other."""
        pass
```

### 6. BudgetAwarePrioritization (`budget_aware_prioritization.py`)

Ranking under constraints:

```python
class BudgetAwarePrioritization:
    """Ranks actions when budget is constrained."""

    async def prioritize(
        self,
        scored_actions: List[EconomicScore],
        budget: float,
    ) -> List[PriorityRank]:
        """Rank actions by budget-aware priority."""
        pass

    async def identify_deferrals(
        self,
        scored_actions: List[EconomicScore],
        budget: float,
    ) -> Tuple[List[EconomicScore], List[EconomicScore]]:
        """Split into execute-now vs defer."""
        pass
```

### 7. Integration Layer (`integration.py`)

Consumes outputs from Layers 8-12:

```python
class Layer13IntegrationLayer:
    """Consumes outputs from Layers 8-12."""

    async def collect_candidates_from_layer8(
        self,
        meta_control_output: Any,
    ) -> List[ActionCandidate]:
        """Extract action candidates from meta-control."""
        pass

    async def apply_execution_costs_from_layer9(
        self,
        candidates: List[ActionCandidate],
        execution_metrics: Any,
    ) -> List[ActionCandidate]:
        """Apply cost estimates from execution layer."""
        pass

    async def apply_confidence_from_layer10(
        self,
        candidates: List[ActionCandidate],
        verification_output: Any,
    ) -> List[ActionCandidate]:
        """Apply confidence scores from verification."""
        pass

    async def apply_success_probability_from_layer11(
        self,
        candidates: List[ActionCandidate],
        learning_output: Any,
    ) -> List[ActionCandidate]:
        """Apply success probabilities from learning."""
        pass

    async def apply_network_consensus_from_layer12(
        self,
        candidates: List[ActionCandidate],
        federation_output: Any,
    ) -> List[ActionCandidate]:
        """Apply federation-wide agreement scores."""
        pass
```

### 8. Architecture Document

Create `docs/layer13/LAYER13_ARCHITECTURE.md` with:

- System diagram showing Layer 13 consuming from 8-12
- Data flow from candidate → scored → allocated
- Scoring formula documentation
- Integration interface contracts
- API surface for TORQ execution

---

## Design Considerations

### Scoring Formula Structure

The core economic score should combine:

```
EconomicScore = RiskAdjustedValue - OpportunityCost

RiskAdjustedValue = ExpectedValue × Confidence × SuccessProbability
ExpectedValue = BaseValue × UrgencyBoost - CostPenalty

OpportunityCost = Sum of sacrificed alternatives
```

### Resource Dimensions

Layer 13 must handle multi-dimensional constraints:

- **Compute budget** (tokens, API calls)
- **Time budget** (wall-clock time)
- **Attention budget** (human-in-loop required)
- **Financial budget** (if applicable)

### Recommendation Thresholds

Define clear cutoffs:

- **EXECUTE**: Net benefit > threshold, within budget
- **DEFER**: Positive value but budget constrained
- **REJECT**: Negative net benefit or low confidence

---

## Integration Constraints

- **DO NOT modify Layer 12** code
- Layer 13 must be **backward compatible** with existing TORQ
- Integration should be **optional** - TORQ works without Layer 13
- All Layer 13 outputs should be **explainable**

---

## Success Criteria

Your scaffold is complete when:

1. ✅ All 8 files exist with proper type hints
2. ✅ All Pydantic models validate correctly
3. ✅ Engine classes have async method stubs
4. ✅ `python -m torq_console.layer13.economics` imports without error
5. ✅ Architecture doc shows Layer 8-12 consumption
6. ✅ No Layer 12 code was modified

---

## Next Steps (After This Brief)

1. Create the file scaffold
2. Define all models with type hints
3. Stub engine classes with docstrings
4. Create architecture diagram
5. Verify imports work

**DO NOT proceed to full implementation** until Agent 2 delivers PRD and validation scenarios. The scaffold must align with validation requirements.

---

## Checkpoint

After completing this brief, you will have:

- [ ] File scaffold created
- [ ] Core models defined
- [ ] Engine interfaces stubbed
- [ ] Architecture document drafted
- [ ] Import verification passed

At this point, **STOP** and wait for Agent 2's PRD and validation scenarios before continuing implementation.

---

**Agent 1, you own the Layer 13 runtime. Build it clean, build it typed, build it ready for validation.**
