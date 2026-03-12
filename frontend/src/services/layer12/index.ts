/**
 * Layer 12: Collective Intelligence Exchange
 * Service Barrel
 *
 * Central export point for all Layer 12 services
 */

export { EpistemicArtifactPublisher, createEpistemicArtifactPublisher } from './EpistemicArtifactPublisher';
export { FederatedClaimRegistry, createFederatedClaimRegistry } from './FederatedClaimRegistry';
export { LocalQualificationEngine, createLocalQualificationEngine } from './LocalQualificationEngine';
export { ContradictionAndPluralityManager, createContradictionAndPluralityManager } from './ContradictionAndPluralityManager';
export { EpistemicAuditService, createEpistemicAuditService } from './EpistemicAuditService';

/**
 * Type exports
 */
export type {
  // Core types
  EpistemicArtifact,
  ArtifactType,
  ArtifactContext,
  EvidenceEnvelope,
  AllowedUse,
  ClaimProvenance,

  // Qualification
  QualificationResult,
  SuggestedAction,
  ContextComparison,
  TransferabilityCheck,
  TransferabilityLevel,
  PolicyCompatibility,

  // Contradictions
  ContradictionRecord,
  ContradictionType,
  ResolutionType,
  PluralityView,
  CompetingClaim,

  // Publication
  PublicationOptions,
  PublicationResult,
  ValidationResult,

  // Queries
  ClaimQuery,
  ClaimRecord,
  LocalContext,

  // Audit
  AuditEventType,
  BaseAuditEvent,
  PublicationEvent,
  QualificationEvent,
  AdoptionEvent,
  RejectionEvent,
  SimulationTestEvent,
  GovernanceReviewEvent,
  AuditQuery,
  AdoptionStatistics,

  // Authority (L14 integration)
  AuthorityTier,
  AuthorityScope,
  Delegation
} from '@/types/layer12/epistemic';

/**
 * Re-export commonly used types for convenience
 */
import type {
  EpistemicArtifact,
  QualificationResult,
  ClaimQuery,
  PublicationOptions
} from '@/types/layer12/epistemic';

export type {
  EpistemicArtifact as Artifact,
  QualificationResult as Qualification,
  ClaimQuery as Query,
  PublicationOptions as PublishOptions
};
