"""TORQ Layer 14 - Legitimacy Scoring Engine

This module implements legitimacy scoring for governance decisions,
combining multiple factors into a single legitimacy score.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .models import (
    GovernanceDecisionPacket,
    GovernanceResult,
    GovernanceViolation,
)

if TYPE_CHECKING:
    from .constitutional_framework_engine import ConstitutionalFrameworkEngine
    from .authority_boundary_enforcer import AuthorityBoundaryEnforcer


# =============================================================================
# LEGITIMACY SCORE COMPONENTS
# =============================================================================


@dataclass
class LegitimacyWeights:
    """Weights for legitimacy score components.

    Defines how much each factor contributes to the overall
    legitimacy score.
    """

    rule_compliance_weight: float = 0.4
    authority_validity_weight: float = 0.3
    plurality_integrity_weight: float = 0.2
    transparency_weight: float = 0.1

    def __post_init__(self):
        """Ensure weights sum to 1.0."""
        total = (
            self.rule_compliance_weight
            + self.authority_validity_weight
            + self.plurality_integrity_weight
            + self.transparency_weight
        )
        if total != 1.0:
            # Normalize weights
            self.rule_compliance_weight /= total
            self.authority_validity_weight /= total
            self.plurality_integrity_weight /= total
            self.transparency_weight /= total


@dataclass
class LegitimacyScore:
    """Legitimacy score for a governance decision.

    Represents the overall legitimacy assessment for a decision,
    including component scores and any warnings or violations.
    """

    decision_id: str
    score: float  # 0.0 to 1.0
    threshold: float = 0.7  # Minimum score for execution

    # Component scores
    rule_compliance_score: float = 1.0
    authority_validity_score: float = 1.0
    plurality_integrity_score: float = 1.0
    transparency_score: float = 1.0

    # Issues
    warnings: list[str] = field(default_factory=list)
    violations: list[GovernanceViolation] = field(default_factory=list)

    @property
    def is_legitimate(self) -> bool:
        """Check if score meets legitimacy threshold."""
        return self.score >= self.threshold

    @property
    def has_critical_violations(self) -> bool:
        """Check if there are any critical violations."""
        return any(v.severity == "critical" for v in self.violations)


# =============================================================================
# LEGITIMACY SCORING ENGINE
# =============================================================================


class LegitimacyScoringEngine:
    """Engine for computing legitimacy scores of governance decisions.

    The legitimacy score combines multiple factors:
    - Constitutional rule compliance
    - Authority validity
    - Plurality integrity
    - Transparency

    A decision must meet the legitimacy threshold to execute.
    """

    def __init__(
        self,
        weights: LegitimacyWeights | None = None,
        threshold: float = 0.7,
    ):
        """Initialize the legitimacy scoring engine.

        Args:
            weights: Optional custom weights for scoring
            threshold: Minimum legitimacy score for execution
        """
        self.weights = weights or LegitimacyWeights()
        self.threshold = threshold

    async def compute_legitimacy(
        self,
        decision: GovernanceDecisionPacket,
        constitution_compliant: bool,
        authority_compliant: bool,
        violations: list[GovernanceViolation],
    ) -> LegitimacyScore:
        """Compute legitimacy score for a decision.

        Args:
            decision: Decision packet to score
            constitution_compliant: Whether decision is constitutionally compliant
            authority_compliant: Whether decision respects authority boundaries
            violations: List of any violations

        Returns:
            LegitimacyScore with overall score and components
        """
        # Calculate component scores
        rule_compliance = self._score_rule_compliance(
            constitution_compliant,
            violations,
        )

        authority_validity = self._score_authority_validity(
            authority_compliant,
            decision,
        )

        plurality_integrity = self._score_plurality_integrity(decision)

        transparency = self._score_transparency(decision)

        # Calculate weighted score
        score = (
            rule_compliance * self.weights.rule_compliance_weight
            + authority_validity * self.weights.authority_validity_weight
            + plurality_integrity * self.weights.plurality_integrity_weight
            + transparency * self.weights.transparency_weight
        )

        # Build warnings list
        warnings = self._generate_warnings(
            decision,
            rule_compliance,
            authority_validity,
            plurality_integrity,
            transparency,
        )

        return LegitimacyScore(
            decision_id=decision.decision_id,
            score=score,
            threshold=self.threshold,
            rule_compliance_score=rule_compliance,
            authority_validity_score=authority_validity,
            plurality_integrity_score=plurality_integrity,
            transparency_score=transparency,
            warnings=warnings,
            violations=violations,
        )

    def _score_rule_compliance(
        self,
        constitution_compliant: bool,
        violations: list[GovernanceViolation],
    ) -> float:
        """Score constitutional rule compliance.

        Args:
            constitution_compliant: Whether decision is compliant
            violations: List of violations

        Returns:
            Score from 0.0 to 1.0
        """
        if not constitution_compliant:
            # Check for critical violations
            critical = [v for v in violations if v.severity == "critical"]
            if critical:
                return 0.0
            return 0.3

        # Minor violations reduce score slightly
        if violations:
            non_critical = len([v for v in violations if v.severity != "critical"])
            return max(0.5, 1.0 - (non_critical * 0.1))

        return 1.0

    def _score_authority_validity(
        self,
        authority_compliant: bool,
        decision: GovernanceDecisionPacket,
    ) -> float:
        """Score authority validity.

        Args:
            authority_compliant: Whether authority boundaries are respected
            decision: Decision packet

        Returns:
            Score from 0.0 to 1.0
        """
        if not authority_compliant:
            return 0.0

        # Check for self-approval (reduces legitimacy)
        if decision.approving_agent_id:
            if decision.proposing_agent_id == decision.approving_agent_id:
                return 0.2

        # Check approval chain depth
        if len(decision.approval_chain) == 0 and decision.estimated_cost > 100:
            return 0.7  # Large decisions without approval have reduced legitimacy

        return 1.0

    def _score_plurality_integrity(
        self,
        decision: GovernanceDecisionPacket,
    ) -> float:
        """Score plurality integrity.

        Args:
            decision: Decision packet

        Returns:
            Score from 0.0 to 1.0
        """
        # High-value decisions require plural approval
        if decision.estimated_cost > 1000:
            if len(decision.approval_chain) >= 2:
                return 1.0
            return 0.5

        # Governance changes require plural approval
        if decision.is_governance_change:
            if len(decision.approval_chain) >= 2:
                return 1.0
            return 0.3

        # Standard decisions
        if len(decision.approval_chain) >= 2:
            return 1.0  # Plural approval is good
        elif len(decision.approval_chain) == 1:
            return 0.9  # Single approval is acceptable
        else:
            return 0.8  # No approval is slightly suspicious

    def _score_transparency(
        self,
        decision: GovernanceDecisionPacket,
    ) -> float:
        """Score decision transparency.

        Args:
            decision: Decision packet

        Returns:
            Score from 0.0 to 1.0
        """
        score = 1.0

        # Has description
        if not decision.action_description:
            score -= 0.3

        # Has governance context
        if not decision.governance_context:
            score -= 0.1

        # Budget transparency
        if decision.estimated_cost <= 0:
            score -= 0.2

        # Resource transparency
        if not decision.target_resources and decision.estimated_cost > 100:
            score -= 0.1

        return max(0.0, score)

    def _generate_warnings(
        self,
        decision: GovernanceDecisionPacket,
        rule_compliance: float,
        authority_validity: float,
        plurality_integrity: float,
        transparency: float,
    ) -> list[str]:
        """Generate warning messages based on component scores.

        Args:
            decision: Decision packet
            rule_compliance: Rule compliance score
            authority_validity: Authority validity score
            plurality_integrity: Plurality integrity score
            transparency: Transparency score

        Returns:
            List of warning messages
        """
        warnings = []

        if rule_compliance < 0.5:
            warnings.append("Low rule compliance score")

        if authority_validity < 0.5:
            warnings.append("Authority validity concerns detected")

        if plurality_integrity < 0.6:
            warnings.append("Limited plurality in approval chain")

        if transparency < 0.7:
            warnings.append("Insufficient decision transparency")

        # Specific warnings for high-impact decisions
        if decision.estimated_cost > 1000:
            if len(decision.approval_chain) < 2:
                warnings.append("High-value decision lacks plural approval")

        if decision.is_governance_change:
            if not decision.requires_human_approval:
                warnings.append("Governance change not flagged for human review")

        return warnings

    async def create_governance_result(
        self,
        decision: GovernanceDecisionPacket,
        constitution_compliant: bool,
        authority_compliant: bool,
        plurality_compliant: bool,
        violations: list[GovernanceViolation],
        authority_risk_score: float = 0.0,
    ) -> GovernanceResult:
        """Create a complete governance result.

        Args:
            decision: Decision packet
            constitution_compliant: Constitutional compliance status
            authority_compliant: Authority compliance status
            plurality_compliant: Plurality compliance status
            violations: List of violations
            authority_risk_score: Authority capture risk score

        Returns:
            Complete GovernanceResult
        """
        legitimacy = await self.compute_legitimacy(
            decision,
            constitution_compliant,
            authority_compliant,
            violations,
        )

        # Separate violations by blocking status
        blocking_violations = [v for v in violations if v.severity in ("critical", "high")]
        warning_violations = [v for v in violations if v.severity in ("low", "medium")]

        # Execution is authorized only if legitimate and no critical violations
        execution_authorized = (
            legitimacy.is_legitimate
            and not legitimacy.has_critical_violations
        )

        return GovernanceResult(
            decision_id=decision.decision_id,
            legitimacy_score=legitimacy.score,
            legitimacy_threshold=self.threshold,
            execution_authorized=execution_authorized,
            blocking_violations=blocking_violations,
            warning_violations=warning_violations,
            constitutional_compliant=constitution_compliant,
            authority_compliant=authority_compliant,
            plurality_compliant=plurality_compliant,
            authority_risk_score=authority_risk_score,
            transparency_score=legitimacy.transparency_score,
            evaluation_details={
                "legitimacy_components": {
                    "rule_compliance": legitimacy.rule_compliance_score,
                    "authority_validity": legitimacy.authority_validity_score,
                    "plurality_integrity": legitimacy.plurality_integrity_score,
                    "transparency": legitimacy.transparency_score,
                },
                "warnings": legitimacy.warnings,
            },
        )

    def set_threshold(self, threshold: float):
        """Set the legitimacy threshold for execution.

        Args:
            threshold: New threshold (0.0 to 1.0)
        """
        if 0.0 <= threshold <= 1.0:
            self.threshold = threshold

    def set_weights(self, weights: LegitimacyWeights):
        """Set custom weights for legitimacy scoring.

        Args:
            weights: New weight configuration
        """
        self.weights = weights


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def create_legitimacy_scoring_engine(
    weights: LegitimacyWeights | None = None,
    threshold: float = 0.7,
) -> LegitimacyScoringEngine:
    """Factory function to create a legitimacy scoring engine.

    Args:
        weights: Optional custom weights
        threshold: Legitimacy threshold for execution

    Returns:
        Configured LegitimacyScoringEngine instance
    """
    return LegitimacyScoringEngine(weights=weights, threshold=threshold)


# =============================================================================
# ALL EXPORTS
# =============================================================================

__all__ = [
    "LegitimacyScoringEngine",
    "LegitimacyScore",
    "LegitimacyWeights",
    "create_legitimacy_scoring_engine",
]
