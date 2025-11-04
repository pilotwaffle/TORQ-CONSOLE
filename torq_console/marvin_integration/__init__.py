"""
Marvin 3.0 Integration for TORQ Console

Provides structured outputs, data extraction, classification,
and agentic workflows using Marvin 3.0.

Marvin supersedes ControlFlow by combining:
- Structured output utilities (extract, cast, classify, generate)
- Agentic workflows (tasks, agents, threads)
- Full Pydantic type safety
- Universal LLM support via Pydantic AI
"""

from .core import TorqMarvinIntegration
from .models import (
    TorqSpecAnalysis,
    TorqCodeReview,
    TorqResearchFindings,
    TorqTaskBreakdown,
    IntentClassification,
    SentimentClassification,
    ComplexityLevel,
    Priority,
    Severity,
    AnalysisConfidence,
)
from .agents import (
    create_spec_analyzer,
    create_code_reviewer,
    create_research_agent,
    create_general_agent,
    create_task_planner,
    create_spec_kit_orchestrator,
    get_agent,
)

__all__ = [
    # Core integration
    'TorqMarvinIntegration',
    # Structured output models
    'TorqSpecAnalysis',
    'TorqCodeReview',
    'TorqResearchFindings',
    'TorqTaskBreakdown',
    # Classification enums
    'IntentClassification',
    'SentimentClassification',
    'ComplexityLevel',
    'Priority',
    'Severity',
    'AnalysisConfidence',
    # Agent factories
    'create_spec_analyzer',
    'create_code_reviewer',
    'create_research_agent',
    'create_general_agent',
    'create_task_planner',
    'create_spec_kit_orchestrator',
    'get_agent',
]

__version__ = '0.1.0'  # Phase 1: Foundation
