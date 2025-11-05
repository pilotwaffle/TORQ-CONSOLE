import { create } from 'zustand';
import websocketManager from '@/services/websocket';

export type WorkflowType = 'pipeline' | 'parallel' | 'multi' | 'single';

export interface AgentProgress {
  agentId: string;
  agentName: string;
  agentType: string;
  status: 'idle' | 'working' | 'complete' | 'error';
  progress: number;
  currentTask?: string;
  lastAction?: string;
  lastActionTimestamp?: number;
  output?: string;
  error?: string;
}

export interface WorkflowExecution {
  id: string;
  type: WorkflowType;
  status: 'initializing' | 'running' | 'paused' | 'complete' | 'cancelled' | 'error';
  startTime: number;
  endTime?: number;
  totalAgents: number;
  completedAgents: number;
  agents: AgentProgress[];
  description: string;
  dependencies?: Record<string, string[]>;
  currentAgent?: string;
  overallProgress: number;
}

interface CoordinationState {
  // State
  activeWorkflows: WorkflowExecution[];
  currentWorkflowId: string | null;
  viewMode: 'list' | 'graph';
  isExpanded: boolean;

  // Actions
  setViewMode: (mode: 'list' | 'graph') => void;
  setExpanded: (expanded: boolean) => void;
  toggleExpanded: () => void;

  // Workflow management
  addWorkflow: (workflow: WorkflowExecution) => void;
  updateWorkflow: (workflowId: string, updates: Partial<WorkflowExecution>) => void;
  removeWorkflow: (workflowId: string) => void;
  setCurrentWorkflow: (workflowId: string | null) => void;
  cancelWorkflow: (workflowId: string) => void;

  // Agent management within workflows
  updateAgentProgress: (
    workflowId: string,
    agentId: string,
    updates: Partial<AgentProgress>
  ) => void;

  // WebSocket integration
  initializeWebSocket: () => void;
  disconnectWebSocket: () => void;

  // Computed getters
  getCurrentWorkflow: () => WorkflowExecution | null;
  hasActiveWorkflows: () => boolean;
  getWorkflowById: (id: string) => WorkflowExecution | null;
}

