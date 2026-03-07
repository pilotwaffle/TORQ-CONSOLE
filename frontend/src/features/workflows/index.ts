/**
 * Workflow Builder Feature Module
 *
 * Exports all components, hooks, and utilities for workflow management.
 */

// Pages
export { WorkflowsPage } from "./pages/WorkflowsPage";
export { ExecutionsPage } from "./pages/ExecutionsPage";

// Components
export { WorkflowListTable } from "./components/WorkflowListTable";
export { ExecutionListTable } from "./components/ExecutionListTable";
export { WorkflowStatusBadge } from "./components/WorkflowStatusBadge";

// Graph Components
export {
  WorkflowGraphCanvas,
  WorkflowNodeComponent,
  ExecutionGraphOverlay,
  GraphControls,
  NodeDetailsPanel,
} from "./components";

// Execution Monitor Components
export { ExecutionTimeline } from "./components/ExecutionTimeline";
export { LiveOutputPanel } from "./components/LiveOutputPanel";

// Creation Components
export { TemplateGallery } from "./components/TemplateGallery";
export { WorkflowEditor } from "./components/WorkflowEditor";
export { WorkflowPromptBuilder } from "./components/WorkflowPromptBuilder";
export { WorkflowDraftPreview } from "./components/WorkflowDraftPreview";

// Hooks
export {
  useWorkflows,
  useWorkflow,
  useCreateWorkflow,
  useUpdateWorkflowStatus,
  useDeleteWorkflow,
  useActivateWorkflow,
  useArchiveWorkflow,
  useExecutions,
  useExecution,
  useExecutionGraph,
  useExecuteWorkflow,
  useCancelExecution,
  useWorkflowTemplates,
  useWorkflowHealthCheck,
} from "./hooks/useWorkflows";

export {
  useExecutionMonitor,
  type ExecutionMonitorState,
  type ExecutionMonitorOptions,
} from "./hooks/useExecutionMonitor";

export {
  useDraftWorkflow,
  useWorkflowPlannerHealth,
} from "./hooks/useDraftWorkflow";

// Store
export { useWorkflowUiStore } from "./stores/workflowUiStore";

// Types
export type {
  WorkflowStatus,
  ExecutionStatus,
  NodeStatus,
  NodeType,
  TriggerType,
  WorkflowGraph,
  WorkflowNode,
  WorkflowEdge,
  WorkflowLimits,
  RetryPolicy,
  WorkflowExecution,
  ExecutionNodeResult,
  ExecutionGraphResponse,
  WorkflowTemplate,
  CreateWorkflowRequest,
  ExecuteWorkflowRequest,
  CreateWorkflowResponse,
  ExecuteWorkflowResponse,
} from "./api/workflowTypes";

// Utils
export {
  formatWorkflowStatus,
  formatExecutionStatus,
  formatNodeStatus,
  getWorkflowStatusColor,
  getExecutionStatusColor,
  getNodeStatusColor,
  getNodeStatusBgColor,
  formatRelativeTime,
  formatDuration,
  formatDate,
  formatNumber,
  formatBytes,
  formatRetryPolicy,
  formatExecutionSummary,
} from "./utils/workflowFormatters";
