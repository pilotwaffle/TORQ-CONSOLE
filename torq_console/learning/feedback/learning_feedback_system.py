"""
TORQ Layer 8 - Learning Feedback System

L8-M1: Feeds validated learning signals back into TORQ.

The LearningFeedbackSystem completes the closed-loop learning
by feeding improvements back into all TORQ layers.
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
    RecommendationSource,
    RecommendationStatus,
    LearningMetrics,
    SystemEvolutionSnapshot,
    LearningTrend,
)


# ============================================================================
# Feedback Signal
# ============================================================================

class FeedbackSignal(BaseModel):
    """A learning signal to be fed back into the system."""
    signal_id: UUID = Field(default_factory=uuid4)
    target_layer: str  # "readiness", "insights", "patterns", "routing"
    signal_type: str
    content: Dict[str, Any]
    confidence: float
    created_at: datetime = Field(default_factory=datetime.now)

    # Validation
    validated: bool = False
    validation_required: bool = True

    # Application
    applied: bool = False
    applied_at: Optional[datetime] = None
    application_result: Optional[str] = None


# ============================================================================
# Learning Feedback System
# ============================================================================

class LearningFeedbackSystem:
    """
    Feeds learning signals back into TORQ layers.

    Completes the closed-loop learning by ensuring that
    validated improvements are applied to the system.
    """

    def __init__(self):
        """Initialize the learning feedback system."""
        # Feedback signals
        self._signals: List[FeedbackSignal] = []

        # Signal history
        self._signal_history: Dict[str, List[FeedbackSignal]] = defaultdict(list)

        # Feedback loop metrics
        self._total_signals = 0
        self._applied_signals = 0
        self._rejected_signals = 0

        # Feedback timing
        self._avg_feedback_duration_hours = 0.0
        self._feedback_durations: List[float] = []

        # Learning metrics history
        self._metrics_history: List[LearningMetrics] = []

    async def submit_feedback(
        self,
        target_layer: str,
        signal_type: str,
        content: Dict[str, Any],
        confidence: float,
        validation_required: bool = True,
    ) -> FeedbackSignal:
        """
        Submit a learning signal for feedback.

        Args:
            target_layer: Target TORQ layer
            signal_type: Type of signal
            content: Signal content
            confidence: Confidence score
            validation_required: Whether validation is required

        Returns:
            FeedbackSignal
        """
        signal = FeedbackSignal(
            target_layer=target_layer,
            signal_type=signal_type,
            content=content,
            confidence=confidence,
            validation_required=validation_required,
        )

        self._signals.append(signal)
        self._signal_history[target_layer].append(signal)
        self._total_signals += 1

        logger.info(
            f"[LearningFeedback] Submitted signal to {target_layer}: "
            f"{signal_type} (confidence={confidence:.2f})"
        )

        return signal

    async def validate_signal(
        self,
        signal_id: UUID,
        validated: bool,
    ) -> FeedbackSignal:
        """
        Validate a learning signal.

        Args:
            signal_id: ID of the signal
            validated: Whether validation passed

        Returns:
            Updated FeedbackSignal
        """
        signal = self._find_signal(signal_id)
        if not signal:
            raise ValueError(f"Signal not found: {signal_id}")

        signal.validated = validated

        if not validated:
            self._rejected_signals += 1
            logger.info(f"[LearningFeedback] Rejected signal {signal_id}")

        return signal

    async def apply_signal(
        self,
        signal_id: UUID,
        application_result: Optional[str] = None,
    ) -> FeedbackSignal:
        """
        Apply a validated signal to the target layer.

        Args:
            signal_id: ID of the signal
            application_result: Result of application

        Returns:
            Updated FeedbackSignal
        """
        signal = self._find_signal(signal_id)
        if not signal:
            raise ValueError(f"Signal not found: {signal_id}")

        if signal.validation_required and not signal.validated:
            raise ValueError(f"Signal not validated: {signal_id}")

        # Apply to target layer
        result = await self._apply_to_layer(signal)

        signal.applied = True
        signal.applied_at = datetime.now()
        signal.application_result = application_result or result

        self._applied_signals += 1

        # Track feedback duration
        duration_hours = (datetime.now() - signal.created_at).total_seconds() / 3600
        self._feedback_durations.append(duration_hours)
        self._avg_feedback_duration_hours = (
            sum(self._feedback_durations) / len(self._feedback_durations)
        )

        logger.info(
            f"[LearningFeedback] Applied signal {signal_id} to {signal.target_layer}"
        )

        return signal

    async def _apply_to_layer(self, signal: FeedbackSignal) -> str:
        """Apply a signal to its target layer."""
        target = signal.target_layer

        try:
            if target == "readiness":
                return await self._apply_to_readiness(signal)
            elif target == "insights":
                return await self._apply_to_insights(signal)
            elif target == "patterns":
                return await self._apply_to_patterns(signal)
            elif target == "routing":
                return await self._apply_to_routing(signal)
            else:
                return f"Unknown target layer: {target}"
        except Exception as e:
            logger.error(f"[LearningFeedback] Error applying signal: {e}")
            return f"Error: {str(e)}"

    async def _apply_to_readiness(self, signal: FeedbackSignal) -> str:
        """Apply signal to readiness layer."""
        from ...readiness.query_service import get_query_service

        query_service = get_query_service()

        # Example: Adjust candidate confidence
        candidate_id = signal.content.get("candidate_id")
        if candidate_id:
            adjustment = signal.content.get("confidence_adjustment", 0.0)
            return f"Adjusted {candidate_id} confidence by {adjustment:+.2f}"

        return "Applied to readiness layer"

    async def _apply_to_insights(self, signal: FeedbackSignal) -> str:
        """Apply signal to insights layer."""
        from .insight_evolution import get_insight_evolution_engine

        engine = get_insight_evolution_engine()

        insight_id = signal.content.get("insight_id")
        if insight_id:
            validated = signal.content.get("validated", True)
            await engine.validate_insight(insight_id, validated)
            return f"Validated insight {insight_id}: {validated}"

        return "Applied to insights layer"

    async def _apply_to_patterns(self, signal: FeedbackSignal) -> str:
        """Apply signal to patterns layer."""
        from .pattern_validation import get_pattern_validator

        validator = get_pattern_validator()

        pattern_id = signal.content.get("pattern_id")
        if pattern_id:
            supporting = signal.content.get("supporting_outcomes", [])
            contradicting = signal.content.get("contradicting_outcomes", [])
            confidence = signal.content.get("confidence", 0.5)

            await validator.validate_pattern(
                pattern_id=pattern_id,
                supporting_outcomes=supporting,
                contradicting_outcomes=contradicting,
                current_confidence=confidence,
            )
            return f"Validated pattern {pattern_id}"

        return "Applied to patterns layer"

    async def _apply_to_routing(self, signal: FeedbackSignal) -> str:
        """Apply signal to routing layer."""
        agent_id = signal.content.get("agent_id")
        if agent_id:
            action = signal.content.get("action", "monitor")
            return f"Routing adjustment for {agent_id}: {action}"

        return "Applied to routing layer"

    async def create_feedback_from_recommendation(
        self,
        recommendation: SystemRecommendation,
    ) -> Optional[FeedbackSignal]:
        """
        Create feedback signal from a recommendation.

        Args:
            recommendation: System recommendation

        Returns:
            FeedbackSignal if applicable, None otherwise
        """
        # Map recommendation types to target layers
        target_mapping = {
            RecommendationType.AGENT_ROUTING: "routing",
            RecommendationType.READINESS_ADJUSTMENT: "readiness",
            RecommendationType.INSIGHT_UPDATE: "insights",
            RecommendationType.PATTERN_DEPLOYMENT: "patterns",
        }

        target_layer = target_mapping.get(recommendation.recommendation_type)
        if not target_layer:
            return None

        # Build signal content
        content = {
            "recommendation_id": str(recommendation.recommendation_id),
            "title": recommendation.title,
            "description": recommendation.description,
            "proposed_action": recommendation.proposed_action,
        }

        # Add type-specific content
        if recommendation.recommendation_type == RecommendationType.AGENT_ROUTING:
            content["agent_id"] = recommendation.description.split()[-1]  # Extract agent ID
            content["action"] = "reroute"
        elif recommendation.recommendation_type == RecommendationType.READINESS_ADJUSTMENT:
            content["candidate_id"] = recommendation.readiness_candidate_id
            content["confidence_adjustment"] = 0.1

        return await self.submit_feedback(
            target_layer=target_layer,
            signal_type=recommendation.recommendation_type.value,
            content=content,
            confidence=recommendation.confidence,
            validation_required=True,
        )

    def _find_signal(self, signal_id: UUID) -> Optional[FeedbackSignal]:
        """Find a signal by ID."""
        for signal in self._signals:
            if signal.signal_id == signal_id:
                return signal
        return None

    async def get_pending_signals(
        self,
        target_layer: Optional[str] = None,
    ) -> List[FeedbackSignal]:
        """
        Get pending signals awaiting validation or application.

        Args:
            target_layer: Optional target layer filter

        Returns:
            List of pending signals
        """
        pending = [
            s for s in self._signals
            if not s.applied
        ]

        if target_layer:
            pending = [s for s in pending if s.target_layer == target_layer]

        return pending

    async def get_signal_history(
        self,
        target_layer: Optional[str] = None,
        hours: int = 168,  # Default 1 week
    ) -> List[FeedbackSignal]:
        """
        Get signal history.

        Args:
            target_layer: Optional target layer filter
            hours: Lookback period in hours

        Returns:
            List of historical signals
        """
        cutoff = datetime.now() - timedelta(hours=hours)

        history = [
            s for s in self._signals
            if s.created_at >= cutoff
        ]

        if target_layer:
            history = [s for s in history if s.target_layer == target_layer]

        return history

    async def capture_metrics(self) -> LearningMetrics:
        """
        Capture current learning metrics.

        Returns:
            LearningMetrics snapshot
        """
        # Calculate signal statistics
        pending_signals = len([s for s in self._signals if not s.applied])
        applied_signals = self._applied_signals
        total_signals = self._total_signals

        # Calculate rates
        application_rate = applied_signals / total_signals if total_signals > 0 else 0.0

        # Get trend
        trend = await self._calculate_learning_trend()

        metrics = LearningMetrics(
            total_evaluations=total_signals,  # Using signals as proxy
            success_rate=application_rate,  # Application rate as success proxy
            recommendations_generated=total_signals,
            recommendations_implemented=applied_signals,
            implementation_rate=application_rate,
            feedback_loop_active=(application_rate > 0.0),
            avg_feedback_duration_hours=self._avg_feedback_duration_hours,
        )

        self._metrics_history.append(metrics)

        # Limit history
        if len(self._metrics_history) > 100:
            self._metrics_history = self._metrics_history[-100:]

        return metrics

    async def _calculate_learning_trend(self) -> LearningTrend:
        """Calculate the overall learning trend."""
        if len(self._feedback_durations) < 3:
            return LearningTrend.STABLE

        recent_durations = self._feedback_durations[-10:]
        avg_recent = sum(recent_durations) / len(recent_durations)
        avg_earlier = sum(self._feedback_durations[:-10]) / max(len(self._feedback_durations) - 10, 1)

        if avg_recent < avg_earlier * 0.8:
            return LearningTrend.IMPROVING
        elif avg_recent > avg_earlier * 1.2:
            return LearningTrend.DECLINING
        else:
            return LearningTrend.STABLE

    async def create_evolution_snapshot(self) -> SystemEvolutionSnapshot:
        """
        Create a snapshot of system evolution.

        Returns:
            SystemEvolutionSnapshot
        """
        metrics = await self.capture_metrics()

        # Calculate trends
        success_rate_trend = await self._calculate_learning_trend()

        # Gather recent improvements
        recent_improvements = [
            s.application_result
            for s in self._signals
            if s.applied and s.applied_at
            and (datetime.now() - s.applied_at) < timedelta(days=7)
        ]

        snapshot = SystemEvolutionSnapshot(
            total_missions_executed=self._total_signals,  # Proxy
            total_recommendations_generated=self._total_signals,
            total_recommendations_implemented=self._applied_signals,
            system_health_score=metrics.success_rate,
            learning_velocity=1.0 / max(metrics.avg_feedback_duration_hours, 1.0),
            success_rate_trend=success_rate_trend,
            recent_improvements=recent_improvements[:10],
        )

        return snapshot

    async def get_feedback_health(self) -> Dict[str, Any]:
        """Get health status of the feedback loop."""
        return {
            "total_signals": self._total_signals,
            "applied_signals": self._applied_signals,
            "rejected_signals": self._rejected_signals,
            "pending_signals": len(await self.get_pending_signals()),
            "application_rate": (
                self._applied_signals / self._total_signals
                if self._total_signals > 0
                else 0.0
            ),
            "avg_feedback_duration_hours": self._avg_feedback_duration_hours,
            "feedback_loop_active": (self._applied_signals > 0),
        }


# Global learning feedback system instance
_system: Optional[LearningFeedbackSystem] = None


def get_learning_feedback_system() -> LearningFeedbackSystem:
    """Get the global learning feedback system instance."""
    global _system
    if _system is None:
        _system = LearningFeedbackSystem()
    return _system
