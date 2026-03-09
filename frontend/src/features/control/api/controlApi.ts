/**
 * Operator Control Surface - API Client
 *
 * HTTP client for communicating with the Operator Control Surface backend APIs.
 * Uses fetch API with TypeScript typing for all endpoints.
 */

import type {
  MissionListResponse,
  MissionListFilters,
  MissionDetail,
  MissionGraphResponse,
  NodeDetail,
  WorkstreamsResponse,
  EventStreamResponse,
  EventFilters,
  HandoffsResponse,
  HandoffDetail,
  HandoffFilters,
  DashboardSummary,
} from "../types/mission";

// ============================================================================
// Configuration
// ============================================================================

const API_BASE_URL = import.meta.env.VITE_API_URL || "/api";

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      message: response.statusText,
    }));
    throw new Error(error.message || error.detail || "API request failed");
  }

  return response.json();
}

// ============================================================================
// Mission Portfolio API
// ============================================================================

/**
 * Get list of missions with pagination and filtering
 */
export async function getMissions(
  filters: MissionListFilters = {}
): Promise<MissionListResponse> {
  const params = new URLSearchParams();

  if (filters.status) params.append("status", filters.status);
  if (filters.mission_type) params.append("mission_type", filters.mission_type);
  params.append("page", String(filters.page || 1));
  params.append("per_page", String(filters.per_page || 20));
  params.append("sort_by", filters.sort_by || "updated_at");
  params.append("sort_order", filters.sort_order || "desc");

  const query = params.toString();
  return apiRequest<MissionListResponse>(`/control/missions${query ? `?${query}` : ""}`);
}

/**
 * Get detailed mission information
 */
export async function getMissionDetail(missionId: string): Promise<MissionDetail> {
  return apiRequest<MissionDetail>(`/control/missions/${missionId}/detail`);
}

// ============================================================================
// Mission Graph API
// ============================================================================

/**
 * Get mission graph for visualization
 */
export async function getMissionGraph(missionId: string): Promise<MissionGraphResponse> {
  return apiRequest<MissionGraphResponse>(`/control/missions/${missionId}/graph`);
}

/**
 * Get detailed node information
 */
export async function getNodeDetail(
  missionId: string,
  nodeId: string
): Promise<NodeDetail> {
  return apiRequest<NodeDetail>(`/control/missions/${missionId}/nodes/${nodeId}/detail`);
}

// ============================================================================
// Workstream Health API
// ============================================================================

/**
 * Get workstream health status for a mission
 */
export async function getWorkstreamsHealth(
  missionId: string
): Promise<WorkstreamsResponse> {
  return apiRequest<WorkstreamsResponse>(`/control/missions/${missionId}/workstreams/health`);
}

// ============================================================================
// Event Stream API
// ============================================================================

/**
 * Get paginated events for a mission
 */
export async function getMissionEvents(
  missionId: string,
  filters: EventFilters = {}
): Promise<EventStreamResponse> {
  const params = new URLSearchParams();

  params.append("limit", String(filters.limit || 100));
  params.append("offset", String(filters.offset || 0));
  if (filters.event_type) params.append("event_type", filters.event_type);
  if (filters.severity) params.append("severity", filters.severity);
  if (filters.entity_type) params.append("entity_type", filters.entity_type);

  const query = params.toString();
  return apiRequest<EventStreamResponse>(
    `/control/missions/${missionId}/events${query ? `?${query}` : ""}`
  );
}

/**
 * Create Server-Sent Events connection for real-time event streaming
 */
export function createEventStream(
  missionId: string,
  onMessage: (event: unknown) => void,
  onError?: (error: Event) => void
): EventSource {
  const url = `${API_BASE_URL}/control/missions/${missionId}/events/stream`;
  const eventSource = new EventSource(url);

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (e) {
      console.error("Failed to parse SSE data:", e);
    }
  };

  eventSource.onerror = (error) => {
    console.error("SSE error:", error);
    if (onError) onError(error);
  };

  return eventSource;
}

// ============================================================================
// Handoff Viewer API
// ============================================================================

/**
 * Get handoffs for a mission
 */
export async function getMissionHandoffs(
  missionId: string,
  filters: HandoffFilters = {}
): Promise<HandoffsResponse> {
  const params = new URLSearchParams();

  if (filters.source_node_id) params.append("source_node_id", filters.source_node_id);
  if (filters.target_node_id) params.append("target_node_id", filters.target_node_id);

  const query = params.toString();
  return apiRequest<HandoffsResponse>(
    `/control/missions/${missionId}/handoffs${query ? `?${query}` : ""}`
  );
}

/**
 * Get detailed handoff information
 */
export async function getHandoffDetail(
  missionId: string,
  handoffId: string
): Promise<HandoffDetail> {
  return apiRequest<HandoffDetail>(`/control/missions/${missionId}/handoffs/${handoffId}`);
}

// ============================================================================
// Dashboard API
// ============================================================================

/**
 * Get dashboard summary with aggregate statistics
 */
export async function getDashboardSummary(): Promise<DashboardSummary> {
  return apiRequest<DashboardSummary>("/control/dashboard/summary");
}

// ============================================================================
// React Query Keys
// ============================================================================

export const controlQueryKeys = {
  // Mission queries
  missions: (filters?: MissionListFilters) => ["control", "missions", filters] as const,
  missionDetail: (missionId: string) => ["control", "mission", missionId] as const,

  // Graph queries
  missionGraph: (missionId: string) => ["control", "graph", missionId] as const,
  nodeDetail: (missionId: string, nodeId: string) =>
    ["control", "node", missionId, nodeId] as const,

  // Workstream queries
  workstreams: (missionId: string) => ["control", "workstreams", missionId] as const,

  // Event queries
  events: (missionId: string, filters?: EventFilters) =>
    ["control", "events", missionId, filters] as const,

  // Handoff queries
  handoffs: (missionId: string, filters?: HandoffFilters) =>
    ["control", "handoffs", missionId, filters] as const,

  // Dashboard queries
  dashboard: () => ["control", "dashboard"] as const,
} as const;
