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
- (Future) publishing_service.py: Insight publishing pipeline
- (Future) retrieval_service.py: Agent retrieval interface
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
]
