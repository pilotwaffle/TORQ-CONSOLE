"""TORQ Layer 14 - Constitutional Governance

Layer 14 provides TORQ with constitutional governance - the ability to enforce
system rules, prevent authority abuse, and ensure decision legitimacy.

## Architecture

Layer 14 acts as the final legitimacy gate between economic prioritization
and execution:

1. **Constitutional Framework** - Defines and enforces system rules
2. **Authority Boundaries** - Ensures agents operate within authorized domains
3. **Legitimacy Scoring** - Computes legitimacy scores for all decisions
4. **Authority Capture Detection** - Monitors for excessive influence concentration
5. **Governance Audit Ledger** - Immutable log of all governance events

## Execution Flow

    Layer 13 Economic Prioritization
            ↓
    Layer 14 Legitimacy Check (NEW GATE)
            ↓
    Execution Fabric (Layers 6-11)

If legitimacy score is below threshold: execution is blocked.

## Key Principle

> No system decision should execute without passing constitutional legitimacy checks.
> Authority must be bounded, pluralism protected, and all actions auditable.

## Version

**Version:** 0.14.0-planning
**Status:** GOVERNANCE SCAFFOLD
**Depends On:** Layer 13 (Economic Intelligence) - v0.13.0
"""

from .constitutional_framework_engine import (
    ConstitutionalFrameworkEngine,
    ConstitutionalRule,
    ConstitutionEvaluation,
    create_constitutional_framework_engine,
)

from .authority_boundary_enforcer import (
    AuthorityBoundaryEnforcer,
    AuthorityProfile,
    AuthorityCheck,
    create_authority_boundary_enforcer,
)

from .legitimacy_scoring_engine import (
    LegitimacyScoringEngine,
    LegitimacyScore,
    LegitimacyWeights,
    create_legitimacy_scoring_engine,
)

from .authority_capture_detector import (
    AuthorityCaptureDetector,
    AuthorityRisk,
    InfluenceMetrics,
    create_authority_capture_detector,
)

from .governance_audit_ledger import (
    GovernanceAuditLedger,
    GovernanceRecord,
    GovernanceDecision,
    create_governance_audit_ledger,
)

from .models import (
    GovernanceDecisionPacket,
    GovernanceResult,
    GovernanceViolation,
    AuthorityLevel,
    RuleType,
    AgentAuthority,
    SystemConstitution,
)

from .governance_service import (
    GovernanceService,
    create_governance_service,
)


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
    # Core Models
    "GovernanceDecisionPacket",
    "GovernanceResult",
    "GovernanceViolation",
    "AuthorityLevel",
    "RuleType",
    "AgentAuthority",
    "SystemConstitution",
    # Governance Service
    "GovernanceService",
    "create_governance_service",
]


__version__ = "0.14.0-planning"
