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

  constructor(private url: string = 'http://localhost:8899') {}

  connect(): void {
    if (this.socket?.connected) {
      console.warn('WebSocket already connected');
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

  sendMessage(sessionId: string, content: string, agentId: string): void {
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
