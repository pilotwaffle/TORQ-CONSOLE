/**
 * Node Details Panel
 *
 * Shows detailed information about a selected workflow node.
 * Displays configuration, inputs, outputs, and execution results.
 */

import { useMemo } from "react";
import type { WorkflowNode, ExecutionNodeResult, NodeType } from "@workflows/api";
import { formatNodeStatus, formatDuration } from "@workflows/utils/workflowFormatters";
import { X, FileText, Cpu, Settings, Clock, Globe, Search, GitBranch, GitMerge, ArrowRight } from "lucide-react";

interface NodeDetailsPanelProps {
  node: WorkflowNode;
  executionResult?: ExecutionNodeResult;
  onClose: () => void;
  className?: string;
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

export function NodeDetailsPanel({ node, executionResult, onClose, className = "" }: NodeDetailsPanelProps) {
  const Icon = NodeIcons[node.node_type] || FileText;

  // Group config items
  const configGroups = useMemo(() => {
    if (!node.parameters) return [];

    const groups: Array<{ title: string; items: Array<{ key: string; value: string }> }> = [];
    const mainItems = Object.entries(node.parameters).map(([key, value]) => ({
      key,
      value: typeof value === "object" ? JSON.stringify(value, null, 2) : String(value),
    }));

    if (mainItems.length > 0) {
      groups.push({ title: "Parameters", items: mainItems });
    }

    return groups;
  }, [node.parameters]);

  return (
    <div className={`node-details-panel ${className}`}>
      <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-white rounded-lg border border-gray-200">
            <Icon className="w-5 h-5 text-gray-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{node.name}</h3>
            <p className="text-sm text-gray-500">{node.node_type}</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-200 rounded transition"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      <div className="p-4 space-y-4 max-h-96 overflow-y-auto">
        {/* Node Info */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Node ID:</span>
            <p className="font-mono text-gray-900 text-xs truncate" title={node.node_id}>
              {node.node_id}
            </p>
          </div>
          {node.agent_id && (
            <div>
              <span className="text-gray-500">Agent:</span>
              <p className="font-mono text-gray-900 text-xs truncate" title={node.agent_id}>
                {node.agent_id}
              </p>
            </div>
          )}
          {node.tool_name && (
            <div>
              <span className="text-gray-500">Tool:</span>
              <p className="text-gray-900">{node.tool_name}</p>
            </div>
          )}
          {node.timeout_seconds && (
            <div>
              <span className="text-gray-500">Timeout:</span>
              <p className="text-gray-900">{node.timeout_seconds}s</p>
            </div>
          )}
          {node.retry_policy && (
            <div className="col-span-2">
              <span className="text-gray-500">Retry Policy:</span>
              <p className="text-gray-900 text-xs">
                {node.retry_policy.max_retries ?? 3} max retries,{" "}
                {node.retry_policy.retry_delay_ms ?? 1000}ms delay
                {node.retry_policy.failure_strategy && (
                  <>, fail strategy: {node.retry_policy.failure_strategy}</>
                )}
              </p>
            </div>
          )}
          {node.depends_on && node.depends_on.length > 0 && (
            <div className="col-span-2">
              <span className="text-gray-500">Depends on:</span>
              <p className="text-gray-900 text-xs">{node.depends_on.join(", ")}</p>
            </div>
          )}
        </div>

        {/* Execution Result (if available) */}
        {executionResult && (
          <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
            <div className="flex items-center gap-2 mb-2">
              <Clock className="w-4 h-4 text-gray-500" />
              <span className="font-medium text-gray-900">Execution Result</span>
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <span className="text-gray-500">Status:</span>
                <p className="font-medium">{formatNodeStatus(executionResult.status)}</p>
              </div>
              {executionResult.duration_ms && (
                <div>
                  <span className="text-gray-500">Duration:</span>
                  <p className="text-gray-900">{formatDuration(executionResult.duration_ms)}</p>
                </div>
              )}
              {executionResult.retry_count !== undefined && executionResult.retry_count > 0 && (
                <div>
                  <span className="text-gray-500">Retries:</span>
                  <p className="text-gray-900">{executionResult.retry_count}</p>
                </div>
              )}
              {executionResult.started_at && (
                <div>
                  <span className="text-gray-500">Started:</span>
                  <p className="text-gray-900 text-xs">
                    {new Date(executionResult.started_at).toLocaleTimeString()}
                  </p>
                </div>
              )}
            </div>
            {executionResult.error_message && (
              <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                {executionResult.error_message}
              </div>
            )}
          </div>
        )}

        {/* Parameters Groups */}
        {configGroups.map((group) => (
          <div key={group.title}>
            <h4 className="text-sm font-medium text-gray-700 mb-2">{group.title}</h4>
            <div className="space-y-2">
              {group.items.map((item) => (
                <div key={item.key} className="p-2 bg-gray-50 rounded border border-gray-200">
                  <div className="text-xs font-medium text-gray-600 mb-1">{item.key}</div>
                  <pre className="text-xs text-gray-900 whitespace-pre-wrap break-all font-mono">
                    {item.value}
                  </pre>
                </div>
              ))}
            </div>
          </div>
        ))}

        {/* Output (if execution result exists) */}
        {executionResult?.output && Object.keys(executionResult.output).length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Output</h4>
            <div className="p-3 bg-gray-900 rounded-lg overflow-x-auto">
              <pre className="text-xs text-green-400 font-mono">
                {JSON.stringify(executionResult.output, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
