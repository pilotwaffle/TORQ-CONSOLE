# Phase 7: Multi-Mission Firm Operating Layer

**Status**: Planning / PRD
**Target Release**: v0.12.0
**Depends On**: Phase 5.1, 5.2, 5.3, Phase 6
**Last Updated**: March 8, 2026

---

## Executive Summary

**Problem**: Phase 5.1-5.3 enable sophisticated single-mission execution. Phase 6 adds human oversight. But TORQ still operates one mission at a time without organizational coordination.

**Solution**: Phase 7 introduces the **Firm Operating Layer** — enabling TORQ to operate multiple missions simultaneously with shared resources, mission portfolios, practice areas, and executive governance.

**Strategic Result**: TORQ transforms from "a system that executes missions" to "a digital consulting firm operating a portfolio of engagements."

---

## Core Shift

### Before Phase 7

```
One mission → one graph → one execution → complete
```

### After Phase 7

```
Many missions → mission portfolio → shared resources → organizational queueing → firm-level learning
```

### The Questions Change

| Before Phase 7 | After Phase 7 |
|----------------|---------------|
| What should this mission do next? | Which missions matter most right now? |
| Which node is ready? | Which missions are blocked by scarce capacity? |
| Which team pattern for this node? | Where should top-quality resources be allocated? |
| How did this mission perform? | Which methodologies work best across the portfolio? |

---

## Six Core Subsystems

### 1. Mission Portfolio Manager

**Purpose**: Track and coordinate all active missions across the organization.

**Location**: `torq_console/portfolios/`

**Responsibilities**:
- Maintain portfolio registry (client, domain, strategic, internal)
- Track mission health across portfolio
- Monitor progress and deadlines
- Identify blocked missions
- Compute mission priority scores

**Key Metrics**:
- Mission health score
- Priority score
- Urgency score
- Strategic value score
- Risk score
- Deadline pressure

**API**:
```python
from torq_console.portfolios import PortfolioService

service = PortfolioService(supabase_client)

# Create portfolio
portfolio = await service.create_portfolio(
    name="Strategic Client Portfolio",
    portfolio_type="client",
    owner="Prince Flowers"
)

# Attach mission with scores
await service.attach_mission(
    portfolio_id=portfolio.id,
    mission_id="mission_123",
    practice_area="Strategy",
    priority_score=0.85,
    urgency_score=0.70,
    strategic_value_score=0.90,
    risk_score=0.40
)

# Get portfolio health
health = await service.get_portfolio_health(portfolio.id)
# {
#     "active_missions": 18,
#     "blocked_missions": 3,
#     "high_risk_missions": 2,
#     "average_score": 0.82,
#     "missions_deadline_pressure": 5
# }
```

---

### 2. Capacity & Resource Manager

**Purpose**: Manage scarce specialist resources across missions.

**Location**: `torq_console/resources/`

**Resource Types**:
- Strategist agents
- Risk specialists
- Financial analysts
- Synthesis engines
- Human review capacity
- Token budgets
- Tool budgets

**Responsibilities**:
- Define specialist pools
- Track available capacity
- Allocate resources to missions
- Detect over-allocation
- Publish utilization metrics

**Example Resource Pool**:
```
Strategist Pool (Top-Tier)
  Total Capacity: 20
  Allocated: 17
  Available: 3
  Utilization: 85%

Risk Specialist Pool
  Total Capacity: 15
  Allocated: 9
  Available: 6
  Utilization: 60%
```

**API**:
```python
from torq_console.resources import ResourceService

service = ResourceService(supabase_client)

# Allocate resources to mission
allocation = await service.allocate_resources(
    mission_id="mission_123",
    resources=[
        {"resource_type": "strategist", "resource_key": "top_tier", "capacity": 2},
        {"resource_type": "risk_analyst", "resource_key": "standard", "capacity": 1}
    ]
)

# Check if allocation succeeded
if not allocation.success:
    # Handle capacity conflict
    await queueing_service.queue_or_pause(
        mission_id="mission_123",
        reason="capacity_blocked"
    )

# Get utilization
utilization = await service.get_utilization()
# {
#     "strategist_top_tier": {"total": 20, "allocated": 17, "utilization_percent": 85},
#     "risk_analyst_standard": {"total": 15, "allocated": 9, "utilization_percent": 60}
# }
```

