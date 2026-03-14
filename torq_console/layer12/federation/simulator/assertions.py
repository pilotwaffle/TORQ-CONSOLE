"""
Federation Simulation Assertions

Layer 12 Phase 2A — Federation Stability Validation Harness

Validation assertions for testing safeguard effectiveness and expected behaviors.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum

from .models import SimulatedClaim, SimulatedNode, SimulationScenario, SimulationMetrics, SimulationReport

logger = logging.getLogger(__name__)


# ============================================================================
# Assertion Types
# ============================================================================

class AssertionType(Enum):
    """Types of assertions."""
    METRIC_THRESHOLD = "metric_threshold"
    SAFEGUARD_TRIGGER = "safeguard_trigger"
    BEHAVIORAL_PATTERN = "behavioral_pattern"
    DISTRIBUTION_PROPERTY = "distribution_property"
    CONSTRAINT_VIOLATION = "constraint_violation"


class AssertionStatus(Enum):
    """Assertion result status."""
    PASSED = "passed"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class AssertionResult:
    """Result of an assertion check."""
    assertion_id: str
    status: AssertionStatus
    message: str
    expected_value: Any
    actual_value: Any
    details: Dict[str, Any] = None


# ============================================================================
# Base Assertion
# ============================================================================

class Assertion:
    """Base class for simulation assertions."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"{__name__}.{name}")

    def check(self, simulation_data: Dict[str, Any]) -> AssertionResult:
        """Check the assertion. Override in subclasses."""
        raise NotImplementedError

    def _create_result(
        self,
        status: AssertionStatus,
        message: str,
        expected: Any = None,
        actual: Any = None,
        details: Optional[Dict[str, Any]] = None
    ) -> AssertionResult:
        """Create an assertion result."""
        return AssertionResult(
            assertion_id=self.name,
            status=status,
            message=message,
            expected_value=expected,
            actual_value=actual,
            details=details or {}
        )


# ============================================================================
# Metric Threshold Assertions
# ============================================================================

class MetricThresholdAssertion(Assertion):
    """Assert that a metric meets a threshold requirement."""

    def __init__(
        self,
        name: str,
        metric_name: str,
        min_threshold: float = None,
        max_threshold: float = None,
        description: str = None
    ):
        super().__init__(
            name,
            description or f"{metric_name} should be within [{min_threshold}, {max_threshold}]"
        )
        self.metric_name = metric_name
        self.min_threshold = min_threshold
        self.max_threshold = max_threshold

    def check(self, simulation_data: Dict[str, Any]) -> AssertionResult:
        """Check if metric meets threshold."""
        # Get metrics from simulation data
        metrics = simulation_data.get("metrics", {})

        # Get metric value
        metric_value = None
        if isinstance(metrics, SimulationMetrics):
            # Direct SimulationMetrics object
            metric_value = getattr(metrics, self.metric_name, None)
        elif isinstance(metrics, dict):
            # Nested dictionary
            metric_value = metrics.get(self.metric_name, None)

        if metric_value is None:
            return self._create_result(
                AssertionStatus.UNKNOWN,
                f"Metric {self.metric_name} not found in simulation data",
                expected=f"Metric {self.metric_name}",
                actual="Not found"
            )

        # Check thresholds
        details = {
            "metric_name": self.metric_name,
            "metric_value": metric_value,
            "min_threshold": self.min_threshold,
            "max_threshold": self.max_threshold,
        }

        # Check minimum threshold
        if self.min_threshold is not None and metric_value < self.min_threshold:
            return self._create_result(
                AssertionStatus.FAILED,
                f"{self.metric_name} {metric_value:.3f} is below minimum threshold {self.min_threshold}",
                self.min_threshold,
                metric_value,
                details=details
            )

        # Check maximum threshold
        if self.max_threshold is not None and metric_value > self.max_threshold:
            return self._create_result(
                AssertionStatus.FAILED,
                f"{self.metric_name} {metric_value:.3f} exceeds maximum threshold {self.max_threshold}",
                self.max_threshold,
                metric_value,
                details=details
            )

        # Passed
        return self._create_result(
            AssertionStatus.PASSED,
            f"{self.metric_name} {metric_value:.3f} meets threshold requirements",
            expected=f"[{self.min_threshold}, {self.max_threshold}]",
            actual=metric_value,
            details=details
        )


# ============================================================================
# Safeguard Trigger Assertions
# ============================================================================

