# Layer 13 Architecture
## TORQ Economic Intelligence System

**Version:** 0.13.0-planning
**Status:** ARCHITECTURE DESIGN
**Author:** Agent 1
**Date:** 2026-03-14

---

## Executive Summary

Layer 13 provides TORQ with economic intelligence - the ability to make resource-aware decisions about what actions deserve investment. It transforms validated claims and mission proposals into economically prioritized action plans.

### Key Design Principle

> **No single raw score should combine value, confidence, cost, urgency, and opportunity cost in one step. Layer 13 scoring must be staged and explainable.**

The architecture uses a **five-layer evaluation pipeline** to avoid common prioritization bugs:
- Double-counting the same factor
- Cost dominating all other considerations
- Urgency overpowering long-term value
- Confidence filtering out high-value risky bets
- Opportunity cost being calculated inconsistently

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TORQ LAYER 13                                      │
│                      ECONOMIC INTELLIGENCE                                   │
└─────────────────────────────────────────────────────────────────────────────┘

                                      ┌─────────────────────────────────────────┐
                                      │   Input: Mission Proposals             │
                                      │   - Requirements (L8)                  │
                                      │   - Resource costs (L9)                │
                                      │   - Federation results (L11/L12)       │
                                      └────────────────────┬────────────────────┘
                                                           │
                                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                         FIVE-LAYER EVALUATION PIPELINE                                │
├──────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐     │
│  │  Layer 1:           │    │  Layer 2:           │    │  Layer 3:           │     │
│  │  Feasibility Gate   │───▶│  Base Value Score   │───▶│  Execution Quality  │     │
│  │                     │    │                     │    │  Modifier           │     │
│  │  - Hard filters     │    │  - User value       │    │  - Confidence boost │     │
│  │  - Resource checks  │    │  - Urgency          │    │  - Federation       │     │
│  │  - Deadline valid?  │    │  - Strategic fit    │    │    validation       │     │
│  └─────────────────────┘    └─────────────────────┘    └─────────────────────┘     │
│           │                           │                           │                │
│           ▼                           ▼                           ▼                │
│  ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐     │
│  │  Layer 4:           │    │  Layer 5:           │    │  Output:            │     │
│  │  Economic Efficiency│    │  Portfolio          │    │  Prioritized Queue  │     │
│  │                     │    │  Allocation         │    │  - Resource assigns │     │
│  │  - Value per cost   │    │  - Opportunity cost │    │  - Budget remainder │     │
│  │  - Resource stress  │    │  - Budget fitting   │    │  - Queued missions  │     │
│  └─────────────────────┘    └─────────────────────┘    └─────────────────────┘     │
│                                                                      │                │
│                                                                      ▼                │
│                         ┌─────────────────────────────────────────────────────────┐  │
│                         │         Metrics & Monitoring (to L14)                    │  │
│                         │  - Allocation efficiency                                │  │
│                         │  - Budget utilization                                    │  │
│                         │  - Regret scores                                         │  │
│                         └─────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────────┘

                                        │
                                        ▼
                         ┌─────────────────────────────────────────┐
                         │   Execution Queue (to L15)              │
                         │   - Funded missions in priority order   │
                         │   - Resource assignments                │
                         │   - Queued missions for next budget     │
                         └─────────────────────────────────────────┘
