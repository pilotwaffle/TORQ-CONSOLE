-- Migration 009: Add metadata fields to working_memory_entries
-- Purpose: Enable importance-based filtering and source tracking for learning signals
-- Created: 2026-03-07

-- Add importance field for entry prioritization
ALTER TABLE working_memory_entries
ADD COLUMN importance TEXT NOT NULL DEFAULT 'medium'
CHECK (importance IN ('low', 'medium', 'high', 'critical'));

-- Add source_type field for provenance tracking
ALTER TABLE working_memory_entries
ADD COLUMN source_type TEXT NOT NULL DEFAULT 'agent'
CHECK (source_type IN ('agent', 'tool', 'user', 'system', 'synthesis'));

-- Add execution_id reference for multi-execution workspaces
ALTER TABLE working_memory_entries
ADD COLUMN execution_id UUID REFERENCES task_executions(id) ON DELETE SET NULL;

-- Create index on importance for fast filtering
CREATE INDEX idx_working_memory_entries_importance ON working_memory_entries(importance);

-- Create index on source_type for provenance queries
CREATE INDEX idx_working_memory_entries_source_type ON working_memory_entries(source_type);

-- Create composite index for learning signal queries
CREATE INDEX idx_working_memory_entries_importance_source
ON working_memory_entries(importance, source_type, created_at DESC);

-- Add comments for documentation
COMMENT ON COLUMN working_memory_entries.importance IS 'Entry importance: low|medium|high|critical. Used for filtering and learning signal prioritization.';
COMMENT ON COLUMN working_memory_entries.source_type IS 'Entry provenance: agent|tool|user|system|synthesis. Used for learning signal source attribution.';
COMMENT ON COLUMN working_memory_entries.execution_id IS 'Optional reference to the task execution that generated this entry. Enables multi-execution workspaces.';

-- Create view for high-value entries (used by learning signal engine)
CREATE OR REPLACE VIEW high_value_working_memory_entries AS
SELECT
    e.*,
    w.scope_type,
    w.scope_id,
    ex.agent_id,
    ex.status as execution_status
FROM working_memory_entries e
JOIN workspaces w ON e.workspace_id = w.id
LEFT JOIN task_executions ex ON e.execution_id = ex.id
WHERE e.importance IN ('high', 'critical')
  AND e.deleted_at IS NULL
ORDER BY e.importance DESC, e.created_at DESC;

COMMENT ON VIEW high_value_working_memory_entries IS 'High-value entries for learning signal extraction. Includes agent and execution context.';
