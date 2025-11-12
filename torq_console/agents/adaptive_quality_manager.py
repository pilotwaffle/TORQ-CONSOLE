"""
Adaptive Quality Manager for Enhanced Prince Flowers v2.

Implements best practices for dynamic quality thresholds and adaptive baselines:
- Statistical adaptive thresholding with historical data
- Multi-metric scoring (format, semantic, relevance, tone)
- Drift detection and auto-adjustment
- Closed feedback loops for continuous improvement

Based on latest AI quality management research.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import statistics

logger = logging.getLogger(__name__)


@dataclass
class QualityMetrics:
    """Multi-dimensional quality metrics."""
    format_compliance: float  # 0-1: Response format correctness
    semantic_correctness: float  # 0-1: Factual accuracy
    relevance: float  # 0-1: Query relevance
    tone: float  # 0-1: Appropriate tone
    solution_quality: float  # 0-1: Solution effectiveness
    timestamp: datetime = field(default_factory=datetime.now)

    def overall_score(self) -> float:
        """Calculate weighted overall score."""
        weights = {
            "semantic": 0.3,
            "relevance": 0.25,
            "solution": 0.25,
            "tone": 0.1,
            "format": 0.1
        }
        return (
            self.semantic_correctness * weights["semantic"] +
            self.relevance * weights["relevance"] +
            self.solution_quality * weights["solution"] +
            self.tone * weights["tone"] +
            self.format_compliance * weights["format"]
        )


@dataclass
class AdaptiveThreshold:
    """Adaptive threshold that adjusts based on performance history."""
    name: str
    current_value: float
    min_value: float
    max_value: float
    history: deque = field(default_factory=lambda: deque(maxlen=100))
    adjustment_rate: float = 0.05  # How quickly threshold adapts

    def update(self, observed_value: float):
        """Update threshold based on observed performance."""
        self.history.append(observed_value)

        if len(self.history) >= 20:  # Need sufficient data
            # Calculate statistics
            mean = statistics.mean(self.history)
            stdev = statistics.stdev(self.history) if len(self.history) > 1 else 0

            # Adjust threshold: move toward (mean - 0.5*stdev)
            # This keeps threshold challenging but achievable
            target = max(self.min_value, min(self.max_value, mean - 0.5 * stdev))

            # Gradual adjustment
            adjustment = (target - self.current_value) * self.adjustment_rate
            self.current_value = max(
                self.min_value,
                min(self.max_value, self.current_value + adjustment)
            )

    def get_value(self) -> float:
        """Get current threshold value."""
        return self.current_value

    def is_met(self, value: float) -> bool:
        """Check if value meets threshold."""
        return value >= self.current_value


class AdaptiveQualityManager:
    """
    Manages adaptive quality thresholds with continuous learning.

    Features:
    - Statistical adaptive thresholding
    - Multi-metric scoring
    - Drift detection
    - Auto-adjustment based on performance trends
    - Closed feedback loops
    """

    def __init__(self):
        self.logger = logging.getLogger('AdaptiveQualityManager')

        # Adaptive thresholds for different aspects
        self.thresholds = {
            "format": AdaptiveThreshold("format", 0.7, 0.5, 0.95),
            "semantic": AdaptiveThreshold("semantic", 0.65, 0.5, 0.90),
            "relevance": AdaptiveThreshold("relevance", 0.70, 0.55, 0.95),
            "tone": AdaptiveThreshold("tone", 0.75, 0.60, 0.95),
            "solution": AdaptiveThreshold("solution", 0.65, 0.50, 0.90),
            "overall": AdaptiveThreshold("overall", 0.65, 0.50, 0.90),
        }

        # Performance history for drift detection
        self.performance_history: deque = deque(maxlen=200)
        self.drift_detected = False
        self.last_drift_check = datetime.now()

        # Feedback loop data
        self.feedback_data: List[Dict[str, Any]] = []

        self.logger.info("Adaptive Quality Manager initialized")

    async def evaluate_quality(
        self,
        query: str,
        response: str,
        context: Optional[Dict] = None
    ) -> Tuple[QualityMetrics, bool]:
        """
        Evaluate response quality with multi-metric scoring.

        Returns:
            (metrics, meets_thresholds)
        """
        try:
            # Calculate each metric
            metrics = QualityMetrics(
                format_compliance=self._assess_format(response),
                semantic_correctness=self._assess_semantic(response, query),
                relevance=self._assess_relevance(response, query),
                tone=self._assess_tone(response),
                solution_quality=self._assess_solution(response, query)
            )

            # Check against adaptive thresholds
            meets_thresholds = all([
                self.thresholds["format"].is_met(metrics.format_compliance),
                self.thresholds["semantic"].is_met(metrics.semantic_correctness),
                self.thresholds["relevance"].is_met(metrics.relevance),
                self.thresholds["tone"].is_met(metrics.tone),
                self.thresholds["solution"].is_met(metrics.solution_quality),
                self.thresholds["overall"].is_met(metrics.overall_score())
            ])

            # Update thresholds with observed performance
            self.thresholds["format"].update(metrics.format_compliance)
            self.thresholds["semantic"].update(metrics.semantic_correctness)
            self.thresholds["relevance"].update(metrics.relevance)
            self.thresholds["tone"].update(metrics.tone)
            self.thresholds["solution"].update(metrics.solution_quality)
            self.thresholds["overall"].update(metrics.overall_score())

            # Track for drift detection
            self.performance_history.append({
                "timestamp": datetime.now(),
                "overall_score": metrics.overall_score(),
                "meets_thresholds": meets_thresholds
            })

            # Periodic drift check
            if (datetime.now() - self.last_drift_check).seconds > 300:  # Every 5 min
                await self._check_for_drift()

            return metrics, meets_thresholds

        except Exception as e:
            self.logger.error(f"Quality evaluation failed: {e}")
            # Return neutral metrics on error
            metrics = QualityMetrics(0.5, 0.5, 0.5, 0.5, 0.5)
            return metrics, False

    def _assess_format(self, response: str) -> float:
        """Assess format compliance."""
        score = 0.5  # Base score

        # Check length (not too short, not empty)
        if len(response) > 20:
            score += 0.2
        if len(response) > 50:
            score += 0.1

        # Check structure (has sentences)
        sentences = [s for s in response.split('.') if s.strip()]
        if len(sentences) >= 2:
            score += 0.1

        # Check for markdown or formatting
        if any(marker in response for marker in ['#', '*', '-', '1.', '```']):
            score += 0.1

        return min(score, 1.0)

    def _assess_semantic(self, response: str, query: str) -> float:
        """Assess semantic correctness (simplified)."""
        score = 0.5  # Base score

        # Check if response addresses query keywords
        query_words = set(query.lower().split())
        response_words = set(response.lower().split())

        # Remove common words
        common = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'in', 'on', 'at', 'to', 'for'}
        query_words -= common

        if query_words:
            coverage = len(query_words & response_words) / len(query_words)
            score += coverage * 0.3

        # Check for specific technical terms
        if any(word in response.lower() for word in ['implement', 'create', 'build', 'use']):
            score += 0.1

        # Check for error indicators
        if 'error' in response.lower() or 'placeholder' in response.lower():
            score -= 0.2

        return max(0.0, min(score, 1.0))

    def _assess_relevance(self, response: str, query: str) -> float:
        """Assess query relevance."""
        # Keyword overlap
        query_keywords = set(query.lower().split())
        response_keywords = set(response.lower().split())

        common = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'in', 'on', 'at'}
        query_keywords -= common

        if not query_keywords:
            return 0.7

        overlap = len(query_keywords & response_keywords) / len(query_keywords)
        return max(0.4, min(0.95, 0.5 + overlap * 0.5))

    def _assess_tone(self, response: str) -> float:
        """Assess response tone."""
        score = 0.7  # Base score

        # Check for professional tone
        if any(word in response.lower() for word in ['please', 'help', 'assist', 'understand']):
            score += 0.1

        # Check for negative indicators
        if any(word in response.lower() for word in ['cannot', 'unable', 'fail']):
            score -= 0.1

        # Check for placeholder indicators
        if 'placeholder' in response.lower():
            score -= 0.2

        return max(0.0, min(score, 1.0))

    def _assess_solution(self, response: str, query: str) -> float:
        """Assess solution quality."""
        score = 0.5  # Base score

        # Check if query asks for action (build, create, implement)
        action_words = ['build', 'create', 'implement', 'design', 'develop']
        is_action_query = any(word in query.lower() for word in action_words)

        if is_action_query:
            # Check if response provides solution
            if any(word in response.lower() for word in action_words):
                score += 0.2

            # Check for steps or structure
            if any(marker in response for marker in ['1.', '2.', '-', '*']):
                score += 0.1

            # Check for technical details
            if len(response) > 100:
                score += 0.1

        else:
            # For non-action queries, check explanation quality
            if len(response) > 50:
                score += 0.2

            # Check for examples
            if 'example' in response.lower() or 'for instance' in response.lower():
                score += 0.1

        return min(score, 1.0)

    async def _check_for_drift(self):
        """Check for performance drift."""
        try:
            if len(self.performance_history) < 50:
                return

            # Split history into recent and older
            recent = list(self.performance_history)[-25:]
            older = list(self.performance_history)[-50:-25]

            # Calculate average scores
            recent_avg = statistics.mean([p["overall_score"] for p in recent])
            older_avg = statistics.mean([p["overall_score"] for p in older])

            # Detect significant drift (>15% change)
            if abs(recent_avg - older_avg) / older_avg > 0.15:
                self.drift_detected = True
                self.logger.warning(
                    f"Performance drift detected: {older_avg:.2f} → {recent_avg:.2f}"
                )
            else:
                self.drift_detected = False

            self.last_drift_check = datetime.now()

        except Exception as e:
            self.logger.error(f"Drift detection failed: {e}")

    async def record_feedback(
        self,
        interaction_id: str,
        user_feedback: float,  # 0-1
        metrics: QualityMetrics
    ):
        """Record user feedback for closed-loop learning."""
        self.feedback_data.append({
            "interaction_id": interaction_id,
            "timestamp": datetime.now(),
            "user_feedback": user_feedback,
            "predicted_quality": metrics.overall_score(),
            "metrics": metrics
        })

        # Keep only recent feedback
        if len(self.feedback_data) > 1000:
            self.feedback_data = self.feedback_data[-1000:]

    def get_threshold_status(self) -> Dict[str, Any]:
        """Get current threshold status and history."""
        return {
            "thresholds": {
                name: {
                    "current": t.current_value,
                    "min": t.min_value,
                    "max": t.max_value,
                    "history_size": len(t.history)
                }
                for name, t in self.thresholds.items()
            },
            "drift_detected": self.drift_detected,
            "performance_history_size": len(self.performance_history),
            "feedback_data_size": len(self.feedback_data)
        }

    def get_recent_performance(self, last_n: int = 20) -> Dict[str, Any]:
        """Get recent performance statistics."""
        if not self.performance_history:
            return {}

        recent = list(self.performance_history)[-last_n:]

        scores = [p["overall_score"] for p in recent]
        pass_rate = sum(1 for p in recent if p["meets_thresholds"]) / len(recent)

        return {
            "average_score": statistics.mean(scores),
            "min_score": min(scores),
            "max_score": max(scores),
            "stdev": statistics.stdev(scores) if len(scores) > 1 else 0,
            "pass_rate": pass_rate,
            "sample_size": len(recent)
        }


# Global instance
_adaptive_quality_manager: Optional[AdaptiveQualityManager] = None


def get_adaptive_quality_manager() -> AdaptiveQualityManager:
    """Get or create global adaptive quality manager."""
    global _adaptive_quality_manager

    if _adaptive_quality_manager is None:
        _adaptive_quality_manager = AdaptiveQualityManager()

    return _adaptive_quality_manager
