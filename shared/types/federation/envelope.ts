/**
 * Federation Envelope Type Definitions
 *
 * Phase 1B - Core data structures for federated claim envelopes.
 * These types define the wire format for exchanging artifacts between nodes.
 */

import type { ArtifactType, OriginLayer, SignatureAlgorithm, ProtocolVersion } from "./enums";

/**
 * Federation trace information for message routing.
 */
export interface FederationTrace {
  /** Unique message identifier */
  messageId: string;
  /** Number of hops this message has taken */
  hopCount: number;
  /** IDs of prior nodes in the routing path */
  priorNodeIds: string[];
  /** Optional correlation ID for request/response tracking */
  correlationId?: string;
}

/**
 * Cryptographic signature for an artifact.
 */
export interface ArtifactSignature {
  /** Signature algorithm used */
  algorithm: SignatureAlgorithm;
  /** Node ID that created the signature */
  signerNodeId: string;
  /** Base64-encoded signature value */
  signatureValue: string;
  /** When the signature was created (ISO 8601) */
  signedAt: string;
}

/**
 * The core artifact payload being federated.
 */
export interface FederatedArtifactPayload {
  /** Unique identifier for this artifact */
  artifactId: string;
  /** Type of artifact */
  artifactType: ArtifactType;
  /** Human-readable title */
  title: string;
  /** The core claim or assertion */
  claimText: string;
  /** Optional summary of the claim */
  summary?: string;
  /** Confidence score (0.0 - 1.0) */
  confidence: number;
  /** Provenance reliability score (0.0 - 1.0) */
  provenanceScore?: number;
  /** Origin layer within source node */
  originLayer: OriginLayer;
  /** Original insight ID if applicable */
  originInsightId?: string;
  /** Additional context metadata */
  context: Record<string, unknown>;
  /** Known limitations */
  limitations: string[];
  /** Categorization tags */
  tags: string[];
}

/**
 * Complete envelope for a federated claim.
 */
export interface FederatedClaimEnvelope {
  /** Unique identifier for this envelope */
  envelopeId: string;
  /** Federation protocol version */
  protocolVersion: ProtocolVersion;
  /** Node ID sending this claim */
  sourceNodeId: string;
  /** Target node ID (null for broadcast) */
  targetNodeId?: string | null;
  /** When the envelope was sent (ISO 8601) */
  sentAt: string;
  /** The artifact payload */
  artifact: FederatedArtifactPayload;
  /** Artifact signature */
  signature: ArtifactSignature;
  /** Federation trace information */
  trace: FederationTrace;
}

/**
 * Node registration credentials.
 */
export interface NodeCredentials {
  /** Unique node identifier */
  nodeId: string;
  /** Key identifier */
  keyId: string;
  /** Public key for signature verification (Base64) */
  publicKey: string;
  /** Trust tier classification */
  trustTier?: string;
  /** Whether the node is currently active */
  isActive: boolean;
  /** When the node was registered (ISO 8601) */
  registeredAt?: string;
  /** Last activity timestamp (ISO 8601) */
  lastSeen?: string;
}

/**
 * Envelope creation options.
 */
export interface CreateEnvelopeOptions {
  /** Source node ID (defaults to current node) */
  sourceNodeId?: string;
  /** Target node ID (null for broadcast) */
  targetNodeId?: string | null;
  /** Include signature? */
  includeSignature?: boolean;
}

/**
 * Envelope validation options.
 */
export interface ValidateEnvelopeOptions {
  /** Strict mode - fail on warnings */
  strict?: boolean;
  /** Skip signature verification */
  skipSignatureCheck?: boolean;
  /** Skip protocol version check */
  skipProtocolCheck?: boolean;
  /** Custom clock tolerance in seconds */
  clockToleranceSeconds?: number;
}
