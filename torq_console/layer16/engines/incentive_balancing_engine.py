"""TORQ Layer 16 - Incentive Balancing Engine

This engine ensures system-wide stability by balancing
exploration vs exploitation and agent profit vs network efficiency.
"""

from datetime import timedelta
from typing import Dict, List

from ..models import (
    IncentiveAdjustment,
    AgentMarketState,
    AgentCapabilities,
)


# =============================================================================
# INCENTIVE BALANCING ENGINE
# =============================================================================


class IncentiveBalancingEngine:
    """Engine for balancing agent incentives.

    Manages:
    - Exploration vs exploitation
    - Agent profit vs network efficiency
    - Specialization vs redundancy
    - Load balancing
    """

    def __init__(self):
        """Initialize the incentive balancing engine."""
        self._active_adjustments: Dict[str, List[IncentiveAdjustment]] = {}

        # Balancing thresholds
        self._exploration_target = 0.3  # 30% exploration
        self._load_balance_threshold = 0.8  # 80% load triggers rebalancing
        self._specialization_max = 0.9  # 90% specialization triggers redundancy incentive

    async def calculate_incentives(
        self,
        market_state: AgentMarketState,
        registered_agents: Dict[str, AgentCapabilities],
    ) -> List[IncentiveAdjustment]:
        """Calculate incentive adjustments for system balance.

        Args:
            market_state: Current market state
            registered_agents: All registered agents

        Returns:
            List of incentive adjustments
        """
        adjustments = []

        # Load balancing incentives
        load_adjustments = await self._balance_load(market_state, registered_agents)
        adjustments.extend(load_adjustments)

        # Specialization vs redundancy incentives
        specialization_adjustments = await self._balance_specialization(
            market_state, registered_agents
        )
        adjustments.extend(specialization_adjustments)

        # Exploration incentives
        exploration_adjustments = await self._incentivize_exploration(
            registered_agents
        )
        adjustments.extend(exploration_adjustments)

        # Apply adjustments
        for adj in adjustments:
            if adj.agent_id not in self._active_adjustments:
                self._active_adjustments[adj.agent_id] = []
            self._active_adjustments[adj.agent_id].append(adj)

        return adjustments

    async def _balance_load(
        self,
        market_state: AgentMarketState,
        agents: Dict[str, AgentCapabilities],
    ) -> List[IncentiveAdjustment]:
        """Create incentives for load balancing.

        Args:
            market_state: Current market state
            agents: All registered agents

        Returns:
            List of load balancing adjustments
        """
        adjustments = []

        # Identify overloaded and underloaded agents
        overloaded = []
        underloaded = []

        for agent_id, agent in agents.items():
            if agent.current_load > self._load_balance_threshold:
                overloaded.append(agent_id)
            elif agent.current_load < 0.5:
                underloaded.append(agent_id)

        # Create incentives to shift load
        for agent_id in overloaded:
            # Penalize (increase cost) to discourage new missions
            adjustments.append(IncentiveAdjustment(
                agent_id=agent_id,
                adjustment_type="tax",
                cost_multiplier=1.5,  # 50% more expensive
                reason="Agent overloaded - load balancing incentive",
                duration=timedelta(hours=1),
            ))

        for agent_id in underloaded:
            # Subsidize (decrease cost) to attract missions
            adjustments.append(IncentiveAdjustment(
                agent_id=agent_id,
                adjustment_type="subsidy",
                cost_multiplier=0.7,  # 30% discount
                reason="Agent underloaded - load balancing incentive",
                duration=timedelta(hours=1),
            ))

        return adjustments

    async def _balance_specialization(
        self,
        market_state: AgentMarketState,
        agents: Dict[str, AgentCapabilities],
    ) -> List[IncentiveAdjustment]:
        """Create incentives for specialization vs redundancy.

        Args:
            market_state: Current market state
            agents: All registered agents

        Returns:
            List of specialization adjustments
        """
        adjustments = []

        # Count specializations
        specialization_counts: Dict[str, int] = {}
        for agent in agents.values():
            for spec in agent.specializations:
                specialization_counts[spec] = specialization_counts.get(spec, 0) + 1

        if not specialization_counts:
            return []

        total_agents = len(agents)

        # Find over-concentrated specializations
        for spec, count in specialization_counts.items():
            concentration = count / max(total_agents, 1)

            if concentration > self._specialization_max:
                # Too concentrated - incentivize diversification or new specialists
                # Find agents with this specialization
                for agent_id, agent in agents.items():
                    if spec in agent.specializations:
                        # Slight penalty for being in over-concentrated area
                        adjustments.append(IncentiveAdjustment(
                            agent_id=agent_id,
                            adjustment_type="penalty",
                            cost_multiplier=1.1,  # 10% penalty
                            reason=f"Over-concentration in {spec} - consider diversification",
                            duration=timedelta(hours=4),
                        ))
                        break  # Only adjust one agent

            elif concentration < 0.2:  # Less than 20% have this
                # Under-served - incentivize this specialization
                for agent_id, agent in agents.items():
                    if spec in agent.specializations:
                        # Bonus for under-served specialization
                        adjustments.append(IncentiveAdjustment(
                            agent_id=agent_id,
                            adjustment_type="bonus",
                            cost_multiplier=0.8,  # 20% discount
                            reason=f"Under-served specialization {spec} - incentive bonus",
                            duration=timedelta(hours=4),
                        ))
                        break

        return adjustments

    async def _incentivize_exploration(
        self,
        agents: Dict[str, AgentCapabilities],
    ) -> List[IncentiveAdjustment]:
        """Create incentives for exploration.

        Args:
            agents: All registered agents

        Returns:
            List of exploration incentives
        """
        adjustments = []

        # Count agent types
        type_counts = {"specialist": 0, "generalist": 0, "orchestrator": 0}
        for agent in agents.values():
            type_counts[agent.agent_type] += 1

        total = sum(type_counts.values())
        if total == 0:
            return []

        # Calculate current exploration rate
        specialist_ratio = type_counts["specialist"] / total

        # If too few specialists (exploration), incentivize specialization
        if specialist_ratio < self._exploration_target:
            # Give generalists a reason to explore specialization
            for agent_id, agent in agents.items():
                if agent.agent_type == "generalist":
                    adjustments.append(IncentiveAdjustment(
                        agent_id=agent_id,
                        adjustment_type="priority_boost",
                        priority_adjustment=0.2,
                        reason="Exploration incentive - consider specializing",
                        duration=timedelta(hours=24),
                    ))

        return adjustments

    async def get_agent_multiplier(
        self,
        agent_id: str,
    ) -> float:
        """Get current cost multiplier for an agent.

        Args:
            agent_id: Agent to check

        Returns:
            Cost multiplier (1.0 = no adjustment)
        """
        adjustments = self._active_adjustments.get(agent_id, [])

        if not adjustments:
            return 1.0

        # Remove expired adjustments
        now = datetime.utcnow()
        active = [
            adj for adj in adjustments
            if adj.expires_at is None or adj.expires_at > now
        ]
        self._active_adjustments[agent_id] = active

        # Combine multipliers
        multiplier = 1.0
        for adj in active:
            multiplier *= adj.cost_multiplier

        return multiplier

    async def clear_expired_adjustments(self):
        """Remove expired incentive adjustments."""
        now = datetime.utcnow()

        for agent_id in list(self._active_adjustments.keys()):
            active = [
                adj for adj in self._active_adjustments[agent_id]
                if adj.expires_at is None or adj.expires_at > now
            ]
            if active:
                self._active_adjustments[agent_id] = active
            else:
                del self._active_adjustments[agent_id]

    def get_active_adjustments(self, agent_id: str | None = None) -> List[IncentiveAdjustment]:
        """Get active incentive adjustments.

        Args:
            agent_id: Optional agent ID to filter by

        Returns:
            List of active adjustments
        """
        if agent_id:
            return self._active_adjustments.get(agent_id, []).copy()

        all_adjustments = []
        for adj_list in self._active_adjustments.values():
            all_adjustments.extend(adj_list)
        return all_adjustments


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def create_incentive_balancing_engine() -> IncentiveBalancingEngine:
    """Factory function to create an incentive balancing engine.

    Returns:
        Configured IncentiveBalancingEngine instance
    """
    return IncentiveBalancingEngine()


# =============================================================================
# ALL EXPORTS
# =============================================================================

__all__ = [
    "IncentiveBalancingEngine",
    "create_incentive_balancing_engine",
]
