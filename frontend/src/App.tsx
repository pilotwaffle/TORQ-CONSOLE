import { useEffect, useState } from 'react';
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

  const { setAgents, addSession, setActiveSession, setActiveAgent, setWorkspace, setConnectionStatus } =
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
    // The agentStore already initializes WebSocket on creation (see agentStore.ts line 220-224).
    // We ensure Prince Flowers and fallback agents are always available.

    const princeFlowers: Agent = {
      id: 'prince_flowers',
      name: 'Prince Flowers',
      status: 'idle',
      type: 'orchestrator',
      capabilities: ['AI Search', 'Web Research', 'Agent Orchestration', 'Code Generation'],
    };

    const fallbackAgents: Agent[] = [
      princeFlowers,
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

    // After 3 seconds, merge backend agents with fallback agents
    // This ensures Prince Flowers is always present, even if backend doesn't return him
    const fallbackTimer = setTimeout(() => {
      const { agents: backendAgents } = useAgentStore.getState();

      // Create a map of existing agents to avoid duplicates
      const existingAgentMap = new Map(backendAgents.map((a) => [a.id, a]));

      // Add fallback agents for any missing ones (with Prince Flowers taking precedence)
      fallbackAgents.forEach((fallbackAgent) => {
        if (!existingAgentMap.has(fallbackAgent.id)) {
          existingAgentMap.set(fallbackAgent.id, fallbackAgent);
        }
      });

      // Convert back to array, ensuring Prince Flowers is first
      const mergedAgents = Array.from(existingAgentMap.values());
      const princeFlowersAgent = mergedAgents.find((a) => a.id === 'prince_flowers');
      const otherAgents = mergedAgents.filter((a) => a.id !== 'prince_flowers');

      if (princeFlowersAgent) {
        setAgents([princeFlowersAgent, ...otherAgents]);
      } else {
        setAgents(mergedAgents);
      }
    }, 3000);

    // Create initial session immediately with Prince Flowers if none exists
    const { sessions } = useAgentStore.getState();

    if (sessions.length === 0) {
      const initialSession: ChatSession = {
        id: `session_${Date.now()}`,
        title: 'Chat with Prince Flowers',
        agentId: 'prince_flowers',
        messages: [],
        createdAt: Date.now(),
        updatedAt: Date.now(),
      };
      addSession(initialSession);
      setActiveSession(initialSession.id);
      // Set active agent to Prince Flowers
      setActiveAgent('prince_flowers');
    }

    setWorkspace({
      path: '/workspace',
      name: 'TORQ Console',
      activeSessions: [],
    });

    return () => {
      clearTimeout(fallbackTimer);
    };
  }, [setAgents, addSession, setActiveSession, setActiveAgent, setWorkspace, setConnectionStatus]);

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
