/**
 * Workflow Formatters
 *
 * Utility functions for formatting workflow data for display.
 */

import type { WorkflowStatus, ExecutionStatus, NodeStatus } from "../api";

// ============================================================================
// Status Formatters
// ============================================================================

/**
 * Get display label for workflow status
 */
export function formatWorkflowStatus(status: WorkflowStatus): string {
  const statusMap: Record<WorkflowStatus, string> = {
    draft: "Draft",
    active: "Active",
    archived: "Archived",
  };
  return statusMap[status] || status;
}

/**
 * Get display label for execution status
 */
export function formatExecutionStatus(status: ExecutionStatus): string {
  const statusMap: Record<ExecutionStatus, string> = {
    pending: "Pending",
    running: "Running",
    completed: "Completed",
    failed: "Failed",
    canceled: "Canceled",
  };
  return statusMap[status] || status;
}

/**
 * Get display label for node status
 */
export function formatNodeStatus(status: NodeStatus): string {
  const statusMap: Record<NodeStatus, string> = {
    pending: "Pending",
    running: "Running",
    completed: "Completed",
    failed: "Failed",
    skipped: "Skipped",
  };
  return statusMap[status] || status;
}

/**
 * Get color class for workflow status badge
 */
export function getWorkflowStatusColor(status: WorkflowStatus): string {
  const colorMap: Record<WorkflowStatus, string> = {
    draft: "bg-gray-100 text-gray-700 border-gray-300",
    active: "bg-green-100 text-green-700 border-green-300",
    archived: "bg-gray-50 text-gray-500 border-gray-200",
  };
  return colorMap[status] || "bg-gray-100 text-gray-700";
}

/**
 * Get color class for execution status badge
 */
export function getExecutionStatusColor(status: ExecutionStatus): string {
  const colorMap: Record<ExecutionStatus, string> = {
    pending: "bg-gray-100 text-gray-700 border-gray-300",
    running: "bg-blue-100 text-blue-700 border-blue-300",
    completed: "bg-green-100 text-green-700 border-green-300",
    failed: "bg-red-100 text-red-700 border-red-300",
    canceled: "bg-yellow-100 text-yellow-700 border-yellow-300",
  };
  return colorMap[status] || "bg-gray-100 text-gray-700";
}

/**
 * Get color class for node status in execution graph
 */
export function getNodeStatusColor(status: NodeStatus): string {
  const colorMap: Record<NodeStatus, string> = {
    pending: "fill-gray-300 stroke-gray-400",
    running: "fill-blue-400 stroke-blue-600",
    completed: "fill-green-400 stroke-green-600",
    failed: "fill-red-400 stroke-red-600",
    skipped: "fill-yellow-200 stroke-yellow-400",
  };
  return colorMap[status] || "fill-gray-300 stroke-gray-400";
}

/**
 * Get background color class for node status
 */
export function getNodeStatusBgColor(status: NodeStatus): string {
  const colorMap: Record<NodeStatus, string> = {
    pending: "bg-gray-50 border-gray-300",
    running: "bg-blue-50 border-blue-400",
    completed: "bg-green-50 border-green-400",
    failed: "bg-red-50 border-red-400",
    skipped: "bg-yellow-50 border-yellow-300",
  };
  return colorMap[status] || "bg-gray-50 border-gray-300";
}

// ============================================================================
// Time Formatters
// ============================================================================

/**
 * Format relative time (e.g., "2h ago", "3d ago")
 */
export function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  // For older dates, show the actual date
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

/**
 * Format duration in milliseconds to human-readable string
 */
export function formatDuration(ms: number | undefined): string {
  if (ms === undefined || ms === null) return "-";

  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  if (ms < 3600000) return `${Math.floor(ms / 60000)}m ${Math.floor((ms % 60000) / 1000)}s`;

  const hours = Math.floor(ms / 3600000);
  const mins = Math.floor((ms % 3600000) / 60000);
  return `${hours}h ${mins}m`;
}

/**
 * Format date to locale string
 */
export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: date.getFullYear() !== new Date().getFullYear() ? "numeric" : undefined,
    hour: "2-digit",
    minute: "2-digit",
  });
}

// ============================================================================
// Number Formatters
// ============================================================================

/**
 * Format number with abbreviated suffixes (K, M, B)
 */
export function formatNumber(num: number): string {
  if (num < 1000) return num.toString();
  if (num < 1000000) return `${(num / 1000).toFixed(1)}K`;
  if (num < 1000000000) return `${(num / 1000000).toFixed(1)}M`;
  return `${(num / 1000000000).toFixed(1)}B`;
}

/**
 * Format bytes to human-readable string
 */
export function formatBytes(bytes: number | undefined): string {
  if (bytes === undefined || bytes === null) return "-";

  const units = ["B", "KB", "MB", "GB"];
  let size = bytes;
  let unitIndex = 0;

  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }

  return `${size.toFixed(unitIndex > 0 ? 1 : 0)}${units[unitIndex]}`;
}

// ============================================================================
// Retry Policy Formatters
// ============================================================================

/**
 * Format retry policy for display
 */
export function formatRetryPolicy(retryPolicy: {
  max_retries?: number;
  retry_delay_ms?: number;
} | undefined): string {
  if (!retryPolicy) return "Default";

  const maxRetries = retryPolicy.max_retries ?? 3;
  const delay = (retryPolicy.retry_delay_ms ?? 1000) / 1000;

  return `Retry ${maxRetries}x, ${delay}s delay`;
}

// ============================================================================
// Summary Formatters
// ============================================================================

/**
 * Format execution summary text
 */
export function formatExecutionSummary(summary: {
  total_nodes: number;
  completed: number;
  failed: number;
  running: number;
  pending: number;
}): string {
  const { total_nodes, completed, failed, running, pending } = summary;
  const done = completed + failed;

  if (done === total_nodes) {
    return failed > 0
      ? `${completed}/${total_nodes} completed, ${failed} failed`
      : "All nodes completed";
  }

  return `${done}/${total_nodes} completed${running > 0 ? `, ${running} running` : ""}`;
}
