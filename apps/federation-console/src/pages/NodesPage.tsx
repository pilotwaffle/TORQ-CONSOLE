/**
 * Nodes Page
 * Phase 1B - View and manage registered nodes
 */

import { useQuery } from '@tanstack/react-query'
import { listNodes, getNodeTrustProfile } from '@/services/api/federationClient'
import { useFederationStore } from '@/app/store'

export default function NodesPage() {
  const { setSelectedNode, setNodeTrustProfile } = useFederationStore()

  // Load nodes
  const { data: nodesData, isLoading } = useQuery({
    queryKey: ['nodes'],
    queryFn: () => listNodes({ limit: 100 }),
    refetchInterval: 15000,
  })

  const handleNodeClick = async (nodeId: string) => {
    try {
      const profile = await getNodeTrustProfile(nodeId)
      setSelectedNode(nodesData?.nodes.find(n => n.nodeId === nodeId) || null)
      setNodeTrustProfile(profile)
    } catch (err) {
      console.error('Failed to load node profile:', err)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Federated Nodes</h1>
        <p className="text-gray-600 mt-1">
          View and manage registered nodes in the federation
        </p>
      </div>

      {/* Nodes Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            Registered Nodes ({nodesData?.total || 0})
          </h2>
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-gray-500">Loading nodes...</div>
        ) : !nodesData || nodesData.nodes.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No registered nodes found
          </div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Node ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Trust Tier
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Trust Score
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Last Seen
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {nodesData.nodes.map((node) => (
                <tr
                  key={node.nodeId}
                  onClick={() => handleNodeClick(node.nodeId)}
                  className="hover:bg-gray-50 cursor-pointer"
                >
                  <td className="px-6 py-4 whitespace-nowrap font-mono text-sm">
                    {node.nodeId}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 py-1 rounded text-xs font-medium capitalize">
                      {node.trustTier}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={clsx(
                      'inline-flex items-center gap-1',
                      node.status === 'active' ? 'text-green-600' : 'text-gray-400'
                    )}>
                      <span className={node.status === 'active' ? '●' : '○'} />
                      {node.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <div className="w-16 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-torq-500 h-2 rounded-full"
                          style={{ width: `${node.baselineTrustScore * 100}%` }}
                        />
                      </div>
                      <span className="text-sm text-gray-700">
                        {Math.round(node.baselineTrustScore * 100)}%
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {node.lastSeen ? new Date(node.lastSeen).toLocaleString() : 'Never'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

function clsx(...classes: (string | boolean | undefined | null)[]) {
  return classes.filter(Boolean).join(' ')
}
