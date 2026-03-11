/**
 * useWorkspaceByScope Hook
 *
 * Production-ready hook for getting or creating workspaces by scope.
 * This is the primary integration hook for TORQ pages.
 */

import { useQuery, UseQueryResult } from "@tanstack/react-query";
import { getOrCreateWorkspaceByScope } from "../api/workspaceApi";
import type { Workspace } from "../api/workspaceTypes";

export interface UseWorkspaceByScopeOptions {
  /**
   * Whether to enable the query. Set to false to skip auto-fetching.
   */
  enabled?: boolean;
  /**
   * Whether to auto-create a workspace if none exists.
   * When true, the hook will always return a workspace (new or existing).
   * When false, the hook may return undefined if no workspace exists.
   *
   * @default true
   */
  createIfMissing?: boolean;
  /**
   * Optional title for the workspace if it needs to be created.
   */
  title?: string;
  /**
   * Optional description for the workspace if it needs to be created.
   */
  description?: string;
  /**
   * Optional creator identifier.
   */
  createdBy?: string;
}

export interface UseWorkspaceByScopeResult extends UseQueryResult<Workspace, Error> {
  /**
   * The workspace (if found or created).
   */
  workspace: Workspace | undefined;
  /**
   * Whether a workspace exists for this scope.
   */
  workspaceExists: boolean;
}

/**
 * Get or create a workspace by scope.
 *
 * This hook provides idempotent workspace lookup/creation:
 * - Returns existing workspace if one matches the scope
 * - Creates new workspace if none exists (when createIfMissing=true)
 *
 * @example
 * ```tsx
 * const { workspace, isLoading, isError } = useWorkspaceByScope(
 *   "workflow_execution",
 *   executionId
 * );
 * ```
 */
export function useWorkspaceByScope(
  scopeType: "session" | "workflow_execution" | "agent_team",
  scopeId: string,
  options: UseWorkspaceByScopeOptions = {}
): UseWorkspaceByScopeResult {
  const {
    enabled = true,
    createIfMissing = true,
    title,
    description,
    createdBy,
  } = options;

  const queryKey = ["workspace", "scope", scopeType, scopeId];

  const query = useQuery<Workspace, Error>({
    queryKey,
    queryFn: () =>
      getOrCreateWorkspaceByScope(scopeType, scopeId, {
        title,
        description,
        created_by: createdBy,
      }),
    enabled: enabled && !!scopeId,
    // Cache for 5 minutes since workspaces don't change frequently
    staleTime: 5 * 60 * 1000,
    // Don't refetch on window focus (workspaces are stable)
    refetchOnWindowFocus: false,
  });

  return {
    ...query,
    workspace: query.data,
    workspaceExists: !!query.data,
  };
}
