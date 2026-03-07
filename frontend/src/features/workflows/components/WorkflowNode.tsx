/**
 * Workflow Node Component
 *
 * Custom React Flow node for displaying workflow nodes.
 * Shows node type, agent, status, and configuration summary.
 */

import { memo } from "react";
import { Handle, Position, type NodeProps } from "reactflow";
import { AlertCircle, CheckCircle2, Clock, Loader, Cpu, FileText, Search, TestTube, Settings, Globe, GitBranch, GitMerge, ArrowRight } from "lucide-react";
import type { NodeStatus, NodeType } from "@workflows/api";
import { formatNodeStatus, getNodeStatusBgColor } from "@workflows/utils/workflowFormatters";

interface WorkflowNodeData {
  id: string;
  name: string;
  type: NodeType;
  agentId?: string;
  status?: NodeStatus;
  config?: Record<string, unknown>;
}

// Icon mapping for node types
const NodeIcons: Record<NodeType, React.ElementType> = {
  agent: Cpu,
  tool: Settings,
  api_call: Globe,
  analysis: Search,
  condition: GitBranch,
  parallel: GitMerge,
  sequential: ArrowRight,
};

// Status icons
const StatusIcons: Record<NodeStatus, React.ElementType> = {
  pending: Clock,
  running: Loader,
  completed: CheckCircle2,
  failed: AlertCircle,
  skipped: Clock,
};

export const WorkflowNodeComponent = memo(({ data, selected }: NodeProps<WorkflowNodeData>) => {
  const Icon = NodeIcons[data.type] || FileText;
  const StatusIcon = data.status ? StatusIcons[data.status] : null;
  const bgColorClass = data.status ? getNodeStatusBgColor(data.status) : "bg-white border-gray-300";

  return (
    <div
      className={`workflow-node-wrapper ${selected ? "ring-2 ring-blue-500 ring-offset-2" : ""}`}
      style={{ minWidth: "200px" }}
    >
      {/* Input Handle */}
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-gray-400 !border-gray-500 !w-3 !h-3"
      />

      {/* Node Content */}
      <div
        className={`px-4 py-3 rounded-lg border-2 shadow-sm ${bgColorClass} transition-all`}
      >
        {/* Header: Icon + Name */}
        <div className="flex items-center gap-2 mb-2">
          <div className={`p-1.5 rounded-md ${
            data.status === "running" ? "bg-blue-100" :
            data.status === "completed" ? "bg-green-100" :
            data.status === "failed" ? "bg-red-100" :
            "bg-gray-100"
          }`}>
            <Icon className="w-4 h-4 text-gray-600" />
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="text-sm font-semibold text-gray-900 truncate">{data.name}</h4>
          </div>
          {StatusIcon && data.status === "running" && (
            <Loader className="w-4 h-4 text-blue-500 animate-spin" />
          )}
          {StatusIcon && data.status === "completed" && (
            <CheckCircle2 className="w-4 h-4 text-green-500" />
          )}
          {StatusIcon && data.status === "failed" && (
            <AlertCircle className="w-4 h-4 text-red-500" />
          )}
        </div>

        {/* Type Badge */}
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xs font-mono text-gray-500 bg-white px-2 py-0.5 rounded border border-gray-200">
            {data.type}
          </span>
          {data.agentId && (
            <span className="text-xs text-gray-500 truncate" title={data.agentId}>
              {data.agentId.length > 15 ? `${data.agentId.slice(0, 15)}...` : data.agentId}
            </span>
          )}
        </div>

        {/* Status Badge (if status exists) */}
        {data.status && (
          <div className="mt-2 pt-2 border-t border-gray-200">
            <span className={`text-xs font-medium px-2 py-0.5 rounded ${getNodeStatusBgColor(data.status)}`}>
              {formatNodeStatus(data.status)}
            </span>
          </div>
        )}

        {/* Config Summary */}
        {data.config && Object.keys(data.config).length > 0 && (
          <div className="mt-2 pt-2 border-t border-gray-200">
            <div className="text-xs text-gray-500">
              {Object.entries(data.config).slice(0, 2).map(([key, value]) => (
                <div key={key} className="truncate" title={`${key}: ${String(value)}`}>
                  <span className="font-medium">{key}:</span>{" "}
                  <span className="text-gray-400">
                    {typeof value === "string" && value.length > 20
                      ? `${value.slice(0, 20)}...`
                      : String(value)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Output Handle */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-gray-400 !border-gray-500 !w-3 !h-3"
      />

      <style>{`
        .workflow-node-wrapper {
          transition: all 150ms ease-in-out;
        }
        .workflow-node-wrapper:hover {
          transform: translateY(-2px);
        }
        .workflow-node-wrapper .react-flow__handle {
          width: 12px;
          height: 12px;
          border-width: 2px;
        }
      `}</style>
    </div>
  );
});

WorkflowNodeComponent.displayName = "WorkflowNodeComponent";
