"""TORQ Layer 16 - API Router

This module provides the API surface for multi-agent economic coordination.
"""

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..models import (
    AgentRegistration,
    AgentMarketState,
    CoordinationResult,
    MarketEquilibrium,
    MissionBid,
    MissionRequirements,
    ResourceOffer,
    ResourcePrice,
)
from ..services import EconomicCoordinationService


# =============================================================================
# API MODELS
# =============================================================================


class RegisterAgentRequest(BaseModel):
    """Request model for agent registration."""
    agent_id: str
    agent_type: Literal["specialist", "generalist", "orchestrator"]
    cpu_capacity: float = 100.0
    memory_capacity: float = 8.0
    storage_capacity: float = 50.0
    network_bandwidth: float = 1000.0
    can_inference: bool = False
    can_plan: bool = False
    can_execute: bool = False
    can_monitor: bool = False
    specializations: list[str] = []
    cost_per_cpu_unit: float = 1.0
    cost_per_memory_gb: float = 0.5
    base_hourly_rate: float = 10.0
    reliability_score: float = 0.9
    avg_completion_time: float = 60.0
    current_load: float = 0.0


class SubmitResourceOfferRequest(BaseModel):
    """Request model for resource offer submission."""
    offer_id: str
    agent_id: str
    resource_type: Literal["cpu", "memory", "storage", "network", "inference", "planning", "execution"]
    quantity: float
    asking_price: float = 10.0
    min_quantity: float = 1.0
    can_partial: bool = True


class SubmitMissionRequest(BaseModel):
    """Request model for mission submission."""
    mission_id: str
    mission_type: str
    required_cpu: float = 10.0
    required_memory: float = 1.0
    required_storage: float = 5.0
    required_network: float = 100.0
    requires_inference: bool = False
    requires_planning: bool = False
    requires_execution: bool = False
    requires_monitoring: bool = False
    required_specializations: list[str] = []
    max_cost: float = 1000.0
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    expected_value: float = 100.0


class SubmitMissionBidRequest(BaseModel):
    """Request model for mission bid submission."""
    bid_id: str
    mission_id: str
    agent_id: str
    bid_cost: float
    expected_value: float
    completion_probability: float
    estimated_duration_hours: float = 1.0
    cpu_usage: float
    memory_usage: float
    storage_usage: float
    specialization_match: float = 0.5
    capability_coverage: float = 0.5


class RunCoordinationRequest(BaseModel):
    """Request model for running coordination cycle."""
    mission_ids: list[str] = []


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str
    registered_agents: int
    pending_missions: int


class MarketStateResponse(BaseModel):
    """Market state response."""
    market_state: AgentMarketState
    resource_prices: dict[str, ResourcePrice]


class EquilibriumResponse(BaseModel):
    """Equilibrium state response."""
    equilibrium: MarketEquilibrium


# =============================================================================
# API ROUTER
# =============================================================================


router = APIRouter(
    prefix="/api/l16",
    tags=["economic-coordination"],
)

# Service singleton
_coordination_service: EconomicCoordinationService | None = None


def get_coordination_service() -> EconomicCoordinationService:
    """Get the coordination service instance."""
    global _coordination_service
    if _coordination_service is None:
        _coordination_service = EconomicCoordinationService()
    return _coordination_service


@router.post("/market/register-agent", response_model=AgentMarketState)
async def register_agent(request: RegisterAgentRequest) -> AgentMarketState:
    """Register a new agent in the economic coordination system.

    Args:
        request: Agent registration request

    Returns:
        Updated market state
    """
    service = get_coordination_service()

    # Build capabilities
    from ..models import AgentCapabilities
    capabilities = AgentCapabilities(
        agent_id=request.agent_id,
        agent_type=request.agent_type,
        cpu_capacity=request.cpu_capacity,
        memory_capacity=request.memory_capacity,
        storage_capacity=request.storage_capacity,
        network_bandwidth=request.network_bandwidth,
        can_inference=request.can_inference,
        can_plan=request.can_plan,
        can_execute=request.can_execute,
        can_monitor=request.can_monitor,
        specializations=request.specializations,
        cost_per_cpu_unit=request.cost_per_cpu_unit,
        cost_per_memory_gb=request.cost_per_memory_gb,
        base_hourly_rate=request.base_hourly_rate,
        reliability_score=request.reliability_score,
        avg_completion_time=request.avg_completion_time,
        current_load=request.current_load,
    )

    # Build registration
    registration = AgentRegistration(
        agent_id=request.agent_id,
        agent_type=request.agent_type,
        capabilities=capabilities,
    )

    return await service.register_agent(registration)


@router.post("/market/offer-resource", response_model=AgentMarketState)
async def offer_resource(request: SubmitResourceOfferRequest) -> AgentMarketState:
    """Submit a resource offer to the market.

    Args:
        request: Resource offer request

    Returns:
        Updated market state
    """
    service = get_coordination_service()

    offer = ResourceOffer(
        offer_id=request.offer_id,
        agent_id=request.agent_id,
        resource_type=request.resource_type,
        quantity=request.quantity,
        asking_price=request.asking_price,
        min_quantity=request.min_quantity,
        can_partial=request.can_partial,
    )

    return await service.submit_resource_offer(offer)


