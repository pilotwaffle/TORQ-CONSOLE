/**
 * Workflow Status Badge Component
 *
 * Reusable badge for displaying workflow/execution/node status.
 */

import { type WorkflowStatus, type ExecutionStatus, type NodeStatus } from "../api";
import {
  formatWorkflowStatus,
  getWorkflowStatusColor,
  formatExecutionStatus,
  getExecutionStatusColor,
  formatNodeStatus,
  getNodeStatusBgColor,
} from "../utils/workflowFormatters";

interface WorkflowStatusBadgeProps {
  status: WorkflowStatus | ExecutionStatus | NodeStatus;
  type?: "workflow" | "execution" | "node";
}

export function WorkflowStatusBadge({ status, type = "workflow" }: WorkflowStatusBadgeProps) {
  if (type === "execution") {
    return (
      <span
        className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium border ${getExecutionStatusColor(
          status as ExecutionStatus
        )}`}
      >
        {formatExecutionStatus(status as ExecutionStatus)}
      </span>
    );
  }

  if (type === "node") {
    return (
      <span
        className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium border ${getNodeStatusBgColor(
          status as NodeStatus
        )}`}
      >
        {formatNodeStatus(status as NodeStatus)}
      </span>
    );
  }

  return (
    <span
      className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium border ${getWorkflowStatusColor(
        status as WorkflowStatus
      )}`}
    >
      {formatWorkflowStatus(status as WorkflowStatus)}
    </span>
  );
}
