/**
 * TORQ Console Main App Router
 *
 * Root component that provides the Router.
 * This is a simple wrapper to avoid circular imports.
 */

import { RouterProvider } from "react-router-dom";
import { router } from "./router";

function AppWithRouter() {
  return <RouterProvider router={router} />;
}

export default AppWithRouter;
