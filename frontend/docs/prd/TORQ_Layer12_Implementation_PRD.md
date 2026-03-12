# TORQ Console
# Layer 12 Implementation PRD
# Collective Intelligence Exchange

**Document Location:** docs/prd/TORQ_Layer12_Implementation_PRD.md
**Status:** Implementation Specification
**Version:** 1.0
**Date:** 2026-03-12

---

# 1. Executive Summary

## 1.1 Purpose

This PRD translates the Federated Epistemology architecture into concrete implementation specifications for Layer 12 — Collective Intelligence Exchange.

## 1.2 What Layer 12 Does

Layer 12 enables TORQ nodes to share insights, patterns, and recommendations across the distributed fabric **without creating centralized truth authority**.

## 1.3 Core Design Principles

| Principle | Meaning |
|-----------|---------|
| **Provenance Over Assertion** | Every shared artifact preserves its origin |
| **Context Over Universality** | Knowledge is situated, not universal |
| **Confidence Over Certainty** | All shared knowledge is probabilistic |
| **Local Interpretation** | Receiving nodes qualify locally before adopting |
| **Plurality Over Monoculture** | Multiple competing explanations are preserved |

## 1.4 Anti-Goals

What Layer 12 explicitly does **NOT** do:

- Create a global "best practice" registry
- Rank insights by universal score
- Allow shared artifacts to become directly authoritative
- Enable cross-node state leakage
- Bypass local governance

---

# 2. Scope & Objectives

## 2.1 In Scope

| Component | Description |
|-----------|-------------|
| **Epistemic Artifact Publisher** | Package insights/patterns as federatable claims |
| **Federated Claim Registry** | Store network-visible claims with evidence |
| **Local Qualification Engine** | Evaluate incoming claims for local adoption |
| **Contradiction & Plurality Manager** | Track conflicting claims without collapse |
| **Epistemic Audit Service** | Track knowledge exchange and adoption |
| **Claim Exchange APIs** | Publish, query, retrieve, qualify claims |
| **Data Models** | TypeScript interfaces, database schemas |
| **UI Surfaces** | Operator visibility into collective intelligence |
| **Integration** | L11 fabric connectivity, L13 mediation prep |

## 2.2 Out of Scope

| Component | Why Out of Scope |
|-----------|------------------|
| **Layer 13 Economic Intelligence** | Separate layer, depends on L12 |
| **Layer 14 Constitutional Authority** | Separate layer, validates L12→L13 |
| **Layer 15 Meta-Strategic** | Roadmap-level, requires L12-L14 stability |
| **Raw State Federation** | Explicitly forbidden by architecture |
| **Direct Economic Routing** | Must go through L13 mediation |
| **Universal Truth Authority** | Explicitly anti-goal |

## 2.3 Success Criteria

Layer 12 is complete when:

1. ✅ Node can publish an insight as an epistemic artifact
2. ✅ Other nodes can retrieve that artifact
3. ✅ Retrieving node qualifies artifact locally
4. ✅ Artifact is never treated as authoritative by default
5. ✅ Contradictions are preserved, not collapsed
6. ✅ All exchanges produce audit records
7. ✅ No raw operational state is federated
8. ✅ Integration tests pass end-to-end
9. ✅ UI surfaces show shared claims, qualifications, contradictions
10. ✅ No artifact bypasses local qualification

---

# 3. Service Specifications

## 3.1 EpistemicArtifactPublisher

### Purpose

Publishes local insights and patterns as federatable epistemic artifacts.

### Responsibilities

- Package insight/pattern with complete provenance
- Attach context metadata
- Declare allowed uses
- Include uncertainty/confidence scores
- Redact local references and sensitive data
- Export to federation boundary

### Interface

```typescript
interface EpistemicArtifactPublisher {
  // Publish an insight as a federatable artifact
  publishArtifact(
    insight: PublishedInsight | Pattern,
    options: PublicationOptions
  ): Promise<EpistemicArtifact>;

  // Redact local references before federation
  redactForFederation(artifact: EpistemicArtifact): Promise<RedactedArtifact>;

  // Validate artifact meets publication standards
  validateForPublication(artifact: EpistemicArtifact): ValidationResult;

  // Check if insight is eligible for federation
  isFederatable(insight: PublishedInsight | Pattern): boolean;
}
```

### Publication Options

```typescript
interface PublicationOptions {
  allowedUses: AllowedUse[];
  transferabilityHint: TransferabilityLevel;
  requiresContext?: string[];
  limitations?: string[];
  contradictions?: string[];  // References to conflicting claims
}
```

### Implementation Notes

- **Redaction is mandatory**: Remove node-specific IDs, local paths, PII
- **Provenance preservation**: Never mask origin node or layer
- **Context bundling**: Include domain, mission type, agent topology
- **Uncertainty encoding**: Confidence 0-1, stability score, reproducibility

### Service Location

```
src/services/layer12/EpistemicArtifactPublisher.ts
```

---

## 3.2 FederatedClaimRegistry

### Purpose

Stores network-visible epistemic claims. Acts as a **claim exchange**, not a truth database.

### Responsibilities

- Store epistemic artifacts
- Index by context, type, origin
- Support relevance-based queries
- Track lineage and contradictions
- Maintain claim metadata
- Prevent raw state storage

### Interface

```typescript
interface FederatedClaimRegistry {
  // Register a new claim
  registerClaim(artifact: EpistemicArtifact): Promise<ClaimRecord>;

  // Query claims with context filters
  queryClaims(query: ClaimQuery): Promise<ClaimRecord[]>;

  // Retrieve specific claim by ID
  getClaim(claimId: string): Promise<ClaimRecord | null>;

  // Find claims by relevance to local context
  findRelevantClaims(localContext: LocalContext): Promise<ClaimRecord[]>;

  // Register a contradiction
  registerContradiction(contradiction: ContradictionRecord): Promise<void>;

  // Get contradictions for a claim
  getContradictions(claimId: string): Promise<ContradictionRecord[]>;
}
```

### Query Interface

```typescript
interface ClaimQuery {
  artifactType?: ArtifactType;
  originNode?: string;
  domain?: string;
  missionType?: string;
  agentTopology?: string;
  minConfidence?: number;
  allowedUse?: AllowedUse;
  timeRange?: { start: number; end: number };
  limit?: number;
}
```

### Storage Schema

```sql
CREATE TABLE epistemic_claims (
  claim_id TEXT PRIMARY KEY,
  artifact_type TEXT NOT NULL,
  origin_node TEXT NOT NULL,
  origin_layer INTEGER NOT NULL,
  created_at INTEGER NOT NULL,
  version TEXT NOT NULL,

  -- Claim content
  claim TEXT NOT NULL,
  summary TEXT NOT NULL,

  -- Context (JSON)
  context_json TEXT NOT NULL,

  -- Evidence (JSON)
  evidence_json TEXT NOT NULL,

  -- Limitations (JSON array)
  limitations_json TEXT,

  -- Allowed uses (JSON array)
  allowed_uses_json TEXT NOT NULL,

  -- Provenance (JSON)
  provenance_json TEXT NOT NULL,

  -- Indexes
  INDEX idx_artifact_type (artifact_type),
  INDEX idx_origin_node (origin_node),
  INDEX idx_domain (context_json),
  INDEX idx_created_at (created_at)
);
```

