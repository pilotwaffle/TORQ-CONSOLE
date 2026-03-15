# Layer 13 Scoring Architecture
## Staged Evaluation for Economic Decision Intelligence

**Status:** Design Specification
**Applies To:** Agent 1 (Architecture) + Agent 2 (Validation)
**Date:** 2026-03-14

---

## Core Principle

**No single raw score should combine value, confidence, cost, urgency, and opportunity cost in one step.**

Layer 13 scoring must be **staged and explainable**.

---

## The Five Evaluation Stages

```
┌─────────────────────────────────────────────────────────────────────┐
│                    LAYER 13 SCORING PIPELINE                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Stage 1: FEASIBILITY GATE                                          │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Input:  ActionCandidate                                       │ │
│  │  Checks: policy_allowed, dependencies_satisfied,               │ │
│  │          confidence_above_floor, risk_below_ceiling            │ │
│  │  Output: eligible: bool, rejection_reason: str|None            │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                          ↓                                          │
│  Stage 2: BASE VALUE SCORE                                         │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Inputs: estimated_value, urgency, time_to_realization         │ │
│  │  Formula: w_value × normalized_value +                         │ │
│  │           w_urgency × urgency +                                │ │
│  │           w_speed × time_realization_score                     │ │
│  │  Output: base_value: float                                     │ │
│  │  Question: "How attractive is this if it works?"               │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                          ↓                                          │
│  Stage 3: EXECUTION QUALITY MODIFIER                               │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Inputs: confidence, risk, dependency_complexity               │ │
│  │  Formula: w_conf × confidence +                                │ │
│  │           w_simplicity × dep_simplicity -                      │ │
│  │           w_risk × risk                                        │ │
│  │  Output: execution_modifier: float (clamped 0.1-1.25)         │ │
│  │  Then: quality_adjusted_value = base_value × modifier         │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                          ↓                                          │
│  Stage 4: ECONOMIC EFFICIENCY SCORE                                │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Inputs: quality_adjusted_value, estimated_cost                │ │
│  │  Formula: efficiency = qav / max(cost, cost_floor)            │ │
│  │  Output: efficiency: float                                     │ │
│  │  Keeps both: qav AND efficiency (not just efficiency)         │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                          ↓                                          │
│  Stage 5: PORTFOLIO ALLOCATION LAYER                               │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Inputs: All scored candidates, budget, dependencies           │ │
│  │  Factors: remaining_budget, dependencies,                     │ │
│  │           diversification, opportunity_cost, strategic_balance │ │
│  │  Output: AllocationPlan (bundle, not just sorted list)         │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## EconomicScore Model

**CRITICAL:** Store intermediate values for explainability. Do NOT collapse to final score only.

```python
@dataclass
class EconomicScore(BaseModel):
    """Complete economic evaluation of an action candidate."""

    # Identity
    candidate_id: str

    # Stage 1: Feasibility
    eligible: bool
    rejection_reason: Optional[str] = None

    # Stage 2: Base Value
    base_value: float
    normalized_value: float
    urgency_score: float
    time_realization_score: float

    # Stage 3: Execution Quality
    execution_modifier: float
    confidence_factor: float
    risk_penalty: float
    dependency_simplicity: float

    # Combined
    quality_adjusted_value: float

    # Stage 4: Efficiency
    efficiency: float
    estimated_cost: float

    # Stage 5: Portfolio Considerations
    strategic_bonus: float = 0.0
    opportunity_cost_penalty: float = 0.0
    dependency_unlock_bonus: float = 0.0

    # Final (but explainable)
    final_priority_score: float
    recommendation: Literal["execute", "defer", "reject"]

    # Rationale
    rationale: str = ""
```

---

## Final Priority Formula

```python
final_priority_score = (
    w_qav × quality_adjusted_value +
    w_efficiency × efficiency +
    w_strategy × strategic_bonus -
    w_opp_cost × opportunity_cost_penalty
)
```

**Default weights (v1):**
```python
w_qav = 0.55
w_efficiency = 0.25
w_strategy = 0.20
w_opp_cost = 0.15
```

---

## ActionCandidate Model (Updated)

```python
@dataclass
class ActionCandidate(BaseModel):
    """Potential action for economic evaluation."""

    # Identity
    id: str
    description: str
    domain: str

    # Economic Dimensions
    estimated_value: float
    estimated_cost: float

    # Uncertainty Dimensions
    confidence: float        # 0-1, from Layer 10
    risk: float              # 0-1

    # Timing Dimensions
    urgency: float           # 0-1
    time_to_realization: float  # in seconds or normalized

    # Structural Dimensions
    dependencies: List[str]  # action IDs that must complete first

    # Strategic Dimensions (NEW)
    strategic_alignment: float = 0.5  # 0-1, alignment with goals
    reversibility: float = 0.5        # 0-1, can this be undone?

    # Resource Specification
    resource_type: str = "general"    # what budget pool to draw from
