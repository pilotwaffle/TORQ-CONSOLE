#!/usr/bin/env python3
"""Layer 17 Cycle 002 - Evolution with Active L16 Ecosystem

This script executes Cycle 002 with a populated L16 ecosystem:
1. Populate L16 with agents, resource offers, and bids
2. Run coordination cycle to generate real market state
3. Execute evolution cycle with live L16 signals
4. Persist all results to Supabase
5. Generate comprehensive report
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from torq_console.layer17.models import (
    AgentGenome,
    GenomeStatus,
    L16EcosystemSignal,
    BenchmarkEvaluationResult,
)
from torq_console.layer17.services import create_signal_collector
from torq_console.layer17.mutation import create_mutation_engine
from torq_console.layer17.evaluation import create_evaluation_harness
from torq_console.layer17.evaluation.benchmark_missions import get_benchmark_missions
from torq_console.layer16.services import create_economic_coordination_service
from torq_console.layer16.models import (
    AgentRegistration,
    AgentCapabilities,
    MissionRequirements,
    MissionBid,
    ResourceOffer,
)

# =============================================================================
# CYCLE CONFIGURATION
# =============================================================================

CYCLE_ID = "cycle_002"
DETERMINISTIC_SEED = 43  # Different seed for Cycle 002
PARENT_GENOME_ID = "genome_9c07d72cdc75"  # Use child from Cycle 001 as parent


# =============================================================================
# L16 ECOSYSTEM POPULATION
# =============================================================================

async def populate_l16_ecosystem(service) -> dict:
    """Populate L16 with agents, offers, and bids for realistic market state."""

    print("\n" + "="*60)
    print("POPULATING L16 ECOSYSTEM")
    print("="*60)

    population_result = {
        "agents_registered": [],
        "offers_submitted": [],
        "bids_submitted": [],
        "missions_submitted": [],
    }

    # Register 3 specialist agents with verified fields
    specialist_configs = [
        {
            "agent_id": "crypto_specialist_001",
            "agent_type": "specialist",
            "specializations": ["trading", "crypto_analysis", "market_data"],
            "cpu": 80.0,
            "memory": 16.0,
            "cost": 15.0,
        },
        {
            "agent_id": "ml_researcher_001",
            "agent_type": "specialist",
            "specializations": ["ml_training", "data_science", "inference"],
            "cpu": 120.0,
            "memory": 32.0,
            "cost": 25.0,
        },
        {
            "agent_id": "api_integrator_001",
            "agent_type": "specialist",
            "specializations": ["api_integration", "webhooks", "etl"],
            "cpu": 50.0,
            "memory": 8.0,
            "cost": 10.0,
        },
    ]

    for config in specialist_configs:
        capabilities = AgentCapabilities(
            agent_id=config["agent_id"],
            agent_type=config["agent_type"],
            cpu_capacity=config["cpu"],
            memory_capacity=config["memory"],
            storage_capacity=100.0,
            network_bandwidth=1000.0,
            can_inference=config["agent_type"] == "specialist",
            can_planning=True,
            can_execute=True,
            can_monitoring=True,
            specializations=config["specializations"],
            cost_per_cpu_unit=config["cost"] / config["cpu"],
            cost_per_memory_gb=config["cost"] / config["memory"],
            base_hourly_rate=config["cost"],
            reliability_score=0.9,
            avg_completion_time=60.0,
            current_load=0.2,
        )

        registration = AgentRegistration(
            agent_id=config["agent_id"],
            agent_type=config["agent_type"],
            capabilities=capabilities,
        )

        await service.register_agent(registration)
        population_result["agents_registered"].append(config["agent_id"])
        print(f"  [OK] Registered: {config['agent_id']} ({config['agent_type']})")

    # Submit resource offers
    offer_configs = [
        {
            "offer_id": "offer_cpu_crypto_001",
            "agent_id": "crypto_specialist_001",
            "resource_type": "cpu",
            "quantity": 60.0,
            "price": 8.0,
        },
        {
            "offer_id": "offer_memory_ml_001",
            "agent_id": "ml_researcher_001",
            "resource_type": "memory",
            "quantity": 24.0,
            "price": 12.0,
        },
        {
            "offer_id": "offer_cpu_api_001",
            "agent_id": "api_integrator_001",
            "resource_type": "cpu",
            "quantity": 40.0,
            "price": 6.0,
        },
    ]

    for config in offer_configs:
        offer = ResourceOffer(
            offer_id=config["offer_id"],
            agent_id=config["agent_id"],
            resource_type=config["resource_type"],
            quantity=config["quantity"],
            asking_price=config["price"],
            min_quantity=1.0,
            can_partial=True,
        )

        await service.submit_resource_offer(offer)
        population_result["offers_submitted"].append(config["offer_id"])
        print(f"  [OK] Offer: {config['offer_id']} - {config['quantity']} {config['resource_type']} @ ${config['price']}")

    # Submit a mission for bidding
    mission = MissionRequirements(
        mission_id="cycle002_mission_001",
        mission_type="crypto_trading_analysis",
        required_cpu=40.0,
        required_memory=8.0,
        required_storage=10.0,
        required_network=100.0,
        requires_inference=True,
        requires_planning=True,
        requires_execution=True,
        requires_monitoring=False,
        required_specializations=["trading"],
        max_cost=500.0,
        deadline=None,
        priority="high",
        expected_value=1500.0,
    )

    await service.submit_mission(mission)
    population_result["missions_submitted"].append(mission.mission_id)
    print(f"  [OK] Mission: {mission.mission_id}")

    # Submit bids from agents
    bid_configs = [
        {
            "bid_id": "bid_crypto_001",
            "mission_id": "cycle002_mission_001",
            "agent_id": "crypto_specialist_001",
            "cost": 350.0,
            "value": 1400.0,
            "probability": 0.95,
            "specialization_match": 1.0,
        },
        {
            "bid_id": "bid_ml_001",
            "mission_id": "cycle002_mission_001",
            "agent_id": "ml_researcher_001",
            "cost": 400.0,
            "value": 1200.0,
            "probability": 0.85,
            "specialization_match": 0.3,
        },
    ]

    for config in bid_configs:
        bid = MissionBid(
            bid_id=config["bid_id"],
            mission_id=config["mission_id"],
            agent_id=config["agent_id"],
            bid_cost=config["cost"],
            expected_value=config["value"],
            completion_probability=config["probability"],
            estimated_duration=timedelta(hours=2),
            cpu_usage=40.0,
            memory_usage=8.0,
            storage_usage=10.0,
            specialization_match=config["specialization_match"],
            capability_coverage=1.0,
            can_start_before=None,
            can_complete_by=None,
        )

        await service.submit_mission_bid(bid)
        population_result["bids_submitted"].append(config["bid_id"])
        print(f"  [OK] Bid: {config['bid_id']} from {config['agent_id']} - ${config['cost']}")

    # Run coordination cycle to establish market state
    print("\n  Running coordination cycle...")
    coordination_result = await service.run_coordination_cycle()

    print(f"\n  Coordination Result:")
    print(f"    Cycle: {coordination_result.cycle_number}")
    print(f"    Total agents: {coordination_result.market_state.total_agents}")
    print(f"    Missions allocated: {len(coordination_result.mission_allocations)}")
    print(f"    Market health: {coordination_result.market_state.market_health:.2f}")

    population_result["coordination_result"] = {
        "cycle_number": coordination_result.cycle_number,
        "total_agents": coordination_result.market_state.total_agents,
        "total_missions_allocated": len(coordination_result.mission_allocations),
        "market_health": coordination_result.market_state.market_health,
        "market_stable": coordination_result.equilibrium.stable,
    }

    return population_result


# =============================================================================
# CYCLE EXECUTION
# =============================================================================

async def execute_cycle() -> dict:
    """Execute full Layer 17 evolution cycle with active L16 ecosystem."""

    print(f"\n{'='*60}")
    print(f"LAYER 17 CYCLE 002 - EVOLUTION WITH ACTIVE L16 ECOSYSTEM")
    print(f"{'='*60}\n")

    results = {
        "cycle_id": CYCLE_ID,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "l16_population": None,
        "parent_genome": None,
        "mutated_genome": None,
        "l16_signal": None,
        "benchmark_result": None,
        "final_decision": None,
        "persistence": {},
        "errors": [],
    }

    # -------------------------------------------------------------------------
    # STEP 0: Populate L16 Ecosystem
    # -------------------------------------------------------------------------
    print("STEP 0: Populating L16 Ecosystem with active agents...")

    l16_service = create_economic_coordination_service()
    population_result = await populate_l16_ecosystem(l16_service)

    results["l16_population"] = population_result

    # -------------------------------------------------------------------------
    # STEP 1: Load Parent Genome (from Cycle 001)
    # -------------------------------------------------------------------------
    print("\nSTEP 1: Loading Parent Genome from Cycle 001...")

    # Load the genome that was created in Cycle 001
    parent_genome = AgentGenome(
        genome_id="genome_9c07d72cdc75",  # From Cycle 001
        parent_genome_id="torq_production_v1",
        generation=1,
        status=GenomeStatus.EXPERIMENTAL,
        toolset=["web_search", "file_write", "bash_execute", "test_runner"],
        min_toolset_size=3,
        max_toolset_size=15,
        llm_model="claude-sonnet-4-6",
        llm_temperature=0.7,
        llm_max_tokens=4096,
        missions_completed=0,
        missions_attempted=0,
        total_value_generated=0.0,
        total_cost_incurred=0.0,
        benchmark_completion_score=0.25,
        benchmark_latency_score=0.92,
        benchmark_consistency_score=1.0,
        benchmark_overall_score=0.676,
        benchmark_passed=True,
    )

    results["parent_genome"] = {
        "genome_id": parent_genome.genome_id,
        "status": parent_genome.status.value,
        "generation": parent_genome.generation,
        "toolset": parent_genome.toolset,
        "toolset_count": len(parent_genome.toolset),
        "benchmark_overall_score": parent_genome.benchmark_overall_score,
    }

    print(f"  [OK] Parent genome: {parent_genome.genome_id}")
    print(f"    Generation: {parent_genome.generation}")
    print(f"    Toolset: {parent_genome.toolset}")
    print(f"    Previous benchmark: {parent_genome.benchmark_overall_score:.3f}")

    # -------------------------------------------------------------------------
    # STEP 2: Generate Mutated Genome
    # -------------------------------------------------------------------------
    print("\nSTEP 2: Generating Mutated Genome...")

    mutation_engine = create_mutation_engine(seed=DETERMINISTIC_SEED)
    mutated_genome = await mutation_engine.mutate_genome(
        parent_genome,
        mutation_rate=0.25,
    )

    results["mutated_genome"] = {
        "new_genome_id": mutated_genome.genome_id,
        "parent_genome_id": mutated_genome.parent_genome_id,
        "generation": mutated_genome.generation,
        "mutation_operators_applied": [],
        "deterministic_seed": DETERMINISTIC_SEED,
    }

    # Track mutations
    if mutated_genome.toolset != parent_genome.toolset:
        added = set(mutated_genome.toolset) - set(parent_genome.toolset)
        removed = set(parent_genome.toolset) - set(mutated_genome.toolset)
        if added:
            results["mutated_genome"]["mutation_operators_applied"].append(f"added_tools: {list(added)}")
        if removed:
            results["mutated_genome"]["mutation_operators_applied"].append(f"removed_tools: {list(removed)}")

    print(f"  [OK] Mutated genome: {mutated_genome.genome_id}")
    print(f"    Generation: {mutated_genome.generation}")
    print(f"    Toolset: {mutated_genome.toolset}")
    print(f"    Mutations: {results['mutated_genome']['mutation_operators_applied']}")

    # -------------------------------------------------------------------------
    # STEP 3: Collect L16 Ecosystem Signals (from active ecosystem)
    # -------------------------------------------------------------------------
    print("\nSTEP 3: Collecting L16 Ecosystem Signals from active ecosystem...")

    signal_collector = create_signal_collector(l16_service)
    l16_signal = await signal_collector.collect()

    results["l16_signal"] = {
        "source_service_class": "torq_console.layer16.services.EconomicCoordinationService",
        "timestamp": l16_signal.collected_at.isoformat(),
        "key_fields_captured": {
            "total_agents": l16_signal.total_agents,
            "active_agents": l16_signal.active_agents,
            "market_health": l16_signal.market_health,
            "total_missions_processed": l16_signal.total_missions_processed,
            "total_missions_allocated": l16_signal.total_missions_allocated,
            "allocation_success_rate": l16_signal.allocation_success_rate,
            "market_stable": l16_signal.market_stable,
            "equilibrium_confidence": l16_signal.equilibrium_confidence,
            "supply_demand_gap": l16_signal.supply_demand_gap,
            "active_adjustments": l16_signal.active_adjustments,
        },
        "signal_id": l16_signal.signal_id,
    }

    print(f"  [OK] L16 Signal collected: {l16_signal.signal_id}")
    print(f"    Total agents: {l16_signal.total_agents} (ACTIVE ECOSYSTEM)")
    print(f"    Market health: {l16_signal.market_health:.2f} (LIVE MARKET)")
    print(f"    Allocation success rate: {l16_signal.allocation_success_rate:.2f}")
    print(f"    Supply-demand gap: {l16_signal.supply_demand_gap:.2f}")

    # -------------------------------------------------------------------------
    # STEP 4: Run Benchmark Evaluation
    # -------------------------------------------------------------------------
    print("\nSTEP 4: Running Benchmark Evaluation...")

    evaluation_harness = create_evaluation_harness()
    evaluation_harness.load_benchmarks(get_benchmark_missions())

    benchmark_result = await evaluation_harness.run_benchmark_suite(mutated_genome)

    results["benchmark_result"] = {
        "benchmark_count": benchmark_result.benchmark_count,
        "completion_score": benchmark_result.completion_score,
        "latency_score": benchmark_result.latency_score,
        "consistency_score": benchmark_result.consistency_score,
        "overall_score": benchmark_result.overall_score,
        "passed": benchmark_result.passed,
        "evaluated_at": benchmark_result.evaluated_at.isoformat(),
        "evaluation_duration_ms": benchmark_result.evaluation_duration_ms,
    }

    print(f"  [OK] Benchmark evaluation complete")
    print(f"    Benchmarks: {benchmark_result.benchmark_count}")
    print(f"    Completion: {benchmark_result.completion_score:.3f}")
    print(f"    Latency: {benchmark_result.latency_score:.3f}")
    print(f"    Consistency: {benchmark_result.consistency_score:.3f}")
    print(f"    Overall: {benchmark_result.overall_score:.3f}")
    print(f"    Passed: {benchmark_result.passed}")

    # -------------------------------------------------------------------------
    # STEP 5: Promote or Retire Decision
    # -------------------------------------------------------------------------
    print("\nSTEP 5: Making Promotion/Retirement Decision...")

    # Decision criteria (slightly stricter for Cycle 002)
    THRESHOLD_OVERALL = 0.65
    THRESHOLD_COMPLETION = 0.4
    THRESHOLD_CONSISTENCY = 0.5

    passed = (
        benchmark_result.overall_score >= THRESHOLD_OVERALL and
        benchmark_result.completion_score >= THRESHOLD_COMPLETION and
        benchmark_result.consistency_score >= THRESHOLD_CONSISTENCY
    )

    if passed:
        decision = "promoted"
        mutated_genome.status = GenomeStatus.PRODUCTION
        reason = f"Passed all thresholds (overall: {benchmark_result.overall_score:.2f} >= {THRESHOLD_OVERALL}, completion: {benchmark_result.completion_score:.2f} >= {THRESHOLD_COMPLETION}, consistency: {benchmark_result.consistency_score:.2f} >= {THRESHOLD_CONSISTENCY})"
    else:
        decision = "retained_as_experimental"
        mutated_genome.status = GenomeStatus.EXPERIMENTAL
        reason = f"Below threshold (overall: {benchmark_result.overall_score:.2f} < {THRESHOLD_OVERALL} or completion: {benchmark_result.completion_score:.2f} < {THRESHOLD_COMPLETION} or consistency: {benchmark_result.consistency_score:.2f} < {THRESHOLD_CONSISTENCY})"

    results["final_decision"] = {
        "decision": decision,
        "reason": reason,
        "thresholds": {
            "overall": THRESHOLD_OVERALL,
            "completion": THRESHOLD_COMPLETION,
            "consistency": THRESHOLD_CONSISTENCY,
        },
        "final_status": mutated_genome.status.value,
    }

    print(f"  [OK] Decision: {decision}")
    print(f"    Reason: {reason}")
    print(f"    Final status: {mutated_genome.status.value}")

    # -------------------------------------------------------------------------
    # STEP 6: Persist to Supabase
    # -------------------------------------------------------------------------
    print("\nSTEP 6: Persisting to Supabase...")

    try:
        from dotenv import load_dotenv
        load_dotenv()

        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if supabase_url and supabase_key:
            from supabase import create_client

            supabase = create_client(supabase_url, supabase_key)

            # Persist parent genome (update from Cycle 001)
            parent_data = {
                "genome_id": parent_genome.genome_id,
                "parent_genome_id": parent_genome.parent_genome_id,
                "generation": parent_genome.generation,
                "status": parent_genome.status.value,
                "toolset": parent_genome.toolset,
                "min_toolset_size": parent_genome.min_toolset_size,
                "max_toolset_size": parent_genome.max_toolset_size,
                "llm_model": parent_genome.llm_model,
                "llm_temperature": float(parent_genome.llm_temperature),
                "llm_max_tokens": parent_genome.llm_max_tokens,
                "missions_completed": parent_genome.missions_completed,
                "missions_attempted": parent_genome.missions_attempted,
                "total_value_generated": float(parent_genome.total_value_generated),
                "total_cost_incurred": float(parent_genome.total_cost_incurred),
                "fitness_score": None,
                "completion_rate": 0.0,
                "efficiency_score": 0.0,
                "reliability_score": 0.5,
                "benchmark_completion_score": float(parent_genome.benchmark_completion_score) if parent_genome.benchmark_completion_score else None,
                "benchmark_latency_score": float(parent_genome.benchmark_latency_score) if parent_genome.benchmark_latency_score else None,
                "benchmark_consistency_score": float(parent_genome.benchmark_consistency_score) if parent_genome.benchmark_consistency_score else None,
                "benchmark_overall_score": float(parent_genome.benchmark_overall_score) if parent_genome.benchmark_overall_score else None,
                "benchmark_passed": parent_genome.benchmark_passed,
            }

            parent_result = supabase.table("agent_genomes").upsert(parent_data).execute()
            results["persistence"]["parent_genome"] = f"Row upserted: {parent_genome.genome_id}"

            # Persist mutated genome
            mutated_data = {
                "genome_id": mutated_genome.genome_id,
                "parent_genome_id": mutated_genome.parent_genome_id,
                "generation": mutated_genome.generation,
                "status": mutated_genome.status.value,
                "toolset": mutated_genome.toolset,
                "min_toolset_size": mutated_genome.min_toolset_size,
                "max_toolset_size": mutated_genome.max_toolset_size,
                "llm_model": mutated_genome.llm_model,
                "llm_temperature": float(mutated_genome.llm_temperature),
                "llm_max_tokens": mutated_genome.llm_max_tokens,
                "missions_completed": 0,
                "missions_attempted": 0,
                "total_value_generated": 0.0,
                "total_cost_incurred": 0.0,
                "fitness_score": None,
                "completion_rate": 0.0,
                "efficiency_score": 0.0,
                "reliability_score": 0.5,
                "benchmark_completion_score": float(benchmark_result.completion_score),
                "benchmark_latency_score": float(benchmark_result.latency_score),
                "benchmark_consistency_score": float(benchmark_result.consistency_score),
                "benchmark_overall_score": float(benchmark_result.overall_score),
                "benchmark_passed": benchmark_result.passed,
            }

            mutated_result = supabase.table("agent_genomes").upsert(mutated_data).execute()
            results["persistence"]["mutated_genome"] = f"Row upserted: {mutated_genome.genome_id}"

            # Persist L16 signal
            signal_data = {
                "signal_id": l16_signal.signal_id,
                "collected_at": l16_signal.collected_at.isoformat(),
                "total_agents": l16_signal.total_agents,
                "active_agents": l16_signal.active_agents,
                "market_health": float(l16_signal.market_health),
                "resource_supply": l16_signal.resource_supply,
                "resource_demand": l16_signal.resource_demand,
                "supply_demand_gap": float(l16_signal.supply_demand_gap),
                "total_missions_processed": l16_signal.total_missions_processed,
                "total_missions_allocated": l16_signal.total_missions_allocated,
                "allocation_success_rate": float(l16_signal.allocation_success_rate),
                "recent_allocations": l16_signal.recent_allocations,
                "equilibrium_prices": l16_signal.equilibrium_prices,
                "market_stable": l16_signal.market_stable,
                "equilibrium_confidence": float(l16_signal.equilibrium_confidence),
                "active_adjustments": l16_signal.active_adjustments,
                "evolved_genome_id": mutated_genome.genome_id,
            }

            signal_result = supabase.table("l16_ecosystem_signals").upsert(signal_data).execute()
            results["persistence"]["l16_ecosystem_signals"] = f"Row upserted: {l16_signal.signal_id}"

            # Persist benchmark evaluation
            benchmark_data = {
                "genome_id": mutated_genome.genome_id,
                "benchmark_count": benchmark_result.benchmark_count,
                "evaluated_at": benchmark_result.evaluated_at.isoformat(),
                "evaluation_duration_ms": float(benchmark_result.evaluation_duration_ms),
                "completion_score": float(benchmark_result.completion_score),
                "latency_score": float(benchmark_result.latency_score),
                "consistency_score": float(benchmark_result.consistency_score),
                "overall_score": float(benchmark_result.overall_score),
                "passed": benchmark_result.passed,
                "benchmark_details": benchmark_result.benchmark_details,
            }

            eval_result = supabase.table("benchmark_evaluations").insert(benchmark_data).execute()
            eval_id = eval_result.data[0]['evaluation_id']
            results["persistence"]["benchmark_evaluations"] = f"Row inserted: evaluation_id={eval_id}"

            print(f"  [OK] All records persisted to Supabase")
            for table, result in results["persistence"].items():
                print(f"    {table}: {result}")

        else:
            results["persistence"]["error"] = "Supabase credentials not configured"
            print(f"  [FAIL] Supabase not configured")

    except Exception as e:
        results["persistence"]["error"] = f"Persistence failed: {str(e)}"
        results["errors"].append(f"Persistence error: {str(e)}")
        print(f"  [FAIL] Persistence error: {e}")

    results["completed_at"] = datetime.now(timezone.utc).isoformat()

    return results


# =============================================================================
# REPORT GENERATION
# =============================================================================

def generate_markdown_report(results: dict) -> str:
    """Generate markdown report from cycle results."""

    report = f"""# Layer 17 Cycle 002

