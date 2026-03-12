-- Migration: Add workspace_id to task_executions
-- Purpose: Link workflow executions to Shared Cognitive Workspaces
-- Date: 2026-03-08

-- Add workspace_id column (nullable for backward compatibility)
ALTER TABLE task_executions
ADD COLUMN IF NOT EXISTS workspace_id UUID;

-- Add index for workspace lookups
CREATE INDEX IF NOT EXISTS idx_task_executions_workspace_id
ON task_executions(workspace_id)
WHERE workspace_id IS NOT NULL;

-- Add comment
COMMENT ON COLUMN task_executions.workspace_id IS 'Link to Shared Cognitive Workspace for execution-level working memory';
