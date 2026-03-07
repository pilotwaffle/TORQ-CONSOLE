/**
 * TORQ Console Router
 *
 * Defines application routing with React Router.
 *
 * Uses a root layout that conditionally shows navigation and renders
 * the appropriate content for each route.
 */

import { createBrowserRouter, Navigate } from "react-router-dom";
import { RootLayout } from "../components/RootLayout";

// Import pages directly (not lazy) for simpler build
import { WorkflowsPage } from "./pages/WorkflowsPage";
import { ExecutionsPage } from "./pages/ExecutionsPage";
import { WorkflowDetailsPage } from "./pages/WorkflowDetailsPage";
import { ExecutionDetailsPage } from "./pages/ExecutionDetailsPage";
import { NewWorkflowPage } from "./pages/NewWorkflowPage";

// Create router with RootLayout as the parent
export const router = createBrowserRouter([
  {
    path: "/",
    element: <RootLayout />,
    children: [
      {
        index: true,
        // Chat route is handled directly by RootLayout
        element: <div />, // Placeholder - RootLayout renders OriginalApp
      },
      {
        path: "workflows",
        element: <WorkflowsPage />,
      },
      {
        path: "workflows/new",
        element: <NewWorkflowPage />,
      },
      {
        path: "workflows/:graphId",
        element: <WorkflowDetailsPage />,
      },
      {
        path: "executions",
        element: <ExecutionsPage />,
      },
      {
        path: "executions/:executionId",
        element: <ExecutionDetailsPage />,
      },
      {
        path: "*",
        element: <Navigate to="/" replace />,
      },
    ],
  },
]);
