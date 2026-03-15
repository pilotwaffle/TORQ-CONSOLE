"""TORQ Layer 15 - Scenario Projection Engine

This module implements scenario projection for strategic foresight,
generating plausible future scenarios based on decision parameters.
"""

from typing import Literal

from ..models import (
    DecisionPacket,
    ScenarioProjection,
)


# =============================================================================
# SCENARIO PROJECTION ENGINE
# =============================================================================


class ScenarioProjectionEngine:
    """Engine for projecting future scenarios.

    This engine generates 2-5 plausible future scenarios resulting
    from a decision, using deterministic rules and heuristics.

    Initial implementation is rules-based, not LLM-heavy.
    """

    # Default scenario templates
    DEFAULT_SCENARIOS = {
        "baseline": {
            "description": "Decision proceeds as planned",
            "assumptions": ["No major disruptions", "Cost estimates hold"],
            "outcome_modifier": 0.0,
        },
        "optimistic": {
            "description": "Better than expected outcomes",
            "assumptions": ["Efficiency gains realized", "Cost savings achieved"],
            "outcome_modifier": 0.2,
        },
        "pessimistic": {
            "description": "Worse than expected outcomes",
            "assumptions": ["Cost overruns", "Delayed benefits", "Implementation issues"],
            "outcome_modifier": -0.2,
        },
        "disruptive": {
            "description": "Significant changes to environment",
            "assumptions": ["Technology shift", "Market change", "Regulatory change"],
            "outcome_modifier": -0.1,
        },
        "breakthrough": {
            "description": "Unexpected positive development",
            "assumptions": ["Innovation unlocked", "Network effects realized"],
            "outcome_modifier": 0.3,
        },
    }

    def __init__(self):
        """Initialize the scenario projection engine."""
        self.scenario_templates = self.DEFAULT_SCENARIOS.copy()

    async def project_scenarios(
        self,
        packet: DecisionPacket,
        count: int = 3,
    ) -> list[ScenarioProjection]:
        """Project future scenarios for a decision.

        Args:
            packet: Decision packet to project
            count: Number of scenarios to generate (2-5)

        Returns:
            List of ScenarioProjection objects
        """
        count = max(2, min(5, count))

        scenarios = []

        # Always include baseline scenario
        scenarios.append(self._create_scenario(packet, "baseline"))

        # Add optimistic if count > 1
        if count > 1:
            scenarios.append(self._create_scenario(packet, "optimistic"))

        # Add pessimistic if count > 2
        if count > 2:
            scenarios.append(self._create_scenario(packet, "pessimistic"))

        # Add disruptive if count > 3 and high-impact decision
        if count > 3 and packet.estimated_cost > 500:
            scenarios.append(self._create_scenario(packet, "disruptive"))

        # Add breakthrough if count > 4 and high-value decision
        if count > 4 and packet.economic_priority_score > 0.7:
            scenarios.append(self._create_scenario(packet, "breakthrough"))

        return scenarios

    def _create_scenario(
        self,
        packet: DecisionPacket,
        scenario_type: str,
    ) -> ScenarioProjection:
        """Create a single scenario projection.

        Args:
            packet: Decision packet
            scenario_type: Type of scenario to create

        Returns:
            ScenarioProjection object
        """
        template = self.scenario_templates.get(scenario_type, self.scenario_templates["baseline"])

        # Determine horizon
        horizon = packet.mission_horizon

        # Calculate projected outcomes based on scenario type
        projected_outcomes = self._calculate_outcomes(
            packet, scenario_type, template["outcome_modifier"]
        )

        # Calculate confidence
        confidence = self._calculate_confidence(packet, scenario_type)

        return ScenarioProjection(
            scenario_id=f"{packet.decision_id}_{scenario_type}",
            decision_id=packet.decision_id,
            horizon=horizon,
            assumptions=template["assumptions"].copy(),
            projected_outcomes=projected_outcomes,
            confidence=confidence,
            notes=[template["description"]],
        )

    def _calculate_outcomes(
        self,
        packet: DecisionPacket,
        scenario_type: str,
        modifier: float,
    ) -> dict[str, float]:
        """Calculate projected outcomes for a scenario.

        Args:
            packet: Decision packet
            scenario_type: Type of scenario
            modifier: Outcome modifier

        Returns:
            Dictionary of projected outcomes
        """
        # Base outcomes from economic score
        base_efficiency = packet.economic_priority_score * 0.5
        base_resilience = 0.3

        # Apply scenario modifier
        efficiency = max(-1.0, min(1.0, base_efficiency + modifier))
        resilience = max(-1.0, min(1.0, base_resilience + modifier * 0.5))

        # Additional outcomes
        cost_overrun = max(0.0, -modifier * 0.3) if scenario_type == "pessimistic" else 0.0

        return {
            "efficiency": efficiency,
            "resilience": resilience,
            "cost_overrun": cost_overrun,
        }

    def _calculate_confidence(
        self,
        packet: DecisionPacket,
        scenario_type: str,
    ) -> float:
        """Calculate confidence in a scenario.

        Args:
            packet: Decision packet
            scenario_type: Type of scenario

        Returns:
            Confidence score (0.0 to 1.0)
        """
        # Base confidence by scenario type
        base_confidence = {
            "baseline": 0.6,
            "optimistic": 0.3,
            "pessimistic": 0.4,
            "disruptive": 0.2,
            "breakthrough": 0.2,
        }.get(scenario_type, 0.5)

        # Adjust based on decision characteristics
        if packet.estimated_cost < 100:
            base_confidence += 0.1  # Low cost = more predictable

        if packet.action_type in ["standard", "routine"]:
            base_confidence += 0.1  # Routine actions = more predictable

        if packet.is_governance_change:
            base_confidence -= 0.2  # Governance changes = less predictable

        return max(0.0, min(1.0, base_confidence))

    def add_scenario_template(
        self,
        name: str,
        description: str,
        assumptions: list[str],
        outcome_modifier: float,
    ):
        """Add a custom scenario template.

        Args:
            name: Scenario name
            description: Description of the scenario
            assumptions: Key assumptions
            outcome_modifier: Effect on outcomes
        """
        self.scenario_templates[name] = {
            "description": description,
            "assumptions": assumptions,
            "outcome_modifier": outcome_modifier,
        }


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def create_scenario_projection_engine() -> ScenarioProjectionEngine:
    """Factory function to create a scenario projection engine.

    Returns:
        Configured ScenarioProjectionEngine instance
    """
    return ScenarioProjectionEngine()


# =============================================================================
# ALL EXPORTS
# =============================================================================

__all__ = [
    "ScenarioProjectionEngine",
    "create_scenario_projection_engine",
]
