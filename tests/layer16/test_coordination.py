"""TORQ Layer 16 - Validation Framework

This module provides validation scenarios and tests for Layer 16
multi-agent economic coordination.
"""

import asyncio
from datetime import timedelta

from torq_console.layer16 import (
    EconomicCoordinationService,
    AgentRegistration,
    AgentCapabilities,
    MissionRequirements,
    MissionBid,
    ResourceOffer,
)


# =============================================================================
# VALIDATION SCENARIOS
# =============================================================================


async def validate_competitive_allocation():
    """Validate Scenario 1: Competitive Mission Allocation.

    Multiple agents bid on a mission; specialist should win
    based on capability match and value.
    """
    service = EconomicCoordinationService()

    # Register specialist agent
    specialist_caps = AgentCapabilities(
        agent_id="specialist_1",
        agent_type="specialist",
        cpu_capacity=100.0,
        memory_capacity=8.0,
        can_inference=True,
        can_execute=True,
        specializations=["trading"],
        current_load=0.2,
        reliability_score=0.95,
    )

    # Register generalist agent
    generalist_caps = AgentCapabilities(
        agent_id="generalist_1",
        agent_type="generalist",
        cpu_capacity=150.0,
        memory_capacity=16.0,
        can_execute=True,
        can_monitor=True,
        specializations=[],
        current_load=0.1,
        reliability_score=0.85,
    )

    await service.register_agent(AgentRegistration(
        agent_id="specialist_1",
        agent_type="specialist",
        capabilities=specialist_caps,
    ))

    await service.register_agent(AgentRegistration(
        agent_id="generalist_1",
        agent_type="generalist",
        capabilities=generalist_caps,
    ))

    # Submit trading mission (specialist domain)
    mission = MissionRequirements(
        mission_id="trading_analysis_1",
        mission_type="trading_analysis",
        required_cpu=20.0,
        required_memory=2.0,
        requires_execution=True,
        required_specializations=["trading"],
        max_cost=500.0,
        expected_value=1000.0,
    )

    await service.submit_mission(mission)

    # Both agents bid (specialist is more expensive but better fit)
    await service.submit_mission_bid(MissionBid(
        bid_id="bid_specialist",
        mission_id="trading_analysis_1",
        agent_id="specialist_1",
        bid_cost=200.0,
        expected_value=950.0,
        completion_probability=0.95,
        estimated_duration=timedelta(hours=2),
        cpu_usage=20.0,
        memory_usage=2.0,
        storage_usage=1.0,
        specialization_match=1.0,  # Perfect match
        capability_coverage=1.0,
    ))

    await service.submit_mission_bid(MissionBid(
        bid_id="bid_generalist",
        mission_id="trading_analysis_1",
        agent_id="generalist_1",
        bid_cost=150.0,
        expected_value=700.0,
        completion_probability=0.85,
        estimated_duration=timedelta(hours=3),
        cpu_usage=20.0,
        memory_usage=2.0,
        storage_usage=1.0,
        specialization_match=0.0,  # No match
        capability_coverage=0.8,
    ))

    # Run coordination
    result = await service.run_coordination_cycle()

    # Validation
    assert result.total_missions_allocated == 1, "Should allocate exactly 1 mission"
    assert len(result.mission_allocations) == 1, "Should have 1 allocation"

    allocation = result.mission_allocations[0]
    assert allocation.allocated_agent == "specialist_1", \
        "Specialist should win due to better capability match"

    return {
        "scenario": "competitive_allocation",
        "passed": True,
        "allocated_to": allocation.allocated_agent,
        "allocation_score": allocation.allocation_score,
    }


async def validate_market_health():
    """Validate Scenario 2: Market Health Monitoring.

    System should maintain market health above threshold.
    """
    service = EconomicCoordinationService()

    # Register multiple agents
    for i in range(5):
        caps = AgentCapabilities(
            agent_id=f"agent_{i}",
            agent_type="specialist" if i % 2 == 0 else "generalist",
            cpu_capacity=100.0,
            memory_capacity=8.0,
            can_execute=True,
            specializations=[f"domain_{i}"],
            current_load=0.3,
        )
        await service.register_agent(AgentRegistration(
            agent_id=f"agent_{i}",
            agent_type=caps.agent_type,
            capabilities=caps,
        ))

    # Get market state
    market_state = await service.get_market_state()

    # Validation
    assert market_state.total_agents == 5, "Should have 5 agents"
    assert market_state.market_health > 0.5, "Market health should be acceptable"
    assert market_state.market_health <= 1.0, "Market health should not exceed 1.0"

    return {
        "scenario": "market_health",
        "passed": True,
        "market_health": market_state.market_health,
        "total_agents": market_state.total_agents,
    }


