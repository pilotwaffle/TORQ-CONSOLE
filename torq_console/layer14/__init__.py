"""TORQ Layer 14 - Constitutional Governance Package

Layer 14 provides TORQ with constitutional governance - the ability to enforce
system rules, prevent authority abuse, and ensure decision legitimacy.
"""

from .governance import (
    # Constitutional Framework
    ConstitutionalFrameworkEngine,
    ConstitutionalRule,
    ConstitutionEvaluation,
    create_constitutional_framework_engine,
    # Authority Boundary
    AuthorityBoundaryEnforcer,
    AuthorityProfile,
    AuthorityCheck,
    create_authority_boundary_enforcer,
    # Legitimacy Scoring
    LegitimacyScoringEngine,
    LegitimacyScore,
    LegitimacyWeights,
    create_legitimacy_scoring_engine,
    # Authority Capture Detection
    AuthorityCaptureDetector,
    AuthorityRisk,
    InfluenceMetrics,
    create_authority_capture_detector,
    # Audit Ledger
    GovernanceAuditLedger,
    GovernanceRecord,
    GovernanceDecision,
    create_governance_audit_ledger,
    # Governance Service
    GovernanceService,
    create_governance_service,
    # Core Models
    GovernanceDecisionPacket,
    GovernanceResult,
    GovernanceViolation,
    AuthorityLevel,
    RuleType,
    AgentAuthority,
    SystemConstitution,
)

__version__ = "0.14.0-planning"

__all__ = [
    # Constitutional Framework
    "ConstitutionalFrameworkEngine",
    "ConstitutionalRule",
    "ConstitutionEvaluation",
    "create_constitutional_framework_engine",
    # Authority Boundary
    "AuthorityBoundaryEnforcer",
    "AuthorityProfile",
    "AuthorityCheck",
    "create_authority_boundary_enforcer",
    # Legitimacy Scoring
    "LegitimacyScoringEngine",
    "LegitimacyScore",
    "LegitimacyWeights",
    "create_legitimacy_scoring_engine",
    # Authority Capture Detection
    "AuthorityCaptureDetector",
    "AuthorityRisk",
    "InfluenceMetrics",
    "create_authority_capture_detector",
    # Audit Ledger
    "GovernanceAuditLedger",
    "GovernanceRecord",
    "GovernanceDecision",
    "create_governance_audit_ledger",
    # Governance Service
    "GovernanceService",
    "create_governance_service",
    # Core Models
    "GovernanceDecisionPacket",
    "GovernanceResult",
    "GovernanceViolation",
    "AuthorityLevel",
    "RuleType",
    "AgentAuthority",
    "SystemConstitution",
]
