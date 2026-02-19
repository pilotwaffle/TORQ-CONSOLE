import { io, Socket } from 'socket.io-client';
import { Agent, Message } from '@/lib/types';

type ConnectionStatus = 'connected' | 'disconnected' | 'connecting' | 'error';

interface WebSocketEventHandlers {
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Error) => void;
  onAgentStatus?: (agent: Agent) => void;
  onMessage?: (message: Message) => void;
  onAgentResponse?: (data: { sessionId: string; message: Message }) => void;
  onSessionCreated?: (data: { sessionId: string; agentId: string }) => void;
}

class WebSocketManager {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private eventHandlers: WebSocketEventHandlers = {};
  private connectionStatus: ConnectionStatus = 'disconnected';
  private isManualDisconnect = false;

  // Phase 1 Feature Flag + Caching
  private statusCache?: { ts: number; streaming: boolean };

  constructor(private url: string = '') { }

  private async getStreamingEnabled(): Promise<boolean> {
    const now = Date.now();
    // Cache valid for 30 seconds
    if (this.statusCache && now - this.statusCache.ts < 30000) {
      return this.statusCache.streaming;
    }

    try {
      const res = await fetch('/api/status');
      if (res.ok) {
        const data = await res.json();
        const streaming = !!data.streaming_enabled;
        this.statusCache = { ts: now, streaming };
        return streaming;
      }
    } catch (e) {
      console.warn('Failed to check streaming status:', e);
    }
    return false; // Default off if check fails
  }

  async connect(): Promise<void> {

    // Pre-warm cache for generic info, but don't block
    this.getStreamingEnabled().then(enabled => {
      if (enabled) console.log('Phase 1: Streaming Enabled 🌊');
    });

    if (this.socket?.connected) {
      console.warn('WebSocket already connected');
      return;
    }

    // Check Vercel environment
    const isVercel = typeof window !== 'undefined' && window.location.hostname.includes('vercel.app');

    if (isVercel) {
      console.log('Running in Vercel mode: using REST/Stream fallback (WebSockets disabled)');
      this.connectionStatus = 'connected';
      this.eventHandlers.onConnect?.();
      return;
    }

    this.isManualDisconnect = false;
    this.connectionStatus = 'connecting';

    this.socket = io(this.url, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: this.reconnectDelay,
      reconnectionDelayMax: 5000,
      timeout: 20000,
    });

