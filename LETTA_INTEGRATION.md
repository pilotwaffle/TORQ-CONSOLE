# Letta Memory Integration for TORQ Console

**Branch:** `claude/letta-memory-integration-011CUtyHaWVGi61W7QuCa7pw`
**Status:** 🚧 In Progress
**Date:** 2025-11-11

## Overview

Integration of Letta (formerly MemGPT) into TORQ Console to provide persistent memory, learning capabilities, and enhanced context management for Prince Flowers and other agents.

## Why Letta?

Letta provides:
- **Persistent Memory**: Remember conversations across sessions
- **Learning from Feedback**: Improve responses based on user interactions
- **Long-term Context**: Maintain context beyond single conversations
- **Multi-agent Memory**: Share knowledge between agents
- **Multiple Backends**: SQLite, PostgreSQL, Redis support

## Architecture

```
TORQ Console
├── Prince Flowers Agent
│   ├── Existing Prince Flowers Logic
│   └── Letta Memory Layer (NEW)
│       ├── Conversation Memory
│       ├── User Preferences
│       ├── Learned Patterns
│       └── Shared Agent Knowledge
├── Swarm Orchestrator
│   └── Letta Memory Coordinator (NEW)
└── Memory Backends
    ├── SQLite (default)
    ├── PostgreSQL (production)
    └── Redis (high-performance)
```

## Implementation Steps

### Phase 1: Core Integration ✅ (Complete)
- [x] Install Letta and dependencies
- [x] Create Letta memory wrapper
- [x] Integrate with Prince Flowers
- [x] Add configuration options

### Phase 2: Memory Features (Next)
- [ ] Conversation history tracking
- [ ] User preference learning
- [ ] Pattern recognition
- [ ] Multi-session context

### Phase 3: Agent Enhancement (Future)
- [ ] Cross-agent memory sharing
- [ ] Collaborative learning
- [ ] Advanced memory backends
- [ ] Memory analytics dashboard

## Key Features

### 1. Persistent Memory
```python
# Prince Flowers remembers previous conversations
prince.chat("I like Python for data science")
# ... later session ...
prince.chat("What do I prefer for data science?")
# Response: "You mentioned you like Python for data science"
```

### 2. Learning from Feedback
```python
# Prince Flowers learns from corrections
prince.chat("Write me a React component")
# User: "No, I prefer Vue.js"
# System learns preference
# Next time: Automatically suggests Vue.js
```

### 3. Long-term Context
```python
# Maintains context across multiple sessions
# Session 1: Discussing architecture
# Session 2: Continue from where we left off
# Session 3: Reference decisions from Session 1
```

## Technical Details

### Dependencies
```
letta==0.13.0
llama-index==0.14.8
trafilatura==2.0.0
markitdown==0.1.3
```

### Configuration
```python
# config.yaml
letta:
  enabled: true
  backend: sqlite  # or postgresql, redis
  db_path: ~/.torq/letta_memory.db
  memory_size: 10000  # Max memories to store
  learning_rate: 0.1
```

### API Integration
```python
from torq_console.memory import LettaMemoryManager

# Initialize memory manager
memory = LettaMemoryManager(
    agent_name="prince_flowers",
    backend="sqlite"
)

# Store memory
memory.add_memory("User prefers Python over JavaScript")

# Retrieve relevant memories
context = memory.get_relevant_context(query="What languages does user like?")

# Learn from feedback
memory.record_feedback(interaction_id, score=0.9)
```

## Benefits for TORQ Console

1. **Enhanced User Experience**
   - Agents remember user preferences
   - Continuity across sessions
   - Personalized responses

2. **Improved Agent Performance**
   - Learn from mistakes
   - Adapt to user patterns
   - Reduce repetitive explanations

3. **Enterprise Features**
   - Team knowledge sharing
   - Organizational learning
   - Context preservation

4. **Developer Experience**
   - Easy memory management
   - Flexible backends
   - Simple API

## Migration Path

### For Existing Users
1. Letta is **opt-in** by default
2. Existing conversations work without changes
3. Enable Letta in config to get memory features
4. Migrate existing data with provided tools

### For New Users
1. Letta enabled by default
2. Start with SQLite backend
3. Upgrade to PostgreSQL/Redis as needed

## Performance Considerations

- **Memory overhead**: ~50-100MB for SQLite backend
- **Query latency**: <50ms for memory retrieval
- **Storage growth**: ~1KB per memory entry
- **Optimizations**: LRU caching, batch operations, async I/O

## Security & Privacy

- **Local-first**: SQLite backend keeps data on device
- **Encryption**: Optional at-rest encryption
- **Data retention**: Configurable memory TTL
- **Export/Delete**: Full user control over data

## Testing Strategy

1. **Unit Tests**: Memory CRUD operations
2. **Integration Tests**: Prince Flowers with Letta
3. **Performance Tests**: Memory retrieval speed
4. **Load Tests**: Large memory stores

## Rollout Plan

1. **Alpha**: Internal testing (this PR)
2. **Beta**: Early adopters with opt-in flag
3. **GA**: Enabled by default with documentation
4. **Enterprise**: PostgreSQL/Redis backends

## Documentation

- User guide for memory features
- Developer guide for Letta API
- Configuration reference
- Migration guide

## Future Enhancements

1. **Vector Memory**: Semantic search in memories
2. **Memory Compression**: Archive old memories
3. **Cross-device Sync**: Cloud memory sync
4. **Memory Visualization**: Dashboard for memory insights

---

**Status**: Ready for implementation
**Next Steps**: Create Letta memory wrapper and integrate with Prince Flowers
