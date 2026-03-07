/**
 * Execution Graph Overlay
 *
 * Shows real-time execution status overlay on the workflow graph.
 * Displays running nodes, completed nodes, and failed nodes with animations.
 */

import { useMemo } from "react";
import type {
  ExecutionGraphResponse,
  NodeStatus,
  CreateWorkflowResponse,
  WorkflowNode,
  WorkflowEdge,
} from "@workflows/api";
import { WorkflowGraphCanvas } from "./WorkflowGraphCanvas";

interface ExecutionGraphOverlayProps {
  executionData: ExecutionGraphResponse;
  onNodeClick?: (nodeId: string) => void;
  className?: string;
}

export function ExecutionGraphOverlay({
  executionData,
  onNodeClick,
  className = "",
}: ExecutionGraphOverlayProps) {
  // Build node statuses from execution data
  const nodeStatuses = useMemo<Record<string, NodeStatus>>(() => {
    const statuses: Record<string, NodeStatus> = {};

    // Set status from runtime information
    executionData.nodes.forEach((node) => {
      statuses[node.node_id] = node.runtime.status;
    });

    return statuses;
  }, [executionData.nodes]);

  // Convert execution graph to workflow graph format
  const workflowGraph = useMemo<CreateWorkflowResponse>(() => ({
    graph_id: executionData.execution.execution_id,
    name: executionData.graph.name,
    description: executionData.graph.description,
    status: executionData.graph.status,
    version: 1,
    created_at: executionData.execution.started_at || "",
    updated_at: executionData.execution.completed_at || "",
    nodes: executionData.nodes.map((node): WorkflowNode => ({
      node_id: node.node_id,
      node_key: node.node_key,
      name: node.name,
      node_type: node.node_type,
      agent_id: node.agent_id,
      parameters: node.parameters,
      position_x: node.position_x,
      position_y: node.position_y,
      depends_on: node.depends_on,
    })),
    edges: executionData.edges.map((edge): WorkflowEdge => ({
      source_node_id: edge.source_node_id,
      target_node_id: edge.target_node_id,
      condition: edge.condition,
    })),
  }), [executionData]);

  return (
    <div className={`execution-graph-overlay ${className}`}>
      {/* Execution Summary Bar */}
      <div className="execution-summary-bar mb-4 px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6 text-sm">
            <div>
              <span className="text-gray-500">Progress:</span>{" "}
              <span className="font-medium text-gray-900">
                {executionData.summary.completed}/{executionData.summary.total_nodes} nodes
              </span>
            </div>
            {executionData.summary.running > 0 && (
              <div className="flex items-center gap-1 text-blue-600">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                <span>{executionData.summary.running} running</span>
              </div>
            )}
            {executionData.summary.failed > 0 && (
              <div className="text-red-600">
                <span>{executionData.summary.failed} failed</span>
              </div>
            )}
            {executionData.execution.total_duration_ms && (
              <div>
                <span className="text-gray-500">Duration:</span>{" "}
                <span className="font-medium">
                  {executionData.execution.total_duration_ms > 1000
                    ? `${(executionData.execution.total_duration_ms / 1000).toFixed(1)}s`
                    : `${executionData.execution.total_duration_ms}ms`}
                </span>
              </div>
            )}
          </div>
          <div className={`px-3 py-1 rounded-full text-xs font-medium ${
            executionData.execution.status === "running"
              ? "bg-blue-100 text-blue-700"
              : executionData.execution.status === "completed"
              ? "bg-green-100 text-green-700"
              : executionData.execution.status === "failed"
              ? "bg-red-100 text-red-700"
              : "bg-gray-100 text-gray-700"
          }`}>
            {executionData.execution.status.toUpperCase()}
          </div>
        </div>
      </div>

      {/* Graph Canvas */}
      <WorkflowGraphCanvas
        workflow={workflowGraph}
        nodeStatuses={nodeStatuses}
        onNodeClick={onNodeClick}
        readonly
        className="h-[500px] border border-gray-200 rounded-lg"
      />
    </div>
  );
}
