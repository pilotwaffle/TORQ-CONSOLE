"""
Agent Teams - Team Definition Registry

Phase 5.2: Agent Teams as a governed execution primitive.

This module manages team definitions, including CRUD operations
and retrieval of team configurations for execution.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional
from uuid import UUID

from .models import TeamDefinition, TeamMemberRole, TeamPattern, DecisionPolicy, TeamRole


logger = logging.getLogger(__name__)


# ============================================================================
# Default Team Templates
# ============================================================================

DEFAULT_TEAMS: Dict[str, TeamDefinition] = {
    "planning_team": TeamDefinition(
        team_id="planning_team",
        name="Planning Team",
        description="Mission decomposition and strategic planning",
        pattern=TeamPattern.DELIBERATIVE_REVIEW,
        decision_policy=DecisionPolicy.WEIGHTED_CONSENSUS,
        max_rounds=3,
        members=[
            TeamMemberRole(
                role_name=TeamRole.LEAD,
                agent_type="planner_agent",
                confidence_weight=0.30,
                execution_order=1,
            ),
            TeamMemberRole(
                role_name=TeamRole.STRATEGIST,
                agent_type="strategist_agent",
                confidence_weight=0.20,
                execution_order=2,
            ),
            TeamMemberRole(
                role_name=TeamRole.CRITIC,
                agent_type="critic_agent",
                confidence_weight=0.20,
                execution_order=3,
            ),
            TeamMemberRole(
                role_name=TeamRole.VALIDATOR,
                agent_type="validator_agent",
                confidence_weight=0.30,
                execution_order=4,
            ),
        ],
    ),
    "research_team": TeamDefinition(
        team_id="research_team",
        name="Research Team",
        description="Evidence gathering and analysis",
        pattern=TeamPattern.DELIBERATIVE_REVIEW,
        decision_policy=DecisionPolicy.WEIGHTED_CONSENSUS,
        max_rounds=3,
        members=[
            TeamMemberRole(
                role_name=TeamRole.LEAD,
                agent_type="planner_agent",
                confidence_weight=0.30,
                execution_order=1,
            ),
            TeamMemberRole(
                role_name=TeamRole.RESEARCHER,
                agent_type="research_agent",
                confidence_weight=0.20,
                execution_order=2,
            ),
            TeamMemberRole(
                role_name=TeamRole.CRITIC,
                agent_type="critic_agent",
                confidence_weight=0.20,
                execution_order=3,
            ),
            TeamMemberRole(
                role_name=TeamRole.VALIDATOR,
                agent_type="validator_agent",
                confidence_weight=0.30,
                execution_order=4,
            ),
        ],
    ),
    "build_team": TeamDefinition(
        team_id="build_team",
        name="Build Team",
        description="Execution and implementation",
        pattern=TeamPattern.DELIBERATIVE_REVIEW,
        decision_policy=DecisionPolicy.WEIGHTED_CONSENSUS,
        max_rounds=3,
        members=[
            TeamMemberRole(
                role_name=TeamRole.LEAD,
                agent_type="planner_agent",
                confidence_weight=0.30,
                execution_order=1,
            ),
            TeamMemberRole(
                role_name=TeamRole.BUILDER,
                agent_type="builder_agent",
                confidence_weight=0.20,
                execution_order=2,
            ),
            TeamMemberRole(
                role_name=TeamRole.REVIEWER,
                agent_type="critic_agent",
                confidence_weight=0.20,
                execution_order=3,
            ),
            TeamMemberRole(
                role_name=TeamRole.VALIDATOR,
                agent_type="validator_agent",
                confidence_weight=0.30,
                execution_order=4,
            ),
        ],
    ),
}


# ============================================================================
# Team Registry
# ============================================================================

class TeamDefinitionRegistry:
    """
    Registry for managing team definitions.

    Provides CRUD operations for team configurations and
    caches team definitions for efficient runtime access.
    """

    def __init__(self):
        self._teams: Dict[str, TeamDefinition] = {}
        self._teams_by_id: Dict[UUID, TeamDefinition] = {}
        self._loaded_from_db = False

    async def initialize(self, supabase, load_from_db: bool = True) -> None:
        """
        Initialize the registry, optionally loading from database.

        Args:
            supabase: Supabase client
            load_from_db: Whether to load teams from database
        """
        if load_from_db:
            await self._load_from_database(supabase)

        # Always ensure default teams are available
        for team_id, definition in DEFAULT_TEAMS.items():
            if team_id not in self._teams:
                self.register(definition)

        logger.info(f"Team registry initialized with {len(self._teams)} teams")

    async def _load_from_database(self, supabase) -> None:
        """Load active team definitions from database."""
        try:
            result = supabase.table("agent_teams").select("*").eq("is_active", True).execute()

            for team_data in result.data:
                # Load members for this team
                members_result = supabase.table("agent_team_members").select("*").eq(
                    "team_id", team_data["id"]
                ).execute()

                members = []
                for member_data in members_result.data:
                    members.append(TeamMemberRole(
                        role_name=TeamRole(member_data["role_name"]),
                        agent_type=member_data["agent_type"],
                        confidence_weight=member_data.get("confidence_weight", 1.0),
                        execution_order=member_data.get("execution_order", 0),
                        is_required=member_data.get("is_required", True),
                        agent_config=member_data.get("agent_config", {}),
                    ))

                definition = TeamDefinition(
                    id=UUID(team_data["id"]),
                    team_id=team_data["team_id"],
                    name=team_data["name"],
                    description=team_data.get("description", ""),
                    pattern=TeamPattern(team_data["pattern"]),
                    decision_policy=DecisionPolicy(team_data["decision_policy"]),
                    max_rounds=team_data.get("max_rounds", 3),
                    output_schema=team_data.get("output_schema"),
                    escalation_policy=team_data.get("escalation_policy", "retry_with_fallback"),
                    is_active=team_data.get("is_active", True),
                    members=members,
                    metadata=team_data.get("metadata", {}),
                )

                self.register(definition)

            self._loaded_from_db = True
            logger.info(f"Loaded {len(result.data)} teams from database")

        except Exception as e:
            logger.warning(f"Failed to load teams from database: {e}")

    def register(self, definition: TeamDefinition) -> None:
        """
        Register a team definition.

        Args:
            definition: Team definition to register
        """
        self._teams[definition.team_id] = definition
        self._teams_by_id[definition.id] = definition
        logger.debug(f"Registered team: {definition.team_id}")

    def get_by_team_id(self, team_id: str) -> Optional[TeamDefinition]:
        """
        Get a team definition by team_id.

        Args:
            team_id: Team identifier

        Returns:
            Team definition or None if not found
        """
        return self._teams.get(team_id)

    def get_by_id(self, team_uuid: UUID) -> Optional[TeamDefinition]:
        """
        Get a team definition by UUID.

        Args:
            team_uuid: Team UUID

        Returns:
            Team definition or None if not found
        """
        return self._teams_by_id.get(team_uuid)

    def list_all(self) -> List[TeamDefinition]:
        """Get all registered team definitions."""
        return list(self._teams.values())

    def list_active(self) -> List[TeamDefinition]:
        """Get all active team definitions."""
        return [t for t in self._teams.values() if t.is_active]

    def list_by_pattern(self, pattern: TeamPattern) -> List[TeamDefinition]:
        """
        Get teams by collaboration pattern.

        Args:
            pattern: Collaboration pattern

        Returns:
            List of team definitions
        """
        return [t for t in self._teams.values() if t.pattern == pattern]

    def unregister(self, team_id: str) -> bool:
        """
        Unregister a team definition.

        Args:
            team_id: Team identifier

        Returns:
            True if unregistered, False if not found
        """
        definition = self._teams.pop(team_id, None)
        if definition:
            self._teams_by_id.pop(definition.id, None)
            logger.debug(f"Unregistered team: {team_id}")
            return True
        return False

    def get_member_role(
        self,
        team_id: str,
        role_name: TeamRole
    ) -> Optional[TeamMemberRole]:
        """
        Get a specific role from a team.

        Args:
            team_id: Team identifier
            role_name: Role to find

        Returns:
            Team member role or None if not found
        """
        definition = self.get_by_team_id(team_id)
        if definition:
            for member in definition.members:
                if member.role_name == role_name:
                    return member
        return None

    def get_roles_in_order(self, team_id: str) -> List[TeamMemberRole]:
        """
        Get team roles sorted by execution order.

        Args:
            team_id: Team identifier

        Returns:
            List of team member roles in execution order
        """
        definition = self.get_by_team_id(team_id)
        if definition:
            return sorted(definition.members, key=lambda m: m.execution_order)
        return []

    def get_required_roles(self, team_id: str) -> List[TeamMemberRole]:
        """
        Get required roles for a team.

        Args:
            team_id: Team identifier

        Returns:
            List of required team member roles
        """
        definition = self.get_by_team_id(team_id)
        if definition:
            return [m for m in definition.members if m.is_required]
        return []

    def get_confidence_weights(self, team_id: str) -> Dict[TeamRole, float]:
        """
        Get confidence weights for all roles in a team.

        Args:
            team_id: Team identifier

        Returns:
            Dictionary mapping roles to confidence weights
        """
        definition = self.get_by_team_id(team_id)
        if definition:
            return {m.role_name: m.confidence_weight for m in definition.members}
        return {}


# Global registry instance
_registry: Optional[TeamDefinitionRegistry] = None


def get_registry() -> TeamDefinitionRegistry:
    """Get the global team registry instance."""
    global _registry
    if _registry is None:
        _registry = TeamDefinitionRegistry()
    return _registry


async def initialize_registry(supabase) -> TeamDefinitionRegistry:
    """
    Initialize the global team registry.

    Args:
        supabase: Supabase client

    Returns:
        Initialized registry
    """
    registry = get_registry()
    await registry.initialize(supabase)
    return registry
