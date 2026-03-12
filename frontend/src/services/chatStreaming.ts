/**
 * Chat Streaming Service
 *
 * SSE-based streaming for chat responses with fallback to non-streaming.
 * Matches backend SSE format: data: {"token": "..."}\n\n
 */

import { createUserMessage } from '@/utils/messageUtils';

// ============================================================================
// Types matching backend SSE format
// ============================================================================

export interface ChatStreamOptions {
  onStart?: (messageId: string) => void;
  onToken?: (token: string, messageId: string) => void;
  onComplete?: (result: ChatStreamResult) => void;
  onError?: (error: Error) => void;
}

export interface ChatStreamResult {
  text: string;
  messageId: string;
  sessionId: string;
  agentId: string;
  metadata: {
    latency_ms: number;
    provider: string;
    cold_start_ms?: number;
    timestamp: string;
  };
}

export interface ChatRequest {
  message: string;
  session_id: string;
  agent_id?: string;
  mode?: string;
  context?: Record<string, unknown>;
  model?: string;
}

// ============================================================================
// Chat Streaming Service
// ============================================================================

class ChatStreamingService {
  private abortControllers = new Map<string, AbortController>();
  private activeStreams = new Set<string>();

  /**
   * Send a chat message with streaming response
   *
   * Tries streaming first, falls back to non-streaming if:
   * - Streaming is disabled (feature flag)
   * - SSE not supported
   * - Connection fails
   */
  async sendMessage(
    request: ChatRequest,
    options: ChatStreamOptions = {}
  ): Promise<string> {
    const messageId = `msg_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
    options.onStart?.(messageId);

    // First, check if streaming might be available
    const streamingEnabled = await this.checkStreamingEnabled();

    if (streamingEnabled && this.supportsSSE()) {
      try {
        await this.sendMessageStream(request, messageId, options);
        return messageId;
      } catch (streamError) {
        console.warn('[ChatStream] Streaming failed, falling back to non-streaming:', streamError);
        // Fall through to non-streaming
      }
    }

    // Fallback to non-streaming
    return this.sendMessageNonStreaming(request, messageId, options);
  }

  /**
   * Check if streaming is enabled via feature flag
   */
  private async checkStreamingEnabled(): Promise<boolean> {
    try {
      const response = await fetch('/api/status');
      if (!response.ok) return false;
      const data = await response.json();
      return data.streaming_enabled === true;
    } catch {
      return false;
    }
  }

  /**
   * Check if browser supports SSE
   */
  private supportsSSE(): boolean {
    return typeof ReadableStream !== 'undefined' &&
           typeof TextDecoder !== 'undefined';
  }

  /**
   * Send message with SSE streaming
   *
   * Backend SSE format:
   * data: {"token": "..."}\n\n
   * data: {"meta": {...}}\n\n
   * data: [DONE]\n\n
   */
  private async sendMessageStream(
    request: ChatRequest,
    messageId: string,
    options: ChatStreamOptions
  ): Promise<void> {
    const abortController = new AbortController();
    this.abortControllers.set(messageId, abortController);
    this.activeStreams.add(messageId);

    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify({
        v: 1,
        message: request.message,
        session_id: request.session_id,
        agent_id: request.agent_id,
        mode: request.mode || 'auto',
        context: request.context,
        model: request.model,
      }),
      signal: abortController.signal,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    if (!response.body) {
      throw new Error('Response body is null');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let fullText = '';
    let metadata: ChatStreamResult['metadata'] | null = null;

    try {
      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        // Decode chunk and add to buffer
        buffer += decoder.decode(value, { stream: true });

        // Process complete SSE messages
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim();

            // Check for [DONE] sentinel
            if (data === '[DONE]') {
              this.activeStreams.delete(messageId);
              this.abortControllers.delete(messageId);

              if (metadata && fullText) {
                options.onComplete?.({
                  text: fullText,
                  messageId,
                  sessionId: request.session_id,
                  agentId: request.agent_id || 'prince_flowers',
                  metadata,
                });
              }
              return;
            }

            // Parse JSON data
            try {
              const parsed = JSON.parse(data);

              if (parsed.token) {
                fullText += parsed.token;
                options.onToken?.(parsed.token, messageId);
              }

              if (parsed.meta) {
                metadata = parsed.meta;
              }

              if (parsed.error) {
                throw new Error(parsed.error);
              }
            } catch (parseError) {
              // Not JSON or invalid, skip
              console.debug('[ChatStream] Failed to parse SSE data:', data);
            }
          }
        }
      }
    } finally {
      this.activeStreams.delete(messageId);
      this.abortControllers.delete(messageId);
    }
  }

  /**
   * Fallback: Non-streaming chat
   */
  private async sendMessageNonStreaming(
    request: ChatRequest,
    messageId: string,
    options: ChatStreamOptions
  ): Promise<string> {
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          v: 1,
          message: request.message,
          session_id: request.session_id,
          agent_id: request.agent_id,
          mode: request.mode || 'auto',
          context: request.context,
          model: request.model,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();

      // Single "token" event with full response
      options.onToken?.(result.response || result.text || '', messageId);

      options.onComplete?.({
        text: result.response || result.text || '',
        messageId,
        sessionId: request.session_id,
        agentId: result.agent_id || request.agent_id || 'prince_flowers',
        metadata: {
          latency_ms: result.metadata?.duration_ms || result.metadata?.latency_ms || 0,
          provider: result.metadata?.provider || 'unknown',
          timestamp: result.timestamp || new Date().toISOString(),
        },
      });

      return messageId;
    } catch (error) {
      options.onError?.(error as Error);
      throw error;
    }
  }

  /**
   * Cancel an active stream
   */
  cancel(messageId: string): void {
    const controller = this.abortControllers.get(messageId);
    if (controller) {
      controller.abort();
      this.abortControllers.delete(messageId);
    }
    this.activeStreams.delete(messageId);
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

export const chatStreamingService = new ChatStreamingService();

// ============================================================================
// React Hook
// ============================================================================

import { useState, useCallback, useRef } from 'react';

export interface UseChatStreamingState {
  isStreaming: boolean;
  streamedText: string;
  error: Error | null;
  messageId: string | null;
}

export function useChatStreaming(sessionId: string, agentId?: string) {
  const [state, setState] = useState<UseChatStreamingState>({
    isStreaming: false,
    streamedText: '',
    error: null,
    messageId: null,
  });

  const currentMessageIdRef = useRef<string | null>(null);

  const sendMessage = useCallback(async (message: string) => {
    setState({
      isStreaming: true,
      streamedText: '',
      error: null,
      messageId: null,
    });

    try {
      await chatStreamingService.sendMessage(
        {
          message,
          session_id: sessionId,
          agent_id: agentId,
        },
        {
          onStart: (messageId) => {
            currentMessageIdRef.current = messageId;
            setState((prev) => ({ ...prev, messageId }));
          },
          onToken: (token) => {
            setState((prev) => ({
              ...prev,
              streamedText: prev.streamedText + token,
            }));
          },
          onComplete: (result) => {
            setState({
              isStreaming: false,
              streamedText: result.text,
              error: null,
              messageId: result.messageId,
            });
          },
          onError: (error) => {
            setState({
              isStreaming: false,
              streamedText: '',
              error,
              messageId: null,
            });
          },
        }
      );
    } catch (error) {
      setState({
        isStreaming: false,
        streamedText: '',
        error: error as Error,
        messageId: null,
      });
    }
  }, [sessionId, agentId]);

  const cancelStream = useCallback(() => {
    if (currentMessageIdRef.current) {
      chatStreamingService.cancel(currentMessageIdRef.current);
      setState((prev) => ({ ...prev, isStreaming: false }));
    }
  }, []);

  const reset = useCallback(() => {
    setState({
      isStreaming: false,
      streamedText: '',
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
