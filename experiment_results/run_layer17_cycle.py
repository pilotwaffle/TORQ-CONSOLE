"""TORQ Layer 17 - Cycle 001 Execution

Execute one real Layer 17 cycle using live L16-backed signals.
This script performs:
1. Creates L16 service with real agents
2. Submits resource offers and missions
3. Runs coordination cycle to generate live market state
4. Collects L16 signal using L16SignalCollector
5. Creates founder genome
6. Mutates genome based on L16 ecosystem state
7. Runs benchmark evaluation
8. Makes promote/retire decision
9. Persists all outputs
10. Documents results
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from torq_console.layer16.services import create_economic_coordination_service
from torq_console.layer16.models import (
    AgentRegistration,
    AgentCapabilities,
    ResourceOffer,
    MissionRequirements,
    MissionBid,
)

from torq_console.layer17.services import (
    create_agent_registry,
    create_signal_collector,
)
from torq_console.layer17.models import (
    AgentGenome,
    GenomeStatus,
)
from torq_console.layer17.mutation import create_mutation_engine
from torq_console.layer17.evaluation import create_evaluation_harness
from torq_console.layer17.evaluation.benchmark_missions import get_benchmark_missions


async def run_cycle_001():
    """Execute Layer 17 Cycle 001 with live L16 signals."""

    print("=" * 70)
    print("TORQ LAYER 17 - CYCLE 001 EXECUTION")
    print(f"Started: {datetime.utcnow().isoformat()}")
    print("=" * 70)

    # ========================================================================
    # STEP 1: Create L16 Service and Register Agents
    # ========================================================================
    print("\n[STEP 1] Creating L16 Economic Coordination Service...")

    service = create_economic_coordination_service()

    # Register Trading Specialist Agent
    print("  - Registering trading_specialist_001...")
    specialist_caps = AgentCapabilities(
        agent_id="trading_specialist_001",
        agent_type="specialist",
        cpu_capacity=80.0,
        memory_capacity=16.0,
        storage_capacity=100.0,
        network_bandwidth=1000.0,
        can_inference=True,
        can_plan=True,
        can_execute=True,
        can_monitor=True,
        specializations=["crypto_trading", "technical_analysis", "risk_management"],
        cost_per_cpu_unit=2.0,
        cost_per_memory_gb=0.8,
        base_hourly_rate=25.0,
        reliability_score=0.92,
        avg_completion_time=45.0,
        current_load=0.25,
    )

    await service.register_agent(AgentRegistration(
        agent_id="trading_specialist_001",
        agent_type="specialist",
        capabilities=specialist_caps,
    ))

    # Register Generalist Agent
    print("  - Registering generalist_001...")
    generalist_caps = AgentCapabilities(
        agent_id="generalist_001",
        agent_type="generalist",
        cpu_capacity=200.0,
        memory_capacity=32.0,
        storage_capacity=500.0,
        network_bandwidth=2000.0,
        can_execute=True,
        can_monitor=True,
        specializations=[],
        cost_per_cpu_unit=1.5,
        cost_per_memory_gb=0.5,
        base_hourly_rate=15.0,
        reliability_score=0.88,
        avg_completion_time=60.0,
        current_load=0.4,
    )

    await service.register_agent(AgentRegistration(
        agent_id="generalist_001",
        agent_type="generalist",
        capabilities=generalist_caps,
    ))

    print(f"  [OK] Registered 2 agents")

    # ========================================================================
    # STEP 2: Submit Resource Offers
    # ========================================================================
    print("\n[STEP 2] Submitting resource offers...")

    await service.submit_resource_offer(ResourceOffer(
        offer_id="offer_cpu_specialist_001",
        agent_id="trading_specialist_001",
        resource_type="cpu",
        quantity=60.0,
        asking_price=6.0,
        min_quantity=5.0,
        can_partial=True,
    ))

    await service.submit_resource_offer(ResourceOffer(
        offer_id="offer_cpu_generalist_001",
        agent_id="generalist_001",
        resource_type="cpu",
        quantity=120.0,
        asking_price=4.5,
        min_quantity=10.0,
        can_partial=True,
    ))

    await service.submit_resource_offer(ResourceOffer(
        offer_id="offer_memory_specialist_001",
        agent_id="trading_specialist_001",
        resource_type="memory",
        quantity=12.0,
        asking_price=1.5,
        min_quantity=1.0,
        can_partial=True,
    ))

    print(f"  [OK] Submitted 3 resource offers")

    # ========================================================================
    # STEP 3: Submit Missions and Bids
    # ========================================================================
    print("\n[STEP 3] Submitting missions...")

    mission_1 = MissionRequirements(
        mission_id="crypto_analysis_mission_001",
        mission_type="crypto_market_analysis",
        required_cpu=30.0,
        required_memory=4.0,
        required_storage=10.0,
        required_network=500.0,
        requires_inference=True,
        requires_planning=True,
        requires_execution=True,
        requires_monitoring=True,
        required_specializations=["crypto_trading"],
        max_cost=200.0,
        deadline=datetime.utcnow() + timedelta(hours=4),
        priority="high",
        expected_value=500.0,
    )

    await service.submit_mission(mission_1)
    print(f"  [OK] Submitted mission: {mission_1.mission_id}")

    # Submit bids
    await service.submit_mission_bid(MissionBid(
        bid_id="bid_specialist_001",
        mission_id="crypto_analysis_mission_001",
        agent_id="trading_specialist_001",
        bid_cost=120.0,
        expected_value=480.0,
        completion_probability=0.95,
        estimated_duration=timedelta(hours=2),
        cpu_usage=30.0,
        memory_usage=4.0,
        storage_usage=10.0,
        specialization_match=1.0,
        capability_coverage=1.0,
    ))

    await service.submit_mission_bid(MissionBid(
        bid_id="bid_generalist_001",
        mission_id="crypto_analysis_mission_001",
        agent_id="generalist_001",
        bid_cost=90.0,
        expected_value=350.0,
        completion_probability=0.82,
        estimated_duration=timedelta(hours=3),
        cpu_usage=30.0,
        memory_usage=4.0,
        storage_usage=10.0,
        specialization_match=0.3,
        capability_coverage=0.9,
    ))

    print(f"  [OK] Submitted 2 bids")

    # ========================================================================
    # STEP 4: Run Coordination Cycle (Generate Live Market State)
    # ========================================================================
    print("\n[STEP 4] Running L16 coordination cycle...")

    coordination_result = await service.run_coordination_cycle()

    print(f"  [OK] Coordination cycle complete")
    print(f"       - Coordination ID: {coordination_result.coordination_id}")
    print(f"       - Cycle Number: {coordination_result.cycle_number}")
    print(f"       - Missions Allocated: {len(coordination_result.mission_allocations)}")
    print(f"       - Coordination Health: {coordination_result.coordination_health:.2f}")

    # ========================================================================
    # STEP 5: Collect L16 Ecosystem Signal
    # ========================================================================
    print("\n[STEP 5] Collecting L16 ecosystem signal...")

    collector = create_signal_collector(service)
    signal = await collector.collect()

    print(f"  [OK] Signal collected: {signal.signal_id}")
    print(f"       - Total Agents: {signal.total_agents}")
    print(f"       - Active Agents: {signal.active_agents}")
    print(f"       - Market Health: {signal.market_health:.2f}")
    print(f"       - Market Stable: {signal.market_stable}")
    print(f"       - Supply/Demand Gap: {signal.supply_demand_gap:.2f}")
    print(f"       - Missions Processed: {signal.total_missions_processed}")
    print(f"       - Missions Allocated: {signal.total_missions_allocated}")

    # ========================================================================
    # STEP 6: Create Founder Genome
    # ========================================================================
    print("\n[STEP 6] Creating founder genome...")

    founder_genome = AgentGenome(
        genome_id="genome_founder_001",
        parent_genome_id=None,
        generation=0,
        status=GenomeStatus.EXPERIMENTAL,
        toolset=["web_search", "code_executor", "file_read", "data_analyzer"],
        min_toolset_size=3,
        max_toolset_size=10,
        llm_model="claude-sonnet-4-6",
        llm_temperature=0.7,
        llm_max_tokens=4096,
    )

    registry = create_agent_registry()
    genome_id = await registry.register_genome(founder_genome)

    print(f"  [OK] Founder genome created: {genome_id}")
    print(f"       - Toolset: {founder_genome.toolset}")
    print(f"       - LLM Model: {founder_genome.llm_model}")

    # ========================================================================
    # STEP 7: Mutate Genome Based on L16 Ecosystem State
    # ========================================================================
    print("\n[STEP 7] Mutating genome based on L16 ecosystem state...")

    mutation_engine = create_mutation_engine(seed=42)
    # Use signal market health to influence mutation rate
    # Higher market health = lower mutation rate (conservative)
    # Lower market health = higher mutation rate (exploratory)
    mutation_rate = max(0.05, min(0.5, 1.0 - signal.market_health))
    child_genome = await mutation_engine.mutate_genome(founder_genome, mutation_rate=mutation_rate)

    print(f"  [OK] Child genome created: {child_genome.genome_id}")
    print(f"       - Generation: {child_genome.generation}")
    print(f"       - Parent: {child_genome.parent_genome_id}")
    print(f"       - Mutation Rate: {mutation_rate:.2f}")

    # Show what changed
    if child_genome.toolset != founder_genome.toolset:
        added = set(child_genome.toolset) - set(founder_genome.toolset)
        removed = set(founder_genome.toolset) - set(child_genome.toolset)
        if added:
            print(f"       - Tools Added: {list(added)}")
        if removed:
            print(f"       - Tools Removed: {list(removed)}")

    # Register child genome
    await registry.register_genome(child_genome)

    # ========================================================================
    # STEP 8: Run Benchmark Evaluation
    # ========================================================================
    print("\n[STEP 8] Running benchmark evaluation...")

    harness = create_evaluation_harness()
    harness.load_benchmarks(get_benchmark_missions())

    evaluation_result = await harness.run_benchmark_suite(child_genome)

    print(f"  [OK] Evaluation complete")
    print(f"       - Benchmark Count: {evaluation_result.benchmark_count}")
    print(f"       - Passed: {evaluation_result.passed}")
    print(f"       - Completion Score: {evaluation_result.completion_score:.2f}")
    print(f"       - Latency Score: {evaluation_result.latency_score:.2f}")
    print(f"       - Consistency Score: {evaluation_result.consistency_score:.2f}")
    print(f"       - Overall Score: {evaluation_result.overall_score:.2f}")
    print(f"       - Duration: {evaluation_result.evaluation_duration_ms:.0f}ms")

    # ========================================================================
    # STEP 9: Make Promote/Retire Decision
    # ========================================================================
    print("\n[STEP 9] Making promote/retire decision...")

    BETA_THRESHOLD = 0.75

    passed = evaluation_result.overall_score >= BETA_THRESHOLD

    if passed:
        child_genome.status = GenomeStatus.PRODUCTION
        child_genome.benchmark_passed = True
        decision = "PROMOTE TO PRODUCTION"
    else:
        child_genome.status = GenomeStatus.RETIRED
        child_genome.benchmark_passed = False
        child_genome.retired_at = datetime.utcnow()
        decision = "RETIRE"

    # Update fitness scores
    child_genome.benchmark_overall_score = evaluation_result.overall_score
    child_genome.benchmark_completion_score = evaluation_result.completion_score
    child_genome.benchmark_latency_score = evaluation_result.latency_score
    child_genome.benchmark_consistency_score = evaluation_result.consistency_score

    await registry.update_fitness(child_genome.genome_id, evaluation_result.overall_score)

    print(f"  [DECISION] {decision}")
    print(f"       - Threshold: {BETA_THRESHOLD}")
    print(f"       - Score: {evaluation_result.overall_score:.2f}")
    print(f"       - New Status: {child_genome.status.value}")

    # ========================================================================
    # STEP 10: Generate Experiment Report
    # ========================================================================
    print("\n[STEP 10] Generating experiment report...")

    report_content = f"""# Layer 17 Cycle 001 Execution Report

**Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
**Status:** {'PASSED' if passed else 'FAILED'}
**Decision:** {decision}

---

## Executive Summary

Layer 17 Cycle 001 completed successfully with live L16 ecosystem signals.
The evaluation resulted in **{decision}** based on benchmark performance.

- **Founder Genome:** genome_founder_001
- **Child Genome:** {child_genome.genome_id}
- **Overall Score:** {evaluation_result.overall_score:.2f}
- **Threshold:** {BETA_THRESHOLD}
- **Result:** {'PASSED' if passed else 'FAILED'}

---

## L16 Ecosystem State

Live market state collected from Layer 16 Economic Coordination:

| Metric | Value |
|--------|-------|
| Total Agents | {signal.total_agents} |
| Active Agents | {signal.active_agents} |
| Market Health | {signal.market_health:.2f} |
| Market Stable | {signal.market_stable} |
| Supply/Demand Gap | {signal.supply_demand_gap:.2f} |
| Missions Processed | {signal.total_missions_processed} |
| Missions Allocated | {signal.total_missions_allocated} |
| Allocation Success Rate | {signal.allocation_success_rate:.2f} |
| Equilibrium Confidence | {signal.equilibrium_confidence:.2f} |

### Resource Supply
```json
{{"cpu": {signal.resource_supply.get("cpu", 0)}, "memory": {signal.resource_supply.get("memory", 0)}}}
```

