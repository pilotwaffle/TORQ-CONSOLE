/**
 * Status Page
 * Phase 1B - Comprehensive federation status and health metrics
 */

import { useQuery } from '@tanstack/react-query'
import { getFederationStatus, listNodes } from '@/services/api/federationClient'
import { FederationEventLog } from '@/components/federation'

export default function StatusPage() {
  // Load federation status
  const { data: status, isLoading: statusLoading } = useQuery({
    queryKey: ['federation-status'],
    queryFn: getFederationStatus,
    refetchInterval: 5000,
  })

  // Load nodes for additional stats
  const { data: nodesData } = useQuery({
    queryKey: ['nodes'],
    queryFn: () => listNodes({ limit: 100 }),
    refetchInterval: 15000,
  })

  // Calculate derived metrics
  const activeNodes = nodesData?.nodes.filter(n => n.status === 'active').length ?? 0
  const totalNodes = nodesData?.total ?? 0
  const acceptanceRate = status
    ? (status.totalClaimsAccepted / Math.max(status.totalClaimsProcessed, 1)) * 100
    : 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Federation Status</h1>
        <p className="text-gray-600 mt-1">
          Comprehensive health and performance metrics for the federation layer
        </p>
      </div>

      {/* Status Loading */}
      {statusLoading && (
        <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
          Loading federation status...
        </div>
      )}

      {/* Status Cards */}
      {status && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Protocol Version */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Protocol Version</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {status.protocolVersion}
                </p>
              </div>
              <div className="text-3xl">🔄</div>
            </div>
          </div>

          {/* Active Connections */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Connections</p>
                <p className="text-2xl font-bold text-torq-600 mt-1">
                  {status.activeConnections}
                </p>
              </div>
              <div className="text-3xl">🔗</div>
            </div>
          </div>

          {/* Active Nodes */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Nodes</p>
                <p className="text-2xl font-bold text-green-600 mt-1">
                  {activeNodes} / {totalNodes}
                </p>
              </div>
              <div className="text-3xl">🖥️</div>
            </div>
          </div>

          {/* Uptime */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Uptime</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {formatUptime(status.uptimeSeconds)}
                </p>
              </div>
              <div className="text-3xl">⏱️</div>
            </div>
          </div>
        </div>
      )}

      {/* Claims Processing Stats */}
      {status && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">
              Claims Processing
            </h2>
          </div>
          <div className="p-6">
            {/* Total Claims */}
            <div className="mb-6">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">Total Processed</span>
                <span className="text-2xl font-bold text-gray-900">
                  {status.totalClaimsProcessed.toLocaleString()}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="bg-torq-500 h-3 rounded-full transition-all"
                  style={{ width: '100%' }}
                />
              </div>
            </div>

            {/* Decision Breakdown */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Accepted */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-gray-700">Accepted</span>
                  <span className="text-lg font-semibold text-green-600">
                    {status.totalClaimsAccepted.toLocaleString()}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-green-500 h-2 rounded-full transition-all"
                    style={{
                      width: `${(status.totalClaimsAccepted / Math.max(status.totalClaimsProcessed, 1)) * 100}%`
                    }}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {acceptanceRate.toFixed(1)}% acceptance rate
                </p>
              </div>

              {/* Quarantined */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-gray-700">Quarantined</span>
                  <span className="text-lg font-semibold text-yellow-600">
                    {status.totalClaimsQuarantined.toLocaleString()}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-yellow-500 h-2 rounded-full transition-all"
                    style={{
                      width: `${(status.totalClaimsQuarantined / Math.max(status.totalClaimsProcessed, 1)) * 100}%`
                    }}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {((status.totalClaimsQuarantined / Math.max(status.totalClaimsProcessed, 1)) * 100).toFixed(1)}% of total
                </p>
              </div>

              {/* Rejected */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-gray-700">Rejected</span>
                  <span className="text-lg font-semibold text-red-600">
                    {status.totalClaimsRejected.toLocaleString()}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-red-500 h-2 rounded-full transition-all"
                    style={{
                      width: `${(status.totalClaimsRejected / Math.max(status.totalClaimsProcessed, 1)) * 100}%`
                    }}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {((status.totalClaimsRejected / Math.max(status.totalClaimsProcessed, 1)) * 100).toFixed(1)}% of total
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Health & Performance */}
      {status && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Health Status */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Health Status</h3>
            <div className="space-y-3">
              <HealthItem
                label="Identity Service"
                healthy={status.health.identityService}
              />
              <HealthItem
                label="Signature Verification"
                healthy={status.health.signatureVerification}
              />
              <HealthItem
                label="Trust Evaluation"
                healthy={status.health.trustEvaluation}
              />
              <HealthItem
                label="Node Registry"
                healthy={status.health.nodeRegistry}
              />
            </div>
          </div>

          {/* Performance Metrics */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance</h3>
            <div className="space-y-4">
              <MetricRow
                label="Avg. Validation Time"
                value={`${status.performance.avgValidationTimeMs.toFixed(2)} ms`}
              />
              <MetricRow
                label="P95 Validation Time"
                value={`${status.performance.p95ValidationTimeMs.toFixed(2)} ms`}
              />
              <MetricRow
                label="Claims per Second"
                value={status.performance.claimsPerSecond.toFixed(2)}
              />
              <MetricRow
                label="Memory Usage"
                value={`${(status.performance.memoryUsageMB / 1024).toFixed(2)} GB`}
              />
            </div>
          </div>
        </div>
      )}

      {/* Event Log */}
      <FederationEventLog maxEvents={50} />
    </div>
  )
}

function HealthItem({ label, healthy }: { label: string; healthy: boolean }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
      <span className="text-sm text-gray-700">{label}</span>
      <span className={clsx(
        'inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium',
        healthy ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
      )}>
        <span className={healthy ? '●' : '●'} />
        {healthy ? 'Healthy' : 'Unhealthy'}
      </span>
    </div>
  )
}

function MetricRow({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
      <span className="text-sm text-gray-600">{label}</span>
      <span className="text-sm font-mono font-semibold text-gray-900">{value}</span>
    </div>
  )
}

function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)

  if (days > 0) {
    return `${days}d ${hours}h`
  }
  if (hours > 0) {
    return `${hours}h ${minutes}m`
  }
  return `${minutes}m`
}

function clsx(...classes: (string | boolean | undefined | null)[]) {
  return classes.filter(Boolean).join(' ')
}
