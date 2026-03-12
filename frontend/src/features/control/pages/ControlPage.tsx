/**
 * Operator Control Surface - Main Control Page
 *
 * Landing page for the Operator Control Surface.
 * Redirects to Mission Portfolio which is the main entry point.
 */

import { Navigate } from "react-router-dom";

export default function ControlPage() {
  // Redirect to mission portfolio as the main control surface view
  return <Navigate to="/control/missions" replace />;
}