### Implementation Notes

- **No ranking by "best"**: Store claims, not scores
- **Plurality preservation**: Store contradictions, don't resolve them
- **Query by local relevance**: Support context-aware retrieval
- **Immutable records**: Claims are never modified, only superseded

### Service Location

```
src/services/layer12/FederatedClaimRegistry.ts
src/db/schema/epistemic_claims.sql
```

---

## 3.3 LocalQualificationEngine

### Purpose

Each receiving node runs this locally to evaluate incoming claims before adoption.

### Responsibilities

- Check transferability to local context
- Compare local vs. origin context
- Assess policy compatibility
- Compute local relevance score
- Compute local trust score
- Recommend informational/advisory/allocative classification
- Detect context clashes

### Interface

```typescript
interface LocalQualificationEngine {
  // Qualify an artifact for local adoption
  qualifyArtifact(
    artifact: EpistemicArtifact,
    localContext: LocalContext
  ): Promise<QualificationResult>;

  // Check transferability
  checkTransferability(
    artifact: EpistemicArtifact,
    localContext: LocalContext
  ): Promise<TransferabilityCheck>;

  // Compare contexts
  compareContexts(
    artifactContext: ArtifactContext,
    localContext: LocalContext
  ): Promise<ContextComparison>;

  // Assess policy compatibility
  checkPolicyCompatibility(
    artifact: EpistemicArtifact,
    localPolicies: Policy[]
  ): Promise<PolicyCompatibility>;

  // Compute local relevance
  computeRelevance(
    artifact: EpistemicArtifact,
    localContext: LocalContext
  ): Promise<number>;

  // Compute local trust
  computeTrust(
    artifact: EpistemicArtifact,
    localContext: LocalContext
  ): Promise<number>;
}
```

### Qualification Result

```typescript
interface QualificationResult {
  artifactId: string;

  // Classification
  category: 'informational' | 'advisory' | 'simulation_only' | 'allocative_eligible';

  // Scores (0-1)
  localRelevance: number;
  provenanceStrength: number;
  confidenceStability: number;
  overallTrust: number;

  // Flags
  hasContextClash: boolean;
  hasContradictions: boolean;
  requiresSimulation: boolean;
  policyCompatible: boolean;

  // Context comparison
  contextComparison: {
    domainMatch: boolean;
    missionTypeMatch: boolean;
    agentTopologyMatch: boolean;
    environmentMatch: boolean;
  };

  // Recommendations
  recommendedUses: AllowedUse[];
  warnings: string[];
  adaptations?: string[];

  // Decision guidance
  suggestedAction: 'ignore' | 'store_informational' | 'use_advisory' | 'send_to_simulation' | 'send_to_governance';
}
```

### Decision Matrix

| Local Trust | Local Relevance | Contradictions? | Decision |
|-------------|-----------------|-----------------|----------|
| Low | Low | Any | Ignore |
| Low | High | None | Store as informational |
| Medium | High | None | Advisory use |
| High | High | None | Simulation test |
| Any | Any | Yes | Governance review |
| High | Any | Unresolved | Mark as conflicted |

### Implementation Notes

- **Always run locally**: Never defer qualification to network
- **Context is primary**: Mismatched context = low relevance regardless of confidence
- **Contradictions matter**: Any unresolved contradiction requires governance review
- **Authority is local**: This is where adoption decision happens, not at publication

### Service Location

```
src/services/layer12/LocalQualificationEngine.ts
```

---

## 3.4 ContradictionAndPluralityManager

### Purpose

Tracks when different nodes report conflicting patterns. Preserves disagreement instead of collapsing it.

### Responsibilities

- Detect contradictions between claims
- Store contradiction records
- Link contradictory claims
- Preserve plurality of explanations
- Flag contradictions for resolution
- Support contradiction queries

### Interface

```typescript
interface ContradictionAndPluralityManager {
  // Register a contradiction
  registerContradiction(
    claimA: EpistemicArtifact,
    claimB: EpistemicArtifact,
    contradictionType: ContradictionType
  ): Promise<ContradictionRecord>;

  // Detect contradictions automatically
  detectContradictions(claim: EpistemicArtifact): Promise<ContradictionDetection>;

  // Get all contradictions for a claim
  getContradictions(claimId: string): Promise<ContradictionRecord[]>;

  // Get unresolved contradictions
  getUnresolvedContradictions(): Promise<ContradictionRecord[]>;

  // Mark contradiction as resolved
  resolveContradiction(
    contradictionId: string,
    resolution: ContradictionResolution
  ): Promise<void>;

  // Get plurality view for a topic
  getPluralityView(topic: string): Promise<PluralityView>;
}
```

### Contradiction Types

```typescript
type ContradictionType =
  | "direct_contradiction"     // Claims directly oppose each other
  | "context_conflict"         // Claims valid in different contexts
  | "causal_disagreement"      // Different causal explanations
  | "recommendation_conflict";  // Conflicting recommendations
```

### Plurality View

```typescript
interface PluralityView {
  topic: string;
  competingClaims: Array<{
    claimId: string;
    claim: string;
    originNode: string;
    confidence: number;
    context: ArtifactContext;
    supportingEvidence: number;
  }>;
  contradictionCount: number;
  hasResolution: boolean;
  suggestedAction: 'preserve_plurality' | 'simulation_test' | 'governance_review';
}
```

### Storage Schema

```sql
CREATE TABLE claim_contradictions (
  contradiction_id TEXT PRIMARY KEY,
  claim_a_id TEXT NOT NULL,
  claim_b_id TEXT NOT NULL,
  contradiction_type TEXT NOT NULL,
  detected_at INTEGER NOT NULL,
  resolved BOOLEAN DEFAULT FALSE,
  resolution_type TEXT,
  resolution_notes TEXT,

  FOREIGN KEY (claim_a_id) REFERENCES epistemic_claims(claim_id),
  FOREIGN KEY (claim_b_id) REFERENCES epistemic_claims(claim_id),

  INDEX idx_resolved (resolved),
  INDEX idx_claim_a (claim_a_id),
  INDEX idx_claim_b (claim_b_id)
);
```

### Implementation Notes

- **Never auto-resolve**: Preserve contradictions until explicit resolution
- **Context is key**: Many "contradictions" are context-dependent
- **Simulation priority**: Contradictions should trigger simulation testing
- **Plurality is healthy**: Multiple competing explanations are desired state

