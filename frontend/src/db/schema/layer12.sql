-- ============================================================================
-- Layer 12: Collective Intelligence Exchange
-- Database Schema
--
-- This schema defines the storage structures for federated epistemic artifacts,
-- contradiction tracking, local qualification, and audit logging.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Epistemic Claims Registry
-- ----------------------------------------------------------------------------

-- Stores network-visible epistemic claims (artifacts)
CREATE TABLE IF NOT EXISTS epistemic_claims (
  -- Identity
  claim_id TEXT PRIMARY KEY,
  artifact_type TEXT NOT NULL CHECK (artifact_type IN (
    'observation', 'pattern_claim', 'causal_claim', 'policy_claim', 'recommendation'
  )),
  origin_node TEXT NOT NULL,
  origin_layer INTEGER NOT NULL,
  created_at INTEGER NOT NULL,
  version TEXT NOT NULL,

  -- The Claim
  claim TEXT NOT NULL,
  summary TEXT NOT NULL,

  -- Context (JSON)
  context_json TEXT NOT NULL,

  -- Evidence (JSON)
  evidence_json TEXT NOT NULL,

  -- Limitations (JSON array)
  limitations_json TEXT,

  -- Allowed uses (JSON array)
  allowed_uses_json TEXT NOT NULL,

  -- Provenance (JSON)
  provenance_json TEXT NOT NULL,

  -- Metadata
  received_at INTEGER,
  indexed_at INTEGER,

  -- Soft delete
  deleted_at INTEGER,

  FOREIGN KEY (origin_node) REFERENCES nodes(node_id)
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_epistemic_claims_artifact_type ON epistemic_claims(artifact_type);
CREATE INDEX IF NOT EXISTS idx_epistemic_claims_origin_node ON epistemic_claims(origin_node);
CREATE INDEX IF NOT EXISTS idx_epistemic_claims_created_at ON epistemic_claims(created_at);
CREATE INDEX IF NOT EXISTS idx_epistemic_claims_received_at ON epistemic_claims(received_at);
CREATE INDEX IF NOT EXISTS idx_epistemic_claims_deleted_at ON epistemic_claims(deleted_at);

-- GIN index for JSON context queries (PostgreSQL)
CREATE INDEX IF NOT EXISTS idx_epistemic_claims_context_gin ON epistemic_claims USING gin(context_json jsonb_path_ops);

-- ----------------------------------------------------------------------------
-- Claim Contradictions
-- ----------------------------------------------------------------------------

-- Tracks contradictions between conflicting claims
CREATE TABLE IF NOT EXISTS claim_contradictions (
  contradiction_id TEXT PRIMARY KEY,
  claim_a_id TEXT NOT NULL,
  claim_b_id TEXT NOT NULL,
  contradiction_type TEXT NOT NULL CHECK (contradiction_type IN (
    'direct_contradiction', 'context_conflict', 'causal_disagreement', 'recommendation_conflict'
  )),
  detected_at INTEGER NOT NULL,
  detected_by TEXT NOT NULL,
  resolved BOOLEAN DEFAULT FALSE,
  resolution_type TEXT CHECK (resolution_type IN (
    'context_dependent', 'simulation_resolved', 'governance_resolved', 'both_valid', 'superseded'
  )),
  resolution_notes TEXT,
  resolved_at INTEGER,
  resolved_by TEXT,

  FOREIGN KEY (claim_a_id) REFERENCES epistemic_claims(claim_id),
  FOREIGN KEY (claim_b_id) REFERENCES epistemic_claims(claim_id)
);

-- Indexes for contradiction queries
CREATE INDEX IF NOT EXISTS idx_claim_contradictions_resolved ON claim_contradictions(resolved);
CREATE INDEX IF NOT EXISTS idx_claim_contradictions_claim_a ON claim_contradictions(claim_a_id);
CREATE INDEX IF NOT EXISTS idx_claim_contradictions_claim_b ON claim_contradictions(claim_b_id);
CREATE INDEX IF NOT EXISTS idx_claim_contradictions_detected_at ON claim_contradictions(detected_at);

-- ----------------------------------------------------------------------------
-- Local Qualification Results (per-node)
-- ----------------------------------------------------------------------------

-- Stores qualification results from receiving nodes
CREATE TABLE IF NOT EXISTS local_qualifications (
  qualification_id TEXT PRIMARY KEY,
  artifact_id TEXT NOT NULL,
  qualifying_node TEXT NOT NULL,
  qualified_at INTEGER NOT NULL,

  -- Classification
  category TEXT NOT NULL CHECK (category IN (
    'informational', 'advisory', 'simulation_only', 'allocative_eligible'
  )),

  -- Scores (0-1)
  local_relevance REAL NOT NULL CHECK (local_relevance BETWEEN 0 AND 1),
  provenance_strength REAL NOT NULL CHECK (provenance_strength BETWEEN 0 AND 1),
  confidence_stability REAL NOT NULL CHECK (confidence_stability BETWEEN 0 AND 1),
  overall_trust REAL NOT NULL CHECK (overall_trust BETWEEN 0 AND 1),

  -- Flags
  has_context_clash BOOLEAN NOT NULL,
  has_contradictions BOOLEAN NOT NULL,
  requires_simulation BOOLEAN NOT NULL,
  policy_compatible BOOLEAN NOT NULL,

  -- Context comparison (JSON)
  context_comparison_json TEXT,

  -- Recommendations
  recommended_uses_json TEXT NOT NULL,
  warnings_json TEXT,
  adaptations_json TEXT,

  -- Decision
  suggested_action TEXT NOT NULL CHECK (suggested_action IN (
    'ignore', 'store_informational', 'use_advisory', 'send_to_simulation', 'send_to_governance'
  )),

  FOREIGN KEY (artifact_id) REFERENCES epistemic_claims(claim_id),
  FOREIGN KEY (qualifying_node) REFERENCES nodes(node_id)
);

-- Indexes for qualification queries
CREATE INDEX IF NOT EXISTS idx_local_qualifications_artifact_id ON local_qualifications(artifact_id);
CREATE INDEX IF NOT EXISTS idx_local_qualifications_qualifying_node ON local_qualifications(qualifying_node);
CREATE INDEX IF NOT EXISTS idx_local_qualifications_qualified_at ON local_qualifications(qualified_at);
CREATE INDEX IF NOT EXISTS idx_local_qualifications_category ON local_qualifications(category);
CREATE INDEX IF NOT EXISTS idx_local_qualifications_suggested_action ON local_qualifications(suggested_action);

-- ----------------------------------------------------------------------------
-- Epistemic Audit Log
-- ----------------------------------------------------------------------------

-- Logs all epistemic exchange events
CREATE TABLE IF NOT EXISTS epistemic_audit_log (
  event_id TEXT PRIMARY KEY,
  event_type TEXT NOT NULL CHECK (event_type IN (
    'publication', 'qualification', 'adoption', 'rejection', 'simulation_test', 'governance_review'
  )),
  artifact_id TEXT NOT NULL,
  node_id TEXT NOT NULL,
  timestamp INTEGER NOT NULL,

  -- Event-specific data (JSON)
  event_data_json TEXT NOT NULL,

  -- For quick querying
  adoption_outcome TEXT,
  rejection_reason TEXT,
  governance_decision TEXT,

  FOREIGN KEY (artifact_id) REFERENCES epistemic_claims(claim_id),
  FOREIGN KEY (node_id) REFERENCES nodes(node_id)
);

-- Indexes for audit queries
CREATE INDEX IF NOT EXISTS idx_epistemic_audit_log_artifact_id ON epistemic_audit_log(artifact_id);
CREATE INDEX IF NOT EXISTS idx_epistemic_audit_log_event_type ON epistemic_audit_log(event_type);
CREATE INDEX IF NOT EXISTS idx_epistemic_audit_log_timestamp ON epistemic_audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_epistemic_audit_log_node_id ON epistemic_audit_log(node_id);
CREATE INDEX IF NOT EXISTS idx_epistemic_audit_log_adoption_outcome ON epistemic_audit_log(adoption_outcome);

-- ----------------------------------------------------------------------------
-- Local Adoption Decisions (per-node)
-- ----------------------------------------------------------------------------

-- Tracks what each node has adopted from the federation
CREATE TABLE IF NOT EXISTS local_adoptions (
  adoption_id TEXT PRIMARY KEY,
  artifact_id TEXT NOT NULL,
  adopting_node TEXT NOT NULL,
  adopted_at INTEGER NOT NULL,

  -- Adoption type
  adoption_type TEXT NOT NULL CHECK (adoption_type IN (
    'informational', 'advisory', 'simulation_tested', 'allocative_eligible'
  )),

  -- Tracking
  usage_count INTEGER DEFAULT 0,
  last_used_at INTEGER,
  effectiveness_score REAL CHECK (effectiveness_score BETWEEN 0 AND 1),

  -- Adaptations made (JSON)
  adaptations_json TEXT,

  -- Superseded by
  superseded_by TEXT,
  superseded_at INTEGER,

  FOREIGN KEY (artifact_id) REFERENCES epistemic_claims(claim_id),
  FOREIGN KEY (adopting_node) REFERENCES nodes(node_id)
);

-- Indexes for adoption queries
CREATE INDEX IF NOT EXISTS idx_local_adoptions_artifact_id ON local_adoptions(artifact_id);
CREATE INDEX IF NOT EXISTS idx_local_adoptions_adopting_node ON local_adoptions(adopting_node);
CREATE INDEX IF NOT EXISTS idx_local_adoptions_adopted_at ON local_adoptions(adopted_at);
CREATE INDEX IF NOT EXISTS idx_local_adoptions_adoption_type ON local_adoptions(adoption_type);
CREATE INDEX IF NOT EXISTS idx_local_adoptions_superseded_by ON local_adoptions(superseded_by);

-- ----------------------------------------------------------------------------
-- Federation Eligibility Cache
-- ----------------------------------------------------------------------------

-- Caches eligibility checks for insights to prevent republishing
CREATE TABLE IF NOT EXISTS federation_eligibility_cache (
  insight_id TEXT PRIMARY KEY,
  eligible BOOLEAN NOT NULL,
  checked_at INTEGER NOT NULL,
  reason TEXT,
  expires_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_federation_eligibility_cache_expires_at ON federation_eligibility_cache(expires_at);

-- ----------------------------------------------------------------------------
-- Publication Rate Limits
-- ----------------------------------------------------------------------------

-- Tracks publication counts per node to enforce rate limits
CREATE TABLE IF NOT EXISTS publication_rate_limits (
  node_id TEXT NOT NULL,
  date TEXT NOT NULL,  -- YYYY-MM-DD format
  publication_count INTEGER NOT NULL DEFAULT 0,
  last_published_at INTEGER,

  PRIMARY KEY (node_id, date)
);

CREATE INDEX IF NOT EXISTS idx_publication_rate_limits_date ON publication_rate_limits(date);

-- ----------------------------------------------------------------------------
-- Trust Scores (per-node)
-- ----------------------------------------------------------------------------

-- Tracks trust scores for nodes with time decay
CREATE TABLE IF NOT EXISTS node_trust_scores (
  node_id TEXT NOT NULL,
  scoring_node TEXT NOT NULL,
  trust_score REAL NOT NULL CHECK (trust_score BETWEEN 0 AND 1),
  recent_accuracy REAL DEFAULT 0,
  simulation_success REAL DEFAULT 0,
  historical_reputation REAL DEFAULT 0,
  last_updated_at INTEGER NOT NULL,
  sample_size INTEGER NOT NULL DEFAULT 1,

  PRIMARY KEY (node_id, scoring_node),
  FOREIGN KEY (node_id) REFERENCES nodes(node_id),
  FOREIGN KEY (scoring_node) REFERENCES nodes(node_id)
);

CREATE INDEX IF NOT EXISTS idx_node_trust_scores_trust_score ON node_trust_scores(trust_score);
CREATE INDEX IF NOT EXISTS idx_node_trust_scores_last_updated ON node_trust_scores(last_updated_at);

-- ----------------------------------------------------------------------------
-- Context Similarity Cache
-- ----------------------------------------------------------------------------

-- Caches context similarity scores to avoid recomputation
CREATE TABLE IF NOT EXISTS context_similarity_cache (
  cache_key TEXT PRIMARY KEY,
  similarity_score REAL NOT NULL,
  computed_at INTEGER NOT NULL,
  expires_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_context_similarity_cache_expires_at ON context_similarity_cache(expires_at);

-- ----------------------------------------------------------------------------
-- Views for Common Queries
-- ----------------------------------------------------------------------------

-- View: Active claims (not deleted, not superseded)
CREATE VIEW IF NOT EXISTS v_active_claims AS
SELECT
  c.*,
  COUNT(DISTINCT qc.qualification_id) as qualification_count,
  COUNT(DISTINCT ad.adoption_id) as adoption_count
FROM epistemic_claims c
LEFT JOIN local_qualifications qc ON c.claim_id = qc.artifact_id
LEFT JOIN local_adoptions ad ON c.claim_id = ad.artifact_id AND ad.superseded_by IS NULL
WHERE c.deleted_at IS NULL
GROUP BY c.claim_id;

-- View: Claims with contradictions
CREATE VIEW IF NOT EXISTS v_claims_with_contradictions AS
SELECT
  c.*,
  COUNT(cc.contradiction_id) as contradiction_count,
  MAX(cc.resolved) as all_resolved
FROM epistemic_claims c
INNER JOIN claim_contradictions cc_a ON c.claim_id = cc_a.claim_a_id OR c.claim_id = cc_a.claim_b_id
INNER JOIN claim_contradictions cc ON cc.contradiction_id = cc_a.contradiction_id
WHERE c.deleted_at IS NULL
GROUP BY c.claim_id;

-- View: Recent publications by node
CREATE VIEW IF NOT EXISTS v_recent_publications AS
SELECT
  origin_node,
  COUNT(*) as publication_count,
  MAX(created_at) as latest_publication
FROM epistemic_claims
WHERE deleted_at IS NULL
  AND created_at > strftime('%s', 'now', '-7 days') * 1000
GROUP BY origin_node;

-- View: Adoption statistics by node
CREATE VIEW IF NOT EXISTS v_adoption_statistics AS
SELECT
  adopting_node,
  COUNT(*) as total_adoptions,
  COUNT(CASE WHEN adoption_type = 'informational' THEN 1 END) as informational_count,
  COUNT(CASE WHEN adoption_type = 'advisory' THEN 1 END) as advisory_count,
  COUNT(CASE WHEN adoption_type = 'simulation_tested' THEN 1 END) as simulation_count,
  COUNT(CASE WHEN adoption_type = 'allocative_eligible' THEN 1 END) as allocative_count,
  AVG(effectiveness_score) as avg_effectiveness
FROM local_adoptions
WHERE superseded_by IS NULL
GROUP BY adopting_node;

-- ----------------------------------------------------------------------------
-- Triggers for Automatic Timestamps
-- ----------------------------------------------------------------------------

-- Trigger for epistemic_claims
CREATE TRIGGER IF NOT EXISTS trg_epistemic_claims_insert_timestamp
AFTER INSERT ON epistemic_claims
BEGIN
  UPDATE epistemic_claims SET indexed_at = strftime('%s', 'now') * 1000 WHERE claim_id = NEW.claim_id;
END;

-- Trigger for local_qualifications
CREATE TRIGGER IF NOT EXISTS trg_local_qualifications_timestamp
AFTER INSERT ON local_qualifications
BEGIN
  UPDATE local_qualifications SET qualified_at = COALESCE(NEW.qualified_at, strftime('%s', 'now') * 1000)
  WHERE qualification_id = NEW.qualification_id;
END;

-- ----------------------------------------------------------------------------
-- Stored Procedures (PostgreSQL-style functions)
-- ----------------------------------------------------------------------------

-- Function: Check if node has exceeded publication rate limit
CREATE OR REPLACE FUNCTION check_publication_rate_limit(
  p_node_id TEXT,
  p_max_per_day INTEGER DEFAULT 50
) RETURNS BOOLEAN AS $$
DECLARE
  v_count INTEGER;
  v_date TEXT := to_char(CURRENT_DATE, 'YYYY-MM-DD');
BEGIN
  INSERT INTO publication_rate_limits (node_id, date, publication_count)
  VALUES (p_node_id, v_date, 0)
  ON CONFLICT (node_id, date) DO NOTHING;

  SELECT publication_count INTO v_count
  FROM publication_rate_limits
  WHERE node_id = p_node_id AND date = v_date;

  RETURN v_count < p_max_per_day;
END;
$$ LANGUAGE plpgsql;

-- Function: Get or create trust score
CREATE OR REPLACE FUNCTION get_trust_score(
  p_node_id TEXT,
  p_scoring_node TEXT
) RETURNS REAL AS $$
DECLARE
  v_score REAL;
BEGIN
  SELECT trust_score INTO v_score
  FROM node_trust_scores
  WHERE node_id = p_node_id AND scoring_node = p_scoring_node;

  IF v_score IS NULL THEN
    INSERT INTO node_trust_scores (node_id, scoring_node, trust_score, last_updated_at, sample_size)
    VALUES (p_node_id, p_scoring_node, 0.5, EXTRACT(EPOCH FROM NOW()) * 1000, 0)
    RETURNING trust_score INTO v_score;
  END IF;

  RETURN v_score;
END;
$$ LANGUAGE plpgsql;

-- Function: Decay trust scores (should be run periodically)
CREATE OR REPLACE FUNCTION decay_trust_scores(
  p_decay_factor REAL DEFAULT 0.95,
  p_days_threshold INTEGER DEFAULT 60
) RETURNS INTEGER AS $$
DECLARE
  v_updated_count INTEGER := 0;
BEGIN
  UPDATE node_trust_scores
  SET
    trust_score = trust_score * p_decay_factor,
    last_updated_at = EXTRACT(EPOCH FROM NOW()) * 1000
  WHERE last_updated_at < EXTRACT(EPOCH FROM NOW() - INTERVAL '1 day' * p_days_threshold) * 1000
    AND trust_score > 0.1;

  GET DIAGNOSTICS v_updated_count = ROW_COUNT;
  RETURN v_updated_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- End of Layer 12 Schema
-- ============================================================================