class SafeguardTriggerAssertion(Assertion):
    """Assert that safeguards trigger appropriately."""

    def __init__(
        self,
        name: str,
        safeguard_name: str,
        min_triggers: int = None,
        max_triggers: int = None,
        description: str = None
    ):
        super().__init__(
            name,
            description or f"{safeguard_name} should trigger between [{min_triggers}, {max_triggers}] times"
        )
        self.safeguard_name = safeguard_name
        self.min_triggers = min_triggers
        self.max_triggers = max_triggers

    def check(self, simulation_data: Dict[str, Any]) -> AssertionResult:
        """Check safeguard trigger count."""
        # Get safeguard triggers from simulation data
        triggers = simulation_data.get("safeguard_triggers", {})
        trigger_count = triggers.get(self.safeguard_name, 0)

        details = {
            "safeguard_name": self.safeguard_name,
            "trigger_count": trigger_count,
            "min_triggers": self.min_triggers,
            "max_triggers": self.max_triggers,
        }

        # Check minimum triggers
        if self.min_triggers is not None and trigger_count < self.min_triggers:
            return self._create_result(
                AssertionStatus.FAILED,
                f"{self.safeguard_name} triggered {trigger_count} times, expected at least {self.min_triggers}",
                self.min_triggers,
                trigger_count,
                details=details
            )

        # Check maximum triggers
        if self.max_triggers is not None and trigger_count > self.max_triggers:
            return self._create_result(
                AssertionStatus.FAILED,
                f"{self.safeguard_name} triggered {trigger_count} times, expected at most {self.max_triggers}",
                self.max_triggers,
                trigger_count,
                details=details
            )

        # Passed
        return self._create_result(
            AssertionStatus.PASSED,
            f"{self.safeguard_name} triggered {trigger_count} times - within expected range",
            expected=f"[{self.min_triggers}, {self.max_triggers}]",
            actual=trigger_count,
            details=details
        )


# ============================================================================
# Behavioral Pattern Assertions
# ============================================================================