### Service Location

```
src/services/layer12/ContradictionAndPluralityManager.ts
src/db/schema/claim_contradictions.sql
```

---

## 3.5 EpistemicAuditService

### Purpose

Tracks the knowledge network: what was shared, what was adopted, what was rejected, and why.

### Responsibilities

- Log all artifact publications
- Log all qualification results
- Log all adoption decisions
- Log all rejections with reasons
- Track simulation confirmations
- Track governance reviews
- Support audit queries

### Interface

```typescript
interface EpistemicAuditService {
  // Log artifact publication
  logPublication(event: PublicationEvent): Promise<void>;

  // Log qualification result
  logQualification(event: QualificationEvent): Promise<void>;

  // Log adoption decision
  logAdoption(event: AdoptionEvent): Promise<void>;

  // Log rejection with reason
  logRejection(event: RejectionEvent): Promise<void>;

  // Log simulation test
  logSimulationTest(event: SimulationTestEvent): Promise<void>;

  // Log governance review
  logGovernanceReview(event: GovernanceReviewEvent): Promise<void>;

  // Query audit trail
  queryAudit(query: AuditQuery): Promise<AuditRecord[]>;

  // Get adoption statistics
  getAdoptionStats(timeRange: TimeRange): Promise<AdoptionStats>;
}
```

### Audit Event Types

```typescript
interface PublicationEvent {
  eventId: string;
  artifactId: string;
  originNode: string;
  publishedAt: number;
  artifactType: ArtifactType;
  allowedUses: AllowedUse[];
}

interface QualificationEvent {
  eventId: string;
  artifactId: string;
  receivingNode: string;
  qualifiedAt: number;
  category: string;
  localRelevance: number;
  localTrust: number;
  suggestedAction: string;
}

interface AdoptionEvent {
  eventId: string;
  artifactId: string;
  adoptingNode: string;
  adoptedAt: number;
  adoptionType: 'informational' | 'advisory' | 'simulation_tested';
  adaptations?: string[];
}

interface RejectionEvent {
  eventId: string;
  artifactId: string;
  rejectingNode: string;
  rejectedAt: number;
  reason: string;
  details?: string;
}
```

### Storage Schema

```sql
CREATE TABLE epistemic_audit_log (
  event_id TEXT PRIMARY KEY,
  event_type TEXT NOT NULL,
  artifact_id TEXT NOT NULL,
  node_id TEXT NOT NULL,
  timestamp INTEGER NOT NULL,

  -- Event-specific data (JSON)
  event_data_json TEXT NOT NULL,

  -- For adoption tracking
  adoption_outcome TEXT,
  rejection_reason TEXT,

  INDEX idx_artifact_id (artifact_id),
  INDEX idx_event_type (event_type),
  INDEX idx_timestamp (timestamp),
  INDEX idx_node_id (node_id)
);
```

### Implementation Notes

- **Every exchange is logged**: No silent failures or hidden adoptions
- **Reasons matter**: Rejections must include why
- **Simulation confirmation**: Track whether simulation confirmed or contradicted
- **Self-correcting**: Audit data should inform future qualification

### Service Location

```
src/services/layer12/EpistemicAuditService.ts
src/db/schema/epistemic_audit_log.sql
```

---

# 4. Data Models & Schemas

## 4.1 Core Type Definitions

```typescript
// src/types/layer12/epistemic.ts

/**
 * The canonical epistemic artifact structure
 */
export interface EpistemicArtifact {
  // Identity
  artifactId: string;
  artifactType: ArtifactType;
  originNode: string;
  originLayer: number;
  createdAt: number;
  version: string;

  // The Claim
  claim: string;
  summary: string;

  // Context
  context: ArtifactContext;

  // Evidence
  evidence: EvidenceEnvelope;

  // Limitations
  limitations: string[];
  contradictions?: string[];  // refs to conflicting claims

  // Usage Scope
  allowedUses: AllowedUse[];

  // Provenance
  provenance: ClaimProvenance;
}

/**
 * Artifact types
 */
export type ArtifactType =
  | "observation"        // "We observed X in environment Y"
  | "pattern_claim"      // "Pattern P appears across N missions"
  | "causal_claim"       // "Change C caused effect E"
  | "policy_claim"       // "Policy rule R improved outcome O"
  | "recommendation";    // "We suggest approach A for problem P"

/**
 * Context metadata
 */
export interface ArtifactContext {
  domain?: string;
  missionType?: string;
  agentTopology?: string;
  policyRegime?: string;
  environmentClass?: string;
  constraints?: string[];
  regulatoryEnvironment?: string;
  modelFamily?: string;
  workloadClass?: string;
}

/**
 * Evidence envelope
 */
export interface EvidenceEnvelope {
  sampleSize?: number;
  confidence: number;           // 0-1
  effectSize?: number;          // statistical significance
  validationMethod?: string;
  stabilityScore?: number;      // how consistent over time
  reproducibility?: number;     // can this be replicated
  supportingArtifacts?: string[];
  timeSpan?: { start: number; end: number };
}

/**
 * Allowed use classes
 */
export type AllowedUse =
  | "informational"        // Awareness only, dashboards, planning
  | "advisory"            // Can inform decisions, no direct action
  | "simulation_only"      // Can be used in simulations only
  | "allocative_eligible"; // May influence economic optimization (requires mediation)

/**
 * Provenance tracking
 */
export interface ClaimProvenance {
  sourceArtifacts: string[];
  sourceInsights: string[];
  lineageDepth: number;
  createdBy: string;
  creationPath: string[];
}

/**
 * Qualification result
 */
export interface QualificationResult {
  artifactId: string;
  category: 'informational' | 'advisory' | 'simulation_only' | 'allocative_eligible';
  localRelevance: number;
  provenanceStrength: number;
  confidenceStability: number;
  overallTrust: number;
  hasContextClash: boolean;
  hasContradictions: boolean;
  requiresSimulation: boolean;
  policyCompatible: boolean;
  contextComparison: ContextComparison;
  recommendedUses: AllowedUse[];
  warnings: string[];
  adaptations?: string[];
  suggestedAction: SuggestedAction;
}

export type SuggestedAction =
  | "ignore"
  | "store_informational"
  | "use_advisory"
  | "send_to_simulation"
  | "send_to_governance";

/**
 * Context comparison
 */
export interface ContextComparison {
  domainMatch: boolean;
  missionTypeMatch: boolean;
  agentTopologyMatch: boolean;
  environmentMatch: boolean;
  overallMatch: number;
}

/**
 * Contradiction record
 */
export interface ContradictionRecord {
  contradictionId: string;
  claimAId: string;
  claimBId: string;
  contradictionType: ContradictionType;
  detectedAt: number;
  resolved: boolean;
  resolutionType?: ResolutionType;
  resolutionNotes?: string;
}

export type ContradictionType =
  | "direct_contradiction"
  | "context_conflict"
  | "causal_disagreement"
  | "recommendation_conflict";

export type ResolutionType =
  | "context_dependent"
  | "simulation_resolved"
  | "governance_resolved"
  | "both_valid"
  | "superseded";

/**
 * Transferability check
 */
export interface TransferabilityCheck {
  canMoveAcrossNodes: boolean;
  requiresContext: string[];
  localAdaptationRequired: boolean;
  riskLevel: 'low' | 'medium' | 'high';
  reasons: string[];
}

/**
 * Policy compatibility
 */
export interface PolicyCompatibility {
  compatibleWith: string[];  // Policy IDs
  conflictsWith: string[];    // Policy IDs
  requiresApproval: boolean;
  authorityLevel: 'node' | 'region' | 'network';
}
```

