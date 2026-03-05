/**
 * TORQ Agent Registry Service
 *
 * Direct integration with Railway backend.
 * Uses the unified /api/chat endpoint with improved contract.
 */

import { Agent } from '@/lib/types';

// ============================================================================
// Configuration
// ============================================================================

// Direct Railway URL - bypasses Vercel proxy for now
const RAILWAY_URL = 'https://web-production-74ed0.up.railway.app/api';
const VERCEL_PROXY_URL = '/api'; // Falls back to local proxy if available

// Use Railway direct for now (Vercel proxy not working)
const API_BASE_URL = RAILWAY_URL;

// ============================================================================
// Types
// ============================================================================

export interface BackendAgent {
  agent_id: string;
  agent_name: string;
  agent_type: string;
  capabilities: string[];
  status: string;
  description?: string;
  speed?: string;
  best_for?: string[];
  tools?: string[];
}

export interface ChatRequest {
  message: string;
  session_id: string;
  agent_id?: string; // Optional - if null, auto-route
  mode?: 'auto' | 'single' | 'sequential' | 'parallel' | 'consensus' | 'hierarchical';
  context?: Record<string, any>;
}

export interface ChatResponse {
  response: string;
  session_id: string;
  agent_id: string;
  mode_used: string;
  agents_involved: string[];
  routing: {
    selected_agent: string;
    confidence: number;
    reasoning?: string;
  };
  metadata: {
    task_id: string;
    duration_ms: number;
    agent_count: number;
  };
  error?: string;
  duration_ms: number;
}

// ============================================================================
// Agent Icons & Type Mapping
// ============================================================================

const AGENT_ICONS: Record<string, string> = {
  prince_flowers: '👑',
  orchestrator: '🌸',
  code: '💻',
  debug: '🐛',
  docs: '📚',
  test: '🧪',
  architecture: '🏗️',
  research: '🔍',
  workflow: '⚙️',
  core: '🤖',
  enhanced: '✨',
  conversational: '💬',
  orchestration: '🎯',
};

// Map backend agent IDs to frontend agent types
const AGENT_TYPE_MAP: Record<string, string> = {
  torq_prince_flowers: 'prince_flowers',
  conversational_agent: 'orchestrator',
  workflow_agent: 'code',
  research_agent: 'research',
  orchestration_agent: 'orchestration',
};

// ============================================================================
// Service Class
// ============================================================================

class AgentRegistryService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE_URL;
    console.log(`[AgentRegistry] Using backend: ${this.baseUrl}`);
  }

  /**
   * Load all agents from the backend registry
   */
  async loadAgents(): Promise<Agent[]> {
    try {
      // Try the new unified endpoint first
      let response = await fetch(`${this.baseUrl}/chat/agents`);
      if (!response.ok) {
        // Fall back to legacy endpoint
        response = await fetch(`${this.baseUrl}/agent/registry`);
      }

      if (!response.ok) {
        throw new Error(`Failed to load agents: ${response.status}`);
      }

      const backendAgents: BackendAgent[] = await response.json();

      // Transform backend agents to frontend Agent format
      const agents: Agent[] = backendAgents.map((backendAgent) => {
        const frontendType = AGENT_TYPE_MAP[backendAgent.agent_id] || backendAgent.agent_type;

        return {
          id: backendAgent.agent_id,
          name: backendAgent.agent_name,
          status: backendAgent.status === 'active' ? 'idle' : backendAgent.status as Agent['status'],
          type: frontendType as Agent['type'],
          capabilities: backendAgent.capabilities,
          // Store additional metadata for UI display
          metadata: {
            description: backendAgent.description,
            speed: backendAgent.speed,
            best_for: backendAgent.best_for,
            tools: backendAgent.tools,
          } as any,
        };
      });

      console.log(`[AgentRegistry] Loaded ${agents.length} agents from backend`);
      return agents;
    } catch (error) {
      console.error('[AgentRegistry] Failed to load agents from backend:', error);
      // Return empty array - let fallback handle it
      return [];
    }
  }

  /**
   * Get detailed info about a specific agent
   */
  async getAgentDetails(agentId: string): Promise<BackendAgent | null> {
    try {
      const response = await fetch(`${this.baseUrl}/chat/agents/${agentId}`);
      if (!response.ok) {
        return null;
      }
      return await response.json();
    } catch (error) {
      console.error(`[AgentRegistry] Failed to get details for ${agentId}:`, error);
      return null;
    }
  }

  /**
   * Get system health status
   */
  async getHealth(): Promise<{
    status: string;
    agents_count: number;
    active_agents: number;
  } | null> {
    try {
      const response = await fetch(`${this.baseUrl}/chat/health`);
      if (!response.ok) {
        return null;
      }
      return await response.json();
    } catch (error) {
      console.error('[AgentRegistry] Health check failed:', error);
      return null;
    }
  }

  /**
   * Send a chat message using the unified endpoint
   *
   * This is the primary method - supports auto-routing and orchestration
   */
  async chat(request: ChatRequest): Promise<ChatResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: request.message,
          session_id: request.session_id,
          agent_id: request.agent_id || null, // null means auto-route
          mode: request.mode || 'auto',
          context: request.context || {},
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Chat request failed: ${response.status} - ${errorText}`);
      }

      const result: ChatResponse = await response.json();
      console.log(`[AgentRegistry] Chat completed: agent=${result.agent_id}, mode=${result.mode_used}, duration=${result.duration_ms}ms`);
      return result;
    } catch (error) {
      console.error('[AgentRegistry] Chat request failed:', error);
      throw error;
    }
  }

  /**
   * Orchestrate multiple agents (legacy - kept for compatibility)
   */
  async orchestrate(
    query: string,
    mode: 'single' | 'sequential' | 'parallel' = 'single',
    agents?: string[]
  ): Promise<any> {
    // Use the new unified chat endpoint instead
    return this.chat({
      message: query,
      session_id: `orchestrate-${Date.now()}`,
      agent_id: agents?.[0], // For now, use first agent
      mode: mode,
    });
  }
}

// ============================================================================
// Export Singleton
// ============================================================================

export const agentRegistryService = new AgentRegistryService();
export default agentRegistryService;

// ============================================================================
// Type Exports
// ============================================================================

export type { BackendAgent, ChatRequest, ChatResponse };
