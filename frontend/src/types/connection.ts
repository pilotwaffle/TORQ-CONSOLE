/**
 * Connection-related type definitions
 *
 * Phase 1 - Platform Reliability Hardening
 */

export type AppStateStatus =
  | 'connected'      // Fully connected with WebSocket
  | 'degraded'       // Connected but using polling fallback
  | 'disconnected'   // Not connected
  | 'error';         // Connection error

export interface AppState {
  status: AppStateStatus;
  lastConnected: number | null;
  usePolling: boolean;
  reconnectAttempts: number;
}

export interface ConnectionHealth {
  backend: 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
  realtime: 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
  agents: 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
}