---

# 5. API Contracts

## 5.1 Claim Publication API

### POST /api/l12/claims/publish

Publish an insight as a federatable epistemic artifact.

**Request:**

```typescript
interface PublishClaimRequest {
  insightId: string;
  options: {
    allowedUses: AllowedUse[];
    transferabilityHint?: 'low' | 'medium' | 'high';
    limitations?: string[];
    contradictions?: string[];
  };
}
```

**Response:**

```typescript
interface PublishClaimResponse {
  artifactId: string;
  status: 'published' | 'redacted' | 'rejected';
  redactions?: string[];
  warnings?: string[];
  publishedAt: number;
}
```

**Errors:**

- `400` — Invalid insight or options
- `403` — Insight not marked federatable
- `422` — Fails validation (missing provenance, context, etc.)

---

## 5.2 Claim Query API

### GET /api/l12/claims/query

Query claims with context filters.

**Query Parameters:**

```
?artifactType=pattern_claim
&domain=financial_planning
&minConfidence=0.7
&allowedUse=advisory
&limit=20
```

**Response:**

```typescript
interface ClaimQueryResponse {
  claims: Array<{
    artifactId: string;
    artifactType: ArtifactType;
    originNode: string;
    claim: string;
    summary: string;
    confidence: number;
    context: ArtifactContext;
    allowedUses: AllowedUse[];
    createdAt: number;
  }>;
  total: number;
  returned: number;
}
```

---

## 5.3 Local Qualification API

### POST /api/l12/claims/qualify

Qualify an artifact for local adoption.

**Request:**

```typescript
interface QualifyRequest {
  artifactId: string;
  localContext: {
    domain: string;
    missionType?: string;
    agentTopology?: string;
    policyRegime?: string;
    environmentClass?: string;
  };
  localPolicies?: string[];  // Policy IDs in effect
}
```

**Response:**

```typescript
interface QualifyResponse extends QualificationResult {
  artifact: {
    artifactId: string;
    claim: string;
    summary: string;
    originNode: string;
  };
  qualifiedAt: number;
}
```

---

## 5.4 Contradiction API

### GET /api/l12/contradictions

Get contradictions for a claim or all unresolved contradictions.

**Query Parameters:**

```
?claimId={artifactId}
  or
?unresolved=true
```

**Response:**

```typescript
interface ContradictionsResponse {
  contradictions: Array<{
    contradictionId: string;
    claimAId: string;
    claimBId: string;
    claimA: string;
    claimB: string;
    contradictionType: ContradictionType;
    detectedAt: number;
    resolved: boolean;
  }>;
}
```

### POST /api/l12/contradictions/resolve

Mark a contradiction as resolved.

**Request:**

```typescript
interface ResolveContradictionRequest {
  contradictionId: string;
  resolutionType: ResolutionType;
  resolutionNotes: string;
}
```

---

## 5.5 Audit API

### GET /api/l12/audit/query

Query the epistemic audit log.

**Query Parameters:**

```
?artifactId={artifactId}
&eventType=qualification
&startDate={timestamp}
&endDate={timestamp}
```

**Response:**

```typescript
interface AuditQueryResponse {
  events: Array<{
    eventId: string;
    eventType: string;
    artifactId: string;
    nodeId: string;
    timestamp: number;
    eventData: Record<string, unknown>;
  }>;
}
```

### GET /api/l12/audit/statistics

Get adoption statistics.

**Query Parameters:**

```
?startDate={timestamp}
&endDate={timestamp}
```

**Response:**

```typescript
interface AdoptionStatistics {
  totalReceived: number;
  totalAdopted: number;
  totalRejected: number;
  adoptionRate: number;
  byCategory: {
    informational: number;
    advisory: number;
    simulationOnly: number;
    allocativeEligible: number;
  };
  byRejectionReason: Record<string, number>;
}
```

---

# 6. Database Schema

## 6.1 Complete Schema File

**File:** `src/db/schema/layer12.sql`

