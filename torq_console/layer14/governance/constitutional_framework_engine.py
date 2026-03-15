"""TORQ Layer 14 - Constitutional Framework Engine

This module implements the constitutional rule evaluation engine,
which defines and enforces the TORQ system constitution.
"""

from typing import TYPE_CHECKING

from .models import (
    GovernanceDecisionPacket,
    GovernanceResult,
    GovernanceViolation,
    RuleType,
    SystemConstitution,
)

if TYPE_CHECKING:
    from .authority_boundary_enforcer import AuthorityBoundaryEnforcer


# =============================================================================
# CONSTITUTIONAL RULE DEFINITIONS
# =============================================================================


class ConstitutionalRule:
    """A single constitutional rule.

    Defines a rule that all system decisions must comply with.
    Rules are evaluated by the ConstitutionalFrameworkEngine.
    """

    def __init__(
        self,
        rule_id: str,
        rule_type: RuleType,
        description: str,
        check_function: callable,
        severity: str = "medium",
    ):
        """Initialize a constitutional rule.

        Args:
            rule_id: Unique rule identifier
            rule_type: Category of rule
            description: Human-readable description
            check_function: Function that evaluates if decision complies
            severity: Severity level for violations
        """
        self.rule_id = rule_id
        self.rule_type = rule_type
        self.description = description
        self.check_function = check_function
        self.severity = severity

    def evaluate(self, decision: GovernanceDecisionPacket) -> GovernanceViolation | None:
        """Evaluate if decision complies with this rule.

        Args:
            decision: Decision packet to evaluate

        Returns:
            GovernanceViolation if rule violated, None if compliant
        """
        result = self.check_function(decision)
        if result is True or result is None:
            return None

        # Result can be a violation message or False
        violation_message = (
            result if isinstance(result, str) else self.description
        )

        return GovernanceViolation(
            violation_id=f"{decision.decision_id}-{self.rule_id}",
            rule_type=self.rule_type,
            violated_rule_id=self.rule_id,
            severity=self.severity,
            description=violation_message,
            violating_agent_id=decision.proposing_agent_id,
        )


class ConstitutionEvaluation:
    """Result of constitutional evaluation.

    Contains the outcome of evaluating a decision against
    all constitutional rules.
    """

    def __init__(
        self,
        decision_id: str,
        compliant: bool,
        violated_rules: list[str],
        violations: list[GovernanceViolation],
    ):
        """Initialize constitution evaluation result.

        Args:
            decision_id: Associated decision ID
            compliant: Whether decision is constitutionally compliant
            violated_rules: List of rule IDs that were violated
            violations: Detailed violation records
        """
        self.decision_id = decision_id
        self.compliant = compliant
        self.violated_rules = violated_rules
        self.violations = violations
        self.critical_violations = [
            v for v in violations if v.severity == "critical"
        ]


# =============================================================================
# CONSTITUTIONAL FRAMEWORK ENGINE
# =============================================================================


