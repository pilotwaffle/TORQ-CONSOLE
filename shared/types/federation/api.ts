/**
 * Federation API Contract Definitions
 *
 * Phase 1B - Request/response types for federation API endpoints.
 * These define the wire format for communication between browser console
 * and Python backend.
 */

import type { FederatedClaimEnvelope, NodeCredentials } from "./envelope";
import type { IdentityValidationResult, NodeTrustProfile } from "./identity";
import type { SignatureVerificationResult } from "./signature";
import type { InboundTrustDecision, ExtendedTrustDecision } from "./trust";
import type { FederationErrorCode, ApiResponseStatus, ProtocolVersion } from "./enums";

/**
 * Base API response wrapper.
 */
export interface ApiResponse<T = unknown> {
  /** Response status */
  status: ApiResponseStatus;
  /** Response data (present on success) */
  data?: T;
  /** Error details (present on error) */
  error?: FederationErrorResponse;
  /** Request metadata */
  meta?: ResponseMeta;
}

/**
 * Response metadata.
 */
export interface ResponseMeta {
  /** Response timestamp (ISO 8601) */
  timestamp: string;
  /** Request ID for tracing */
  requestId: string;
  /** Processing duration in milliseconds */
  processingDurationMs: number;
  /** API version */
  apiVersion: string;
}

/**
 * Federation error response.
 */
export interface FederationErrorResponse {
  /** Error code */
  code: FederationErrorCode;
  /** Human-readable error message */
  message: string;
  /** Detailed error context */
  details?: Record<string, unknown>;
  /** Stack trace (dev only) */
  stack?: string;
}

/**
 * Validate Identity API request.
 */
export interface ValidateIdentityApiRequest {
  /** Node ID to validate */
  nodeId: string;
  /** Optional presented credentials */
  credentials?: {
    keyId: string;
    publicKey: string;
  };
}

/**
 * Validate Identity API response.
 */
export interface ValidateIdentityApiResponse extends ApiResponse<IdentityValidationResult> {
}

/**
 * Verify Signature API request.
 */
export interface VerifySignatureApiRequest {
  /** Envelope containing signature */
  envelope: FederatedClaimEnvelope;
  /** Verification options */
  options?: {
    clockToleranceSeconds?: number;
    skipTimestampCheck?: boolean;
  };
}

/**
 * Verify Signature API response.
 */
export interface VerifySignatureApiResponse extends ApiResponse<SignatureVerificationResult> {
}

/**
 * Evaluate Inbound Trust API request.
 */
export interface EvaluateInboundTrustApiRequest {
  /** Envelope to evaluate */
  envelope: FederatedClaimEnvelope;
  /** Optional pre-computed validations */
  preComputed?: {
    identityValidation?: IdentityValidationResult;
    signatureVerification?: SignatureVerificationResult;
  };
  /** Evaluation options */
  options?: {
    skipIdentityCheck?: boolean;
    skipSignatureCheck?: boolean;
    forceTrustScore?: number;
  };
}

/**
 * Evaluate Inbound Trust API response.
 */
export interface EvaluateInboundTrustApiResponse extends ApiResponse<ExtendedTrustDecision> {
}

/**
 * Register Node API request.
 */
export interface RegisterNodeApiRequest {
  /** Node credentials */
  credentials: {
    nodeId: string;
    keyId: string;
    publicKey: string;
  };
  /** Initial trust tier */
  trustTier?: string;
  /** Start as active */
  isActive?: boolean;
}

/**
 * Register Node API response.
 */
export interface RegisterNodeApiResponse extends ApiResponse<{ success: boolean; nodeId: string }> {
}

/**
 * Get Node Trust Profile API request.
 */
export interface GetNodeTrustProfileApiRequest {
  /** Node ID */
  nodeId: string;
}

/**
 * Get Node Trust Profile API response.
 */
export interface GetNodeTrustProfileApiResponse extends ApiResponse<NodeTrustProfile> {
}

/**
 * List Nodes API request.
 */
export interface ListNodesApiRequest {
  /** Filter by status */
  status?: string;
  /** Filter by trust tier */
  trustTier?: string;
  /** Pagination offset */
  offset?: number;
  /** Pagination limit */
  limit?: number;
}

/**
 * Node list entry.
 */
export interface NodeListEntry {
  nodeId: string;
  trustTier: string;
  status: string;
  baselineTrustScore: number;
  lastSeen: string;
}

/**
 * List Nodes API response.
 */
export interface ListNodesApiResponse extends ApiResponse<{ nodes: NodeListEntry[]; total: number }> {
}

/**
 * Submit Claim API request (for future inbound processor).
 */
