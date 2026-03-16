#!/usr/bin/env python3
"""Layer 17 Cycle 001 - Full Evolution Cycle Execution

This script executes one complete Layer 17 evolution cycle:
1. Select parent genome
2. Generate mutated genome
3. Collect L16 signals
4. Run benchmark evaluation
5. Promote or retire genome
6. Persist records
7. Generate evidence report
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4, uuid4 as generate_uuid

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from torq_console.layer17.models import (
    AgentGenome,
    GenomeStatus,
    L16EcosystemSignal,
    BenchmarkEvaluationResult,
)
from torq_console.layer17.services import (
    create_agent_registry,
    create_signal_collector,
)
from torq_console.layer17.mutation import create_mutation_engine
from torq_console.layer17.evaluation import create_evaluation_harness
from torq_console.layer17.evaluation.benchmark_missions import get_benchmark_missions
from torq_console.layer16.services import create_economic_coordination_service
from torq_console.layer16.models import MissionRequirements


# =============================================================================
# CYCLE CONFIGURATION
# =============================================================================

CYCLE_ID = "cycle_001"
DETERMINISTIC_SEED = 42  # Fixed seed for reproducibility
PARENT_GENOME_ID = "torq_production_v1"  # Starting genome


# =============================================================================
# CYCLE EXECUTION
# =============================================================================

async def execute_cycle() -> dict:
    """Execute full Layer 17 evolution cycle."""

    print(f"\n{'='*60}")
    print(f"LAYER 17 CYCLE 001 - EVOLUTION CYCLE EXECUTION")
    print(f"{'='*60}\n")

    results = {
        "cycle_id": CYCLE_ID,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "parent_genome": None,
        "mutated_genome": None,
        "l16_signal": None,
        "benchmark_result": None,
        "final_decision": None,
        "persistence": {},
        "errors": [],
    }

    # -------------------------------------------------------------------------
    # STEP 1: Create Parent Genome (Production Baseline)
    # -------------------------------------------------------------------------
    print("STEP 1: Creating Parent Genome...")

    parent_genome = AgentGenome(
        genome_id=PARENT_GENOME_ID,
        parent_genome_id=None,
        generation=0,
        status=GenomeStatus.PRODUCTION,
        toolset=[
            "web_search",
            "code_executor",
            "file_read",
            "file_write",
            "bash_execute",
        ],
        min_toolset_size=3,
        max_toolset_size=15,
        llm_model="claude-sonnet-4-6",
        llm_temperature=0.7,
        llm_max_tokens=4096,
        missions_completed=50,
        missions_attempted=52,
        total_value_generated=15000.0,
        total_cost_incurred=5000.0,
        fitness_score=0.85,
        completion_rate=0.96,
        efficiency_score=0.88,
        reliability_score=0.92,
    )

    results["parent_genome"] = {
        "genome_id": parent_genome.genome_id,
        "status": parent_genome.status.value,
        "type": "production",
        "toolset_count": len(parent_genome.toolset),
        "fitness_score": parent_genome.fitness_score,
    }

    print(f"  Parent genome: {parent_genome.genome_id}")
    print(f"    Status: {parent_genome.status.value}")
    print(f"    Toolset: {parent_genome.toolset}")
    print(f"    Fitness: {parent_genome.fitness_score}")

    # -------------------------------------------------------------------------
    # STEP 2: Generate Mutated Genome
    # -------------------------------------------------------------------------
    print("\nSTEP 2: Generating Mutated Genome...")

    mutation_engine = create_mutation_engine(seed=DETERMINISTIC_SEED)
    mutated_genome = await mutation_engine.mutate_genome(
        parent_genome,
        mutation_rate=0.3,  # Higher rate for visible mutation
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

    print(f"  Mutated genome: {mutated_genome.genome_id}")
    print(f"    Generation: {mutated_genome.generation}")
    print(f"    Toolset: {mutated_genome.toolset}")
    print(f"    Mutations: {results['mutated_genome']['mutation_operators_applied']}")

    # -------------------------------------------------------------------------
    # STEP 3: Collect L16 Ecosystem Signals
    # -------------------------------------------------------------------------
    print("\nSTEP 3: Collecting L16 Ecosystem Signals...")

    l16_service = create_economic_coordination_service()
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
        },
        "signal_id": l16_signal.signal_id,
    }

    print(f"  L16 Signal collected: {l16_signal.signal_id}")
    print(f"    Total agents: {l16_signal.total_agents}")
    print(f"    Market health: {l16_signal.market_health}")
    print(f"    Allocation success rate: {l16_signal.allocation_success_rate}")

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

    print(f"  Benchmark evaluation complete")
    print(f"    Benchmarks: {benchmark_result.benchmark_count}")
    print(f"    Completion: {benchmark_result.completion_score}")
    print(f"    Latency: {benchmark_result.latency_score}")
    print(f"    Consistency: {benchmark_result.consistency_score}")
    print(f"    Overall: {benchmark_result.overall_score}")
    print(f"    Passed: {benchmark_result.passed}")

    # -------------------------------------------------------------------------
    # STEP 5: Promote or Retire Decision
    # -------------------------------------------------------------------------
    print("\nSTEP 5: Making Promotion/Retirement Decision...")

    # Decision criteria
    THRESHOLD_OVERALL = 0.6
    THRESHOLD_COMPLETION = 0.5
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

    print(f"  Decision: {decision}")
    print(f"    Reason: {reason}")
    print(f"    Final status: {mutated_genome.status.value}")

    # -------------------------------------------------------------------------
    # STEP 6: Persist to Supabase (if available)
    # -------------------------------------------------------------------------
    print("\nSTEP 6: Persisting to Supabase...")

    try:
        # Check for Supabase credentials
        from dotenv import load_dotenv
        load_dotenv()

        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if supabase_url and supabase_key:
            from supabase import create_client

            supabase = create_client(supabase_url, supabase_key)

            # Persist parent genome
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
                "fitness_score": float(parent_genome.fitness_score) if parent_genome.fitness_score else None,
                "completion_rate": float(parent_genome.completion_rate),
                "efficiency_score": float(parent_genome.efficiency_score),
                "reliability_score": float(parent_genome.reliability_score),
                "benchmark_passed": True,  # Parent is production
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
                "fitness_score": None,  # No ecosystem fitness yet
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
            results["persistence"]["benchmark_evaluations"] = f"Row inserted: evaluation_id={eval_result.data[0]['evaluation_id']}"

            print(f"  All records persisted to Supabase")
            for table, result in results["persistence"].items():
                print(f"    {table}: {result}")

        else:
            results["persistence"]["error"] = "Supabase credentials not configured - skipping persistence"
            print(f"  Supabase not configured - skipping persistence")

    except Exception as e:
        results["persistence"]["error"] = f"Persistence failed: {str(e)}"
        results["errors"].append(f"Persistence error: {str(e)}")
        print(f"  Persistence error: {e}")

    results["completed_at"] = datetime.now(timezone.utc).isoformat()

    return results


# =============================================================================
# REPORT GENERATION
# =============================================================================

def generate_markdown_report(results: dict) -> str:
    """Generate markdown report from cycle results."""

    report = f"""# Layer 17 Cycle 001

