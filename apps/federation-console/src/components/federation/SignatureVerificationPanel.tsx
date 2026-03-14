/**
 * Signature Verification Panel
 * Phase 1B - Display signature verification status
 */

import { clsx } from 'clsx'
import type { SignatureVerificationResult } from '@torq/federation-contracts'

interface SignatureVerificationPanelProps {
  result: SignatureVerificationResult | null
  loading?: boolean
}

export function SignatureVerificationPanel({ result, loading }: SignatureVerificationPanelProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Signature Verification</h3>
          <div className="animate-pulse">
            <div className="h-4 w-24 bg-gray-200 rounded" />
          </div>
        </div>
        <div className="space-y-3">
          <div className="h-12 bg-gray-100 rounded animate-pulse" />
          <div className="h-12 bg-gray-100 rounded animate-pulse" />
        </div>
      </div>
    )
  }

  if (!result) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Signature Verification</h3>
          <span className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-sm">
            Pending
          </span>
        </div>
        <div className="text-center py-8 text-gray-500">
          No envelope loaded for verification
        </div>
      </div>
    )
  }

  const checks = [
    { label: 'Algorithm Supported', pass: result.algorithmSupported },
    { label: 'Signer Matches Source', pass: result.signerMatchesSource },
    { label: 'Timestamp Valid', pass: result.timestampValid },
    { label: 'Payload Hash Matches', pass: result.payloadHashMatches },
  ]

  const overallValid = result.isValid
  const statusColor = overallValid ? 'text-green-600' : 'text-red-600'
  const statusBg = overallValid ? 'bg-green-50' : 'bg-red-50'
  const statusBorder = overallValid ? 'border-green-200' : 'border-red-200'
  const statusIcon = overallValid ? '✓' : '✗'

  return (
    <div className={clsx(
      'bg-white rounded-lg shadow p-6 border-2',
      statusBorder
    )}>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Signature Verification</h3>
        <div className={clsx(
          'flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium',
          statusBg,
          statusColor
        )}>
          <span>{statusIcon}</span>
          <span>{overallValid ? 'Valid' : 'Invalid'}</span>
        </div>
      </div>

      {/* Verification Checks */}
      <div className="space-y-2 mb-4">
        {checks.map((check, index) => (
          <div
            key={index}
            className={clsx(
              'flex items-center justify-between p-3 rounded-lg border',
              check.pass
                ? 'bg-green-50 border-green-200'
                : 'bg-red-50 border-red-200'
            )}
          >
            <span className="text-sm font-medium text-gray-700">{check.label}</span>
            <span className={clsx(
              'text-lg',
              check.pass ? 'text-green-600' : 'text-red-600'
            )}>
              {check.pass ? '✓' : '✗'}
            </span>
          </div>
        ))}
      </div>

      {/* Failure Reasons */}
      {!overallValid && result.reasons.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">Issues</h4>
          <ul className="space-y-1">
            {result.reasons.map((reason, index) => (
              <li
                key={index}
                className="text-sm px-3 py-2 rounded-lg bg-red-50 text-red-800"
              >
                • {reason}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
