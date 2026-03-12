/**
 * React Query Hooks for Workflow Management
 *
 * Provides server state management for workflows and executions.
 * Phase 3: Enhanced with toast notifications for user feedback.
 * Phase 4.1: Optimized with specific cache timings per query type.
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
import { useToast } from "@/components/toasts";
import { QUERY_CONFIG, CACHE_TIMING } from "@/lib/reactQueryConfig";

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
 * Phase 4.1: Optimized cache configuration
 */
export function useWorkflows(params?: {
  status?: WorkflowStatus;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: [...workflowKeys.lists(), params],
    queryFn: () => workflowsApi.getWorkflows(params),
    ...QUERY_CONFIG.workflows,
  });
}

/**
 * Fetch a single workflow by ID
 * Phase 4.1: Optimized cache configuration
 */
export function useWorkflow(graphId: string) {
  return useQuery({
    queryKey: workflowKeys.detail(graphId),
    queryFn: () => workflowsApi.getWorkflow(graphId),
    enabled: !!graphId,
    ...QUERY_CONFIG.workflow,
  });
}

/**
 * Create a new workflow
 */
export function useCreateWorkflow() {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation({
    mutationFn: (request: CreateWorkflowRequest) =>
      workflowsApi.createWorkflow(request),
    onSuccess: (data) => {
      // Invalidate workflows list to refetch
      queryClient.invalidateQueries({ queryKey: workflowKeys.lists() });
      toast.success(`Workflow "${data.name}" created successfully`);
    },
    onError: (error: Error) => {
      toast.error(`Failed to create workflow: ${error.message}`);
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
  const toast = useToast();

  return useMutation({
    mutationFn: (graphId: string) => workflowsApi.deleteWorkflow(graphId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.lists() });
      toast.success('Workflow deleted successfully');
    },
    onError: (error: Error) => {
      toast.error(`Failed to delete workflow: ${error.message}`);
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
  const toast = useToast();

  return useMutation({
    mutationFn: (graphId: string) => workflowsApi.archiveWorkflow(graphId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workflowKeys.lists() });
      queryClient.invalidateQueries({ queryKey: workflowKeys.details() });
      toast.success('Workflow archived successfully');
    },
    onError: (error: Error) => {
      toast.error(`Failed to archive workflow: ${error.message}`);
    },
  });
}

// ============================================================================
// Execution Hooks
// ============================================================================

/**
 * Fetch all executions
 * Phase 4.1: Optimized with configured polling interval
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
    ...QUERY_CONFIG.executions,
  });
}

/**
 * Fetch a single execution
 * Phase 4.1: Adaptive polling based on execution status
 */
export function useExecution(executionId: string) {
  return useQuery({
    queryKey: executionKeys.detail(executionId),
    queryFn: () => workflowsApi.getExecution(executionId),
    enabled: !!executionId,
    refetchInterval: (data) => {
      // Poll faster if running, slower if completed
      if (!data) return QUERY_CONFIG.executions.refetchInterval;
      const status = (data as { status?: string }).status;
      if (status === "running" || status === "pending") {
        return 3000; // Poll every 3 seconds for active executions
      }
      return false; // Stop polling for completed/failed executions
    },
    ...QUERY_CONFIG.execution,
  });
}

/**
 * Fetch execution graph with node statuses (for visualization)
 * Phase 4.1: Adaptive polling based on execution status
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
      if (!data) return QUERY_CONFIG.executionGraph.staleTime;
      const graph = data as ExecutionGraphResponse;
      const isRunning = graph.execution.status === "running" || graph.execution.status === "pending";
      return isRunning
        ? CACHE_TIMING.EXECUTION_GRAPH_ACTIVE_STALE_TIME // 1 second for active
        : false; // Stop polling when complete
    }),
    ...QUERY_CONFIG.executionGraph,
  });
}

/**
 * Execute a workflow
 */
export function useExecuteWorkflow() {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation({
    mutationFn: ({ graphId, request }: { graphId: string; request?: ExecuteWorkflowRequest }) =>
      workflowsApi.executeWorkflow(graphId, request),
    onSuccess: (data) => {
      // Invalidate executions list to show new execution
      queryClient.invalidateQueries({ queryKey: executionKeys.lists() });
      toast.success(`Workflow execution started: ${data.execution_id}`, {
        title: 'Execution Started',
        duration: 3000,
      });
    },
    onError: (error: Error) => {
      toast.error(`Failed to start workflow execution: ${error.message}`, {
        duration: 8000,
      });
    },
  });
}

/**
 * Cancel a running execution
 */
export function useCancelExecution() {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation({
    mutationFn: (executionId: string) => workflowsApi.cancelExecution(executionId),
    onSuccess: (_, executionId) => {
      queryClient.invalidateQueries({ queryKey: executionKeys.detail(executionId) });
      queryClient.invalidateQueries({ queryKey: executionKeys.graphs(executionId) });
      queryClient.invalidateQueries({ queryKey: executionKeys.lists() });
      toast.info('Workflow execution canceled', {
        duration: 3000,
      });
    },
    onError: (error: Error) => {
      toast.error(`Failed to cancel execution: ${error.message}`, {
        duration: 8000,
      });
    },
  });
}

// ============================================================================
// Template Hooks
// ============================================================================

/**
 * Fetch workflow templates
 * Phase 4.1: Optimized for long cache (templates rarely change)
 */
export function useWorkflowTemplates() {
  return useQuery({
    queryKey: templateKeys.all,
    queryFn: () => workflowsApi.getWorkflowTemplates(),
    ...QUERY_CONFIG.templates,
  });
}

// ============================================================================
// Health Check Hook
// ============================================================================

/**
 * Check if Task Graph Engine is healthy
 * Phase 4.1: Optimized health check configuration
 */
export function useWorkflowHealthCheck() {
  return useQuery({
    queryKey: ["workflows", "health"],
    queryFn: () => workflowsApi.healthCheck(),
    ...QUERY_CONFIG.health,
  });
}
