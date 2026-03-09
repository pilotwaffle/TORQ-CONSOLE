# Phase 5.3: Organizational Learning Loop

**Status**: Planning / PRD
**Target Release**: v0.11.0
**Last Updated**: March 8, 2026

---

## Executive Summary

**Problem**: Phase 5.2 gives TORQ specialist teams, but team composition and reasoning strategies are static. The system doesn't learn which team structures work best.

**Solution**: Phase 5.3 introduces **Organizational Learning Loop** — TORQ learns which team patterns, reasoning strategies, and collaboration patterns produce the best outcomes, and adapts future missions accordingly.

**Strategic Result**: TORQ transforms from "powerful but static system" to "self-improving organization" that studies its own engagements and gets better at staffing, analysis, review, and synthesis.

---

## Core Shift

### Before Phase 5.3

```
Assemble teams → Run missions → Produce outputs
```

### After Phase 5.3

```
Assemble teams → Run missions → Evaluate performance
                          ↓
                  Learn what worked
                          ↓
          Update future team selection & reasoning strategies
                          ↓
              Improve organizational performance over time
```

### The Unit of Learning Expands

| Before Phase 5.3 | After Phase 5.3 |
|------------------|-----------------|
| Prompt optimization | Team composition optimization |
| Agent routing | Collaboration pattern selection |
| Tool preference | Reasoning strategy selection |
| Single-agent performance | Multi-specialist team dynamics |
| Escalation patterns | Synthesis style optimization |

---

## What This Layer Does

### Five Core Capabilities

#### 1. Team Pattern Evaluation

Every node-team execution is scored on **how the team worked**, not just output quality.

**Questions Answered**:
- Did parallel specialists outperform lead+challenger?
- Did adding a risk specialist improve contradiction handling?
- Did the synthesizer resolve disagreements well?
- Did a team of 3 outperform a team of 5 for this node type?
- Was the extra latency worth the quality gain?

**Example Discovery**:
> "For recommendation nodes with high uncertainty, lead+challenger produces 15% better contradiction resolution than parallel specialists, with only 8% additional latency."

#### 2. Strategy Selection Learning

TORQ learns which reasoning strategies work best in which contexts.

**Context Dimensions**:
- Node type (task, decision, deliverable)
- Domain (finance, legal, operations, strategy)
- Mission type (market entry, acquisition, product launch)
- Risk level (low, medium, high)
- Uncertainty level (low, medium, high)

**Example Learning**:
> "Analysis nodes in market-entry missions → evidence_weighted strategy produces 22% better synthesis quality."

#### 3. Team Composition Optimization

TORQ learns optimal staffing for different situations.

**Questions Answered**:
- Which roles are essential for this node type?
- Which roles are redundant?
- When do challenger roles improve quality?
- When do extra specialists add cost without benefit?

**Example Discovery**:
> "Legal specialist improves recommendation quality by 18% for regulated-domain nodes, but adds 15% latency with no benefit for general business analysis."

#### 4. Organizational Playbook Formation

Repeatedly successful team patterns graduate into reusable playbooks.

**Example Playbooks**:
> "For risk-heavy recommendation nodes: use lead strategist + risk challenger + synthesizer with sequential review."
>
> "For evidence-heavy analysis nodes: parallel gatherers + reviewer outperforms debate mode."
>
> "For planning nodes: checklist-driven strategist + ops reviewer improves completeness by 27%."

#### 5. Mission-Level Adaptation

TORQ begins redesigning missions based on learning.

**Example Adaptations**:
> "Missions with high uncertainty should include 2x more review gates."
>
> "Risk nodes should default to team execution (not single agent)."
>
> "Acquisition missions should trigger challenger review earlier in graph."

---

## Five New Subsystems

### 1. Team Performance Analyzer

**Purpose**: Measures team execution patterns and effectiveness.

**Location**: `torq_console/organizational_learning/team_performance_analyzer.py`

**Metrics Tracked**:

