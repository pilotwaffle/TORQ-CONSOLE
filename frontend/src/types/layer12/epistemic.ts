/**
 * Layer 12: Collective Intelligence Exchange
 * Core Type Definitions
 *
 * This file defines the TypeScript interfaces for the federated epistemology system.
 * These types ensure proper data structures across all Layer 12 services.
 */

/**
 * The canonical epistemic artifact structure
 * Represents a knowledge object (claim) packaged with provenance, context, and evidence for federation
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
  contradictions?: string[]; // refs to conflicting claims

  // Usage Scope
  allowedUses: AllowedUse[];

  // Provenance
  provenance: ClaimProvenance;
}

/**
 * Artifact types - categorizes the kind of claim being made
 */
export type ArtifactType =
  | "observation"        // "We observed X in environment Y"
  | "pattern_claim"      // "Pattern P appears across N missions"
  | "causal_claim"       // "Change C caused effect E"
  | "policy_claim"       // "Policy rule R improved outcome O"
  | "recommendation";    // "We suggest approach A for problem P"

/**
 * Context metadata - describes the conditions under which a claim is valid
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
 * Evidence envelope - quantifies the support for a claim
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
 * Allowed use classes - defines how an artifact may be used
 */
export type AllowedUse =
  | "informational"        // Awareness only, dashboards, planning
  | "advisory"            // Can inform decisions, no direct action
  | "simulation_only"      // Can be used in simulations only
  | "allocative_eligible"; // May influence economic optimization (requires mediation)

/**
 * Provenance tracking - tracks the origin and lineage of an artifact
 */
export interface ClaimProvenance {
  sourceArtifacts: string[];
  sourceInsights: string[];
  lineageDepth: number;
  createdBy: string;
  creationPath: string[];
}

/**
 * Qualification result - the output of local qualification evaluation
 */
export interface QualificationResult {
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
  contextComparison: ContextComparison;

  // Recommendations
  recommendedUses: AllowedUse[];
  warnings: string[];
  adaptations?: string[];

  // Decision guidance
  suggestedAction: SuggestedAction;
}

/**
 * Suggested action - what the qualification engine recommends
 */
export type SuggestedAction =
  | "ignore"
  | "store_informational"
  | "use_advisory"
  | "send_to_simulation"
  | "send_to_governance";

/**
 * Context comparison - compares origin context to local context
 */
export interface ContextComparison {
  domainMatch: boolean;
  missionTypeMatch: boolean;
  agentTopologyMatch: boolean;
  environmentMatch: boolean;
  overallMatch: number;
}

/**
 * Contradiction record - tracks conflicts between claims
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

/**
 * Contradiction types - categorizes the kind of conflict
 */
export type ContradictionType =
  | "direct_contradiction"
  | "context_conflict"
  | "causal_disagreement"
  | "recommendation_conflict";

/**
 * Resolution types - how a contradiction was resolved
 */
export type ResolutionType =
  | "context_dependent"
  | "simulation_resolved"
  | "governance_resolved"
  | "both_valid"
  | "superseded";

/**
 * Transferability check - assesses whether an artifact can move across nodes
 */
export interface TransferabilityCheck {
  canMoveAcrossNodes: boolean;
  transferable?: boolean; // Alias for canMoveAcrossNodes
  requiresContext: string[];
  localAdaptationRequired: boolean;
  riskLevel: 'low' | 'medium' | 'high';
  reasons: string[];
  score?: number; // Transferability score 0-1
}

/**
 * Transferability level - hint for how transferable an artifact is
 */
export type TransferabilityLevel = 'low' | 'medium' | 'high';

/**
 * Policy compatibility - checks if an artifact is compatible with local policies
 */
export interface PolicyCompatibility {
  compatibleWith: string[];  // Policy IDs
  conflictsWith: string[];    // Policy IDs
  requiresApproval: boolean;
  authorityLevel: 'node' | 'region' | 'network';
  compatible?: boolean; // Computed property: true if no conflicts
  violations?: string[]; // Alias for conflictsWith
}

/**
 * Publication options - options for publishing an artifact
 */
export interface PublicationOptions {
  allowedUses: AllowedUse[];
  transferabilityHint?: TransferabilityLevel;
  limitations?: string[];
  contradictions?: string[];
}

/**
 * Publication result - result of publishing an artifact
 */
export interface PublicationResult {
  artifactId: string;
  status: 'published' | 'redacted' | 'rejected';
  redactions?: string[];
  warnings?: string[];
  publishedAt: number;
}

/**
 * Validation result - result of validating an artifact for publication
 */
export interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

/**
 * Claim query - query parameters for searching claims
 */
