"""
Strategic Memory - Phase 4H

Persistent strategic knowledge that shapes future reasoning.

Strategic memory moves TORQ from episodic learning to institutional intelligence:
- Heuristics: Reusable reasoning shortcuts
- Playbooks: Structured action guidance
- Warnings: Known failure patterns to guard against
- Assumptions: Stable operating priors
- Adaptation Lessons: Validated learnings from experiments

The system now accumulates durable knowledge, not just reactive patterns.
"""

from .models import (
    # Core types
    MemoryType,
    MemoryScope,
    MemoryStatus,

    # Models
    StrategicMemory,
    StrategicMemoryCreate,
    StrategicMemoryUpdate,
    MemoryCandidate,
    MemorySearchRequest,
    MemorySearchResult,
    MemoryInjectionContext,
    MemoryInjection,

    # Governance
    MemoryValidation,
    MemorySupersedence,
    MemoryChallenge,
    GovernanceMetrics,

    # Templates
    MemoryTemplates,
    EXAMPLE_MEMORIES,
)

from .consolidation import (
    MemoryConsolidationEngine,
    ConsolidationRule,
    DEFAULT_CONSOLIDATION_RULES,
)

from .retrieval import (
    MemoryRetrievalEngine,
    MemoryInjector,
    RelevanceSignal,
)

from .governance import (
    MemoryGovernanceEngine,
    MemoryLineageTracker,
    GovernanceTransition,
    VALID_TRANSITIONS,
)

__all__ = [
    # Core types
    "MemoryType",
    "MemoryScope",
    "MemoryStatus",

    # Models
    "StrategicMemory",
    "StrategicMemoryCreate",
    "StrategicMemoryUpdate",
    "MemoryCandidate",
    "MemorySearchRequest",
    "MemorySearchResult",
    "MemoryInjectionContext",
    "MemoryInjection",

    # Governance
    "MemoryValidation",
    "MemorySupersedence",
    "MemoryChallenge",
    "GovernanceMetrics",

    # Templates
    "MemoryTemplates",
    "EXAMPLE_MEMORIES",

    # Consolidation
    "MemoryConsolidationEngine",
    "ConsolidationRule",
    "DEFAULT_CONSOLIDATION_RULES",

    # Retrieval
    "MemoryRetrievalEngine",
    "MemoryInjector",
    "RelevanceSignal",

    # Governance
    "MemoryGovernanceEngine",
    "MemoryLineageTracker",
    "GovernanceTransition",
    "VALID_TRANSITIONS",
]
