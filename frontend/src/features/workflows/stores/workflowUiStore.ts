/**
 * Workflow UI State Store
 *
 * Manages local UI state for workflows using Zustand.
 * Server state is managed by React Query hooks.
 */

import { create } from "zustand";

export interface WorkflowUiStore {
  // Selection state
  selectedWorkflowId: string | null;
  selectedNodeId: string | null;
  selectedExecutionNodeId: string | null;
  selectedExecutionId: string | null;

  // View preferences
  graphLayout: "horizontal" | "vertical";
  showNodeDetails: boolean;
  showMiniMap: boolean;
  autoRefreshExecutions: boolean;

  // Dialog/modals state
  isCreateDialogOpen: boolean;
  isDeleteDialogOpen: boolean;
  isExecuteDialogOpen: boolean;

  // Filtering
  statusFilter: string | null;
  searchQuery: string;

  // Actions
  setSelectedWorkflowId: (id: string | null) => void;
  setSelectedNodeId: (id: string | null) => void;
  setSelectedExecutionNodeId: (id: string | null) => void;
  setSelectedExecutionId: (id: string | null) => void;

  setGraphLayout: (layout: "horizontal" | "vertical") => void;
  setShowNodeDetails: (show: boolean) => void;
  setShowMiniMap: (show: boolean) => void;
  setAutoRefreshExecutions: (enabled: boolean) => void;

  setIsCreateDialogOpen: (open: boolean) => void;
  setIsDeleteDialogOpen: (open: boolean) => void;
  setIsExecuteDialogOpen: (open: boolean) => void;

  setStatusFilter: (status: string | null) => void;
  setSearchQuery: (query: string) => void;

  // Reset actions
  clearSelections: () => void;
  resetFilters: () => void;
}

export const useWorkflowUiStore = create<WorkflowUiStore>((set) => ({
  // Initial state
  selectedWorkflowId: null,
  selectedNodeId: null,
  selectedExecutionNodeId: null,
  selectedExecutionId: null,

  graphLayout: "horizontal",
  showNodeDetails: true,
  showMiniMap: true,
  autoRefreshExecutions: true,

  isCreateDialogOpen: false,
  isDeleteDialogOpen: false,
  isExecuteDialogOpen: false,

  statusFilter: null,
  searchQuery: "",

  // Actions
  setSelectedWorkflowId: (id) => set({ selectedWorkflowId: id }),
  setSelectedNodeId: (id) => set({ selectedNodeId: id }),
  setSelectedExecutionNodeId: (id) => set({ selectedExecutionNodeId: id }),
  setSelectedExecutionId: (id) => set({ selectedExecutionId: id }),

  setGraphLayout: (layout) => set({ graphLayout: layout }),
  setShowNodeDetails: (show) => set({ showNodeDetails: show }),
  setShowMiniMap: (show) => set({ showMiniMap: show }),
  setAutoRefreshExecutions: (enabled) => set({ autoRefreshExecutions: enabled }),

  setIsCreateDialogOpen: (open) => set({ isCreateDialogOpen: open }),
  setIsDeleteDialogOpen: (open) => set({ isDeleteDialogOpen: open }),
  setIsExecuteDialogOpen: (open) => set({ isExecuteDialogOpen: open }),

  setStatusFilter: (status) => set({ statusFilter: status }),
  setSearchQuery: (query) => set({ searchQuery: query }),

  // Reset actions
  clearSelections: () =>
    set({
      selectedWorkflowId: null,
      selectedNodeId: null,
      selectedExecutionNodeId: null,
      selectedExecutionId: null,
    }),

  resetFilters: () =>
    set({
      statusFilter: null,
      searchQuery: "",
    }),
}));
