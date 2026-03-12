-- Migration: Add workspace_id to task_graphs
-- Purpose: Link workflow graphs to Shared Cognitive Workspaces for planning reasoning
-- Date: 2026-03-08

-- Add workspace_id column (nullable for backward compatibility)
ALTER TABLE task_graphs
ADD COLUMN IF NOT EXISTS workspace_id UUID;

-- Add index for workspace lookups
CREATE INDEX IF NOT EXISTS idx_task_graphs_workspace_id
ON task_graphs(workspace_id)
WHERE workspace_id IS NOT NULL;

-- Add comment
COMMENT ON COLUMN task_graphs.workspace_id IS 'Link to Shared Cognitive Workspace for graph-level planning and reasoning';
