"""
TORQ Layer 8 - Outcome Analysis Module

L8-M1: Evaluates mission outcomes and generates improvement signals.

The OutcomeAnalyzer processes mission execution results to:
- Measure success and performance
- Compare predicted vs actual outcomes
- Detect patterns in outcomes
- Generate improvement candidates
"""

from .outcome_evaluator import (
    OutcomeAnalyzer,
    get_outcome_analyzer,
)

__all__ = [
    "OutcomeAnalyzer",
    "get_outcome_analyzer",
]
