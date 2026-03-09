# Phase 5.2: Agent Teams on Mission Graphs

**Status**: Planning / PRD
**Target Release**: v0.10.0
**Last Updated**: March 8, 2026

---

## Executive Summary

**Problem**: Phase 5.1 executes one agent per node. This produces coherent but shallow outputs for complex, multi-dimensional nodes.

**Solution**: Phase 5.2 introduces **Node Team Execution** — specialist teams collaborate within nodes, producing synthesized outputs with broader domain coverage and stronger tradeoff analysis.

**Strategic Result**: TORQ transforms from "structured reasoning by solo specialists" to "structured reasoning by coordinated specialist teams" — the behavior pattern of a real consulting firm.

---

## Core Shift

### Before (Phase 5.1)

```
One Node → One Agent → One Output
```

### After (Phase 5.2)

```
One Node → Specialist Team → Structured Collaboration → Synthesized Output
```

### Example: Market Entry Viability Node

**Before**: One analyst produces assessment

**After**: Team produces integrated assessment
- **Financial Analyst**: Market sizing, revenue projections
- **Legal/Risk Specialist**: Regulatory barriers, compliance requirements
- **Operations Strategist**: Implementation complexity, resource needs
- **Market Strategist**: Competitive positioning, go-to-market
- **Synthesizer**: Integrates all perspectives into recommendation

---

## Architectural Model

### Top-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        Mission Graph                             │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Objective  │───▶│     Node     │───▶│  Deliverable │      │
│  │              │    │              │    │              │      │
│  └──────────────┘    └──────┬───────┘    └──────────────┘      │
│                             │                                   │
│                             ▼                                   │
│                    ┌─────────────────┐                          │
│                    │   Node Team     │                          │
│                    │                 │                          │
│                    │  • Specialist A │                          │
│                    │  • Specialist B │                          │
│                    │  • Specialist C │                          │
│                    │  • Synthesizer  │                          │
│                    └────────┬────────┘                          │
│                             │                                   │
│                             ▼                                   │
│                      Synthesized Output                         │
└─────────────────────────────────────────────────────────────────┘
```

### Node as Mini-Mission

Each eligible node becomes a **mini-mission** with its own:
- Team composition
- Collaboration pattern
- Workspace for specialist contributions
- Internal handoffs
- Synthesis step
- Quality gate

---

## Five New Subsystems

### 1. Node Team Builder

**Purpose**: Determines whether a node should use single-agent or team-based execution.

**Location**: `torq_console/mission_graph/node_teams/team_builder.py`

**Inputs**:
- Node type (objective, task, decision, evidence, deliverable)
- Reasoning strategy (risk_first, analytical, creative, etc.)
- Domain tags (finance, legal, operations, strategy, etc.)
- Risk score (from node or parent mission)
- Strategic memory (past team effectiveness)
- Mission context (complexity, stakes)

**Outputs**:
- Team composition (roles, agent types)
- Collaboration pattern (see Team Patterns below)
- Execution mode (single_agent, fixed_team, dynamic_team)

**Decision Logic**:

| Factor | Single Agent | Fixed Team | Dynamic Team |
|--------|--------------|------------|--------------|
| Node type | Evidence, simple tasks | Recommendation, risk, strategic synthesis | Complex deliverables |
| Risk level | Low | Medium-High | High |
| Domain breadth | Single domain | 2-3 domains | 4+ domains |
| Strategic importance | Low | Medium | Critical |
| Uncertainty | Low | Medium | High |

**API**:
```python
from torq_console.mission_graph.node_teams import TeamBuilder

builder = TeamBuilder(supabase_client, strategic_memory)

# Determine team requirements
team_spec = await builder.build_team_for_node(
    node_id="node_123",
    node_type="task",
    reasoning_strategy="risk_first",
    domain_tags=["finance", "legal", "operations"],
    risk_score=0.75,
    mission_context={"complexity": "high"}
)

