/**
 * Phase 2 - Chat System Integrity Tests
 *
 * Tests for:
 * - UUID-based message IDs
 * - Message deduplication
 * - Streaming response support
 * - Session persistence
 * - Duplicate prevention
 *
 * Run with: npm run test:phase2
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useChatStore } from '@/stores/chatStore';
import {
  generateMessageId,
  generateSessionId,
  legacyToChatMessage,
} from '@/types/chat';
import {
  createUserMessage,
  createAssistantMessage,
  insertMessageIfMissing,
  hasMessage,
  findMessageById,
} from '@/utils/messageUtils';

describe('Phase 2: Chat System Integrity', () => {
  let store: ReturnType<typeof useChatStore>;

  beforeEach(() => {
    // Reset store before each test
    const { result } = renderHook(() => useChatStore());

    // Clear all sessions
    const sessions = result.current.listSessions();
    sessions.forEach((session) => {
      act(() => {
        result.current.deleteSession(session.id);
      });
    });

    // Store reference for tests
    store = result.current;
  });

  describe('UUID-based Message IDs', () => {
    it('should generate unique message IDs', () => {
      const id1 = generateMessageId();
      const id2 = generateMessageId();

      expect(id1).not.toBe(id2);
      expect(id1).toMatch(/^msg_[a-f0-9-]+$/);
      expect(id2).toMatch(/^msg_[a-f0-9-]+$/);
    });

    it('should generate unique session IDs', () => {
      const id1 = generateSessionId();
      const id2 = generateSessionId();

      expect(id1).not.toBe(id2);
      expect(id1).toMatch(/^session_[a-f0-9-]+$/);
    });

    it('should create user message with UUID', () => {
      const msg = createUserMessage('test', 'session-1', 'agent-1');

      expect(msg.message_id).toMatch(/^msg_[a-f0-9-]+$/);
      expect(msg.content).toBe('test');
      expect(msg.role).toBe('user');
      expect(msg.session_id).toBe('session-1');
    });

    it('should create assistant message with UUID', () => {
      const msg = createAssistantMessage('response', 'session-1', 'agent-1');

      expect(msg.message_id).toMatch(/^msg_[a-f0-9-]+$/);
      expect(msg.content).toBe('response');
      expect(msg.role).toBe('assistant');
    });
  });

  describe('Message Deduplication', () => {
    it('should prevent duplicate messages with same ID', () => {
      let session: ReturnType<typeof store.createSession>;

      act(() => {
        session = store.createSession('agent-1');
      });

      const msg = createUserMessage('test message', session.id, 'agent-1');

      // First insert should succeed
      let addResult: ReturnType<typeof store.addMessage>;
      act(() => {
        addResult = store.addMessage(session.id, msg);
      });

      expect(addResult.inserted).toBe(true);
      expect(addResult.reason).toBe('success');

      // Second insert with same ID should fail
      act(() => {
        addResult = store.addMessage(session.id, msg);
      });

      expect(addResult.inserted).toBe(false);
      expect(addResult.reason).toBe('duplicate');
    });

    it('should allow different messages with different IDs', () => {
      let session: ReturnType<typeof store.createSession>;

      act(() => {
        session = store.createSession('agent-1');
      });

      const msg1 = createUserMessage('message 1', session.id, 'agent-1');
      const msg2 = createUserMessage('message 2', session.id, 'agent-1');

      let result1: ReturnType<typeof store.addMessage>;
      let result2: ReturnType<typeof store.addMessage>;

      act(() => {
        result1 = store.addMessage(session.id, msg1);
        result2 = store.addMessage(session.id, msg2);
      });

      expect(result1.inserted).toBe(true);
      expect(result2.inserted).toBe(true);
    });

    it('should handle rapid message sends without duplicates', () => {
      let session: ReturnType<typeof store.createSession>;

      act(() => {
        session = store.createSession('agent-1');
      });

      // Simulate rapid sends (same timestamp, different UUIDs)
      const messages = Array.from({ length: 10 }, (_, i) =>
        createUserMessage(`Message ${i}`, session.id, 'agent-1')
      );

      // Add all messages rapidly
      const results: ReturnType<typeof store.addMessage>[] = [];

      act(() => {
        messages.forEach((msg) => {
          results.push(store.addMessage(session.id, msg));
        });
      });

      // All should be inserted (no duplicates)
      results.forEach((result) => {
        expect(result.inserted).toBe(true);
      });

      // Verify all messages are in session
      const updatedSession = store.getSession(session.id);
      expect(updatedSession?.messages.length).toBe(10);
    });
  });

  describe('Streaming Response Support', () => {
    it('should create streaming message placeholder', () => {
      let session: ReturnType<typeof store.createSession>;
      let streamMsg: ReturnType<typeof store.startStreamingMessage>;

      act(() => {
        session = store.createSession('agent-1');
        streamMsg = store.startStreamingMessage(session.id, 'agent-1', 'single_agent');
      });

      expect(streamMsg.message_id).toMatch(/^msg_[a-f0-9-]+$/);
      expect(streamMsg.streaming).toBe('streaming');
      expect(streamMsg.content).toBe('');
    });

    it('should append content to streaming message', () => {
      let session: ReturnType<typeof store.createSession>;
      let streamMsg: ReturnType<typeof store.startStreamingMessage>;

      act(() => {
        session = store.createSession('agent-1');
        streamMsg = store.startStreamingMessage(session.id, 'agent-1');
        store.appendToStream(session.id, streamMsg.message_id, 'Hello ');
        store.appendToStream(session.id, streamMsg.message_id, 'World');
      });

      const updated = store.getSession(session.id);
      const updatedMsg = updated?.messages.find(
        (m) => m.message_id === streamMsg.message_id
      );

      expect(updatedMsg?.content).toBe('Hello World');
    });

    it('should complete streaming message', () => {
      let session: ReturnType<typeof store.createSession>;
      let streamMsg: ReturnType<typeof store.startStreamingMessage>;

      act(() => {
        session = store.createSession('agent-1');
        streamMsg = store.startStreamingMessage(session.id, 'agent-1');
        store.appendToStream(session.id, streamMsg.message_id, 'Streaming');
        store.completeStream(session.id, streamMsg.message_id);
      });

      const updated = store.getSession(session.id);
      const completedMsg = updated?.messages.find(
        (m) => m.message_id === streamMsg.message_id
      );

      expect(completedMsg?.streaming).toBe('complete');
      expect(completedMsg?.content).toBe('Streaming');
    });

    it('should handle streaming errors', () => {
      let session: ReturnType<typeof store.createSession>;
      let streamMsg: ReturnType<typeof store.startStreamingMessage>;

      act(() => {
        session = store.createSession('agent-1');
        streamMsg = store.startStreamingMessage(session.id, 'agent-1');
        store.errorStream(session.id, streamMsg.message_id, 'Connection lost');
      });

      const updated = store.getSession(session.id);
      const erroredMsg = updated?.messages.find(
        (m) => m.message_id === streamMsg.message_id
      );

      expect(erroredMsg?.streaming).toBe('error');
      expect(erroredMsg?.content).toContain('Connection lost');
      expect(erroredMsg?.type).toBe('error');
    });
  });

  describe('Session Persistence', () => {
    it('should persist session across operations', () => {
      let session: ReturnType<typeof store.createSession>;

      act(() => {
        session = store.createSession('agent-1');
      });

      // Add a message
      const msg = createUserMessage('test', session.id, 'agent-1');
      act(() => {
        store.addMessage(session.id, msg);
      });

      // Session should still exist
      const retrieved = store.getSession(session.id);
      expect(retrieved).toBeDefined();
      expect(retrieved?.messages.length).toBe(1);
    });

    it('should maintain session continuity over multiple turns', () => {
      let session: ReturnType<typeof store.createSession>;

      act(() => {
        session = store.createSession('agent-1');
      });

      // Multiple conversation turns
      act(() => {
        store.addMessage(
          session.id,
          createUserMessage('Hello', session.id, 'agent-1')
        );
        store.addMessage(
          session.id,
          createAssistantMessage('Hi there!', session.id, 'agent-1')
        );
        store.addMessage(
          session.id,
          createUserMessage('How are you?', session.id, 'agent-1')
        );
        store.addMessage(
          session.id,
          createAssistantMessage('Doing great!', session.id, 'agent-1')
        );
      });

      const retrieved = store.getSession(session.id);
      expect(retrieved?.messages.length).toBe(4);
    });
  });

  describe('Typing Indicator', () => {
    it('should set typing state', () => {
      let session: ReturnType<typeof store.createSession>;

      act(() => {
        session = store.createSession('agent-1');
        store.setTyping(session.id, true, 'agent-1');
      });

      // Check session has typing state
      expect(store.getSession(session.id)?.isTyping).toBe(true);
    });

    it('should clear typing state when set to false', () => {
      let session: ReturnType<typeof store.createSession>;

      act(() => {
        session = store.createSession('agent-1');
        store.setTyping(session.id, true);
        store.setTyping(session.id, false);
      });

      expect(store.getSession(session.id)?.isTyping).toBe(false);
    });
  });

  describe('Legacy Compatibility', () => {
    it('should convert legacy messages to new format', () => {
      const legacyMsg = {
        id: 'msg_123',
        agentId: 'agent-1',
        type: 'text' as const,
        content: 'Legacy message',
        timestamp: Date.now(),
      };

      const converted = legacyToChatMessage(legacyMsg, 'session-1');

      expect(converted.message_id).toBe('msg_123');
      expect(converted.session_id).toBe('session-1');
      expect(converted.role).toBe('assistant');
      expect(converted.streaming).toBe('complete');
    });

    it('should handle legacy message insertion', () => {
      let session: ReturnType<typeof store.createSession>;

      act(() => {
        session = store.createSession('agent-1');
      });

      const legacyMsg = {
        id: 'msg_legacy',
        agentId: 'agent-1',
        type: 'text' as const,
        content: 'Legacy message',
        timestamp: Date.now(),
      };

      let insertResult: ReturnType<typeof store.legacyAddMessage>;

      act(() => {
        insertResult = store.legacyAddMessage(session.id, legacyMsg);
      });

      expect(insertResult.inserted).toBe(true);

      const retrieved = store.getSession(session.id);
      expect(retrieved?.messages.length).toBe(1);
    });
  });

  describe('Message Utility Functions', () => {
    it('should detect existing messages by ID', () => {
      const msg1 = createUserMessage('test1', 'session-1', 'agent-1');
      const msg2 = createUserMessage('test2', 'session-1', 'agent-1');

      expect(hasMessage([msg1], msg1)).toBe(true);
      expect(hasMessage([msg1], msg2)).toBe(false);
    });

    it('should find message by ID', () => {
      const msg = createUserMessage('test', 'session-1', 'agent-1');

      expect(findMessageById([msg], msg.message_id)).toBe(msg);
      expect(findMessageById([msg], 'nonexistent')).toBeUndefined();
    });

    it('should insert message if missing', () => {
      const msg = createUserMessage('test', 'session-1', 'agent-1');

      const result = insertMessageIfMissing([], msg);
      expect(result.inserted).toBe(true);
      expect(result.reason).toBe('success');
    });

    it('should not insert duplicate message', () => {
      const msg = createUserMessage('test', 'session-1', 'agent-1');

      const result1 = insertMessageIfMissing([], msg);
      const result2 = insertMessageIfMissing([msg], msg);

      expect(result1.inserted).toBe(true);
      expect(result2.inserted).toBe(false);
      expect(result2.reason).toBe('duplicate');
    });
  });

  describe('Multiple Agent Routing', () => {
    it('should handle switching between agents in same session', () => {
      let session: ReturnType<typeof store.createSession>;

      act(() => {
        session = store.createSession('agent-1');
        // Send message with agent-1
        store.addMessage(
          session.id,
          createAssistantMessage('Response from agent 1', session.id, 'agent-1')
        );
        // Switch agent
        store.addMessage(
          session.id,
          createAssistantMessage('Response from agent 2', session.id, 'agent-2')
        );
      });

      const retrieved = store.getSession(session.id);
      expect(retrieved?.messages.length).toBe(2);
    });
  });

  describe('Duplicate Prevention Tests', () => {
    it('should prevent duplicates when WebSocket and local both add same message', () => {
      let session: ReturnType<typeof store.createSession>;

      act(() => {
        session = store.createSession('agent-1');
      });

      // Simulate optimistic local insert
      const msg = createUserMessage('test', session.id, 'agent-1');

      let localResult: ReturnType<typeof store.addMessage>;
      let wsResult: ReturnType<typeof store.addMessage>;

      act(() => {
        localResult = store.addMessage(session.id, msg);
        // Simulate WebSocket delivery (same message)
        wsResult = store.addMessage(session.id, msg);
      });

      expect(localResult.inserted).toBe(true);
      expect(wsResult.inserted).toBe(false);
      expect(wsResult.reason).toBe('duplicate');

      // Should only have one message
      const retrieved = store.getSession(session.id);
      expect(retrieved?.messages.length).toBe(1);
    });
  });

  describe('Session Management', () => {
    it('should create and list sessions', () => {
      let session1: ReturnType<typeof store.createSession>;
      let session2: ReturnType<typeof store.createSession>;

      act(() => {
        session1 = store.createSession('agent-1');
        session2 = store.createSession('agent-2');
      });

      const sessions = store.listSessions();
      expect(sessions.length).toBeGreaterThanOrEqual(2);
    });

    it('should delete sessions', () => {
      let session: ReturnType<typeof store.createSession>;

      act(() => {
        session = store.createSession('agent-1');
        store.deleteSession(session.id);
      });

      const deleted = store.getSession(session.id);
      expect(deleted).toBeUndefined();
    });

    it('should set current session', () => {
      let session: ReturnType<typeof store.createSession>;

      act(() => {
        session = store.createSession('agent-1');
        store.setCurrentSession(session.id);
      });

      // Use getState() to read current state
      expect(useChatStore.getState().currentSessionId).toBe(session.id);
    });
  });

  describe('Connection Status', () => {
    it('should update connection status', () => {
      act(() => {
        store.setConnectionStatus(true);
      });

      expect(useChatStore.getState().isConnected).toBe(true);

      act(() => {
        store.setConnectionStatus(false);
      });

      expect(useChatStore.getState().isConnected).toBe(false);
    });
  });
});
