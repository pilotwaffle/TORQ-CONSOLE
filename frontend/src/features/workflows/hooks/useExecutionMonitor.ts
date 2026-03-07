/**
 * Execution Monitor Hook
 *
 * Provides real-time execution monitoring with WebSocket or polling.
 * Tracks node status changes and output streaming.
 */

import { useEffect, useState, useCallback, useRef } from "react";
import { useExecutionGraph } from "../hooks";
import type { ExecutionGraphResponse, NodeStatus } from "@workflows/api";

export interface ExecutionMonitorState {
  execution: ExecutionGraphResponse | null;
  isLive: boolean;
  currentStep: number;
  totalSteps: number;
  completedNodes: string[];
  runningNodes: string[];
  failedNodes: string[];
  nodeOutputs: Record<string, unknown>;
}

export interface ExecutionMonitorOptions {
  executionId: string;
  pollInterval?: number;
  onNodeComplete?: (nodeId: string) => void;
  onNodeFailed?: (nodeId: string, error: string) => void;
  onExecutionComplete?: (result: ExecutionGraphResponse) => void;
}

export function useExecutionMonitor({
  executionId,
  pollInterval = 2000, // Poll every 2 seconds for near-real-time updates
  onNodeComplete,
  onNodeFailed,
  onExecutionComplete,
}: ExecutionMonitorOptions) {
  const [state, setState] = useState<ExecutionMonitorState>({
    execution: null,
    isLive: true,
    currentStep: 0,
    totalSteps: 0,
    completedNodes: [],
    runningNodes: [],
    failedNodes: [],
    nodeOutputs: {},
  });

  const previousNodeStatuses = useRef<Record<string, NodeStatus>>({});
  const { data: executionData, isLoading, error } = useExecutionGraph(executionId, {
    refetchInterval: (data) => {
      // Poll faster for running executions
      if (!data) return pollInterval;
      const exec = data as ExecutionGraphResponse;
      const isRunning = exec.execution.status === "running" || exec.execution.status === "pending";
      return isRunning ? pollInterval : false;
    },
  });

  // Process execution data updates
  useEffect(() => {
    if (!executionData) return;

    const newCompletedNodes: string[] = [];
    const newRunningNodes: string[] = [];
    const newFailedNodes: string[] = [];

    executionData.nodes.forEach((node) => {
      const previousStatus = previousNodeStatuses.current[node.node_id];
      const currentStatus = node.runtime.status;

      // Detect status changes
      if (previousStatus && previousStatus !== currentStatus) {
        if (currentStatus === "completed" && previousStatus !== "completed") {
          newCompletedNodes.push(node.node_id);
          onNodeComplete?.(node.node_id);
        } else if (currentStatus === "failed" && previousStatus !== "failed") {
          newFailedNodes.push(node.node_id);
          onNodeFailed?.(node.node_id, node.runtime.error_message || "Unknown error");
        }
      }

      // Track current state
      if (currentStatus === "completed") {
        newCompletedNodes.push(node.node_id);
      } else if (currentStatus === "running") {
        newRunningNodes.push(node.node_id);
      } else if (currentStatus === "failed") {
        newFailedNodes.push(node.node_id);
      }

      previousNodeStatuses.current[node.node_id] = currentStatus;
    });

    const isLive = executionData.execution.status === "running" || executionData.execution.status === "pending";
    const totalSteps = executionData.summary.total_nodes;
    const currentStep = executionData.summary.completed + executionData.summary.failed + executionData.summary.running;

    setState((prev) => ({
      execution: executionData,
      isLive,
      currentStep,
      totalSteps,
      completedNodes: Array.from(new Set([...prev.completedNodes, ...newCompletedNodes])),
      runningNodes: newRunningNodes,
      failedNodes: Array.from(new Set([...prev.failedNodes, ...newFailedNodes])),
      nodeOutputs: prev.nodeOutputs, // Outputs would need to be fetched separately via getExecutionNodes
    }));

    // Trigger completion callback
    if (executionData.execution.status === "completed" && !isLive) {
      onExecutionComplete?.(executionData);
    }
  }, [executionData, onNodeComplete, onNodeFailed, onExecutionComplete]);

  const getNodeStatus = useCallback(
    (nodeId: string): NodeStatus | undefined => {
      return executionData?.nodes.find((n) => n.node_id === nodeId)?.runtime.status;
    },
    [executionData]
  );

  const getNodeOutput = useCallback(
    (nodeId: string): unknown => {
      return state.nodeOutputs[nodeId];
    },
    [state.nodeOutputs]
  );

  const getNodeProgress = useCallback(
    (nodeId: string): { status: NodeStatus | undefined; duration: number | undefined } => {
      const node = executionData?.nodes.find((n) => n.node_id === nodeId);
      return {
        status: node?.runtime.status,
        duration: node?.runtime.duration_ms,
      };
    },
    [executionData]
  );

  return {
    ...state,
    isLoading,
    error,
    getNodeStatus,
    getNodeOutput,
    getNodeProgress,
    isComplete: executionData?.execution.status === "completed",
    isFailed: executionData?.execution.status === "failed",
  };
}
