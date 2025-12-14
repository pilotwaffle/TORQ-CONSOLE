"""
TORQ Console Evaluation Module

Provides deterministic evaluation capabilities with:
- Task loading and execution
- Scoring and regression detection
- CLI integration
- CI/CD support
"""

from .runner import EvaluationRunner
from .scoring import EvaluationScorer, ScoreBreakdown, TaskResult

__all__ = [
    'EvaluationRunner',
    'TaskResult',
    'EvaluationScorer',
    'ScoreBreakdown'
]