---

### 3. Organizational Queueing & Prioritization Engine

**Purpose**: Decide what gets resources first across the firm.

**Location**: `torq_console/queueing/`

**Priority Score Calculation**:
```
priority_score =
    (strategic_value * 0.40) +
    (deadline_pressure * 0.30) +
    (mission_risk * 0.20) +
    (portfolio_weight * 0.10)
```

**Decisions**:
- Which mission receives resources next
- Which mission is paused/queued
- Which mission escalates for executive review
- Which mission preempts lower-priority work

**API**:
```python
from torq_console.queueing import QueueingService

service = QueueingService(supabase_client, resource_service)

# Recompute queue
await service.recompute_queue()

# Get prioritized missions
missions = await service.get_prioritized_missions(limit=20)
# [
#     {"mission_id": "mission_1", "priority_score": 0.92, "status": "ready"},
#     {"mission_id": "mission_2", "priority_score": 0.87, "status": "ready"},
#     {"mission_id": "mission_3", "priority_score": 0.65, "status": "queued"},
#     {"mission_id": "mission_4", "priority_score": 0.42, "status": "paused"}
# ]

# Dispatch next mission
next_mission = await service.dispatch_next()
```

---

### 4. Practice Areas & Methodologies

**Purpose**: Organizational specialization and standardized methodologies.

**Location**: `torq_console/practice_areas/`

**Practice Areas**:
- **Strategy**: Market entry, growth, product strategy
- **Risk**: Technical risk, regulatory risk, diligence
- **Operations**: Process improvement, delivery design, capability planning
- **Finance**: Financial modeling, valuation, due diligence
- **Regulatory**: Compliance, GDPR, regulatory strategy
- **Product/GTM**: Product launch, go-to-market, positioning

**Each Practice Area Owns**:
- Mission types
- Methodology templates
- Default team patterns
- Default reasoning strategies
- Quality thresholds
- Playbooks

**Example: Strategy Practice**
```json
{
    "name": "Strategy",
    "mission_types": ["market_entry", "product_strategy", "growth"],
    "default_team_pattern": "parallel_specialists",
    "default_reasoning_strategy": "evidence_weighted",
    "quality_thresholds": {
        "min_confidence": 0.75,
        "min_evidence_coverage": 0.80
    },
    "decision_gates": {
        "market_attractiveness": 0.70,
        "feasibility": 0.75
    },
    "playbooks": ["market_entry_methodology_v3", "growth_strategy_v2"]
}
```

---

### 5. Cross-Mission Learning & Benchmarking

**Purpose**: Extend Phase 5.3 learning to portfolio scale.

**Location**: `torq_console/org_learning/`

**Capabilities**:
- Compare methodology performance across missions
- Benchmark team patterns by practice area
- Identify top-performing configurations
- Generate organizational playbooks
- Track portfolio-wide metrics

**Example Insights**:
```
Market Entry Methodology v3
  Average Quality: 0.86
  Baseline: 0.72
  Improvement: +19%
  Sample Size: 47 missions
  Confidence: 0.91

Risk-First + Lead+Challenger Pattern
  Best For: High-uncertainty recommendation nodes
  Average Quality: 0.89
  vs Baseline: +0.17
  Latency Cost: +27%
```

---

### 6. Executive Oversight Layer

**Purpose**: Firm-scale human-in-the-loop control.

**Location**: `torq_console/executive/`

**Capabilities**:
- Rebalance resources across missions
- Pause/resume missions
- Escalate missions for review
- Override methodologies
- Approve high-risk recommendations
- Reprioritize engagements

**Review Types**:
- **Escalation**: Mission needs executive attention
- **Reprioritization**: Change mission priority
- **Methodology Override**: Use non-standard approach
- **High-Risk Signoff**: Approve critical recommendation
- **Resource Conflict**: Resolve capacity competition

---

## Data Model

### Core Tables

