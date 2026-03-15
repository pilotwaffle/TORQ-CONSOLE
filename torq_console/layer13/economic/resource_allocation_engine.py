"""TORQ Layer 13 - Resource Allocation Engine

This module implements Layer 5 of the economic evaluation pipeline:
- Portfolio Allocation

The allocation engine selects the optimal mission set under budget
constraints using knapsack-style optimization with opportunity cost
analysis.
"""

from typing import TYPE_CHECKING

from .models import (
    AllocationResult,
    EconomicConfiguration,
    EconomicScore,
    OpportunityCostResult,
    ResourceConstraints,
)

if TYPE_CHECKING:
    from .opportunity_cost_model import OpportunityCostModel


# =============================================================================
# RESOURCE ALLOCATION ENGINE
# =============================================================================


class ResourceAllocationEngine:
    """Engine for budget-constrained resource allocation (Layer 5).

    This class implements Layer 5 of the five-layer evaluation pipeline:
    Portfolio Allocation.

    Layer 5 selects the optimal set of missions to fund given budget
    constraints. It uses a greedy knapsack-style approach optimized
    for economic efficiency.

    The engine produces:
    - Funded missions (selected for execution)
    - Queued missions (valid but not funded due to budget)
    - Rejected missions (failed some criteria)
    - Opportunity cost analysis for rejected missions
    """

    def __init__(
        self,
        configuration: EconomicConfiguration | None = None,
    ):
        """Initialize the resource allocation engine.

        Args:
            configuration: Economic evaluation configuration
        """
        self.configuration = configuration or EconomicConfiguration()

    async def allocate_budget(
        self,
        ranked_proposals: list[EconomicScore],
        constraints: ResourceConstraints,
        costs: dict[str, float],  # mission_id -> estimated_cost
    ) -> AllocationResult:
        """Layer 5: Select mission set under budget constraint.

        This method implements the portfolio allocation layer, selecting
        which missions to fund based on:
        1. Efficiency ranking (from Layer 4)
        2. Budget constraints
        3. Strategic requirements

        The algorithm uses greedy selection by efficiency, which is
        near-optimal for fractional knapsack and provides good
        approximations for 0-1 knapsack.

        Args:
            ranked_proposals: Proposals ranked by efficiency (descending)
            constraints: Resource constraints including available budget
            costs: Dictionary mapping mission_id to estimated_cost

        Returns:
            AllocationResult with funded/queued/rejected missions and metrics
        """
        # Separate eligible from ineligible proposals
        eligible = [p for p in ranked_proposals if p.eligible]
        ineligible = [p for p in ranked_proposals if not p.eligible]

        # Apply knapsack selection
        funded_ids, queued_ids = self._apply_knapsack_selection(
            eligible,
            costs,
            constraints.budget_remaining,
        )

        # Calculate totals and create result
        funded_proposals = [p for p in eligible if p.candidate_id in funded_ids]
        queued_proposals = [p for p in eligible if p.candidate_id in queued_ids]

        # Calculate total costs and values
        funded_total_cost = sum(costs.get(p.candidate_id, 0.0) for p in funded_proposals)
        funded_total_value = sum(p.quality_adjusted_value for p in funded_proposals)
        queued_total_cost = sum(costs.get(p.candidate_id, 0.0) for p in queued_proposals)
        queued_total_value = sum(p.quality_adjusted_value for p in queued_proposals)

        # Build rejected list
        rejected_ids = [p.candidate_id for p in ineligible]
        rejected_reasons = {
            p.candidate_id: p.rejection_reason or "Not specified"
            for p in ineligible
        }

        # Calculate budget status
        budget_utilization = funded_total_cost / constraints.total_budget
        remaining_budget = constraints.budget_remaining - funded_total_cost

        # Calculate metrics
        allocation_efficiency = (
            funded_total_value / funded_total_cost if funded_total_cost > 0 else 0.0
        )

        # Calculate regret (value of best foregone alternative)
        regret_score = self._calculate_regret(queued_proposals)

        # Build result (opportunity costs calculated separately)
        result = AllocationResult(
            funded_mission_ids=funded_ids,
            funded_total_cost=funded_total_cost,
            funded_total_value=funded_total_value,
            queued_mission_ids=queued_ids,
            queued_total_cost=queued_total_cost,
            queued_total_value=queued_total_value,
            rejected_mission_ids=rejected_ids,
            rejected_reasons=rejected_reasons,
            budget_utilization=budget_utilization,
            remaining_budget=remaining_budget,
            opportunity_costs={},  # Populated by OpportunityCostModel
            allocation_efficiency=allocation_efficiency,
            regret_score=regret_score,
        )

        return result

    def _apply_knapsack_selection(
        self,
        proposals: list[EconomicScore],
        costs: dict[str, float],
        budget: float,
    ) -> tuple[list[str], list[str]]:
        """Select funded vs queued missions using knapsack optimization.

        This implements a greedy 0-1 knapsack algorithm. Missions are
        considered in order of efficiency (already sorted) and selected
        if they fit within the remaining budget.

        Args:
            proposals: Eligible proposals ranked by efficiency
            costs: Cost for each proposal
            budget: Remaining budget

        Returns:
            Tuple of (funded_mission_ids, queued_mission_ids)
        """
        funded = []
        queued = []
        remaining_budget = budget

        for proposal in proposals:
            cost = costs.get(proposal.candidate_id, 0.0)

            if cost <= remaining_budget:
                # Mission fits within budget - fund it
                funded.append(proposal.candidate_id)
                remaining_budget -= cost
            else:
                # Mission doesn't fit - queue for next budget cycle
                queued.append(proposal.candidate_id)

        return funded, queued

    def _calculate_regret(
        self,
        queued_proposals: list[EconomicScore],
    ) -> float:
        """Calculate regret score (value of best foregone alternative).

        Regret is the quality-adjusted value of the highest-value
        mission that had to be queued due to budget constraints.

        Lower regret means we're not missing out on much by not
        having infinite budget.

        Args:
            queued_proposals: Proposals that were queued (not funded)

        Returns:
            Regret score (0.0 if no queued proposals)
        """
        if not queued_proposals:
            return 0.0

        # Best queued proposal is the one with highest quality-adjusted value
        best_queued = max(queued_proposals, key=lambda p: p.quality_adjusted_value)
        return best_queued.quality_adjusted_value

    async def allocate_with_strategic_constraints(
        self,
        ranked_proposals: list[EconomicScore],
        constraints: ResourceConstraints,
        costs: dict[str, float],
    ) -> AllocationResult:
        """Allocate budget with strategic mission type constraints.

        This variant of allocation ensures that required mission types
        are prioritized even if they have lower efficiency scores.

        The algorithm:
        1. First, fund all required-type missions that fit
        2. Then, fund remaining missions by efficiency

        Args:
            ranked_proposals: Proposals ranked by efficiency
            constraints: Resource constraints (including required_types)
            costs: Cost for each proposal

        Returns:
            AllocationResult with strategic constraints applied
        """
        if not constraints.required_mission_types:
            # No strategic constraints - use standard allocation
            return await self.allocate_budget(ranked_proposals, constraints, costs)

        # Separate required and optional missions
        required = [
            p
            for p in ranked_proposals
            if p.mission_type in constraints.required_mission_types
        ]
        optional = [
            p
            for p in ranked_proposals
            if p.mission_type not in constraints.required_mission_types
        ]

        funded = []
        queued = []
        remaining_budget = constraints.budget_remaining

        # First pass: fund required missions
        for proposal in required:
            cost = costs.get(proposal.candidate_id, 0.0)
            if cost <= remaining_budget:
                funded.append(proposal.candidate_id)
                remaining_budget -= cost
            else:
                queued.append(proposal.candidate_id)

        # Second pass: fund optional missions by efficiency
        for proposal in optional:
            cost = costs.get(proposal.candidate_id, 0.0)
            if cost <= remaining_budget:
                funded.append(proposal.candidate_id)
                remaining_budget -= cost
            else:
                queued.append(proposal.candidate_id)

        # Build result (similar to allocate_budget)
        eligible = [p for p in ranked_proposals if p.eligible]
        ineligible = [p for p in ranked_proposals if not p.eligible]

        funded_proposals = [p for p in eligible if p.candidate_id in funded]
        queued_proposals = [p for p in eligible if p.candidate_id in queued]

        result = AllocationResult(
            funded_mission_ids=funded,
            funded_total_cost=sum(costs.get(p.candidate_id, 0.0) for p in funded_proposals),
            funded_total_value=sum(p.quality_adjusted_value for p in funded_proposals),
            queued_mission_ids=queued,
            queued_total_cost=sum(costs.get(p.candidate_id, 0.0) for p in queued_proposals),
            queued_total_value=sum(p.quality_adjusted_value for p in queued_proposals),
            rejected_mission_ids=[p.candidate_id for p in ineligible],
            rejected_reasons={
                p.candidate_id: p.rejection_reason or "Not specified" for p in ineligible
            },
            budget_utilization=(constraints.budget_remaining - remaining_budget) / constraints.total_budget,
            remaining_budget=remaining_budget,
            opportunity_costs={},
            allocation_efficiency=(
                sum(p.quality_adjusted_value for p in funded_proposals) /
                sum(costs.get(p.candidate_id, 0.0) for p in funded_proposals)
                if funded_proposals else 0.0
            ),
            regret_score=self._calculate_regret(queued_proposals),
        )

        return result


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def create_allocation_engine(
    configuration: EconomicConfiguration | None = None,
) -> ResourceAllocationEngine:
    """Factory function to create a resource allocation engine.

    Args:
        configuration: Optional economic evaluation configuration

    Returns:
        Configured ResourceAllocationEngine instance
    """
    return ResourceAllocationEngine(configuration=configuration)


# =============================================================================
# ALL EXPORTS
# =============================================================================

__all__ = [
    "ResourceAllocationEngine",
    "create_allocation_engine",
]
