/**
 * Execution Timeline Component
 *
 * Visual timeline of execution progress with node status indicators.
 */

import { useMemo } from "react";
import { CheckCircle2, Clock, AlertCircle, Loader } from "lucide-react";
import type { ExecutionGraphResponse, NodeStatus } from "@workflows/api";
import { formatDuration } from "@workflows/utils/workflowFormatters";

interface ExecutionTimelineProps {
  executionData: ExecutionGraphResponse;
  onNodeClick?: (nodeId: string) => void;
  className?: string;
}

export function ExecutionTimeline({ executionData, onNodeClick, className = "" }: ExecutionTimelineProps) {
  // Build a timeline based on node dependencies and start times
  const timeline = useMemo(() => {
    const nodes = [...executionData.nodes].sort((a, b) => {
      const aStart = a.runtime.started_at ? new Date(a.runtime.started_at).getTime() : 0;
      const bStart = b.runtime.started_at ? new Date(b.runtime.started_at).getTime() : 0;
      return aStart - bStart;
    });

    return nodes.map((node, index) => {
      const status = node.runtime.status as NodeStatus;
      const isComplete = status === "completed";
      const isRunning = status === "running";
      const isFailed = status === "failed";
      const isPending = status === "pending";

      return {
        index,
        node,
        status,
        isComplete,
        isRunning,
        isFailed,
        isPending,
        startedAt: node.runtime.started_at,
        completedAt: node.runtime.completed_at,
        duration: node.runtime.duration_ms,
        error: node.runtime.error_message,
      };
    });
  }, [executionData.nodes]);

  const overallStatus = executionData.execution.status;
  const totalDuration = executionData.execution.total_duration_ms || 0;

  return (
    <div className={`execution-timeline ${className}`}>
      {/* Progress Bar */}
      <div className="mb-4">
        <div className="flex items-center justify-between text-sm mb-2">
          <span className="text-gray-600">Execution Progress</span>
          <span className="font-medium">
            {executionData.summary.completed}/{executionData.summary.total_nodes} nodes
          </span>
        </div>
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ${
              overallStatus === "failed"
                ? "bg-red-500"
                : overallStatus === "completed"
                ? "bg-green-500"
                : overallStatus === "running"
                ? "bg-blue-500"
                : "bg-gray-400"
            }`}
            style={{
              width: `${Math.round((executionData.summary.completed / executionData.summary.total_nodes) * 100)}%`,
            }}
          />
        </div>
      </div>

      {/* Timeline */}
      <div className="space-y-2">
        {timeline.map((item, index) => (
          <div
            key={item.node.node_id}
            className={`flex items-start gap-3 p-3 rounded-lg border transition-all cursor-pointer ${
              item.isFailed
                ? "bg-red-50 border-red-200"
                : item.isComplete
                ? "bg-green-50 border-green-200"
                : item.isRunning
                ? "bg-blue-50 border-blue-200"
                : "bg-gray-50 border-gray-200"
            } ${onNodeClick ? "hover:shadow-sm" : ""}`}
            onClick={() => onNodeClick?.(item.node.node_id)}
          >
            {/* Status Icon */}
            <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
              item.isComplete
                ? "bg-green-100"
                : item.isRunning
                ? "bg-blue-100"
                : item.isFailed
                ? "bg-red-100"
                : "bg-gray-200"
            }`}>
              {item.isComplete ? (
                <CheckCircle2 className="w-4 h-4 text-green-600" />
              ) : item.isRunning ? (
                <Loader className="w-4 h-4 text-blue-600 animate-spin" />
              ) : item.isFailed ? (
                <AlertCircle className="w-4 h-4 text-red-600" />
              ) : (
                <Clock className="w-4 h-4 text-gray-400" />
              )}
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between mb-1">
                <h4 className="font-medium text-gray-900 truncate">{item.node.name}</h4>
                {item.duration !== undefined && (
                  <span className="text-xs text-gray-500 ml-2">
                    {formatDuration(item.duration)}
                  </span>
                )}
              </div>

              <p className="text-sm text-gray-500 truncate">
                {item.node.node_type}
                {item.node.agent_id && ` • ${item.node.agent_id}`}
              </p>

              {/* Error Message */}
              {item.isFailed && item.error && (
                <p className="text-sm text-red-600 mt-1 truncate" title={item.error}>
                  {item.error}
                </p>
              )}

              {/* Timestamps */}
              {item.startedAt && (
                <div className="text-xs text-gray-400 mt-1">
                  {new Date(item.startedAt).toLocaleTimeString()}
                  {item.completedAt && (
                    <> → {new Date(item.completedAt).toLocaleTimeString()}</>
                  )}
                </div>
              )}
            </div>

            {/* Connector Line (except last item) */}
            {index < timeline.length - 1 && (
              <div
                className={`absolute left-7 w-0.5 -bottom-6 ${
                  item.isComplete ? "bg-green-200" : "bg-gray-200"
                }`}
                style={{ height: "16px" }}
              />
            )}
          </div>
        ))}
      </div>

      {/* Summary */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="grid grid-cols-4 gap-4 text-center">
          <div>
            <div className="text-2xl font-semibold text-gray-900">{executionData.summary.total_nodes}</div>
            <div className="text-xs text-gray-500">Total</div>
          </div>
          <div>
            <div className="text-2xl font-semibold text-green-600">{executionData.summary.completed}</div>
            <div className="text-xs text-gray-500">Completed</div>
          </div>
          <div>
            <div className="text-2xl font-semibold text-blue-600">{executionData.summary.running}</div>
            <div className="text-xs text-gray-500">Running</div>
          </div>
          <div>
            <div className="text-2xl font-semibold text-red-600">{executionData.summary.failed}</div>
            <div className="text-xs text-gray-500">Failed</div>
          </div>
        </div>
      </div>
    </div>
  );
}