```sql
-- Mission Portfolios
CREATE TABLE mission_portfolios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    portfolio_type TEXT NOT NULL,  -- client, domain, strategic, internal
    owner TEXT,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Portfolio Missions
CREATE TABLE portfolio_missions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES mission_portfolios(id),
    mission_id UUID NOT NULL,
    practice_area TEXT,
    priority_score NUMERIC(5,2) DEFAULT 0,
    urgency_score NUMERIC(5,2) DEFAULT 0,
    strategic_value_score NUMERIC(5,2) DEFAULT 0,
    risk_score NUMERIC(5,2) DEFAULT 0,
    deadline_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'active',  -- active, queued, paused, blocked, completed
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(portfolio_id, mission_id)
);

-- Organizational Resources
CREATE TABLE organizational_resources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_type TEXT NOT NULL,  -- strategist, risk_analyst, synthesizer, human_review, token_budget
    resource_key TEXT NOT NULL,
    practice_area TEXT,
    total_capacity NUMERIC(10,2) NOT NULL DEFAULT 0,
    available_capacity NUMERIC(10,2) NOT NULL DEFAULT 0,
    reserved_capacity NUMERIC(10,2) NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active',
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(resource_type, resource_key)
);

-- Resource Allocations
CREATE TABLE mission_resource_allocations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL,
    resource_id UUID NOT NULL REFERENCES organizational_resources(id),
    allocated_capacity NUMERIC(10,2) NOT NULL,
    allocation_reason TEXT,
    allocation_status TEXT NOT NULL DEFAULT 'active',  -- active, released, blocked
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    released_at TIMESTAMPTZ
);

-- Practice Areas
CREATE TABLE practice_areas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,  -- Strategy, Risk, Finance, Operations, Product
    description TEXT,
    default_team_pattern TEXT,
    default_reasoning_strategy TEXT,
    quality_thresholds JSONB NOT NULL DEFAULT '{}',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Methodologies
CREATE TABLE methodologies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    practice_area_id UUID NOT NULL REFERENCES practice_areas(id),
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    mission_type TEXT,
    methodology_content JSONB NOT NULL,
    confidence NUMERIC(5,2),
    status TEXT NOT NULL DEFAULT 'candidate',  -- candidate, active, deprecated
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(practice_area_id, name, version)
);

-- Organizational Playbooks (extended from Phase 5.3)
CREATE TABLE organizational_playbooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    practice_area TEXT,
    mission_type TEXT,
    node_type TEXT,
    recommended_team_pattern TEXT,
    recommended_reasoning_strategy TEXT,
    evidence_requirements JSONB NOT NULL DEFAULT '{}',
    decision_gate_templates JSONB NOT NULL DEFAULT '{}',
    confidence NUMERIC(5,2),
    source_metrics JSONB NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'candidate',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Executive Reviews
CREATE TABLE executive_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID,
    portfolio_id UUID REFERENCES mission_portfolios(id),
    review_type TEXT NOT NULL,  -- escalation, reprioritization, methodology_override, signoff
    priority TEXT NOT NULL DEFAULT 'medium',
    review_content JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',  -- open, approved, rejected, completed
    created_by TEXT,
    resolved_by TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);
```

---

## Runtime Flow

```
New Mission Request
        │
        ▼
Portfolio Assignment
        ├─ assign to portfolio
        ├─ assign practice area
        └─ compute priority/urgency/risk
        │
        ▼
Capacity Check
        ├─ specialist availability
        ├─ token budget
        └─ human review load
        │
        ▼
Queueing Decision
        ├─ start immediately
        ├─ defer to queue
        ├─ escalate to executive
        └─ preempt lower-priority work
        │
        ▼
Mission Graph Execution
        ├─ scheduler dispatches nodes
        ├─ node teams execute
        ├─ execution fabric coordinates
        └─ outputs captured
        │
        ▼
Cross-Mission Telemetry
        ├─ mission health updates
        ├─ resource usage updates
        ├─ methodology performance
        └─ portfolio benchmarking
        │
        ▼
Executive Oversight
        ├─ review escalations
        ├─ rebalance resources
        ├─ override priorities
        └─ approve methodology changes
        │
        ▼
Organizational Learning
        ├─ compare missions
        ├─ update playbooks
        ├─ improve staffing patterns
        └─ influence future missions
```

---

## API Surface

