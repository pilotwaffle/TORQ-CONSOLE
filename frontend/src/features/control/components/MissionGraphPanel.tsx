/**
 * Operator Control Surface - Mission Graph Panel
 *
 * Interactive mission graph visualization using React Flow.
 * Shows nodes colored by state with click-to-detail functionality.
 */

import { useCallback, useMemo, useState } from "react";
import {
  ReactFlow,
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  BackgroundVariant,
  NodeTypes,
} from "reactflow";
import "reactflow/dist/style.css";
import { useMissionGraph, useNodeDetail } from "../hooks/useControlMissions";
import { NODE_STATUS_COLORS, type NodeState } from "../types/mission";
import { formatNodeType } from "../utils/formatters";
import { NodeTimeline } from "./NodeTimeline";

// ============================================================================
// Types
// ============================================================================

interface MissionGraphPanelProps {
  missionId: string;
  onNodeSelect?: (nodeId: string) => void;
  selectedNodeId?: string | null;
}

// ============================================================================
// Custom Node Component
// ============================================================================

interface CustomNodeData {
  label: string;
  nodeType: string;
  status: NodeState;
}

function CustomNode({ data }: { data: CustomNodeData }) {
  const statusColor = NODE_STATUS_COLORS[data.status];

  return (
    <div
      className={`px-4 py-2 rounded-lg border-2 shadow-md min-w-[150px] max-w-[200px] bg-white transition-all hover:shadow-lg`}
      style={{ borderColor: statusColor }}
    >
      {/* Status Indicator */}
      <div className="flex items-center gap-2 mb-1">
        <div
          className="w-2 h-2 rounded-full"
          style={{ backgroundColor: statusColor }}
        />
        <span className="text-xs font-medium text-gray-500 uppercase">
          {formatNodeType(data.nodeType)}
        </span>
      </div>

      {/* Node Title */}
      <div className="font-medium text-gray-900 text-sm leading-tight">
        {data.label}
      </div>

      {/* Status Badge */}
      <div className="mt-1">
        <span
          className="text-xs px-1.5 py-0.5 rounded"
          style={{ backgroundColor: `${statusColor}20`, color: statusColor }}
        >
          {data.status}
        </span>
      </div>
    </div>
  );
}

const nodeTypes: NodeTypes = {
  custom: CustomNode,
};

// ============================================================================
// Loading State
// ============================================================================

function LoadingState() {
  return (
    <div className="bg-white border rounded-lg shadow-sm p-8 flex items-center justify-center h-96">
      <div className="text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-gray-200 border-t-blue-600 mb-4" />
        <p className="text-sm text-gray-500">Loading mission graph...</p>
      </div>
    </div>
  );
}

// ============================================================================
// Empty State
// ============================================================================

function EmptyState() {
  return (
    <div className="bg-white border rounded-lg shadow-sm p-8 flex items-center justify-center h-96">
      <div className="text-center">
        <svg
          className="w-16 h-16 text-gray-300 mx-auto mb-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01"
          />
        </svg>
        <h3 className="text-lg font-medium text-gray-900 mb-1">No graph available</h3>
        <p className="text-sm text-gray-500">
          This mission doesn't have a graph structure yet.
        </p>
      </div>
    </div>
  );
}

// ============================================================================
// Node Detail Drawer
// ============================================================================

interface NodeDetailDrawerProps {
  missionId: string;
  nodeId: string;
  onClose: () => void;
}

