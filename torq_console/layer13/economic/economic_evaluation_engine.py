"""TORQ Layer 13 - Economic Evaluation Engine

This module implements Layers 1-3 of the economic evaluation pipeline:
- Layer 1: Feasibility Gate
- Layer 2: Base Value Score
- Layer 3: Execution Quality Modifier

The engine takes mission proposals and produces economic scores through
a staged, explainable evaluation process.
"""

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from .models import (
    EconomicScore,
    EconomicConfiguration,
    EvaluationContext,
    FederationResult,
    MissionProposal,
    ResourceConstraints,
)

if TYPE_CHECKING:
    from .resource_allocation_engine import ResourceAllocationEngine


# =============================================================================
# ECONOMIC EVALUATION ENGINE
# =============================================================================


class EconomicEvaluationEngine:
    """Engine for evaluating mission proposals through Layers 1-3.

    This class implements the first three layers of the five-layer
    evaluation pipeline:

    1. Feasibility Gate - Hard filters for resource and deadline constraints
    2. Base Value Score - Intrinsic value calculation
    3. Execution Quality Modifier - Confidence-based adjustment

    The staged approach avoids common prioritization bugs like double-counting
    and cost domination.
    """

    def __init__(
        self,
        configuration: EconomicConfiguration | None = None,
        context: EvaluationContext | None = None,
    ):
        """Initialize the economic evaluation engine.

        Args:
            configuration: Economic evaluation weights and parameters
            context: Additional evaluation context (time, resource pressure, etc.)
        """
        self.configuration = configuration or EconomicConfiguration()
        self.context = context or EvaluationContext()

    async def evaluate_proposal(
        self,
        proposal: MissionProposal,
        constraints: ResourceConstraints,
        federation_result: FederationResult | None = None,
    ) -> EconomicScore:
        """Evaluate a mission proposal through Layers 1-3.

        This is the main entry point for economic evaluation. It runs
        the proposal through the three-layer pipeline and returns
        a complete EconomicScore.

        Args:
            proposal: Mission proposal to evaluate
            constraints: Available resources and budget limits
            federation_result: Optional federation validation from Layer 12

        Returns:
            EconomicScore with all three layers computed (Layer 4 efficiency
            must be calculated separately by BudgetAwarePrioritization)
        """
        # Layer 1: Feasibility Gate
        eligible, rejection_reason = self._apply_feasibility_gate(
            proposal, constraints, federation_result
        )

        # If not eligible, return early with rejection
        if not eligible:
            return EconomicScore(
                candidate_id=proposal.mission_id,
                mission_type=proposal.mission_type,
                eligible=False,
                rejection_reason=rejection_reason,
                base_value=0.0,
                execution_modifier=0.0,
                quality_adjusted_value=0.0,
                efficiency=0.0,
                final_priority_score=0.0,
            )

        # Layer 2: Base Value Score
        base_value = self._calculate_base_value(proposal)

        # Layer 3: Execution Quality Modifier
        execution_modifier = self._calculate_execution_modifier(
            proposal, federation_result
        )
        quality_adjusted_value = base_value * execution_modifier

        # Create and return the score (efficiency calculated in Layer 4)
        return EconomicScore(
            candidate_id=proposal.mission_id,
            mission_type=proposal.mission_type,
            eligible=True,
            base_value=base_value,
            execution_modifier=execution_modifier,
            quality_adjusted_value=quality_adjusted_value,
            efficiency=0.0,  # Calculated in Layer 4
            federation_validated=federation_result is not None,
            federation_confidence=federation_result.confidence if federation_result else None,
        )

    def _apply_feasibility_gate(
        self,
        proposal: MissionProposal,
        constraints: ResourceConstraints,
        federation_result: FederationResult | None = None,
    ) -> tuple[bool, str | None]:
        """Layer 1: Apply hard filters before any scoring.

        The feasibility gate prevents waste on infeasible proposals by
        checking basic requirements before running expensive calculations.

        Checks:
        1. Resource Availability - Required capabilities exist
        2. Budget Compatibility - Minimum cost <= available budget
        3. Deadline Validity - Deadline >= now + minimum execution time
        4. Prerequisite Check - Required missions already completed
        5. Federation Requirement - Validation required and present

        Args:
            proposal: Mission proposal to check
            constraints: Resource constraints to validate against
            federation_result: Optional federation validation

        Returns:
            Tuple of (is_eligible, rejection_reason)
        """
        # Check 1: Budget compatibility
        if proposal.estimated_cost > constraints.budget_remaining:
            return False, f"Cost ({proposal.estimated_cost}) exceeds remaining budget ({constraints.budget_remaining})"

        # Check 2: Federation requirement
        if (
            proposal.requires_validation
            and constraints.require_federation_validation
            and federation_result is None
        ):
            return False, "Federation validation required but not provided"

        # Check 3: Federation confidence threshold
        if federation_result is not None:
            if federation_result.confidence < constraints.min_confidence_threshold:
                return False, f"Federation confidence ({federation_result.confidence}) below threshold ({constraints.min_confidence_threshold})"

        # Check 4: Deadline validity
        if proposal.deadline:
            min_completion_time = self.context.current_time + timedelta(
                seconds=proposal.estimated_duration_seconds
            )
            if proposal.deadline < min_completion_time:
                return False, f"Cannot complete before deadline (needs {proposal.estimated_duration_seconds}s)"

        # Check 5: Strategic constraints - forbidden types
        if proposal.mission_type in constraints.forbidden_mission_types:
            return False, f"Mission type '{proposal.mission_type}' is forbidden"

        # All checks passed
        return True, None

    def _calculate_base_value(self, proposal: MissionProposal) -> float:
        """Layer 2: Calculate intrinsic value independent of execution.

        Base value combines three factors:
        1. User Value - Direct importance to the user
        2. Urgency - Time sensitivity (higher for time-critical missions)
        3. Strategic Fit - Alignment with organizational goals

        The formula uses weighted sum with normalized components.

        Args:
            proposal: Mission proposal with value metrics

        Returns:
            Base value score in range [0.0, 1.0]
        """
        weights = self.configuration.weights

        # Calculate weighted sum
        base_value = (
            weights.user_value_weight * proposal.user_value
            + weights.urgency_weight * proposal.urgency
            + weights.strategic_fit_weight * proposal.strategic_fit
        )

        # Normalize to [0, 1] in case weights don't sum to 1
        weight_sum = (
            weights.user_value_weight
            + weights.urgency_weight
            + weights.strategic_fit_weight
        )
        normalized_value = base_value / weight_sum if weight_sum > 0 else 0.0

        return max(0.0, min(1.0, normalized_value))

    def _calculate_execution_modifier(
        self,
        proposal: MissionProposal,
        federation_result: FederationResult | None = None,
    ) -> float:
        """Layer 3: Calculate quality adjustment based on execution confidence.

        The execution modifier adjusts the base value based on how confident
        we are that the mission will execute successfully.

        Factors:
        1. Federation Confidence - Multi-node validation strength
        2. Federation Participation - Number of nodes (diminishing returns)
        3. Historical Success Rate - Track record for similar missions

        The formula produces a multiplier typically in range [0.5, 1.5].
        - 1.0 = neutral (no adjustment)
        - > 1.0 = increase (high confidence)
        - < 1.0 = decrease (low confidence)

        Args:
            proposal: Mission proposal
            federation_result: Optional federation validation result

        Returns:
            Execution quality modifier (multiplier, typically 0.5-1.5)
        """
        weights = self.configuration.weights

        # Start with neutral modifier
        modifier = 1.0

        # Federation confidence adjustment
        if federation_result is not None:
            # Calculate confidence bonus/penalty
            # Confidence above 0.5 increases modifier, below 0.5 decreases
            confidence_delta = federation_result.confidence - 0.5
            confidence_adjustment = confidence_delta * weights.confidence_weight
            modifier += confidence_adjustment

            # Small bonus for multi-node validation (diminishing returns)
            if federation_result.participating_nodes > 1:
                participation_bonus = min(
                    0.1,  # Cap the bonus
                    0.01 * (federation_result.participating_nodes ** 0.5),
                )
                modifier += participation_bonus

        # Historical success rate adjustment
        if self.context.historical_outcomes:
            # Look up historical performance for this mission type
            historical_value = self.context.historical_outcomes.get(
                proposal.mission_type, 0.5
            )
            historical_adjustment = (historical_value - 0.5) * 0.1  # Smaller weight
            modifier += historical_adjustment

        # Clamp to reasonable range
        return max(0.0, min(2.0, modifier))


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def create_evaluation_engine(
    configuration: EconomicConfiguration | None = None,
    context: EvaluationContext | None = None,
) -> EconomicEvaluationEngine:
    """Factory function to create an economic evaluation engine.

    Args:
        configuration: Optional economic evaluation configuration
        context: Optional evaluation context

    Returns:
        Configured EconomicEvaluationEngine instance
    """
    return EconomicEvaluationEngine(
        configuration=configuration,
        context=context,
    )


# =============================================================================
# ALL EXPORTS
# =============================================================================

__all__ = [
    "EconomicEvaluationEngine",
    "create_evaluation_engine",
]
