/**
 * Federation Enumerations and Literals
 *
 * Phase 1B - Shared type definitions for federation layer enums and literal types.
 * These contracts define the stable values used across both frontend and backend.
 */

/**
 * Trust decision outcomes for inbound claim evaluation.
 */
export type TrustDecision = "accept" | "quarantine" | "reject" | "reject_and_flag";

/**
 * Signature algorithm types supported for federation.
 */
export type SignatureAlgorithm = "ED25519" | "RSA-2048" | "RSA-4096" | "ECDSA-P256";

/**
 * Node trust tiers for classification.
 */
export type TrustTier = "trusted" | "verified" | "unknown" | "quarantined";

/**
 * Artifact types that can be federated.
 */
export type ArtifactType = "insight" | "pattern" | "strategy" | "observation" | "recommendation";

/**
 * Origin layers within a node.
 */
export type OriginLayer =
  | "layer1"  // Ingest
  | "layer2"  // Processing
  | "layer3"  // Memory
  | "layer4"  // Insight Intelligence
  | "layer5"  // Context
  | "layer6"  // Qualification
  | "layer7"  // Publishing
  | "layer8"  // Retention
  | "layer9"  // Learning
  | "layer10" // Evolution
  | "layer11" // Distributed Fabric
  | "layer12"; // Epistemic Federation

/**
 * Protocol version for federation compatibility.
 */
export const FEDERATION_PROTOCOL_VERSION = "1.0.0" as const;

/**
 * Supported protocol versions.
 */
export type ProtocolVersion = "1.0.0";

/**
 * Trust score ranges for decision making.
 */
export interface TrustThresholds {
  /** Minimum trust score for automatic acceptance (default: 0.75) */
  acceptMin: number;
  /** Minimum trust score for quarantine range (default: 0.45) */
  quarantineMin: number;
  /** Maximum trust score for quarantine range (default: 0.74) */
  quarantineMax: number;
}

/**
 * Default trust thresholds.
 */
export const DEFAULT_TRUST_THRESHOLDS: TrustThresholds = {
  acceptMin: 0.75,
  quarantineMin: 0.45,
  quarantineMax: 0.74,
} as const;

/**
 * Signature tolerance in seconds (default: 300 = 5 minutes).
 */
export const SIGNATURE_TOLERANCE_SECONDS = 300 as const;

/**
 * Federation error codes.
 */
export type FederationErrorCode =
  | "IDENTITY_VALIDATION_FAILED"
  | "SIGNATURE_VERIFICATION_FAILED"
  | "TRUST_EVALUATION_FAILED"
  | "UNKNOWN_NODE"
  | "UNSUPPORTED_PROTOCOL_VERSION"
  | "UNSUPPORTED_ALGORITHM"
  | "SIGNATURE_EXPIRED"
  | "PAYLET_MISMATCH"
  | "REPLAY_ATTACK_DETECTED"
  | "DUPLICATE_CLAIM"
  | "QUARANTINE"
  | "NODE_INACTIVE"
  | "CREDENTIAL_MISMATCH";

/**
 * Validation status for components.
 */
export type ValidationStatus =
  | "pending"
  | "validating"
  | "valid"
  | "invalid"
  | "quarantined"
  | "error";

/**
 * Federation event types for logging.
 */
export type FederationEventType =
  | "envelope_received"
  | "identity_validated"
  | "signature_verified"
  | "trust_evaluated"
  | "claim_accepted"
  | "claim_quarantined"
  | "claim_rejected"
  | "claim_flagged"
  | "replay_detected"
  | "duplicate_suppressed";

/**
 * Node status indicators.
 */
export type NodeStatus = "active" | "inactive" | "quarantined" | "unknown";

/**
 * Processing states for inbound claims.
 */
export type ClaimProcessingState =
  | "received"
  | "normalizing"
  | "identity_check"
  | "signature_check"
  | "replay_check"
  | "duplicate_check"
  | "persisting"
  | "qualifying"
  | "contradiction_check"
  | "completed"
  | "failed";

/**
 * API response status codes.
 */
export type ApiResponseStatus = "success" | "error" | "partial";

/**
 * Quality gate outcomes.
 */
export type QualityGateOutcome = "passed" | "failed" | "warning" | "skipped";
