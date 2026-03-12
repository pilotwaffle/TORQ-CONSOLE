/**
 * Operator Control Surface - Mission Detail Header
 *
 * Header component for the Mission Detail page showing mission info,
 * status, and progress. Displays at the top of the mission detail view.
 */

import { useNavigate } from "react-router-dom";
import { useMissionDetail } from "../hooks/useControlMissions";
import {
  formatDateTime,
  formatProgressPercent,
  getStatusBadgeStyle,
  formatMissionType,
} from "../utils/formatters";
import type { MissionStatus } from "../types/mission";

// ============================================================================
// Types
// ============================================================================

interface MissionDetailHeaderProps {
  missionId: string;
}

// ============================================================================
// Sub-Components
// ============================================================================

function StatusBadge({ status }: { status: MissionStatus }) {
  const style = getStatusBadgeStyle(status);

  return (
    <span
      className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${style.bgColor} ${style.textColor}`}
    >
      {style.label}
    </span>
  );
}

function ProgressBar({ completed, total }: { completed: number; total: number }) {
  const percent = total > 0 ? (completed / total) * 100 : 0;

  const getBarColor = () => {
    if (percent >= 100) return "bg-green-500";
    if (percent >= 75) return "bg-blue-500";
    if (percent >= 50) return "bg-yellow-500";
    return "bg-orange-500";
  };

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium text-gray-700">{formatProgressPercent(completed, total)}</span>
        <span className="text-gray-500">{completed} of {total} nodes complete</span>
      </div>
      <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full ${getBarColor()} transition-all duration-500`}
          style={{ width: `${Math.min(percent, 100)}%` }}
        />
      </div>
    </div>
  );
}

function MissionMetaItem({
  label,
  value,
}: {
  label: string;
  value: string | React.ReactNode;
}) {
  return (
    <div>
      <div className="text-xs text-gray-500 uppercase tracking-wide">{label}</div>
      <div className="text-sm text-gray-900">{value}</div>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="bg-white border rounded-lg shadow-sm p-6 space-y-4">
      <div className="flex items-center gap-4">
        <div className="h-8 bg-gray-200 rounded animate-pulse w-48" />
        <div className="h-6 bg-gray-200 rounded animate-pulse w-20" />
      </div>
      <div className="h-4 bg-gray-200 rounded animate-pulse w-full max-w-2xl" />
      <div className="h-3 bg-gray-200 rounded animate-pulse w-3/4" />
      <div className="h-2 bg-gray-200 rounded animate-pulse w-full" />
    </div>
  );
}

function ErrorState({ error, onRetry }: { error: Error; onRetry: () => void }) {
  return (
    <div className="bg-white border rounded-lg shadow-sm p-6">
      <div className="flex items-center gap-3 text-red-600">
        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
            clipRule="evenodd"
          />
        </svg>
        <div>
          <div className="font-medium">Failed to load mission</div>
          <div className="text-sm">{error.message}</div>
        </div>
        <button
          onClick={onRetry}
          className="ml-auto px-3 py-1 text-sm border border-red-300 rounded hover:bg-red-50"
        >
          Retry
        </button>
      </div>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function MissionDetailHeader({ missionId }: MissionDetailHeaderProps) {
  const navigate = useNavigate();
  const { data, isLoading, isError, error, refetch } = useMissionDetail(missionId);

  if (isLoading) {
    return <LoadingState />;
  }

  if (isError || !data) {
    return <ErrorState error={error as Error} onRetry={() => refetch()} />;
  }

  const { mission, progress, graph, node_count } = data;

  return (
    <div className="bg-white border rounded-lg shadow-sm">
      {/* Top Bar */}
      <div className="px-6 py-4 border-b flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate("/control")}
            className="p-1 hover:bg-gray-100 rounded transition-colors"
            title="Back to mission list"
          >
            <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <div>
            <h1 className="text-xl font-semibold text-gray-900">{mission.title || "Untitled Mission"}</h1>
            <div className="text-sm text-gray-500">
              ID: <code className="text-xs bg-gray-100 px-1.5 py-0.5 rounded">
                {mission.id.substring(0, 8)}
              </code>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <StatusBadge status={mission.status} />
        </div>
      </div>

      {/* Objective & Progress */}
      <div className="px-6 py-4 space-y-4">
        {/* Objective */}
        <div>
          <h2 className="text-sm font-medium text-gray-700 mb-1">Objective</h2>
          <p className="text-gray-900">{mission.objective}</p>
        </div>

        {/* Progress Bar */}
        <div className="max-w-2xl">
          <ProgressBar
            completed={progress.completed}
            total={progress.total}
          />
        </div>

        {/* Metadata Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 pt-2 border-t">
          <MissionMetaItem
            label="Mission Type"
            value={formatMissionType(mission.mission_type)}
          />
          <MissionMetaItem
            label="Reasoning Strategy"
            value={mission.reasoning_strategy || "Default"}
          />
          <MissionMetaItem
            label="Total Nodes"
            value={node_count.toString()}
          />
          <MissionMetaItem
            label="Created"
            value={formatDateTime(mission.created_at)}
          />
        </div>

        {/* Context Info (if exists) */}
        {mission.context && Object.keys(mission.context).length > 0 && (
          <div className="pt-2 border-t">
            <details className="group">
              <summary className="text-sm font-medium text-gray-700 cursor-pointer hover:text-gray-900">
                Mission Context
              </summary>
              <div className="mt-2 p-3 bg-gray-50 rounded-md">
                <pre className="text-xs text-gray-600 overflow-x-auto">
                  {JSON.stringify(mission.context, null, 2)}
                </pre>
              </div>
            </details>
          </div>
        )}
      </div>
    </div>
  );
}
