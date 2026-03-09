-- Migration 018: Agent Teams
-- Phase 5.2 - Agent Teams as a governed execution primitive
--
-- This migration introduces the database schema for multi-agent teams
-- that can execute mission nodes under defined collaboration patterns.

-- ============================================================================
-- TABLE: agent_teams
-- Stores reusable team definitions
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.agent_teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    pattern TEXT NOT NULL DEFAULT 'deliberative_review',
    decision_policy TEXT NOT NULL DEFAULT 'weighted_consensus',
    max_rounds INTEGER NOT NULL DEFAULT 3,
    output_schema TEXT,
    escalation_policy TEXT DEFAULT 'retry_with_fallback',
    is_active BOOLEAN NOT NULL DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_pattern CHECK (pattern IN ('deliberative_review', 'parallel_synthesis', 'supervisor_workers')),
    CONSTRAINT valid_decision_policy CHECK (decision_policy IN ('weighted_consensus', 'unanimous', 'majority', 'validator_gate')),
    CONSTRAINT valid_max_rounds CHECK (max_rounds > 0 AND max_rounds <= 10)
);

-- Index for team lookup
CREATE INDEX idx_agent_teams_team_id ON public.agent_teams(team_id);
CREATE INDEX idx_agent_teams_is_active ON public.agent_teams(is_active);
CREATE INDEX idx_agent_teams_pattern ON public.agent_teams(pattern);

-- ============================================================================
-- TABLE: agent_team_members
-- Defines roles within a team
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.agent_team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES public.agent_teams(id) ON DELETE CASCADE,
    role_name TEXT NOT NULL,
    agent_type TEXT NOT NULL,
    agent_config JSONB DEFAULT '{}',
    confidence_weight FLOAT NOT NULL DEFAULT 1.0,
    execution_order INTEGER NOT NULL DEFAULT 0,
    is_required BOOLEAN NOT NULL DEFAULT true,
    capabilities TEXT[] DEFAULT '{}',
    constraints TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_role_name CHECK (role_name IN ('lead', 'researcher', 'strategist', 'builder', 'critic', 'reviewer', 'validator')),
    CONSTRAINT valid_confidence_weight CHECK (confidence_weight > 0 AND confidence_weight <= 1),
    CONSTRAINT valid_execution_order CHECK (execution_order >= 0),
    CONSTRAINT unique_team_role UNIQUE (team_id, role_name)
);

-- Index for member lookup
CREATE INDEX idx_agent_team_members_team_id ON public.agent_team_members(team_id);
CREATE INDEX idx_agent_team_members_role_name ON public.agent_team_members(role_name);

-- ============================================================================
-- TABLE: team_executions
-- Tracks each team run
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.team_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL REFERENCES public.missions(id) ON DELETE CASCADE,
    node_id UUID NOT NULL REFERENCES public.mission_nodes(id) ON DELETE CASCADE,
    execution_id TEXT NOT NULL UNIQUE,
    team_id UUID NOT NULL REFERENCES public.agent_teams(id),
    workspace_id TEXT,

    -- Execution state
    status TEXT NOT NULL DEFAULT 'created',
    current_round INTEGER NOT NULL DEFAULT 0,
    max_rounds INTEGER NOT NULL DEFAULT 3,

    -- Results
    final_confidence FLOAT,
    decision_outcome TEXT,

    -- Timing
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    estimated_duration_seconds INTEGER,

    -- Metadata
    objective TEXT,
    constraints TEXT[] DEFAULT '{}',
    telemetry JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_status CHECK (status IN (
        'created', 'initialized', 'running', 'awaiting_validation',
        'revising', 'approved', 'blocked', 'failed', 'completed'
    )),
    CONSTRAINT valid_decision_outcome CHECK (decision_outcome IN (
        'approved', 'approved_with_dissent', 'revision_required',
        'blocked', 'escalated', 'failed'
    )),
    CONSTRAINT valid_current_round CHECK (current_round >= 0 AND current_round <= max_rounds)
);

-- Indexes for execution lookup
CREATE INDEX idx_team_executions_mission_id ON public.team_executions(mission_id);
CREATE INDEX idx_team_executions_node_id ON public.team_executions(node_id);
CREATE INDEX idx_team_executions_execution_id ON public.team_executions(execution_id);
CREATE INDEX idx_team_executions_team_id ON public.team_executions(team_id);
CREATE INDEX idx_team_executions_status ON public.team_executions(status);
CREATE INDEX idx_team_executions_created_at ON public.team_executions(created_at DESC);

