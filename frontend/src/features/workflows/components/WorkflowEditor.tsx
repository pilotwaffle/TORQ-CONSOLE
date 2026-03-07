/**
 * Workflow Editor Component
 *
 * Form-based workflow creation and editing interface.
 */

import { useState, useCallback } from "react";
import { Plus, Trash2, Save, ArrowRight, X } from "lucide-react";
import type { WorkflowNode, WorkflowEdge, CreateWorkflowRequest, NodeType } from "@workflows/api";

interface WorkflowEditorProps {
  initialNodes?: WorkflowNode[];
  initialEdges?: WorkflowEdge[];
  onSave: (workflow: CreateWorkflowRequest) => void;
  onCancel: () => void;
  className?: string;
}

const nodeTypes: Array<{ value: NodeType; label: string; description: string }> = [
  { value: "agent", label: "Agent", description: "AI agent node" },
  { value: "tool", label: "Tool", description: "External tool integration" },
  { value: "api_call", label: "API Call", description: "HTTP API request" },
  { value: "analysis", label: "Analysis", description: "Data analysis node" },
  { value: "condition", label: "Condition", description: "Branch on condition" },
  { value: "parallel", label: "Parallel", description: "Execute in parallel" },
  { value: "sequential", label: "Sequential", description: "Sequential execution" },
];

