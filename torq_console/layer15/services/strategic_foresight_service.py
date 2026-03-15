"""TORQ Layer 15 - Strategic Foresight Service

This module provides the main service interface for Layer 15 strategic foresight,
coordinating all foresight engines for decision evaluation.
"""

from typing import TYPE_CHECKING

from ..models import (
    BranchComparison,
    ConsequenceAnalysis,
    DecisionPacket,
    HorizonAlignmentResult,
    OptionalityAssessment,
    ScenarioProjection,
    StrategicForesightResult,
    StrategicWeights,
)

if TYPE_CHECKING:
    from ..foresight import (
        ScenarioProjectionEngine,
        StrategicBranchComparator,
        SecondOrderConsequenceAnalyzer,
        OptionalityPreservationEngine,
        HorizonAlignmentEngine,
    )


# =============================================================================
# STRATEGIC FORESIGHT SERVICE
# =============================================================================


class StrategicForesightService:
    """Main service for Layer 15 strategic foresight.

    This service orchestrates all foresight engines:
    - ScenarioProjectionEngine: Generate future scenarios
    - StrategicBranchComparator: Compare strategic paths
    - SecondOrderConsequenceAnalyzer: Evaluate downstream effects
    - OptionalityPreservationEngine: Assess reversibility
    - HorizonAlignmentEngine: Score time-horizon alignment

    The service acts as the strategic evaluation layer AFTER
    Layer 14 legitimacy checks.
    """

    def __init__(
        self,
        weights: StrategicWeights | None = None,
        deep_foresight_threshold: float = 0.8,
    ):
        """Initialize the strategic foresight service.

        Args:
            weights: Optional custom weights for strategic scoring
            deep_foresight_threshold: Threshold for requiring deep foresight analysis
        """
        self.weights = weights or StrategicWeights()
        self.deep_foresight_threshold = deep_foresight_threshold
        self.enabled = True

        # Engines (will be set later)
        self._scenario_engine = None
        self._branch_comparator = None
        self._consequence_analyzer = None
        self._optionality_engine = None
        self._alignment_engine = None

    def set_engines(
        self,
        scenario_engine,
        branch_comparator,
        consequence_analyzer,
        optionality_engine,
        alignment_engine,
    ):
        """Set the foresight engines.

        Args:
            scenario_engine: ScenarioProjectionEngine instance
            branch_comparator: StrategicBranchComparator instance
            consequence_analyzer: SecondOrderConsequenceAnalyzer instance
            optionality_engine: OptionalityPreservationEngine instance
            alignment_engine: HorizonAlignmentEngine instance
        """
        self._scenario_engine = scenario_engine
        self._branch_comparator = branch_comparator
        self._consequence_analyzer = consequence_analyzer
        self._optionality_engine = optionality_engine
        self._alignment_engine = alignment_engine

    async def evaluate_decision(
        self,
        packet: DecisionPacket,
    ) -> StrategicForesightResult:
        """Evaluate a decision through full foresight pipeline.

        This is the main entry point for Layer 15 foresight.

        Args:
            packet: Decision packet from Layer 14

        Returns:
            StrategicForesightResult with strategic assessment
        """
        if not self.enabled:
            # Service disabled - return neutral result
            return StrategicForesightResult(
                decision_id=packet.decision_id,
                strategic_score=0.5,
                recommendation="defer",
                recommendation_reason="Foresight service disabled",
                warnings=["Foresight analysis was bypassed"],
            )

        # Guardrail: Only evaluate authorized decisions
        # Layer 15 does NOT override Layer 14 legitimacy
        if not packet.execution_authorized:
            return StrategicForesightResult(
                decision_id=packet.decision_id,
                strategic_score=0.0,
                recommendation="reject",
                recommendation_reason="Decision not authorized by Layer 14",
                warnings=["Cannot evaluate unauthorized decision"],
            )

        # Guardrail: Low-value decisions skip deep foresight
        requires_deep_foresight = (
            packet.estimated_cost > 1000
            or packet.is_governance_change
            or packet.is_budget_change
        )

        if not requires_deep_foresight:
            # Light evaluation for low-impact decisions
            return await self._light_evaluation(packet)

        # Full foresight evaluation
        return await self._full_evaluation(packet)

    async def _light_evaluation(
        self,
        packet: DecisionPacket,
    ) -> StrategicForesightResult:
        """Light evaluation for low-impact decisions.

        Args:
            packet: Decision packet

        Returns:
            StrategicForesightResult with basic assessment
        """
        warnings = []

        # Basic heuristics
        strategic_score = 0.5  # Neutral baseline

        # Check for obvious flags
        if packet.is_governance_change:
            warnings.append("Governance change detected - recommend defer")
            strategic_score -= 0.1

        if packet.is_budget_change:
            warnings.append("Budget change detected - review horizon alignment")
            strategic_score -= 0.05

        # Low cost is generally good for optionality
        if packet.estimated_cost < 100:
            strategic_score += 0.1

        recommendation = self._score_to_recommendation(strategic_score)

        return StrategicForesightResult(
            decision_id=packet.decision_id,
            strategic_score=max(0.0, min(1.0, strategic_score)),
            recommendation=recommendation,
            recommendation_reason=f"Light evaluation: score={strategic_score:.2f}",
            warnings=warnings,
            requires_deep_foresight=False,
        )

    async def _full_evaluation(
        self,
        packet: DecisionPacket,
    ) -> StrategicForesightResult:
        """Full foresight evaluation for high-impact decisions.

        Args:
            packet: Decision packet

        Returns:
            StrategicForesightResult with complete assessment
        """
        warnings = []

        # Step 1: Scenario Projection
        scenarios = []
        if self._scenario_engine:
            scenarios = await self._scenario_engine.project_scenarios(packet)
        else:
            # Generate default scenarios
            scenarios = self._default_scenarios(packet)

        # Step 2: Branch Comparison
        comparison = None
        if self._branch_comparator and len(scenarios) > 1:
            comparison = await self._branch_comparator.compare_branches(
                packet, scenarios
            )

        # Step 3: Second-Order Consequence Analysis
        consequences = None
        if self._consequence_analyzer:
            consequences = await self._consequence_analyzer.analyze_consequences(
                packet
            )

        # Step 4: Optionality Assessment
        optionality = None
        if self._optionality_engine:
            optionality = await self._optionality_engine.assess_optionality(packet)

        # Step 5: Horizon Alignment
        alignment = None
        if self._alignment_engine:
            alignment = await self._alignment_engine.assess_horizon_alignment(packet)

        # Step 6: Calculate Strategic Score
        strategic_score = await self._calculate_strategic_score(
            packet,
            scenarios,
            comparison,
            consequences,
            optionality,
            alignment,
        )

        # Step 7: Generate Recommendation
        recommendation, reason = await self._generate_recommendation(
            packet, strategic_score, consequences, optionality
        )

        # Step 8: Generate Warnings
        warnings.extend(await self._generate_warnings(
            packet, scenarios, consequences, optionality, alignment
        ))

        return StrategicForesightResult(
            decision_id=packet.decision_id,
            scenario_projections=scenarios,
            branch_comparison=comparison,
            consequence_analysis=consequences,
            optionality_assessment=optionality,
            horizon_alignment=alignment,
            strategic_score=strategic_score,
            recommendation=recommendation,
            recommendation_reason=reason,
            warnings=warnings,
            requires_deep_foresight=strategic_score < self.deep_foresight_threshold,
        )

    def _default_scenarios(
        self, packet: DecisionPacket
    ) -> list[ScenarioProjection]:
        """Generate default scenarios when engine is unavailable.

        Args:
            packet: Decision packet

        Returns:
            List of default scenario projections
        """
        return [
            ScenarioProjection(
                scenario_id=f"{packet.decision_id}_baseline",
                decision_id=packet.decision_id,
                horizon=packet.mission_horizon,
                assumptions=["Decision proceeds as planned"],
                projected_outcomes={
                    "efficiency": 0.1,
                    "resilience": 0.0,
                    "cost_overrun": 0.0,
                },
                confidence=0.5,
            ),
            ScenarioProjection(
                scenario_id=f"{packet.decision_id}_pessimistic",
                decision_id=packet.decision_id,
                horizon=packet.mission_horizon,
                assumptions=["Cost overrun", "Delayed benefits"],
                projected_outcomes={
                    "efficiency": -0.1,
                    "resilience": -0.1,
                    "cost_overrun": 0.2,
                },
                confidence=0.3,
            ),
        ]

    async def _calculate_strategic_score(
        self,
        packet: DecisionPacket,
        scenarios: list[ScenarioProjection],
        comparison: BranchComparison | None,
        consequences: ConsequenceAnalysis | None,
        optionality: OptionalityAssessment | None,
        alignment: HorizonAlignmentResult | None,
    ) -> float:
        """Calculate overall strategic score.

        Formula:
        strategic_score = 0.30 * long_term_value
                          + 0.25 * resilience_score
                          + 0.20 * optionality_score
                          + 0.15 * horizon_alignment
                          - 0.10 * lock_in_risk

        Args:
            packet: Decision packet
            scenarios: Projected scenarios
            comparison: Branch comparison
            consequences: Consequence analysis
            optionality: Optionality assessment
            alignment: Horizon alignment

        Returns:
            Strategic score (0.0 to 1.0)
        """
        weights = self.weights

        # Extract component scores
        long_term_value = self._extract_long_term_value(scenarios, comparison)
        resilience_score = self._extract_resilience(consequences)
        optionality_score = optionality.optionality_score if optionality else 0.5
        horizon_alignment_score = self._extract_horizon_alignment(alignment)
        lock_in_risk = optionality.lock_in_risk if optionality else 0.0

        # Calculate weighted score
        score = (
            weights.long_term_value_weight * long_term_value
            + weights.resilience_score_weight * resilience_score
            + weights.optionality_score_weight * optionality_score
            + weights.horizon_alignment_weight * horizon_alignment_score
            - weights.lock_in_risk_penalty * lock_in_risk
        )

        return max(0.0, min(1.0, score))

    def _extract_long_term_value(
        self,
        scenarios: list[ScenarioProjection],
        comparison: BranchComparison | None,
    ) -> float:
        """Extract long-term value from scenarios and comparison."""
        if not scenarios:
            return 0.5

        # Average projected outcomes weighted by confidence
        total_value = 0.0
        total_weight = 0.0

        for scenario in scenarios:
            weight = scenario.confidence
            outcomes = scenario.projected_outcomes
            value = outcomes.get("efficiency", 0.0) + outcomes.get("resilience", 0.0)
            total_value += value * weight
            total_weight += weight

        return (total_value / total_weight) if total_weight > 0 else 0.5

    def _extract_resilience(
        self, consequences: ConsequenceAnalysis | None
    ) -> float:
        """Extract resilience score from consequence analysis."""
        if not consequences:
            return 0.5

        # Net second-order score indicates resilience impact
        # Positive = good for resilience, Negative = harmful
        return (consequences.net_second_order_score + 1.0) / 2.0

    def _extract_horizon_alignment(
        self, alignment: HorizonAlignmentResult | None
    ) -> float:
        """Extract horizon alignment score."""
        if not alignment:
            return 0.5

        # Average across all horizons
        return (
            alignment.short_term_score
            + alignment.medium_term_score
            + alignment.long_term_score
        ) / 3.0

    async def _generate_recommendation(
        self,
        packet: DecisionPacket,
        strategic_score: float,
        consequences: ConsequenceAnalysis | None,
        optionality: OptionalityAssessment | None,
    ) -> tuple[str, str]:
        """Generate strategic recommendation.

        Args:
            packet: Decision packet
            strategic_score: Calculated strategic score
            consequences: Consequence analysis
            optionality: Optionality assessment

        Returns:
            Tuple of (recommendation, reason)
        """
        if strategic_score >= 0.7:
            return "approve", f"High strategic score ({strategic_score:.2f}) indicates good long-term outcome"
        elif strategic_score >= 0.5:
            return "condition", "Moderate strategic score - approve with monitoring"
        elif strategic_score >= 0.3:
            return "defer", "Low strategic score - defer for further analysis"
        else:
            return "reject", f"Low strategic score ({strategic_score:.2f}) indicates poor long-term outcome"

    def _score_to_recommendation(self, score: float) -> str:
        """Convert strategic score to recommendation.

        Args:
            score: Strategic score (0-1)

        Returns:
            Recommendation string
        """
        if score >= 0.7:
            return "approve"
        elif score >= 0.5:
            return "condition"
        elif score >= 0.3:
            return "defer"
        else:
            return "reject"

    async def _generate_warnings(
        self,
        packet: DecisionPacket,
        scenarios: list[ScenarioProjection],
        consequences: ConsequenceAnalysis | None,
        optionality: OptionalityAssessment | None,
        alignment: HorizonAlignmentResult | None,
    ) -> list[str]:
        """Generate strategic warnings.

        Args:
            packet: Decision packet
            scenarios: Projected scenarios
            consequences: Consequence analysis
            optionality: Optionality assessment
            alignment: Horizon alignment

        Returns:
            List of warning messages
        """
        warnings = []

        # Check for low confidence projections
        low_confidence = [s for s in scenarios if s.confidence < 0.4]
        if low_confidence:
            warnings.append(f"{len(low_confidence)} scenarios have low confidence")

        # Check for negative second-order effects
        if consequences and consequences.net_second_order_score < -0.2:
            warnings.append("Significant negative second-order effects detected")

        # Check for high lock-in risk
        if optionality and optionality.lock_in_risk > 0.6:
            warnings.append("High lock-in risk - path dependency likely")

        # Check for horizon misalignment
        if alignment and not alignment.aligned:
            warnings.append("Poor alignment across time horizons")

        # Check for governance changes
        if packet.is_governance_change:
            warnings.append("Governance changes require special review")

        return warnings

    def set_weights(self, weights: StrategicWeights):
        """Set custom strategic weights.

        Args:
            weights: New weight configuration
        """
        self.weights = weights

    def enable(self):
        """Enable the foresight service."""
        self.enabled = True

    def disable(self):
        """Disable the foresight service."""
        self.enabled = False


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def create_strategic_foresight_service(
    weights: StrategicWeights | None = None,
    deep_foresight_threshold: float = 0.8,
) -> StrategicForesightService:
    """Factory function to create a strategic foresight service.

    Args:
        weights: Optional custom weights for strategic scoring
        deep_foresight_threshold: Threshold for requiring deep foresight

    Returns:
        Configured StrategicForesightService instance
    """
    return StrategicForesightService(
        weights=weights,
        deep_foresight_threshold=deep_foresight_threshold,
    )


# =============================================================================
# ALL EXPORTS
# =============================================================================

__all__ = [
    "StrategicForesightService",
    "create_strategic_foresight_service",
]
