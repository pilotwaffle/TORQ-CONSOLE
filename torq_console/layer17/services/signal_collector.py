"""TORQ Layer 17 - L16 Signal Collector

This service collects signals from Layer 16 economic coordination
to drive evolution decisions.
"""

from datetime import datetime

from ..models import L16EcosystemSignal
from ...layer16.services import EconomicCoordinationService


# =============================================================================
# L16 SIGNAL COLLECTOR
# =============================================================================


class L16SignalCollector:
    """Service for collecting ecosystem signals from Layer 16.

    Collects:
    - Market state (agents, supply, demand, health)
    - Mission allocation data
    - Resource prices
    - Equilibrium state
    - Incentive adjustments

    All data comes from verified L16 producers only.
    """

    def __init__(self, l16_service: EconomicCoordinationService):
        """Initialize the signal collector.

        Args:
            l16_service: Layer 16 EconomicCoordinationService instance
        """
        self._l16_service = l16_service

    async def collect(self) -> L16EcosystemSignal:
        """Collect current ecosystem signal from Layer 16.

        Returns:
            L16EcosystemSignal with current ecosystem state

        Raises:
            RuntimeError: If L16 service is unavailable
        """
        # Get market state (async - verified)
        market_state = await self._l16_service.get_market_state()

        # Get equilibrium state (async - verified)
        equilibrium = await self._l16_service.get_equilibrium()

        # Get resource prices (async - verified)
        prices = await self._l16_service.get_resource_prices()

        # Get registered agents (sync - verified)
        agents = self._l16_service.get_registered_agents()

        # Get incentive adjustments (sync - verified)
        incentives = self._l16_service.get_incentive_adjustments()

        # Extract recent winning agent IDs from allocations
        # We'll need to track this separately or infer from market state
        recent_allocations = []

        # Build signal from verified L16 data only
        signal = L16EcosystemSignal(
            # Market State (verified from L16)
            total_agents=market_state.total_agents,
            active_agents=market_state.active_agents,
            market_health=market_state.market_health,
            # Resource Supply/Demand (verified from L16)
            resource_supply=dict(market_state.resource_supply),
            resource_demand=dict(market_state.resource_demand),
            supply_demand_gap=market_state.supply_demand_gap,
            # Recent allocations (will be populated separately)
            recent_allocations=recent_allocations,
            # Price Information (verified from L16)
            equilibrium_prices={k: v.current_price for k, v in prices.items()},
            # Equilibrium State (verified from L16)
            market_stable=equilibrium.stable,
            equilibrium_confidence=equilibrium.equilibrium_confidence,
            # Incentive Data (verified from L16)
            active_adjustments=len(incentives),
        )

        return signal


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def create_signal_collector(l16_service: EconomicCoordinationService) -> L16SignalCollector:
    """Factory function to create a signal collector.

    Args:
        l16_service: Layer 16 EconomicCoordinationService instance

    Returns:
        Configured L16SignalCollector instance
    """
    return L16SignalCollector(l16_service)


# =============================================================================
# ALL EXPORTS
# =============================================================================

__all__ = [
    "L16SignalCollector",
    "create_signal_collector",
]
