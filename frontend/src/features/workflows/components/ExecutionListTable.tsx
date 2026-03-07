/**
 * Execution List Table Component
 *
 * Displays a table of workflow executions with status.
 */

import { Link } from "react-router-dom";
import { formatExecutionStatus, getExecutionStatusColor, formatDuration, formatRelativeTime } from "../utils/workflowFormatters";
import type { WorkflowExecution } from "../api";
import { Clock, ChevronRight, AlertCircle, CheckCircle2, Loader } from "lucide-react";

interface ExecutionListTableProps {
  executions: WorkflowExecution[];
  isLoading?: boolean;
}

export function ExecutionListTable({ executions, isLoading = false }: ExecutionListTableProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900" />
      </div>
    );
  }

  if (executions.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-100 mb-4">
          <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-1">No executions yet</h3>
        <p className="text-gray-500">Execute a workflow to see runs here</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-200">
            <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Execution</th>
            <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Workflow</th>
            <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Status</th>
            <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Started</th>
            <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Duration</th>
            <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">Actions</th>
          </tr>
        </thead>
        <tbody>
          {executions.map((execution) => (
            <tr key={execution.execution_id} className="border-b border-gray-100 hover:bg-gray-50">
              <td className="py-3 px-4">
                <code className="text-sm text-gray-600">{execution.execution_id.slice(0, 8)}...</code>
              </td>
              <td className="py-3 px-4">
                <span className="text-sm text-gray-900">{execution.graph_name || "Unknown"}</span>
              </td>
              <td className="py-3 px-4">
                <div className="flex items-center gap-2">
                  {execution.status === "running" && (
                    <Loader className="w-3 h-3 text-blue-500 animate-spin" />
                  )}
                  {execution.status === "completed" && (
                    <CheckCircle2 className="w-3 h-3 text-green-500" />
                  )}
                  {execution.status === "failed" && (
                    <AlertCircle className="w-3 h-3 text-red-500" />
                  )}
                  <span
                    className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium border ${getExecutionStatusColor(
                      execution.status
                    )}`}
                  >
                    {formatExecutionStatus(execution.status)}
                  </span>
                </div>
              </td>
              <td className="py-3 px-4 text-sm text-gray-500">
                <div className="flex items-center">
                  <Clock className="w-3 h-3 mr-1" />
                  {execution.started_at ? formatRelativeTime(execution.started_at) : "-"}
                </div>
              </td>
              <td className="py-3 px-4 text-sm text-gray-600">
                {formatDuration(execution.total_duration_ms)}
              </td>
              <td className="py-3 px-4">
                <Link
                  to={`/executions/${execution.execution_id}`}
                  className="flex items-center justify-end text-gray-500 hover:text-gray-700"
                >
                  <ChevronRight className="w-4 h-4" />
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
