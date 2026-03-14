/**
 * Layer 12: Collective Intelligence Exchange
 * Federation Types
 *
 * Data contracts for cross-node claim exchange.
 */

/**
 * Federated claim envelope for network transmission
 */
export interface FederatedClaimEnvelope {
  envelopeId: string;
  protocolVersion: string;
  sourceNodeId: string;
  targetNodeId?: string;
  sentAt: number;
  artifact: FederatedArtifactPayload;
  signature: ArtifactSignature;
  trace: FederationTrace;
}

/**
 * Artifact payload suitable for federation (redacted)
 */
export interface FederatedArtifactPayload {
  artifactId: string;
  artifactType: 'observational' | 'pattern' | 'causal' | 'recommendation';
  title: string;
  claimText: string;
  summary?: string;
  confidence: number;
  provenanceScore?: number;
  originLayer: number;
  originInsightId?: string;
  context: Record<string, unknown>;
  limitations?: string[];
  allowedUses: ('informational' | 'advisory' | 'simulation_tested' | 'allocative_eligible')[];
  tags?: string[];
  redactedFields?: string[];
}

/**
 * Digital signature for artifact authenticity
 */
export interface ArtifactSignature {
  algorithm: string;
  signerNodeId: string;
  signatureValue: string;
  signedAt: number;
}

/**
 * Federation trace for routing and replay protection
 */
export interface FederationTrace {
  messageId: string;
  hopCount: number;
  priorNodeIds: string[];
  correlationId?: string;
}

/**
 * Result of publishing an artifact
 */
export interface PublishArtifactResult {
  success: boolean;
  envelopeId?: string;
  transmittedAt?: number;
  errors?: string[];
}

/**
 * Result of receiving an inbound claim
 */
export interface InboundEnvelopeResult {
  accepted: boolean;
  reason?: string;
  processingResult?: InboundProcessingResult;
}

/**
 * Result of processing an inbound claim through the full pipeline
 */
export interface InboundProcessingResult {
  claimId: string;
  qualificationResult?: 'adopted' | 'rejected' | 'quarantined' | 'ignored';
  contradictionIds?: string[];
  warnings?: string[];
  processedAt: number;
}

/**
 * Node identity and credentials
 */
export interface NodeCredentials {
  nodeId: string;
  publicKey: string;
  certificate?: string;
  credentialsVersion: number;
}

/**
 * Result of validating node identity
 */
export interface IdentityValidationResult {
  valid: boolean;
  nodeId: string;
  trustLevel?: 'trusted' | 'known' | 'unknown' | 'untrusted';
  errors?: string[];
}

/**
 * Result of verifying artifact signature
 */
export interface SignatureVerificationResult {
  valid: boolean;
  signerNodeId: string;
  algorithm: string;
  verifiedAt: number;
  errors?: string[];
}

/**
 * Node trust profile
 */
export interface NodeTrustProfile {
  nodeId: string;
  trustScore: number; // 0-1
  historicalClaimQuality: number;
  contradictionRate: number;
  adoptionSuccessRate: number;
  signatureFailures: number;
  replayViolations: number;
  duplicateViolations: number;
  lastUpdated: number;
}

/**
 * Replay protection check result
 */
export interface ReplayCheckResult {
  isReplay: boolean;
  originalMessageId?: string;
  originalSeenAt?: number;
}

/**
 * Duplicate suppression check result
 */
export interface DuplicateCheckResult {
  isDuplicate: boolean;
  existingClaimId?: string;
  existingClaimNodeId?: string;
}

/**
 * Normalized claim ready for local processing
 */
export interface NormalizedClaim {
  envelopeId: string;
  sourceNodeId: string;
  artifact: FederatedArtifactPayload;
  receivedAt: number;
}

/**
 * Federation eligibility filter result
 */
export interface FederationEligibilityResult {
  eligible: boolean;
  reasons: string[];
  redactedFields?: string[];
}

/**
 * Context similarity result
 */
export interface ContextSimilarityResult {
  similar: boolean;
  similarityScore: number;
  contextDifferences: string[];
}

/**
 * Federation audit event types
 */
export type FederationAuditEventType =
  | 'insight_adapted'
  | 'artifact_published'
  | 'envelope_sent'
  | 'envelope_received'
  | 'identity_validated'
  | 'signature_verified'
  | 'replay_detected'
  | 'duplicate_suppressed'
  | 'claim_qualified'
  | 'contradiction_detected'
  | 'contradiction_resolved'
  | 'quarantine_triggered'
  | 'node_trust_updated';

/**
 * Federation audit event
 */
export interface FederationAuditEvent {
  eventId: string;
  eventType: FederationAuditEventType;
  nodeId: string;
  timestamp: number;
  envelopeId?: string;
  artifactId?: string;
  sourceNodeId?: string;
  details: Record<string, unknown>;
}

/**
 * Federation audit query
 */
export interface FederationAuditQuery {
  nodeId?: string;
  eventType?: FederationAuditEventType;
  envelopeId?: string;
  artifactId?: string;
  sourceNodeId?: string;
  startDate?: number;
  endDate?: number;
}
