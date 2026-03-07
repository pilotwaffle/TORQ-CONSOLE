/**
 * useDraftWorkflow Hook
 *
 * React Query hook for AI workflow generation.
 */

import { useMutation, useQuery } from "@tanstack/react-query";
import { workflowPlannerApi, type WorkflowPlannerRequest, type WorkflowPlannerResponse } from "@workflows/api/workflowPlannerApi";

/**
 * Generate a workflow draft from a natural language prompt
 */
export function useDraftWorkflow() {
  return useMutation({
    mutationFn: (request: WorkflowPlannerRequest) =>
      workflowPlannerApi.generateDraft(request),
  });
}

/**
 * Check workflow planner health
 */
export function useWorkflowPlannerHealth() {
  return useQuery({
    queryKey: ["workflow-planner", "health"],
    queryFn: () => workflowPlannerApi.healthCheck(),
    refetchInterval: 60000, // Check every minute
    retry: false,
  });
}
