import React, { useState, useEffect } from "react";
import { ChatWindow } from "../../components/chat/ChatWindow";
import { AgentSidebar } from "../../components/layout/AgentSidebar";
import { TopNav } from "../../components/layout/TopNav";
import { CommandPalette } from "../../components/command/CommandPalette";
import { CoordinationPanel } from "../../components/coordination/CoordinationPanel";
import { useAgentStore } from "../../stores/agentStore";
import { useCoordinationStore } from "../../stores/coordinationStore";
import { useKeyboardShortcuts, SHORTCUTS } from "../../hooks/useKeyboardShortcuts";
import type { Agent, ChatSession } from "../../lib/types";
import agentRegistryService from "../../services/agentRegistryService";

function ChatPageWrapper() {
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const { setAgents, addSession, setActiveSession, setActiveAgent, setWorkspace } = useAgentStore();
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
        const { activeAgentId, addSession, setActiveSession } = useAgentStore.getState();
        if (activeAgentId) {
          const newSession: ChatSession = {
            id: `session_${Date.now()}`,
            title: "New Chat",
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
    // Load agents
    const princeFlowers: Agent = {
      id: "torq_prince_flowers",
      name: "Prince Flowers",
      status: "idle",
      type: "prince_flowers",
      capabilities: ["AI Search", "Web Research", "Agent Orchestration", "Code Generation"],
    };

    const fallbackAgents: Agent[] = [
      princeFlowers,
      {
        id: "conversational_agent",
        name: "Conversational Agent",
        status: "idle",
        type: "orchestrator",
        capabilities: ["Conversation", "Memory", "Learning"],
      },
      {
        id: "workflow_agent",
        name: "Workflow Agent",
        status: "idle",
        type: "code",
        capabilities: ["Code Generation", "Debugging", "Testing", "Architecture"],
      },
      {
        id: "research_agent",
        name: "Research Agent",
        status: "idle",
        type: "research",
        capabilities: ["Research", "Analysis", "Web Search"],
      },
      {
        id: "orchestration_agent",
        name: "Orchestration Agent",
        status: "idle",
        type: "orchestration",
        capabilities: ["Orchestration", "Coordination"],
      },
    ];

    const loadBackendAgents = async () => {
      try {
        const backendAgents = await agentRegistryService.loadAgents();
        if (backendAgents.length > 0) {
          const hasPrinceFlowers = backendAgents.some((a) => a.id === "torq_prince_flowers");
          if (!hasPrinceFlowers) {
            backendAgents.unshift(princeFlowers);
          }
          setAgents(backendAgents);
        } else {
          setAgents(fallbackAgents);
        }
      } catch (error) {
        console.error("Failed to load backend agents, using fallback:", error);
        setAgents(fallbackAgents);
      }
    };

    loadBackendAgents();

    const { sessions } = useAgentStore.getState();
    if (sessions.length === 0) {
      const initialSession: ChatSession = {
        id: `session_${Date.now()}`,
        title: "Chat with Prince Flowers",
        agentId: "torq_prince_flowers",
        messages: [],
        createdAt: Date.now(),
        updatedAt: Date.now(),
      };
      addSession(initialSession);
      setActiveSession(initialSession.id);
      setActiveAgent("torq_prince_flowers");
    }

    setWorkspace({
      path: "/workspace",
      name: "TORQ Console",
      activeSessions: [],
    });
  }, [setAgents, addSession, setActiveSession, setActiveAgent, setWorkspace]);

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden">
      <TopNav />
      <div className={`flex-1 flex overflow-hidden transition-all duration-300 ${hasActiveWorkflows ? "mb-14" : "mb-0"}`}>
        <AgentSidebar />
        <ChatWindow />
      </div>
      <CommandPalette isOpen={isCommandPaletteOpen} onClose={() => setIsCommandPaletteOpen(false)} />
      <CoordinationPanel />
    </div>
  );
}

export function ChatPage() {
  return (
    <ChatPageWrapper />
  );
}
