/**
 * Federation Type Definitions
 *
 * Phase 1B - Shared TypeScript contracts for federation layer.
 * These types are used across:
 * - Browser-based federation console (TypeScript)
 * - Backend API serialization (Python -> JSON)
 * - Future external node integrations
 *
 * @version 1.0.0
 * @phase 1B
 */

// ============================================================================
// Enumerations and Literals
// ============================================================================
export type {
  TrustDecision,
  SignatureAlgorithm,
  TrustTier,
  ArtifactType,
  OriginLayer,
  ProtocolVersion,
  TrustThresholds,
  FederationErrorCode,
  ValidationStatus,
  FederationEventType,
  NodeStatus,
  ClaimProcessingState,
  ApiResponseStatus,
  QualityGateOutcome,
} from "./enums";

export const {
  FEDERATION_PROTOCOL_VERSION,
  DEFAULT_TRUST_THRESHOLDS,
  SIGNATURE_TOLERANCE_SECONDS,
} from "./enums";

// ============================================================================
// Envelope Types
// ============================================================================
export type {
  FederationTrace,
  ArtifactSignature,
  FederatedArtifactPayload,
  FederatedClaimEnvelope,
  NodeCredentials,
  CreateEnvelopeOptions,
  ValidateEnvelopeOptions,
} from "./envelope";

// ============================================================================
// Identity and Trust Types
// ============================================================================
export type {
  IdentityValidationResult,
  NodeTrustProfile,
  NodeTrustMetrics,
  NodeTrustBaseline,
  NodeRegistryEntry,
  NodeIdentity,
  ValidateIdentityRequest,
  RegisterNodeRequest,
  NodeLookupResult,
  TrustScoreAdjustment,
} from "./identity";

// ============================================================================
// Signature Types
// ============================================================================
export type {
  SignatureVerificationResult,
  VerifySignatureRequest,
  PublicKeyInfo,
  KeyRotationEvent,
  TimestampValidationResult,
  PayloadHashResult,
  CryptoVerificationOptions,
  BatchVerifyRequest,
  BatchVerifyResult,
} from "./signature";

// ============================================================================
// Trust Decision Types
// ============================================================================
export type {
  InboundTrustDecision,
  TrustDecisionProperties,
  ExtendedTrustDecision,
  EvaluateInboundTrustRequest,
  TrustEvaluationResult,
  EvaluationStep,
  TrustThresholdConfig,
  TrustDecisionRule,
  QuarantineDetails,
  FlaggedClaimDetails,
  TrustHistoryEntry,
} from "./trust";

// ============================================================================
// API Contract Types
// ============================================================================
export type {
  ApiResponse,
  ResponseMeta,
  FederationErrorResponse,
  ValidateIdentityApiRequest,
  ValidateIdentityApiResponse,
  VerifySignatureApiRequest,
  VerifySignatureApiResponse,
  EvaluateInboundTrustApiRequest,
  EvaluateInboundTrustApiResponse,
  RegisterNodeApiRequest,
  RegisterNodeApiResponse,
  GetNodeTrustProfileApiRequest,
  GetNodeTrustProfileApiResponse,
  ListNodesApiRequest,
  ListNodesApiResponse,
  NodeListEntry,
  SubmitClaimApiRequest,
  SubmitClaimApiResponse,
  ProcessInboundClaimApiRequest,
  ProcessInboundClaimApiResponse,
  GetFederationStatusApiResponse,
  FederationStatus,
  BatchEvaluateTrustApiRequest,
  BatchEvaluateTrustApiResponse,
  FederationWebSocketMessage,
  EnvelopeReceivedEvent,
  DecisionMadeEvent,
} from "./api";

// ============================================================================
// Error Types
// ============================================================================
export type {
  FederationError,
  IdentityValidationError,
  SignatureVerificationError,
  TrustEvaluationError,
  QuarantineException,
  ReplayAttackError,
  DuplicateSuppressionError,
  ProtocolVersionError,
  ApiRequestError,
  NetworkError,
  ValidationError,
  ErrorContext,
  ErrorSeverity,
  ClassifiedError,
  ErrorReport,
} from "./errors";

// ============================================================================
// Utility Types
// ============================================================================

/**
 * Extract the data type from an ApiResponse.
 */
export type ApiDataType<T extends ApiResponse> = T extends ApiResponse<infer D> ? D : never;

/**
 * Create a successful API response.
 */
export function createSuccessResponse<T>(data: T, meta?: Partial<ResponseMeta>): ApiResponse<T> {
  return {
    status: "success",
    data,
    meta: {
      timestamp: new Date().toISOString(),
      requestId: crypto.randomUUID(),
      processingDurationMs: 0,
      apiVersion: "1.0.0",
      ...meta,
    },
  };
}

/**
 * Create an error API response.
 */
export function createErrorResponse(
  code: FederationErrorCode,
  message: string,
  details?: Record<string, unknown>
): ApiResponse<never> {
  return {
    status: "error",
    error: {
      code,
      message,
      details,
      timestamp: new Date().toISOString(),
    },
    meta: {
      timestamp: new Date().toISOString(),
      requestId: crypto.randomUUID(),
      processingDurationMs: 0,
      apiVersion: "1.0.0",
    },
  };
}

/**
 * Check if an API response was successful.
 */
export function isSuccessfulResponse<T>(response: ApiResponse<T>): response is ApiResponse<T> & { data: T } {
  return response.status === "success" && response.data !== undefined;
}

/**
 * Check if an envelope is valid for federation.
 */
export function isValidEnvelope(envelope: unknown): envelope is FederatedClaimEnvelope {
  return (
    typeof envelope === "object" &&
    envelope !== null &&
    "envelopeId" in envelope &&
    "protocolVersion" in envelope &&
    "sourceNodeId" in envelope &&
    "artifact" in envelope &&
    "signature" in envelope &&
    "trace" in envelope
  );
}

/**
 * Check if a trust decision is "accept".
 */
export function isAccepted(decision: TrustDecision): boolean {
  return decision === "accept";
}

/**
 * Check if a trust decision is "quarantine".
 */
export function isQuarantined(decision: TrustDecision): boolean {
  return decision === "quarantine";
}

/**
 * Check if a trust decision is any form of rejection.
 */
export function isRejected(decision: TrustDecision): boolean {
  return decision === "reject" || decision === "reject_and_flag";
}

/**
 * Check if a trust decision requires flagging.
 */
export function requiresFlagging(decision: TrustDecision): boolean {
  return decision === "reject_and_flag";
}

/**
 * Get trust decision from trust score.
 */
export function getTrustDecisionFromScore(
  score: number,
  thresholds: TrustThresholds = DEFAULT_TRUST_THRESHOLDS
): TrustDecision {
  if (score >= thresholds.acceptMin) {
    return "accept";
  }
  if (score >= thresholds.quarantineMin && score <= thresholds.quarantineMax) {
    return "quarantine";
  }
  return "reject";
}