class BehavioralPatternAssertion(Assertion):
    """Assert specific behavioral patterns are observed."""

    def __init__(
        self,
        name: str,
        pattern_type: str,
        expected_behavior: str,
        parameters: Dict[str, Any] = None,
        description: str = None
    ):
        super().__init__(
            name,
            description or f"Should exhibit {expected_behavior} pattern"
        )
        self.pattern_type = pattern_type
        self.expected_behavior = expected_behavior
        self.parameters = parameters or {}

    def check(self, simulation_data: Dict[str, Any]) -> AssertionResult:
        """Check for behavioral patterns."""
        # Extract simulation data
        rounds = simulation_data.get("rounds", [])
        metrics = simulation_data.get("metrics", {})

        details = {
            "pattern_type": self.pattern_type,
            "expected_behavior": self.expected_behavior,
            "parameters": self.parameters,
        }

        if self.pattern_type == "resilience":
            return self._check_resilience_pattern(rounds, details)
        elif self.pattern_type == "recovery":
            return self._check_recovery_pattern(rounds, details)
        elif self.pattern_type == "adaptation":
            return self._check_adaptation_pattern(rounds, details)
        else:
            return self._create_result(
                AssertionStatus.UNKNOWN,
                f"Unknown pattern type: {self.pattern_type}",
                expected="Valid pattern type",
                actual=self.pattern_type,
                details=details
            )

    def _check_resilience_pattern(self, rounds: List[Dict], details: Dict) -> AssertionResult:
        """Check resilience pattern."""
        # Find any degradation below threshold
        degraded_rounds = [
            r for r in rounds
            if r.get("overall_health", 1.0) < 0.70
        ]

        if not degraded_rounds:
            return self._create_result(
                AssertionStatus.PASSED,
                "No degradation observed - system maintained resilience",
                expected="No degradation",
                actual="No degradation",
                details=details
            )

        # Check if system recovered within expected rounds
        max_degradation = min(r.get("overall_health", 0.0) for r in degraded_rounds)
        recovery_threshold = self.parameters.get("recovery_threshold", 0.80)

        if max_degradation >= recovery_threshold:
            return self._create_result(
                AssertionStatus.PASSED,
                f"System degraded but recovered to acceptable level ({max_degradation:.2f})",
                expected=f"Recovery >= {recovery_threshold}",
                actual=f"{max_degradation:.2f}",
                details=details
            )
        else:
            return self._create_result(
                AssertionStatus.FAILED,
                f"System degradation too severe - did not recover to {recovery_threshold}",
                recovery_threshold,
                max_degradation,
                details=details
            )

    def _check_recovery_pattern(self, rounds: List[Dict], details: Dict) -> AssertionResult:
        """Check recovery pattern."""
        if len(rounds) < 3:
            return self._create_result(
                AssertionStatus.UNKNOWN,
                "Insufficient rounds to analyze recovery pattern",
                expected=">= 3 rounds",
                actual=len(rounds),
                details=details
            )

        # Find recovery points (health increase after degradation)
        recovery_points = []
        for i in range(1, len(rounds)):
            prev_health = rounds[i-1].get("overall_health", 0.0)
            curr_health = rounds[i].get("overall_health", 0.0)

            if prev_health < 0.70 and curr_health >= 0.80:
                recovery_points.append(i)

        if not recovery_points:
            return self._create_result(
                AssertionStatus.FAILED,
                "No recovery points detected - system did not recover from degradation",
                expected="Recovery points",
                actual="None",
                details=details
            )

        # Check recovery speed
        max_recovery_time = max(recovery_points) if recovery_points else 0
        max_acceptable_time = self.parameters.get("max_recovery_time", 5)

        if max_recovery_time <= max_acceptable_time:
            return self._create_result(
                AssertionStatus.PASSED,
                f"System recovered within {max_recovery_time} rounds",
                expected=f"<= {max_acceptable_time} rounds",
                actual=max_recovery_time,
                details=details
            )
        else:
            return self._create_result(
                AssertionStatus.FAILED,
                f"Recovery took {max_recovery_time} rounds - exceeds acceptable limit",
                max_acceptable_time,
                max_recovery_time,
                details=details
            )

    def _check_adaptation_pattern(self, rounds: List[Dict], details: Dict) -> AssertionResult:
        """Check adaptation pattern."""
        if len(rounds) < 5:
            return self._create_result(
                AssertionStatus.UNKNOWN,
                "Insufficient rounds to analyze adaptation pattern",
                expected=">= 5 rounds",
                actual=len(rounds),
                details=details
            )

        # Check if system adapts to changing conditions
        adaptation_window = self.parameters.get("adaptation_window", 3)
        adaptation_threshold = self.parameters.get("adaptation_threshold", 0.10)

        adaptations = []
        for i in range(adaptation_window, len(rounds)):
            window_health = sum(r.get("overall_health", 0.0) for r in rounds[i-adaptation_window:i])
            current_health = rounds[i].get("overall_health", 0.0)

            if abs(current_health - (window_health / adaptation_window)) > adaptation_threshold:
                adaptations.append(i)

        if len(adaptations) >= 2:  # Should adapt multiple times
            return self._create_result(
                AssertionStatus.PASSED,
                f"System adapted {len(adaptations)} times to changing conditions",
                expected="Multiple adaptations",
                actual=len(adaptations),
                details=details
            )
        else:
            return self._create_result(
                AssertionStatus.FAILED,
                f"System adapted only {len(adaptations)} times - insufficient adaptation",
                expected=">= 2 adaptations",
                actual=len(adaptations),
                details=details
            )


# ============================================================================
# Distribution Property Assertions
# ============================================================================

class DistributionPropertyAssertion(Assertion):
    """Assert distribution properties like balance, diversity, etc."""

    def __init__(
        self,
        name: str,
        property_name: str,
        expected_value: Any,
        tolerance: float = 0.1,
        description: str = None
    ):
        super().__init__(
            name,
            description or f"Should have {property_name} of {expected_value} ± {tolerance}"
        )
        self.property_name = property_name
        self.expected_value = expected_value
        self.tolerance = tolerance

    def check(self, simulation_data: Dict[str, Any]) -> AssertionResult:
        """Check distribution property."""
        # Get distribution data
        distributions = simulation_data.get("distributions", {})
        actual_value = distributions.get(self.property_name)

        if actual_value is None:
            # Try to extract from metrics
            metrics = simulation_data.get("metrics", {})
            if isinstance(metrics, dict):
                actual_value = metrics.get(self.property_name)
            elif hasattr(metrics, self.property_name):
                actual_value = getattr(metrics, self.property_name)

        if actual_value is None:
            return self._create_result(
                AssertionStatus.UNKNOWN,
                f"Distribution property {self.property_name} not found",
                expected=self.expected_value,
                actual="Not found"
            )

        # Check with tolerance
        lower_bound = self.expected_value - self.tolerance
        upper_bound = self.expected_value + self.tolerance

        if lower_bound <= actual_value <= upper_bound:
            return self._create_result(
                AssertionStatus.PASSED,
                f"{self.property_name} {actual_value:.3f} is within expected range [{lower_bound:.3f}, {upper_bound:.3f}]",
                expected=f"{self.expected_value:.3f} ± {self.tolerance}",
                actual=actual_value
            )
        else:
            return self._create_result(
                AssertionStatus.FAILED,
                f"{self.property_name} {actual_value:.3f} is outside expected range [{lower_bound:.3f}, {upper_bound:.3f}]",
                expected=f"{self.expected_value:.3f} ± {self.tolerance}",
                actual=actual_value
            )