| Metric | Description | Use |
|--------|-------------|-----|
| Node Quality | Final output quality score | Baseline effectiveness |
| Synthesis Quality | Coherence and integration | Synthesizer effectiveness |
| Contradiction Resolution | Conflicts resolved or surfaced | Team dynamics quality |
| Evidence Coverage | Domain coverage completeness | Specialist adequacy |
| Latency | Time from start to completion | Efficiency measure |
| Token Cost | LLM tokens consumed | Cost efficiency |
| Role Participation | Each role's contribution quality | Role value assessment |

**API**:
```python
from torq_console.organizational_learning import TeamPerformanceAnalyzer

analyzer = TeamPerformanceAnalyzer(supabase_client)

# Analyze completed team execution
evaluation = await analyzer.evaluate_team_execution(
    team_id="team_123",
    node_id="node_456",
    mission_context={
        "node_type": "recommendation",
        "domain": "acquisition",
        "risk_level": "high",
        "uncertainty": "medium"
    }
)

# Result:
# {
#     "team_id": "team_123",
#     "overall_score": 0.87,
#     "synthesis_quality": 0.91,
#     "contradiction_resolution": 0.82,
#     "evidence_coverage": 0.88,
#     "latency": 180,  # seconds
#     "token_cost": 45000,
#     "role_participation": {
#         "strategist": {"quality": 0.92, "contribution": "lead"},
#         "challenger": {"quality": 0.88, "contribution": "challenged assumptions"},
#         "risk_analyst": {"quality": 0.85, "contribution": "flagged risks"},
#         "synthesizer": {"quality": 0.91, "contribution": "integrated"}
#     },
#     "insights": [
#         "Challenger role improved contradiction handling by 23%",
#         "Synthesizer successfully integrated 3 conflicting views",
#         "Token cost elevated due to 3 review rounds"
#     ]
# }
```

---

### 2. Strategy Learning Engine

**Purpose**: Learns which reasoning strategies work best per context.

**Location**: `torq_console/organizational_learning/strategy_learning_engine.py`

**Learning Dimensions**:

| Dimension | Values | Example Impact |
|-----------|--------|----------------|
| Node Type | task, decision, deliverable, evidence | Decision nodes benefit from risk_first |
| Domain | finance, legal, operations, strategy, market | Legal benefits from checklist_driven |
| Mission Type | market_entry, acquisition, product_launch, compliance | Acquisitions benefit from challenger patterns |
| Risk Level | low, medium, high | High risk benefits from additional review |
| Uncertainty | low, medium, high | High uncertainty benefits from parallel specialists |

**API**:
```python
from torq_console.organizational_learning import StrategyLearningEngine

engine = StrategyLearningEngine(supabase_client)

# Learn from completed missions
await engine.learn_from_missions(mission_ids=["mission_1", "mission_2", ...])

# Query best strategy for context
recommendation = await engine.recommend_strategy(
    node_type="recommendation",
    domain="acquisition",
    mission_type="acquisition_assessment",
    risk_level="high",
    uncertainty="medium"
)

# Result:
# {
#     "recommended_reasoning_strategy": "risk_first",
#     "recommended_team_pattern": "lead_plus_challenger",
#     "recommended_challenger_count": 2,
#     "recommended_quality_threshold": 0.80,
#     "confidence": 0.89,
#     "basis": "47 similar nodes, risk_first+2challenger produces 18% better contradiction resolution",
#     "expected_improvement": "+0.15 overall score vs baseline"
# }
```

---

### 3. Team Design Optimizer

**Purpose**: Learns optimal team compositions and collaboration patterns.

**Location**: `torq_console/organizational_learning/team_design_optimizer.py`

**Optimization Questions**:
- Which roles are essential for this node type?
- Which roles are redundant (remove to save cost)?
- When should we use challenger roles?
- What's the optimal team size for quality vs cost tradeoff?

