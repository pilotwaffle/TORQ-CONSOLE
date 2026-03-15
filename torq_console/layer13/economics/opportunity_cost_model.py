"""
Opportunity Cost Model - Stage 5a

This model calculates what is sacrificed by choosing one action over others.
It answers: "What value do we lose by NOT choosing the alternatives?"

Opportunity cost is calculated AFTER candidate scoring, not during initial evaluation.
"""

from typing import List, Optional

from torq_console.layer13.economics.models import (
    ActionCandidate,
    AllocationPlan,
    EconomicScore,
    EconomicContext,
    OpportunityCostAnalysis,
    ResourceCost,
)


class OpportunityCostModel:
    """
    Calculates opportunity costs for action choices.

    Stage 5a of the pipeline - comes AFTER candidate scoring.

    The model answers:
    - What gets displaced if this action is chosen?
    - What is the regret of choosing this action?
    - What alternatives could have been chosen instead?
    """

    def __init__(
        self,
        context: Optional[EconomicContext] = None,
    ):
        """
        Initialize the opportunity cost model.

        Args:
            context: Economic context with budget information
        """
        self.context = context or EconomicContext()

    async def calculate_opportunity_cost(
        self,
        chosen_action: ActionCandidate,
        chosen_score: EconomicScore,
        alternatives: List[tuple[ActionCandidate, EconomicScore]],
        budget: float,
    ) -> OpportunityCostAnalysis:
        """
        Calculate the opportunity cost of choosing an action.

        Opportunity cost = Value of best excluded alternatives - Value of chosen action

        Args:
            chosen_action: The action being considered
            chosen_score: Pre-computed score for the chosen action
            alternatives: List of (candidate, score) tuples for alternatives
            budget: Remaining budget after this choice

        Returns:
            OpportunityCostAnalysis with full opportunity cost breakdown
        """
        excluded_ids = []
        total_excluded_value = 0.0
        total_excluded_efficiency = 0.0

        # Calculate what's excluded
        for alt_candidate, alt_score in alternatives:
            if alt_candidate.id != chosen_action.id:
                excluded_ids.append(alt_candidate.id)
                total_excluded_value += alt_score.quality_adjusted_value
                total_excluded_efficiency += alt_score.efficiency

        # Find best alternative
        best_alternative_value = 0.0
        if alternatives:
            best_alternative_value = max(
                (score.quality_adjusted_value for _, score in alternatives),
                default=0.0
            )

        # Opportunity cost = value of best alternative - value of chosen
        # (if chosen is not the best, otherwise zero)
        chosen_value = chosen_score.quality_adjusted_value
        if chosen_value >= best_alternative_value:
            opportunity_cost = 0.0
        else:
            opportunity_cost = best_alternative_value - chosen_value

        # Normalize regret to 0-1
        max_possible_value = max(chosen_value, best_alternative_value)
        if max_possible_value > 0:
            regret_score = opportunity_cost / max_possible_value
        else:
            regret_score = 0.0

        # Check if alternatives could fit in remaining budget
        # Simplified: check if any single alternative fits
        could_fit_alternatives = False
        for alt_candidate, _ in alternatives:
            if alt_candidate.estimated_cost.compute_budget <= budget:
                could_fit_alternatives = True
                break

        # Calculate remaining budget after choice
        remaining_budget = budget - chosen_action.estimated_cost.compute_budget

        return OpportunityCostAnalysis(
            chosen_action_id=chosen_action.id,
            excluded_alternatives=excluded_ids,
            total_excluded_value=total_excluded_value,
            total_excluded_efficiency=total_excluded_efficiency,
            opportunity_cost=opportunity_cost,
            regret_score=regret_score,
            remaining_budget_after_choice=remaining_budget,
            could_fit_alternatives=could_fit_alternatives,
        )

    async def compare_alternatives(
        self,
        candidates: List[ActionCandidate],
        scores: List[EconomicScore],
        budget: float,
    ) -> dict[str, OpportunityCostAnalysis]:
        """
        Compare all actions to each other.

        For each action, calculate what would be sacrificed if it were chosen.

        Args:
            candidates: All candidate actions
            scores: Pre-computed scores for all candidates
            budget: Total budget available

        Returns:
            Dictionary mapping action_id to its opportunity cost analysis
        """
        # Create candidate-score pairs
        pairs = list(zip(candidates, scores))
        results = {}

        for chosen_candidate, chosen_score in pairs:
            # Get alternatives (all other actions)
            alternatives = [(c, s) for c, s in pairs if c.id != chosen_candidate.id]

            # Calculate opportunity cost for this choice
            analysis = await self.calculate_opportunity_cost(
                chosen_candidate,
                chosen_score,
                alternatives,
                budget,
            )
            results[chosen_candidate.id] = analysis

        return results

    async def calculate_bundle_opportunity_cost(
        self,
        chosen_bundle: List[tuple[ActionCandidate, EconomicScore]],
        excluded_candidates: List[tuple[ActionCandidate, EconomicScore]],
    ) -> float:
        """
        Calculate opportunity cost for a bundle of chosen actions.

        This answers: "What value do we lose by choosing THIS bundle vs alternatives?"

        Args:
            chosen_bundle: List of (candidate, score) for chosen actions
            excluded_candidates: List of (candidate, score) for excluded actions

        Returns:
            Total opportunity cost for the bundle
        """
        # Sum value of excluded actions
        excluded_value = sum(
            score.quality_adjusted_value
            for _, score in excluded_candidates
        )

        # Sum value of chosen actions
        chosen_value = sum(
            score.quality_adjusted_value
            for _, score in chosen_bundle
        )

        # Opportunity cost = excluded value - chosen value
        # (This is the "regret" of not choosing the excluded actions)
        return max(0.0, excluded_value - chosen_value)


# =============================================================================
# Factory Function
# =============================================================================

def create_opportunity_cost_model(
    context: Optional[EconomicContext] = None,
) -> OpportunityCostModel:
    """
    Factory function to create an opportunity cost model.

    Args:
        context: Optional economic context

    Returns:
        Configured OpportunityCostModel instance
    """
    return OpportunityCostModel(context=context)
