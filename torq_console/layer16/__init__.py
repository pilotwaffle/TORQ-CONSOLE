"""TORQ Layer 16 - Multi-Agent Economic Coordination

This layer enables distributed economic coordination across TORQ agents,
allowing resource markets, mission bidding, price discovery, and incentive
balancing across the network.
"""

from .models import (
    AgentMarketState,
    MissionBid,
    ResourceOffer,
    MarketEquilibrium,
    CoordinationResult,
    ResourcePrice,
    IncentiveAdjustment,
    AgentRegistration,
    MissionRequirements,
    AgentCapabilities,
)
from .engines import (
    ResourceMarketEngine,
    MissionAllocationEngine,
    PriceDiscoveryEngine,
    IncentiveBalancingEngine,
    EquilibriumDetector,
)
from .services import EconomicCoordinationService, create_economic_coordination_service

__all__ = [
    # Models
    "AgentMarketState",
    "MissionBid",
    "ResourceOffer",
    "MarketEquilibrium",
    "CoordinationResult",
    "ResourcePrice",
    "IncentiveAdjustment",
    "AgentRegistration",
    "MissionRequirements",
    "AgentCapabilities",
    # Engines
    "ResourceMarketEngine",
    "MissionAllocationEngine",
    "PriceDiscoveryEngine",
    "IncentiveBalancingEngine",
    "EquilibriumDetector",
    # Services
    "EconomicCoordinationService",
    "create_economic_coordination_service",
]
