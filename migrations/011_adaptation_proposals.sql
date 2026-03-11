-- Migration 011: Adaptation Proposals Storage
-- Purpose: Store governed adaptation proposals derived from learning signals
-- Created: 2026-03-07

-- Main adaptation proposals table
CREATE TABLE IF NOT EXISTS adaptation_proposals (
    proposal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Source signal
    learning_signal_id UUID NOT NULL REFERENCES learning_signals(signal_id) ON DELETE CASCADE,

    -- Adaptation classification
    adaptation_type TEXT NOT NULL CHECK (
        adaptation_type IN (
            'prompt_revision',
            'prompt_context_enrichment',
            'prompt_checklist_addition',
            'prompt_structural_rewrite',
            'reasoning_step_enforcement',
            'risk_detection_prompt_enhancement',
            'routing_profile_adjustment',
            'routing_weight_tweak',
            'routing_threshold_change',
            'tool_priority_increase',
            'tool_priority_decrease',
            'tool_enable',
            'tool_disable',
            'tool_ordering_preference',
            'policy_change',
            'safety_prompt_change',
            'audit_behavior_change',
            'memory_rule_change'
        )
    ),

    -- Target specification
    target_asset_type TEXT NOT NULL CHECK (
        target_asset_type IN (
            'agent_prompt',
            'agent_system_instructions',
            'routing_profile',
            'tool_preferences',
            'workflow_config',
            'safety_policy',
            'memory_rules'
        )
    ),
    target_scope TEXT NOT NULL,  -- agent_id, workflow_id, or 'global'
    target_key TEXT NOT NULL,   -- Specific asset identifier

    -- Proposed change
    proposed_change JSONB NOT NULL,
    change_description TEXT NOT NULL,

    -- Evidence and justification
    evidence_summary TEXT NOT NULL,
    evidence_count INTEGER NOT NULL DEFAULT 1,
    supporting_execution_ids TEXT[] DEFAULT '{}',

    -- Risk and approval
    risk_tier TEXT NOT NULL CHECK (risk_tier IN ('tier_1_low', 'tier_2_medium', 'tier_3_high')),
    approval_mode TEXT NOT NULL CHECK (approval_mode IN ('auto_low_risk', 'human_review', 'restricted')),
    status TEXT NOT NULL DEFAULT 'pending_review' CHECK (
        status IN (
            'draft',
            'pending_review',
            'approved',
            'rejected',
            'applied',
            'rolled_back',
            'expired'
        )
    ),

    -- Version tracking
    current_version TEXT,
    candidate_version TEXT NOT NULL,

    -- Expected impact and rollback
    expected_improvement TEXT,
    rollback_plan TEXT,

    -- Approval tracking
    reviewed_by TEXT,
    reviewed_at TIMESTAMPTZ,
    review_notes TEXT,

    -- Application tracking
    applied_by TEXT,
    applied_at TIMESTAMPTZ,

    -- Rollback tracking
    rolled_back_by TEXT,
    rolled_back_at TIMESTAMPTZ,
    rollback_reason TEXT,

    -- Metrics for impact measurement
    metrics_baseline JSONB,
    metrics_after JSONB,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

-- Indexes for common queries
CREATE INDEX idx_adaptation_proposals_signal ON adaptation_proposals(learning_signal_id);
CREATE INDEX idx_adaptation_proposals_target ON adaptation_proposals(target_scope, target_key);
CREATE INDEX idx_adaptation_proposals_status ON adaptation_proposals(status, created_at DESC);
CREATE INDEX idx_adaptation_proposals_risk_tier ON adaptation_proposals(risk_tier, status);

-- Composite index for finding applicable proposals
CREATE INDEX idx_adaptation_proposals_applicable ON adaptation_proposals(
    target_scope, status, risk_tier, created_at DESC
) WHERE status IN ('pending_review', 'approved');

-- Unique constraint: one active proposal per signal
CREATE UNIQUE INDEX idx_adaptation_proposals_unique_signal ON adaptation_proposals(learning_signal_id)
WHERE status NOT IN ('rejected', 'expired', 'rolled_back');

-- Comments
COMMENT ON TABLE adaptation_proposals IS 'Governed adaptation proposals derived from learning signals. All behavioral changes must flow through this table for safety and traceability.';
COMMENT ON COLUMN adaptation_proposals.risk_tier IS 'Tier 1 (low risk) = auto-apply possible; Tier 2 (medium risk) = human review required; Tier 3 (high risk) = restricted, manual only.';
COMMENT ON COLUMN adaptation_proposals.approval_mode IS 'How the proposal is approved: auto_low_risk, human_review, or restricted.';
COMMENT ON COLUMN adaptation_proposals.candidate_version IS 'Version identifier if this proposal is applied. Used for rollback.';

-- Proposal events table (audit trail)
CREATE TABLE IF NOT EXISTS adaptation_proposal_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID NOT NULL REFERENCES adaptation_proposals(proposal_id) ON DELETE CASCADE,

    event_type TEXT NOT NULL CHECK (
        event_type IN (
            'created',
            'submitted_for_review',
            'approved',
            'rejected',
            'applied',
            'rolled_back',
            'expired'
        )
    ),

    event_data JSONB DEFAULT '{}',
    triggered_by TEXT,  -- User or system that triggered the event

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_adaptation_proposal_events_proposal ON adaptation_proposal_events(proposal_id, created_at DESC);

COMMENT ON TABLE adaptation_proposal_events IS 'Audit trail of proposal lifecycle events for governance and compliance.';

-- Guardrail violations table (policy enforcement tracking)
CREATE TABLE IF NOT EXISTS adaptation_guardrail_violations (
    violation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID REFERENCES adaptation_proposals(proposal_id) ON DELETE SET NULL,
    learning_signal_id UUID REFERENCES learning_signals(signal_id) ON DELETE SET NULL,

    violation_type TEXT NOT NULL,
    description TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('warning', 'error')),
    affected_field TEXT,

    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_adaptation_guardrail_violations_signal ON adaptation_guardrail_violations(learning_signal_id);
CREATE INDEX idx_adaptation_guardrail_violations_unresolved ON adaptation_guardrail_violations(resolved) WHERE resolved = FALSE;

COMMENT ON TABLE adaptation_guardrail_violations IS 'Policy guardrail violations detected during proposal generation or application. Used for policy compliance monitoring.';

-- Policy configuration table (for runtime governance settings)
CREATE TABLE IF NOT EXISTS adaptation_policy_config (
    config_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Proposal generation thresholds
    min_confidence_for_proposal NUMERIC(3,2) DEFAULT 0.70,
    min_evidence_count INTEGER DEFAULT 3,
    min_signal_strength TEXT DEFAULT 'moderate',

    -- Cooldown and deduplication
    proposal_cooldown_hours INTEGER DEFAULT 24,
    max_open_proposals_per_asset INTEGER DEFAULT 3,
    deduplication_similarity_threshold NUMERIC(3,2) DEFAULT 0.85,

    -- Approval defaults
    tier_1_auto_apply BOOLEAN DEFAULT FALSE,
    tier_2_require_approval BOOLEAN DEFAULT TRUE,
    tier_3_require_manual BOOLEAN DEFAULT TRUE,

    -- Expiration
    proposal_expiry_days INTEGER DEFAULT 30,

    -- Governance
    require_rollback_plan BOOLEAN DEFAULT TRUE,
    require_evidence_linkage BOOLEAN DEFAULT TRUE,

    -- Metadata
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (active) WHERE active = TRUE  -- Only one active config
);

COMMENT ON TABLE adaptation_policy_config IS 'Runtime governance configuration for the adaptation policy engine. Changes take effect immediately.';
COMMENT ON COLUMN adaptation_policy_config.min_confidence_for_proposal IS 'Minimum signal confidence (0-1) to generate a proposal.';
COMMENT ON COLUMN adaptation_policy_config.proposal_cooldown_hours IS 'Minimum hours between proposals for the same target asset.';
COMMENT ON COLUMN adaptation_policy_config.max_open_proposals_per_asset IS 'Maximum number of pending/open proposals per target asset.';

-- Insert default configuration
INSERT INTO adaptation_policy_config (
    min_confidence_for_proposal,
    min_evidence_count,
    min_signal_strength,
    proposal_cooldown_hours,
    max_open_proposals_per_asset,
    tier_1_auto_apply,
    tier_2_require_approval,
    tier_3_require_manual,
    proposal_expiry_days
) VALUES (
    0.70,
    3,
    'moderate',
    24,
    3,
    FALSE,  -- Don't auto-apply by default
    TRUE,
    TRUE,
    30
);
