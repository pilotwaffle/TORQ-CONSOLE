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

# Apply compatibility fixes before importing anything else
from .compatibility import apply_compatibility_fixes, check_marvin_compatibility
_fixes_applied = apply_compatibility_fixes()

# Export Field for forward reference compatibility with Pydantic v2
try:
    from pydantic import Field  # noqa: F401
    _field_available = True
except ImportError:
    _field_available = False
    # Create a dummy Field if Pydantic is not available
    def Field(*args, **kwargs):
        from dataclasses import field
        return field(default_factory=lambda: None)

try:
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

    MARVIN_AVAILABLE = True

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
        'MARVIN_AVAILABLE',
        'Field',  # Export Field for forward references
    ]

except ImportError as e:
    # Handle Marvin import errors gracefully
    import warnings
    warnings.warn(f"Marvin integration not available: {e}", ImportWarning)

    # Create stub classes when Marvin is not available
    from typing import Any, Dict, List, Optional, Type

    class TorqMarvinIntegration:
        def __init__(self, *args, **kwargs):
            raise ImportError("Marvin is not installed. Install with: pip install marvin>=0.19.0")

    # Stub enums and classes
    class IntentClassification:
        QUESTION = "question"
        COMMAND = "command"
        STATEMENT = "statement"

    class SentimentClassification:
        POSITIVE = "positive"
        NEGATIVE = "negative"
        NEUTRAL = "neutral"

    class ComplexityLevel:
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"

    class Priority:
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
        CRITICAL = "critical"

    class Severity:
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
        CRITICAL = "critical"

    class AnalysisConfidence:
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"

    # Stub functions
    def create_spec_analyzer():
        raise ImportError("Marvin is not installed")

    def create_code_reviewer():
        raise ImportError("Marvin is not installed")

    def create_research_agent():
        raise ImportError("Marvin is not installed")

    def create_general_agent():
        raise ImportError("Marvin is not installed")

    def create_task_planner():
        raise ImportError("Marvin is not installed")

    def create_spec_kit_orchestrator():
        raise ImportError("Marvin is not installed")

    def get_agent():
        raise ImportError("Marvin is not installed")

    # Stub model classes
    class TorqSpecAnalysis(dict):
        pass

    class TorqCodeReview(dict):
        pass

    class TorqResearchFindings(dict):
        pass

    class TorqTaskBreakdown(dict):
        pass

    MARVIN_AVAILABLE = False

    __all__ = [
        'TorqMarvinIntegration',
        'TorqSpecAnalysis',
        'TorqCodeReview',
        'TorqResearchFindings',
        'TorqTaskBreakdown',
        'IntentClassification',
        'SentimentClassification',
        'ComplexityLevel',
        'Priority',
        'Severity',
        'AnalysisConfidence',
        'create_spec_analyzer',
        'create_code_reviewer',
        'create_research_agent',
        'create_general_agent',
        'create_task_planner',
        'create_spec_kit_orchestrator',
        'get_agent',
        'MARVIN_AVAILABLE',
        'Field',  # Export Field even when Marvin is not available
    ]

__version__ = '0.1.0'  # Phase 1: Foundation
