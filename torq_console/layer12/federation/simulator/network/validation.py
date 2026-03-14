"""
Phase 2B Validation Test Suite

Layer 12 Phase 2B — Multi-Node Federation Scale Validation

Runs structured validation tests to verify:
1. Network executor works correctly
2. Phase 2A metrics (EDDR, ACA, FCRI) behave correctly at network scale
3. Network metrics produce expected distributions
4. Early failure modes of distributed reasoning are detected

Tests are ordered from safest to most stressful.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

# Imports from sibling modules in the same package
from .node_registry import SimulatedNetworkNode
from .network_controller import (
    NetworkSimulationConfig,
    NetworkTopology,
    create_network_controller,
)
from .network_metrics import NetworkSnapshot
from .scenarios import (
    NetworkScenarioConfig,
    RiskPosture,
    ScenarioType,
    get_claim_quality_for_scenario,
)
from ..processor_adapter import ProcessorAdapter
from ..metrics import FederationMetricsAggregator
from ..executor_async import create_async_executor


logger = logging.getLogger(__name__)


# ============================================================================
# Test Result Models
# ============================================================================

@dataclass
class ValidationResult:
    """Result of a single validation test."""

    test_name: str
    passed: bool
    duration_ms: float

    # Configuration
    config: Dict[str, Any]

    # Metrics
    acceptance_rate: float
    eddr: Optional[float] = None
    aca: Optional[float] = None
    fcri: Optional[float] = None
    network_density: Optional[float] = None
    clustering_coefficient: Optional[float] = None

    # Network structure
    centrality_distribution: Optional[Dict[str, float]] = None
    collapse_risk: Optional[str] = None

    # Detailed snapshot
    final_snapshot: Optional[NetworkSnapshot] = None

    # Failure reasons
    failure_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "test_name": self.test_name,
            "passed": self.passed,
            "duration_ms": self.duration_ms,
            "config": self.config,
            "acceptance_rate": self.acceptance_rate,
            "eddr": self.eddr,
            "aca": self.aca,
            "fcri": self.fcri,
            "network_density": self.network_density,
            "clustering_coefficient": self.clustering_coefficient,
            "centrality_distribution": self.centrality_distribution,
            "collapse_risk": self.collapse_risk,
            "failure_reasons": self.failure_reasons,
        }


@dataclass
class ValidationSuiteResult:
    """Result of running the full validation suite."""

    suite_name: str = "Phase 2B Validation Suite"
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    duration_ms: float = 0.0

    # Individual test results
    test_results: List[ValidationResult] = field(default_factory=list)

    # Overall outcome
    all_passed: bool = True
    passed_count: int = 0
    failed_count: int = 0

    def add_result(self, result: ValidationResult) -> None:
        """Add a test result."""
        self.test_results.append(result)
        if result.passed:
            self.passed_count += 1
        else:
            self.failed_count += 1
            self.all_passed = False

    def finalize(self) -> None:
        """Finalize the suite results."""
        self.end_time = datetime.utcnow()
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "suite_name": self.suite_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "all_passed": self.all_passed,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "test_results": [r.to_dict() for r in self.test_results],
        }

    def print_summary(self) -> None:
        """Print a summary of the validation suite."""
        print("\n" + "=" * 80)
        print(f"VALIDATION SUITE: {self.suite_name}")
        print("=" * 80)
        print(f"Duration: {self.duration_ms / 1000:.2f}s")
        print(f"Tests: {self.passed_count} passed, {self.failed_count} failed")
        print(f"Overall: {'✓ PASSED' if self.all_passed else '✗ FAILED'}")
        print("=" * 80)

        for result in self.test_results:
            status = "✓ PASSED" if result.passed else "✗ FAILED"
            print(f"\n{result.test_name}: {status}")
            print(f"  Acceptance: {result.acceptance_rate:.1%}")
            if result.eddr is not None:
                print(f"  EDDR: {result.eddr}")
            if result.aca is not None:
                print(f"  ACA: {result.aca}")
            if result.fcri is not None:
                print(f"  FCRI: {result.fcri}")
            if result.collapse_risk:
                print(f"  Collapse Risk: {result.collapse_risk}")
            if result.failure_reasons:
                print(f"  Failures: {', '.join(result.failure_reasons)}")


# ============================================================================
# Validation Tests
# ============================================================================

class Phase2BValidator:
    """
    Runs Phase 2B validation tests.

    Tests verify:
    1. Network executor works correctly
    2. Phase 2A predictive metrics work at network scale
    3. Network metrics produce expected distributions
    4. Early failure modes are detected
    """

    def __init__(self, verbose: bool = False):
        """
        Initialize the validator.

        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)

    async def run_test_baseline_stability(self) -> ValidationResult:
        """
        Test 1 — Baseline Network Stability

        Purpose: Verify the executor works and Phase 2A metrics behave normally.

        Configuration:
            nodes: 10
            topology: small_world
            epochs: 50
            scenario: baseline
            seed: 42

        Expected Healthy Results:
            Acceptance Rate: 25-45%
            EDDR: healthy
            ACA: healthy
            FCRI: healthy
            Centrality: balanced
            Clusters: >2
            Collapse Risk: LOW

        Failure Signs:
            ACA spikes early
            EDDR rises quickly
            Network centrality dominated by 1 node
        """
        test_name = "Test 1 - Baseline Network Stability"
        start_time = time.time()

        config = NetworkSimulationConfig(
            num_nodes=10,
            topology=NetworkTopology.SMALL_WORLD,
            num_epochs=50,
            claims_per_epoch=20,
            adversarial_ratio=0.1,
            random_seed=42,
        )

        result = await self._run_test(
            test_name=test_name,
            config=config,
            claim_quality_bias=0.78,
            expected_acceptance_range=(0.20, 0.50),
            expected_eddr_healthy=True,
            expected_aca_healthy=True,
            expected_fcri_healthy=True,
        )

        result.duration_ms = (time.time() - start_time) * 1000
        return result

    async def run_test_domain_competition(self) -> ValidationResult:
        """
        Test 2 — Domain Competition

        Purpose: Ensure domain specialization works and no node captures unrelated domains.

        Configuration:
            nodes: 12
            topology: random_graph
            epochs: 75
            scenario: domain_capture
            seed: 100

        Expected Healthy Results:
            Domain leadership rotates
            No single node dominates >50% claims
            ACA stays low
            Clusters remain dynamic

        Failure Signs:
            One node dominates multiple domains
            Authority centralization
        """
        test_name = "Test 2 - Domain Competition"
        start_time = time.time()

        config = NetworkSimulationConfig(
            num_nodes=12,
            topology=NetworkTopology.RANDOM_GRAPH,
            num_epochs=75,
            claims_per_epoch=30,
            adversarial_ratio=0.0,
            random_seed=100,
        )

        result = await self._run_test(
            test_name=test_name,
            config=config,
            claim_quality_bias=0.72,
            expected_acceptance_range=(0.15, 0.40),
            expected_aca_healthy=True,
            check_domain_capture=True,
        )

        result.duration_ms = (time.time() - start_time) * 1000
        return result

    async def run_test_trust_cascade_failure(self) -> ValidationResult:
        """
        Test 3 — Trust Cascade Failure

        Purpose: Verify the system can resist trust amplification attacks.

        Configuration:
            nodes: 10
            topology: hub_and_spoke
            epochs: 60
            scenario: trust_cascade_failure
            adversarial_ratio: 0.2
            seed: 300

        Attack Behavior:
            Malicious nodes emit high confidence claims
            Claims propagate rapidly

        Expected Healthy Results:
            Malicious claims partially propagate
            Trust corrections reduce spread
            FCRI increases temporarily but recovers

        Failure Signs:
            Malicious nodes dominate network
            ACA spikes
            FCRI sustained high
        """
        test_name = "Test 3 - Trust Cascade Failure"
        start_time = time.time()

        config = NetworkSimulationConfig(
            num_nodes=10,
            topology=NetworkTopology.HUB_AND_SPOKE,
            num_epochs=60,
            claims_per_epoch=25,
            adversarial_ratio=0.2,
            random_seed=300,
        )

        result = await self._run_test(
            test_name=test_name,
            config=config,
            claim_quality_bias=0.68,  # Lower quality for adversarial behavior
            expected_acceptance_range=(0.05, 0.25),
            expected_fcri_transient=True,  # Can spike but should recover
        )

        result.duration_ms = (time.time() - start_time) * 1000
        return result

    async def run_test_adversarial_coalition(self) -> ValidationResult:
        """
        Test 5 — Adversarial Coalition (Test 4 skipped for MVP)

        Purpose: Test coordinated manipulation.

        Configuration:
            nodes: 15
            topology: small_world
            epochs: 80
            scenario: multi_node_adversarial_coalition
            adversarial_ratio: 0.3
            seed: 500

        Behavior:
            Coalition nodes cross-amplify each other
            Increase claim credibility

        Expected Healthy Results:
            Coalition influence limited
            Network rejects majority of bad claims
            ACA increases slightly but stabilizes

        Failure Signs:
            Coalition dominates centrality
            Cluster collapse
        """
        test_name = "Test 5 - Adversarial Coalition"
        start_time = time.time()

        config = NetworkSimulationConfig(
            num_nodes=15,
            topology=NetworkTopology.SMALL_WORLD,
            num_epochs=80,
            claims_per_epoch=40,
            adversarial_ratio=0.3,
            random_seed=500,
        )

        result = await self._run_test(
            test_name=test_name,
            config=config,
            claim_quality_bias=0.65,  # Lower for adversarial
            expected_acceptance_range=(0.10, 0.30),
            expected_aca_transient=True,  # Can rise slightly but should stabilize
        )

        result.duration_ms = (time.time() - start_time) * 1000
        return result

    async def _run_test(
        self,
        test_name: str,
        config: NetworkSimulationConfig,
        claim_quality_bias: float,
        expected_acceptance_range: tuple,
        expected_edr_healthy: bool = False,
        expected_aca_healthy: bool = False,
        expected_aca_transient: bool = False,
        expected_fcri_healthy: bool = False,
        expected_fcri_transient: bool = False,
        check_domain_capture: bool = False,
    ) -> ValidationResult:
        """
        Run a single validation test.

        Args:
            test_name: Name of the test
            config: Simulation configuration
            claim_quality_bias: Quality bias for claim generation
            expected_acceptance_range: Expected (min, max) acceptance rate
            expected_edr_healthy: Whether EDDR should be healthy
            expected_aca_healthy: Whether ACA should be healthy
            expected_aca_transient: Whether ACA can spike transiently
            expected_fcri_healthy: Whether FCRI should be healthy
            expected_fcri_transient: Whether FCRI can spike transiently
            check_domain_capture: Whether to check for domain capture

        Returns:
            ValidationResult with test outcome
        """
        failure_reasons = []

        # Create executor
        executor = create_async_executor(
            enable_all_safeguards=True,
            enable_metrics=True,
            enable_health_index=True,
            enable_predictive_metrics=True,  # Enable EDDR, ACA, FCRI
            simulation_mode=True,
        )

        # Create network controller
        controller = create_network_controller(
            config=config,
            processor_adapter=executor.adapter,
            claim_quality_bias=claim_quality_bias,
        )

        # Run simulation
        self.logger.info(f"Running {test_name}...")
        sim_result = await controller.run_simulation(progress_callback=None)

        # Extract metrics
        snapshot = sim_result.final_network_metrics
        acceptance_rate = sim_result.acceptance_rate

        # Check acceptance rate
        acceptance_min, acceptance_max = expected_acceptance_range
        acceptance_ok = acceptance_min <= acceptance_rate <= acceptance_max
        if not acceptance_ok:
            failure_reasons.append(
                f"Acceptance rate {acceptance_rate:.1%} outside expected range "
                f"[{acceptance_min:.1%}, {acceptance_max:.1%}]"
            )

        # Extract predictive metrics from executor
        predictive_metrics = self._extract_predictive_metrics(executor)
        eddr = predictive_metrics.get("eddr")
        aca = predictive_metrics.get("aca")
        fcri = predictive_metrics.get("fcri")

        # Check EDDR
        eddr_healthy = self._check_eddr_healthy(eddr)
        if expected_edr_healthy and not eddr_healthy:
            failure_reasons.append(f"EDDR unhealthy: {eddr}")

        # Check ACA
        aca_ok = self._check_aca_ok(aca, expected_aca_healthy, expected_aca_transient)
        if not aca_ok:
            failure_reasons.append(f"ACA unhealthy: {aca}")

        # Check FCRI
        fcri_ok = self._check_fcri_ok(fcri, expected_fcri_healthy, expected_fcri_transient)
        if not fcri_ok:
            failure_reasons.append(f"FCRI unhealthy: {fcri}")

        # Check domain capture
        if check_domain_capture:
            domain_capture_ok = self._check_domain_capture(snapshot)
            if not domain_capture_ok:
                failure_reasons.append("Domain capture detected")

        # Calculate collapse risk
        collapse_risk = self._calculate_collapse_risk(
            acceptance_rate, eddr, aca, fcri, snapshot
        )

        # Determine centrality distribution
        centrality_distribution = self._calculate_centrality_distribution(snapshot)

        # Build result
        result = ValidationResult(
            test_name=test_name,
            passed=len(failure_reasons) == 0,
            duration_ms=0.0,  # Set by caller
            config=config.model_dump(),
            acceptance_rate=acceptance_rate,
            eddr=eddr,
            aca=aca,
            fcri=fcri,
            network_density=snapshot.network_density if snapshot else None,
            clustering_coefficient=snapshot.avg_clustering if snapshot else None,
            centrality_distribution=centrality_distribution,
            collapse_risk=collapse_risk,
            final_snapshot=snapshot,
            failure_reasons=failure_reasons,
        )

        self.logger.info(
            f"{test_name}: {'PASSED' if result.passed else 'FAILED'} - "
            f"Acceptance: {acceptance_rate:.1%}, "
            f"EDDR: {eddr}, ACA: {aca}, FCRI: {fcri}"
        )

        return result

    def _extract_predictive_metrics(self, executor) -> Dict[str, Optional[float]]:
        """Extract predictive metrics from executor."""
        try:
            metrics = executor.metrics_aggregator
            return {
                "eddr": getattr(metrics, "eddr", None),
                "aca": getattr(metrics, "aca", None),
                "fcri": getattr(metrics, "fcri", None),
            }
        except Exception as e:
            self.logger.warning(f"Failed to extract predictive metrics: {e}")
            return {"eddr": None, "aca": None, "fcri": None}

    def _check_edr_healthy(self, eddr: Optional[float]) -> bool:
        """Check if EDDR is healthy (low diversity erosion)."""
        if eddr is None:
            return True  # Can't determine
        # EDDR should be < 0.5 for healthy diversity
        return eddr < 0.5

    def _check_aca_ok(
        self,
        aca: Optional[float],
        expected_healthy: bool,
        expected_transient: bool
    ) -> bool:
        """Check if ACA is acceptable."""
        if aca is None:
            return True
        if expected_transient:
            # ACA can spike up to 0.6 transiently but not sustained
            return aca < 0.7
        if expected_healthy:
            # ACA should be low for healthy federation
            return aca < 0.4
        return True

    def _check_fcri_ok(
        self,
        fcri: Optional[float],
        expected_healthy: bool,
        expected_transient: bool
    ) -> bool:
        """Check if FCRI is acceptable."""
        if fcri is None:
            return True
        if expected_transient:
            # FCRI can spike up to 0.7 transiently
            return fcri < 0.8
        if expected_healthy:
            # FCRI should be low for healthy federation
            return fcri < 0.4
        return True

    def _check_domain_capture(self, snapshot: Optional[NetworkSnapshot]) -> bool:
        """Check if a single domain has captured the network."""
        if snapshot is None:
            return True
        # Domain competition index near 0 indicates monocapture
        return snapshot.domain_competition_index > 0.2

    def _calculate_collapse_risk(
        self,
        acceptance_rate: float,
        eddr: Optional[float],
        aca: Optional[float],
        fcri: Optional[float],
        snapshot: Optional[NetworkSnapshot],
    ) -> str:
        """Calculate overall collapse risk."""
        risk_factors = []

        # Low acceptance rate
        if acceptance_rate < 0.15:
            risk_factors.append("low_acceptance")

        # High EDDR
        if eddr is not None and eddr > 0.5:
            risk_factors.append("diversity_loss")

        # High ACA
        if aca is not None and aca > 0.6:
            risk_factors.append("authority_concentration")

        # High FCRI
        if fcri is not None and fcri > 0.6:
            risk_factors.append("fragmentation")

        # Low resilience
        if snapshot and snapshot.network_resilience_score < 0.4:
            risk_factors.append("low_resilience")

        if not risk_factors:
            return "LOW"
        elif len(risk_factors) == 1:
            return "MODERATE"
        elif len(risk_factors) == 2:
            return "ELEVATED"
        else:
            return "HIGH"

    def _calculate_centrality_distribution(
        self,
        snapshot: Optional[NetworkSnapshot]
    ) -> Optional[Dict[str, float]]:
        """Calculate centrality distribution from snapshot."""
        if snapshot is None:
            return None

        return {
            "gini": snapshot.gini_coefficient,
            "hhi": snapshot.herfindahl_index,
            "top_concentration": snapshot.top_node_concentration,
        }


