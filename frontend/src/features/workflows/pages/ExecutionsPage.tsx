/**
 * Phase 3: Product UX & Identity
 *
 * Executions Page with enhanced UX
 * Empty states, consistent headers, better polish
 */

import { Link, useNavigate } from "react-router-dom";
import { useExecutions } from "../hooks/useWorkflows";
import { ExecutionListTable } from "../components/ExecutionListTable";
import { ExecutionEmptyState } from "@/components/empty-states";
import { PageHeader } from "@/components/page-headers";
import { TableSkeleton } from "@/components/loading/Skeleton";
import { RefreshCw, Plus, Activity } from "lucide-react";

export function ExecutionsPage() {
  const navigate = useNavigate();
  const { data: executions, isLoading, error, refetch } = useExecutions();

  const hasExecutions = executions && executions.length > 0;

  // Loading state
  if (isLoading) {
    return (
      <div className="flex flex-col h-full">
        <PageHeader
          title="Executions"
          description="Monitor workflow runs and inspect results"
          onRefresh={() => refetch()}
          isLoading={isLoading}
          primaryAction={{
            label: "New Workflow",
            icon: <Plus className="w-4 h-4" />,
            onClick: () => navigate("/workflows/new"),
          }}
        />
        <div className="flex-1 px-6 py-4">
          <TableSkeleton rows={5} columns={6} />
        </div>
      </div>
    );
  }

  // Empty state
  if (!hasExecutions && !isLoading) {
    return (
      <div className="flex flex-col h-full">
        <PageHeader
          title="Executions"
          description="Monitor workflow runs and inspect results"
          onRefresh={() => refetch()}
        />
        <div className="flex-1">
          <ExecutionEmptyState onCreateWorkflow={() => navigate("/workflows/new")} />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <PageHeader
        title="Executions"
        description="Monitor workflow runs and inspect results"
        onRefresh={() => refetch()}
        isLoading={isLoading}
        meta={
          !isLoading && hasExecutions && (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-green-50 text-green-700 text-sm rounded-full">
              <Activity className="w-4 h-4 animate-pulse" />
              <span>Auto-refreshing every 5 seconds</span>
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
          <p className="text-sm text-red-600">Failed to load executions: {error.message}</p>
        </div>
      )}

      {/* Execution List */}
      <div className="flex-1 px-6 py-4">
        <ExecutionListTable executions={executions || []} isLoading={isLoading} />
      </div>
    </div>
  );
}
