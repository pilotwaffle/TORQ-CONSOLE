/**
 * TORQ Federation Console - Federation API Client
 * Phase 1B - HTTP client for federation backend endpoints
 */

import type {
  ValidateIdentityApiRequest,
  ValidateIdentityApiResponse,
  VerifySignatureApiRequest,
  VerifySignatureApiResponse,
  EvaluateInboundTrustApiRequest,
  EvaluateInboundTrustApiResponse,
  GetNodeTrustProfileApiRequest,
  GetNodeTrustProfileApiResponse,
  ListNodesApiRequest,
  ListNodesApiResponse,
  RegisterNodeApiRequest,
  RegisterNodeApiResponse,
  GetFederationStatusApiResponse,
  FederationStatus,
  ProcessInboundClaimApiRequest,
  ProcessInboundClaimApiResponse,
} from '@torq/federation-contracts'

// ============================================================================
// Processing Result Types (inline for now, will move to contracts)
// ============================================================================

export interface ClaimProcessingResult {
  status: 'accepted' | 'quarantined' | 'rejected'
  envelopeId: string
  claimId: string | null
  sourceNodeId: string
  identityValidation: {
    isValid: boolean
    nodeId: string
    reasons: string[]
    isRegistered: boolean
    isActive: boolean
    credentialsMatch: boolean
  } | null
  signatureVerification: {
    isValid: boolean
    algorithmSupported: boolean
    signerMatchesSource: boolean
    timestampValid: boolean
    payloadHashMatches: boolean
    reasons: string[]
  } | null
  trustDecision: {
    decision: 'accept' | 'quarantine' | 'reject' | 'reject_and_flag'
    reasons: string[]
    nodeTrustScore: number
    identityValid: boolean
    signatureValid: boolean
    nodeId: string
    envelopeId: string
  } | null
  replayProtection: {
    isReplay: boolean
    envelopeId: string
    checkType: string
    firstSeen: string | null
    blockedReason: string | null
  } | null
  duplicateSuppression: {
    isDuplicate: boolean
    claimId: string
    envelopeId: string
    existingEnvelopeId: string | null
    firstSeen: string | null
    sourceCount: number
    sources: string[]
  } | null
  persistedClaimId: string | null
  qualificationScore: number | null
  contradictionCount: number
  pluralityStatus: string | null
  auditEventIds: string[]
  processingStartedAt: string
  processingCompletedAt: string
  processingDurationMs: number
  rejectionReason: string | null
  quarantineReasons: string[]
}

// ============================================================================
// API Configuration
// ============================================================================

const API_BASE_URL = '/api/l12/federation'

// ============================================================================
// Error Handling
// ============================================================================

class FederationApiError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode: number,
    public details?: unknown
  ) {
    super(message)
    this.name = 'FederationApiError'
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    const error = data.error || {}

    throw new FederationApiError(
      error.message || 'API request failed',
      error.code || 'UNKNOWN_ERROR',
      response.status,
      error.details
    )
  }

  return response.json().then((data) => data.data)
}

// ============================================================================
// API Client Functions
// ============================================================================

/**
 * Validate a node's identity credentials.
 */