```sql
-- ============================================================================
-- Layer 12: Collective Intelligence Exchange
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Epistemic Claims Registry
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS epistemic_claims (
  -- Identity
  claim_id TEXT PRIMARY KEY,
  artifact_type TEXT NOT NULL CHECK (artifact_type IN (
    'observation', 'pattern_claim', 'causal_claim', 'policy_claim', 'recommendation'
  )),
  origin_node TEXT NOT NULL,
  origin_layer INTEGER NOT NULL,
  created_at INTEGER NOT NULL,
  version TEXT NOT NULL,

  -- The Claim
  claim TEXT NOT NULL,
  summary TEXT NOT NULL,

  -- Context (JSON)
  context_json TEXT NOT NULL,

  -- Evidence (JSON)
  evidence_json TEXT NOT NULL,

  -- Limitations (JSON array)
  limitations_json TEXT,

  -- Allowed uses (JSON array)
  allowed_uses_json TEXT NOT NULL,

  -- Provenance (JSON)
  provenance_json TEXT NOT NULL,

  -- Metadata
  received_at INTEGER,
  indexed_at INTEGER,

  -- Indexes
  INDEX idx_artifact_type (artifact_type),
  INDEX idx_origin_node (origin_node),
  INDEX idx_created_at (created_at),
  INDEX idx_received_at (received_at)
);

-- ----------------------------------------------------------------------------
-- Claim Contradictions
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS claim_contradictions (
  contradiction_id TEXT PRIMARY KEY,
  claim_a_id TEXT NOT NULL,
  claim_b_id TEXT NOT NULL,
  contradiction_type TEXT NOT NULL CHECK (contradiction_type IN (
    'direct_contradiction', 'context_conflict', 'causal_disagreement', 'recommendation_conflict'
  )),
  detected_at INTEGER NOT NULL,
  detected_by TEXT NOT NULL,
  resolved BOOLEAN DEFAULT FALSE,
  resolution_type TEXT,
  resolution_notes TEXT,
  resolved_at INTEGER,
  resolved_by TEXT,

  FOREIGN KEY (claim_a_id) REFERENCES epistemic_claims(claim_id),
  FOREIGN KEY (claim_b_id) REFERENCES epistemic_claims(claim_id),

  INDEX idx_resolved (resolved),
  INDEX idx_claim_a (claim_a_id),
  INDEX idx_claim_b (claim_b_id),
  INDEX idx_detected_at (detected_at)
);

-- ----------------------------------------------------------------------------
-- Local Qualification Results (per-node)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS local_qualifications (
  qualification_id TEXT PRIMARY KEY,
  artifact_id TEXT NOT NULL,
  qualifying_node TEXT NOT NULL,
  qualified_at INTEGER NOT NULL,

  -- Classification
  category TEXT NOT NULL CHECK (category IN (
    'informational', 'advisory', 'simulation_only', 'allocative_eligible'
  )),

  -- Scores
  local_relevance REAL NOT NULL CHECK (local_relevance BETWEEN 0 AND 1),
  provenance_strength REAL NOT NULL CHECK (provenance_strength BETWEEN 0 AND 1),
  confidence_stability REAL NOT NULL CHECK (confidence_stability BETWEEN 0 AND 1),
  overall_trust REAL NOT NULL CHECK (overall_trust BETWEEN 0 AND 1),

  -- Flags
  has_context_clash BOOLEAN NOT NULL,
  has_contradictions BOOLEAN NOT NULL,
  requires_simulation BOOLEAN NOT NULL,
  policy_compatible BOOLEAN NOT NULL,

  -- Context comparison (JSON)
  context_comparison_json TEXT,

  -- Recommendations
  recommended_uses_json TEXT NOT NULL,
  warnings_json TEXT,
  adaptations_json TEXT,

  -- Decision
  suggested_action TEXT NOT NULL CHECK (suggested_action IN (
    'ignore', 'store_informational', 'use_advisory', 'send_to_simulation', 'send_to_governance'
  )),

  FOREIGN KEY (artifact_id) REFERENCES epistemic_claims(claim_id),

  INDEX idx_artifact_id (artifact_id),
  INDEX idx_qualifying_node (qualifying_node),
  INDEX idx_qualified_at (qualified_at),
  INDEX idx_category (category)
);

-- ----------------------------------------------------------------------------
-- Epistemic Audit Log
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS epistemic_audit_log (
  event_id TEXT PRIMARY KEY,
  event_type TEXT NOT NULL CHECK (event_type IN (
    'publication', 'qualification', 'adoption', 'rejection', 'simulation_test', 'governance_review'
  )),
  artifact_id TEXT NOT NULL,
  node_id TEXT NOT NULL,
  timestamp INTEGER NOT NULL,

  -- Event-specific data (JSON)
  event_data_json TEXT NOT NULL,

  -- For quick querying
  adoption_outcome TEXT,
  rejection_reason TEXT,
  governance_decision TEXT,

  FOREIGN KEY (artifact_id) REFERENCES epistemic_claims(claim_id),

  INDEX idx_artifact_id (artifact_id),
  INDEX idx_event_type (event_type),
  INDEX idx_timestamp (timestamp),
  INDEX idx_node_id (node_id),
  INDEX idx_adoption_outcome (adoption_outcome)
);

-- ----------------------------------------------------------------------------
-- Local Adoption Decisions (per-node)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS local_adoptions (
  adoption_id TEXT PRIMARY KEY,
  artifact_id TEXT NOT NULL,
  adopting_node TEXT NOT NULL,
  adopted_at INTEGER NOT NULL,

  -- Adoption type
  adoption_type TEXT NOT NULL CHECK (adoption_type IN (
    'informational', 'advisory', 'simulation_tested', 'allocative_eligible'
  )),

  -- Tracking
  usage_count INTEGER DEFAULT 0,
  last_used_at INTEGER,
  effectiveness_score REAL,

  -- Adaptations made
  adaptations_json TEXT,

  -- Superseded by
  superseded_by TEXT,
  superseded_at INTEGER,

  FOREIGN KEY (artifact_id) REFERENCES epistemic_claims(claim_id),

  INDEX idx_artifact_id (artifact_id),
  INDEX idx_adopting_node (adopting_node),
  INDEX idx_adopted_at (adopted_at),
  INDEX idx_adoption_type (adoption_type)
);
```

---

# 7. Integration Points

## 7.1 Layer 11 → Layer 12

Layer 11 provides the distributed fabric that Layer 12 uses for cross-node communication.

**Integration:**

```typescript
// src/services/layer12/FederatedClaimPublisher.ts

import { DistributedFabricClient } from '../layer11/DistributedFabricClient';

class FederatedClaimPublisher {
  constructor(
    private fabric: DistributedFabricClient,
    private registry: FederatedClaimRegistry,
    private audit: EpistemicAuditService
  ) {}

  async publishToNetwork(artifact: EpistemicArtifact): Promise<void> {
    // Use L11 fabric for cross-node communication
    await this.fabric.publish('claims', artifact.artifactId, artifact);

    // Log publication
    await this.audit.logPublication({
      eventId: uuid(),
      artifactId: artifact.artifactId,
      originNode: artifact.originNode,
      publishedAt: Date.now(),
      artifactType: artifact.artifactType,
      allowedUses: artifact.allowedUses
    });
  }

  async retrieveFromNetwork(artifactId: string): Promise<EpistemicArtifact | null> {
    return await this.fabric.retrieve<EpistemicArtifact>('claims', artifactId);
  }
}
```

## 7.2 Layer 12 → Layer 13 (Preparation)

Layer 12 produces qualified artifacts that Layer 13 may consume (only if marked `allocative_eligible`).

**Integration Contract:**

```typescript
// src/services/layer13/AllocativeEligibilityFilter.ts

import { QualificationResult } from '../layer12/types';

class AllocativeEligibilityFilter {
  canConsume(qualification: QualificationResult): boolean {
    return (
      qualification.category === 'allocative_eligible' &&
      qualification.policyCompatible &&
      !qualification.hasContextClash &&
      qualification.overallTrust >= 0.8
    );
  }
}
```

**Critical Constraint**: Layer 13 MUST NOT consume raw epistemic artifacts directly. Only qualification results that pass the filter may influence economic decisions.

## 7.3 Layer 4 Integration

Layer 12 consumes published insights from Layer 4.

```typescript
// src/services/layer12/EpistemicArtifactPublisher.ts

import { PublishedInsight, Pattern } from '../layer4/types';

class EpistemicArtifactPublisher {
  async fromInsight(insight: PublishedInsight): Promise<EpistemicArtifact> {
    return {
      artifactId: `artifact_${insight.insightId}`,
      artifactType: this.mapInsightTypeToArtifactType(insight.type),
      originNode: this.localNodeId,
      originLayer: 4,
      createdAt: insight.publishedAt,
      version: '1.0.0',
      claim: insight.summary,
      summary: insight.description,
      context: this.extractContext(insight),
      evidence: this.extractEvidence(insight),
      limitations: insight.limitations || [],
      allowedUses: insight.federatable ? ['informational', 'advisory'] : [],
      provenance: {
        sourceArtifacts: insight.sourceArtifacts || [],
        sourceInsights: [insight.insightId],
        lineageDepth: 1,
        createdBy: insight.createdBy,
        creationPath: [`insight_${insight.insightId}`]
      }
    };
  }
}
```

