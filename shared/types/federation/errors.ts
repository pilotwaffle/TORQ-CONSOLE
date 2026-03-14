/**
 * Federation Error Type Definitions
 *
 * Phase 1B - Error types for federation operations.
 * These define the error contracts used across frontend and backend.
 */

import type { FederationErrorCode } from "./enums";

/**
 * Base federation error.
 */
export interface FederationError {
  /** Error code */
  code: FederationErrorCode;
  /** Human-readable message */
  message: string;
  /** Additional error details */
  details?: Record<string, unknown>;
  /** Original error that caused this */
  cause?: unknown;
  /** Timestamp (ISO 8601) */
  timestamp: string;
}

/**
 * Identity validation error.
 */
export interface IdentityValidationError extends FederationError {
  code: "IDENTITY_VALIDATION_FAILED" | "UNKNOWN_NODE" | "NODE_INACTIVE" | "CREDENTIAL_MISMATCH";
  /** Node ID that failed validation */
  nodeId: string;
  /** Validation step that failed */
  failedStep: "registration" | "active_status" | "credential_match" | "protocol_version";
}

/**
 * Signature verification error.
 */
export interface SignatureVerificationError extends FederationError {
  code:
    | "SIGNATURE_VERIFICATION_FAILED"
    | "UNSUPPORTED_ALGORITHM"
    | "SIGNATURE_EXPIRED"
    | "PAYLET_MISMATCH";
  /** Envelope ID */
  envelopeId: string;
  /** Verification step that failed */
  failedStep: "algorithm" | "signer_match" | "timestamp" | "payload_hash";
}

/**
 * Trust evaluation error.
 */
export interface TrustEvaluationError extends FederationError {
  code: "TRUST_EVALUATION_FAILED";
  /** Node ID */
  nodeId: string;
  /** Envelope ID */
  envelopeId: string;
}

/**
 * Quarantine exception.
 */
export interface QuarantineException extends FederationError {
  code: "QUARANTINE";
  /** Quarantine ID */
  quarantineId: string;
  /** Envelope ID */
  envelopeId: string;
  /** Source node ID */
  nodeId: string;
  /** Quarantine reasons */
  quarantineReasons: string[];
}

/**
 * Replay attack error.
 */
export interface ReplayAttackError extends FederationError {
  code: "REPLAY_ATTACK_DETECTED";
  /** Message ID that was replayed */
  messageId: string;
  /** Original timestamp */
  originalTimestamp: string;
  /** Replay timestamp */
  replayTimestamp: string;
}

/**
 * Duplicate suppression error.
 */
export interface DuplicateSuppressionError extends FederationError {
  code: "DUPLICATE_CLAIM";
  /** Duplicate envelope ID */
  envelopeId: string;
  /** Original envelope timestamp */
  originalTimestamp: string;
}

/**
 * Protocol version error.
 */
export interface ProtocolVersionError extends FederationError {
  code: "UNSUPPORTED_PROTOCOL_VERSION";
  /** Requested protocol version */
  requestedVersion: string;
  /** Supported protocol versions */
  supportedVersions: string[];
}

/**
 * API request error.
 */
export interface ApiRequestError extends FederationError {
  /** HTTP status code */
  statusCode: number;
  /** HTTP status text */
  statusText: string;
  /** Request URL */
  url: string;
  /** HTTP method */
  method: string;
}

/**
 * Network error.
 */
export interface NetworkError extends FederationError {
  /** Whether request timed out */
  isTimeout: boolean;
  /** Whether network is unavailable */
  isNetworkError: boolean;
  /** Retry attempt number */
  retryAttempt?: number;
}

/**
 * Validation error for malformed requests.
 */
export interface ValidationError extends FederationError {
  /** Field that failed validation */
  field: string;
  /** Expected type/format */
  expected: string;
  /** Actual value received */
  received: unknown;
}

/**
 * Error context for logging.
 */
export interface ErrorContext {
  /** Error type */
  type: string;
  /** Component where error occurred */
  component: string;
  /** Operation being performed */
  operation: string;
  /** Additional context */
  context?: Record<string, unknown>;
  /** User-friendly message */
  userMessage?: string;
  /** Whether error is recoverable */
  recoverable: boolean;
}

/**
 * Error severity levels.
 */
export type ErrorSeverity = "low" | "medium" | "high" | "critical";

/**
 * Classified error with severity.
 */
export interface ClassifiedError extends FederationError {
  /** Error severity */
  severity: ErrorSeverity;
  /** Whether to alert user */
  alertUser: boolean;
  /** Whether to log to monitoring */
  logToMonitoring: boolean;
  /** Suggested recovery action */
  recoveryAction?: string;
}

/**
 * Error report for telemetry.
 */
export interface ErrorReport {
  /** Report ID */
  reportId: string;
  /** Error details */
  error: ClassifiedError;
  /** Environment context */
  environment: {
    nodeUrl?: string;
    userAgent: string;
    timestamp: string;
    sessionId?: string;
  };
  /** User context (sanitized) */
  userContext?: {
    nodeId?: string;
    envelopeId?: string;
  };
}