-- ============================================================================
-- TABLE: team_messages
-- Stores internal collaboration events
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.team_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_execution_id UUID NOT NULL REFERENCES public.team_executions(id) ON DELETE CASCADE,
    round_number INTEGER NOT NULL DEFAULT 1,

    -- Message routing
    sender_role TEXT NOT NULL,
    receiver_role TEXT NOT NULL,
    message_type TEXT NOT NULL,

    -- Content
    content JSONB NOT NULL,
    text_content TEXT,

    -- Quality metrics
    confidence FLOAT,
    token_count INTEGER DEFAULT 0,

    -- Timing
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_message_type CHECK (message_type IN (
        'role_to_role', 'critique', 'validation_block', 'validation_pass',
        'round_summary', 'synthesis', 'escalation', 'revision_request'
    ))
);

-- Indexes for message lookup
CREATE INDEX idx_team_messages_team_execution_id ON public.team_messages(team_execution_id);
CREATE INDEX idx_team_messages_round_number ON public.team_messages(round_number);
CREATE INDEX idx_team_messages_sender_role ON public.team_messages(sender_role);
CREATE INDEX idx_team_messages_message_type ON public.team_messages(message_type);
CREATE INDEX idx_team_messages_created_at ON public.team_messages(created_at DESC);

-- ============================================================================
-- TABLE: team_decisions
-- Stores the final resolution record
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.team_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_execution_id UUID NOT NULL REFERENCES public.team_executions(id) ON DELETE CASCADE,

    -- Final output
    final_output JSONB NOT NULL,
    text_output TEXT,

    -- Decision metadata
    decision_policy TEXT NOT NULL,
    approval_summary JSONB DEFAULT '{}',
    dissent_summary JSONB DEFAULT '{}',

    -- Validator status
    validator_status TEXT NOT NULL DEFAULT 'pending',
    validator_notes TEXT,

    -- Confidence
    confidence_score FLOAT NOT NULL,
    confidence_breakdown JSONB DEFAULT '{}',

    -- Revision tracking
    revision_count INTEGER DEFAULT 0,
    escalation_count INTEGER DEFAULT 0,

    -- Timing
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_validator_status CHECK (validator_status IN (
        'pending', 'approved', 'blocked', 'escalated'
    ))
);

-- Index for decision lookup
CREATE INDEX idx_team_decisions_team_execution_id ON public.team_decisions(team_execution_id);
CREATE INDEX idx_team_decisions_validator_status ON public.team_decisions(validator_status);

-- ============================================================================
-- ENABLE ROW LEVEL SECURITY
-- ============================================================================
ALTER TABLE public.agent_teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.agent_team_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.team_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.team_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.team_decisions ENABLE ROW LEVEL SECURITY;

-- RLS Policies: Allow read access to authenticated users
CREATE POLICY "Allow authenticated read on agent_teams"
    ON public.agent_teams FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Allow authenticated read on agent_team_members"
    ON public.agent_team_members FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Allow authenticated read on team_executions"
    ON public.team_executions FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Allow authenticated read on team_messages"
    ON public.team_messages FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Allow authenticated read on team_decisions"
    ON public.team_decisions FOR SELECT
    TO authenticated
    USING (true);

-- RLS Policies: Service role has full access
CREATE POLICY "Allow service role full access on agent_teams"
    ON public.agent_teams FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Allow service role full access on agent_team_members"
    ON public.agent_team_members FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Allow service role full access on team_executions"
    ON public.team_executions FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Allow service role full access on team_messages"
    ON public.team_messages FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Allow service role full access on team_decisions"
    ON public.team_decisions FOR ALL
    TO service_role
    USING (true);

-- ============================================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================================

-- Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_agent_teams_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_agent_teams_updated_at
    BEFORE UPDATE ON public.agent_teams
    FOR EACH ROW
    EXECUTE FUNCTION update_agent_teams_updated_at();

CREATE TRIGGER trigger_update_team_executions_updated_at
    BEFORE UPDATE ON public.team_executions
    FOR EACH ROW
    EXECUTE FUNCTION update_agent_teams_updated_at();

-- ============================================================================
-- INITIAL TEAM TEMPLATES
-- ============================================================================

-- Planning Team
INSERT INTO public.agent_teams (team_id, name, description, pattern, max_rounds) VALUES
('planning_team', 'Planning Team', 'Mission decomposition and strategic planning', 'deliberative_review', 3)
ON CONFLICT (team_id) DO NOTHING;

