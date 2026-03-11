/**
 * Phase 2 - Chat System Integrity
 *
 * Enhanced chat store with:
 * - UUID-based message IDs (no duplicates)
 * - Message deduplication
 * - Streaming response support
 * - Typing indicators
 * - Session persistence
 */

import { create } from 'zustand';
import type { Agent, ChatSession, Message } from '@/lib/types';
import type {
  ChatMessage,
  TypingState,
  MessageInsertResult,
} from '@/types/chat';
import type {
  MessageRole,
  MessageType,
  StreamingStatus,
} from '@/types/chat';
import {
  generateMessageId,
  generateSessionId,
  legacyToChatMessage,
  chatToLegacyMessage,
} from '@/types/chat';
import {
  insertMessageIfMissing,
  insertMessagesIfMissing,
  createUserMessage,
  createAssistantMessage,
  createStreamingMessage,
  updateStreamingMessage,
  completeStreamingMessage,
  errorStreamingMessage,
  createSystemMessage,
  sortMessagesByTimestamp,
} from '@/utils/messageUtils';

/**
 * Extended state with typing indicator and streaming support
 */
interface ChatState {
  // Sessions with new chat schema
  chatSessions: Map<string, ChatSession>;

  // Current session ID
  currentSessionId: string | null;

  // Typing state
  typingState: TypingState | null;

  // Connection status
  isConnected: boolean;

  // Agents
  agents: Agent[];
  activeAgentId: string | null;

  // Legacy support (can be removed after migration)
  sessions: ChatSession[];
}

interface ChatActions {
  // Session management
  createSession: (agentId: string) => ChatSession;
  getSession: (sessionId: string) => ChatSession | undefined;
  setCurrentSession: (sessionId: string | null) => void;
  deleteSession: (sessionId: string) => void;
  listSessions: () => ChatSession[];

  // Message operations with deduplication
  addMessage: (sessionId: string, message: ChatMessage) => MessageInsertResult;
  addMessages: (sessionId: string, messages: ChatMessage[]) => MessageInsertResult[];
  updateMessage: (
    sessionId: string,
    messageId: string,
    updates: Partial<ChatMessage>
  ) => boolean;

  // Streaming operations
  startStreamingMessage: (
    sessionId: string,
    agentId: string,
    mode?: string
  ) => ChatMessage;
  appendToStream: (
    sessionId: string,
    messageId: string,
    content: string
  ) => void;
  completeStream: (
    sessionId: string,
    messageId: string,
    finalContent?: string
  ) => void;
  errorStream: (
    sessionId: string,
    messageId: string,
    error: string
  ) => void;

  // Typing indicator
  setTyping: (sessionId: string, isTyping: boolean, agentId?: string) => void;

  // Legacy compatibility
  legacyAddMessage: (sessionId: string, message: Message) => MessageInsertResult;

  // Connection
  setConnectionStatus: (isConnected: boolean) => void;

  // Agents
  setAgents: (agents: Agent[]) => void;
  setActiveAgent: (agentId: string) => void;
}

/**
 * Chat Store with Phase 2 Improvements
 */
