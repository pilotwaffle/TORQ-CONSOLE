/**
 * Envelope Page
 * Phase 1B - Detailed envelope view with manual input
 */

import { useState } from 'react'
import { useFederationStore } from '@/app/store'
import { evaluateEnvelopeTrust } from '@/services/api/federationClient'
import { EnvelopeViewer } from '@/components/federation'
import { IdentityValidationPanel } from '@/components/federation'
import { SignatureVerificationPanel } from '@/components/federation'
import { TrustDecisionPanel } from '@/components/federation'
import { FederationEventLog } from '@/components/federation'

export default function EnvelopePage() {
  const { setCurrentEnvelope, addEvent } = useFederationStore()
  const [jsonInput, setJsonInput] = useState('')
  const [parseError, setParseError] = useState<string | null>(null)

  const handleLoadEnvelope = () => {
    setParseError(null)

    try {
      const parsed = JSON.parse(jsonInput)

      // Basic validation
      if (!parsed.envelopeId || !parsed.protocolVersion || !parsed.sourceNodeId) {
        throw new Error('Missing required fields: envelopeId, protocolVersion, sourceNodeId')
      }

      setCurrentEnvelope(parsed)
      addEvent({
        type: 'envelope_received',
        message: `Envelope loaded: ${parsed.envelopeId}`,
        timestamp: new Date(),
        envelopeId: parsed.envelopeId,
      })

      setJsonInput('')
    } catch (err) {
      setParseError(err instanceof Error ? err.message : 'Invalid JSON')
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Envelope Viewer</h1>
        <p className="text-gray-600 mt-1">
          Load and validate federated claim envelopes
        </p>
      </div>

      {/* Input Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Load Envelope</h2>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Paste Envelope JSON
          </label>
          <textarea
            value={jsonInput}
            onChange={(e) => setJsonInput(e.target.value)}
            placeholder='{"envelopeId": "env-001", "protocolVersion": "1.0.0", ...}'
            className={clsx(
              'w-full h-40 font-mono text-sm p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-torq-500 focus:border-transparent',
              parseError && 'border-red-300'
            )}
          />
          {parseError && (
            <p className="text-red-600 text-sm mt-2">{parseError}</p>
          )}
        </div>

        <div className="flex gap-3">
          <button
            onClick={handleLoadEnvelope}
            className="px-4 py-2 bg-torq-600 text-white rounded-lg hover:bg-torq-700 transition-colors"
          >
            Load Envelope
          </button>
          <button
            onClick={() => {
              setJsonInput('')
              setParseError(null)
              useFederationStore.getState().clearCurrentEnvelope()
            }}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
          >
            Clear
          </button>
        </div>
      </div>

      {/* Envelope Display */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Envelope Viewer */}
          <EnvelopeViewer />

          {/* Validation Panels */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <IdentityValidationPanel />
            <SignatureVerificationPanel />
            <TrustDecisionPanel />
          </div>
        </div>

        {/* Event Log */}
        <div>
          <FederationEventLog />
        </div>
      </div>
    </div>
  )
}

function clsx(...classes: (string | boolean | undefined | null)[]) {
  return classes.filter(Boolean).join(' ')
}
