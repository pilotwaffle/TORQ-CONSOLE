import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  addWorkspaceEntry,
  createWorkspace,
  fetchWorkspace,
  fetchWorkspaceEntries,
  resolveWorkspaceEntry,
  summarizeWorkspace,
  updateWorkspaceEntry,
} from "../api/workspaceApi";
import type { CreateWorkspaceEntryPayload, CreateWorkspacePayload, UpdateWorkspaceEntryPayload } from "../api/workspaceTypes";

export function useWorkspace(workspaceId?: string) {
  return useQuery({
    queryKey: ["workspace", workspaceId],
    queryFn: () => fetchWorkspace(workspaceId!),
    enabled: !!workspaceId,
  });
}

export function useWorkspaceEntries(workspaceId?: string) {
  return useQuery({
    queryKey: ["workspaceEntries", workspaceId],
    queryFn: () => fetchWorkspaceEntries(workspaceId!),
    enabled: !!workspaceId,
  });
}

export function useCreateWorkspace() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateWorkspacePayload) => createWorkspace(payload),
    onSuccess: (workspace) => {
      qc.invalidateQueries({ queryKey: ["workspace", workspace.workspace_id] });
    },
  });
}

export function useAddWorkspaceEntry(workspaceId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateWorkspaceEntryPayload) => addWorkspaceEntry(workspaceId, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["workspaceEntries", workspaceId] });
    },
  });
}

export function useUpdateWorkspaceEntry(workspaceId: string, memoryId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: UpdateWorkspaceEntryPayload) => updateWorkspaceEntry(workspaceId, memoryId, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["workspaceEntries", workspaceId] });
    },
  });
}

export function useResolveWorkspaceEntry(workspaceId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (memoryId: string) => resolveWorkspaceEntry(workspaceId, memoryId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["workspaceEntries", workspaceId] });
    },
  });
}

export function useWorkspaceSummary(workspaceId?: string) {
  return useMutation({
    mutationFn: (model?: string) => summarizeWorkspace(workspaceId!, model),
  });
}
