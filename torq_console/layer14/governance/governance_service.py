"""TORQ Layer 14 - Governance Service

This module provides the main service interface for Layer 14 governance,
coordinating all governance engines.
"""

from typing import Optional

from .constitutional_framework_engine import ConstitutionalFrameworkEngine
from .authority_boundary_enforcer import AuthorityBoundaryEnforcer, AuthorityProfile
from .legitimacy_scoring_engine import LegitimacyScoringEngine
from .authority_capture_detector import AuthorityCaptureDetector
from .governance_audit_ledger import GovernanceAuditLedger
from .models import (
    AgentAuthority,
    AuthorityLevel,
    GovernanceDecisionPacket,
    GovernanceResult,
    GovernanceViolation,
)


# =============================================================================
# GOVERNANCE SERVICE
# =============================================================================


class GovernanceService:
    """Main service for Layer 14 constitutional governance.

    This service coordinates all governance engines:
    - Constitutional framework evaluation
    - Authority boundary enforcement
    - Legitimacy scoring
    - Authority capture detection
    - Audit ledger

    The service acts as the final legitimacy gate between
    Layer 13 economic prioritization and execution.
    """

    def __init__(
        self,
        legitimacy_threshold: float = 0.7,
    ):
        """Initialize the governance service.

        Args:
            legitimacy_threshold: Minimum legitimacy score for execution
        """
        # Initialize engines
        self.constitution_engine = ConstitutionalFrameworkEngine()
        self.authority_enforcer = AuthorityBoundaryEnforcer()
        self.legitimacy_engine = LegitimacyScoringEngine(threshold=legitimacy_threshold)
        self.capture_detector = AuthorityCaptureDetector()
        self.audit_ledger = GovernanceAuditLedger()

        # Service configuration
        self.legitimacy_threshold = legitimacy_threshold
        self.enabled = True

    async def evaluate_decision(
        self,
        decision: GovernanceDecisionPacket,
    ) -> GovernanceResult:
        """Evaluate a decision through full governance pipeline.

        This is the main entry point for Layer 14 governance.
        All decisions must pass through this method before execution.

        Args:
            decision: Decision packet from Layer 13

        Returns:
            GovernanceResult with execution authorization decision
        """
        if not self.enabled:
            # Service disabled - auto-approve with warning
            return GovernanceResult(
                decision_id=decision.decision_id,
                legitimacy_score=1.0,
                legitimacy_threshold=self.legitimacy_threshold,
                execution_authorized=True,
                warning_violations=[
                    GovernanceViolation(
                        violation_id=f"{decision.decision_id}-disabled",
                        rule_type="governance_disabled",
                        violated_rule_id="N/A",
                        severity="low",
                        description="Governance service is disabled - auto-approved",
                    )
                ],
            )

        # Step 1: Constitutional evaluation
        constitution_eval = await self.constitution_engine.evaluate_decision(
            decision,
            self.authority_enforcer,
        )

        # Step 2: Authority boundary check
        proposer_check, approver_check = await self.authority_enforcer.check_decision_authority(
            decision,
        )

        authority_compliant = (
            (proposer_check.permitted if proposer_check else True)
            and (approver_check.permitted if approver_check else True)
        )

        # Step 3: Track decision for capture detection
        self.capture_detector.track_decision(decision)

        # Step 4: Assess capture risk
        capture_risk = await self.capture_detector.assess_capture_risk(
            decision.proposing_agent_id,
        )

        # Step 5: Compute legitimacy score
        result = await self.legitimacy_engine.create_governance_result(
            decision=decision,
            constitution_compliant=constitution_eval.compliant,
            authority_compliant=authority_compliant,
            plurality_compliant=self._check_plurality_compliant(decision),
            violations=constitution_eval.violations,
            authority_risk_score=capture_risk.influence_score,
        )

        # Step 6: Record in audit ledger
        record_id = await self.audit_ledger.record_decision(decision, result)
        result.audit_record_id = record_id

        return result

    def _check_plurality_compliant(
        self, decision: GovernanceDecisionPacket,
    ) -> bool:
        """Check if decision meets plurality requirements.

        Args:
            decision: Decision packet

        Returns:
            True if plurality compliant, False otherwise
        """
        # High-value decisions require plural approval
        if decision.estimated_cost > 1000:
            return len(decision.approval_chain) >= 2

        # Governance changes require plural approval
        if decision.is_governance_change:
            return len(decision.approval_chain) >= 2

        return True

    def register_agent_authority(
        self,
        agent_id: str,
        authority_level: AuthorityLevel,
        permitted_actions: list[str] | None = None,
        forbidden_actions: list[str] | None = None,
        role: str = "agent",
    ) -> AuthorityProfile:
        """Register an agent's authority profile.

        Args:
            agent_id: Agent identifier
            authority_level: Granted authority level
            permitted_actions: Actions agent is permitted to perform
            forbidden_actions: Actions agent is forbidden from performing
            role: Functional role

        Returns:
            Created AuthorityProfile
        """
        authority = AgentAuthority(
            agent_id=agent_id,
            authority_level=authority_level,
            permitted_actions=permitted_actions or [],
            forbidden_actions=forbidden_actions or [],
        )

        profile = AuthorityProfile(
            agent_id=agent_id,
            authority=authority,
            role=role,
        )

        self.authority_enforcer.register_profile(profile)
        return profile

    def revoke_agent_authority(self, agent_id: str) -> bool:
        """Revoke an agent's authority.

        Args:
            agent_id: Agent to revoke

        Returns:
            True if revoked, False if not found
        """
        return self.authority_enforcer.revoke_authority(agent_id)

    async def check_authority(
        self,
        agent_id: str,
        action: str,
    ) -> bool:
        """Check if an agent is authorized to perform an action.

        Args:
            agent_id: Agent to check
            action: Action to check

        Returns:
            True if authorized, False otherwise
        """
        check = await self.authority_enforcer.check_authority(agent_id, action)
        return check.permitted

    async def assess_capture_risk(self, agent_id: str) -> dict:
        """Assess authority capture risk for an agent.

        Args:
            agent_id: Agent to assess

        Returns:
            Dictionary with risk assessment
        """
        risk = await self.capture_detector.assess_capture_risk(agent_id)
        return {
            "agent_id": risk.agent_id,
            "influence_score": risk.influence_score,
            "risk_level": risk.capture_risk_level,
            "warnings": risk.warnings,
        }

    def get_audit_records(
        self,
        limit: int = 100,
        agent_id: Optional[str] = None,
    ) -> list:
        """Get records from the audit ledger.

        Args:
            limit: Maximum records to return
            agent_id: Filter by agent ID

        Returns:
            List of audit records
        """
        return self.audit_ledger.get_records(limit=limit, agent_id=agent_id)

    def get_agent_statistics(self, agent_id: str) -> dict:
        """Get governance statistics for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Dictionary with agent statistics
        """
        return self.audit_ledger.get_agent_history(agent_id)

    def get_system_statistics(self) -> dict:
        """Get overall system governance statistics.

        Returns:
            Dictionary with system statistics
        """
        return self.audit_ledger.get_statistics()

    def set_legitimacy_threshold(self, threshold: float):
        """Set the legitimacy threshold for execution.

        Args:
            threshold: New threshold (0.0 to 1.0)
        """
        if 0.0 <= threshold <= 1.0:
            self.legitimacy_threshold = threshold
            self.legitimacy_engine.set_threshold(threshold)

    def enable(self):
        """Enable the governance service."""
        self.enabled = True

    def disable(self):
        """Disable the governance service (auto-approve all decisions).

        Warning: Disabling governance is a security risk.
        """
        self.enabled = False


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def create_governance_service(
    legitimacy_threshold: float = 0.7,
) -> GovernanceService:
    """Factory function to create a governance service.

    Args:
        legitimacy_threshold: Minimum legitimacy score for execution

    Returns:
        Configured GovernanceService instance
    """
    return GovernanceService(legitimacy_threshold=legitimacy_threshold)


# =============================================================================
# ALL EXPORTS
# =============================================================================

__all__ = [
    "GovernanceService",
    "create_governance_service",
]