```

---

## Five-Layer Evaluation Pipeline

### Layer 1: Feasibility Gate

**Purpose:** Apply hard filters before any scoring. Prevents waste on infeasible proposals.

**Engine:** `economic_evaluation_engine.py`

| Filter | Check | Fail Action |
|--------|-------|-------------|
| Resource Availability | Required capabilities exist in L9 registry | REJECT |
| Budget Compatibility | Minimum cost <= available budget | REJECT |
| Deadline Validity | Deadline >= now + minimum execution time | REJECT |
| Prerequisite Check | Required missions already completed | QUEUE |

**Output:** `eligible: bool` + `rejection_reason: str | None`

### Layer 2: Base Value Score

**Purpose:** Calculate intrinsic value independent of execution quality or cost.

**Engine:** `economic_evaluation_engine.py`

**Formula (Stage 2 - Avoid mixing concerns):**
```
base_value = (
    user_value_weight * normalized_user_value +
    urgency_weight * normalized_urgency +
    strategic_fit_weight * normalized_strategic_fit
)
```

| Component | Source | Range | Notes |
|-----------|--------|-------|-------|
| user_value | Mission definition (L8) | 0.0-1.0 | User-provided importance |
| urgency | Mission definition (L8) | 0.0-1.0 | Time sensitivity (decays over time) |
| strategic_fit | Mission metadata | 0.0-1.0 | Alignment with strategic goals |

**Output:** `base_value: float` (0.0-1.0)

### Layer 3: Execution Quality Modifier

**Purpose:** Adjust base value based on confidence in successful execution.

**Engine:** `economic_evaluation_engine.py`

**Formula:**
```
quality_modifier = 1.0 + (federation_confidence - 0.5) * confidence_weight
```

| Component | Source | Range | Effect |
|-----------|--------|-------|--------|
| federation_confidence | L12 validation result | 0.0-1.0 | Multiplier based on validation strength |
| federation_validation_count | L12 node count | 0-∞ | Diminishing returns bonus |
| historical_success_rate | Mission history | 0.0-1.0 | Track record bonus |

**Output:** `quality_modifier: float` (typically 0.5-1.5)

**Intermediate Score:**
```
quality_adjusted_value = base_value * quality_modifier
```

### Layer 4: Economic Efficiency Score

**Purpose:** Calculate value achieved per unit of resource spent.

**Engine:** `budget_aware_prioritization.py`

**Formula:**
```
efficiency = quality_adjusted_value / (total_cost + cost_epsilon)
```

| Component | Source | Range | Notes |
|-----------|--------|-------|-------|
| total_cost | L9 capability registry | >0 | Sum of all required resources |
| cost_epsilon | Configuration | small | Prevents division by zero |

**Output:** `efficiency: float` (0.0-∞, typically 0.0-2.0)

### Layer 5: Portfolio Allocation Layer

**Purpose:** Select optimal mission set under budget constraint using opportunity cost.

**Engine:** `resource_allocation_engine.py` + `opportunity_cost_model.py`

**Algorithm:** Knapsack-style optimization with economic scoring

```
1. Sort candidates by efficiency (Layer 4 score)
2. Greedy select missions until budget exhaustion
3. Calculate opportunity cost for each rejection
4. Apply strategic bonus for critical path missions
5. Finalize allocation
```

**Opportunity Cost Calculation:**
```
opportunity_cost = (
    rejected_quality_adjusted_value -
    next_best_accepted_quality_adjusted_value
)
```

**Output:** `final_priority_score: float` + `opportunity_cost_penalty: float`

---

## Core Components

### 1. EconomicEvaluationEngine

**File:** `torq_console/layer13/economic/economic_evaluation_engine.py`

**Responsibilities:**
- Layer 1: Feasibility gate
- Layer 2: Base value scoring
- Layer 3: Execution quality modification

**Key Methods:**
```python
class EconomicEvaluationEngine:
    async def evaluate_proposal(
        self,
        proposal: MissionProposal,
        constraints: ResourceConstraints,
        federation_result: FederationResult | None = None,
    ) -> EconomicScore:
        """Run Layers 1-3 of evaluation pipeline."""

    def _apply_feasibility_gate(
        self,
        proposal: MissionProposal,
        constraints: ResourceConstraints,
    ) -> tuple[bool, str | None]:
        """Layer 1: Apply hard filters."""

    def _calculate_base_value(
        self,
        proposal: MissionProposal,
    ) -> float:
        """Layer 2: Calculate intrinsic value."""

    def _calculate_execution_modifier(
        self,
        proposal: MissionProposal,
        federation_result: FederationResult | None,
    ) -> float:
        """Layer 3: Calculate quality adjustment."""
