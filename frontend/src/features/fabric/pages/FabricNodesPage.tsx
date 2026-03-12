/**
 * TORQ Console - Distributed Fabric Nodes Page
 *
 * Phase 1 - Operator UI Foundation
 *
 * Displays the distributed fabric node status with:
 * - Node list with health information
 * - Region and tier information
 * - Capabilities display
 * - Failover status
 */

import { useState } from "react";

// ============================================================================
// Mock Fabric Node Data
// ============================================================================

interface FabricNode {
  id: string;
  name: string;
  region: "us_east" | "us_west" | "europe" | "asia";
  tier: "enterprise" | "standard" | "edge";
  health: "healthy" | "degraded" | "unhealthy";
  status: "active" | "standby" | "maintenance";
  capabilities: string[];
  lastSeen: string;
}

const MOCK_NODES: FabricNode[] = [
  {
    id: "node_001",
    name: "TORQ-Primary-East",
    region: "us_east",
    tier: "enterprise",
    health: "healthy",
    status: "active",
    capabilities: ["simulation", "execution", "coordination"],
    lastSeen: "2025-03-12T09:30:00Z",
  },
  {
    id: "node_002",
    name: "TORQ-Secondary-West",
    region: "us_west",
    tier: "enterprise",
    health: "healthy",
    status: "standby",
    capabilities: ["simulation", "execution"],
    lastSeen: "2025-03-12T09:29:45Z",
  },
  {
    id: "node_003",
    name: "TORQ-Edge-Europe",
    region: "europe",
    tier: "edge",
    health: "degraded",
    status: "active",
    capabilities: ["execution"],
    lastSeen: "2025-03-12T09:28:30Z",
  },
  {
    id: "node_004",
    name: "TORQ-Standard-Asia",
    region: "asia",
    tier: "standard",
    health: "healthy",
    status: "active",
    capabilities: ["simulation"],
    lastSeen: "2025-03-12T09:30:00Z",
  },
];

// ============================================================================
// Health Badge Component
// ============================================================================

interface HealthBadgeProps {
  health: FabricNode["health"];
}