export function WorkflowEditor({
  initialNodes = [],
  initialEdges = [],
  onSave,
  onCancel,
  className = "",
}: WorkflowEditorProps) {
  const [workflowName, setWorkflowName] = useState("");
  const [workflowDescription, setWorkflowDescription] = useState("");
  const [nodes, setNodes] = useState<WorkflowNode[]>(initialNodes);
  const [edges, setEdges] = useState<WorkflowEdge[]>(initialEdges);
  const [selectedNode, setSelectedNode] = useState<WorkflowNode | null>(null);

  const addNode = useCallback(() => {
    const newNode: WorkflowNode = {
      node_id: `node_${Date.now()}`,
      node_key: `node_${nodes.length}`,
      name: `Node ${nodes.length + 1}`,
      node_type: "agent",
      parameters: {},
      position_x: nodes.length * 200,
      position_y: 0,
    };
    setNodes((prev) => [...prev, newNode]);
    setSelectedNode(newNode);
  }, [nodes.length]);

  const updateNode = useCallback((nodeId: string, updates: Partial<WorkflowNode>) => {
    setNodes((prev) =>
      prev.map((node) => (node.node_id === nodeId ? { ...node, ...updates } : node))
    );
    if (selectedNode?.node_id === nodeId) {
      setSelectedNode((prev) => prev ? { ...prev, ...updates } : null);
    }
  }, [selectedNode]);

  const deleteNode = useCallback((nodeId: string) => {
    setNodes((prev) => prev.filter((n) => n.node_id !== nodeId));
    setEdges((prev) => prev.filter((e) => e.source_node_id !== nodeId && e.target_node_id !== nodeId));
    if (selectedNode?.node_id === nodeId) {
      setSelectedNode(null);
    }
  }, [selectedNode]);

  const addEdge = useCallback((sourceId: string, targetId: string) => {
    const newEdge: WorkflowEdge = {
      source_node_id: sourceId,
      target_node_id: targetId,
    };
    setEdges((prev) => [...prev, newEdge]);
  }, []);

  const deleteEdge = useCallback((sourceId: string, targetId: string) => {
    setEdges((prev) =>
      prev.filter(
        (e) => !(e.source_node_id === sourceId && e.target_node_id === targetId)
      )
    );
  }, []);

  const handleSave = () => {
    if (!workflowName.trim()) {
      alert("Please enter a workflow name");
      return;
    }

    if (nodes.length === 0) {
      alert("Please add at least one node");
      return;
    }

    const workflow: CreateWorkflowRequest = {
      name: workflowName,
      description: workflowDescription || undefined,
      nodes,
      edges,
    };

    onSave(workflow);
  };

  const updateNodeParameter = useCallback((nodeId: string, key: string, value: string) => {
    setNodes((prev) =>
      prev.map((node) => {
        if (node.node_id === nodeId) {
          const params = { ...(node.parameters || {}) };
          try {
            params[key] = JSON.parse(value);
          } catch {
            params[key] = value;
          }
          return { ...node, parameters: params };
        }
        return node;
      })
    );
  }, []);

  return (
    <div className={`workflow-editor ${className}`}>
      <div className="flex h-full">
        {/* Main Editor Area */}
        <div className="flex-1 flex flex-col border-r border-gray-200">
          {/* Workflow Info */}
          <div className="p-4 border-b border-gray-200 bg-gray-50">
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Workflow Name *
                </label>
                <input
                  type="text"
                  value={workflowName}
                  onChange={(e) => setWorkflowName(e.target.value)}
                  placeholder="My Workflow"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <input
                  type="text"
                  value={workflowDescription}
                  onChange={(e) => setWorkflowDescription(e.target.value)}
                  placeholder="What this workflow does..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Nodes List */}
          <div className="flex-1 p-4 overflow-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-gray-900">Nodes</h3>
              <button
                onClick={addNode}
                className="inline-flex items-center px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
              >
                <Plus className="w-4 h-4 mr-1" />
                Add Node
              </button>
            </div>

            {/* Simple Visual List */}
            <div className="space-y-2">
              {nodes.map((node, index) => (
                <div
                  key={node.node_id}
                  className={`p-3 border rounded-lg cursor-pointer transition ${
                    selectedNode?.node_id === node.node_id
                      ? "border-blue-500 bg-blue-50"
                      : "border-gray-200 hover:border-gray-300"
                  }`}
                  onClick={() => setSelectedNode(node)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-500">{index + 1}.</span>
                      <span className="font-medium text-gray-900">{node.name}</span>
                      <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
                        {node.node_type}
                      </span>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteNode(node.node_id);
                      }}
                      className="p-1 text-gray-400 hover:text-red-600 transition"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {/* Edges Visualization */}
            {edges.length > 0 && (
              <div className="mt-6">
                <h4 className="text-sm font-semibold text-gray-900 mb-3">Connections</h4>
                <div className="space-y-1">
                  {edges.map((edge, index) => {
                    const sourceNode = nodes.find((n) => n.node_id === edge.source_node_id);
                    const targetNode = nodes.find((n) => n.node_id === edge.target_node_id);
                    return (
                      <div
                        key={index}
                        className="flex items-center gap-2 text-sm text-gray-600 p-2 bg-gray-50 rounded"
                      >
                        <span>{sourceNode?.name || edge.source_node_id}</span>
                        <ArrowRight className="w-4 h-4" />
                        <span>{targetNode?.name || edge.target_node_id}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="p-4 border-t border-gray-200 bg-gray-50 flex items-center justify-between">
            <button
              onClick={onCancel}
              className="px-4 py-2 text-gray-700 hover:text-gray-900 transition"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="inline-flex items-center px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition"
            >
              <Save className="w-4 h-4 mr-2" />
              Save Workflow
            </button>
          </div>
        </div>

        {/* Node Configuration Panel */}
        {selectedNode && (
          <div className="w-80 bg-white border-l border-gray-200">
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <h3 className="font-semibold text-gray-900">Configure Node</h3>
              <button
                onClick={() => setSelectedNode(null)}
                className="p-1 text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-4 space-y-4">
              {/* Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input
                  type="text"
                  value={selectedNode.name}
                  onChange={(e) => updateNode(selectedNode.node_id, { name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                <select
                  value={selectedNode.node_type}
                  onChange={(e) => updateNode(selectedNode.node_id, { node_type: e.target.value as NodeType })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {nodeTypes.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label} - {type.description}
                    </option>
                  ))}
                </select>
              </div>

              {/* Agent ID (for agent nodes) */}
              {selectedNode.node_type === "agent" && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Agent ID</label>
                  <input
                    type="text"
                    value={selectedNode.agent_id || ""}
                    onChange={(e) => updateNode(selectedNode.node_id, { agent_id: e.target.value })}
                    placeholder="e.g., torq_prince_flowers"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              )}

              {/* Timeout */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Timeout (seconds)
                </label>
                <input
                  type="number"
                  value={selectedNode.timeout_seconds || ""}
                  onChange={(e) => updateNode(selectedNode.node_id, { timeout_seconds: parseInt(e.target.value) || undefined })}
                  placeholder="30"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Parameters */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Parameters</label>
                <div className="space-y-2">
                  {Object.entries(selectedNode.parameters || {}).map(([key, value]) => (
                    <div key={key} className="flex gap-2">
                      <input
                        type="text"
                        value={key}
                        readOnly
                        className="flex-1 px-2 py-1.5 border border-gray-300 rounded text-sm bg-gray-50"
                      />
                      <input
                        type="text"
                        value={typeof value === "object" ? JSON.stringify(value) : String(value)}
                        onChange={(e) => updateNodeParameter(selectedNode.node_id, key, e.target.value)}
                        className="flex-1 px-2 py-1.5 border border-gray-300 rounded text-sm"
                      />
                      <button
                        onClick={() => {
                          const params = { ...selectedNode.parameters };
                          delete params[key];
                          updateNode(selectedNode.node_id, { parameters: params });
                        }}
                        className="p-1 text-gray-400 hover:text-red-600"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                  <button
                    onClick={() => {
                      const params = selectedNode.parameters || {};
                      params[`param_${Object.keys(params).length + 1}`] = "";
                      updateNode(selectedNode.node_id, { parameters: params });
                    }}
                    className="w-full px-3 py-2 border border-dashed border-gray-300 rounded text-sm text-gray-500 hover:text-gray-700 hover:border-gray-400 transition"
                  >
                    + Add Parameter
                  </button>
                </div>
              </div>

              {/* Depends On (dependencies) */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Dependencies (runs after these nodes)
                </label>
                <div className="space-y-1">
                  {selectedNode.depends_on?.map((depId) => {
                    const depNode = nodes.find((n) => n.node_id === depId);
                    return (
                      <div key={depId} className="flex items-center justify-between p-2 bg-gray-50 rounded text-sm">
                        <span>{depNode?.name || depId}</span>
                        <button
                          onClick={() => {
                            const deps = (selectedNode.depends_on || []).filter((d) => d !== depId);
                            updateNode(selectedNode.node_id, { depends_on: deps });
                          }}
                          className="p-1 text-gray-400 hover:text-red-600"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </div>
                    );
                  })}
                  {nodes
                    .filter((n) => n.node_id !== selectedNode.node_id && !(selectedNode.depends_on || []).includes(n.node_id))
                    .map((node) => (
                      <button
                        key={node.node_id}
                        onClick={() => {
                          const deps = [...(selectedNode.depends_on || []), node.node_id];
                          updateNode(selectedNode.node_id, { depends_on: deps });
                        }}
                        className="w-full text-left px-2 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded transition"
                      >
                        + {node.name}
                      </button>
                    ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