    this.setupEventListeners();
  }

  disconnect(): void {
    this.isManualDisconnect = true;
    this.connectionStatus = 'disconnected';

    if (this.socket) {
      this.socket.removeAllListeners();
      this.socket.disconnect();
      this.socket = null;
    }

    this.reconnectAttempts = 0;
  }

  private setupEventListeners(): void {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.connectionStatus = 'connected';
      this.reconnectAttempts = 0;
      this.eventHandlers.onConnect?.();
    });

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      this.connectionStatus = 'disconnected';
      this.eventHandlers.onDisconnect?.();

      if (!this.isManualDisconnect && reason === 'io server disconnect') {
        this.attemptReconnect();
      }
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      this.connectionStatus = 'error';
      this.eventHandlers.onError?.(error);
      this.attemptReconnect();
    });

    this.socket.on('error', (error) => {
      console.error('WebSocket error:', error);
      this.connectionStatus = 'error';
      this.eventHandlers.onError?.(new Error(error));
    });

    this.socket.on('agent:status', (data: { agent: Agent }) => {
      this.eventHandlers.onAgentStatus?.(data.agent);
    });

    this.socket.on('agent:response', (data: { sessionId: string; message: Message }) => {
      this.eventHandlers.onAgentResponse?.(data);
    });

    this.socket.on('session:created', (data: { sessionId: string; agentId: string }) => {
      this.eventHandlers.onSessionCreated?.(data);
    });

    this.socket.on('message:received', (data: { message: Message }) => {
      this.eventHandlers.onMessage?.(data.message);
    });
  }

  private attemptReconnect(): void {
    if (this.isManualDisconnect || this.reconnectAttempts >= this.maxReconnectAttempts) {
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000);

    setTimeout(() => {
      if (!this.isManualDisconnect && this.connectionStatus !== 'connected') {
        this.connect();
      }
    }, delay);
  }

  on<K extends keyof WebSocketEventHandlers>(event: K, handler: WebSocketEventHandlers[K]): void {
    this.eventHandlers[event] = handler;
  }

  off<K extends keyof WebSocketEventHandlers>(event: K): void {
    delete this.eventHandlers[event];
  }

  emit(event: string, data?: any): void {
    if (!this.socket?.connected) {
      console.warn('Cannot emit event: WebSocket not connected');
      return;
    }

    this.socket.emit(event, data);
  }

  async sendMessage(sessionId: string, content: string, agentId: string): Promise<void> {
    const isVercel = typeof window !== 'undefined' && window.location.hostname.includes('vercel.app');

    // Check streaming status dynamically (cached)
    const streamingEnabled = await this.getStreamingEnabled();

    // Use streaming if enabled and on Vercel (or forced)
    if ((isVercel || !this.socket?.connected) && streamingEnabled) {
      return this.streamMessage(sessionId, content, agentId);
    }

    // Use REST fallback if streaming disabled
    if (isVercel || !this.socket?.connected) {
      return this.sendRestMessage(sessionId, content, agentId);
    }

    this.emit('message:send', {
      sessionId,
      content,
      agentId,
      timestamp: Date.now(),
    });
  }

  private async sendRestMessage(sessionId: string, content: string, agentId: string): Promise<void> {
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: content,
          mode: 'single_agent', // Default mode
          model: 'claude-3-5-sonnet-20240620',
        }),
      });

      if (!response.ok) throw new Error(await response.text());
      const data = await response.json();

      const responseMessage: Message = {
        id: `msg_${Date.now()}`,
        role: 'assistant',
        content: data.response,
        timestamp: Date.now(),
        agentId: data.agent_id || 'prince_flowers',
      };

      // Use onAgentResponse to trigger upsert logic in store
      this.eventHandlers.onAgentResponse?.({ sessionId, message: responseMessage });
      this.eventHandlers.onMessage?.(responseMessage);

    } catch (error) {
      console.error('REST API Error:', error);
      this.eventHandlers.onError?.(error instanceof Error ? error : new Error(String(error)));
    }
  }

  private async streamMessage(sessionId: string, content: string, agentId: string): Promise<void> {
    try {
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: content,
          mode: 'single_agent',
          model: 'claude-3-5-sonnet-20240620',
        }),
      });

      if (!response.ok) throw new Error(await response.text());

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response body');

      const decoder = new TextDecoder();
      let buffer = '';
      let accumulatedText = '';
      const msgId = `msg_${Date.now()}`;

      // Helper to emit update
      const emitUpdate = (text: string, isFinal = false) => {
        const msg: Message = {
          id: msgId,
          role: 'assistant',
          content: text,
          timestamp: Date.now(),
          agentId: agentId || 'prince_flowers',
        };
        // Emit via onAgentResponse for store upsert (with sessionId)
        this.eventHandlers.onAgentResponse?.({ sessionId, message: msg });

        // DO NOT emit onMessage for stream updates to avoid store append duplication!
        // this.eventHandlers.onMessage?.(msg); 
      };

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        buffer = parts.pop() || ''; // Keep incomplete part

        for (const part of parts) {
          const line = part.trim();
          if (!line.startsWith('data: ')) continue;

          const jsonStr = line.slice(6);
          if (jsonStr === '[DONE]') break;

          try {
            const event = JSON.parse(jsonStr);
            if (event.token) {
              accumulatedText += event.token;
              emitUpdate(accumulatedText);
            }
            if (event.meta) {
              console.log('Stream Metadata:', event.meta);
            }
            if (event.error) {
              console.error('Stream Error:', event.error);
            }
          } catch (e) {
            console.warn('Failed to parse SSE event:', jsonStr);
          }
        }
      }
      emitUpdate(accumulatedText, true);

    } catch (error) {
      console.error('Streaming Error:', error);
      this.eventHandlers.onError?.(error instanceof Error ? error : new Error(String(error)));
    }
  }

  createSession(agentId: string, title?: string): void {
    this.emit('session:create', {
      agentId,
      title: title || 'New Session',
      timestamp: Date.now(),
    });
  }

  updateAgentStatus(agentId: string, status: Agent['status']): void {
    this.emit('agent:update_status', {
      agentId,
      status,
      timestamp: Date.now(),
    });
  }

  requestAgentAction(agentId: string, action: string, payload?: any): void {
    this.emit('agent:action', {
      agentId,
      action,
      payload,
      timestamp: Date.now(),
    });
  }

  getConnectionStatus(): ConnectionStatus {
    return this.connectionStatus;
  }

  isConnected(): boolean {
    return this.socket?.connected ?? false;
  }
}

export const websocketManager = new WebSocketManager();

export default websocketManager;
