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

  constructor(private url: string = '') { }

  connect(): void {
    if (this.socket?.connected) {
      console.warn('WebSocket already connected');
      return;
    }

    // Check if we are running on Vercel (or configured to use REST fallback)
    // Vercel serverless functions do not support persistent WebSockets
    const isVercel = typeof window !== 'undefined' && window.location.hostname.includes('vercel.app');

    if (isVercel) {
      console.log('Running in Vercel mode: using REST fallback for chat (WebSockets disabled)');
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
    // If running in Vercel mode (no socket), use REST API
    const isVercel = typeof window !== 'undefined' && window.location.hostname.includes('vercel.app');

    if (isVercel || !this.socket?.connected) {
      if (isVercel) {
        console.log('Sending message via REST API (Vercel mode)');
      } else {
        // Only warn if explicitly trying to send while disconnected in non-Vercel mode
        if (!isVercel) console.warn('WebSocket not connected, falling back to REST API');
      }

      try {
        const response = await fetch('/api/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message: content,
            mode: 'single_agent', // Default mode
            model: 'claude-3-sonnet-20240229', // Default model
            context: { sessionId, agentId }
          }),
        });

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`API Error: ${response.status} ${errorText}`);
        }

        const data = await response.json();

        const responseMessage: Message = {
          id: `msg_${Date.now()}`,
          role: 'assistant',
          content: data.response,
          timestamp: Date.now(),
          agentId: data.agent_id || 'prince_flowers',
        };

        this.eventHandlers.onMessage?.(responseMessage);

        this.eventHandlers.onAgentResponse?.({
          sessionId,
          message: responseMessage
        });

      } catch (error) {
        console.error('REST API Error:', error);
        this.eventHandlers.onError?.(error instanceof Error ? error : new Error(String(error)));
      }
      return;
    }

    this.emit('message:send', {
      sessionId,
      content,
      agentId,
      timestamp: Date.now(),
    });
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
