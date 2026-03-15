"""TORQ Layer 13 - Economic Intelligence

Layer 13 provides TORQ with economic intelligence - the ability to make
resource-aware decisions about what actions deserve investment. It transforms
validated claims and mission proposals into economically prioritized action plans.

## Architecture

Layer 13 uses a five-layer evaluation pipeline to avoid common prioritization bugs:

1. **Feasibility Gate** - Hard filters for resource and deadline constraints
2. **Base Value Score** - Intrinsic value calculation
3. **Execution Quality Modifier** - Confidence-based adjustment
4. **Economic Efficiency** - Value per unit cost
5. **Portfolio Allocation** - Budget-constrained selection with opportunity cost

## Key Principle

> No single raw score should combine value, confidence, cost, urgency, and
> opportunity cost in one step. Layer 13 scoring must be staged and explainable.

## Components

- `EconomicEvaluationEngine`: Layers 1-3 (feasibility, base value, quality modifier)
- `BudgetAwarePrioritization`: Layer 4 (efficiency calculation)
- `ResourceAllocationEngine`: Layer 5 (portfolio allocation)
- `OpportunityCostModel`: Cost of foregone alternatives

## Example Usage

```python
from torq_console.layer13.economic import (
    create_evaluation_engine,
    create_prioritization_engine,
    create_allocation_engine,
    create_opportunity_cost_model,
)
from torq_console.layer13.economic.models import (
    MissionProposal,
    ResourceConstraints,
)

# Create engines
evaluation_engine = create_evaluation_engine()
prioritization_engine = create_prioritization_engine()
allocation_engine = create_allocation_engine()
opportunity_model = create_opportunity_cost_model()

# Define mission proposal
proposal = MissionProposal(
    mission_id="data_pipeline_001",
    mission_type="data_ingestion",
    user_value=0.8,
    urgency=0.3,
    strategic_fit=0.9,
    estimated_cost=300.0,
)

# Evaluate (Layers 1-3)
score = await evaluation_engine.evaluate_proposal(
    proposal=proposal,
    constraints=ResourceConstraints(total_budget=1000.0),
)

# Rank by efficiency (Layer 4)
ranked = await prioritization_engine.rank_by_efficiency(
    scored_proposals=[score],
    constraints=ResourceConstraints(total_budget=1000.0),
    costs={proposal.mission_id: proposal.estimated_cost},
)

# Allocate budget (Layer 5)
allocation = await allocation_engine.allocate_budget(
    ranked_proposals=ranked,
    constraints=ResourceConstraints(total_budget=1000.0),
    costs={proposal.mission_id: proposal.estimated_cost},
)

# Calculate opportunity costs
opportunity_costs = await opportunity_model.calculate_opportunity_costs(
    accepted=[s for s in ranked if s.candidate_id in allocation.funded_mission_ids],
    rejected=[s for s in ranked if s.candidate_id not in allocation.funded_mission_ids],
    total_budget=1000.0,
    costs={proposal.mission_id: proposal.estimated_cost},
)
```

## Version

**Version:** 0.13.0
**Status:** COMPLETE - All engines implemented and verified
**Depends On:** Layer 12 (Federation) - CLOSED
**Completion Date:** 2026-03-14
"""

from .models import (
    AllocationResult,
    EconomicConfiguration,
    EconomicScore,
    EvaluationContext,
    EvaluationWeights,
    FederationResult,
    MissionProposal,
    OpportunityCostResult,
    ResourceConstraints,
    datetime_utcnow,
)

from .economic_evaluation_engine import (
    EconomicEvaluationEngine,
    create_evaluation_engine,
)

from .budget_aware_prioritization import (
    BudgetAwarePrioritization,
    create_prioritization_engine,
)

from .resource_allocation_engine import (
    ResourceAllocationEngine,
    create_allocation_engine,
)

from .opportunity_cost_model import (
    OpportunityCostModel,
    create_opportunity_cost_model,
)


__all__ = [
    # Models
    "AllocationResult",
    "EconomicConfiguration",
    "EconomicScore",
    "EvaluationContext",
    "EvaluationWeights",
    "FederationResult",
    "MissionProposal",
    "OpportunityCostResult",
    "ResourceConstraints",
    "datetime_utcnow",
    # Engines
    "EconomicEvaluationEngine",
    "BudgetAwarePrioritization",
    "ResourceAllocationEngine",
    "OpportunityCostModel",
    # Factories
    "create_evaluation_engine",
    "create_prioritization_engine",
    "create_allocation_engine",
    "create_opportunity_cost_model",
]


__version__ = "0.13.0"