**Execution Date:** {results['started_at']}
**Cycle ID:** {results['cycle_id']}
**Status:** {'COMPLETE' if not results['errors'] else 'COMPLETE WITH ERRORS'}

---

## Parent Genome
- **genome_id:** {results['parent_genome']['genome_id']}
- **status:** {results['parent_genome']['status']}
- **type:** {results['parent_genome']['type']}
- **toolset_count:** {results['parent_genome']['toolset_count']}
- **fitness_score:** {results['parent_genome']['fitness_score']}

---

## Mutation
- **new_genome_id:** {results['mutated_genome']['new_genome_id']}
- **parent_genome_id:** {results['mutated_genome']['parent_genome_id']}
- **generation:** {results['mutated_genome']['generation']}
- **mutation_operators_applied:** {', '.join(results['mutated_genome']['mutation_operators_applied']) if results['mutated_genome']['mutation_operators_applied'] else 'none'}
- **deterministic_seed:** {results['mutated_genome']['deterministic_seed']}

---

## L16 Signal Evidence
- **source service/class:** {results['l16_signal']['source_service_class']}
- **timestamp:** {results['l16_signal']['timestamp']}
- **signal_id:** {results['l16_signal']['signal_id']}

**Key Fields Captured:**
"""
    for field, value in results['l16_signal']['key_fields_captured'].items():
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

## Test Output

**Pytest Status:** Run separately with `pytest tests/layer17/ -v`

**Migration Status:** Run migration with:
```sql
-- Execute migrations/017_layer17_agent_genome_evolution.sql in Supabase
```

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
    report_path = Path(__file__).parent / "layer17_cycle_001.md"
    report_path.write_text(report)

    print(f"\n{'='*60}")
    print(f"CYCLE COMPLETE")
    print(f"{'='*60}")
    print(f"\nReport saved to: {report_path}")

    # Return exit code based on errors
    return 1 if results['errors'] else 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
