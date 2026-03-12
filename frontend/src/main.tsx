import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import AppRouter from './AppRouter';
import { AppErrorBoundary } from './components/errors';
import { HealthStatus } from './components/layout/HealthStatus';
import { createOptimizedQueryClient } from './lib/reactQueryConfig';
import './index.css';

/**
 * Phase 4.1: Performance Optimization
 *
 * Using optimized React Query configuration with:
 * - Specific cache timings per data type
 * - Intelligent retry logic
 * - Configurable refetch behavior
 */
const queryClient = createOptimizedQueryClient();

/**
 * Phase 1 - Platform Reliability Hardening
 * Phase 4.1 - Performance Optimization
 *
 * The app is now wrapped in an AppErrorBoundary to prevent blank-screen failures.
 * HealthStatus banner shows service availability without blocking the UI.
 * React Query is configured with optimized cache strategies.
 */
function AppWithProviders() {
  return (
    <>
      <HealthStatus />
      <AppRouter />
    </>
  );
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <AppErrorBoundary>
        <AppWithProviders />
      </AppErrorBoundary>
      <ReactQueryDevtools
        initialIsOpen={false}
        buttonPosition="bottom-left"
      />
    </QueryClientProvider>
  </React.StrictMode>
);