# Result:
# {
#     "execution_mode": "fixed_team",
#     "team_pattern": "lead_plus_challenger",
#     "roles": [
#         {"agent_type": "strategist", "role": "lead"},
#         {"agent_type": "risk_analyst", "role": "challenger"},
#         {"agent_type": "synthesizer", "role": "synthesizer"}
#     ],
#     "collaboration_mode": "sequential_with_review"
# }
```

---

### 2. Team Collaboration Engine

**Purpose**: Orchestrates specialist collaboration within a node.

**Location**: `torq_console/mission_graph/node_teams/collaboration_engine.py`

**Collaboration Patterns**:

#### Pattern 1: Parallel Specialists + Synthesis

**Best for**: Multidimensional analysis requiring broad coverage

**Flow**:
```
1. All specialists receive same brief simultaneously
2. Each specialist produces independent analysis
3. Synthesizer receives all outputs
4. Synthesizer integrates, identifies conflicts
5. Optional: specialists review and refine synthesis
6. Final output produced
```

**Example**: Market entry viability (finance, legal, ops, market → synthesizer)

#### Pattern 2: Lead + Challenger

**Best for**: Critical recommendation nodes requiring stress-testing

**Flow**:
```
1. Lead specialist produces initial recommendation
2. Challenger agent attacks assumptions and logic
3. Risk specialist flags potential issues
4. Lead responds to challenges
5. Synthesizer produces final recommendation with challenges addressed
```

**Example**: Go/no-go decision, acquisition recommendation

#### Pattern 3: Gatherers + Reviewer

**Best for**: Evidence-heavy nodes requiring comprehensive coverage

**Flow**:
```
1. Evidence gatherers work in parallel on different sources
2. Verifier cross-checks and validates
3. Summarizer produces consolidated evidence package
4. Optional: quality scorer assesses evidence sufficiency
```

**Example**: Competitive intelligence, regulatory landscape analysis

**API**:
```python
from torq_console.mission_graph.node_teams import CollaborationEngine

engine = CollaborationEngine(supabase_client)

# Execute team collaboration
result = await engine.execute_collaboration(
    team_id="team_123",
    pattern="parallel_specialists",
    node_context={
        "title": "Assess acquisition target viability",
        "brief": "Target company is $50M SaaS, 40% growth, EU market",
        "specialists": [
            {"agent_type": "financial_analyst", "role": "finance"},
            {"agent_type": "legal_specialist", "role": "legal"},
            {"agent_type": "operations_strategist", "role": "ops"},
            {"agent_type": "synthesizer", "role": "synthesizer"}
        ]
    }
)

# Result:
# {
#     "status": "completed",
#     "specialist_outputs": [...],
#     "synthesis": {...},
#     "conflicts_resolved": 3,
#     "confidence": 0.87,
#     "team_quality_score": 0.92
# }
```

---

### 3. Node Team Workspace

**Purpose**: Stores specialist contributions, internal handoffs, and collaboration artifacts.

**Location**: `torq_console/mission_graph/node_teams/workspace.py`

**Workspace Hierarchy**:
```
Mission Workspace
    └── Node Workspace
            ├── Specialist A contributions
            ├── Specialist B contributions
            ├── Specialist C contributions
            ├── Internal handoffs
            ├── Conflict log
            └── Synthesis drafts
```

**Stored Data**:
- Specialist contributions (with attribution)
- Internal handoffs between specialists
- Contradictions and conflicts
- Sub-decisions within node
- Evidence gathered
- Synthesis iterations

**Linkage**: Each node workspace is linked to parent mission workspace for full traceability.

**API**:
```python
from torq_console.mission_graph.node_teams import NodeTeamWorkspace

workspace = NodeTeamWorkspace(supabase_client)

# Create workspace for node team
await workspace.create(team_id="team_123", node_id="node_456")

