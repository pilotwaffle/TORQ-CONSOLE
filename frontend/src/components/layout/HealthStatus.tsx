/**
 * Health Status Banner
 *
 * Displays real-time system health status for backend and realtime connections.
 * Provides visibility into service availability without blocking the UI.
 *
 * Phase 1 - Platform Reliability Hardening
 */

import { useEffect, useState } from 'react';
import { CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';

type HealthStatus = 'healthy' | 'degraded' | 'unhealthy' | 'unknown';

interface ServiceHealth {
  backend: HealthStatus;
  realtime: HealthStatus;
  agents: HealthStatus;
}

/**
 * Get status icon for a health status
 */
function StatusIcon({ status }: { status: HealthStatus }) {
  switch (status) {
    case 'healthy':
      return (
        <CheckCircle2 className="w-4 h-4 text-green-500" />
      );
    case 'degraded':
      return (
        <AlertTriangle className="w-4 h-4 text-yellow-500" />
      );
    case 'unhealthy':
      return (
        <XCircle className="w-4 h-4 text-red-500" />
      );
    default:
      return (
        <div className="w-4 h-4 bg-gray-300 rounded-full" />
      );
  }
}

/**
 * Get status text for a health status
 */
function getStatusText(status: HealthStatus): string {
  switch (status) {
    case 'healthy':
      return 'Connected';
    case 'degraded':
      return 'Degraded';
    case 'unhealthy':
      return 'Unavailable';
    default:
      return 'Unknown';
  }
}

/**
 * Health Status Banner Component
 *
 * Displays a compact status bar showing:
 * - Backend API health
 * - Realtime (WebSocket) connection status
 * - Agent system status
 */
export function HealthStatus() {
  const [health, setHealth] = useState<ServiceHealth>({
    backend: 'unknown',
    realtime: 'unknown',
    agents: 'unknown',
  });
  const [isVisible, setIsVisible] = useState(false);

  // Show status bar briefly on connection changes
  useEffect(() => {
    if (health.backend !== 'healthy' || health.realtime !== 'healthy') {
      setIsVisible(true);
    }
  }, [health.backend, health.realtime]);

  // Check backend health
  useEffect(() => {
    const checkBackendHealth = async () => {
      try {
        const response = await fetch('/api/status', {
          method: 'GET',
          signal: AbortSignal.timeout(5000), // 5 second timeout
        });

        if (response.ok) {
          setHealth(prev => ({ ...prev, backend: 'healthy' }));
        } else {
          setHealth(prev => ({ ...prev, backend: 'unhealthy' }));
        }
      } catch {
        setHealth(prev => ({ ...prev, backend: 'unhealthy' }));
      }
    };

    // Check immediately
    checkBackendHealth();

    // Then check every 30 seconds
    const interval = setInterval(checkBackendHealth, 30000);

    return () => clearInterval(interval);
  }, []);

  // Monitor realtime connection from agentStore
  useEffect(() => {
    // Import agentStore to get connection status
    const checkRealtimeStatus = () => {
      try {
        // @ts-ignore - accessing store directly
        const { isConnected } = window.__agentStore__?.getState() || { isConnected: false };
        setHealth(prev => ({
          ...prev,
          realtime: isConnected ? 'healthy' : 'unhealthy',
          agents: isConnected ? 'healthy' : 'degraded',
        }));
      } catch {
        setHealth(prev => ({ ...prev, realtime: 'unhealthy' }));
      }
    };

    // Check immediately and every 5 seconds
    checkRealtimeStatus();
    const interval = setInterval(checkRealtimeStatus, 5000);

    return () => clearInterval(interval);
  }, []);

  // Don't show if everything is healthy and no recent issues
  if (!isVisible && health.backend === 'healthy' && health.realtime === 'healthy') {
    return null;
  }

  const hasIssues = health.backend !== 'healthy' || health.realtime !== 'healthy';

  return (
    <div
      className={`
        fixed top-0 left-0 right-0 z-50
        flex items-center justify-center gap-6
        px-4 py-2
        text-xs font-medium
        transition-all duration-300
        ${hasIssues
          ? 'bg-yellow-50 border-b border-yellow-200 text-yellow-800'
          : 'bg-green-50 border-b border-green-200 text-green-800'
        }
      `}
    >
      {/* Backend Status */}
      <div className="flex items-center gap-2">
        <StatusIcon status={health.backend} />
        <span>API: {getStatusText(health.backend)}</span>
      </div>

      {/* Realtime Status */}
      <div className="flex items-center gap-2">
        <StatusIcon status={health.realtime} />
        <span>Realtime: {getStatusText(health.realtime)}</span>
      </div>

      {/* Agents Status */}
      <div className="flex items-center gap-2">
        <StatusIcon status={health.agents} />
        <span>Agents: {getStatusText(health.agents)}</span>
      </div>

      {/* Dismiss button */}
      <button
        onClick={() => setIsVisible(false)}
        className="ml-4 hover:opacity-70"
        aria-label="Dismiss status banner"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  );
}

/**
 * Compact health indicator (smaller version for header)
 */
export function HealthIndicator() {
  const [health, setHealth] = useState<HealthStatus>('unknown');

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch('/api/status', {
          method: 'GET',
          signal: AbortSignal.timeout(3000),
        });
        setHealth(response.ok ? 'healthy' : 'unhealthy');
      } catch {
        setHealth('unhealthy');
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div
      className="flex items-center gap-1.5"
      title={`Backend status: ${health}`}
    >
      <StatusIcon status={health} />
    </div>
  );
}

export default HealthStatus;