INSERT INTO public.agent_team_members (team_id, role_name, agent_type, confidence_weight, execution_order)
SELECT
    (SELECT id FROM public.agent_teams WHERE team_id = 'planning_team'),
    role_name,
    agent_type,
    confidence_weight,
    execution_order
FROM (VALUES
    ('lead', 'planner_agent', 0.30, 1),
    ('strategist', 'strategist_agent', 0.20, 2),
    ('critic', 'critic_agent', 0.20, 3),
    ('validator', 'validator_agent', 0.30, 4)
) AS v(role_name, agent_type, confidence_weight, execution_order)
WHERE EXISTS (SELECT 1 FROM public.agent_teams WHERE team_id = 'planning_team')
ON CONFLICT (team_id, role_name) DO NOTHING;

-- Research Team
INSERT INTO public.agent_teams (team_id, name, description, pattern, max_rounds) VALUES
('research_team', 'Research Team', 'Evidence gathering and analysis', 'deliberative_review', 3)
ON CONFLICT (team_id) DO NOTHING;

INSERT INTO public.agent_team_members (team_id, role_name, agent_type, confidence_weight, execution_order)
SELECT
    (SELECT id FROM public.agent_teams WHERE team_id = 'research_team'),
    role_name,
    agent_type,
    confidence_weight,
    execution_order
FROM (VALUES
    ('lead', 'planner_agent', 0.30, 1),
    ('researcher', 'research_agent', 0.20, 2),
    ('critic', 'critic_agent', 0.20, 3),
    ('validator', 'validator_agent', 0.30, 4)
) AS v(role_name, agent_type, confidence_weight, execution_order)
WHERE EXISTS (SELECT 1 FROM public.agent_teams WHERE team_id = 'research_team')
ON CONFLICT (team_id, role_name) DO NOTHING;

-- Build Team
INSERT INTO public.agent_teams (team_id, name, description, pattern, max_rounds) VALUES
('build_team', 'Build Team', 'Execution and implementation', 'deliberative_review', 3)
ON CONFLICT (team_id) DO NOTHING;

INSERT INTO public.agent_team_members (team_id, role_name, agent_type, confidence_weight, execution_order)
SELECT
    (SELECT id FROM public.agent_teams WHERE team_id = 'build_team'),
    role_name,
    agent_type,
    confidence_weight,
    execution_order
FROM (VALUES
    ('lead', 'planner_agent', 0.30, 1),
    ('builder', 'builder_agent', 0.20, 2),
    ('reviewer', 'critic_agent', 0.20, 3),
    ('validator', 'validator_agent', 0.30, 4)
) AS v(role_name, agent_type, confidence_weight, execution_order)
WHERE EXISTS (SELECT 1 FROM public.agent_teams WHERE team_id = 'build_team')
ON CONFLICT (team_id, role_name) DO NOTHING;

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Active team definitions with members
CREATE OR REPLACE VIEW v_active_teams_with_members AS
SELECT
    t.id,
    t.team_id,
    t.name,
    t.description,
    t.pattern,
    t.decision_policy,
    t.max_rounds,
    jsonb_agg(
        jsonb_build_object(
            'role_name', m.role_name,
            'agent_type', m.agent_type,
            'confidence_weight', m.confidence_weight,
            'execution_order', m.execution_order,
            'is_required', m.is_required
        ) ORDER BY m.execution_order
    ) AS members
FROM public.agent_teams t
LEFT JOIN public.agent_team_members m ON m.team_id = t.id
WHERE t.is_active = true
GROUP BY t.id
ORDER BY t.name;

-- Team execution summary
CREATE OR REPLACE VIEW v_team_execution_summary AS
SELECT
    te.id,
    te.execution_id,
    te.mission_id,
    te.node_id,
    at.name AS team_name,
    te.status,
    te.current_round,
    te.max_rounds,
    te.final_confidence,
    te.decision_outcome,
    te.started_at,
    te.completed_at,
    COUNT(tm.id) AS message_count,
    EXTRACT(EPOCH FROM (COALESCE(te.completed_at, NOW()) - te.started_at)) AS duration_seconds
FROM public.team_executions te
JOIN public.agent_teams at ON at.id = te.team_id
LEFT JOIN public.team_messages tm ON tm.team_execution_id = te.id
GROUP BY te.id, at.name
ORDER BY te.created_at DESC;

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
