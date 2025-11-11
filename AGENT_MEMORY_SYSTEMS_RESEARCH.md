# Agent Memory Systems - Comprehensive Research & Comparison

**Date:** 2025-11-11
**Purpose:** Research and compare memory systems for TORQ Console agents
**Systems Analyzed:** Letta, Zep, Mem0, LangGraph+LlamaIndex

---

## Executive Summary

This document provides comprehensive research and comparison of four leading agent memory systems to enhance TORQ Console's Prince Flowers and swarm agents with persistent memory, learning capabilities, and long-term context management.

### Quick Recommendation Matrix

| Use Case | Recommended System | Why |
|----------|-------------------|-----|
| **Multi-agent Orchestration** | **Letta** | Best swarm orchestrator integration, shared memory |
| **Enterprise Knowledge Graphs** | **Zep** | Temporal knowledge graphs, fact extraction |
| **Rapid Prototyping** | **Mem0** | Simplest API, fastest setup |
| **Document-Heavy RAG** | **LangGraph+LlamaIndex** | Advanced document processing, complex workflows |
| **Hybrid Solution** | **Letta + Zep** | Memory + Knowledge graphs |

---

## 1. Letta (formerly MemGPT)

### Overview
- **GitHub:** https://github.com/letta-ai/letta
- **Version:** 0.13.0
- **License:** Apache 2.0
- **Company:** Letta AI
- **Focus:** AI agents with persistent memory and learning

### Key Features

#### Memory Architecture
- **Core Memory**: Quick-access working memory for agent personality and key facts
- **Recall Memory**: Long-term storage with semantic search
- **Archival Memory**: Unlimited storage for historical data
- **Memory Editing**: Agent can modify its own memory

#### Multi-agent Support
- **Shared Memory**: Agents can share knowledge bases
- **Agent-to-Agent Communication**: Built-in messaging
- **Hierarchical Agents**: Parent-child agent relationships
- **Memory Isolation**: Per-agent or shared memory modes

#### Technical Capabilities
- **LLM Agnostic**: Works with OpenAI, Anthropic, local models
- **Backend Options**: SQLite, PostgreSQL, Redis
- **Function Calling**: Native tool use integration
- **Streaming**: Real-time response streaming

### Integration with TORQ Console

#### Strengths
✅ **Perfect for Swarm Orchestrator**: Multi-agent architecture matches TORQ's swarm system
✅ **Shared Knowledge Base**: Prince Flowers and Analysis Agent can share memories
✅ **Flexible Backends**: SQLite for dev, PostgreSQL for production
✅ **Active Development**: Frequent updates and improvements

#### Implementation Path
1. ✅ **Phase 1 (Complete)**: Core integration with Prince Flowers
2. **Phase 2**: Extend to all swarm agents
3. **Phase 3**: Shared memory pools for agent collaboration
4. **Phase 4**: Memory analytics dashboard

#### Code Example
```python
from torq_console.memory import LettaMemoryManager

# Initialize memory for Prince Flowers
memory = LettaMemoryManager(
    agent_name="prince_flowers",
    backend="postgresql"  # Production backend
)

# Add conversational memory
await memory.add_memory(
    "User is building a FastAPI application for data analysis",
    metadata={"project": "data_api", "stack": "python"}
)

# Get relevant context
context = await memory.get_relevant_context(
    query="What is user working on?",
    max_memories=5
)

# Agent learns from feedback
await memory.record_feedback(
    interaction_id="conv_123",
    score=0.9,
    feedback_type="helpful"
)
```

### Performance Characteristics
- **Memory Retrieval**: ~50-100ms
- **Context Generation**: ~200-500ms
- **Storage Overhead**: ~1KB per memory
- **Concurrent Agents**: 100+ agents simultaneously

### Cost Analysis
- **Open Source**: Free
- **Cloud Hosting**: ~$50-200/month (PostgreSQL + Redis)
- **Inference**: Standard LLM API costs

---

## 2. Zep

### Overview
- **GitHub:** https://github.com/getzep/zep
- **Version:** Latest (actively developed)
- **License:** Apache 2.0
- **Company:** Getzep
- **Focus:** Long-term memory with knowledge graphs

### Key Features

#### Knowledge Graph Architecture
- **Temporal Knowledge Graphs**: Time-aware fact storage
- **Entity Extraction**: Automatic entity and relationship detection
- **Fact Clustering**: Groups related facts together
- **Graph Queries**: GraphQL-style memory queries

