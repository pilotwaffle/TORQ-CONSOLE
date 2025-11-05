import React, { useEffect } from 'react';
import { useCoordinationStore } from '@/stores/coordinationStore';
import { AgentCard } from './AgentCard';
import { WorkflowGraph } from './WorkflowGraph';

export const CoordinationPanel: React.FC = () => {
  const {
    activeWorkflows,
    currentWorkflowId,
    viewMode,
    isExpanded,
    setViewMode,
    toggleExpanded,
    setCurrentWorkflow,
    cancelWorkflow,
    getCurrentWorkflow,
    hasActiveWorkflows,
  } = useCoordinationStore();

  const currentWorkflow = getCurrentWorkflow();
  const isActive = hasActiveWorkflows();

  useEffect(() => {
    // Auto-collapse when no active workflows
    if (!isActive && isExpanded) {
      toggleExpanded();
    }
  }, [isActive, isExpanded, toggleExpanded]);

  if (!isActive) {
    return null;
  }

  const getStatusColor = (
    status: 'initializing' | 'running' | 'paused' | 'complete' | 'cancelled' | 'error'
  ): string => {
    switch (status) {
      case 'running':
        return 'text-agent-thinking';
      case 'complete':
        return 'text-agent-success';
      case 'error':
      case 'cancelled':
        return 'text-agent-error';
      default:
        return 'text-text-muted';
    }
  };

  const getStatusIcon = (
    status: 'initializing' | 'running' | 'paused' | 'complete' | 'cancelled' | 'error'
  ): string => {
    switch (status) {
      case 'initializing':
        return '⏳';
      case 'running':
        return '⚡';
      case 'paused':
        return '⏸️';
      case 'complete':
        return '✓';
      case 'cancelled':
        return '⊘';
      case 'error':
        return '✕';
      default:
        return '○';
    }
  };

  const formatDuration = (startTime: number, endTime?: number): string => {
    const duration = (endTime || Date.now()) - startTime;
    const seconds = Math.floor(duration / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
    return `${seconds}s`;
  };

  return (
    <div
      className={`
        fixed bottom-0 left-0 right-0 z-50 bg-bg-secondary border-t border-border
        transition-all duration-300 ease-in-out shadow-2xl
        ${isExpanded ? 'h-96' : 'h-14'}
      `}
    >
      {/* Header Bar */}
      <div
        className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-bg-tertiary transition-colors"
        onClick={toggleExpanded}
      >
        <div className="flex items-center space-x-4">
          {/* Expand/Collapse Icon */}
          <div
            className={`
              text-text-secondary transition-transform duration-200
              ${isExpanded ? 'rotate-180' : ''}
            `}
          >
            ▲
          </div>

          {/* Title and Count */}
          <div className="flex items-center space-x-3">
            <h2 className="text-sm font-semibold text-text-primary">
              Multi-Agent Coordination
            </h2>
            <span className="text-xs bg-accent-primary text-white px-2 py-1 rounded-full">
              {activeWorkflows.filter((w) =>
                ['initializing', 'running', 'paused'].includes(w.status)
              ).length}{' '}
              Active
            </span>
          </div>

          {/* Current Workflow Info */}
          {currentWorkflow && (
            <div className="flex items-center space-x-3 ml-4">
              <span
                className={`text-lg ${
                  currentWorkflow.status === 'running' ? 'animate-pulse-soft' : ''
                }`}
              >
                {getStatusIcon(currentWorkflow.status)}
              </span>
              <div className="flex flex-col">
                <span className="text-xs text-text-secondary">
                  {currentWorkflow.description}
                </span>
                <div className="flex items-center space-x-2 text-xs text-text-muted">
                  <span>
                    {currentWorkflow.completedAgents}/{currentWorkflow.totalAgents}{' '}
                    agents
                  </span>
                  <span>•</span>
                  <span>{formatDuration(currentWorkflow.startTime, currentWorkflow.endTime)}</span>
                  <span>•</span>
                  <span className={getStatusColor(currentWorkflow.status)}>
                    {currentWorkflow.status}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center space-x-2" onClick={(e) => e.stopPropagation()}>
          {/* View Mode Toggle */}
          {isExpanded && (
            <div className="flex items-center bg-bg-tertiary rounded-md p-1">
              <button
                onClick={() => setViewMode('list')}
                className={`
                  px-3 py-1 text-xs rounded transition-colors
                  ${
                    viewMode === 'list'
                      ? 'bg-accent-primary text-white'
                      : 'text-text-secondary hover:text-text-primary'
                  }
                `}
              >
                List
              </button>
              <button
                onClick={() => setViewMode('graph')}
                className={`
                  px-3 py-1 text-xs rounded transition-colors
                  ${
                    viewMode === 'graph'
                      ? 'bg-accent-primary text-white'
                      : 'text-text-secondary hover:text-text-primary'
                  }
                `}
              >
                Graph
              </button>
            </div>
          )}

          {/* Cancel Button */}
          {currentWorkflow && currentWorkflow.status === 'running' && (
            <button
              onClick={() => {
                if (currentWorkflow) {
                  cancelWorkflow(currentWorkflow.id);
                }
              }}
              className="px-3 py-1 text-xs bg-agent-error hover:bg-opacity-80 text-white rounded transition-colors"
            >
              Cancel
            </button>
          )}
        </div>
      </div>

      {/* Content Area */}
      {isExpanded && currentWorkflow && (
        <div className="h-[calc(100%-56px)] overflow-hidden">
          {/* Workflow Tabs */}
          {activeWorkflows.length > 1 && (
            <div className="flex items-center space-x-2 px-4 py-2 bg-bg-primary border-b border-border overflow-x-auto scrollbar-thin">
              {activeWorkflows.map((workflow) => (
                <button
                  key={workflow.id}
                  onClick={() => setCurrentWorkflow(workflow.id)}
                  className={`
                    flex items-center space-x-2 px-3 py-1.5 rounded text-xs whitespace-nowrap
                    transition-colors
                    ${
                      workflow.id === currentWorkflowId
                        ? 'bg-accent-primary text-white'
                        : 'bg-bg-tertiary text-text-secondary hover:text-text-primary'
                    }
                  `}
                >
                  <span>{getStatusIcon(workflow.status)}</span>
                  <span className="truncate max-w-xs">{workflow.description}</span>
                  <span className="text-xs opacity-70">
                    {workflow.completedAgents}/{workflow.totalAgents}
                  </span>
                </button>
              ))}
            </div>
          )}

          {/* Main Content */}
          <div className="h-[calc(100%-48px)] overflow-auto scrollbar-thin p-4">
            {viewMode === 'list' ? (
              <div className="space-y-3">
                {/* Overall Progress */}
                <div className="bg-bg-primary rounded-lg border border-border p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-semibold text-text-primary">
                      Overall Progress
                    </span>
                    <span className="text-sm font-mono text-text-secondary">
                      {currentWorkflow.overallProgress}%
                    </span>
                  </div>
                  <div className="w-full bg-bg-tertiary rounded-full h-2 overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-accent-primary to-agent-success transition-all duration-500"
                      style={{ width: `${currentWorkflow.overallProgress}%` }}
                    />
                  </div>
                </div>

                {/* Agent Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {currentWorkflow.agents.map((agent) => (
                    <AgentCard
                      key={agent.agentId}
                      agent={agent}
                      isActive={agent.agentId === currentWorkflow.currentAgent}
                    />
                  ))}
                </div>
              </div>
            ) : (
              <WorkflowGraph workflow={currentWorkflow} />
            )}
          </div>
        </div>
      )}
    </div>
  );
};