# ============================================================================
# Constraint Violation Assertions
# ============================================================================

class ConstraintViolationAssertion(Assertion):
    """Assert that constraints are not violated."""

    def __init__(
        self,
        name: str,
        constraint_name: str,
        description: str = None
    ):
        super().__init__(
            name,
            description or f"Should not violate {constraint_name} constraint"
        )
        self.constraint_name = constraint_name

    def check(self, simulation_data: Dict[str, Any]) -> AssertionResult:
        """Check for constraint violations."""
        # Get constraint violations
        violations = simulation_data.get("constraint_violations", [])

        relevant_violations = [
            v for v in violations
            if self.constraint_name in v.get("constraint_types", [])
        ]

        if not relevant_violations:
            return self._create_result(
                AssertionStatus.PASSED,
                f"No {self.constraint_name} violations detected",
                expected="No violations",
                actual=0
            )
        else:
            return self._create_result(
                AssertionStatus.FAILED,
                f"{len(relevant_violations)} {self.constraint_name} violations detected",
                expected=0,
                actual=len(relevant_violations),
                details={"violations": relevant_violations}
            )


# ============================================================================
# Assertion Registry
# ============================================================================

class AssertionRegistry:
    """Registry and runner for simulation assertions."""

    def __init__(self):
        self.assertions: Dict[str, Assertion] = {}
        self.results: List[AssertionResult] = []
        self.logger = logging.getLogger(__name__)

    def register(self, assertion: Assertion) -> None:
        """Register an assertion."""
        self.assertions[assertion.name] = assertion
        self.logger.info(f"Registered assertion: {assertion.name}")

    def register_metric_threshold(
        self,
        name: str,
        metric_name: str,
        min_threshold: float = None,
        max_threshold: float = None,
        description: str = None
    ) -> None:
        """Register a metric threshold assertion."""
        assertion = MetricThresholdAssertion(
            name,
            metric_name,
            min_threshold,
            max_threshold,
            description
        )
        self.register(assertion)

    def register_safeguard_trigger(
        self,
        name: str,
        safeguard_name: str,
        min_triggers: int = None,
        max_triggers: int = None,
        description: str = None
    ) -> None:
        """Register a safeguard trigger assertion."""
        assertion = SafeguardTriggerAssertion(
            name,
            safeguard_name,
            min_triggers,
            max_triggers,
            description
        )
        self.register(assertion)

    def register_behavioral_pattern(
        self,
        name: str,
        pattern_type: str,
        expected_behavior: str,
        parameters: Dict[str, Any] = None,
        description: str = None
    ) -> None:
        """Register a behavioral pattern assertion."""
        assertion = BehavioralPatternAssertion(
            name,
            pattern_type,
            expected_behavior,
            parameters,
            description
        )
        self.register(assertion)

    def run_all_assertions(self, simulation_data: Dict[str, Any]) -> List[AssertionResult]:
        """Run all registered assertions."""
        self.results = []

        for assertion in self.assertions.values():
            try:
                result = assertion.check(simulation_data)
                self.results.append(result)

                self.logger.info(
                    f"Assertion {result.assertion_id}: {result.status.value} - {result.message}"
                )

            except Exception as e:
                error_result = AssertionResult(
                    assertion_id=assertion.name,
                    status=AssertionStatus.FAILED,
                    message=f"Assertion failed with error: {str(e)}",
                    expected=None,
                    actual=None,
                    details={"error": str(e)}
                )
                self.results.append(error_result)

        return self.results

    def get_summary(self) -> Dict[str, Any]:
        """Get assertion summary statistics."""
        if not self.results:
            return {"total": 0, "passed": 0, "failed": 0, "unknown": 0}

        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == AssertionStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == AssertionStatus.FAILED)
        unknown = sum(1 for r in self.results if r.status == AssertionStatus.UNKNOWN)

        pass_rate = passed / total if total > 0 else 0.0

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "unknown": unknown,
            "pass_rate": pass_rate,
        }

    def get_failed_assertions(self) -> List[AssertionResult]:
        """Get list of failed assertions."""
        return [r for r in self.results if r.status == AssertionStatus.FAILED]


