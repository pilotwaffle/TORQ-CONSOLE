# Phase 4H: Strategic Memory

**Status**: Beta
**Version**: v0.9.0-beta
**Last Updated**: March 8, 2026

---

## Overview

Strategic Memory is TORQ's long-term memory system that enables cross-session learning by injecting relevant past experiences into current missions. Unlike working memory (which holds current mission context), strategic memory persists across sessions and shapes reasoning over time.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    STRATEGIC MEMORY LAYER                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐      ┌─────────────┐│
│  │ Memory Store │ ───→ │Memory Router │ ───→ │  Memory     ││
│  │              │      │              │      │ Synthesizer ││
│  │ - Storage    │      │ - Retrieval  │      │             ││
│  │ - Indexing   │      │ - Scoring    │      │ - Combine   ││
│  │ - Quality    │      │ - Ranking    │      │ - Summarize ││
│  └──────────────┘      └──────────────┘      └─────────────┘│
│         ↑                                           ↓         │
│         │                                    Injection         │
│  Collection                                   Context           │
│  (from missions)                               (to missions)    │
└─────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Memory Store

**Location**: `torq_console/strategic_memory/memory_store.py`

Persistent storage and indexing of mission memories.

**Memory Schema:**
```python
{
    "id": str,
    "mission_id": str,
    "content": str,                    # Core memory content
    "summary": str,                    # Brief summary
    "tags": List[str],                 # Searchable tags
    "quality_score": float,            # 0.0 - 1.0
    "outcome": str,                    # success, failure, partial
    "created_at": datetime,
    "accessed_at": datetime,
    "access_count": int,               # Usage frequency
    "embedding": Optional[List[float]] # Vector embedding (future)
}
```

**API:**
```python
from torq_console.strategic_memory import MemoryStore

store = MemoryStore(supabase_client)

# Store memory from mission
memory_id = await store.store_memory(
    mission_id="mission_123",
    content="Market entry analysis revealed high regulatory barriers",
    summary="Regulatory barriers inhibit market entry",
    tags=["market-entry", "regulatory", "europe"],
    outcome="success",
    quality_score=0.91
)

# Retrieve memory
memory = await store.get_memory(memory_id)

# Search memories
memories = await store.search_memories(
    query="market entry regulatory",
    limit=5
)
```

---

### 2. Memory Router

**Location**: `torq_console/strategic_memory/memory_router.py`

Intelligent retrieval of relevant memories based on current mission context.

**Routing Strategy:**

1. **Keyword Matching**: Exact tag and content matches
2. **Semantic Similarity** (future): Vector embedding similarity
3. **Recency Bias**: Prefer recently accessed memories
4. **Quality Weighting**: Prefer high-quality-score memories

**API:**
```python
from torq_console.strategic_memory import MemoryRouter

router = MemoryRouter(supabase_client, memory_store)

# Get relevant memories for current mission
memories = await router.get_relevant_memories(
    mission_context={
        "objective": "Assess market entry for Germany",
        "reasoning_strategy": "risk_first",
        "tags": ["market-entry", "europe"]
    },
    limit=10
)

# Memories ranked by relevance score
for memory in memories:
    print(f"{memory['summary']} (relevance: {memory['relevance_score']})")
```

---

### 3. Memory Synthesizer

**Location**: `torq_console/strategic_memory/memory_synthesizer.py`

Combines related memories into coherent context for mission injection.

**Synthesis Types:**

| Type | Purpose | Output |
|------|---------|--------|
| `summary` | Consolidate related memories | Single summarized memory |
| `comparison` | Compare outcomes across memories | Comparison table |
| `trends` | Identify patterns across memories | Trend analysis |
| `recommendations` | Extract actionable recommendations | Recommendation list |

**API:**
```python
from torq_console.strategic_memory import MemorySynthesizer

synthesizer = MemorySynthesizer(supabase_client)

# Synthesize related memories
synthesis = await synthesizer.synthesize(
    memories=related_memories,
    synthesis_type="summary",
    context={
        "current_objective": "Assess market entry for Germany"
    }
)

# Output:
# {
#     "type": "summary",
#     "content": "Across 3 European market entry missions, regulatory barriers...",
#     "key_insights": [...],
#     "recommendations": [...],
#     "confidence": 0.87
# }
```

---

## Memory Quality Scoring

