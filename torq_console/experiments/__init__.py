"""
Behavior Experiment & Versioning Layer

Completes the adaptive cognition loop with:
- Behavior version registry (prompt, routing, tool profiles)
- Deterministic hash-based traffic assignment
- Experiment orchestration (control vs candidate)
- Impact measurement from evaluation metrics
- Promotion and rollback with full traceability

Flow:
Approved Proposal → Candidate Version → Experiment → Assignment
→ Execution with Variant → Evaluation → Impact Analysis → Promote/Rollback
"""

from .models import (
    BehaviorAssetType,
    BehaviorVersionStatus,
    BehaviorVersionCreate,
    BehaviorVersionRead,
    ExperimentStatus,
    AssignmentMode,
    BehaviorExperimentCreate,
    BehaviorExperimentRead,
    ExperimentImpactSummary,
    AdaptationImpact,
    AssignmentRequest,
    AssignmentResponse,
    PromotionDecision,
    RollbackDecision,
)

from .assigner import ExperimentAssigner, AssignmentValidator, compute_assignment_hash
from .analyzer import ExperimentImpactAnalyzer
from .service import BehaviorExperimentService
from .api import router as experiments_router

__all__ = [
    # Models
    "BehaviorAssetType",
    "BehaviorVersionStatus",
    "BehaviorVersionCreate",
    "BehaviorVersionRead",
    "ExperimentStatus",
    "AssignmentMode",
    "BehaviorExperimentCreate",
    "BehaviorExperimentRead",
    "ExperimentImpactSummary",
    "AdaptationImpact",
    "AssignmentRequest",
    "AssignmentResponse",
    "PromotionDecision",
    "RollbackDecision",
    # Components
    "ExperimentAssigner",
    "AssignmentValidator",
    "compute_assignment_hash",
    "ExperimentImpactAnalyzer",
    "BehaviorExperimentService",
    # API
    "experiments_router",
]
