import React, { useMemo } from 'react';
import { WorkflowExecution, AgentProgress } from '@/stores/coordinationStore';

interface WorkflowGraphProps {
  workflow: WorkflowExecution;
}

interface NodePosition {
  x: number;
  y: number;
}

interface Edge {
  from: string;
  to: string;
  isActive: boolean;
}

export const WorkflowGraph: React.FC<WorkflowGraphProps> = ({ workflow }) => {
  const { nodes, edges } = useMemo(() => {
    const agents = workflow.agents;
    const nodePositions: Record<string, NodePosition> = {};
    const calculatedEdges: Edge[] = [];

    // Layout logic based on workflow type
    if (workflow.type === 'pipeline') {
      // Linear layout for pipeline
      agents.forEach((agent, index) => {
        nodePositions[agent.agentId] = {
          x: 50 + (index * 400) / Math.max(agents.length - 1, 1),
          y: 150,
        };

        if (index > 0) {
          const isActive =
            agent.status === 'working' ||
            agents[index - 1].status === 'complete';
          calculatedEdges.push({
            from: agents[index - 1].agentId,
            to: agent.agentId,
            isActive,
          });
        }
      });
    } else if (workflow.type === 'parallel') {
      // Parallel layout - vertical arrangement
      const spacing = Math.min(100, 300 / Math.max(agents.length - 1, 1));
      agents.forEach((agent, index) => {
        nodePositions[agent.agentId] = {
          x: 250,
          y: 50 + index * spacing,
        };
      });
    } else if (workflow.type === 'multi') {
      // Multi-agent with dependencies
      const dependencies = workflow.dependencies || {};
      const levels = assignLevels(agents, dependencies);
      const maxLevel = Math.max(...Object.values(levels));

      // Group agents by level
      const levelGroups: Record<number, string[]> = {};
      Object.entries(levels).forEach(([agentId, level]) => {
        if (!levelGroups[level]) levelGroups[level] = [];
        levelGroups[level].push(agentId);
      });

      // Position nodes
      Object.entries(levelGroups).forEach(([level, agentIds]) => {
        const levelNum = parseInt(level);
        const x = 50 + (levelNum * 400) / Math.max(maxLevel, 1);
        const spacing = Math.min(100, 300 / Math.max(agentIds.length - 1, 1));

        agentIds.forEach((agentId, index) => {
          const centerOffset = (agentIds.length - 1) * spacing / 2;
          nodePositions[agentId] = {
            x,
            y: 150 - centerOffset + index * spacing,
          };
        });
      });

      // Create edges based on dependencies
      Object.entries(dependencies).forEach(([agentId, deps]) => {
        deps.forEach((depId) => {
          const agent = agents.find((a) => a.agentId === agentId);
          const depAgent = agents.find((a) => a.agentId === depId);
          const isActive =
            depAgent?.status === 'complete' &&
            (agent?.status === 'working' || agent?.status === 'complete');

          calculatedEdges.push({
            from: depId,
            to: agentId,
            isActive,
          });
        });
      });
    } else {
      // Single agent - center it
      if (agents.length > 0) {
        nodePositions[agents[0].agentId] = { x: 250, y: 150 };
      }
    }

    return { nodes: nodePositions, edges: calculatedEdges };
  }, [workflow]);

  const getNodeColor = (agent: AgentProgress): string => {
    switch (agent.status) {
      case 'idle':
        return '#808080';
      case 'working':
        return '#f59e0b';
      case 'complete':
        return '#10b981';
      case 'error':
        return '#ef4444';
      default:
        return '#808080';
    }
  };

  const getNodeBorderColor = (agent: AgentProgress): string => {
    return agent.agentId === workflow.currentAgent ? '#0078d4' : getNodeColor(agent);
  };

  return (
    <div className="w-full h-full bg-bg-secondary rounded-lg border border-border overflow-hidden">
      <svg
        width="100%"
        height="100%"
        viewBox="0 0 500 300"
        className="w-full h-full"
        style={{ minHeight: '300px' }}
      >
        <defs>
          {/* Animated gradient for active connections */}
          <linearGradient id="activeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#0078d4" stopOpacity="0">
              <animate
                attributeName="offset"
                values="0;1"
                dur="2s"
                repeatCount="indefinite"
              />
            </stop>
            <stop offset="50%" stopColor="#0086f0" stopOpacity="1">
              <animate
                attributeName="offset"
                values="0.5;1.5"
                dur="2s"
                repeatCount="indefinite"
              />
            </stop>
            <stop offset="100%" stopColor="#0078d4" stopOpacity="0">
              <animate
                attributeName="offset"
                values="1;2"
                dur="2s"
                repeatCount="indefinite"
              />
            </stop>
          </linearGradient>

          {/* Arrow marker */}
          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="10"
            refX="9"
            refY="3"
            orient="auto"
          >
            <polygon points="0 0, 10 3, 0 6" fill="#3e3e42" />
          </marker>

          <marker
            id="arrowhead-active"
            markerWidth="10"
            markerHeight="10"
            refX="9"
            refY="3"
            orient="auto"
          >
            <polygon points="0 0, 10 3, 0 6" fill="#0078d4" />
          </marker>
        </defs>

        {/* Draw edges (connections) */}
        {edges.map((edge, index) => {
          const fromPos = nodes[edge.from];
          const toPos = nodes[edge.to];

          if (!fromPos || !toPos) return null;

          const midX = (fromPos.x + toPos.x) / 2;
          const pathData = `M ${fromPos.x + 30} ${fromPos.y} Q ${midX} ${fromPos.y}, ${midX} ${
            (fromPos.y + toPos.y) / 2
          } Q ${midX} ${toPos.y}, ${toPos.x - 30} ${toPos.y}`;

          return (
            <g key={`edge-${index}`}>
              {edge.isActive ? (
                <>
                  <path
                    d={pathData}
                    fill="none"
                    stroke="#0078d4"
                    strokeWidth="2"
                    markerEnd="url(#arrowhead-active)"
                  />
                  <path
                    d={pathData}
                    fill="none"
                    stroke="url(#activeGradient)"
                    strokeWidth="3"
                    strokeOpacity="0.6"
                    strokeLinecap="round"
                  />
                </>
              ) : (
                <path
                  d={pathData}
                  fill="none"
                  stroke="#3e3e42"
                  strokeWidth="2"
                  markerEnd="url(#arrowhead)"
                  strokeDasharray="5,5"
                />
              )}
            </g>
          );
        })}

        {/* Draw nodes (agents) */}
        {workflow.agents.map((agent) => {
          const pos = nodes[agent.agentId];
          if (!pos) return null;

          const nodeColor = getNodeColor(agent);
          const borderColor = getNodeBorderColor(agent);
          const isActive = agent.agentId === workflow.currentAgent;

          return (
            <g key={agent.agentId} className="cursor-pointer">
              {/* Active glow effect */}
              {isActive && (
                <circle
                  cx={pos.x}
                  cy={pos.y}
                  r="35"
                  fill="none"
                  stroke="#0078d4"
                  strokeWidth="2"
                  opacity="0.3"
                >
                  <animate
                    attributeName="r"
                    values="35;40;35"
                    dur="2s"
                    repeatCount="indefinite"
                  />
                  <animate
                    attributeName="opacity"
                    values="0.3;0.1;0.3"
                    dur="2s"
                    repeatCount="indefinite"
                  />
                </circle>
              )}

              {/* Node circle */}
              <circle
                cx={pos.x}
                cy={pos.y}
                r="30"
                fill="#1e1e1e"
                stroke={borderColor}
                strokeWidth={isActive ? "3" : "2"}
              />

              {/* Progress ring */}
              <circle
                cx={pos.x}
                cy={pos.y}
                r="26"
                fill="none"
                stroke={nodeColor}
                strokeWidth="4"
                strokeDasharray={`${(agent.progress / 100) * 163.36} 163.36`}
                strokeLinecap="round"
                transform={`rotate(-90 ${pos.x} ${pos.y})`}
                opacity="0.8"
              />

              {/* Agent type icon (first letter) */}
              <text
                x={pos.x}
                y={pos.y}
                textAnchor="middle"
                dominantBaseline="central"
                fill="#ffffff"
                fontSize="14"
                fontWeight="bold"
                fontFamily="Inter, sans-serif"
              >
                {agent.agentType.charAt(0).toUpperCase()}
              </text>

              {/* Agent name label */}
              <text
                x={pos.x}
                y={pos.y + 45}
                textAnchor="middle"
                fill="#cccccc"
                fontSize="10"
                fontFamily="Inter, sans-serif"
              >
                {agent.agentName.length > 15
                  ? agent.agentName.substring(0, 12) + '...'
                  : agent.agentName}
              </text>

              {/* Status indicator */}
              <circle
                cx={pos.x + 20}
                cy={pos.y - 20}
                r="6"
                fill={nodeColor}
                stroke="#1e1e1e"
                strokeWidth="2"
              >
                {agent.status === 'working' && (
                  <animate
                    attributeName="opacity"
                    values="1;0.3;1"
                    dur="1s"
                    repeatCount="indefinite"
                  />
                )}
              </circle>
            </g>
          );
        })}

        {/* Workflow type label */}
        <text
          x="10"
          y="20"
          fill="#808080"
          fontSize="12"
          fontFamily="Inter, sans-serif"
        >
          Type: {workflow.type.toUpperCase()}
        </text>
      </svg>
    </div>
  );
};

// Helper function to assign levels to agents based on dependencies
function assignLevels(
  agents: AgentProgress[],
  dependencies: Record<string, string[]>
): Record<string, number> {
  const levels: Record<string, number> = {};
  const visited = new Set<string>();

  const assignLevel = (agentId: string): number => {
    if (visited.has(agentId)) return levels[agentId] || 0;
    visited.add(agentId);

    const deps = dependencies[agentId] || [];
    if (deps.length === 0) {
      levels[agentId] = 0;
      return 0;
    }

    const maxDepLevel = Math.max(...deps.map((depId) => assignLevel(depId)));
    levels[agentId] = maxDepLevel + 1;
    return levels[agentId];
  };

  agents.forEach((agent) => assignLevel(agent.agentId));

  return levels;
}