**API**:
```python
from torq_console.organizational_learning import TeamDesignOptimizer

optimizer = TeamDesignOptimizer(supabase_client)

# Get optimized team design for node
design = await optimizer.optimize_team_design(
    node_type="recommendation",
    domain="acquisition",
    constraints={
        "max_latency": 300,  # seconds
        "max_token_cost": 50000,
        "min_quality": 0.80
    }
)

# Result:
# {
#     "recommended_composition": [
#         {"role": "lead_strategist", "agent_type": "strategist", "essential": true},
#         {"role": "challenger", "agent_type": "risk_analyst", "essential": true},
#         {"role": "challenger", "agent_type": "financial_analyst", "essential": false, "value": "+0.08 quality"},
#         {"role": "synthesizer", "agent_type": "synthesizer", "essential": true}
#     ],
#     "team_pattern": "lead_plus_challenger",
#     "expected_quality": 0.87,
#     "expected_latency": 240,
#     "expected_cost": 42000,
#     "optimization_insights": [
#         "Second challenger adds marginal value (+0.08 quality) but increases cost by 18%",
#         "Legal specialist not needed for preliminary assessment (can add in later node)"
#     ]
# }
```

---

### 4. Organizational Playbook Generator

**Purpose**: Converts successful patterns into reusable playbooks.

**Location**: `torq_console/organizational_learning/playbook_generator.py`

**Playbook Lifecycle**:

```
Candidate Pattern (n=10-20)
    ↓ Sufficient data?
Validated Pattern (n=20-50)
    ↓ Statistical significance?
Promoted Playbook (n=50+, stable performance)
    ↓ Organizational endorsement?
Standard Operating Procedure
```

**Playbook Structure**:

```python
{
    "id": "playbook_acquisition_risk_recommendation",
    "title": "Risk-Heavy Acquisition Recommendation Node",
    "scope": {
        "node_type": "recommendation",
        "domain": "acquisition",
        "risk_level": "high"
    },
    "team_composition": [
        {"role": "lead_strategist", "agent_type": "strategist"},
        {"role": "challenger", "agent_type": "risk_analyst"},
        {"role": "challenger", "agent_type": "financial_analyst"},
        {"role": "synthesizer", "agent_type": "synthesizer"}
    ],
    "team_pattern": "lead_plus_challenger",
    "reasoning_strategy": "risk_first",
    "quality_threshold": 0.80,
    "collaboration_mode": "sequential_with_review",
    "review_rounds": 2,
    "expected_quality": 0.87,
    "expected_latency": 240,
    "sample_size": 67,
    "confidence": 0.92,
    "status": "promoted_playbook",
    "created_at": "2026-03-08",
    "last_validated": "2026-03-01"
}
```

**API**:
```python
from torq_console.organizational_learning import PlaybookGenerator

generator = PlaybookGenerator(supabase_client)

# Generate candidate playbooks from recent data
candidates = await generator.generate_candidates(
    min_sample_size=20,
    min_confidence=0.75
)

# Validate playbook against new data
validation = await generator.validate_playbook(
    playbook_id="playbook_acquisition_risk_recommendation",
    new_data_nodes=["node_1", "node_2", ...]
)

# Promote playbook to SOP
await generator.promote_to_sop(playbook_id="playbook_acquisition_risk_recommendation")
```

---

### 5. Mission Design Feedback Engine

**Purpose**: Feeds lessons back into mission graph planning and node selection.

**Location**: `torq_console/organizational_learning/mission_design_feedback.py`

**Feedback Types**:

| Feedback Type | Example |
|---------------|---------|
| Node Type Upgrade | "Risk nodes should default to team execution" |
| Graph Structure | "High-uncertainty missions need 2x more review gates" |
| Escalation Triggers | "Acquisition missions should trigger challenger review earlier" |
| Parallelism Guidance | "Analysis nodes benefit from parallel evidence gathering" |

