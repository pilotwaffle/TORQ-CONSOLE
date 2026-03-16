"""TORQ Layer 17 - Test Configuration

Shared pytest fixtures for Layer 17 testing.

Layer 17 integrates with Layer 16 Economic Coordination, so this
conftest provides fixtures for both layers.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from typing import AsyncGenerator

from torq_console.layer17.models import AgentGenome, GenomeStatus
from torq_console.layer17.services import AgentRegistry, create_agent_registry
from torq_console.layer17.mutation import MutationEngine, create_mutation_engine
from torq_console.layer17.evaluation import EvaluationHarness, create_evaluation_harness
from torq_console.layer17.evaluation.benchmark_missions import get_benchmark_missions

# Layer 16 imports for integration testing
# Verified import paths from VERIFIED_L16_SOURCES.md:
# - Service: from torq_console.layer16.services import create_economic_coordination_service
# - Models: from torq_console.layer16.models import ...

from torq_console.layer16 import EconomicCoordinationService
from torq_console.layer16.services import create_economic_coordination_service
from torq_console.layer16.models import (
    AgentRegistration,
    AgentCapabilities,
    MissionRequirements,
    MissionBid,
    ResourceOffer,
    AgentMarketState,
    CoordinationResult,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def sample_genome() -> AgentGenome:
    """Create a sample agent genome for testing."""
    return AgentGenome(
        genome_id="test_genome_001",
        parent_genome_id=None,
        generation=0,
        status=GenomeStatus.EXPERIMENTAL,
        toolset=["web_search", "code_executor", "file_read"],
        min_toolset_size=3,
        max_toolset_size=10,
        llm_model="claude-sonnet-4-6",
        llm_temperature=0.7,
        llm_max_tokens=4096,
        missions_completed=10,
        missions_attempted=12,
        total_value_generated=5000.0,
        total_cost_incurred=2000.0,
        fitness_score=0.75,
        completion_rate=0.83,
        efficiency_score=0.8,
        reliability_score=0.9,
    )


@pytest.fixture
def agent_registry():
    """Create an agent registry instance."""
    return create_agent_registry()


@pytest.fixture
def mutation_engine():
    """Create a mutation engine instance."""
    return create_mutation_engine(seed=42)  # Fixed seed for deterministic tests


@pytest.fixture
def evaluation_harness():
    """Create an evaluation harness with loaded benchmarks."""
    harness = create_evaluation_harness()
    harness.load_benchmarks(get_benchmark_missions())
    return harness


# =============================================================================
# LAYER 16 INTEGRATION FIXTURES
# =============================================================================


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def l16_coordination_service() -> AsyncGenerator[EconomicCoordinationService, None]:
    """Provide a Layer 16 coordination service for testing.

    Uses verified import path from VERIFIED_L16_SOURCES.md:
    from torq_console.layer16.services import create_economic_coordination_service

    All methods are async per verified sources.
    """
    service = create_economic_coordination_service()
    yield service
    # No explicit cleanup needed - in-memory only


@pytest.fixture
async def populated_l16_service() -> AsyncGenerator[EconomicCoordinationService, None]:
    """Provide a populated L16 service with agents and missions.

    Uses ONLY verified fields from VERIFIED_L16_MODELS.md:

    AgentCapabilities fields:
        agent_id, agent_type, cpu_capacity, memory_capacity, storage_capacity,
        network_bandwidth, can_inference, can_plan, can_execute, can_monitor,
        specializations, cost_per_cpu_unit, cost_per_memory_gb, base_hourly_rate,
        reliability_score, avg_completion_time, current_load

    MissionRequirements fields:
        mission_id, mission_type, required_cpu, required_memory, required_storage,
        required_network, requires_inference, requires_planning, requires_execution,
        requires_monitoring, required_specializations, max_cost, deadline, priority,
        expected_value

    MissionBid fields:
        bid_id, mission_id, agent_id, bid_cost, expected_value,
        completion_probability, estimated_duration, cpu_usage, memory_usage,
        storage_usage, specialization_match, capability_coverage, can_start_before,
        can_complete_by

    ResourceOffer fields:
        offer_id, agent_id, resource_type, quantity, asking_price,
        min_quantity, valid_from, valid_until, can_partial
    """
    service = create_economic_coordination_service()

    # Register specialist agent using verified fields
    specialist_caps = AgentCapabilities(
        agent_id="specialist_1",
        agent_type="specialist",
        cpu_capacity=100.0,
        memory_capacity=8.0,
        storage_capacity=50.0,
        network_bandwidth=1000.0,
        can_inference=True,
        can_plan=True,
        can_execute=True,
        can_monitor=True,
        specializations=["trading", "analysis"],
        cost_per_cpu_unit=1.0,
        cost_per_memory_gb=0.5,
        base_hourly_rate=10.0,
        reliability_score=0.95,
        avg_completion_time=60.0,
        current_load=0.3,
    )

    await service.register_agent(AgentRegistration(
        agent_id="specialist_1",
        agent_type="specialist",
        capabilities=specialist_caps,
    ))

    # Register generalist agent using verified fields
    generalist_caps = AgentCapabilities(
        agent_id="generalist_1",
        agent_type="generalist",
        cpu_capacity=150.0,
        memory_capacity=16.0,
        storage_capacity=100.0,
        network_bandwidth=1000.0,
        can_execute=True,
        can_monitor=True,
        specializations=[],
        cost_per_cpu_unit=0.8,
        cost_per_memory_gb=0.3,
        base_hourly_rate=8.0,
        reliability_score=0.85,
        avg_completion_time=90.0,
        current_load=0.2,
    )

    await service.register_agent(AgentRegistration(
        agent_id="generalist_1",
        agent_type="generalist",
        capabilities=generalist_caps,
    ))

    # Submit resource offers using verified fields
    await service.submit_resource_offer(ResourceOffer(
        offer_id="offer_cpu_1",
        agent_id="specialist_1",
        resource_type="cpu",
        quantity=70.0,
        asking_price=5.0,
        min_quantity=1.0,
        can_partial=True,
    ))

    await service.submit_resource_offer(ResourceOffer(
        offer_id="offer_cpu_2",
        agent_id="generalist_1",
        resource_type="cpu",
        quantity=120.0,
        asking_price=4.0,
        min_quantity=1.0,
        can_partial=True,
    ))

    # Submit a mission using verified fields
    mission = MissionRequirements(
        mission_id="test_mission_1",
        mission_type="trading_analysis",
        required_cpu=20.0,
        required_memory=2.0,
        required_storage=5.0,
        required_network=100.0,
        requires_inference=True,
        requires_planning=False,
        requires_execution=True,
        requires_monitoring=False,
        required_specializations=["trading"],
        max_cost=500.0,
        deadline=None,
        priority="high",
        expected_value=1000.0,
    )

    await service.submit_mission(mission)

    # Submit bids using verified fields
    await service.submit_mission_bid(MissionBid(
        bid_id="bid_specialist",
        mission_id="test_mission_1",
        agent_id="specialist_1",
        bid_cost=200.0,
        expected_value=950.0,
        completion_probability=0.95,
        estimated_duration=timedelta(hours=2),
        cpu_usage=20.0,
        memory_usage=2.0,
        storage_usage=5.0,
        specialization_match=1.0,
        capability_coverage=1.0,
        can_start_before=None,
        can_complete_by=None,
    ))

    await service.submit_mission_bid(MissionBid(
        bid_id="bid_generalist",
        mission_id="test_mission_1",
        agent_id="generalist_1",
        bid_cost=150.0,
        expected_value=700.0,
        completion_probability=0.85,
        estimated_duration=timedelta(hours=3),
        cpu_usage=20.0,
        memory_usage=2.0,
        storage_usage=5.0,
        specialization_match=0.0,
        capability_coverage=0.8,
        can_start_before=None,
        can_complete_by=None,
    ))

    yield service


@pytest.fixture
def sample_l16_market_state() -> AgentMarketState:
    """Provide a sample AgentMarketState using verified fields.

    AgentMarketState verified fields:
        resource_supply, resource_demand, equilibrium_price, market_health,
        total_agents, active_agents, available_agents, total_supply,
        total_demand, supply_demand_gap, market_liquidity, updated_at
    """
    return AgentMarketState(
        resource_supply={"cpu": 400.0, "memory": 32.0, "inference": 2.0},
        resource_demand={"cpu": 350.0, "memory": 24.0, "inference": 1.5},
        equilibrium_price={"cpu": 5.0, "memory": 2.5, "inference": 10.0},
        market_health=0.85,
        total_agents=5,
        active_agents=4,
        available_agents=3,
        total_supply=434.0,
        total_demand=375.5,
        supply_demand_gap=58.5,
        market_liquidity=0.8,
    )


# =============================================================================
# TEST HELPERS
# =============================================================================


def create_test_genome(
    genome_id: str = "test_genome",
    toolset: list[str] | None = None,
) -> AgentGenome:
    """Helper to create test genomes.

    Args:
        genome_id: Unique identifier
        toolset: Optional tool list (defaults to basic tools)

    Returns:
        AgentGenome instance
    """
    if toolset is None:
        toolset = ["web_search", "file_read"]

    return AgentGenome(
        genome_id=genome_id,
        parent_genome_id=None,
        generation=0,
        status=GenomeStatus.EXPERIMENTAL,
        toolset=toolset,
        min_toolset_size=2,
        max_toolset_size=10,
        llm_model="claude-sonnet-4-6",
    )


def assert_valid_l16_signal(signal) -> None:
    """Assert L16EcosystemSignal uses only verified L16 fields.

    Checks against VERIFIED_L16_SOURCES.md producer methods.
    """
    from torq_console.layer17.models import L16EcosystemSignal

    assert isinstance(signal, L16EcosystemSignal)
    assert signal.total_agents >= 0
    assert signal.active_agents >= 0
    assert 0.0 <= signal.market_health <= 1.0
    assert signal.total_missions_processed >= 0
    assert signal.total_missions_allocated >= 0
    assert 0.0 <= signal.allocation_success_rate <= 1.0
    assert 0.0 <= signal.equilibrium_confidence <= 1.0


# =============================================================================
# PYTEST HOOKS
# =============================================================================


def pytest_collection_modifyitems(config, items):
    """Add markers to Layer 17 tests."""
    for item in items:
        # Add asyncio marker to async tests
        if asyncio.iscoroutinefunction(item.obj):
            item.add_marker("asyncio")

        # Add layer17 marker
        if "layer17" in str(item.fspath):
            item.add_marker("layer17")
            item.add_marker("integration")
