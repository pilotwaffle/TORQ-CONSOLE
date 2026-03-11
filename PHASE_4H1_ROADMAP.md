# Phase 4H.1 — Strategic Memory Validation & Control

## Purpose

Prove that strategic memory actually improves reasoning before expanding to agent teams.

**Premise:** Memory injection is only valuable if it measurably improves outcomes without degrading performance.

**Risk:** Unvalidated memory injection could:
- Degrade reasoning quality through context overload
- Increase latency and token costs
- Introduce institutional bias
- Mask local signals with broad doctrine

**Approach:** Controlled experiments → Effectiveness scoring → Operational UI → Scoped rules

---

## Milestone 1: Memory Injection Experiments

### Goal

Prove that strategic memory injection improves reasoning outcomes.

### Experiment Design

#### Experiment A: Control vs Candidate

| Group | Configuration |
|-------|---------------|
| **Control** | No strategic memory injection |
| **Candidate** | Top-5 strategic memory injection |

**Metrics to Compare:**
- Overall evaluation score (primary)
- Coherence score
- Actionability score
- Contradiction rate
- Latency (seconds)
- Token cost

**Sample Size:**
- Minimum 50 executions per group
- Stratified by workflow type
- Same workflow types in both groups

**Success Criteria:**
- Candidate shows ≥3% improvement in overall evaluation score
- No significant degradation in actionability
- Latency increase <10%
- Token cost increase <15%

#### Experiment B: Top-3 vs Top-5

| Group | Configuration |
|-------|---------------|
| **Top-3** | Top-3 most relevant strategic memories |
| **Top-5** | Top-5 most relevant strategic memories |

**Metrics to Compare:**
- Same as Experiment A, plus:
- Memory relevance score correlation
- Context length impact

**Success Criteria:**
- Identify optimal memory count threshold
- Detect "context overload" point if it exists

### Implementation

**New Table: `memory_injection_experiments`**
```sql
CREATE TABLE memory_injection_experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_name TEXT NOT NULL,
    control_group_config JSONB,
    candidate_group_config JSONB,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    status TEXT DEFAULT 'running',
    sample_size_target INTEGER,
    sample_size_current INTEGER DEFAULT 0
);
```

**New Table: `memory_injection_results`**
```sql
CREATE TABLE memory_injection_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID REFERENCES memory_injection_experiments(id),
    execution_id UUID,
    group_assignment TEXT, -- 'control' or 'candidate'
    injected_memory_ids UUID[],
    evaluation_overall NUMERIC,
    evaluation_coherence NUMERIC,
    evaluation_actionability NUMERIC,
    evaluation_contradictions NUMERIC,
    latency_seconds NUMERIC,
    token_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**New Module: `strategic_memory/experiments.py`**
```python
class MemoryInjectionExperiment:
    """Run controlled experiments on memory effectiveness."""

    async def assign_to_group(self, execution_id: str) -> str:
        """Deterministically assign execution to control or candidate."""
        # Hash-based assignment (consistent for same execution)
        hash_value = int(hashlib.sha256(f"{experiment_id}:{execution_id}".encode()).hexdigest(), 16)
        return "candidate" if hash_value % 2 == 0 else "control"

    async def record_result(self, execution_id: str, group: str, evaluation: EvaluationResult):
        """Record experiment outcome."""
        # Store result for analysis
        pass

    async def analyze_results(self, experiment_id: str) -> ExperimentAnalysis:
        """Compare control vs candidate performance."""
        # Statistical analysis with confidence intervals
        pass
