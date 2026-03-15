"""
Budget-Aware Prioritization - Stage 5b

This component handles ranking policy and strategic adjustments.
It applies opportunity cost penalties and produces final rankings.

Stage 5b comes after candidate scoring and opportunity cost calculation,
but before final bundle allocation.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from torq_console.layer13.economics.models import (
    ActionCandidate,
    EconomicContext,
    EconomicScore,
    OpportunityCostAnalysis,
)


@dataclass
class PrioritizationConfig:
    """Configuration for budget-aware prioritization."""

    # Strategic weights
    strategic_bonus_weight: float = 0.2
    domain_diversity_weight: float = 0.1

    # Opportunity cost handling
    enable_opportunity_cost_penalty: bool = True
    opportunity_cost_tolerance: float = 0.15  # Allowable regret before penalty

    # Domain balancing
    enable_domain_balancing: bool = False
    max_domain_concentration: float = 0.6  # Max share for single domain

    # Tie-breaking
    tie_break_by_urgency: bool = True
    tie_break_by_strategic: bool = True


@dataclass
class PriorityRank:
    """
    A ranked action with priority information.
    """
    action_id: str
    rank: int
    score: EconomicScore
    opportunity_cost: Optional[OpportunityCostAnalysis] = None
    priority_category: str = "medium"  # high, medium, low


class BudgetAwarePrioritization:
    """
    Ranks actions considering budget constraints and opportunity costs.

    Stage 5b of the pipeline:
    - Applies strategic bonuses
    - Applies opportunity cost penalties
    - Balances domains (if enabled)
    - Produces final ranking
    - Handles tie-breaking

    CRITICAL: This produces a RANKED LIST, but does NOT select the final bundle.
    Bundle selection is handled by ResourceAllocationEngine (Stage 5c).
    """

    def __init__(
        self,
        context: Optional[EconomicContext] = None,
        config: Optional[PrioritizationConfig] = None,
    ):
        """
        Initialize the prioritization engine.

        Args:
            context: Economic context
            config: Prioritization configuration
        """
        self.context = context or EconomicContext()
        self.config = config or PrioritizationConfig()

    async def prioritize(
        self,
        candidates: List[ActionCandidate],
        scores: List[EconomicScore],
        opportunity_costs: Optional[dict[str, OpportunityCostAnalysis]] = None,
    ) -> List[PriorityRank]:
        """
        Prioritize actions considering budget and opportunity costs.

        Args:
            candidates: All candidate actions
            scores: Pre-computed scores for all candidates
            opportunity_costs: Optional opportunity cost analysis per action

        Returns:
            List of PriorityRank objects, sorted by final priority
        """
        # Create candidate-score pairs
        pairs = list(zip(candidates, scores))

        # Apply opportunity cost penalties
        if self.config.enable_opportunity_cost_penalty and opportunity_costs:
            pairs = await self._apply_opportunity_cost_penalties(pairs, opportunity_costs)

        # Apply strategic bonuses (dependency unlocks, domain alignment)
        pairs = await self._apply_strategic_bonuses(pairs)

        # Apply domain balancing (if enabled)
        if self.config.enable_domain_balancing:
            pairs = await self._apply_domain_balancing(pairs)

        # Re-calculate final scores after adjustments
        adjusted_scores = []
        for candidate, score in pairs:
            # Re-score with adjustments
            final_score = (
                self.context.qav_weight * score.quality_adjusted_value +
                self.context.efficiency_weight * score.efficiency +
                self.context.strategy_weight * score.strategic_bonus -
                self.context.opp_cost_weight * score.opportunity_cost_penalty
            )
            score.final_priority_score = final_score
            adjusted_scores.append((candidate, score))

        # Sort by final score
        sorted_pairs = sorted(
            adjusted_scores,
            key=lambda x: x[1].final_priority_score,
            reverse=True,
        )

        # Apply tie-breaking
        sorted_pairs = await self._apply_tie_breaking(sorted_pairs)

        # Determine priority categories
        max_score = sorted_pairs[0][1].final_priority_score if sorted_pairs else 1.0
        min_score = sorted_pairs[-1][1].final_priority_score if sorted_pairs else 0.0
        score_range = max_score - min_score if max_score != min_score else 1.0

        # Create ranks
        ranks = []
        for rank, (candidate, score) in enumerate(sorted_pairs, start=1):
            # Normalize score to 0-1 for category
            norm_score = (score.final_priority_score - min_score) / score_range

            # Determine category
            if norm_score >= 0.7:
                category = "high"
            elif norm_score >= 0.4:
                category = "medium"
            else:
                category = "low"

            # Get opportunity cost if available
            opp_cost = opportunity_costs.get(candidate.id) if opportunity_costs else None

            # Update recommendation based on rank and budget
            # (This is preliminary; final allocation may differ)
            score.recommendation = "execute"  # Default for high-ranked

            ranks.append(PriorityRank(
                action_id=candidate.id,
                rank=rank,
                score=score,
                opportunity_cost=opp_cost,
                priority_category=category,
            ))

        return ranks

    async def identify_deferrals(
        self,
        ranks: List[PriorityRank],
        budget: float,
    ) -> tuple[List[PriorityRank], List[PriorityRank]]:
        """
        Split prioritized actions into execute-now vs defer.

        This is a preliminary split. The final bundle is determined by
        ResourceAllocationEngine.

        Args:
            ranks: Prioritized actions
            budget: Available budget

        Returns:
            Tuple of (execute_now, defer_later) lists
        """
        execute_now = []
        defer_later = []
        remaining_budget = budget

        for rank in ranks:
            cost = rank.score.total_cost

            if cost <= remaining_budget:
                execute_now.append(rank)
                remaining_budget -= cost
            else:
                defer_later.append(rank)

        return execute_now, defer_later

    # ==========================================================================
    # Private Methods
    # ==========================================================================

    async def _apply_opportunity_cost_penalties(
        self,
        pairs: List[tuple[ActionCandidate, EconomicScore]],
        opportunity_costs: dict[str, OpportunityCostAnalysis],
    ) -> List[tuple[ActionCandidate, EconomicScore]]:
        """Apply opportunity cost penalties to scores."""
        result = []

        for candidate, score in pairs:
            opp_cost = opportunity_costs.get(candidate.id)

            if opp_cost and opp_cost.opportunity_cost > 0:
                # Apply penalty proportional to opportunity cost
                penalty = opp_cost.opportunity_cost * self.context.opp_cost_weight
                score.opportunity_cost_penalty = penalty

            result.append((candidate, score))

        return result

    async def _apply_strategic_bonuses(
        self,
        pairs: List[tuple[ActionCandidate, EconomicScore]],
    ) -> List[tuple[ActionCandidate, EconomicScore]]:
        """Apply strategic bonuses for dependency unlocks and alignment."""
        result = []

        for candidate, score in pairs:
            # Base strategic bonus from candidate
            bonus = candidate.strategic_alignment * self.config.strategic_bonus_weight

            # Dependency unlock bonus
            # TODO: Calculate which other actions this enables
            # For now, use a simple heuristic: more dependencies = higher unlock potential
            if candidate.dependencies:
                unlock_bonus = 0.05 * len(candidate.dependencies)
                bonus += unlock_bonus

            score.strategic_bonus = bonus
            result.append((candidate, score))

        return result

    async def _apply_domain_balancing(
        self,
        pairs: List[tuple[ActionCandidate, EconomicScore]],
    ) -> List[tuple[ActionCandidate, EconomicScore]]:
        """Apply domain balancing to prevent concentration."""
        # Count domain distribution
        domain_counts: dict[str, int] = {}
        for candidate, _ in pairs:
            domain_counts[candidate.domain] = domain_counts.get(candidate.domain, 0) + 1

        total = len(pairs)
        result = []

        for candidate, score in pairs:
            domain_concentration = domain_counts.get(candidate.domain, 0) / total

            # If domain is over-represented, apply penalty
            if domain_concentration > self.config.max_domain_concentration:
                penalty = (domain_concentration - self.config.max_domain_concentration) * 0.1
                score.strategic_bonus -= penalty

            result.append((candidate, score))

        return result

    async def _apply_tie_breaking(
        self,
        pairs: List[tuple[ActionCandidate, EconomicScore]],
    ) -> List[tuple[ActionCandidate, EconomicScore]]:
        """Apply tie-breaking rules for equal-scoring actions."""
        # Group by score
        score_groups: dict[float, List[tuple[ActionCandidate, EconomicScore]]] = {}
        for pair in pairs:
            score_val = round(pair[1].final_priority_score, 6)
            score_groups.setdefault(score_val, []).append(pair)

        # Sort within each tie group
        result = []
        for score_val, group in sorted(score_groups.items(), reverse=True):

            if len(group) == 1:
                result.append(group[0])
            else:
                # Apply tie-breaking
                if self.config.tie_break_by_urgency:
                    group.sort(key=lambda x: x[0].urgency, reverse=True)

                if self.config.tie_break_by_strategic:
                    # Secondary tie-break by strategic alignment
                    # Sort in-place (stable sort preserves urgency order)
                    group.sort(key=lambda x: x[0].strategic_alignment, reverse=True)

                result.extend(group)

        return result


# =============================================================================
# Factory Function
# =============================================================================

def create_prioritization(
    context: Optional[EconomicContext] = None,
    config: Optional[PrioritizationConfig] = None,
) -> BudgetAwarePrioritization:
    """
    Factory function to create a prioritization engine.

    Args:
        context: Optional economic context
        config: Optional prioritization configuration

    Returns:
        Configured BudgetAwarePrioritization instance
    """
    return BudgetAwarePrioritization(context=context, config=config)
