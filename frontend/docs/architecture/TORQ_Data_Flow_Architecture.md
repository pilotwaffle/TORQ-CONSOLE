# TORQ Console
# Data Flow Architecture

**Document Location:** docs/architecture/TORQ_Data_Flow_Architecture.md
**Purpose:** Detailed data flow from execution through artifacts, memory, insights, and patterns
**Companion:** TORQ_Master_Architecture.md (conceptual overview), TORQ_Service_Map.md (service organization)

---

# 1. Overview

This document traces how data flows through TORQ's intelligence pipeline — from raw execution output to reusable strategic intelligence.

Understanding these flows is critical for:
- Debugging intelligence pipeline issues
- Adding new insight types
- Implementing custom pattern detectors
- Optimizing data retention policies

---

# 2. The Master Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         EXECUTION                              │
│                    (Agent / Workflow Runs)                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         ARTIFACTS (L2)                         │
│              Raw Outputs, Traces, Reasoning Chains            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Validation Gate │
                    │  Quality Check   │
                    └─────────────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
            ┌───────────┐          ┌──────────┐
            │  Memory   │          │ Discard  │
            │   (L3)   │          │          │
            └───────────┘          └──────────┘
                    │
                    ┌─────────┴─────────┐
                    ▼                   ▼
            ┌───────────┐          ┌──────────┐
            │  Direct   │          │ Insight  │
            │ Agent Use │          │  (L4)   │
            └───────────┘          └──────────┘
                                          │
                                          ▼
                                ┌───────────────────┐
                                │  Candidate         │
                                │  Extraction        │
                                └───────────────────┘
                                          │
                                          ▼
                                ┌───────────────────┐
                                │  Quality Gate      │
                                │  Confidence Check  │
                                └───────────────────┘
                                          │
                                ┌─────────┴─────────┐
                                ▼                   ▼
                        ┌───────────┐          ┌──────────┐
                        │  Publish  │          │ Discard  │
                        └───────────┘          └──────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        PUBLISHED INSIGHTS (L4)                    │
│           Strategic Insight, Playbooks, Findings, etc.          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                        ┌───────────────────┐
                        │  Agent Retrieval   │
                        │  Context-Aware     │
                        └───────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         PATTERNS (L5)                           │
│            Recurring Signals, Predictive Models                │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STRATEGIC SIMULATION (L10)                   │
│              Scenario Modeling, Forecasting, Risk               │
└─────────────────────────────────────────────────────────────────┘
```

---

# 3. Detailed Flow: Execution → Artifacts

## 3.1 Execution Sources

| Source | Description | Artifacts Produced |
|--------|-------------|-------------------|
| **Agent Execution** | Single agent completes a task | Reasoning chain, tool calls, result |
| **Workflow Execution** | Multi-step workflow runs | Trace logs, node outputs, execution graph |
| **Mission Execution** | Complex multi-workflow mission | Mission timeline, handoffs, outcomes |
| **Simulation Run** | Strategic scenario simulation | Model inputs, scenario outcomes |

## 3.2 Artifact Structure

Each artifact contains:

```typescript
interface Artifact {
  id: string;
  type: ArtifactType;
  source: ExecutionSource;
  timestamp: number;

  // Core content
  content: {
    reasoning?: string[];
    toolCalls?: ToolCall[];
    outputs?: any[];
    trace?: ExecutionTrace;
  };

  // Metadata
  metadata: {
    missionId?: string;
    agentId?: string;
    workflowId?: string;
    executionId: string;
    duration?: number;
    success: boolean;
  };

  // Provenance
  provenance: {
    createdBy: string;
    created_at: number;
    lineage?: string[];  // Parent artifact IDs
  };
}
```

## 3.3 Artifact Storage

Artifacts are stored in **L2 Artifact Persistence** with:
- Immutable write-once storage
- Content-addressed indexing
- Time-based retention policies
- Efficient retrieval by execution context

---

# 4. Detailed Flow: Artifacts → Memory

## 4.1 Validation Gate

Not all artifacts become memory. The validation gate checks:

| Check | Purpose | Threshold |
|-------|---------|-----------|
| **Completeness** | Required fields present | 100% |
| **Consistency** | No contradictions | Semantic validation |
| **Quality Score** | Minimum confidence | ≥ 0.6 |
| **Privacy** | No sensitive data leak | Redaction check |
| **Duplicate** | No near-exact copy | Similarity < 0.95 |

## 4.2 Memory Formation

Artifacts passing validation are transformed into memory objects:

```typescript
interface Memory {
  id: string;
  type: MemoryType;

