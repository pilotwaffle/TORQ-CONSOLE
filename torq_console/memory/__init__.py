"""
Memory management for TORQ Console agents.

Provides two memory systems:
1. Letta integration - Persistent memory and context management
2. Governed Memory (Phase 4H.1) - Validated, artifact-based memory with controls
"""

# Letta integration (existing)
from .letta_integration import (
    LettaMemoryManager,
    get_memory_manager as get_letta_memory_manager,
    initialize_memory as initialize_letta_memory,
    LETTA_AVAILABLE
)

# Governed Memory (Phase 4H.1)
from .memory_models import (
    # Enums
    MemoryType,
    ConfidenceLevel,
    MemoryStatus,
    ValidationDecision,
    RejectionReason,
    # Core models
    MemoryProvenance,
    MemoryMetadata,
    MemoryContent,
    MemoryCandidate,
    ValidatedMemory,
    # Rules
    EligibilityRule,
    EligibilityRuleset,
    # Helpers
    DEFAULT_ELIGIBILITY_RULESET,
    FRESHNESS_RULES,
    get_freshness_window,
    confidence_to_level,
    level_to_min_score,
)

from .eligibility_rules import (
    EligibilityEngine,
    ConflictDetector,
    get_eligibility_engine,
    get_conflict_detector,
    ELIGIBLE_ARTIFACT_TYPES,
    INELIGIBLE_ARTIFACT_TYPES,
    CONFIDENCE_REQUIREMENTS,
    COMPLETENESS_REQUIREMENTS,
    REQUIRED_FIELDS,
)

from .memory_persistence import (
    MemoryPersistenceService,
    MemoryWritePipeline,
    MemoryRecord,
    RejectionLog,
    get_memory_persistence,
    get_memory_write_pipeline,
)

__all__ = [
    # Letta integration (existing)
    'LettaMemoryManager',
    'get_letta_memory_manager',
    'initialize_letta_memory',
    'LETTA_AVAILABLE',
    # Governed Memory (Phase 4H.1)
    'MemoryType',
    'ConfidenceLevel',
    'MemoryStatus',
    'ValidationDecision',
    'RejectionReason',
    'MemoryProvenance',
    'MemoryMetadata',
    'MemoryContent',
    'MemoryCandidate',
    'ValidatedMemory',
    'EligibilityRule',
    'EligibilityRuleset',
    'DEFAULT_ELIGIBILITY_RULESET',
    'FRESHNESS_RULES',
    'get_freshness_window',
    'confidence_to_level',
    'level_to_min_score',
    'EligibilityEngine',
    'ConflictDetector',
    'get_eligibility_engine',
    'get_conflict_detector',
    'ELIGIBLE_ARTIFACT_TYPES',
    'INELIGIBLE_ARTIFACT_TYPES',
    'CONFIDENCE_REQUIREMENTS',
    'COMPLETENESS_REQUIREMENTS',
    'REQUIRED_FIELDS',
    # Milestone 2: Write Pipeline
    'MemoryPersistenceService',
    'MemoryWritePipeline',
    'MemoryRecord',
    'RejectionLog',
    'get_memory_persistence',
    'get_memory_write_pipeline',
]

# Backward compatibility aliases
get_memory_manager = get_letta_memory_manager
initialize_memory = initialize_letta_memory
