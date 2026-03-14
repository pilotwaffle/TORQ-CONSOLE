/**
 * Processing Page
 * Phase 1B - Submit and process inbound federated claims
 *
 * This page provides a full pipeline view:
 * 1. Paste/load envelope
 * 2. Submit to process-inbound-claim endpoint
 * 3. View complete processing results
 */

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { ClaimProcessingPanel } from '@/components/federation'
import { useFederationStore } from '@/app/store'
import { processInboundClaim } from '@/services/api/federationClient'
import { FederationEventLog } from '@/components/federation'
import { clsx } from 'clsx'

export default function ProcessingPage() {
  const [envelopeJson, setEnvelopeJson] = useState('')
  const [error, setError] = useState<string | null>(null)
  const { setProcessingResult, addEvent } = useFederationStore()

  // Process claim mutation
  const processMutation = useMutation({
    mutationFn: async (envelope: unknown) => {
      return processInboundClaim({
        envelope: envelope as any,
        options: {
          skipReplayCheck: false,
          skipDuplicateCheck: false,
          forceAccept: false,
        },
      })
    },
    onSuccess: (result) => {
      setProcessingResult(result)
      setError(null)

      // Add event log
      addEvent({
        type: 'processing_complete',
        message: `Claim processed: ${result.status.toUpperCase()}`,
        timestamp: new Date(),
        envelopeId: result.envelopeId,
      })
    },
    onError: (err: any) => {
      setError(err.message || 'Failed to process claim')
      addEvent({
        type: 'processing_error',
        message: `Processing failed: ${err.message || 'Unknown error'}`,
        timestamp: new Date(),
      })
    },
  })

  // Handle submit
  const handleSubmit = () => {
    setError(null)

    if (!envelopeJson.trim()) {
      setError('Please paste an envelope JSON')
      return
    }

    try {
      const envelope = JSON.parse(envelopeJson)
      processMutation.mutate(envelope)
    } catch (parseErr) {
      setError('Invalid JSON format')
    }
  }

  // Handle clear
  const handleClear = () => {
    setEnvelopeJson('')
    setError(null)
    setProcessingResult(null)
  }

  // Load example envelope
  const loadExample = () => {
    const exampleEnvelope = {
      envelopeId: `env_${Date.now()}`,
      protocolVersion: "1.0.0",
      sourceNodeId: "node_alice",
      targetNodeId: null,
      sentAt: new Date().toISOString(),
      artifact: {
        artifactId: "artifact_001",
        artifactType: "insight",
        title: "Federation Layer Design",
        claimText: "TORQ Federation Layer enables secure cross-node knowledge exchange with cryptographic verification and trust-based decision making.",
        summary: "Design principles for the federation layer",
        confidence: 0.92,
        provenanceScore: 0.88,
        originLayer: "layer4",
        originInsightId: null,
        context: {},
        limitations: [],
        tags: ["federation", "security", "trust"],
      },
      signature: {
        algorithm: "ED25519",
        signerNodeId: "node_alice",
        signatureValue: "sig_" + Math.random().toString(36).substring(2, 66),
        signedAt: new Date().toISOString(),
      },
      trace: {
        messageId: "msg_" + Math.random().toString(36).substring(2, 20),
        hopCount: 0,
        priorNodeIds: [],
        correlationId: null,
      },
    }
    setEnvelopeJson(JSON.stringify(exampleEnvelope, null, 2))
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Claim Processing</h1>
        <p className="text-gray-600 mt-1">
          Submit inbound claims for full pipeline processing
        </p>
      </div>

      {/* Input Section */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Inbound Claim</h2>
          <div className="flex gap-2">
            <button
              onClick={loadExample}
              className="px-3 py-1 text-sm text-torq-600 hover:bg-torq-50 rounded"
            >
              Load Example
            </button>
            {envelopeJson && (
              <button
                onClick={handleClear}
                className="px-3 py-1 text-sm text-gray-600 hover:bg-gray-50 rounded"
              >
                Clear
              </button>
            )}
          </div>
        </div>

        <div className="p-6">
          <textarea
            value={envelopeJson}
            onChange={(e) => setEnvelopeJson(e.target.value)}
            placeholder="Paste federated claim envelope JSON here..."
            className="w-full h-64 p-3 font-mono text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-torq-500 focus:border-transparent"
          />

          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
              {error}
            </div>
          )}

          <div className="mt-4 flex items-center gap-3">
            <button
              onClick={handleSubmit}
              disabled={processMutation.isPending || !envelopeJson.trim()}
              className={clsx(
                "px-4 py-2 rounded-lg font-medium text-white",
                processMutation.isPending || !envelopeJson.trim()
                  ? "bg-gray-300 cursor-not-allowed"
                  : "bg-torq-600 hover:bg-torq-700"
              )}
            >
              {processMutation.isPending ? (
                <>
                  <span className="inline-block animate-spin mr-2">⏳</span>
                  Processing...
                </>
              ) : (
                <>
                  <span className="mr-2">🚀</span>
                  Process Claim
                </>
              )}
            </button>

            {processMutation.data && (
              <span className="text-sm text-green-600">
                ✓ Completed in {processMutation.data.processingDurationMs.toFixed(2)}ms
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Processing Results */}
      {(processMutation.data || processMutation.isPending) && (
        <ClaimProcessingPanel detailed={true} />
      )}

      {/* Event Log */}
      <FederationEventLog maxEvents={50} />
    </div>
  )
}
