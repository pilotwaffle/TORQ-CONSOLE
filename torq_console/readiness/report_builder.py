"""
TORQ Readiness Checker - Report Builder

Milestone 4: Build structured readiness reports.

Generates comprehensive reports for governance review,
audit exports, and control plane dashboards.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel

from .readiness_models import (
    ReadinessState,
    ReadinessCandidate,
)
from .inspection_models import (
    ReadinessInspection,
    ReadinessReportSection,
    CandidateReadinessReport,
    SystemReadinessReport,
    StateDistribution,
    get_score_label,
)
from .inspection_service import (
    get_inspection_service,
)
from .analytics_service import (
    get_analytics_service,
)
from .audit_service import (
    get_audit_service,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Report Builder
# ============================================================================

class ReadinessReportBuilder:
    """
    Builds structured readiness reports.

    Generates comprehensive reports for governance review,
    compliance auditing, and operational dashboards.
    """

    def __init__(self):
        self.inspection_service = get_inspection_service()
        self.analytics_service = get_analytics_service()
        self.audit_service = get_audit_service()

    def build_candidate_report(
        self,
        candidate_id: UUID,
        generated_by: str = "system",
    ) -> Optional[CandidateReadinessReport]:
        """
        Build a detailed readiness report for a single candidate.

        Args:
            candidate_id: ID of the candidate
            generated_by: Who is generating the report

        Returns:
            CandidateReadinessReport with full analysis
        """
        inspection = self.inspection_service.inspect_candidate(candidate_id)

        if inspection is None:
            return None

        # Build report sections
        sections = self._build_candidate_sections(inspection)

        # Generate recommendations
        recommendations = self._generate_candidate_recommendations(inspection)

        # Identify blocking issues
        blocking_issues = inspection.hard_blocks.copy()

        # Suggest actions
        suggested_actions = self._suggest_candidate_actions(inspection)

        return CandidateReadinessReport(
            report_id=uuid4(),
            candidate_id=candidate_id,
            generated_at=datetime.now(),
            generated_by=generated_by,
            candidate_type=inspection.candidate_type,
            candidate_key=inspection.candidate_key,
            title=inspection.title,
            current_state=inspection.current_state,
            current_score=inspection.current_score,
            sections=sections,
            recommendations=recommendations,
            blocking_issues=blocking_issues,
            suggested_actions=suggested_actions,
        )

    def build_system_readiness_report(
        self,
        period_days: int = 30,
        generated_by: str = "system",
    ) -> SystemReadinessReport:
        """
        Build a system-wide readiness report.

        Args:
            period_days: Number of days to cover in the report
            generated_by: Who is generating the report

        Returns:
            SystemReadinessReport with system-wide analysis
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)

        # Get metrics
        metrics = self.analytics_service.get_metrics()

        # Get blocked candidates with reasons
        blocked_candidates = self.analytics_service.get_blocked_candidates(limit=100)

        # Group blocking issues
        blocking_issues: Dict[str, List[str]] = {}
        for candidate in blocked_candidates:
            for reason in candidate.get("blocking_reasons", []):
                if reason not in blocking_issues:
                    blocking_issues[reason] = []
                blocking_issues[reason].append(candidate.get("title", candidate["candidate_type"]))

        # Generate executive summary
        executive_summary = self._generate_executive_summary(metrics, blocking_issues)

        # Build sections
        sections = self._build_system_sections(metrics, blocked_candidates, period_days)

        # Generate recommendations
        recommendations = self._generate_system_recommendations(metrics, blocking_issues)

        return SystemReadinessReport(
            report_id=uuid4(),
            generated_at=datetime.now(),
            generated_by=generated_by,
            period_start=start_date,
            period_end=end_date,
            total_candidates=metrics.total_candidates,
            ready_count=metrics.state_distribution[0].count if metrics.state_distribution else 0,
            blocked_count=metrics.blocked_count,
            regressed_count=metrics.regressed_count,
            executive_summary=executive_summary,
            state_distribution=metrics.state_distribution,
            blocking_issues=blocking_issues,
            recommendations=recommendations,
            sections=sections,
        )

    def build_blocked_capabilities_report(
        self,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        Build a report of all blocked capabilities.

        Args:
            limit: Maximum number of blocked candidates to include

        Returns:
            Dictionary with blocked capabilities analysis
        """
        blocked = self.analytics_service.get_blocked_candidates(limit)

        # Group by blocking reason
        by_reason: Dict[str, List[Dict[str, Any]]] = {}

        for candidate in blocked:
            for reason in candidate.get("blocking_reasons", ["Unknown"]):
                if reason not in by_reason:
                    by_reason[reason] = []
                by_reason[reason].append(candidate)

        return {
            "total_blocked": len(blocked),
            "by_reason": {reason: len(candidates) for reason, candidates in by_reason.items()},
            "blocked_candidates": blocked,
            "generated_at": datetime.now().isoformat(),
        }

    def _build_candidate_sections(
        self,
        inspection: ReadinessInspection,
    ) -> List[ReadinessReportSection]:
        """Build report sections for a candidate."""
        sections = []

        # Overview section
        sections.append(ReadinessReportSection(
            title="Overview",
            content=f"""
Candidate: {inspection.title or inspection.candidate_type}
Current State: {inspection.current_state.upper()}
Overall Score: {inspection.current_score:.2f} ({inspection.score_label})
Confidence: {inspection.confidence:.2f}
Time in State: {inspection.time_in_state_days:.1f} days
Policy Profile: {inspection.policy_profile_name}
            """.strip(),
            data={
                "current_state": inspection.current_state,
                "score": inspection.current_score,
                "confidence": inspection.confidence,
                "time_in_state_days": inspection.time_in_state_days,
            },
        ))

        # Dimension scores section
        dimension_text = "\n".join([
            f"• {d.dimension}: {d.score:.2f} ({d.label}) - weight: {d.weight:.2f}, contribution: {d.contribution:.2f}"
            for d in inspection.dimension_scores
        ])

        sections.append(ReadinessReportSection(
            title="Dimension Scores",
            content=dimension_text,
            data={
                "dimensions": [
                    {
                        "name": d.dimension,
                        "score": d.score,
                        "label": d.label,
                        "weight": d.weight,
                        "contribution": d.contribution,
                    }
                    for d in inspection.dimension_scores
                ],
            },
        ))

        # Evidence summary section
        sections.append(ReadinessReportSection(
            title="Evidence Summary",
            content=f"""
Executions: {inspection.evidence_summary.execution_count} (success rate: {inspection.evidence_summary.success_rate:.1%})
Artifacts: {inspection.evidence_summary.artifact_count} (completeness: {inspection.evidence_summary.artifact_completeness_rate:.1%})
Memory: {inspection.evidence_summary.governed_memory_count} governed
Insights: {inspection.evidence_summary.approved_insight_count} approved
Patterns: {inspection.evidence_summary.validated_pattern_count} validated
            """.strip(),
            data={
                "execution_count": inspection.evidence_summary.execution_count,
                "success_rate": inspection.evidence_summary.success_rate,
                "artifact_count": inspection.evidence_summary.artifact_count,
            },
        ))

        # Transition history section
        if inspection.transition_history:
            recent = inspection.transition_history[:5]
            history_text = "\n".join([
                f"• {t.transitioned_at.strftime('%Y-%m-%d')}: {t.from_state} → {t.to_state} ({t.transition_type})"
                for t in recent
            ])

            sections.append(ReadinessReportSection(
                title="Recent Transitions",
                content=history_text,
                data={
                    "transitions": len(inspection.transition_history),
                    "recent": [
                        {
                            "date": t.transitioned_at.isoformat(),
                            "from": t.from_state,
                            "to": t.to_state,
                            "type": t.transition_type,
                        }
                        for t in recent
                    ],
                },
            ))

        return sections

    def _generate_candidate_recommendations(
        self,
        inspection: ReadinessInspection,
    ) -> List[str]:
        """Generate recommendations for a candidate."""
        recommendations = []

        if inspection.current_state == "observed":
            if inspection.current_score >= 0.7:
                recommendations.append("Candidate meets readiness threshold - consider promotion to WATCHLIST")
            else:
                recommendations.append("Score below threshold - gather more evidence")

        elif inspection.current_state == "watchlist":
            if inspection.current_score >= 0.8:
                recommendations.append("Strong score - candidate ready for promotion to READY")
            elif inspection.current_score >= 0.7:
                recommendations.append("Adequate score - consider promotion to READY")
            else:
                recommendations.append("Score declined - investigate and address issues")

        elif inspection.current_state == "ready":
            if inspection.regression_flags:
                recommendations.append("Regression flags detected - review immediately")
            elif inspection.current_score < 0.7:
                recommendations.append("Score below READY threshold - consider moving to WATCHLIST")
            else:
                recommendations.append("Candidate stable - continue monitoring")

        elif inspection.current_state == "blocked":
            recommendations.append("Address hard blocks before considering promotion")
            if inspection.hard_blocks:
                recommendations.append(f"Primary issues: {', '.join(inspection.hard_blocks[:3])}")

        elif inspection.current_state == "regressed":
            recommendations.append("Investigate cause of regression")
            recommendations.append("Address degraded metrics before reconsidering READY state")

        # Dimension-specific recommendations
        low_dimensions = [
            d.dimension for d in inspection.dimension_scores
            if d.score < 0.6
        ]

        if low_dimensions:
            recommendations.append(f"Low-scoring dimensions: {', '.join(low_dimensions)}")

        return recommendations

    def _suggest_candidate_actions(
        self,
        inspection: ReadinessInspection,
    ) -> List[str]:
        """Suggest actions for a candidate."""
        actions = []

        if inspection.current_state == "observed":
            actions.append("Request evaluation to assess readiness")
            actions.append("Review evidence completeness")

        elif inspection.current_state == "watchlist":
            actions.append("Run full readiness evaluation")
            actions.append("Review dimension scores for improvement areas")

        elif inspection.current_state == "blocked":
            actions.append("Resolve hard blocks")
            actions.append("Request re-evaluation after fixes")

        elif inspection.current_state == "regressed":
            actions.append("Identify cause of score degradation")
            actions.append("Implement recovery plan")
            actions.append("Increase monitoring frequency")

        elif inspection.current_state == "ready":
            actions.append("Schedule periodic evaluations")
            actions.append("Monitor for regression signals")

        return actions

    def _generate_executive_summary(
        self,
        metrics: Any,
        blocking_issues: Dict[str, List[str]],
    ) -> str:
        """Generate executive summary for system report."""
        ready_pct = 0.0
        if metrics.state_distribution:
            ready_dist = next((d for d in metrics.state_distribution if d.state == "ready"), None)
            if ready_dist:
                ready_pct = ready_dist.percentage * 100

        summary = f"""
System Readiness Report

Total Candidates: {metrics.total_candidates}
Ready: {ready_pct:.1f}%
Blocked: {metrics.blocked_count}
Regressed: {metrics.regressed_count}

Average Score: {metrics.avg_score:.2f}
Regression Rate: {metrics.regression_rate:.1%}
Policy Compliance: {metrics.policy_compliance_rate:.1%}
        """.strip()

        return summary

    def _build_system_sections(
        self,
        metrics: Any,
        blocked_candidates: List[Dict[str, Any]],
        period_days: int,
    ) -> List[ReadinessReportSection]:
        """Build report sections for system report."""
        sections = []

        # State distribution section
        dist_text = "\n".join([
            f"• {d.state.title()}: {d.count} candidates ({d.percentage:.1%}, avg score: {d.avg_score:.2f})"
            for d in metrics.state_distribution
        ])

        sections.append(ReadinessReportSection(
            title="State Distribution",
            content=dist_text,
            data={"distribution": [d.dict() for d in metrics.state_distribution]},
        ))

        # Blocking issues section
        if metrics.block_reasons:
            blocks_text = "\n".join([
                f"• {reason}: {count} candidates"
                for reason, count in metrics.block_reasons.items()
            ])

            sections.append(ReadinessReportSection(
                title="Blocking Issues",
                content=blocks_text,
                data={"block_reasons": metrics.block_reasons},
            ))

        # Trends section
        trends_text = f"""
Ready Trend: {metrics.ready_trend.title()}
Regression Trend: {metrics.regression_trend.title()}
Promotion Rate: {metrics.promotion_rate:.1%}
Avg Promotion Time: {metrics.avg_promotion_time_days:.1f} days
        """.strip()

        sections.append(ReadinessReportSection(
            title="Trends and Metrics",
            content=trends_text,
            data={
                "ready_trend": metrics.ready_trend,
                "regression_trend": metrics.regression_trend,
                "promotion_rate": metrics.promotion_rate,
            },
        ))

        return sections

    def _generate_system_recommendations(
        self,
        metrics: Any,
        blocking_issues: Dict[str, List[str]],
    ) -> List[str]:
        """Generate system-wide recommendations."""
        recommendations = []

        if metrics.blocked_count > 0:
            recommendations.append(f"Address {metrics.blocked_count} blocked candidates")

        if metrics.regressed_count > 0:
            recommendations.append(f"Investigate {metrics.regressed_count} regressed candidates")

        if metrics.avg_score < 0.7:
            recommendations.append("System-wide score below threshold - review evidence quality")

        if metrics.regression_rate > 0.1:
            recommendations.append("High regression rate - strengthen monitoring")

        if metrics.policy_compliance_rate < 0.9:
            recommendations.append("Low policy compliance - review governance policies")

        if metrics.ready_trend == "declining":
            recommendations.append("Readiness declining - investigate root causes")

        if not recommendations:
            recommendations.append("System health is good - continue monitoring")

        return recommendations


# Global report builder instance
_report_builder: Optional[ReadinessReportBuilder] = None


def get_report_builder() -> ReadinessReportBuilder:
    """Get the global report builder instance."""
    global _report_builder
    if _report_builder is None:
        _report_builder = ReadinessReportBuilder()
    return _report_builder
