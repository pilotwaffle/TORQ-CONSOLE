"""
TORQ Console Chain-of-Thought (CoT) Reasoning Framework

This module provides advanced reasoning capabilities that enhance AI decision-making
through transparent, step-by-step logical processes.

Key Components:
- CoTReasoning: Base reasoning framework
- ReasoningChain: Container for reasoning steps
- CoTTemplate: Pre-built reasoning patterns
- CoTValidator: Quality assurance for reasoning chains
"""

from .core import CoTReasoning, ReasoningStep, ReasoningChain
from .templates import CoTTemplate, ResearchTemplate, AnalysisTemplate, DecisionTemplate
from .validator import CoTValidator
from .enhancers import PerplexityCoTEnhancer, AgentCoTEnhancer, SpecKitCoTEnhancer

__version__ = "1.0.0"
__all__ = [
    "CoTReasoning",
    "ReasoningStep",
    "ReasoningChain",
    "CoTTemplate",
    "ResearchTemplate",
    "AnalysisTemplate",
    "DecisionTemplate",
    "CoTValidator",
    "PerplexityCoTEnhancer",
    "AgentCoTEnhancer",
    "SpecKitCoTEnhancer"
]