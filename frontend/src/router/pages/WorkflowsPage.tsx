/**
 * Workflows Page Router Wrapper
 */

import { Suspense } from "react";
import { WorkflowsPage as WorkflowsPageComponent } from "../../features/workflows";

export function WorkflowsPage() {
  return (
    <Suspense fallback={<LoadingScreen />}>
      <WorkflowsPageComponent />
    </Suspense>
  );
}

function LoadingScreen() {
  return (
    <div className="h-screen flex items-center justify-center">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900" />
    </div>
  );
}
