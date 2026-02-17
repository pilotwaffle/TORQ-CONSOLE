/**
 * TORQ Console Dashboard Store
 * 
 * Extends the existing agentStore pattern with:
 * - Chat message management with routing metadata
 * - API-driven agent loading (replaces WebSocket-only approach)
 * - Session management
 * - System status polling
 */

import { create } from 'zustand';
import torqApi from '@/services/torqApi';
import type {
  AgentInfo,
  UIMessage,
  UISession,
  OrchestrationMode,
  SystemStatus,
  ChatMetadata,
} from '@/types/api';

interface DashboardState {
  // Data
  agents: AgentInfo[];
  sessions: UISession[];
  activeSessionId: string | null;
  systemStatus: SystemStatus | null;
  selectedMode: OrchestrationMode;
  selectedAgentId: string;

  // UI state
  isLoading: boolean;
  isSending: boolean;
  error: string | null;
  sidebarOpen: boolean;

  // Actions
  loadAgents: () => Promise<void>;
  loadStatus: () => Promise<void>;
  setSelectedMode: (mode: OrchestrationMode) => void;
  setSelectedAgent: (agentId: string) => void;
  setSidebarOpen: (open: boolean) => void;

  // Session actions
  createSession: (title?: string) => void;
  setActiveSession: (sessionId: string) => void;
  deleteSession: (sessionId: string) => void;

  // Chat actions
  sendMessage: (content: string) => Promise<void>;

  // Helpers
  getActiveSession: () => UISession | null;
}

export const useDashboardStore = create<DashboardState>((set, get) => ({
  // Initial state
  agents: [],
  sessions: [],
  activeSessionId: null,
  systemStatus: null,
  selectedMode: 'single_agent',
  selectedAgentId: 'prince_flowers',
  isLoading: false,
  isSending: false,
  error: null,
  sidebarOpen: true,

  // Load agents from API
  loadAgents: async () => {
    try {
      set({ isLoading: true, error: null });
      const agents = await torqApi.getAgents();
      set({ agents, isLoading: false });
    } catch (err: any) {
      console.error('Failed to load agents:', err);
      // Set fallback agents for demo mode
      set({
        agents: [
          {
            id: 'prince_flowers',
            name: 'Prince Flowers',
            description: 'Enhanced conversational AI with code, task, and general chat',
            capabilities: ['general_chat', 'code_generation', 'task_planning', 'documentation'],
            status: 'active',
            metrics: {},
          },
          {
            id: 'orchestrator',
            name: 'Agent Orchestrator',
            description: 'Coordinates multiple agents for complex tasks',
            capabilities: ['multi_agent_coordination', 'workflow_orchestration', 'intelligent_routing'],
            status: 'active',
            metrics: {},
          },
          {
            id: 'query_router',
            name: 'Query Router',
            description: 'Intelligently routes queries to appropriate agents',
            capabilities: ['intent_classification', 'query_analysis', 'agent_selection'],
            status: 'active',
            metrics: {},
          },
        ],
        isLoading: false,
        error: 'Running in demo mode — backend unavailable',
      });
    }
  },

  // Load system status
  loadStatus: async () => {
    try {
      const status = await torqApi.getStatus();
      set({ systemStatus: status });
    } catch (err) {
      console.error('Failed to load status:', err);
    }
  },

  setSelectedMode: (mode) => set({ selectedMode: mode }),
  setSelectedAgent: (agentId) => set({ selectedAgentId: agentId }),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),

  // Create a new local session
  createSession: (title) => {
    const sessionId = `session-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    const newSession: UISession = {
      id: sessionId,
      title: title || `Chat ${get().sessions.length + 1}`,
      agentId: get().selectedAgentId,
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
      mode: get().selectedMode,
    };
    set((state) => ({
      sessions: [...state.sessions, newSession],
      activeSessionId: sessionId,
    }));
  },

  setActiveSession: (sessionId) => set({ activeSessionId: sessionId }),

  deleteSession: (sessionId) =>
    set((state) => {
      const filtered = state.sessions.filter((s) => s.id !== sessionId);
      return {
        sessions: filtered,
        activeSessionId:
          state.activeSessionId === sessionId
            ? filtered[0]?.id || null
            : state.activeSessionId,
      };
    }),

  // Send a message via the verified API endpoint
  sendMessage: async (content) => {
    const state = get();
    let session = state.getActiveSession();

    // Auto-create session if none exists
    if (!session) {
      get().createSession();
      session = get().getActiveSession();
      if (!session) return;
    }

    const userMsg: UIMessage = {
      id: `msg-${Date.now()}-user`,
      role: 'user',
      content,
      timestamp: Date.now(),
    };

    const loadingMsg: UIMessage = {
      id: `msg-${Date.now()}-assistant`,
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      isLoading: true,
    };

    // Add user message + loading indicator
    set((s) => ({
      isSending: true,
      sessions: s.sessions.map((sess) =>
        sess.id === session!.id
          ? {
              ...sess,
              messages: [...sess.messages, userMsg, loadingMsg],
              updatedAt: Date.now(),
              title: sess.messages.length === 0 ? content.slice(0, 40) : sess.title,
            }
          : sess
      ),
    }));

    try {
      // Call verified endpoint: POST /api/agents/{id}/chat
      const response = await torqApi.sendMessage(state.selectedAgentId, {
        message: content,
        mode: state.selectedMode,
      });

      const assistantMsg: UIMessage = {
        id: loadingMsg.id,
        role: 'assistant',
        content: response.response,
        timestamp: Date.now(),
        routing: response.metadata.routing_decision,
        metadata: response.metadata,
        isLoading: false,
      };

      // Replace loading message with real response
      set((s) => ({
        isSending: false,
        sessions: s.sessions.map((sess) =>
          sess.id === session!.id
            ? {
                ...sess,
                messages: sess.messages.map((msg) =>
                  msg.id === loadingMsg.id ? assistantMsg : msg
                ),
                updatedAt: Date.now(),
              }
            : sess
        ),
      }));
    } catch (err: any) {
      // Show error in the loading message
      const errorMsg: UIMessage = {
        id: loadingMsg.id,
        role: 'assistant',
        content: `Error: ${err.message || 'Failed to get response'}. The backend may not be running.`,
        timestamp: Date.now(),
        isLoading: false,
      };

      set((s) => ({
        isSending: false,
        error: err.message,
        sessions: s.sessions.map((sess) =>
          sess.id === session!.id
            ? {
                ...sess,
                messages: sess.messages.map((msg) =>
                  msg.id === loadingMsg.id ? errorMsg : msg
                ),
                updatedAt: Date.now(),
              }
            : sess
        ),
      }));
    }
  },

  getActiveSession: () => {
    const state = get();
    return state.sessions.find((s) => s.id === state.activeSessionId) || null;
  },
}));
