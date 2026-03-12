/**
 * Execution Details Page
 *
 * Shows execution graph with live node status updates.
 * Phase 3: Now includes live monitoring with timeline and output streaming.
 */

import { Suspense, useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useExecutionGraph } from "../../features/workflows";
import { ExecutionGraphOverlay, NodeDetailsPanel, ExecutionTimeline, LiveOutputPanel } from "../../features/workflows/components";
import type { WorkflowNode } from "../../features/workflows/api";
import type { ExecutionNodeResult } from "../../features/workflows/api";
import { formatRelativeTime, formatDuration } from "../../features/workflows/utils/workflowFormatters";
import { ChevronRight, ChevronDown, Activity, Brain } from "lucide-react";
import { WorkspaceInspectorByScope } from "../../features/workspace";

function ExecutionDetailsPageContent() {
  const { executionId } = useParams<{ executionId: string }>();
  const navigate = useNavigate();
  const { data: graphData, isLoading, error } = useExecutionGraph(executionId || "");
  const [selectedNodeData, setSelectedNodeData] = useState<WorkflowNode | null>(null);
  const [selectedNodeResult, setSelectedNodeResult] = useState<ExecutionNodeResult | undefined>(undefined);
  const [showOutput, setShowOutput] = useState(true);
  const [showTimeline, setShowTimeline] = useState(true);
  const [showWorkspace, setShowWorkspace] = useState(false);

  useEffect(() => {
    if (error && error.message.includes("404")) {
      navigate("/executions");
    }
  }, [error, navigate]);

  const handleNodeClick = (nodeId: string) => {
    const node = graphData?.nodes.find((n) => n.node_id === nodeId);
    if (node) {
      setSelectedNodeData({
        node_id: node.node_id,
        node_key: node.node_key,
        name: node.name,
        node_type: node.node_type,
        agent_id: node.agent_id,
        parameters: node.parameters,
        position_x: node.position_x,
        position_y: node.position_y,
        depends_on: node.depends_on,
      });
      setSelectedNodeResult({
        result_id: node.node_id,
        execution_id: graphData!.execution.execution_id,
        node_id: node.node_id,
        node_key: node.node_key,
        name: node.name,
        status: node.runtime.status,
        error_message: node.runtime.error_message,
        started_at: node.runtime.started_at,
        completed_at: node.runtime.completed_at,
        duration_ms: node.runtime.duration_ms,
        retry_count: node.runtime.attempt,
        agent_id: node.agent_id,
      });
      setShowOutput(true);
    }
  };

  const handleCloseDetails = () => {
    setSelectedNodeData(null);
    setSelectedNodeResult(undefined);
    setShowOutput(false);
  };

  if (isLoading) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900" />
      </div>
    );
  }

  if (error && !graphData) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-lg font-semibold text-red-600 mb-2">Execution not found</h2>
          <button
            onClick={() => navigate("/executions")}
            className="text-blue-600 hover:underline"
          >
            Back to Executions
          </button>
        </div>
      </div>
    );
  }

  if (!graphData) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900" />
      </div>
    );
  }

  const { execution, graph, nodes, edges, summary } = graphData;
  const isRunning = execution.status === "running" || execution.status === "pending";

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate("/executions")}
            className="text-gray-400 hover:text-gray-600"
          >
            ← Back
          </button>
          <div>
            <h1 className="text-xl font-semibold text-gray-900">
              Execution: {execution.execution_id.slice(0, 12)}...
            </h1>
            <p className="text-sm text-gray-500 mt-1">{graph.name}</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-sm">
            <span className="text-gray-500">Status:</span>{" "}
            <span
              className={`font-medium ${
                execution.status === "running"
                  ? "text-blue-600"
                  : execution.status === "completed"
                  ? "text-green-600"
                  : execution.status === "failed"
                  ? "text-red-600"
                  : "text-gray-600"
              }`}
            >
              {execution.status.toUpperCase()}
              {isRunning && (
                <>
                  <span className="ml-2 inline-block w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                </>
              )}
            </span>
          </div>
          {execution.started_at && (
            <div className="text-sm text-gray-500">
              {formatRelativeTime(execution.started_at)}
            </div>
          )}
          <button
            onClick={() => setShowWorkspace(!showWorkspace)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border transition-colors ${
              showWorkspace
                ? "bg-purple-50 border-purple-300 text-purple-700"
                : "bg-white border-gray-300 text-gray-600 hover:bg-gray-50"
            }`}
          >
            <Brain className="w-4 h-4" />
            <span className="text-sm font-medium">Workspace</span>
          </button>
        </div>
      </div>

      {/* Summary */}
      <div className="px-6 py-3 bg-gray-50 border-b border-gray-200">
        <div className="flex items-center gap-6 text-sm">
          <div>
            <span className="text-gray-500">Progress:</span>{" "}
            <span className="font-medium">
              {summary.completed}/{summary.total_nodes} completed
            </span>
          </div>
          {summary.failed > 0 && (
            <div className="text-red-600">{summary.failed} failed</div>
          )}
          {summary.running > 0 && (
            <div className="flex items-center gap-1 text-blue-600">
              <Activity className="w-3 h-3" />
              {summary.running} running
            </div>
          )}
          <div>
            <span className="text-gray-500">Duration:</span>{" "}
            <span className="font-medium">{formatDuration(execution.total_duration_ms)}</span>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Workspace Side Panel */}
        {showWorkspace && executionId && (
          <div className="w-80 border-r border-gray-200 bg-white flex flex-col overflow-auto">
            <WorkspaceInspectorByScope
              scopeType="workflow_execution"
              scopeId={executionId}
              onClose={() => setShowWorkspace(false)}
            />
          </div>
        )}

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Toggles */}
          <div className="px-4 py-2 bg-gray-50 border-b border-gray-200 flex gap-4">
            <button
              onClick={() => setShowTimeline(!showTimeline)}
              className={`flex items-center gap-1 text-sm ${showTimeline ? "text-gray-900 font-medium" : "text-gray-500"}`}
            >
              {showTimeline ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              Timeline
            </button>
            {selectedNodeData && (
              <button
                onClick={() => setShowOutput(!showOutput)}
                className={`flex items-center gap-1 text-sm ${showOutput ? "text-gray-900 font-medium" : "text-gray-500"}`}
              >
                {showOutput ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                Output
              </button>
            )}
          </div>

          {/* Scrollable Content */}
          <div className="flex-1 overflow-auto">
            {/* Timeline Section */}
            {showTimeline && (
              <div className="p-4 border-b border-gray-200">
                <ExecutionTimeline
                  executionData={graphData}
                  onNodeClick={handleNodeClick}
                />
              </div>
            )}

            {/* Graph Section */}
            <div className="p-4">
              <ExecutionGraphOverlay
                executionData={graphData}
                onNodeClick={handleNodeClick}
                className="min-h-[400px]"
              />
            </div>
          </div>
        </div>

        {/* Side Panel */}
        {(selectedNodeData && showOutput) && (
          <div className="w-96 border-l border-gray-200 bg-white flex flex-col">
            <div className="flex-1 overflow-auto">
              <NodeDetailsPanel
                node={selectedNodeData}
                executionResult={selectedNodeResult}
                onClose={handleCloseDetails}
              />
            </div>
            {/* Live Output */}
            {selectedNodeData && selectedNodeResult && (
              <LiveOutputPanel
                nodeId={selectedNodeData.node_id}
                nodeName={selectedNodeData.name}
                output={selectedNodeResult.output}
                status={selectedNodeResult.status}
                isStreaming={isRunning && selectedNodeResult.status === "running"}
              />
            )}
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

export function ExecutionDetailsPage() {
  return (
    <Suspense fallback={<LoadingScreen />}>
      <ExecutionDetailsPageContent />
    </Suspense>
  );
}

export default function ExecutionDetailsPageWrapper() {
  return (
    <Suspense fallback={<LoadingScreen />}>
      <ExecutionDetailsPage />
    </Suspense>
  );
}
