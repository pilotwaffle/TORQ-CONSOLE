"""
TORQ Console - Layer 8: Autonomous Intelligence & Continuous Learning

L8-M1: Closed-loop self-improving AI governance system.

This layer enables TORQ to continuously improve itself through:
- Outcome analysis from mission execution
- Pattern validation and prediction accuracy
- Insight evolution through supersession
- System recommendation generation
- Learning feedback into all TORQ layers

Original Learning Signal Engine:
- Extracts learning signals from evaluations, workspace entries, and syntheses
- Two-pass extraction: deterministic rules + optional LLM-assisted summarization
"""

# ============================================================================
# Original Learning Signal Engine
# ============================================================================

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

# ============================================================================
# Layer 8 Autonomous Intelligence Models
# ============================================================================

from .autonomous_models import (
    # Outcome Analysis Models
    OutcomeEvaluation,
    PerformanceMetrics,
    OutcomeCategory,
    ImprovementCandidate,

    # Pattern Validation Models
    PatternValidation,
    PatternAccuracyMetrics,
    PatternDriftDetection,
    PatternValidationStatus,

    # Insight Evolution Models
    InsightEvolution,
    InsightLineage,
    InsightSupersession,
    InsightLifecycleStage,

    # Recommendation Models
    SystemRecommendation,
    RecommendationType,
    RecommendationPriority,
    RecommendationSource,
    RecommendationStatus,

    # Learning Analytics Models
    LearningMetrics,
    LearningTrend,
    SystemEvolutionSnapshot,

    # Factory Functions
    create_outcome_evaluation,
    create_pattern_validation,
    create_system_recommendation,
    get_default_recommendation_types,
    get_default_outcome_categories,
)

# ============================================================================
# Layer 8 Services
# ============================================================================

from .outcome_analysis.outcome_evaluator import (
    OutcomeAnalyzer,
    get_outcome_analyzer,
)

from .pattern_validation.pattern_validator import (
    PatternValidator,
    get_pattern_validator,
)

from .insight_evolution.insight_evolution_engine import (
    InsightEvolutionEngine,
    get_insight_evolution_engine,
)

from .recommendations.recommendation_engine import (
    RecommendationEngine,
    get_recommendation_engine,
)

from .feedback.learning_feedback_system import (
    LearningFeedbackSystem,
    FeedbackSignal,
    get_learning_feedback_system,
)

from .analytics import (
    LearningAnalytics,
    get_learning_analytics,
)

__all__ = [
    # Original Learning Signal Engine
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
    "LearningSignalService",
    "learning_router",

    # Layer 8 Models
    "OutcomeEvaluation",
    "PerformanceMetrics",
    "OutcomeCategory",
    "ImprovementCandidate",
    "PatternValidation",
    "PatternAccuracyMetrics",
    "PatternDriftDetection",
    "PatternValidationStatus",
    "InsightEvolution",
    "InsightLineage",
    "InsightSupersession",
    "InsightLifecycleStage",
    "SystemRecommendation",
    "RecommendationType",
    "RecommendationPriority",
    "RecommendationSource",
    "RecommendationStatus",
    "LearningMetrics",
    "LearningTrend",
    "SystemEvolutionSnapshot",

    # Factory Functions
    "create_outcome_evaluation",
    "create_pattern_validation",
    "create_system_recommendation",
    "get_default_recommendation_types",
    "get_default_outcome_categories",

    # Layer 8 Services
    "OutcomeAnalyzer",
    "PatternValidator",
    "InsightEvolutionEngine",
    "RecommendationEngine",
    "LearningFeedbackSystem",
    "LearningAnalytics",

    # Service Getters
    "get_outcome_analyzer",
    "get_pattern_validator",
    "get_insight_evolution_engine",
    "get_recommendation_engine",
    "get_learning_feedback_system",
    "get_learning_analytics",
]


def get_layer8_services() -> dict:
    """
    Get all Layer 8 autonomous intelligence services.

    Returns:
        Dictionary of all Layer 8 service instances
    """
    return {
        "outcome_analyzer": get_outcome_analyzer(),
        "pattern_validator": get_pattern_validator(),
        "insight_evolution": get_insight_evolution_engine(),
        "recommendation_engine": get_recommendation_engine(),
        "feedback_system": get_learning_feedback_system(),
        "analytics": get_learning_analytics(),
    }