**API**:
```python
from torq_console.organizational_learning import MissionDesignFeedback

feedback = MissionDesignFeedback(supabase_client)

# Generate mission design recommendations
recommendations = await feedback.generate_recommendations(
    mission_type="acquisition_assessment",
    historical_performance="last_30_missions"
)

# Result:
# {
#     "mission_type": "acquisition_assessment",
#     "recommendations": [
#         {
#             "type": "node_team_upgrade",
#             "target": "risk_nodes",
#             "change": "default_to_team_execution",
#             "reason": "Team execution improves risk node quality by 34%",
#             "confidence": 0.91
#         },
#         {
#             "type": "graph_structure",
#             "target": "review_gates",
#             "change": "add_additional_gate_before_final_deliverable",
#             "reason": "Late-stage issues detected in 27% of missions",
#             "confidence": 0.84
#         },
#         {
#             "type": "escalation_trigger",
#             "target": "challenger_review",
#             "change": "trigger_after_financial_analysis_node",
#             "reason": "Early challenge reduces late rework by 40%",
#             "confidence": 0.78
#         }
#     ]
# }
```

---

## Data Model

### New Tables

#### team_execution_evaluations

```sql
CREATE TABLE team_execution_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL REFERENCES missions(id),
    node_id UUID NOT NULL REFERENCES mission_nodes(id),
    team_id UUID NOT NULL REFERENCES node_teams(id),
    team_pattern TEXT NOT NULL,
    reasoning_strategy TEXT NOT NULL,
    node_type TEXT NOT NULL,
    domain TEXT,
    mission_type TEXT,
    risk_level TEXT,
    uncertainty_level TEXT,

    -- Quality metrics
    overall_score NUMERIC(5,2),
    synthesis_quality NUMERIC(5,2),
    contradiction_resolution NUMERIC(5,2),
    evidence_coverage NUMERIC(5,2),

    -- Efficiency metrics
    latency_seconds INTEGER,
    token_cost INTEGER,
    latency_score NUMERIC(5,2),
    cost_score NUMERIC(5,2),

    -- Role participation
    role_participation JSONB,

    -- Context
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    INDEX idx_team_evals_node_type (node_type),
    INDEX idx_team_evals_domain (domain),
    INDEX idx_team_evals_pattern (team_pattern),
    INDEX idx_team_evals_strategy (reasoning_strategy)
);
```

#### team_pattern_learnings

```sql
CREATE TABLE team_pattern_learnings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_type TEXT NOT NULL,
    domain TEXT,
    mission_type TEXT,
    risk_level TEXT,
    uncertainty_level TEXT,

    -- What was learned
    team_pattern TEXT NOT NULL,
    reasoning_strategy TEXT NOT NULL,
    team_composition JSONB,

    -- Performance statistics
    average_overall_score NUMERIC(5,2),
    average_synthesis_quality NUMERIC(5,2),
    average_contradiction_resolution NUMERIC(5,2),
    average_latency NUMERIC(10,2),
    average_token_cost NUMERIC(10,2),

    -- Statistical significance
    sample_size INTEGER NOT NULL,
    confidence NUMERIC(5,2),
    standard_deviation NUMERIC(5,2),

    -- Comparison to baseline
    baseline_score NUMERIC(5,2),
    improvement_delta NUMERIC(5,2),
    improvement_percent NUMERIC(5,2),

    -- Metadata
    status TEXT NOT NULL DEFAULT 'candidate',  -- candidate, validated, promoted, deprecated
    last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    INDEX idx_pattern_learnings_context (node_type, domain, mission_type),
    INDEX idx_pattern_learnings_status (status),
    INDEX idx_pattern_learnings_pattern (team_pattern)
);
```

#### organizational_playbooks

