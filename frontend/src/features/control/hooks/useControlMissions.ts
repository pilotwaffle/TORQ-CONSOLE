/**
 * Operator Control Surface - React Hooks
 *
 * Custom React Query hooks for fetching mission control surface data.
 * Provides caching, refetching, and real-time updates for all control APIs.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useCallback } from "react";
import type {
  MissionListFilters,
  EventFilters,
  HandoffFilters,
  EventItem,
} from "../types/mission";
import {
  getMissions,
  getMissionDetail,
  getMissionGraph,
  getNodeDetail,
  getWorkstreamsHealth,
  getMissionEvents,
  createEventStream,
  getMissionHandoffs,
  getHandoffDetail,
  getDashboardSummary,
  controlQueryKeys,
} from "../api/controlApi";

// ============================================================================
// Mission Portfolio Hooks
// ============================================================================

/**
 * Hook for fetching the mission list with pagination and filtering
 */
export function useControlMissions(filters: MissionListFilters = {}) {
  return useQuery({
    queryKey: controlQueryKeys.missions(filters),
    queryFn: () => getMissions(filters),
    staleTime: 5000, // Consider data stale after 5 seconds
    refetchInterval: 10000, // Auto-refetch every 10 seconds
  });
}

/**
 * Hook for fetching mission detail
 */
export function useMissionDetail(missionId: string) {
  return useQuery({
    queryKey: controlQueryKeys.missionDetail(missionId),
    queryFn: () => getMissionDetail(missionId),
    enabled: !!missionId,
    staleTime: 5000,
    refetchInterval: 5000,
  });
}

// ============================================================================
// Mission Graph Hooks
// ============================================================================

/**
 * Hook for fetching mission graph for visualization
 */
export function useMissionGraph(missionId: string) {
  return useQuery({
    queryKey: controlQueryKeys.missionGraph(missionId),
    queryFn: () => getMissionGraph(missionId),
    enabled: !!missionId,
    staleTime: 10000, // Graph changes less frequently
    refetchInterval: 5000,
  });
}

/**
 * Hook for fetching node detail
 */
export function useNodeDetail(missionId: string, nodeId: string | null) {
  return useQuery({
    queryKey: controlQueryKeys.nodeDetail(missionId, nodeId || ""),
    queryFn: () => getNodeDetail(missionId, nodeId!),
    enabled: !!missionId && !!nodeId,
    staleTime: 3000,
    refetchInterval: 3000,
  });
}

// ============================================================================
// Workstream Health Hooks
// ============================================================================

/**
 * Hook for fetching workstream health status
 */
export function useWorkstreamsHealth(missionId: string) {
  return useQuery({
    queryKey: controlQueryKeys.workstreams(missionId),
    queryFn: () => getWorkstreamsHealth(missionId),
    enabled: !!missionId,
    staleTime: 5000,
    refetchInterval: 5000,
  });
}

// ============================================================================
// Event Stream Hooks
// ============================================================================

/**
 * Hook for fetching paginated events
 */
export function useMissionEvents(missionId: string, filters: EventFilters = {}) {
  return useQuery({
    queryKey: controlQueryKeys.events(missionId, filters),
    queryFn: () => getMissionEvents(missionId, filters),
    enabled: !!missionId,
    staleTime: 2000, // Events are very time-sensitive
    refetchInterval: 3000,
  });
}

/**
 * Hook for real-time event streaming via Server-Sent Events
 *
 * @param missionId - Mission to stream events for
 * @param enabled - Whether to start streaming
 * @param onEvent - Callback when new event arrives
 * @returns Object with connection status and controls
 */
export function useMissionEventStream(
  missionId: string,
  enabled: boolean = true,
  onEvent?: (event: EventItem) => void
) {
  const eventSourceRef = useRef<EventSource | null>(null);
  const queryClient = useQueryClient();
  const isConnectedRef = useRef(false);

  useEffect(() => {
    if (!enabled || !missionId) return;

    // Create SSE connection
    const eventSource = createEventStream(
      missionId,
      (data) => {
        isConnectedRef.current = true;
        // Invalidate events query to trigger refetch
        queryClient.invalidateQueries({
          queryKey: controlQueryKeys.events(missionId),
        });
        // Call custom callback if provided
        if (onEvent) {
          onEvent(data as EventItem);
        }
      },
      (error) => {
        console.error("Event stream error:", error);
        isConnectedRef.current = false;
      }
    );

    eventSourceRef.current = eventSource;

    // Cleanup on unmount
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
        isConnectedRef.current = false;
      }
    };
  }, [missionId, enabled, onEvent, queryClient]);

  const isConnected = isConnectedRef.current;

  const close = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      isConnectedRef.current = false;
    }
  }, []);

  return {
    isConnected,
    close,
  };
}

// ============================================================================
// Handoff Viewer Hooks
// ============================================================================

/**
 * Hook for fetching mission handoffs
 */
export function useMissionHandoffs(
  missionId: string,
  filters: HandoffFilters = {}
) {
  return useQuery({
    queryKey: controlQueryKeys.handoffs(missionId, filters),
    queryFn: () => getMissionHandoffs(missionId, filters),
    enabled: !!missionId,
    staleTime: 10000,
    refetchInterval: 10000,
  });
}

/**
 * Hook for fetching handoff detail
 */
export function useHandoffDetail(
  missionId: string,
  handoffId: string | null
) {
  return useQuery({
    queryKey: ["control", "handoff", missionId, handoffId],
    queryFn: () => getHandoffDetail(missionId, handoffId!),
    enabled: !!missionId && !!handoffId,
    staleTime: 30000, // Handoff details don't change often
  });
}

// ============================================================================
// Dashboard Hooks
// ============================================================================

/**
 * Hook for fetching dashboard summary
 */
export function useDashboardSummary() {
  return useQuery({
    queryKey: controlQueryKeys.dashboard(),
    queryFn: getDashboardSummary,
    staleTime: 15000, // Dashboard stats can be cached longer
    refetchInterval: 30000,
  });
}

// ============================================================================
// Utility Hooks
// ============================================================================

/**
 * Hook for auto-refreshing control surface data
 *
 * @param missionId - Mission to refresh data for
 * @param interval - Refresh interval in milliseconds
 */
export function useControlAutoRefresh(missionId: string, interval: number = 5000) {
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!missionId) return;

    const timer = setInterval(() => {
      // Invalidate all control queries for this mission
      queryClient.invalidateQueries({
        predicate: (query) => {
          const key = query.queryKey as Array<string | number | object>;
          return (
            Array.isArray(key) &&
            key[0] === "control" &&
            (key.includes(missionId) || key.length === 2)
          );
        },
      });
    }, interval);

    return () => clearInterval(timer);
  }, [missionId, interval, queryClient]);
}
