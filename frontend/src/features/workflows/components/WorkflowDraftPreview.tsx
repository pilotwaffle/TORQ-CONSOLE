/**
 * WorkflowDraftPreview Component
 *
 * Displays a generated workflow draft with rationale and graph preview.
 */

import { useState } from "react";
import { CheckCircle2, Info, Edit2 } from "lucide-react";
import { WorkflowGraphCanvas } from "./WorkflowGraphCanvas";
import type { WorkflowDraft } from "@workflows/api/workflowPlannerApi";
import type { CreateWorkflowResponse } from "@workflows/api/workflowTypes";

interface WorkflowDraftPreviewProps {
  draft: WorkflowDraft;
  onSave: (draft: WorkflowDraft) => void;
  onEdit: (draft: WorkflowDraft) => void;
  onDiscard: () => void;
  className?: string;
}

function draftToWorkflowResponse(draft: WorkflowDraft): CreateWorkflowResponse {
  // Convert draft to workflow format for graph canvas
  const nodes = draft.nodes.map((node, index) => ({
    node_id: node.node_key,
    node_key: node.node_key,
    name: node.name,
    node_type: node.node_type,
    agent_id: node.agent_id,
    depends_on: node.depends_on,
    parameters: node.parameters,
    timeout_seconds: node.timeout_seconds,
    retry_policy: node.retry_policy,
    position_x: 100,
    position_y: index * 150,
  }));

  const edges = draft.edges.map((edge) => ({
    edge_id: `${edge.source_node_key}-${edge.target_node_key}`,
    source_node_id: edge.source_node_key,
    target_node_id: edge.target_node_key,
  }));

  return {
    graph_id: "draft",
    name: draft.name,
    description: draft.description,
    nodes,
    edges,
    status: "draft",
    limits: draft.limits,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };
}

export function WorkflowDraftPreview({ draft, onSave, onEdit, onDiscard, className = "" }: WorkflowDraftPreviewProps) {
  const [selectedTab, setSelectedTab] = useState<"graph" | "details">("graph");
  const workflowData = draftToWorkflowResponse(draft);

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              {draft.name}
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {draft.description}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 text-xs font-medium rounded-full flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3" />
              Draft
            </span>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-4 mt-4">
          <button
            onClick={() => setSelectedTab("graph")}
            className={`text-sm font-medium pb-2 border-b-2 transition-colors ${
              selectedTab === "graph"
                ? "border-purple-500 text-purple-600 dark:text-purple-400"
                : "border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
            }`}
          >
            Graph View
          </button>
          <button
            onClick={() => setSelectedTab("details")}
            className={`text-sm font-medium pb-2 border-b-2 transition-colors ${
              selectedTab === "details"
                ? "border-purple-500 text-purple-600 dark:text-purple-400"
                : "border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
            }`}
          >
            Details & Rationale
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {selectedTab === "graph" ? (
          <div className="h-full">
            <WorkflowGraphCanvas
              workflow={workflowData}
              readonly
              className="h-full"
            />
          </div>
        ) : (
          <div className="h-full overflow-y-auto p-6">
            {/* Rationale */}
            {draft.rationale && (
              <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                <div className="flex items-start gap-3">
                  <Info className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-blue-900 dark:text-blue-300">
                      Why this workflow?
                    </p>
                    <p className="text-sm text-blue-800 dark:text-blue-400 mt-1">
                      {draft.rationale}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Nodes List */}
            <div className="mb-6">
              <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
                Workflow Steps ({draft.nodes.length})
              </h3>
              <div className="space-y-2">
                {draft.nodes.map((node, index) => (
                  <div
                    key={node.node_key}
                    className="p-3 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg"
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 w-6 h-6 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-full flex items-center justify-center text-xs font-medium">
                        {index + 1}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 dark:text-white">
                          {node.name}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                          Agent: {node.agent_id}
                        </p>
                        {node.depends_on.length > 0 && (
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                            After: {node.depends_on.join(", ")}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Limits */}
            <div>
              <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
                Workflow Limits
              </h3>
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-center">
                  <p className="text-lg font-semibold text-gray-900 dark:text-white">
                    {draft.limits.max_nodes}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Max Nodes</p>
                </div>
                <div className="p-3 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-center">
                  <p className="text-lg font-semibold text-gray-900 dark:text-white">
                    {Math.floor(draft.limits.max_runtime_seconds / 60)}m
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Max Runtime</p>
                </div>
                <div className="p-3 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-center">
                  <p className="text-lg font-semibold text-gray-900 dark:text-white">
                    {draft.limits.max_parallel_nodes}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Max Parallel</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer - Action Buttons */}
      <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex gap-3">
          <button
            onClick={onDiscard}
            className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
          >
            Discard
          </button>
          <button
            onClick={() => onEdit(draft)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-lg flex items-center gap-2 transition-colors"
          >
            <Edit2 className="w-4 h-4" />
            Edit
          </button>
          <div className="flex-1" />
          <button
            onClick={() => onSave(draft)}
            className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg flex items-center gap-2 transition-colors"
          >
            <CheckCircle2 className="w-4 h-4" />
            Save Workflow
          </button>
        </div>
      </div>
    </div>
  );
}
