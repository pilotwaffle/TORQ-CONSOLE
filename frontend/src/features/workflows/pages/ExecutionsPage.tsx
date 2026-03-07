/**
 * Executions Page
 *
 * Lists all workflow executions with live status updates.
 */

import { Link } from "react-router-dom";
import { useExecutions } from "../hooks/useWorkflows";
import { ExecutionListTable } from "../components/ExecutionListTable";
import { RefreshCw, Plus } from "lucide-react";

export function ExecutionsPage() {
  const { data: executions, isLoading, error, refetch } = useExecutions();

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Executions</h1>
          <p className="text-sm text-gray-500 mt-1">
            Monitor workflow runs and inspect results
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
            to="/workflows"
            className="inline-flex items-center px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition"
          >
            <Plus className="w-4 h-4 mr-2" />
            New Workflow
          </Link>
        </div>
      </div>

      {/* Auto-refresh indicator */}
      <div className="px-6 py-2 bg-blue-50 border-b border-blue-100">
        <p className="text-sm text-blue-600 flex items-center">
          <svg className="w-4 h-4 mr-2 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 5.373 0 12 0h0z"></path>
          </svg>
          Auto-refreshing every 5 seconds
        </p>
      </div>

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
