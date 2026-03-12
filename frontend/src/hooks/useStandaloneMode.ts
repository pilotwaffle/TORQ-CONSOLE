/**
 * useStandaloneMode Hook
 *
 * Detects if TORQ Console is running in standalone mode (without Marvin AI agents).
 * Standalone mode is indicated by:
 * - agents_active: 0 in status response
 * - marvin_available: false in metadata
 */

import { useState, useEffect } from 'react';

interface SystemStatus {
  status: string;
  agents_active: number;
  sessions_active: number;
  uptime_seconds: number;
  metrics: {
    marvin_available?: boolean;
    [key: string]: any;
  };
}

export function useStandaloneMode() {
  const [isStandalone, setIsStandalone] = useState(true);
  const [isLoading, setIsLoading] = useState(true);
  const [status, setStatus] = useState<SystemStatus | null>(null);

  useEffect(() => {
    const checkStandaloneMode = async () => {
      try {
        const response = await fetch('/api/status');
        if (response.ok) {
          const data: SystemStatus = await response.json();
          setStatus(data);

          // Check if we're in standalone mode
          const noAgentsActive = data.agents_active === 0;
          const marvinUnavailable = data.metrics?.marvin_available === false;

          setIsStandalone(noAgentsActive || marvinUnavailable);
        }
      } catch (error) {
        console.error('[useStandaloneMode] Failed to check status:', error);
        // Assume standalone mode on error
        setIsStandalone(true);
      } finally {
        setIsLoading(false);
      }
    };

    checkStandaloneMode();

    // Recheck every 30 seconds
    const interval = setInterval(checkStandaloneMode, 30000);
    return () => clearInterval(interval);
  }, []);

  return {
    isStandalone,
    isLoading,
    status,
  };
}