### Portfolios
```python
POST   /api/portfolios
GET    /api/portfolios
GET    /api/portfolios/{id}
POST   /api/portfolios/{id}/missions
GET    /api/portfolios/{id}/health
GET    /api/portfolios/{id}/missions
```

### Resources
```python
POST   /api/resources
GET    /api/resources
GET    /api/resources/utilization
POST   /api/resources/allocate
POST   /api/resources/allocations/{id}/release
GET    /api/resources/allocations/by-mission/{mission_id}
```

### Queueing
```python
GET    /api/queueing
POST   /api/queueing/recompute
GET    /api/queueing/priorities
POST   /api/queueing/missions/{id}/pause
POST   /api/queueing/missions/{id}/resume
POST   /api/queueing/dispatch-next
```

### Practice Areas
```python
GET    /api/practice-areas
POST   /api/practice-areas
GET    /api/practice-areas/{id}/methodologies
POST   /api/methodologies/{id}/activate
POST   /api/methodologies/{id}/deprecate
```

### Organizational Learning
```python
GET    /api/org-learning/portfolio-insights
GET    /api/org-learning/methodology-performance
GET    /api/org-learning/team-pattern-performance
GET    /api/org-learning/playbooks
POST   /api/org-learning/generate-playbooks
```

### Executive
```python
GET    /api/executive/reviews
POST   /api/executive/reviews
GET    /api/executive/reviews/{id}
POST   /api/executive/reviews/{id}/approve
POST   /api/executive/reviews/{id}/reject
POST   /api/executive/reprioritize
POST   /api/executive/methodology-override
POST   /api/executive/pause-mission
POST   /api/executive/escalate
```

---

## UI / Control Plane

### Firm Operations Dashboard

**Route**: `/admin/firm-ops`

**Panels**:
- Active mission count
- Blocked mission count
- High-risk mission count
- Average portfolio score
- Mission heatmap
- Resource utilization summary
- Executive review alerts

### Portfolio Detail Page

**Route**: `/admin/firm-ops/portfolios/:id`

**Shows**:
- Portfolio mission list
- Mission priority and health
- Portfolio-level metrics
- Open escalations
- Performance trend

### Resource Management Page

**Route**: `/admin/firm-ops/resources`

**Shows**:
- Specialist pools
- Utilization %
- Allocations by mission
- Over-allocation warnings
- Release/reassign actions

### Practice Areas Page

**Route**: `/admin/firm-ops/practice-areas`

**Shows**:
- Practice areas
- Active methodologies
- Default strategies
- Playbook performance
- Quality benchmarks

### Organizational Learning Page

**Route**: `/admin/firm-ops/learning`

**Shows**:
- Methodology comparison
- Team pattern performance
- Benchmark trends
- Emerging playbooks

### Executive Control Page

**Route**: `/admin/firm-ops/executive`

**Shows**:
- Open executive reviews
- Pause/resume controls
- Reprioritization controls
- Methodology overrides
- High-risk signoffs

---

## Minimum Viable Rollout

### Phase 7A: Portfolio Visibility

**Scope**:
- Multiple concurrent missions
- Portfolio dashboard
- Mission priority/urgency/risk scoring
- Mission health aggregation

**Deliverables**:
- Mission portfolios table
- Portfolio missions table
- Portfolio API
- Portfolio dashboard UI

**Definition of Done**:
- Multiple missions visible in one portfolio
- Priority/urgency/risk scoring displayed
- Mission health aggregated

---

### Phase 7B: Shared Resource Pools

**Scope**:
- Specialist pools
- Capacity tracking
- Resource allocation
- Mission queueing

**Deliverables**:
- Organizational resources table
- Resource allocations table
- Resource API
- Utilization dashboard

**Definition of Done**:
- Resources can be allocated and released
- Over-allocation detected and prevented
- Utilization visible in UI

---

### Phase 7C: Practice Areas

**Scope**:
- Practice area definitions
- Methodology templates
- Default strategies

**Deliverables**:
- Practice areas table
- Methodologies table
- Practice area API
- Practice area dashboard

**Definition of Done**:
- Missions mapped to practice areas
- Methodologies visible and activatable
- Practice defaults applied

---

### Phase 7D: Executive Control

**Scope**:
- Executive review queue
- Mission reprioritization
- Pause/resume controls
- Methodology overrides

