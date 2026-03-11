/**
 * WorkspaceInspectorByScope Component
 *
 * Wrapper that provides a scope-based interface to the WorkspaceInspector.
 * This is the primary component for integrating workspaces into TORQ pages.
 *
 * @example
 * ```tsx
 * <WorkspaceInspectorByScope
 *   scopeType="workflow_execution"
 *   scopeId={executionId}
 *   onClose={() => setShowWorkspace(false)}
 * />
 * ```
 */

import { useState } from "react";
import { Brain, X } from "lucide-react";
import { WorkspaceInspector } from "./WorkspaceInspector";
import { useWorkspaceByScope } from "../hooks/useWorkspaceByScope";

type Props = {
  scopeType: "session" | "workflow_execution" | "agent_team";
  scopeId: string;
  onClose?: () => void;
  className?: string;
  /**
   * Whether to show the header with title and close button.
   * @default true
   */
  showHeader?: boolean;
  /**
   * Title to override the default.
   */
  title?: string;
};

export function WorkspaceInspectorByScope({
  scopeType,
  scopeId,
  onClose,
  className,
  showHeader = true,
  title,
}: Props) {
  const { workspace, isLoading, isError, error } = useWorkspaceByScope(
    scopeType,
    scopeId,
    {
      // Auto-create workspace if it doesn't exist
      createIfMissing: true,
      title: title || `Workspace for ${scopeType}:${scopeId}`,
    }
  );

  // Loading state
  if (isLoading) {
    return (
      <div className={className || "p-4"}>
        <div className="flex flex-col items-center justify-center py-8">
          <div className="w-6 h-6 border-2 border-purple-300 border-t-transparent rounded-full animate-spin mb-3" />
          <p className="text-sm text-gray-500">Loading workspace...</p>
        </div>
      </div>
    );
  }

  // Error state (e.g., Supabase not configured)
  if (isError) {
    return (
      <div className={className || "p-4"}>
        <div className="rounded-xl border border-dashed border-gray-300 bg-gray-50 p-6 text-center">
          <Brain className="w-8 h-8 text-gray-300 mx-auto mb-2" />
          <p className="text-sm font-medium text-gray-600">Shared Workspace</p>
          <p className="text-xs text-gray-500 mt-1">
            {error?.message || "Unable to connect to workspace service."}
          </p>
        </div>
      </div>
    );
  }

  // No workspace (shouldn't happen with createIfMissing=true, but handle gracefully)
  if (!workspace) {
    return (
      <div className={className || "p-4"}>
        <div className="rounded-xl border border-dashed border-gray-300 bg-gray-50 p-6 text-center">
          <Brain className="w-8 h-8 text-gray-300 mx-auto mb-2" />
          <p className="text-sm font-medium text-gray-600">Shared Workspace</p>
          <p className="text-xs text-gray-500 mt-1">No workspace found for this context.</p>
        </div>
      </div>
    );
  }

  // Render the workspace inspector
  return (
    <div className={className || "flex flex-col h-full bg-white"}>
      {showHeader && (
        <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between bg-gray-50">
          <div className="flex items-center gap-2">
            <Brain className="w-4 h-4 text-purple-600" />
            <div>
              <h3 className="font-semibold text-gray-900 text-sm">Shared Workspace</h3>
              <p className="text-xs text-gray-500">
                {workspace.title || `${scopeType}:${scopeId}`}
              </p>
            </div>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 p-1 hover:bg-gray-200 rounded"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      )}
      <div className="flex-1 overflow-auto">
        <WorkspaceInspector workspaceId={workspace.workspace_id} className="border-0 rounded-none" />
      </div>
    </div>
  );
}

/**
 * Empty state component to show when workspace is not applicable.
 */
export function WorkspaceEmptyState({ message }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center">
      <Brain className="w-12 h-12 text-gray-300 mb-3" />
      <h3 className="text-sm font-semibold text-gray-600 mb-1">Shared Workspace</h3>
      <p className="text-xs text-gray-500">
        {message || "Workspace will be available when you start a task."}
      </p>
    </div>
  );
}
