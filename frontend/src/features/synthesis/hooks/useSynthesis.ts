/**
 * React Query hooks for Reasoning Synthesis Engine
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  generateSynthesis,
  getLatestSynthesis,
  listSyntheses,
  regenerateSynthesis,
  type GenerateSynthesisRequest,
  type SynthesisType,
  type WorkspaceSynthesis,
} from "../api";

export function useWorkspaceSyntheses(workspaceId: string) {
  return useQuery<WorkspaceSynthesis[], Error>({
    queryKey: ["syntheses", workspaceId],
    queryFn: () => listSyntheses(workspaceId),
    enabled: !!workspaceId,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

export function useLatestSynthesis(
  workspaceId: string,
  type: SynthesisType,
  options: { enabled?: boolean } = {}
) {
  return useQuery<WorkspaceSynthesis, Error>({
    queryKey: ["synthesis", "latest", workspaceId, type],
    queryFn: () => getLatestSynthesis(workspaceId, type),
    enabled: !!workspaceId && (options.enabled ?? true),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useGenerateSynthesis() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ workspaceId, options }: { workspaceId: string; options?: GenerateSynthesisRequest }) =>
      generateSynthesis(workspaceId, options),
    onSuccess: (data, variables) => {
      // Invalidate syntheses list for this workspace
      queryClient.invalidateQueries({ queryKey: ["syntheses", variables.workspaceId] });
      // Invalidate specific synthesis types
      if (variables.options?.types) {
        for (const type of variables.options.types) {
          queryClient.invalidateQueries({
            queryKey: ["synthesis", "latest", variables.workspaceId, type],
          });
        }
      }
    },
  });
}

export function useRegenerateSynthesis() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ workspaceId, options }: { workspaceId: string; options?: GenerateSynthesisRequest }) =>
      regenerateSynthesis(workspaceId, options),
    onSuccess: (data, variables) => {
      // Invalidate syntheses list for this workspace
      queryClient.invalidateQueries({ queryKey: ["syntheses", variables.workspaceId] });
      // Invalidate specific synthesis types
      if (variables.options?.types) {
        for (const type of variables.options.types) {
          queryClient.invalidateQueries({
            queryKey: ["synthesis", "latest", variables.workspaceId, type],
          });
        }
      }
    },
  });
}

/**
 * Hook to generate synthesis on mount if not exists
 */
export function useLazySynthesis(
  workspaceId: string,
  type: SynthesisType,
  options: { autoGenerate?: boolean; generateOptions?: GenerateSynthesisRequest } = {}
) {
  const { data: synthesis, isLoading, error } = useLatestSynthesis(workspaceId, type, {
    enabled: !options.autoGenerate,
  });

  const generateMutation = useGenerateSynthesis();

  const generate = () => {
    generateMutation.mutate({
      workspaceId,
      options: { ...options.generateOptions, types: [type] },
    });
  };

  return {
    synthesis,
    isLoading,
    error,
    generate,
    isGenerating: generateMutation.isPending,
  };
}
