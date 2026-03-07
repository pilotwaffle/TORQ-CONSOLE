/**
 * Workflows Page
 *
 * Lists all workflow graphs with filtering and actions.
 */

import { Link } from "react-router-dom";
import { useWorkflows, useArchiveWorkflow, useDeleteWorkflow, useExecuteWorkflow } from "../hooks/useWorkflows";
import { useWorkflowUiStore } from "../stores/workflowUiStore";
import { WorkflowListTable } from "../components/WorkflowListTable";
import type { WorkflowGraph } from "../api";
import { Plus, RefreshCw, Filter } from "lucide-react";

export function WorkflowsPage() {
  const { data: workflows, isLoading, error, refetch } = useWorkflows();
  const archiveWorkflow = useArchiveWorkflow();
  const deleteWorkflow = useDeleteWorkflow();
  const executeWorkflow = useExecuteWorkflow();

  const { statusFilter, setStatusFilter } = useWorkflowUiStore();

  // Filter workflows by status
  const filteredWorkflows = workflows?.filter((w) => {
    if (statusFilter && w.status !== statusFilter) return false;
    return true;
  }) || [];

  const handleExecute = (workflow: WorkflowGraph) => {
    executeWorkflow.mutate(
      { graphId: workflow.graph_id, request: { trigger_type: "manual" } },
      {
        onSuccess: (result) => {
          window.location.href = `/executions/${result.execution_id}`;
        },
        onError: (error) => {
          console.error("Failed to execute workflow:", error);
          alert("Failed to execute workflow. Please try again.");
        },
      }
    );
  };

  const handleArchive = (workflow: WorkflowGraph) => {
    if (!confirm(`Archive workflow "${workflow.name}"?`)) return;

    archiveWorkflow.mutate(workflow.graph_id, {
      onSuccess: () => {
        refetch();
      },
      onError: (error) => {
        console.error("Failed to archive workflow:", error);
        alert("Failed to archive workflow. Please try again.");
      },
    });
  };

  const handleDelete = (workflow: WorkflowGraph) => {
    if (!confirm(`Delete workflow "${workflow.name}"? This cannot be undone.`)) return;

    deleteWorkflow.mutate(workflow.graph_id, {
      onSuccess: () => {
        refetch();
      },
      onError: (error) => {
        console.error("Failed to delete workflow:", error);
        alert("Failed to delete workflow. Please try again.");
      },
    });
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Workflows</h1>
          <p className="text-sm text-gray-500 mt-1">
            Manage and execute automated workflow graphs
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => refetch()}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <Link
            to="/workflows/new"
            className="inline-flex items-center px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition"
          >
            <Plus className="w-4 h-4 mr-2" />
            New Workflow
          </Link>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 px-6 py-3 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-400" />
          <select
            value={statusFilter || "all"}
            onChange={(e) => setStatusFilter(e.target.value === "all" ? null : e.target.value)}
            className="text-sm border border-gray-300 rounded px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-gray-200"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="draft">Draft</option>
            <option value="archived">Archived</option>
          </select>
        </div>
        <div className="text-sm text-gray-500">
          Showing {filteredWorkflows.length} workflow{filteredWorkflows.length !== 1 ? "s" : ""}
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="mx-6 mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-600">Failed to load workflows: {error.message}</p>
        </div>
      )}

      {/* Workflow List */}
      <div className="flex-1 px-6 py-4">
        <WorkflowListTable
          workflows={filteredWorkflows}
          isLoading={isLoading}
          onExecute={handleExecute}
          onArchive={handleArchive}
          onDelete={handleDelete}
        />
      </div>
    </div>
  );
}
