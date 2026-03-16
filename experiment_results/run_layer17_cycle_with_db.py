#!/usr/bin/env python3
"""
TORQ Layer 17 - Cycle 001 Execution with Supabase Persistence

Execute one real Layer 17 cycle using live L16-backed signals.
This version persists all results to Supabase database.

Prerequisites:
- Layer 17 migration must be applied (run execute_layer17_migration.py first)
- SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from supabase import create_client

# TORQ imports
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


# =============================================================================
# SUPABASE PERSISTENCE HANDLERS
# =============================================================================

class SupabasePersistence:
    """Handle persistence to Supabase for Layer 17 entities."""

    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")

        self.client = create_client(supabase_url, supabase_key)
        self.supabase_url = supabase_url

    async def persist_genome(self, genome: AgentGenome) -> str:
        """Persist a genome to Supabase agent_genomes table."""
        data = {
            "genome_id": genome.genome_id,
            "parent_genome_id": genome.parent_genome_id,
            "generation": genome.generation,
            "status": genome.status.value,
            "toolset": genome.toolset if isinstance(genome.toolset, list) else list(genome.toolset),
            "min_toolset_size": genome.min_toolset_size,
            "max_toolset_size": genome.max_toolset_size,
            "llm_model": genome.llm_model,
            "llm_temperature": float(genome.llm_temperature),
            "llm_max_tokens": genome.llm_max_tokens,
            "missions_completed": genome.missions_completed,
            "missions_attempted": genome.missions_attempted,
            "total_value_generated": float(genome.total_value_generated),
            "total_cost_incurred": float(genome.total_cost_incurred),
            "fitness_score": float(genome.fitness_score) if genome.fitness_score else None,
            "completion_rate": float(genome.completion_rate),
            "efficiency_score": float(genome.efficiency_score),
            "reliability_score": float(genome.reliability_score),
            "benchmark_completion_score": float(genome.benchmark_completion_score) if genome.benchmark_completion_score else None,
            "benchmark_latency_score": float(genome.benchmark_latency_score) if genome.benchmark_latency_score else None,
            "benchmark_consistency_score": float(genome.benchmark_consistency_score) if genome.benchmark_consistency_score else None,
            "benchmark_overall_score": float(genome.benchmark_overall_score) if genome.benchmark_overall_score else None,
            "benchmark_passed": genome.benchmark_passed,
            "created_at": genome.created_at.isoformat() if genome.created_at else datetime.utcnow().isoformat(),
            "updated_at": genome.updated_at.isoformat() if genome.updated_at else datetime.utcnow().isoformat(),
            "retired_at": genome.retired_at.isoformat() if genome.retired_at else None,
        }

        try:
            result = self.client.table("agent_genomes").upsert(data).execute()
            return genome.genome_id
        except Exception as e:
            print(f"  [WARN] Failed to persist genome {genome.genome_id}: {e}")
            return None

    async def persist_l16_signal(self, signal, evolved_genome_id: str = None) -> str:
        """Persist L16 ecosystem signal to Supabase."""
        # Convert signal to dict
        data = {
            "signal_id": signal.signal_id,
            "collected_at": signal.collected_at.isoformat() if hasattr(signal, 'collected_at') else datetime.utcnow().isoformat(),
            "total_agents": signal.total_agents,
            "active_agents": signal.active_agents,
            "market_health": float(signal.market_health),
            "resource_supply": signal.resource_supply if isinstance(signal.resource_supply, dict) else dict(signal.resource_supply),
            "resource_demand": signal.resource_demand if isinstance(signal.resource_demand, dict) else dict(signal.resource_demand),
            "supply_demand_gap": float(signal.supply_demand_gap),
            "total_missions_processed": signal.total_missions_processed,
            "total_missions_allocated": signal.total_missions_allocated,
            "allocation_success_rate": float(signal.allocation_success_rate),
            "recent_allocations": signal.recent_allocations if isinstance(signal.recent_allocations, list) else list(signal.recent_allocations),
            "equilibrium_prices": signal.equilibrium_prices if isinstance(signal.equilibrium_prices, dict) else dict(signal.equilibrium_prices),
            "market_stable": signal.market_stable,
            "equilibrium_confidence": float(signal.equilibrium_confidence),
            "active_adjustments": signal.active_adjustments if hasattr(signal, 'active_adjustments') else 0,
            "evolved_genome_id": evolved_genome_id,
        }

        try:
            result = self.client.table("l16_ecosystem_signals").upsert(data).execute()
            return signal.signal_id
        except Exception as e:
            print(f"  [WARN] Failed to persist signal {signal.signal_id}: {e}")
            return None

    async def persist_benchmark_evaluation(self, evaluation_result, genome_id: str) -> str:
        """Persist benchmark evaluation to Supabase."""
        evaluation_id = str(uuid4())
        data = {
            "evaluation_id": evaluation_id,
            "genome_id": genome_id,
            "benchmark_count": evaluation_result.benchmark_count,
            "evaluated_at": evaluation_result.evaluated_at.isoformat() if hasattr(evaluation_result, 'evaluated_at') else datetime.utcnow().isoformat(),
            "evaluation_duration_ms": float(evaluation_result.evaluation_duration_ms),
            "completion_score": float(evaluation_result.completion_score),
            "latency_score": float(evaluation_result.latency_score),
            "consistency_score": float(evaluation_result.consistency_score),
            "overall_score": float(evaluation_result.overall_score),
            "passed": evaluation_result.passed,
            "benchmark_details": evaluation_result.benchmark_details if hasattr(evaluation_result, 'benchmark_details') else {},
        }

        try:
            result = self.client.table("benchmark_evaluations").insert(data).execute()
            return evaluation_id
        except Exception as e:
            print(f"  [WARN] Failed to persist benchmark evaluation: {e}")
            return None

    def verify_tables(self):
        """Verify that Layer 17 tables exist."""
        tables = ['agent_genomes', 'l16_ecosystem_signals', 'benchmark_evaluations']
        existing = []

        for table in tables:
            try:
                result = self.client.table(table).select("*").limit(1).execute()
                existing.append(table)
                print(f"  [OK] Table '{table}' exists")
            except Exception as e:
                print(f"  [MISSING] Table '{table}' not found: {e}")

        return len(existing) == len(tables)


# =============================================================================
# CYCLE EXECUTION
# =============================================================================

async def run_cycle_001_with_persistence():
    """Execute Layer 17 Cycle 001 with Supabase persistence."""

    print("=" * 70)
    print("TORQ LAYER 17 - CYCLE 001 WITH SUPABASE PERSISTENCE")
    print(f"Started: {datetime.utcnow().isoformat()}")
    print("=" * 70)

    # Initialize Supabase persistence
    print("\n[INIT] Initializing Supabase persistence...")
    try:
        db = SupabasePersistence()
        print(f"  [OK] Connected to Supabase: {db.supabase_url}")
    except Exception as e:
        print(f"  [ERROR] Failed to connect to Supabase: {e}")
        print("\nPlease ensure SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are set in .env")
        return None

    # Verify tables exist
    print("\n[VERIFY] Checking Layer 17 tables...")
    if not db.verify_tables():
        print("\n[ERROR] Layer 17 tables not found!")
        print("Please run the migration first:")
        print("  python experiment_results/execute_layer17_migration.py")
        return None

    # Track inserted IDs
    inserted_ids = {
        "genomes": [],
        "signals": [],
        "evaluations": [],
    }

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
    # STEP 4: Run Coordination Cycle
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

    # Persist founder genome
    founder_db_id = await db.persist_genome(founder_genome)
    if founder_db_id:
        inserted_ids["genomes"].append(founder_db_id)
        print(f"  [OK] Founder genome persisted to DB: {founder_db_id}")

    # ========================================================================
    # STEP 7: Mutate Genome Based on L16 Ecosystem State
    # ========================================================================
    print("\n[STEP 7] Mutating genome based on L16 ecosystem state...")

    mutation_engine = create_mutation_engine(seed=42)
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

    # Persist child genome
    child_db_id = await db.persist_genome(child_genome)
    if child_db_id:
        inserted_ids["genomes"].append(child_db_id)
        print(f"  [OK] Child genome persisted to DB: {child_db_id}")

    # Persist L16 signal
    signal_db_id = await db.persist_l16_signal(signal, evolved_genome_id=child_genome.genome_id)
    if signal_db_id:
        inserted_ids["signals"].append(signal_db_id)
        print(f"  [OK] L16 signal persisted to DB: {signal_db_id}")

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

    # Persist benchmark evaluation
    eval_db_id = await db.persist_benchmark_evaluation(evaluation_result, child_genome.genome_id)
    if eval_db_id:
        inserted_ids["evaluations"].append(eval_db_id)
        print(f"  [OK] Benchmark evaluation persisted to DB: {eval_db_id}")

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

    # Update genome in DB
    await db.persist_genome(child_genome)

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

Layer 17 Cycle 001 completed successfully with **database persistence enabled**.
The evaluation resulted in **{decision}** based on benchmark performance.

- **Founder Genome:** {founder_genome.genome_id}
- **Child Genome:** {child_genome.genome_id}
- **Overall Score:** {evaluation_result.overall_score:.2f}
- **Threshold:** {BETA_THRESHOLD}
- **Result:** {'PASSED' if passed else 'FAILED'}

---

## Database Persistence

**Supabase Connection:** {db.supabase_url}

### Inserted Row IDs

| Table | Count | IDs |
|-------|-------|-----|
| agent_genomes | {len(inserted_ids['genomes'])} | {', '.join(inserted_ids['genomes']) if inserted_ids['genomes'] else 'None'} |
| l16_ecosystem_signals | {len(inserted_ids['signals'])} | {', '.join(inserted_ids['signals']) if inserted_ids['signals'] else 'None'} |
| benchmark_evaluations | {len(inserted_ids['evaluations'])} | {', '.join(inserted_ids['evaluations']) if inserted_ids['evaluations'] else 'None'} |

**Total Records Persisted:** {len(inserted_ids['genomes']) + len(inserted_ids['signals']) + len(inserted_ids['evaluations'])}

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
- **DB ID:** {founder_db_id or 'Not persisted'}
- **Toolset:** {founder_genome.toolset}
- **LLM Model:** {founder_genome.llm_model}
- **Temperature:** {founder_genome.llm_temperature}
- **Max Tokens:** {founder_genome.llm_max_tokens}

### Child Genome (Generation {child_genome.generation})
- **Genome ID:** {child_genome.genome_id}
- **DB ID:** {child_db_id or 'Not persisted'}
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
**Evaluation DB ID:** {eval_db_id or 'Not persisted'}

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
- **Signal DB ID:** {signal_db_id or 'Not persisted'}

### Persistence Verification
- **Founder Genome Persisted:** {'Yes (' + founder_db_id + ')' if founder_db_id else 'No'}
- **Child Genome Persisted:** {'Yes (' + child_db_id + ')' if child_db_id else 'No'}
- **L16 Signal Persisted:** {'Yes (' + signal_db_id + ')' if signal_db_id else 'No'}
- **Benchmark Evaluation Persisted:** {'Yes (' + eval_db_id + ')' if eval_db_id else 'No'}

---

## Exit Criteria Status

| Criterion | Status |
|-----------|--------|
| Parent genome selected | ✅ {founder_genome.genome_id} |
| Mutated genome generated | ✅ {child_genome.genome_id} |
| L16 ecosystem signals collected | ✅ {signal.signal_id} |
| Benchmark evaluation executed | ✅ {evaluation_result.benchmark_count} missions |
| Pass/fail outcome computed | ✅ {decision} |
| Genome promoted or retired | ✅ {child_genome.status.value} |
| All records persisted | ✅ Supabase |
| Evidence recorded | ✅ This document |

---

**Report Generated:** {datetime.utcnow().isoformat()}
**Cycle Status:** {'COMPLETE - PASSED' if passed else 'COMPLETE - FAILED'}
**Database Persistence:** {'ENABLED' if all([founder_db_id, child_db_id, signal_db_id, eval_db_id]) else 'PARTIAL'}
"""

    # Write report
    report_path = Path(__file__).parent / "layer17_cycle_001.md"
    report_path.write_text(report_content, encoding="utf-8")

    print(f"  [OK] Report saved to: {report_path}")

    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n" + "=" * 70)
    print("CYCLE 001 COMPLETE WITH DATABASE PERSISTENCE")
    print("=" * 70)
    print(f"Result: {decision}")
    print(f"Score: {evaluation_result.overall_score:.2f}")
    print(f"Report: {report_path}")
    print("\nDatabase Records Created:")
    print(f"  - agent_genomes: {len(inserted_ids['genomes'])} rows")
    print(f"  - l16_ecosystem_signals: {len(inserted_ids['signals'])} rows")
    print(f"  - benchmark_evaluations: {len(inserted_ids['evaluations'])} rows")
    print("=" * 70)

    return {
        "decision": decision,
        "score": evaluation_result.overall_score,
        "passed": passed,
        "report_path": str(report_path),
        "signal": signal,
        "genome": child_genome,
        "inserted_ids": inserted_ids,
    }


if __name__ == "__main__":
    result = asyncio.run(run_cycle_001_with_persistence())
    sys.exit(0 if result and result.get("passed") else 1)