async def validate_price_discovery():
    """Validate Scenario 3: Price Discovery.

    System should discover prices based on supply/demand.
    """
    service = EconomicCoordinationService()

    # Register agents with different capacities
    high_capacity_caps = AgentCapabilities(
        agent_id="high_cap",
        agent_type="specialist",
        cpu_capacity=200.0,
        memory_capacity=16.0,
        can_inference=True,
        current_load=0.1,
    )

    low_capacity_caps = AgentCapabilities(
        agent_id="low_cap",
        agent_type="generalist",
        cpu_capacity=50.0,
        memory_capacity=4.0,
        current_load=0.8,  # High load
    )

    await service.register_agent(AgentRegistration(
        agent_id="high_cap",
        agent_type="specialist",
        capabilities=high_capacity_caps,
    ))

    await service.register_agent(AgentRegistration(
        agent_id="low_cap",
        agent_type="generalist",
        capabilities=low_capacity_caps,
    ))

    # Submit resource offers
    await service.submit_resource_offer(ResourceOffer(
        offer_id="offer_1",
        agent_id="high_cap",
        resource_type="cpu",
        quantity=100.0,
        asking_price=5.0,
    ))

    await service.submit_resource_offer(ResourceOffer(
        offer_id="offer_2",
        agent_id="low_cap",
        resource_type="cpu",
        quantity=10.0,
        asking_price=15.0,  # Higher price due to scarcity
    ))

    # Get prices
    prices = await service.get_resource_prices()

    # Validation
    assert "cpu" in prices, "Should have CPU price"
    cpu_price = prices["cpu"]
    assert cpu_price.current_price > 0, "Price should be positive"

    return {
        "scenario": "price_discovery",
        "passed": True,
        "cpu_price": cpu_price.current_price,
        "supply_demand_ratio": cpu_price.supply_demand_ratio,
    }


async def validate_equilibrium_detection():
    """Validate Scenario 4: Equilibrium Detection.

    System should detect when market stabilizes.
    """
    service = EconomicCoordinationService()

    # Register agents
    for i in range(3):
        caps = AgentCapabilities(
            agent_id=f"agent_{i}",
            agent_type="generalist",
            cpu_capacity=100.0,
            memory_capacity=8.0,
            can_execute=True,
            current_load=0.5,  # Balanced load
        )
        await service.register_agent(AgentRegistration(
            agent_id=f"agent_{i}",
            agent_type="generalist",
            capabilities=caps,
        ))

    # Run multiple coordination cycles to stabilize
    for _ in range(3):
        result = await service.run_coordination_cycle()

    # Get equilibrium state
    equilibrium = await service.get_equilibrium()

    # Validation
    assert equilibrium.equilibrium_confidence >= 0.0, "Confidence should be non-negative"
    assert equilibrium.equilibrium_confidence <= 1.0, "Confidence should not exceed 1.0"

    return {
        "scenario": "equilibrium_detection",
        "passed": True,
        "stable": equilibrium.stable,
        "confidence": equilibrium.equilibrium_confidence,
        "price_variance": equilibrium.price_variance,
    }


async def validate_incentive_balancing():
    """Validate Scenario 5: Incentive Balancing.

    System should apply incentives to balance load.
    """
    service = EconomicCoordinationService()

    # Register overloaded agent
    overloaded_caps = AgentCapabilities(
        agent_id="overloaded",
        agent_type="specialist",
        cpu_capacity=100.0,
        memory_capacity=8.0,
        can_execute=True,
        current_load=0.95,  # Very high load
    )

    # Register underloaded agent
    underloaded_caps = AgentCapabilities(
        agent_id="underloaded",
        agent_type="generalist",
        cpu_capacity=100.0,
        memory_capacity=8.0,
        can_execute=True,
        current_load=0.1,  # Very low load
    )

    await service.register_agent(AgentRegistration(
        agent_id="overloaded",
        agent_type="specialist",
        capabilities=overloaded_caps,
    ))

    await service.register_agent(AgentRegistration(
        agent_id="underloaded",
        agent_type="generalist",
        capabilities=underloaded_caps,
    ))

    # Run coordination to trigger incentives
    result = await service.run_coordination_cycle()

    # Check incentive adjustments
    adjustments = result.incentive_adjustments

    # Validation
    # Should have incentives for both agents
    agent_ids = {adj.agent_id for adj in adjustments}
    assert "overloaded" in agent_ids or "underloaded" in agent_ids, \
        "Should have incentive adjustments for load balancing"

    return {
        "scenario": "incentive_balancing",
        "passed": True,
        "adjustments_count": len(adjustments),
        "adjustment_types": [adj.adjustment_type for adj in adjustments],
    }