#### Advanced Memory Operations
- **Fact Verification**: Detect contradictions in memory
- **Memory Consolidation**: Merge redundant memories
- **Temporal Queries**: "What did user say last week?"
- **Semantic Search**: Vector-based memory retrieval

#### Enterprise Features
- **Multi-user Support**: Isolated memory per user/session
- **Privacy Controls**: Data retention policies
- **Analytics Dashboard**: Built-in memory insights
- **Cloud or Self-hosted**: Flexible deployment

### Integration with TORQ Console

#### Strengths
✅ **Temporal Knowledge**: Perfect for tracking project evolution
✅ **Enterprise Focus**: Built for production workloads
✅ **Fact Extraction**: Automatically builds knowledge from conversations
✅ **Analytics**: Built-in dashboards for memory insights

#### Best Use Cases for TORQ
1. **Project Context Tracking**: Remember project decisions over time
2. **Team Collaboration**: Track who said what and when
3. **Knowledge Base Building**: Accumulate organizational knowledge
4. **Fact Verification**: Ensure consistency in recommendations

#### Code Example
```python
from zep_python import ZepClient

# Initialize Zep client
zep = ZepClient(base_url="https://api.getzep.com", api_key="...")

# Add session memory
await zep.memory.add_session(
    session_id="prince_flowers_session",
    memory={
        "messages": [{
            "role": "user",
            "content": "We're using FastAPI for our new microservice"
        }],
        "metadata": {"project": "microservice_api"}
    }
)

# Get temporal knowledge graph
knowledge_graph = await zep.memory.get_session_facts(
    session_id="prince_flowers_session"
)

# Query: "What framework are we using?"
# Zep returns: "FastAPI" with temporal context
```

### Performance Characteristics
- **Fact Extraction**: ~1-2s per conversation
- **Graph Queries**: <100ms
- **Storage**: ~5KB per conversation (with facts)
- **Scalability**: Millions of facts per graph

### Cost Analysis
- **Open Source Core**: Free
- **Cloud Service**: $99-499/month (includes hosting)
- **Self-hosted**: ~$100-300/month (infrastructure)

---

## 3. Mem0

### Overview
- **GitHub:** https://github.com/mem0ai/mem0
- **Version:** Latest
- **License:** MIT
- **Company:** Mem0 AI
- **Focus:** Simplest possible memory layer

### Key Features

#### Simplicity First
- **One-line Integration**: `memory.add()` and `memory.search()`
- **Minimal Configuration**: Works out of the box
- **No Setup Required**: SQLite by default
- **Python-first**: Pythonic API design

#### Memory Operations
- **Add Memories**: Simple key-value storage with metadata
- **Semantic Search**: Vector-based retrieval
- **Memory Decay**: Time-based importance weighting
- **Memory Merging**: Combines similar memories

#### Integration Features
- **LangChain Integration**: Drop-in replacement for LangChain memory
- **Multiple Backends**: Qdrant, Pinecone, ChromaDB
- **Custom Embeddings**: Bring your own model
- **Lightweight**: Minimal dependencies

### Integration with TORQ Console

#### Strengths
✅ **Fastest Setup**: Get memory working in minutes
✅ **Lightweight**: Minimal overhead
✅ **Perfect for Prototyping**: Test memory features quickly
✅ **Easy Migration**: Start simple, upgrade to Letta/Zep later

#### Best Use Cases for TORQ
1. **Quick Experiments**: Test memory features rapidly
2. **Simple Agents**: Single-purpose agents with basic memory
3. **Development/Testing**: Fast iteration cycles
4. **Proof of Concepts**: Validate memory architecture

#### Code Example
```python
from mem0 import Memory

# Initialize (that's it!)
memory = Memory()

# Add memory
memory.add(
    "User prefers Python for scripting tasks",
    user_id="prince_flowers_user"
)

# Search memory
results = memory.search(
    "What languages does user prefer?",
    user_id="prince_flowers_user"
)

# That's really all there is to it!
```

### Performance Characteristics
- **Add Memory**: <10ms
- **Search**: <50ms
- **Storage**: ~500 bytes per memory
- **Scalability**: Thousands of memories (not millions)

### Cost Analysis
- **Open Source**: Free
- **Self-hosted**: ~$20-50/month (minimal resources)
- **Vector DB Hosting**: $0-100/month (depending on backend)