# ============================================================================
# Predefined Assertion Sets
# ============================================================================

def create_baseline_healthy_assertions() -> AssertionRegistry:
    """Create assertions for baseline healthy scenario."""
    registry = AssertionRegistry()

    # Overall health assertions
    registry.register_metric_threshold(
        "overall_health_min",
        "overall_health_index",
        min_threshold=0.80,
        description="Overall health should be good"
    )

    # Diversity assertions
    registry.register_metric_threshold(
        "topic_entropy_min",
        "topic_entropy",
        min_threshold=0.70,
        description="Topic diversity should be maintained"
    )
    registry.register_metric_threshold(
        "stance_entropy_min",
        "stance_entropy",
        min_threshold=0.60,
        description="Stance diversity should be maintained"
    )

    # Influence balance assertions
    registry.register_metric_threshold(
        "gini_max",
        "gini_coefficient",
        max_threshold=0.50,
        description="Gini coefficient should not indicate high concentration"
    )
    registry.register_metric_threshold(
        "hhi_max",
        "herfindahl_index",
        max_threshold=0.40,
        description="HHI should not indicate excessive concentration"
    )

    # Trust stability assertions
    registry.register_metric_threshold(
        "trust_drift_max",
        "average_trust_drift",
        max_threshold=0.20,
        description="Trust drift should be minimal"
    )

    # Quality assertions
    registry.register_metric_threshold(
        "acceptance_rate_min",
        "acceptance_rate",
        min_threshold=0.60,
        description="Acceptance rate should be reasonable"
    )

    return registry


def create_insight_flooding_assertions() -> AssertionRegistry:
    """Create assertions for insight flooding scenario."""
    registry = AssertionRegistry()

    # Overall health should be maintained despite attack
    registry.register_metric_threshold(
        "overall_health_min",
        "overall_health_index",
        min_threshold=0.65,
        description="System should maintain health despite flooding"
    )

    # Flood-specific assertions
    registry.register_metric_threshold(
        "rejection_rate_min",
        "rejection_rate",
        min_threshold=0.30,
        description="Rejection rate should be high for flood attack"
    )
    registry.register_metric_threshold(
        "flood_node_concentration_max",
        "top_node_concentration",
        max_threshold=0.40,
        description="Flood node should not dominate network"
    )

    # Safeguard triggers
    registry.register_safeguard_trigger(
        "eligibility_triggers_min",
        "FederationEligibilityFilter",
        min_triggers=5,
        description="Eligibility filter should activate frequently"
    )

    # Quality should be maintained
    registry.register_metric_threshold(
        "quality_integrity_min",
        "quality_integrity",
        min_threshold=0.70,
        description="Quality integrity should be maintained despite attack"
    )

    return registry


def create_semantic_monoculture_assertions() -> AssertionRegistry:
    """Create assertions for semantic monoculture scenario."""
    registry = AssertionRegistry()

    # Monoculture should be detected
    registry.register_metric_threshold(
        "topic_entropy_min",
        "topic_entropy",
        min_threshold=0.50,
        description="Topic entropy should not collapse completely"
    )

    # Safeguard triggers
    registry.register_safeguard_trigger(
        "context_triggers_min",
        "ContextSimilarityEngine",
        min_triggers=3,
        description="Context similarity engine should detect monoculture"
    )

    # Diversity should be preserved
    registry.register_metric_threshold(
        "diversity_health_min",
        "diversity_health",
        min_threshold=0.60,
        description="Diversity health should be maintained"
    )

    return registry


def create_authority_concentration_assertions() -> AssertionRegistry:
    """Create assertions for authority concentration scenario."""
    registry = AssertionRegistry()

    # Concentration should be limited
    registry.register_metric_threshold(
        "gini_max",
        "gini_coefficient",
        max_threshold=0.60,
        description="Gini coefficient should not exceed threshold"
    )
    registry.register_metric_threshold(
        "hhi_max",
        "herfindahl_index",
        max_threshold=0.50,
        description="HHI should not be too high"
    )

    # Safeguard triggers
    registry.register_safeguard_trigger(
        "allocative_triggers_min",
        "AllocativeBoundaryGuard",
        min_triggers=3,
        description="Allocative boundary guard should activate"
    )

    # Influence balance should be maintained
    registry.register_metric_threshold(
        "influence_balance_min",
        "influence_balance",
        min_threshold=0.65,
        description="Influence balance should be maintained"
    )

    return registry


