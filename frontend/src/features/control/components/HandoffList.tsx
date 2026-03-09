/**
 * Operator Control Surface - Handoff Viewer
 *
 * Displays collaboration handoffs between nodes with confidence scores,
 * summaries, and detailed inspection capabilities.
 */

import { useState } from "react";
import { useMissionHandoffs } from "../hooks/useControlMissions";
import {
  formatDateTime,
  formatConfidence,
  getConfidenceColor,
  truncateText,
} from "../utils/formatters";
import type { HandoffFormat } from "../types/mission";

// ============================================================================
// Types
// ============================================================================

interface HandoffListProps {
  missionId: string;
}

// ============================================================================
// Format Badge Component
// ============================================================================

function FormatBadge({ format }: { format: HandoffFormat }) {
  const isRich = format === "rich";

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
        isRich
          ? "bg-purple-100 text-purple-700"
          : "bg-gray-100 text-gray-700"
      }`}
    >
      {isRich ? "Rich" : "Minimal"}
    </span>
  );
}

// ============================================================================
// Confidence Bar Component
// ============================================================================

function ConfidenceBar({ confidence }: { confidence: number }) {
  const percent = confidence * 100;
  const color = getConfidenceColor(confidence);

  return (
    <div className="flex items-center gap-2">
      <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full ${color.replace("text-", "bg-")} transition-all`}
          style={{ width: `${percent}%` }}
        />
      </div>
      <span className={`text-xs font-medium ${color}`}>
        {formatConfidence(confidence)}
      </span>
    </div>
  );
}

// ============================================================================
// Handoff Item Component
// ============================================================================

interface HandoffItemProps {
  handoff: {
    id: string;
    source_node_title: string;
    target_node_title: string;
    confidence: number;
    summary: string;
    recommendations: string[];
    artifacts: Array<Record<string, unknown>>;
    format: HandoffFormat;
    created_at: string;
  };
  onClick: () => void;
  isExpanded: boolean;
}