**Execution Date:** {results['started_at']}
**Cycle ID:** {results['cycle_id']}
**Status:** {'COMPLETE' if not results['errors'] else 'COMPLETE WITH ERRORS'}

---

## L16 Ecosystem Population

**Agents Registered:** {len(results['l16_population']['agents_registered'])}
{chr(10).join(f"- {agent}" for agent in results['l16_population']['agents_registered'])}

**Resource Offers:** {len(results['l16_population']['offers_submitted'])}
{chr(10).join(f"- {offer}" for offer in results['l16_population']['offers_submitted'])}

**Bids Submitted:** {len(results['l16_population']['bids_submitted'])}
{chr(10).join(f"- {bid}" for bid in results['l16_population']['bids_submitted'])}

**Coordination Result:**
- Cycle: {results['l16_population']['coordination_result']['cycle_number']}
- Total agents: {results['l16_population']['coordination_result']['total_agents']}
- Missions allocated: {results['l16_population']['coordination_result']['total_missions_allocated']}
- Market health: {results['l16_population']['coordination_result']['market_health']:.2f}

---

## Parent Genome
- **genome_id:** {results['parent_genome']['genome_id']}
- **status:** {results['parent_genome']['status']}
- **generation:** {results['parent_genome']['generation']}
- **toolset:** {results['parent_genome']['toolset']}
- **previous_benchmark_score:** {results['parent_genome']['benchmark_overall_score']:.3f}

