/**
 * Operator Control Surface - Node Timeline Component
 *
 * Displays the execution timeline for a specific node showing
 * when it started, events that occurred, and completion.
 */

import { useQuery } from "@tanstack/react-query";
import { formatDateTime, getSeverityBadgeStyle } from "../utils/formatters";
import type { EventItem } from "../types/mission";

// ============================================================================
// Types
// ============================================================================

interface NodeTimelineProps {
  missionId: string;
  nodeId: string;
}

// ============================================================================
// API
// ============================================================================

async function getNodeEvents(missionId: string, nodeId: string): Promise<EventItem[]> {
  const API_BASE_URL = import.meta.env.VITE_API_URL || "/api";
  const response = await fetch(
    `${API_BASE_URL}/control/missions/${missionId}/events?limit=100`
  );
  if (!response.ok) throw new Error("Failed to fetch node events");
  const data = await response.json();
  // Filter to only events for this node
  return data.events.filter((e: EventItem) => e.entity_id === nodeId);
}

// ============================================================================
// Timeline Event Component
// ============================================================================

interface TimelineEventProps {
  event: EventItem;
  index: number;
  total: number;
}

function TimelineEvent({ event, index, total }: TimelineEventProps) {
  const style = getSeverityBadgeStyle(event.severity);

  return (
    <div className="flex gap-3">
      {/* Timeline Line */}
      <div className="flex flex-col items-center">
        <div
          className={`w-3 h-3 rounded-full border-2 ${style.textColor.replace("text-", "bg-").replace("700", "100").replace("600", "100")} border-current`}
        />
        {index < total - 1 && (
          <div className="w-0.5 flex-1 bg-gray-200 my-1" />
        )}
      </div>

      {/* Event Content */}
      <div className="flex-1 pb-4">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-medium text-gray-900 text-sm">
            {event.event_type.replace(/\./g, " ").replace(/_/g, " ")}
          </span>
          <span
            className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs ${style.bgColor} ${style.textColor}`}
          >
            {style.icon}
          </span>
        </div>
        <div className="text-xs text-gray-500" title={formatDateTime(event.created_at)}>
          {event.created_at}
        </div>
        {event.event_data && Object.keys(event.event_data).length > 0 && (
          <details className="mt-2">
            <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-700">
              View data
            </summary>
            <div className="mt-1 p-2 bg-gray-900 rounded text-xs text-gray-100 overflow-x-auto">
              <pre>{JSON.stringify(event.event_data, null, 2)}</pre>
            </div>
          </details>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Loading State
// ============================================================================

function LoadingState() {
  return (
    <div className="flex items-center justify-center py-8">
      <div className="inline-block animate-spin rounded-full h-5 w-5 border-2 border-gray-200 border-t-blue-600" />
    </div>
  );
}

// ============================================================================
// Empty State
// ============================================================================

function EmptyState() {
  return (
    <div className="text-center py-8 text-gray-500 text-sm">
      No events recorded for this node yet.
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function NodeTimeline({ missionId, nodeId }: NodeTimelineProps) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["control", "node-timeline", missionId, nodeId],
    queryFn: () => getNodeEvents(missionId, nodeId),
    enabled: !!missionId && !!nodeId,
    refetchInterval: 5000,
  });

  if (isLoading) {
    return <LoadingState />;
  }

  if (isError) {
    return (
      <div className="text-center py-8 text-red-500 text-sm">
        Failed to load timeline
      </div>
    );
  }

  if (!data || data.length === 0) {
    return <EmptyState />;
  }

  // Calculate duration if we have started/completed events
  const startedEvent = data.find((e) => e.event_type === "node.started");
  const completedEvent = data.find((e) => e.event_type === "node.completed");

  let duration = null;
  if (startedEvent && completedEvent) {
    const start = new Date(startedEvent.created_at).getTime();
    const end = new Date(completedEvent.created_at).getTime();
    const seconds = Math.round((end - start) / 1000);
    duration = `${seconds}s`;
  } else if (startedEvent && !completedEvent) {
    const start = new Date(startedEvent.created_at).getTime();
    const now = Date.now();
    const seconds = Math.round((now - start) / 1000);
    duration = `${seconds}s (running)`;
  }

  return (
    <div className="border-t pt-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-sm font-medium text-gray-900">Execution Timeline</h4>
        {duration && (
          <span className="text-sm text-gray-500">Duration: {duration}</span>
        )}
      </div>

      {/* Timeline */}
      <div className="max-h-64 overflow-y-auto">
        {data.map((event, index) => (
          <TimelineEvent
            key={event.id}
            event={event}
            index={index}
            total={data.length}
          />
        ))}
      </div>
    </div>
  );
}