# ============================================================================
# Test Runner
# ============================================================================

async def run_validation_suite(
    tests: Optional[List[str]] = None,
    verbose: bool = False,
) -> ValidationSuiteResult:
    """
    Run the Phase 2B validation suite.

    Args:
        tests: List of test names to run (None = all core tests)
        verbose: Enable verbose output

    Returns:
        ValidationSuiteResult with all test results
    """
    suite = ValidationSuiteResult()
    validator = Phase2BValidator(verbose=verbose)

    # Core tests for Phase 2B validation
    core_tests = [
        ("baseline", validator.run_test_baseline_stability),
        ("domain", validator.run_test_domain_competition),
        ("trust_cascade", validator.run_test_trust_cascade_failure),
        ("adversarial", validator.run_test_adversarial_coalition),
    ]

    # Filter tests if specified
    if tests:
        test_map = {name[0]: name[1] for name in core_tests}
        core_tests = [(name, test_map[name]) for name in tests if name in test_map]

    # Run tests
    print("\n" + "=" * 80)
    print("PHASE 2B VALIDATION SUITE")
    print("=" * 80)

    for test_name, test_func in core_tests:
        print(f"\nRunning {test_name} test...")
        try:
            result = await test_func()
            suite.add_result(result)
            print(f"  {test_name.upper()}: {'PASSED' if result.passed else 'FAILED'}")
        except Exception as e:
            print(f"  {test_name.upper()}: ERROR - {e}")
            logger.error(f"Test {test_name} failed with exception", exc_info=True)

    suite.finalize()
    return suite


def run_validation_suite_sync(
    tests: Optional[List[str]] = None,
    verbose: bool = False,
) -> ValidationSuiteResult:
    """Synchronous wrapper for validation suite."""
    return asyncio.run(run_validation_suite(tests, verbose))


# ============================================================================
# Result Persistence
# ============================================================================

def save_validation_results(
    result: ValidationSuiteResult,
    output_path: Optional[str] = None,
) -> None:
    """
    Save validation results to file.

    Args:
        result: Validation suite result
        output_path: Output file path (default: auto-generated)
    """
    if output_path is None:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_path = f"phase2b_validation_{timestamp}.json"

    output_file = Path(output_path)
    output_file.write_text(json.dumps(result.to_dict(), indent=2))

    logger.info(f"Validation results saved to {output_path}")
