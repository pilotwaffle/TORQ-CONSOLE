/**
 * Workflow Builder Types
 *
 * Type definitions for Task Graph Engine integration.
 */

// ============================================================================
// Enums
// ============================================================================

export type WorkflowStatus = "draft" | "active" | "archived";
export type ExecutionStatus = "pending" | "running" | "completed" | "failed" | "canceled";
export type NodeStatus = "pending" | "running" | "completed" | "failed" | "skipped";
export type NodeType = "agent" | "tool" | "api_call" | "analysis" | "condition" | "parallel" | "sequential";
export type TriggerType = "manual" | "webhook" | "timer" | "event";

// ============================================================================
// Core Types
// ============================================================================

export interface WorkflowGraph {
  graph_id: string;
  name: string;
  description?: string;
  status: WorkflowStatus;
  version: number;
  parent_graph_id?: string;
  config?: Record<string, unknown>;
  limits?: WorkflowLimits;
  created_at: string;
  updated_at?: string;
}

export interface WorkflowNode {
  node_id: string;
  node_key: string;
  name: string;
  node_type: NodeType;
  agent_id?: string;
  tool_name?: string;
  parameters?: Record<string, unknown>;
  retry_policy?: RetryPolicy;
  timeout_seconds?: number;
  depends_on?: string[]; // Array of node_ids
  position_x?: number;
  position_y?: number;
}

export interface WorkflowEdge {
  source_node_id: string;
  target_node_id: string;
  condition?: Record<string, unknown>;
}

export interface WorkflowLimits {
  max_nodes_per_graph?: number;
  max_runtime_seconds?: number;
  max_parallel_nodes?: number;
  max_output_size_bytes?: number;
}

export interface RetryPolicy {
  max_retries?: number;
  retry_delay_ms?: number;
  backoff_multiplier?: number;
  failure_strategy?: "retry" | "skip" | "reroute" | "fail";
}

// ============================================================================
// Execution Types
// ============================================================================

export interface WorkflowExecution {
  execution_id: string;
  graph_id: string;
  graph_name?: string;
  status: ExecutionStatus;
  started_at?: string;
  completed_at?: string;
  total_duration_ms?: number;
  nodes_completed?: number;
  nodes_failed?: number;
  output?: Record<string, unknown>;
  error_message?: string;
  trace_id?: string;
  created_at?: string;
}

export interface ExecutionNodeResult {
  result_id: string;
  execution_id: string;
  node_id: string;
  node_key: string;
  name: string;
  status: NodeStatus;
  output?: Record<string, unknown>;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  duration_ms?: number;
  retry_count?: number;
  agent_id?: string;
}

export interface ExecutionGraphResponse {
  execution: {
    execution_id: string;
    status: ExecutionStatus;
    started_at?: string;
    completed_at?: string;
    total_duration_ms?: number;
    nodes_completed: number;
    nodes_failed: number;
    trace_id?: string;
  };
  graph: {
    graph_id: string;
    name: string;
    description?: string;
    status: WorkflowStatus;
  };
  nodes: Array<{
    node_id: string;
    node_key: string;
    name: string;
    node_type: NodeType;
    agent_id?: string;
    parameters?: Record<string, unknown>;
    depends_on?: string[];
    position_x?: number;
    position_y?: number;
    runtime: {
      status: NodeStatus;
      started_at?: string;
      completed_at?: string;
      duration_ms?: number;
      attempt?: number;
      error_message?: string;
      output_size_bytes?: number;
    };
  }>;
  edges: WorkflowEdge[];
  summary: {
    total_nodes: number;
    completed: number;
    failed: number;
    running: number;
    pending: number;
  };
}

// ============================================================================
// Template Types
// ============================================================================

export interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  category?: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  config?: Record<string, unknown>;
}

// ============================================================================
// Request/Response Types
// ============================================================================

export interface CreateWorkflowRequest {
  name: string;
  description?: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  config?: Record<string, unknown>;
}

export interface ExecuteWorkflowRequest {
  trigger_type?: TriggerType;
  trigger_source?: string;
  input_data?: Record<string, unknown>;
}

export interface CreateWorkflowResponse extends WorkflowGraph {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}

export interface ExecuteWorkflowResponse extends WorkflowExecution {
  nodes_completed: number;
  nodes_failed: number;
}

// ============================================================================
// API Response Wrappers
// ============================================================================

export interface WorkflowListResponse {
  workflows: WorkflowGraph[];
  total: number;
}

export interface ExecutionListResponse {
  executions: WorkflowExecution[];
  total: number;
}

export interface WorkflowTemplatesResponse {
  examples: WorkflowTemplate[];
}