# Store specialist contribution
await workspace.store_contribution(
    team_id="team_123",
    specialist_id="specialist_finance",
    contribution={
        "analysis": "Financial modeling complete",
        "findings": ["Revenue projections $20-30M by Y3"],
        "confidence": 0.85
    }
)

# Log conflict
await workspace.log_conflict(
    team_id="team_123",
    conflict_type="assumption_disagreement",
    description="Finance assumes 30% growth, ops assumes 20%",
    parties=["specialist_finance", "specialist_ops"]
)

# Retrieve for synthesis
contributions = await workspace.get_contributions(team_id="team_123")
conflicts = await workspace.get_conflicts(team_id="team_123")
```

---

### 4. Team Synthesizer

**Purpose**: Combines all specialist outputs into final node output.

**Location**: `torq_console/mission_graph/node_teams/synthesizer.py`

**Critical Without This**: Node becomes pile of parallel opinions with no integration.

**Synthesis Process**:

1. **Collect**: Gather all specialist outputs
2. **Identify**: Find agreements, contradictions, gaps
3. **Weigh**: Assess evidence quality and specialist credibility
4. **Integrate**: Produce coherent recommendation
5. **Attribute**: Clearly credit each specialist's contributions
6. **Surface**: Explicitly call out unresolved disagreements

**Output Structure**:

```python
{
    "synthesis": {
        "recommendation": "Proceed with acquisition, subject to conditions",
        "reasoning": "Financials strong, operations manageable, legal risks moderate",
        "agreements": [
            "Market opportunity validated (finance + market + ops alignment)",
            "Integration complexity moderate (ops + legal alignment)"
        ],
        "contradictions_resolved": [
            "Growth rate: Finance 30%, Ops 20% → Reconciled at 20-25% range with sensitivity analysis"
        ],
        "unresolved_issues": [
            "Regulatory approval timeline uncertain (6-12 months)"
        ],
        "conditions": [
            "Secure legal opinion on GDPR compliance",
            "Confirm operations integration within 90 days"
        ]
    },
    "specialist_contributions": {
        "finance": {...},
        "legal": {...},
        "operations": {...},
        "market": {...}
    },
    "confidence": 0.87,
    "confidence_basis": "Strong specialist agreement on core thesis, moderate risks identified",
    "attribution": "Synthesis produced by specialist_synthesizer from inputs by finance_analyst, legal_specialist, operations_strategist, market_analyst"
}
```

**API**:
```python
from torq_console.mission_graph.node_teams import TeamSynthesizer

synthesizer = TeamSynthesizer(supabase_client)

# Synthesize team outputs
synthesis = await synthesizer.synthesize_team_output(
    team_id="team_123",
    collaboration_mode="parallel_specialists"
)
```

---

### 5. Team Quality Gate

**Purpose**: Ensures node meets quality standards before completion.

**Location**: `torq_console/mission_graph/node_teams/quality_gate.py`

**Quality Checks**:

| Check | Description | Pass Criteria |
|-------|-------------|---------------|
| Participation | Required specialist roles participated | All roles present |
| Contradictions | Contradictions resolved or surfaced | All addressed or explicit |
| Evidence | Evidence quality sufficient | Minimum evidence score |
| Confidence | Confidence threshold met | Score ≥ threshold |
| Attribution | Contributions properly attributed | All inputs credited |
| Synthesis | Synthesis coherence acceptable | Coherence score ≥ threshold |

**Gate Behavior**:

```python
{
    "status": "pass",  # or "fail", "conditional"
    "checks": {
        "participation": {"status": "pass", "detail": "4/4 roles participated"},
        "contradictions": {"status": "pass", "detail": "3 conflicts resolved, 1 surfaced"},
        "evidence": {"status": "pass", "detail": "Evidence score 0.85"},
        "confidence": {"status": "conditional", "detail": "Confidence 0.72, threshold 0.75"},
        "attribution": {"status": "pass", "detail": "All contributions attributed"},
        "synthesis": {"status": "pass", "detail": "Coherence 0.91"}
    },
    "overall_score": 0.87,
    "can_complete": true,
    "conditions": ["Surface regulatory uncertainty in final output"]
}
```

**API**:
```python
from torq_console.mission_graph.node_teams import TeamQualityGate