```

---

## Clean Default Scoring Pattern (v1)

This is the starting formula for Layer 13 v1:

```python
def score_candidate(
    candidate: ActionCandidate,
    context: EconomicContext,
    alternatives: List[ActionCandidate],
) -> EconomicScore:
    """Stage 1-4 evaluation. Stage 5 (allocation) happens separately."""

    # Stage 0: Pre-check
    if not _feasibility_gate(candidate, context):
        return EconomicScore(
            candidate_id=candidate.id,
            eligible=False,
            rejection_reason="failed_feasibility_gate",
            # ... zeros for other fields
        )

    # Stage 1: Feasibility (already passed)

    # Stage 2: Base Value (intrinsic upside, no cost yet)
    time_realization_score = 1.0 / (1.0 + candidate.time_to_realization)

    normalized_value = _normalize_value(
        candidate.estimated_value,
        [c.estimated_value for c in alternatives + [candidate]],
    )

    base_value = (
        0.50 * normalized_value +
        0.25 * candidate.urgency +
        0.25 * time_realization_score
    )

    # Stage 3: Execution Quality Modifier
    dependency_simplicity = 1.0 / (1.0 + len(candidate.dependencies))

    execution_modifier = max(
        0.1,  # floor
        0.60 * candidate.confidence +
        0.20 * dependency_simplicity +
        0.20 * (1.0 - candidate.risk)
    )

    quality_adjusted_value = base_value * execution_modifier

    # Stage 4: Economic Efficiency
    efficiency = quality_adjusted_value / max(candidate.estimated_cost, 1.0)

    # Stage 5: Portfolio layer (done by ResourceAllocationEngine, not here)
    # strategic_bonus, opportunity_cost_penalty computed during allocation

    final_priority_score = (
        0.55 * quality_adjusted_value +
        0.25 * efficiency +
        0.20 * candidate.strategic_alignment
    )

    return EconomicScore(
        candidate_id=candidate.id,
        eligible=True,
        base_value=base_value,
        normalized_value=normalized_value,
        urgency_score=candidate.urgency,
        time_realization_score=time_realization_score,
        execution_modifier=execution_modifier,
        confidence_factor=candidate.confidence,
        risk_penalty=candidate.risk,
        dependency_simplicity=dependency_simplicity,
        quality_adjusted_value=quality_adjusted_value,
        efficiency=efficiency,
        estimated_cost=candidate.estimated_cost,
        strategic_alignment=candidate.strategic_alignment,
        final_priority_score=final_priority_score,
        recommendation=_determine_recommendation(final_priority_score),
        rationale=_generate_rationale(candidate, final_priority_score),
    )
```

---

## Engine Responsibilities

### EconomicEvaluationEngine

**Owns:**
- Feasibility gate (Stage 1)
- Base value calculation (Stage 2)
- Execution modifier (Stage 3)
- Quality-adjusted value (Stage 3)
- Efficiency score (Stage 4)

**Does NOT own:**
- Opportunity cost (Stage 5)
- Bundle selection (Stage 5)

### OpportunityCostModel

**Owns:**
- What gets displaced if this action is chosen
- Regret estimation
- Opportunity cost penalty calculation
- Alternative bundle comparison

### BudgetAwarePrioritization

**Owns:**
- Ranking policy configuration
- Strategic weighting
- Domain balancing
- Tie-breaking rules
- Shortlist generation

### ResourceAllocationEngine

**Owns:**
- Final bundle selection under constraints
- Dependency ordering
- Budget optimization
- Deferred queue management

---

## Bugs This Architecture Avoids

| Bug | What Happens | Fix |
|-----|--------------|-----|
| **Double-counting confidence** | Confidence multiplied in multiple places, crushing uncertain but worthwhile actions | Confidence appears ONCE in execution modifier |
| **Cost dominating too early** | Tiny cheap tasks always outrank valuable ones | Evaluate value FIRST, cost SECOND |
| **Urgency overpowering value** | Every urgent low-value action jumps to top | Urgency shapes base value, doesn't replace it |
| **Ignoring dependency unlocks** | Mediocre actions that unlock high-value work get deprioritized | Strategic bonus for dependency unlocks |
| **Top-N instead of best bundle** | Highest-ranked actions individually may not be best set under budget | Allocation optimizes across SET, not sort by rank |

---

## Validation Rules for Agent 2

Each scenario must confirm correct scoring behavior:

### 1. Value vs Urgency
```
Action A: high value, moderate urgency
Action B: low value, high urgency

