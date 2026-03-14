#!/usr/bin/env python3
"""
Phase 2B Validation Tests - Simplified Runner

Direct test runner without complex module imports to avoid caching issues.

Runs 4 core validation tests:
1. Baseline Network Stability
2. Domain Competition
3. Trust Cascade Failure
4. Adversarial Coalition
"""

import asyncio
import json
import logging
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Setup path
_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent.parent.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from torq_console.layer12.federation.simulator.executor_async import create_async_executor
from torq_console.layer12.federation.simulator.network.network_controller import create_network_controller
from torq_console.layer12.federation.simulator.network import NetworkSimulationConfig, NetworkTopology


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Result of a validation test."""
    test_name: str
    passed: bool
    duration_ms: float
    acceptance_rate: float
    claims_processed: int
    claims_accepted: int
    network_density: float
    clustering_coefficient: float
    resilience_score: float
    failure_reasons: List[str] = field(default_factory=list)


async def run_baseline_test() -> TestResult:
    """
    Test 1 - Baseline Network Stability

    Configuration:
        nodes: 10
        topology: small_world
        epochs: 50
        seed: 42
        claim_quality_bias: 0.78

    Expected:
        Acceptance Rate: 20-50%
        Resilience: > 0.5
        Density: 0.3-0.6
    """
    test_name = "Test 1 - Baseline Network Stability"
    start_time = time.time()
    failure_reasons = []

    config = NetworkSimulationConfig(
        num_nodes=10,
        topology=NetworkTopology.SMALL_WORLD,
        num_epochs=50,
        claims_per_epoch=20,
        adversarial_ratio=0.1,
        random_seed=42,
    )

    executor = create_async_executor(
        enable_all_safeguards=True,
        enable_metrics=True,
        enable_health_index=True,
        enable_predictive_metrics=True,
        simulation_mode=True,
    )

    controller = create_network_controller(
        config=config,
        processor_adapter=executor.adapter,
        claim_quality_bias=0.78,
    )

    print(f"\n{'='*80}")
    print(f"Running: {test_name}")
    print(f"{'='*80}")

    result = await controller.run_simulation(progress_callback=None)

    # Extract metrics
    acceptance_rate = result.acceptance_rate
    snapshot = result.final_network_metrics

    # Check acceptance rate
    if not (0.20 <= acceptance_rate <= 0.50):
        failure_reasons.append(
            f"Acceptance {acceptance_rate:.1%} outside expected range [20%, 50%]"
        )

    # Check resilience
    if snapshot and snapshot.network_resilience_score < 0.5:
        failure_reasons.append(
            f"Resilience {snapshot.network_resilience_score:.2f} below threshold 0.5"
        )

    duration_ms = (time.time() - start_time) * 1000

    return TestResult(
        test_name=test_name,
        passed=len(failure_reasons) == 0,
        duration_ms=duration_ms,
        acceptance_rate=acceptance_rate,
        claims_processed=result.total_claims_processed,
        claims_accepted=result.total_claims_accepted,
        network_density=snapshot.network_density if snapshot else 0,
        clustering_coefficient=snapshot.avg_clustering if snapshot else 0,
        resilience_score=snapshot.network_resilience_score if snapshot else 0,
        failure_reasons=failure_reasons,
    )


async def run_domain_competition_test() -> TestResult:
    """
    Test 2 - Domain Competition

    Configuration:
        nodes: 12
        topology: random_graph
        epochs: 75
        seed: 100
        claim_quality_bias: 0.72

    Expected:
        Acceptance Rate: 15-40%
        No single node dominates >50% claims
        Domain competition index > 0.2
    """
    test_name = "Test 2 - Domain Competition"
    start_time = time.time()
    failure_reasons = []

    config = NetworkSimulationConfig(
        num_nodes=12,
        topology=NetworkTopology.RANDOM_GRAPH,
        num_epochs=75,
        claims_per_epoch=30,
        adversarial_ratio=0.0,
        random_seed=100,
    )

    executor = create_async_executor(
        enable_all_safeguards=True,
        enable_metrics=True,
        enable_health_index=True,
        enable_predictive_metrics=True,
        simulation_mode=True,
    )

    controller = create_network_controller(
        config=config,
        processor_adapter=executor.adapter,
        claim_quality_bias=0.72,
    )

    print(f"\n{'='*80}")
    print(f"Running: {test_name}")
    print(f"{'='*80}")

    result = await controller.run_simulation(progress_callback=None)

    acceptance_rate = result.acceptance_rate
    snapshot = result.final_network_metrics

    # Check acceptance rate
    if not (0.15 <= acceptance_rate <= 0.40):
        failure_reasons.append(
            f"Acceptance {acceptance_rate:.1%} outside expected range [15%, 40%]"
        )

    # Check domain competition (should not be monoculture)
    if snapshot and snapshot.domain_competition_index < 0.2:
        failure_reasons.append(
            f"Domain competition {snapshot.domain_competition_index:.2f} indicates monoculture"
        )

    # Check top node concentration (should not dominate)
    if snapshot and snapshot.top_node_concentration > 0.5:
        failure_reasons.append(
            f"Top node concentration {snapshot.top_node_concentration:.1%} > 50%"
        )

    duration_ms = (time.time() - start_time) * 1000

    return TestResult(
        test_name=test_name,
        passed=len(failure_reasons) == 0,
        duration_ms=duration_ms,
        acceptance_rate=acceptance_rate,
        claims_processed=result.total_claims_processed,
        claims_accepted=result.total_claims_accepted,
        network_density=snapshot.network_density if snapshot else 0,
        clustering_coefficient=snapshot.avg_clustering if snapshot else 0,
        resilience_score=snapshot.network_resilience_score if snapshot else 0,
        failure_reasons=failure_reasons,
    )


async def run_trust_cascade_test() -> TestResult:
    """
    Test 3 - Trust Cascade Failure

    Configuration:
        nodes: 10
        topology: hub_and_spoke
        epochs: 60
        adversarial_ratio: 0.2
        seed: 300
        claim_quality_bias: 0.68

    Expected:
        Acceptance Rate: 5-25% (lower due to adversarial)
        Resilience should recover (not stay <0.3)
    """
    test_name = "Test 3 - Trust Cascade Failure"
    start_time = time.time()
    failure_reasons = []

    config = NetworkSimulationConfig(
        num_nodes=10,
        topology=NetworkTopology.HUB_AND_SPOKE,
        num_epochs=60,
        claims_per_epoch=25,
        adversarial_ratio=0.2,
        random_seed=300,
    )

    executor = create_async_executor(
        enable_all_safeguards=True,
        enable_metrics=True,
        enable_health_index=True,
        enable_predictive_metrics=True,
        simulation_mode=True,
    )

    controller = create_network_controller(
        config=config,
        processor_adapter=executor.adapter,
        claim_quality_bias=0.68,
    )

    print(f"\n{'='*80}")
    print(f"Running: {test_name}")
    print(f"{'='*80}")

    result = await controller.run_simulation(progress_callback=None)

    acceptance_rate = result.acceptance_rate
    snapshot = result.final_network_metrics

    # Check acceptance rate (lower due to adversarial)
    if not (0.05 <= acceptance_rate <= 0.25):
        failure_reasons.append(
            f"Acceptance {acceptance_rate:.1%} outside expected range [5%, 25%]"
        )

    # Check resilience (should not completely collapse)
    if snapshot and snapshot.network_resilience_score < 0.3:
        failure_reasons.append(
            f"Resilience {snapshot.network_resilience_score:.2f} indicates collapse"
        )

    duration_ms = (time.time() - start_time) * 1000

    return TestResult(
        test_name=test_name,
        passed=len(failure_reasons) == 0,
        duration_ms=duration_ms,
        acceptance_rate=acceptance_rate,
        claims_processed=result.total_claims_processed,
        claims_accepted=result.total_claims_accepted,
        network_density=snapshot.network_density if snapshot else 0,
        clustering_coefficient=snapshot.avg_clustering if snapshot else 0,
        resilience_score=snapshot.network_resilience_score if snapshot else 0,
        failure_reasons=failure_reasons,
    )


async def run_adversarial_coalition_test() -> TestResult:
    """
    Test 5 - Adversarial Coalition

    Configuration:
        nodes: 15
        topology: small_world
        epochs: 80
        adversarial_ratio: 0.3
        seed: 500
        claim_quality_bias: 0.65

    Expected:
        Acceptance Rate: 10-30%
        Coalition influence limited
    """
    test_name = "Test 5 - Adversarial Coalition"
    start_time = time.time()
    failure_reasons = []

    config = NetworkSimulationConfig(
        num_nodes=15,
        topology=NetworkTopology.SMALL_WORLD,
        num_epochs=80,
        claims_per_epoch=40,
        adversarial_ratio=0.3,
        random_seed=500,
    )

    executor = create_async_executor(
        enable_all_safeguards=True,
        enable_metrics=True,
        enable_health_index=True,
        enable_predictive_metrics=True,
        simulation_mode=True,
    )

    controller = create_network_controller(
        config=config,
        processor_adapter=executor.adapter,
        claim_quality_bias=0.65,
    )

    print(f"\n{'='*80}")
    print(f"Running: {test_name}")
    print(f"{'='*80}")

    result = await controller.run_simulation(progress_callback=None)

    acceptance_rate = result.acceptance_rate
    snapshot = result.final_network_metrics

    # Check acceptance rate
    if not (0.10 <= acceptance_rate <= 0.30):
        failure_reasons.append(
            f"Acceptance {acceptance_rate:.1%} outside expected range [10%, 30%]"
        )

    # Check resilience (should not collapse completely)
    if snapshot and snapshot.network_resilience_score < 0.4:
        failure_reasons.append(
            f"Resilience {snapshot.network_resilience_score:.2f} indicates collapse"
        )

    duration_ms = (time.time() - start_time) * 1000

    return TestResult(
        test_name=test_name,
        passed=len(failure_reasons) == 0,
        duration_ms=duration_ms,
        acceptance_rate=acceptance_rate,
        claims_processed=result.total_claims_processed,
        claims_accepted=result.total_claims_accepted,
        network_density=snapshot.network_density if snapshot else 0,
        clustering_coefficient=snapshot.avg_clustering if snapshot else 0,
        resilience_score=snapshot.network_resilience_score if snapshot else 0,
        failure_reasons=failure_reasons,
    )


async def run_validation_suite(tests: Optional[List[str]] = None) -> List[TestResult]:
    """Run the Phase 2B validation suite."""

    # Define all tests
    all_tests = [
        ("baseline", run_baseline_test),
        ("domain", run_domain_competition_test),
        ("trust_cascade", run_trust_cascade_test),
        ("adversarial", run_adversarial_coalition_test),
    ]

    # Filter if specified
    if tests:
        test_map = {name[0]: name[1] for name in all_tests}
        all_tests = [(name, test_map[name]) for name in tests if name in test_map]

    results = []

    print("\n" + "="*80)
    print("PHASE 2B VALIDATION TEST SUITE")
    print("="*80)

    for test_name, test_func in all_tests:
        try:
            result = await test_func()
            results.append(result)

            status = "[PASSED]" if result.passed else "[FAILED]"
            print(f"{test_name.upper()}: {status}")
            print(f"  Acceptance: {result.acceptance_rate:.1%}")
            print(f"  Resilience: {result.resilience_score:.2f}")
            print(f"  Density: {result.network_density:.2f}")

            if result.failure_reasons:
                print(f"  Failures: {', '.join(result.failure_reasons)}")

        except Exception as e:
            logger.error(f"Test {test_name} failed: {e}", exc_info=True)
            results.append(TestResult(
                test_name=test_name,
                passed=False,
                duration_ms=0,
                acceptance_rate=0,
                claims_processed=0,
                claims_accepted=0,
                network_density=0,
                clustering_coefficient=0,
                resilience_score=0,
                failure_reasons=[str(e)],
            ))

    # Print summary
    print("\n" + "="*80)
    print("VALIDATION SUITE SUMMARY")
    print("="*80)

    passed = sum(1 for r in results if r.passed)
    total = len(results)

    print(f"Tests: {passed}/{total} passed")

    for result in results:
        status = "[PASSED]" if result.passed else "[FAILED]"
        print(f"  {result.test_name}: {status} ({result.duration_ms/1000:.2f}s)")

    if all(r.passed for r in results):
        print("\n[SUCCESS] PHASE 2B VALIDATION COMPLETE - All tests passed!")
    else:
        print("\n[WARNING] Some tests failed - review above for details")

    return results


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Run Phase 2B validation tests")
    parser.add_argument(
        "--tests",
        nargs="+",
        choices=["baseline", "domain", "trust_cascade", "adversarial", "all"],
        help="Tests to run (default: all)"
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save results to JSON file"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output file path"
    )

    args = parser.parse_args()

    # Determine which tests to run
    if args.tests and "all" in args.tests:
        tests = None  # Run all
    else:
        tests = args.tests if args.tests else None

    # Run tests
    results = asyncio.run(run_validation_suite(tests))

    # Save results if requested
    if args.save:
        output_path = args.output or f"phase2b_validation_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        output_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "results": [
                {
                    "test_name": r.test_name,
                    "passed": r.passed,
                    "duration_ms": r.duration_ms,
                    "acceptance_rate": r.acceptance_rate,
                    "claims_processed": r.claims_processed,
                    "claims_accepted": r.claims_accepted,
                    "network_density": r.network_density,
                    "clustering_coefficient": r.clustering_coefficient,
                    "resilience_score": r.resilience_score,
                    "failure_reasons": r.failure_reasons,
                }
                for r in results
            ],
        }

        Path(output_path).write_text(json.dumps(output_data, indent=2))
        print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    main()
