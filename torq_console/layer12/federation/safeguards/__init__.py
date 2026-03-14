"""
TORQ Federation Safeguards

Phase 1B Hardening - Core epistemic safety guarantees for federated knowledge exchange.

This package provides five critical safeguards that operate in the inbound
federation pipeline to prevent insight flood, context collapse, knowledge
monoculture, authority concentration, and trust drift.

## Safeguard Pipeline Order

Claims flow through safeguards in this order:

1. **FederationEligibilityFilter** - Quality gate (content quality, rate limits, spam)
2. **ContextSimilarityEngine** - Context collapse detection (semantic clustering)
3. **PluralityPreservationRules** - Monoculture prevention (viewpoint diversity)
4. **AllocativeBoundaryGuard** - Centralization prevention (resource distribution)
5. **TrustDecayModel** - Trust drift detection (temporal trust patterns)

## Usage

```python
from torq_console.layer12.federation.safeguards import (
    create_eligibility_filter,
    create_context_similarity_engine,
    create_plurality_preservation_rules,
    create_allocative_boundary_guard,
    create_trust_decay_model,
)

# Create safeguards
eligibility_filter = create_eligibility_filter()
similarity_engine = create_context_similarity_engine()
plurality_rules = create_plurality_preservation_rules()
allocative_guard = create_allocative_boundary_guard()
trust_decay = create_trust_decay_model()

# Process inbound claim
eligibility_result = eligibility_filter.check_claim_eligibility(artifact, envelope_id, source_node_id)
similarity_result = similarity_engine.analyze_claim(artifact, envelope_id, source_node_id)
plurality_result = plurality_rules.analyze_claim(artifact, envelope_id, source_node_id)
allocative_result = allocative_guard.evaluate_claim(artifact, envelope_id, source_node_id)
decay_result = trust_decay.assess_trust_decay(artifact, envelope_id, source_node_id, trust_score)

# Combine results for final decision
if (eligibility_result.is_eligible and
    not similarity_result.should_throttle and
    plurality_result.assessment.plurality_level != "monoculture" and
    allocative_result.is_allowed and
    decay_result.recommendation != "reject"):
    # Accept claim for federation
    pass
```

## Key Concepts

### Eligibility Filter
Prevents low-quality or spam content from entering federation.
- Content quality thresholds (confidence, length, provenance)
- Rate limiting per node
- Spam keyword detection
- Near-duplicate prevention

### Context Similarity Engine
Detects semantic clustering and context monoculture.
- Keyword-based similarity clustering
- Diversity scoring via Shannon entropy
- Source concentration detection
- Cluster size monitoring

### Plurality Preservation Rules
Enforces viewpoint diversity within topic domains.
- Perspective-based grouping (not just semantic similarity)
- Contradiction tracking (healthy for plurality)
- Minority perspective protection
- At-risk perspective detection

### Allocative Boundary Guard
Prevents authority and resource concentration.
- Gini coefficient and Herfindahl Index tracking
- Dominant node detection and throttling
- Domain leadership limits
- Fair distribution enforcement

### Trust Decay Model
Detects trust drift and anomalous patterns.
- Linear regression trend analysis
- Sudden spike/drop detection
- Volatility monitoring
- Predictive trust trajectory

---

*Generated: Phase 1B Federation Hardening*
*Layer 12: Collective Intelligence Exchange*
"""

from torq_console.layer12.federation.safeguards.federation_eligibility_filter import (
    EligibilityCriteria,
    EligibilityResult,
    FederationEligibilityFilter,
    NodeRateTracker,
    create_eligibility_filter,
)

from torq_console.layer12.federation.safeguards.context_similarity_engine import (
    ContextRiskProfile,
    ContextSimilarityEngine,
    SimilarityEngineConfig,
    SimilarityAnalysisResult,
    TopicCluster,
    create_context_similarity_engine,
)

from torq_console.layer12.federation.safeguards.plurality_preservation_rules import (
    ContradictionReport,
    PerspectiveCluster,
    PerspectiveSignature,
    PluralityAssessment,
    PluralityMetrics,
    PluralityAnalysisResult,
    PluralityPreservationConfig,
    PluralityPreservationRules,
    create_plurality_preservation_rules,
)

from torq_console.layer12.federation.safeguards.allocative_boundary_guard import (
    AllocativeBoundaryConfig,
    AllocativeBoundaryGuard,
    AllocativeDecision,
    AllocativeSnapshot,
    NodeAllocativeProfile,
    create_allocative_boundary_guard,
)

from torq_console.layer12.federation.safeguards.trust_decay_model import (
    TrustDecayAssessment,
    TrustDecayConfig,
    TrustDecayModel,
    TrustObservation,
    TrustTrajectory,
    create_trust_decay_model,
)

__all__ = [
    # FederationEligibilityFilter
    "EligibilityCriteria",
    "EligibilityResult",
    "FederationEligibilityFilter",
    "NodeRateTracker",
    "create_eligibility_filter",

    # ContextSimilarityEngine
    "ContextRiskProfile",
    "ContextSimilarityEngine",
    "SimilarityEngineConfig",
    "SimilarityAnalysisResult",
    "TopicCluster",
    "create_context_similarity_engine",

    # PluralityPreservationRules
    "ContradictionReport",
    "PerspectiveCluster",
    "PerspectiveSignature",
    "PluralityAssessment",
    "PluralityMetrics",
    "PluralityAnalysisResult",
    "PluralityPreservationConfig",
    "PluralityPreservationRules",
    "create_plurality_preservation_rules",

    # AllocativeBoundaryGuard
    "AllocativeBoundaryConfig",
    "AllocativeBoundaryGuard",
    "AllocativeDecision",
    "AllocativeSnapshot",
    "NodeAllocativeProfile",
    "create_allocative_boundary_guard",

    # TrustDecayModel
    "TrustDecayAssessment",
    "TrustDecayConfig",
    "TrustDecayModel",
    "TrustObservation",
    "TrustTrajectory",
    "create_trust_decay_model",
]
