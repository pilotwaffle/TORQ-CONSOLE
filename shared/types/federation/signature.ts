/**
 * Signature Verification Type Definitions
 *
 * Phase 1B - Types for artifact signature verification
 * and cryptographic validation.
 */

import type { SignatureAlgorithm } from "./enums";

/**
 * Result of artifact signature verification.
 */
export interface SignatureVerificationResult {
  /** Whether signature is valid */
  isValid: boolean;
  /** Whether algorithm is supported */
  algorithmSupported: boolean;
  /** Whether signer matches source node */
  signerMatchesSource: boolean;
  /** Whether signature timestamp is valid */
  timestampValid: boolean;
  /** Whether payload hash matches */
  payloadHashMatches: boolean;
  /** Verification failure reasons */
  reasons: string[];
  /** Algorithm used */
  algorithm?: SignatureAlgorithm;
  /** Verification timestamp */
  verifiedAt?: string;
}

/**
 * Signature verification request.
 */
export interface VerifySignatureRequest {
  /** Envelope ID containing signature to verify */
  envelopeId: string;
  /** Signature to verify */
  signature: {
    algorithm: SignatureAlgorithm;
    signerNodeId: string;
    signatureValue: string;
    signedAt: string;
  };
  /** Source node ID from envelope */
  sourceNodeId: string;
  /** Artifact payload for hash verification */
  artifactPayload: {
    artifactId: string;
    [key: string]: unknown;
  };
  /** Verification options */
  options?: {
    /** Clock tolerance in seconds */
    clockToleranceSeconds?: number;
    /** Skip timestamp check */
    skipTimestampCheck?: boolean;
    /** Skip hash check */
    skipHashCheck?: boolean;
  };
}

/**
 * Public key information.
 */
export interface PublicKeyInfo {
  /** Key identifier */
  keyId: string;
  /** Node ID that owns the key */
  nodeId: string;
  /** Public key value (Base64) */
  publicKey: string;
  /** Key algorithm */
  algorithm: SignatureAlgorithm;
  /** Key creation timestamp */
  createdAt: string;
  /** Whether key is currently active */
  isActive: boolean;
}

/**
 * Key rotation event.
 */
export interface KeyRotationEvent {
  /** Node ID */
  nodeId: string;
  /** Old key ID */
  oldKeyId: string;
  /** New key ID */
  newKeyId: string;
  /** Rotation timestamp */
  rotatedAt: string;
  /** Reason for rotation */
  reason: string;
}

/**
 * Signature timestamp validation result.
 */
export interface TimestampValidationResult {
  /** Whether timestamp is valid */
  isValid: boolean;
  /** Time difference in seconds */
  diffSeconds: number;
  /** Allowed tolerance */
  toleranceSeconds: number;
  /** Reason if invalid */
  reason?: string;
}

/**
 * Payload hash verification result.
 */
export interface PayloadHashResult {
  /** Whether hash matches */
  matches: boolean;
  /** Computed hash */
  computedHash?: string;
  /** Expected hash from signature */
  expectedHash?: string;
  /** Hash algorithm used */
  algorithm: string;
}

/**
 * Cryptographic verification options.
 */
export interface CryptoVerificationOptions {
  /** Signature algorithm */
  algorithm: SignatureAlgorithm;
  /** Public key for verification */
  publicKey: string;
  /** Signature value */
  signature: string;
  /** Payload to verify */
  payload: string | Uint8Array;
  /** Encoding format */
  encoding?: "base64" | "hex" | "utf8";
}

/**
 * Batch signature verification request.
 */
export interface BatchVerifyRequest {
  /** Envelopes to verify */
  envelopes: Array<{
    envelopeId: string;
    signature: VerifySignatureRequest["signature"];
    sourceNodeId: string;
  }>;
  /** Verification options */
  options?: VerifySignatureRequest["options"];
}

/**
 * Batch signature verification result.
 */
export interface BatchVerifyResult {
  /** Individual results */
  results: Array<{
    envelopeId: string;
    result: SignatureVerificationResult;
  }>;
  /** Summary */
  summary: {
    total: number;
    valid: number;
    invalid: number;
    pending: number;
  };
}
