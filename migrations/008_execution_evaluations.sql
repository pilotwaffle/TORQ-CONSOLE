-- Migration: Execution Evaluations Table
-- Purpose: Store execution evaluations for the Adaptive Cognition Loop
-- Date: 2026-03-08
-- Phase: 4F - Adaptive Cognition Loop

CREATE TABLE IF NOT EXISTS execution_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID NOT NULL,
    workspace_id UUID,
    overall_score NUMERIC(5,2) NOT NULL,
    reasoning_score NUMERIC(5,2) NOT NULL,
    outcome_score NUMERIC(5,2) NOT NULL,
    risk_score NUMERIC(5,2) NOT NULL,
    coherence_score NUMERIC(5,2) NOT NULL,
    actionability_score NUMERIC(5,2) NOT NULL,
    evaluator_type TEXT NOT NULL CHECK (evaluator_type IN ('heuristic', 'llm', 'hybrid')),
    evaluation_content JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT fk_execution FOREIGN KEY (execution_id) REFERENCES task_executions(execution_id) ON DELETE CASCADE,
    CONSTRAINT fk_workspace FOREIGN KEY (workspace_id) REFERENCES workspaces(workspace_id) ON DELETE SET NULL
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_execution_evaluations_execution_id ON execution_evaluations(execution_id);
CREATE INDEX IF NOT EXISTS idx_execution_evaluations_workspace_id ON execution_evaluations(workspace_id);
CREATE INDEX IF NOT EXISTS idx_execution_evaluations_overall_score ON execution_evaluations(overall_score);
CREATE INDEX IF NOT EXISTS idx_execution_evaluations_created_at ON execution_evaluations(created_at DESC);

-- Comment
COMMENT ON TABLE execution_evaluations IS 'Evaluations of workflow execution quality across reasoning, coherence, and outcome dimensions';
COMMENT ON COLUMN execution_evaluations.evaluator_type IS 'heuristic, llm, or hybrid evaluation method';
COMMENT ON COLUMN execution_evaluations.overall_score IS 'Composite score 0-100 from all metric dimensions';
