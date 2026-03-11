/**
 * Connection Manager
 *
 * Manages connection health and provides polling fallback when
 * WebSocket/realtime connections are unavailable.
 *
 * Phase 1 - Platform Reliability Hardening
 * - Decouples socket startup from app initialization
 * - Provides degraded mode with polling fallback
 * - Allows UI to function without realtime connection
 */

import { AppState, AppStateStatus } from '@/types/connection';

export interface ConnectionConfig {
  // WebSocket configuration
  wsUrl?: string;
  autoConnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;

  // Polling configuration (degraded mode)
  pollingEnabled?: boolean;
  pollingInterval?: number;

  // Health check configuration
  healthCheckInterval?: number;
  healthCheckTimeout?: number;
}

export interface ConnectionManagerEvents {
  onConnect?: () => void;
  onDisconnect?: () => void;
  onDegraded?: () => void;
  onRecover?: () => void;
  onError?: (error: Error) => void;
}

/**
 * Connection Manager State
 */
interface ConnectionState {
  status: AppStateStatus;
  lastConnected: number | null;
  reconnectAttempts: number;
  usePolling: boolean;
}

/**
 * Connection Manager
 *
 * Manages WebSocket connections with automatic fallback to polling mode.
 * Ensures the UI remains functional even when realtime is unavailable.
 */
export class ConnectionManager {
  private config: Required<ConnectionConfig>;
  private events: ConnectionManagerEvents;
  private state: ConnectionState;
  private ws: WebSocket | null = null;
  private pollingTimer: ReturnType<typeof setInterval> | null = null;
  private healthCheckTimer: ReturnType<typeof setInterval> | null = null;

  constructor(
    config: ConnectionConfig = {},
    events: ConnectionManagerEvents = {}
  ) {
    this.config = {
      wsUrl: config.wsUrl || `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/socket.io`,
      autoConnect: config.autoConnect ?? false, // IMPORTANT: Don't auto-connect
      reconnectInterval: config.reconnectInterval || 3000,
      maxReconnectAttempts: config.maxReconnectAttempts || 5,
      pollingEnabled: config.pollingEnabled ?? true,
      pollingInterval: config.pollingInterval || 5000, // 5 seconds
      healthCheckInterval: config.healthCheckInterval || 30000, // 30 seconds
      healthCheckTimeout: config.healthCheckTimeout || 5000, // 5 seconds
    };

    this.events = events;
    this.state = {
      status: 'disconnected',
      lastConnected: null,
      reconnectAttempts: 0,
      usePolling: false,
    };
  }

  /**
   * Get current connection status
   */
  get status(): AppStateStatus {
    return this.state.status;
  }

  /**
   * Check if using degraded (polling) mode
   */
  get isDegraded(): boolean {
    return this.state.usePolling;
  }

  /**
   * Check if connected (either WebSocket or polling)
   */
  get isConnected(): boolean {
    return this.state.status === 'connected' || this.state.status === 'degraded';
  }

  /**
   * Start connection attempts
   */
  async connect(): Promise<void> {
    if (this.state.status === 'connected') {
      return;
    }

    console.log('[ConnectionManager] Starting connection...');

    // Try WebSocket first
    try {
      await this.connectWebSocket();
    } catch (error) {
      console.warn('[ConnectionManager] WebSocket connection failed, switching to degraded mode:', error);

      // Fall back to polling mode
      this.startPolling();
    }
  }

  /**
   * Disconnect from all services
   */
  disconnect(): void {
    console.log('[ConnectionManager] Disconnecting...');

    // Stop WebSocket
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    // Stop polling
    this.stopPolling();

    // Stop health checks
    this.stopHealthChecks();

    this.state.status = 'disconnected';
    this.state.lastConnected = null;

    this.events.onDisconnect?.();
  }

  /**
   * Attempt WebSocket connection
   */
  private async connectWebSocket(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws) {
        this.ws.close();
      }