export const useCoordinationStore = create<CoordinationState>((set, get) => ({
  // Initial state
  activeWorkflows: [],
  currentWorkflowId: null,
  viewMode: 'list',
  isExpanded: false,

  // Actions
  setViewMode: (mode) => set({ viewMode: mode }),

  setExpanded: (expanded) => set({ isExpanded: expanded }),

  toggleExpanded: () => set((state) => ({ isExpanded: !state.isExpanded })),

  // Workflow management
  addWorkflow: (workflow) =>
    set((state) => ({
      activeWorkflows: [...state.activeWorkflows, workflow],
      currentWorkflowId: workflow.id,
      isExpanded: true,
    })),

  updateWorkflow: (workflowId, updates) =>
    set((state) => ({
      activeWorkflows: state.activeWorkflows.map((workflow) =>
        workflow.id === workflowId
          ? {
              ...workflow,
              ...updates,
              overallProgress: calculateOverallProgress({
                ...workflow,
                ...updates,
              }),
            }
          : workflow
      ),
    })),

  removeWorkflow: (workflowId) =>
    set((state) => {
      const filtered = state.activeWorkflows.filter((w) => w.id !== workflowId);
      return {
        activeWorkflows: filtered,
        currentWorkflowId:
          state.currentWorkflowId === workflowId
            ? filtered[0]?.id || null
            : state.currentWorkflowId,
      };
    }),

  setCurrentWorkflow: (workflowId) => set({ currentWorkflowId: workflowId }),

  cancelWorkflow: (workflowId) => {
    const workflow = get().getWorkflowById(workflowId);
    if (workflow && workflow.status === 'running') {
      get().updateWorkflow(workflowId, {
        status: 'cancelled',
        endTime: Date.now(),
      });

      // Send cancel request via WebSocket
      websocketManager.emit('cancelWorkflow', { workflowId });
    }
  },

  // Agent progress updates
  updateAgentProgress: (workflowId, agentId, updates) =>
    set((state) => ({
      activeWorkflows: state.activeWorkflows.map((workflow) => {
        if (workflow.id !== workflowId) return workflow;

        const updatedAgents = workflow.agents.map((agent) =>
          agent.agentId === agentId
            ? { ...agent, ...updates, lastActionTimestamp: Date.now() }
            : agent
        );

        const completedCount = updatedAgents.filter(
          (a) => a.status === 'complete'
        ).length;

        return {
          ...workflow,
          agents: updatedAgents,
          completedAgents: completedCount,
          currentAgent: updates.status === 'working' ? agentId : workflow.currentAgent,
          overallProgress: (completedCount / workflow.totalAgents) * 100,
        };
      }),
    })),

  // WebSocket initialization
  initializeWebSocket: () => {
    // Workflow started event
    websocketManager.on('onWorkflowStarted', (data: any) => {
      const workflow: WorkflowExecution = {
        id: data.workflowId || `workflow_${Date.now()}`,
        type: data.type || 'multi',
        status: 'running',
        startTime: Date.now(),
        totalAgents: data.agents?.length || 0,
        completedAgents: 0,
        agents: (data.agents || []).map((agent: any) => ({
          agentId: agent.id,
          agentName: agent.name,
          agentType: agent.type,
          status: 'idle',
          progress: 0,
        })),
        description: data.description || 'Multi-agent workflow',
        dependencies: data.dependencies,
        overallProgress: 0,
      };

      get().addWorkflow(workflow);
    });

    // Agent status updates
    websocketManager.on('onWorkflowAgentUpdate', (data: any) => {
      const { workflowId, agentId, status, progress, currentTask, output, error } =
        data;

      get().updateAgentProgress(workflowId, agentId, {
        status,
        progress: progress || 0,
        currentTask,
        output,
        error,
        lastAction: currentTask,
      });
    });

    // Workflow completed
    websocketManager.on('onWorkflowComplete', (data: any) => {
      const { workflowId } = data;
      get().updateWorkflow(workflowId, {
        status: 'complete',
        endTime: Date.now(),
        overallProgress: 100,
      });
    });

    // Workflow error
    websocketManager.on('onWorkflowError', (data: any) => {
      const { workflowId, error } = data;
      get().updateWorkflow(workflowId, {
        status: 'error',
        endTime: Date.now(),
      });
    });

    // Agent output streaming
    websocketManager.on('onAgentOutput', (data: any) => {
      const { workflowId, agentId, output, append } = data;

      const workflow = get().getWorkflowById(workflowId);
      if (!workflow) return;

      const agent = workflow.agents.find((a) => a.agentId === agentId);
      const currentOutput = agent?.output || '';

      get().updateAgentProgress(workflowId, agentId, {
        output: append ? currentOutput + output : output,
      });
    });
  },

  // WebSocket disconnection
  disconnectWebSocket: () => {
    websocketManager.off('onWorkflowStarted');
    websocketManager.off('onWorkflowAgentUpdate');
    websocketManager.off('onWorkflowComplete');
    websocketManager.off('onWorkflowError');
    websocketManager.off('onAgentOutput');
  },

  // Computed getters
  getCurrentWorkflow: () => {
    const state = get();
    return (
      state.activeWorkflows.find((w) => w.id === state.currentWorkflowId) || null
    );
  },

  hasActiveWorkflows: () => {
    return get().activeWorkflows.some((w) =>
      ['initializing', 'running', 'paused'].includes(w.status)
    );
  },

  getWorkflowById: (id) => {
    return get().activeWorkflows.find((w) => w.id === id) || null;
  },
}));

// Helper function to calculate overall progress
function calculateOverallProgress(workflow: WorkflowExecution): number {
  if (workflow.totalAgents === 0) return 0;

  const totalProgress = workflow.agents.reduce(
    (sum, agent) => sum + agent.progress,
    0
  );

  return Math.min(100, Math.round(totalProgress / workflow.totalAgents));
}

// Initialize WebSocket on store creation
if (typeof window !== 'undefined') {
  const store = useCoordinationStore.getState();
  store.initializeWebSocket();
}
