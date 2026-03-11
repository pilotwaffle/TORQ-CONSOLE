# Phase 4H: Strategic Memory - Implementation Complete

## Overview

Phase 4H implements persistent strategic knowledge that shapes future reasoning. This moves TORQ from episodic learning to **institutional intelligence**.

### The Leap

**Before Phase 4H:**
- "What worked in this experiment?"
- Patterns detected, insights published, prompts improved
- System reasons episodically

**After Phase 4H:**
- "What have we learned that should shape all future reasoning?"
- Enduring knowledge accumulated, validated, and reused
- System reasons from institutional context

## What Was Built

### 1. Memory Consolidation Engine
**File:** `torq_console/strategic_memory/consolidation.py`

Converts cross-workspace patterns into durable memory candidates.

**Key Features:**
- Consolidation rules with configurable thresholds
- Confidence, durability, and applicability scoring
- Pattern → memory content generation using templates

**Default Rules:**
| Rule | Min Workspaces | Min Executions | Min Success | Memory Type |
|------|----------------|----------------|-------------|-------------|
| Planning Playbook | 5 | 20 | 70% | playbook |
| Warning Pattern | 3 | 10 | - | warning |
| Heuristic Extraction | 4 | 15 | 75% | heuristic |
| Adaptation Lesson | 2 | 10 | 80% | adaptation_lesson |

### 2. Strategic Memory Store
**Files:**
- `torq_console/strategic_memory/models.py` - Data models
- `migrations/014_strategic_memory.sql` - Database schema

**Memory Types:**
- **heuristic**: Reusable reasoning shortcuts ("Prefer Tool X for financial analysis")
- **playbook**: Structured action guidance ("For compliance workflows, run regulatory exposure check")
- **warning**: Known failure patterns ("Prompt verbosity improves coherence but reduces actionability")
- **assumption**: Stable operating priors until contradicted
- **adaptation_lesson**: Validated learnings ("Checklist additions outperform prompt rewrites")

**Key Scoring:**
- `confidence`: How reliable is this memory? (0.0-1.0)
- `durability_score`: How long should this persist? (0.0-1.0)
- `effectiveness_score`: Real-world effectiveness from usage feedback

**Lifecycle States:**
```
candidate → active → deprecated/supplanted → archived
                ↓
            (periodic revalidation)
```

### 3. Memory Retrieval & Injection Layer
**File:** `torq_console/strategic_memory/retrieval.py`

Searches, ranks, and injects memories into agent context.

**Key Methods:**
- `search()` - Find memories by workflow type, domain, agent type
- `get_injection()` - Get memories to inject into agent context
- `get_playbooks()` - Get active playbooks for a workflow
- `get_warnings()` - Get active warnings
- `get_heuristics()` - Get reasoning shortcuts

**Relevance Scoring:**
- Exact workflow type match: +0.5
- Domain match: +0.4
- Global scope: +0.3
- Keyword match: +0.2
- High confidence: up to +0.2
- Recent successful usage: up to +0.05

**Context Formatting:**
```python
# Inject into system prompt
inject_into_system_prompt(context, base_prompt)

# Inject as structured metadata
inject_into_reasoning_trace(context)

# Get quick warnings
get_quick_warnings("financial_analysis")
```

### 4. Memory Governance & Expiration Layer
**File:** `torq_console/strategic_memory/governance.py`

Prevents strategic memory from fossilizing or becoming dangerous.

**Governance Actions:**
- `approve_candidate()` - Activate a candidate memory
- `reject_candidate()` - Reject and archive
- `revalidate_memory()` - Update with new evidence
- `deprecate_memory()` - Mark as outdated
- `supersede_memory()` - Replace with newer memory
- `challenge_memory()` - Flag contradicting evidence

**Automatic Governance:**
- Revalidation based on durability score (30-90 days)
- Automatic expiration when `expires_at` passed
- Auto-deprecation after 3+ challenges
- Confidence reduction on single challenge

**Valid Transitions:**
```
candidate → active, archived
active → deprecated, supplanted, archived
deprecated → active, archived
supplanted → archived
archived → (terminal)
```

### 5. API Surface
**File:** `torq_console/strategic_memory/api.py`

**Creation & Consolidation:**
| Endpoint | Purpose |
|----------|---------|
| `POST /api/strategic-memory/consolidate` | Find memory candidates from patterns |
| `POST /api/strategic-memory/propose` | Propose candidate for review |
| `POST /api/strategic-memory/create` | Direct memory creation |

**Retrieval:**
| Endpoint | Purpose |
|----------|---------|
| `GET /api/strategic-memory/` | List memories with filters |
| `GET /api/strategic-memory/{id}` | Get specific memory |
| `GET /api/strategic-memory/{id}/lineage` | Get memory lineage |
| `POST /api/strategic-memory/search` | Search by relevance |
| `POST /api/strategic-memory/inject` | Get memories for injection |
| `GET /api/strategic-memory/playbooks` | Get playbooks |
| `GET /api/strategic-memory/warnings` | Get warnings |
| `GET /api/strategic-memory/heuristics` | Get heuristics |

