"""
TORQ Layer 8 - Learning Feedback System Module

L8-M1: Feeds validated learning signals back into TORQ.
"""

from .learning_feedback_system import (
    LearningFeedbackSystem,
    FeedbackSignal,
    get_learning_feedback_system,
)

__all__ = [
    "LearningFeedbackSystem",
    "FeedbackSignal",
    "get_learning_feedback_system",
]