gate = TeamQualityGate(supabase_client)

# Run quality gate
result = await gate.evaluate_team(
    team_id="team_123",
    quality_threshold=0.75
)

if result["can_complete"]:
    await complete_node_team(team_id="team_123")
else:
    # Request additional specialist input or refinement
    await request_refinement(team_id="team_123", result["conditions"])
```

---

## Data Model

### New Tables

#### node_teams

```sql
CREATE TABLE node_teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL REFERENCES missions(id),
    node_id UUID NOT NULL REFERENCES mission_nodes(id),
    team_pattern TEXT NOT NULL,  -- parallel_specialists, lead_plus_challenger, gatherers_plus_reviewer
    execution_mode TEXT NOT NULL,  -- single_agent, fixed_team, dynamic_team
    status TEXT NOT NULL DEFAULT 'planned',  -- planned, assembling, active, synthesizing, completed, failed
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    INDEX idx_node_teams_mission (mission_id),
    INDEX idx_node_teams_node (node_id),
    INDEX idx_node_teams_status (status)
);
```

#### node_team_members

```sql
CREATE TABLE node_team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES node_teams(id),
    agent_type TEXT NOT NULL,  -- financial_analyst, legal_specialist, etc.
    role_name TEXT NOT NULL,  -- lead, challenger, synthesizer, etc.
    status TEXT NOT NULL DEFAULT 'assigned',  -- assigned, active, completed, failed
    contribution_summary TEXT,
    confidence NUMERIC(5,2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,

    INDEX idx_node_team_members_team (team_id),
    INDEX idx_node_team_members_agent (agent_type)
);
```

#### node_team_outputs

```sql
CREATE TABLE node_team_outputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES node_teams(id),
    member_id UUID REFERENCES node_team_members(id),
    output_type TEXT NOT NULL,  -- analysis, recommendation, evidence, synthesis
    content JSONB NOT NULL,
    confidence NUMERIC(5,2),
    token_count INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    INDEX idx_node_team_outputs_team (team_id),
    INDEX idx_node_team_outputs_member (member_id)
);
```

#### node_team_decisions

```sql
CREATE TABLE node_team_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES node_teams(id),
    decision_type TEXT NOT NULL,  -- contradiction_resolution, role_conflict, synthesis_direction
    decision_content JSONB NOT NULL,
    made_by TEXT,  -- synthesizer, orchestrator, or specialist
    confidence NUMERIC(5,2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    INDEX idx_node_team_decisions_team (team_id)
);
```

#### node_team_conflicts

```sql
CREATE TABLE node_team_conflicts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES node_teams(id),
    conflict_type TEXT NOT NULL,  -- assumption_disagreement, evidence_conflict, recommendation_divergence
    description TEXT NOT NULL,
    parties TEXT[],  -- List of specialist IDs involved
    status TEXT NOT NULL DEFAULT 'open',  -- open, in_progress, resolved, surfaced, deferred
    resolution TEXT,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    INDEX idx_node_team_conflicts_team (team_id),
    INDEX idx_node_team_conflicts_status (status)
);
```

---

## Workspace Design

### Hierarchy

```
Mission Workspace
    ├── Mission-level context
    ├── Mission-level handoffs
    ├── Mission-level decisions
    └── Node Workspaces
            ├── Node context
            ├── Specialist contributions
            ├── Internal handoffs
            ├── Conflict log
            └── Synthesis iterations
