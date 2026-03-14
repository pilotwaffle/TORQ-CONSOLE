/**
 * Envelope Viewer Component
 * Phase 1B - Display federated claim envelope details
 */

import { clsx } from 'clsx'
import type { FederatedClaimEnvelope } from '@torq/federation-contracts'

interface EnvelopeViewerProps {
  envelope: FederatedClaimEnvelope | null
  loading?: boolean
}

export function EnvelopeViewer({ envelope, loading }: EnvelopeViewerProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Claim Envelope</h3>
          <div className="animate-pulse">
            <div className="h-4 w-24 bg-gray-200 rounded" />
          </div>
        </div>
        <div className="space-y-3">
          <div className="h-8 bg-gray-100 rounded animate-pulse" />
          <div className="h-20 bg-gray-100 rounded animate-pulse" />
        </div>
      </div>
    )
  }

  if (!envelope) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Claim Envelope</h3>
          <span className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-sm">
            Empty
          </span>
        </div>
        <div className="text-center py-8 text-gray-500">
          No envelope loaded
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      {/* Header */}
      <div className="bg-torq-900 text-white px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold">{envelope.artifact.title}</h3>
            <p className="text-torq-300 text-sm">{envelope.envelopeId}</p>
          </div>
          <div className="text-right">
            <div className="text-torq-300 text-xs">Protocol</div>
            <div className="font-mono">{envelope.protocolVersion}</div>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Source & Target */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
              Source Node
            </h4>
            <div className="font-mono text-sm bg-gray-50 px-3 py-2 rounded">
              {envelope.sourceNodeId}
            </div>
          </div>
          <div>
            <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
              Target Node
            </h4>
            <div className="font-mono text-sm bg-gray-50 px-3 py-2 rounded">
              {envelope.targetNodeId || <span className="text-gray-400 italic">Broadcast</span>}
            </div>
          </div>
        </div>

        {/* Artifact Details */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-3">Artifact Details</h4>
          <div className="bg-gray-50 rounded-lg p-4 space-y-2">
            <div>
              <span className="text-xs text-gray-500">Type:</span>
              <span className="ml-2 text-sm font-mono bg-white px-2 py-1 rounded">
                {envelope.artifact.artifactType}
              </span>
            </div>
            <div>
              <span className="text-xs text-gray-500">Confidence:</span>
              <div className="ml-2 inline-flex items-center gap-2">
                <div className="w-24 bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-torq-500 h-2 rounded-full"
                    style={{ width: `${envelope.artifact.confidence * 100}%` }}
                  />
                </div>
                <span className="text-sm text-gray-700">
                  {Math.round(envelope.artifact.confidence * 100)}%
                </span>
              </div>
            </div>
            <div>
              <span className="text-xs text-gray-500">Origin Layer:</span>
              <span className="ml-2 text-sm font-mono">
                {envelope.artifact.originLayer}
              </span>
            </div>
            {envelope.artifact.originInsightId && (
              <div>
                <span className="text-xs text-gray-500">Origin ID:</span>
                <span className="ml-2 text-sm font-mono text-xs">
                  {envelope.artifact.originInsightId}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Claim Text */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">Claim</h4>
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-gray-900">{envelope.artifact.claimText}</p>
          </div>
        </div>

        {/* Signature Info */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">Signature</h4>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-xs text-gray-500">Algorithm:</span>
                <div className="font-mono">{envelope.signature.algorithm}</div>
              </div>
              <div>
                <span className="text-xs text-gray-500">Signer:</span>
                <div className="font-mono text-xs">{envelope.signature.signerNodeId}</div>
              </div>
              <div className="col-span-2">
                <span className="text-xs text-gray-500">Signed:</span>
                <div className="font-mono text-xs">
                  {new Date(envelope.signature.signedAt).toLocaleString()}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Trace */}
        {envelope.trace.hopCount > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Trace</h4>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-sm">
                <span className="text-gray-500">Hops:</span>
                <span className="font-mono">{envelope.trace.hopCount}</span>
                {envelope.trace.priorNodeIds.length > 0 && (
                  <span className="text-gray-400">→ [{envelope.trace.priorNodeIds.join(' → ')}]</span>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Tags */}
        {envelope.artifact.tags.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Tags</h4>
            <div className="flex flex-wrap gap-2">
              {envelope.artifact.tags.map((tag, index) => (
                <span
                  key={index}
                  className="px-2 py-1 bg-torq-100 text-torq800 rounded text-xs"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