export interface SubmitClaimApiRequest {
  /** Envelope to submit */
  envelope: FederatedClaimEnvelope;
  /** Skip trust evaluation (for testing) */
  skipTrustEvaluation?: boolean;
}

/**
 * Submit Claim API response.
 */
export interface SubmitClaimApiResponse extends ApiResponse<{
  success: boolean;
  claimId: string;
  decision?: InboundTrustDecision;
}> {
}

/**
 * Process Inbound Claim API request.
 */
export interface ProcessInboundClaimApiRequest {
  /** Envelope to process */
  envelope: FederatedClaimEnvelope;
  /** Processing options */
  options?: {
    /** Skip replay protection check */
    skipReplayCheck?: boolean;
    /** Skip duplicate suppression check */
    skipDuplicateCheck?: boolean;
    /** Force acceptance regardless of validation (testing only) */
    forceAccept?: boolean;
  };
}

/**
 * Process Inbound Claim API response.
 */
export interface ProcessInboundClaimApiResponse extends ApiResponse<{
  /** Processing status */
  status: "accepted" | "quarantined" | "rejected";
  /** Envelope ID */
  envelopeId: string;
  /** Internal claim ID if assigned */
  claimId: string | null;
  /** Source node ID */
  sourceNodeId: string;
  /** Identity validation result */
  identityValidation: IdentityValidationResult | null;
  /** Signature verification result */
  signatureVerification: SignatureVerificationResult | null;
  /** Trust evaluation decision */
  trustDecision: ExtendedTrustDecision | null;
  /** Replay protection result */
  replayProtection: {
    isReplay: boolean;
    envelopeId: string;
    checkType: string;
    firstSeen: string | null;
    blockedReason: string | null;
  } | null;
  /** Duplicate suppression result */
  duplicateSuppression: {
    isDuplicate: boolean;
    claimId: string;
    envelopeId: string;
    existingEnvelopeId: string | null;
    firstSeen: string | null;
    sourceCount: number;
    sources: string[];
  } | null;
  /** Persisted claim ID */
  persistedClaimId: string | null;
  /** Qualification score from LocalQualificationEngine */
  qualificationScore: number | null;
  /** Number of contradictions detected */
  contradictionCount: number;
  /** Plurality status after processing */
  pluralityStatus: string | null;
  /** IDs of audit events written */
  auditEventIds: string[];
  /** When processing started */
  processingStartedAt: string;
  /** When processing completed */
  processingCompletedAt: string;
  /** Processing duration in milliseconds */
  processingDurationMs: number;
  /** Rejection reason if rejected */
  rejectionReason: string | null;
  /** Quarantine reasons if quarantined */
  quarantineReasons: string[];
}> {
}

/**
 * Get Federation Status API response.
 */
export interface FederationStatus {
  /** Protocol version */
  protocolVersion: ProtocolVersion;
  /** Node ID */
  nodeId: string;
  /** Active connections */
  activeConnections: number;
  /** Total claims processed */
  totalClaimsProcessed: number;
  /** Total claims accepted */
  totalClaimsAccepted: number;
  /** Total claims quarantined */
  totalClaimsQuarantined: number;
  /** Total claims rejected */
  totalClaimsRejected: number;
  /** Uptime in seconds */
  uptimeSeconds: number;
}

/**
 * Get Federation Status API response.
 */
export interface GetFederationStatusApiResponse extends ApiResponse<FederationStatus> {
}

/**
 * Batch Trust Evaluation API request.
 */
export interface BatchEvaluateTrustApiRequest {
  /** Envelopes to evaluate */
  envelopes: FederatedClaimEnvelope[];
  /** Shared options */
  options?: EvaluateInboundTrustApiRequest["options"];
}

/**
 * Batch Trust Evaluation API response.
 */
export interface BatchEvaluateTrustApiResponse extends ApiResponse<{
  decisions: ExtendedTrustDecision[];
  summary: {
    total: number;
    accept: number;
    quarantine: number;
    reject: number;
    rejectAndFlag: number;
  };
}> {
}

/**
 * WebSocket message types.
 */
export interface FederationWebSocketMessage {
  /** Message type */
  type: "envelope_received" | "decision_made" | "status_update" | "error";
  /** Message payload */
  payload: unknown;
  /** Timestamp */
  timestamp: string;
}

/**
 * Envelope received event.
 */
export interface EnvelopeReceivedEvent {
  envelope: FederatedClaimEnvelope;
  receivedAt: string;
}

/**
 * Decision made event.
 */
export interface DecisionMadeEvent {
  envelopeId: string;
  decision: ExtendedTrustDecision;
  decidedAt: string;
}
