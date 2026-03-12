"""
TORQ Layer 8 - Recommendation Engine

L8-M1: Generates system improvement recommendations.

The RecommendationEngine creates operational improvement proposals
based on learning signals and manages their lifecycle.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from collections import defaultdict

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


# Import models
from ..autonomous_models import (
    SystemRecommendation,
    RecommendationType,
    RecommendationPriority,
    RecommendationSource,
    RecommendationStatus,
)


# ============================================================================
# Recommendation Proposal
# ============================================================================

class RecommendationProposal(BaseModel):
    """A proposal for a system recommendation."""
    recommendation_type: RecommendationType
    source: RecommendationSource
    title: str
    description: str
    proposed_action: str

    # Evidence
    supporting_patterns: List[str] = Field(default_factory=list)
    supporting_outcomes: List[str] = Field(default_factory=list)

    # Impact estimation
    expected_improvement: Optional[str] = None
    estimated_effort: Optional[str] = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    # Priority
    priority: RecommendationPriority = RecommendationPriority.MEDIUM


# ============================================================================
# Recommendation Engine
# ============================================================================

class RecommendationEngine:
    """
    Generates system improvement recommendations.

    Creates recommendations from outcome analysis, pattern validation,
    insight evolution, and learning feedback.
    """

    def __init__(self):
        """Initialize the recommendation engine."""
        # Recommendations storage
        self._recommendations: Dict[str, SystemRecommendation] = {}

        # Pending proposals
        self._proposals: List[RecommendationProposal] = []

        # Statistics
        self._total_generated = 0
        self._total_implemented = 0

        # Auto-generation settings
        self._auto_generate = True
        self._min_confidence = 0.5

    async def create_recommendation(
        self,
        proposal: RecommendationProposal,
    ) -> SystemRecommendation:
        """
        Create a new recommendation from a proposal.

        Args:
            proposal: Recommendation proposal

        Returns:
            SystemRecommendation
        """
        recommendation = SystemRecommendation(
            recommendation_type=proposal.recommendation_type,
            source=proposal.source,
            title=proposal.title,
            description=proposal.description,
            proposed_action=proposal.proposed_action,
            supporting_patterns=proposal.supporting_patterns,
            supporting_outcomes=proposal.supporting_outcomes,
            confidence=proposal.confidence,
            expected_improvement=proposal.expected_improvement,
            estimated_effort=proposal.estimated_effort,
            priority=proposal.priority,
        )

        self._recommendations[str(recommendation.recommendation_id)] = recommendation
        self._total_generated += 1

        logger.info(
            f"[RecommendationEngine] Created recommendation {recommendation.recommendation_id}: "
            f"{proposal.recommendation_type} - {proposal.title}"
        )

        return recommendation

    async def generate_from_outcomes(
        self,
        outcome_evaluations: List[Any],
    ) -> List[SystemRecommendation]:
        """
        Generate recommendations from outcome evaluations.

        Args:
            outcome_evaluations: List of outcome evaluations

        Returns:
            List of generated recommendations
        """
        recommendations = []

        # Analyze patterns across evaluations
        pattern_counts = defaultdict(int)
        low_score_missions = []

        for eval in outcome_evaluations:
            for pattern in eval.detected_patterns:
                pattern_counts[pattern] += 1
            if eval.success_score < 0.4:
                low_score_missions.append(eval)

        # Generate routing recommendations
        if "high_error_rate" in pattern_counts and pattern_counts["high_error_rate"] >= 3:
            recommendations.append(await self.create_recommendation(
                RecommendationProposal(
                    recommendation_type=RecommendationType.WORKFLOW,
                    source=RecommendationSource.OUTCOME_ANALYSIS,
                    title="High Error Rate Detected",
                    description=f"High error rates observed in {pattern_counts['high_error_rate']} executions",
                    proposed_action="Add error handling checkpoints and validation steps",
                    confidence=0.8,
                    priority=RecommendationPriority.HIGH,
                    expected_improvement="Reduce errors by 50-70%",
                )
            ))

        # Generate timeout recommendations
        if "timeout_pattern" in pattern_counts and pattern_counts["timeout_pattern"] >= 2:
            recommendations.append(await self.create_recommendation(
                RecommendationProposal(
                    recommendation_type=RecommendationType.MISSION_WORKFLOW,
                    source=RecommendationSource.OUTCOME_ANALYSIS,
                    title="Mission Timeout Pattern",
                    description=f"Multiple timeouts observed ({pattern_counts['timeout_pattern']} occurrences)",
                    proposed_action="Implement task decomposition and progress checkpoints",
                    confidence=0.9,
                    priority=RecommendationPriority.HIGH,
                    expected_improvement="Reduce timeouts by 80%",
                )
            ))

        # Generate agent routing recommendations
        if low_score_missions:
            agent_scores = defaultdict(list)
            for mission in low_score_missions:
                if mission.agent_id:
                    agent_scores[mission.agent_id].append(mission.success_score)

            for agent_id, scores in agent_scores.items():
                avg_score = sum(scores) / len(scores)
                if avg_score < 0.4 and len(scores) >= 2:
                    recommendations.append(await self.create_recommendation(
                        RecommendationProposal(
                            recommendation_type=RecommendationType.AGENT_ROUTING,
                            source=RecommendationSource.OUTCOME_ANALYSIS,
                            title=f"Agent {agent_id} Underperforming",
                            description=f"Average success score: {avg_score:.2f} across {len(scores)} missions",
                            proposed_action=f"Redirect tasks from {agent_id} to alternative agents",
                            confidence=0.7,
                            priority=RecommendationPriority.MEDIUM,
                            expected_improvement="Increase success rate by 30-50%",
                        )
                    ))

        return recommendations

    async def generate_from_patterns(
        self,
        pattern_validations: List[Any],
    ) -> List[SystemRecommendation]:
        """
        Generate recommendations from pattern validations.

        Args:
            pattern_validations: List of pattern validations

        Returns:
            List of generated recommendations
        """
        recommendations = []

        for validation in pattern_validations:
            # Check for drift
            if validation.drift_detection and validation.drift_detection.drift_detected:
                if validation.drift_detection.drift_severity in ["medium", "high"]:
                    recommendations.append(await self.create_recommendation(
                        RecommendationProposal(
                            recommendation_type=RecommendationType.PATTERN_DEPLOYMENT,
                            source=RecommendationSource.PATTERN_VALIDATION,
                            title=f"Pattern {validation.pattern_id} Drift Detected",
                            description=validation.drift_detection.recommendation or "Pattern accuracy degrading",
                            proposed_action="Retrain pattern or remove from production",
                            confidence=validation.drift_detection.trend_confidence,
                            priority=RecommendationPriority.HIGH,
                            supporting_patterns=[validation.pattern_id],
                        )
                    ))

            # Check for disproven patterns
            if validation.validation_status == "disproven":
                recommendations.append(await self.create_recommendation(
                    RecommendationProposal(
                        recommendation_type=RecommendationType.PATTERN_DEPLOYMENT,
                        source=RecommendationSource.PATTERN_VALIDATION,
                        title=f"Retire Pattern {validation.pattern_id}",
                        description="Pattern has been disproven by outcomes",
                        proposed_action="Remove pattern from active use",
                        confidence=0.9,
                        priority=RecommendationPriority.MEDIUM,
                        supporting_patterns=[validation.pattern_id],
                    )
                ))

        return recommendations

    async def generate_from_insights(
        self,
        insight_evolutions: List[Any],
    ) -> List[SystemRecommendation]:
        """
        Generate recommendations from insight evolution.

        Args:
            insight_evolutions: List of insight evolutions

        Returns:
            List of generated recommendations
        """
        recommendations = []

        # Look for insights that need updating
        for evolution in insight_evolutions:
            if evolution.contradiction_count > evolution.reinforcement_count:
                recommendations.append(await self.create_recommendation(
                    RecommendationProposal(
                        recommendation_type=RecommendationType.INSIGHT_UPDATE,
                        source=RecommendationSource.INSIGHT_EVOLUTION,
                        title=f"Review Insight {evolution.insight_id}",
                        description=f"Insight has {evolution.contradiction_count} contradictions",
                        proposed_action="Review and update insight or retire if invalid",
                        confidence=0.7,
                        priority=RecommendationPriority.MEDIUM,
                    )
                ))

            # Check for superseded insights that need cleanup
            if evolution.current_stage == "superseded":
                # Check if superseded recently (within 7 days)
                if evolution.superseded_at:
                    days_since = (datetime.now() - evolution.superseded_at).days
                    if days_since > 7:
                        recommendations.append(await self.create_recommendation(
                            RecommendationProposal(
                                recommendation_type=RecommendationType.INSIGHT_UPDATE,
                                source=RecommendationSource.INSIGHT_EVOLUTION,
                                title=f"Archive Superseded Insight {evolution.insight_id}",
                                description=f"Insight superseded {days_since} days ago",
                                proposed_action="Archive superseded insight",
                                confidence=0.9,
                                priority=RecommendationPriority.LOW,
                            )
                        ))

        return recommendations

    async def update_recommendation_status(
        self,
        recommendation_id: str,
        status: RecommendationStatus,
        implemented_by: Optional[str] = None,
        implementation_notes: Optional[str] = None,
    ) -> SystemRecommendation:
        """
        Update the status of a recommendation.

        Args:
            recommendation_id: ID of the recommendation
            status: New status
            implemented_by: Optional implementer
            implementation_notes: Optional notes

        Returns:
            Updated SystemRecommendation
        """
        recommendation = self._recommendations.get(recommendation_id)
        if not recommendation:
            raise ValueError(f"Recommendation not found: {recommendation_id}")

        recommendation.status = status

        if status == RecommendationStatus.REVIEWED:
            recommendation.reviewed_at = datetime.now()
        elif status == RecommendationStatus.IMPLEMENTED:
            recommendation.implemented_at = datetime.now()
            recommendation.implemented_by = implemented_by
            recommendation.implementation_notes = implementation_notes
            self._total_implemented += 1

        logger.info(
            f"[RecommendationEngine] Updated {recommendation_id}: {status}"
        )

        return recommendation

    async def link_to_readiness_candidate(
        self,
        recommendation_id: str,
        candidate_id: str,
    ) -> SystemRecommendation:
        """
        Link a recommendation to a readiness candidate.

        Args:
            recommendation_id: ID of the recommendation
            candidate_id: ID of the readiness candidate

        Returns:
            Updated SystemRecommendation
        """
        recommendation = self._recommendations.get(recommendation_id)
        if not recommendation:
            raise ValueError(f"Recommendation not found: {recommendation_id}")

        recommendation.readiness_candidate_id = candidate_id
        recommendation.status = RecommendationStatus.REVIEWED

        logger.info(
            f"[RecommendationEngine] Linked {recommendation_id} to candidate {candidate_id}"
        )

        return recommendation

    async def get_recommendations(
        self,
        status: Optional[RecommendationStatus] = None,
        priority: Optional[RecommendationPriority] = None,
        recommendation_type: Optional[RecommendationType] = None,
        limit: int = 100,
    ) -> List[SystemRecommendation]:
        """
        Get recommendations with optional filtering.

        Args:
            status: Optional status filter
            priority: Optional priority filter
            recommendation_type: Optional type filter
            limit: Maximum results

        Returns:
            List of recommendations
        """
        recommendations = list(self._recommendations.values())

        # Apply filters
        if status:
            recommendations = [r for r in recommendations if r.status == status]
        if priority:
            recommendations = [r for r in recommendations if r.priority == priority]
        if recommendation_type:
            recommendations = [r for r in recommendations if r.recommendation_type == recommendation_type]

        # Sort by priority and created date
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(
            key=lambda r: (
                priority_order.get(r.priority, 99),
                r.created_at,
            ),
            reverse=False,  # Lower priority number = higher priority
        )

        return recommendations[:limit]

    async def get_statistics(self) -> Dict[str, Any]:
        """Get recommendation statistics."""
        by_status = defaultdict(int)
        by_type = defaultdict(int)
        by_priority = defaultdict(int)

        for r in self._recommendations.values():
            by_status[r.status] += 1
            by_type[r.recommendation_type] += 1
            by_priority[r.priority] += 1

        implementation_rate = (
            self._total_implemented / self._total_generated
            if self._total_generated > 0
            else 0.0
        )

        return {
            "total_generated": self._total_generated,
            "total_implemented": self._total_implemented,
            "implementation_rate": implementation_rate,
            "pending_count": by_status.get("pending", 0),
            "by_status": dict(by_status),
            "by_type": dict(by_type),
            "by_priority": dict(by_priority),
        }


# Global recommendation engine instance
_engine: Optional[RecommendationEngine] = None


def get_recommendation_engine() -> RecommendationEngine:
    """Get the global recommendation engine instance."""
    global _engine
    if _engine is None:
        _engine = RecommendationEngine()
    return _engine
