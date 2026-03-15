"""
Resource Allocation Engine - Stage 5c

This engine handles the final bundle selection under budget constraints.

CRITICAL: This does NOT simply pick top-ranked actions.
It optimizes the BUNDLE as a whole, considering:
- Budget constraints
- Dependencies
- Total bundle value
- Opportunity cost of excluded actions

This is the difference between "pick best N" and "pick best SET".
"""

from enum import Enum
from typing import List, Optional, Tuple
import asyncio

from torq_console.layer13.economics.models import (
    ActionCandidate,
    AllocationPlan,
    AllocationStrategy,
    AllocatedAction,
    EconomicContext,
    EconomicScore,
    OpportunityCostAnalysis,
)


class ResourceAllocationEngine:
    """
    Allocates constrained resources across a set of actions.

    Stage 5c of the pipeline - final bundle optimization.

    CRITICAL: This optimizes across a SET of actions, not just sorting.
    The highest-ranked individual action is not always the best bundle choice.

    Strategies:
    - GREEDY: Pick highest net-benefit first until budget exhausted
    - OPTIMAL: Solve knapsack for optimal bundle (slower but better)
    - SATISFICE: Good enough, fast selection
    """

    def __init__(
        self,
        context: Optional[EconomicContext] = None,
        strategy: AllocationStrategy = AllocationStrategy.GREEDY,
    ):
        """
        Initialize the allocation engine.

        Args:
            context: Economic context with budget constraints
            strategy: Allocation strategy to use
        """
        self.context = context or EconomicContext()
        self.strategy = strategy

    async def allocate(
        self,
        candidates: List[ActionCandidate],
        scores: List[EconomicScore],
        budget: float,
        opportunity_costs: Optional[dict[str, OpportunityCostAnalysis]] = None,
        available_dependencies: Optional[set[str]] = None,
    ) -> AllocationPlan:
        """
        Allocate budget to optimize total value.

        CRITICAL: This does NOT simply pick top-N by score.
        It considers the BUNDLE as a whole.

        Args:
            candidates: All candidate actions
            scores: Pre-computed scores for all candidates
            budget: Total budget available
            opportunity_costs: Optional opportunity cost analysis
            available_dependencies: Set of completed action IDs

        Returns:
            AllocationPlan with optimal bundle selection
        """
        available_dependencies = available_dependencies or set()

        # Filter eligible candidates
        eligible_pairs = [
            (c, s) for c, s in zip(candidates, scores)
            if s.eligible and self._dependencies_satisfied(c, available_dependencies)
        ]

        if not eligible_pairs:
            return self._create_empty_plan(budget)

        # Choose allocation strategy
        if self.strategy == AllocationStrategy.GREEDY:
            selected = await self._greedy_allocation(eligible_pairs, budget)
        elif self.strategy == AllocationStrategy.OPTIMAL:
            selected = await self._optimal_allocation(eligible_pairs, budget)
        else:  # SATISFICE
            selected = await self._satisfice_allocation(eligible_pairs, budget)

        # Build allocation plan
        return await self._build_plan(
            eligible_pairs,
            selected,
            budget,
            opportunity_costs,
        )

    async def _greedy_allocation(
        self,
        pairs: List[Tuple[ActionCandidate, EconomicScore]],
        budget: float,
    ) -> List[Tuple[ActionCandidate, EconomicScore]]:
        """
        Greedy allocation: pick highest value-per-cost first.

        This is fast but may not find the absolute optimal bundle.
        """
        # Sort by efficiency (value per cost)
        sorted_pairs = sorted(
            pairs,
            key=lambda x: x[1].efficiency,
            reverse=True,
        )

        selected = []
        remaining_budget = budget

        for candidate, score in sorted_pairs:
            cost = candidate.estimated_cost.compute_budget

            if cost <= remaining_budget:
                selected.append((candidate, score))
                remaining_budget -= cost

        return selected

    async def _optimal_allocation(
        self,
        pairs: List[Tuple[ActionCandidate, EconomicScore]],
        budget: float,
    ) -> List[Tuple[ActionCandidate, EconomicScore]]:
        """
        Optimal allocation using 0/1 knapsack.

        Finds the mathematically optimal bundle under budget.
        Slower than greedy for large candidate sets.
        """
        n = len(pairs)

        # Extract costs and values
        costs = [c.estimated_cost.compute_budget for c, _ in pairs]
        values = [s.quality_adjusted_value for _, s in pairs]

        # Scale budget to integers for DP
        scale = 100  # precision
        budget_scaled = int(budget * scale)
        costs_scaled = [int(c * scale) for c in costs]

        # DP table: dp[i][w] = max value with first i items and budget w
        dp = [[0] * (budget_scaled + 1) for _ in range(n + 1)]

        for i in range(1, n + 1):
            for w in range(budget_scaled + 1):
                # Don't take item i
                dp[i][w] = dp[i - 1][w]

                # Take item i (if it fits)
                if costs_scaled[i - 1] <= w:
                    take_value = dp[i - 1][w - costs_scaled[i - 1]] + values[i - 1]
                    if take_value > dp[i][w]:
                        dp[i][w] = take_value

        # Backtrack to find selected items
        selected = []
        w = budget_scaled
        for i in range(n, 0, -1):
            if dp[i][w] != dp[i - 1][w]:
                # Item i was taken
                selected.append(pairs[i - 1])
                w -= costs_scaled[i - 1]

        return selected

    async def _satisfice_allocation(
        self,
        pairs: List[Tuple[ActionCandidate, EconomicScore]],
        budget: float,
    ) -> List[Tuple[ActionCandidate, EconomicScore]]:
        """
        Satisficing allocation: good enough, fast.

        Targets 80% of optimal value with minimal computation.
        """
        # Start with greedy
        greedy_selection = await self._greedy_allocation(pairs, budget)

        # Calculate greedy value
        greedy_value = sum(s.quality_adjusted_value for _, s in greedy_selection)

        # If greedy is good enough (simple heuristic), return it
        if len(pairs) <= 10 or greedy_value > 0:
            return greedy_selection

        # For larger sets, add a simple local improvement step
        # Try swapping one item to see if we can improve
        selected = greedy_selection.copy()
        selected_ids = {c.id for c, _ in selected}

        for candidate, score in pairs:
            if candidate.id in selected_ids:
                continue

            # Try replacing lowest-value selected item
            if selected:
                lowest_idx = min(range(len(selected)), key=lambda i: selected[i][1].quality_adjusted_value)
                lowest_candidate, lowest_score = selected[lowest_idx]

                # Check if swap improves value and fits budget
                selected_cost = sum(c.estimated_cost.compute_budget for c, _ in selected)
                new_cost = selected_cost - lowest_candidate.estimated_cost.compute_budget + candidate.estimated_cost.compute_budget

                if new_cost <= budget:
                    new_value = sum(s.quality_adjusted_value for _, s in selected) - lowest_score.quality_adjusted_value + score.quality_adjusted_value
                    old_value = sum(s.quality_adjusted_value for _, s in selected)

                    if new_value > old_value:
                        # Make the swap
                        selected[lowest_idx] = (candidate, score)
                        selected_ids = {c.id for c, _ in selected}

        return selected

    def _dependencies_satisfied(
        self,
        candidate: ActionCandidate,
        available: set[str],
    ) -> bool:
        """Check if all dependencies are satisfied."""
        return all(dep in available for dep in candidate.dependencies)

    async def _build_plan(
        self,
        all_pairs: List[Tuple[ActionCandidate, EconomicScore]],
        selected_pairs: List[Tuple[ActionCandidate, EconomicScore]],
        budget: float,
        opportunity_costs: Optional[dict[str, OpportunityCostAnalysis]],
    ) -> AllocationPlan:
        """Build the final allocation plan."""
        selected_ids = {c.id for c, _ in selected_pairs}

        # Calculate metrics
        allocated_budget = sum(c.estimated_cost.compute_budget for c, _ in selected_pairs)
        expected_total_value = sum(s.quality_adjusted_value for _, s in selected_pairs)

        # Calculate regret (value of best excluded actions)
        excluded_pairs = [(c, s) for c, s in all_pairs if c.id not in selected_ids]
        if excluded_pairs:
            best_excluded_value = max(s.quality_adjusted_value for _, s in excluded_pairs)
            worst_included_value = min(s.quality_adjusted_value for _, s in selected_pairs) if selected_pairs else 0
            expected_regret = max(0, best_excluded_value - worst_included_value)
        else:
            expected_regret = 0.0

        # Create allocated action list
        allocated_actions = []
        for rank, (candidate, score) in enumerate(selected_pairs, start=1):
            allocated_actions.append(AllocatedAction(
                action_id=candidate.id,
                allocated_budget=candidate.estimated_cost.compute_budget,
                expected_value=score.quality_adjusted_value,
                priority_rank=rank,
                score=score,
            ))

        # Deferred and rejected lists
        deferred_actions = []
        rejected_actions = []

        for candidate, score in all_pairs:
            if candidate.id in selected_ids:
                continue

            if score.eligible and score.recommendation != "reject":
                deferred_actions.append(candidate.id)
            else:
                rejected_actions.append(candidate.id)

        # Allocation efficiency
        allocation_efficiency = allocated_budget / budget if budget > 0 else 0

        # Generate rationale
        rationale = f"Allocated {len(allocated_actions)} actions using {self.strategy.value} strategy. "
        rationale += f"Expected value: {expected_total_value:.2f}, Budget used: {allocated_budget:.2f}/{budget:.2f}"

        # Generate trace
        allocation_trace = [
            f"Strategy: {self.strategy.value}",
            f"Total budget: {budget:.2f}",
            f"Allocated: {allocated_budget:.2f} ({allocation_efficiency:.1%})",
            f"Expected value: {expected_total_value:.2f}",
            f"Actions selected: {len(allocated_actions)}",
        ]

        return AllocationPlan(
            plan_id=f"plan_{hash(budget)}",
            total_budget=budget,
            allocated_budget=allocated_budget,
            remaining_budget=budget - allocated_budget,
            allocated_actions=allocated_actions,
            expected_total_value=expected_total_value,
            expected_regret=expected_regret,
            allocation_efficiency=allocation_efficiency,
            deferred_actions=deferred_actions,
            rejected_actions=rejected_actions,
            strategy=self.strategy,
            rationale=rationale,
            allocation_trace=allocation_trace,
        )

    def _create_empty_plan(self, budget: float) -> AllocationPlan:
        """Create an empty allocation plan when no candidates are eligible."""
        return AllocationPlan(
            plan_id="empty",
            total_budget=budget,
            allocated_budget=0.0,
            remaining_budget=budget,
            allocated_actions=[],
            expected_total_value=0.0,
            expected_regret=0.0,
            allocation_efficiency=0.0,
            deferred_actions=[],
            rejected_actions=[],
            strategy=self.strategy,
            rationale="No eligible candidates to allocate",
            allocation_trace=["No eligible candidates"],
        )


# =============================================================================
# Factory Function
# =============================================================================

def create_allocation_engine(
    context: Optional[EconomicContext] = None,
    strategy: AllocationStrategy = AllocationStrategy.GREEDY,
) -> ResourceAllocationEngine:
    """
    Factory function to create a resource allocation engine.

    Args:
        context: Optional economic context
        strategy: Allocation strategy (default: GREEDY)

    Returns:
        Configured ResourceAllocationEngine instance
    """
    return ResourceAllocationEngine(context=context, strategy=strategy)
