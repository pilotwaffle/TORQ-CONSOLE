/**
 * Phase 3: Product UX & Identity
 *
 * Workflows Page with enhanced UX
 * Empty states, consistent headers, better polish
 */

import { Link, useNavigate } from "react-router-dom";
import { useWorkflows, useArchiveWorkflow, useDeleteWorkflow, useExecuteWorkflow } from "../hooks/useWorkflows";
import { useWorkflowUiStore } from "../stores/workflowUiStore";
import { WorkflowListTable } from "../components/WorkflowListTable";
import { WorkflowEmptyState } from "@/components/empty-states";
import { PageHeader } from "@/components/page-headers";
import { WorkflowCardSkeleton, TableSkeleton } from "@/components/loading/Skeleton";
import { useToast } from "@/components/toasts";
import type { WorkflowGraph } from "../api";
import { Plus, RefreshCw, Filter, Archive, Trash2 } from "lucide-react";

export function WorkflowsPage() {
  const navigate = useNavigate();
  const { data: workflows, isLoading, error, refetch } = useWorkflows();
  const archiveWorkflow = useArchiveWorkflow();
  const deleteWorkflow = useDeleteWorkflow();
  const executeWorkflow = useExecuteWorkflow();
  const toast = useToast();

  const { statusFilter, setStatusFilter } = useWorkflowUiStore();

  // Filter workflows by status
  const filteredWorkflows = workflows?.filter((w) => {
    if (statusFilter && w.status !== statusFilter) return false;
    return true;
  }) || [];

  const hasWorkflows = workflows && workflows.length > 0;

  const handleExecute = (workflow: WorkflowGraph) => {
    executeWorkflow.mutate(
      { graphId: workflow.graph_id, request: { trigger_type: "manual" } },
      {
        onSuccess: (result) => {
          navigate(`/executions/${result.execution_id}`);
        },
        onError: (error) => {
          console.error("Failed to execute workflow:", error);
          toast.error("Failed to execute workflow. Please try again.");
        },
      }
    );
  };

  const handleArchive = (workflow: WorkflowGraph) => {
    // Phase 3: Use toast with action instead of confirm dialog
    toast.warning(`Archive workflow "${workflow.name}"?`, {
      title: 'Confirm Archive',
      action: {
        label: 'Archive',
        onClick: () => {
          archiveWorkflow.mutate(workflow.graph_id, {
            onSuccess: () => {
              refetch();
            },
            onError: (error) => {
              console.error("Failed to archive workflow:", error);
              toast.error("Failed to archive workflow. Please try again.");
            },
          });
        },
      },
    });
  };

  const handleDelete = (workflow: WorkflowGraph) => {
    // Phase 3: Use toast with action instead of confirm dialog
    toast.error(`Delete workflow "${workflow.name}"? This cannot be undone.`, {
      title: 'Confirm Delete',
      action: {
        label: 'Delete',
        onClick: () => {
          deleteWorkflow.mutate(workflow.graph_id, {
            onSuccess: () => {
              refetch();
            },
            onError: (error) => {
              console.error("Failed to delete workflow:", error);
              toast.error("Failed to delete workflow. Please try again.");
            },
          });
        },
      },
    });
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex flex-col h-full">
        <PageHeader
          title="Workflows"
          description="Manage and execute automated workflow graphs"
          onRefresh={() => refetch()}
          isLoading={isLoading}
          primaryAction={{
            label: "New Workflow",
            icon: <Plus className="w-4 h-4" />,
            onClick: () => navigate("/workflows/new"),
          }}
        />
        <div className="flex-1 px-6 py-4">
          <TableSkeleton rows={5} columns={5} />
        </div>
      </div>
    );
  }

  // Empty state
  if (!hasWorkflows && !isLoading) {
    return (
      <div className="flex flex-col h-full">
        <PageHeader
          title="Workflows"
          description="Manage and execute automated workflow graphs"
          onRefresh={() => refetch()}
          isLoading={isLoading}
          primaryAction={{
            label: "Create Workflow",
            icon: <Plus className="w-4 h-4" />,
            onClick: () => navigate("/workflows/new"),
          }}
        />
        <div className="flex-1">
          <WorkflowEmptyState onCreateWorkflow={() => navigate("/workflows/new")} />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header with consistent design */}
      <PageHeader
        title="Workflows"
        description="Manage and execute automated workflow graphs"
        onRefresh={() => refetch()}
        isLoading={isLoading}
        meta={
          !isLoading && hasWorkflows && (
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Filter className="w-4 h-4 text-gray-400" />
                <select
                  value={statusFilter || "all"}
                  onChange={(e) => setStatusFilter(e.target.value === "all" ? null : e.target.value)}
                  className="text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">All Status</option>
                  <option value="active">Active</option>
                  <option value="draft">Draft</option>
                  <option value="archived">Archived</option>
                </select>
              </div>
              <div className="text-sm text-gray-500">
                {filteredWorkflows.length} workflow{filteredWorkflows.length !== 1 ? "s" : ""}
              </div>
            </div>
          )
        }
        primaryAction={{
          label: "New Workflow",
          icon: <Plus className="w-4 h-4" />,
          onClick: () => navigate("/workflows/new"),
        }}
      />

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