```

### Linkage

Each node team workspace is:
- Linked to parent mission workspace
- Linked to parent node in mission graph
- Attributable to specific specialists

This enables:
- Full traceability from mission outcome to specialist contribution
- Evaluation at mission, node, and specialist levels
- Strategic memory formation at all three levels

---

## Strategic Memory Integration

### Memory Shapes Team Assembly

Strategic memory should influence:

**Who is on the team**:
- "Risk-heavy nodes benefit from challenger pattern"
- "Financial nodes need evidence-weighted synthesis"

**How they collaborate**:
- "Planning nodes perform best with checklist-driven strategist + ops reviewer"
- "Legal nodes require sequential specialist review (not parallel)"

**What reasoning strategy**:
- "Acquisition nodes with risk_first strategy need 2 challengers, not 1"

### Memory Queries at Team Assembly

```python
# Query strategic memory for team patterns
memory = await strategic_memory.query({
    "context": {
        "node_type": "recommendation",
        "domain": ["finance", "legal", "operations"],
        "risk_level": "high"
    },
    "query_type": "team_pattern_recommendation"
})

# Result:
# {
#     "recommended_pattern": "lead_plus_challenger",
#     "required_roles": ["lead_strategist", "challenger", "risk_analyst", "synthesizer"],
#     "collaboration_mode": "sequential_with_review",
#     "confidence": 0.87,
#     "basis": "15 similar nodes, 87% success rate with this pattern"
# }
```

---

## Reasoning Strategy Integration

### Node-Level Strategy Declaration

Each node can declare:

```python
Node(
    id="node_acquisition",
    title="Assess acquisition viability",
    node_type="task",
    reasoning_strategy="risk_first",
    team_pattern="lead_plus_challenger",
    required_roles=["strategist", "risk_analyst", "financial_analyst", "synthesizer"],
    collaboration_params={
        "challenger_count": 2,
        "review_rounds": 2,
        "synthesis_mode": "conservative"
    }
)
```

### Strategy → Team Mapping

| Reasoning Strategy | Recommended Team Pattern |
|--------------------|--------------------------|
| risk_first | lead_plus_challenger (2 challengers) |
| analytical | parallel_specialists + evidence verifier |
| creative | parallel_specialists + divergent synthesis |
| conservative | sequential_review + synthesizer |
| aggressive | parallel_specialists + red_team_challenger |

---

## Execution Flow Example

### Parent Node: "Assess Acquisition Target Viability"

**Step 1: Node Team Builder determines team composition**
```
- Pattern: lead_plus_challenger
- Roles: strategist (lead), risk_analyst (challenger), financial_analyst (challenger), synthesizer
- Mode: sequential_with_review
```

**Step 2: Team Collaboration Engine orchestrates specialists**
```
Lead Strategist produces initial recommendation:
  "Proceed with acquisition. Financials strong, market position solid."

Challenger 1 (Risk Analyst) attacks assumptions:
  "Revenue growth unsustainable at 40%. Regulatory risk underweighted."

Challenger 2 (Financial Analyst) challenges valuation:
  "50x revenue multiple aggressive. Comparable at 35-40x."

Lead Strategist responds to challenges:
  "Growth rate conservative at 25% for projections. Regulatory timeline baked into integration plan."
```

**Step 3: Synthesizer integrates**
```
Synthesis: "Proceed with acquisition, subject to conditions:
  1) Confirm revenue growth ≥25% in Q1
  2) Secure legal opinion on regulatory pathway
  3) Negotiate price to ≤40x revenue

Confidence: 0.82 (down from initial 0.91 due to surfaced risks)"
```

**Step 4: Team Quality Gate evaluates**
```
✓ Participation: All 4 roles participated
✓ Contradictions: 3 resolved, 1 surfaced (regulatory)
✓ Evidence: Adequate
✓ Confidence: 0.82 ≥ threshold 0.75
✓ Attribution: All contributions credited
✓ Synthesis: Coherent

