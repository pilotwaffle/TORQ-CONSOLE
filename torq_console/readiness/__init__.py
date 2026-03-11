"""
TORQ Readiness Checker for Observation Mode Transition

This module provides the governance layer that decides when TORQ should allow
a capability to move from observation mode into active use.

Architecture:
    Execution / Tools / Teams / Memory / Insights / Patterns
                            │
                            ▼
                    Readiness Evidence Collector
                            │
                            ▼
                     Readiness Scoring Engine
                            │
         ┌──────────────┼──────────────┐
         ▼              ▼              ▼
     Policy Gate    Audit Logger   Transition Controller
         │              │              │
         └──────────────┴──────────────┘
                            │
                            ▼
                  Observation Mode Decision
    observed | watchlist | ready | blocked | regressed

Phase Milestones:
    M1: Readiness object model + policy schema ✅
    M2: Evidence collection and scoring engine ✅
    M3: Transition controller and governance actions ✅
    M4: Query / inspection / audit layer 🔄 IN PROGRESS
    M5: Hardening & regression
"""

from .readiness_models import (
    # Candidate Types
    CandidateType,
    CandidateScope,

    # Readiness States
    ReadinessState,
    ReadinessOutcome,

    # Core Models
    ReadinessCandidate,
    ReadinessEvaluation,
    ReadinessScore,
    EvidenceSummary,

    # Policy
    PolicyProfile,
    PolicyDimension,
    HardBlockRule,
    ReadinessThresholds,

    # Transitions
    TransitionRequest,
    TransitionResult,
    TransitionEvent,

    # Templates
    DEFAULT_POLICY_PROFILES,
    DEFAULT_READINESS_THRESHOLDS,
)

from .readiness_policy import (
    # Policy Management
    ReadinessPolicyRegistry,
    get_policy_registry,

    # Hard Block Evaluation
    HardBlockEvaluator,
    get_hard_block_evaluator,

    # Policy Application
    PolicyApplicator,
    get_policy_applicator,
)

from .evidence_collector import (
    # Evidence Collection Interface
    EvidenceCollector,
    CollectorResult,
    CollectorError,

    # Dimension Collectors
    ExecutionStabilityCollector,
    ArtifactCompletenessCollector,
    MemoryConfidenceCollector,
    InsightQualityCollector,
    PatternConfidenceCollector,
    AuditCoverageCollector,
    PolicyComplianceCollector,
    OperationalConsistencyCollector,

    # Collection Orchestration
    EvidenceCollectionOrchestrator,
    collect_all_evidence,
    get_evidence_orchestrator,
)

from .scoring_engine import (
    # Scoring Engine
    ReadinessScoringEngine,
    ScoreBreakdown,
    ScoringContext,
    compute_readiness_score,
    get_scoring_engine,
)

from .transition_controller import (
    # Transition Controller
    ReadinessTransitionController,
    get_transition_controller,

    # Governance Engine
    GovernanceActionEngine,
    GovernanceActionType,
    GovernanceAction,
    get_governance_engine,

    # State Machine
    ReadinessStateMachine,
    get_state_machine,

    # Policy Validator
    TransitionPolicyValidator,

    # Audit Log
    TransitionAuditLog,
    get_audit_logs,
    add_audit_log,
)

# M4: Inspection and Query Layer
from .inspection_models import (
    # Inspection Models
    ReadinessInspection,
    TransitionRecord,
    DimensionScoreView,
    EvidenceSummaryView,
    GovernanceActionView,

    # Query Models
    CandidateListFilter,
    CandidateListItem,
    CandidateListResult,

    # Analytics Models
    StateDistribution,
    ReadinessMetrics,
    ReadinessTrend,

    # Report Models
    ReadinessReportSection,
    CandidateReadinessReport,
    SystemReadinessReport,

    # Helpers
    get_score_label,
    get_dimension_label,
)

from .query_service import (
    # Query Service
    ReadinessQueryService,
    get_query_service,

    # Storage helpers
    register_candidate,
    add_evaluation,
    get_candidate_storage,
    clear_candidate_storage,
)

from .inspection_service import (
    # Inspection Service
    ReadinessInspectionService,
    get_inspection_service,
)

from .audit_service import (
    # Audit Service
    ReadinessAuditService,
    TransitionAuditFilter,
    get_audit_service,
)

from .analytics_service import (
    # Analytics Service
    ReadinessAnalyticsService,
    get_analytics_service,
)

from .report_builder import (
    # Report Builder
    ReadinessReportBuilder,
    get_report_builder,
)

__all__ = [
    # Models
    "CandidateType",
    "CandidateScope",
    "ReadinessState",
    "ReadinessOutcome",
    "ReadinessCandidate",
    "ReadinessEvaluation",
    "ReadinessScore",
    "EvidenceSummary",
    "PolicyProfile",
    "PolicyDimension",
    "HardBlockRule",
    "ReadinessThresholds",
    "TransitionRequest",
    "TransitionResult",
    "TransitionEvent",
    "DEFAULT_POLICY_PROFILES",
    "DEFAULT_READINESS_THRESHOLDS",

    # Policy
    "ReadinessPolicyRegistry",
    "get_policy_registry",
    "HardBlockEvaluator",
    "get_hard_block_evaluator",
    "PolicyApplicator",
    "get_policy_applicator",

    # Evidence Collection
    "EvidenceCollector",
    "CollectorResult",
    "CollectorError",
    "ExecutionStabilityCollector",
    "ArtifactCompletenessCollector",
    "MemoryConfidenceCollector",
    "InsightQualityCollector",
    "PatternConfidenceCollector",
    "AuditCoverageCollector",
    "PolicyComplianceCollector",
    "OperationalConsistencyCollector",
    "EvidenceCollectionOrchestrator",
    "collect_all_evidence",
    "get_evidence_orchestrator",

    # Scoring Engine
    "ReadinessScoringEngine",
    "ScoreBreakdown",
    "ScoringContext",
    "compute_readiness_score",
    "get_scoring_engine",

    # Transition Controller
    "ReadinessTransitionController",
    "get_transition_controller",

    # Governance Engine
    "GovernanceActionEngine",
    "GovernanceActionType",
    "GovernanceAction",
    "get_governance_engine",

    # State Machine
    "ReadinessStateMachine",
    "get_state_machine",

    # Policy Validator
    "TransitionPolicyValidator",

    # Audit Log
    "TransitionAuditLog",
    "get_audit_logs",
    "add_audit_log",

    # Inspection Models (M4)
    "ReadinessInspection",
    "TransitionRecord",
    "DimensionScoreView",
    "EvidenceSummaryView",
    "GovernanceActionView",
    "CandidateListFilter",
    "CandidateListItem",
    "CandidateListResult",
    "StateDistribution",
    "ReadinessMetrics",
    "ReadinessTrend",
    "ReadinessReportSection",
    "CandidateReadinessReport",
    "SystemReadinessReport",
    "get_score_label",
    "get_dimension_label",

    # Query Service (M4)
    "ReadinessQueryService",
    "get_query_service",
    "register_candidate",
    "add_evaluation",

    # Inspection Service (M4)
    "ReadinessInspectionService",
    "get_inspection_service",

    # Audit Service (M4)
    "ReadinessAuditService",
    "TransitionAuditFilter",
    "get_audit_service",

    # Analytics Service (M4)
    "ReadinessAnalyticsService",
    "get_analytics_service",

    # Report Builder (M4)
    "ReadinessReportBuilder",
    "get_report_builder",
]