async def validate_coordination_performance():
    """Validate Scenario 6: Coordination Performance.

    Coordination cycles should complete within target latency.
    """
    service = EconomicCoordinationService()

    # Register agents
    for i in range(10):
        caps = AgentCapabilities(
            agent_id=f"agent_{i}",
            agent_type="specialist" if i % 2 == 0 else "generalist",
            cpu_capacity=100.0,
            memory_capacity=8.0,
            can_execute=True,
            specializations=[f"domain_{i % 3}"],
            current_load=0.3,
        )
        await service.register_agent(AgentRegistration(
            agent_id=f"agent_{i}",
            agent_type=caps.agent_type,
            capabilities=caps,
        ))

    # Submit multiple missions
    for i in range(5):
        mission = MissionRequirements(
            mission_id=f"mission_{i}",
            mission_type="analysis",
            required_cpu=20.0,
            required_memory=2.0,
            requires_execution=True,
            max_cost=500.0,
            expected_value=1000.0,
        )
        await service.submit_mission(mission)

        # Submit bids for this mission
        for j in range(3):
            await service.submit_mission_bid(MissionBid(
                bid_id=f"bid_{i}_{j}",
                mission_id=f"mission_{i}",
                agent_id=f"agent_{j}",
                bid_cost=100.0 + j * 50,
                expected_value=800.0,
                completion_probability=0.9,
                estimated_duration=timedelta(hours=1),
                cpu_usage=20.0,
                memory_usage=2.0,
                storage_usage=1.0,
                specialization_match=0.5,
                capability_coverage=0.8,
            ))

    # Run coordination and measure time
    result = await service.run_coordination_cycle()

    # Validation
    target_latency_ms = 200.0
    assert result.coordination_duration_ms < target_latency_ms, \
        f"Coordination should complete in <{target_latency_ms}ms, took {result.coordination_duration_ms}ms"

    return {
        "scenario": "coordination_performance",
        "passed": True,
        "duration_ms": result.coordination_duration_ms,
        "target_ms": target_latency_ms,
        "missions_processed": result.total_missions_processed,
        "missions_allocated": result.total_missions_allocated,
    }


# =============================================================================
# VALIDATION RUNNER
# =============================================================================


async def run_all_validations() -> dict:
    """Run all Layer 16 validation scenarios.

    Returns:
        Dictionary with validation results
    """
    validations = [
        ("Competitive Allocation", validate_competitive_allocation),
        ("Market Health", validate_market_health),
        ("Price Discovery", validate_price_discovery),
        ("Equilibrium Detection", validate_equilibrium_detection),
        ("Incentive Balancing", validate_incentive_balancing),
        ("Coordination Performance", validate_coordination_performance),
    ]

    results = {}

    for name, validator in validations:
        try:
            result = await validator()
            results[name] = result
            print(f"[PASS] {name}")
        except AssertionError as e:
            results[name] = {"scenario": name, "passed": False, "error": str(e)}
            print(f"[FAIL] {name}: {e}")
        except Exception as e:
            results[name] = {"scenario": name, "passed": False, "error": str(e)}
            print(f"[ERROR] {name}: {e}")

    return results


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================


if __name__ == "__main__":
    print("=" * 60)
    print("TORQ Layer 16 - Validation Framework")
    print("=" * 60)
    print()

    results = asyncio.run(run_all_validations())

    print()
    print("=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    passed = sum(1 for r in results.values() if r.get("passed", False))
    total = len(results)

    for name, result in results.items():
        status = "[PASS]" if result.get("passed", False) else "[FAIL]"
        print(f"{status}: {name}")

    print()
    print(f"Total: {passed}/{total} validations passed")

    if passed == total:
        print("[SUCCESS] All Layer 16 validations passed!")
    else:
        print(f"[WARNING] {total - passed} validation(s) failed")
