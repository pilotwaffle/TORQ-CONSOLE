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

from .query_service import (
    MemoryQueryService,
    MemoryQuery,
    MemoryQueryResult,
    MemoryInspection,
    ProvenanceFilter,
    FreshnessFilter,
    AccessLogEntry,
    get_memory_query_service,
)

from .inspection_service import (
    MemoryInspectionService,
    MemoryRecordDetail,
    MemoryTraceability,
    ValidationDecisionReport,
    RejectionLogEntry,
    RetrievalAuditRecord,
    RetrievalAuditSummary,
    GovernanceAction,
    GovernanceActionResult,
    get_memory_inspection_service,
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

    # Query (Phase 4H.1 Milestone 3)
    "MemoryQueryService",
    "MemoryQuery",
    "MemoryQueryResult",
    "MemoryInspection",
    "ProvenanceFilter",
    "FreshnessFilter",
    "AccessLogEntry",
    "get_memory_query_service",

    # Inspection & Control (Phase 4H.1 Milestone 4)
    "MemoryInspectionService",
    "MemoryRecordDetail",
    "MemoryTraceability",
    "ValidationDecisionReport",
    "RejectionLogEntry",
    "RetrievalAuditRecord",
    "RetrievalAuditSummary",
    "GovernanceAction",
    "GovernanceActionResult",
    "get_memory_inspection_service",
]