function NodeDetailDrawer({ missionId, nodeId, onClose }: NodeDetailDrawerProps) {
  const { data, isLoading } = useNodeDetail(missionId, nodeId);

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/20"
        onClick={onClose}
      />

      {/* Drawer */}
      <div className="relative w-96 max-w-full bg-white shadow-xl h-full overflow-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b px-4 py-3 flex items-center justify-between">
          <h3 className="font-semibold text-gray-900">Node Details</h3>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-4">
          {isLoading ? (
            <div className="space-y-3">
              <div className="h-4 bg-gray-200 rounded animate-pulse" />
              <div className="h-4 bg-gray-200 rounded animate-pulse w-3/4" />
              <div className="h-20 bg-gray-200 rounded animate-pulse" />
            </div>
          ) : !data ? (
            <p className="text-sm text-gray-500">Failed to load node details.</p>
          ) : (
            <div className="space-y-4">
              {/* Title & Type */}
              <div>
                <h4 className="font-medium text-gray-900">{data.title}</h4>
                <p className="text-sm text-gray-500">{formatNodeType(data.type)}</p>
              </div>

              {/* Status */}
              <div className="flex items-center justify-between py-2 border-b">
                <span className="text-sm text-gray-500">Status</span>
                <span className="text-sm font-medium capitalize">{data.status}</span>
              </div>

              {/* Agent */}
              {data.agent_type && (
                <div className="flex items-center justify-between py-2 border-b">
                  <span className="text-sm text-gray-500">Agent</span>
                  <span className="text-sm font-medium capitalize">{data.agent_type}</span>
                </div>
              )}

              {/* Workstream */}
              {data.workstream_id && (
                <div className="flex items-center justify-between py-2 border-b">
                  <span className="text-sm text-gray-500">Workstream</span>
                  <span className="text-sm font-mono">{data.workstream_id.substring(0, 8)}</span>
                </div>
              )}

              {/* Description */}
              {data.description && (
                <div className="py-2 border-b">
                  <span className="text-sm text-gray-500 block mb-1">Description</span>
                  <p className="text-sm text-gray-700">{data.description}</p>
                </div>
              )}

              {/* Output Summary */}
              {data.output_summary && (
                <div className="py-2 border-b">
                  <span className="text-sm text-gray-500 block mb-1">Output</span>
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">{data.output_summary}</p>
                </div>
              )}

              {/* Timestamps */}
              <div className="py-2 border-b space-y-1">
                <span className="text-sm text-gray-500 block">Timeline</span>
                <div className="text-xs space-y-1">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Created:</span>
                    <span className="text-gray-700">{new Date(data.created_at).toLocaleString()}</span>
                  </div>
                  {data.started_at && (
                    <div className="flex justify-between">
                      <span className="text-gray-500">Started:</span>
                      <span className="text-gray-700">{new Date(data.started_at).toLocaleString()}</span>
                    </div>
                  )}
                  {data.completed_at && (
                    <div className="flex justify-between">
                      <span className="text-gray-500">Completed:</span>
                      <span className="text-gray-700">{new Date(data.completed_at).toLocaleString()}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Node Timeline */}
              <NodeTimeline missionId={missionId} nodeId={nodeId} />

              {/* Counts */}
              <div className="flex gap-4 py-2">
                <div className="flex-1 bg-blue-50 rounded p-2 text-center">
                  <div className="text-xl font-semibold text-blue-600">{data.event_count}</div>
                  <div className="text-xs text-blue-500">Events</div>
                </div>
                <div className="flex-1 bg-purple-50 rounded p-2 text-center">
                  <div className="text-xl font-semibold text-purple-600">{data.handoff_count}</div>
                  <div className="text-xs text-purple-500">Handoffs</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Legend Component
// ============================================================================

function GraphLegend() {
  const legendItems: Array<{ status: NodeState; label: string }> = [
    { status: "completed", label: "Completed" },
    { status: "running", label: "Running" },
    { status: "ready", label: "Ready" },
    { status: "pending", label: "Pending" },
    { status: "blocked", label: "Blocked" },
    { status: "failed", label: "Failed" },
  ];

  return (
    <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-md border p-3 z-10">
      <div className="text-xs font-medium text-gray-700 mb-2">Node Status</div>
      <div className="space-y-1">
        {legendItems.map((item) => (
          <div key={item.status} className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded"
              style={{ backgroundColor: NODE_STATUS_COLORS[item.status] }}
            />
            <span className="text-xs text-gray-600">{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function MissionGraphPanel({
  missionId,
  onNodeSelect,
  selectedNodeId: propSelectedNodeId,
}: MissionGraphPanelProps) {
  const { data, isLoading, isError } = useMissionGraph(missionId);
  const [internalSelectedNodeId, setInternalSelectedNodeId] = useState<string | null>(null);
  const selectedNodeId = propSelectedNodeId ?? internalSelectedNodeId;

  const { data: nodeDetail } = useNodeDetail(
    missionId,
    selectedNodeId ?? undefined
  );

  // Convert API response to React Flow format
  const { initialNodes, initialEdges } = useMemo(() => {
    if (!data) return { initialNodes: [], initialEdges: [] };

    // Create nodes with auto-layout (simple hierarchical)
    const nodes: Node[] = data.nodes.map((node, index) => {
      // Simple layout: arrange in rows based on index
      const row = Math.floor(index / 4);
      const col = index % 4;

      return {
        id: node.id,
        type: "custom",
        position: node.position || { x: col * 250, y: row * 150 },
        data: {
          label: node.title,
          nodeType: node.type,
          status: node.status,
        },
        sourcePosition: "bottom",
        targetPosition: "top",
      };
    });

    const edges: Edge[] = data.edges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      animated: edge.condition !== null, // Animate conditional edges
      label: edge.condition,
      labelStyle: { fontSize: 10, fontWeight: 500 },
      labelBgStyle: { fill: "#f0f0f0", fillOpacity: 0.7 },
      style: { stroke: edge.condition ? "#f59e0b" : "#94a3b8", strokeWidth: 2 },
    }));

    return { initialNodes, initialEdges };
  }, [data]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Update nodes/edges when data changes
  useMemo(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  const handleNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      const nodeId = node.id;
      setInternalSelectedNodeId(nodeId);
      if (onNodeSelect) {
        onNodeSelect(nodeId);
      }
    },
    [onNodeSelect]
  );

  const handleCloseDrawer = useCallback(() => {
    setInternalSelectedNodeId(null);
  }, []);

  if (isLoading) {
    return <LoadingState />;
  }

  if (isError || !data || data.nodes.length === 0) {
    return <EmptyState />;
  }

  return (
    <div className="bg-white border rounded-lg shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-gray-50 border-b flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Mission Graph</h2>
        <div className="text-sm text-gray-500">
          {data.nodes.length} nodes • {data.edges.length} edges
        </div>
      </div>

      {/* Graph Canvas */}
      <div className="h-[600px] relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={handleNodeClick}
          nodeTypes={nodeTypes}
          fitView
          defaultEdgeOptions={{
            animated: false,
            style: { strokeWidth: 2 },
          }}
        >
          <Background variant={BackgroundVariant.Dots} gap={16} size={1} />
          <Controls />
          <MiniMap
            nodeColor={(node) => {
              const data = node.data as CustomNodeData;
              return NODE_STATUS_COLORS[data.status];
            }}
            className="!bg-gray-50 !border !border-gray-200"
          />
        </ReactFlow>

        {/* Legend */}
        <GraphLegend />
      </div>

      {/* Node Detail Drawer */}
      {selectedNodeId && (
        <NodeDetailDrawer
          missionId={missionId}
          nodeId={selectedNodeId}
          onClose={handleCloseDrawer}
        />
      )}
    </div>
  );
}
