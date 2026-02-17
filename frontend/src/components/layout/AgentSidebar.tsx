import React, { useState } from 'react';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import { useAgentStore } from '@/stores/agentStore';
import { AddAgentModal } from './AddAgentModal';
import { SettingsModal } from './SettingsModal';
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

  const agentIcons: Record<string, string> = {
    orchestrator: '🌸',
    code: '💻',
    debug: '🐛',
    docs: '📚',
    test: '🧪',
    architecture: '🏗️',
    research: '🔍',
  };

  return (
    <Card
      className={`p-3 cursor-pointer transition-all hover:border-border-focus ${isActive ? 'border-accent-primary bg-bg-tertiary' : ''
        }`}
      onClick={() => setActiveAgent(agent.id)}
    >
      <div className="flex items-center gap-3">
        <div className="text-2xl">{agentIcons[agent.type] || '🤖'}</div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-body font-medium truncate">{agent.name}</span>
            <Badge variant={statusColors[agent.status as keyof typeof statusColors] || 'secondary'} className="text-xs">
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
  const [isAddAgentOpen, setIsAddAgentOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  return (
    <>
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
            <button
              onClick={() => setIsAddAgentOpen(true)}
              className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-small text-text-muted hover:text-text-primary hover:bg-bg-tertiary transition-all border border-transparent hover:border-border"
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M7 1V13M1 7H13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
              Add Agent
            </button>
            <button
              onClick={() => setIsSettingsOpen(true)}
              className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-small text-text-muted hover:text-text-primary hover:bg-bg-tertiary transition-all border border-transparent hover:border-border"
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="7" cy="7" r="2" stroke="currentColor" strokeWidth="1.5" />
                <path d="M7 1V3M7 11V13M1 7H3M11 7H13M2.76 2.76L4.17 4.17M9.83 9.83L11.24 11.24M11.24 2.76L9.83 4.17M4.17 9.83L2.76 11.24" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
              Settings
            </button>
          </div>
        </div>
      </div>

      {/* Modals */}
      <AddAgentModal isOpen={isAddAgentOpen} onClose={() => setIsAddAgentOpen(false)} />
      <SettingsModal isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
    </>
  );
};
