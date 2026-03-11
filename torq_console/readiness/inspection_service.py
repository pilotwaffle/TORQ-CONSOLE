"""
TORQ Readiness Checker - Inspection Service

Milestone 4: Generate human-readable readiness inspections.

Assembles complete inspection views of readiness candidates
including scores, evidence, transitions, and governance actions.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel

from .readiness_models import (
    ReadinessCandidate,
    ReadinessState,
    CandidateType,
    ReadinessEvaluation,
    ReadinessScore,
    EvidenceSummary as ModelsEvidenceSummary,
)
from .inspection_models import (
    ReadinessInspection,
    TransitionRecord,
    DimensionScoreView,
    EvidenceSummaryView,
    GovernanceActionView,
    get_score_label,
    get_dimension_label,
)
from .transition_controller import (
    TransitionAuditLog,
    get_audit_logs,
    get_state_machine,
)
from .readiness_policy import (
    get_policy_registry,
)
from .query_service import (
    get_query_service,
    register_candidate,
    get_all_evaluations,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Inspection Service
# ============================================================================

class ReadinessInspectionService:
    """
    Service for generating human-readable readiness inspections.

    Assembles complete views of readiness candidates including
    scores, evidence, transitions, and governance history.
    """

    def __init__(self):
        self.policy_registry = get_policy_registry()
        self.query_service = get_query_service()

    def inspect_candidate(
        self,
        candidate_id: UUID,
    ) -> Optional[ReadinessInspection]:
        """
        Generate a complete inspection view for a candidate.

        Args:
            candidate_id: ID of the candidate to inspect

        Returns:
            ReadinessInspection with complete readiness view, or None if not found
        """
        candidate = self.query_service.get_candidate(candidate_id)
        if candidate is None:
            return None

        # Get latest evaluation
        evaluation = self.query_service.get_latest_evaluation(candidate_id)

        # Get state machine
        state_machine = get_state_machine(candidate_id, candidate.current_state)

        # Get transition history
        audit_logs = get_audit_logs(candidate_id)
        transitions = self._build_transition_records(audit_logs)

        # Get latest transition
        latest_transition = transitions[0] if transitions else None

        # Build dimension score views
        dimension_views = self._build_dimension_views(evaluation)

        # Build evidence summary
        evidence_summary = self._build_evidence_summary(evaluation)

        # Get governance actions
        governance_actions = self._build_governance_actions(candidate_id, evaluation)

        # Get policy profile
        profile = self.policy_registry.get_profile(candidate.policy_profile_id)
        policy_name = profile.name if profile else "Unknown"

        # Calculate time in state
        time_in_state = (datetime.now() - state_machine.state_since).total_seconds() / 86400

        # Build inspection
        inspection = ReadinessInspection(
            candidate_id=candidate.id,
            candidate_type=candidate.candidate_type.value,
            candidate_key=candidate.key if hasattr(candidate, 'key') else None,
            title=candidate.title,
            description=candidate.description,
            current_state=candidate.current_state.value,
            state_since=state_machine.state_since,
            time_in_state_days=time_in_state,
            current_score=evaluation.score.overall_score if evaluation else 0.0,
            confidence=evaluation.score.confidence if evaluation else 0.0,
            score_label=get_score_label(evaluation.score.overall_score if evaluation else 0.0),
            dimension_scores=dimension_views,
            evidence_summary=evidence_summary,
            hard_blocks=evaluation.score.hard_blocks if evaluation else [],
            warnings=evaluation.score.warnings if evaluation else [],
            regression_flags=self._get_regression_flags(evaluation),
            policy_profile=candidate.policy_profile_id,
            policy_profile_name=policy_name,
            policy_version=evaluation.policy_version if evaluation else "1.0",
            latest_evaluation_id=evaluation.id if evaluation else None,
            latest_evaluation_at=evaluation.evaluated_at if evaluation else None,
            latest_evaluation_outcome=evaluation.outcome.value if evaluation else None,
            latest_evaluation_reason=evaluation.reason if evaluation else None,
            transition_history=transitions,
            recent_governance_actions=governance_actions,
            created_at=candidate.created_at,
            updated_at=candidate.updated_at,
            last_assessed_at=evaluation.evaluated_at if evaluation else None,
            owner=candidate.owner,
            steward=candidate.steward,
        )

        return inspection

    def _build_transition_records(
        self,
        audit_logs: List[TransitionAuditLog],
    ) -> List[TransitionRecord]:
        """Convert audit logs to transition records."""
        records = []

        for log in reversed(audit_logs):  # Most recent first
            record = TransitionRecord(
                id=log.id,
                candidate_id=log.candidate_id,
                from_state=log.from_state.value,
                to_state=log.to_state.value,
                transition_type=log.transition_type,
                triggered_by=log.triggered_by,
                trigger_reason=log.trigger_reason,
                evaluation_id=log.evaluation_id,
                evaluation_score=log.evaluation_score,
                evaluation_outcome=log.evaluation_outcome.value if log.evaluation_outcome else None,
                policy_profile_id=log.policy_profile_id,
                policy_version=log.policy_version,
                forced=log.force_used,
                governance_override=log.governance_override,
                approved_by=log.approved_by,
                transitioned_at=log.transitioned_at,
                duration_ms=log.transition_duration_ms,
                state_locked=log.previous_state_locked,
            )
            records.append(record)

        return records

    def _build_dimension_views(
        self,
        evaluation: Optional[ReadinessEvaluation],
    ) -> List[DimensionScoreView]:
        """Build dimension score views from evaluation."""
        if not evaluation:
            return []

        views = []
        score = evaluation.score

        # Map dimension names to weights
        profile = self.policy_registry.get_profile(evaluation.policy_profile_id)
        weights = {}
        if profile:
            weights = {dim.value: weight for dim, weight in profile.weights.items()}

        dimensions = [
            ("execution_stability", score.execution_stability),
            ("artifact_completeness", score.artifact_completeness),
            ("memory_confidence", score.memory_confidence),
            ("insight_quality", score.insight_quality),
            ("pattern_confidence", score.pattern_confidence),
            ("audit_coverage", score.audit_coverage),
            ("policy_compliance", score.policy_compliance),
            ("operational_consistency", score.operational_consistency),
        ]

        for dim_name, dim_score in dimensions:
            weight = weights.get(dim_name, 0.0)
            contribution = weight * dim_score

            view = DimensionScoreView(
                dimension=dim_name,
                score=dim_score,
                label=get_dimension_label(dim_name, dim_score),
                weight=weight,
                contribution=contribution,
                warnings=[] if dim_score >= 0.7 else ["Below recommended threshold"],
                hard_blocks=[block for block in score.hard_blocks if dim_name in block.lower()],
            )
            views.append(view)

        # Sort by contribution descending
        views.sort(key=lambda v: v.contribution, reverse=True)

        return views

    def _build_evidence_summary(
        self,
        evaluation: Optional[ReadinessEvaluation],
    ) -> EvidenceSummaryView:
        """Build evidence summary view from evaluation."""
        if not evaluation or not evaluation.evidence:
            return EvidenceSummaryView()

        evidence = evaluation.evidence

        return EvidenceSummaryView(
            execution_count=evidence.execution_count,
            success_rate=evidence.success_rate,
            avg_runtime_ms=evidence.avg_runtime_ms,
            artifact_count=evidence.artifact_count,
            artifact_completeness_rate=evidence.artifact_completeness_rate,
            governed_memory_count=evidence.governed_memory_count,
            memory_confidence_score=evidence.memory_confidence_score,
            approved_insight_count=evidence.approved_insight_count,
            insight_quality_score=evidence.insight_quality_score,
            validated_pattern_count=evidence.validated_pattern_count,
            pattern_confidence_score=evidence.pattern_confidence_score,
            audit_coverage_score=evidence.audit_coverage_score,
            last_execution_at=evidence.last_execution_at,
            last_memory_validated_at=evidence.last_memory_validated_at,
            oldest_evidence_age_days=evidence.oldest_evidence_age_days,
            total_evidence_sources=evidence.total_evidence_sources,
            evidence_freshness_score=evidence.evidence_freshness_score,
        )

    def _build_governance_actions(
        self,
        candidate_id: UUID,
        evaluation: Optional[ReadinessEvaluation],
    ) -> List[GovernanceActionView]:
        """Build governance action views from transition history."""
        actions = []
        audit_logs = get_audit_logs(candidate_id)

        # Get most recent 5 governance actions
        recent_logs = sorted(audit_logs, key=lambda l: l.transitioned_at, reverse=True)[:5]

        for log in recent_logs:
            action = GovernanceActionView(
                id=log.id,
                action_type=log.transition_type,
                description=f"{log.transition_type.title()}: {log.from_state.value} → {log.to_state.value}",
                requested_by=log.triggered_by,
                reason=log.trigger_reason,
                executed_at=log.transitioned_at,
                success=True,
                transition_event_id=log.id,
            )
            actions.append(action)

        return actions

    def _get_regression_flags(
        self,
        evaluation: Optional[ReadinessEvaluation],
    ) -> List[str]:
        """Get regression flags from evaluation."""
        flags = []

        if not evaluation:
            return flags

        if evaluation.is_regression:
            flags.append(f"Score decreased by {evaluation.regression_delta:.2f}")

        if evaluation.recommended_state == ReadinessState.REGRESSED:
            flags.append("Marked for regression review")

        # Check for score drops in dimensions
        if evaluation.score:
            for dim_name, dim_value in evaluation.score.dimension_scores_raw.items():
                if isinstance(dim_value, dict):
                    # Look for degraded metrics
                    pass

        return flags


# Global inspection service instance
_inspection_service: Optional[ReadinessInspectionService] = None


def get_inspection_service() -> ReadinessInspectionService:
    """Get the global inspection service instance."""
    global _inspection_service
    if _inspection_service is None:
        _inspection_service = ReadinessInspectionService()
    return _inspection_service