class ConstitutionalFrameworkEngine:
    """Engine for evaluating constitutional compliance.

    This engine loads the system constitution and evaluates
    all decisions against constitutional rules.

    The framework enforces:
    - Self-approval prohibitions
    - Plurality requirements
    - Authority boundaries
    - Budget limits
    - Separation of powers
    """

    def __init__(self, constitution: SystemConstitution | None = None):
        """Initialize the constitutional framework engine.

        Args:
            constitution: System constitution (uses default if None)
        """
        self.constitution = constitution or SystemConstitution()
        self.rules: list[ConstitutionalRule] = []
        self._load_default_rules()

    def _load_default_rules(self):
        """Load the default constitutional rules.

        These rules define the core governance constraints for TORQ.
        """
        # Rule: No self-approval
        self.rules.append(
            ConstitutionalRule(
                rule_id="NO_SELF_APPROVAL",
                rule_type=RuleType.SELF_APPROVAL,
                description="Agents cannot approve their own proposals",
                check_function=self._check_no_self_approval,
                severity="critical",
            )
        )

        # Rule: Plurality required for major actions
        self.rules.append(
            ConstitutionalRule(
                rule_id="PLURALITY_REQUIRED",
                rule_type=RuleType.PLURALITY,
                description="Major actions require approval from multiple agents",
                check_function=self._check_plurality,
                severity="high",
            )
        )

        # Rule: Authority boundaries
        self.rules.append(
            ConstitutionalRule(
                rule_id="AUTHORITY_BOUNDARY",
                rule_type=RuleType.AUTHORITY_BOUNDARY,
                description="Agents must operate within their authority level",
                check_function=self._check_authority_boundary,
                severity="critical",
            )
        )

        # Rule: Budget limits
        self.rules.append(
            ConstitutionalRule(
                rule_id="BUDGET_LIMIT",
                rule_type=RuleType.BUDGET_LIMIT,
                description="Cannot exceed allocated budget",
                check_function=self._check_budget_limit,
                severity="critical",
            )
        )

        # Rule: Separation of powers
        self.rules.append(
            ConstitutionalRule(
                rule_id="SEPARATION_OF_POWERS",
                rule_type=RuleType.SEPARATION_OF_POWERS,
                description="Planning and execution roles must be separated",
                check_function=self._check_separation_of_powers,
                severity="high",
            )
        )

        # Rule: Governance changes require higher approval
        self.rules.append(
            ConstitutionalRule(
                rule_id="GOVERNANCE_CHANGE_PROTECTION",
                rule_type=RuleType.HUMAN_OVERRIDE,
                description="Governance changes require special approval",
                check_function=self._check_governance_change_protection,
                severity="critical",
            )
        )

    async def evaluate_decision(
        self,
        decision: GovernanceDecisionPacket,
        authority_enforcer: "AuthorityBoundaryEnforcer | None" = None,
    ) -> ConstitutionEvaluation:
        """Evaluate a decision against all constitutional rules.

        Args:
            decision: Decision packet to evaluate
            authority_enforcer: Optional authority enforcer for detailed checks

        Returns:
            ConstitutionEvaluation with compliance results
        """
        violations = []
        violated_rules = []

        for rule in self.rules:
            # Skip authority check if enforcer not provided (will be checked separately)
            if (
                rule.rule_id == "AUTHORITY_BOUNDARY"
                and authority_enforcer is None
            ):
                continue

            violation = rule.evaluate(decision)
            if violation:
                violations.append(violation)
                violated_rules.append(rule.rule_id)

        # Decision is compliant if no critical violations
        critical_violations = [v for v in violations if v.severity == "critical"]
        compliant = len(critical_violations) == 0

        return ConstitutionEvaluation(
            decision_id=decision.decision_id,
            compliant=compliant,
            violated_rules=violated_rules,
            violations=violations,
        )

    # -------------------------------------------------------------------------
    # RULE CHECK FUNCTIONS
    # -------------------------------------------------------------------------

    def _check_no_self_approval(
        self, decision: GovernanceDecisionPacket
    ) -> bool | str:
        """Check that agent is not approving their own proposal."""
        if decision.approving_agent_id is None:
            return True  # No approval yet, not a violation

        if decision.proposing_agent_id == decision.approving_agent_id:
            return f"Agent {decision.proposing_agent_id} cannot approve their own proposal"

        return True

    def _check_plurality(
        self, decision: GovernanceDecisionPacket
    ) -> bool | str:
        """Check plurality requirements for major actions."""
        # High-cost decisions require plural approval
        if decision.estimated_cost > 1000:
            if len(decision.approval_chain) < 2:
                return "High-cost decisions require approval from multiple agents"

        # Governance changes always require plural approval
        if decision.is_governance_change:
            if len(decision.approval_chain) < 2:
                return "Governance changes require approval from multiple agents"

        return True

    def _check_authority_boundary(
        self, decision: GovernanceDecisionPacket
    ) -> bool | str:
        """Check that agents operate within authority boundaries.

        Note: This is a basic check. Full authority checking is done
        by AuthorityBoundaryEnforcer.
        """
        # Budget changes require higher authority
        if decision.is_budget_change:
            if decision.approving_agent_id is None:
                return "Budget changes require explicit approval"

        return True

    def _check_budget_limit(
        self, decision: GovernanceDecisionPacket
    ) -> bool | str:
        """Check that decision doesn't exceed remaining budget."""
        if decision.estimated_cost > decision.budget_remaining:
            return f"Cost {decision.estimated_cost} exceeds remaining budget {decision.budget_remaining}"

        return True

    def _check_separation_of_powers(
        self, decision: GovernanceDecisionPacket
    ) -> bool | str:
        """Check separation between planning and execution roles."""
        # If action is execution, verify it wasn't proposed by an executor-only agent
        # (This is a simplified check - full implementation would track agent roles)

        # For now, just check that planning and execution aren't the same agent
        # for critical actions
        if decision.estimated_cost > 500:
            if (
                decision.proposing_agent_id == decision.approving_agent_id
                and decision.approving_agent_id is not None
            ):
                return "High-value actions require separation between proposal and approval"

        return True

    def _check_governance_change_protection(
        self, decision: GovernanceDecisionPacket
    ) -> bool | str:
        """Check that governance changes have proper approval."""
        if not decision.is_governance_change:
            return True

        # Governance changes require plural approval
        if len(decision.approval_chain) < 2:
            return "Governance changes require plural approval"

        # Governance changes should be flagged for human review
        if not decision.requires_human_approval:
            return "Governance changes should be flagged for human review"

        return True

    def add_rule(self, rule: ConstitutionalRule):
        """Add a new constitutional rule.

        Args:
            rule: Rule to add to the constitution
        """
        self.rules.append(rule)

    def remove_rule(self, rule_id: str) -> bool:
        """Remove a constitutional rule.

        Args:
            rule_id: ID of rule to remove

        Returns:
            True if rule was removed, False if not found
        """
        for i, rule in enumerate(self.rules):
            if rule.rule_id == rule_id:
                self.rules.pop(i)
                return True
        return False

    def get_rules(self) -> list[ConstitutionalRule]:
        """Get all constitutional rules.

        Returns:
            List of all rules
        """
        return self.rules.copy()


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def create_constitutional_framework_engine(
    constitution: SystemConstitution | None = None,
) -> ConstitutionalFrameworkEngine:
    """Factory function to create a constitutional framework engine.

    Args:
        constitution: Optional system constitution

    Returns:
        Configured ConstitutionalFrameworkEngine instance
    """
    return ConstitutionalFrameworkEngine(constitution=constitution)


# =============================================================================
# ALL EXPORTS
# =============================================================================

__all__ = [
    "ConstitutionalFrameworkEngine",
    "ConstitutionalRule",
    "ConstitutionEvaluation",
    "create_constitutional_framework_engine",
]
