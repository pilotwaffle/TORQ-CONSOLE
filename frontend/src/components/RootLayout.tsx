/**
 * TORQ Console Root Layout
 *
 * Layout component that conditionally shows navigation and renders
 * the appropriate content for chat vs non-chat routes.
 *
 * This file is separate from AppRouter.tsx to avoid circular imports.
 */

import { Outlet, useLocation } from "react-router-dom";
import { lazy, Suspense } from "react";

// Lazy load the original App for chat route
const OriginalApp = lazy(() =>
  import("../App").then((m) => ({ default: m.default }))
);

// Root layout that conditionally shows nav bar and uses Outlet for nested routes
export function RootLayout() {
  const location = useLocation();
  const isChatRoute = location.pathname === "/" || location.pathname === "";

  // Chat route doesn't get the nav bar, other routes do
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

  // Non-chat routes get nav bar + outlet for nested content
  return (
    <div className="h-screen w-screen flex flex-col">
      {/* Top navigation bar */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-white">
        <div className="flex items-center gap-6">
          <a href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gray-900 rounded flex items-center justify-center text-white font-bold text-sm">
              T
            </div>
            <span className="font-semibold text-gray-900">TORQ Console</span>
          </a>
          <nav className="flex items-center gap-4 text-sm">
            <a href="/" className="text-gray-600 hover:text-gray-900">
              Chat
            </a>
            <a href="/workflows" className="text-gray-600 hover:text-gray-900">
              Workflows
            </a>
            <a href="/executions" className="text-gray-600 hover:text-gray-900">
              Executions
            </a>
          </nav>
        </div>
      </div>
      {/* Nested route content */}
      <Outlet />
    </div>
  );
}