### Resource Demand
```json
{{"cpu": {signal.resource_demand.get("cpu", 0)}, "memory": {signal.resource_demand.get("memory", 0)}}}
```

---

## Genome Evolution

### Founder Genome (Generation 0)
- **Genome ID:** {founder_genome.genome_id}
- **Toolset:** {founder_genome.toolset}
- **LLM Model:** {founder_genome.llm_model}
- **Temperature:** {founder_genome.llm_temperature}
- **Max Tokens:** {founder_genome.llm_max_tokens}

### Child Genome (Generation {child_genome.generation})
- **Genome ID:** {child_genome.genome_id}
- **Parent:** {child_genome.parent_genome_id}
- **Toolset:** {child_genome.toolset}
- **LLM Model:** {child_genome.llm_model}
- **Temperature:** {child_genome.llm_temperature}
- **Status:** {child_genome.status.value}

### Mutations Applied
- **Mutation Rate:** {mutation_rate:.2f} (based on L16 market health: {signal.market_health:.2f})
- **Deterministic Seed:** 42

---

## Benchmark Results

| Benchmark | Status | Score |
|-----------|--------|-------|
| Completion | {evaluation_result.completion_score:.2f} | {'PASS' if evaluation_result.completion_score >= BETA_THRESHOLD else 'FAIL'} |
| Latency | {evaluation_result.latency_score:.2f} | {'PASS' if evaluation_result.latency_score >= BETA_THRESHOLD else 'FAIL'} |
| Consistency | {evaluation_result.consistency_score:.2f} | {'PASS' if evaluation_result.consistency_score >= BETA_THRESHOLD else 'FAIL'} |
| **OVERALL** | **{evaluation_result.overall_score:.2f}** | **{'PASS' if passed else 'FAIL'}** |

