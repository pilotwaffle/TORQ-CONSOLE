/**
 * Federation Exchange Simulator Page
 * Phase 1B - UI for two-node federation exchange testing
 *
 * Features:
 * - Source/target node selection
 * - Claim builder
 * - One-click exchange execution
 * - Real-time timeline visualization
 * - Audit trace viewer
 * - Scenario presets (trusted, low-trust, replay, duplicate)
 */

import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { publishClaim, getExchangeTrace } from '@/services/api/federationClient'
import { useFederationStore } from '@/app/store'
import { FederationEventLog } from '@/components/federation'
import { clsx } from 'clsx'

type ScenarioType = 'trusted_exchange' | 'low_trust_sender' | 'replay_attack' | 'duplicate_content' | 'contradiction'

interface ScenarioPreset {
  name: ScenarioType
  label: string
  description: string
  expectedOutcome: 'accepted' | 'quarantined' | 'rejected'
  icon: string
}

const SCENARIO_PRESETS: ScenarioPreset[] = [
  {
    name: 'trusted_exchange',
    label: 'Trusted Exchange',
    description: 'Trusted node A sends valid claim to trusted node B',
    expectedOutcome: 'accepted',
    icon: '✅',
  },
  {
    name: 'low_trust_sender',
    label: 'Low Trust Sender',
    description: 'Low-trust node sends claim to trusted node',
    expectedOutcome: 'quarantined',
    icon: '⚠️',
  },
  {
    name: 'replay_attack',
    label: 'Replay Attack',
    description: 'Same envelope resent (should be blocked)',
    expectedOutcome: 'rejected',
    icon: '🔁',
  },
  {
    name: 'duplicate_content',
    label: 'Duplicate Content',
    description: 'Same claim in different envelope (tracked)',
    expectedOutcome: 'accepted',
    icon: '📑',
  },
  {
    name: 'contradiction',
    label: 'Contradiction',
    description: 'Contradictory claim to existing knowledge',
    expectedOutcome: 'accepted',
    icon: '⚔️',
  },
]

interface TimelineEvent {
  id: string
  type: string
  label: string
  timestamp: Date
  status: 'pending' | 'success' | 'error' | 'info'
  details?: Record<string, unknown>
}