---

# 8. UI/UX Requirements

## 8.1 Collective Intelligence Dashboard

**Route:** `/operator/collective-intelligence`

**Purpose:** Operator visibility into shared epistemic claims

**Components:**

| Component | Description |
|-----------|-------------|
| **Shared Claims Feed** | Live feed of incoming claims from federation |
| **Local Qualification Queue** | Claims pending local qualification |
| **Contradiction Panel** | Active contradictions and plurality views |
| **Adoption Status** | What this node has adopted and how it's being used |
| **Audit Trail** | Exchange and adoption history |

### Shared Claims Feed

**Columns:**

- Claim ID
- Origin Node
- Artifact Type
- Claim (summary)
- Confidence
- Context
- Allowed Uses
- Local Relevance (after qualification)
- Actions (Qualify, Ignore, Request Simulation)

**Filters:**

- Artifact Type
- Origin Node
- Domain
- Min Confidence
- Allowed Use

### Local Qualification Queue

Shows artifacts awaiting local qualification decisions.

**Display:**

```typescript
interface QualificationQueueItem {
  artifactId: string;
  claim: string;
  originNode: string;
  confidence: number;
  context: ArtifactContext;
  autoQualification?: QualificationResult;
  status: 'pending' | 'auto_qualified' | 'manual_review';
}
```

**Actions:**

- Approve (with category selection)
- Reject (with reason)
- Send to Simulation
- Request Governance Review

### Contradiction Panel

Shows active contradictions between claims.

**Display:**

```typescript
interface ContradictionPanelItem {
  contradictionId: string;
  claimA: string;
  claimB: string;
  type: ContradictionType;
  detectedAt: number;
  resolved: boolean;
  action: 'view_plurality' | 'send_to_simulation' | 'send_to_governance';
}
```

### Adoption Status

Shows what this node has adopted from the federation.

**Display:**

```typescript
interface AdoptionStatusItem {
  artifactId: string;
  claim: string;
  originNode: string;
  adoptionType: 'informational' | 'advisory' | 'simulation_tested';
  adoptedAt: number;
  usageCount: number;
  lastUsed: number;
  effectivenessScore?: number;
}
```

---

## 8.2 Qualification Detail View

**Route:** `/operator/collective-intelligence/qualify/:artifactId`

**Purpose:** Detailed view for manual qualification of an artifact

**Sections:**

1. **Artifact Overview**
   - Claim, summary, origin
   - Artifact type, confidence
   - Created at, version

2. **Context Comparison**
   - Origin context vs local context
   - Match/mismatch indicators
   - Context clash warnings

3. **Evidence Assessment**
   - Sample size, confidence interval
   - Validation method
   - Stability score

4. **Auto-Qualification Result**
   - Pre-computed qualification result
   - Category recommendation
   - Relevance/trust scores
   - Warnings

5. **Manual Override**
   - Override category selection
   - Add adaptations
   - Add warnings
   - Approve/reject with reason

---

## 8.3 Contradiction Detail View

**Route:** `/operator/collective-intelligence/contradictions/:contradictionId`

**Purpose:** View and manage contradictions

**Sections:**

1. **Contradicted Claims**
   - Side-by-side view of Claim A and Claim B
   - Highlight differences
   - Show context differences

2. **Contradiction Analysis**
   - Type of contradiction
   - Detected at
   - Resolution status

3. **Plurality View**
   - Other related claims on the same topic
   - Context breakdown
   - Evidence comparison

4. **Resolution Actions**
   - Mark as context-dependent
   - Send to simulation testing
   - Send to governance review
   - Mark both valid (context-dependent)

---

# 9. Testing Strategy

## 9.1 Unit Tests

### EpistemicArtifactPublisher

```typescript
describe('EpistemicArtifactPublisher', () => {
  test('should convert insight to artifact with proper structure', async () => {
    const insight = createTestInsight();
    const artifact = await publisher.fromInsight(insight);

    expect(artifact.artifactType).toBe('pattern_claim');
    expect(artifact.originNode).toBeDefined();
    expect(artifact.context).toBeDefined();
    expect(artifact.evidence.confidence).toBeGreaterThanOrEqual(0);
    expect(artifact.allowedUses).toContain('informational');
  });

  test('should redact local references before federation', async () => {
    const artifact = createTestArtifact({
      claim: 'Node torq-east uses pattern X',
      context: { localPath: '/var/torq/east' }
    });

    const redacted = await publisher.redactForFederation(artifact);

    expect(redacted.claim).not.toContain('torq-east');
    expect(redacted.context?.localPath).toBeUndefined();
  });

  test('should reject publication without required metadata', async () => {
    const invalidArtifact = createTestArtifact({
      context: undefined,
      evidence: undefined
    });

    const result = await publisher.validateForPublication(invalidArtifact);

    expect(result.valid).toBe(false);
    expect(result.errors).toContain('missing_context');
    expect(result.errors).toContain('missing_evidence');
  });
});
```

### LocalQualificationEngine

```typescript
describe('LocalQualificationEngine', () => {
  test('should reject artifact with context mismatch', async () => {
    const artifact = createTestArtifact({
      context: { domain: 'healthcare', missionType: 'compliance' }
    });

    const localContext = {
      domain: 'financial_planning',
      missionType: 'analysis'
    };

    const result = await qualifier.qualifyArtifact(artifact, localContext);

    expect(result.hasContextClash).toBe(true);
    expect(result.localRelevance).toBeLessThan(0.5);
    expect(result.suggestedAction).toBe('ignore');
  });

  test('should recommend governance review for contradictions', async () => {
    const artifact = createTestArtifact({
      contradictions: ['claim_xyz']
    });

    const result = await qualifier.qualifyArtifact(artifact, localContext);

    expect(result.hasContradictions).toBe(true);
    expect(result.suggestedAction).toBe('send_to_governance');
  });

  test('should allow high-trust, high-relevance artifact', async () => {
    const artifact = createTestArtifact({
      evidence: { confidence: 0.9, sampleSize: 100 },
      context: { domain: 'financial_planning' }
    });

    const localContext = { domain: 'financial_planning' };

    const result = await qualifier.qualifyArtifact(artifact, localContext);

    expect(result.localRelevance).toBeGreaterThan(0.8);
    expect(result.overallTrust).toBeGreaterThan(0.8);
    expect(result.suggestedAction).toBeOneOf([
      'use_advisory',
      'send_to_simulation'
    ]);
  });
});
```

