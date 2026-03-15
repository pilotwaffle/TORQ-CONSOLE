"""TORQ Layer 15 - Second Order Consequence Analyzer

This module implements analysis of second-order consequences,
evaluating downstream effects beyond immediate outcomes.
"""

from ..models import (
    ConsequenceAnalysis,
    DecisionPacket,
)


# =============================================================================
# SECOND ORDER CONSEQUENCE ANALYZER
# =============================================================================


class SecondOrderConsequenceAnalyzer:
    """Engine for analyzing second-order consequences.

    Evaluates downstream effects such as:
    - Local efficiency gain vs future resilience loss
    - Centralization gain vs fragility increase
    - Budget savings vs innovation drag
    - Throughput gain vs drift accumulation
    """

    # Consequence patterns and their effects
    CONSEQUENCE_PATTERNS = {
        "efficiency_optimization": {
            "direct_effects": {"efficiency": 0.3, "cost_savings": 0.2},
            "second_order_effects": {"resilience": -0.1, "flexibility": -0.15},
            "systemic_risks": {"fragility": 0.2},
        },
        "centralization": {
            "direct_effects": {"control": 0.3, "coordination": 0.2},
            "second_order_effects": {"innovation": -0.15, "local_adaptation": -0.1},
            "systemic_risks": {"single_point_failure": 0.3},
        },
        "standardization": {
            "direct_effects": {"interoperability": 0.3, "efficiency": 0.2},
            "second_order_effects": {"customization": -0.1, "innovation": -0.05},
            "systemic_risks": {"lock_in": 0.1},
        },
        "resource_investment": {
            "direct_effects": {"capacity": 0.3, "capability": 0.2},
            "second_order_effects": {"opportunity_cost": -0.1},
            "delayed_benefits": {"scale_benefits": 0.3},
        },
        "automation": {
            "direct_effects": {"efficiency": 0.4, "consistency": 0.2},
            "second_order_effects": {"skill_atrophy": -0.1, "maintenance_dependency": 0.2},
            "delayed_benefits": {"productivity": 0.3},
        },
    }

    def __init__(self):
        """Initialize the consequence analyzer."""
        self.patterns = self.CONSEQUENCE_PATTERNS.copy()

    async def analyze_consequences(
        self,
        packet: DecisionPacket,
    ) -> ConsequenceAnalysis:
        """Analyze second-order consequences of a decision.

        Args:
            packet: Decision packet to analyze

        Returns:
            ConsequenceAnalysis with full assessment
        """
        # Identify which consequence patterns apply
        applicable_patterns = self._identify_patterns(packet)

        # Aggregate effects
        direct_effects = {}
        second_order_effects = {}
        systemic_risks = {}
        delayed_benefits = {}

        for pattern in applicable_patterns:
            pattern_data = self.patterns[pattern]

            # Aggregate direct effects
            for key, value in pattern_data["direct_effects"].items():
                direct_effects[key] = direct_effects.get(key, 0.0) + value

            # Aggregate second-order effects
            for key, value in pattern_data["second_order_effects"].items():
                second_order_effects[key] = second_order_effects.get(key, 0.0) + value

            # Aggregate systemic risks
            for key, value in pattern_data["systemic_risks"].items():
                systemic_risks[key] = systemic_risks.get(key, 0.0) + value

            # Aggregate delayed benefits
            if "delayed_benefits" in pattern_data:
                for key, value in pattern_data["delayed_benefits"].items():
                    delayed_benefits[key] = delayed_benefits.get(key, 0.0) + value

        # Calculate net second-order score
        net_second_order = self._calculate_net_score(
            direct_effects, second_order_effects, systemic_risks
        )

        return ConsequenceAnalysis(
            decision_id=packet.decision_id,
            direct_effects=direct_effects,
            second_order_effects=second_order_effects,
            systemic_risks=systemic_risks,
            delayed_benefits=delayed_benefits,
            net_second_order_score=net_second_order,
        )

    def _identify_patterns(
        self,
        packet: DecisionPacket,
    ) -> list[str]:
        """Identify which consequence patterns apply to a decision.

        Args:
            packet: Decision packet

        Returns:
            List of applicable pattern names
        """
        patterns = []

        # Pattern detection based on action type
        action_type = packet.action_type.lower()

        if "optimize" in action_type or "efficiency" in action_type:
            patterns.append("efficiency_optimization")

        if "centralize" in action_type or "consolidate" in action_type:
            patterns.append("centralization")

        if "standard" in action_type or "unify" in action_type:
            patterns.append("standardization")

        if "invest" in action_type or "build" in action_type or "expand" in action_type:
            patterns.append("resource_investment")

        if "automate" in action_type or "automate" in action_type:
            patterns.append("automation")

        # High-cost decisions likely involve resource investment
        if packet.estimated_cost > 500:
            if "resource_investment" not in patterns:
                patterns.append("resource_investment")

        return patterns

    def _calculate_net_score(
        self,
        direct_effects: dict,
        second_order_effects: dict,
        systemic_risks: dict,
    ) -> float:
        """Calculate net second-order score.

        Args:
            direct_effects: Direct effects
            second_order_effects: Second-order effects
            systemic_risks: Systemic risks

        Returns:
            Net score (-1.0 to 1.0)
        """
        # Sum direct effects (weighted positively)
        direct_sum = sum(direct_effects.values()) * 0.3

        # Sum second-order effects (can be negative)
        second_order_sum = sum(second_order_effects.values()) * 0.5

        # Subtract systemic risks (always negative)
        risk_sum = sum(systemic_risks.values()) * -0.2

        net_score = direct_sum + second_order_sum + risk_sum

        return max(-1.0, min(1.0, net_score))

    def add_pattern(
        self,
        name: str,
        direct_effects: dict,
        second_order_effects: dict,
        systemic_risks: dict,
    ):
        """Add a custom consequence pattern.

        Args:
            name: Pattern name
            direct_effects: Direct effects mapping
            second_order_effects: Second-order effects mapping
            systemic_risks: Systemic risks mapping
        """
        self.patterns[name] = {
            "direct_effects": direct_effects,
            "second_order_effects": second_order_effects,
            "systemic_risks": systemic_risks,
        }


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def create_second_order_consequence_analyzer() -> SecondOrderConsequenceAnalyzer:
    """Factory function to create a consequence analyzer.

    Returns:
        Configured SecondOrderConsequenceAnalyzer instance
    """
    return SecondOrderConsequenceAnalyzer()


# =============================================================================
# ALL EXPORTS
# =============================================================================

__all__ = [
    "SecondOrderConsequenceAnalyzer",
    "create_second_order_consequence_analyzer",
]