  // Content
  content: {
    summary: string;
    key_points: string[];
    entities?: Entity[];
    relationships?: Relationship[];
  };

  // Validation
  validation: {
    confidence: number;
    validated_by: string | 'auto';
    validated_at: number;
  };

  // Lifecycle
  lifecycle: {
    created_at: number;
    freshness_score: number;
    last_accessed: number;
    access_count: number;
  };

  // Provenance
  provenance: {
    source_artifacts: string[];
    transformation: string;
  };
}
```

## 4.3 Memory Types

| Type | Description | Retention |
|------|-------------|----------|
| **Fact Memory** | Validated factual knowledge | Long-term |
| **Procedural Memory** | How-to knowledge | Medium-term |
| **Episodic Memory** | What-happened context | Short-term |
| **Semantic Memory** | Concept relationships | Long-term |

---

# 5. Detailed Flow: Memory → Insights

## 5.1 Candidate Extraction

The insight extraction process scans memory for:

1. **Reusable patterns** - Approaches that worked well
2. **Risk signals** - Problems that occurred
3. **Decisions made** - Choices with rationale
4. **Outcomes** - Results achieved
5. **Context** - When/where this applies

## 5.2 Insight Types

Each insight type has specific extraction rules:

```typescript
type InsightType =
  | "strategic_insight"      // High-level direction
  | "reusable_playbook"      // Procedural knowledge
  | "validated_finding"      // Fact-based discovery
  | "architecture_decision"  // Design choice with rationale
  | "best_practice"          // Proven effective method
  | "risk_pattern"           // Recurring failure mode
  | "execution_lesson"      // Learned improvement
  | "research_summary";      // Curated external knowledge
```

## 5.3 Quality Gate for Insights

Insights must pass:

| Criterion | Threshold |
|-----------|-----------|
| **Confidence** | ≥ 0.75 (varies by type) |
| **Evidence Count** | ≥ 2 supporting artifacts |
| **Applicability** | Clear use case identified |
| **Novelty** | Not duplicate of existing insight |
| **Clarity** | Human-readable description |

## 5.4 Approval Workflow

High-impact insights require approval:

```
              ┌─────────────┐
              │  Candidate  │
              │   Insight   │
              └──────┬──────┘
                     │
            ┌────────┴────────┐
            ▼                 ▼
      ┌──────────┐      ┌──────────┐
      │  Auto-   │      │ Manual   │
      │ Publish │      │ Review  │
      └──────────┘      └────┬────┘
                               │
                     ┌─────────┴─────────┐
                     ▼                   ▼
             ┌──────────┐          ┌──────────┐
             │ Approve │          │ Reject   │
             └──────────┘          └──────────┘
```

---

# 6. Detailed Flow: Insights → Patterns

## 6.1 Pattern Detection

Patterns are detected across multiple insights:

```typescript
interface Pattern {
  id: string;
  type: PatternType;

  // The pattern
  pattern: {
    signal: string;              // What repeats
    conditions: Condition[];      // When it appears
    confidence: number;           // Statistical certainty
    frequency: number;            // How often seen
  };

  // Supporting evidence
  evidence: {
    insight_ids: string[];
    artifact_count: number;
    time_span: { start: number; end: number };
  };

  // Predictive power
  prediction: {
    predicts: string;           // What this pattern forecasts
    accuracy: number;             // Historical accuracy
  };

  // Metadata
  metadata: {
    first_seen: number;
    last_seen: number;
    strengthening: boolean;      // Is pattern becoming more certain?
  };
}
```

## 6.2 Pattern Types

| Type | Description | Example |
|------|-------------|---------|
| **Success Pattern** | Correlates with positive outcomes | "Code review before deployment reduces bugs" |
| **Failure Pattern** | Correlates with negative outcomes | "Deployments after 6pm have 3x failure rate" |
| **Efficiency Pattern** | Predicts faster execution | "Using cache for API calls improves speed" |
| **Risk Pattern** | Indicates potential problems | "Large missions (>100 tasks) often timeout" |

## 6.3 Pattern Evolution

Patterns strengthen over time:

```
Initial Detection (confidence: 0.6, frequency: 3)
           ↓