```sql
CREATE TABLE organizational_playbooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT,

    -- Scope (when to apply)
    playbook_type TEXT NOT NULL,  -- team_composition, reasoning_strategy, mission_structure
    scope TEXT NOT NULL,
    scope_key JSONB,

    -- What to do
    content JSONB NOT NULL,

    -- Performance evidence
    sample_size INTEGER NOT NULL,
    average_score NUMERIC(5,2),
    confidence NUMERIC(5,2),

    -- Lifecycle
    status TEXT NOT NULL DEFAULT 'candidate',  -- candidate, validated, promoted, deprecated, archived
    validated_at TIMESTAMPTZ,
    promoted_at TIMESTAMPTZ,
    deprecated_at TIMESTAMPTZ,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by TEXT,  -- system, human_admin

    INDEX idx_playbooks_scope (scope, scope_key),
    INDEX idx_playbooks_status (status),
    INDEX idx_playbooks_type (playbook_type)
);
```

---

## Cognitive Strategy Engine Integration

### Strategy Selection Becomes Data-Driven

**Before Phase 5.3** (Rule-based):
```python
if node.domain == "legal" and node.risk_level == "high":
    strategy = "checklist_driven"
elif node.node_type == "decision":
    strategy = "risk_first"
else:
    strategy = "analytical"
```

**After Phase 5.3** (Learned):
```python
strategy = await cognitive_strategy_engine.select_strategy(
    node_type=node.node_type,
    domain=node.domain,
    mission_type=mission.type,
    risk_level=node.risk_level,
    uncertainty=node.uncertainty
)

# Engine queries team_pattern_learnings table
# Returns strategy with statistical backing
# Example: "risk_first" with 0.89 confidence, based on 47 similar nodes
```

### Combined Optimization

The Cognitive Strategy Engine optimizes the full stack:

```
Context (node type, domain, risk, uncertainty)
        ↓
Query organizational playbooks
        ↓
Select optimal combination:
    • Team composition
    • Collaboration pattern
    • Reasoning strategy
    • Quality gate strictness
    • Review rounds
        ↓
Execute mission with optimized stack
        ↓
Evaluate performance
        ↓
Update learnings
```

---

## Example: What 5.3 Learns

### Scenario: 80 Recommendation Nodes

TORQ executes 80 recommendation nodes across various missions.

#### Discovery 1: Pattern Effectiveness

| Team Pattern | Avg Quality | Avg Latency | Best For |
|--------------|-------------|-------------|----------|
| parallel_specialists | 0.81 | 145s | Low uncertainty |
| lead_plus_challenger | 0.87 | 185s | High uncertainty |
| gatherers_plus_review | 0.79 | 165s | Evidence-heavy |

**Learning**: "lead_plus_challenger produces 7% better quality for high-uncertainty nodes, with 27% higher latency."

#### Discovery 2: Role Value

| Role | Quality Impact | Cost Impact | When Essential |
|------|----------------|-------------|---------------|
| Strategist (lead) | +baseline | +baseline | Always |
| Challenger (risk) | +12% quality | +18% cost | High-risk nodes |
| Challenger (financial) | +8% quality | +15% cost | Acquisition nodes |
| Legal specialist | +18% quality | +22% latency | Regulated domains |

**Learning**: "Legal specialist essential for regulated domains, redundant for general business analysis."

#### Discovery 3: Strategy Interaction

| Strategy | Best Pattern | Quality Improvement |
|----------|--------------|---------------------|
| risk_first | lead_plus_challenger (2 challengers) | +15% vs baseline |
| analytical | parallel_specialists | +8% vs baseline |
| evidence_weighted | gatherers_plus_review | +12% vs baseline |

**Learning**: "Strategy and pattern must be optimized together, not independently."

#### Resulting Playbook

```json
{
    "title": "High-Risk Acquisition Recommendation",
    "scope": {
        "node_type": "recommendation",
        "domain": "acquisition",
        "risk_level": "high"
    },
    "team_composition": [
        "lead_strategist",
        "risk_challenger",
        "financial_challenger",
        "synthesizer"
    ],
    "team_pattern": "lead_plus_challenger",
    "reasoning_strategy": "risk_first",
    "challenger_count": 2,
    "review_rounds": 2,
    "quality_threshold": 0.85,
    "expected_quality": 0.89,
    "sample_size": 23,
    "confidence": 0.91,
    "improvement_vs_baseline": "+0.18 overall score"
}
```

