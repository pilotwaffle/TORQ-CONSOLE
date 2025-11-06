import { Agent, Message } from '@/lib/types';
import apiService from './api';
import websocketManager from './websocket';

export type AgentType = 'prince_flowers' | 'orchestration' | 'meta' | 'code' | 'debug' | 'docs' | 'test' | 'architecture';

interface AgentActionPayload {
  action: string;
  parameters?: Record<string, any>;
}

interface AgentQueryRequest {
  query: string;
  context?: Record<string, any>;
}

interface AgentWorkflowRequest {
  type: 'code' | 'debug' | 'docs' | 'test' | 'architecture';
  parameters: Record<string, any>;
}

class AgentService {
  // Prince Flowers Agent - Conversational AI
  async queryPrinceFlowers(query: string, sessionId?: string): Promise<Message | null> {
    try {
      const agent = await this.getAgentByType('prince_flowers');
      if (!agent) {
        console.error('Prince Flowers agent not found');
        return null;
      }

      // If no session, create one
      if (!sessionId) {
        const session = await apiService.createSession({
          agentId: agent.id,
          title: 'Prince Flowers Chat',
        });
        sessionId = session?.id;
      }

      if (!sessionId) {
        console.error('Failed to create session for Prince Flowers');
        return null;
      }

      // Send message via WebSocket for real-time response
      websocketManager.sendMessage(sessionId, query, agent.id);

      // Also send via HTTP API for persistence
      const message = await apiService.sendMessage({
        sessionId,
        content: query,
        agentId: agent.id,
      });

      return message;
    } catch (error) {
      console.error('Failed to query Prince Flowers:', error);
      return null;
    }
  }

  // Orchestration Agent - Multi-agent coordination
  async requestOrchestration(
    workflowType: 'single' | 'multi' | 'pipeline' | 'parallel',
    query: string,
    agents?: string[]
  ): Promise<any> {
    try {
      const orchestrator = await this.getAgentByType('orchestration');
      if (!orchestrator) {
        console.error('Orchestration agent not found');
        return null;
      }

      websocketManager.requestAgentAction(orchestrator.id, 'orchestrate', {
        workflowType,
        query,
        agents,
        timestamp: Date.now(),
      });

      return { success: true, workflowType, query };
    } catch (error) {
      console.error('Failed to request orchestration:', error);
      return null;
    }
  }

  // Meta Agent - System-level operations
  async requestMetaAction(action: string, parameters?: Record<string, any>): Promise<any> {
    try {
      const metaAgent = await this.getAgentByType('meta');
      if (!metaAgent) {
        console.error('Meta agent not found');
        return null;
      }

      websocketManager.requestAgentAction(metaAgent.id, action, parameters);

      return { success: true, action, parameters };
    } catch (error) {
      console.error('Failed to request meta action:', error);
      return null;
    }
  }

  // Workflow Agents - Specialized tasks
  async requestCodeGeneration(
    requirements: string,
    language: string,
    sessionId?: string
  ): Promise<Message | null> {
    return this.executeWorkflowAgent('code', {
      requirements,
      language,
      sessionId,
    });
  }

  async requestDebugging(
    code: string,
    errorMessage: string,
    language: string,
    sessionId?: string
  ): Promise<Message | null> {
    return this.executeWorkflowAgent('debug', {
      code,
      errorMessage,
      language,
      sessionId,
    });
  }

  async requestDocumentation(
    code: string,
    docType: 'api' | 'guide' | 'reference',
    sessionId?: string
  ): Promise<Message | null> {
    return this.executeWorkflowAgent('docs', {
      code,
      docType,
      sessionId,
    });
  }

  async requestTesting(
    code: string,
    framework: string,
    language: string,
    sessionId?: string
  ): Promise<Message | null> {
    return this.executeWorkflowAgent('test', {
      code,
      framework,
      language,
      sessionId,
    });
  }

  async requestArchitecture(
    requirements: string,
    systemType: string,
    sessionId?: string
  ): Promise<Message | null> {
    return this.executeWorkflowAgent('architecture', {
      requirements,
      systemType,
      sessionId,
    });
  }

  // Generic workflow agent executor
  private async executeWorkflowAgent(
    agentType: AgentType,
    parameters: Record<string, any>
  ): Promise<Message | null> {
    try {
      const agent = await this.getAgentByType(agentType);
      if (!agent) {
        console.error(`${agentType} agent not found`);
        return null;
      }

      let sessionId = parameters.sessionId;

      // Create session if not provided
      if (!sessionId) {
        const session = await apiService.createSession({
          agentId: agent.id,
          title: `${agentType.charAt(0).toUpperCase() + agentType.slice(1)} Task`,
        });
        sessionId = session?.id;
      }

      if (!sessionId) {
        console.error(`Failed to create session for ${agentType} agent`);
        return null;
      }

      // Send request via WebSocket
      websocketManager.requestAgentAction(agent.id, 'execute', {
        ...parameters,
        sessionId,
      });

      // Return placeholder message (actual response will come via WebSocket)
      return {
        id: `temp-${Date.now()}`,
        agentId: agent.id,
        type: 'system',
        content: `Processing ${agentType} request...`,
        timestamp: Date.now(),
      };
    } catch (error) {
      console.error(`Failed to execute ${agentType} agent:`, error);
      return null;
    }
  }

  // Agent status management
  async updateAgentStatus(agentId: string, status: Agent['status']): Promise<void> {
    try {
      // Update via API
      await apiService.updateAgent(agentId, { status });

      // Update via WebSocket for real-time sync
      websocketManager.updateAgentStatus(agentId, status);
    } catch (error) {
      console.error(`Failed to update agent ${agentId} status:`, error);
    }
  }

  // Agent discovery
  async getAgentByType(type: AgentType): Promise<Agent | null> {
    try {
      const agents = await apiService.getAgents();

      // Map agent types to names
      const typeToName: Record<AgentType, string> = {
        prince_flowers: 'Prince Flowers',
        orchestration: 'Orchestrator',
        meta: 'Meta Agent',
        code: 'Code Generator',
        debug: 'Debugger',
        docs: 'Documentation',
        test: 'Testing',
        architecture: 'Architecture',
      };

      const agentName = typeToName[type];
      return agents.find((a) => a.name === agentName) || null;
    } catch (error) {
      console.error(`Failed to get agent by type ${type}:`, error);
      return null;
    }
  }

  async getAllAgents(): Promise<Agent[]> {
    try {
      return await apiService.getAgents();
    } catch (error) {
      console.error('Failed to get all agents:', error);
      return [];
    }
  }

  // Agent capabilities query
  async getAgentCapabilities(agentId: string): Promise<string[]> {
    try {
      const agent = await apiService.getAgent(agentId);
      return agent?.capabilities || [];
    } catch (error) {
      console.error(`Failed to get capabilities for agent ${agentId}:`, error);
      return [];
    }
  }

  // Query routing
  async routeQuery(query: string): Promise<{ agentId: string; confidence: number } | null> {
    try {
      // Request routing decision from orchestration agent
      const orchestrator = await this.getAgentByType('orchestration');
      if (!orchestrator) {
        console.error('Orchestration agent not available for routing');
        return null;
      }

      websocketManager.requestAgentAction(orchestrator.id, 'route_query', {
        query,
        timestamp: Date.now(),
      });

      // Actual routing result will come via WebSocket event
      return null;
    } catch (error) {
      console.error('Failed to route query:', error);
      return null;
    }
  }
}

// Singleton instance
export const agentService = new AgentService();

export default agentService;
