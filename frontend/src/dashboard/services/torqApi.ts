/**
 * TORQ Console API Service
 * 
 * Endpoints verified from torq_console/api/routes.py source code.
 * Base URL adapts to environment.
 */

import type {
  AgentInfo,
  ChatMessage,
  ChatResponse,
  SessionInfo,
  CreateSessionRequest,
  SystemStatus,
} from '@/types/api';

const API_BASE = import.meta.env.VITE_API_BASE || '';

class TorqApiService {
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
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(error.detail || `API error: ${res.status}`);
    }

    return res.json();
  }

  // === Agent Endpoints (EXISTING in routes.py) ===

  async getAgents(): Promise<AgentInfo[]> {
    return this.request<AgentInfo[]>('/api/agents');
  }

  async getAgent(agentId: string): Promise<AgentInfo> {
    return this.request<AgentInfo>(`/api/agents/${agentId}`);
  }

  async sendMessage(
    agentId: string,
    message: ChatMessage
  ): Promise<ChatResponse> {
    return this.request<ChatResponse>(`/api/agents/${agentId}/chat`, {
      method: 'POST',
      body: JSON.stringify(message),
    });
  }

  // === Session Endpoints (EXISTING in routes.py) ===

  async getSessions(): Promise<SessionInfo[]> {
    return this.request<SessionInfo[]>('/api/sessions');
  }

  async createSession(req: CreateSessionRequest): Promise<SessionInfo> {
    return this.request<SessionInfo>('/api/sessions', {
      method: 'POST',
      body: JSON.stringify(req),
    });
  }

  async getSession(sessionId: string): Promise<SessionInfo> {
    return this.request<SessionInfo>(`/api/sessions/${sessionId}`);
  }

  // === System Endpoints (EXISTING in routes.py) ===

  async getStatus(): Promise<SystemStatus> {
    return this.request<SystemStatus>('/api/status');
  }

  async getHealth(): Promise<{ status: string; service: string }> {
    return this.request<{ status: string; service: string }>('/health');
  }
}

export const torqApi = new TorqApiService();
export default torqApi;