```

### 2. BudgetAwarePrioritization

**File:** `torq_console/layer13/economic/budget_aware_prioritization.py`

**Responsibilities:**
- Layer 4: Economic efficiency scoring
- Ranking by value-per-cost
- Budget-aware candidate filtering

**Key Methods:**
```python
class BudgetAwarePrioritization:
    async def rank_by_efficiency(
        self,
        scored_proposals: list[EconomicScore],
        constraints: ResourceConstraints,
    ) -> list[EconomicScore]:
        """Layer 4: Calculate efficiency and sort."""

    def _calculate_efficiency(
        self,
        score: EconomicScore,
        constraints: ResourceConstraints,
    ) -> float:
        """Calculate value per unit cost."""
```

### 3. ResourceAllocationEngine

**File:** `torq_console/layer13/economic/resource_allocation_engine.py`

**Responsibilities:**
- Layer 5: Portfolio allocation
- Budget-constrained selection
- Resource assignment

**Key Methods:**
```python
class ResourceAllocationEngine:
    async def allocate_budget(
        self,
        ranked_proposals: list[EconomicScore],
        constraints: ResourceConstraints,
    ) -> AllocationResult:
        """Layer 5: Select mission set under budget."""

    def _apply_knapsack_selection(
        self,
        proposals: list[EconomicScore],
        budget: float,
    ) -> tuple[list[str], list[str]]:
        """Select funded vs queued missions."""
```

### 4. OpportunityCostModel

**File:** `torq_console/layer13/economic/opportunity_cost_model.py`

**Responsibilities:**
- Calculate cost of foregone alternatives
- Regret minimization
- Portfolio optimization hints

**Key Methods:**
```python
class OpportunityCostModel:
    async def calculate_opportunity_costs(
        self,
        accepted: list[EconomicScore],
        rejected: list[EconomicScore],
    ) -> dict[str, OpportunityCostResult]:
        """Calculate opportunity cost for each rejection."""

    def _find_best_accepted_alternative(
        self,
        rejected_proposal: EconomicScore,
        accepted: list[EconomicScore],
    ) -> EconomicScore | None:
        """Find closest accepted mission for comparison."""
```

---

## Data Models

### EconomicScore

**Purpose:** Complete evaluation result for a mission proposal.

```python
class EconomicScore(BaseModel):
    """Result of economic evaluation through Layers 1-4."""

    # Identity
    candidate_id: str
    mission_type: str

    # Layer 1: Feasibility
    eligible: bool
    rejection_reason: str | None = None

    # Layer 2: Base Value
    base_value: float = Field(ge=0.0, le=1.0)

    # Layer 3: Execution Quality
    execution_modifier: float = Field(ge=0.0, le=2.0)
    quality_adjusted_value: float = Field(ge=0.0)

    # Layer 4: Efficiency
    efficiency: float = Field(ge=0.0)

    # Layer 5: Portfolio (final)
    strategic_bonus: float = Field(default=0.0, ge=-0.5, le=0.5)
    opportunity_cost_penalty: float = Field(default=0.0, ge=0.0)
    final_priority_score: float = Field(ge=0.0)

    # Metadata
    evaluation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    federation_validated: bool = False
    federation_confidence: float | None = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
```

### ResourceConstraints

**Purpose:** Budget and resource limits.

```python
class ResourceConstraints(BaseModel):
    """Resource availability for allocation."""

    # Monetary budget
    total_budget: float = Field(gt=0)
    budget_remaining: float = Field(ge=0)

    # Resource limits (from L9 capability registry)
    max_compute_units: int | None = None
    max_api_calls: int | None = None
    max_execution_time_seconds: int | None = None

    # Time constraints
    allocation_deadline: datetime | None = None

    # Priority constraints
    require_federation_validation: bool = True
    min_confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)

    # Strategic constraints
    required_mission_types: list[str] = Field(default_factory=list)
    forbidden_mission_types: list[str] = Field(default_factory=list)