Memories are scored on multiple dimensions:

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Outcome Success | 0.3 | Mission succeeded? |
| Information Richness | 0.25 | Depth of content |
| Applicability | 0.2 | Generalizability |
| Recency | 0.15 | How recent? |
| Usage Frequency | 0.1 | How often accessed? |

**Scoring Function:**
```python
quality_score = (
    outcome_success * 0.3 +
    information_richness * 0.25 +
    applicability * 0.2 +
    recency_score * 0.15 +
    usage_frequency * 0.1
)
```

---

## Memory Injection

### Injection Points

Memories are injected into missions at key points:

1. **Mission Creation**: Provide context from similar past missions
2. **Node Execution**: Inject relevant task-specific memories
3. **Decision Gates**: Provide outcomes from similar decisions
4. **Post-Completion**: Extract new memories from mission results

### Injection Format

```python
{
    "strategic_context": {
        "related_missions": [
            {
                "mission_id": "mission_456",
                "summary": "European market entry assessment",
                "outcome": "success",
                "key_learnings": [
                    "Regulatory approval takes 6-8 months",
                    "Local partnerships essential"
                ]
            }
        ],
        "patterns": [
            "Markets with GDPR-like regulations have 40% longer entry timelines"
        ],
        "recommendations": [
            "Engage legal counsel early",
            "Plan extended timeline for regulatory approval"
        ]
    }
}
```

---

## Data Model

### Strategic Memories Table

```sql
CREATE TABLE strategic_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL REFERENCES missions(id),
    content TEXT NOT NULL,
    summary TEXT NOT NULL,
    tags TEXT[] DEFAULT '{}',
    quality_score DECIMAL(3,2) DEFAULT 0.5,
    outcome VARCHAR(20),  -- success, failure, partial
    created_at TIMESTAMPTZ DEFAULT NOW(),
    accessed_at TIMESTAMPTZ DEFAULT NOW(),
    access_count INTEGER DEFAULT 0,
    embedding VECTOR(1536),  -- Optional, for semantic search

    INDEX idx_strategic_memories_tags (tags),
    INDEX idx_strategic_memories_quality (quality_score DESC),
    INDEX idx_strategic_memories_outcome (outcome)
);
```

---

## API Reference

### Complete Workflow

```python
from torq_console.strategic_memory import (
    MemoryStore,
    MemoryRouter,
    MemorySynthesizer
)

# Initialize components
store = MemoryStore(supabase_client)
router = MemoryRouter(supabase_client, store)
synthesizer = MemorySynthesizer(supabase_client)

# 1. Store memory after mission completion
memory_id = await store.store_memory(
    mission_id="mission_123",
    content="Market entry analysis for Germany revealed...",
    summary="German market entry requires GDPR compliance",
    tags=["market-entry", "germany", "gdpr"],
    outcome="success",
    quality_score=0.91
)

# 2. Retrieve relevant memories for new mission
memories = await router.get_relevant_memories(
    mission_context={
        "objective": "Assess market entry for Austria",
        "reasoning_strategy": "analytical",
        "tags": ["market-entry", "europe"]
    },
    limit=10
)

# 3. Synthesize for injection
synthesis = await synthesizer.synthesize(
    memories=memories,
    synthesis_type="recommendations"
)

# 4. Inject into mission context
mission_context = {
    "objective": "Assess market entry for Austria",
    "strategic_memory": synthesis
}
```

---

## Maturity: Beta

**Implemented:**
- Memory storage with quality scoring
- Tag-based retrieval
- Basic synthesis (summary, recommendations)

**In Progress:**
- Semantic search via embeddings
- Trend analysis synthesis
- Automated memory extraction

**Next:**
- Advanced synthesis types
- Memory decay/freshness management
- Cross-mission pattern recognition

---

## Future Enhancements

### Short Term
- Embedding-based semantic search
- Automated memory extraction from mission outcomes
- Memory freshness scoring

### Long Term
- Cross-mission pattern recognition
- Predictive memory injection (anticipate needs)
- Memory consolidation (merge related memories)

---

## See Also

- [Phase 4F Adaptive Cognition Loop](docs/PHASE_4F_ADAPTIVE_COGNITION_LOOP.md) — Learning system
- [Phase 5 Mission Graph Planning](docs/PHASE_5_MISSION_GRAPH_PLANNING.md) — Mission execution
- [Architecture Index](docs/ARCHITECTURE_INDEX.md) — System overview
