/**
 * Workflow Planning Copilot API Client
 *
 * Communicates with the AI workflow generation endpoint.
 */

import type {
  WorkflowNode,
  WorkflowEdge,
  CreateWorkflowRequest,
} from "./workflowTypes";

/**
 * Request to generate a workflow draft from a prompt
 */
export interface WorkflowPlannerRequest {
  prompt: string;
  session_id?: string;
  tenant_id?: string;
}

/**
 * A single node in a generated workflow draft
 */
export interface DraftNode {
  node_key: string;
  name: string;
  node_type: "agent";
  agent_id: string;
  depends_on: string[];
  parameters: Record<string, unknown>;
  timeout_seconds: number;
  retry_policy: {
    max_retries: number;
    retry_delay_ms: number;
    failure_strategy: string;
  };
}

/**
 * A directed edge between two nodes
 */
export interface DraftEdge {
  source_node_key: string;
  target_node_key: string;
}

/**
 * A complete generated workflow draft
 */
export interface WorkflowDraft {
  name: string;
  description: string;
  rationale?: string;
  nodes: DraftNode[];
  edges: DraftEdge[];
  limits: {
    max_nodes: number;
    max_runtime_seconds: number;
    max_parallel_nodes: number;
  };
}

/**
 * Response from workflow draft generation
 */
export interface WorkflowPlannerResponse {
  success: boolean;
  draft?: WorkflowDraft;
  error_code?: string;
  error_message?: string;
  generation_time_ms?: number;
}

const API_BASE = import.meta.env.VITE_API_BASE || "";

/**
 * Workflow Planner API Service
 */
class WorkflowPlannerApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    path: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const res = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      ...options,
    });

    if (!res.ok) {
      let errorMessage = `API error: ${res.status}`;
      try {
        const errorData = await res.json();
        errorMessage = errorData.detail || errorData.message || errorMessage;
      } catch {
        errorMessage = res.statusText || errorMessage;
      }
      throw new Error(errorMessage);
    }

    return res.json();
  }

  /**
   * Generate a workflow draft from a natural language prompt
   * POST /api/workflow-planner/draft
   */
  async generateDraft(request: WorkflowPlannerRequest): Promise<WorkflowPlannerResponse> {
    return this.request<WorkflowPlannerResponse>("/api/workflow-planner/draft", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  /**
   * Check if the workflow planner service is healthy
   */
  async healthCheck(): Promise<{ status: string; module: string; anthropic_configured: string }> {
    return this.request<{ status: string; module: string; anthropic_configured: string }>("/api/workflow-planner/health");
  }

  /**
   * Convert a WorkflowDraft to CreateWorkflowRequest
   */
  draftToCreateRequest(draft: WorkflowDraft): CreateWorkflowRequest {
    // Convert draft nodes to workflow nodes
    const nodes: WorkflowNode[] = draft.nodes.map((node, index) => ({
      node_id: node.node_key,
      node_key: node.node_key,
      name: node.name,
      node_type: node.node_type,
      agent_id: node.agent_id,
      depends_on: node.depends_on,
      parameters: node.parameters,
      timeout_seconds: node.timeout_seconds,
      retry_policy: node.retry_policy,
      position_x: 100,
      position_y: index * 150,
    }));

    // Convert draft edges to workflow edges
    const edges: WorkflowEdge[] = draft.edges.map((edge) => ({
      edge_id: `${edge.source_node_key}-${edge.target_node_key}`,
      source_node_id: edge.source_node_key,
      target_node_id: edge.target_node_key,
    }));

    return {
      name: draft.name,
      description: draft.description,
      nodes,
      edges,
      limits: draft.limits,
    };
  }
}

// Export singleton instance
export const workflowPlannerApi = new WorkflowPlannerApiService();
export default workflowPlannerApi;
