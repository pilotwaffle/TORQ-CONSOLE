"""
Phase 4G: Pattern Aggregation

This module provides pattern detection and aggregation capabilities for TORQ Console.

Layer Architecture:
- Artifact = Raw execution output (Phase 5.3)
- Memory = Validated carry-forward knowledge (Phase 4H.1)
- Insight = Curated reusable intelligence (Insight Publishing M1-M4)
- Pattern = Recurring, cross-execution structure or signal (This Phase - 4G)

Key Components:
- pattern_models.py: Pattern data models and types (Milestone 1)
- aggregation_rules.py: Rules for aggregating observations into patterns (Milestone 1)
- extraction.py: Pattern extraction and aggregation pipeline (Milestone 2)
- validation.py: Pattern validation and promotion workflow (Milestone 3)
- query.py: Pattern query, inspection, and audit layer (Milestone 4)
"""

from .pattern_models import (
    # Pattern Types
    PatternType,

    # Lifecycle States
    PatternLifecycleState,

    # Source Types
    PatternSourceType,

    # Core Models
    Pattern,
    PatternCreate,
    PatternUpdate,
    PatternSourceReference,
    PatternQualityMetrics,

    # Aggregation Models
    AggregationEligibilityRule,
    PatternLineageRequirement,
    AggregationCriteria,

    # Detection Models
    PatternObservation,
    PatternDetectionResult,

    # Templates
    PatternTemplates,
    EXAMPLE_PATTERNS,
)

from .aggregation_rules import (
    # Eligibility
    PatternTypeEligibility,
    DEFAULT_ELIGIBILITY_RULES,
    get_eligibility_rules,

    # Quality Thresholds
    PatternQualityThresholds,
    DEFAULT_QUALITY_THRESHOLDS,

    # Lifecycle
    LIFECYCLE_TRANSITIONS,
    is_transition_valid,
    get_valid_transitions,

    # Validators
    AggregationEligibilityChecker,
    PatternLifecycleValidator,

    # Convenience Functions
    get_default_eligibility_checker,
    get_default_lifecycle_validator,
    check_pattern_eligibility,
    validate_pattern_transition,
)

from .extraction import (
    # Extraction Source Models
    ExtractionSource,
    PatternEvidence,
    RejectionReason,
    PatternRejectionRecord,

    # Pattern Candidate Models
    PatternCandidate,

    # Extractor
    PatternCandidateExtractor,

    # Aggregation
    PatternAggregationEngine,

    # Scoring
    PatternScoringService,

    # Persistence
    PatternPersistenceService,

    # Pipeline
    PatternExtractionPipeline,

    # Convenience Functions
    run_pattern_extraction,
    extract_and_aggregate,
)

from .validation import (
    # Validation Outcomes
    ValidationOutcome,
    ValidationResult,

    # Promotion Models
    PromotionRequest,
    PromotionResult,

    # Validation Thresholds
    ValidationThresholds,

    # Validation Service
    PatternValidationService,

    # Promotion Workflow
    PatternPromotionWorkflow,

    # Supersession Handler
    PatternSupersessionHandler,

    # Audit Logger
    PatternAuditRecord,
    PatternAuditLogger,

    # Orchestrator
    PatternValidationOrchestrator,

    # Convenience Functions
    validate_pattern_candidate,
    promote_pattern,
    check_pattern_supersession,
)

from .query import (
    # Query
    PatternQueryFilter,
    PatternQuerySort,
    PatternQueryResult,
    PatternQueryService,

    # Inspection
    PatternEvidenceSummary,
    PatternScoreBreakdown,
    PatternLifecycleHistoryEntry,
    PatternSupersessionInfo,
    PatternInspectionView,
    PatternInspectionService,

    # Audit
    PatternDecisionRecord,
    PatternPromotionRecord,
    PatternSupersessionRecord,
    PatternAuditView,
    PatternAuditService,

    # Governance
    GovernanceAction,
    GovernanceActionResult,
    PatternGovernanceService,

    # Convenience Functions
    create_pattern_query_service,
    create_pattern_inspection_service,
    create_pattern_audit_service,
    create_pattern_governance_service,
)


__all__ = [
    # Pattern Types
    "PatternType",

    # Lifecycle States
    "PatternLifecycleState",

    # Source Types
    "PatternSourceType",

    # Core Models
    "Pattern",
    "PatternCreate",
    "PatternUpdate",
    "PatternSourceReference",
    "PatternQualityMetrics",

    # Aggregation
    "AggregationEligibilityRule",
    "PatternLineageRequirement",
    "AggregationCriteria",

    # Detection
    "PatternObservation",
    "PatternDetectionResult",

    # Templates
    "PatternTemplates",
    "EXAMPLE_PATTERNS",

    # Eligibility
    "PatternTypeEligibility",
    "DEFAULT_ELIGIBILITY_RULES",
    "get_eligibility_rules",

    # Quality
    "PatternQualityThresholds",
    "DEFAULT_QUALITY_THRESHOLDS",

    # Lifecycle
    "LIFECYCLE_TRANSITIONS",
    "is_transition_valid",
    "get_valid_transitions",

    # Validators
    "AggregationEligibilityChecker",
    "PatternLifecycleValidator",

    # Convenience
    "get_default_eligibility_checker",
    "get_default_lifecycle_validator",
    "check_pattern_eligibility",
    "validate_pattern_transition",

    # Extraction (Milestone 2)
    "ExtractionSource",
    "PatternEvidence",
    "RejectionReason",
    "PatternRejectionRecord",
    "PatternCandidate",
    "PatternCandidateExtractor",
    "PatternAggregationEngine",
    "PatternScoringService",
    "PatternPersistenceService",
    "PatternExtractionPipeline",
    "run_pattern_extraction",
    "extract_and_aggregate",

    # Validation (Milestone 3)
    "ValidationOutcome",
    "ValidationResult",
    "PromotionRequest",
    "PromotionResult",
    "ValidationThresholds",
    "PatternValidationService",
    "PatternPromotionWorkflow",
    "PatternSupersessionHandler",
    "PatternAuditRecord",
    "PatternAuditLogger",
    "PatternValidationOrchestrator",
    "validate_pattern_candidate",
    "promote_pattern",
    "check_pattern_supersession",

    # Query (Milestone 4)
    "PatternQueryFilter",
    "PatternQuerySort",
    "PatternQueryResult",
    "PatternQueryService",
    "PatternEvidenceSummary",
    "PatternScoreBreakdown",
    "PatternLifecycleHistoryEntry",
    "PatternSupersessionInfo",
    "PatternInspectionView",
    "PatternInspectionService",
    "PatternDecisionRecord",
    "PatternPromotionRecord",
    "PatternSupersessionRecord",
    "PatternAuditView",
    "PatternAuditService",
    "GovernanceAction",
    "GovernanceActionResult",
    "PatternGovernanceService",
    "create_pattern_query_service",
    "create_pattern_inspection_service",
    "create_pattern_audit_service",
    "create_pattern_governance_service",
]
