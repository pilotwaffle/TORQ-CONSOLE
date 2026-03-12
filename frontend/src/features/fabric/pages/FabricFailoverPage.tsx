/**
 * TORQ Console - Distributed Fabric Failover Page
 *
 * Phase 1 - Operator UI Foundation
 *
 * Displays failover status, history, and controls
 */

import { useState } from "react";

// ============================================================================
// Mock Failover Event Data
// ============================================================================

interface FailoverEvent {
  id: string;
  timestamp: string;
  fromNode: string;
  toNode: string;
  reason: string;
  status: "completed" | "in_progress" | "failed";
}

const MOCK_FAILOVER_EVENTS: FailoverEvent[] = [
  {
    id: "fo_001",
    timestamp: "2025-03-12T08:30:00Z",
    fromNode: "node_003",
    toNode: "node_001",
    reason: "Health check failed - node degraded",
    status: "completed",
  },
  {
    id: "fo_002",
    timestamp: "2025-03-11T14:15:00Z",
    fromNode: "node_002",
    toNode: "node_001",
    reason: "Scheduled maintenance",
    status: "completed",
  },
];

// ============================================================================
// Failover Status Badge
// ============================================================================

interface FailoverStatusBadgeProps {
  status: FailoverEvent["status"];
}

function FailoverStatusBadge({ status }: FailoverStatusBadgeProps) {
  const styles = {
    completed: "bg-green-100 text-green-700",
    in_progress: "bg-blue-100 text-blue-700",
    failed: "bg-red-100 text-red-700",
  };

  const labels = {
    completed: "Completed",
    in_progress: "In Progress",
    failed: "Failed",
  };

  return (
    <span
      className={`px-2 py-1 text-xs font-medium rounded ${styles[status]}`}
      data-testid={`failover-status-${status}`}
    >
      {labels[status]}
    </span>
  );
}

// ============================================================================
// Main Fabric Failover Page Component
// ============================================================================

export default function FabricFailoverPage() {
  const [failoverEvents] = useState<FailoverEvent[]>(MOCK_FAILOVER_EVENTS);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);

  const stats = {
    total: failoverEvents.length,
    completed: failoverEvents.filter((e) => e.status === "completed").length,
    inProgress: failoverEvents.filter((e) => e.status === "in_progress").length,
    failed: failoverEvents.filter((e) => e.status === "failed").length,
  };

  return (
    <div className="container mx-auto px-4 py-6 max-w-7xl">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900" data-testid="page-title">
          Failover Management
        </h1>
        <p className="text-gray-500 mt-1">
          Monitor and manage failover events across the distributed fabric.
        </p>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6" data-testid="failover-stats">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-sm text-gray-600">Total Events</div>
          <div className="text-2xl font-bold text-gray-900">{stats.total}</div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-sm text-gray-600">Completed</div>
          <div className="text-2xl font-bold text-green-600">{stats.completed}</div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-sm text-gray-600">In Progress</div>
          <div className="text-2xl font-bold text-blue-600">{stats.inProgress}</div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-sm text-gray-600">Failed</div>
          <div className="text-2xl font-bold text-red-600">{stats.failed}</div>
        </div>
      </div>

      {/* Manual Failover Controls */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Manual Failover</h2>
        <p className="text-sm text-gray-600 mb-4">
          Initiate a manual failover to migrate workloads from one node to another.
        </p>
        <button
          onClick={() => setShowConfirmDialog(true)}
          className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
          data-testid="manual-failover-button"
        >
          Initiate Manual Failover
        </button>
      </div>

      {/* Failover History */}
      <div className="bg-white rounded-lg border border-gray-200" data-testid="failover-log">
        <div className="px-4 py-3 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Failover History</h2>
        </div>
        {failoverEvents.length === 0 ? (
          <div className="p-8 text-center text-gray-500">No failover events recorded.</div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Timestamp</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">From Node</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">To Node</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Reason</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Status</th>
              </tr>
            </thead>
            <tbody>
              {failoverEvents.map((event) => (
                <tr
                  key={event.id}
                  className="border-b border-gray-200"
                  data-testid="failover-event"
                >
                  <td className="px-4 py-3 text-sm text-gray-900">
                    {new Date(event.timestamp).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-900">{event.fromNode}</td>
                  <td className="px-4 py-3 text-sm text-gray-900">{event.toNode}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{event.reason}</td>
                  <td className="px-4 py-3">
                    <FailoverStatusBadge status={event.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Confirmation Dialog */}
      {showConfirmDialog && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          data-testid="confirmation-dialog"
        >
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Confirm Manual Failover
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              This will initiate a manual failover operation. Are you sure you want to continue?
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowConfirmDialog(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setShowConfirmDialog(false);
                  // In a real implementation, this would trigger the failover
                }}
                className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700"
              >
                Confirm Failover
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export { FabricFailoverPage };
