import React, { useEffect, useState } from 'react';
import { TopNav } from '@/components/layout/TopNav';
import { AgentSidebar } from '@/components/layout/AgentSidebar';
import { ChatWindow } from '@/components/chat/ChatWindow';
import { CommandPalette } from '@/components/command/CommandPalette';
import { CoordinationPanel } from '@/components/coordination/CoordinationPanel';
import { useAgentStore } from '@/stores/agentStore';
import { useCoordinationStore } from '@/stores/coordinationStore';
import { useKeyboardShortcuts, SHORTCUTS } from '@/hooks/useKeyboardShortcuts';
import type { Agent, ChatSession } from '@/lib/types';

function App() {
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);

  const { setAgents, addSession, setActiveSession, setWorkspace, setConnectionStatus } =
    useAgentStore();

  const hasActiveWorkflows = useCoordinationStore((state) => state.hasActiveWorkflows());

  // Global keyboard shortcuts
  useKeyboardShortcuts([
    {
      ...SHORTCUTS.COMMAND_PALETTE,
      callback: () => setIsCommandPaletteOpen(true),
    },
    {
      ...SHORTCUTS.NEW_CHAT,
      callback: () => {
        // Create new chat with current agent
        const { activeAgentId, addSession, setActiveSession } = useAgentStore.getState();
        if (activeAgentId) {
          const newSession: ChatSession = {
            id: `session_${Date.now()}`,
            title: 'New Chat',
            agentId: activeAgentId,
            messages: [],
            createdAt: Date.now(),
            updatedAt: Date.now(),
          };
          addSession(newSession);
          setActiveSession(newSession.id);
        }
      },
    },
  ]);

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
      <div
        className={`
          flex-1 flex overflow-hidden transition-all duration-300
          ${hasActiveWorkflows ? 'mb-14' : 'mb-0'}
        `}
      >
        <AgentSidebar />
        <ChatWindow />
      </div>

      {/* Command Palette */}
      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
      />

      {/* Multi-Agent Coordination Panel */}
      <CoordinationPanel />
    </div>
  );
}

export default App;