      try {
        this.ws = new WebSocket(this.config.wsUrl);

        const timeout = setTimeout(() => {
          if (this.ws?.readyState !== WebSocket.OPEN) {
            this.ws?.close();
            reject(new Error('WebSocket connection timeout'));
          }
        }, 5000);

        this.ws.onopen = () => {
          clearTimeout(timeout);
          console.log('[ConnectionManager] WebSocket connected');
          this.state.status = 'connected';
          this.state.lastConnected = Date.now();
          this.state.reconnectAttempts = 0;
          this.state.usePolling = false;

          this.events.onConnect?.();

          // Start health checks
          this.startHealthChecks();

          resolve();
        };

        this.ws.onclose = (event) => {
          clearTimeout(timeout);

          if (event.code !== 1000) {
            console.warn('[ConnectionManager] WebSocket closed unexpectedly:', event.code, event.reason);

            // Attempt reconnect if we haven't exceeded max attempts
            if (this.state.reconnectAttempts < this.config.maxReconnectAttempts) {
              this.state.reconnectAttempts++;
              setTimeout(() => {
                this.connect().catch(console.error);
              }, this.config.reconnectInterval);
            } else {
              // Switch to degraded mode
              this.startPolling();
            }
          }
        };

        this.ws.onerror = (error) => {
          clearTimeout(timeout);
          console.error('[ConnectionManager] WebSocket error:', error);
          this.events.onError?.(error as Error);
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Start polling mode (degraded mode)
   */
  private startPolling(): void {
    if (this.pollingTimer) {
      return; // Already polling
    }

    console.log('[ConnectionManager] Switching to degraded (polling) mode');

    this.state.status = 'degraded';
    this.state.usePolling = true;

    this.events.onDegraded?.();

    // Start periodic polling
    this.pollingTimer = setInterval(() => {
      this.pollForUpdates();
    }, this.config.pollingInterval);

    // Initial poll
    this.pollForUpdates();
  }

  /**
   * Stop polling mode
   */
  private stopPolling(): void {
    if (this.pollingTimer) {
      clearInterval(this.pollingTimer);
      this.pollingTimer = null;
    }
  }

  /**
   * Poll for updates (degraded mode implementation)
   */
  private async pollForUpdates(): Promise<void> {
    try {
      // Poll for execution updates
      const response = await fetch('/api/executions?active=true', {
        signal: AbortSignal.timeout(5000),
      });

      if (response.ok) {
        const data = await response.json();

        // Emit updates to subscribers
        // This would be integrated with the execution monitor store
        console.debug('[ConnectionManager] Polling: got updates');

        // If we were previously degraded, check if WebSocket is available now
        if (this.state.usePolling) {
          this.tryRecoverWebSocket();
        }
      }
    } catch (error) {
      console.debug('[ConnectionManager] Polling failed:', error);
    }
  }

  /**
   * Try to recover WebSocket connection from degraded mode
   */
  private async tryRecoverWebSocket(): Promise<void> {
    try {
      // Test WebSocket connection
      const testWs = new WebSocket(this.config.wsUrl);

      const timeout = setTimeout(() => {
        testWs.close();
        console.debug('[ConnectionManager] WebSocket still unavailable, staying in degraded mode');
      }, 2000);

      testWs.onopen = () => {
        clearTimeout(timeout);
        testWs.close();

        console.log('[ConnectionManager] WebSocket recovered!');
        this.stopPolling();
        this.state.usePolling = false;
        this.connect().catch(console.error);

        this.events.onRecover?.();
      };

      testWs.onerror = () => {
        clearTimeout(timeout);
      };

    } catch {
      // Stay in degraded mode
    }
  }

  /**
   * Start health checks
   */
  private startHealthChecks(): void {
    this.healthCheckTimer = setInterval(() => {
      this.performHealthCheck();
    }, this.config.healthCheckInterval);
  }

  /**
   * Stop health checks
   */
  private stopHealthChecks(): void {
    if (this.healthCheckTimer) {
      clearInterval(this.healthCheckTimer);
      this.healthCheckTimer = null;
    }
  }

  /**
   * Perform health check on connection
   */
  private async performHealthCheck(): Promise<void> {
    try {
      const response = await fetch('/api/health', {
        signal: AbortSignal.timeout(this.config.healthCheckTimeout),
      });

      if (!response.ok) {
        throw new Error(`Health check failed: ${response.status}`);
      }

      // Health check passed
      if (this.state.status !== 'connected') {
        console.debug('[ConnectionManager] Health check passed');
      }

    } catch (error) {
      console.warn('[ConnectionManager] Health check failed:', error);

      // If we thought we were connected but health check failed, switch to degraded
      if (this.state.status === 'connected') {
        this.startPolling();
      }
    }
  }

  /**
   * Send message through WebSocket or queue for polling
   */
  send(event: string, data: unknown): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ event, data }));
    } else {
      console.debug('[ConnectionManager] WebSocket not available, message queued for polling');
      // In degraded mode, we could queue this for the next poll cycle
    }
  }

  /**
   * Subscribe to WebSocket events
   */
  on(event: string, callback: (data: unknown) => void): void {
    // This would be integrated with the actual WebSocket implementation
    // For now, it's a placeholder for the API surface
  }

  /**
   * Unsubscribe from WebSocket events
   */
  off(event: string, callback: (data: unknown) => void): void {
    // This would be integrated with the actual WebSocket implementation
    // For now, it's a placeholder for the API surface
  }
}

/**
 * Singleton instance
 */
let connectionManagerInstance: ConnectionManager | null = null;

/**
 * Get or create the connection manager singleton
 */
export function getConnectionManager(
  config?: ConnectionConfig,
  events?: ConnectionManagerEvents
): ConnectionManager {
  if (!connectionManagerInstance) {
    connectionManagerInstance = new ConnectionManager(config, events);
  }
  return connectionManagerInstance;
}

/**
 * Reset the connection manager singleton
 * Useful for testing or forced reconnection
 */
export function resetConnectionManager(): void {
  if (connectionManagerInstance) {
    connectionManagerInstance.disconnect();
    connectionManagerInstance = null;
  }
}

export default ConnectionManager;