---

## User Experience Changes

### Before Phase 5.3

- Users manually configure team composition
- Users select reasoning strategy
- System doesn't learn from missions
- Each mission starts fresh

### After Phase 5.3

- System recommends optimal team composition
- System selects reasoning strategy based on data
- System improves with each mission
- Users feel: better recommendations, more consistency, fewer blind spots

### Progressive Disclosure

| Phase | Auto-Apply | Require Approval | Show Insight Only |
|-------|-----------|------------------|-------------------|
| 5.3A | ❌ | ❌ | ✅ (Show recommendations) |
| 5.3B | ❌ | ✅ (Require opt-in) | ✅ |
| 5.3C | ✅ (High confidence only) | ✅ (Medium confidence) | ✅ |
| 5.3D | ✅ (All promoted playbooks) | ✅ (New patterns) | ✅ |

---

## Minimum Viable Rollout

### Phase 5.3A: Evaluation Only

**Scope**: Track and analyze, don't change behavior

**Node Types**: analysis, recommendation, risk

**Metrics**:
- Overall score
- Contradiction resolution
- Latency
- Token cost

**Deliverables**:
- TeamPerformanceAnalyzer
- team_execution_evaluations table
- Basic analytics dashboard
- No automatic recommendations

**Definition of Done**:
- All team executions evaluated
- Performance metrics collected
- Dashboard shows team performance trends
- No mission behavior changed

---

### Phase 5.3B: Recommendations (Opt-In)

**Scope**: Recommend, but require human approval

**New Capabilities**:
- StrategyLearningEngine
- TeamDesignOptimizer
- Recommendation API
- Opt-in UI for applying recommendations

**Deliverables**:
- Strategy learning from historical data
- Team optimization recommendations
- Playbook candidates
- User can opt-in to recommendations

**Definition of Done**:
- System recommends team compositions
- User must approve before applying
- Recommendations include confidence and evidence
- A/B testing framework ready

---

### Phase 5.3C: Playbook Promotion

**Scope**: Promote validated patterns to playbooks

**New Capabilities**:
- OrganizationalPlaybookGenerator
- Statistical validation
- Playbook lifecycle management
- Playbook viewer UI

**Deliverables**:
- Playbook generation and validation
- Promoted playbooks auto-applied (high confidence)
- Playbook viewer and editor
- Playbook performance tracking

**Definition of Done**:
- Validated playbooks promoted automatically
- Playbooks visible in UI
- Playbook performance monitored
- Deprecated playbooks removed

---

### Phase 5.3D: Full Integration

**Scope**: Mission design feedback and automatic optimization

**New Capabilities**:
- MissionDesignFeedback
- Automatic mission structure optimization
- Full Cognitive Strategy Engine integration
- Organizational SOPs

**Deliverables**:
- Mission design recommendations
- Automatic strategy selection
- Mission graph optimization
- Full organizational learning loop

**Definition of Done**:
- Mission structure adapts based on learning
- Strategy selection fully automated
- Organizational playbooks shape all missions
- Continuous improvement loop active

---

## UI / Control Plane

### Team Performance Dashboard

Shows:
- Team performance over time
- Pattern comparison charts
- Role value analysis
- Cost/quality tradeoffs
- Latency trends

### Playbook Viewer

Shows:
- Available playbooks
- Playbook scope and applicability
- Performance evidence
- Sample size and confidence
- Option to apply or customize

### Strategy Insights Panel

Shows:
- Recommended strategies for current context
- Why recommended (evidence)
- Expected improvement
- Option to accept or override

### Mission Design Feedback

Shows:
- Suggested mission structure improvements
- Node type upgrade recommendations
- Graph structure optimizations
- Expected impact

---

## API Surface

### Evaluation

```python
POST   /api/organizational-learning/evaluate-team
GET    /api/organizational-learning/team-evaluations
GET    /api/organizational-learning/team-evaluations/{id}
```

