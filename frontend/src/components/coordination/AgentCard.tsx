import React, { useState } from 'react';
import { AgentProgress } from '@/stores/coordinationStore';

interface AgentCardProps {
  agent: AgentProgress;
  isActive?: boolean;
}

export const AgentCard: React.FC<AgentCardProps> = ({ agent, isActive = false }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const getStatusColor = (status: AgentProgress['status']): string => {
    switch (status) {
      case 'idle':
        return 'text-text-muted';
      case 'working':
        return 'text-agent-thinking';
      case 'complete':
        return 'text-agent-success';
      case 'error':
        return 'text-agent-error';
      default:
        return 'text-text-muted';
    }
  };

  const getStatusBgColor = (status: AgentProgress['status']): string => {
    switch (status) {
      case 'idle':
        return 'bg-bg-tertiary';
      case 'working':
        return 'bg-agent-thinking bg-opacity-20';
      case 'complete':
        return 'bg-agent-success bg-opacity-20';
      case 'error':
        return 'bg-agent-error bg-opacity-20';
      default:
        return 'bg-bg-tertiary';
    }
  };

  const getStatusIcon = (status: AgentProgress['status']): string => {
    switch (status) {
      case 'idle':
        return '⏸️';
      case 'working':
        return '⚡';
      case 'complete':
        return '✓';
      case 'error':
        return '✕';
      default:
        return '○';
    }
  };

  const getProgressBarColor = (status: AgentProgress['status']): string => {
    switch (status) {
      case 'working':
        return 'bg-agent-thinking';
      case 'complete':
        return 'bg-agent-success';
      case 'error':
        return 'bg-agent-error';
      default:
        return 'bg-border';
    }
  };

  const formatTimestamp = (timestamp?: number): string => {
    if (!timestamp) return 'Never';
    const now = Date.now();
    const diff = now - timestamp;

    if (diff < 1000) return 'Just now';
    if (diff < 60000) return `${Math.floor(diff / 1000)}s ago`;
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    return `${Math.floor(diff / 3600000)}h ago`;
  };

  return (
    <div
      className={`
        rounded-md border transition-all duration-200 cursor-pointer
        ${isActive ? 'border-accent-primary shadow-lg' : 'border-border'}
        ${getStatusBgColor(agent.status)}
        hover:border-accent-hover
      `}
      onClick={() => setIsExpanded(!isExpanded)}
    >
      {/* Card Header */}
      <div className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-3 flex-1">
            {/* Status Icon */}
            <div
              className={`
                text-2xl mt-0.5 transition-transform duration-200
                ${agent.status === 'working' ? 'animate-pulse-soft' : ''}
              `}
            >
              {getStatusIcon(agent.status)}
            </div>

            {/* Agent Info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2">
                <h3 className="font-semibold text-text-primary truncate">
                  {agent.agentName}
                </h3>
                <span className="text-xs text-text-muted bg-bg-tertiary px-2 py-0.5 rounded">
                  {agent.agentType}
                </span>
              </div>

              {/* Status */}
              <div className={`text-sm mt-1 ${getStatusColor(agent.status)}`}>
                <span className="capitalize">{agent.status}</span>
                {agent.currentTask && (
                  <span className="text-text-secondary ml-2">
                    • {agent.currentTask}
                  </span>
                )}
              </div>

              {/* Progress Bar */}
              <div className="mt-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-text-muted">Progress</span>
                  <span className="text-xs font-mono text-text-secondary">
                    {agent.progress}%
                  </span>
                </div>
                <div className="w-full bg-bg-tertiary rounded-full h-1.5 overflow-hidden">
                  <div
                    className={`h-full transition-all duration-300 ${getProgressBarColor(
                      agent.status
                    )}`}
                    style={{ width: `${agent.progress}%` }}
                  />
                </div>
              </div>

              {/* Last Action */}
              {agent.lastAction && (
                <div className="mt-2 text-xs text-text-muted">
                  Last: {agent.lastAction} •{' '}
                  {formatTimestamp(agent.lastActionTimestamp)}
                </div>
              )}
            </div>
          </div>

          {/* Expand Indicator */}
          <div
            className={`
              ml-2 text-text-muted transition-transform duration-200
              ${isExpanded ? 'rotate-180' : ''}
            `}
          >
            ▼
          </div>
        </div>

        {/* Expanded Output */}
        {isExpanded && (agent.output || agent.error) && (
          <div className="mt-4 pt-4 border-t border-border">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-xs font-semibold text-text-secondary uppercase tracking-wide">
                {agent.error ? 'Error Output' : 'Agent Output'}
              </h4>
            </div>

            <div
              className={`
                p-3 rounded bg-bg-primary border max-h-64 overflow-y-auto scrollbar-thin
                ${agent.error ? 'border-agent-error' : 'border-border'}
              `}
            >
              <pre className="text-xs text-text-primary font-mono whitespace-pre-wrap break-words">
                {agent.error || agent.output || 'No output yet...'}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
