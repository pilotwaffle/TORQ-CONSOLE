"""TORQ Layer 14 - Authority Boundary Enforcer

This module implements authority boundary enforcement to ensure
agents operate within their authorized domains.
"""

from typing import TYPE_CHECKING

from .models import (
    AgentAuthority,
    AuthorityLevel,
    GovernanceDecisionPacket,
)

if TYPE_CHECKING:
    pass


# =============================================================================
# AUTHORITY CHECK RESULTS
# =============================================================================


class AuthorityCheck:
    """Result of an authority boundary check.

    Indicates whether an agent is authorized to perform
    a specific action.
    """

    def __init__(
        self,
        agent_id: str,
        action: str,
        permitted: bool,
        violation_reason: str | None = None,
        required_level: AuthorityLevel | None = None,
        actual_level: AuthorityLevel | None = None,
    ):
        """Initialize authority check result.

        Args:
            agent_id: Agent being checked
            action: Action being attempted
            permitted: Whether action is permitted
            violation_reason: Reason for denial if not permitted
            required_level: Authority level required for action
            actual_level: Agent's actual authority level
        """
        self.agent_id = agent_id
        self.action = action
        self.permitted = permitted
        self.violation_reason = violation_reason
        self.required_level = required_level
        self.actual_level = actual_level


class AuthorityProfile:
    """Authority profile for an agent.

    Contains the complete authority configuration for an agent,
    including granted permissions and constraints.
    """

    def __init__(
        self,
        agent_id: str,
        authority: AgentAuthority,
        role: str = "agent",
        constraints: dict | None = None,
    ):
        """Initialize authority profile.

        Args:
            agent_id: Agent identifier
            authority: Agent's authority configuration
            role: Functional role (e.g., "planner", "executor", "governor")
            constraints: Additional constraints dictionary
        """
        self.agent_id = agent_id
        self.authority = authority
        self.role = role
        self.constraints = constraints or {}

    def has_permission(self, action: str) -> bool:
        """Check if agent has permission for an action.

        Args:
            action: Action to check

        Returns:
            True if permitted, False otherwise
        """
        # Check forbidden list first
        if action in self.authority.forbidden_actions:
            return False

        # Check permitted list
        if self.authority.permitted_actions:
            return action in self.authority.permitted_actions

        # No specific list, check by authority level
        return True

    def can_access_resource(self, resource: str) -> bool:
        """Check if agent can access a resource.

        Args:
            resource: Resource identifier

        Returns:
            True if access permitted, False otherwise
        """
        if not self.authority.resource_constraints:
            return True

        for constraint in self.authority.resource_constraints:
            if constraint in resource:
                return False

        return True

    def is_expired(self) -> bool:
        """Check if authority has expired.

        Returns:
            True if expired, False otherwise
        """
        if self.authority.expires_at is None:
            return False

        from datetime import datetime

        return datetime.utcnow() > self.authority.expires_at


# =============================================================================
# AUTHORITY BOUNDARY ENFORCER
# =============================================================================