Status: PASS (with conditions)
```

**Step 5: Final node output returned to mission graph**
```
Node completed with synthesized recommendation.
```

---

## API Surface

### Team Orchestration

```python
POST   /api/node-teams/create
GET    /api/node-teams/{id}
POST   /api/node-teams/{id}/start
GET    /api/node-teams/{id}/outputs
GET    /api/node-teams/{id}/conflicts
POST   /api/node-teams/{id}/synthesize
POST   /api/node-teams/{id}/complete
GET    /api/node-teams/{id}/status
```

### Team Members

```python
GET    /api/node-teams/{id}/members
POST   /api/node-teams/{id}/members
GET    /api/node-teams/{id}/members/{member_id}
PUT    /api/node-teams/{id}/members/{member_id}
```

### Workspace

```python
GET    /api/node-teams/{id}/workspace
GET    /api/node-teams/{id}/workspace/contributions
GET    /api/node-teams/{id}/workspace/conflicts
POST   /api/node-teams/{id}/workspace/resolve-conflict
```

### Quality Gate

```python
POST   /api/node-teams/{id}/quality-gate
GET    /api/node-teams/{id}/quality-report
```

---

## UI / Control Plane

### Node Team Inspector

Inside Mission Control, add Node Team Inspector showing:

**Team Composition**:
- Active specialists and roles
- Status of each specialist (assigned, active, completed)
- Time spent per specialist

**Contributions**:
- Each specialist's output
- Attribution and confidence
- Token count per specialist

**Collaboration**:
- Internal handoffs between specialists
- Challenge/response exchanges
- Review iterations

**Conflicts**:
- Open conflicts
- Resolved conflicts
- Surfaced issues (not resolved, but acknowledged)

**Synthesis**:
- Draft synthesis
- Specialist agreement level
- Unresolved issues
- Confidence by specialist

**Quality Gate**:
- Pass/fail status per check
- Overall quality score
- Conditions before node completion

### Mission Graph Visualization Enhancement

Show node team indicators on graph:
- Solo node: Single icon
- Team node: Group icon with specialist count
- Hover: Show team composition

---

## Evaluation Extensions

### Team Quality Scoring

Phase 5.2 extends evaluation to score team performance, not just node outcome.

**New Metrics**:

| Metric | Description |
|--------|-------------|
| Participation Completeness | Required roles participated? |
| Contradiction Resolution | Conflicts addressed or surfaced? |
| Cross-Specialist Alignment | Agreement level across specialists |
| Evidence Coverage | Adequate evidence from all domains? |
| Synthesis Coherence | Integrated vs fragmented output |
| Attribution Quality | Contributions properly credited? |

**Learning Targets**:

TORQ can learn:
- Which team pattern works for which node type
- Which role mix produces best outcomes
- Which collaboration mode produces best node outcomes
- How many challengers is optimal for risk level
- When parallel vs sequential execution works better

---

## Implementation Phases

### Phase 5.2A: Fixed Team Patterns (MVP)

**Scope**: Team execution for high-value node types only

**Node Types**:
- Recommendation nodes
- Risk nodes
- Strategic synthesis nodes

**Team Patterns**:
- parallel_specialists + synthesis
- lead_plus_challenger

**Deliverables**:
- NodeTeamBuilder (rule-based, no strategic memory)
- CollaborationEngine (2 patterns)
- NodeTeamWorkspace (basic)
- TeamSynthesizer (rule-based synthesis)
- TeamQualityGate (5 basic checks)
- Database migrations
- API endpoints
- Basic UI indicator

**Definition of Done**:
- Can create fixed team for recommendation node
- Specialists collaborate and produce synthesis
- Quality gate prevents low-quality completion
- Mission graph shows team nodes
- Evaluation collects team metrics

---

### Phase 5.2B: Dynamic Team Selection

**Scope**: Team selection based on node complexity

**New Capabilities**:
- Strategic memory influences team assembly
- Dynamic specialist selection based on domain tags
- Adaptive collaboration mode selection
- Cost/latency tracking per pattern

**Deliverables**:
- Enhanced NodeTeamBuilder with strategic memory queries
- Team performance tracking (latency, cost, quality)
- Pattern effectiveness learning
- gatherers_plus_reviewer pattern

**Definition of Done**:
- Teams assembled based on past performance
- System recommends team composition
- Pattern effectiveness measured
- Cost/latency tracked

---

### Phase 5.2C: Team Pattern Experimentation

**Scope**: A/B testing and adaptation

**New Capabilities**:
- A/B test team patterns for similar nodes
- Adaptive policy updates based on outcomes
- Advanced conflict resolution strategies
- Multi-round synthesis refinement

**Deliverables**:
- Experiment framework for team patterns
- Adaptation policy integration
- Advanced synthesis (multi-round, iterative refinement)
- Team learning dashboard

**Definition of Done**:
- System experiments with team patterns
- Best patterns auto-promoted
- Continuous improvement loop active
- Full team analytics available

---

## Pitfalls to Avoid

### 1. Over-Teaming Everything

**Problem**: Every node gets 5 specialists → Cost explosion, slow execution

**Solution**: Clear thresholds for team execution. Most nodes stay single-agent.

### 2. No Synthesizer Role

**Problem**: Team outputs become fragmented opinions with no integration

**Solution**: Synthesizer is mandatory for all team patterns

### 3. Hidden Disagreement

**Problem**: Conflicts silently averaged away in synthesis

**Solution**: All conflicts must be explicitly resolved or surfaced in final output

### 4. Team Cost Explosion

**Problem**: No tracking of latency and token cost per pattern

**Solution**: Track cost/latency per pattern, set budgets, optimize over time

### 5. Weak Completion Gates

**Problem**: Node marked complete just because everyone spoke

**Solution**: Quality gate must verify synthesis quality, not just participation

### 6. Attribution Loss

**Problem**: Can't trace recommendation back to specialist

**Solution**: Full attribution in synthesis, workspace traceability

---

## Definition of Done (Phase 5.2 Complete)

### Technical

- [ ] All 5 subsystems implemented and tested
- [ ] Database migrations deployed
- [ ] API endpoints functional
- [ ] UI shows team composition and status
- [ ] Evaluation collects team metrics

### Functional

- [ ] Can create fixed team for recommendation node
- [ ] Can create dynamic team based on node complexity
- [ ] Specialists collaborate via all 3 patterns
- [ ] Synthesis integrates specialist outputs
- [ ] Quality gate prevents low-quality completion
- [ ] Strategic memory influences team assembly

### Quality

- [ ] Team execution validated on 3+ mission types
- [ ] Cost/latency within acceptable bounds (≤3x single agent)
- [ ] Synthesis quality ≥ single agent quality
- [ ] No hidden disagreements in final outputs
- [ ] Full attribution traceability

### Documentation

- [ ] API documentation complete
- [ ] Team patterns documented
- [ ] UI/UX guide for team inspector
- [ ] Evaluation metrics defined

---

## Strategic Result

After Phase 5.2, TORQ becomes:

| Dimension | Before Phase 5.2 | After Phase 5.2 |
|-----------|------------------|-----------------|
| Execution | One agent per node | Specialist team per node (when needed) |
| Reasoning | Solo specialist | Coordinated multi-specialist |
| Outputs | Coherent but shallow | Coherent and deep |
| Behavior | Task executor | Consulting firm |

---

## What's Next After Phase 5.2

**Phase 5.3: Replanning Engine**

When mission conditions change mid-execution, TORQ should:
- Detect deviation from expected path
- Replan remaining graph
- Migrate completed nodes to new plan
- Preserve work already done

This enables true adaptive mission execution.

---

## References

- [Phase 5: Mission Graph Planning](PHASE_5_MISSION_GRAPH_PLANNING.md)
- [Phase 5.1: Execution Fabric](PHASE_5_1_EXECUTION_FABRIC.md)
- [Architecture Index](ARCHITECTURE_INDEX.md)
- [System Overview](TORQ_SYSTEM_OVERVIEW.md)