---

## Mutation
- **new_genome_id:** {results['mutated_genome']['new_genome_id']}
- **parent_genome_id:** {results['mutated_genome']['parent_genome_id']}
- **generation:** {results['mutated_genome']['generation']}
- **mutation_operators_applied:** {', '.join(results['mutated_genome']['mutation_operators_applied']) if results['mutated_genome']['mutation_operators_applied'] else 'none'}
- **deterministic_seed:** {results['mutated_genome']['deterministic_seed']}

---

## L16 Signal Evidence (ACTIVE ECOSYSTEM)
- **source service/class:** {results['l16_signal']['source_service_class']}
- **timestamp:** {results['l16_signal']['timestamp']}
- **signal_id:** {results['l16_signal']['signal_id']}

**Key Fields Captured:**
"""
    for field, value in results['l16_signal']['key_fields_captured'].items():
        if isinstance(value, float):
            report += f"- `{field}`: {value:.2f}\n"
        else:
            report += f"- `{field}`: {value}\n"

    report += f"""
---

## Benchmark Evaluation
- **benchmark_count:** {results['benchmark_result']['benchmark_count']}
- **completion_score:** {results['benchmark_result']['completion_score']:.4f}
- **latency_score:** {results['benchmark_result']['latency_score']:.4f}
- **consistency_score:** {results['benchmark_result']['consistency_score']:.4f}
- **overall_score:** {results['benchmark_result']['overall_score']:.4f}
- **passed:** {results['benchmark_result']['passed']}
- **evaluated_at:** {results['benchmark_result']['evaluated_at']}

