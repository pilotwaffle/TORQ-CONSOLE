"""TORQ Layer 15 - Strategic Branch Comparator

This module implements comparison between strategic branches,
evaluating expected value, resilience, and risk across paths.
"""

from typing import Literal

from ..models import (
    BranchComparison,
    DecisionPacket,
    ScenarioProjection,
)


# =============================================================================
# STRATEGIC BRANCH COMPARATOR
# =============================================================================


class StrategicBranchComparator:
    """Engine for comparing strategic branches.

    Compares different strategic paths by:
    - Expected value at each time horizon
    - Risk profile
    - Resilience score
    """

    def __init__(self):
        """Initialize the branch comparator."""
        self.risk_tolerance = 0.5  # 0 = risk-averse, 1 = risk-seeking

    async def compare_branches(
        self,
        packet: DecisionPacket,
        scenarios: list[ScenarioProjection],
    ) -> BranchComparison:
        """Compare strategic branches.

        Args:
            packet: Decision packet
            scenarios: Projected scenarios to compare

        Returns:
            BranchComparison with analysis
        """
        # Extract path IDs from scenarios
        path_ids = [s.scenario_id for s in scenarios]

        # Calculate expected value by horizon
        expected_value = self._calculate_expected_value_by_horizon(scenarios)

        # Calculate risk profile
        risk_profile = self._calculate_risk_profile(scenarios)

        # Calculate resilience score
        resilience_score = self._calculate_resilience_score(scenarios)

        # Determine recommended path
        recommended_path = self._select_recommended_path(
            path_ids, expected_value, risk_profile, resilience_score
        )

        return BranchComparison(
            compared_paths=path_ids,
            decision_id=packet.decision_id,
            expected_value_by_horizon=expected_value,
            risk_profile=risk_profile,
            resilience_score=resilience_score,
            recommended_path=recommended_path,
        )

    def _calculate_expected_value_by_horizon(
        self,
        scenarios: list[ScenarioProjection],
    ) -> dict[str, dict[str, float]]:
        """Calculate expected value for each path at each horizon.

        Args:
            scenarios: Scenarios to evaluate

        Returns:
            Dict mapping path_id to dict of horizon to value
        """
        result = {}

        for scenario in scenarios:
            # Weight outcomes by confidence
            confidence = scenario.confidence
            outcomes = scenario.projected_outcomes

            # Expected value = sum of outcomes weighted by probability
            expected_value = (
                outcomes.get("efficiency", 0.0) * 0.4
                + outcomes.get("resilience", 0.0) * 0.3
                - outcomes.get("cost_overrun", 0.0) * 0.3
            )

            # Organize by horizon
            horizon_multiplier = {
                "short": 0.8,
                "medium": 1.0,
                "long": 1.2,
            }.get(scenario.horizon, 1.0)

            result[scenario.scenario_id] = {
                scenario.horizon: expected_value * horizon_multiplier,
            }

        return result

    def _calculate_risk_profile(
        self,
        scenarios: list[ScenarioProjection],
    ) -> dict[str, float]:
        """Calculate risk profile for each path.

        Args:
            scenarios: Scenarios to evaluate

        Returns:
            Dict mapping path_id to risk score (0=low, 1=high)
        """
        result = {}

        for scenario in scenarios:
            outcomes = scenario.projected_outcomes

            # Risk indicators:
            # - Low confidence
            # - Negative outcomes
            # - Cost overrun
            risk_score = (
                (1.0 - scenario.confidence) * 0.3
                + max(0.0, -outcomes.get("efficiency", 0.0)) * 0.4
                + outcomes.get("cost_overrun", 0.0) * 0.3
            )

            result[scenario.scenario_id] = risk_score

        return result

    def _calculate_resilience_score(
        self,
        scenarios: list[ScenarioProjection],
    ) -> dict[str, float]:
        """Calculate resilience score for each path.

        Args:
            scenarios: Scenarios to evaluate

        Returns:
            Dict mapping path_id to resilience score (0=fragile, 1=resilient)
        """
        result = {}

        for scenario in scenarios:
            outcomes = scenario.projected_outcomes

            # Resilience = positive resilience outcome
            resilience = max(0.0, min(1.0, outcomes.get("resilience", 0.0) + 0.5))

            result[scenario.scenario_id] = resilience

        return result

    def _select_recommended_path(
        self,
        path_ids: list[str],
        expected_value: dict[str, dict[str, float]],
        risk_profile: dict[str, float],
        resilience_score: dict[str, float],
    ) -> str | None:
        """Select the recommended path.

        Args:
            path_ids: Available paths
            expected_value: Expected values
            risk_profile: Risk scores
            resilience_score: Resilience scores

        Returns:
            ID of recommended path, or None if no clear winner
        """
        if not path_ids:
            return None

        # Score each path
        best_path = None
        best_score = -1.0

        for path_id in path_ids:
            # Calculate weighted score
            ev = expected_value.get(path_id, {}).get(path_id.split("_")[-1], 0.0)
            risk = risk_profile.get(path_id, 0.5)
            resilience = resilience_score.get(path_id, 0.5)

            # Risk-adjusted score
            score = (
                ev * 0.5
                + (1.0 - risk) * 0.3
                + resilience * 0.2
            )

            if score > best_score:
                best_score = score
                best_path = path_id

        return best_path

    def set_risk_tolerance(self, tolerance: float):
        """Set risk tolerance for comparisons.

        Args:
            tolerance: Risk tolerance (0=averse, 1=seeking)
        """
        self.risk_tolerance = max(0.0, min(1.0, tolerance))


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def create_strategic_branch_comparator() -> StrategicBranchComparator:
    """Factory function to create a branch comparator.

    Returns:
        Configured StrategicBranchComparator instance
    """
    return StrategicBranchComparator()


# =============================================================================
# ALL EXPORTS
# =============================================================================

__all__ = [
    "StrategicBranchComparator",
    "create_strategic_branch_comparator",
]
