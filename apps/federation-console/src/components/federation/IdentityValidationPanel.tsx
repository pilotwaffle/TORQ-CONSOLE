/**
 * Identity Validation Panel
 * Phase 1B - Display node identity validation status
 */

import { useFederationStore } from '@/app/store'
import { clsx } from 'clsx'
import type { IdentityValidationResult } from '@torq/federation-contracts'

interface IdentityValidationPanelProps {
  result: IdentityValidationResult | null
  loading?: boolean
}

export function IdentityValidationPanel({ result, loading }: IdentityValidationPanelProps) {
  const { addEvent } = useFederationStore()

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Identity Validation</h3>
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
          <h3 className="text-lg font-semibold text-gray-900">Identity Validation</h3>
          <span className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-sm">
            Pending
          </span>
        </div>
        <div className="text-center py-8 text-gray-500">
          No envelope loaded for validation
        </div>
      </div>
    )
  }

  const isValid = result.isValid
  const statusColor = isValid ? 'text-green-600' : 'text-red-600'
  const statusBg = isValid ? 'bg-green-50' : 'bg-red-50'
  const statusBorder = isValid ? 'border-green-200' : 'border-red-200'
  const statusIcon = isValid ? '✓' : '✗'

  return (
    <div className={clsx(
      'bg-white rounded-lg shadow p-6 border-2',
      statusBorder
    )}>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Identity Validation</h3>
        <div className={clsx(
          'flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium',
          statusBg,
          statusColor
        )}>
          <span>{statusIcon}</span>
          <span>{isValid ? 'Valid' : 'Invalid'}</span>
        </div>
      </div>

      {/* Node Identity Card */}
      <div className="mb-4">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Node Identity</h4>
        <div className="bg-gray-50 rounded-lg p-4 space-y-2">
          <div className="flex justify-between">
            <span className="text-gray-600">Node ID:</span>
            <span className="font-mono text-sm">{result.nodeId}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Registered:</span>
            <span className={clsx(
              'inline-flex items-center gap-1',
              result.isRegistered ? 'text-green-600' : 'text-red-600'
            )}>
              {result.isRegistered ? '✓' : '✗'}
              {result.isRegistered ? 'Yes' : 'No'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Active:</span>
            <span className={clsx(
              'inline-flex items-center gap-1',
              result.isActive ? 'text-green-600' : 'text-red-600'
            )}>
              {result.isActive ? '✓' : '✗'}
              {result.isActive ? 'Yes' : 'No'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Credentials Match:</span>
            <span className={clsx(
              'inline-flex items-center gap-1',
              result.credentialsMatch ? 'text-green-600' : 'text-red-600'
            )}>
              {result.credentialsMatch ? '✓' : '✗'}
              {result.credentialsMatch ? 'Yes' : 'No'}
            </span>
          </div>
        </div>
      </div>

      {/* Validation Reasons */}
      {result.reasons.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">
            {isValid ? 'Warnings' : 'Issues'}
          </h4>
          <ul className="space-y-1">
            {result.reasons.map((reason, index) => (
              <li
                key={index}
                className={clsx(
                  'text-sm px-3 py-2 rounded-lg',
                  isValid ? 'bg-yellow-50 text-yellow-800' : 'bg-red-50 text-red-800'
                )}
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
