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
    M2: Evidence collection and scoring engine 🔄 IN PROGRESS
    M3: Transition controller and governance actions
    M4: Query / inspection / audit layer
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
]
