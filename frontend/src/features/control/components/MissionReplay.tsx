/**
 * Operator Control Surface - Mission Replay Component
 *
 * Timeline-based replay of mission execution allowing step-by-step
 * inspection of how the mission unfolded.
 */

import { useState, useEffect, useRef, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { formatDateTime, getSeverityBadgeStyle } from "../utils/formatters";
import type { EventItem } from "../types/mission";

// ============================================================================
// Types
// ============================================================================

interface MissionReplayProps {
  missionId: string;
}

interface ReplayState {
  isPlaying: boolean;
  currentEventIndex: number;
  speed: number; // milliseconds per event
}

// ============================================================================
// API
// ============================================================================

async function getMissionEventsForReplay(missionId: string): Promise<{
  events: EventItem[];
  total: number;
}> {
  const API_BASE_URL = import.meta.env.VITE_API_URL || "/api";
  const response = await fetch(
    `${API_BASE_URL}/control/missions/${missionId}/events?limit=1000`
  );
  if (!response.ok) throw new Error("Failed to fetch events for replay");
  return response.json();
}

// ============================================================================
// Replay Controls Component
// ============================================================================

interface ReplayControlsProps {
  state: ReplayState;
  eventCount: number;
  onPlayPause: () => void;
  onReset: () => void;
  onSeek: (index: number) => void;
  onSpeedChange: (speed: number) => void;
}

function ReplayControls({
  state,
  eventCount,
  onPlayPause,
  onReset,
  onSeek,
  onSpeedChange,
}: ReplayControlsProps) {
  const progress = eventCount > 0 ? ((state.currentEventIndex + 1) / eventCount) * 100 : 0;

  return (
    <div className="flex items-center gap-4 p-3 bg-gray-50 border-b">
      {/* Play/Pause Button */}
      <button
        onClick={onPlayPause}
        className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
        disabled={eventCount === 0}
      >
        {state.isPlaying ? (
          <>
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path d="M5 4h3v12H5V4zm7 0h3v12h-3V4z" />
            </svg>
            Pause
          </>
        ) : (
          <>
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
            </svg>
            Play
          </>
        )}
      </button>

      {/* Reset Button */}
      <button
        onClick={onReset}
        className="p-1.5 text-gray-600 hover:text-gray-900 hover:bg-gray-200 rounded transition-colors"
        title="Reset to start"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      </button>

      {/* Progress Bar */}
      <div className="flex-1 flex items-center gap-2">
        <span className="text-xs text-gray-500 w-12">
          {state.currentEventIndex + 1} / {eventCount}
        </span>
        <input
          type="range"
          min={0}
          max={Math.max(eventCount - 1, 0)}
          value={state.currentEventIndex}
          onChange={(e) => onSeek(parseInt(e.target.value))}
          className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
          disabled={state.isPlaying || eventCount === 0}
        />
        <span className="text-xs text-gray-500 w-12 text-right">
          {Math.round(progress)}%
        </span>
      </div>

      {/* Speed Control */}
      <select
        value={state.speed}
        onChange={(e) => onSpeedChange(parseInt(e.target.value))}
        className="px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
      >
        <option value={2000}>Slow</option>
        <option value={1000}>Normal</option>
        <option value={500}>Fast</option>
        <option value={200}>Very Fast</option>
      </select>
    </div>
  );
}

// ============================================================================
// Current Event Display
// ============================================================================

interface CurrentEventDisplayProps {
  event: EventItem | null;
  index: number;
  total: number;
}

function CurrentEventDisplay({ event, index, total }: CurrentEventDisplayProps) {
  if (!event) {
    return (
      <div className="p-8 text-center text-gray-500">
        <p>Click Play to start the replay</p>
      </div>
    );
  }

  const style = getSeverityBadgeStyle(event.severity);

  return (
    <div className="p-4 border-b">
      <div className="flex items-center gap-3 mb-3">
        <span className="text-sm text-gray-500">
          Event {index + 1} of {total}
        </span>
        <span className="text-gray-400">•</span>
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded text-xs ${style.bgColor} ${style.textColor}`}
        >
          {style.icon} {event.severity}
        </span>
        <span className="text-gray-400">•</span>
        <span className="text-sm text-gray-500" title={formatDateTime(event.created_at)}>
          {event.created_at}
        </span>
      </div>

      <div className="text-lg font-medium text-gray-900 mb-1">
        {event.event_type.replace(/\./g, " ").replace(/_/g, " ").toUpperCase()}
      </div>

      <div className="text-sm text-gray-600 mb-2">
        Entity: <span className="font-mono">{event.entity_id.substring(0, 12)}...</span>
        <span className="mx-2">•</span>
        Type: <span className="font-mono">{event.entity_type}</span>
      </div>

      {event.event_data && Object.keys(event.event_data).length > 0 && (
        <div className="mt-3">
          <details className="group">
            <summary className="text-sm text-blue-600 cursor-pointer hover:text-blue-700">
              Event Data
            </summary>
            <div className="mt-2 p-3 bg-gray-900 rounded-md">
              <pre className="text-xs text-gray-100 overflow-x-auto">
                {JSON.stringify(event.event_data, null, 2)}
              </pre>
            </div>
          </details>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Event List Component
// ============================================================================

interface EventListProps {
  events: EventItem[];
  currentIndex: number;
  onEventClick: (index: number) => void;
}

function EventList({ events, currentIndex, onEventClick }: EventListProps) {
  return (
    <div className="h-64 overflow-y-auto border-t">
      <table className="w-full">
        <thead className="bg-gray-50 sticky top-0">
          <tr>
            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase w-16">
              #
            </th>
            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
              Event
            </th>
            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase w-20">
              Severity
            </th>
            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase w-24">
              Time
            </th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {events.map((event, index) => (
            <tr
              key={event.id}
              onClick={() => onEventClick(index)}
              className={`cursor-pointer transition-colors ${
                index === currentIndex
                  ? "bg-blue-50"
                  : "hover:bg-gray-50"
              }`}
            >
              <td className="px-3 py-2 text-sm text-gray-500">{index + 1}</td>
              <td className="px-3 py-2 text-sm text-gray-900">
                {event.event_type.split(".").pop()}
              </td>
              <td className="px-3 py-2">
                <span
                  className={`inline-flex items-center justify-center w-5 h-5 rounded text-xs ${
                    event.severity === "error"
                      ? "bg-red-100 text-red-700"
                      : event.severity === "warning"
                      ? "bg-yellow-100 text-yellow-700"
                      : "bg-blue-100 text-blue-700"
                  }`}
                >
                  {event.severity === "error" ? "✖" : event.severity === "warning" ? "⚠" : "•"}
                </span>
              </td>
              <td className="px-3 py-2 text-xs text-gray-500">
                {new Date(event.created_at).toLocaleTimeString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
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
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-gray-200 border-t-blue-600 mb-4" />
        <p className="text-sm text-gray-500">Loading replay data...</p>
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
          d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
        />
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <h3 className="text-sm font-medium text-gray-900 mb-1">No events to replay</h3>
      <p className="text-xs text-gray-500">
        This mission doesn't have any recorded events yet.
      </p>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function MissionReplay({ missionId }: MissionReplayProps) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["control", "mission-replay", missionId],
    queryFn: () => getMissionEventsForReplay(missionId),
    enabled: !!missionId,
    refetchOnWindowFocus: false,
  });

  const [state, setState] = useState<ReplayState>({
    isPlaying: false,
    currentEventIndex: 0,
    speed: 1000,
  });

  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Handle playback
  useEffect(() => {
    if (!state.isPlaying || !data || data.events.length === 0) return;

    if (state.currentEventIndex >= data.events.length - 1) {
      setState({ ...state, isPlaying: false });
      return;
    }

    timeoutRef.current = setTimeout(() => {
      setState((prev) => ({
        ...prev,
        currentEventIndex: Math.min(prev.currentEventIndex + 1, data.events.length - 1),
      }));
    }, state.speed);

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [state.isPlaying, state.currentEventIndex, state.speed, data?.events.length]);

  const handlePlayPause = useCallback(() => {
    if (!data || data.events.length === 0) return;

    // If we're at the end, reset to start
    if (state.currentEventIndex >= data.events.length - 1) {
      setState({ ...state, isPlaying: true, currentEventIndex: 0 });
    } else {
      setState({ ...state, isPlaying: !state.isPlaying });
    }
  }, [state, data?.events.length]);

  const handleReset = useCallback(() => {
    setState({ ...state, isPlaying: false, currentEventIndex: 0 });
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
  }, [state]);

  const handleSeek = useCallback((index: number) => {
    setState({ ...state, currentEventIndex: index, isPlaying: false });
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
  }, [state]);

  const handleSpeedChange = useCallback((speed: number) => {
    setState({ ...state, speed });
  }, [state]);

  const handleEventClick = useCallback((index: number) => {
    setState({ ...state, currentEventIndex: index, isPlaying: false });
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
  }, [state]);

  if (isLoading) {
    return (
      <div className="bg-white border rounded-lg shadow-sm overflow-hidden">
        <LoadingState />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-white border rounded-lg shadow-sm overflow-hidden">
        <div className="p-8 text-center text-red-500">Failed to load replay data</div>
      </div>
    );
  }

  if (!data || data.events.length === 0) {
    return (
      <div className="bg-white border rounded-lg shadow-sm overflow-hidden">
        <EmptyState />
      </div>
    );
  }

  const currentEvent = data.events[state.currentEventIndex];

  return (
    <div className="bg-white border rounded-lg shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-gray-50 border-b flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-lg font-semibold text-gray-900">Mission Replay</span>
          <span className="text-sm text-gray-500">({data.events.length} events)</span>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>Step through mission execution</span>
        </div>
      </div>

      {/* Controls */}
      <ReplayControls
        state={state}
        eventCount={data.events.length}
        onPlayPause={handlePlayPause}
        onReset={handleReset}
        onSeek={handleSeek}
        onSpeedChange={handleSpeedChange}
      />

      {/* Current Event */}
      <CurrentEventDisplay
        event={currentEvent}
        index={state.currentEventIndex}
        total={data.events.length}
      />

      {/* Event List */}
      <EventList
        events={data.events}
        currentIndex={state.currentEventIndex}
        onEventClick={handleEventClick}
      />
    </div>
  );
}
