/**
 * Validation Page
 * Phase 1B - Standalone validation page for detailed analysis
 */

import { useFederationStore } from '@/app/store'
import { EnvelopeViewer } from '@/components/federation'
import { IdentityValidationPanel } from '@/components/federation'
import { SignatureVerificationPanel } from '@/components/federation'
import { TrustDecisionPanel } from '@/components/federation'
import { FederationEventLog } from '@/components/federation'

export default function ValidationPage() {
  const { currentEnvelope } = useFederationStore()

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Validation Center</h1>
        <p className="text-gray-600 mt-1">
          Detailed identity, signature, and trust validation for federated claims
        </p>
      </div>

      {/* Validation Content */}
      {currentEnvelope ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Envelope Display */}
          <div className="space-y-6">
            <EnvelopeViewer envelope={currentEnvelope} />
          </div>

          {/* Validation Panels */}
          <div className="space-y-6">
            <IdentityValidationPanel />
            <SignatureVerificationPanel />
            <TrustDecisionPanel />
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <div className="text-6xl mb-4">📋</div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No Envelope to Validate</h3>
          <p className="text-gray-600 mb-6">
            Load an envelope from the Dashboard or Envelope page
          </p>
          <a
            href="/envelope"
            className="inline-block px-6 py-3 bg-torq-600 text-white rounded-lg hover:bg-torq-700 transition-colors"
          >
            Go to Envelope Page
          </a>
        </div>
      )}

      {/* Event Log (full width) */}
      <FederationEventLog maxEvents={100} />
    </div>
  )
}