class AuthorityBoundaryEnforcer:
    """Engine for enforcing agent authority boundaries.

    This engine ensures that all actions performed by agents
    stay within their granted authority levels and permissions.

    The enforcer validates:
    - Agent authority levels
    - Specific action permissions
    - Resource access constraints
    - Authority expiration
    """

    # Default authority requirements for action types
    DEFAULT_ACTION_REQUIREMENTS = {
        "propose": AuthorityLevel.PROPOSE,
        "advise": AuthorityLevel.ADVISE,
        "execute": AuthorityLevel.EXECUTE,
        "approve": AuthorityLevel.APPROVE,
        "govern": AuthorityLevel.GOVERN,
        "allocate_budget": AuthorityLevel.APPROVE,
        "modify_governance": AuthorityLevel.GOVERN,
    }

    def __init__(self):
        """Initialize the authority boundary enforcer."""
        self.profiles: dict[str, AuthorityProfile] = {}
        self.action_requirements = self.DEFAULT_ACTION_REQUIREMENTS.copy()

    def register_profile(self, profile: AuthorityProfile):
        """Register an agent's authority profile.

        Args:
            profile: Authority profile to register
        """
        self.profiles[profile.agent_id] = profile

    def get_profile(self, agent_id: str) -> AuthorityProfile | None:
        """Get an agent's authority profile.

        Args:
            agent_id: Agent identifier

        Returns:
            AuthorityProfile if found, None otherwise
        """
        return self.profiles.get(agent_id)

    async def check_authority(
        self,
        agent_id: str,
        action: str,
        context: dict | None = None,
    ) -> AuthorityCheck:
        """Check if an agent is authorized to perform an action.

        Args:
            agent_id: Agent to check
            action: Action being attempted
            context: Additional context for the check

        Returns:
            AuthorityCheck with permit/deny result
        """
        profile = self.get_profile(agent_id)

        if profile is None:
            # No profile found - assume minimal authority
            return AuthorityCheck(
                agent_id=agent_id,
                action=action,
                permitted=False,
                violation_reason=f"Agent {agent_id} has no registered authority profile",
                required_level=self._get_required_level(action),
                actual_level=AuthorityLevel.NONE,
            )

        # Check if authority is expired
        if profile.is_expired():
            return AuthorityCheck(
                agent_id=agent_id,
                action=action,
                permitted=False,
                violation_reason="Agent authority has expired",
                required_level=self._get_required_level(action),
                actual_level=profile.authority.authority_level,
            )

        # Check if agent has permission for this specific action
        if not profile.has_permission(action):
            return AuthorityCheck(
                agent_id=agent_id,
                action=action,
                permitted=False,
                violation_reason=f"Agent {agent_id} is not permitted to perform action: {action}",
                required_level=self._get_required_level(action),
                actual_level=profile.authority.authority_level,
            )

        # Check authority level
        required_level = self._get_required_level(action)
        actual_level = profile.authority.authority_level

        if not self._sufficient_authority(actual_level, required_level):
            return AuthorityCheck(
                agent_id=agent_id,
                action=action,
                permitted=False,
                violation_reason=f"Insufficient authority level: {actual_level.value} < {required_level.value}",
                required_level=required_level,
                actual_level=actual_level,
            )

        return AuthorityCheck(
            agent_id=agent_id,
            action=action,
            permitted=True,
            required_level=required_level,
            actual_level=actual_level,
        )

    async def check_decision_authority(
        self,
        decision: GovernanceDecisionPacket,
    ) -> tuple[AuthorityCheck, AuthorityCheck | None]:
        """Check authority for both proposer and approver.

        Args:
            decision: Decision packet with proposer and approver

        Returns:
            Tuple of (proposer_check, approver_check or None)
        """
        proposer_check = await self.check_authority(
            decision.proposing_agent_id,
            decision.action_type,
        )

        approver_check = None
        if decision.approving_agent_id:
            approver_check = await self.check_authority(
                decision.approving_agent_id,
                "approve",
            )

        return proposer_check, approver_check

    async def check_resource_access(
        self,
        agent_id: str,
        resource: str,
    ) -> bool:
        """Check if an agent can access a resource.

        Args:
            agent_id: Agent to check
            resource: Resource identifier

        Returns:
            True if access permitted, False otherwise
        """
        profile = self.get_profile(agent_id)
        if profile is None:
            return False

        return profile.can_access_resource(resource)

    def _get_required_level(self, action: str) -> AuthorityLevel:
        """Get the required authority level for an action.

        Args:
            action: Action type

        Returns:
            Required AuthorityLevel
        """
        return self.action_requirements.get(
            action,
            AuthorityLevel.EXECUTE,  # Default to EXECUTE if unknown
        )

    def _sufficient_authority(
        self,
        actual: AuthorityLevel,
        required: AuthorityLevel,
    ) -> bool:
        """Check if actual authority is sufficient for required.

        Args:
            actual: Agent's actual authority level
            required: Required authority level

        Returns:
            True if sufficient, False otherwise
        """
        # Authority hierarchy (higher value = more authority)
        hierarchy = {
            AuthorityLevel.NONE: 0,
            AuthorityLevel.READ: 1,
            AuthorityLevel.PROPOSE: 2,
            AuthorityLevel.ADVISE: 3,
            AuthorityLevel.EXECUTE: 4,
            AuthorityLevel.APPROVE: 5,
            AuthorityLevel.GOVERN: 6,
            AuthorityLevel.ROOT: 7,
        }

        return hierarchy.get(actual, 0) >= hierarchy.get(required, 0)

    def set_action_requirement(
        self,
        action: str,
        required_level: AuthorityLevel,
    ):
        """Set the authority requirement for an action type.

        Args:
            action: Action type
            required_level: Required authority level
        """
        self.action_requirements[action] = required_level

    def revoke_authority(self, agent_id: str) -> bool:
        """Revoke an agent's authority.

        Args:
            agent_id: Agent to revoke

        Returns:
            True if revoked, False if not found
        """
        if agent_id in self.profiles:
            del self.profiles[agent_id]
            return True
        return False


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def create_authority_boundary_enforcer() -> AuthorityBoundaryEnforcer:
    """Factory function to create an authority boundary enforcer.

    Returns:
        Configured AuthorityBoundaryEnforcer instance
    """
    return AuthorityBoundaryEnforcer()


# =============================================================================
# ALL EXPORTS
# =============================================================================

__all__ = [
    "AuthorityBoundaryEnforcer",
    "AuthorityProfile",
    "AuthorityCheck",
    "create_authority_boundary_enforcer",
]
