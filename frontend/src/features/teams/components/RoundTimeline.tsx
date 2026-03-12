/**
 * Round Timeline Component
 *
 * Phase 5.2B: Observability + UI
 *
 * Displays event timeline in persisted order.
 * Uses backend order - no client-side sorting.
 */

import { useState, useEffect, useCallback, useRef } from 'react';

interface RoundTimelineProps {
  executionId: string;
  live?: boolean;
}

interface TimelineEvent {
  id: string;
  round_number: number;
  event_type: string;
  sender_role: string | null;
  receiver_role: string | null;
  content_preview: string | null;
  confidence: number | null;
  timestamp: string;
}

interface SSEEvent {
  type: string;
  data: TimelineEvent | { status: string } | any;
  timestamp?: string;
}

export function RoundTimeline({ executionId, live = false }: RoundTimelineProps) {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);

  // Track received event IDs to prevent duplicates
  const eventIdsRef = useRef(new Set<string>());

  const loadTimeline = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/teams/executions/${executionId}/timeline`);

      if (!response.ok) {
        throw new Error(`Failed to load timeline: ${response.statusText}`);
      }

      const result: TimelineEvent[] = await response.json();

      // Store event IDs
      result.forEach(event => {
        eventIdsRef.current.add(event.id);
      });

      setEvents(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [executionId]);

  // SSE connection for live updates
  useEffect(() => {
    if (!live) return;

    let eventSource: EventSource | null = null;

    const connectSSE = () => {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const sseUrl = `${apiUrl}/api/teams/executions/${executionId}/events/stream`;

      eventSource = new EventSource(sseUrl);

      eventSource.onopen = () => {
        setConnected(true);
      };

      eventSource.onerror = (err) => {
        setConnected(false);
        console.error('SSE error:', err);
      };

      eventSource.addEventListener('status', (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data);
          // Status updates don't add to timeline
          if (data.status === 'completed' || data.status === 'failed') {
            setConnected(false);
          }
        } catch (err) {
          console.error('Error parsing status event:', err);
        }
      });

      eventSource.addEventListener('complete', (e: MessageEvent) => {
        setConnected(false);
        if (eventSource) {
          eventSource.close();
        }
      });

      eventSource.addEventListener('error', (e: MessageEvent) => {
        setError(e.data?.message || 'Stream error');
        setConnected(false);
      });
    };

    connectSSE();

    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [executionId, live]);

  // Initial load
  useEffect(() => {
    loadTimeline();
  }, [loadTimeline]);

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 border border-gray-200 dark:border-gray-700">
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse">
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-2"></div>
              <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded w-full mb-1"></div>
              <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 rounded-lg shadow p-4 border border-red-200 dark:border-red-800">
        <p className="text-red-600 dark:text-red-400 text-sm">Error loading timeline: {error}</p>
      </div>
    );
  }

  // Group events by round
  const rounds = new Map<number, TimelineEvent[]>();
  events.forEach(event => {
    if (!rounds.has(event.round_number)) {
      rounds.set(event.round_number, []);
    }
    rounds.get(event.round_number)!.push(event);
  });

  // Get event type color
  const getEventTypeColor = (eventType: string) => {
    switch (eventType) {
      case 'role_to_role':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300';
      case 'validation_pass':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300';
      case 'validation_block':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300';
      case 'round_summary':
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
    }
  };

  // Format event type for display
  const formatEventType = (eventType: string) => {
    return eventType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 border border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
          Execution Timeline
        </h3>
        {live && (
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-gray-400'}`}></div>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {connected ? 'Live' : 'Connecting...'}
            </span>
          </div>
        )}
      </div>

      <div className="space-y-4">
        {Array.from(rounds.entries())
          .sort(([a], [b]) => a - b)
          .map(([roundNum, roundEvents]) => (
          <div key={roundNum} className="relative">
            {/* Round header */}
            <div className="flex items-center gap-2 mb-2">
              <div className="w-6 h-6 rounded-full bg-blue-500 text-white text-xs flex items-center justify-center font-medium">
                {roundNum}
              </div>
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Round {roundNum}
              </span>
              <span className="text-xs text-gray-500 dark:text-gray-400">
                {roundEvents.length} event{roundEvents.length !== 1 ? 's' : ''}
              </span>
            </div>

            {/* Events */}
            <div className="ml-8 space-y-2 border-l-2 border-gray-200 dark:border-gray-700 pl-4">
              {roundEvents.map((event, idx) => (
                <div key={event.id} className="relative">
                  {idx < roundEvents.length - 1 && (
                    <div className="absolute -left-6 top-4 w-4 h-px bg-gray-200 dark:bg-gray-700"></div>
                  )}

                  <div className={`inline-block px-2 py-1 rounded text-xs ${getEventTypeColor(event.event_type)}`}>
                    {formatEventType(event.event_type)}
                  </div>

                  <div className="mt-1 text-sm text-gray-900 dark:text-white">
                    {event.sender_role && (
                      <span className="font-medium capitalize">{event.sender_role}</span>
                    )}
                    {event.receiver_role && (
                      <>
                        <span className="text-gray-500"> → </span>
                        <span className="font-medium capitalize">{event.receiver_role}</span>
                      </>
                    )}
                  </div>

                  {event.content_preview && (
                    <div className="mt-1 text-xs text-gray-600 dark:text-gray-400 italic">
                      "{event.content_preview}"
                    </div>
                  )}

                  {event.confidence !== null && (
                    <div className="mt-1 text-xs">
                      <span className="text-gray-500 dark:text-gray-400">Confidence: </span>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {(event.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  )}

                  <div className="mt-1 text-xs text-gray-400 dark:text-gray-500">
                    {new Date(event.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {rounds.size === 0 && !loading && (
        <div className="text-center py-8 text-gray-500 dark:text-gray-400 text-sm">
          No events recorded yet
        </div>
      )}
    </div>
  );
}
