"""TORQ Layer 15 - Horizon Alignment Engine

This module implements horizon alignment assessment,
scoring decisions across short, medium, and long-term horizons.
"""

from ..models import (
    DecisionPacket,
    HorizonAlignmentResult,
)


# =============================================================================
# HORIZON ALIGNMENT ENGINE
# =============================================================================


class HorizonAlignmentEngine:
    """Engine for assessing alignment across time horizons.

    Scores whether a decision helps or harms:
    - Short-term operations (0-3 months)
    - Medium-term roadmap (3-12 months)
    - Long-term mission coherence (12+ months)
    """

    def __init__(self):
        """Initialize the horizon alignment engine."""
        self.alignment_threshold = 0.6  # Minimum score for "aligned"

    async def assess_horizon_alignment(
        self,
        packet: DecisionPacket,
    ) -> HorizonAlignmentResult:
        """Assess horizon alignment for a decision.

        Args:
            packet: Decision packet to assess

        Returns:
            HorizonAlignmentResult with full assessment
        """
        # Calculate scores for each horizon
        short_term = self._score_short_term(packet)
        medium_term = self._score_medium_term(packet)
        long_term = self._score_long_term(packet)

        # Calculate alignment delta (variance)
        scores = [short_term, medium_term, long_term]
        avg_score = sum(scores) / len(scores)
        alignment_delta = max(abs(s - avg_score) for s in scores)

        # Determine if aligned
        aligned = (
            short_term >= self.alignment_threshold * 0.8
            and medium_term >= self.alignment_threshold
            and long_term >= self.alignment_threshold
        ) or all(s >= 0.5 for s in scores)

        return HorizonAlignmentResult(
            decision_id=packet.decision_id,
            short_term_score=short_term,
            medium_term_score=medium_term,
            long_term_score=long_term,
            alignment_delta=alignment_delta,
            aligned=aligned,
        )

    def _score_short_term(
        self,
        packet: DecisionPacket,
    ) -> float:
        """Score short-term (0-3 month) alignment.

        Args:
            packet: Decision packet

        Returns:
            Short-term alignment score (0.0 to 1.0)
        """
        score = 0.5  # Baseline

        # High economic priority = good for short-term
        score += packet.economic_priority_score * 0.3

        # Low cost = good for short-term execution
        if packet.estimated_cost < 200:
            score += 0.2
        elif packet.estimated_cost < 500:
            score += 0.1

        # Short horizon missions align better with short-term
        if packet.mission_horizon == "short":
            score += 0.2

        # Routine actions good for short-term operations
        if packet.action_type in ["standard", "routine", "maintenance"]:
            score += 0.1

        return min(1.0, score)

    def _score_medium_term(
        self,
        packet: DecisionPacket,
    ) -> float:
        """Score medium-term (3-12 month) alignment.

        Args:
            packet: Decision packet

        Returns:
            Medium-term alignment score (0.0 to 1.0)
        """
        score = 0.5  # Baseline

        # Strategic fit matters for medium-term
        # (Assuming user_value from L13 maps through)
        score += packet.economic_priority_score * 0.2

        # Medium horizon missions align better
        if packet.mission_horizon == "medium":
            score += 0.2

        # Investment actions good for medium-term
        if any(keyword in packet.action_type.lower() for keyword in ["invest", "build", "develop"]):
            score += 0.15

        # Governance changes need medium-term alignment
        if packet.is_governance_change:
            # Check if there's approval chain (indicating planning)
            if len(getattr(packet, "approval_chain", [])) > 0:
                score += 0.1
            else:
                score -= 0.2  # Unplanned governance change is risky

        return max(0.0, min(1.0, score))

    def _score_long_term(
        self,
        packet: DecisionPacket,
    ) -> float:
        """Score long-term (12+ month) alignment.

        Args:
            packet: Decision packet

        Returns:
            Long-term alignment score (0.0 to 1.0)
        """
        score = 0.5  # Baseline

        # Long horizon missions naturally align
        if packet.mission_horizon == "long":
            score += 0.3

        # Investment in infrastructure/capability is good for long-term
        if any(keyword in packet.action_type.lower() for keyword in ["infrastructure", "capability", "platform", "foundation"]):
            score += 0.25

        # Governance changes affect long-term
        if packet.is_governance_change:
            # Planned changes are good for long-term
            if len(getattr(packet, "approval_chain", [])) > 1:
                score += 0.2
            else:
                score -= 0.3  # Ad-hoc changes are risky for long-term

        # Budget changes affect long-term sustainability
        if packet.is_budget_change:
            if packet.estimated_cost < 0:  # Budget cut
                score -= 0.2  # May harm long-term capability
            else:  # Budget increase
                score += 0.1  # May enable long-term growth

        # High lock-in reduces long-term alignment
        # (We can't access optionality assessment here without circular dependency,
        # so use basic heuristics)
        if packet.estimated_cost > 1000:
            score -= 0.1

        return max(0.0, min(1.0, score))

    def set_alignment_threshold(self, threshold: float):
        """Set the threshold for considering a decision aligned.

        Args:
            threshold: New threshold (0.0 to 1.0)
        """
        self.alignment_threshold = max(0.0, min(1.0, threshold))


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def create_horizon_alignment_engine() -> HorizonAlignmentEngine:
    """Factory function to create a horizon alignment engine.

    Returns:
        Configured HorizonAlignmentEngine instance
    """
    return HorizonAlignmentEngine()


# =============================================================================
# ALL EXPORTS
# =============================================================================

__all__ = [
    "HorizonAlignmentEngine",
    "create_horizon_alignment_engine",
]
