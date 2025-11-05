import { create } from 'zustand';
import { Agent, ChatSession, Message, Workspace } from '@/lib/types';
import websocketManager from '@/services/websocket';
import apiService from '@/services/api';
import agentService from '@/services/agentService';

interface AgentState {
  // State
  agents: Agent[];
  activeAgentId: string | null;
  sessions: ChatSession[];
  activeSessionId: string | null;
  workspace: Workspace | null;
  isConnected: boolean;

  // Actions
  setAgents: (agents: Agent[]) => void;
  setActiveAgent: (agentId: string | null) => void;
  updateAgentStatus: (agentId: string, status: Agent['status']) => void;

  addSession: (session: ChatSession) => void;
  setActiveSession: (sessionId: string | null) => void;
  addMessage: (sessionId: string, message: Message) => void;
  updateMessage: (sessionId: string, messageId: string, updates: Partial<Message>) => void;

  setWorkspace: (workspace: Workspace | null) => void;
  setConnectionStatus: (isConnected: boolean) => void;

  // WebSocket actions
  initializeWebSocket: () => void;
  disconnectWebSocket: () => void;

  // Data loading actions
  loadAgents: () => Promise<void>;
  loadSessions: () => Promise<void>;
}

export const useAgentStore = create<AgentState>((set, get) => ({
  // Initial state
  agents: [],
  activeAgentId: null,
  sessions: [],
  activeSessionId: null,
  workspace: null,
  isConnected: false,

  // Actions
  setAgents: (agents) => set({ agents }),

  setActiveAgent: (agentId) => set({ activeAgentId: agentId }),

  updateAgentStatus: (agentId, status) =>
    set((state) => ({
      agents: state.agents.map((agent) =>
        agent.id === agentId ? { ...agent, status } : agent
      ),
    })),

  addSession: (session) =>
    set((state) => ({
      sessions: [...state.sessions, session],
    })),

  setActiveSession: (sessionId) => set({ activeSessionId: sessionId }),

  addMessage: (sessionId, message) =>
    set((state) => ({
      sessions: state.sessions.map((session) =>
        session.id === sessionId
          ? {
              ...session,
              messages: [...session.messages, message],
              updatedAt: Date.now(),
            }
          : session
      ),
    })),

  updateMessage: (sessionId, messageId, updates) =>
    set((state) => ({
      sessions: state.sessions.map((session) =>
        session.id === sessionId
          ? {
              ...session,
              messages: session.messages.map((msg) =>
                msg.id === messageId ? { ...msg, ...updates } : msg
              ),
              updatedAt: Date.now(),
            }
          : session
      ),
    })),

  setWorkspace: (workspace) => set({ workspace }),

  setConnectionStatus: (isConnected) => set({ isConnected }),

  // WebSocket initialization
  initializeWebSocket: () => {
    // Setup event handlers
    websocketManager.on('onConnect', () => {
      console.log('WebSocket connected - updating store');
      set({ isConnected: true });

      // Load initial data on connection
      get().loadAgents();
      get().loadSessions();
    });

    websocketManager.on('onDisconnect', () => {
      console.log('WebSocket disconnected - updating store');
      set({ isConnected: false });
    });

    websocketManager.on('onError', (error) => {
      console.error('WebSocket error in store:', error);
      set({ isConnected: false });
    });

    websocketManager.on('onAgentStatus', (agent) => {
      console.log('Agent status update received:', agent);
      set((state) => ({
        agents: state.agents.map((a) =>
          a.id === agent.id ? { ...a, ...agent } : a
        ),
      }));
    });

    websocketManager.on('onAgentResponse', (data) => {
      console.log('Agent response received:', data);
      const { sessionId, message } = data;

      set((state) => ({
        sessions: state.sessions.map((session) =>
          session.id === sessionId
            ? {
                ...session,
                messages: [...session.messages, message],
                updatedAt: Date.now(),
              }
            : session
        ),
      }));
    });

    websocketManager.on('onSessionCreated', (data) => {
      console.log('Session created:', data);
      const { sessionId, agentId } = data;

      // Create new session object
      const newSession: ChatSession = {
        id: sessionId,
        title: 'New Session',
        agentId,
        messages: [],
        createdAt: Date.now(),
        updatedAt: Date.now(),
      };

      set((state) => ({
        sessions: [...state.sessions, newSession],
        activeSessionId: sessionId,
      }));
    });

    websocketManager.on('onMessage', (message) => {
      console.log('Message received:', message);

      // Find the session for this message
      const state = get();
      const session = state.sessions.find((s) =>
        s.messages.some((m) => m.id === message.id)
      );

      if (session) {
        get().addMessage(session.id, message);
      }
    });

    // Connect to WebSocket
    websocketManager.connect();
  },

  // WebSocket disconnection
  disconnectWebSocket: () => {
    websocketManager.off('onConnect');
    websocketManager.off('onDisconnect');
    websocketManager.off('onError');
    websocketManager.off('onAgentStatus');
    websocketManager.off('onAgentResponse');
    websocketManager.off('onSessionCreated');
    websocketManager.off('onMessage');

    websocketManager.disconnect();
    set({ isConnected: false });
  },

  // Load agents from API
  loadAgents: async () => {
    try {
      const agents = await agentService.getAllAgents();
      set({ agents });
    } catch (error) {
      console.error('Failed to load agents:', error);
    }
  },

  // Load sessions from API
  loadSessions: async () => {
    try {
      const sessions = await apiService.getSessions();
      set({ sessions });
    } catch (error) {
      console.error('Failed to load sessions:', error);
    }
  },
}));

// Initialize WebSocket on store creation
if (typeof window !== 'undefined') {
  // Only initialize in browser environment
  const store = useAgentStore.getState();
  store.initializeWebSocket();
}
