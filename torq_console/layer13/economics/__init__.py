"""
Layer 13 - Economic Intelligence Engine

This layer enables TORQ to decide what actions deserve resources by evaluating
costs, value, urgency, and opportunity costs through a staged scoring pipeline.

Components:
- EconomicEvaluationEngine: Stages 1-4 (feasibility through efficiency)
- OpportunityCostModel: Stage 5a (opportunity cost calculation)
- BudgetAwarePrioritization: Stage 5b (ranking policy)
- ResourceAllocationEngine: Stage 5c (bundle optimization)

Scoring follows a staged pipeline to avoid common prioritization bugs:
1. Feasibility gate (filter before scoring)
2. Base value (intrinsic upside, no cost)
3. Execution quality modifier (confidence/risk adjustment)
4. Economic efficiency (value-per-unit-cost)
5. Portfolio allocation (bundle optimization, not just ranking)
"""

from torq_console.layer13.economics.models import (
    EconomicContext,
    ActionCandidate,
    ResourceCost,
    ResourceConstraint,
    EconomicScore,
    AllocationPlan,
    AllocatedAction,
    OpportunityCostAnalysis,
    FeasibilityResult,
    ScoringConfig,
)

from torq_console.layer13.economics.economic_evaluation_engine import (
    EconomicEvaluationEngine,
    create_evaluation_engine,
)

from torq_console.layer13.economics.resource_allocation_engine import (
    ResourceAllocationEngine,
    AllocationStrategy,
    create_allocation_engine,
)

from torq_console.layer13.economics.opportunity_cost_model import (
    OpportunityCostModel,
    create_opportunity_cost_model,
)

from torq_console.layer13.economics.budget_aware_prioritization import (
    BudgetAwarePrioritization,
    PrioritizationConfig,
    create_prioritization,
)

from torq_console.layer13.economics.integration_adapter import (
    Layer13IntegrationAdapter,
    create_integration_adapter,
)

__all__ = [
    # Models
    "EconomicContext",
    "ActionCandidate",
    "ResourceCost",
    "ResourceConstraint",
    "EconomicScore",
    "AllocationPlan",
    "AllocatedAction",
    "OpportunityCostAnalysis",
    "FeasibilityResult",
    "ScoringConfig",
    # Engines
    "EconomicEvaluationEngine",
    "ResourceAllocationEngine",
    "OpportunityCostModel",
    "BudgetAwarePrioritization",
    "Layer13IntegrationAdapter",
    # Factory functions
    "create_evaluation_engine",
    "create_allocation_engine",
    "create_opportunity_cost_model",
    "create_prioritization",
    "create_integration_adapter",
    # Enums
    "AllocationStrategy",
]
