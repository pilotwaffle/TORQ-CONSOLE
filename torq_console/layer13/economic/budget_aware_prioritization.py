"""TORQ Layer 13 - Budget-Aware Prioritization

This module implements Layer 4 of the economic evaluation pipeline:
- Economic Efficiency Score

The prioritization system ranks missions by value achieved per unit
of resource spent, ensuring efficient resource allocation.
"""

from typing import TYPE_CHECKING

from .models import (
    EconomicScore,
    EconomicConfiguration,
    ResourceConstraints,
)

if TYPE_CHECKING:
    from .economic_evaluation_engine import EconomicEvaluationEngine


# =============================================================================
# BUDGET-AWARE PRIORITIZATION
# =============================================================================


class BudgetAwarePrioritization:
    """Engine for budget-aware mission prioritization (Layer 4).

    This class implements Layer 4 of the five-layer evaluation pipeline:
    Economic Efficiency calculation.

    Layer 4 takes the quality-adjusted value from Layer 3 and calculates
    efficiency as value per unit cost. This ensures that we maximize
    total value achieved within budget constraints.

    The efficiency score prevents cost domination - a low-cost mission
    should only win if it provides good value per dollar, not just
    because it's cheap.
    """

    def __init__(
        self,
        configuration: EconomicConfiguration | None = None,
    ):
        """Initialize the budget-aware prioritization engine.

        Args:
            configuration: Economic evaluation configuration
        """
        self.configuration = configuration or EconomicConfiguration()

    async def rank_by_efficiency(
        self,
        scored_proposals: list[EconomicScore],
        constraints: ResourceConstraints,
        costs: dict[str, float],  # mission_id -> estimated_cost
    ) -> list[EconomicScore]:
        """Layer 4: Calculate efficiency and sort proposals.

        This method takes proposals that have passed through Layers 1-3
        and calculates their economic efficiency (value per cost).
        Proposals are then ranked by efficiency to prepare for
        portfolio allocation in Layer 5.

        Args:
            scored_proposals: Proposals with Layers 1-3 scores computed
            constraints: Resource constraints including budget
            costs: Dictionary mapping mission_id to estimated cost

        Returns:
            List of EconomicScore objects with efficiency computed,
            sorted by efficiency in descending order
        """
        # Calculate efficiency for each proposal
        for score in scored_proposals:
            if score.eligible:
                cost = costs.get(score.candidate_id, 0.0)
                score.efficiency = self._calculate_efficiency(
                    score, cost, constraints
                )

        # Sort ALL proposals, eligible first, then by efficiency
        # This preserves ineligible proposals for rejection categorization
        ranked_proposals = sorted(
            scored_proposals,
            key=lambda s: (
                s.eligible,  # True (1) sorts before False (0)
                s.efficiency if s.eligible else 0.0,
                s.quality_adjusted_value,
            ),
            reverse=True,
        )

        return ranked_proposals

    def _calculate_efficiency(
        self,
        score: EconomicScore,
        cost: float,
        constraints: ResourceConstraints,
    ) -> float:
        """Calculate economic efficiency (value per unit cost).

        Efficiency measures how much value we get per dollar spent.
        Higher efficiency means better return on investment.

        Formula:
            efficiency = quality_adjusted_value / (cost + epsilon)

        The epsilon prevents division by zero and ensures that
        zero-cost missions have finite efficiency.

        Args:
            score: EconomicScore with quality_adjusted_value computed
            cost: Estimated cost of the mission
            constraints: Resource constraints

        Returns:
            Efficiency score (non-negative, higher is better)
        """
        weights = self.configuration.weights

        # Prevent division by zero
        denominator = cost + weights.cost_epsilon

        # Calculate efficiency
        efficiency = score.quality_adjusted_value / denominator

        return max(0.0, efficiency)

    async def filter_by_budget(
        self,
        ranked_proposals: list[EconomicScore],
        constraints: ResourceConstraints,
        costs: dict[str, float],
    ) -> tuple[list[EconomicScore], list[EconomicScore]]:
        """Filter proposals into affordable and unaffordable.

        This pre-filtering step helps the allocation engine by
        identifying which proposals can fit within the remaining
        budget.

        Args:
            ranked_proposals: Proposals ranked by efficiency
            constraints: Resource constraints
            costs: Dictionary mapping mission_id to estimated_cost

        Returns:
            Tuple of (affordable_proposals, unaffordable_proposals)
        """
        affordable = []
        unaffordable = []

        for proposal in ranked_proposals:
            cost = costs.get(proposal.candidate_id, 0.0)
            if cost <= constraints.budget_remaining:
                affordable.append(proposal)
            else:
                unaffordable.append(proposal)

        return affordable, unaffordable

    def apply_strategic_bonus(
        self,
        proposals: list[EconomicScore],
        required_types: list[str],
    ) -> list[EconomicScore]:
        """Apply strategic bonus for critical mission types.

        Missions that match required strategic types receive a bonus
        to their efficiency score. This ensures that critical-path
        missions are prioritized even if they have lower raw efficiency.

        The bonus is applied directly to the efficiency score and
        is recorded in the strategic_bonus field.

        Args:
            proposals: Proposals to potentially bonus
            required_types: List of mission types that are strategic

        Returns:
            Proposals with strategic bonus applied (modified in place)
        """
        weights = self.configuration.weights

        for proposal in proposals:
            if proposal.mission_type in required_types:
                # Apply strategic bonus (capped)
                bonus = min(weights.strategic_bonus_cap, 0.2)
                proposal.strategic_bonus = bonus
                proposal.efficiency += bonus

        return proposals


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def create_prioritization_engine(
    configuration: EconomicConfiguration | None = None,
) -> BudgetAwarePrioritization:
    """Factory function to create a prioritization engine.

    Args:
        configuration: Optional economic evaluation configuration

    Returns:
        Configured BudgetAwarePrioritization instance
    """
    return BudgetAwarePrioritization(configuration=configuration)


# =============================================================================
# ALL EXPORTS
# =============================================================================

__all__ = [
    "BudgetAwarePrioritization",
    "create_prioritization_engine",
]