---

## 4. LangGraph + LlamaIndex

### Overview
- **LangGraph**: Workflow orchestration for agents
- **LlamaIndex**: Document indexing and RAG
- **Combined**: Powerful document-centric memory system

### Key Features

#### LangGraph Capabilities
- **State Graphs**: Model complex agent workflows
- **Checkpointing**: Save and restore agent state
- **Branching Logic**: Conditional execution paths
- **Human-in-the-Loop**: Request human input mid-workflow

#### LlamaIndex Memory
- **Document Ingestion**: PDFs, Word, Web pages, etc.
- **Vector Indexes**: Multiple index types (tree, keyword, vector)
- **Query Engines**: Natural language queries over documents
- **Agent Memory**: Document-based context

#### Combined Power
- **Stateful RAG**: RAG with conversation history
- **Multi-step Reasoning**: Complex document analysis
- **Memory-augmented Workflows**: Documents + conversation context
- **Production-grade**: Battle-tested at scale

### Integration with TORQ Console

#### Strengths
✅ **Document Processing**: Already have LlamaIndex in Letta stack
✅ **Complex Workflows**: Perfect for multi-step agent tasks
✅ **RAG Excellence**: Best-in-class document retrieval
✅ **Checkpointing**: Save agent state mid-workflow

#### Best Use Cases for TORQ
1. **Code Analysis**: Index and query codebase
2. **Documentation**: Spec-Kit with document memory
3. **Research Agents**: Document-heavy research tasks
4. **Multi-step Tasks**: Complex workflows with checkpoints

#### Code Example
```python
from langgraph.graph import StateGraph
from llama_index import VectorStoreIndex, Document

# LlamaIndex: Build document memory
documents = [
    Document(text="TORQ Console uses FastAPI for web UI"),
    Document(text="Prince Flowers is the main conversational agent")
]
index = VectorStoreIndex.from_documents(documents)

# LangGraph: Define agent workflow with memory
workflow = StateGraph()

@workflow.node
async def retrieve_context(state):
    query = state["query"]
    context = index.as_query_engine().query(query)
    state["context"] = str(context)
    return state

@workflow.node
async def generate_response(state):
    response = await prince_flowers.chat(
        state["query"],
        context=state["context"]
    )
    state["response"] = response
    return state

# Execute workflow
result = await workflow.run({"query": "Tell me about TORQ Console"})
```

### Performance Characteristics
- **Index Build**: Varies by document size
- **Query**: ~100-500ms
- **Checkpoint Save**: <100ms
- **Scalability**: Millions of documents

### Cost Analysis
- **Open Source**: Free
- **Vector Storage**: $50-200/month (Pinecone, Weaviate)
- **Compute**: Depends on document processing volume

---

## Comprehensive Comparison Matrix

| Feature | Letta | Zep | Mem0 | LangGraph+LlamaIndex |
|---------|-------|-----|------|---------------------|
| **Ease of Setup** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **Multi-agent** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| **Knowledge Graphs** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐ |
| **Document RAG** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Enterprise Ready** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| **Learning** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Temporal Queries** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐ |
| **API Simplicity** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **Performance** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Scalability** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Community** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Documentation** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## Recommended Integration Strategy for TORQ Console

### Phase 1: Foundation (Current - Letta)
✅ **Status**: Implemented
**Focus**: Core memory for Prince Flowers

**Why Letta First:**
- Perfect match for swarm orchestrator
- Multi-agent support built-in
- Flexible backend options
- Already integrated!

### Phase 2: Enterprise Knowledge (Next - Zep)
🚧 **Timeline**: Q1 2026
**Focus**: Temporal knowledge graphs

**Use Cases:**
- Project context tracking
- Team collaboration memory
- Fact verification
- Knowledge base building

**Integration:**
```python
# Hybrid approach
letta_memory = get_memory_manager()  # For conversations
zep_memory = ZepClient()  # For knowledge graphs

# Store conversation in Letta
await letta_memory.add_memory("User discussed microservices")

# Extract facts to Zep knowledge graph
facts = await zep_memory.extract_facts(conversation)
```

### Phase 3: Rapid Prototyping (Parallel - Mem0)
📅 **Timeline**: Q2 2026
**Focus**: Simple memory for new agents