export default function ExchangeSimulatorPage() {
  const [selectedScenario, setSelectedScenario] = useState<ScenarioType>('trusted_exchange')
  const [sourceNodeId, setSourceNodeId] = useState('node_alice')
  const [targetNodeId, setTargetNodeId] = useState('node_bob')
  const [claimTitle, setClaimTitle] = useState('Federation Layer Design')
  const [claimText, setClaimText] = useState('TORQ Federation Layer enables secure cross-node knowledge exchange.')
  const [claimConfidence, setClaimConfidence] = useState(0.92)
  const [timeline, setTimeline] = useState<TimelineEvent[]>([])
  const [correlationId, setCorrelationId] = useState<string | null>(null)

  const { addEvent } = useFederationStore()

  // Publish mutation
  const publishMutation = useMutation({
    mutationFn: async () => {
      const result = await publishClaim({
        draft: {
          artifactType: 'insight',
          title: claimTitle,
          claimText: claimText,
          summary: 'Federation design principles',
          confidence: claimConfidence,
          provenanceScore: 0.88,
          originLayer: 'layer4',
          tags: ['federation', 'security'],
        },
        targetNodeId: targetNodeId,
        options: {
          signatureAlgorithm: 'ED25519',
          includeTrace: true,
          dispatchImmediately: true,
        },
      })

      return result
    },
    onSuccess: async (data) => {
      setCorrelationId(data.correlationId)
      addEvent({
        type: 'claim_published',
        message: `Claim published: ${data.envelopeId} → ${data.targetNodeId}`,
        timestamp: new Date(),
        envelopeId: data.envelopeId,
      })

      // Add timeline events
      setTimeline([
        {
          id: '1',
          type: 'publish',
          label: 'Claim Published',
          timestamp: new Date(),
          status: 'success',
          details: {
            envelopeId: data.envelopeId,
            targetNodeId: data.targetNodeId,
          },
        },
        {
          id: '2',
          type: 'dispatch',
          label: 'Dispatched to Target',
          timestamp: new Date(),
          status: 'success',
          details: {
            correlationId: data.correlationId,
          },
        },
      ])

      // Poll for exchange trace updates
      if (data.correlationId) {
        await pollExchangeTrace(data.correlationId)
      }
    },
    onError: (err: any) => {
      addEvent({
        type: 'publish_error',
        message: `Publish failed: ${err.message || 'Unknown error'}`,
        timestamp: new Date(),
      })
      setTimeline([
        {
          id: 'error',
          type: 'error',
          label: 'Publish Failed',
          timestamp: new Date(),
          status: 'error',
          details: { error: err.message },
        },
      ])
    },
  })

  // Poll exchange trace
  const pollExchangeTrace = async (corrId: string, attempts = 0) => {
    if (attempts > 5) return

    try {
      const trace = await getExchangeTrace(corrId)

      // Update timeline from trace events
      const newTimeline: TimelineEvent[] = trace.events.map((evt, idx) => ({
        id: `trace-${idx}`,
        type: evt.eventType,
        label: formatEventType(evt.eventType),
        timestamp: new Date(evt.timestamp),
        status: getEventStatus(evt.eventType, evt.status),
        details: evt.details,
      }))

      setTimeline(newTimeline)

      // If still in progress, poll again
      if (trace.status === 'in_progress' && attempts < 5) {
        setTimeout(() => pollExchangeTrace(corrId, attempts + 1), 1000)
      }
    } catch (err) {
      console.error('Failed to poll exchange trace:', err)
    }
  }

  // Handle run scenario
  const handleRunScenario = () => {
    setTimeline([])
    setCorrelationId(null)
    publishMutation.reset()
    publishMutation.mutate()
  }

  // Handle load preset
  const handleLoadPreset = (preset: ScenarioPreset) => {
    setSelectedScenario(preset.name)

    // Set nodes based on scenario
    if (preset.name === 'low_trust_sender') {
      setSourceNodeId('node_charlie')
      setTargetNodeId('node_bob')
      setClaimTitle('Unverified Insight from Unknown Node')
      setClaimText('This claim requires additional verification.')
      setClaimConfidence(0.5)
    } else if (preset.name === 'replay_attack') {
      setSourceNodeId('node_alice')
      setTargetNodeId('node_bob')
      setClaimTitle('Replay Test Claim')
      setClaimText('Testing replay protection mechanism.')
      setClaimConfidence(0.9)
    } else if (preset.name === 'duplicate_content') {
      setSourceNodeId('node_alice')
      setTargetNodeId('node_bob')
      setClaimTitle('Duplicate Content Test')
      setClaimText('TORQ Federation Layer enables secure cross-node knowledge exchange.')
      setClaimConfidence(0.92)
    } else if (preset.name === 'contradiction') {
      setSourceNodeId('node_alice')
      setTargetNodeId('node_bob')
      setClaimTitle('Contradictory Claim')
      setClaimText('TORQ Federation Layer is NOT secure for cross-node exchange.')
      setClaimConfidence(0.7)
    } else {
      // Default trusted exchange
      setSourceNodeId('node_alice')
      setTargetNodeId('node_bob')
      setClaimTitle('Federation Layer Design')
      setClaimText('TORQ Federation Layer enables secure cross-node knowledge exchange.')
      setClaimConfidence(0.92)
    }
  }

  const formatEventType = (type: string) => {
    return type.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
  }

  const getEventStatus = (eventType: string, status: string | null) => {
    if (eventType === 'FAILED' || eventType === 'REJECTED') return 'error'
    if (eventType === 'ACCEPTED' || eventType === 'COMPLETED') return 'success'
    if (eventType === 'QUARANTINED') return 'info'
    return 'pending'
  }

  const currentScenario = SCENARIO_PRESETS.find(s => s.name === selectedScenario)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Federation Exchange Simulator</h1>
        <p className="text-gray-600 mt-1">
          Simulate two-node federated claim exchange with real validation
        </p>
      </div>

      {/* Scenario Presets */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Scenario Presets</h2>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          {SCENARIO_PRESETS.map((preset) => (
            <button
              key={preset.name}
              onClick={() => handleLoadPreset(preset)}
              className={clsx(
                'p-3 rounded-lg border-2 text-left transition-all',
                selectedScenario === preset.name
                  ? 'border-torq-500 bg-torq-50'
                  : 'border-gray-200 hover:border-gray-300'
              )}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-lg">{preset.icon}</span>
                <span className="font-medium text-sm">{preset.label}</span>
              </div>
              <p className="text-xs text-gray-500 line-clamp-2">{preset.description}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Configuration */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Exchange Configuration</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Node Selection */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Source Node (Publisher)
              </label>
              <select
                value={sourceNodeId}
                onChange={(e) => setSourceNodeId(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-torq-500"
              >
                <option value="node_alice">node_alice (trusted, score: 0.9)</option>
                <option value="node_bob">node_bob (trusted, score: 0.9)</option>
                <option value="node_charlie">node_charlie (unknown, score: 0.3)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Target Node (Receiver)
              </label>
              <select
                value={targetNodeId}
                onChange={(e) => setTargetNodeId(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-torq-500"
              >
                <option value="node_alice">node_alice (trusted, score: 0.9)</option>
                <option value="node_bob">node_bob (trusted, score: 0.9)</option>
                <option value="node_charlie">node_charlie (unknown, score: 0.3)</option>
              </select>
            </div>
          </div>

          {/* Claim Details */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Claim Title
              </label>
              <input
                type="text"
                value={claimTitle}
                onChange={(e) => setClaimTitle(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-torq-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Claim Text
              </label>
              <textarea
                value={claimText}
                onChange={(e) => setClaimText(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-torq-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Confidence: {claimConfidence.toFixed(2)}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={claimConfidence}
                onChange={(e) => setClaimConfidence(parseFloat(e.target.value))}
                className="w-full"
              />
            </div>
          </div>
        </div>

        {/* Expected Outcome */}
        {currentScenario && (
          <div className="mt-4 p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">Expected Outcome:</span>
              <span className={clsx(
                'px-2 py-1 rounded text-xs font-medium',
                currentScenario.expectedOutcome === 'accepted' && 'bg-green-100 text-green-800',
                currentScenario.expectedOutcome === 'quarantined' && 'bg-yellow-100 text-yellow-800',
                currentScenario.expectedOutcome === 'rejected' && 'bg-red-100 text-red-800',
              )}>
                {currentScenario.expectedOutcome.toUpperCase()}
              </span>
            </div>
          </div>
        )}

        {/* Run Button */}
        <div className="mt-6 flex items-center gap-3">
          <button
            onClick={handleRunScenario}
            disabled={publishMutation.isPending}
            className={clsx(
              'px-6 py-2 rounded-lg font-medium text-white',
              publishMutation.isPending
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-torq-600 hover:bg-torq-700'
            )}
          >
            {publishMutation.isPending ? (
              <>
                <span className="inline-block animate-spin mr-2">⏳</span>
                Running Exchange...
              </>
            ) : (
              <>
                <span className="mr-2">🚀</span>
                Run Exchange
              </>
            )}
          </button>

          {publishMutation.data && (
            <span className="text-sm text-green-600">
              ✓ Published: {publishMutation.data.envelopeId}
            </span>
          )}
        </div>
      </div>

      {/* Timeline */}
      {timeline.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Exchange Timeline</h2>
            {correlationId && (
              <span className="text-xs text-gray-500 font-mono">{correlationId}</span>
            )}
          </div>

          <div className="relative">
            {/* Timeline line */}
            <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200" />

            <div className="space-y-4">
              {timeline.map((event, idx) => (
                <div key={event.id} className="relative flex items-start gap-4">
                  {/* Timeline dot */}
                  <div className={clsx(
                    'w-8 h-8 rounded-full border-2 flex items-center justify-center z-10',
                    event.status === 'success' && 'border-green-500 bg-green-50',
                    event.status === 'error' && 'border-red-500 bg-red-50',
                    event.status === 'info' && 'border-yellow-500 bg-yellow-50',
                    event.status === 'pending' && 'border-gray-300 bg-gray-50',
                  )}>
                    {event.status === 'success' && <span>✓</span>}
                    {event.status === 'error' && <span>✕</span>}
                    {event.status === 'pending' && <span>○</span>}
                  </div>

                  {/* Event content */}
                  <div className="flex-1 bg-gray-50 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-gray-900">{event.label}</span>
                      <span className="text-xs text-gray-500">
                        {event.timestamp.toLocaleTimeString()}
                      </span>
                    </div>
                    {event.details && Object.keys(event.details).length > 0 && (
                      <div className="text-xs text-gray-600 mt-1 space-y-1">
                        {Object.entries(event.details).map(([key, value]) => (
                          <div key={key}>
                            <span className="font-medium">{key}:</span>{' '}
                            <span className="font-mono">{String(value)}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Exchange Trace Details */}
      {timeline.length > 0 && publishMutation.data && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Exchange Details</h2>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <DetailItem
              label="Envelope ID"
              value={publishMutation.data.envelopeId}
              icon="📨"
            />
            <DetailItem
              label="Correlation ID"
              value={publishMutation.data.correlationId}
              icon="🔗"
            />
            <DetailItem
              label="Target Node"
              value={publishMutation.data.targetNodeId}
              icon="🎯"
            />
            <DetailItem
              label="Signature Status"
              value={publishMutation.data.signatureStatus}
              icon="✍️"
            />
          </div>

          {publishMutation.data.envelope && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <h3 className="text-sm font-medium text-gray-700 mb-2">Envelope Payload</h3>
              <pre className="text-xs bg-gray-900 text-gray-100 p-3 rounded overflow-auto max-h-48">
                {JSON.stringify(publishMutation.data.envelope, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* Event Log */}
      <FederationEventLog maxEvents={50} />
    </div>
  )
}

function DetailItem({ label, value, icon }: { label: string; value: string; icon: string }) {
  return (
    <div>
      <div className="flex items-center gap-1 mb-1">
        <span className="text-sm">{icon}</span>
        <p className="text-xs text-gray-600">{label}</p>
      </div>
      <p className="text-sm font-mono text-gray-900 truncate" title={value}>
        {value}
      </p>
    </div>
  )
}