export async function validateIdentity(request: ValidateIdentityApiRequest): Promise<ValidateIdentityApiResponse['data']> {
  const response = await fetch(`${API_BASE_URL}/validate-identity`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  return handleResponse<ValidateIdentityApiResponse['data']>(response)
}

/**
 * Verify the signature on a federated claim envelope.
 */
export async function verifySignature(request: VerifySignatureApiRequest): Promise<VerifySignatureApiResponse['data']> {
  const response = await fetch(`${API_BASE_URL}/verify-signature`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  return handleResponse<VerifySignatureApiResponse['data']>(response)
}

/**
 * Evaluate whether to accept, quarantine, or reject an inbound claim.
 */
export async function evaluateInboundTrust(request: EvaluateInboundTrustApiRequest): Promise<EvaluateInboundTrustApiResponse['data']> {
  const response = await fetch(`${API_BASE_URL}/evaluate-inbound-trust`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  return handleResponse<EvaluateInboundTrustApiResponse['data']>(response)
}

/**
 * Register a new node in the federation.
 */
export async function registerNode(request: RegisterNodeApiRequest): Promise<RegisterNodeApiResponse['data']> {
  const response = await fetch(`${API_BASE_URL}/nodes/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  return handleResponse<RegisterNodeApiResponse['data']>(response)
}

/**
 * Get the trust profile for a specific node.
 */
export async function getNodeTrustProfile(nodeId: string): Promise<GetNodeTrustProfileApiResponse['data']> {
  const response = await fetch(`${API_BASE_URL}/nodes/${encodeURIComponent(nodeId)}/trust-profile`)

  return handleResponse<GetNodeTrustProfileApiResponse['data']>(response)
}

/**
 * List registered nodes with optional filtering.
 */
export async function listNodes(request?: ListNodesApiRequest): Promise<ListNodesApiResponse['data']> {
  const params = new URLSearchParams()

  if (request?.status) {
    params.append('status', request.status)
  }
  if (request?.trustTier) {
    params.append('trust_tier', request.trustTier)
  }
  if (request?.offset !== undefined) {
    params.append('offset', request.offset.toString())
  }
  if (request?.limit !== undefined) {
    params.append('limit', request.limit.toString())
  }

  const query = params.toString()
  const response = await fetch(`${API_BASE_URL}/nodes${query ? `?${query}` : ''}`)

  return handleResponse<ListNodesApiResponse['data']>(response)
}

/**
 * Get the current federation status.
 */
export async function getFederationStatus(): Promise<GetFederationStatusApiResponse['data']> {
  const response = await fetch(`${API_BASE_URL}/status`)

  return handleResponse<GetFederationStatusApiResponse['data']>(response)
}

/**
 * Process an inbound federated claim through the full pipeline.
 *
 * This is the authoritative endpoint for all inbound federation claims.
 * It orchestrates identity validation, signature verification, replay
 * protection, duplicate suppression, trust evaluation, and more.
 */
export async function processInboundClaim(
  request: ProcessInboundClaimApiRequest
): Promise<ClaimProcessingResult> {
  const response = await fetch(`${API_BASE_URL}/process-inbound-claim`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  return handleResponse<ClaimProcessingResult>(response)
}

/**
 * Get processor statistics.
 */
export async function getProcessorStatistics(): Promise<{
  totalProcessed: number
  acceptedCount: number
  quarantinedCount: number
  rejectedCount: number
  acceptRate: number
  uptimeSeconds: number
  processorStartedAt: string
  replayProtection: {
    totalChecked: number
    replaysDetected: number
    trackedEnvelopeIds: number
  } | null
  duplicateSuppression: {
    totalChecked: number
    duplicatesDetected: number
    uniqueClaimsProcessed: number
    trackedClaims: number
  } | null
}> {
  const response = await fetch(`${API_BASE_URL}/processor/statistics`)

  return handleResponse(response)
}

/**
 * Publish a federated claim to a target node.
 */
export async function publishClaim(request: {
  draft: {
    artifactId?: string
    artifactType: string
    title: string
    claimText: string
    summary?: string
    confidence: number
    provenanceScore?: number
    originLayer: string
    originInsightId?: string
    context?: Record<string, unknown>
    limitations?: string[]
    tags?: string[]
  }
  targetNodeId: string
  options?: {
    signatureAlgorithm?: string
    includeTrace?: boolean
    dispatchImmediately?: boolean
  }
}): Promise<{
  success: boolean
  envelopeId: string
  correlationId: string
  messageId: string
  publishedAt: string
  targetNodeId: string
  signatureStatus: string
  dispatchStatus: string
  errorMessage: string | null
  envelope: unknown
}> {
  const response = await fetch(`${API_BASE_URL}/publish-claim`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  return handleResponse(response)
}

/**
 * Get exchange trace by correlation ID.
 */
export async function getExchangeTrace(correlationId: string): Promise<{
  correlationId: string
  envelopeId: string
  sourceNodeId: string
  targetNodeId: string | null
  createdAt: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  finalDisposition: 'accepted' | 'quarantined' | 'rejected' | null
  eventCount: number
  events: Array<{
    eventId: string
    eventType: string
    correlationId: string
    envelopeId: string
    nodeId: string
    timestamp: string
    sourceNodeId: string | null
    targetNodeId: string | null
    status: string | null
    details: Record<string, unknown>
    errorMessage: string | null
  }>
}> {
  const response = await fetch(`${API_BASE_URL}/exchange-trace/${encodeURIComponent(correlationId)}`)

  return handleResponse(response)
}

// ============================================================================
// Convenience Functions
// ============================================================================

/**
 * Validate identity with simplified parameters.
 */
export async function validateNodeIdentity(
  nodeId: string,
  keyId?: string,
  publicKey?: string
): Promise<ValidateIdentityApiResponse['data']> {
  return validateIdentity({
    nodeId,
    credentials: keyId && publicKey ? { keyId, publicKey } : undefined,
  })
}

/**
 * Verify signature for an envelope.
 */
export async function verifyEnvelopeSignature(envelope: {
  envelopeId: string
  protocolVersion: string
  sourceNodeId: string
  targetNodeId?: string | null
  sentAt: string
  artifact: unknown
  signature: {
    algorithm: string
    signerNodeId: string
    signatureValue: string
    signedAt: string
  }
  trace: unknown
}): Promise<VerifySignatureApiResponse['data']> {
  return verifySignature({ envelope } as VerifySignatureApiRequest)
}

/**
 * Evaluate trust for an envelope (orchestrates full validation).
 */
export async function evaluateEnvelopeTrust(envelope: {
  envelopeId: string
  protocolVersion: string
  sourceNodeId: string
  targetNodeId?: string | null
  sentAt: string
  artifact: unknown
  signature: unknown
  trace: unknown
}): Promise<EvaluateInboundTrustApiResponse['data']> {
  return evaluateInboundTrust({ envelope } as EvaluateInboundTrustApiRequest)
}
