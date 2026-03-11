/**
 * Phase 4.1: Streaming Chat Infrastructure
 *
 * Frontend infrastructure for streaming AI responses.
 * Ready for backend integration with Server-Sent Events or streaming WebSocket.
 *
 * Benefits:
 * - Perceived speed (tokens appear as they're generated)
 * - More natural AI responses
 * - Better UX for long responses
 */

// ============================================================================
// Types
// ============================================================================

export interface StreamingChatMessage {
  messageId: string;
  sessionId: string;
  agentId: string;
  content: string;
  isComplete: boolean;
  timestamp: number;
  metadata?: {
    model?: string;
    tokens?: number;
    duration?: number;
  };
}

export interface StreamingChatOptions {
  onChunk?: (chunk: string, messageId: string) => void;
  onComplete?: (message: StreamingChatMessage) => void;
  onError?: (error: Error) => void;
  onStart?: (messageId: string) => void;
}

export type StreamChunk = {
  type: 'chunk' | 'done' | 'error' | 'metadata';
  data: string | StreamingChatMessage | Error;
  messageId: string;
};

// ============================================================================
// Streaming Chat Manager
// ============================================================================

class StreamingChatManager {
  private activeStreams = new Map<string, ReadableStreamDefaultReader<Uint8Array>>();
  private abortControllers = new Map<string, AbortController>();

  /**
   * Send a message with streaming response
   *
   * This uses fetch with ReadableStream for Server-Sent Events style streaming.
   * The backend should respond with text/event-stream or chunked transfer encoding.
   */
  async sendMessageStream(
    sessionId: string,
    message: string,
    agentId: string,
    options: StreamingChatOptions = {}
  ): Promise<string> {
    const messageId = `msg_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
    const abortController = new AbortController();
    this.abortControllers.set(messageId, abortController);

    options.onStart?.(messageId);

    try {
      const response = await fetch('/api/v1/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify({
          session_id: sessionId,
          message,
          agent_id: agentId,
          stream: true,
        }),
        signal: abortController.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      if (!response.body) {
        throw new Error('Response body is null');
      }

      // Process the stream
      const reader = response.body.getReader();
      this.activeStreams.set(messageId, reader);

      const decoder = new TextDecoder();
      let fullContent = '';

      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        // Decode the chunk
        const chunk = decoder.decode(value, { stream: true });

        // Parse SSE format: "data: <json>\n\n"
        const lines = chunk.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') {
              continue;
            }

            try {
              const parsed = JSON.parse(data) as StreamChunk;

              switch (parsed.type) {
                case 'chunk':
                  fullContent += parsed.data as string;
                  options.onChunk?.(parsed.data as string, messageId);
                  break;

                case 'done':
                  const completeMessage: StreamingChatMessage = {
                    messageId,
                    sessionId,
                    agentId,
                    content: fullContent,
                    isComplete: true,
                    timestamp: Date.now(),
                    metadata: (parsed.data as StreamingChatMessage).metadata,
                  };
                  options.onComplete?.(completeMessage);
                  break;

                case 'error':
                  options.onError?.(new Error((parsed.data as Error).message));
                  break;

                case 'metadata':
                  // Update metadata without changing content
                  break;
              }
            } catch (e) {
              // If not JSON, treat as raw text chunk
              fullContent += data;
              options.onChunk?.(data, messageId);
            }
          }
        }
      }

      this.activeStreams.delete(messageId);
      this.abortControllers.delete(messageId);

      return messageId;
    } catch (error) {
      this.activeStreams.delete(messageId);
      this.abortControllers.delete(messageId);

      if (error instanceof Error && error.name === 'AbortError') {
        // User canceled the stream
        return messageId;
      }

      options.onError?.(error as Error);
      throw error;
    }
  }

  /**
   * Cancel an active stream
   */
  cancelStream(messageId: string): void {
    const reader = this.activeStreams.get(messageId);
    const controller = this.abortControllers.get(messageId);

    if (reader) {
      reader.cancel().catch(() => {
        // Ignore cancel errors
      });
      this.activeStreams.delete(messageId);
    }

    if (controller) {
      controller.abort();
      this.abortControllers.delete(messageId);
    }
  }

  /**
   * Cancel all active streams
   */
  cancelAllStreams(): void {
    for (const [messageId] of this.activeStreams) {
      this.cancelStream(messageId);
    }
  }

  /**
   * Get count of active streams
   */
  getActiveStreamCount(): number {
    return this.activeStreams.size;
  }
}

// ============================================================================
// Global singleton
// ============================================================================

export const streamingChat = new StreamingChatManager();

// ============================================================================
// React Hook for streaming chat
// ============================================================================

import { useState, useCallback, useRef } from 'react';

export interface UseStreamingChatState {
  isStreaming: boolean;
  streamedContent: string;
  error: Error | null;
  messageId: string | null;
}

export function useStreamingChat(sessionId: string, agentId: string) {
  const [state, setState] = useState<UseStreamingChatState>({
    isStreaming: false,
    streamedContent: '',
    error: null,
    messageId: null,
  });

  const currentMessageIdRef = useRef<string | null>(null);

  const sendMessage = useCallback(async (message: string) => {
    setState({
      isStreaming: true,
      streamedContent: '',
      error: null,
      messageId: null,
    });

    try {
      await streamingChat.sendMessageStream(
        sessionId,
        message,
        agentId,
        {
          onStart: (messageId) => {
            currentMessageIdRef.current = messageId;
            setState((prev) => ({ ...prev, messageId }));
          },
          onChunk: (chunk) => {
            setState((prev) => ({
              ...prev,
              streamedContent: prev.streamedContent + chunk,
            }));
          },
          onComplete: (completeMessage) => {
            setState({
              isStreaming: false,
              streamedContent: completeMessage.content,
              error: null,
              messageId: completeMessage.messageId,
            });
          },
          onError: (error) => {
            setState({
              isStreaming: false,
              streamedContent: '',
              error,
              messageId: null,
            });
          },
        }
      );
    } catch (error) {
      setState({
        isStreaming: false,
        streamedContent: '',
        error: error as Error,
        messageId: null,
      });
    }
  }, [sessionId, agentId]);

  const cancelStream = useCallback(() => {
    if (currentMessageIdRef.current) {
      streamingChat.cancelStream(currentMessageIdRef.current);
      setState((prev) => ({ ...prev, isStreaming: false }));
    }
  }, []);

  const reset = useCallback(() => {
    setState({
      isStreaming: false,
      streamedContent: '',
      error: null,
      messageId: null,
    });
  }, []);

  return {
    ...state,
    sendMessage,
    cancelStream,
    reset,
  };
}

// ============================================================================
// Mock streaming for development (when backend doesn't support it yet)
// ============================================================================

export class MockStreamingChat {
  /**
   * Simulate streaming response for development
   */
  static async simulateStream(
    content: string,
    options: StreamingChatOptions = {},
    delay: number = 30
  ): Promise<string> {
    const messageId = `msg_mock_${Date.now()}`;
    options.onStart?.(messageId);

    const chunks = content.split(/(?=\s)/g); // Split by word boundaries
    let accumulated = '';

    for (const chunk of chunks) {
      await new Promise((resolve) => setTimeout(resolve, delay + Math.random() * 20));
      accumulated += chunk;
      options.onChunk?.(chunk, messageId);
    }

    const completeMessage: StreamingChatMessage = {
      messageId,
      sessionId: 'mock_session',
      agentId: 'mock_agent',
      content: accumulated,
      isComplete: true,
      timestamp: Date.now(),
    };

    options.onComplete?.(completeMessage);
    return messageId;
  }
}
