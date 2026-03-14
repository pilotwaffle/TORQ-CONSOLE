/**
 * Dashboard Page
 * Phase 1B - Main dashboard with quick actions and status
 */

import { useMutation, useQuery } from '@tanstack/react-query'
import { useFederationStore } from '@/app/store'
import {
  getFederationStatus,
  listNodes,
  validateIdentity,
  verifySignature,
  evaluateInboundTrust,
} from '@/services/api/federationClient'
import { EnvelopeViewer } from '@/components/federation'
import { IdentityValidationPanel } from '@/components/federation'
import { SignatureVerificationPanel } from '@/components/federation'
import { TrustDecisionPanel } from '@/components/federation'
import { FederationEventLog } from '@/components/federation'
import { useState } from 'react'

export default function DashboardPage() {
  const {
    currentEnvelope,
    identityResult,
    signatureResult,
    trustDecision,
    addEvent,
  } = useFederationStore()

  // Load federation status
  const { data: status } = useQuery({
    queryKey: ['federation-status'],
    queryFn: getFederationStatus,
    refetchInterval: 5000,
  })

  // Load nodes
  const { data: nodesData } = useQuery({
    queryKey: ['nodes'],
    queryFn: () => listNodes({ limit: 100 }),
    refetchInterval: 10000,
  })

  // Validate identity mutation
  const validateIdentityMutation = useMutation({
    mutationFn: validateIdentity,
    onSuccess: (data) => {
      addEvent({
        type: 'identity_validated',
        message: `Identity validated: ${data.isValid ? 'Valid' : 'Invalid'}`,
        timestamp: new Date(),
        nodeId: data.nodeId,
      })
    },
  })

  // Verify signature mutation
  const verifySignatureMutation = useMutation({
    mutationFn: verifySignature,
    onSuccess: (data) => {
      addEvent({
        type: 'signature_verified',
        message: `Signature ${data.isValid ? 'valid' : 'invalid'}`,
        timestamp: new Date(),
      })
    },
  })

  // Evaluate trust mutation
  const evaluateTrustMutation = useMutation({
    mutationFn: evaluateInboundTrust,
    onSuccess: (data) => {
      addEvent({
        type: 'trust_evaluated',
        message: `Decision: ${data.decision}`,
        timestamp: new Date(),
        envelopeId: data.envelopeId,
      })
    },
  })

  const handleLoadSample = () => {
    const now = new Date()
    const sampleEnvelope = {
      envelopeId: `env-sample-${Date.now()}`,
      protocolVersion: '1.0.0',
      sourceNodeId: 'node-test-trusted',
      targetNodeId: null,
      sentAt: now.toISOString(),
      artifact: {
        artifactId: `artifact-${Date.now()}`,
        artifactType: 'insight',
        title: 'Sample Insight',
        claimText: 'This is a sample federated claim for testing the federation console.',
        confidence: 0.85,
        provenanceScore: 0.9,
        originLayer: 'layer4',
        originInsightId: 'insight-sample',
        context: {},
        limitations: [],
        tags: ['sample', 'test'],
      },
      signature: {
        algorithm: 'ED25519',
        signerNodeId: 'node-test-trusted',
        signatureValue: 'valid-signature-001-7ae71c0a11521b2b-mock',
        signedAt: new Date(now.getTime() - 60000).toISOString(),
      },
      trace: {
        messageId: `msg-${Date.now()}`,
        hopCount: 0,
        priorNodeIds: [],
        correlationId: null,
      },
    }

    useFederationStore.getState().setCurrentEnvelope(sampleEnvelope)
    addEvent({
      type: 'envelope_received',
      message: `Envelope received: ${sampleEnvelope.envelopeId}`,
      timestamp: now,
      envelopeId: sampleEnvelope.envelopeId,
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Federation Dashboard</h1>
        <p className="text-gray-600 mt-1">
          Monitor and validate federated claims between TORQ nodes
        </p>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="flex gap-3">
          <button
            onClick={handleLoadSample}
            className="px-4 py-2 bg-torq-600 text-white rounded-lg hover:bg-torq-700 transition-colors"
          >
            Load Sample Envelope
          </button>
          {currentEnvelope && (
            <button
              onClick={() => evaluateTrustMutation.mutate({ envelope: currentEnvelope })}
              disabled={evaluateTrustMutation.isPending}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
            >
              {evaluateTrustMutation.isPending ? 'Validating...' : 'Run Full Validation'}
            </button>
          )}
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Envelope & Validation Panels */}
        <div className="lg:col-span-2 space-y-6">
          {currentEnvelope && (
            <>
              <EnvelopeViewer envelope={currentEnvelope} />

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <IdentityValidationPanel
                  result={identityResult}
                  loading={validateIdentityMutation.isPending}
                />
                <SignatureVerificationPanel
                  result={signatureResult}
                  loading={verifySignatureMutation.isPending}
                />
                <TrustDecisionPanel
                  decision={trustDecision}
                  loading={evaluateTrustMutation.isPending}
                />
              </div>
            </>
          )}

          {!currentEnvelope && (
            <div className="bg-white rounded-lg shadow p-12 text-center">
              <div className="text-6xl mb-4">📨</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">No Envelope Loaded</h3>
              <p className="text-gray-600 mb-6">
                Load a sample envelope or paste an envelope to begin validation
              </p>
              <button
                onClick={handleLoadSample}
                className="px-6 py-3 bg-torq-600 text-white rounded-lg hover:bg-torq-700 transition-colors"
              >
                Load Sample Envelope
              </button>
            </div>
          )}
        </div>

        {/* Right Column - Status & Events */}
        <div className="space-y-6">
          {/* Federation Status */}
          {status && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Federation Status</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Protocol:</span>
                  <span className="font-mono">{status.protocolVersion}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Connections:</span>
                  <span>{status.activeConnections}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Claims Processed:</span>
                  <span>{status.totalClaimsProcessed}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Accepted:</span>
                  <span className="text-green-600">{status.totalClaimsAccepted}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Quarantined:</span>
                  <span className="text-yellow-600">{status.totalClaimsQuarantined}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Rejected:</span>
                  <span className="text-red-600">{status.totalClaimsRejected}</span>
                </div>
              </div>
            </div>
          )}

          {/* Event Log */}
          <FederationEventLog />
        </div>
      </div>
    </div>
  )
}
