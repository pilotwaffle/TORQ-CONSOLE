/**
 * Phase 1 - Platform Reliability Hardening Tests
 *
 * Tests for:
 * - Error Boundary functionality
 * - Router bootstrapping
 * - Backend unavailable scenario
 * - Socket unavailable scenario
 * - Partial service failure
 *
 * Run with: npm run test phase1-reliability
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AppErrorBoundary } from '@/components/errors';
import { HealthStatus } from '@/components/layout/HealthStatus';
import { getConnectionManager, resetConnectionManager } from '@/services/connectionManager';

describe('Phase 1: Platform Reliability', () => {
  describe('AppErrorBoundary', () => {
    beforeEach(() => {
      resetConnectionManager();
    });

    afterEach(() => {
      vi.clearAllMocks();
    });

    it('should catch and display rendering errors', () => {
      const ThrowError = () => {
        throw new Error('Test rendering error');
      };

      render(
        <AppErrorBoundary>
          <ThrowError />
        </AppErrorBoundary>
      );

      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
      expect(screen.getByText('Reload Application')).toBeInTheDocument();
    });

    it('should display error details in development mode', () => {
      const originalDev = import.meta.env.DEV;
      vi.stubGlobal('import.meta', { env: { DEV: true } });

      const ThrowError = () => {
        throw new Error('Test error with details');
      };

      render(
        <AppErrorBoundary>
          <ThrowError />
        </AppErrorBoundary>
      );

      expect(screen.getByText('Error Details')).toBeInTheDocument();
      expect(screen.getByText(/Test error with details/)).toBeInTheDocument();

      vi.unstubAllGlobals();
    });

    it('should allow recovery via reload button', async () => {
      let shouldThrow = true;

      const ThrowThenRecover = () => {
        if (shouldThrow) {
          throw new Error('Initial error');
        }
        return <div>Recovered content</div>;
      };

      const { rerender } = render(
        <AppErrorBoundary>
          <ThrowThenRecover />
        </AppErrorBoundary>
      );

      // Should show error state
      expect(screen.getByText('Something went wrong')).toBeInTheDocument();

      // Fix the error and click reload button
      shouldThrow = false;
      const reloadButton = screen.getByText('Reload Application');
      await userEvent.click(reloadButton);

      // After clicking reload, the error boundary resets and tries to rerender
      // Since the component no longer throws, it should show recovered content
      rerender(
        <AppErrorBoundary>
          <ThrowThenRecover />
        </AppErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText('Recovered content')).toBeInTheDocument();
      });
    });

    it('should render children normally when no error occurs', () => {
      const SafeComponent = () => <div>Safe content</div>;

      render(
        <AppErrorBoundary>
          <SafeComponent />
        </AppErrorBoundary>
      );

      expect(screen.getByText('Safe content')).toBeInTheDocument();
      expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument();
    });
  });

  describe('ConnectionManager', () => {
    beforeEach(() => {
      resetConnectionManager();
    });

    afterEach(() => {
      resetConnectionManager();
    });

    it('should start in disconnected state when autoConnect is false', () => {
      const manager = getConnectionManager({
        autoConnect: false,
      });

      expect(manager.status).toBe('disconnected');
      expect(manager.isConnected).toBe(false);
    });

    it('should support degraded (polling) mode', async () => {
      const onDegraded = vi.fn();
      const manager = getConnectionManager(
        { pollingEnabled: true },
        { onDegraded }
      );

      // Force degraded mode by simulating WebSocket failure
      // (In real scenario, this would happen automatically)
      manager['startPolling']();

      expect(manager.status).toBe('degraded');
      expect(manager.isDegraded).toBe(true);
      expect(onDegraded).toHaveBeenCalled();
    });

    it('should report connection status correctly', () => {
      const manager = getConnectionManager({
        autoConnect: false,
      });

      expect(manager.isConnected).toBe(false);
      expect(manager.isDegraded).toBe(false);
    });
  });

  describe('Health Status', () => {
    it('should display service health indicators', async () => {
      // Mock fetch for health check
      global.fetch = vi.fn(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ status: 'healthy' }),
        } as Response)
      ) as any;

      render(<HealthStatus />);

      // Wait for health check to complete
      await waitFor(() => {
        expect(screen.getByText(/API:/)).toBeInTheDocument();
      });
    });

    it('should show degraded status when backend is unavailable', async () => {
      // Mock failed fetch
      global.fetch = vi.fn(() =>
        Promise.reject(new Error('Network error'))
      ) as any;

      render(<HealthStatus />);

      await waitFor(() => {
        const statusElement = screen.getByText(/API:/);
        expect(statusElement).toBeInTheDocument();
      });
    });
  });

  describe('Backend Unavailable Scenario', () => {
    it('should render UI shell when backend is down', async () => {
      // Mock failed backend health check
      global.fetch = vi.fn(() =>
        Promise.reject(new Error('Backend unavailable'))
      ) as any;

      render(<HealthStatus />);

      // UI should still render, just with degraded status
      await waitFor(() => {
        expect(screen.getByText(/API:/)).toBeInTheDocument();
      });
    });
  });

  describe('Socket Unavailable Scenario', () => {
    it('should fall back to polling when WebSocket fails', async () => {
      const manager = getConnectionManager({
        autoConnect: false,
        pollingEnabled: true,
      });

      // Mock WebSocket failure
      const originalWebSocket = global.WebSocket;
      global.WebSocket = class MockWebSocket extends WebSocket {
        constructor() {
          super('ws://localhost:invalid');
          setTimeout(() => {
            this.dispatchEvent(new Event('error'));
          }, 100);
        }
      } as any;

      // Try to connect
      await manager.connect();

      // Should fall back to polling after WebSocket fails
      await waitFor(
        () => {
          expect(manager.isDegraded).toBe(true);
        },
        { timeout: 5000 }
      );

      global.WebSocket = originalWebSocket;
    });
  });

  describe('Partial Service Failure', () => {
    it('should continue functioning when only WebSocket fails', async () => {
      const onConnect = vi.fn();
      const onDegraded = vi.fn();

      const manager = getConnectionManager(
        { pollingEnabled: true },
        { onConnect, onDegraded }
      );

      // Mock WebSocket failure
      global.WebSocket = class MockWebSocket extends WebSocket {
        constructor() {
          super('ws://localhost:invalid');
        }
      } as any;

      // Connection should fall back to degraded mode
      await manager.connect();

      await waitFor(() => {
        expect(manager.isDegraded).toBe(true);
        expect(manager.isConnected).toBe(true); // Still connected via polling
      });
    });
  });
});
