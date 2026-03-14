/**
 * Layer 12: Collective Intelligence Exchange
 * Phase 1B: Insight + Distributed Fabric Integration
 *
 * FEDERATION CONFIGURATION
 *
 * Central configuration for all federation behavior including
 * eligibility thresholds, trust parameters, and safety limits.
 */

/**
 * Federation eligibility configuration
 * Controls which insights are allowed to be published externally
 */
export interface FederationEligibilityConfig {
  minimumConfidence: number; // Default: 0.7
  minimumProvenanceScore: number; // Default: 0.5
  minimumSampleSize: number; // Default: 50
  allowedDomains: string[]; // Empty = all domains allowed
  restrictedDomains: string[]; // Domains that cannot be federated
  requirePeerReview: boolean; // Default: true
  requireVerification: boolean; // Default: false
  maxArtifactAgeHours: number; // Default: 168 (1 week)
}

/**
 * Federation transport configuration
 */
export interface FederationTransportConfig {
  defaultTimeout: number; // Default: 30000 (30s)
  maxRetries: number; // Default: 3
  retryBackoffMs: number; // Default: 1000
  enableCompression: boolean; // Default: true
  maxEnvelopeSize: number; // Default: 1MB
}

/**
 * Identity and signature configuration
 */
export interface FederationSecurityConfig {
  signatureAlgorithm: string; // Default: 'ed25519'
  signatureVersion: string; // Default: '1.0'
  requireSignature: boolean; // Default: true
  allowUnsignedFromTrusted: boolean; // Default: false
  maxClockSkewMs: number; // Default: 60000 (1 minute)
}

/**
 * Replay protection configuration
 */
export interface ReplayProtectionConfig {
  enableReplayProtection: boolean; // Default: true
  messageCacheTtl: number; // Default: 86400000 (24 hours)
  maxHops: number; // Default: 10
  nonceValidation: boolean; // Default: true
}

/**
 * Duplicate suppression configuration
 */
export interface DuplicateSuppressionConfig {
  enableDuplicateSuppression: boolean; // Default: true
  duplicateDetectionWindow: number; // Default: 604800000 (7 days)
  similarityThreshold: number; // Default: 0.95 (very high similarity)
  checkByContentHash: boolean; // Default: true
  checkBySemanticSignature: boolean; // Default: true
}

/**
 * Node trust configuration
 */
export interface NodeTrustConfig {
  initialTrustScore: number; // Default: 0.5 (neutral)
  trustIncreaseRate: number; // Default: 0.01
  trustDecayRate: number; // Default: 0.05
  minimumTrustForAdoption: number; // Default: 0.3
  quarantineThreshold: number; // Default: 0.2
  banThreshold: number; // Default: 0.1
}

/**
 * Context similarity configuration
 */
export interface ContextSimilarityConfig {
  enableContextSimilarity: boolean; // Default: true
  requiredSimilarityForConsensus: number; // Default: 0.7
  requiredDifferenceForPlurality: number; // Default: 0.3
  contextDimensions: string[]; // Default: ['domain', 'missionType', 'agentTopology', 'policyRegime']
}

/**
 * Plurality preservation configuration
 */
export interface PluralityPreservationConfig {
  enablePluralityPreservation: boolean; // Default: true
  maxCompetingClaims: number; // Default: 10
  consensusThreshold: number; // Default: 0.9 (high agreement required)
  preferPluralityOverConsensus: boolean; // Default: true
}

/**
 * Allocative boundary configuration
 */
export interface AllocativeBoundaryConfig {
  enableAllocativeGuard: boolean; // Default: true
  requireSimulationForAllocative: boolean; // Default: true
  simulationRequiredThreshold: number; // Default: 0.8
  highImpactThreshold: number; // Default: 0.85
  quarantineHighImpactRecommendations: boolean; // Default: true
}

/**
 * Trust decay model configuration
 */
export interface TrustDecayConfig {
  enableTrustDecay: boolean; // Default: true
  decayFactor: number; // Default: 0.95 per day
  boostFactor: number; // Default: 1.05 per successful adoption
  penaltyFactor: number; // Default: 0.9 per violation
  recalibrationIntervalMs: number; // Default: 86400000 (daily)
}

/**
 * Complete federation configuration
 */
export interface FederationConfig {
  eligibility: FederationEligibilityConfig;
  transport: FederationTransportConfig;
  security: FederationSecurityConfig;
  replayProtection: ReplayProtectionConfig;
  duplicateSuppression: DuplicateSuppressionConfig;
  nodeTrust: NodeTrustConfig;
  contextSimilarity: ContextSimilarityConfig;
  pluralityPreservation: PluralityPreservationConfig;
  allocativeBoundary: AllocativeBoundaryConfig;
  trustDecay: TrustDecayConfig;
}

/**
 * Default federation configuration
 */
export const DEFAULT_FEDERATION_CONFIG: FederationConfig = {
  eligibility: {
    minimumConfidence: 0.7,
    minimumProvenanceScore: 0.5,
    minimumSampleSize: 50,
    allowedDomains: [],
    restrictedDomains: [],
    requirePeerReview: true,
    requireVerification: false,
    maxArtifactAgeHours: 168
  },
  transport: {
    defaultTimeout: 30000,
    maxRetries: 3,
    retryBackoffMs: 1000,
    enableCompression: true,
    maxEnvelopeSize: 1024 * 1024 // 1MB
  },
  security: {
    signatureAlgorithm: 'ed25519',
    signatureVersion: '1.0',
    requireSignature: true,
    allowUnsignedFromTrusted: false,
    maxClockSkewMs: 60000
  },
  replayProtection: {
    enableReplayProtection: true,
    messageCacheTtl: 86400000,
    maxHops: 10,
    nonceValidation: true
  },
  duplicateSuppression: {
    enableDuplicateSuppression: true,
    duplicateDetectionWindow: 604800000,
    similarityThreshold: 0.95,
    checkByContentHash: true,
    checkBySemanticSignature: true
  },
  nodeTrust: {
    initialTrustScore: 0.5,
    trustIncreaseRate: 0.01,
    trustDecayRate: 0.05,
    minimumTrustForAdoption: 0.3,
    quarantineThreshold: 0.2,
    banThreshold: 0.1
  },
  contextSimilarity: {
    enableContextSimilarity: true,
    requiredSimilarityForConsensus: 0.7,
    requiredDifferenceForPlurality: 0.3,
    contextDimensions: ['domain', 'missionType', 'agentTopology', 'policyRegime']
  },
  pluralityPreservation: {
    enablePluralityPreservation: true,
    maxCompetingClaims: 10,
    consensusThreshold: 0.9,
    preferPluralityOverConsensus: true
  },
  allocativeBoundary: {
    enableAllocativeGuard: true,
    requireSimulationForAllocative: true,
    simulationRequiredThreshold: 0.8,
    highImpactThreshold: 0.85,
    quarantineHighImpactRecommendations: true
  },
  trustDecay: {
    enableTrustDecay: true,
    decayFactor: 0.95,
    boostFactor: 1.05,
    penaltyFactor: 0.9,
    recalibrationIntervalMs: 86400000
  }
};