---

## Final Decision
- **decision:** {results['final_decision']['decision']}
- **reason:** {results['final_decision']['reason']}
- **final_status:** {results['final_decision']['final_status']}

**Thresholds Applied:**
- overall: {results['final_decision']['thresholds']['overall']}
- completion: {results['final_decision']['thresholds']['completion']}
- consistency: {results['final_decision']['thresholds']['consistency']}

---

## Persistence Evidence

"""
    if results['persistence']:
        for table, evidence in results['persistence'].items():
            report += f"**{table}:**\n- {evidence}\n\n"
    else:
        report += "No persistence records.\n"

    report += f"""
---

## Errors

"""
    if results['errors']:
        for error in results['errors']:
            report += f"- {error}\n"
    else:
        report += "No errors.\n"

    report += f"""
---

**Report Generated:** {results['completed_at']}
**Cycle Duration:** {datetime.fromisoformat(results['completed_at']) - datetime.fromisoformat(results['started_at'])}
"""
    return report


# =============================================================================
# MAIN
# =============================================================================

async def main():
    """Execute cycle and generate report."""

    # Run cycle
    results = await execute_cycle()

    # Generate report
    report = generate_markdown_report(results)

    # Write report
    report_path = Path(__file__).parent / "layer17_cycle_002.md"
    report_path.write_text(report)

    print(f"\n{'='*60}")
    print(f"CYCLE 002 COMPLETE")
    print(f"{'='*60}")
    print(f"\nReport saved to: {report_path}")

    # Return exit code based on errors
    return 1 if results['errors'] else 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