```

### Success Metrics

- **Primary:** Candidate overall score ≥ Control overall score + 3%
- **Secondary:** No significant actionability degradation
- **Operational:** Latency increase <10%, token cost increase <15%

### Deliverables

- Experiment assignment infrastructure
- Results tracking schema
- Statistical analysis module
- A/B test results report

---

## Milestone 2: Memory Effectiveness Scoring

### Goal

Track whether injected memories actually help downstream outcomes.

### Current State

We track `usage_count` and `last_used_at`, but not whether the memory helped.

### New Scoring

**For each memory injection, track:**

1. **Evaluation Delta**
   - Compare execution evaluation to historical baseline for workflow type
   - Positive delta = memory helped

2. **Experiment Outcomes**
   - If execution led to adaptation proposal, did it succeed?
   - Promoted adaptations = memory contributed to improvement

3. **Workflow-Type Performance**
   - Aggregate evaluation scores for workflows using this memory
   - Compare to same workflows without memory

4. **Contradiction Reduction**
   - Track contradiction rate in executions using memory
   - Lower rate = memory improved coherence

### Effectiveness Score Formula

```python
effectiveness_score = (
    evaluation_delta_impact * 0.30 +
    experiment_success_rate * 0.25 +
    workflow_performance_boost * 0.25 +
    contradiction_reduction * 0.20
)
```

**Components:**

- `evaluation_delta_impact`: -1.0 to +1.0 (normalized)
- `experiment_success_rate`: 0.0 to 1.0
- `workflow_performance_boost`: -1.0 to +1.0 (normalized)
- `contradiction_reduction`: 0.0 to 1.0

### Schema Addition

**Update `memory_usage` table:**
```sql
ALTER TABLE memory_usage ADD COLUMN evaluation_delta NUMERIC;
ALTER TABLE memory_usage ADD COLUMN led_to_proposal BOOLEAN;
ALTER TABLE memory_usage ADD COLUMN proposal_succeeded BOOLEAN;
ALTER TABLE memory_usage ADD COLUMN contradiction_count INTEGER;
ALTER TABLE memory_usage ADD COLUMN effectiveness_contribution NUMERIC;
```

**New function: Recalculate effectiveness**
```python
async def recalculate_memory_effectiveness(memory_id: str):
    """Update effectiveness score based on all usage data."""
    # Aggregate usage data
    # Calculate component scores
    # Update strategic_memories.effectiveness_score