function HealthBadge({ health }: HealthBadgeProps) {
  const styles = {
    healthy: "bg-green-100 text-green-700",
    degraded: "bg-yellow-100 text-yellow-700",
    unhealthy: "bg-red-100 text-red-700",
  };

  const icons = {
    healthy: "●",
    degraded: "◆",
    unhealthy: "●",
  };

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded ${styles[health]}`}
      data-testid={`health-badge-${health}`}
    >
      <span>{icons[health]}</span>
      <span className="capitalize">{health}</span>
    </span>
  );
}

// ============================================================================
// Region Badge Component
// ============================================================================

interface RegionBadgeProps {
  region: FabricNode["region"];
}

function RegionBadge({ region }: RegionBadgeProps) {
  const labels = {
    us_east: "US East",
    us_west: "US West",
    europe: "Europe",
    asia: "Asia",
  };

  return (
    <span
      className="px-2 py-1 text-xs font-medium rounded bg-gray-100 text-gray-700"
      data-testid="region-badge"
    >
      {labels[region]}
    </span>
  );
}

// ============================================================================
// Tier Badge Component
// ============================================================================

interface TierBadgeProps {
  tier: FabricNode["tier"];
}

function TierBadge({ tier }: TierBadgeProps) {
  const styles = {
    enterprise: "bg-purple-100 text-purple-700",
    standard: "bg-blue-100 text-blue-700",
    edge: "bg-green-100 text-green-700",
  };

  const labels = {
    enterprise: "Enterprise",
    standard: "Standard",
    edge: "Edge",
  };

  return (
    <span
      className={`px-2 py-1 text-xs font-medium rounded ${styles[tier]}`}
      data-testid="tier-badge"
    >
      {labels[tier]}
    </span>
  );
}

// ============================================================================
// Status Badge Component
// ============================================================================

interface StatusBadgeProps {
  status: FabricNode["status"];
}

function StatusBadge({ status }: StatusBadgeProps) {
  const labels = {
    active: "Active",
    standby: "Standby",
    maintenance: "Maintenance",
  };

  const styles = {
    active: "text-green-700",
    standby: "text-blue-700",
    maintenance: "text-gray-600",
  };

  return (
    <span className={`text-sm font-medium ${styles[status]}`} data-testid="status-badge">
      {labels[status]}
    </span>
  );
}

// ============================================================================
// Node Card Component
// ============================================================================

interface NodeCardProps {
  node: FabricNode;
}

function NodeCard({ node }: NodeCardProps) {
  return (
    <div
      className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow"
      data-testid="node-card"
      data-node-id={node.id}
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-semibold text-gray-900" data-testid="node-name">
            {node.name}
          </h3>
          <p className="text-sm text-gray-500" data-testid="node-id">
            {node.id}
          </p>
        </div>
        <HealthBadge health={node.health} />
      </div>

      <div className="flex flex-wrap gap-2 mb-3">
        <RegionBadge region={node.region} />
        <TierBadge tier={node.tier} />
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Status</span>
          <StatusBadge status={node.status} />
        </div>

        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Last Seen</span>
          <span className="text-gray-900">
            {new Date(node.lastSeen).toLocaleTimeString()}
          </span>
        </div>

        {node.capabilities.length > 0 && (
          <div>
            <span className="text-sm text-gray-600">Capabilities:</span>
            <div className="flex flex-wrap gap-1 mt-1" data-testid="capabilities">
              {node.capabilities.map((cap) => (
                <span
                  key={cap}
                  className="px-2 py-0.5 text-xs bg-gray-100 text-gray-700 rounded"
                >
                  {cap}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Main Fabric Nodes Page Component
// ============================================================================

export default function FabricNodesPage() {
  const [nodes] = useState<FabricNode[]>(MOCK_NODES);
  const [selectedRegion, setSelectedRegion] = useState<"all" | FabricNode["region"]>("all");
  const [selectedHealth, setSelectedHealth] = useState<"all" | FabricNode["health"]>("all");

  const filteredNodes = nodes.filter((node) => {
    if (selectedRegion !== "all" && node.region !== selectedRegion) return false;
    if (selectedHealth !== "all" && node.health !== selectedHealth) return false;
    return true;
  });

  const healthyCount = nodes.filter((n) => n.health === "healthy").length;
  const degradedCount = nodes.filter((n) => n.health === "degraded").length;
  const unhealthyCount = nodes.filter((n) => n.health === "unhealthy").length;

  return (
    <div className="container mx-auto px-4 py-6 max-w-7xl">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900" data-testid="page-title">
          Distributed Fabric
        </h1>
        <p className="text-gray-500 mt-1">
          Monitor and manage TORQ nodes across the distributed infrastructure.
        </p>
      </div>

      {/* Health Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-sm text-gray-600">Total Nodes</div>
          <div className="text-2xl font-bold text-gray-900" data-testid="total-nodes">
            {nodes.length}
          </div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-sm text-gray-600">Healthy</div>
          <div className="text-2xl font-bold text-green-600" data-testid="healthy-nodes">
            {healthyCount}
          </div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-sm text-gray-600">Degraded</div>
          <div className="text-2xl font-bold text-yellow-600" data-testid="degraded-nodes">
            {degradedCount}
          </div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-sm text-gray-600">Unhealthy</div>
          <div className="text-2xl font-bold text-red-600" data-testid="unhealthy-nodes">
            {unhealthyCount}
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 mb-6">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-700">Region:</label>
          <select
            value={selectedRegion}
            onChange={(e) => setSelectedRegion(e.target.value as typeof selectedRegion)}
            className="px-3 py-1.5 border border-gray-300 rounded text-sm"
            data-testid="region-filter"
          >
            <option value="all">All Regions</option>
            <option value="us_east">US East</option>
            <option value="us_west">US West</option>
            <option value="europe">Europe</option>
            <option value="asia">Asia</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-700">Health:</label>
          <select
            value={selectedHealth}
            onChange={(e) => setSelectedHealth(e.target.value as typeof selectedHealth)}
            className="px-3 py-1.5 border border-gray-300 rounded text-sm"
            data-testid="health-filter"
          >
            <option value="all">All</option>
            <option value="healthy">Healthy</option>
            <option value="degraded">Degraded</option>
            <option value="unhealthy">Unhealthy</option>
          </select>
        </div>
      </div>

      {/* Node List */}
      {filteredNodes.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
          <div className="text-gray-500">No nodes found matching the selected filters.</div>
        </div>
      ) : (
        <div
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
          data-testid="node-list"
        >
          {filteredNodes.map((node) => (
            <NodeCard key={node.id} node={node} />
          ))}
        </div>
      )}
    </div>
  );
}

export { FabricNodesPage };
