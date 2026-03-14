/**
 * Trust Decision Panel
 * Phase 1B - Display trust decision and related actions
 */

import { clsx } from 'clsx'
import { useFederationStore } from '@/app/store'
import type { ExtendedTrustDecision } from '@torq/federation-contracts'

interface TrustDecisionPanelProps {
  decision: ExtendedTrustDecision | null
  loading?: boolean
}

function DecisionBadge({ decision }: { decision: ExtendedTrustDecision['decision'] }) {
  const config = {
    accept: {
      icon: '✓',
      label: 'Accept',
      color: 'bg-decision-accept',
      textColor: 'text-white',
    },
    quarantine: {
      icon: '⚠',
      label: 'Quarantine',
      color: 'bg-decision-quarantine',
      textColor: 'text-white',
    },
    reject: {
      icon: '✗',
      label: 'Reject',
      color: 'bg-decision-reject',
      textColor: 'text-white',
    },
    reject_and_flag: {
      icon: '🚩',
      label: 'Reject & Flag',
      color: 'bg-decision-flag',
      textColor: 'text-white',
    },
  }[decision]

  if (!config) return null

  return (
    <div className={clsx(
      'inline-flex items-center gap-2 px-4 py-2 rounded-lg font-semibold',
      config.color,
      config.textColor
    )}>
      <span className="text-lg">{config.icon}</span>
      <span>{config.label}</span>
    </div>
  )
}

export function TrustDecisionPanel({ decision, loading }: TrustDecisionPanelProps) {
  const { addEvent } = useFederationStore()

  const handleReevaluate = () => {
    addEvent({
      type: 'status_update',
      message: 'Re-evaluation requested',
      timestamp: new Date(),
    })
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Trust Decision</h3>
          <div className="animate-pulse">
            <div className="h-4 w-24 bg-gray-200 rounded" />
          </div>
        </div>
        <div className="text-center py-8 text-gray-500">
          Evaluating trust...
        </div>
      </div>
    )
  }

  if (!decision) {
    return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Trust Decision</h3>
        <span className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-sm">
          Pending
        </span>
      </div>
      <div className="text-center py-8 text-gray-500">
        No envelope loaded for evaluation
      </div>
    </div>
  )
  }

  const trustScorePercent = Math.round(decision.nodeTrustScore * 100)

  return (
    <div className={clsx(
      'bg-white rounded-lg shadow p-6 border-2',
      decision.shouldProceed ? 'border-green-200' :
        decision.requiresQuarantine ? 'border-yellow-200' :
        'border-red-200'
    )}>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Trust Decision</h3>
        <DecisionBadge decision={decision.decision} />
      </div>

      {/* Trust Score */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Node Trust Score</span>
          <span className="text-2xl font-bold text-gray-900">
            {trustScorePercent}%
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className={clsx(
              'h-3 rounded-full transition-all',
              decision.nodeTrustScore >= 0.75 ? 'bg-green-500' :
              decision.nodeTrustScore >= 0.45 ? 'bg-yellow-500' :
              'bg-red-500'
            )}
            style={{ width: `${trustScorePercent}%` }}
          />
        </div>
      </div>

      {/* Validation Summary */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-gray-50 rounded-lg p-4 text-center">
          <div className="text-2xl mb-1">
            {decision.identityValid ? '✓' : '✗'}
          </div>
          <div className="text-xs text-gray-600">Identity</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-4 text-center">
          <div className="text-2xl mb-1">
            {decision.signatureValid ? '✓' : '✗'}
          </div>
          <div className="text-xs text-gray-600">Signature</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-4 text-center">
          <div className="text-2xl mb-1">
            {decision.shouldProceed ? '→' : '⛔'}
          </div>
          <div className="text-xs text-gray-600">Proceed</div>
        </div>
      </div>

      {/* Reasons */}
      {decision.reasons.length > 0 && (
        <div className="mb-6">
          <h4 className="text-sm font-medium text-gray-700 mb-2">
            {decision.shouldProceed ? 'Reasons' : 'Issues'}
          </h4>
          <ul className="space-y-1">
            {decision.reasons.map((reason, index) => (
              <li
                key={index}
                className={clsx(
                  'text-sm px-3 py-2 rounded-lg',
                  decision.shouldProceed ? 'bg-green-50 text-green-800' :
                  decision.requiresQuarantine ? 'bg-yellow-50 text-yellow-800' :
                  'bg-red-50 text-red-800'
                )}
              >
                • {reason}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-3">
        {decision.requiresQuarantine && (
          <button
            onClick={handleRevaluate}
            className="px-4 py-2 bg-torq-600 text-white rounded-lg hover:bg-torq-700 transition-colors"
          >
            Review Quarantine
          </button>
        )}
        {decision.isRejection && decision.requiresFlagging && (
          <button
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            View Incident Report
          </button>
        )}
      </div>
    </div>
  )
}
