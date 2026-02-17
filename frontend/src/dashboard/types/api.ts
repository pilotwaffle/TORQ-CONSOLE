/**
 * TORQ Console Dashboard API Types
 * 
 * These TypeScript interfaces match the VERIFIED Pydantic models
 * from torq_console/api/routes.py (source-code verified).
 */

// === Agent Types ===

export interface AgentInfo {
  id: string;
  name: string;
  description: string;
  capabilities: string[];
  status: string;
  metrics: Record<string, any>;
}

// === Chat Types ===

export interface ChatMessage {
  message: string;
  context?: Record<string, any>;
  mode?: OrchestrationMode;
}

export interface ChatResponse {
  response: string;
  agent_id: string;
  timestamp: string;
  metadata: ChatMetadata;
}

export interface ChatMetadata {
  mode: string;
  routing_decision: RoutingDecision | null;
  success: boolean;
  agent_used?: string;
  capabilities?: string[];
  used_tools?: boolean;
  [key: string]: any;
}

export interface RoutingDecision {
  primary_agent: string;
  capabilities: string[];
}

// === Session Types ===

export interface SessionInfo {
  session_id: string;
  created_at: string;
  agent_id: string;
  message_count: number;
  status: string;
}

export interface CreateSessionRequest {
  agent_id: string;
  metadata?: Record<string, any>;
}

// === System Types ===

export interface SystemStatus {
  status: string;
  agents_active: number;
  sessions_active: number;
  uptime_seconds: number;
  metrics: Record<string, any>;
}

// === Enums (matching Python backend) ===

export type OrchestrationMode = 'single_agent' | 'multi_agent' | 'pipeline' | 'parallel';

export type ReasoningMode = 'direct' | 'research' | 'analysis' | 'composition' | 'meta_planning';

// === UI Message Type (frontend-only, extends backend response) ===

export interface UIMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
  routing?: RoutingDecision | null;
  metadata?: ChatMetadata;
  isLoading?: boolean;
}

export interface UISession {
  id: string;
  title: string;
  agentId: string;
  messages: UIMessage[];
  createdAt: number;
  updatedAt: number;
  mode: OrchestrationMode;
}