**Deliverables**:
- Executive reviews table
- Executive API
- Executive control UI

**Definition of Done**:
- Humans can intervene in mission priority
- Methodology changes are reviewable
- High-risk missions can be escalated

---

### Phase 7E: Cross-Mission Learning

**Scope**:
- Portfolio insights
- Methodology performance
- Playbook generation

**Deliverables**:
- Org learning service
- Benchmarking API
- Learning dashboard

**Definition of Done**:
- Firm-level performance insights generated
- Methodologies compared across missions
- Organizational playbooks generated

---

## Directory Structure

```
torq_console/
├── portfolios/           # NEW - Mission portfolio manager
│   ├── __init__.py
│   ├── models.py
│   ├── service.py
│   ├── scoring.py
│   └── api.py
│
├── resources/            # NEW - Capacity & resource manager
│   ├── __init__.py
│   ├── models.py
│   ├── service.py
│   ├── allocator.py
│   ├── utilization.py
│   └── api.py
│
├── queueing/             # NEW - Organizational queueing engine
│   ├── __init__.py
│   ├── models.py
│   ├── service.py
│   ├── prioritizer.py
│   ├── dispatcher.py
│   └── api.py
│
├── practice_areas/       # NEW - Practice area + methodology layer
│   ├── __init__.py
│   ├── models.py
│   ├── service.py
│   ├── methodologies.py
│   └── api.py
│
├── org_learning/         # NEW - Cross-mission learning/benchmarking
│   ├── __init__.py
│   ├── models.py
│   ├── service.py
│   ├── benchmarking.py
│   └── api.py
│
├── executive/            # NEW - Executive oversight layer
│   ├── __init__.py
│   ├── models.py
│   ├── service.py
│   └── api.py
│
└── firm_ops/             # NEW - Orchestration glue
    ├── __init__.py
    ├── runtime.py
    ├── coordination.py
    └── policies.py
```

---

## Migration Plan

Create migrations:

```
021_mission_portfolios.sql
022_organizational_resources.sql
023_queueing_and_allocations.sql
024_practice_areas_and_methodologies.sql
025_organizational_playbooks.sql
026_executive_reviews.sql
027_phase7_views_and_functions.sql
```

---

## Definition of Done (Phase 7 Complete)

### Functional
- [ ] 10+ missions tracked concurrently
- [ ] Missions grouped into portfolios
- [ ] Resources allocated/released correctly
- [ ] Queueing prioritizes missions
- [ ] Practice areas active and visible
- [ ] Executive controls work

### Operational
- [ ] Resource utilization visible
- [ ] Mission health visible portfolio-wide
- [ ] Escalations surface in executive queue
- [ ] Over-allocation prevented

### Learning
- [ ] Methodology performance compared
- [ ] Team patterns benchmarked
- [ ] Organizational playbooks generated

### Safety/Governance
- [ ] Executive override works
- [ ] Methodology changes reviewable
- [ ] High-risk missions can be paused

---

## Strategic Result

After Phase 7, TORQ becomes:

| Dimension | Before Phase 7 | After Phase 7 |
|-----------|----------------|---------------|
| Scale | One mission at a time | Portfolio of missions |
| Resources | Per-mission allocation | Shared organizational pools |
| Prioritization | Manual | Automated queueing |
| Learning | Per-mission | Cross-mission portfolio learning |
| Organization | Flat structure | Practice areas with methodologies |
| Governance | Mission-level | Firm-level executive oversight |

---

## What This Feels Like

At Phase 7, TORQ no longer feels like "one smart AI doing one thing."

It feels like:

- A strategy practice running market entry assessments
- A risk practice running diligence engagements
- An operations practice running process improvement
- All running concurrently
- All learning across work
- All managed through a shared operating system

**That is the digital consulting firm model.**

---

## See Also

- [Phase 5.2 PRD](PHASE_5_2_AGENT_TEAMS_PRD.md)
- [Phase 5.3 PRD](PHASE_5_3_ORGANIZATIONAL_LEARNING_PRD.md)
- [Architecture Roadmap](ARCHITECTURE_ROADMAP.md)
- [System Overview](TORQ_SYSTEM_OVERVIEW.md)
