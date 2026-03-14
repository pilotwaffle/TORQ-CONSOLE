/**
 * Trust Decision Type Definitions
 *
 * Phase 1B - Types for trust evaluation, inbound decisions,
 * and trust-based claim acceptance.
 */

import type { TrustDecision, TrustTier } from "./enums";
import type { IdentityValidationResult } from "./identity";
import type { SignatureVerificationResult } from "./signature";
import type { FederatedClaimEnvelope } from "./envelope";

/**
 * Unified inbound trust decision for a claim envelope.
 */
export interface InboundTrustDecision {
  /** Decision outcome */
  decision: TrustDecision;
  /** Reasons for the decision */
  reasons: string[];
  /** Trust score of source node (0.0 - 1.0) */
  nodeTrustScore: number;
  /** Whether identity validation passed */
  identityValid: boolean;
  /** Whether signature verification passed */
  signatureValid: boolean;
  /** Source node ID */
  nodeId: string;
  /** Envelope ID being decided */
  envelopeId: string;
  /** When decision was made (ISO 8601) */
  decidedAt: string;
  /** Optional decision metadata */
  metadata?: {
    /** Processing duration in milliseconds */
    processingDurationMs?: number;
    /** Decision rule version */
    ruleVersion?: string;
    /** Additional context */
    [key: string]: unknown;
  };
}

/**
 * Computed properties for trust decision.
 */
export interface TrustDecisionProperties {
  /** Whether envelope should proceed to processing */
  shouldProceed: boolean;
  /** Whether envelope requires quarantine */
  requiresQuarantine: boolean;
  /** Whether envelope was rejected */
  isRejection: boolean;
  /** Whether rejection requires flagging */
  requiresFlagging: boolean;
}

/**
 * Full trust decision with computed properties.
 */
export interface ExtendedTrustDecision extends InboundTrustDecision, TrustDecisionProperties {}

/**
 * Trust evaluation request.
 */
export interface EvaluateInboundTrustRequest {
  /** Envelope to evaluate */
  envelope: FederatedClaimEnvelope;
  /** Optional pre-computed identity validation */
  identityValidation?: IdentityValidationResult;
  /** Optional pre-computed signature verification */
  signatureVerification?: SignatureVerificationResult;
  /** Evaluation options */
  options?: {
    /** Skip identity validation */
    skipIdentityCheck?: boolean;
    /** Skip signature verification */
    skipSignatureCheck?: boolean;
    /** Force trust score for testing */
    forceTrustScore?: number;
    /** Override decision for testing */
    overrideDecision?: TrustDecision;
  };
}

/**
 * Trust evaluation result with full details.
 */
export interface TrustEvaluationResult {
  /** Final decision */
  decision: ExtendedTrustDecision;
  /** Identity validation details */
  identityValidation?: IdentityValidationResult;
  /** Signature verification details */
  signatureVerification?: SignatureVerificationResult;
  /** Node trust profile used */
  trustProfile?: {
    nodeId: string;
    baselineTrustScore: number;
    trustTier: TrustTier;
    isTrusted: boolean;
    isQuarantined: boolean;
  };
  /** Evaluation steps taken */
  steps: EvaluationStep[];
}

/**
 * Individual evaluation step.
 */
export interface EvaluationStep {
  /** Step name */
  name: string;
  /** Step result */
  result: "pass" | "fail" | "skip" | "warn";
  /** Step duration in milliseconds */
  durationMs?: number;
  /** Step details */
  details?: string;
  /** Timestamp */
  timestamp: string;
}

/**
 * Trust threshold configuration.
 */
export interface TrustThresholdConfig {
  /** Minimum trust score for acceptance */
  acceptMin: number;
  /** Minimum trust score for quarantine */
  quarantineMin: number;
  /** Maximum trust score for quarantine */
  quarantineMax: number;
  /** Reject threshold (below this) */
  rejectThreshold: number;
}

/**
 * Trust decision rule definition.
 */
export interface TrustDecisionRule {
  /** Rule name */
  name: string;
  /** Rule priority (higher = evaluated first) */
  priority: number;
  /** Rule condition */
  condition: {
    /** Required identity status */
    identityValid?: boolean;
    /** Required signature status */
    signatureValid?: boolean;
    /** Minimum trust score */
    minTrustScore?: number;
    /** Maximum trust score */
    maxTrustScore?: number;
    /** Required trust tier */
    trustTier?: TrustTier;
  };
  /** Decision if condition matches */
  decision: TrustDecision;
  /** Reason template */
  reasonTemplate: string;
}

/**
 * Quarantine details for quarantined claims.
 */
export interface QuarantineDetails {
  /** Quarantine ID */
  quarantineId: string;
  /** Envelope ID */
  envelopeId: string;
  /** Source node ID */
  nodeId: string;
  /** Quarantine reason */
  reason: string;
  /** Quarantine timestamp */
  quarantinedAt: string;
  /** Review status */
  reviewStatus: "pending" | "under_review" | "approved" | "rejected";
  /** Optional reviewer notes */
  reviewerNotes?: string;
  /** When quarantine was resolved */
  resolvedAt?: string;
}

/**
 * Flagged claim details for reject_and_flag.
 */
export interface FlaggedClaimDetails {
  /** Flag ID */
  flagId: string;
  /** Envelope ID */
  envelopeId: string;
  /** Source node ID */
  nodeId: string;
  /** Flag reason */
  reason: string;
  /** Flag severity */
  severity: "low" | "medium" | "high" | "critical";
  /** Flag timestamp */
  flaggedAt: string;
  /** Resolution status */
  resolutionStatus: "pending" | "investigating" | "resolved" | "false_positive";
  /** Incident ID if created */
  incidentId?: string;
}

/**
 * Trust history entry.
 */
export interface TrustHistoryEntry {
  /** Entry ID */
  entryId: string;
  /** Node ID */
  nodeId: string;
  /** Timestamp */
  timestamp: string;
  /** Event type */
  eventType: "decision" | "score_change" | "tier_change" | "quarantine" | "flag";
  /** Previous value */
  previousValue?: {
    trustScore?: number;
    trustTier?: TrustTier;
  };
  /** New value */
  newValue: {
    trustScore?: number;
    trustTier?: TrustTier;
  };
  /** Associated envelope ID if applicable */
  envelopeId?: string;
  /** Reason for change */
  reason: string;
}
