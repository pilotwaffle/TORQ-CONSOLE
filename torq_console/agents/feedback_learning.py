"""
Feedback Learning for TORQ Console Agents.

Learns from user feedback to improve future responses.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """Types of user feedback."""
    ACCEPTED = "accepted"  # User accepted response without changes
    MODIFIED = "modified"  # User modified the response
    REJECTED = "rejected"  # User rejected the response
    THUMBS_UP = "thumbs_up"  # Explicit positive feedback
    THUMBS_DOWN = "thumbs_down"  # Explicit negative feedback
    CORRECTION = "correction"  # User provided correction


@dataclass
class FeedbackEntry:
    """A single feedback entry."""
    interaction_id: str
    feedback_type: FeedbackType
    score: float  # 0.0-1.0
    timestamp: datetime = field(default_factory=datetime.now)
    original_query: Optional[str] = None
    original_response: Optional[str] = None
    corrected_response: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class FeedbackLearning:
    """
    Learns from user feedback to improve agent responses.

    Features:
    - Implicit feedback capture (accepted/modified/rejected)
    - Explicit feedback capture (thumbs up/down)
    - Correction learning
    - Pattern extraction from feedback
    - Response improvement suggestions
    """

    def __init__(self, memory_manager=None):
        """
        Initialize feedback learning.

        Args:
            memory_manager: Optional Letta memory manager for persistence
        """
        self.memory = memory_manager
        self.logger = logging.getLogger(__name__)

        # Feedback history
        self.feedback_history: List[FeedbackEntry] = []

        # Learned patterns
        self.correction_patterns: List[Dict[str, Any]] = []

    async def record_implicit_feedback(
        self,
        interaction_id: str,
        feedback_type: FeedbackType,
        original_query: Optional[str] = None,
        original_response: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FeedbackEntry:
        """
        Record implicit feedback from user actions.

        Args:
            interaction_id: ID of the interaction
            feedback_type: Type of implicit feedback
            original_query: The original user query
            original_response: The agent's response
            metadata: Additional metadata

        Returns:
            FeedbackEntry
        """
        # Calculate score based on feedback type
        score_map = {
            FeedbackType.ACCEPTED: 1.0,
            FeedbackType.MODIFIED: 0.5,
            FeedbackType.REJECTED: 0.0
        }
        score = score_map.get(feedback_type, 0.5)

        # Create feedback entry
        feedback = FeedbackEntry(
            interaction_id=interaction_id,
            feedback_type=feedback_type,
            score=score,
            original_query=original_query,
            original_response=original_response,
            metadata=metadata or {}
        )

        # Store in history
        self.feedback_history.append(feedback)

        # Store in memory if available
        if self.memory:
            try:
                await self.memory.record_feedback(
                    interaction_id=interaction_id,
                    score=score,
                    feedback_type=feedback_type.value
                )
            except Exception as e:
                self.logger.error(f"Error recording implicit feedback: {e}")

        self.logger.info(f"Recorded implicit feedback: {feedback_type.value} (score: {score})")
        return feedback

    async def record_explicit_feedback(
        self,
        interaction_id: str,
        is_positive: bool,
        original_query: Optional[str] = None,
        original_response: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FeedbackEntry:
        """
        Record explicit feedback (thumbs up/down).

        Args:
            interaction_id: ID of the interaction
            is_positive: True for thumbs up, False for thumbs down
            original_query: The original user query
            original_response: The agent's response
            metadata: Additional metadata

        Returns:
            FeedbackEntry
        """
        feedback_type = FeedbackType.THUMBS_UP if is_positive else FeedbackType.THUMBS_DOWN
        score = 1.0 if is_positive else 0.0

        feedback = FeedbackEntry(
            interaction_id=interaction_id,
            feedback_type=feedback_type,
            score=score,
            original_query=original_query,
            original_response=original_response,
            metadata=metadata or {}
        )

        self.feedback_history.append(feedback)

        # Store in memory
        if self.memory:
            try:
                await self.memory.record_feedback(
                    interaction_id=interaction_id,
                    score=score,
                    feedback_type=feedback_type.value
                )
            except Exception as e:
                self.logger.error(f"Error recording explicit feedback: {e}")

        self.logger.info(f"Recorded explicit feedback: {feedback_type.value}")
        return feedback

    async def record_correction(
        self,
        interaction_id: str,
        original_query: str,
        original_response: str,
        corrected_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FeedbackEntry:
        """
        Learn from user corrections.

        Args:
            interaction_id: ID of the interaction
            original_query: The original user query
            original_response: The agent's original response
            corrected_response: User's corrected version
            metadata: Additional metadata

        Returns:
            FeedbackEntry
        """
        feedback = FeedbackEntry(
            interaction_id=interaction_id,
            feedback_type=FeedbackType.CORRECTION,
            score=0.3,  # Low score for needed correction
            original_query=original_query,
            original_response=original_response,
            corrected_response=corrected_response,
            metadata=metadata or {}
        )

        self.feedback_history.append(feedback)

        # Extract correction patterns
        patterns = self._extract_correction_patterns(
            original_response,
            corrected_response
        )

        # Store patterns
        for pattern in patterns:
            self.correction_patterns.append(pattern)

            # Store in memory
            if self.memory:
                try:
                    await self.memory.add_memory(
                        f"User correction: {pattern['description']}",
                        metadata={
                            "type": "correction",
                            "interaction_id": interaction_id,
                            "pattern": pattern
                        },
                        importance=0.95
                    )
                except Exception as e:
                    self.logger.error(f"Error storing correction: {e}")

        # Record feedback
        if self.memory:
            try:
                await self.memory.record_feedback(
                    interaction_id=interaction_id,
                    score=0.3,
                    feedback_type="correction"
                )
            except Exception as e:
                self.logger.error(f"Error recording correction feedback: {e}")

        self.logger.info(f"Recorded correction with {len(patterns)} patterns")
        return feedback

    def _extract_correction_patterns(
        self,
        original: str,
        corrected: str
    ) -> List[Dict[str, Any]]:
        """
        Extract patterns from corrections.

        Args:
            original: Original response
            corrected: Corrected response

        Returns:
            List of correction patterns
        """
        patterns = []

        # Simple diff analysis (placeholder for more sophisticated NLP)
        original_words = set(original.lower().split())
        corrected_words = set(corrected.lower().split())

        added_words = corrected_words - original_words
        removed_words = original_words - corrected_words

        if added_words:
            patterns.append({
                "type": "addition",
                "words": list(added_words),
                "description": f"Added: {', '.join(list(added_words)[:5])}"
            })

        if removed_words:
            patterns.append({
                "type": "removal",
                "words": list(removed_words),
                "description": f"Removed: {', '.join(list(removed_words)[:5])}"
            })

        # Length comparison
        if len(corrected) < len(original) * 0.7:
            patterns.append({
                "type": "shortened",
                "description": "User prefers more concise responses"
            })
        elif len(corrected) > len(original) * 1.3:
            patterns.append({
                "type": "expanded",
                "description": "User prefers more detailed responses"
            })

        return patterns

    async def get_improvement_suggestions(
        self,
        query: str,
        response: str
    ) -> Dict[str, Any]:
        """
        Get suggestions for improving a response based on learned feedback.

        Args:
            query: User query
            response: Proposed response

        Returns:
            Dictionary with improvement suggestions
        """
        suggestions = {
            "apply_patterns": [],
            "warnings": [],
            "confidence": 0.0
        }

        # Check correction patterns
        for pattern in self.correction_patterns[-10:]:  # Last 10 patterns
            if pattern["type"] == "shortened":
                if len(response) > 500:  # Arbitrary threshold
                    suggestions["warnings"].append(
                        "User historically prefers more concise responses"
                    )

            elif pattern["type"] == "expanded":
                if len(response) < 200:
                    suggestions["warnings"].append(
                        "User historically prefers more detailed responses"
                    )

        # Calculate confidence based on feedback history
        recent_feedback = self.feedback_history[-20:]
        if recent_feedback:
            avg_score = sum(f.score for f in recent_feedback) / len(recent_feedback)
            suggestions["confidence"] = avg_score

        return suggestions

    def get_feedback_stats(
        self,
        time_window: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """
        Get feedback statistics.

        Args:
            time_window: Optional time window for stats

        Returns:
            Dictionary with statistics
        """
        # Filter by time window if specified
        if time_window:
            cutoff = datetime.now() - time_window
            feedback = [f for f in self.feedback_history if f.timestamp >= cutoff]
        else:
            feedback = self.feedback_history

        if not feedback:
            return {
                "total_feedback": 0,
                "average_score": 0.0
            }

        # Calculate stats
        total = len(feedback)
        avg_score = sum(f.score for f in feedback) / total

        # Count by type
        by_type = {}
        for f in feedback:
            type_name = f.feedback_type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1

        # Recent trend (last 10 vs previous 10)
        if len(feedback) >= 20:
            recent_10 = feedback[-10:]
            previous_10 = feedback[-20:-10]

            recent_avg = sum(f.score for f in recent_10) / 10
            previous_avg = sum(f.score for f in previous_10) / 10

            trend = "improving" if recent_avg > previous_avg else "declining"
            trend_value = recent_avg - previous_avg
        else:
            trend = "insufficient_data"
            trend_value = 0.0

        return {
            "total_feedback": total,
            "average_score": round(avg_score, 3),
            "by_type": by_type,
            "trend": trend,
            "trend_value": round(trend_value, 3),
            "correction_patterns": len(self.correction_patterns)
        }

    def clear_feedback_history(self):
        """Clear feedback history (useful for testing)."""
        self.feedback_history.clear()
        self.correction_patterns.clear()
        self.logger.info("Cleared feedback history")


# Global feedback learning instance
_feedback_learning: Optional[FeedbackLearning] = None


def get_feedback_learning(memory_manager=None) -> FeedbackLearning:
    """Get or create global feedback learning instance."""
    global _feedback_learning

    if _feedback_learning is None:
        _feedback_learning = FeedbackLearning(memory_manager=memory_manager)

    return _feedback_learning
