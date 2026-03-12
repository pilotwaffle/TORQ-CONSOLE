export type WorkspaceScopeType = "session" | "workflow_execution" | "agent_team";
export type WorkspaceEntryType = "fact" | "hypothesis" | "question" | "decision" | "artifact" | "note";
export type WorkspaceEntryStatus = "active" | "resolved" | "revised" | "deprecated";

/** Importance levels for workspace entries - used for learning signal prioritization */
export type EntryImportance = "low" | "medium" | "high" | "critical";

/** Provenance source for workspace entries - used for learning signal attribution */
export type EntrySourceType = "agent" | "tool" | "user" | "system" | "synthesis";

export interface Workspace {
  workspace_id: string;
  scope_type: WorkspaceScopeType;
  scope_id: string;
  tenant_id: string;
  title?: string;
  description?: string;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface WorkspaceEntry {
  memory_id: string;
  workspace_id: string;
  tenant_id: string;
  entry_type: WorkspaceEntryType;
  content: Record<string, unknown>;
  source_agent?: string;
  confidence: number;
  status: WorkspaceEntryStatus;
  /** Entry importance - used for filtering and learning signal prioritization */
  importance: EntryImportance;
  /** Entry provenance source - used for learning signal attribution */
  source_type: EntrySourceType;
  /** Optional reference to task execution that generated this entry */
  execution_id?: string;
  created_at: string;
  updated_at: string;
}

export interface GroupedWorkspaceEntries {
  workspace_id: string;
  facts: WorkspaceEntry[];
  hypotheses: WorkspaceEntry[];
  questions: WorkspaceEntry[];
  decisions: WorkspaceEntry[];
  artifacts: WorkspaceEntry[];
  notes: WorkspaceEntry[];
}

export interface CreateWorkspacePayload {
  scope_type: WorkspaceScopeType;
  scope_id: string;
  title?: string;
  description?: string;
  created_by?: string;
  tenant_id?: string;
}

export interface CreateWorkspaceEntryPayload {
  entry_type: WorkspaceEntryType;
  content: Record<string, unknown>;
  source_agent?: string;
  confidence?: number;
  status?: WorkspaceEntryStatus;
  importance?: EntryImportance;
  source_type?: EntrySourceType;
  execution_id?: string;
}

export interface UpdateWorkspaceEntryPayload {
  content?: Record<string, unknown>;
  confidence?: number;
  status?: WorkspaceEntryStatus;
  importance?: EntryImportance;
}

export interface WorkspaceSummaryResponse {
  workspace_id: string;
  summary: string;
  facts_count: number;
  hypotheses_count: number;
  questions_count: number;
  decisions_count: number;
  generated_at: string;
}

export interface GetOrCreateWorkspaceRequest {
  scope_type: WorkspaceScopeType;
  scope_id: string;
  title?: string;
  description?: string;
  created_by?: string;
}
