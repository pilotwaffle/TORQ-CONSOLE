/**
 * TORQ Console Router
 *
 * Phase 4.1: Route-level code splitting for performance optimization
 * Integrated with performance monitoring to track route change times.
 *
 * Defines application routing with React Router.
 * All heavy pages are now lazy-loaded to reduce initial bundle size.
 */

import { createBrowserRouter, Navigate, useLocation } from "react-router-dom";
import { lazy, Suspense, useEffect } from "react";
import { RootLayout } from "../components/RootLayout";
import { PageHeaderSkeleton } from "@/components/loading/Skeleton";
import { performanceMonitor } from "@/lib/performanceMonitor";

// ============================================================================
// Phase 4.1: Lazy-loaded route components
// ============================================================================

// Core chat app is already lazy-loaded in RootLayout

// Workflow routes - split into separate bundles
const WorkflowsPage = lazy(() =>
  import("./pages/WorkflowsPage").then((m) => ({ default: m.WorkflowsPage }))
);

const WorkflowDetailsPage = lazy(() =>
  import("./pages/WorkflowDetailsPage").then((m) => ({ default: m.WorkflowDetailsPage }))
);

const NewWorkflowPage = lazy(() =>
  import("./pages/NewWorkflowPage").then((m) => ({ default: m.NewWorkflowPage }))
);

// Execution routes - split into separate bundles
const ExecutionsPage = lazy(() =>
  import("./pages/ExecutionsPage").then((m) => ({ default: m.ExecutionsPage }))
);

const ExecutionDetailsPage = lazy(() =>
  import("./pages/ExecutionDetailsPage").then((m) => ({ default: m.ExecutionDetailsPage }))
);

// Operator Control Surface routes - lazy-loaded
const ControlPage = lazy(() =>
  import("@/features/control/pages/ControlPage").then((m) => ({ default: m.ControlPage }))
);

const MissionDetailPage = lazy(() =>
  import("@/features/control/pages/MissionDetailPage").then((m) => ({
    default: m.MissionDetailPage,
  }))
);

const MissionPortfolioPage = lazy(() =>
  import("@/features/control/pages/MissionPortfolioPage").then((m) => ({
    default: m.MissionPortfolioPage,
  }))
);

// Distributed Fabric routes - lazy-loaded
const FabricNodesPage = lazy(() =>
  import("@/features/fabric/pages/FabricNodesPage").then((m) => ({
    default: m.FabricNodesPage,
  }))
);

const FabricFailoverPage = lazy(() =>
  import("@/features/fabric/pages/FabricFailoverPage").then((m) => ({
    default: m.FabricFailoverPage,
  }))
);

// ============================================================================
// Route change tracker component
// ============================================================================

function RouteChangeTracker() {
  const location = useLocation();

  useEffect(() => {
    // Mark route change end when location changes
    performanceMonitor.markRouteChangeEnd(location.pathname);

    // Log in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`[Router] Route changed to: ${location.pathname}`);
    }
  }, [location.pathname]);

  return null;
}

// ============================================================================
// Loading fallback component
// ============================================================================

function RouteLoadingFallback() {
  return (
    <div className="flex flex-col h-full">
      <PageHeaderSkeleton />
      <div className="flex-1 px-6 py-4">
        <div className="flex items-center justify-center h-64">
          <div className="flex flex-col items-center gap-3">
            <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
            <p className="text-sm text-gray-500">Loading...</p>
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Suspense wrapper for lazy-loaded routes
// ============================================================================

function LazyRoute({ children }: { children: React.ReactNode }) {
  return (
    <Suspense fallback={<RouteLoadingFallback />}>
      {children}
    </Suspense>
  );
}

// ============================================================================
// Router configuration
// ============================================================================

// Create router with RootLayout as the parent
export const router = createBrowserRouter([
  {
    path: "/",
    element: (
      <>
        <RootLayout />
        <RouteChangeTracker />
      </>
    ),
    children: [
      {
        index: true,
        // Chat route is handled directly by RootLayout (already lazy-loaded)
        element: <div />, // Placeholder - RootLayout renders OriginalApp
      },
      {
        path: "workflows",
        element: (
          <LazyRoute>
            <WorkflowsPage />
          </LazyRoute>
        ),
      },
      {
        path: "workflows/new",
        element: (
          <LazyRoute>
            <NewWorkflowPage />
          </LazyRoute>
        ),
      },
      {
        path: "workflows/:graphId",
        element: (
          <LazyRoute>
            <WorkflowDetailsPage />
          </LazyRoute>
        ),
      },
      {
        path: "executions",
        element: (
          <LazyRoute>
            <ExecutionsPage />
          </LazyRoute>
        ),
      },
      {
        path: "executions/:executionId",
        element: (
          <LazyRoute>
            <ExecutionDetailsPage />
          </LazyRoute>
        ),
      },
      {
        path: "control",
        element: (
          <LazyRoute>
            <ControlPage />
          </LazyRoute>
        ),
      },
      {
        path: "control/missions",
        element: (
          <LazyRoute>
            <MissionPortfolioPage />
          </LazyRoute>
        ),
      },
      {
        path: "control/missions/:missionId",
        element: (
          <LazyRoute>
            <MissionDetailPage />
          </LazyRoute>
        ),
      },
      {
        path: "control/fabric",
        element: (
          <LazyRoute>
            <FabricNodesPage />
          </LazyRoute>
        ),
      },
      {
        path: "control/fabric/failover",
        element: (
          <LazyRoute>
            <FabricFailoverPage />
          </LazyRoute>
        ),
      },
      {
        path: "*",
        element: <Navigate to="/" replace />,
      },
    ],
  },
]);

// ============================================================================
// Navigation wrapper for performance tracking
// ============================================================================

export function navigateWithTracking(path: string) {
  performanceMonitor.markRouteChangeStart();
  return router.navigate(path);
}