### ContradictionAndPluralityManager

```typescript
describe('ContradictionAndPluralityManager', () => {
  test('should detect direct contradictions', async () => {
    const claimA = createTestArtifact({
      claim: 'Pattern X improves throughput',
      artifactType: 'pattern_claim'
    });

    const claimB = createTestArtifact({
      claim: 'Pattern X degrades quality',
      artifactType: 'pattern_claim'
    });

    const detection = await manager.detectContradictions(claimA, [claimB]);

    expect(detection.contradictions).toHaveLength(1);
    expect(detection.contradictions[0].type).toBe('direct_contradiction');
  });

  test('should preserve plurality rather than resolve', async () => {
    const contradiction = await manager.registerContradiction(claimA, claimB, 'direct_contradiction');

    const view = await manager.getPluralityView('pattern_x');

    expect(view.competingClaims).toHaveLength(2);
    expect(view.suggestedAction).not.toBe('resolve_automatically');
  });
});
```

## 9.2 Integration Tests

### End-to-End Publication Flow

```typescript
describe('L12 Integration: Publication Flow', () => {
  test('should publish insight as artifact and make available to other nodes', async () => {
    // 1. Publish insight locally
    const insight = await createAndPublishInsight();

    // 2. Convert to epistemic artifact
    const artifact = await publisher.fromInsight(insight);

    // 3. Publish to federation
    await federatedPublisher.publishToNetwork(artifact);

    // 4. Retrieve from another node
    const retrieved = await federatedPublisher.retrieveFromNetwork(artifact.artifactId);

    expect(retrieved).toBeDefined();
    expect(retrieved?.artifactId).toBe(artifact.artifactId);
    expect(retrieved?.claim).toBe(artifact.claim);
  });
});
```

### End-to-End Qualification Flow

```typescript
describe('L12 Integration: Qualification Flow', () => {
  test('should qualify incoming artifact and make adoption decision', async () => {
    // 1. Receive artifact from network
    const artifact = await receiveArtifactFromNetwork();

    // 2. Run local qualification
    const qualification = await qualifier.qualifyArtifact(artifact, localContext);

    // 3. Make adoption decision
    if (qualification.suggestedAction === 'use_advisory') {
      await adoptionService.adopt(artifact.artifactId, 'advisory', qualification);
    }

    // 4. Verify adoption recorded
    const adoption = await adoptionService.getAdoption(artifact.artifactId);
    expect(adoption?.adoptionType).toBe('advisory');

    // 5. Verify audit log
    const auditEvents = await audit.queryAudit({ artifactId: artifact.artifactId });
    expect(auditEvents).toContainEqual(
      expect.objectContaining({ eventType: 'adoption' })
    );
  });
});
```

### Contradiction Handling Flow

```typescript
describe('L12 Integration: Contradiction Handling', () => {
  test('should detect contradiction and preserve plurality', async () => {
    // 1. Publish two contradictory claims
    const claimA = await publishClaim('Pattern X improves throughput');
    const claimB = await publishClaim('Pattern X degrades quality');

    // 2. Detect contradiction
    const contradiction = await manager.registerContradiction(claimA, claimB, 'direct_contradiction');

    // 3. Verify both claims still exist
    const retrievedA = await registry.getClaim(claimA.artifactId);
    const retrievedB = await registry.getClaim(claimB.artifactId);

    expect(retrievedA).toBeDefined();
    expect(retrievedB).toBeDefined();

    // 4. Verify contradiction record exists
    const contradictions = await manager.getContradictions(claimA.artifactId);
    expect(contradictions).toContainEqual(
      expect.objectContaining({ claimBId: claimB.artifactId })
    );
  });
});
```

## 9.3 Anti-Pattern Tests

Ensure the system does NOT create hidden authority:

```typescript
describe('L12 Anti-Pattern Tests', () => {
  test('should not allow shared artifact to become directly authoritative', async () => {
    const artifact = await receiveArtifactFromNetwork();

    // Artifact should NOT be directly usable
    expect(() => {
      // This should fail - artifacts must be qualified first
      agent.useArtifactDirectly(artifact);
    }).toThrow();
  });

  test('should not allow ranking by universal "best" score', async () => {
    const claims = await queryClaims({});

    // Results should be ranked by local relevance, not universal score
    expect(claims[0]).toHaveProperty('localRelevance');
    expect(claims[0]).not.toHaveProperty('universalBestScore');
  });

  test('should not collapse contradictions into single winner', async () => {
    const contradictory = await queryClaims({ topic: 'pattern_x' });

    // Should return multiple competing claims, not one "best" claim
    expect(contradictory.length).toBeGreaterThan(1);
  });

  test('should not allow allocative use without qualification', async () => {
    const artifact = await receiveArtifactFromNetwork();

    // Attempt to use for routing without qualification
    const canRoute = await economicRouter.canUseForRouting(artifact);

    expect(canRoute).toBe(false);
  });
});
```

## 9.4 E2E Test Scenarios

### Scenario 1: Cross-Node Insight Sharing

```typescript
test('E2E: Node A publishes insight, Node B retrieves and qualifies it', async () => {
  // Node A
  const insight = await nodeA.publishInsight({
    type: 'pattern_claim',
    summary: 'Validation checklist improves completion rate',
    confidence: 0.85
  });

  // Wait for federation
  await waitForFederation();

  // Node B
  const artifact = await nodeB.retrieveArtifact(insight.federatedId);
  expect(artifact).toBeDefined();

  const qualification = await nodeB.qualifyArtifact(artifact, nodeB.localContext);
  expect(qualification.suggestedAction).toBe('use_advisory');

  await nodeB.adoptArtifact(artifact.artifactId, 'advisory');
  const adoption = await nodeB.getAdoption(artifact.artifactId);
  expect(adoption?.adoptionType).toBe('advisory');
});
```

### Scenario 2: Contradiction Detection and Resolution

```typescript
test('E2E: Conflicting patterns trigger contradiction management', async () => {
  // Node A publishes positive claim
  await nodeA.publishClaim({
    claim: 'Topology T improves speed',
    evidence: { confidence: 0.8, sampleSize: 50 }
  });

  // Node B publishes negative claim
  await nodeB.publishClaim({
    claim: 'Topology T reduces quality',
    evidence: { confidence: 0.75, sampleSize: 30 }
  });

  // Wait for federation
  await waitForFederation();

  // Node C receives both and detects contradiction
  const contradictions = await nodeC.getContradictions();
  expect(contradictions.length).toBeGreaterThan(0);

  // Verify plurality is preserved
  const claims = await nodeC.queryClaims({ topic: 'topology_t' });
  expect(claims.length).toBeGreaterThanOrEqual(2);
});
```

---

# 10. Migration & Rollout

## 10.1 Phase 1: Foundation (Weeks 1-2)

**Deliverables:**

