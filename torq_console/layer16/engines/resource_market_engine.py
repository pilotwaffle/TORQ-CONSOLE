"""TORQ Layer 16 - Resource Market Engine

This engine manages supply and demand for agent resources,
tracking market state and resource availability.
"""

from collections import defaultdict
from typing import Dict, List

from ..models import (
    AgentMarketState,
    AgentCapabilities,
    ResourceOffer,
)


# =============================================================================
# RESOURCE MARKET ENGINE
# =============================================================================


class ResourceMarketEngine:
    """Engine for managing agent resource markets.

    Tracks:
    - Resource supply from agent capabilities
    - Resource demand from mission requirements
    - Market health metrics
    - Agent availability
    """

    def __init__(self):
        """Initialize the resource market engine."""
        self._registered_agents: Dict[str, AgentCapabilities] = {}
        self._active_offers: List[ResourceOffer] = []
        self._price_history: Dict[str, List[float]] = defaultdict(list)
        self._max_history = 100  # Keep last 100 price points

    async def register_agent(
        self,
        capabilities: AgentCapabilities,
    ) -> AgentMarketState:
        """Register an agent and its capabilities.

        Args:
            capabilities: Agent capabilities to register

        Returns:
            Updated market state
        """
        self._registered_agents[capabilities.agent_id] = capabilities
        return await self.get_market_state()

    async def unregister_agent(self, agent_id: str) -> AgentMarketState:
        """Unregister an agent from the market.

        Args:
            agent_id: Agent to unregister

        Returns:
            Updated market state
        """
        if agent_id in self._registered_agents:
            del self._registered_agents[agent_id]
            # Remove associated offers
            self._active_offers = [
                o for o in self._active_offers if o.agent_id != agent_id
            ]
        return await self.get_market_state()

    async def submit_offer(self, offer: ResourceOffer) -> AgentMarketState:
        """Submit a resource offer to the market.

        Args:
            offer: Resource offer to submit

        Returns:
            Updated market state
        """
        # Verify agent exists
        if offer.agent_id not in self._registered_agents:
            raise ValueError(f"Agent {offer.agent_id} not registered")

        self._active_offers.append(offer)
        return await self.get_market_state()

    async def get_market_state(self) -> AgentMarketState:
        """Get current market state.

        Returns:
            Current AgentMarketState
        """
        # Calculate supply from registered agents
        supply = self._calculate_supply()

        # Calculate demand from active offers
        demand = self._calculate_demand()

        # Calculate equilibrium prices
        prices = self._calculate_equilibrium_prices(supply, demand)

        # Count agents by status
        total_agents = len(self._registered_agents)
        active_agents = sum(
            1 for a in self._registered_agents.values()
            if a.current_load < 0.9  # Less than 90% loaded
        )
        available_agents = sum(
            1 for a in self._registered_agents.values()
            if a.current_load < 0.5  # Less than 50% loaded
        )

        # Calculate market health
        market_health = self._calculate_market_health(supply, demand, total_agents)

        # Calculate totals
        total_supply = sum(supply.values())
        total_demand = sum(demand.values())
        supply_demand_gap = total_supply - total_demand

        # Calculate liquidity (ratio of active offers to agents)
        market_liquidity = min(1.0, len(self._active_offers) / max(1, total_agents))

        return AgentMarketState(
            resource_supply=supply,
            resource_demand=demand,
            equilibrium_price=prices,
            market_health=market_health,
            total_agents=total_agents,
            active_agents=active_agents,
            available_agents=available_agents,
            total_supply=total_supply,
            total_demand=total_demand,
            supply_demand_gap=supply_demand_gap,
            market_liquidity=market_liquidity,
        )

    def _calculate_supply(self) -> Dict[str, float]:
        """Calculate total resource supply from registered agents.

        Returns:
            Dictionary mapping resource type to total supply
        """
        supply = defaultdict(float)

        for agent in self._registered_agents.values():
            # Only count available capacity
            available_cpu = agent.cpu_capacity * (1 - agent.current_load)
            available_memory = agent.memory_capacity * (1 - agent.current_load)

            supply["cpu"] += available_cpu
            supply["memory"] += available_memory
            supply["storage"] += agent.storage_capacity * (1 - agent.current_load)
            supply["network"] += agent.network_bandwidth * (1 - agent.current_load)

            # Binary capabilities
            if agent.can_inference:
                supply["inference"] += 1.0
            if agent.can_plan:
                supply["planning"] += 1.0
            if agent.can_execute:
                supply["execution"] += 1.0
            if agent.can_monitor:
                supply["monitoring"] += 1.0

        return dict(supply)

    def _calculate_demand(self) -> Dict[str, float]:
        """Calculate total resource demand from active offers.

        Returns:
            Dictionary mapping resource type to total demand
        """
        demand = defaultdict(float)

        for offer in self._active_offers:
            demand[offer.resource_type] += offer.quantity

        return dict(demand)

    def _calculate_equilibrium_prices(
        self,
        supply: Dict[str, float],
        demand: Dict[str, float],
    ) -> Dict[str, float]:
        """Calculate equilibrium prices based on supply and demand.

        Args:
            supply: Resource supply
            demand: Resource demand

        Returns:
            Equilibrium prices per resource
        """
        prices = {}

        for resource in set(list(supply.keys()) + list(demand.keys())):
            s = supply.get(resource, 0)
            d = demand.get(resource, 0)

            if s == 0 and d == 0:
                prices[resource] = 10.0  # Base price
            elif s == 0:
                prices[resource] = 100.0  # Scarcity price
            else:
                # Price inversely proportional to supply/demand ratio
                ratio = s / max(d, 1)
                # Clamp ratio to reasonable bounds
                ratio = max(0.1, min(ratio, 10.0))
                # Base price of 10, adjusted by ratio
                prices[resource] = 10.0 / ratio

            # Record in history
            self._price_history[resource].append(prices[resource])
            if len(self._price_history[resource]) > self._max_history:
                self._price_history[resource].pop(0)

        return prices

    def _calculate_market_health(
        self,
        supply: Dict[str, float],
        demand: Dict[str, float],
        agent_count: int,
    ) -> float:
        """Calculate overall market health score.

        Args:
            supply: Resource supply
            demand: Resource demand
            agent_count: Number of registered agents

        Returns:
            Health score (0.0 to 1.0)
        """
        health = 1.0

        # Penalize if no agents
        if agent_count == 0:
            return 0.0

        # Check for critical resources
        critical_resources = ["cpu", "memory"]

        for resource in critical_resources:
            s = supply.get(resource, 0)
            d = demand.get(resource, 0)

            if d > 0 and s == 0:
                health *= 0.5  # Critical shortage
            elif s < d:
                health *= 0.8  # Undersupply
            elif s > d * 2:
                health *= 0.9  # Oversupply (inefficient)

        return max(0.0, min(1.0, health))

    async def find_matching_offers(
        self,
        resource_type: str,
        min_quantity: float = 0.0,
        max_price: float = float("inf"),
    ) -> List[ResourceOffer]:
        """Find resource offers matching criteria.

        Args:
            resource_type: Type of resource needed
            min_quantity: Minimum quantity required
            max_price: Maximum acceptable price

        Returns:
            List of matching offers
        """
        matches = []

        for offer in self._active_offers:
            if offer.resource_type != resource_type:
                continue

            if offer.quantity < min_quantity and not offer.can_partial:
                continue

            if offer.asking_price > max_price:
                continue

            matches.append(offer)

        # Sort by price (lowest first)
        matches.sort(key=lambda o: o.asking_price)

        return matches

    def get_price_history(self, resource_type: str) -> List[float]:
        """Get price history for a resource.

        Args:
            resource_type: Type of resource

        Returns:
            List of historical prices
        """
        return self._price_history.get(resource_type, []).copy()


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def create_resource_market_engine() -> ResourceMarketEngine:
    """Factory function to create a resource market engine.

    Returns:
        Configured ResourceMarketEngine instance
    """
    return ResourceMarketEngine()


# =============================================================================
# ALL EXPORTS
# =============================================================================

__all__ = [
    "ResourceMarketEngine",
    "create_resource_market_engine",
]
