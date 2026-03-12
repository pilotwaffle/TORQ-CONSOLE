"""
TORQ Layer 8 - Recommendations Module

L8-M1: Generates system improvement recommendations.
"""

from .recommendation_engine import (
    RecommendationEngine,
    RecommendationProposal,
    get_recommendation_engine,
)

__all__ = [
    "RecommendationEngine",
    "RecommendationProposal",
    "get_recommendation_engine",
]
