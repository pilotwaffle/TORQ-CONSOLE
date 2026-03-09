/**
 * Operator Control Surface - Mission Types
 *
 * TypeScript types for the mission control surface UI.
 * These mirror the Pydantic models from the backend API.
 */

// ============================================================================
// Mission Types
// ============================================================================

export type MissionStatus =
  | "draft"
  | "planned"
  | "scheduled"
  | "running"
  | "paused"
  | "completed"
  | "failed"
  | "cancelled";

export type MissionType =
  | "analysis"
  | "planning"
  | "evaluation"
  | "design"
  | "transformation";

// ============================================================================
// Node Types
// ============================================================================

export type NodeType =
  | "objective"
  | "task"
  | "decision"
  | "evidence"
  | "deliverable";

export type NodeState =
  | "completed"
  | "running"
  | "ready"
  | "pending"
  | "failed"
  | "blocked"
  | "skipped";

// ============================================================================
// Workstream Types
// ============================================================================

export type WorkstreamHealth =
  | "healthy"
  | "at_risk"
  | "failed"
  | "idle";

// ============================================================================
// Event Types
// ============================================================================

export type EventSeverity = "info" | "warning" | "error";

// ============================================================================
// Handoff Types
// ============================================================================

export type HandoffFormat = "rich" | "minimal";

// ============================================================================
// API Response Types
// ============================================================================

export interface MissionProgress {
  completed: number;
  total: number;
  percent: number;
}

export interface MissionListItem {
  id: string;
  title: string;
  objective: string;
  status: MissionStatus;
  mission_type: MissionType;
  progress: MissionProgress;
  created_at: string;
  updated_at: string;
}

export interface MissionListResponse {
  missions: MissionListItem[];
  total: number;
  page: number;
  per_page: number;
}

export interface MissionDetail {
  mission: {
    id: string;
    title: string;
    objective: string;
    status: MissionStatus;
    mission_type: MissionType;
    reasoning_strategy: string | null;
    context: Record<string, unknown>;
    constraints: Record<string, unknown> | null;
    created_at: string;
    updated_at: string;
  };
  progress: MissionProgress;
  graph: {
    id: string;
    version: number;
    status: string;
    node_count: number;
    edge_count: number;
  } | null;
  node_count: number;
}

// ============================================================================
// Graph Types
// ============================================================================

export interface GraphNode {
  id: string;
  title: string;
  type: NodeType;
  status: NodeState;
  workstream_id: string | null;
  position: { x: number; y: number } | null;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  condition: string | null;
}

export interface MissionGraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// ============================================================================
// Node Detail Types
// ============================================================================

export interface NodeDetail {
  id: string;
  title: string;
  type: NodeType;
  status: NodeState;
  description: string | null;
  agent_type: string | null;
  workstream_id: string | null;
  output_summary: string | null;
  event_count: number;
  handoff_count: number;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  completed_at: string | null;
}

// ============================================================================
// Workstream Types
// ============================================================================

export interface WorkstreamStatus {
  id: string;
  name: string;
  health: WorkstreamHealth;
  progress: MissionProgress;
  active_nodes: number;
  blocked_nodes: number;
  failed_nodes: number;
  completed_nodes: number;
  total_nodes: number;
  last_activity: string | null;
}

export interface WorkstreamsResponse {
  workstreams: WorkstreamStatus[];
}

// ============================================================================
// Event Types
// ============================================================================

export interface EventItem {
  id: string;
  event_type: string;
  entity_id: string;
  entity_type: string;
  severity: EventSeverity;
  event_data: Record<string, unknown>;
  created_at: string;
}

export interface EventStreamResponse {
  events: EventItem[];
  total: number;
  limit: number;
  offset: number;
}

// ============================================================================
// Handoff Types
// ============================================================================

export interface HandoffItem {
  id: string;
  source_node_id: string;
  target_node_id: string;
  source_node_title: string;
  target_node_title: string;
  confidence: number;
  summary: string;
  artifacts: Array<Record<string, unknown>>;
  recommendations: string[];
  dependencies: string[];
  format: HandoffFormat;
  created_at: string;
}

export interface HandoffsResponse {
  handoffs: HandoffItem[];
}

export interface HandoffDetail extends HandoffItem {
  mission_id: string;
  unresolved_questions: string[];
  risks: string[];
  metadata: Record<string, unknown>;
}

// ============================================================================
// Dashboard Types
// ============================================================================

export interface DashboardSummary {
  status_counts: Record<string, number>;
  total_missions: number;
  active_missions_count: number;
  recent_events: EventItem[];
  active_missions: MissionListItem[];
}

// ============================================================================
// Filter/Query Types
// ============================================================================

export interface MissionListFilters {
  status?: MissionStatus;
  mission_type?: MissionType;
  page?: number;
  per_page?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}

export interface EventFilters {
  limit?: number;
  offset?: number;
  event_type?: string;
  severity?: EventSeverity;
  entity_type?: string;
}

export interface HandoffFilters {
  source_node_id?: string;
  target_node_id?: string;
}

// ============================================================================
// UI State Types
// ============================================================================

export interface ControlSurfaceState {
  selectedMissionId: string | null;
  selectedNodeId: string | null;
  activeTab: "graph" | "workstreams" | "events" | "handoffs";
  filters: MissionListFilters;
  isStreaming: boolean;
}

// ============================================================================
// Color Mapping Types
// ============================================================================

export const NODE_STATUS_COLORS: Record<NodeState, string> = {
  completed: "#10b981", // green-500
  running: "#3b82f6",   // blue-500
  ready: "#f59e0b",     // amber-500
  pending: "#6b7280",   // gray-500
  failed: "#ef4444",    // red-500
  blocked: "#f97316",   // orange-500
  skipped: "#8b5cf6",   // violet-500
};

export const WORKSTREAM_HEALTH_COLORS: Record<WorkstreamHealth, string> = {
  healthy: "#10b981",  // green-500
  at_risk: "#f59e0b",  // amber-500
  failed: "#ef4444",   // red-500
  idle: "#6b7280",     // gray-500
};

export const MISSION_STATUS_COLORS: Partial<Record<MissionStatus, string>> = {
  draft: "#6b7280",
  planned: "#3b82f6",
  scheduled: "#8b5cf6",
  running: "#f59e0b",
  paused: "#f97316",
  completed: "#10b981",
  failed: "#ef4444",
  cancelled: "#6b7280",
};

export const EVENT_SEVERITY_COLORS: Record<EventSeverity, string> = {
  info: "#3b82f6",
  warning: "#f59e0b",
  error: "#ef4444",
};