```

### Deliverables

- Enhanced memory_usage schema
- Effectiveness scoring module
- Periodic recalculation job
- Effectiveness trends API

---

## Milestone 3: Strategic Memory Center UI

### Goal

Give operators a strong UI for managing strategic memory.

### Views

#### 1. Candidate Memories Queue

**Purpose:** Review and approve/reject candidates

**Columns:**
- Memory type (icon badge)
- Title (click to view full content)
- Domain/scope tags
- Confidence score (color-coded bar)
- Durability score (color-coded bar)
- Evidence counts (workspaces, executions, patterns)
- Proposed date

**Actions:**
- Approve (with optional notes)
- Reject (with required reason)
- View sources (link to patterns)
- Export (JSON)

**Filters:**
- Memory type
- Domain
- Confidence threshold
- Age

#### 2. Active Memories Dashboard

**Purpose:** Monitor active strategic memory

**Tabs:**
- All Active
- By Type (Heuristics, Playbooks, Warnings, etc.)
- By Domain
- By Scope (Global, Workflow, Agent)

**Cards:**
- Memory title and type badge
- Confidence/durability scores
- Usage count (last 30 days)
- Effectiveness score (if calculated)
- Expiration date (with warning if <30 days)
- Last validated date

**Actions:**
- View details
- Deprecate (with reason)
- Challenge (with evidence)
- View lineage

#### 3. Memory Lineage View

**Purpose:** Track memory evolution

**Visualization:** Tree or timeline

**Shows:**
- Original memory (deprecated/supplanted)
- Superseding memories (linked)
- Source patterns (clickable)
- Related memories (same sources)

**Actions:**
- Compare versions (diff view)
- View supersession reason
- Export lineage

#### 4. Challenged Memories

**Purpose:** Handle contradicting evidence

**List:**
- Memory title
- Challenge count (badge)
- Latest challenge description
- Status (under review, auto-deprecated, reinstated)

**Actions:**
- View challenges
- Uphold challenge (deprecate memory)
- Reject challenge (reinstate with higher confidence)
- Add evidence notes

#### 5. Memory Usage Analytics

**Purpose:** Track effectiveness and trends

**Charts:**
- Usage over time (by memory type)
- Effectiveness score distribution
- Top 10 most injected memories
- Injection by workflow type
- Effectiveness vs confidence scatter

**Tables:**
- Memory | Type | Usage (30d) | Effectiveness | Avg Latency Impact
- Memory | Success Rate | Experiment Count

#### 6. Injection Log

**Purpose:** Debug and audit

**Filters:**
- Date range
- Workflow type
- Memory ID
- Execution ID

**Columns:**
- Timestamp
- Execution ID (link)
- Workflow type
- Injected memories (count + list)
- Outcome score
- Helped? (boolean, if tracked)

### Frontend Routes

| Route | Component | Purpose |
|-------|-----------|---------|
| `/admin/strategic-memory` | StrategicMemoryCenter | Main dashboard |
| `/admin/strategic-memory/candidates` | CandidatesQueue | Approval queue |
| `/admin/strategic-memory/active` | ActiveMemories | Active memories list |
| `/admin/strategic-memory/:id` | MemoryDetail | Single memory view |
| `/admin/strategic-memory/:id/lineage` | MemoryLineage | Lineage visualization |
| `/admin/strategic-memory/challenges` | ChallengedMemories | Challenge handling |
| `/admin/strategic-memory/analytics` | MemoryAnalytics | Usage and effectiveness |
| `/admin/strategic-memory/injections` | InjectionLog | Injection history |

### Deliverables

- Strategic Memory Center page set
- Approval workflow UI
- Lineage visualization component
- Analytics dashboard
- Injection log table

---

## Milestone 4: Challenge/Revalidation Dashboards

### Goal

Streamline governance operations.

### Challenge Dashboard

**Incoming Challenges Panel:**
- Memory title with challenge badge
- Challenge description
- Evidence summary
- Challenge count (if multiple)

**Quick Actions:**
- Accept challenge (deprecate memory)
- Reject challenge (reinstate)
- Escalate to human (if auto-deprecated)

**Challenge Details:**
- Challenging pattern ID
- Contradiction evidence
- Historical challenge history for this memory

### Revalidation Dashboard

**Due for Revalidation:**
- List of memories past revalidation date
- Priority by (importance × overdue days)

**Bulk Actions:**
- Select memories
- Bulk revalidate with confidence adjustment
- Bulk deprecate if no longer valid

**Revalidation Form:**
- Current memory display
- New evidence input
- Confidence adjustment slider
- Durability adjustment slider
- Validation notes

### Automated Rules

**Auto-deprecate triggers:**
- 3+ challenges within 30 days
- Effectiveness score below 0.3 for 60+ days
- Contradiction rate increase in using workflows

**Auto-reinstate triggers:**
- Challenging pattern itself deprecated
- New evidence supports original memory
- Human review override

### Deliverables

- Challenge dashboard UI
- Revalidation dashboard UI
- Bulk action handlers
- Auto-governance rules engine

---

## Milestone 5: Scoped Retrieval Rules

### Goal

Formalize memory scope precedence before expansion.

### Scope Hierarchy

```
1. Tenant-specific (highest precedence)
2. Domain-specific
3. Workflow-type-specific
4. Agent-type-specific
5. Global (lowest precedence)
```

### Retrieval Algorithm

```python
async def retrieve_scoped_memories(context: MemoryContext) -> List[StrategicMemory]:
    """
    Retrieve memories with proper scope precedence.

    Tenant memories override domain memories.
    Domain memories override workflow-type memories.
    Workflow-type memories override global memories.
    """
    memories = []

    # Start with global (baseline)
    global_memories = await search(scope=MemoryScope.GLOBAL, **context)
    memories.extend(global_memories)

    # Layer on agent-type (more specific)
    if context.agent_type:
        agent_memories = await search(
            scope=MemoryScope.AGENT_TYPE,
            scope_key=context.agent_type,
            **context
        )
        memories = _supersedes(memories, agent_memories)

    # Layer on workflow-type (more specific)
    if context.workflow_type:
        workflow_memories = await search(
            scope=MemoryScope.WORKFLOW_TYPE,
            scope_key=context.workflow_type,
            **context
        )
        memories = _supersedes(memories, workflow_memories)

    # Layer on domain (more specific)
    if context.domain:
        domain_memories = await search(
            scope=MemoryScope.DOMAIN,
            scope_key=context.domain,
            **context
        )
        memories = _supersedes(memories, domain_memories)

    # Layer on tenant (most specific)
    if context.tenant_id:
        tenant_memories = await search(
            scope=MemoryScope.TENANT,
            scope_key=context.tenant_id,
            **context
        )
        memories = _supersedes(memories, tenant_memories)

    return deduplicate_by_id(memories)


