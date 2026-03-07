/**
 * Workflow Graph Canvas
 *
 * Main DAG visualization component using React Flow.
 * Displays workflow nodes and edges with interactive controls.
 */

import { useCallback, useEffect, useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  type Connection,
  type Edge,
  type Node,
  type NodeTypes,
} from "reactflow";
import "reactflow/dist/style.css";

import type {
  CreateWorkflowResponse,
  WorkflowNode,
  WorkflowEdge,
  NodeStatus,
  NodeType,
} from "@workflows/api";
import { WorkflowNodeComponent } from "./WorkflowNode";
import { getNodeStatusColor } from "@workflows/utils/workflowFormatters";
import { useWorkflowUiStore } from "@workflows/stores/workflowUiStore";

interface WorkflowGraphCanvasProps {
  workflow: CreateWorkflowResponse;
  nodeStatuses?: Record<string, NodeStatus>;
  onNodeClick?: (nodeId: string) => void;
  readonly?: boolean;
  className?: string;
}

const nodeTypes: NodeTypes = {
  workflowNode: WorkflowNodeComponent,
};

// Icon mapping for node types
const NodeIcons: Record<NodeType, string> = {
  agent: "cpu",
  tool: "settings",
  api_call: "globe",
  analysis: "search",
  condition: "git-branch",
  parallel: "git-merge",
  sequential: "arrow-right",
};

// Convert workflow graph to React Flow nodes
function convertToReactFlowNodes(
  workflowNodes: WorkflowNode[],
  nodeStatuses?: Record<string, NodeStatus>
): Node[] {
  return workflowNodes.map((node, index) => {
    const status = nodeStatuses?.[node.node_id];
    const statusColor = status ? getNodeStatusColor(status) : undefined;
    const strokeColor = statusColor?.match(/stroke-([a-z0-9]+)/)?.[1] || "#6b7280";

    return {
      id: node.node_id,
      type: "workflowNode",
      position: {
        x: node.position_x ?? 0,
        y: node.position_y ?? index * 120,
      },
      data: {
        id: node.node_id,
        name: node.name,
        type: node.node_type,
        agentId: node.agent_id,
        status: status,
        config: node.parameters,
      },
      style: statusColor
        ? {
            stroke: strokeColor,
            strokeWidth: 2,
          }
        : undefined,
    };
  });
}

// Convert workflow edges to React Flow format
function convertToReactFlowEdges(workflowEdges: WorkflowEdge[]): Edge[] {
  return workflowEdges.map((edge, index) => ({
    id: `edge-${index}`,
    source: edge.source_node_id,
    target: edge.target_node_id,
    label: edge.condition ? JSON.stringify(edge.condition) : undefined,
    type: "smoothstep",
    animated: false,
    style: { stroke: "#94a3b8", strokeWidth: 2 },
  }));
}

export function WorkflowGraphCanvas({
  workflow,
  nodeStatuses,
  onNodeClick,
  readonly = true,
  className = "",
}: WorkflowGraphCanvasProps) {
  const { selectedNodeId, setSelectedNodeId } = useWorkflowUiStore();

  // Convert workflow data to React Flow format
  const initialNodes = useMemo(
    () => convertToReactFlowNodes(workflow.nodes || [], nodeStatuses),
    [workflow.nodes, nodeStatuses]
  );

  const initialEdges = useMemo(
    () => convertToReactFlowEdges(workflow.edges || []),
    [workflow.edges]
  );

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Update nodes when workflow or statuses change
  useEffect(() => {
    setNodes(convertToReactFlowNodes(workflow.nodes || [], nodeStatuses));
  }, [workflow, nodeStatuses, setNodes]);

  useEffect(() => {
    setEdges(convertToReactFlowEdges(workflow.edges || []));
  }, [workflow.edges, setEdges]);

  // Handle new connections (only in edit mode)
  const onConnect = useCallback(
    (connection: Connection) => {
      if (readonly) return;
      setEdges((eds) => addEdge(connection, eds));
    },
    [readonly, setEdges]
  );

  // Handle node click
  const onNodeClickHandler = useCallback(
    (_: unknown, node: Node) => {
      setSelectedNodeId(node.id);
      onNodeClick?.(node.id);
    },
    [setSelectedNodeId, onNodeClick]
  );

  return (
    <div className={`workflow-graph-container ${className}`}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={readonly ? undefined : onNodesChange}
        onEdgesChange={readonly ? undefined : onEdgesChange}
        onConnect={onConnect}
        onNodeClick={readonly ? onNodeClickHandler : undefined}
        nodeTypes={nodeTypes}
        fitView
        snapToGrid
        snapGrid={[15, 15]}
        defaultViewport={{ x: 0, y: 0, zoom: 1 }}
        minZoom={0.2}
        maxZoom={2}
        panOnScroll
        selectionOnDrag
        nodesDraggable={!readonly}
        nodesConnectable={!readonly}
        elementsSelectable
        selectNodesOnDrag={false}
        proOptions={{ hideAttribution: true }}
      >
        <Background gap={16} size={1} color="#e2e8f0" />
        <Controls showZoom showFitView showInteractive={!readonly} />
        <MiniMap
          nodeColor={(node) => {
            const nodeData = node.data as { status?: NodeStatus };
            if (nodeData.status) {
              const color = getNodeStatusColor(nodeData.status);
              return color.match(/fill-([a-z0-9]+)/)?.[1] || "#94a3b8";
            }
            return "#3b82f6";
          }}
          nodeStrokeWidth={3}
          nodeBorderRadius={8}
          pannable
          zoomable
        />
      </ReactFlow>
    </div>
  );
}
