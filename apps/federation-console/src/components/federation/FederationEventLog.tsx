/**
 * Federation Event Log
 * Phase 1B - Display federation event history
 */

import { clsx } from 'clsx'
import { useFederationStore } from '@/app/store'
import type { FederationEventType } from '@torq/federation-contracts'

interface FederationEventLogProps {
  maxEvents?: number
}

const eventIcons: Record<FederationEventType, string> = {
  envelope_received: '📨',
  identity_validated: '🛡️',
  signature_verified: '🔐',
  trust_evaluated: '⚖️',
  claim_accepted: '✅',
  claim_quarantined: '⚠️',
  claim_rejected: '❌',
  claim_flagged: '🚩',
  replay_detected: '🔄',
  duplicate_suppressed: '📋',
  status_update: '📡',
}

const eventColors: Record<FederationEventType, string> = {
  envelope_received: 'bg-blue-50 text-blue-700',
  identity_validated: 'bg-green-50 text-green-700',
  signature_verified: 'bg-green-50 text-green-700',
  trust_evaluated: 'bg-purple-50 text-purple-700',
  claim_accepted: 'bg-green-50 text-green-700',
  claim_quarantined: 'bg-yellow-50 text-yellow-700',
  claim_rejected: 'bg-red-50 text-red-700',
  claim_flagged: 'bg-red-50 text-red-900',
  replay_detected: 'bg-orange-50 text-orange-700',
  duplicate_suppressed: 'bg-gray-50 text-gray-700',
  status_update: 'bg-gray-50 text-gray-600',
}

export function FederationEventLog({ maxEvents = 50 }: FederationEventLogProps) {
  const { events, clearEvents } = useFederationStore()

  const recentEvents = events.slice(0, maxEvents)

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Event Log</h3>
        {events.length > 0 && (
          <button
            onClick={clearEvents}
            className="text-sm text-torq-600 hover:text-torq-700"
          >
            Clear
          </button>
        )}
      </div>

      {recentEvents.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No events yet
        </div>
      ) : (
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {recentEvents.map((event) => (
            <div
              key={event.id}
              className={clsx(
                'flex items-start gap-3 p-3 rounded-lg text-sm',
                eventColors[event.type]
              )}
            >
              <div className="text-lg">{eventIcons[event.type]}</div>
              <div className="flex-1">
                <div className="font-medium text-gray-900">{event.message}</div>
                <div className="text-xs text-gray-500 mt-1">
                  {new Date(event.timestamp).toLocaleTimeString()}
                  {event.envelopeId && (
                    <span className="ml-2 font-mono text-xs">
                      ({event.envelopeId.slice(0, 12)}...)
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