```

### AllocationResult

**Purpose:** Output of portfolio allocation (Layer 5).

```python
class AllocationResult(BaseModel):
    """Result of budget allocation process."""

    # Funded missions
    funded_mission_ids: list[str]
    funded_total_cost: float
    funded_total_value: float

    # Queued missions
    queued_mission_ids: list[str]
    queued_total_cost: float
    queued_total_value: float

    # Rejected missions
    rejected_mission_ids: list[str]
    rejected_reasons: dict[str, str]

    # Budget status
    budget_utilization: float  # 0.0-1.0
    remaining_budget: float

    # Opportunity costs
    opportunity_costs: dict[str, OpportunityCostResult]

    # Metrics
    allocation_efficiency: float  # Value achieved per dollar
    regret_score: float  # Value of best foregone alternative

    # Timestamp
    allocation_timestamp: datetime = Field(default_factory=datetime.utcnow)
```

### OpportunityCostResult

**Purpose:** Opportunity cost for a single rejected mission.

```python
class OpportunityCostResult(BaseModel):
    """Opportunity cost of rejecting a mission."""

    rejected_mission_id: str
    rejected_mission_value: float

    best_accepted_alternative_id: str | None
    best_accepted_alternative_value: float

    opportunity_cost: float  # Difference between rejected and best accepted

    # Normalized cost (relative to budget)
    opportunity_cost_ratio: float  # Cost / total_budget

    # Strategic impact
    strategic_impact: str  # "low", "medium", "high"
```

### MissionProposal

**Purpose:** Input from Layer 8 for economic evaluation.

```python
class MissionProposal(BaseModel):
    """Mission proposal for economic evaluation."""

    # Identity
    mission_id: str
    mission_type: str
    description: str

    # Value metrics (Layer 2 input)
    user_value: float = Field(ge=0.0, le=1.0)
    urgency: float = Field(ge=0.0, le=1.0)
    strategic_fit: float = Field(ge=0.0, le=1.0)

    # Execution requirements (from L9)
    required_capabilities: list[str]
    estimated_cost: float = Field(gt=0)
    estimated_duration_seconds: int = Field(gt=0)

    # Constraints
    deadline: datetime | None = None
    prerequisites: list[str] = Field(default_factory=list)

    # Federation (optional, from L11/L12)
    federation_result_id: str | None = None
    requires_validation: bool = True
```

---

## Integration Contracts

### Upstream Dependencies

| Layer | Consumes | Purpose |
|-------|----------|---------|
| **Layer 8** | `MissionProposal` | Mission definitions with value/urgency |
| **Layer 9** | Capability registry | Resource costs and availability |
| **Layer 11** | Validated claims | Federation input for evaluation |
| **Layer 12** | `FederationResult` | Multi-node validation confidence |

### Downstream Outputs

| Layer | Provides | Purpose |
|-------|----------|---------|
| **Layer 14** | Economic metrics | Dashboard visualization |
| **Layer 15** | `AllocationResult` | Execution queue population |

---

## Avoiding Prioritization Bugs

### Bug: Double-Counting

**Problem:** Same factor counted in multiple layers.

**Solution:** Clear separation of concerns:
- `user_value` appears only in Layer 2 (base value)
- `federation_confidence` appears only in Layer 3 (quality modifier)
- `cost` appears only in Layer 4 (efficiency)

### Bug: Cost Domination

**Problem:** Low-cost missions always win regardless of value.

**Solution:** Use `efficiency = value / (cost + epsilon)` with strategic bonus in Layer 5 for critical missions.

### Bug: Urgency Overpowering Value

**Problem:** Urgent but low-value missions displace important work.

**Solution:** Urgency is one component of base_value (Layer 2), not a multiplier. High-value non-urgent missions can outscore urgent low-value missions.

### Bug: Confidence Filtering

**Problem:** High-value risky bets filtered out by low confidence.

**Solution:** Confidence is a modifier (Layer 3), not a gate. Low confidence reduces but doesn't eliminate score unless below threshold.

### Bug: Opportunity Cost Inconsistency

**Problem:** Opportunity cost calculated differently at different stages.

**Solution:** Centralized in `OpportunityCostModel`, calculated once in Layer 5 after selection.

---

## Configuration

### Evaluation Weights

```python
# Layer 2: Base Value Weights
BASE_VALUE_WEIGHTS = {
    "user_value": 0.6,      # Primary driver
    "urgency": 0.3,         # Time sensitivity
    "strategic_fit": 0.1,   # Organizational alignment
}

