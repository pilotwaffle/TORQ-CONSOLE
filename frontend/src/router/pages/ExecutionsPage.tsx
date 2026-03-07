/**
 * Executions Page Router Wrapper
 */

import { Suspense } from "react";
import { ExecutionsPage as ExecutionsPageComponent } from "../../features/workflows";

export function ExecutionsPage() {
  return (
    <Suspense fallback={<LoadingScreen />}>
      <ExecutionsPageComponent />
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
