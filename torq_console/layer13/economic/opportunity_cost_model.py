"""TORQ Layer 13 - Opportunity Cost Model

This module implements opportunity cost analysis for Layer 5:
- Portfolio Allocation Cost Analysis

The model calculates the cost of foregone alternatives when selecting
missions for funding, enabling regret-minimizing allocation decisions.
"""

from typing import TYPE_CHECKING

from .models import (
    EconomicScore,
    OpportunityCostResult,
    ResourceConstraints,
)

if TYPE_CHECKING:
    from .resource_allocation_engine import ResourceAllocationEngine


# =============================================================================
# OPPORTUNITY COST MODEL
# =============================================================================


class OpportunityCostModel:
    """Model for calculating opportunity costs of rejected missions.

    Opportunity cost represents the value lost by not choosing an
    alternative. When we fund one mission instead of another, the
    opportunity cost is the difference in value between the two.

    This model provides:
    1. Per-mission opportunity cost calculations
    2. Strategic impact assessment
    3. Portfolio-level opportunity cost aggregation

    The opportunity cost analysis helps ensure that allocation decisions
    are made with full awareness of what is being sacrificed.
    """

    def __init__(self):
        """Initialize the opportunity cost model."""
        pass

    async def calculate_opportunity_costs(
        self,
        accepted: list[EconomicScore],
        rejected: list[EconomicScore],
        total_budget: float,
        costs: dict[str, float],  # mission_id -> estimated_cost
    ) -> dict[str, OpportunityCostResult]:
        """Calculate opportunity cost for each rejected mission.

        For each rejected mission, we find the best accepted alternative
        and calculate the cost of not choosing the rejected mission.

        The opportunity cost is measured as:
        - Value difference: rejected_value - best_accepted_value
        - Cost ratio: cost / total_budget
        - Strategic impact: low/medium/high assessment

        Args:
            accepted: Missions that were selected for funding
            rejected: Missions that were not funded (queued or rejected)
            total_budget: Total budget available
            costs: Cost for each mission

        Returns:
            Dictionary mapping rejected mission_id to OpportunityCostResult
        """
        opportunity_costs = {}

        if not accepted:
            # No accepted missions - all rejections have max opportunity cost
            for proposal in rejected:
                opportunity_costs[proposal.candidate_id] = OpportunityCostResult(
                    rejected_mission_id=proposal.candidate_id,
                    rejected_mission_value=proposal.quality_adjusted_value,
                    best_accepted_alternative_id=None,
                    best_accepted_alternative_value=0.0,
                    opportunity_cost=proposal.quality_adjusted_value,
                    opportunity_cost_ratio=costs.get(proposal.candidate_id, 0.0) / total_budget,
                    strategic_impact=self._assess_strategic_impact(
                        proposal.quality_adjusted_value, total_budget
                    ),
                )
            return opportunity_costs

        for proposal in rejected:
            # Find the best accepted alternative
            best_alternative = self._find_best_accepted_alternative(
                proposal, accepted
            )

            if best_alternative:
                # Calculate opportunity cost
                alternative_value = best_alternative.quality_adjusted_value
                opportunity_cost = max(
                    0.0, proposal.quality_adjusted_value - alternative_value
                )

                # Calculate cost ratio
                cost = costs.get(proposal.candidate_id, 0.0)
                cost_ratio = cost / total_budget if total_budget > 0 else 0.0

                # Assess strategic impact
                strategic_impact = self._assess_strategic_impact(
                    opportunity_cost, total_budget
                )

                opportunity_costs[proposal.candidate_id] = OpportunityCostResult(
                    rejected_mission_id=proposal.candidate_id,
                    rejected_mission_value=proposal.quality_adjusted_value,
                    best_accepted_alternative_id=best_alternative.candidate_id,
                    best_accepted_alternative_value=alternative_value,
                    opportunity_cost=opportunity_cost,
                    opportunity_cost_ratio=cost_ratio,
                    strategic_impact=strategic_impact,
                )
            else:
                # No accepted alternative - full value is opportunity cost
                cost = costs.get(proposal.candidate_id, 0.0)
                cost_ratio = cost / total_budget if total_budget > 0 else 0.0

                opportunity_costs[proposal.candidate_id] = OpportunityCostResult(
                    rejected_mission_id=proposal.candidate_id,
                    rejected_mission_value=proposal.quality_adjusted_value,
                    best_accepted_alternative_id=None,
                    best_accepted_alternative_value=0.0,
                    opportunity_cost=proposal.quality_adjusted_value,
                    opportunity_cost_ratio=cost_ratio,
                    strategic_impact=self._assess_strategic_impact(
                        proposal.quality_adjusted_value, total_budget
                    ),
                )

        return opportunity_costs

    def _find_best_accepted_alternative(
        self,
        rejected_proposal: EconomicScore,
        accepted: list[EconomicScore],
    ) -> EconomicScore | None:
        """Find the closest accepted mission for comparison.

        The best alternative is the accepted mission that is most
        similar to the rejected mission in terms of:
        1. Mission type (same type preferred)
        2. Quality-adjusted value (closest value)

        If no same-type mission exists, we use the accepted mission
        with the closest quality-adjusted value.

        Args:
            rejected_proposal: The rejected mission to find an alternative for
            accepted: List of accepted missions

        Returns:
            Best accepted alternative, or None if no accepted missions
        """
        if not accepted:
            return None

        # First, try to find same-type missions
        same_type = [
            a for a in accepted if a.mission_type == rejected_proposal.mission_type
        ]

        if same_type:
            # Find the one with closest value
            return self._find_closest_by_value(rejected_proposal, same_type)

        # No same-type mission - use closest value among all accepted
        return self._find_closest_by_value(rejected_proposal, accepted)

    def _find_closest_by_value(
        self,
        target: EconomicScore,
        candidates: list[EconomicScore],
    ) -> EconomicScore | None:
        """Find the candidate with closest quality-adjusted value to target.

        Args:
            target: The mission to match
            candidates: Potential matches

        Returns:
            Candidate with closest value, or None if no candidates
        """
        if not candidates:
            return None

        return min(
            candidates,
            key=lambda c: abs(c.quality_adjusted_value - target.quality_adjusted_value),
        )

    def _assess_strategic_impact(
        self,
        opportunity_cost: float,
        total_budget: float,
    ) -> str:
        """Assess the strategic impact of an opportunity cost.

        Impact is assessed based on the opportunity cost relative to
        the total budget and the absolute value lost.

        Args:
            opportunity_cost: The calculated opportunity cost
            total_budget: Total available budget

        Returns:
            Strategic impact level: "low", "medium", or "high"
        """
        # Calculate relative cost
        relative_cost = opportunity_cost / total_budget if total_budget > 0 else 0.0

        # Assess impact based on both relative and absolute cost
        if relative_cost > 0.1 or opportunity_cost > 0.5:
            return "high"
        elif relative_cost > 0.05 or opportunity_cost > 0.2:
            return "medium"
        else:
            return "low"

    async def calculate_portfolio_regret(
        self,
        opportunity_costs: dict[str, OpportunityCostResult],
    ) -> float:
        """Calculate total portfolio regret.

        Regret is the sum of all opportunity costs, representing the
        total value lost by the allocation decisions.

        Lower regret is better - it means we're not missing out on
        much value with our allocation.

        Args:
            opportunity_costs: Opportunity cost for each rejected mission

        Returns:
            Total regret score
        """
        return sum(result.opportunity_cost for result in opportunity_costs.values())

    async def identify_missed_opportunities(
        self,
        opportunity_costs: dict[str, OpportunityCostResult],
        threshold: float = 0.1,
    ) -> list[OpportunityCostResult]:
        """Identify rejected missions with high opportunity cost.

        These are "missed opportunities" - missions we should consider
        prioritizing in future budget cycles or finding alternative
        funding for.

        Args:
            opportunity_costs: All opportunity costs
            threshold: Minimum cost ratio to consider "high impact"

        Returns:
            List of high-impact opportunity costs, sorted by impact
        """
        # Filter by threshold
        high_impact = [
            result
            for result in opportunity_costs.values()
            if result.opportunity_cost_ratio >= threshold
            or result.strategic_impact == "high"
        ]

        # Sort by opportunity cost (descending)
        return sorted(high_impact, key=lambda r: r.opportunity_cost, reverse=True)


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def create_opportunity_cost_model() -> OpportunityCostModel:
    """Factory function to create an opportunity cost model.

    Returns:
        Configured OpportunityCostModel instance
    """
    return OpportunityCostModel()


# =============================================================================
# ALL EXPORTS
# =============================================================================

__all__ = [
    "OpportunityCostModel",
    "create_opportunity_cost_model",
]
