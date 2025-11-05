import React, { useEffect } from 'react';
import { TopNav } from '@/components/layout/TopNav';
import { AgentSidebar } from '@/components/layout/AgentSidebar';
import { ChatWindow } from '@/components/chat/ChatWindow';
import { useAgentStore } from '@/stores/agentStore';
import type { Agent, ChatSession } from '@/lib/types';

function App() {
  const { setAgents, addSession, setActiveSession, setWorkspace, setConnectionStatus } =
    useAgentStore();

  useEffect(() => {
    // Initialize with mock data for demo purposes
    // This will be replaced with actual WebSocket/API integration
    const mockAgents: Agent[] = [
      {
        id: 'agent_code',
        name: 'Code Generator',
        status: 'idle',
        type: 'code',
        capabilities: ['Python', 'TypeScript', 'React'],
      },
      {
        id: 'agent_debug',
        name: 'Debug Assistant',
        status: 'idle',
        type: 'debug',
        capabilities: ['Error Analysis', 'Root Cause', 'Fixes'],
      },
      {
        id: 'agent_docs',
        name: 'Documentation',
        status: 'idle',
        type: 'docs',
        capabilities: ['API Docs', 'Guides', 'References'],
      },
      {
        id: 'agent_test',
        name: 'Test Engineer',
        status: 'idle',
        type: 'test',
        capabilities: ['Unit Tests', 'Integration', 'E2E'],
      },
      {
        id: 'agent_arch',
        name: 'Architecture',
        status: 'idle',
        type: 'architecture',
        capabilities: ['System Design', 'Patterns', 'Trade-offs'],
      },
    ];

    setAgents(mockAgents);

    // Create initial session
    const initialSession: ChatSession = {
      id: 'session_1',
      title: 'New Chat',
      agentId: 'agent_code',
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };

    addSession(initialSession);
    setActiveSession(initialSession.id);

    setWorkspace({
      path: '/workspace',
      name: 'TORQ Console',
      activeSessions: [initialSession],
    });

    // Simulate connection (will be replaced with actual WebSocket)
    setTimeout(() => {
      setConnectionStatus(true);
    }, 500);

    // TODO: Replace with actual WebSocket connection
    // const ws = new WebSocket('ws://localhost:8899/socket.io');
    // ws.onopen = () => setConnectionStatus(true);
    // ws.onclose = () => setConnectionStatus(false);
    // ws.onmessage = (event) => handleWebSocketMessage(event.data);
  }, [setAgents, addSession, setActiveSession, setWorkspace, setConnectionStatus]);

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden">
      <TopNav />
      <div className="flex-1 flex overflow-hidden">
        <AgentSidebar />
        <ChatWindow />
      </div>
    </div>
  );
}

export default App;
