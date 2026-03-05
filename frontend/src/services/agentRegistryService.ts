/**
 * Agent Registry Service
 *
 * Loads agents from the backend /api/agent/registry endpoint
 * and provides them to the frontend in the correct format.
 */

import { Agent } from '@/lib/types';

export interface BackendAgent {
  agent_id: string;
  agent_name: string;
  agent_type: string;
  capabilities: string[];
  status: string;
  description?: string;
}

// Map backend agent types to frontend icons
const AGENT_ICONS: Record<string, string> = {
  conversational: '💬',
  workflow: '⚙️',
  research: '🔍',
  orchestration: '🎯',
  code: '💻',
  debug: '🐛',
  docs: '📚',
  test: '🧪',
  architecture: '🏗️',
  core: '🤖',
  enhanced: '✨',
};

// Map backend agent types to frontend types
const AGENT_TYPE_MAP: Record<string, string> = {
  conversational_agent: 'orchestrator',
  workflow_agent: 'code',
  research_agent: 'research',
  orchestration_agent: 'orchestration',
  torq_prince_flowers: 'prince_flowers',
};

class AgentRegistryService {
  private baseUrl: string;

  constructor() {
    // Use relative path for Vercel proxy, or direct Railway URL
    this.baseUrl = '/api/agent';
  }

  /**
   * Load all agents from the backend registry
   */
  async loadAgents(): Promise<Agent[]> {
    try {
      const response = await fetch(`${this.baseUrl}/registry`);
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
        };
      });

      return agents;
    } catch (error) {
      console.error('Failed to load agents from backend:', error);
      // Return empty array - let fallback handle it
      return [];
    }
  }

  /**
   * Get status of a specific agent
   */
  async getAgentStatus(agentId: string): Promise<{ status: string; last_active: string } | null> {
    try {
      const response = await fetch(`${this.baseUrl}/status/${agentId}`);
      if (!response.ok) {
        return null;
      }
      return await response.json();
    } catch (error) {
      console.error(`Failed to get status for agent ${agentId}:`, error);
      return null;
    }
  }

  /**
   * Get orchestration system health
   */
  async getHealth(): Promise<{ status: string; agents_count: number; active_agents: number } | null> {
    try {
      const response = await fetch(`${this.baseUrl}/health`);
      if (!response.ok) {
        return null;
      }
      return await response.json();
    } catch (error) {
      console.error('Failed to get orchestration health:', error);
      return null;
    }
  }

  /**
   * Send a chat message with automatic agent routing
   */
  async chatWithRouting(message: string, sessionId: string, agentId?: string): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          session_id: sessionId,
          agent_id: agentId,
        }),
      });

      if (!response.ok) {
        throw new Error(`Chat request failed: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Chat request failed:', error);
      throw error;
    }
  }

  /**
   * Orchestrate multiple agents for a complex task
   */
  async orchestrate(
    query: string,
    mode: 'single' | 'sequential' | 'parallel' | 'hierarchical' | 'consensus',
    agents?: string[]
  ): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/orchestrate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          mode,
          agents,
        }),
      });

      if (!response.ok) {
        throw new Error(`Orchestration request failed: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Orchestration request failed:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const agentRegistryService = new AgentRegistryService();
export default agentRegistryService;
