/**
 * Operator Control Surface - Mission Event Stream
 *
 * Real-time event stream viewer with Server-Sent Events support.
 * Shows mission events with filtering and auto-scroll capabilities.
 */

import { useState, useEffect, useRef, useCallback } from "react";
import {
  useMissionEvents,
  useMissionEventStream,
} from "../hooks/useControlMissions";
import {
  formatDateTime,
  formatRelativeTime,
  getSeverityBadgeStyle,
} from "../utils/formatters";
import type { EventSeverity, EventItem, EventFilters } from "../types/mission";

// ============================================================================
// Types
// ============================================================================

interface MissionEventStreamProps {
  missionId: string;
  maxHeight?: string;
}

// ============================================================================
// Severity Icon Component
// ============================================================================

function SeverityIcon({ severity }: { severity: EventSeverity }) {
  const style = getSeverityBadgeStyle(severity);

  return (
    <span
      className={`inline-flex items-center justify-center w-6 h-6 rounded ${style.bgColor} ${style.textColor} text-xs`}
      title={severity}
    >
      {style.icon}
    </span>
  );
}

// ============================================================================
// Event Item Component
// ============================================================================

interface EventItemRowProps {
  event: EventItem;
  onClick: () => void;
  isExpanded: boolean;
}

function EventItemRow({ event, onClick, isExpanded }: EventItemRowProps) {
  const style = getSeverityBadgeStyle(event.severity);

  return (
    <div
      onClick={onClick}
      className={`border-b last:border-b-0 hover:bg-gray-50 cursor-pointer transition-colors ${
        isExpanded ? "bg-blue-50" : ""
      }`}
    >
      <div className="px-4 py-2 flex items-start gap-3">
        {/* Severity Icon */}
        <div className="pt-0.5">
          <SeverityIcon severity={event.severity} />
        </div>

        {/* Event Content */}
        <div className="flex-1 min-w-0">
          {/* Event Type & Entity */}
          <div className="flex items-center gap-2 mb-0.5">
            <span className="font-medium text-gray-900 text-sm">
              {event.event_type.replace(/\./g, " ").replace(/_/g, " ")}
            </span>
            <span className="text-gray-400">•</span>
            <span className="text-xs text-gray-500 font-mono">
              {event.entity_type}
            </span>
          </div>

          {/* Entity ID (truncated) */}
          <div className="text-xs text-gray-500 mb-1">
            ID: <span className="font-mono">{event.entity_id.substring(0, 8)}...</span>
          </div>

          {/* Timestamp */}
          <div className="text-xs text-gray-400" title={formatDateTime(event.created_at)}>
            {formatRelativeTime(event.created_at)}
          </div>
        </div>

        {/* Expand Indicator */}
        <div className="pt-0.5">
          <svg
            className={`w-4 h-4 text-gray-400 transition-transform ${isExpanded ? "rotate-90" : ""}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </div>
      </div>

      {/* Expanded Data */}
      {isExpanded && (
        <div className="px-4 pb-3 pl-14">
          <div className="bg-gray-900 rounded-md p-3 overflow-x-auto">
            <pre className="text-xs text-gray-100 font-mono">
              {JSON.stringify(event.event_data, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Filter Bar Component
// ============================================================================

interface FilterBarProps {
  filters: EventFilters;
  onFiltersChange: (filters: EventFilters) => void;
  isStreaming: boolean;
  onToggleStream: () => void;
  autoScroll: boolean;
  onToggleAutoScroll: () => void;
}

function FilterBar({
  filters,
  onFiltersChange,
  isStreaming,
  onToggleStream,
  autoScroll,
  onToggleAutoScroll,
}: FilterBarProps) {
  return (
    <div className="flex flex-wrap items-center gap-3 p-3 bg-gray-50 border-b">
      {/* Severity Filter */}
      <select
        value={filters.severity || "all"}
        onChange={(e) =>
          onFiltersChange({
            ...filters,
            severity: e.target.value === "all" ? undefined : (e.target.value as EventSeverity),
          })
        }
        className="px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
      >
        <option value="all">All Severities</option>
        <option value="info">Info</option>
        <option value="warning">Warning</option>
        <option value="error">Error</option>
      </select>

      {/* Auto-scroll Toggle */}
      <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
        <input
          type="checkbox"
          checked={autoScroll}
          onChange={onToggleAutoScroll}
          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
        />
        Auto-scroll
      </label>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Live Indicator */}
      <button
        onClick={onToggleStream}
        className={`flex items-center gap-2 px-3 py-1 text-sm font-medium rounded transition-colors ${
          isStreaming
            ? "bg-green-100 text-green-700 hover:bg-green-200"
            : "bg-gray-100 text-gray-700 hover:bg-gray-200"
        }`}
      >
        <span
          className={`w-2 h-2 rounded-full ${
            isStreaming ? "bg-green-500 animate-pulse" : "bg-gray-400"
          }`}
        />
        {isStreaming ? "Live" : "Paused"}
      </button>
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
        <p className="text-sm text-gray-500">Loading events...</p>
      </div>
    </div>
  );
}

// ============================================================================
// Empty State
// ============================================================================

function EmptyState({ hasFilters }: { hasFilters: boolean }) {
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
          d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <h3 className="text-sm font-medium text-gray-900 mb-1">No events found</h3>
      <p className="text-xs text-gray-500">
        {hasFilters
          ? "Try adjusting your filters to see more events."
          : "Events will appear here as the mission progresses."}
      </p>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function MissionEventStream({ missionId, maxHeight = "600px" }: MissionEventStreamProps) {
  const [filters, setFilters] = useState<EventFilters>({ limit: 100 });
  const [expandedEvents, setExpandedEvents] = useState<Set<string>>(new Set());
  const [autoScroll, setAutoScroll] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  const { data, isLoading, isError, refetch } = useMissionEvents(missionId, filters);
  const { isConnected, close } = useMissionEventStream(missionId, true);

  // Auto-scroll to bottom when new events arrive
  useEffect(() => {
    if (autoScroll && scrollRef.current && data && data.events.length > 0) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [data?.events.length, autoScroll]);

  const handleEventClick = useCallback((eventId: string) => {
    setExpandedEvents((prev) => {
      const next = new Set(prev);
      if (next.has(eventId)) {
        next.delete(eventId);
      } else {
        next.add(eventId);
      }
      return next;
    });
  }, []);

  const handleToggleExpandAll = useCallback(() => {
    if (data && data.events.length > 0) {
      if (expandedEvents.size === data.events.length) {
        setExpandedEvents(new Set());
      } else {
        setExpandedEvents(new Set(data.events.map((e) => e.id)));
      }
    }
  }, [data, expandedEvents.size]);

  const hasActiveFilters = !!filters.severity || !!filters.event_type;

  if (isLoading && (!data || data.events.length === 0)) {
    return (
      <div className="bg-white border rounded-lg shadow-sm overflow-hidden">
        <div className="px-4 py-3 bg-gray-50 border-b">
          <h2 className="text-lg font-semibold text-gray-900">Event Stream</h2>
        </div>
        <LoadingState />
      </div>
    );
  }

  return (
    <div className="bg-white border rounded-lg shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-gray-50 border-b flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Event Stream</h2>
        <div className="flex items-center gap-3">
          {data && data.total > 0 && (
            <span className="text-sm text-gray-500">
              {data.total.toLocaleString()} events
            </span>
          )}
          {isError && (
            <button
              onClick={() => refetch()}
              className="text-sm text-red-600 hover:text-red-700"
            >
              Retry
            </button>
          )}
          {data && data.events.length > 0 && (
            <button
              onClick={handleToggleExpandAll}
              className="text-sm text-blue-600 hover:text-blue-700"
            >
              {expandedEvents.size === data.events.length ? "Collapse All" : "Expand All"}
            </button>
          )}
        </div>
      </div>

      {/* Filter Bar */}
      <FilterBar
        filters={filters}
        onFiltersChange={setFilters}
        isStreaming={isConnected}
        onToggleStream={() => {
          if (isConnected) {
            close();
          } else {
            // Re-enable by refetching, which will trigger stream on next render
            refetch();
          }
        }}
        autoScroll={autoScroll}
        onToggleAutoScroll={() => setAutoScroll((prev) => !prev)}
      />

      {/* Event List */}
      <div
        ref={scrollRef}
        className="overflow-y-auto"
        style={{ maxHeight }}
      >
        {!data || data.events.length === 0 ? (
          <EmptyState hasFilters={hasActiveFilters} />
        ) : (
          <div>
            {data.events.map((event) => (
              <EventItemRow
                key={event.id}
                event={event}
                onClick={() => handleEventClick(event.id)}
                isExpanded={expandedEvents.has(event.id)}
              />
            ))}

            {/* Load More Indicator */}
            {data.events.length < data.total && (
              <div className="px-4 py-3 text-center border-t">
                <button
                  onClick={() =>
                    setFilters((prev) => ({ ...prev, limit: (prev.limit || 100) + 100 }))
                  }
                  className="text-sm text-blue-600 hover:text-blue-700"
                >
                  Load more events
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