**Use Cases:**
- Quick agent prototypes
- Testing memory features
- Lightweight agents
- Development/testing

**Integration:**
```python
# Use Mem0 for simple agents
if agent_type == "simple":
    memory = Mem0Memory()
else:
    memory = LettaMemoryManager()
```

### Phase 4: Document Intelligence (Future - LangGraph+LlamaIndex)
📅 **Timeline**: Q2-Q3 2026
**Focus**: Document-centric memory

**Use Cases:**
- Spec-Kit enhancement
- Code analysis agents
- Research agents
- Documentation agents

**Integration:**
```python
# Use LlamaIndex for document memory
doc_index = build_codebase_index()

# Use LangGraph for complex workflows
workflow = build_analysis_workflow(doc_index, letta_memory)
```

---

## Hybrid Architecture Proposal

### Recommended Multi-tier Memory System

```
TORQ Console Memory Architecture
├── Tier 1: Conversational Memory (Letta)
│   ├── Prince Flowers
│   ├── Analysis Agent
│   ├── Research Agent
│   └── Shared memory pools
│
├── Tier 2: Knowledge Graphs (Zep)
│   ├── Project facts
│   ├── Team knowledge
│   ├── Temporal context
│   └── Fact verification
│
├── Tier 3: Document Memory (LlamaIndex)
│   ├── Codebase index
│   ├── Documentation
│   ├── Spec-Kit documents
│   └── Research papers
│
└── Tier 4: Workflow State (LangGraph)
    ├── Multi-step tasks
    ├── Checkpoints
    ├── Human-in-the-loop
    └── Complex reasoning
```

### Memory Routing Logic

```python
def get_memory_system(context):
    """Route to appropriate memory system based on context."""

    if context.type == "conversation":
        return letta_memory

    elif context.type == "knowledge_query":
        return zep_knowledge_graph

    elif context.type == "document_search":
        return llamaindex

    elif context.type == "complex_workflow":
        return langgraph_state

    else:
        # Default to Letta
        return letta_memory
```

---

## Implementation Roadmap

### Q4 2025 (Current)
- [x] Letta integration complete
- [x] Prince Flowers with memory
- [x] Documentation and tests
- [ ] Deploy to production

### Q1 2026
- [ ] Zep integration
- [ ] Knowledge graph for projects
- [ ] Temporal queries
- [ ] Memory analytics dashboard

### Q2 2026
- [ ] Mem0 for simple agents
- [ ] LangGraph workflow engine
- [ ] Document memory with LlamaIndex
- [ ] Hybrid memory routing

### Q3 2026
- [ ] Full multi-tier memory system
- [ ] Cross-system memory sync
- [ ] Advanced analytics
- [ ] Enterprise features

---

## Cost Analysis (Annual)

### Small Team (1-10 users)
- **Letta (self-hosted)**: $600-1,200/year
- **Zep (cloud)**: $1,200-6,000/year
- **Mem0 (self-hosted)**: $300-600/year
- **LangGraph+LlamaIndex**: $600-2,400/year
- **Total**: $2,700-10,200/year

### Enterprise (100+ users)
- **Letta (cloud/managed)**: $6,000-12,000/year
- **Zep (enterprise)**: $12,000-36,000/year
- **Mem0 (managed)**: $2,400-6,000/year
- **LangGraph+LlamaIndex**: $6,000-24,000/year
- **Total**: $26,400-78,000/year

---

## Conclusion & Next Steps

### Primary Recommendation: **Letta + Zep Hybrid**

✅ **Letta** for core conversational memory (already implemented)
✅ **Zep** for enterprise knowledge graphs (next priority)
✅ **Mem0** for rapid prototyping (when needed)
✅ **LangGraph+LlamaIndex** for document intelligence (future)

### Immediate Actions

1. ✅ **Letta Integration**: Complete and tested
2. **Production Deployment**: Deploy Letta to production
3. **Zep Evaluation**: Set up Zep POC
4. **User Testing**: Get feedback on memory features
5. **Metrics**: Track memory usage and performance

### Success Metrics

- **User Satisfaction**: Memory recall accuracy
- **Performance**: <100ms memory retrieval
- **Adoption**: % of conversations using memory
- **Quality**: Relevance of retrieved context
- **Learning**: Improvement over time

---

**Document Status**: ✅ Complete
**Last Updated**: 2025-11-11
**Next Review**: After Letta production deployment
