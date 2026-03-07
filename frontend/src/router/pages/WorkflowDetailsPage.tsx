/**
 * Workflow Details Page
 *
 * Shows workflow graph visualization with node details.
 * Phase 2: Now includes interactive DAG visualization.
 */

import { Suspense, useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useWorkflow } from "../../features/workflows";
import { WorkflowGraphCanvas, NodeDetailsPanel } from "../../features/workflows/components";
import type { WorkflowNode } from "../../features/workflows/api";

function WorkflowDetailsPageContent() {
  const { graphId } = useParams<{ graphId: string }>();
  const navigate = useNavigate();
  const { data: workflow, isLoading, error } = useWorkflow(graphId || "");
  const [selectedNodeData, setSelectedNodeData] = useState<WorkflowNode | null>(null);

  useEffect(() => {
    if (error && error.message.includes("404")) {
      navigate("/workflows");
    }
  }, [error, navigate]);

  const handleNodeClick = (nodeId: string) => {
    const node = workflow?.nodes?.find((n) => n.node_id === nodeId);
    if (node) {
      setSelectedNodeData(node);
    }
  };

  const handleCloseDetails = () => {
    setSelectedNodeData(null);
  };

  if (isLoading) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-lg font-semibold text-red-600 mb-2">Workflow not found</h2>
          <button
            onClick={() => navigate("/workflows")}
            className="text-blue-600 hover:underline"
          >
            Back to Workflows
          </button>
        </div>
      </div>
    );
  }

  if (!workflow) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
        <div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate("/workflows")}
              className="text-gray-400 hover:text-gray-600"
            >
              ← Back
            </button>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">{workflow.name}</h1>
              {workflow.description && (
                <p className="text-sm text-gray-500 mt-1">{workflow.description}</p>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-sm text-gray-500">v{workflow.version}</div>
          <span
            className={`px-3 py-1 rounded-full text-xs font-medium ${
              workflow.status === "active"
                ? "bg-green-100 text-green-700"
                : workflow.status === "draft"
                ? "bg-yellow-100 text-yellow-700"
                : "bg-gray-100 text-gray-600"
            }`}
          >
            {workflow.status.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Summary Bar */}
      <div className="px-6 py-3 bg-gray-50 border-b border-gray-200">
        <div className="flex items-center gap-6 text-sm">
          <div>
            <span className="text-gray-500">Nodes:</span>{" "}
            <span className="font-medium">{workflow.nodes?.length || 0}</span>
          </div>
          <div>
            <span className="text-gray-500">Edges:</span>{" "}
            <span className="font-medium">{workflow.edges?.length || 0}</span>
          </div>
          {workflow.created_at && (
            <div>
              <span className="text-gray-500">Created:</span>{" "}
              <span className="font-medium">{new Date(workflow.created_at).toLocaleDateString()}</span>
            </div>
          )}
        </div>
      </div>

      {/* Graph Container */}
      <div className="flex-1 flex overflow-hidden">
        {/* Main Graph Area */}
        <div className="flex-1 p-4">
          <div className="h-full bg-white border border-gray-200 rounded-lg overflow-hidden">
            {workflow.nodes && workflow.nodes.length > 0 ? (
              <WorkflowGraphCanvas
                workflow={workflow}
                onNodeClick={handleNodeClick}
                readonly
                className="h-full"
              />
            ) : (
              <div className="h-full flex items-center justify-center text-gray-500">
                <div className="text-center">
                  <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h2a2 2 0 012 2m0 0a2 2 0 114 0m0 0v2a2 2 0 114 0v-4" />
                  </svg>
                  <p>No nodes in this workflow</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Node Details Panel (when node is selected) */}
        {selectedNodeData && (
          <div className="w-80 border-l border-gray-200 bg-white overflow-y-auto">
            <NodeDetailsPanel
              node={selectedNodeData}
              onClose={handleCloseDetails}
            />
          </div>
        )}
      </div>
    </div>
  );
}

function LoadingScreen() {
  return (
    <div className="h-screen flex items-center justify-center">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900" />
    </div>
  );
}

export function WorkflowDetailsPage() {
  return (
    <Suspense fallback={<LoadingScreen />}>
      <WorkflowDetailsPageContent />
    </Suspense>
  );
}

export default function WorkflowDetailsPageWrapper() {
  return (
    <Suspense fallback={<LoadingScreen />}>
      <WorkflowDetailsPage />
    </Suspense>
  );
}
