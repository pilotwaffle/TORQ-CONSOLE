"""TORQ Layer 15 - Optionality Preservation Engine

This module implements optionality assessment to prevent
TORQ from becoming brittle while looking efficient.
"""

from ..models import (
    DecisionPacket,
    OptionalityAssessment,
)


# =============================================================================
# OPTIONALITY PRESERVATION ENGINE
# =============================================================================


class OptionalityPreservationEngine:
    """Engine for assessing decision optionality.

    Evaluates how much a decision preserves or limits future options,
    scoring reversibility and lock-in risk.

    High optionality is critical for preventing brittleness.
    """

    def __init__(self):
        """Initialize the optionality preservation engine."""
        self.lock_in_threshold = 0.6  # Threshold for high lock-in warning

    async def assess_optionality(
        self,
        packet: DecisionPacket,
    ) -> OptionalityAssessment:
        """Assess optionality of a decision.

        Args:
            packet: Decision packet to assess

        Returns:
            OptionalityAssessment with full assessment
        """
        # Calculate optionality score
        optionality_score = self._calculate_optionality_score(packet)

        # Calculate lock-in risk
        lock_in_risk = self._calculate_lock_in_risk(packet)

        # Determine reversibility
        reversible = self._is_reversible(packet)

        # Generate mitigation options
        mitigation_options = self._generate_mitigations(packet, lock_in_risk)

        # Calculate path narrowing score
        path_narrowing = self._calculate_path_narrowing(packet)

        return OptionalityAssessment(
            decision_id=packet.decision_id,
            optionality_score=optionality_score,
            lock_in_risk=lock_in_risk,
            reversible=reversible,
            mitigation_options=mitigation_options,
            path_narrowing_score=path_narrowing,
        )

    def _calculate_optionality_score(
        self,
        packet: DecisionPacket,
    ) -> float:
        """Calculate optionality score.

        Higher score = more options preserved.

        Args:
            packet: Decision packet

        Returns:
            Optionality score (0.0 to 1.0)
        """
        score = 0.5  # Baseline

        # Low cost = high optionality (easy to change)
        if packet.estimated_cost < 100:
            score += 0.3
        elif packet.estimated_cost < 500:
            score += 0.1
        elif packet.estimated_cost > 1000:
            score -= 0.2

        # Short horizon = high optionality (less commitment)
        if packet.mission_horizon == "short":
            score += 0.2
        elif packet.mission_horizon == "long":
            score -= 0.2

        # Governance changes reduce optionality
        if packet.is_governance_change:
            score -= 0.3

        # Budget changes may reduce optionality
        if packet.is_budget_change:
            score -= 0.1

        return max(0.0, min(1.0, score))

    def _calculate_lock_in_risk(
        self,
        packet: DecisionPacket,
    ) -> float:
        """Calculate lock-in risk score.

        Higher score = higher risk of path dependency.

        Args:
            packet: Decision packet

        Returns:
            Lock-in risk score (0.0 to 1.0)
        """
        risk = 0.0

        # High cost = higher lock-in
        if packet.estimated_cost > 1000:
            risk += 0.3
        elif packet.estimated_cost > 500:
            risk += 0.15

        # Long horizon = higher lock-in
        if packet.mission_horizon == "long":
            risk += 0.2

        # Governance changes = high lock-in
        if packet.is_governance_change:
            risk += 0.4

        # Budget changes = moderate lock-in
        if packet.is_budget_change:
            risk += 0.2

        # Infrastructure/investment actions = higher lock-in
        action_type = packet.action_type.lower()
        if any(keyword in action_type for keyword in ["build", "deploy", "implement"]):
            risk += 0.15

        return min(1.0, risk)

    def _is_reversible(
        self,
        packet: DecisionPacket,
    ) -> bool:
        """Check if a decision is reversible.

        Args:
            packet: Decision packet

        Returns:
            True if reversible, False otherwise
        """
        # High-cost decisions are less reversible
        if packet.estimated_cost > 1000:
            return False

        # Governance changes are hard to reverse
        if packet.is_governance_change:
            return False

        # Low-cost, short-horizon decisions are reversible
        if packet.estimated_cost < 100 and packet.mission_horizon == "short":
            return True

        # Default: assume reversible with effort
        return True

    def _generate_mitigations(
        self,
        packet: DecisionPacket,
        lock_in_risk: float,
    ) -> list[str]:
        """Generate mitigation options for lock-in risk.

        Args:
            packet: Decision packet
            lock_in_risk: Calculated lock-in risk

        Returns:
            List of mitigation strategies
        """
        mitigations = []

        if lock_in_risk > 0.5:
            mitigations.append("Phase implementation to validate early")
            mitigations.append("Build exit ramps into the decision")

        if lock_in_risk > 0.7:
            mitigations.append("Set review checkpoint before full commitment")
            mitigations.append("Maintain parallel alternative during transition")

        if packet.estimated_cost > 500:
            mitigations.append("Prototype before full implementation")

        if packet.is_governance_change:
            mitigations.append("Sunset clause for new governance rules")
            mitigations.append("Require supermajority for reversal")

        return mitigations

    def _calculate_path_narrowing(
        self,
        packet: DecisionPacket,
    ) -> float:
        """Calculate how much this decision narrows future paths.

        Args:
            packet: Decision packet

        Returns:
            Path narrowing score (0.0 to 1.0)
        """
        narrowing = 0.0

        # High-cost decisions narrow paths
        if packet.estimated_cost > 1000:
            narrowing += 0.3

        # Governance changes significantly narrow paths
        if packet.is_governance_change:
            narrowing += 0.4

        # Long horizon narrows immediate options
        if packet.mission_horizon == "long":
            narrowing += 0.2

        return min(1.0, narrowing)

    def set_lock_in_threshold(self, threshold: float):
        """Set the threshold for high lock-in warning.

        Args:
            threshold: New threshold (0.0 to 1.0)
        """
        self.lock_in_threshold = max(0.0, min(1.0, threshold))


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def create_optionality_preservation_engine() -> OptionalityPreservationEngine:
    """Factory function to create an optionality preservation engine.

    Returns:
        Configured OptionalityPreservationEngine instance
    """
    return OptionalityPreservationEngine()


# =============================================================================
# ALL EXPORTS
# =============================================================================

__all__ = [
    "OptionalityPreservationEngine",
    "create_optionality_preservation_engine",
]