Confirmation (confidence: 0.75, frequency: 10)
           ↓
Strong Pattern (confidence: 0.9, frequency: 50)
           ↓
Canonical Pattern (confidence: 0.95+, frequency: 100+)
```

---

# 7. Agent Retrieval Flow

Agents use insights during execution:

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENT REQUEST                            │
│         "I need to accomplish X in context Y"              │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
                  ┌────────────────────┐
                  │  Context Building  │
                  │  - mission type      │
                  │  - agent type       │
                  │  - domain           │
                  └────────────────────┘
                           │
                           ▼
                  ┌────────────────────┐
                  │   Insight Query    │
                  │   Multi-factor rank │
                  └────────────────────┘
                           │
            ┌──────────────────┼──────────────────┐
            ▼                  ▼                  ▼
      ┌──────────┐       ┌──────────┐       ┌──────────┐
      │  Ranked  │       │  Filter  │       │ Selected │
      │ Results  │       │  (rules) │       │  Top-K   │
      └──────────┘       └──────────┘       └──────────┘
                                                  │
                                                  ▼
                                    ┌────────────────────────┐
                                    │  Insight Integration    │
                                    │  - Added to prompt       │
                                    │  - Used for decision     │
                                    └────────────────────────┘
```

## 7.1 Multi-Factor Ranking

Insights are ranked by:

| Factor | Weight | Description |
|--------|--------|-------------|
| **Confidence** | 30% | How reliable is this insight |
| **Validation Quality** | 25% | How rigorous was validation |
| **Applicability** | 25% | How well it matches current context |
| **Freshness** | 10% | How recently was it updated |
| **Usage Success** | 10% | Has it helped in past executions |

## 7.2 Context Filters

```typescript
interface InsightQueryContext {
  mission_type?: string;
  agent_type?: string;
  domain?: string;
  min_confidence?: number;
  max_age?: number;
  exclude_insights?: string[];  // Explicitly excluded
  require_insights?: string[];  // Explicitly required
}
```

---

# 8. Strategic Simulation Data Flow

Simulations use historical data to model futures:

```
┌─────────────────────────────────────────────────────────────┐
│              HISTORICAL DATA AGGREGATION                      │
│     Artifacts + Memory + Insights + Patterns                │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
                  ┌────────────────────┐
                  │  Scenario Building │
                  │  - What if X?      │
                  │  - What if Y?      │
                  └────────────────────┘
                           │
            ┌──────────────────┼──────────────────┐
            ▼                  ▼                  ▼
      ┌──────────┐       ┌──────────┐       ┌──────────┐
      │ Scenario  │       │ Scenario  │       │ Scenario  │
      │    A     │       │    B     │       │    C     │
      └──────────┘       └──────────┘       └──────────┘
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
                  ┌────────────────────┐
                  │  Parallel Run      │
                  │  (Model Outcomes)  │
                  └────────────────────┘
                              │
                              ▼
                  ┌────────────────────┐
                  │  Comparison        │
                  │  - Risk analysis   │
                  │  - ROI comparison  │
                  │  - Resource needs  │
                  └────────────────────┘
                              │
                              ▼
                  ┌────────────────────┐
                  │  Recommendation    │
                  │  - Preferred path  │
                  │  - Risk factors    │
                  └────────────────────┘
```

---

# 9. Federation Data Flow (L11-L12)

Cross-node intelligence sharing:

```
┌──────────────────────────┐         ┌──────────────────────────┐
│      TORQ Node A          │         │      TORQ Node B          │
└──────────────────────────┘         └──────────────────────────┘
           │                                    │
           │  1. Publish Insight                 │
           ▼                                    │
    ┌─────────────┐                            │
    │   Insight    │                            │
    │  (Local)     │                            │
    └─────────────┘                            │
           │                                    │
           │  2. Federate (Redact)               │
           ▼                                    │
    ┌─────────────────────┐                    │
    │  Redacted Insight   │                    │
    │  - Remove local refs│                    │
    │  - Anonymize data   │                    │
    └─────────────────────┘                    │
           │                                    │
           │  3. Publish to Fabric              │
           ▼                                    │
    ┌──────────────────────────────────────┐  │
    │         Distributed Fabric           │  │
    │         (L11 Collective Layer)       │  │
    └──────────────────────────────────────┘  │
                                    │           │
                                    │  4. Retrieve │
                                    ▼           ▼
                         ┌─────────────────────────┐
                         │  Node B Query Context   │
                         │  - Agent needs insight   │
                         │  - Filters applicable    │
                         └─────────────────────────┘
                                    │
                                    ▼
                         ┌─────────────────────────┐
                         │  Return Matched Insights │
                         │  (No raw state leak)     │
                         └─────────────────────────┘
```

