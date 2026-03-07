/**
 * React Query Hooks for Workflow Management
 *
 * Provides server state management for workflows and executions.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  type WorkflowGraph,
  type WorkflowExecution,
  type ExecutionGraphResponse,
  type CreateWorkflowRequest,
  type ExecuteWorkflowRequest,
  workflowsApi,
  type WorkflowStatus,
} from "../api";

// ============================================================================
// Query Keys
// ============================================================================

export const workflowKeys = {
  all: ["workflows"] as const,
  lists: () => ["workflows", "list"] as const,
  details: () => ["workflows", "detail"] as const,
  detail: (id: string) => ["workflows", "detail", id] as const,
} as const;

export const executionKeys = {
  all: ["executions"] as const,
  lists: () => ["executions", "list"] as const,
  details: () => ["executions", "detail"] as const,
  detail: (id: string) => ["executions", "detail", id] as const,
  graphs: (id: string) => ["executions", "graph", id] as const,
} as const;

export const templateKeys = {
  all: ["templates"] as const,
} as const;

// ============================================================================
// Workflow Hooks
// ============================================================================

/**
 * Fetch all workflows
 */
export function useWorkflows(params?: {
  status?: WorkflowStatus;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: [...workflowKeys.lists(), params],
    queryFn: () => workflowsApi.getWorkflows(params),
  });
}

/**
 * Fetch a single workflow by ID
 */
export function useWorkflow(graphId: string) {
  return useQuery({
    queryKey: workflowKeys.detail(graphId),
    queryFn: () => workflowsApi.getWorkflow(graphId),
    enabled: !!graphId,
  });
}

/**
 * Create a new workflow
 */
export function useCreateWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CreateWorkflowRequest) =>
      workflowsApi.createWorkflow(request),
    onSuccess: () => {
      // Invalidate workflows list to refetch
      queryClient.invalidateQueries({ queryKey: workflowKeys.lists() });
    },
  });
}

/**
 * Update workflow status (activate/archive)
 */
export function useUpdateWorkflowStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ graphId, status }: { graphId: string; status: WorkflowStatus }) =>
      workflowsApi.updateWorkflowStatus(graphId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.lists() });
      queryClient.invalidateQueries({ queryKey: workflowKeys.details() });
    },
  });
}

/**
 * Delete a workflow
 */
export function useDeleteWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (graphId: string) => workflowsApi.deleteWorkflow(graphId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.lists() });
    },
  });
}

/**
 * Activate a workflow
 */
export function useActivateWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (graphId: string) => workflowsApi.activateWorkflow(graphId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.lists() });
      queryClient.invalidateQueries({ queryKey: workflowKeys.details() });
    },
  });
}

/**
 * Archive a workflow
 */
export function useArchiveWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (graphId: string) => workflowsApi.archiveWorkflow(graphId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.lists() });
      queryClient.invalidateQueries({ queryKey: workflowKeys.details() });
    },
  });
}

// ============================================================================
// Execution Hooks
// ============================================================================

/**
 * Fetch all executions
 */
export function useExecutions(params?: {
  graph_id?: string;
  status?: string;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: [...executionKeys.lists(), params],
    queryFn: () => workflowsApi.getExecutions(params),
    refetchInterval: 5000, // Poll every 5 seconds for live updates
  });
}

/**
 * Fetch a single execution
 */
export function useExecution(executionId: string) {
  return useQuery({
    queryKey: executionKeys.detail(executionId),
    queryFn: () => workflowsApi.getExecution(executionId),
    enabled: !!executionId,
    refetchInterval: (data) => {
      // Poll faster if running, slower if completed
      if (!data) return 5000;
      const status = (data as { status?: string }).status;
      if (status === "running" || status === "pending") {
        return 3000; // Poll every 3 seconds for active executions
      }
      return false; // Stop polling for completed/failed executions
    },
  });
}

/**
 * Fetch execution graph with node statuses (for visualization)
 */
export function useExecutionGraph(
  executionId: string,
  options?: {
    enabled?: boolean;
    refetchInterval?: number | false | ((data: unknown) => number | false | undefined);
  }
) {
  return useQuery({
    queryKey: executionKeys.graphs(executionId),
    queryFn: () => workflowsApi.getExecutionGraph(executionId),
    enabled: !!executionId && (options?.enabled !== false),
    refetchInterval: options?.refetchInterval || ((data: unknown) => {
      // Auto-poll while running
      if (!data) return 3000;
      const graph = data as ExecutionGraphResponse;
      const isRunning = graph.execution.status === "running" || graph.execution.status === "pending";
      return isRunning ? 3000 : false;
    }),
  });
}

/**
 * Execute a workflow
 */
export function useExecuteWorkflow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ graphId, request }: { graphId: string; request?: ExecuteWorkflowRequest }) =>
      workflowsApi.executeWorkflow(graphId, request),
    onSuccess: () => {
      // Invalidate executions list to show new execution
      queryClient.invalidateQueries({ queryKey: executionKeys.lists() });
    },
  });
}

/**
 * Cancel a running execution
 */
export function useCancelExecution() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (executionId: string) => workflowsApi.cancelExecution(executionId),
    onSuccess: (_, executionId) => {
      queryClient.invalidateQueries({ queryKey: executionKeys.detail(executionId) });
      queryClient.invalidateQueries({ queryKey: executionKeys.graphs(executionId) });
      queryClient.invalidateQueries({ queryKey: executionKeys.lists() });
    },
  });
}

// ============================================================================
// Template Hooks
// ============================================================================

/**
 * Fetch workflow templates
 */
export function useWorkflowTemplates() {
  return useQuery({
    queryKey: templateKeys.all,
    queryFn: () => workflowsApi.getWorkflowTemplates(),
  });
}

// ============================================================================
// Health Check Hook
// ============================================================================

/**
 * Check if Task Graph Engine is healthy
 */
export function useWorkflowHealthCheck() {
  return useQuery({
    queryKey: ["workflows", "health"],
    queryFn: () => workflowsApi.healthCheck(),
    refetchInterval: 30000, // Check every 30 seconds
    retry: 3,
  });
}
