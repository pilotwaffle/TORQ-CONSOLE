"""
Economic Evaluation Engine - Stages 1 through 4

This engine implements the first four stages of the scoring pipeline:
1. Feasibility gate (filter before scoring)
2. Base value (intrinsic upside, no cost)
3. Execution quality modifier (confidence/risk adjustment)
4. Economic efficiency (value-per-unit-cost)

CRITICAL: This engine does NOT handle opportunity cost or bundle allocation.
Those are handled by OpportunityCostModel and ResourceAllocationEngine (Stage 5).
"""

import asyncio
from typing import Any, Dict, List, Optional

from torq_console.layer13.economics.models import (
    ActionCandidate,
    EconomicContext,
    EconomicScore,
    FeasibilityResult,
    RecommendationReason,
    ScoringConfig,
    ResourceCost,
)


class EconomicEvaluationEngine:
    """
    Evaluates action candidates through a staged scoring pipeline.

    Stages:
        1. Feasibility Gate: Filter out ineligible candidates
        2. Base Value: Calculate intrinsic upside (no cost yet)
        3. Execution Modifier: Adjust for confidence, risk, dependencies
        4. Efficiency: Calculate value-per-unit-cost
        5. (NOT HERE) Opportunity Cost & Allocation: Handled by separate engines

    The engine stores ALL intermediate values in EconomicScore for explainability.
    """

    def __init__(
        self,
        context: EconomicContext,
        config: Optional[ScoringConfig] = None,
    ):
        """
        Initialize the evaluation engine.

        Args:
            context: Economic context with budgets and thresholds
            config: Optional scoring configuration to override defaults
        """
        self.context = context
        self.config = config or ScoringConfig()

    # ==========================================================================
    # Stage 1: Feasibility Gate
    # ==========================================================================

    async def check_feasibility(
        self,
        candidate: ActionCandidate,
        available_dependencies: Optional[set[str]] = None,
    ) -> FeasibilityResult:
        """
        Stage 1: Feasibility Gate

        Filter candidates BEFORE scoring to prevent bad options from
        contaminating the ranking.

        Checks:
        - Policy allowed (domain not blocked)
        - Dependencies satisfied (all prerequisites exist)
        - Confidence above floor (not too uncertain)
        - Risk below ceiling (not too dangerous)
        - Resource minimums met (can actually execute)

        Args:
            candidate: Action candidate to check
            available_dependencies: Set of completed action IDs

        Returns:
            FeasibilityResult with eligible flag and rejection reason if not eligible
        """
        available_dependencies = available_dependencies or set()

        checks = {
            "policy_allowed": True,
            "dependencies_satisfied": True,
            "confidence_above_floor": True,
            "risk_below_ceiling": True,
            "resource_minimums_met": True,
        }

        rejection_reason: Optional[RecommendationReason] = None
        rejection_detail: Optional[str] = None

        # Check 1: Policy allowed
        if self.config.enable_feasibility_gate:
            if candidate.domain in self.context.blocked_domains:
                checks["policy_allowed"] = False
                rejection_reason = RecommendationReason.POLICY_VIOLATION
                rejection_detail = f"Domain '{candidate.domain}' is blocked"

            if self.context.allowed_domains and candidate.domain not in self.context.allowed_domains:
                checks["policy_allowed"] = False
                rejection_reason = RecommendationReason.POLICY_VIOLATION
                rejection_detail = f"Domain '{candidate.domain}' not in allowed list"

        # Check 2: Dependencies satisfied
        if self.config.require_dependencies_satisfied and candidate.dependencies:
            missing_deps = set(candidate.dependencies) - available_dependencies
            if missing_deps:
                checks["dependencies_satisfied"] = False
                rejection_reason = RecommendationReason.DEPENDENCIES_MISSING
                rejection_detail = f"Missing dependencies: {missing_deps}"

        # Check 3: Confidence above floor
        if self.config.require_confidence_above_floor:
            if candidate.confidence < self.context.confidence_floor:
                checks["confidence_above_floor"] = False
                rejection_reason = RecommendationReason.LOW_CONFIDENCE
                rejection_detail = f"Confidence {candidate.confidence:.2f} below floor {self.context.confidence_floor:.2f}"

        # Check 4: Risk below ceiling
        if self.config.require_risk_below_ceiling:
            if candidate.risk > self.context.risk_ceiling:
                checks["risk_below_ceiling"] = False
                rejection_reason = RecommendationReason.HIGH_RISK
                rejection_detail = f"Risk {candidate.risk:.2f} above ceiling {self.context.risk_ceiling:.2f}"

        # Check 5: Resource minimums met (cost is not zero or unknown)
        # TODO: Add resource availability checks when resource tracking is implemented

        eligible = all(checks.values())

        return FeasibilityResult(
            eligible=eligible,
            rejection_reason=rejection_reason,
            rejection_detail=rejection_detail,
            **checks
        )

    # ==========================================================================
    # Stage 2: Base Value (Intrinsic Upside, NO Cost Yet)
    # ==========================================================================

    async def calculate_base_value(
        self,
        candidate: ActionCandidate,
        all_candidates: Optional[List[ActionCandidate]] = None,
    ) -> tuple[float, float, float, float]:
        """
        Stage 2: Base Value Calculation

        Calculate intrinsic upside WITHOUT considering cost.
        This answers: "How attractive is this action if it works?"

        Inputs:
        - estimated_value
        - urgency
        - time_to_realization

        Does NOT include:
        - cost (comes later in Stage 4)
        - confidence (comes later in Stage 3)
        - risk (comes later in Stage 3)

        Args:
            candidate: Action to evaluate
            all_candidates: All candidates for normalization

        Returns:
            Tuple of (base_value, normalized_value, urgency_score, time_realization_score)
        """
        all_candidates = all_candidates or [candidate]

        # Normalize value against the candidate set
        values = [c.estimated_value for c in all_candidates]
        max_val = max(values) if values else 1.0
        min_val = min(values) if values else 0.0
        val_range = max_val - min_val if max_val != min_val else 1.0

        normalized_value = (candidate.estimated_value - min_val) / val_range

        # Urgency is already 0-1, use as-is
        urgency_score = candidate.urgency

        # Time realization score: faster is better
        # Normalize by max time in set
        times = [c.time_to_realization for c in all_candidates]
        max_time = max(times) if times else 1.0
        if max_time > 0:
            time_realization_score = 1.0 - (candidate.time_to_realization / max_time)
        else:
            time_realization_score = 1.0

        # Weighted combination for base value
        # CRITICAL: Cost is NOT here
        base_value = (
            self.config.value_weight * normalized_value +
            self.config.urgency_weight * urgency_score +
            self.config.speed_weight * time_realization_score
        )

        return base_value, normalized_value, urgency_score, time_realization_score

    # ==========================================================================
    # Stage 3: Execution Quality Modifier
    # ==========================================================================

    async def calculate_execution_modifier(
        self,
        candidate: ActionCandidate,
    ) -> tuple[float, float, float, float]:
        """
        Stage 3: Execution Quality Modifier

        Discount base value by how likely and safely it can be realized.

        Inputs:
        - confidence (used ONCE here)
        - risk
        - dependency complexity

        CRITICAL: Confidence should appear ONLY HERE, not in other stages.

        Args:
            candidate: Action to evaluate

        Returns:
            Tuple of (modifier, confidence_factor, risk_penalty, dependency_simplicity)
        """
        # Confidence factor: from candidate (0-1)
        confidence_factor = candidate.confidence

        # Risk penalty: higher risk = higher penalty
        risk_penalty = candidate.risk

        # Dependency simplicity: fewer dependencies = simpler
        dep_count = len(candidate.dependencies)
        dependency_simplicity = 1.0 / (1.0 + dep_count)

        # Combine into execution modifier
        # CRITICAL: Confidence appears only in this calculation
        modifier = max(
            0.1,  # Floor - even risky/low-confidence actions get 10%
            self.config.confidence_weight * confidence_factor +
            self.config.simplicity_weight * dependency_simplicity -
            self.config.risk_penalty_weight * risk_penalty
        )

        # Clamp to reasonable range (allow small bonus for high confidence/low risk)
        modifier = min(1.25, modifier)

        return modifier, confidence_factor, risk_penalty, dependency_simplicity

    # ==========================================================================
    # Stage 4: Economic Efficiency
    # ==========================================================================

    async def calculate_efficiency(
        self,
        quality_adjusted_value: float,
        candidate: ActionCandidate,
    ) -> tuple[float, float]:
        """
        Stage 4: Economic Efficiency

        Calculate value-per-unit-cost.

        Efficiency = Quality-Adjusted Value / Cost

        CRITICAL: Keep both quality_adjusted_value AND efficiency.
        Do NOT use efficiency alone, or cheap trivial actions will dominate.

        Args:
            quality_adjusted_value: Value after execution modifier
            candidate: Action with cost information

        Returns:
            Tuple of (efficiency, total_cost)
        """
        # Normalize cost to single dimension
        # For v1, use compute_budget as primary cost
        # TODO: Handle multi-dimensional costs properly
        total_cost = max(candidate.estimated_cost.compute_budget, self.config.cost_floor)

        # Efficiency: value per unit cost
        efficiency = quality_adjusted_value / total_cost

        return efficiency, total_cost

    # ==========================================================================
    # Full Pipeline (Stages 1-4)
    # ==========================================================================

    async def evaluate_candidate(
        self,
        candidate: ActionCandidate,
        all_candidates: Optional[List[ActionCandidate]] = None,
        available_dependencies: Optional[set[str]] = None,
    ) -> EconomicScore:
        """
        Run complete Stages 1-4 evaluation pipeline.

        Stage 5 (opportunity cost and allocation) is handled separately
        by OpportunityCostModel and ResourceAllocationEngine.

        Args:
            candidate: Action to evaluate
            all_candidates: All candidates for normalization/competition
            available_dependencies: Set of completed action IDs

        Returns:
            EconomicScore with all intermediate values stored
        """
        all_candidates = all_candidates or [candidate]

        # Stage 1: Feasibility Gate
        feasibility = await self.check_feasibility(candidate, available_dependencies)

        if not feasibility.eligible:
            return EconomicScore(
                candidate_id=candidate.id,
                eligible=False,
                rejection_reason=feasibility.rejection_reason,
                recommendation="reject",
                rationale=f"Failed feasibility: {feasibility.rejection_detail}",
            )

        # Stage 2: Base Value (NO cost yet)
        base_value, normalized_value, urgency_score, time_score = \
            await self.calculate_base_value(candidate, all_candidates)

        # Stage 3: Execution Modifier (confidence used ONCE here)
        modifier, conf_factor, risk_penalty, dep_simplicity = \
            await self.calculate_execution_modifier(candidate)

        # Combined: Quality-Adjusted Value
        quality_adjusted_value = base_value * modifier

        # Stage 4: Efficiency
        efficiency, total_cost = \
            await self.calculate_efficiency(quality_adjusted_value, candidate)

        # Calculate preliminary final score (without opportunity cost yet)
        # Opportunity cost will be added by OpportunityCostModel in Stage 5
        final_priority_score = (
            self.config.qav_weight * quality_adjusted_value +
            self.config.efficiency_weight * efficiency +
            self.config.strategy_weight * candidate.strategic_alignment
        )

        # Determine preliminary recommendation
        # Will be refined by ResourceAllocationEngine in Stage 5
        if final_priority_score >= self.config.execute_threshold:
            recommendation = "execute"
        elif final_priority_score <= self.config.reject_threshold:
            recommendation = "reject"
        else:
            recommendation = "defer"

        # Build score breakdown for explainability
        score_breakdown = {
            "base_value": base_value,
            "normalized_value": normalized_value,
            "urgency_score": urgency_score,
            "time_score": time_score,
            "execution_modifier": modifier,
            "confidence_factor": conf_factor,
            "risk_penalty": risk_penalty,
            "dependency_simplicity": dep_simplicity,
            "quality_adjusted_value": quality_adjusted_value,
            "efficiency": efficiency,
            "total_cost": total_cost,
            "strategic_alignment": candidate.strategic_alignment,
        }

        # Generate rationale
        rationale = (
            f"Base value {base_value:.2f} adjusted by "
            f"execution modifier {modifier:.2f} → {quality_adjusted_value:.2f}. "
            f"Efficiency: {efficiency:.2f} per unit cost."
        )

        return EconomicScore(
            candidate_id=candidate.id,
            eligible=True,

            # Stage 2
            base_value=base_value,
            normalized_value=normalized_value,
            urgency_score=urgency_score,
            time_realization_score=time_score,

            # Stage 3
            execution_modifier=modifier,
            confidence_factor=conf_factor,
            risk_penalty=risk_penalty,
            dependency_simplicity=dep_simplicity,
            quality_adjusted_value=quality_adjusted_value,

            # Stage 4
            efficiency=efficiency,
            total_cost=total_cost,

            # Stage 5 (will be populated by other engines)
            strategic_bonus=candidate.strategic_alignment,
            opportunity_cost_penalty=0.0,  # Populated by OpportunityCostModel
            dependency_unlock_bonus=0.0,  # Populated by ResourceAllocationEngine

            # Final
            final_priority_score=final_priority_score,
            recommendation=recommendation,
            rationale=rationale,
            score_breakdown=score_breakdown,
        )

    async def evaluate_batch(
        self,
        candidates: List[ActionCandidate],
        available_dependencies: Optional[set[str]] = None,
    ) -> List[EconomicScore]:
        """
        Evaluate multiple candidates in parallel.

        Args:
            candidates: All candidates to evaluate
            available_dependencies: Set of completed action IDs

        Returns:
            List of EconomicScore objects, one per candidate
        """
        tasks = [
            self.evaluate_candidate(c, candidates, available_dependencies)
            for c in candidates
        ]
        return await asyncio.gather(*tasks)


# =============================================================================
# Factory Function
# =============================================================================

def create_evaluation_engine(
    context: Optional[EconomicContext] = None,
    config: Optional[ScoringConfig] = None,
) -> EconomicEvaluationEngine:
    """
    Factory function to create an evaluation engine.

    Args:
        context: Optional economic context (uses defaults if None)
        config: Optional scoring config (uses defaults if None)

    Returns:
        Configured EconomicEvaluationEngine instance
    """
    if context is None:
        context = EconomicContext()

    return EconomicEvaluationEngine(context=context, config=config)