def _supersedes(base: List[Memory], new: List[Memory]) -> List[Memory]:
    """
    Merge lists where new memories supersede conflicting base memories.

    A memory supersedes another if:
    - Same memory_type
    - Similar topic (title/content similarity)
    - Newer created_at
    - Higher confidence
    """
    result = list(base)

    for new_memory in new:
        # Find conflicting base memories
        conflicting = [
            m for m in result
            if m.memory_type == new_memory.memory_type
            and _topics_similar(m, new_memory)
        ]

        # Remove superseded memories
        for c in conflicting:
            if new_memory.created_at > c.created_at:
                result.remove(c)

        # Add new memory
        result.append(new_memory)

    return result
```

### Scope Configuration

**New table: `memory_scope_rules`**
```sql
CREATE TABLE memory_scope_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scope TEXT NOT NULL,
    scope_key TEXT,
    precedence INTEGER NOT NULL UNIQUE, -- 1=highest, 10=lowest
    max_memories INTEGER DEFAULT 5,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Default precedence
INSERT INTO memory_scope_rules (scope, precedence) VALUES
    ('tenant', 1),
    ('domain', 2),
    ('workflow_type', 3),
    ('agent_type', 4),
    ('global', 5);
```

### Per-Scope Limits

**Prevent context overload:**
```python
SCOPE_LIMITS = {
    MemoryScope.TENANT: 10,        # Most specific, allow more
    MemoryScope.DOMAIN: 5,
    MemoryScope.WORKFLOW_TYPE: 5,
    MemoryScope.AGENT_TYPE: 3,
    MemoryScope.GLOBAL: 3,         # Least specific, allow fewer
}
```

### Deliverables

- Scoped retrieval algorithm
- Scope precedence configuration
- Per-scope memory limits
- Supersedence logic

---

## Phase 4H.1 Deliverables Summary

| Milestone | Key Output | Success Criteria |
|-----------|------------|------------------|
| 1. Experiments | A/B test infrastructure | Prove memory improves outcomes ≥3% |
| 2. Effectiveness | Impact scoring system | Track real downstream value |
| 3. UI Center | Operator dashboard | Team can trust and manage memories |
| 4. Governance | Challenge/revalidation workflows | Safe memory lifecycle management |
| 5. Scoping | Precedence rules | Prevent doctrine sprawl |

---

## Success Criteria for Phase 4H.1

### Quantitative

- Memory injection shows ≥3% improvement in overall evaluation scores
- Effectiveness scores calculated for 80%+ of active memories
- 0 memories auto-deprecated without valid reason
- Operator can review candidates in <5 minutes each

### Qualitative

- Team trusts strategic memory system
- Clear visibility into memory lineage and challenges
- Confident expansion to agent teams

---

## After Phase 4H.1: Phase 5

**Phase 5 — Autonomous Agent Teams with Strategic Planning**

Once memory is proven and operationalized:

```
Top-level planner → Mission plan
     ↓
Specialist agents → Subplan execution
     ↓
Workspace capture → Team reasoning
     ↓
Strategic memory → Prior doctrine injection
     ↓
Evaluation → Team performance scoring
     ↓
Adaptive loop → Team behavior improvement
```

This makes TORQ a true **consulting operating system**.

---

## Timeline Estimate

| Milestone | Duration |
|-----------|----------|
| 1. Experiments | 1 week |
| 2. Effectiveness | 3 days |
| 3. UI Center | 1 week |
| 4. Governance | 3 days |
| 5. Scoping | 2 days |

**Total: ~3 weeks** to validated, operational strategic memory.

Then proceed to Phase 5 with confidence.
