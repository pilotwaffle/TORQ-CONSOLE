import { useEffect, useState } from 'react';
import { TopNav } from '@/components/layout/TopNav';
import { AgentSidebar } from '@/components/layout/AgentSidebar';
import { ChatWindow } from '@/components/chat/ChatWindow';
import { CommandPalette } from '@/components/command/CommandPalette';
import { CoordinationPanel } from '@/components/coordination/CoordinationPanel';
import { OnboardingWelcome, useOnboarding } from '@/components/onboarding';
import { ToastContainer } from '@/components/toasts';
import { useAgentStore } from '@/stores/agentStore';
import { useCoordinationStore } from '@/stores/coordinationStore';
import { useKeyboardShortcuts, SHORTCUTS } from '@/hooks/useKeyboardShortcuts';
import type { Agent, ChatSession } from '@/lib/types';
import agentRegistryService from '@/services/agentRegistryService';

function App() {
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const { hasSeenOnboarding, markOnboardingComplete } = useOnboarding();

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
    // Load agents from backend registry
    // The agentStore already initializes WebSocket on creation (see agentStore.ts line 220-224).

    const princeFlowers: Agent = {
      id: 'torq_prince_flowers',
      name: 'Prince Flowers',
      status: 'idle',
      type: 'prince_flowers',
      capabilities: ['AI Search', 'Web Research', 'Agent Orchestration', 'Code Generation'],
    };

    // Fallback agents in case backend is unavailable
    const fallbackAgents: Agent[] = [
      princeFlowers,
      {
        id: 'conversational_agent',
        name: 'Conversational Agent',
        status: 'idle',
        type: 'orchestrator',
        capabilities: ['Conversation', 'Memory', 'Learning'],
      },
      {
        id: 'workflow_agent',
        name: 'Workflow Agent',
        status: 'idle',
        type: 'code',
        capabilities: ['Code Generation', 'Debugging', 'Testing', 'Architecture'],
      },
      {
        id: 'research_agent',
        name: 'Research Agent',
        status: 'idle',
        type: 'research',
        capabilities: ['Research', 'Analysis', 'Web Search'],
      },
      {
        id: 'orchestration_agent',
        name: 'Orchestration Agent',
        status: 'idle',
        type: 'orchestration',
        capabilities: ['Orchestration', 'Coordination'],
      },
    ];

    // Try to load agents from backend
    const loadBackendAgents = async () => {
      try {
        const backendAgents = await agentRegistryService.loadAgents();

        if (backendAgents.length > 0) {
          console.log(`Loaded ${backendAgents.length} agents from backend registry`);

          // Ensure Prince Flowers is present
          const hasPrinceFlowers = backendAgents.some((a) =>
            a.id === 'torq_prince_flowers' || a.id === 'prince_flowers'
          );

          if (!hasPrinceFlowers) {
            backendAgents.unshift(princeFlowers);
          }

          setAgents(backendAgents);
        } else {
          // Use fallback agents
          console.log('Backend returned no agents, using fallback');
          setAgents(fallbackAgents);
        }
      } catch (error) {
        console.error('Failed to load backend agents, using fallback:', error);
        setAgents(fallbackAgents);
      }
    };

    // Load immediately and also after 3 seconds as fallback
    loadBackendAgents();

    // After 3 seconds, if we still have no agents, ensure fallback is loaded
    const fallbackTimer = setTimeout(() => {
      const { agents } = useAgentStore.getState();
      if (agents.length === 0) {
        console.log('No agents loaded after 3s, using fallback');
        setAgents(fallbackAgents);
      }
    }, 3000);

    // Create initial session immediately with Prince Flowers if none exists
    const { sessions } = useAgentStore.getState();

    if (sessions.length === 0) {
      const initialSession: ChatSession = {
        id: `session_${Date.now()}`,
        title: 'Chat with Prince Flowers',
        agentId: 'torq_prince_flowers',  // Use backend ID
        messages: [],
        createdAt: Date.now(),
        updatedAt: Date.now(),
      };
      addSession(initialSession);
      setActiveSession(initialSession.id);
      // Set active agent to Prince Flowers (backend ID)
      setActiveAgent('torq_prince_flowers');
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
      {/* Phase 3: Onboarding for first-time users */}
      {!hasSeenOnboarding && (
        <OnboardingWelcome onComplete={markOnboardingComplete} />
      )}

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

      {/* Phase 3: Toast Notifications */}
      <ToastContainer />
    </div>
  );
}

export default App;
