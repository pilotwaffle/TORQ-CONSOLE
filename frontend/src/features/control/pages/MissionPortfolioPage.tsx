/**
 * TORQ Console - Mission Portfolio Page
 *
 * Phase 1 - Operator UI Foundation
 *
 * Displays the mission portfolio with:
 * - Mission list or empty state
 * - Filter controls
 * - Status badges
 * - Progress indicators
 */

import { useState } from "react";

// ============================================================================
// Mock Mission Data
// ============================================================================

interface Mission {
  id: string;
  name: string;
  status: "running" | "completed" | "failed" | "pending";
  progress: number;
  created_at: string;
  description?: string;
}

const MOCK_MISSIONS: Mission[] = [
  {
    id: "mission_001",
    name: "Data Pipeline Migration",
    status: "running",
    progress: 65,
    created_at: "2025-03-10T09:30:00Z",
    description: "Migrate legacy data pipeline to new infrastructure",
  },
  {
    id: "mission_002",
    name: "AI Model Training",
    status: "completed",
    progress: 100,
    created_at: "2025-03-08T14:00:00Z",
    description: "Train production ML model",
  },
  {
    id: "mission_003",
    name: "System Health Check",
    status: "pending",
    progress: 0,
    created_at: "2025-03-12T08:00:00Z",
    description: "Comprehensive system health verification",
  },
  {
    id: "mission_004",
    name: "API Integration",
    status: "failed",
    progress: 45,
    created_at: "2025-03-09T16:45:00Z",
    description: "Integrate third-party API services",
  },
];

// ============================================================================
// Status Badge Component
// ============================================================================

interface StatusBadgeProps {
  status: Mission["status"];
}

function StatusBadge({ status }: StatusBadgeProps) {
  const styles = {
    running: "bg-blue-100 text-blue-700",
    completed: "bg-green-100 text-green-700",
    failed: "bg-red-100 text-red-700",
    pending: "bg-gray-100 text-gray-700",
  };

  const labels = {
    running: "Running",
    completed: "Completed",
    failed: "Failed",
    pending: "Pending",
  };

  return (
    <span
      className={`px-2 py-1 text-xs font-medium rounded ${styles[status]}`}
      data-testid={`status-badge-${status}`}
    >
      {labels[status]}
    </span>
  );
}

// ============================================================================
// Progress Bar Component
// ============================================================================

interface ProgressBarProps {
  progress: number;
  status: Mission["status"];
}

function ProgressBar({ progress, status }: ProgressBarProps) {
  const colorClass = {
    running: "bg-blue-600",
    completed: "bg-green-600",
    failed: "bg-red-600",
    pending: "bg-gray-400",
  }[status];

  return (
    <div className="w-full">
      <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
        <span>Progress</span>
        <span>{progress}%</span>
      </div>
      <div
        className="w-full bg-gray-200 rounded-full h-2"
        role="progressbar"
        aria-valuenow={progress}
        aria-valuemin={0}
        aria-valuemax={100}
        data-testid="progress-bar"
      >
        <div
          className={`h-2 rounded-full ${colorClass} transition-all duration-300`}
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}

// ============================================================================
// Mission Row Component
// ============================================================================

interface MissionRowProps {
  mission: Mission;
}

function MissionRow({ mission }: MissionRowProps) {
  return (
    <tr
      className="border-b border-gray-200 hover:bg-gray-50 transition-colors"
      data-mission-id={mission.id}
      data-testid="mission-item"
    >
      <td className="px-4 py-3">
        <div>
          <div className="font-medium text-gray-900">{mission.name}</div>
          {mission.description && (
            <div className="text-sm text-gray-500">{mission.description}</div>
          )}
        </div>
      </td>
      <td className="px-4 py-3">
        <StatusBadge status={mission.status} />
      </td>
      <td className="px-4 py-3 w-48">
        <ProgressBar progress={mission.progress} status={mission.status} />
      </td>
      <td className="px-4 py-3 text-sm text-gray-600">
        {new Date(mission.created_at).toLocaleDateString()}
      </td>
      <td className="px-4 py-3">
        <a
          href={`/control/missions/${mission.id}`}
          className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          data-testid="view-mission-link"
        >
          View
        </a>
      </td>
    </tr>
  );
}

// ============================================================================
// Empty State Component
// ============================================================================

function EmptyState() {
  return (
    <div
      className="flex flex-col items-center justify-center py-16"
      data-testid="empty-state"
    >
      <div className="text-6xl mb-4">📋</div>
      <h3 className="text-lg font-medium text-gray-900 mb-2">No missions found</h3>
      <p className="text-gray-500 mb-6">
        Create your first mission to get started with automated workflows.
      </p>
      <button
        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        data-testid="create-mission-button"
      >
        Create Mission
      </button>
    </div>
  );
}

// ============================================================================
// Loading State Component
// ============================================================================

function LoadingState() {
  return (
    <div className="flex items-center justify-center py-16" data-testid="loading-state">
      <div className="flex flex-col items-center gap-3">
        <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm text-gray-500">Loading missions...</p>
      </div>
    </div>
  );
}

// ============================================================================
// Main Mission Portfolio Page Component
// ============================================================================

export default function MissionPortfolioPage() {
  const [missions] = useState<Mission[]>(MOCK_MISSIONS);
  const [filter, setFilter] = useState<"all" | "running" | "completed" | "failed">("all");
  const [isLoading] = useState(false);

  const filteredMissions = missions.filter((mission) => {
    if (filter === "all") return true;
    return mission.status === filter;
  });

  return (
    <div className="container mx-auto px-4 py-6 max-w-7xl">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900" data-testid="page-title">
          Mission Portfolio
        </h1>
        <p className="text-gray-500 mt-1">
          Monitor and manage all active missions across the TORQ fabric.
        </p>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setFilter("all")}
            className={`px-3 py-1.5 text-sm font-medium rounded ${
              filter === "all"
                ? "bg-blue-600 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
            data-testid="filter-all"
          >
            All
          </button>
          <button
            onClick={() => setFilter("running")}
            className={`px-3 py-1.5 text-sm font-medium rounded ${
              filter === "running"
                ? "bg-blue-600 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
            data-testid="filter-running"
          >
            Running
          </button>
          <button
            onClick={() => setFilter("completed")}
            className={`px-3 py-1.5 text-sm font-medium rounded ${
              filter === "completed"
                ? "bg-blue-600 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
            data-testid="filter-completed"
          >
            Completed
          </button>
          <button
            onClick={() => setFilter("failed")}
            className={`px-3 py-1.5 text-sm font-medium rounded ${
              filter === "failed"
                ? "bg-blue-600 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
            data-testid="filter-failed"
          >
            Failed
          </button>
        </div>

        <button
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          data-testid="refresh-button"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>

      {/* Content */}
      {isLoading ? (
        <LoadingState />
      ) : filteredMissions.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden" data-testid="mission-list">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Mission</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Status</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Progress</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Created</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredMissions.map((mission) => (
                <MissionRow key={mission.id} mission={mission} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// Export the page with a default export alias for router
export { MissionPortfolioPage };
