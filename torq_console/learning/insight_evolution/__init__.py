"""
TORQ Layer 8 - Insight Evolution Module

L8-M1: Enables insights to evolve through supersession.
"""

from .insight_evolution_engine import (
    InsightEvolutionEngine,
    InsightUpdateProposal,
    get_insight_evolution_engine,
)

__all__ = [
    "InsightEvolutionEngine",
    "InsightUpdateProposal",
    "get_insight_evolution_engine",
]
