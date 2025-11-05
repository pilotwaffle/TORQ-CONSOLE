import React from 'react';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import { useAgentStore } from '@/stores/agentStore';
import type { Agent } from '@/lib/types';

const AgentCard: React.FC<{ agent: Agent; isActive: boolean }> = ({ agent, isActive }) => {
  const { setActiveAgent } = useAgentStore();

  const statusColors = {
    idle: 'secondary',
    thinking: 'warning',
    active: 'active',
    error: 'error',
    success: 'success',
  } as const;

  const agentIcons = {
    code: '💻',
    debug: '🐛',
    docs: '📚',
    test: '🧪',
    architecture: '🏗️',
    research: '🔍',
  };

  return (
    <Card
      className={`p-3 cursor-pointer transition-all hover:border-border-focus ${
        isActive ? 'border-accent-primary bg-bg-tertiary' : ''
      }`}
      onClick={() => setActiveAgent(agent.id)}
    >
      <div className="flex items-center gap-3">
        <div className="text-2xl">{agentIcons[agent.type]}</div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-body font-medium truncate">{agent.name}</span>
            <Badge variant={statusColors[agent.status]} className="text-xs">
              {agent.status}
            </Badge>
          </div>
          <p className="text-small text-text-muted truncate">
            {agent.capabilities.slice(0, 2).join(', ')}
          </p>
        </div>
      </div>
    </Card>
  );
};

export const AgentSidebar: React.FC = () => {
  const { agents, activeAgentId } = useAgentStore();

  return (
    <div className="w-80 bg-bg-secondary border-r border-border flex flex-col">
      <div className="p-4 border-b border-border">
        <h2 className="text-h3 font-semibold">Agents</h2>
        <p className="text-small text-text-muted mt-1">
          {agents.length} agent{agents.length !== 1 ? 's' : ''} available
        </p>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-2">
        {agents.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-text-muted text-small">No agents available</p>
            <p className="text-text-muted text-small mt-1">
              Connect to the TORQ backend to see agents
            </p>
          </div>
        ) : (
          agents.map((agent) => (
            <AgentCard
              key={agent.id}
              agent={agent}
              isActive={agent.id === activeAgentId}
            />
          ))
        )}
      </div>

      <div className="p-4 border-t border-border">
        <div className="flex gap-2">
          <button className="flex-1 text-small text-text-muted hover:text-text-primary transition-colors">
            Add Agent
          </button>
          <button className="flex-1 text-small text-text-muted hover:text-text-primary transition-colors">
            Settings
          </button>
        </div>
      </div>
    </div>
  );
};