Expected: A outranks B (urgency doesn't replace value)
```

### 2. Opportunity Cost
```
Action A: cost 100, value 200
Action B: cost 50, value 120
Budget: 100

Expected: B + another action beats A alone
```

### 3. Low-Confidence Rejection
```
Action: value 500, cost 100, confidence 0.2

Expected: Rejected or heavily discounted (execution modifier ~0.1)
```

### 4. High-Value Moderate-Cost Beats Flashy
```
Action A: value 100, cost 50, confidence 0.9
Action B: value 200, cost 80, confidence 0.3

Expected: A outranks B (high confidence beats high risk)
```

### 5. Urgency Rises, Not Irrationally
```
Action A: value 100, urgency 0.3
Action B: value 90, urgency 0.9

Expected: B gets boost, A should still win or be close
```

### 6. Dependency Unlock Matters
```
Action A: mediocre alone, unlocks 3 high-value actions
Action B: good alone, no unlocks

Expected: A gets strategic bonus
```

### 7. Bundle Beats Naive Top-N
```
Budget: 100
Top-3 by score: A(cost 95), B(cost 40), C(cost 30)
Best bundle: B + C + D (total cost 95)

Expected: Allocation picks B+C+D, not A alone
```

---

## Alignment Review Checklist (Task #20)

At alignment review, confirm:

- [ ] Feasibility gate exists (Stage 1)
- [ ] Base value is separate from cost (Stage 2)
- [ ] Confidence is applied ONCE (Stage 3)
- [ ] Opportunity cost is AFTER candidate scoring (Stage 5)
- [ ] Allocation is bundle-aware, not only rank-based
- [ ] EconomicScore stores intermediate values for explainability
- [ ] ActionCandidate includes strategic_alignment and reversibility
- [ ] No single formula combines all dimensions at once

---

## Engine Interface Signatures

```python
class EconomicEvaluationEngine:
    async def evaluate_candidate(
        self,
        candidate: ActionCandidate,
        context: EconomicContext,
        alternatives: List[ActionCandidate],
    ) -> EconomicScore:
        """Stages 1-4. Returns scored candidate."""
        pass

class OpportunityCostModel:
    async def calculate_opportunity_cost(
        self,
        candidate: ActionCandidate,
        alternatives: List[ActionCandidate],
        budget: float,
    ) -> OpportunityCostAnalysis:
        """Stage 5a. Returns what's sacrificed by choosing this."""
        pass

class BudgetAwarePrioritization:
    async def rank_candidates(
        self,
        scored: List[EconomicScore],
        context: EconomicContext,
    ) -> List[EconomicScore]:
        """Stage 5b. Returns ranked list with strategic adjustments."""
        pass

class ResourceAllocationEngine:
    async def allocate(
        self,
        candidates: List[ActionCandidate],
        scored: List[EconomicScore],
        context: EconomicContext,
    ) -> AllocationPlan:
        """Stage 5c. Returns optimal bundle, not just top-N."""
        pass
```

---

## For Agent 1: Architecture Extraction

From this document, extract:

1. **Model definitions** - EconomicScore with all intermediate fields
2. **Engine interfaces** - Method signatures above
3. **Integration adapter** - Convert Layers 8-12 outputs to ActionCandidate[]
4. **DO NOT implement** the actual scoring formulas yet

## For Agent 2: Validation Extraction

From this document, extract:

1. **Validation scenarios** - The 7 rules above
2. **Expected behaviors** - What each scenario should produce
3. **Metrics** - allocation_efficiency, regret_score, etc.
4. **DO NOT assume exact numeric weights** - formulas may be tuned

---

**Design locked. Agents: Build to this spec.**
