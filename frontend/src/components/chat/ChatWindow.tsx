import React, { useCallback, useEffect, useRef, useState } from 'react';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { TypingIndicator } from './TypingIndicator';
import { ChatEmptyState } from '@/components/empty-states';
import { StandaloneModeBadge } from './StandaloneModeBadge';
import { useAgentStore } from '@/stores/agentStore';
import { useChatStore, useTypingState } from '@/stores/chatStore';
import { useStandaloneMode } from '@/hooks/useStandaloneMode';
import { createUserMessage } from '@/utils/messageUtils';
import { chatStreamingService } from '@/services/chatStreaming';
import websocketManager from '@/services/websocket';

export const ChatWindow: React.FC = () => {
  // ALL hooks must be declared before any conditional returns
  const agentStore = useAgentStore();
  const chatStore = useChatStore();
  const [isFirstMessage, setIsFirstMessage] = useState(true);
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null);
  const typingState = useTypingState();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { isStandalone } = useStandaloneMode();

  // Guard against undefined store (AFTER all hooks)
  if (!chatStore) {
    return (
      <div className="flex-1 flex items-center justify-center bg-bg-primary">
        <div className="text-center">
          <div className="text-4xl mb-4">⚠️</div>
          <h3 className="text-h3 text-text-secondary mb-2">Chat Store Unavailable</h3>
          <p className="text-small text-text-muted">
            The chat store is not initialized. Please refresh the page.
          </p>
        </div>
      </div>
    );
  }

  // Destructure after guard check
  const {
    sessions,
    activeSessionId,
    agents,
    addMessage: agentStoreAddMessage,
    updateMessage: agentStoreUpdateMessage,
  } = agentStore;

  const {
    addMessage: chatStoreAddMessage,
    appendToStream,
    completeStream,
    setTyping,
  } = chatStore;

  const activeSession = sessions.find((s) => s.id === activeSessionId);
  const activeAgent = agents.find((a) => a.id === activeSession?.agentId);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [activeSession?.messages, streamingMessageId]);

  /**
   * Phase 4.1: Send message with streaming
   *
   * Flow:
   * 1. Add user message immediately
   * 2. Create placeholder assistant message
   * 3. Stream tokens into placeholder
   * 4. On error, fall back to WebSocket/non-streaming
   */
  const handleSend = useCallback(async (message: string) => {
    if (!activeSessionId) return;

    // Update first message state
    if (isFirstMessage) {
      setIsFirstMessage(false);
    }

    // Add user message
    const userMessage = createUserMessage(
      message,
      activeSessionId,
      activeSession?.agentId || ''
    );

    chatStoreAddMessage(activeSessionId, userMessage);
    agentStoreAddMessage(activeSessionId, {
      id: userMessage.message_id,
      agentId: userMessage.agent_id,
      type: 'text' as const,
      content: userMessage.content,
      timestamp: userMessage.timestamp,
    });

    // Create assistant message placeholder for streaming
    // We'll let the streaming service generate the ID and use that
    let streamingMessageId: string | null = null;

    // Try streaming first, fall back to WebSocket
    try {
      await chatStreamingService.sendMessage(
        {
          message,
          session_id: activeSessionId,
          agent_id: activeSession?.agentId || undefined,
        },
        {
          onStart: (messageId) => {
            // Store the message ID from streaming service
            streamingMessageId = messageId;

            // Add empty assistant message placeholder using the service's ID
            chatStoreAddMessage(activeSessionId, {
              message_id: messageId,
              session_id: activeSessionId,
              agent_id: activeSession?.agentId || 'prince_flowers',
              role: 'assistant',
              content: '',
              timestamp: Date.now(),
              streaming: true,
            } as any);

            agentStoreAddMessage(activeSessionId, {
              id: messageId,
              agentId: activeSession?.agentId || 'prince_flowers',
              type: 'text' as const,
              content: '',
              timestamp: Date.now(),
              isStreaming: true,
            });

            setStreamingMessageId(messageId);
          },
          onToken: (token, messageId) => {
            // Append token to message using the service's ID
            if (streamingMessageId !== messageId) {
              streamingMessageId = messageId;
            }
            appendToStream(activeSessionId, messageId, token);
            agentStoreUpdateMessage(activeSessionId, messageId, {
              content: (agentStore.sessions.find(s => s.id === activeSessionId)?.messages.find(m => m.id === messageId)?.content || '') + token,
            });
          },
          onComplete: (result) => {
            // Finalize the message using the service's ID
            const finalMessageId = result.messageId || streamingMessageId;
            if (finalMessageId) {
              completeStream(activeSessionId, finalMessageId, result.text);
              agentStoreUpdateMessage(activeSessionId, finalMessageId, {
                content: result.text,
                isStreaming: false,
              });
            }
            setStreamingMessageId(null);
          },
          onError: (error) => {
            console.warn('[ChatWindow] Streaming failed, trying fallback:', error);
            // Remove the empty placeholder using the service's ID
            if (streamingMessageId) {
              chatStoreAddMessage(activeSessionId, {
                message_id: `msg_remove_${streamingMessageId}`,
                session_id: activeSessionId,
                agent_id: activeSession?.agentId || 'prince_flowers',
                content: '',
                timestamp: Date.now(),
                _remove: streamingMessageId, // Marker to remove placeholder
              } as any);
            }

            setStreamingMessageId(null);
            handleFallbackSend(message, error);
          },
        }
      );
    } catch (error) {
      console.error('[ChatWindow] Streaming service error:', error);
      setStreamingMessageId(null);
      await handleFallbackSend(message, error);
    }
  }, [
    activeSessionId,
    activeSession?.agentId,
    isFirstMessage,
    chatStoreAddMessage,
    agentStoreAddMessage,
    agentStoreUpdateMessage,
    appendToStream,
    completeStream,
    setStreamingMessageId,
    agentStore,
  ]);

  /**
   * Fallback to WebSocket/non-streaming
   */
  const handleFallbackSend = useCallback(async (message: string, streamingError?: Error) => {
    if (!activeSessionId) return;

    // Show typing indicator
    setTyping(activeSessionId, true, activeSession?.agentId);

    try {
      await websocketManager.sendMessage(
        activeSessionId,
        message,
        activeSession?.agentId || ''
      );
    } catch (err: any) {
      console.error('Failed to send message via fallback:', err);
      setTyping(activeSessionId, false);

      // Show error message to user
      const errorMsg = {
        id: `msg_err_${Date.now()}`,
        agentId: activeSession?.agentId || '',
        type: 'text' as const,
        content: `⚠️ Failed to send: ${err.message || streamingError?.message || 'Unknown error'}`,
        timestamp: Date.now(),
      };
      agentStoreAddMessage(activeSessionId, errorMsg);
    }
  }, [activeSessionId, activeSession?.agentId, setTyping, agentStoreAddMessage]);

  // Listen for suggestion-click events from empty state
  useEffect(() => {
    const handleSuggestionClick = (e: Event) => {
      const customEvent = e as CustomEvent<{suggestion: string}>;
      const suggestion = customEvent.detail.suggestion;
      if (suggestion && activeSessionId && handleSend) {
        handleSend(suggestion);
      }
    };

    window.addEventListener('suggestion-click', handleSuggestionClick);
    return () => window.removeEventListener('suggestion-click', handleSuggestionClick);
  }, [activeSessionId, handleSend]);

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

        {/* Standalone mode badge */}
        <StandaloneModeBadge visible={isStandalone} />
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {activeSession.messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full">
            <ChatEmptyState
              agentName={activeAgent?.name}
              isFirstMessage={isFirstMessage}
            />
            {/* Standalone mode info panel */}
            {isStandalone && (
              <div className="mt-6 px-6 max-w-md">
                <div className="flex items-center gap-3 px-4 py-3 bg-amber-500/5 border border-amber-500/20 rounded-lg">
                  <span className="text-amber-400 flex-shrink-0">📡</span>
                  <div className="flex-1 text-sm">
                    <p className="font-medium text-amber-200">
                      TORQ Console is running in standalone mode
                    </p>
                    <p className="text-amber-300/70 mt-1">
                      Basic chat is available, but advanced multi-agent research requires Marvin AI runtime.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="divide-y divide-border">
            {activeSession.messages
              .filter(m => !m._remove || m._remove !== streamingMessageId) // Filter out placeholder during fallback
              .map((message) => (
              <ChatMessage
                key={message.id}
                message={message}
                agentName={activeAgent?.name || 'Agent'}
                isStreaming={message.id === streamingMessageId}
              />
            ))}
            {/* Typing indicator for fallback mode */}
            {typingState && typingState.isTyping && !streamingMessageId && (
              <TypingIndicator typingState={typingState} />
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <ChatInput
        onSend={handleSend}
        disabled={!!streamingMessageId}
      />
    </div>
  );
};
