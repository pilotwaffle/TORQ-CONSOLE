/**
 * Operator Control Surface - Mission Detail Page
 *
 * Main mission detail view with tabbed interface for:
 * Graph, Workstreams, Events, and Handoffs.
 */

import { useState } from "react";
import { useParams, Navigate } from "react-router-dom";
import { MissionDetailHeader } from "../components/MissionDetailHeader";
import { MissionGraphPanel } from "../components/MissionGraphPanel";
import { WorkstreamHealthPanel } from "../components/WorkstreamHealthPanel";
import { MissionEventStream } from "../components/MissionEventStream";
import { HandoffList } from "../components/HandoffList";
import { MissionReplay } from "../components/MissionReplay";

// ============================================================================
// Tab Type
// ============================================================================

type TabType = "graph" | "workstreams" | "events" | "handoffs" | "replay";

// ============================================================================
// Tab Navigation Component
// ============================================================================

interface TabNavProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
  counts?: {
    events?: number;
    handoffs?: number;
  };
}

function TabNav({ activeTab, onTabChange, counts }: TabNavProps) {
  const tabs: Array<{ id: TabType; label: string; icon: string }> = [
    { id: "graph", label: "Graph", icon: "📊" },
    { id: "workstreams", label: "Workstreams", icon: "🔄" },
    { id: "events", label: "Events", icon: "⚡" },
    { id: "handoffs", label: "Handoffs", icon: "🤝" },
    { id: "replay", label: "Replay", icon: "▶️" },
  ];

  return (
    <div className="bg-white border-b">
      <nav className="flex -mb-px">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`flex items-center gap-2 px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.id
                ? "border-blue-500 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            }`}
          >
            <span>{tab.icon}</span>
            <span>{tab.label}</span>
            {tab.id === "events" && (counts?.events || 0) > 0 && (
              <span className="ml-1 px-1.5 py-0.5 text-xs bg-blue-100 text-blue-700 rounded-full">
                {counts.events}
              </span>
            )}
            {tab.id === "handoffs" && (counts?.handoffs || 0) > 0 && (
              <span className="ml-1 px-1.5 py-0.5 text-xs bg-purple-100 text-purple-700 rounded-full">
                {counts.handoffs}
              </span>
            )}
          </button>
        ))}
      </nav>
    </div>
  );
}

// ============================================================================
// Loading State
// ============================================================================

function LoadingState() {
  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <div className="text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-gray-200 border-t-blue-600 mb-4" />
        <p className="text-sm text-gray-500">Loading mission...</p>
      </div>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export default function MissionDetailPage() {
  const { missionId } = useParams<{ missionId: string }>();
  const [activeTab, setActiveTab] = useState<TabType>("graph");
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  // Redirect if no mission ID
  if (!missionId) {
    return <Navigate to="/control" replace />;
  }

  const handleTabChange = (tab: TabType) => {
    setActiveTab(tab);
    setSelectedNodeId(null);
  };

  return (
    <div className="container mx-auto px-4 py-6 max-w-7xl">
      {/* Breadcrumb */}
      <div className="text-sm text-gray-500 mb-4">
        <span className="hover:text-gray-700 cursor-pointer" onClick={() => window.history.back()}>
          Control
        </span>
        <span className="mx-2">/</span>
        <span className="text-gray-900">Mission Details</span>
      </div>

      {/* Mission Detail Header */}
      <MissionDetailHeader missionId={missionId} />

      {/* Tab Navigation */}
      <div className="mt-6">
        <TabNav
          activeTab={activeTab}
          onTabChange={handleTabChange}
        />
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {activeTab === "graph" && (
          <MissionGraphPanel
            missionId={missionId}
            onNodeSelect={setSelectedNodeId}
            selectedNodeId={selectedNodeId}
          />
        )}

        {activeTab === "workstreams" && (
          <WorkstreamHealthPanel missionId={missionId} />
        )}

        {activeTab === "events" && (
          <MissionEventStream missionId={missionId} maxHeight="500px" />
        )}

        {activeTab === "handoffs" && (
          <HandoffList missionId={missionId} />
        )}

        {activeTab === "replay" && (
          <MissionReplay missionId={missionId} />
        )}
      </div>
    </div>
  );
}
