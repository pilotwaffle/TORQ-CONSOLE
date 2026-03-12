import type {
  CreateWorkspaceEntryPayload,
  CreateWorkspacePayload,
  GroupedWorkspaceEntries,
  UpdateWorkspaceEntryPayload,
  Workspace,
  WorkspaceEntry,
  WorkspaceSummaryResponse,
} from "./workspaceTypes";

const base = "/api/workspaces";

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "Workspace API request failed");
  }
  return response.json();
}

export async function createWorkspace(payload: CreateWorkspacePayload): Promise<Workspace> {
  return parseJson(await fetch(base, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }));
}

export async function fetchWorkspace(workspaceId: string): Promise<Workspace> {
  return parseJson(await fetch(`${base}/${workspaceId}`));
}

export async function fetchWorkspaceEntries(workspaceId: string): Promise<GroupedWorkspaceEntries> {
  return parseJson(await fetch(`${base}/${workspaceId}/entries?grouped=true`));
}

export async function addWorkspaceEntry(workspaceId: string, payload: CreateWorkspaceEntryPayload): Promise<WorkspaceEntry> {
  return parseJson(await fetch(`${base}/${workspaceId}/entries`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }));
}

export async function updateWorkspaceEntry(workspaceId: string, memoryId: string, payload: UpdateWorkspaceEntryPayload): Promise<WorkspaceEntry> {
  return parseJson(await fetch(`${base}/${workspaceId}/entries/${memoryId}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }));
}

export async function resolveWorkspaceEntry(workspaceId: string, memoryId: string): Promise<WorkspaceEntry> {
  return parseJson(await fetch(`${base}/${workspaceId}/entries/${memoryId}/resolve`, { method: "POST" }));
}

export async function summarizeWorkspace(workspaceId: string, model?: string): Promise<WorkspaceSummaryResponse> {
  return parseJson(await fetch(`${base}/${workspaceId}/summarize`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ model }) }));
}

/**
 * Get or create a workspace by scope.
 * This is the primary integration endpoint for TORQ pages.
 *
 * @param scopeType - Type of scope (session, workflow_execution, agent_team)
 * @param scopeId - Scope identifier (e.g., execution ID, session ID)
 * @param options - Optional title, description, created_by
 * @returns The workspace (existing or newly created)
 */
export async function getOrCreateWorkspaceByScope(
  scopeType: "session" | "workflow_execution" | "agent_team",
  scopeId: string,
  options?: {
    title?: string;
    description?: string;
    created_by?: string;
  }
): Promise<Workspace> {
  return parseJson(
    await fetch(`${base}/get-or-create`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        scope_type: scopeType,
        scope_id: scopeId,
        ...options,
      }),
    })
  );
}

/**
 * Get a workspace by scope. Returns 404 if not found.
 *
 * Unlike getOrCreateWorkspaceByScope, this will NOT create a new workspace.
 */
export async function fetchWorkspaceByScope(
  scopeType: "session" | "workflow_execution" | "agent_team",
  scopeId: string
): Promise<Workspace> {
  const params = new URLSearchParams({
    scope_type: scopeType,
    scope_id: scopeId,
  });
  return parseJson(await fetch(`${base}/by-scope?${params.toString()}`));
}
