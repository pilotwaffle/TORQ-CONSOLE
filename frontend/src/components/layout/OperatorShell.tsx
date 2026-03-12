/**
 * TORQ Console - Operator Shell Layout
 *
 * Phase 1 - Operator UI Foundation
 *
 * Provides the complete app shell with:
 * - Top navigation bar with TORQ logo
 * - Sidebar navigation
 * - Main content area
 * - Responsive layout
 */

import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { useState } from "react";

// ============================================================================
// Types
// ============================================================================

interface NavItem {
  path: string;
  label: string;
  icon: string;
  description?: string;
}

// ============================================================================
// TORQ Logo Component
// ============================================================================

export function TORQLogo({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const sizeClasses = {
    sm: "w-6 h-6 text-xs",
    md: "w-8 h-8 text-sm",
    lg: "w-10 h-10 text-base",
  };

  return (
    <div
      className={`${sizeClasses[size]} bg-gradient-to-br from-blue-600 to-blue-800 rounded-lg flex items-center justify-center text-white font-bold shadow-sm`}
      data-testid="torq-logo"
    >
      T
    </div>
  );
}

// ============================================================================
// Sidebar Navigation Component
// ============================================================================

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

function Sidebar({ isOpen, onClose }: SidebarProps) {
  const location = useLocation();
  const navigate = useNavigate();

  const navItems: NavItem[] = [
    { path: "/", label: "Chat", icon: "💬", description: "AI Assistant" },
    { path: "/workflows", label: "Workflows", icon: "⚙️", description: "Workflow Management" },
    { path: "/executions", label: "Executions", icon: "🚀", description: "Execution History" },
    { path: "/control", label: "Control", icon: "🎛️", description: "Operator Control" },
    { path: "/control/missions", label: "Missions", icon: "📋", description: "Mission Portfolio" },
    { path: "/control/fabric", label: "Fabric", icon: "🌐", description: "Distributed Fabric" },
  ];

  return (
    <>
      {/* Backdrop on mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
          data-testid="sidebar-backdrop"
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed lg:static inset-y-0 left-0 z-50
          w-64 bg-white border-r border-gray-200
          transform transition-transform duration-300 ease-in-out
          ${isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
        `}
        data-testid="sidebar"
      >
        <div className="flex flex-col h-full">
          {/* Sidebar Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200">
            <div className="flex items-center gap-2">
              <TORQLogo size="sm" />
              <span className="font-semibold text-gray-900">TORQ Console</span>
            </div>
            <button
              onClick={onClose}
              className="lg:hidden p-1 rounded hover:bg-gray-100"
              aria-label="Close sidebar"
              data-testid="sidebar-close"
            >
              ✕
            </button>
          </div>

          {/* Navigation */}
          <nav
            className="flex-1 overflow-y-auto p-4"
            role="navigation"
            aria-label="Main navigation"
            data-testid="main-navigation"
          >
            <ul className="space-y-1">
              {navItems.map((item) => {
                const isActive = location.pathname === item.path ||
                  (item.path !== "/" && location.pathname.startsWith(item.path));

                return (
                  <li key={item.path}>
                    <button
                      onClick={() => {
                        navigate(item.path);
                        onClose();
                      }}
                      className={`
                        w-full flex items-center gap-3 px-3 py-2 rounded-lg
                        text-sm font-medium transition-colors
                        ${isActive
                          ? "bg-blue-50 text-blue-700"
                          : "text-gray-700 hover:bg-gray-100"
                        }
                      `}
                      aria-current={isActive ? "page" : undefined}
                    >
                      <span className="text-lg" aria-hidden="true">
                        {item.icon}
                      </span>
                      <span>{item.label}</span>
                    </button>
                  </li>
                );
              })}
            </ul>

            {/* Section: Distributed Fabric */}
            <div className="mt-8">
              <h3 className="px-3 mb-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Distributed Fabric
              </h3>
              <ul className="space-y-1">
                <li>
                  <button
                    onClick={() => {
                      navigate("/control/fabric");
                      onClose();
                    }}
                    className={`
                      w-full flex items-center gap-3 px-3 py-2 rounded-lg
                      text-sm font-medium transition-colors
                      ${location.pathname.startsWith("/control/fabric")
                        ? "bg-blue-50 text-blue-700"
                        : "text-gray-700 hover:bg-gray-100"
                      }
                    `}
                  >
                    <span className="text-lg" aria-hidden="true">🌐</span>
                    <span>Nodes</span>
                  </button>
                </li>
                <li>
                  <button
                    onClick={() => {
                      navigate("/control/fabric/failover");
                      onClose();
                    }}
                    className={`
                      w-full flex items-center gap-3 px-3 py-2 rounded-lg
                      text-sm font-medium transition-colors
                      ${location.pathname.includes("failover")
                        ? "bg-blue-50 text-blue-700"
                        : "text-gray-700 hover:bg-gray-100"
                      }
                    `}
                  >
                    <span className="text-lg" aria-hidden="true">🔄</span>
                    <span>Failover</span>
                  </button>
                </li>
              </ul>
            </div>
          </nav>

          {/* Sidebar Footer */}
          <div className="p-4 border-t border-gray-200">
            <div className="text-xs text-gray-500">
              <div className="flex items-center justify-between">
                <span>Status</span>
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 bg-green-500 rounded-full" data-testid="health-status-indicator" />
                  <span>Online</span>
                </span>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}

// ============================================================================
// Top Navigation Component
// ============================================================================

interface TopNavProps {
  onMenuClick: () => void;
}

function TopNav({ onMenuClick }: TopNavProps) {
  const location = useLocation();

  // Get current page title
  const getPageTitle = () => {
    if (location.pathname === "/" || location.pathname === "") return "Chat";
    if (location.pathname.startsWith("/workflows")) return "Workflows";
    if (location.pathname.startsWith("/executions")) return "Executions";
    if (location.pathname.startsWith("/control/missions")) return "Mission Portfolio";
    if (location.pathname.startsWith("/control/fabric")) return "Distributed Fabric";
    if (location.pathname.startsWith("/control")) return "Operator Control";
    return "TORQ Console";
  };

  return (
    <header
      className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-white"
      data-testid="top-navigation"
    >
      <div className="flex items-center gap-4">
        {/* Mobile menu button */}
        <button
          onClick={onMenuClick}
          className="lg:hidden p-2 rounded hover:bg-gray-100"
          aria-label="Open menu"
          data-testid="mobile-menu-button"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 6h16M4 12h16M4 18h16"
            />
          </svg>
        </button>

        {/* Logo and title */}
        <div className="flex items-center gap-3">
          <TORQLogo size="sm" />
          <div>
            <h1 className="font-semibold text-gray-900" data-testid="page-title">
              {getPageTitle()}
            </h1>
          </div>
        </div>
      </div>

      {/* Right side controls */}
      <div className="flex items-center gap-3">
        <button
          className="p-2 rounded hover:bg-gray-100 text-gray-600"
          aria-label="Settings"
          data-testid="settings-button"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
            />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
            />
          </svg>
        </button>
      </div>
    </header>
  );
}

// ============================================================================
// Main Operator Shell Component
// ============================================================================

export function OperatorShell() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  // Don't show shell on chat route (uses original App layout)
  const isChatRoute = location.pathname === "/" || location.pathname === "";
  if (isChatRoute) {
    return <Outlet />;
  }

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden">
      <TopNav onMenuClick={() => setSidebarOpen(true)} />

      <div className="flex-1 flex overflow-hidden">
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

        {/* Main content area */}
        <main
          className="flex-1 overflow-y-auto bg-gray-50"
          data-testid="main-content"
        >
          <Outlet />
        </main>
      </div>
    </div>
  );
}
