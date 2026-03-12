/**
 * Phase 2 - Chat System Integrity
 *
 * Enhanced ChatWindow with:
 * - UUID-based message IDs
 * - Message deduplication
 * - Streaming support
 * - Typing indicators
 */

import React, { useEffect, useRef, useState } from 'react';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { TypingIndicator } from './TypingIndicator';
import { StreamingIndicator } from './StreamingIndicator';
import { useChatStore, useTypingState, useCurrentSession, useStreamingMessage } from '@/stores/chatStore';
import { useAgentStore } from '@/stores/agentStore';
import {
  createUserMessage,
  createAssistantMessage,
  generateMessageId,
} from '@/types/chat';
import websocketManager from '@/services/websocket';

export const ChatWindow: React.FC = () => {
  // Get current session from new chat store
  const currentSession = useCurrentSession();
  const typingState = useTypingState();
  const streamingMessage = useStreamingMessage();

  // Legacy store for compatibility during migration
  const { sessions: legacySessions, agents, activeAgentId } = useAgentStore();

  // Use new chat store methods
  const {
    createSession,
    setCurrentSession,
    addMessage,
    startStreamingMessage,
    appendToStream,
    completeStream,
    errorStream,
    setTyping,
    setActiveAgent,
  } = useChatStore();

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [isSending, setIsSending] = useState(false);

  // Get active agent
  const activeAgent = agents.find((a) => a.id === currentSession?.agentId);
  const activeSession = currentSession || legacySessions.find((s) => s.id === activeAgentId);

  const scrollToBottom = (smooth = true) => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({
        behavior: smooth ? 'smooth' : 'instant',
      });
    }
  };

  // Auto-scroll when messages change or streaming updates
  useEffect(() => {
    scrollToBottom(true);
  }, [activeSession?.messages, streamingMessage?.content]);

  // Scroll during streaming (more frequent)
  useEffect(() => {
    if (streamingMessage?.streaming === 'streaming') {
      const timer = setInterval(() => scrollToBottom(false), 100);
      return () => clearInterval(timer);
    }
  }, [streamingMessage?.streaming]);

  /**
   * Send a message with Phase 2 improvements:
   * - UUID-based IDs
   * - No duplicates
   * - Streaming support
   */
  const handleSend = async (message: string) => {
    if (!activeSession || isSending) return;

    setIsSending(true);

    try {
      // Ensure we have a valid session ID
      const sessionId = activeSession.id;

      // Create user message with UUID (no duplicates!)
      const userMessage = createUserMessage(
        message,
        sessionId,
        activeSession.agentId
      );

      // Add to store (deduplication built-in)
      const addResult = addMessage(sessionId, userMessage);

      if (!addResult.inserted) {
        console.warn('[ChatWindow] Duplicate user message prevented');
        setIsSending(false);
        return;
      }

      // Set typing indicator
      setTyping(sessionId, true, activeSession.agentId);

      // Start streaming message for response
      const streamMsg = startStreamingMessage(
        sessionId,
        activeSession.agentId,
        'single_agent'
      );

      // Send via WebSocket/HTTP
      await websocketManager.sendMessage(
        sessionId,
        message,
        activeSession.agentId
      );

      // Note: WebSocket handler will update the streaming message
      // via appendToStream/completeStream as chunks arrive

    } catch (err: any) {
      console.error('[ChatWindow] Failed to send message:', err);

      // Show error in chat
      if (activeSession) {
        const errorMsg = createAssistantMessage(
          `⚠️ Failed to send: ${err.message || 'Unknown error'}`,
          activeSession.id,
          activeSession.agentId,
          { type: 'error' }
        );
        addMessage(activeSession.id, errorMsg);
      }

      // Clear typing on error
      if (activeSession) {
        setTyping(activeSession.id, false);
      }
    } finally {
      setIsSending(false);
    }
  };

  // Handle stopping streaming (user cancellation)
  const handleStopStreaming = () => {
    if (streamingMessage && activeSession) {
      completeStream(activeSession.id, streamingMessage.message_id);
    }
  };

  if (!activeSession) {
    return (
      <div className="flex-1 flex items-center justify-center bg-bg-primary">
        <div className="text-center">
          <div className="text-4xl mb-4">💬</div>
          <h3 className="text-h3 text-text-secondary mb-2">No Active Chat</h3>
          <p className="text-small text-text-muted">
            Select an agent from the sidebar to start chatting
          </p>
        </div>
      </div>
    );
  }

  // Convert legacy messages to new format if needed
  const displayMessages = activeSession.messages.map((msg) => {
    // Check if it's already a ChatMessage (has message_id)
    if ('message_id' in msg) {
      return msg;
    }
    // Convert legacy Message to ChatMessage display format
    return {
      message_id: msg.id,
      session_id: activeSession.id,
      role: msg.agentId === 'user' ? 'user' : 'assistant',
      agent_id: msg.agentId,
      timestamp: msg.timestamp,
      content: msg.content,
      type: msg.type,
      streaming: 'complete',
      metadata: msg.metadata,
    };
  });

  return (
    <div className="flex-1 flex flex-col bg-bg-primary">
      {/* Chat header */}
      <div className="h-14 bg-bg-secondary border-b border-border flex items-center justify-between px-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-accent-primary flex items-center justify-center text-small font-semibold">
            {activeAgent?.name.slice(0, 2).toUpperCase() || 'AG'}
          </div>
          <div>
            <h3 className="text-body font-medium">{activeAgent?.name || 'Agent'}</h3>
            <p className="text-small text-text-muted">
              {activeAgent?.capabilities.join(', ') || 'No capabilities'}
            </p>
          </div>
        </div>

        {/* Streaming status indicator */}
        {streamingMessage?.streaming === 'streaming' && (
          <button
            onClick={handleStopStreaming}
            className="px-3 py-1.5 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors"
          >
            Stop Streaming
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {displayMessages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <p className="text-text-muted text-small">
                Start a conversation with {activeAgent?.name || 'the agent'}
              </p>
            </div>
          </div>
        ) : (
          <div className="divide-y divide-border">
            {displayMessages.map((message) => (
              <ChatMessage
                key={
                  'message_id' in message
                    ? message.message_id
                    : message.id
                }
                message={message}
                agentName={activeAgent?.name || 'Agent'}
              />
            ))}

            {/* Typing indicator */}
            {typingState?.isTyping && typingState.sessionId === activeSession.id && (
              <div className="py-2">
                <TypingIndicator typingState={typingState} />
              </div>
            )}

            {/* Streaming indicator */}
            {streamingMessage?.streaming === 'streaming' && (
              <div className="py-2">
                <StreamingIndicator active={true} />
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <ChatInput
        onSend={handleSend}
        disabled={!activeAgent || isSending}
        placeholder={
          streamingMessage?.streaming === 'streaming'
            ? 'Streaming response...'
            : undefined
        }
      />
    </div>
  );
};

export default ChatWindow;