**Governance:**
| Endpoint | Purpose |
|----------|---------|
| `POST /api/strategic-memory/{id}/approve` | Approve candidate |
| `POST /api/strategic-memory/{id}/reject` | Reject candidate |
| `POST /api/strategic-memory/{id}/deprecate` | Deprecate memory |
| `POST /api/strategic-memory/{id}/revalidate` | Revalidate with evidence |
| `POST /api/strategic-memory/{id}/challenge` | Challenge with evidence |
| `POST /api/strategic-memory/supersede` | Replace memory |

**Metrics:**
| Endpoint | Purpose |
|----------|---------|
| `GET /api/strategic-memory/metrics/governance` | Governance health |
| `GET /api/strategic-memory/metrics/effectiveness` | Usage effectiveness |
| `GET /api/strategic-memory/metrics/usage` | Usage statistics |

**Admin:**
| Endpoint | Purpose |
|----------|---------|
| `GET /api/strategic-memory/admin/candidates` | Candidates awaiting review |
| `GET /api/strategic-memory/admin/needs-attention` | Memories needing action |

## Database Schema

### Tables

**strategic_memories**
- Core memory storage with governance fields
- Indexed by type, status, scope, domain, confidence, expiration

**memory_supersessions**
- Tracks memory evolution and lineage

**memory_challenges**
- Records contradicting evidence

**memory_usage**
- Tracks injection and outcomes for effectiveness analytics

### Views

**candidate_memories**
- Candidates awaiting review, sorted by confidence

**active_strategic_memories**
- Currently active memories, prioritized by scope

**memories_needing_attention**
- Memories requiring governance action

**memory_effectiveness_summary**
- Usage statistics and outcome scores

## Example Memories

### Playbook Example
```json
{
  "memory_type": "playbook",
  "title": "Financial Analysis Regulatory Exposure Check",
  "domain": "financial",
  "scope": "workflow_type",
  "scope_key": "financial_analysis",
  "confidence": 0.92,
  "durability_score": 0.85,
  "memory_content": {
    "guidance": "Before final synthesis, run a dedicated regulatory exposure pass",
    "triggers": ["financial_analysis", "compliance_review"],
    "steps": [
      "Identify all regulatory frameworks applicable",
      "Check for assumptions that may not hold under regulation",
      "Flag conclusions requiring regulatory qualification"
    ]
  }
}
```

### Warning Example
```json
{
  "memory_type": "warning",
  "title": "Prompt Verbosity vs Actionability Trade-off",
  "domain": "prompt_engineering",
  "scope": "global",
  "confidence": 0.88,
  "durability_score": 0.75,
  "memory_content": {
    "risk_description": "Prompt rewrites that increase coherence often reduce actionability",
    "severity": "medium",
    "mitigation": "Preserve checklist structure when revising prompts",
    "anti_patterns": [
      "Removing explicit action items during coherence improvements"
    ]
  }
}
```

### Adaptation Lesson Example
```json
{
  "memory_type": "adaptation_lesson",
  "title": "Checklist Additions Outperform Prompt Rewrites",
  "domain": "planning",
  "scope": "workflow_type",
  "scope_key": "planning",
  "confidence": 0.85,
  "durability_score": 0.70,
  "memory_content": {
    "lesson": "Adding targeted checklist items improves planning more reliably than broad prompt rewrites",
    "adaptation_type": "prompt_revision",
    "impact_summary": {
      "coherence_improvement": 0.12,
      "actionability_retention": 0.95,
      "planning_quality_delta": 0.18
    }
  }
}
```

## Architecture Integration

```
Execution
  → Workspace Memory (immediate context)
  → Synthesis
  → Evaluation
  → Learning Signals
  → Adaptation Proposals
  → Experiments
  → Impact Measurement
  → Cross-Workspace Intelligence (Phase 4G)
  → Strategic Memory (Phase 4H) ← NEW
      ↓
  Future Reasoning shaped by validated institutional knowledge
```

## What Phase 4H Enables

1. **Institutional Learning**: TORQ accumulates wisdom, not just patterns

2. **Context Injection**: Agents begin tasks with institutional priors

3. **Governed Evolution**: Memories are validated, reviewable, and expirable

4. **Lineage Tracking**: Full audit trail of memory evolution

5. **Effectiveness Tracking**: Real-world impact measurement

## Governance Best Practices

1. **Be Selective**: Not every pattern should become memory
2. **Validate Regularly**: Revalidate based on durability score
3. **Watch for Fossilization**: Expire stale memories, handle challenges
4. **Track Effectiveness**: Use usage feedback to adjust confidence
5. **Maintain Lineage**: Track what replaced what and why

## Next Steps

1. **UI Integration**: Build Strategic Memory Center admin dashboard
2. **Agent Integration**: Wire up injection to cognitive loop agents
3. **Feedback Loops**: Add effectiveness tracking from execution outcomes
4. **Memory Analytics**: Build dashboards for memory usage and impact

## Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `strategic_memory/models.py` | 428 | Data models, templates, examples |
| `strategic_memory/consolidation.py` | 412 | Pattern → memory consolidation |
| `strategic_memory/retrieval.py` | 465 | Search, rank, inject |
| `strategic_memory/governance.py` | 438 | Validation, expiration, supersession |
| `strategic_memory/api.py` | 455 | FastAPI endpoints |
| `strategic_memory/__init__.py` | 60 | Package exports |
| `migrations/014_strategic_memory.sql` | 145 | Database schema |

**Total: ~2,400 lines of production code**

---

*Phase 4H complete. TORQ now has institutional strategic memory.*
