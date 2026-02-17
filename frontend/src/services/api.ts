import axios, { AxiosInstance, AxiosError } from 'axios';
import { Agent, ChatSession, Message } from '@/lib/types';

interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

interface CreateSessionRequest {
  agentId: string;
  title?: string;
}

interface SendMessageRequest {
  sessionId: string;
  content: string;
  agentId: string;
}

interface UpdateAgentRequest {
  status?: Agent['status'];
  capabilities?: string[];
}

class ApiService {
  private client: AxiosInstance;

  constructor(baseURL: string = '/api') {
    this.client = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add timestamp to all requests
        config.params = {
          ...config.params,
          _t: Date.now(),
        };
        return config;
      },
      (error) => {
        console.error('Request error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        console.error('Response error:', error);

        if (error.response) {
          // Server responded with error status
          const status = error.response.status;
          const data = error.response.data as any;

          switch (status) {
            case 401:
              console.error('Unauthorized access');
              break;
            case 403:
              console.error('Forbidden access');
              break;
            case 404:
              console.error('Resource not found');
              break;
            case 500:
              console.error('Internal server error');
              break;
            default:
              console.error(`Error ${status}:`, data?.message || error.message);
          }
        } else if (error.request) {
          // Request made but no response
          console.error('No response from server');
        } else {
          // Error in request setup
          console.error('Request setup error:', error.message);
        }

        return Promise.reject(error);
      }
    );
  }

  // Agent endpoints
  async getAgents(): Promise<Agent[]> {
    try {
      const response = await this.client.get<ApiResponse<Agent[]>>('/agents');
      return response.data.data || [];
    } catch (error) {
      console.error('Failed to fetch agents:', error);
      return [];
    }
  }

  async getAgent(agentId: string): Promise<Agent | null> {
    try {
      const response = await this.client.get<ApiResponse<Agent>>(`/agents/${agentId}`);
      return response.data.data || null;
    } catch (error) {
      console.error(`Failed to fetch agent ${agentId}:`, error);
      return null;
    }
  }

  async updateAgent(agentId: string, updates: UpdateAgentRequest): Promise<Agent | null> {
    try {
      const response = await this.client.patch<ApiResponse<Agent>>(
        `/agents/${agentId}`,
        updates
      );
      return response.data.data || null;
    } catch (error) {
      console.error(`Failed to update agent ${agentId}:`, error);
      return null;
    }
  }

  async deleteAgent(agentId: string): Promise<boolean> {
    try {
      const response = await this.client.delete<ApiResponse>(`/agents/${agentId}`);
      return response.data.success;
    } catch (error) {
      console.error(`Failed to delete agent ${agentId}:`, error);
      return false;
    }
  }

  // Session endpoints
  async getSessions(): Promise<ChatSession[]> {
    try {
      const response = await this.client.get<ApiResponse<ChatSession[]>>('/sessions');
      return response.data.data || [];
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
      return [];
    }
  }

  async getSession(sessionId: string): Promise<ChatSession | null> {
    try {
      const response = await this.client.get<ApiResponse<ChatSession>>(
        `/sessions/${sessionId}`
      );
      return response.data.data || null;
    } catch (error) {
      console.error(`Failed to fetch session ${sessionId}:`, error);
      return null;
    }
  }

  async createSession(request: CreateSessionRequest): Promise<ChatSession | null> {
    try {
      const response = await this.client.post<ApiResponse<ChatSession>>(
        '/sessions',
        request
      );
      return response.data.data || null;
    } catch (error) {
      console.error('Failed to create session:', error);
      return null;
    }
  }

  async deleteSession(sessionId: string): Promise<boolean> {
    try {
      const response = await this.client.delete<ApiResponse>(`/sessions/${sessionId}`);
      return response.data.success;
    } catch (error) {
      console.error(`Failed to delete session ${sessionId}:`, error);
      return false;
    }
  }

  async getSessionMessages(sessionId: string): Promise<Message[]> {
    try {
      const response = await this.client.get<ApiResponse<Message[]>>(
        `/sessions/${sessionId}/messages`
      );
      return response.data.data || [];
    } catch (error) {
      console.error(`Failed to fetch messages for session ${sessionId}:`, error);
      return [];
    }
  }

  // Message endpoints
  async sendMessage(request: SendMessageRequest): Promise<Message | null> {
    try {
      const response = await this.client.post<ApiResponse<Message>>(
        '/messages',
        request
      );
      return response.data.data || null;
    } catch (error) {
      console.error('Failed to send message:', error);
      return null;
    }
  }

  async getMessage(messageId: string): Promise<Message | null> {
    try {
      const response = await this.client.get<ApiResponse<Message>>(
        `/messages/${messageId}`
      );
      return response.data.data || null;
    } catch (error) {
      console.error(`Failed to fetch message ${messageId}:`, error);
      return null;
    }
  }

  async deleteMessage(messageId: string): Promise<boolean> {
    try {
      const response = await this.client.delete<ApiResponse>(`/messages/${messageId}`);
      return response.data.success;
    } catch (error) {
      console.error(`Failed to delete message ${messageId}:`, error);
      return false;
    }
  }

  // Health check
  async healthCheck(): Promise<boolean> {
    try {
      // Use fetch directly to hit /health endpoint (not proxied through /api)
      const response = await fetch('/health');
      return response.ok;
    } catch (error) {
      console.error('Health check failed:', error);
      return false;
    }
  }

  // Get base URL for other uses
  getBaseURL(): string {
    return this.client.defaults.baseURL || '';
  }
}

// Singleton instance
export const apiService = new ApiService();

export default apiService;
