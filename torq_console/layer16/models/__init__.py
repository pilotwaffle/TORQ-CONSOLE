"""TORQ Layer 16 - Core Data Models

This module defines the core data structures for multi-agent economic
coordination, resource markets, mission allocation, and price discovery.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def datetime_utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.utcnow()


# =============================================================================
# AGENT AND MISSION MODELS
# =============================================================================


class AgentCapabilities(BaseModel):
    """Capabilities offered by an agent."""

    agent_id: str = Field(description="Unique agent identifier")
    agent_type: Literal["specialist", "generalist", "orchestrator"] = Field(
        description="Type of agent"
    )

    # Resource Capacities
    cpu_capacity: float = Field(default=100.0, ge=0, description="CPU capacity units")
    memory_capacity: float = Field(default=8.0, ge=0, description="Memory in GB")
    storage_capacity: float = Field(default=50.0, ge=0, description="Storage in GB")
    network_bandwidth: float = Field(default=1000.0, ge=0, description="Network Mbps")

    # Specialized Capabilities
    can_inference: bool = Field(default=False, description="Can run model inference")
    can_plan: bool = Field(default=False, description="Can perform planning")
    can_execute: bool = Field(default=False, description="Can execute actions")
    can_monitor: bool = Field(default=False, description="Can monitor systems")

    # Specializations
    specializations: list[str] = Field(
        default_factory=list,
        description="Agent specializations (e.g., 'trading', 'monitoring', 'analysis')",
    )

    # Cost Model
    cost_per_cpu_unit: float = Field(default=1.0, ge=0, description="Cost per CPU unit")
    cost_per_memory_gb: float = Field(default=0.5, ge=0, description="Cost per GB memory")
    base_hourly_rate: float = Field(default=10.0, ge=0, description="Base hourly rate")

    # Performance Metrics
    reliability_score: float = Field(
        default=0.9, ge=0.0, le=1.0, description="Historical reliability"
    )
    avg_completion_time: float = Field(
        default=60.0, ge=0, description="Average task completion time (seconds)"
    )

    # Availability
    availability_start: datetime | None = Field(
        default=None, description="When agent becomes available"
    )
    availability_end: datetime | None = Field(
        default=None, description="When agent becomes unavailable"
    )
    current_load: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Current utilization (0-1)"
    )

    registered_at: datetime = Field(default_factory=datetime_utcnow)


class AgentRegistration(BaseModel):
    """Registration request for a new agent."""

    agent_id: str = Field(description="Unique agent identifier")
    agent_type: Literal["specialist", "generalist", "orchestrator"] = Field(
        description="Type of agent"
    )
    capabilities: AgentCapabilities = Field(description="Agent capabilities")
    registration_token: str | None = Field(
        default=None, description="Optional registration token"
    )
    registered_at: datetime = Field(default_factory=datetime_utcnow)


class MissionRequirements(BaseModel):
    """Requirements for a mission to be allocated."""

    mission_id: str = Field(description="Unique mission identifier")
    mission_type: str = Field(description="Type of mission")

    # Resource Requirements
    required_cpu: float = Field(default=10.0, ge=0, description="CPU units required")
    required_memory: float = Field(default=1.0, ge=0, description="Memory in GB required")
    required_storage: float = Field(default=5.0, ge=0, description="Storage in GB required")
    required_network: float = Field(
        default=100.0, ge=0, description="Network Mbps required"
    )

    # Capability Requirements
    requires_inference: bool = Field(default=False, description="Needs inference capability")
    requires_planning: bool = Field(default=False, description="Needs planning capability")
    requires_execution: bool = Field(default=False, description="Needs execution capability")
    requires_monitoring: bool = Field(
        default=False, description="Needs monitoring capability"
    )

    # Required Specializations
    required_specializations: list[str] = Field(
        default_factory=list, description="Required agent specializations"
    )

    # Constraints
    max_cost: float = Field(default=1000.0, ge=0, description="Maximum acceptable cost")
    deadline: datetime | None = Field(
        default=None, description="Mission completion deadline"
    )
    priority: Literal["low", "medium", "high", "critical"] = Field(
        default="medium", description="Mission priority"
    )

    # Value
    expected_value: float = Field(
        default=100.0, ge=0, description="Expected value of mission completion"
    )

    created_at: datetime = Field(default_factory=datetime_utcnow)


# =============================================================================
# RESOURCE MARKET MODELS
# =============================================================================


class ResourceOffer(BaseModel):
    """An offer to sell/provide resources."""

    offer_id: str = Field(description="Unique offer identifier")
    agent_id: str = Field(description="Agent offering resources")
    resource_type: Literal[
        "cpu", "memory", "storage", "network", "inference", "planning", "execution"
    ] = Field(description="Type of resource")
    quantity: float = Field(default=100.0, gt=0, description="Quantity of resource")
    asking_price: float = Field(default=10.0, ge=0, description="Price per unit")
    min_quantity: float = Field(
        default=1.0, gt=0, description="Minimum quantity to sell"
    )

    # Validity
    valid_from: datetime = Field(default_factory=datetime_utcnow)
    valid_until: datetime | None = Field(
        default=None, description="When offer expires"
    )

    # Constraints
    can_partial: bool = Field(
        default=True, description="Whether partial quantities are acceptable"
    )

    created_at: datetime = Field(default_factory=datetime_utcnow)


class ResourcePrice(BaseModel):
    """Discovered price for a resource."""

    resource_type: str = Field(description="Type of resource")
    current_price: float = Field(default=10.0, ge=0, description="Current market price")
    price_trend: Literal["rising", "stable", "falling"] = Field(
        default="stable", description="Price trend direction"
    )
    price_volatility: float = Field(
        default=0.1, ge=0.0, le=1.0, description="Price volatility (0=stable, 1=highly volatile)"
    )

    # Market Data
    total_supply: float = Field(default=1000.0, ge=0, description="Total supply")
    total_demand: float = Field(default=500.0, ge=0, description="Total demand")
    supply_demand_ratio: float = Field(
        default=2.0, ge=0, description="Ratio of supply to demand"
    )

    # Statistics
    avg_price_24h: float = Field(default=10.0, ge=0, description="24-hour average price")
    min_price_24h: float = Field(default=8.0, ge=0, description="24-hour minimum price")
    max_price_24h: float = Field(default=12.0, ge=0, description="24-hour maximum price")

    calculated_at: datetime = Field(default_factory=datetime_utcnow)


# =============================================================================
# MISSION BIDDING MODELS
# =============================================================================


class MissionBid(BaseModel):
    """A bid from an agent to complete a mission."""

    bid_id: str = Field(description="Unique bid identifier")
    mission_id: str = Field(description="Mission being bid on")
    agent_id: str = Field(description="Agent making the bid")

    # Bid Details
    bid_cost: float = Field(default=100.0, ge=0, description="Cost to complete mission")
    expected_value: float = Field(
        default=100.0, ge=0, description="Expected value to the network"
    )
    completion_probability: float = Field(
        default=0.9, ge=0.0, le=1.0, description="Probability of completion"
    )
    estimated_duration: timedelta = Field(
        default=timedelta(hours=1), description="Estimated completion time"
    )

    # Resource Usage
    cpu_usage: float = Field(default=10.0, ge=0, description="CPU units to use")
    memory_usage: float = Field(default=1.0, ge=0, description="Memory in GB to use")
    storage_usage: float = Field(default=5.0, ge=0, description="Storage in GB to use")

    # Capability Fit
    specialization_match: float = Field(
        default=0.5, ge=0.0, le=1.0, description="How well specializations match"
    )
    capability_coverage: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Coverage of required capabilities"
    )

    # Constraints
    can_start_before: datetime | None = Field(
        default=None, description="Latest start time for this bid"
    )
    can_complete_by: datetime | None = Field(
        default=None, description="Completion deadline"
    )

    created_at: datetime = Field(default_factory=datetime_utcnow)


# =============================================================================
# MARKET STATE MODELS
# =============================================================================


class AgentMarketState(BaseModel):
    """Current state of the agent resource market."""

    # Supply and Demand
    resource_supply: dict[str, float] = Field(
        default_factory=dict, description="Current supply of each resource"
    )
    resource_demand: dict[str, float] = Field(
        default_factory=dict, description="Current demand for each resource"
    )

    # Prices
    equilibrium_price: dict[str, float] = Field(
        default_factory=dict, description="Equilibrium price for each resource"
    )

    # Market Health
    market_health: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Overall market health score"
    )

    # Agent Counts
    total_agents: int = Field(default=0, ge=0, description="Total registered agents")
    active_agents: int = Field(default=0, ge=0, description="Currently active agents")
    available_agents: int = Field(default=0, ge=0, description="Agents available for work")

    # Market Metrics
    total_supply: float = Field(default=0.0, ge=0, description="Total supply across all resources")
    total_demand: float = Field(default=0.0, ge=0, description="Total demand across all resources")
    supply_demand_gap: float = Field(default=0.0, description="Supply minus demand")

    # Liquidity
    market_liquidity: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Market liquidity score"
    )

    updated_at: datetime = Field(default_factory=datetime_utcnow)


# =============================================================================
# EQUILIBRIUM MODELS
# =============================================================================


class MarketEquilibrium(BaseModel):
    """State of market equilibrium detection."""

    stable: bool = Field(default=False, description="Whether market is in equilibrium")

    # Price Metrics
    price_variance: float = Field(
        default=0.1, ge=0.0, description="Current price variance"
    )
    price_variance_threshold: float = Field(
        default=0.05, ge=0.0, description="Threshold for stability"
    )

    # Supply/Demand Balance
    supply_demand_balance: float = Field(
        default=0.0, ge=-1.0, le=1.0,
        description="Balance between supply and demand (-1=excess demand, +1=excess supply)"
    )

    # Confidence
    equilibrium_confidence: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Confidence in equilibrium assessment"
    )

    # Stability Duration
    stable_for_seconds: float = Field(
        default=0.0, ge=0, description="How long market has been stable"
    )

    # Analysis
    destabilizing_factors: list[str] = Field(
        default_factory=list, description="Factors preventing equilibrium"
    )

    calculated_at: datetime = Field(default_factory=datetime_utcnow)


# =============================================================================
# INCENTIVE MODELS
# =============================================================================


class IncentiveAdjustment(BaseModel):
    """Adjustment to agent incentives for system balance."""

    agent_id: str = Field(description="Agent to adjust")
    adjustment_type: Literal[
        "bonus", "penalty", "subsidy", "tax", "priority_boost", "priority_reduction"
    ] = Field(description="Type of incentive adjustment")

    # Adjustment Values
    resource_adjustment: dict[str, float] = Field(
        default_factory=dict, description="Adjustment per resource type"
    )
    cost_multiplier: float = Field(
        default=1.0, ge=0.0, description="Multiplier for agent costs"
    )
    priority_adjustment: float = Field(
        default=0.0, description="Adjustment to agent priority"
    )

    # Reasoning
    reason: str = Field(default="", description="Reason for adjustment")
    duration: timedelta | None = Field(
        default=None, description="How long adjustment applies"
    )

    expires_at: datetime | None = Field(
        default=None, description="When adjustment expires"
    )

    created_at: datetime = Field(default_factory=datetime_utcnow)


# =============================================================================
# COORDINATION RESULT MODELS
# =============================================================================


class MissionAllocation(BaseModel):
    """Result of mission allocation."""

    mission_id: str = Field(description="Mission allocated")
    allocated_agent: str = Field(description="Agent allocated to mission")
    allocation_cost: float = Field(default=0.0, ge=0, description="Cost of allocation")
    expected_value: float = Field(default=0.0, ge=0, description="Expected value")
    completion_probability: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Probability of completion"
    )

    # Bids Considered
    total_bids: int = Field(default=0, ge=0, description="Total bids received")
    qualified_bids: int = Field(default=0, ge=0, description="Qualified bids considered")

    # Allocation Metrics
    allocation_score: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Overall allocation quality score"
    )
    resource_utilization: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Expected resource utilization"
    )

    allocated_at: datetime = Field(default_factory=datetime_utcnow)


class CoordinationResult(BaseModel):
    """Result of a full coordination cycle."""

    coordination_id: str = Field(description="Unique coordination cycle identifier")
    cycle_number: int = Field(default=0, ge=0, description="Cycle number")

    # Market State
    market_state: AgentMarketState = Field(
        description="Market state after coordination"
    )

    # Equilibrium
    equilibrium: MarketEquilibrium = Field(
        description="Equilibrium assessment"
    )

    # Allocations
    mission_allocations: list[MissionAllocation] = Field(
        default_factory=list, description="Mission allocations made"
    )

    # Incentives
    incentive_adjustments: list[IncentiveAdjustment] = Field(
        default_factory=list, description="Incentive adjustments applied"
    )

    # Prices
    resource_prices: dict[str, ResourcePrice] = Field(
        default_factory=dict, description="Current resource prices"
    )

    # Coordination Metrics
    total_missions_processed: int = Field(
        default=0, ge=0, description="Missions processed"
    )
    total_missions_allocated: int = Field(
        default=0, ge=0, description="Missions successfully allocated"
    )
    total_value_generated: float = Field(
        default=0.0, ge=0, description="Total value generated"
    )
    total_cost_incurred: float = Field(
        default=0.0, ge=0, description="Total cost incurred"
    )

    # System Health
    coordination_health: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Coordination system health"
    )

    # Duration
    coordination_duration_ms: float = Field(
        default=0.0, ge=0, description="Coordination cycle duration"
    )

    started_at: datetime = Field(default_factory=datetime_utcnow)
    completed_at: datetime | None = Field(
        default=None, description="When coordination completed"
    )


# =============================================================================
# ALL EXPORTS
# =============================================================================

__all__ = [
    # Agent and Mission Models
    "AgentCapabilities",
    "AgentRegistration",
    "MissionRequirements",
    # Resource Market Models
    "ResourceOffer",
    "ResourcePrice",
    # Mission Bidding Models
    "MissionBid",
    # Market State Models
    "AgentMarketState",
    # Equilibrium Models
    "MarketEquilibrium",
    # Incentive Models
    "IncentiveAdjustment",
    # Coordination Result Models
    "MissionAllocation",
    "CoordinationResult",
    # Utility
    "datetime_utcnow",
]