@router.post("/market/submit-mission")
async def submit_mission(request: SubmitMissionRequest):
    """Submit a mission for allocation.

    Args:
        request: Mission submission request

    Returns:
        Mission ID
    """
    service = get_coordination_service()

    mission = MissionRequirements(
        mission_id=request.mission_id,
        mission_type=request.mission_type,
        required_cpu=request.required_cpu,
        required_memory=request.required_memory,
        required_storage=request.required_storage,
        required_network=request.required_network,
        requires_inference=request.requires_inference,
        requires_planning=request.requires_planning,
        requires_execution=request.requires_execution,
        requires_monitoring=request.requires_monitoring,
        required_specializations=request.required_specializations,
        max_cost=request.max_cost,
        priority=request.priority,
        expected_value=request.expected_value,
    )

    mission_id = await service.submit_mission(mission)
    return {"mission_id": mission_id, "status": "pending"}


@router.post("/market/bid-mission")
async def bid_mission(request: SubmitMissionBidRequest):
    """Submit a bid for a mission.

    Args:
        request: Mission bid request

    Returns:
        Bid status
    """
    service = get_coordination_service()

    from datetime import timedelta
    bid = MissionBid(
        bid_id=request.bid_id,
        mission_id=request.mission_id,
        agent_id=request.agent_id,
        bid_cost=request.bid_cost,
        expected_value=request.expected_value,
        completion_probability=request.completion_probability,
        estimated_duration=timedelta(hours=request.estimated_duration_hours),
        cpu_usage=request.cpu_usage,
        memory_usage=request.memory_usage,
        storage_usage=request.storage_usage,
        specialization_match=request.specialization_match,
        capability_coverage=request.capability_coverage,
    )

    accepted = await service.submit_mission_bid(bid)
    return {"bid_id": request.bid_id, "accepted": accepted}


@router.post("/market/run-coordination", response_model=CoordinationResult)
async def run_coordination(request: RunCoordinationRequest) -> CoordinationResult:
    """Run a full economic coordination cycle.

    This orchestrates all Layer 16 engines to:
    - Discover resource prices
    - Balance incentives
    - Detect equilibrium
    - Allocate missions

    Args:
        request: Coordination request

    Returns:
        Full coordination result
    """
    service = get_coordination_service()

    mission_ids = request.mission_ids if request.mission_ids else None

    return await service.run_coordination_cycle(mission_ids)


@router.get("/market/state", response_model=MarketStateResponse)
async def get_market_state() -> MarketStateResponse:
    """Get current market state and resource prices.

    Returns:
        Market state and prices
    """
    service = get_coordination_service()

    market_state = await service.get_market_state()
    resource_prices = await service.get_resource_prices()

    return MarketStateResponse(
        market_state=market_state,
        resource_prices=resource_prices,
    )


@router.get("/market/equilibrium", response_model=EquilibriumResponse)
async def get_equilibrium() -> EquilibriumResponse:
    """Get current equilibrium state.

    Returns:
        Equilibrium assessment
    """
    service = get_coordination_service()

    equilibrium = await service.get_equilibrium()

    return EquilibriumResponse(equilibrium=equilibrium)


@router.get("/market/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint for the coordination service.

    Returns:
        Health status
    """
    service = get_coordination_service()

    agents = service.get_registered_agents()
    pending = service.get_pending_missions()

    return HealthResponse(
        status="healthy",
        service="economic_coordination",
        version="0.16.0",
        registered_agents=len(agents),
        pending_missions=len(pending),
    )


# =============================================================================
# OPTIONAL ENDPOINTS (can be added later)
# =============================================================================

@router.get("/market/agents")
async def list_agents():
    """List all registered agents.

    Optional endpoint - can be added in v2 if needed.
    """
    service = get_coordination_service()
    agents = service.get_registered_agents()
    return {
        "agents": [
            {
                "agent_id": agent_id,
                "agent_type": caps.agent_type,
                "current_load": caps.current_load,
                "specializations": caps.specializations,
            }
            for agent_id, caps in agents.items()
        ]
    }


@router.get("/market/missions")
async def list_missions():
    """List all pending missions.

    Optional endpoint - can be added in v2 if needed.
    """
    service = get_coordination_service()
    missions = service.get_pending_missions()
    return {"mission_ids": missions}


@router.get("/market/incentives/{agent_id}")
async def get_agent_incentives(agent_id: str):
    """Get incentive adjustments for an agent.

    Optional endpoint - can be added in v2 if needed.
    """
    service = get_coordination_service()
    adjustments = service.get_incentive_adjustments(agent_id)
    multiplier = await service.get_agent_cost_multiplier(agent_id)

    return {
        "agent_id": agent_id,
        "cost_multiplier": multiplier,
        "adjustments": adjustments,
    }


__all__ = ["router"]
