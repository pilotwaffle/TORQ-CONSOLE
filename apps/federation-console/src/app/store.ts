/**
 * TORQ Federation Console - Global State Store
 * Phase 1B - Zustand store for federation state management
 */

import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import type {
  FederatedClaimEnvelope,
  IdentityValidationResult,
  SignatureVerificationResult,
  ExtendedTrustDecision,
  NodeTrustProfile,
  NodeListEntry,
  FederationStatus,
  TrustDecision,
  ValidationStatus,
  FederationEventType,
} from '@torq/federation-contracts'

// ============================================================================
// Store State
// ============================================================================

interface FederationState {
  // Current envelope being validated
  currentEnvelope: FederatedClaimEnvelope | null

  // Validation results
  identityResult: IdentityValidationResult | null
  signatureResult: SignatureVerificationResult | null
  trustDecision: ExtendedTrustDecision | null

  // Processing result (from process-inbound-claim)
  processingResult: {
    status: 'accepted' | 'quarantined' | 'rejected'
    envelopeId: string
    claimId: string | null
    sourceNodeId: string
    identityValidation: IdentityValidationResult | null
    signatureVerification: SignatureVerificationResult | null
    trustDecision: ExtendedTrustDecision | null
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
  } | null

  // UI State
  validationStatus: ValidationStatus
  loading: boolean
  error: string | null

  // Node registry
  nodes: NodeListEntry[]
  selectedNode: NodeListEntry | null
  nodeTrustProfile: NodeTrustProfile | null

  // Federation status
  federationStatus: FederationStatus | null

  // Event log
  events: FederationEvent[]

  // Actions
  setCurrentEnvelope: (envelope: FederatedClaimEnvelope) => void
  clearCurrentEnvelope: () => void
  setIdentityResult: (result: IdentityValidationResult) => void
  setSignatureResult: (result: SignatureVerificationResult) => void
  setTrustDecision: (decision: ExtendedTrustDecision) => void
  setProcessingResult: (result: FederationState['processingResult']) => void
  setValidationStatus: (status: ValidationStatus) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  setNodes: (nodes: NodeListEntry[]) => void
  setSelectedNode: (node: NodeListEntry | null) => void
  setNodeTrustProfile: (profile: NodeTrustProfile | null) => void
  setFederationStatus: (status: FederationStatus | null) => void
  addEvent: (event: FederationEvent) => void
  clearEvents: () => void

  // Reset actions
  resetValidation: () => void
  resetAll: () => void

  // Computed
  getDecisionBadgeColor: (decision: TrustDecision) => string
  getValidationStatusBadge: (status: ValidationStatus) => string
}

interface FederationEvent {
  id: string
  type: FederationEventType
  message: string
  timestamp: Date
  envelopeId?: string
  nodeId?: string
}

// ============================================================================
// Create Store
// ============================================================================

export const useFederationStore = create<FederationState>()(
  devtools(
    (set, get) => ({
      // Initial state
      currentEnvelope: null,
      identityResult: null,
      signatureResult: null,
      trustDecision: null,
      processingResult: null,
      validationStatus: 'pending',
      loading: false,
      error: null,
      nodes: [],
      selectedNode: null,
      nodeTrustProfile: null,
      federationStatus: null,
      events: [],

      // Actions
      setCurrentEnvelope: (envelope) => set({ currentEnvelope: envelope }),

      clearCurrentEnvelope: () => set({
        currentEnvelope: null,
        identityResult: null,
        signatureResult: null,
        trustDecision: null,
        processingResult: null,
        validationStatus: 'pending',
        error: null,
      }),

      setIdentityResult: (result) => set({ identityResult: result }),

      setSignatureResult: (result) => set({ signatureResult: result }),

      setTrustDecision: (decision) => set({ trustDecision: decision }),

      setProcessingResult: (result) => set({ processingResult: result }),

      setValidationStatus: (status) => set({ validationStatus: status }),

      setLoading: (loading) => set({ loading }),

      setError: (error) => set({ error }),

      setNodes: (nodes) => set({ nodes }),

      setSelectedNode: (node) => set({ selectedNode: node }),

      setNodeTrustProfile: (profile) => set({ nodeTrustProfile: profile }),

      setFederationStatus: (status) => set({ federationStatus: status }),

      addEvent: (event) => set((state) => ({
        events: [{ ...event, id: `evt_${Date.now()}_${Math.random().toString(36).substr(2, 9)}` }, ...state.events].slice(0, 100),
      })),

      clearEvents: () => set({ events: [] }),

      // Reset actions
      resetValidation: () => set({
        identityResult: null,
        signatureResult: null,
        trustDecision: null,
        processingResult: null,
        validationStatus: 'pending',
        error: null,
      }),

      resetAll: () => set({
        currentEnvelope: null,
        identityResult: null,
        signatureResult: null,
        trustDecision: null,
        processingResult: null,
        validationStatus: 'pending',
        loading: false,
        error: null,
        events: [],
      }),

      // Computed helpers
      getDecisionBadgeColor: (decision: TrustDecision) => {
        const colors: Record<TrustDecision, string> = {
          accept: 'bg-decision-accept text-white',
          quarantine: 'bg-decision-quarantine text-white',
          reject: 'bg-decision-reject text-white',
          reject_and_flag: 'bg-decision-flag text-white',
        }
        return colors[decision]
      },

      getValidationStatusBadge: (status: ValidationStatus) => {
        const badges: Record<ValidationStatus, string> = {
          pending: 'bg-gray-100 text-gray-800',
          validating: 'bg-blue-100 text-blue-800',
          valid: 'bg-green-100 text-green-800',
          invalid: 'bg-red-100 text-red-800',
          quarantined: 'bg-yellow-100 text-yellow-800',
          error: 'bg-red-100 text-red-800',
        }
        return badges[status]
      },
    })),
    {
      name: 'FederationStore',
    }
  )
)
