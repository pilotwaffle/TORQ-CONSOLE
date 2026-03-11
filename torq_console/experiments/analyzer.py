"""
Experiment Impact Analyzer

Compares control vs candidate outcomes using evaluation metrics.
Generates impact summaries and promotion/rollback recommendations.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Literal
from statistics import mean, stdev
from math import sqrt

from .models import (
    MetricComparison,
    ExperimentImpactSummary,
    ExperimentAnalysis,
    ExperimentStatus,
    GuardrailMetric,
)


logger = logging.getLogger(__name__)


class ExperimentImpactAnalyzer:
    """
    Analyzes experiment results and produces impact summaries.

    Uses evaluation scores to compare control vs candidate performance.
    """

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    async def analyze_experiment(
        self,
        experiment_id: str
    ) -> Optional[ExperimentImpactSummary]:
        """
        Generate a complete impact summary for an experiment.

        Fetches assignments, evaluations, and computes all metric comparisons.
        """
        # Fetch experiment details
        experiment = await self._fetch_experiment(experiment_id)
        if not experiment:
            logger.warning(f"Experiment not found: {experiment_id}")
            return None

        # Fetch assignments grouped by variant
        assignments = await self._fetch_assignments(experiment_id)

        control_executions = [a["execution_id"] for a in assignments if a["assigned_variant"] == "control"]
        candidate_executions = [a["execution_id"] for a in assignments if a["assigned_variant"] == "candidate"]

        if not control_executions or not candidate_executions:
            logger.warning(f"Insufficient assignments for experiment {experiment_id}")
            return None

        # Fetch evaluations for these executions
        control_evals = await self._fetch_evaluations_for_executions(control_executions)
        candidate_evals = await self._fetch_evaluations_for_executions(candidate_executions)

        if not control_evals or not candidate_evals:
            logger.warning(f"No evaluations found for experiment {experiment_id}")
            return None

        # Compute metric comparisons
        all_metrics = await self._compute_all_metrics(
            control_evals, candidate_evals, experiment.get("success_metrics", {})
        )

        # Find primary metric
        success_metrics = experiment.get("success_metrics", {})
        primary_metric_name = success_metrics.get("primary_metric", "overall_score")

        primary_metric = next(
            (m for m in all_metrics if m.metric_name == primary_metric_name),
            all_metrics[0] if all_metrics else None
        )

        if not primary_metric:
            logger.warning(f"Could not find primary metric: {primary_metric_name}")
            return None

        # Check guardrails
        guardrail_metrics = success_metrics.get("guardrails", [])
        guardrail_results = self._check_guardrails(
            all_metrics, guardrail_metrics
        )

        # Determine recommendation
        can_promote, should_rollback, promotion_reason, rollback_reason = self._determine_recommendation(
            experiment, primary_metric, guardrail_results,
            len(control_executions), len(candidate_executions)
        )

        return ExperimentImpactSummary(
            experiment_id=experiment_id,
            proposal_id=experiment.get("proposal_id", ""),
            status=ExperimentStatus(experiment.get("status", "draft")),
            sample_control=len(control_executions),
            sample_candidate=len(candidate_executions),
            total_assignments=len(assignments),
            primary_metric=primary_metric,
            guardrail_results=guardrail_results,
            all_metrics=all_metrics,
            can_promote=can_promote,
            should_rollback=should_rollback,
            promotion_reason=promotion_reason,
            rollback_reason=rollback_reason,
            generated_at=datetime.now()
        )

    async def _compute_all_metrics(
        self,
        control_evals: List[Dict],
        candidate_evals: List[Dict],
        success_metrics: Dict
    ) -> List[MetricComparison]:
        """Compute comparisons for all available metrics."""
        # Determine which metrics to compare
        primary = success_metrics.get("primary_metric", "overall_score")
        secondaries = success_metrics.get("secondary_metrics", [])
        guardrail_defs = success_metrics.get("guardrails", [])

        # All metrics to track
        metric_names = set([primary] + secondaries + [g.get("metric") for g in guardrail_defs])

        # Extract metric values from evaluations
        control_metrics = self._extract_metric_values(control_evals, metric_names)
        candidate_metrics = self._extract_metric_values(candidate_evals, metric_names)

        comparisons = []

        for metric_name in metric_names:
            control_values = control_metrics.get(metric_name, [])
            candidate_values = candidate_metrics.get(metric_name, [])

            if not control_values or not candidate_values:
                continue

            comparison = self._compare_metric(
                metric_name, control_values, candidate_values
            )
            if comparison:
                comparisons.append(comparison)

        return comparisons

    def _extract_metric_values(
        self,
        evaluations: List[Dict],
        metric_names: set[str]
    ) -> Dict[str, List[float]]:
        """Extract metric values from evaluation records."""
        result = {name: [] for name in metric_names}

        for eval_data in evaluations:
            metrics = eval_data.get("metrics", {})
            overall = eval_data.get("overall_score")
            reasoning = eval_data.get("reasoning_score")
            outcome = eval_data.get("outcome_score")
            coherence = eval_data.get("coherence_score")
            risk = eval_data.get("risk_score")
            actionability = eval_data.get("actionability_score")

            # Map various field names to standard metric names
            if "overall_score" in metric_names and overall is not None:
                result["overall_score"].append(float(overall))
            if "reasoning_score" in metric_names and reasoning is not None:
                result["reasoning_score"].append(float(reasoning))
            if "outcome_score" in metric_names and outcome is not None:
                result["outcome_score"].append(float(outcome))
            if "coherence_score" in metric_names and coherence is not None:
                result["coherence_score"].append(float(coherence))
            if "risk_score" in metric_names and risk is not None:
                result["risk_score"].append(float(risk))
            if "actionability_score" in metric_names and actionability is not None:
                result["actionability_score"].append(float(actionability))

            # Also check metrics dict directly
            for name in metric_names:
                if name in metrics and metrics[name] is not None:
                    result[name].append(float(metrics[name]))

        return result

    def _compare_metric(
        self,
        metric_name: str,
        control_values: List[float],
        candidate_values: List[float]
    ) -> Optional[MetricComparison]:
        """Compare a single metric between control and candidate."""
        control_avg = mean(control_values)
        candidate_avg = mean(candidate_values)

        delta = candidate_avg - control_avg
        delta_percent = (delta / control_avg * 100) if control_avg != 0 else 0

        # Compute confidence using simple t-test approximation
        confidence = self._compute_confidence(
            control_values, candidate_values
        )

        # Determine significance (simple threshold)
        is_significant = (
            len(control_values) >= 30 and
            len(candidate_values) >= 30 and
            abs(delta_percent) > 5  # More than 5% change
        )

        # For most metrics, higher is better
        # For risk_score and failure_rate, lower is better
        is_improvement = delta > 0
        if metric_name in ["risk_score", "failure_rate", "tool_failure_rate", "contradiction_rate"]:
            is_improvement = delta < 0

        return MetricComparison(
            metric_name=metric_name,
            control_value=round(control_avg, 4),
            candidate_value=round(candidate_avg, 4),
            delta_value=round(delta, 4),
            delta_percent=round(delta_percent, 2),
            confidence=round(confidence, 2),
            sample_control=len(control_values),
            sample_candidate=len(candidate_values),
            is_significant=is_significant,
            is_improvement=is_improvement
        )

    def _compute_confidence(
        self,
        control_values: List[float],
        candidate_values: List[float]
    ) -> float:
        """
        Compute statistical confidence using t-test approximation.

        Returns confidence score 0-1.
        """
        n1, n2 = len(control_values), len(candidate_values)
        if n1 < 2 or n2 < 2:
            return 0.0

        mean1, mean2 = mean(control_values), mean(candidate_values)

        try:
            var1 = stdev(control_values) ** 2 if n1 > 1 else 0
            var2 = stdev(candidate_values) ** 2 if n2 > 1 else 0

            # Pooled standard error
            se = sqrt(var1/n1 + var2/n2)

            if se == 0:
                return 1.0 if mean1 == mean2 else 0.5

            # t-statistic
            t = (mean2 - mean1) / se

            # Simple confidence approximation (not exact, but practical)
            # Higher |t| = more confident there's a difference
            confidence = min(abs(t) / 3, 1.0)  # Scale t to 0-1 range

            return round(confidence, 2)

        except Exception:
            return 0.5

    def _check_guardrails(
        self,
        all_metrics: List[MetricComparison],
        guardrail_defs: List[Dict]
    ) -> List[MetricComparison]:
        """Check which guardrails passed or failed."""
        guardrail_results = []

        for guardrail in guardrail_defs:
            metric_name = guardrail.get("metric")
            min_delta = guardrail.get("min_delta")
            max_delta = guardrail.get("max_delta")

            # Find the metric comparison
            metric = next((m for m in all_metrics if m.metric_name == metric_name), None)
            if metric:
                # Check if guardrail violated
                violated = False
                if min_delta is not None and metric.delta_value < min_delta:
                    violated = True
                if max_delta is not None and metric.delta_value > max_delta:
                    violated = True

                # Mark violated guardrails
                if violated:
                    # Create a copy marked as violated
                    guardrail_results.append(metric)

        return guardrail_results

    def _determine_recommendation(
        self,
        experiment: Dict,
        primary_metric: MetricComparison,
        guardrail_results: List[MetricComparison],
        n_control: int,
        n_candidate: int
    ) -> tuple[bool, bool, str, Optional[str]]:
        """
        Determine promotion and rollback recommendations.
        """
        success_metrics = experiment.get("success_metrics", {})
        promotion_rule = success_metrics.get("promotion_rule", {})

        min_improvement = promotion_rule.get("primary_metric_min_improvement", 0.05)
        min_sample = promotion_rule.get("minimum_sample_size", 30)
        min_confidence = promotion_rule.get("confidence_threshold", 0.90)

        # Check minimum sample size
        has_sample_size = n_control >= min_sample and n_candidate >= min_sample

        # Check if primary metric improved sufficiently
        primary_improved = (
            primary_metric.is_improvement and
            abs(primary_metric.delta_value) >= min_improvement
        )

        # Check confidence
        confident = primary_metric.confidence >= min_confidence

        # Check guardrails
        guardrails_passed = len(guardrail_results) == 0

        # Determine promotion
        can_promote = (
            has_sample_size and
            primary_improved and
            confident and
            guardrails_passed
        )

        promotion_reason = self._build_promotion_reason(
            has_sample_size, primary_improved, confident, guardrails_passed,
            primary_metric
        )

        # Determine rollback (immediate rollback conditions)
        should_rollback = False
        rollback_reason = None

        # Rollback if significant regression on primary metric
        if primary_metric.is_significant and not primary_metric.is_improvement:
            if abs(primary_metric.delta_percent) > 10:  # More than 10% regression
                should_rollback = True
                rollback_reason = (
                    f"Significant regression in {primary_metric.metric_name}: "
                    f"{primary_metric.control_value:.2f} → {primary_metric.candidate_value:.2f} "
                    f"({primary_metric.delta_percent:.1f}%)"
                )

        # Rollback if guardrails violated
        if guardrail_results:
            should_rollback = True
            if not rollback_reason:
                rollback_reason = "Guardrail violations: " + ", ".join([
                    f"{m.metric_name} regressed" for m in guardrail_results
                ])

        return can_promote, should_rollback, promotion_reason, rollback_reason

    def _build_promotion_reason(
        self,
        has_sample_size: bool,
        primary_improved: bool,
        confident: bool,
        guardrails_passed: bool,
        primary_metric: MetricComparison
    ) -> str:
        """Build explanation for promotion decision."""
        reasons = []

        if has_sample_size:
            reasons.append("minimum sample size reached")
        else:
            reasons.append("insufficient sample size")

        if primary_improved:
            reasons.append(
                f"{primary_metric.metric_name} improved by "
                f"{abs(primary_metric.delta_percent):.1f}%"
            )
        else:
            reasons.append(f"{primary_metric.metric_name} did not improve sufficiently")

        if confident:
            reasons.append(f"statistical confidence {primary_metric.confidence:.0%}")
        else:
            reasons.append("insufficient statistical confidence")

        if guardrails_passed:
            reasons.append("all guardrails passed")
        else:
            reasons.append("guardrail violations detected")

        return "; ".join(reasons)

    # ========================================================================
    # Database Helpers
    # ========================================================================

    async def _fetch_experiment(self, experiment_id: str) -> Optional[Dict]:
        """Fetch experiment details."""
        try:
            result = self.supabase.table("behavior_experiments").select("*").eq("id", experiment_id).limit(1).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error fetching experiment: {e}")
            return None

    async def _fetch_assignments(self, experiment_id: str) -> List[Dict]:
        """Fetch all assignments for an experiment."""
        try:
            result = self.supabase.table("experiment_assignments").select("*").eq("experiment_id", experiment_id).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error fetching assignments: {e}")
            return []

    async def _fetch_evaluations_for_executions(self, execution_ids: List[str]) -> List[Dict]:
        """Fetch evaluations for given executions."""
        if not execution_ids:
            return []

        try:
            result = self.supabase.table("execution_evaluations").select("*").in_("execution_id", execution_ids).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error fetching evaluations: {e}")
            return []
