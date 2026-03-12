/**
 * TORQ Console Root Layout
 *
 * Layout component that:
 * - Shows original App for chat route (/)
 * - Shows OperatorShell for all other routes (with sidebar navigation)
 *
 * This file is separate from AppRouter.tsx to avoid circular imports.
 */

import { Outlet, useLocation } from "react-router-dom";
import { lazy, Suspense } from "react";
import { OperatorShell } from "./layout/OperatorShell";

// Lazy load the original App for chat route
const OriginalApp = lazy(() =>
  import("../App").then((m) => ({ default: m.default }))
);

// Root layout that conditionally shows nav bar and uses Outlet for nested routes
export function RootLayout() {
  const location = useLocation();
  const isChatRoute = location.pathname === "/" || location.pathname === "";

  // Chat route gets the original app layout (without operator shell)
  if (isChatRoute) {
    return (
      <Suspense
        fallback={
          <div className="flex items-center justify-center h-screen">
            Loading TORQ Console...
          </div>
        }
      >
        <OriginalApp />
      </Suspense>
    );
  }

  // Non-chat routes get the operator shell with sidebar navigation
  return <OperatorShell />;
}