# Layer 3: Confidence Weights
CONFIDENCE_WEIGHT = 0.5  # How much confidence affects score
CONFIDENCE_THRESHOLD = 0.3  # Below this, flag as risky

# Layer 4: Efficiency
COST_EPSILON = 0.01  # Prevent division by zero

# Layer 5: Strategic Bonus
STRATEGIC_BONUS_CAP = 0.5  # Maximum bonus for critical missions
OPPORTUNITY_COST_THRESHOLD = 0.1  # Minimum cost to record
```

### Resource Limits

```python
DEFAULT_CONSTRAINTS = ResourceConstraints(
    total_budget=1000.0,
    require_federation_validation=True,
    min_confidence_threshold=0.5,
)
```

---

## Validation Approach

Layer 13 validation uses scenario-based testing (Agent 2 responsibility):

1. **Constrained Budget Allocation** - Validate optimal budget use
2. **High-Value vs High-Urgency** - Validate prioritization logic
3. **Opportunity Cost Comparison** - Validate alternative selection
4. **Low-Confidence Rejection** - Validate risk filtering
5. **Resource Starvation Stress** - Validate graceful degradation

Each scenario has defined inputs, expected outputs, and success criteria.

---

## Performance Considerations

### Scalability

- **Evaluation complexity:** O(n) where n = number of proposals
- **Allocation complexity:** O(n log n) for sorting + O(n) for selection
- **Opportunity cost:** O(m²) where m = rejected missions

### Optimization

- Cache federation results to avoid re-fetching
- Batch evaluate proposals when possible
- Use approximate sorting for very large candidate sets
- Parallel evaluation across independent proposals

---

## CLI Interface

```bash
# Run economic prioritization
python -m torq_console.layer13.economic.run_prioritization \
    --budget 1000 \
    --missions data/missions.json \
    --constraints data/constraints.json \
    --output data/allocation.json

# Run validation suite
python -m torq_console.layer13.economic.run_validation \
    --scenarios budget_constrained,value_urgency_tradeoff \
    --verbose

# Compare allocation strategies
python -m torq_console.layer13.economic.run_analysis \
    --baseline equal_allocation \
    --test layer13_economic \
    --metrics efficiency,regret,budget_utilization
```

---

## Next Steps

1. **Agent 1:** Create engine scaffolds with type hints and docstrings
2. **Agent 2:** Create validation scenarios and expected outcomes
3. **Alignment Review:** Lock shared models and integration points
4. **Implementation:** Build engines according to this architecture
5. **Validation:** Run Agent 2's scenarios against implementation

---

## Appendix: Evaluation Example

```python
# Input mission
proposal = MissionProposal(
    mission_id="data_pipeline_001",
    mission_type="data_ingestion",
    user_value=0.8,      # High user value
    urgency=0.3,         # Not time-sensitive
    strategic_fit=0.9,   # High strategic alignment
    estimated_cost=300.0,
    requires_validation=True,
)

# Federation result (from Layer 12)
federation_result = FederationResult(
    claim_id="claim_001",
    acceptance_rate=0.85,  # 85% of nodes accepted
    confidence=0.92,       # High confidence
    participating_nodes=12,
)

# Evaluation
result = await engine.evaluate_proposal(
    proposal=proposal,
    constraints=ResourceConstraints(total_budget=1000.0),
    federation_result=federation_result,
)

# Result breakdown
# Layer 1: eligible=True
# Layer 2: base_value = 0.6*0.8 + 0.3*0.3 + 0.1*0.9 = 0.69
# Layer 3: execution_modifier = 1.0 + (0.92-0.5)*0.5 = 1.21
#         quality_adjusted_value = 0.69 * 1.21 = 0.835
# Layer 4: efficiency = 0.835 / 300.0 = 0.00278
# Layer 5: final_priority_score (after portfolio allocation)
```

---

**Document Status:** ARCHITECTURE APPROVED
**Next:** Agent 1 creates engine scaffolds, Agent 2 creates validation scenarios