**Benchmarks Run:** {evaluation_result.benchmark_count}
**Passed:** {evaluation_result.passed}
**Evaluation Duration:** {evaluation_result.evaluation_duration_ms:.0f}ms

---

## Decision Rationale

{'## Promotion Criteria Met' if passed else '## Promotion Criteria Not Met'}

The genome was {'PROMOTED' if passed else 'NOT PROMOTED'} because:
- Overall score ({evaluation_result.overall_score:.2f}) is {'above' if passed else 'below'} threshold ({BETA_THRESHOLD})
- {'All key benchmarks met minimum requirements.' if passed else 'One or more benchmarks failed to meet requirements.'}

---

## Evidence

### L16 Coordination Cycle
- **Coordination ID:** {coordination_result.coordination_id}
- **Cycle Number:** {coordination_result.cycle_number}
- **Health:** {coordination_result.coordination_health:.2f}
- **Duration:** {coordination_result.coordination_duration_ms:.0f}ms

### Persistence
- **Genomes Registered:** 2 (founder + child)
- **L16 Signals Collected:** 1
- **Benchmark Evaluations:** 1

---

## Exit Criteria Status

| Criterion | Status |
|-----------|--------|
| Parent genome selected | ✅ genome_founder_001 |
| Mutated genome generated | ✅ {child_genome.genome_id} |
| L16 ecosystem signals collected | ✅ {signal.signal_id} |
| Benchmark evaluation executed | ✅ {evaluation_result.benchmark_count} missions |
| Pass/fail outcome computed | ✅ {decision} |
| Genome promoted or retired | ✅ {child_genome.status.value} |
| All records persisted | ✅ In-memory registry |
| Evidence recorded | ✅ This document |

---

**Report Generated:** {datetime.utcnow().isoformat()}
**Cycle Status:** {'COMPLETE - PASSED' if passed else 'COMPLETE - FAILED'}
"""

    # Write report with UTF-8 encoding
    report_path = Path(__file__).parent / "layer17_cycle_001.md"
    report_path.write_text(report_content, encoding="utf-8")

    print(f"  [OK] Report saved to: {report_path}")

    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n" + "=" * 70)
    print("CYCLE 001 COMPLETE")
    print("=" * 70)
    print(f"Result: {decision}")
    print(f"Score: {evaluation_result.overall_score:.2f}")
    print(f"Report: {report_path}")
    print("=" * 70)

    return {
        "decision": decision,
        "score": evaluation_result.overall_score,
        "passed": passed,
        "report_path": str(report_path),
        "signal": signal,
        "genome": child_genome,
    }


if __name__ == "__main__":
    result = asyncio.run(run_cycle_001())
    sys.exit(0 if result["passed"] else 1)
