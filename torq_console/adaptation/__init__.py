"""
Adaptation Policy Engine

Converts learning signals into governed adaptation proposals with
risk classification and approval workflows.

Ensures safe, controlled behavioral evolution through:
- Signal-to-proposal mapping
- Risk tier classification (Tier 1/2/3)
- Approval mode enforcement (auto/human/restricted)
- Guardrails (cooldowns, deduplication, evidence thresholds)
- Versioned behavior changes with rollback capability
"""

from .models import (
    AdaptationType,
    TargetAssetType,
    RiskTier,
    ApprovalMode,
    ApprovalStatus,
    AdaptationProposalCreate,
    AdaptationProposalRead,
    AdaptationProposalUpdate,
    PolicyConfig,
    ProposalApplicationResult,
    get_signal_mapping,
    get_adaptation_type,
)

from .policy import AdaptationPolicyEngine
from .mapper import SignalToProposalMapper
from .service import AdaptationProposalService
from .api import router as adaptation_router

__all__ = [
    # Models
    "AdaptationType",
    "TargetAssetType",
    "RiskTier",
    "ApprovalMode",
    "ApprovalStatus",
    "AdaptationProposalCreate",
    "AdaptationProposalRead",
    "AdaptationProposalUpdate",
    "PolicyConfig",
    "ProposalApplicationResult",
    # Utilities
    "get_signal_mapping",
    "get_adaptation_type",
    # Components
    "AdaptationPolicyEngine",
    "SignalToProposalMapper",
    "AdaptationProposalService",
    # API
    "adaptation_router",
]
