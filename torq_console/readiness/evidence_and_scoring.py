"""
TORQ Readiness Checker - Evidence Collection and Scoring Engine

Milestone 2: Collect evidence from TORQ subsystems and compute readiness scores.

Collects evidence from:
- Execution history (5.2)
- Workspace artifacts (5.3)
- Strategic memory (4H.1)
- Published insights (Insight Publishing)
- Validated patterns (4G)
- Audit coverage
- Policy compliance signals
- Operational consistency signals

Produces:
- Dimension-level scores
- Weighted overall score
- Hard-block evaluation
- Final readiness outcome
"""

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

    # Score Computation
    compute_readiness_score,
    get_scoring_engine,
)

__all__ = [
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