## 9.1 Federation Rules

| Rule | Purpose |
|------|---------|
| **No Raw State** | Never share execution logs or unredacted artifacts |
| **Boundary Enforcement** | Respect domain separation rules |
| **Opt-In Sharing** | Insights must be marked as federatable |
| **Redaction Required** | Remove local node references and PII |
| **Provenance Preserved** | Track which node published each insight |

---

# 10. Data Freshness & Lifecycle

## 10.1 Freshness Scores

Each knowledge object has a freshness score:

```typescript
freshness = f(
  time_since_created,
  time_since_validated,
  access_frequency,
  evidence_strength,
  conflicting_signals
)
```

## 10.2 Lifecycle States

```
┌──────────┐   publish   ┌──────────┐   validate   ┌──────────┐
│  Draft   │ ──────────> │  Active  │ ──────────> │ Archived  │
└──────────┘             └──────────┘              └──────────┘
                              │                         ▲
                              │ invalidate              │
                              ▼                         │
                         ┌──────────┐                   │
                         │ Superseded │ ─────────────────┘
                         │ (new version)│
                         └──────────┘
```

## 10.3 Retention Policies

| Object Type | Default Retention | Max Retention | Archive Policy |
|-------------|-------------------|---------------|----------------|
| Artifacts | 90 days | 1 year | Compress after 90 days |
| Memory | 1 year | 5 years | Archive unused |
| Insights | Indefinite | Indefinite | Version on supersede |
| Patterns | Indefinite | Indefinite | Version on change |

---

# 11. Error Handling & Recovery

## 11.1 Pipeline Failure Modes

| Stage | Failure Mode | Recovery |
|-------|--------------|----------|
| Execution | Agent/workflow crash | Retry with backoff, log to artifacts |
| Artifact Capture | Storage failure | Queue and retry, alert operator |
| Memory Validation | Validation failure | Log as "raw" only, discard |
| Insight Extraction | Low confidence | Store as "candidate" for review |
| Pattern Detection | Insufficient data | Accumulate more evidence |
| Agent Retrieval | Query timeout | Fallback to direct execution |
| Federation | Node unreachable | Use local insights, retry later |

## 11.2 Dead Letter Queue

Failed items go to the DLQ for analysis:

```typescript
interface DeadLetterItem {
  id: string;
  stage: string;  // Which pipeline stage failed
  payload: any;   // Original data
  error: string;  // What went wrong
  timestamp: number;
  retry_count: number;
  resolved: boolean;
}
```

---

# 12. Performance Considerations

## 12.1 Hot Paths

| Path | Optimization |
|------|--------------|
| Agent → Memory | In-memory cache, indexed lookup |
| Agent → Insights | Pre-computed rankings, cached by context |
| Memory → Insights | Batch extraction, async validation |
| Pattern Detection | Incremental updates, sliding window |

## 12.2 Caching Strategy

```typescript
// L1: Execution results (5 min cache)
executionCache.set(missionId, result, { ttl: 300 });

// L2: Artifact queries (15 min cache)
artifactCache.set(query, results, { ttl: 900 });

// L3: Memory access (1 hr cache, invalidation on update)
memoryCache.set(key, memory, { ttl: 3600 });

// L4: Insight rankings (context-based, 30 min cache)
insightCache.set(contextHash, ranked, { ttl: 1800 });
```

---

# 13. Summary

The TORQ data flow transforms raw execution into strategic intelligence through:

1. **Capture** (Artifacts) - Immutable evidence of execution
2. **Validate** (Memory) - Quality-checked knowledge
3. **Curate** (Insights) - Reusable intelligence objects
4. **Detect** (Patterns) - Recurring signals across missions
5. **Simulate** (Strategy) - Future scenario modeling
6. **Distribute** (Fabric) - Cross-node intelligence sharing

Each stage has:
- Clear input/output contracts
- Quality gates
- Lifecycle management
- Audit trails
- Performance optimization

This pipeline is what enables TORQ to compound intelligence while maintaining governance.

---

**End of Document**
