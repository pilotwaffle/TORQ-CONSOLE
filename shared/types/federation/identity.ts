/**
 * Identity and Trust Type Definitions
 *
 * Phase 1B - Types for node identity validation, trust profiles,
 * and trust-based decision making.
 */

import type { TrustTier, NodeStatus } from "./enums";

/**
 * Result of node identity validation.
 */
export interface IdentityValidationResult {
  /** Whether identity is valid */
  isValid: boolean;
  /** Node ID that was validated */
  nodeId: string;
  /** Validation failure reasons */
  reasons: string[];
  /** Whether node is registered */
  isRegistered: boolean;
  /** Whether node is active */
  isActive: boolean;
  /** Whether credentials match registration */
  credentialsMatch: boolean;
}

/**
 * Node trust profile for tracking reputation.
 */
export interface NodeTrustProfile {
  /** Node identifier */
  nodeId: string;
  /** Baseline trust score (0.0 - 1.0) */
  baselineTrustScore: number;
  /** Trust tier classification */
  trustTier: TrustTier;
  /** Count of successful exchanges */
  successfulExchanges: number;
  /** Count of failed exchanges */
  failedExchanges: number;
  /** Last profile update (ISO 8601) */
  lastUpdated: string;
  /** Whether node is in trusted set */
  isTrusted: boolean;
  /** Whether node is quarantined */
  isQuarantined: boolean;
}

/**
 * Computed properties from trust profile.
 */
export interface NodeTrustMetrics {
  /** Total number of exchanges */
  totalExchanges: number;
  /** Success rate (0.0 - 1.0) */
  successRate: number;
  /** Trust trend direction */
  trend: "improving" | "stable" | "declining";
}

/**
 * Trust baseline query result.
 */
export interface NodeTrustBaseline {
  /** Node trust profile */
  profile: NodeTrustProfile;
  /** Computed metrics */
  metrics: NodeTrustMetrics;
  /** Whether baseline is established */
  isEstablished: boolean;
}

/**
 * Node registry entry.
 */
export interface NodeRegistryEntry {
  /** Node credentials */
  credentials: {
    nodeId: string;
    keyId: string;
    publicKey: string;
  };
  /** Current status */
  status: NodeStatus;
  /** Registration timestamp */
  registeredAt: string;
  /** Last activity */
  lastSeen: string;
  /** Trust tier */
  trustTier: TrustTier;
}

/**
 * Node identity for validation requests.
 */
export interface NodeIdentity {
  /** Node ID */
  nodeId: string;
  /** Optional key ID for credential verification */
  keyId?: string;
  /** Optional public key for signature verification */
  publicKey?: string;
}

/**
 * Identity validation request.
 */
export interface ValidateIdentityRequest {
  /** Node ID to validate */
  nodeId: string;
  /** Presented credentials (optional for lookup-based validation) */
  credentials?: {
    keyId: string;
    publicKey: string;
  };
  /** Validation options */
  options?: {
    /** Check if node is active */
    requireActive?: boolean;
    /** Verify credentials match registration */
    verifyCredentials?: boolean;
  };
}

/**
 * Node registration request.
 */
export interface RegisterNodeRequest {
  /** Node credentials */
  credentials: {
    nodeId: string;
    keyId: string;
    publicKey: string;
  };
  /** Initial trust tier */
  trustTier?: TrustTier;
  /** Whether to start as active */
  isActive?: boolean;
}

/**
 * Bulk node lookup result.
 */
export interface NodeLookupResult {
  /** Found nodes */
  found: NodeRegistryEntry[];
  /** Missing node IDs */
  missing: string[];
}

/**
 * Trust score adjustment.
 */
export interface TrustScoreAdjustment {
  /** Node ID */
  nodeId: string;
  /** Score delta (positive or negative) */
  delta: number;
  /** Reason for adjustment */
  reason: string;
  /** Adjustment timestamp */
  timestamp: string;
  /** Exchange that triggered adjustment */
  exchangeId?: string;
}