### Learning

```python
POST   /api/organizational-learning/learn-from-missions
GET    /api/organizational-learning/learnings
GET    /api/organizational-learning/learnings/{id}
```

### Optimization

```python
POST   /api/organizational-learning/optimize-team-design
POST   /api/organizational-learning/recommend-strategy
```

### Playbooks

```python
GET    /api/organizational-learning/playbooks
POST   /api/organizational-learning/playbooks
GET    /api/organizational-learning/playbooks/{id}
PUT    /api/organizational-learning/playbooks/{id}
POST   /api/organizational-learning/playbooks/{id}/validate
POST   /api/organizational-learning/playbooks/{id}/promote
POST   /api/organizational-learning/playbooks/{id}/deprecate
```

### Mission Design

```python
POST   /api/organizational-learning/mission-design-feedback
GET    /api/organizational-learning/mission-recommendations
```

---

## Pitfalls to Avoid

### 1. Over-Fitting to Recent Data

**Problem**: System optimizes for last 10 missions, forgets long-term patterns

**Solution**: Minimum sample sizes, statistical significance tests, time-weighted learning

### 2. Premature Auto-Application

**Problem**: System applies weak patterns before validation

**Solution**: Progressive rollout (recommend → opt-in → auto-apply for high confidence only)

### 3. Ignoring Cost/Latency

**Problem**: Optimizes only for quality, ignores efficiency

**Solution**: Multi-objective optimization (quality, latency, cost)

### 4. Context Blindness

**Problem**: Applies playbooks without checking context match

**Solution**: Strict scope matching, confidence penalties for context mismatch

### 5. Stale Playbooks

**Problem**: Old playbooks never updated or deprecated

**Solution**: Continuous validation, deprecation pipeline, performance monitoring

---

## Definition of Done (Phase 5.3 Complete)

### Technical

- [ ] All 5 subsystems implemented and tested
- [ ] Database migrations deployed
- [ ] API endpoints functional
- [ ] Analytics dashboard complete
- [ ] Playbook lifecycle operational

### Functional

- [ ] Team performance evaluated for all executions
- [ ] Strategy learning from historical missions
- [ ] Team optimization recommendations generated
- [ ] Playbooks validated and promoted
- [ ] Mission design feedback operational

### Quality

- [ ] Minimum sample sizes enforced (n≥20 for candidates)
- [ ] Statistical significance tests pass
- [ ] Playbooks monitored for performance drift
- [ ] Deprecation pipeline operational
- [ ] Multi-objective optimization (quality, latency, cost)

### Organizational

- [ ] Clear playbook ownership (system vs human)
- [ ] Playbook review process defined
- [ ] Rollback procedures for bad playbooks
- [ ] Continuous improvement metrics defined

---

## Strategic Result

After Phase 5.3, TORQ becomes:

| Dimension | Before Phase 5.3 | After Phase 5.3 |
|-----------|------------------|-----------------|
| Team Assembly | Manual or rule-based | Data-optimized |
| Strategy Selection | Rule-based | Learned from outcomes |
| Mission Design | Static | Adaptive |
| Organizational Behavior | Fixed configuration | Self-improving |
| Relationship to User | Tool to configure | Partner that learns |

---

## What's Next After Phase 5.3

**Phase 6: Human Strategic Oversight**

Once TORQ has organizational learning, humans need ways to:
- Monitor organizational behavior
- Intervene when needed
- Provide strategic direction
- Validate organizational learning

This adds the "human-in-the-loop" layer that makes TORQ a true AI consulting operating system.

---

## References

- [Phase 5.2 PRD](PHASE_5_2_AGENT_TEAMS_PRD.md)
- [Phase 5.1 Validation Report](PHASE_5_1_VALIDATION_REPORT.md)
- [Architecture Roadmap](ARCHITECTURE_ROADMAP.md)
- [System Overview](TORQ_SYSTEM_OVERVIEW.md)
