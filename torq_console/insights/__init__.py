"""
Insight Publishing & Agent Retrieval - Phase Overview

This module provides the insight layer for TORQ Console.

Layer Architecture:
- Artifact = Raw persisted execution output (Phase 5.3)
- Memory = Validated carry-forward knowledge (Phase 4H.1)
- Insight = Curated, publishable intelligence for reuse (This Phase)

Key Components:
- models.py: Insight data models and types
- publishing_rules.py: Quality gates and publication criteria
- candidate_extractor.py: Extract insight candidates from memory
- validation_service.py: Publishing validation and conflict detection
- persistence.py: Store insights with lineage tracking
- approval_workflow.py: Approval/rejection/supersession workflows
- retrieval.py: Agent retrieval service with context-aware queries
- inspection.py: Inspection, audit, and governance layer
"""

from .models import (
    # Insight Types
    InsightType,
    InsightLifecycleState,
    InsightScope,
    InsightSourceType,

    # Core Models
    Insight,
    InsightCreate,
    InsightUpdate,

    # Source Reference
    SourceReference,

    # Quality
    QualityMetrics,
    QualityGateResult,

    # Publishing
    PublicationRequest,
    PublicationResult,
    PublishingRule,
    PublishingCriteria,

    # Retrieval
    InsightRetrievalRequest,
    InsightRetrievalResult,
    InsightInjection,

    # Templates
    InsightTemplates,

    # Examples
    EXAMPLE_INSIGHTS,
)

from .publishing_rules import (
    # Quality Gates
    QUALITY_GATES,
    QualityGateConfig,

    # Publishing Rules
    get_default_publishing_rules,
    get_default_publishing_criteria,

    # Eligibility Checker
    PublicationEligibilityChecker,

    # Lifecycle Transitions
    LifecycleTransition,
    LIFECYCLE_TRANSITIONS,
    get_valid_transitions,
    is_transition_valid,
    get_transition,
)

from .candidate_extractor import (
    # Extraction
    InsightCandidateExtractor,
    ExtractionRule,
    ExtractionResult,
    DEFAULT_EXTRACTION_RULES,
    extract_insight_candidates,
    get_extraction_summary,
    get_default_extractor,
    is_memory_extractable,
)

from .validation_service import (
    # Validation
    ValidationResult,
    DuplicationCheck,
    DuplicationDetector,
    PublishingValidator,
    validate_candidates_for_publication,
    get_validation_summary,
    get_default_validator,
)

from .persistence import (
    # Persistence
    InsightPersistence,
    InsightRecord,
    RejectionRecord,
    SupabaseInsightPersistence,
    MemoryInsightPersistence,
    get_insight_persistence,
)

from .approval_workflow import (
    # Workflow
    TransitionRequest,
    TransitionResult,
    ApprovalResult,
    RejectionResult,
    ApprovalWorkflowService,
    approve_batch,
    reject_batch,
    get_approval_workflow,
)

from .retrieval import (
    # Retrieval
    RetrievalContext,
    RetrievalResult,
    InsightPayload,
    ProvenanceSummary,
    SuppressedInsight,
    RetrievalAuditEntry,
    RankingConfig,
    InsightRetrievalService,
    get_retrieval_service,
)

from .inspection import (
    # Inspection
    InsightLineage,
    LifecycleEvent,
    UsageRecord,
    InsightDetail,
    RetrievalAuditSummary,
    PublicationAuditTrail,
    RankingExplanation,
    GovernanceAction,
    InsightTypeConfig,
    InsightInspectionService,
    get_inspection_service,
)


__all__ = [
    # Models
    "InsightType",
    "InsightLifecycleState",
    "InsightScope",
    "InsightSourceType",
    "Insight",
    "InsightCreate",
    "InsightUpdate",
    "SourceReference",
    "QualityMetrics",
    "QualityGateResult",
    "PublicationRequest",
    "PublicationResult",
    "PublishingRule",
    "PublishingCriteria",
    "InsightRetrievalRequest",
    "InsightRetrievalResult",
    "InsightInjection",
    "InsightTemplates",
    "EXAMPLE_INSIGHTS",

    # Publishing Rules
    "QUALITY_GATES",
    "QualityGateConfig",
    "get_default_publishing_rules",
    "get_default_publishing_criteria",
    "PublicationEligibilityChecker",

    # Lifecycle
    "LifecycleTransition",
    "LIFECYCLE_TRANSITIONS",
    "get_valid_transitions",
    "is_transition_valid",
    "get_transition",

    # Extraction
    "InsightCandidateExtractor",
    "ExtractionRule",
    "ExtractionResult",
    "DEFAULT_EXTRACTION_RULES",
    "extract_insight_candidates",
    "get_extraction_summary",
    "get_default_extractor",
    "is_memory_extractable",

    # Validation
    "ValidationResult",
    "DuplicationCheck",
    "DuplicationDetector",
    "PublishingValidator",
    "validate_candidates_for_publication",
    "get_validation_summary",
    "get_default_validator",

    # Persistence
    "InsightPersistence",
    "InsightRecord",
    "RejectionRecord",
    "SupabaseInsightPersistence",
    "MemoryInsightPersistence",
    "get_insight_persistence",

    # Workflow
    "TransitionRequest",
    "TransitionResult",
    "ApprovalResult",
    "RejectionResult",
    "ApprovalWorkflowService",
    "approve_batch",
    "reject_batch",
    "get_approval_workflow",

    # Retrieval
    "RetrievalContext",
    "RetrievalResult",
    "InsightPayload",
    "ProvenanceSummary",
    "SuppressedInsight",
    "RetrievalAuditEntry",
    "RankingConfig",
    "InsightRetrievalService",
    "get_retrieval_service",

    # Inspection
    "InsightLineage",
    "LifecycleEvent",
    "UsageRecord",
    "InsightDetail",
    "RetrievalAuditSummary",
    "PublicationAuditTrail",
    "RankingExplanation",
    "GovernanceAction",
    "InsightTypeConfig",
    "InsightInspectionService",
    "get_inspection_service",
]
