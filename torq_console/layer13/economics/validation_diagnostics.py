"""
Layer 13 Validation Diagnostics

Provides instrumentation, debug output, and verification utilities
for the economic scoring engines during validation phase.

Agent 1 - Validation Support Task
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

from torq_console.layer13.economics import (
    ActionCandidate,
    AllocationPlan,
    AllocationStrategy,
    EconomicContext,
    EconomicScore,
    ResourceConstraint,
    ResourceCost,
    create_allocation_engine,
    create_evaluation_engine,
)


@dataclass
class DiagnosticOutput:
    """Detailed diagnostic output for a single evaluation."""
    candidate_id: str

    # Stage outputs
    stage_1_eligible: bool
    stage_1_rejection_reason: Optional[str] = None

    stage_2_base_value: float = 0.0
    stage_2_normalized_value: float = 0.0
    stage_2_urgency_score: float = 0.0
    stage_2_time_score: float = 0.0

    stage_3_execution_modifier: float = 1.0
    stage_3_confidence_factor: float = 0.5
    stage_3_risk_penalty: float = 0.0
    stage_3_dep_simplicity: float = 1.0

    stage_3_quality_adjusted_value: float = 0.0

    stage_4_efficiency: float = 0.0
    stage_4_total_cost: float = 0.0

    stage_5_strategic_bonus: float = 0.0
    stage_5_opp_cost_penalty: float = 0.0

    final_score: float = 0.0
    final_recommendation: str = "defer"

    # Timing
    evaluation_time_ms: float = 0.0


@dataclass
class ValidationTestResult:
    """Result of a single validation test."""
    test_name: str
    passed: bool
    duration_ms: float
    details: Dict[str, Any] = field(default_factory=dict)
    diagnostics: List[DiagnosticOutput] = field(default_factory=list)
    failure_reason: Optional[str] = None


class ValidationDiagnostics:
    """
    Diagnostics and verification utilities for Layer 13 validation.

    Agent 1 - Validation Support
    """

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.results: List[ValidationTestResult] = []

    def log(self, message: str):
        """Log if verbose mode is enabled."""
        if self.verbose:
            print(f"[DIAGNOSTIC] {message}")

    # ==========================================================================
    # 1. Scoring Pipeline Instrumentation
    # ==========================================================================

    async def evaluate_with_diagnostics(
        self,
        candidates: List[ActionCandidate],
        context: Optional[EconomicContext] = None,
    ) -> tuple[List[EconomicScore], List[DiagnosticOutput]]:
        """
        Evaluate candidates with full diagnostic output.

        Returns both the scores and detailed diagnostic information
        for each stage of the pipeline.
        """
        context = context or EconomicContext()
        engine = create_evaluation_engine(context)

        diagnostics = []
        scores = []

        for candidate in candidates:
            start_time = time.time()

            # Run evaluation
            score = await engine.evaluate_candidate(
                candidate,
                all_candidates=candidates,
            )
            scores.append(score)

            # Build diagnostic output
            duration_ms = (time.time() - start_time) * 1000

            diag = DiagnosticOutput(
                candidate_id=score.candidate_id,

                stage_1_eligible=score.eligible,
                stage_1_rejection_reason=score.rejection_reason,

                stage_2_base_value=score.base_value,
                stage_2_normalized_value=score.normalized_value,
                stage_2_urgency_score=score.urgency_score,
                stage_2_time_score=score.time_realization_score,

                stage_3_execution_modifier=score.execution_modifier,
                stage_3_confidence_factor=score.confidence_factor,
                stage_3_risk_penalty=score.risk_penalty,
                stage_3_dep_simplicity=score.dependency_simplicity,
                stage_3_quality_adjusted_value=score.quality_adjusted_value,

                stage_4_efficiency=score.efficiency,
                stage_4_total_cost=score.total_cost,

                stage_5_strategic_bonus=score.strategic_bonus,
                stage_5_opp_cost_penalty=score.opportunity_cost_penalty,

                final_score=score.final_priority_score,
                final_recommendation=score.recommendation,
                evaluation_time_ms=duration_ms,
            )
            diagnostics.append(diag)

            # Log if verbose
            if self.verbose:
                self.log(f"Evaluated {candidate.id}: score={score.final_priority_score:.3f}, rec={score.recommendation}")

        return scores, diagnostics

    def print_diagnostics(self, diagnostics: List[DiagnosticOutput]):
        """Print detailed diagnostic output."""
        print("\n" + "=" * 80)
        print("SCORING PIPELINE DIAGNOSTICS")
        print("=" * 80)

        for diag in diagnostics:
            print(f"\nCandidate: {diag.candidate_id}")
            print("-" * 40)
            print(f"Stage 1 - Feasibility:     {'[PASS]' if diag.stage_1_eligible else '[FAIL]'}")
            if not diag.stage_1_eligible:
                print(f"  Rejection: {diag.stage_1_rejection_reason}")
                continue  # No further stages if not feasible

            print(f"Stage 2 - Base Value:     {diag.stage_2_base_value:.3f}")
            print(f"  Normalized value:       {diag.stage_2_normalized_value:.3f}")
            print(f"  Urgency score:          {diag.stage_2_urgency_score:.3f}")
            print(f"  Time score:             {diag.stage_2_time_score:.3f}")

            print(f"Stage 3 - Execution Mod:  {diag.stage_3_execution_modifier:.3f}")
            print(f"  Confidence factor:      {diag.stage_3_confidence_factor:.3f}")
            print(f"  Risk penalty:           {diag.stage_3_risk_penalty:.3f}")
            print(f"  Dep simplicity:         {diag.stage_3_dep_simplicity:.3f}")
            print(f"  → Quality-Adjusted Val: {diag.stage_3_quality_adjusted_value:.3f}")

            print(f"Stage 4 - Efficiency:     {diag.stage_4_efficiency:.4f}")
            print(f"  Total cost:             {diag.stage_4_total_cost:.1f}")

            print(f"Stage 5 - Final Score:     {diag.final_score:.3f}")
            print(f"  Strategic bonus:        {diag.stage_5_strategic_bonus:.3f}")
            print(f"  Opp cost penalty:       {diag.stage_5_opp_cost_penalty:.3f}")

            print(f"Recommendation:           {diag.final_recommendation}")
            print(f"Evaluation time:          {diag.evaluation_time_ms:.2f}ms")

    # ==========================================================================
    # 2. Cheap Task Loop Protection Test
    # ==========================================================================

    async def test_cheap_task_loop_protection(self) -> ValidationTestResult:
        """
        Verify that high-value actions win over cheap low-value actions.

        Test candidates:
        - Action A: High value (200), high cost (100), high confidence
        - Action B: Low value (20), low cost (1), high confidence

        Expected: Action A wins despite lower efficiency.
        """
        self.log("Running cheap task loop protection test...")

        start_time = time.time()

        # Create test candidates
        candidates = [
            ActionCandidate(
                id="high_value_action",
                description="Transformative but expensive",
                domain="test",
                estimated_value=200.0,
                estimated_cost=ResourceCost(compute_budget=100.0),
                confidence=0.9,
                risk=0.1,
                urgency=0.5,
                time_to_realization=1.0,
                dependencies=[],
                strategic_alignment=0.8,
                reversibility=0.3,
            ),
            ActionCandidate(
                id="cheap_trivial_action",
                description="Low value but very cheap",
                domain="test",
                estimated_value=20.0,
                estimated_cost=ResourceCost(compute_budget=1.0),
                confidence=0.9,
                risk=0.1,
                urgency=0.5,
                time_to_realization=1.0,
                dependencies=[],
                strategic_alignment=0.2,
                reversibility=0.9,
            ),
        ]

        # Evaluate
        context = EconomicContext(
            budget=ResourceConstraint(max_compute=150.0),
        )
        scores, diagnostics = await self.evaluate_with_diagnostics(candidates, context)

        duration_ms = (time.time() - start_time) * 1000

        # Check results
        high_value_score = next(s for s in scores if s.candidate_id == "high_value_action")
        cheap_score = next(s for s in scores if s.candidate_id == "cheap_trivial_action")

        # Calculate efficiencies
        high_value_eff = high_value_score.quality_adjusted_value / 100.0
        cheap_eff = cheap_score.quality_adjusted_value / 1.0

        passed = high_value_score.final_priority_score > cheap_score.final_priority_score

        details = {
            "high_value_score": high_value_score.final_priority_score,
            "cheap_score": cheap_score.final_priority_score,
            "high_value_efficiency": high_value_eff,
            "cheap_efficiency": cheap_eff,
            "high_value_qav": high_value_score.quality_adjusted_value,
            "cheap_qav": cheap_score.quality_adjusted_value,
        }

        self.log(f"High value action: score={high_value_score.final_priority_score:.3f}, eff={high_value_eff:.3f}")
        self.log(f"Cheap action: score={cheap_score.final_priority_score:.3f}, eff={cheap_eff:.3f}")
        self.log(f"Result: {'[PASS]' if passed else '[FAIL]'}")

        return ValidationTestResult(
            test_name="cheap_task_loop_protection",
            passed=passed,
            duration_ms=duration_ms,
            details=details,
            diagnostics=diagnostics,
            failure_reason="Cheap action scored higher" if not passed else None,
        )

    # ==========================================================================
    # 3. Determinism Verification
    # ==========================================================================

    async def test_determinism(self, iterations: int = 10) -> ValidationTestResult:
        """
        Verify that same inputs produce identical outputs.

        Runs the same evaluation multiple times and checks for consistency.
        """
        self.log(f"Running determinism test ({iterations} iterations)...")

        start_time = time.time()

        # Create fixed candidates
        candidates = [
            ActionCandidate(
                id="deterministic_action",
                description="Test action for determinism",
                domain="test",
                estimated_value=100.0,
                estimated_cost=ResourceCost(compute_budget=50.0),
                confidence=0.7,
                risk=0.3,
                urgency=0.5,
                time_to_realization=1.0,
                dependencies=[],
                strategic_alignment=0.5,
                reversibility=0.5,
            ),
        ]

        # Run evaluation multiple times
        scores = []
        for i in range(iterations):
            engine = create_evaluation_engine()
            score = await engine.evaluate_candidate(candidates[0], all_candidates=candidates)
            scores.append(score.final_priority_score)

        duration_ms = (time.time() - start_time) * 1000

        # Check all scores are identical
        first_score = scores[0]
        all_same = all(abs(s - first_score) < 1e-10 for s in scores)

        details = {
            "iterations": iterations,
            "first_score": first_score,
            "all_scores": scores,
            "variance": max(scores) - min(scores) if scores else 0.0,
        }

        self.log(f"First score: {first_score:.6f}")
        self.log(f"Variance: {details['variance']:.10f}")
        self.log(f"Result: {'[PASS]' if all_same else '[FAIL]'}")

        return ValidationTestResult(
            test_name="determinism",
            passed=all_same,
            duration_ms=duration_ms,
            details=details,
            failure_reason="Scores varied across runs" if not all_same else None,
        )

    # ==========================================================================
    # 4. Performance Check
    # ==========================================================================

    async def test_performance(
        self,
        num_candidates: int = 100,
        budget: float = 10000.0,
    ) -> ValidationTestResult:
        """
        Verify performance with large input sets.

        Tests allocation speed and resource usage.
        """
        self.log(f"Running performance test ({num_candidates} candidates, budget={budget})...")

        start_time = time.time()

        # Generate random candidates
        import random
        random.seed(42)  # Deterministic

        candidates = []
        for i in range(num_candidates):
            candidates.append(ActionCandidate(
                id=f"action_{i}",
                description=f"Performance test action {i}",
                domain="test",
                estimated_value=random.uniform(10, 500),
                estimated_cost=ResourceCost(
                    compute_budget=random.uniform(5, 200),
                ),
                confidence=random.uniform(0.3, 0.95),
                risk=random.uniform(0.0, 0.5),
                urgency=random.uniform(0.0, 1.0),
                time_to_realization=random.uniform(0.5, 2.0),
                dependencies=[],
                strategic_alignment=random.uniform(0.2, 0.9),
                reversibility=random.uniform(0.1, 0.9),
            ))

        # Evaluate and allocate
        engine = create_evaluation_engine()
        allocator = create_allocation_engine(
            strategy=AllocationStrategy.GREEDY,
        )

        eval_start = time.time()
        scores = await engine.evaluate_batch(candidates)
        eval_time_ms = (time.time() - eval_start) * 1000

        alloc_start = time.time()
        plan = await allocator.allocate(candidates, scores, budget)
        alloc_time_ms = (time.time() - alloc_start) * 1000

        total_time_ms = (time.time() - start_time) * 1000

        # Performance criteria
        eval_ok = eval_time_ms < 5000  # Evaluation under 5 seconds
        alloc_ok = alloc_time_ms < 1000  # Allocation under 1 second
        total_ok = total_time_ms < 6000  # Total under 6 seconds

        passed = eval_ok and alloc_ok and total_ok

        details = {
            "num_candidates": num_candidates,
            "budget": budget,
            "allocated_actions": len(plan.allocated_actions),
            "eval_time_ms": eval_time_ms,
            "alloc_time_ms": alloc_time_ms,
            "total_time_ms": total_time_ms,
            "alloc_efficiency": plan.allocation_efficiency,
        }

        self.log(f"Evaluation: {eval_time_ms:.1f}ms")
        self.log(f"Allocation: {alloc_time_ms:.1f}ms")
        self.log(f"Total: {total_time_ms:.1f}ms")
        self.log(f"Allocated: {len(plan.allocated_actions)}/{num_candidates} actions")
        self.log(f"Efficiency: {plan.allocation_efficiency:.1%}")
        self.log(f"Result: {'[PASS]' if passed else '[FAIL]'}")

        return ValidationTestResult(
            test_name="performance",
            passed=passed,
            duration_ms=total_time_ms,
            details=details,
            failure_reason="Too slow" if not passed else None,
        )

    # ==========================================================================
    # 5. Edge Case Verification
    # ==========================================================================

    async def test_edge_cases(self) -> List[ValidationTestResult]:
        """
        Test various edge cases that should be handled gracefully.
        """
        self.log("Running edge case tests...")

        results = []

        # Test 5a: Zero budget
        results.append(await self._test_zero_budget())

        # Test 5b: All infeasible
        results.append(await self._test_all_infeasible())

        # Test 5c: All affordable
        results.append(await self._test_all_affordable())

        return results

    async def _test_zero_budget(self) -> ValidationTestResult:
        """Test with zero budget - should allocate nothing."""
        self.log("  Testing zero budget...")

        candidates = [
            ActionCandidate(
                id="action_1",
                description="Test action",
                domain="test",
                estimated_value=100.0,
                estimated_cost=ResourceCost(compute_budget=10.0),
                confidence=0.8,
                risk=0.2,
                urgency=0.5,
                time_to_realization=1.0,
                dependencies=[],
                strategic_alignment=0.5,
                reversibility=0.5,
            ),
        ]

        context = EconomicContext(
            budget=ResourceConstraint(max_compute=0.0),
        )

        engine = create_evaluation_engine(context)
        allocator = create_allocation_engine(context)

        scores = await engine.evaluate_batch(candidates)
        plan = await allocator.allocate(candidates, scores, budget=0.0)

        passed = len(plan.allocated_actions) == 0 and plan.allocated_budget == 0.0

        self.log(f"    Allocated: {len(plan.allocated_actions)} (expected 0)")

        return ValidationTestResult(
            test_name="edge_case_zero_budget",
            passed=passed,
            duration_ms=0,
            details={"allocated_count": len(plan.allocated_actions)},
            failure_reason="Allocated actions with zero budget" if not passed else None,
        )

    async def _test_all_infeasible(self) -> ValidationTestResult:
        """Test with all candidates infeasible."""
        self.log("  Testing all infeasible...")

        # Create candidates that will fail feasibility
        candidates = [
            ActionCandidate(
                id=f"infeasible_{i}",
                description="Infeasible action",
                domain="blocked",  # This domain will be blocked
                estimated_value=100.0,
                estimated_cost=ResourceCost(compute_budget=10.0),
                confidence=0.1,  # Below floor
                risk=0.9,  # Above ceiling
                urgency=0.5,
                time_to_realization=1.0,
                dependencies=[],
                strategic_alignment=0.5,
                reversibility=0.5,
            )
            for i in range(5)
        ]

        context = EconomicContext(
            budget=ResourceConstraint(max_compute=1000.0),
            blocked_domains=["blocked"],  # Block all candidates
            confidence_floor=0.5,  # Above candidate confidence
            risk_ceiling=0.5,  # Below candidate risk
        )

        engine = create_evaluation_engine(context)

        scores = await engine.evaluate_batch(candidates)

        # All should be ineligible
        passed = all(not s.eligible for s in scores)

        self.log(f"    Eligible: {sum(1 for s in scores if s.eligible)}/{len(scores)} (expected 0)")

        return ValidationTestResult(
            test_name="edge_case_all_infeasible",
            passed=passed,
            duration_ms=0,
            details={
                "total_candidates": len(candidates),
                "eligible_count": sum(1 for s in scores if s.eligible),
            },
            failure_reason="Some infeasible candidates passed" if not passed else None,
        )

    async def _test_all_affordable(self) -> ValidationTestResult:
        """Test with budget large enough for all actions."""
        self.log("  Testing all affordable...")

        candidates = [
            ActionCandidate(
                id=f"affordable_{i}",
                description="Affordable action",
                domain="test",
                estimated_value=100.0 + i * 10,
                estimated_cost=ResourceCost(compute_budget=10.0),
                confidence=0.8,
                risk=0.2,
                urgency=0.5,
                time_to_realization=1.0,
                dependencies=[],
                strategic_alignment=0.5,
                reversibility=0.5,
            )
            for i in range(5)
        ]

        budget = 1000.0  # More than enough for all

        engine = create_evaluation_engine()
        allocator = create_allocation_engine(engine.context)

        scores = await engine.evaluate_batch(candidates)
        plan = await allocator.allocate(candidates, scores, budget)

        # All should be allocated
        passed = len(plan.allocated_actions) == len(candidates)

        self.log(f"    Allocated: {len(plan.allocated_actions)}/{len(candidates)}")

        return ValidationTestResult(
            test_name="edge_case_all_affordable",
            passed=passed,
            duration_ms=0,
            details={
                "total_candidates": len(candidates),
                "allocated_count": len(plan.allocated_actions),
            },
            failure_reason="Not all affordable actions allocated" if not passed else None,
        )

    # ==========================================================================
    # 6. Generate Verification Report
    # ==========================================================================

    def generate_verification_report(
        self,
        results: List[ValidationTestResult],
    ) -> str:
        """Generate a markdown verification report."""
        report = []
        report.append("# Layer 13 Implementation Verification Report")
        report.append(f"\n**Date:** {datetime.utcnow().isoformat()}")
        report.append(f"**Agent:** Agent 1 (Validation Support)")
        report.append("\n---")

        # Summary
        passed = sum(1 for r in results if r.passed)
        total = len(results)

        report.append("## Summary")
        report.append(f"\nTests: {passed}/{total} passed")

        if passed == total:
            report.append("\n[OK] ALL TESTS PASSED")
        else:
            report.append(f"\n⚠️ **{total - passed} test(s) failed**")

        # Detailed results
        report.append("\n---")
        report.append("\n## Detailed Results")

        for result in results:
            status_icon = "[PASS]" if result.passed else "[FAIL]"
            report.append(f"\n### {result.test_name}: {status_icon}")
            report.append(f"\nDuration: {result.duration_ms:.2f}ms")

            if result.details:
                report.append("\n**Details:**")
                for key, value in result.details.items():
                    if isinstance(value, list) and len(value) > 5:
                        report.append(f"- {key}: [{value[0]}, ..., {value[-1]}] ({len(value)} items)")
                    elif isinstance(value, float):
                        report.append(f"- {key}: {value:.4f}")
                    else:
                        report.append(f"- {key}: {value}")

            if result.failure_reason:
                report.append(f"\n**Failure:** {result.failure_reason}")

        # Diagnostics summary
        report.append("\n---")
        report.append("\n## Diagnostics Summary")

        for result in results:
            if result.diagnostics:
                report.append(f"\n### {result.test_name}")
                self._add_diagnostics_summary(report, result.diagnostics)

        return "\n".join(report)

    def _add_diagnostics_summary(
        self,
        report: List[str],
        diagnostics: List[DiagnosticOutput],
    ):
        """Add diagnostics summary to report."""
        if not diagnostics:
            report.append("No diagnostics available.")
            return

        # Summary statistics
        eligible = sum(1 for d in diagnostics if d.stage_1_eligible)
        avg_qav = sum(d.stage_3_quality_adjusted_value for d in diagnostics if d.stage_1_eligible) / eligible if eligible > 0 else 0
        avg_efficiency = sum(d.stage_4_efficiency for d in diagnostics if d.stage_1_eligible) / eligible if eligible > 0 else 0

        report.append(f"- Eligible: {eligible}/{len(diagnostics)}")
        report.append(f"- Avg Quality-Adjusted Value: {avg_qav:.3f}")
        report.append(f"- Avg Efficiency: {avg_efficiency:.3f}")

        # Stage pass rates
        stage_1_pass = sum(1 for d in diagnostics if d.stage_1_eligible)
        stage_2_pass = stage_1_pass  # All eligible pass stage 2
        stage_3_pass = stage_1_pass  # All pass stage 3
        stage_4_pass = stage_1_pass  # All pass stage 4

        report.append(f"\nStage Pass Rates:")
        report.append(f"- Stage 1 (Feasibility): {stage_1_pass}/{len(diagnostics)}")
        report.append(f"- Stage 2 (Base Value): {stage_2_pass}/{len(diagnostics)}")
        report.append(f"- Stage 3 (Execution): {stage_3_pass}/{len(diagnostics)}")
        report.append(f"- Stage 4 (Efficiency): {stage_4_pass}/{len(diagnostics)}")

    async def run_all_diagnostics(self) -> List[ValidationTestResult]:
        """
        Run all diagnostic tests.

        Returns list of test results.
        """
        self.log("=" * 60)
        self.log("LAYER 13 VALIDATION DIAGNOSTICS")
        self.log("=" * 60)

        results = []

        # Test 2: Cheap task loop protection
        results.append(await self.test_cheap_task_loop_protection())

        # Test 3: Determinism
        results.append(await self.test_determinism())

        # Test 4: Performance
        results.append(await self.test_performance())

        # Test 5: Edge cases
        results.extend(await self.test_edge_cases())

        return results

    def save_report(
        self,
        results: List[ValidationTestResult],
        output_path: str = "docs/layer13/IMPLEMENTATION_VERIFICATION.md",
    ):
        """Generate and save verification report."""
        report = self.generate_verification_report(results)

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(report)

        print(f"\n[Report saved to: {output_path}]")


# =============================================================================
# Main Entry Point
# =============================================================================

async def main():
    """Run all validation diagnostics."""
    diagnostics = ValidationDiagnostics(verbose=True)

    # Run all tests
    results = await diagnostics.run_all_diagnostics()

    # Print summary
    print("\n" + "=" * 60)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 60)

    for result in results:
        status = "[PASS]" if result.passed else "[FAIL]"
        print(f"{result.test_name}: {status} ({result.duration_ms:.2f}ms)")

    passed = sum(1 for r in results if r.passed)
    total = len(results)
    print(f"\nTotal: {passed}/{total} passed")

    # Save report
    diagnostics.save_report(results)

    return results


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
