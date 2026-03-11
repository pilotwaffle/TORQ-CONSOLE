"""
Learning Signal Engine

Extracts learning signals from evaluations, workspace entries, and syntheses
to drive adaptive improvements in agent behavior.

Two-pass extraction:
1. Deterministic heuristic rules extract explicit patterns
2. Optional LLM-assisted summarization for signal clusters

Signal families:
- prompt_improvement: Structure and clarity issues
- routing_adjustment: Misalignment and missing capabilities
- tool_preference: Emergent preferences and inefficiencies
- reasoning_pattern: Repeated questions, contradictions, risks
"""

from .models import (
    LearningSignalType,
    SignalStrength,
    SignalSource,
    LearningSignalCreate,
    LearningSignalRead,
    LearningSignalUpdate,
    ExtractionContext,
    ExtractionResult,
    AggregatedSignal,
    SignalWeightCalculator,
)

from .service import LearningSignalService

from .api import router as learning_router

__all__ = [
    # Models
    "LearningSignalType",
    "SignalStrength",
    "SignalSource",
    "LearningSignalCreate",
    "LearningSignalRead",
    "LearningSignalUpdate",
    "ExtractionContext",
    "ExtractionResult",
    "AggregatedSignal",
    "SignalWeightCalculator",
    # Service
    "LearningSignalService",
    # API
    "learning_router",
]