- Core type definitions (`src/types/layer12/`)
- Database schema migration (`src/db/schema/layer12.sql`)
- EpistemicArtifactPublisher service
- FederatedClaimRegistry service
- Basic API endpoints

**Success Criteria:**

- ✅ Can create and store epistemic artifact
- ✅ Can query artifacts by filters
- ✅ Schema migrations run successfully

## 10.2 Phase 2: Qualification (Weeks 3-4)

**Deliverables:**

- LocalQualificationEngine service
- ContradictionAndPluralityManager service
- Qualification API endpoints
- Contradiction API endpoints
- Unit tests for qualification logic

**Success Criteria:**

- ✅ Can qualify incoming artifact
- ✅ Context comparison works correctly
- ✅ Contradictions are detected and stored

## 10.3 Phase 3: Audit & Adoption (Weeks 5-6)

**Deliverables:**

- EpistemicAuditService
- Local adoption tracking
- Audit API endpoints
- Audit log queries
- Integration tests

**Success Criteria:**

- ✅ All exchanges produce audit records
- ✅ Can query adoption statistics
- ✅ Audit trail is complete

## 10.4 Phase 4: UI Implementation (Weeks 7-8)

**Deliverables:**

- Collective Intelligence Dashboard
- Qualification Queue view
- Contradiction Panel
- Adoption Status view
- E2E tests with UI

**Success Criteria:**

- ✅ Operators can view shared claims
- ✅ Operators can manually qualify artifacts
- ✅ Operators can view and manage contradictions

## 10.5 Phase 5: L11 Integration (Week 9)

**Deliverables:**

- L11 fabric integration
- Cross-node communication
- Federation testing
- Multi-node E2E tests

**Success Criteria:**

- ✅ Node A can publish claim visible to Node B
- ✅ Node B can retrieve and qualify claim from Node A
- ✅ No raw state is federated

## 10.6 Phase 6: L13 Prep (Week 10)

**Deliverables:**

- Allocative eligibility interface
- Qualification result export format
- L12→L13 boundary enforcement
- Documentation

**Success Criteria:**

- ✅ Only allocative-eligible artifacts can pass to L13
- ✅ Direct consumption of raw artifacts is blocked
- ✅ Integration with L13 mediation is verified

---

# 11. Success Criteria

## 11.1 Functional Requirements

| ID | Requirement | Verification |
|----|-------------|--------------|
| FR-1 | Node can publish insight as epistemic artifact | API test: POST /claims/publish |
| FR-2 | Other nodes can retrieve published artifact | API test: GET /claims/query |
| FR-3 | Receiving node qualifies artifact locally | Unit test: LocalQualificationEngine |
| FR-4 | Artifact is never directly authoritative | Anti-pattern test |
| FR-5 | Contradictions are preserved | Integration test |
| FR-6 | All exchanges produce audit records | Audit query test |
| FR-7 | No raw operational state is federated | Security test |
| FR-8 | Only allocative-eligible artifacts pass to L13 | Boundary test |
| FR-9 | UI surfaces show claims and qualifications | E2E UI test |
| FR-10 | Multi-node federation works | Multi-node E2E test |

## 11.2 Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-1 | Publication latency | < 100ms p95 |
| NFR-2 | Query latency | < 200ms p95 |
| NFR-3 | Qualification latency | < 500ms p95 |
| NFR-4 | Audit completeness | 100% of exchanges logged |
| NFR-5 | Data integrity | No claim modification after publication |
| NFR-6 | Redaction effectiveness | 100% of local refs removed |
| NFR-7 | Contradiction detection | < 5min from publication |

## 11.3 Architecture Constraints

| ID | Constraint | Verification |
|----|------------|--------------|
| AC-1 | No centralized truth authority | Architecture review |
| AC-2 | All authority is local | Qualification always runs locally |
| AC-3 | Plurality is preserved | Contradictions not auto-resolved |
| AC-4 | Context is primary | Context mismatch prevents adoption |
| AC-5 | Provenance is preserved | All claims traceable to origin |
| AC-6 | State boundaries enforced | No raw state in artifacts |

---

# 12. Open Questions

| Question | Impact | Target Resolution |
|----------|--------|-------------------|
| Q1 | How to handle version updates to published claims? | High | Phase 2 |
| Q2 | What's the retention policy for claims and audit logs? | Medium | Phase 1 |
| Q3 | How to handle node disconnection during claim exchange? | High | Phase 5 |
| Q4 | Should there be a claim expiration / stale claim policy? | Medium | Phase 3 |
| Q5 | How to handle very large context/evidence JSON payloads? | Low | Phase 1 |

---

# 13. Dependencies

## 13.1 External Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| Layer 11 Distributed Fabric | L11 complete | Cross-node communication |
| Layer 4 Insight Publishing | L4 M4+ | Source of federatable insights |
| Database | PostgreSQL 15+ | Claim registry storage |
| TypeScript | 5.0+ | Type definitions |

## 13.2 Internal Dependencies

```
Layer 4 (Insight Publishing)
    ↓
Layer 12 (this PRD)
    ↓
Layer 13 (Economic Intelligence)
```

Layer 12 cannot be fully operational until:
- Layer 4 insight publishing is stable
- Layer 11 fabric is available
- Layer 13 mediation boundary is defined

---

# 14. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Hidden authority emergence | Medium | High | Anti-pattern tests, architectural reviews |
| Context mismatch errors | High | Medium | Strict validation, manual review override |
| Contradiction explosion | Low | Medium | Contradiction clustering, auto-archiving |
| Performance at scale | Medium | Medium | Caching, indexing, pagination |
| Redaction failures | Low | High | Automated testing, manual review samples |
| L11 integration issues | Medium | High | Early integration testing, fallback mechanisms |

---

# 15. Appendix

## 15.1 Glossary

| Term | Definition |
|------|------------|
| **Epistemic Artifact** | A knowledge object (claim) packaged with provenance, context, and evidence for federation |
| **Claim** | A statement about what was observed or learned |
| **Qualification** | The local evaluation of a federated artifact before adoption |
| **Contradiction** | When two or more claims conflict with each other |
| **Plurality** | The preservation of multiple competing explanations |
| **Allocative Eligible** | A classification indicating an artifact may influence economic decisions (after L13 mediation) |
| **Provenance** | The origin and lineage of an artifact |
| **Context** | The conditions under which a claim is valid (domain, mission type, etc.) |

## 15.2 Related Documents

- `TORQ_Federated_Epistemology.md` — Design principles and mental models
- `TORQ_Collective_to_Economic_Mediation.md` — L12→L13 boundary constraints
- `TORQ_Legitimacy_and_Constitutional_Intelligence.md` — L14 authority validation
- `TORQ_Master_Architecture.md` — Overall system architecture
- `TORQ_Data_Flow_Architecture.md` — Intelligence pipeline details

---

**End of PRD**
