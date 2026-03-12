/**
 * Operator Control Surface - Workstream Health Dashboard
 *
 * Displays health status across parallel workstreams with phase,
 * confidence, blockers, and completeness information.
 */

import { useWorkstreamsHealth } from "../hooks/useControlMissions";
import {
  formatRelativeTime,
  formatProgressPercent,
  getHealthBadgeStyle,
} from "../utils/formatters";
import type { WorkstreamHealth } from "../types/mission";

// ============================================================================
// Types
// ============================================================================

interface WorkstreamHealthPanelProps {
  missionId: string;
}

// ============================================================================
// Health Card Component
// ============================================================================

interface HealthCardProps {
  workstream: {
    id: string;
    name: string;
    health: WorkstreamHealth;
    progress: { completed: number; total: number };
    active_nodes: number;
    blocked_nodes: number;
    failed_nodes: number;
    completed_nodes: number;
    total_nodes: number;
    last_activity: string | null;
  };
}

function HealthCard({ workstream }: HealthCardProps) {
  const style = getHealthBadgeStyle(workstream.health);
  const percent =
    workstream.progress.total > 0
      ? (workstream.progress.completed / workstream.progress.total) * 100
      : 0;

  return (
    <div className="bg-white border rounded-lg p-4 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="font-medium text-gray-900">{workstream.name}</h3>
          <p className="text-xs text-gray-500 font-mono mt-0.5">{workstream.id.substring(0, 8)}</p>
        </div>
        <div
          className={`inline-flex items-center justify-center w-8 h-8 rounded-full ${style.bgColor} ${style.textColor}`}
        >
          <span className="text-sm">{style.icon}</span>
        </div>
      </div>

      {/* Health Status */}
      <div className="mb-3">
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${style.bgColor} ${style.textColor}`}
        >
          {workstream.health.replace("_", " ")}
        </span>
      </div>

      {/* Progress Bar */}
      <div className="mb-3">
        <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
          <span>Progress</span>
          <span>{formatProgressPercent(workstream.progress.completed, workstream.progress.total)}</span>
        </div>
        <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all ${
              workstream.health === "healthy"
                ? "bg-green-500"
                : workstream.health === "at_risk"
                ? "bg-yellow-500"
                : workstream.health === "failed"
                ? "bg-red-500"
                : "bg-gray-400"
            }`}
            style={{ width: `${Math.min(percent, 100)}%` }}
          />
        </div>
      </div>

      {/* Node Stats */}
      <div className="grid grid-cols-4 gap-2 mb-3">
        <div className="text-center">
          <div className="text-lg font-semibold text-blue-600">{workstream.active_nodes}</div>
          <div className="text-xs text-gray-500">Active</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-semibold text-green-600">{workstream.completed_nodes}</div>
          <div className="text-xs text-gray-500">Done</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-semibold text-orange-600">{workstream.blocked_nodes}</div>
          <div className="text-xs text-gray-500">Blocked</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-semibold text-red-600">{workstream.failed_nodes}</div>
          <div className="text-xs text-gray-500">Failed</div>
        </div>
      </div>

      {/* Last Activity */}
      {workstream.last_activity && (
        <div className="text-xs text-gray-400 border-t pt-2">
          Last activity: {formatRelativeTime(workstream.last_activity)}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Loading State
// ============================================================================

function LoadingState() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {[1, 2, 3].map((i) => (
        <div key={i} className="bg-white border rounded-lg p-4 space-y-3">
          <div className="h-4 bg-gray-200 rounded animate-pulse w-3/4" />
          <div className="h-2 bg-gray-200 rounded animate-pulse w-1/2" />
          <div className="h-2 bg-gray-200 rounded animate-pulse w-full" />
          <div className="grid grid-cols-4 gap-2">
            {[1, 2, 3, 4].map((j) => (
              <div key={j} className="h-6 bg-gray-200 rounded animate-pulse" />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// ============================================================================
// Empty State
// ============================================================================

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <svg
        className="w-12 h-12 text-gray-300 mb-3"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
        />
      </svg>
      <h3 className="text-sm font-medium text-gray-900 mb-1">No workstreams</h3>
      <p className="text-xs text-gray-500">
        This mission doesn't have any workstreams defined yet.
      </p>
    </div>
  );
}

// ============================================================================
// Summary Stats Component
// ============================================================================

interface SummaryStatsProps {
  workstreams: Array<{
    health: WorkstreamHealth;
    active_nodes: number;
    blocked_nodes: number;
    failed_nodes: number;
    completed_nodes: number;
    total_nodes: number;
  }>;
}

function SummaryStats({ workstreams }: SummaryStatsProps) {
  const healthyCount = workstreams.filter((w) => w.health === "healthy").length;
  const atRiskCount = workstreams.filter((w) => w.health === "at_risk").length;
  const failedCount = workstreams.filter((w) => w.health === "failed").length;
  const idleCount = workstreams.filter((w) => w.health === "idle").length;

  const totalActive = workstreams.reduce((sum, w) => sum + w.active_nodes, 0);
  const totalBlocked = workstreams.reduce((sum, w) => sum + w.blocked_nodes, 0);
  const totalFailed = workstreams.reduce((sum, w) => sum + w.failed_nodes, 0);
  const totalCompleted = workstreams.reduce((sum, w) => sum + w.completed_nodes, 0);

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
      <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-center">
        <div className="text-2xl font-bold text-green-600">{healthyCount}</div>
        <div className="text-xs text-green-700">Healthy</div>
      </div>
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-center">
        <div className="text-2xl font-bold text-yellow-600">{atRiskCount}</div>
        <div className="text-xs text-yellow-700">At Risk</div>
      </div>
      <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-center">
        <div className="text-2xl font-bold text-red-600">{failedCount}</div>
        <div className="text-xs text-red-700">Failed</div>
      </div>
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-center">
        <div className="text-2xl font-bold text-gray-600">{idleCount}</div>
        <div className="text-xs text-gray-700">Idle</div>
      </div>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function WorkstreamHealthPanel({ missionId }: WorkstreamHealthPanelProps) {
  const { data, isLoading, isError, refetch } = useWorkstreamsHealth(missionId);

  if (isLoading) {
    return (
      <div className="bg-white border rounded-lg shadow-sm overflow-hidden">
        <div className="px-4 py-3 bg-gray-50 border-b">
          <h2 className="text-lg font-semibold text-gray-900">Workstream Health</h2>
        </div>
        <div className="p-4">
          <LoadingState />
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-white border rounded-lg shadow-sm overflow-hidden">
        <div className="px-4 py-3 bg-gray-50 border-b flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Workstream Health</h2>
          <button
            onClick={() => refetch()}
            className="text-sm text-red-600 hover:text-red-700"
          >
            Retry
          </button>
        </div>
        <div className="p-8 text-center text-red-500">Failed to load workstreams</div>
      </div>
    );
  }

  if (!data || data.workstreams.length === 0) {
    return (
      <div className="bg-white border rounded-lg shadow-sm overflow-hidden">
        <div className="px-4 py-3 bg-gray-50 border-b">
          <h2 className="text-lg font-semibold text-gray-900">Workstream Health</h2>
        </div>
        <div className="p-4">
          <EmptyState />
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border rounded-lg shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-gray-50 border-b flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Workstream Health</h2>
        <div className="text-sm text-gray-500">{data.workstreams.length} workstreams</div>
      </div>

      {/* Summary Stats */}
      <div className="p-4 pb-0">
        <SummaryStats workstreams={data.workstreams} />
      </div>

      {/* Workstream Cards */}
      <div className="p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.workstreams.map((workstream) => (
            <HealthCard key={workstream.id} workstream={workstream} />
          ))}
        </div>
      </div>
    </div>
  );
}
