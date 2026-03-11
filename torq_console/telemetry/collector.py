"""
Adaptive System Telemetry

Collects and reports metrics for the adaptive cognition loop.
Provides observability into signal quality, proposal flow, and experiment outcomes.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .models import (
    TelemetryMetric,
    TelemetryReport,
    MetricDistribution,
    SignalVolumeMetrics,
    ProposalFlowMetrics,
    ExperimentMetrics,
    SystemHealthMetrics,
    ConversionMetrics,
)


logger = logging.getLogger(__name__)


class AdaptiveTelemetryCollector:
    """
    Collects telemetry data for the adaptive system.

    Monitors:
    - Signal generation rates by family
    - Proposal approval rates
    - Experiment success rates
    - Rollback frequency
    - Evaluation score distributions
    """

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    async def collect_report(
        self,
        days_back: int = 7
    ) -> TelemetryReport:
        """
        Collect a comprehensive telemetry report.

        Aggregates metrics for the specified lookback period.
        """
        since = datetime.now() - timedelta(days=days_back)

        signal_metrics = await self.collect_signal_volume_metrics(since)
        proposal_metrics = await self.collect_proposal_flow_metrics(since)
        experiment_metrics = await self.collect_experiment_metrics(since)
        conversion_metrics = await self.collect_conversion_metrics(since)

        # System health aggregates
        system_health = await self.compute_system_health_metrics(
            signal_metrics, proposal_metrics, experiment_metrics, conversion_metrics
        )

        return TelemetryReport(
            period_days=days_back,
            from_date=since,
            to_date=datetime.now(),
            signals=signal_metrics,
            proposals=proposal_metrics,
            experiments=experiment_metrics,
            conversions=conversion_metrics,
            system_health=system_health,
            generated_at=datetime.now()
        )

    async def collect_signal_volume_metrics(
        self,
        since: datetime
    ) -> SignalVolumeMetrics:
        """Collect signal generation metrics grouped by family."""
        try:
            result = self.supabase.table("learning_signals").select("*").gte("created_at", since.isoformat()).execute()

            signals = result.data or []

            # Group by signal type/family
            by_family: Dict[str, int] = {}
            by_strength: Dict[str, int] = {}
            by_source: Dict[str, int] = {}

            for signal in signals:
                signal_type = signal.get("signal_type", "unknown")

                # Determine family
                family = self._get_signal_family(signal_type)
                by_family[family] = by_family.get(family, 0) + 1

                # By strength
                strength = signal.get("strength", "unknown")
                by_strength[strength] = by_strength.get(strength, 0) + 1

                # By source
                source = signal.get("source", "unknown")
                by_source[source] = by_source.get(source, 0) + 1

            return SignalVolumeMetrics(
                total_signals=len(signals),
                by_family=by_family,
                by_strength=by_strength,
                by_source=by_source,
                signals_per_day=round(len(signals) / 7, 1) if signals else 0
            )

        except Exception as e:
            logger.error(f"Error collecting signal metrics: {e}")
            return SignalVolumeMetrics(
                total_signals=0, by_family={}, by_strength={}, by_source={}, signals_per_day=0
            )

    async def collect_proposal_flow_metrics(
        self,
        since: datetime
    ) -> ProposalFlowMetrics:
        """Collect proposal generation and approval metrics."""
        try:
            result = self.supabase.table("adaptation_proposals").select("*").gte("created_at", since.isoformat()).execute()

            proposals = result.data or []

            # Group by status
            by_status: Dict[str, int] = {}
            by_risk_tier: Dict[str, int] = {}
            by_asset: Dict[str, int] = {}

            for proposal in proposals:
                status = proposal.get("status", "unknown")
                by_status[status] = by_status.get(status, 0) + 1

                tier = proposal.get("risk_tier", "unknown")
                by_risk_tier[tier] = by_risk_tier.get(tier, 0) + 1

                asset = proposal.get("target_key", "unknown")
                by_asset[asset] = by_asset.get(asset, 0) + 1

            # Calculate approval rate
            total = len(proposals)
            approved = by_status.get("approved", 0) + by_status.get("applied", 0)
            approval_rate = (approved / total) if total > 0 else 0

            return ProposalFlowMetrics(
                total_proposals=total,
                proposals_per_day=round(total / 7, 1) if total else 0,
                by_status=by_status,
                by_risk_tier=by_risk_tier,
                by_asset=by_asset,
                approval_rate=round(approval_rate, 3)
            )

        except Exception as e:
            logger.error(f"Error collecting proposal metrics: {e}")
            return ProposalFlowMetrics(
                total_proposals=0, proposals_per_day=0, by_status={},
                by_risk_tier={}, by_asset={}, approval_rate=0
            )

    async def collect_experiment_metrics(
        self,
        since: datetime
    ) -> ExperimentMetrics:
        """Collect experiment outcome metrics."""
        try:
            result = self.supabase.table("behavior_experiments").select("*").gte("created_at", since.isoformat()).execute()

            experiments = result.data or []

            # Group by status
            by_status: Dict[str, int] = {}
            promoted = 0
            rolled_back = 0

            for exp in experiments:
                status = exp.get("status", "unknown")
                by_status[status] = by_status.get(status, 0) + 1

                if status == "promoted":
                    promoted += 1
                elif status == "rolled_back":
                    rolled_back += 1

            # Calculate success rate
            completed = promoted + rolled_back + by_status.get("completed", 0)
            success_rate = (promoted / completed) if completed > 0 else 0

            # Get assignment counts for running experiments
            running_ids = [e["id"] for e in experiments if e.get("status") == "running"]

            total_assignments = 0
            if running_ids:
                assign_result = self.supabase.table("experiment_assignments").select("id").in_("experiment_id", running_ids).execute()
                total_assignments = len(assign_result.data) if assign_result.data else 0

            return ExperimentMetrics(
                total_experiments=len(experiments),
                experiments_per_day=round(len(experiments) / 7, 1) if experiments else 0,
                by_status=by_status,
                currently_running=len(running_ids),
                total_assignments=total_assignments,
                promoted_count=promoted,
                rolled_back_count=rolled_back,
                success_rate=round(success_rate, 3)
            )

        except Exception as e:
            logger.error(f"Error collecting experiment metrics: {e}")
            return ExperimentMetrics(
                total_experiments=0, experiments_per_day=0, by_status={},
                currently_running=0, total_assignments=0, promoted_count=0,
                rolled_back_count=0, success_rate=0
            )

    async def collect_conversion_metrics(
        self,
        since: datetime
    ) -> ConversionMetrics:
        """Collect signal-to-proposal conversion metrics."""
        try:
            # Count signals by status
            signal_result = self.supabase.table("learning_signals").select("status").gte("created_at", since.isoformat()).execute()
            all_signals = signal_result.data or []
            pending_signals = len([s for s in all_signals if s.get("status") == "pending"])

            # Count proposals
            proposal_result = self.supabase.table("adaptation_proposals").select("*").gte("created_at", since.isoformat()).execute()
            all_proposals = proposal_result.data or []

            # Calculate conversion rate
            total_signals = len(all_signals)
            total_proposals = len(all_proposals)
            conversion_rate = (total_proposals / total_signals) if total_signals > 0 else 0

            # Group proposals by signal type to see which convert best
            by_signal_type: Dict[str, int] = {}
            for proposal in all_proposals:
                # Get signal type from proposal via learning_signal_id
                signal_id = proposal.get("learning_signal_id")
                if signal_id:
                    # Find the signal
                    signal = next((s for s in all_signals if s.get("signal_id") == signal_id), None)
                    if signal:
                        signal_type = signal.get("signal_type", "unknown")
                        by_signal_type[signal_type] = by_signal_type.get(signal_type, 0) + 1

            return ConversionMetrics(
                total_signals=total_signals,
                total_proposals=total_proposals,
                conversion_rate=round(conversion_rate, 3),
                pending_signals=pending_signals,
                by_signal_type=by_signal_type
            )

        except Exception as e:
            logger.error(f"Error collecting conversion metrics: {e}")
            return ConversionMetrics(
                total_signals=0, total_proposals=0, conversion_rate=0,
                pending_signals=0, by_signal_type={}
            )

    async def compute_system_health_metrics(
        self,
        signal_metrics: SignalVolumeMetrics,
        proposal_metrics: ProposalFlowMetrics,
        experiment_metrics: ExperimentMetrics,
        conversion_metrics: Optional[ConversionMetrics] = None
    ) -> SystemHealthMetrics:
        """Compute aggregated system health indicators."""
        # Signal quality: reasonable volume, not dominated by one family
        signal_families = len(signal_metrics.by_family)
        max_family_ratio = (
            max(signal_metrics.by_family.values()) / signal_metrics.total_signals
            if signal_metrics.total_signals > 0 else 0
        )

        # Proposal health: approval rate not too low or too high
        approval_rate = proposal_metrics.approval_rate
        proposal_health = 0.5 <= approval_rate <= 0.9

        # Experiment health: success rate > 60%, rollback rate < 20%
        success_rate = experiment_metrics.success_rate
        experiment_success = success_rate > 0.6

        total_outcomes = experiment_metrics.promoted_count + experiment_metrics.rolled_back_count
        rollback_rate = (
            experiment_metrics.rolled_back_count / total_outcomes
            if total_outcomes > 0 else 0
        )
        rollback_ok = rollback_rate < 0.2

        # Overall health score
        health_score = 0.0
        if signal_families >= 3:  # Diverse signals
            health_score += 0.2
        if max_family_ratio < 0.7:  # No dominant family
            health_score += 0.2
        if proposal_health:  # Reasonable approval rate
            health_score += 0.2
        if experiment_success:  # Experiments succeeding
            health_score += 0.2
        if rollback_ok:  # Rollbacks controlled
            health_score += 0.2

        # Identify noisy assets (high proposal volume)
        noisy_assets = [
            asset for asset, count in proposal_metrics.by_asset.items()
            if count >= 5  # More than 5 proposals per week
        ]

        return SystemHealthMetrics(
            health_score=round(health_score, 2),
            signal_quality="good" if signal_families >= 3 and max_family_ratio < 0.7 else "needs_attention",
            proposal_quality="good" if 0.3 <= approval_rate <= 0.8 else "volatile",
            experiment_quality="good" if success_rate > 0.6 and rollback_rate < 0.3 else "unstable",
            noisy_assets=noisy_assets,
            recommendations=self._generate_recommendations(
                signal_metrics, proposal_metrics, experiment_metrics, health_score
            )
        )

    def _generate_recommendations(
        self,
        signal_metrics: SignalVolumeMetrics,
        proposal_metrics: ProposalFlowMetrics,
        experiment_metrics: ExperimentMetrics,
        health_score: float,
        conversion_metrics: Optional[ConversionMetrics] = None
    ) -> List[str]:
        """Generate actionable recommendations based on telemetry."""
        recommendations = []

        # Check signal volume
        if signal_metrics.signals_per_day > 10:
            recommendations.append("High signal volume - consider increasing evidence thresholds")
        elif signal_metrics.signals_per_day < 1:
            recommendations.append("Low signal volume - learning may be too conservative")

        # Check conversion rate (NEW)
        if conversion_metrics:
            if conversion_metrics.conversion_rate > 0.25:
                recommendations.append("High signal-to-proposal conversion rate - learning engine may be overly sensitive")
            elif conversion_metrics.conversion_rate < 0.05:
                recommendations.append("Low signal-to-proposal conversion rate - extraction rules may be too strict")

        # Check proposal approval rate
        if proposal_metrics.approval_rate < 0.3:
            recommendations.append("Low approval rate - signals may not be high quality enough")
        elif proposal_metrics.approval_rate > 0.9:
            recommendations.append("Very high approval rate - review may be too permissive")

        # Check experiment outcomes
        if experiment_metrics.success_rate < 0.5:
            recommendations.append("Low experiment success rate - review promotion criteria")
        if experiment_metrics.rolled_back_count > 2:
            recommendations.append("Multiple rollbacks - tighten rollback guardrails")

        # Check noisy assets
        if proposal_metrics.by_asset:
            max_proposals = max(proposal_metrics.by_asset.values())
            if max_proposals > 5:
                noisy = [k for k, v in proposal_metrics.by_asset.items() if v >= 5]
                recommendations.append(f"Noisy assets detected: {', '.join(noisy[:3])}")

        return recommendations

    def _get_signal_family(self, signal_type: str) -> str:
        """Map signal type to family."""
        if "prompt" in signal_type:
            return "prompt_improvement"
        elif "routing" in signal_type:
            return "routing_adjustment"
        elif "tool" in signal_type:
            return "tool_preference"
        elif "question" in signal_type or "contradiction" in signal_type or "risk" in signal_type:
            return "reasoning_pattern"
        else:
            return "other"


class EvaluationDistributionAnalyzer:
    """
    Analyzes evaluation score distributions.

    Computes baseline distributions for adaptive calibration.
    """

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    async def analyze_distributions(
        self,
        days_back: int = 7
    ) -> Dict[str, MetricDistribution]:
        """
        Compute distributions for all evaluation metrics.

        Returns mean, median, p50, p75, p90, p95 for each metric.
        """
        since = datetime.now() - timedelta(days=days_back)

        try:
            result = self.supabase.table("execution_evaluations").select("*").gte("created_at", since.isoformat()).execute()

            evaluations = result.data or []

            if not evaluations:
                return {}

            # Extract metric values
            metrics_data: Dict[str, List[float]] = {
                "overall_score": [],
                "reasoning_score": [],
                "outcome_score": [],
                "coherence_score": [],
                "risk_score": [],
                "actionability_score": [],
            }

            for eval_data in evaluations:
                for metric_name in metrics_data.keys():
                    value = eval_data.get(metric_name)
                    if value is not None:
                        metrics_data[metric_name].append(float(value))

            # Compute distributions
            distributions = {}
            for metric_name, values in metrics_data.items():
                if values:
                    distributions[metric_name] = self._compute_distribution(metric_name, values)

            return distributions

        except Exception as e:
            logger.error(f"Error analyzing distributions: {e}")
            return {}

    def _compute_distribution(self, metric_name: str, values: List[float]) -> MetricDistribution:
        """Compute percentile distribution for a metric."""
        sorted_values = sorted(values)

        n = len(sorted_values)

        return MetricDistribution(
            metric_name=metric_name,
            count=n,
            mean=round(sum(values) / n, 2),
            median=sorted_values[n // 2],
            p50=sorted_values[int(n * 0.5)],
            p75=sorted_values[int(n * 0.75)],
            p90=sorted_values[int(n * 0.90)],
            p95=sorted_values[int(n * 0.95)]
        )
