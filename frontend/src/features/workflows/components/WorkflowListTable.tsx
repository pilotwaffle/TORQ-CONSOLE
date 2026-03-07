/**
 * Workflow List Table Component
 *
 * Displays a table of workflow graphs with actions.
 */

import { Link } from "react-router-dom";
import { formatWorkflowStatus, getWorkflowStatusColor, formatRelativeTime } from "../utils/workflowFormatters";
import type { WorkflowGraph } from "../api";
import { Clock, Play, Archive, Trash2, Eye } from "lucide-react";

interface WorkflowListTableProps {
  workflows: WorkflowGraph[];
  onExecute?: (workflow: WorkflowGraph) => void;
  onDelete?: (workflow: WorkflowGraph) => void;
  onArchive?: (workflow: WorkflowGraph) => void;
  isLoading?: boolean;
}

export function WorkflowListTable({
  workflows,
  onExecute,
  onDelete,
  onArchive,
  isLoading = false,
}: WorkflowListTableProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900" />
      </div>
    );
  }

  if (workflows.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-100 mb-4">
          <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-1">No workflows yet</h3>
        <p className="text-gray-500 mb-6">Create your first workflow to get started</p>
        <Link
          to="/workflows/new"
          className="inline-flex items-center px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition"
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Create Workflow
        </Link>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-200">
            <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Name</th>
            <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Status</th>
            <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Version</th>
            <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Updated</th>
            <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">Actions</th>
          </tr>
        </thead>
        <tbody>
          {workflows.map((workflow) => (
            <tr key={workflow.graph_id} className="border-b border-gray-100 hover:bg-gray-50">
              <td className="py-3 px-4">
                <div className="flex items-center">
                  <Link
                    to={`/workflows/${workflow.graph_id}`}
                    className="font-medium text-gray-900 hover:text-gray-700"
                  >
                    {workflow.name}
                  </Link>
                  {workflow.description && (
                    <p className="text-sm text-gray-500 truncate max-w-xs ml-4">
                      {workflow.description}
                    </p>
                  )}
                </div>
              </td>
              <td className="py-3 px-4">
                <span
                  className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium border ${getWorkflowStatusColor(
                    workflow.status
                  )}`}
                >
                  {formatWorkflowStatus(workflow.status)}
                </span>
              </td>
              <td className="py-3 px-4 text-sm text-gray-600">v{workflow.version}</td>
              <td className="py-3 px-4 text-sm text-gray-500">
                <div className="flex items-center">
                  <Clock className="w-3 h-3 mr-1" />
                  {formatRelativeTime(workflow.updated_at || workflow.created_at)}
                </div>
              </td>
              <td className="py-3 px-4">
                <div className="flex items-center justify-end gap-2">
                  {/* View */}
                  <Link
                    to={`/workflows/${workflow.graph_id}`}
                    className="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded"
                    title="View"
                  >
                    <Eye className="w-4 h-4" />
                  </Link>

                  {/* Execute */}
                  {workflow.status === "active" && onExecute && (
                    <button
                      onClick={() => onExecute(workflow)}
                      className="p-1.5 text-green-600 hover:text-green-700 hover:bg-green-50 rounded"
                      title="Execute"
                    >
                      <Play className="w-4 h-4" />
                    </button>
                  )}

                  {/* Archive */}
                  {workflow.status === "active" && onArchive && (
                    <button
                      onClick={() => onArchive(workflow)}
                      className="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded"
                      title="Archive"
                    >
                      <Archive className="w-4 h-4" />
                    </button>
                  )}

                  {/* Delete */}
                  {onDelete && (
                    <button
                      onClick={() => onDelete(workflow)}
                      className="p-1.5 text-red-500 hover:text-red-700 hover:bg-red-50 rounded"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
