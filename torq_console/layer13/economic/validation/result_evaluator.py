"""TORQ Layer 13 - Result Evaluator

This module evaluates validation results against expected outcomes.
"""

from dataclasses import dataclass, field
from typing import Any

from ..models import AllocationResult, EconomicScore
from .scenario_definitions import ScenarioDefinition, ScenarioExpectation


@dataclass
class CheckResult:
    """Result of a single validation check."""

    check_name: str
    passed: bool
    expected: Any
    actual: Any
    message: str = ""


@dataclass
class ValidationResult:
    """Result of validating a scenario."""

    scenario_name: str
    overall_passed: bool
    check_results: list[CheckResult] = field(default_factory=list)
    budget_utilization: float = 0.0
    allocation_efficiency: float = 0.0
    regret_ratio: float = 0.0


class ResultEvaluator:
    """Evaluates economic allocation results against expected outcomes."""

    def evaluate_scenario(
        self,
        scenario: ScenarioDefinition,
        allocation: AllocationResult,
        scores: list[EconomicScore],
    ) -> ValidationResult:
        """Evaluate a scenario's results against expectations.

        Args:
            scenario: Scenario definition with expectations
            allocation: Actual allocation result
            scores: Economic scores for all proposals

        Returns:
            ValidationResult with all check results
        """
        check_results = []

        if scenario.expected is None:
            return ValidationResult(
                scenario_name=scenario.name,
                overall_passed=True,
                check_results=[],
            )

        # Check 1: Funded missions match expected
        funded_match = self._check_funded_missions(
            scenario.expected.funded_mission_ids,
            set(allocation.funded_mission_ids),
        )
        check_results.append(CheckResult(
            check_name="Funded Missions Match",
            passed=funded_match.passed,
            expected=scenario.expected.funded_mission_ids,
            actual=set(allocation.funded_mission_ids),
            message=funded_match.message,
        ))

        # Check 2: Queued missions match expected
        queued_match = self._check_queued_missions(
            scenario.expected.queued_mission_ids,
            set(allocation.queued_mission_ids),
        )
        check_results.append(CheckResult(
            check_name="Queued Missions Match",
            passed=queued_match.passed,
            expected=scenario.expected.queued_mission_ids,
            actual=set(allocation.queued_mission_ids),
            message=queued_match.message,
        ))

        # Check 3: Rejected missions match expected
        rejected_match = self._check_rejected_missions(
            scenario.expected.rejected_mission_ids,
            set(allocation.rejected_mission_ids),
        )
        check_results.append(CheckResult(
            check_name="Rejected Missions Match",
            passed=rejected_match.passed,
            expected=scenario.expected.rejected_mission_ids,
            actual=set(allocation.rejected_mission_ids),
            message=rejected_match.message,
        ))

        # Check 4: Budget not exceeded
        budget_ok = allocation.funded_total_cost <= scenario.constraints.total_budget
        check_results.append(CheckResult(
            check_name="Budget Not Exceeded",
            passed=budget_ok,
            expected=f"<={scenario.constraints.total_budget}",
            actual=allocation.funded_total_cost,
            message="" if budget_ok else "Budget exceeded!",
        ))

        # Check 5: Budget utilization within range
        utilization_ok = (
            scenario.expected.min_budget_utilization <= allocation.budget_utilization
            <= scenario.expected.max_budget_utilization
        )
        check_results.append(CheckResult(
            check_name="Budget Utilization",
            passed=utilization_ok,
            expected=f"{scenario.expected.min_budget_utilization:.2f}-{scenario.expected.max_budget_utilization:.2f}",
            actual=allocation.budget_utilization,
            message="" if utilization_ok else f"Utilization {allocation.budget_utilization:.2f} outside range",
        ))

        # Check 6: Allocation efficiency meets minimum
        efficiency_ok = allocation.allocation_efficiency >= scenario.expected.min_allocation_efficiency
        check_results.append(CheckResult(
            check_name="Allocation Efficiency",
            passed=efficiency_ok,
            expected=f">={scenario.expected.min_allocation_efficiency}",
            actual=allocation.allocation_efficiency,
            message="" if efficiency_ok else "Efficiency below minimum",
        ))

        # Check 7: Regret ratio within limit
        regret_ratio = allocation.regret_score / allocation.funded_total_value if allocation.funded_total_value > 0 else 0
        regret_ok = regret_ratio <= scenario.expected.max_regret_ratio
        check_results.append(CheckResult(
            check_name="Regret Ratio",
            passed=regret_ok,
            expected=f"<={scenario.expected.max_regret_ratio}",
            actual=regret_ratio,
            message="" if regret_ok else f"Regret ratio {regret_ratio:.2f} exceeds limit",
        ))

        # Overall passed if all checks passed
        overall_passed = all(c.passed for c in check_results)

        return ValidationResult(
            scenario_name=scenario.name,
            overall_passed=overall_passed,
            check_results=check_results,
            budget_utilization=allocation.budget_utilization,
            allocation_efficiency=allocation.allocation_efficiency,
            regret_ratio=regret_ratio,
        )

    def _check_funded_missions(
        self,
        expected: set[str],
        actual: set[str],
    ) -> CheckResult:
        """Check if funded missions match expected."""
        if expected == actual:
            return CheckResult(
                check_name="Funded Missions Match",
                passed=True,
                expected=expected,
                actual=actual,
            )

        missing = expected - actual
        extra = actual - expected

        if missing and extra:
            message = f"Missing: {missing}, Extra: {extra}"
        elif missing:
            message = f"Missing: {missing}"
        elif extra:
            message = f"Extra: {extra}"
        else:
            message = "Order differs"

        return CheckResult(
            check_name="Funded Missions Match",
            passed=False,
            expected=expected,
            actual=actual,
            message=message,
        )

    def _check_queued_missions(
        self,
        expected: set[str],
        actual: set[str],
    ) -> CheckResult:
        """Check if queued missions match expected."""
        # For queued missions, we allow some flexibility
        # as long as the expected ones are queued
        if expected.issubset(actual):
            return CheckResult(
                check_name="Queued Missions Match",
                passed=True,
                expected=expected,
                actual=actual,
            )

        missing = expected - actual
        return CheckResult(
            check_name="Queued Missions Match",
            passed=False,
            expected=expected,
            actual=actual,
            message=f"Missing from queue: {missing}",
        )

    def _check_rejected_missions(
        self,
        expected: set[str],
        actual: set[str],
    ) -> CheckResult:
        """Check if rejected missions match expected."""
        # We allow additional rejections beyond expected
        if expected.issubset(actual):
            return CheckResult(
                check_name="Rejected Missions Match",
                passed=True,
                expected=expected,
                actual=actual,
                message=f"{len(actual)} rejected (expected {len(expected)})",
            )

        missing = expected - actual
        return CheckResult(
            check_name="Rejected Missions Match",
            passed=False,
            expected=expected,
            actual=actual,
            message=f"Should be rejected but weren't: {missing}",
        )


__all__ = [
    "ResultEvaluator",
    "ValidationResult",
    "CheckResult",
]
