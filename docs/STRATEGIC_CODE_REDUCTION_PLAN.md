# Strategic Code Reduction Plan for TORQ Console

## Analysis Summary

**Current State:**
- 463 Python files
- 183,472 lines of code
- 75 agent-related files
- 23 files over 1000 lines
- Estimated 1112K lines (20%) could be eliminated

**Target:** 50% code reduction while maintaining functionality

## Phase 1: Agent Consolidation (30% reduction)

### Current Agent Issues
- **75 agent files** scattered across multiple directories
- **Duplicate functionality** between agents
- **Inconsistent interfaces** and patterns
- **Prince Flowers canonical agent** already selected (4,541 lines)

### Consolidation Strategy

#### 1.1 Create Core Agent Architecture
```
torq_console/agents/
├── core/
│   ├── __init__.py              # Core agent interfaces
│   ├── base_agent.py           # Base agent class
│   ├── agent_manager.py        # Central agent manager
│   └── agent_registry.py        # Agent registration
├── canonical/
│   ├── prince_flowers.py      # Already consolidated (4,541 lines)
│   └── ...
├── specialized/
│   ├── evaluation_agent.py   # From eval system
│   ├── workflow_agent.py    # For PAE workflows
│   └── ...
└── tools/
    ├── consolidated_tools.py   # Merge 12 tools into 5-7
    └── ...
```

#### 1.2 Agent Reduction Steps
1. **Identify core agent patterns**
   - Analysis: 75 agent files
   - Categories: Core, Specialized, Tools, Tests
   - Target: Reduce to 15-20 files

2. **Create common interfaces**
   - `BaseAgent` class with common methods
   - `AgentCapability` enum for type system
   - Standard agent lifecycle methods

3. **Consolidate overlapping functionality**
   - Merge search agents
   - Combine LLM providers
   - Unify tool interfaces

## Phase 2: Tool Consolidation (10% reduction)

### Current Tool Issues
- **12+ tool files** in `torq_console/agents/tools/`
- **Overlapping functionality** between tools
- **Duplicate interface patterns**

### Consolidation Strategy

#### 2.1 Tool Categories
1. **Core Tools** (3 files)
   - File operations
   - Search capabilities
   - System commands

2. **Integration Tools** (2 files)
   - MCP client
   - LLM providers
   - External APIs

3. **Specialized Tools** (2 files)
   - Multi-tool composition
   - Web search
   - Content synthesis

## Phase 3: File Restructuring (10% reduction)

### Target Files >1000 lines
1. `torq_console/ui/web.py` (2,365 lines) → Split into components
2. `maxim_integration/phase*.py` (9 files, ~12K lines) → Archive/restructure
3. `torq_console/ui/command_palette.py` (1,794 lines) → Extract components

### Restructuring Strategy
- **Extract reusable components**
- **Create focused modules**
- **Implement lazy loading**

## Implementation Priority

### Week 1: Agent Architecture
1. Design core agent interfaces
2. Create base agent class
3. Implement agent registry
4. Begin consolidating agent files

### Week 2: Tool Consolidation
1. Map tool functionality
2. Design consolidated interfaces
3. Implement merged tools
4. Update agent dependencies

### Week 3: File Splitting
1. Identify large files for splitting
2. Design module boundaries
3. Extract components
4. Update imports

## Expected Outcomes

### Code Reduction Metrics
- **Before:** 183,472 lines
- **After:** ~91,736 lines (50% reduction)
- **Files Reduced:** 463 → ~300 files

### Quality Improvements
- **Better maintainability**
- **Clearer architecture**
- **Reduced complexity**
- **Faster build times**

### Maintenance Benefits
- **Easier testing**
- **Simpler debugging**
- **Cleaner dependencies**
- **Better documentation**

## Risk Mitigation

### 1. Feature Preservation
- **Comprehensive testing** before consolidation
- **Feature parity validation**
- **Backward compatibility layers**

### 2. Incremental Implementation
- **One module at a time**
- **Continuous integration**
- **Rollback capability**

### 3. Documentation
- **Architecture diagrams**
- **Migration guides**
- **API documentation**

## Success Metrics

### Quantitative
- **Lines of code**: 183,472 → <92,000
- **Python files**: 463 → <300
- **Agent files**: 75 → 15-20
- **Tool files**: 12+ → 5-7

### Qualitative
- **Reduced complexity**
- **Improved readability**
- **Better testability**
- **Clearer separation of concerns**

## Next Steps

1. **Get stakeholder approval** for consolidation plan
2. **Create detailed migration schedules**
3. **Begin Phase 1: Agent Consolidation**
4. **Track progress with metrics**
5. **Validate each phase before proceeding**

---

*This plan represents a 6-week strategic initiative to achieve 50% code reduction while improving system quality and maintainability.*