def create_compound_adversarial_assertions() -> AssertionRegistry:
    """Create assertions for compound adversarial scenario."""
    registry = AssertionRegistry()

    # Overall health should be maintained
    registry.register_metric_threshold(
        "overall_health_min",
        "overall_health_index",
        min_threshold=0.60,
        description="System should withstand compound attacks"
    )

    # Multiple safeguards should activate
    registry.register_safeguard_trigger(
        "multiple_guardians_active",
        "any_safeguard",
        min_triggers=15,
        description="Multiple safeguards should activate"
    )

    # Diversity should be preserved
    registry.register_metric_threshold(
        "diversity_health_min",
        "diversity_health",
        min_threshold=0.55,
        description="Diversity should be preserved under attack"
    )

    # Recovery should be possible
    registry.register_behavioral_pattern(
        "resilience_pattern",
        "resilience",
        "maintains_functionality",
        parameters={"recovery_threshold": 0.70},
        description="System should show resilience"
    )

    return registry


# ============================================================================
# Assertion Runner
# ============================================================================

class AssertionRunner:
    """Runs assertions against simulation results."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def run_scenario_assertions(
        self,
        scenario: SimulationScenario,
        report: SimulationReport
    ) -> Tuple[List[AssertionResult], AssertionRegistry]:
        """Run appropriate assertions for a scenario."""
        # Get assertion registry for scenario
        if scenario.name == "baseline_healthy_exchange":
            registry = create_baseline_healthy_assertions()
        elif scenario.name == "insight_flooding_attack":
            registry = create_insight_flooding_assertions()
        elif scenario.name == "semantic_monoculture":
            registry = create_semantic_monoculture_assertions()
        elif scenario.name == "authority_concentration":
            registry = create_authority_concentration_assertions()
        elif scenario.name == "compound_adversarial_network":
            registry = create_compound_adversarial_assertions()
        else:
            # Default baseline assertions
            registry = create_baseline_healthy_assertions()

        # Prepare simulation data
        simulation_data = self._prepare_simulation_data(report)

        # Run assertions
        results = registry.run_all_assertions(simulation_data)

        return results, registry

    def _prepare_simulation_data(self, report: SimulationReport) -> Dict[str, Any]:
        """Prepare simulation data for assertions."""
        # Extract data from report
        data = {
            "scenario": report.scenario,
            "metrics": report.metrics,
            "safeguard_triggers": report.guardian_triggers_detected,
            "round_history": report.metrics.round_history,
        }

        # Add detailed metrics if available
        if hasattr(report.metrics, 'diversity_details'):
            data["distributions"] = {
                "topic_entropy": report.metrics.topic_entropy,
                "stance_entropy": report.metrics.stance_entropy,
                "gini_coefficient": report.metrics.gini_coefficient,
                "herfindahl_index": report.metrics.herfindahl_index,
            }

        return data

    def validate_assertion_results(self, results: List[AssertionResult]) -> Dict[str, Any]:
        """Validate assertion results and provide summary."""
        summary = {
            "total": len(results),
            "passed": 0,
            "failed": 0,
            "unknown": 0,
            "critical_failures": [],
            "recommendations": [],
        }

        # Count results
        for result in results:
            if result.status == AssertionStatus.PASSED:
                summary["passed"] += 1
            elif result.status == AssertionStatus.FAILED:
                summary["failed"] += 1
                # Check if critical
                if "critical" in result.message.lower() or "severe" in result.message.lower():
                    summary["critical_failures"].append(result.assertion_id)
            else:
                summary["unknown"] += 1

        # Generate recommendations
        if summary["failed"] > summary["passed"] * 0.5:
            summary["recommendations"].append(
                "High failure rate - consider reviewing safeguard configurations"
            )

        if summary["critical_failures"]:
            summary["recommendations"].append(
                f"Critical failures in: {', '.join(summary['critical_failures'])} - immediate attention required"
            )

        summary["pass_rate"] = summary["passed"] / summary["total"] if summary["total"] > 0 else 0.0

        return summary