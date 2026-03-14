/**
 * Claim Processing Panel
 * Phase 1B - Display results of inbound claim processing
 *
 * Shows:
 * - Processing status (accepted/quarantined/rejected)
 * - Identity validation result
 * - Signature verification result
 * - Trust evaluation result
 * - Replay protection result
 * - Duplicate suppression result
 * - Qualification score (when available)
 * - Contradiction count (when available)
 * - Persisted claim ID
 * - Processing duration
 */

import { useFederationStore } from '@/app/store'
import { clsx } from 'clsx'

interface ClaimProcessingPanelProps {
  /** Whether to show full details or compact view */
  detailed?: boolean
}

export function ClaimProcessingPanel({ detailed = true }: ClaimProcessingPanelProps) {
  const {
    identityResult,
    signatureResult,
    trustDecision,
    validationStatus,
    processingResult,
  } = useFederationStore()

  // Get processing status badge
  const getStatusBadge = () => {
    if (processingResult) {
      const badges = {
        accepted: 'bg-green-100 text-green-800',
        quarantined: 'bg-yellow-100 text-yellow-800',
        rejected: 'bg-red-100 text-red-800',
      }
      const badge = badges[processingResult.status as keyof typeof badges] || 'bg-gray-100 text-gray-800'
      return { badge, label: processingResult.status.toUpperCase() }
    }

    const statusBadges: Record<string, string> = {
      pending: 'bg-gray-100 text-gray-800',
      validating: 'bg-blue-100 text-blue-800',
      valid: 'bg-green-100 text-green-800',
      invalid: 'bg-red-100 text-red-800',
      quarantined: 'bg-yellow-100 text-yellow-800',
      error: 'bg-red-100 text-red-800',
    }
    const badge = statusBadges[validationStatus] || statusBadges.pending
    return { badge, label: validationStatus.toUpperCase() }
  }

  const statusBadge = getStatusBadge()

  // Show placeholder when no results
  if (!identityResult && !signatureResult && !trustDecision && !processingResult) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Claim Processing</h3>
        <div className="text-center text-gray-500 py-8">
          <div className="text-4xl mb-2">📋</div>
          <p>Submit a claim to see processing results</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Status Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Claim Processing</h3>
          <span className={clsx('px-3 py-1 rounded-full text-sm font-medium', statusBadge.badge)}>
            {statusBadge.label}
          </span>
        </div>

        {/* Processing Result Summary */}
        {processingResult && (
          <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard
              label="Status"
              value={processingResult.status}
              icon={
                processingResult.status === 'accepted' ? '✅' :
                processingResult.status === 'quarantined' ? '⚠️' : '❌'
              }
            />
            <MetricCard
              label="Processing Time"
              value={`${processingResult.processingDurationMs?.toFixed(2) || 0}ms`}
              icon="⏱️"
            />
            <MetricCard
              label="Claim ID"
              value={processingResult.claimId || 'N/A'}
              icon="🆔"
            />
            <MetricCard
              label="Source Node"
              value={processingResult.sourceNodeId || 'N/A'}
              icon="🔗"
            />
          </div>
        )}
      </div>

      {/* Detailed Results */}
      {detailed && (
        <>
          {/* Identity Validation */}
          {identityResult && (
            <ResultCard
              title="Identity Validation"
              icon="🪪"
              passed={identityResult.isValid}
              details={[
                { label: 'Node ID', value: identityResult.nodeId },
                { label: 'Registered', value: identityResult.isRegistered ? 'Yes' : 'No' },
                { label: 'Active', value: identityResult.isActive ? 'Yes' : 'No' },
                { label: 'Credentials Match', value: identityResult.credentialsMatch ? 'Yes' : 'No' },
              ]}
              reasons={identityResult.reasons}
            />
          )}

          {/* Signature Verification */}
          {signatureResult && (
            <ResultCard
              title="Signature Verification"
              icon="✍️"
              passed={signatureResult.isValid}
              details={[
                { label: 'Algorithm Supported', value: signatureResult.algorithmSupported ? 'Yes' : 'No' },
                { label: 'Signer Matches Source', value: signatureResult.signerMatchesSource ? 'Yes' : 'No' },
                { label: 'Timestamp Valid', value: signatureResult.timestampValid ? 'Yes' : 'No' },
                { label: 'Payload Hash Matches', value: signatureResult.payloadHashMatches ? 'Yes' : 'No' },
              ]}
              reasons={signatureResult.reasons}
            />
          )}

          {/* Trust Decision */}
          {trustDecision && (
            <ResultCard
              title="Trust Evaluation"
              icon="⚖️"
              passed={trustDecision.decision === 'accept'}
              details={[
                { label: 'Decision', value: trustDecision.decision },
                { label: 'Trust Score', value: (trustDecision.nodeTrustScore * 100).toFixed(1) + '%' },
                { label: 'Node ID', value: trustDecision.nodeId },
              ]}
              reasons={trustDecision.reasons}
              decision={trustDecision.decision}
            />
          )}

          {/* Replay Protection */}
          {processingResult?.replayProtection && (
            <ResultCard
              title="Replay Protection"
              icon="🔒"
              passed={!processingResult.replayProtection.isReplay}
              details={processingResult.replayProtection.isReplay ? [
                { label: 'Check Type', value: processingResult.replayProtection.checkType },
                { label: 'First Seen', value: processingResult.replayProtection.firstSeen || 'N/A' },
              ] : [
                { label: 'Status', value: 'No replay detected' },
                { label: 'Check Type', value: processingResult.replayProtection.checkType },
              ]}
              reasons={processingResult.replayProtection.blockedReason ? [processingResult.replayProtection.blockedReason] : []}
            />
          )}

          {/* Duplicate Suppression */}
          {processingResult?.duplicateSuppression && (
            <ResultCard
              title="Duplicate Suppression"
              icon="📑"
              passed={!processingResult.duplicateSuppression.isDuplicate}
              details={processingResult.duplicateSuppression.isDuplicate ? [
                { label: 'Claim ID', value: processingResult.duplicateSuppression.claimId },
                { label: 'Source Count', value: processingResult.duplicateSuppression.sourceCount.toString() },
                { label: 'First Seen', value: processingResult.duplicateSuppression.firstSeen || 'N/A' },
              ] : [
                { label: 'Status', value: 'New claim' },
                { label: 'Claim ID', value: processingResult.duplicateSuppression.claimId },
              ]}
              reasons={processingResult.duplicateSuppression.isDuplicate ? [
                `Previously seen in envelope ${processingResult.duplicateSuppression.existingEnvelopeId}`
              ] : []}
            />
          )}

          {/* Qualification & Contradiction */}
          {processingResult && (processingResult.qualificationScore !== null || processingResult.contradictionCount > 0) && (
            <div className="bg-white rounded-lg shadow p-6">
              <h4 className="text-md font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <span>🧠</span>
                <span>Epistemic Analysis</span>
              </h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-600">Qualification Score</p>
                  <p className="text-2xl font-bold text-torq-600">
                    {processingResult.qualificationScore !== null
                      ? (processingResult.qualificationScore * 100).toFixed(1) + '%'
                      : 'N/A'}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Contradictions Found</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {processingResult.contradictionCount}
                  </p>
                </div>
              </div>
              {processingResult.pluralityStatus && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <p className="text-sm text-gray-600">Plurality Status</p>
                  <p className="text-lg font-semibold text-gray-900">{processingResult.pluralityStatus}</p>
                </div>
              )}
            </div>
          )}

          {/* Persistence */}
          {processingResult?.persistedClaimId && (
            <div className="bg-white rounded-lg shadow p-6">
              <h4 className="text-md font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <span>💾</span>
                <span>Persistence</span>
              </h4>
              <div>
                <p className="text-sm text-gray-600">Persisted Claim ID</p>
                <p className="text-lg font-mono text-gray-900">{processingResult.persistedClaimId}</p>
              </div>
            </div>
          )}

          {/* Audit Trail */}
          {processingResult?.auditEventIds && processingResult.auditEventIds.length > 0 && (
            <div className="bg-white rounded-lg shadow p-6">
              <h4 className="text-md font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <span>📜</span>
                <span>Audit Trail</span>
              </h4>
              <div className="space-y-2">
                {processingResult.auditEventIds.map((eventId) => (
                  <div key={eventId} className="flex items-center gap-2 text-sm">
                    <span className="text-gray-400">•</span>
                    <span className="font-mono text-gray-700">{eventId}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}

interface ResultCardProps {
  title: string
  icon: string
  passed: boolean
  details: Array<{ label: string; value: string }>
  reasons?: string[]
  decision?: string
}

function ResultCard({ title, icon, passed, details, reasons = [], decision }: ResultCardProps) {
  const getDecisionBadge = (decision: string) => {
    const badges: Record<string, string> = {
      accept: 'bg-green-100 text-green-800',
      quarantine: 'bg-yellow-100 text-yellow-800',
      reject: 'bg-red-100 text-red-800',
      reject_and_flag: 'bg-red-100 text-red-800',
    }
    return badges[decision] || 'bg-gray-100 text-gray-800'
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-md font-semibold text-gray-900 flex items-center gap-2">
          <span>{icon}</span>
          <span>{title}</span>
        </h4>
        <div className="flex items-center gap-3">
          {decision && (
            <span className={clsx('px-2 py-1 rounded text-xs font-medium', getDecisionBadge(decision))}>
              {decision}
            </span>
          )}
          <span className={clsx(
            'inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium',
            passed ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          )}>
            <span>{passed ? '●' : '●'}</span>
            {passed ? 'PASSED' : 'FAILED'}
          </span>
        </div>
      </div>

      <div className="space-y-2">
        {details.map((detail) => (
          <div key={detail.label} className="flex justify-between text-sm">
            <span className="text-gray-600">{detail.label}</span>
            <span className={clsx(
              'font-medium',
              passed ? 'text-gray-900' : 'text-red-600'
            )}>
              {detail.value}
            </span>
          </div>
        ))}
      </div>

      {reasons.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-sm text-gray-600 mb-1">Reasons:</p>
          <ul className="text-sm text-gray-700 space-y-1">
            {reasons.map((reason, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-red-500">⚠️</span>
                <span>{reason}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

interface MetricCardProps {
  label: string
  value: string | number
  icon: string
}

function MetricCard({ label, value, icon }: MetricCardProps) {
  return (
    <div className="bg-gray-50 rounded-lg p-3">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-lg">{icon}</span>
        <p className="text-xs text-gray-600">{label}</p>
      </div>
      <p className="text-sm font-semibold text-gray-900 truncate">{value}</p>
    </div>
  )
}