export interface ClaimQuery {
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

/**
 * Claim record - a stored claim in the registry
 */
export interface ClaimRecord {
  artifactId: string;
  artifactType: ArtifactType;
  originNode: string;
  originLayer: number;
  createdAt: number;
  version: string;
  claim: string;
  summary: string;
  context: ArtifactContext;
  evidence: EvidenceEnvelope;
  limitations: string[];
  allowedUses: AllowedUse[];
  provenance: ClaimProvenance;
  receivedAt?: number;
  indexedAt?: number;
}

/**
 * Local context - the receiving node's context for qualification
 */
export interface LocalContext {
  domain: string;
  missionType?: string;
  agentTopology?: string;
  policyRegime?: string;
  environmentClass?: string;
  activePolicies?: string[]; // Policy IDs currently in effect
}

/**
 * Plurality view - shows competing claims on a topic
 */
export interface PluralityView {
  topic: string;
  competingClaims: CompetingClaim[];
  contradictionCount: number;
  hasResolution: boolean;
  suggestedAction: 'preserve_plurality' | 'simulation_test' | 'governance_review';
}

/**
 * Competing claim - a claim in a plurality view
 */
export interface CompetingClaim {
  claimId: string;
  claim: string;
  originNode: string;
  confidence: number;
  context: ArtifactContext;
  supportingEvidence: number;
}

/**
 * Contradiction detection - result of automatic contradiction detection
 */
export interface ContradictionDetection {
  contradictions: DetectedContradiction[];
  pluralityPreserved: boolean;
}

/**
 * Detected contradiction - a detected contradiction between claims
 */
export interface DetectedContradiction {
  claimAId: string;
  claimBId: string;
  type: ContradictionType;
  confidence: number;
}

/**
 * Audit event types - types of events in the epistemic audit log
 */
export type AuditEventType =
  | "publication"
  | "qualification"
  | "adoption"
  | "rejection"
  | "simulation_test"
  | "governance_review";

/**
 * Base audit event - common fields for all audit events
 */
export interface BaseAuditEvent {
  eventId: string;
  eventType: AuditEventType;
  artifactId: string;
  nodeId: string;
  timestamp: number;
}

/**
 * Publication event - logged when an artifact is published
 */
export interface PublicationEvent extends BaseAuditEvent {
  eventType: "publication";
  originNode: string;
  artifactType: ArtifactType;
  allowedUses: AllowedUse[];
}

/**
 * Qualification event - logged when an artifact is qualified
 */
export interface QualificationEvent extends BaseAuditEvent {
  eventType: "qualification";
  category: string;
  localRelevance: number;
  localTrust: number;
  suggestedAction: SuggestedAction;
}

/**
 * Adoption event - logged when an artifact is adopted
 */
export interface AdoptionEvent extends BaseAuditEvent {
  eventType: "adoption";
  adoptionType: 'informational' | 'advisory' | 'simulation_tested' | 'allocative_eligible';
  adaptations?: string[];
}

/**
 * Rejection event - logged when an artifact is rejected
 */
export interface RejectionEvent extends BaseAuditEvent {
  eventType: "rejection";
  reason: string;
  details?: string;
}

/**
 * Simulation test event - logged when an artifact is sent to simulation
 */
export interface SimulationTestEvent extends BaseAuditEvent {
  eventType: "simulation_test";
  simulationId: string;
  result?: 'confirmed' | 'contradicted' | 'inconclusive';
}

/**
 * Governance review event - logged when an artifact is sent to governance
 */
export interface GovernanceReviewEvent extends BaseAuditEvent {
  eventType: "governance_review";
  reviewId: string;
  outcome?: 'approved' | 'rejected' | 'escalated';
}

/**
 * Audit query - query parameters for audit log
 */
export interface AuditQuery {
  artifactId?: string;
  eventType?: AuditEventType;
  nodeId?: string;
  startDate?: number;
  endDate?: number;
}

/**
 * Adoption statistics - summary of adoption metrics
 */
export interface AdoptionStatistics {
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

/**
 * Time range - a range of timestamps
 */
export interface TimeRange {
  start: number;
  end: number;
}

/**
 * Authority tiers - for Layer 14 integration
 */
export type AuthorityTier =
  | "operator"
  | "node"
  | "regional"
  | "network"
  | "constitutional";

/**
 * Authority scope - for Layer 14 integration
 */
export type AuthorityScope =
  | "informational"
  | "advisory"
  | "local_execution"
  | "cross_node_influence"
  | "network_impact"
  | "emergency";

/**
 * Delegation - for Layer 14 integration
 */
export interface Delegation {
  delegatingTier: AuthorityTier;
  receivingTier: AuthorityTier;
  scope: AuthorityScope;
  domain?: string;
  conditions: string[];
  expiresAt?: number;
  revocable: boolean;
  ratificationRequired?: boolean;
}
