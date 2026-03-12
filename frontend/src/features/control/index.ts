/**
 * Operator Control Surface - Public API
 *
 * Main entry point for all control surface exports.
 */

// Pages
export { default as ControlPage } from "./pages/ControlPage";
export { default as MissionDetailPage } from "./pages/MissionDetailPage";

// Components
export { MissionPortfolioTable } from "./components/MissionPortfolioTable";
export { MissionDetailHeader } from "./components/MissionDetailHeader";
export { MissionGraphPanel } from "./components/MissionGraphPanel";
export { WorkstreamHealthPanel } from "./components/WorkstreamHealthPanel";
export { MissionEventStream } from "./components/MissionEventStream";
export { HandoffList } from "./components/HandoffList";
export { MissionReplay } from "./components/MissionReplay";
export { NodeTimeline } from "./components/NodeTimeline";

// Hooks
export {
  useControlMissions,
  useMissionDetail,
  useMissionGraph,
  useNodeDetail,
  useWorkstreamsHealth,
  useMissionEvents,
  useMissionEventStream,
  useMissionHandoffs,
  useHandoffDetail,
  useDashboardSummary,
  useControlAutoRefresh,
} from "./hooks/useControlMissions";

// API
export {
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
} from "./api/controlApi";

// Types
export type {
  MissionStatus,
  MissionType,
  NodeType,
  NodeState,
  WorkstreamHealth,
  EventSeverity,
  HandoffFormat,
  MissionListItem,
  MissionListResponse,
  MissionDetail,
  MissionProgress,
  GraphNode,
  GraphEdge,
  MissionGraphResponse,
  NodeDetail,
  WorkstreamStatus,
  WorkstreamsResponse,
  EventItem,
  EventStreamResponse,
  HandoffItem,
  HandoffsResponse,
  HandoffDetail,
  DashboardSummary,
  MissionListFilters,
  EventFilters,
  HandoffFilters,
  ControlSurfaceState,
} from "./types/mission";

// Utils
export {
  formatDateTime,
  formatRelativeTime,
  formatDuration,
  formatProgressPercent,
  formatProgressCount,
  getProgressColor,
  getStatusBadgeStyle,
  getHealthBadgeStyle,
  getSeverityBadgeStyle,
  truncateText,
  truncateWords,
  shortenId,
  formatNodeType,
  formatMissionType,
  formatConfidence,
  getConfidenceColor,
  getArrayLength,
  isEmptyArray,
} from "./utils/formatters";

// Constants
export {
  NODE_STATUS_COLORS,
  WORKSTREAM_HEALTH_COLORS,
  MISSION_STATUS_COLORS,
  EVENT_SEVERITY_COLORS,
} from "./types/mission";
