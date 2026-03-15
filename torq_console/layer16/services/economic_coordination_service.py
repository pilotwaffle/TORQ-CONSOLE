"""TORQ Layer 16 - Economic Coordination Service

This service orchestrates all Layer 16 engines to enable
multi-agent economic coordination across the TORQ network.
"""

import time
import uuid
from typing import Dict, List

from ..models import (
    AgentCapabilities,
    AgentMarketState,
    AgentRegistration,
    CoordinationResult,
    IncentiveAdjustment,
    MarketEquilibrium,
    MissionAllocation,
    MissionBid,
    MissionRequirements,
    ResourceOffer,
    ResourcePrice,
)
from ..engines import (
    ResourceMarketEngine,
    MissionAllocationEngine,
    PriceDiscoveryEngine,
    IncentiveBalancingEngine,
    EquilibriumDetector,
    create_resource_market_engine,
    create_mission_allocation_engine,
    create_price_discovery_engine,
    create_incentive_balancing_engine,
    create_equilibrium_detector,
)


# =============================================================================
# ECONOMIC COORDINATION SERVICE
# =============================================================================


class EconomicCoordinationService:
    """Service for orchestrating multi-agent economic coordination.

    This service integrates all five Layer 16 engines:
    1. ResourceMarketEngine - manages agent resource markets
    2. MissionAllocationEngine - handles mission bidding and allocation
    3. PriceDiscoveryEngine - discovers fair resource prices
    4. IncentiveBalancingEngine - balances system-wide incentives
    5. EquilibriumDetector - detects market stabilization

    Coordination Flow:
    1. Collect agent resource offers
    2. Collect mission bids
    3. Run price discovery
    4. Calculate incentive adjustments
    5. Detect market equilibrium
    6. Allocate missions
    """

    def __init__(
        self,
        resource_engine: ResourceMarketEngine | None = None,
        allocation_engine: MissionAllocationEngine | None = None,
        price_engine: PriceDiscoveryEngine | None = None,
        incentive_engine: IncentiveBalancingEngine | None = None,
        equilibrium_engine: EquilibriumDetector | None = None,
    ):
        """Initialize the economic coordination service.

        Args:
            resource_engine: Optional custom resource market engine
            allocation_engine: Optional custom mission allocation engine
            price_engine: Optional custom price discovery engine
            incentive_engine: Optional custom incentive balancing engine
            equilibrium_engine: Optional custom equilibrium detector
        """
        self._resource_engine = resource_engine or create_resource_market_engine()
        self._allocation_engine = allocation_engine or create_mission_allocation_engine()
        self._price_engine = price_engine or create_price_discovery_engine()
        self._incentive_engine = incentive_engine or create_incentive_balancing_engine()
        self._equilibrium_engine = equilibrium_engine or create_equilibrium_detector()

        # Coordination state
        self._coordination_count = 0
        self._registered_agents: Dict[str, AgentCapabilities] = {}
        self._pending_missions: Dict[str, MissionRequirements] = {}

    # =============================================================================
    # AGENT REGISTRATION
    # =============================================================================

    async def register_agent(
        self,
        registration: AgentRegistration,
    ) -> AgentMarketState:
        """Register a new agent in the coordination system.

        Args:
            registration: Agent registration details

        Returns:
            Updated market state
        """
        # Store capabilities
        self._registered_agents[registration.agent_id] = registration.capabilities

        # Register with resource market engine
        market_state = await self._resource_engine.register_agent(
            registration.capabilities
        )

        return market_state

    async def unregister_agent(self, agent_id: str) -> AgentMarketState:
        """Unregister an agent from the coordination system.

        Args:
            agent_id: Agent to unregister

        Returns:
            Updated market state
        """
        if agent_id in self._registered_agents:
            del self._registered_agents[agent_id]

        return await self._resource_engine.unregister_agent(agent_id)

    # =============================================================================
    # RESOURCE OFFERS
    # =============================================================================

    async def submit_resource_offer(
        self,
        offer: ResourceOffer,
    ) -> AgentMarketState:
        """Submit a resource offer to the market.

        Args:
            offer: Resource offer

        Returns:
            Updated market state
        """
        return await self._resource_engine.submit_offer(offer)

    # =============================================================================
    # MISSION SUBMISSION AND BIDDING
    # =============================================================================

    async def submit_mission(
        self,
        mission: MissionRequirements,
    ) -> str:
        """Submit a mission for allocation.

        Args:
            mission: Mission requirements

        Returns:
            Mission ID
        """
        mission_id = await self._allocation_engine.submit_mission(mission)
        self._pending_missions[mission_id] = mission
        return mission_id

    async def submit_mission_bid(
        self,
        bid: MissionBid,
    ) -> bool:
        """Submit a bid for a mission.

        Args:
            bid: Mission bid

        Returns:
            True if bid accepted
        """
        return await self._allocation_engine.submit_bid(bid)

    # =============================================================================
    # COORDINATION CYCLE
    # =============================================================================

    async def run_coordination_cycle(
        self,
        mission_ids: List[str] | None = None,
    ) -> CoordinationResult:
        """Run a full coordination cycle.

        This is the main entry point for economic coordination.

        Args:
            mission_ids: Optional list of specific missions to allocate.
                        If None, allocates all pending missions.

        Returns:
            CoordinationResult with full cycle outcomes
        """
        start_time = time.time()
        coordination_id = str(uuid.uuid4())

        # Increment cycle counter
        self._coordination_count += 1

        # Step 1: Get market state
        market_state = await self._resource_engine.get_market_state()

        # Step 2: Discover prices
        resource_prices = await self._price_engine.discover_prices(market_state)

        # Step 3: Calculate incentives
        incentive_adjustments = await self._incentive_engine.calculate_incentives(
            market_state,
            self._registered_agents,
        )

        # Step 4: Detect equilibrium
        equilibrium = await self._equilibrium_engine.detect_equilibrium(
            market_state,
            resource_prices,
        )

        # Step 5: Allocate missions
        if mission_ids is None:
            mission_ids = self._allocation_engine.get_pending_missions()

        mission_allocations = []
        total_value = 0.0
        total_cost = 0.0

        for mission_id in mission_ids:
            allocation = await self._allocation_engine.allocate_mission(
                mission_id,
                self._registered_agents,
            )

            if allocation:
                mission_allocations.append(allocation)
                total_value += allocation.expected_value
                total_cost += allocation.allocation_cost

                # Close allocated mission
                await self._allocation_engine.close_mission(mission_id)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Calculate coordination health
        coordination_health = self._calculate_coordination_health(
            market_state,
            equilibrium,
            len(mission_allocations),
            len(mission_ids),
        )

        # Build result
        result = CoordinationResult(
            coordination_id=coordination_id,
            cycle_number=self._coordination_count,
            market_state=market_state,
            equilibrium=equilibrium,
            mission_allocations=mission_allocations,
            incentive_adjustments=incentive_adjustments,
            resource_prices=resource_prices,
            total_missions_processed=len(mission_ids),
            total_missions_allocated=len(mission_allocations),
            total_value_generated=total_value,
            total_cost_incurred=total_cost,
            coordination_health=coordination_health,
            coordination_duration_ms=duration_ms,
        )

        # Mark completion
        import datetime
        result.completed_at = datetime.datetime.utcnow()

        return result

    def _calculate_coordination_health(
        self,
        market_state: AgentMarketState,
        equilibrium: MarketEquilibrium,
        allocated: int,
        processed: int,
    ) -> float:
        """Calculate coordination health score.

        Args:
            market_state: Current market state
            equilibrium: Equilibrium assessment
            allocated: Missions allocated
            processed: Missions processed

        Returns:
            Health score (0.0 to 1.0)
        """
        health = 0.5  # Base health

        # Market health contributes
        health += market_state.market_health * 0.3

        # Equilibrium confidence contributes
        health += equilibrium.equilibrium_confidence * 0.15

        # Allocation rate contributes
        if processed > 0:
            allocation_rate = allocated / processed
            health += allocation_rate * 0.2

        return max(0.0, min(1.0, health))

    # =============================================================================
    # QUERY METHODS
    # =============================================================================

    async def get_market_state(self) -> AgentMarketState:
        """Get current market state.

        Returns:
            Current AgentMarketState
        """
        return await self._resource_engine.get_market_state()

    async def get_equilibrium(self) -> MarketEquilibrium:
        """Get current equilibrium state.

        Returns:
            Current MarketEquilibrium
        """
        market_state = await self._resource_engine.get_market_state()
        resource_prices = await self._price_engine.discover_prices(market_state)
        return await self._equilibrium_engine.detect_equilibrium(
            market_state,
            resource_prices,
        )

    async def get_resource_prices(self) -> Dict[str, ResourcePrice]:
        """Get current resource prices.

        Returns:
            Dictionary mapping resource type to ResourcePrice
        """
        market_state = await self._resource_engine.get_market_state()
        return await self._price_engine.discover_prices(market_state)

    def get_registered_agents(self) -> Dict[str, AgentCapabilities]:
        """Get all registered agents.

        Returns:
            Dictionary mapping agent ID to capabilities
        """
        return self._registered_agents.copy()

    def get_pending_missions(self) -> List[str]:
        """Get pending mission IDs.

        Returns:
            List of mission IDs awaiting allocation
        """
        return self._allocation_engine.get_pending_missions()

    def get_incentive_adjustments(
        self,
        agent_id: str | None = None,
    ) -> List[IncentiveAdjustment]:
        """Get active incentive adjustments.

        Args:
            agent_id: Optional agent ID to filter by

        Returns:
            List of active adjustments
        """
        return self._incentive_engine.get_active_adjustments(agent_id)

    async def get_agent_cost_multiplier(self, agent_id: str) -> float:
        """Get current cost multiplier for an agent.

        Args:
            agent_id: Agent to check

        Returns:
            Cost multiplier (1.0 = no adjustment)
        """
        return await self._incentive_engine.get_agent_multiplier(agent_id)


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def create_economic_coordination_service() -> EconomicCoordinationService:
    """Factory function to create an economic coordination service.

    Returns:
        Configured EconomicCoordinationService instance
    """
    return EconomicCoordinationService()


# =============================================================================
# ALL EXPORTS
# =============================================================================

__all__ = [
    "EconomicCoordinationService",
    "create_economic_coordination_service",
]
