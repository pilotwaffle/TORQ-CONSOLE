/**
 * Workflow Builder API Client
 *
 * Communicates with Task Graph Engine endpoints via Vercel proxy.
 */

import type {
  WorkflowGraph,
  WorkflowExecution,
  ExecutionGraphResponse,
  CreateWorkflowRequest,
  CreateWorkflowResponse,
  ExecuteWorkflowRequest,
  ExecuteWorkflowResponse,
  WorkflowTemplatesResponse,
  WorkflowStatus,
} from "./workflowTypes";

const API_BASE = import.meta.env.VITE_API_BASE || "";

/**
 * Extract the error message from various error response shapes
 */
function getErrorMessage(error: unknown): string {
  if (typeof error === "string") return error;
  if (error && typeof error === "object" && "message" in error) {
    return String(error.message);
  }
  if (error && typeof error === "object" && "detail" in error) {
    return String(error.detail);
  }
  return "An unknown error occurred";
}

class WorkflowsApiService {
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

  // ============================================================================
  // Workflow Graph Endpoints
  // ============================================================================

  /**
   * List all workflow graphs
   * GET /api/tasks/graphs
   */
  async getWorkflows(params?: {
    status?: WorkflowStatus;
    limit?: number;
    offset?: number;
  }): Promise<WorkflowGraph[]> {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set("status", params.status);
    if (params?.limit) searchParams.set("limit", params.limit.toString());
    if (params?.offset) searchParams.set("offset", params.offset.toString());

    const query = searchParams.toString();
    return this.request<WorkflowGraph[]>(`/api/tasks/graphs${query ? `?${query}` : ""}`);
  }

  /**
   * Get a specific workflow graph
   * GET /api/tasks/graphs/{graph_id}
   */
  async getWorkflow(graphId: string): Promise<CreateWorkflowResponse> {
    return this.request<CreateWorkflowResponse>(`/api/tasks/graphs/${graphId}`);
  }

  /**
   * Create a new workflow graph
   * POST /api/tasks/graphs
   */
  async createWorkflow(request: CreateWorkflowRequest): Promise<CreateWorkflowResponse> {
    return this.request<CreateWorkflowResponse>("/api/tasks/graphs", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  /**
   * Update a workflow graph (not directly exposed, but useful for status changes)
   */
  async updateWorkflowStatus(
    graphId: string,
    status: WorkflowStatus
  ): Promise<{ activated?: boolean; archived?: boolean }> {
    const endpoint = status === "active" ? "activate" : "archive";
    return this.request<{ activated?: boolean; archived?: boolean }>(
      `/api/tasks/graphs/${graphId}/${endpoint}`,
      { method: "POST" }
    );
  }

  /**
   * Delete a workflow graph
   * DELETE /api/tasks/graphs/{graph_id}
   */
  async deleteWorkflow(graphId: string): Promise<{ deleted: boolean }> {
    return this.request<{ deleted: boolean }>(`/api/tasks/graphs/${graphId}`, {
      method: "DELETE",
    });
  }

  /**
   * Activate a workflow graph
   * POST /api/tasks/graphs/{graph_id}/activate
   */
  async activateWorkflow(graphId: string): Promise<{ activated: boolean }> {
    return this.request<{ activated: boolean }>(
      `/api/tasks/graphs/${graphId}/activate`,
      { method: "POST" }
    );
  }

  /**
   * Archive a workflow graph
   * POST /api/tasks/graphs/{graph_id}/archive
   */
  async archiveWorkflow(graphId: string): Promise<{ archived: boolean }> {
    return this.request<{ archived: boolean }>(
      `/api/tasks/graphs/${graphId}/archive`,
      { method: "POST" }
    );
  }

  // ============================================================================
  // Execution Endpoints
  // ============================================================================

  /**
   * Execute a workflow graph
   * POST /api/tasks/graphs/{graph_id}/execute
   */
  async executeWorkflow(
    graphId: string,
    request?: ExecuteWorkflowRequest
  ): Promise<ExecuteWorkflowResponse> {
    return this.request<ExecuteWorkflowResponse>(
      `/api/tasks/graphs/${graphId}/execute`,
      {
        method: "POST",
        body: JSON.stringify(request || {}),
      }
    );
  }

  /**
   * List workflow executions
   * GET /api/tasks/executions
   */
  async getExecutions(params?: {
    graph_id?: string;
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<WorkflowExecution[]> {
    const searchParams = new URLSearchParams();
    if (params?.graph_id) searchParams.set("graph_id", params.graph_id);
    if (params?.status) searchParams.set("status", params.status);
    if (params?.limit) searchParams.set("limit", params.limit.toString());
    if (params?.offset) searchParams.set("offset", params.offset.toString());

    const query = searchParams.toString();
    return this.request<WorkflowExecution[]>(
      `/api/tasks/executions${query ? `?${query}` : ""}`
    );
  }

  /**
   * Get execution details
   * GET /api/tasks/executions/{execution_id}
   */
  async getExecution(executionId: string): Promise<ExecuteWorkflowResponse> {
    return this.request<ExecuteWorkflowResponse>(
      `/api/tasks/executions/${executionId}`
    );
  }

  /**
   * Cancel a running execution
   * POST /api/tasks/executions/{execution_id}/cancel
   */
  async cancelExecution(executionId: string): Promise<{ cancelled: boolean }> {
    return this.request<{ cancelled: boolean }>(
      `/api/tasks/executions/${executionId}/cancel`,
      { method: "POST" }
    );
  }

  /**
   * Get execution graph with node statuses
   * GET /api/tasks/executions/{execution_id}/graph
   */
  async getExecutionGraph(executionId: string): Promise<ExecutionGraphResponse> {
    return this.request<ExecutionGraphResponse>(
      `/api/tasks/executions/${executionId}/graph`
    );
  }

  /**
   * Get node results for an execution
   * GET /api/tasks/executions/{execution_id}/nodes
   */
  async getExecutionNodes(executionId: string): Promise<Array<{
    result_id: string;
    execution_id: string;
    node_id: string;
    status: string;
    output: Record<string, unknown>;
    error_message?: string;
    started_at?: string;
    completed_at?: string;
    duration_ms?: number;
    attempt?: number;
  }>> {
    return this.request(`/api/tasks/executions/${executionId}/nodes`);
  }

  // ============================================================================
  // Template Endpoints
  // ============================================================================

  /**
   * Get workflow example templates
   * GET /api/tasks/examples
   */
  async getWorkflowTemplates(): Promise<WorkflowTemplatesResponse> {
    return this.request<WorkflowTemplatesResponse>("/api/tasks/examples");
  }

  // ============================================================================
  // Health Check
  // ============================================================================

  /**
   * Check if Task Graph Engine is available
   */
  async healthCheck(): Promise<{ healthy: boolean; message?: string }> {
    try {
      await this.getWorkflows({ limit: 1 });
      return { healthy: true };
    } catch (error) {
      return { healthy: false, message: getErrorMessage(error) };
    }
  }
}

// Export singleton instance
export const workflowsApi = new WorkflowsApiService();
export default workflowsApi;