function HandoffItemRow({ handoff, onClick, isExpanded }: HandoffItemProps) {
  return (
    <div
      onClick={onClick}
      className={`border-b last:border-b-0 hover:bg-gray-50 cursor-pointer transition-colors ${
        isExpanded ? "bg-blue-50" : ""
      }`}
    >
      <div className="px-4 py-3">
        {/* Header: Source → Target */}
        <div className="flex items-center gap-2 mb-2">
          <span className="font-medium text-gray-900 text-sm">
            {handoff.source_node_title}
          </span>
          <svg
            className="w-4 h-4 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
          </svg>
          <span className="font-medium text-gray-900 text-sm">
            {handoff.target_node_title}
          </span>
          <FormatBadge format={handoff.format} />
        </div>

        {/* Confidence */}
        <div className="mb-2">
          <ConfidenceBar confidence={handoff.confidence} />
        </div>

        {/* Summary */}
        <div className="text-sm text-gray-600 mb-2">
          {truncateText(handoff.summary, 120)}
        </div>

        {/* Metadata Row */}
        <div className="flex items-center gap-3 text-xs text-gray-500">
          <span>
            {handoff.recommendations.length}{" "}
            {handoff.recommendations.length === 1 ? "recommendation" : "recommendations"}
          </span>
          {handoff.artifacts.length > 0 && (
            <>
              <span>•</span>
              <span>
                {handoff.artifacts.length}{" "}
                {handoff.artifacts.length === 1 ? "artifact" : "artifacts"}
              </span>
            </>
          )}
          <span>•</span>
          <span>{formatDateTime(handoff.created_at)}</span>
        </div>
      </div>

      {/* Expanded Details */}
      {isExpanded && (
        <div className="px-4 pb-4 pl-6 space-y-3 border-t border-gray-100 pt-3">
          {/* Full Summary */}
          <div>
            <h4 className="text-xs font-medium text-gray-500 uppercase mb-1">Summary</h4>
            <p className="text-sm text-gray-700 whitespace-pre-wrap">{handoff.summary}</p>
          </div>

          {/* Recommendations */}
          {handoff.recommendations.length > 0 && (
            <div>
              <h4 className="text-xs font-medium text-gray-500 uppercase mb-1">
                Recommendations
              </h4>
              <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                {handoff.recommendations.map((rec, i) => (
                  <li key={i}>{rec}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Artifacts */}
          {handoff.artifacts.length > 0 && (
            <div>
              <h4 className="text-xs font-medium text-gray-500 uppercase mb-1">Artifacts</h4>
              <div className="bg-gray-50 rounded p-2">
                {handoff.artifacts.map((artifact, i) => (
                  <div key={i} className="text-xs font-mono text-gray-600 bg-white rounded px-2 py-1 mb-1 last:mb-0">
                    {typeof artifact === "string" ? artifact : JSON.stringify(artifact, null, 2)}
                  </div>
                ))}
              </div>
            </div>
          )}
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
    <div className="flex items-center justify-center py-12">
      <div className="text-center">
        <div className="inline-block animate-spin rounded-full h-6 w-6 border-3 border-gray-200 border-t-blue-600 mb-2" />
        <p className="text-sm text-gray-500">Loading handoffs...</p>
      </div>
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
          d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
        />
      </svg>
      <h3 className="text-sm font-medium text-gray-900 mb-1">No handoffs yet</h3>
      <p className="text-xs text-gray-500">
        Handoffs will appear here as nodes complete and transfer data.
      </p>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function HandoffList({ missionId }: HandoffListProps) {
  const [expandedHandoffs, setExpandedHandoffs] = useState<Set<string>>(new Set());

  const { data, isLoading, isError, refetch } = useMissionHandoffs(missionId);

  const handleHandoffClick = (handoffId: string) => {
    setExpandedHandoffs((prev) => {
      const next = new Set(prev);
      if (next.has(handoffId)) {
        next.delete(handoffId);
      } else {
        next.add(handoffId);
      }
      return next;
    });
  };

  const handleExpandAll = () => {
    if (data && data.handoffs.length > 0) {
      if (expandedHandoffs.size === data.handoffs.length) {
        setExpandedHandoffs(new Set());
      } else {
        setExpandedHandoffs(new Set(data.handoffs.map((h) => h.id)));
      }
    }
  };

  // Calculate stats
  const richCount = data?.handoffs.filter((h) => h.format === "rich").length || 0;
  const avgConfidence =
    data && data.handoffs.length > 0
      ? data.handoffs.reduce((sum, h) => sum + h.confidence, 0) / data.handoffs.length
      : 0;

  return (
    <div className="bg-white border rounded-lg shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-gray-50 border-b flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Handoffs</h2>
        <div className="flex items-center gap-3">
          {data && data.handoffs.length > 0 && (
            <>
              <span className="text-sm text-gray-500">
                {data.handoffs.length} total
              </span>
              <span className="text-sm text-purple-600">
                {richCount} rich
              </span>
              {avgConfidence > 0 && (
                <span className={`text-sm font-medium ${getConfidenceColor(avgConfidence)}`}>
                  {formatConfidence(avgConfidence)} avg confidence
                </span>
              )}
              <button
                onClick={handleExpandAll}
                className="text-sm text-blue-600 hover:text-blue-700"
              >
                {expandedHandoffs.size === data.handoffs.length ? "Collapse" : "Expand"} All
              </button>
            </>
          )}
          {isError && (
            <button
              onClick={() => refetch()}
              className="text-sm text-red-600 hover:text-red-700"
            >
              Retry
            </button>
          )}
        </div>
      </div>

      {/* Handoff List */}
      <div className="max-h-[500px] overflow-y-auto">
        {isLoading ? (
          <LoadingState />
        ) : isError ? (
          <div className="px-4 py-8 text-center text-red-500">
            Failed to load handoffs
          </div>
        ) : !data || data.handoffs.length === 0 ? (
          <EmptyState />
        ) : (
          data.handoffs.map((handoff) => (
            <HandoffItemRow
              key={handoff.id}
              handoff={handoff}
              onClick={() => handleHandoffClick(handoff.id)}
              isExpanded={expandedHandoffs.has(handoff.id)}
            />
          ))
        )}
      </div>
    </div>
  );
}