export const useChatStore = create<ChatState & ChatActions>((set, get) => ({
  // Initial state
  chatSessions: new Map(),
  currentSessionId: null,
  typingState: null,
  isConnected: false,
  agents: [],
  activeAgentId: null,
  sessions: [], // Legacy support

  // ========================================================================
  // Session Management
  // ========================================================================

  createSession: (agentId: string) => {
    const sessionId = generateSessionId();
    const agent = get().agents.find((a) => a.id === agentId);

    const newSession: ChatSession = {
      id: sessionId,
      title: agent ? `Chat with ${agent.name}` : 'New Chat',
      agentId,
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
      isTyping: false,
      streamingMessageId: null,
    };

    set((state) => {
      const newSessions = new Map(state.chatSessions);
      newSessions.set(sessionId, newSession);
      return {
        chatSessions: newSessions,
        currentSessionId: sessionId,
        sessions: Array.from(newSessions.values()), // Legacy sync
      };
    });

    return newSession;
  },

  getSession: (sessionId: string) => {
    return get().chatSessions.get(sessionId);
  },

  setCurrentSession: (sessionId: string | null) => {
    set({ currentSessionId: sessionId });
  },

  deleteSession: (sessionId: string) => {
    set((state) => {
      const newSessions = new Map(state.chatSessions);
      newSessions.delete(sessionId);

      // Clear typing state if it was for this session
      const typing = state.typingState;
      if (typing && state.currentSessionId === sessionId) {
        return {
          chatSessions: newSessions,
          typingState: null,
          currentSessionId:
            state.currentSessionId === sessionId ? null : state.currentSessionId,
          sessions: Array.from(newSessions.values()),
        };
      }

      return {
        chatSessions: newSessions,
        currentSessionId:
          state.currentSessionId === sessionId ? null : state.currentSessionId,
        sessions: Array.from(newSessions.values()),
      };
    });
  },

  listSessions: () => {
    return Array.from(get().chatSessions.values());
  },

  // ========================================================================
  // Message Operations with Deduplication
  // ========================================================================

  addMessage: (sessionId: string, message: ChatMessage) => {
    const session = get().chatSessions.get(sessionId);
    if (!session) {
      return {
        inserted: false,
        message: null,
        reason: 'invalid',
      };
    }

    // Use deduplication utility
    const result = insertMessageIfMissing(session.messages, message);

    if (result.inserted && result.message) {
      const newMessages = [...session.messages, result.message];
      const updatedSession: ChatSession = {
        ...session,
        messages: sortMessagesByTimestamp(newMessages),
        updatedAt: Date.now(),
      };

      set((state) => {
        const newSessions = new Map(state.chatSessions);
        newSessions.set(sessionId, updatedSession);
        return {
          chatSessions: newSessions,
          sessions: Array.from(newSessions.values()),
        };
      });
    }

    return result;
  },

  addMessages: (sessionId: string, messages: ChatMessage[]) => {
    const session = get().chatSessions.get(sessionId);
    if (!session) {
      return messages.map(() => ({
        inserted: false,
        message: null,
        reason: 'invalid' as const,
      }));
    }

    const newMessages = insertMessagesIfMissing(session.messages, messages);
    const updatedSession: ChatSession = {
      ...session,
      messages: sortMessagesByTimestamp(newMessages),
      updatedAt: Date.now(),
    };

    set((state) => {
      const newSessions = new Map(state.chatSessions);
      newSessions.set(sessionId, updatedSession);
      return {
        chatSessions: newSessions,
        sessions: Array.from(newSessions.values()),
      };
    });

    // Return results for each message
    return messages.map((msg) => {
      const wasInserted = !session.messages.some(
        (m) => m.message_id === msg.message_id
      );
      return {
        inserted: wasInserted,
        message: msg,
        reason: wasInserted ? ('success' as const) : ('duplicate' as const),
      };
    });
  },

  updateMessage: (
    sessionId: string,
    messageId: string,
    updates: Partial<ChatMessage>
  ) => {
    const session = get().chatSessions.get(sessionId);
    if (!session) {
      return false;
    }

    const messageIndex = session.messages.findIndex(
      (m) => m.message_id === messageId
    );

    if (messageIndex === -1) {
      return false;
    }

    const updatedMessages = [...session.messages];
    updatedMessages[messageIndex] = {
      ...updatedMessages[messageIndex],
      ...updates,
    };

    const updatedSession: ChatSession = {
      ...session,
      messages: updatedMessages,
      updatedAt: Date.now(),
    };

    set((state) => {
      const newSessions = new Map(state.chatSessions);
      newSessions.set(sessionId, updatedSession);
      return {
        chatSessions: newSessions,
        sessions: Array.from(newSessions.values()),
      };
    });

    return true;
  },

  // ========================================================================
  // Streaming Operations
  // ========================================================================

  startStreamingMessage: (
    sessionId: string,
    agentId: string,
    mode?: string
  ) => {
    const streamingMsg = createStreamingMessage(sessionId, agentId, { mode });

    const result = get().addMessage(sessionId, streamingMsg);

    if (result.inserted) {
      // Set typing state
      set({
        typingState: {
          isTyping: true,
          agentId,
          agentName: get().agents.find((a) => a.id === agentId)?.name || 'Agent',
          startedAt: Date.now(),
        },
      });

      // Update session
      set((state) => {
        const session = state.chatSessions.get(sessionId);
        if (session) {
          const updated: ChatSession = {
            ...session,
            streamingMessageId: streamingMsg.message_id,
          };
          const newSessions = new Map(state.chatSessions);
          newSessions.set(sessionId, updated);
          return {
            chatSessions: newSessions,
            sessions: Array.from(newSessions.values()),
          };
        }
      });
    }

    return streamingMsg;
  },

  appendToStream: (sessionId: string, messageId: string, content: string) => {
    const session = get().chatSessions.get(sessionId);
    if (!session) {
      return;
    }

    const messageIndex = session.messages.findIndex(
      (m) => m.message_id === messageId
    );

    if (messageIndex === -1) {
      return;
    }

    const currentMessage = session.messages[messageIndex];
    const updatedMessage = updateStreamingMessage(currentMessage, content);

    get().updateMessage(sessionId, messageId, {
      content: updatedMessage.content,
      timestamp: updatedMessage.timestamp,
    });
  },

  completeStream: (sessionId: string, messageId: string, finalContent?: string) => {
    const session = get().chatSessions.get(sessionId);
    if (!session) {
      return;
    }

    const messageIndex = session.messages.findIndex(
      (m) => m.message_id === messageId
    );

    if (messageIndex === -1) {
      return;
    }

    const currentMessage = session.messages[messageIndex];
    const completedMessage = completeStreamingMessage(
      currentMessage,
      finalContent
    );

    get().updateMessage(sessionId, messageId, {
      content: completedMessage.content,
      streaming: completedMessage.streaming,
      timestamp: completedMessage.timestamp,
    });

    // Clear typing state
    set({
      typingState: null,
    });

    // Update session
    set((state) => {
      const session = state.chatSessions.get(sessionId);
      if (session) {
        const updated: ChatSession = {
          ...session,
          streamingMessageId: null,
        };
        const newSessions = new Map(state.chatSessions);
        newSessions.set(sessionId, updated);
        return {
          chatSessions: newSessions,
          sessions: Array.from(newSessions.values()),
        };
      }
    });
  },

  errorStream: (sessionId: string, messageId: string, error: string) => {
    const session = get().chatSessions.get(sessionId);
    if (!session) {
      return;
    }

    const messageIndex = session.messages.findIndex(
      (m) => m.message_id === messageId
    );

    if (messageIndex === -1) {
      return;
    }

    const currentMessage = session.messages[messageIndex];
    const erroredMessage = errorStreamingMessage(currentMessage, error);

    get().updateMessage(sessionId, messageId, {
      content: erroredMessage.content,
      type: erroredMessage.type,
      streaming: erroredMessage.streaming,
    });

    // Clear typing state
    set({
      typingState: null,
    });

    // Update session
    set((state) => {
      const session = state.chatSessions.get(sessionId);
      if (session) {
        const updated: ChatSession = {
          ...session,
          streamingMessageId: null,
        };
        const newSessions = new Map(state.chatSessions);
        newSessions.set(sessionId, updated);
        return {
          chatSessions: newSessions,
          sessions: Array.from(newSessions.values()),
        };
      }
    });
  },

  // ========================================================================
  // Typing Indicator
  // ========================================================================

  setTyping: (sessionId: string, isTyping: boolean, agentId?: string) => {
    if (isTyping) {
      const agent = get().agents.find((a) => a.id === agentId);
      set({
        typingState: {
          isTyping: true,
          agentId: agentId || null,
          agentName: agent?.name || 'Agent',
          startedAt: Date.now(),
        },
      });
    } else {
      set({ typingState: null });
    }

    // Also update session isTyping flag
    set((state) => {
      const session = state.chatSessions.get(sessionId);
      if (session) {
        const updated: ChatSession = {
          ...session,
          isTyping,
        };
        const newSessions = new Map(state.chatSessions);
        newSessions.set(sessionId, updated);
        return {
          chatSessions: newSessions,
          sessions: Array.from(newSessions.values()),
        };
      }
    });
  },

  // ========================================================================
  // Legacy Compatibility
  // ========================================================================

  legacyAddMessage: (sessionId: string, message: Message) => {
    // Convert to ChatMessage and use new addMessage
    const chatMessage = legacyToChatMessage(message, sessionId);

    // Ensure message has valid UUID
    if (!isValidMessageId(chatMessage.message_id)) {
      chatMessage.message_id = generateMessageId();
    }

    return get().addMessage(sessionId, chatMessage);
  },

  // ========================================================================
  // Connection & Agents
  // ========================================================================

  setConnectionStatus: (isConnected: boolean) => {
    set({ isConnected });
  },

  setAgents: (agents: Agent[]) => {
    set({ agents });
  },

  setActiveAgent: (agentId: string) => {
    set({ activeAgentId: agentId });

    // Create or switch to session for this agent
    const state = get();
    let session = Array.from(state.chatSessions.values()).find(
      (s) => s.agentId === agentId
    );

    if (!session) {
      session = get().createSession(agentId);
    }

    set({ currentSessionId: session.id });
  },
}));

// Helper to check message ID validity
function isValidMessageId(id: string): boolean {
  return id.startsWith('msg_') && id.length > 10;
}

/**
 * Hook to get current session with typing state
 */
export function useCurrentSession() {
  const currentSessionId = useChatStore((state) => state.currentSessionId);
  const chatSessions = useChatStore((state) => state.chatSessions);

  return currentSessionId ? chatSessions.get(currentSessionId) : undefined;
}

/**
 * Hook to get typing state
 */
export function useTypingState() {
  return useChatStore((state) => state.typingState);
}

/**
 * Hook to get streaming message
 */
export function useStreamingMessage() {
  const currentSessionId = useChatStore((state) => state.currentSessionId);
  const chatSessions = useChatStore((state) => state.chatSessions);

  const session = currentSessionId
    ? chatSessions.get(currentSessionId)
    : undefined;

  return session?.streamingMessageId
    ? session.messages.find((m) => m.message_id === session.streamingMessageId)
    : undefined;
}

export default useChatStore;
