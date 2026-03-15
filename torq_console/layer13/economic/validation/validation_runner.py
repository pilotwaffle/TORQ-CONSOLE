"""TORQ Layer 13 - Validation Runner

This module executes validation scenarios and produces pass/fail results.
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

from ..models import AllocationResult, EconomicScore
from .scenario_definitions import ScenarioDefinition, get_all_scenarios
from .result_evaluator import ResultEvaluator, ValidationResult, CheckResult


@dataclass
class TestResult:
    """Result of running a single validation test."""

    scenario_name: str
    test_name: str
    passed: bool
    expected: Any
    actual: Any
    message: str = ""
    duration_ms: float = 0.0


@dataclass
class ScenarioTestResult:
    """Result of running a full validation scenario."""

    scenario_name: str
    description: str
    passed: bool
    test_results: list[TestResult] = field(default_factory=list)
    allocation_result: AllocationResult | None = None
    duration_ms: float = 0.0
    error: str | None = None


class ValidationRunner:
    """Runs validation scenarios for Layer 13 economic intelligence."""

    def __init__(self):
        """Initialize the validation runner."""
        self.evaluator = ResultEvaluator()

    async def run_scenario(
        self,
        scenario: ScenarioDefinition,
        evaluation_engine,
        prioritization_engine,
        allocation_engine,
        opportunity_model,
    ) -> ScenarioTestResult:
        """Run a single validation scenario.

        Args:
            scenario: Scenario definition to run
            evaluation_engine: Economic evaluation engine (Layers 1-3)
            prioritization_engine: Budget-aware prioritization (Layer 4)
            allocation_engine: Resource allocation engine (Layer 5)
            opportunity_model: Opportunity cost model

        Returns:
            ScenarioTestResult with all test results
        """
        start_time = time.time()

        try:
            # Build costs dictionary
            costs = {
                p.mission_id: p.estimated_cost
                for p in scenario.proposals
            }

            # Layer 1-3: Evaluate proposals
            scores = []
            for proposal in scenario.proposals:
                federation_result = scenario.federation_results.get(
                    proposal.mission_id
                )
                score = await evaluation_engine.evaluate_proposal(
                    proposal,
                    scenario.constraints,
                    federation_result,
                )
                scores.append(score)

            # Layer 4: Rank by efficiency
            ranked = await prioritization_engine.rank_by_efficiency(
                scores,
                scenario.constraints,
                costs,
            )

            # Layer 5: Allocate budget
            allocation = await allocation_engine.allocate_budget(
                ranked,
                scenario.constraints,
                costs,
            )

            # Calculate opportunity costs
            funded = [s for s in ranked if s.candidate_id in allocation.funded_mission_ids]
            rejected = [s for s in ranked if s.candidate_id not in allocation.funded_mission_ids]

            opportunity_costs = await opportunity_model.calculate_opportunity_costs(
                funded,
                rejected,
                scenario.constraints.total_budget,
                costs,
            )

            # Store opportunity costs in allocation result
            allocation.opportunity_costs = opportunity_costs

            # Evaluate results
            validation = self.evaluator.evaluate_scenario(
                scenario,
                allocation,
                scores,
            )

            # Build test results
            test_results = self._build_test_results(validation)

            duration = (time.time() - start_time) * 1000

            return ScenarioTestResult(
                scenario_name=scenario.name,
                description=scenario.description,
                passed=validation.overall_passed,
                test_results=test_results,
                allocation_result=allocation,
                duration_ms=duration,
            )

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return ScenarioTestResult(
                scenario_name=scenario.name,
                description=scenario.description,
                passed=False,
                error=str(e),
                duration_ms=duration,
            )

    async def run_all_scenarios(
        self,
        evaluation_engine,
        prioritization_engine,
        allocation_engine,
        opportunity_model,
        scenario_names: list[str] | None = None,
    ) -> list[ScenarioTestResult]:
        """Run all or selected validation scenarios.

        Args:
            evaluation_engine: Economic evaluation engine (Layers 1-3)
            prioritization_engine: Budget-aware prioritization (Layer 4)
            allocation_engine: Resource allocation engine (Layer 5)
            opportunity_model: Opportunity cost model
            scenario_names: Optional list of scenario names to run (default: all)

        Returns:
            List of ScenarioTestResult for each scenario run
        """
        scenarios = get_all_scenarios()

        if scenario_names:
            scenarios = {
                name: s for name, s in scenarios.items() if name in scenario_names
            }

        results = []
        for scenario in scenarios.values():
            result = await self.run_scenario(
                scenario,
                evaluation_engine,
                prioritization_engine,
                allocation_engine,
                opportunity_model,
            )
            results.append(result)

        return results

    def _build_test_results(self, validation: ValidationResult) -> list[TestResult]:
        """Build TestResult objects from ValidationResult.

        Args:
            validation: ValidationResult from evaluator

        Returns:
            List of TestResult objects
        """
        results = []

        for check_result in validation.check_results:
            results.append(TestResult(
                scenario_name=validation.scenario_name,
                test_name=check_result.check_name,
                passed=check_result.passed,
                expected=check_result.expected,
                actual=check_result.actual,
                message=check_result.message,
            ))

        return results

    def print_results(self, results: list[ScenarioTestResult], verbose: bool = False):
        """Print validation results in human-readable format.

        Args:
            results: List of scenario test results
            verbose: Whether to print detailed output
        """
        total_scenarios = len(results)
        passed_scenarios = sum(1 for r in results if r.passed)

        print("\n" + "=" * 60)
        print("Layer 13 Validation Results")
        print("=" * 60)
        print(f"\nTotal Scenarios: {total_scenarios}")
        print(f"Passed: {passed_scenarios}")
        print(f"Failed: {total_scenarios - passed_scenarios}")
        print(f"Success Rate: {passed_scenarios / total_scenarios * 100:.1f}%")

        for result in results:
            status = "[PASS]" if result.passed else "[FAIL]"
            print(f"\n{status} {result.scenario_name}: {result.description}")
            print(f"  Duration: {result.duration_ms:.1f}ms")

            if result.error:
                print(f"  Error: {result.error}")
            elif verbose or not result.passed:
                for test in result.test_results:
                    status = "[PASS]" if test.passed else "[FAIL]"
                    print(f"    {status} {test.test_name}")
                    if not test.passed:
                        print(f"      Expected: {test.expected}")
                        print(f"      Actual: {test.actual}")
                        print(f"      Message: {test.message}")

        print("\n" + "=" * 60)

        if passed_scenarios == total_scenarios:
            print("SUCCESS: All validation scenarios passed!")
        else:
            print(f"WARNING: {total_scenarios - passed_scenarios} scenario(s) failed")

        print("=" * 60 + "\n")

    def print_summary(self, results: list[ScenarioTestResult]):
        """Print a summary of validation results.

        Args:
            results: List of scenario test results
        """
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        total_tests = sum(len(r.test_results) for r in results)
        passed_tests = sum(
            sum(1 for t in r.test_results if t.passed) for r in results
        )
        total_duration = sum(r.duration_ms for r in results)

        print("\nValidation Summary")
        print("-" * 40)
        print(f"Scenarios:  {passed}/{total} passed")
        print(f"Tests:      {passed_tests}/{total_tests} passed")
        print(f"Duration:   {total_duration:.0f}ms")
        print(f"Success:    {passed/total*100:.1f}%")
        print("-" * 40 + "\n")


__all__ = [
    "ValidationRunner",
    "TestResult",
    "ScenarioTestResult",
]
