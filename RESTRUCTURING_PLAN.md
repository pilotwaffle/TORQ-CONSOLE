# TORQ CONSOLE Phase 3: File Restructuring Plan

## Overview
This document outlines the comprehensive plan to restructure 23 large files (>1000 lines) into smaller, more manageable modules for improved maintainability, readability, and performance.

## Files to Restructure (23 total)

### Priority 1: Largest Files (>2000 lines)
1. `torq_console/agents/torq_prince_flowers.py` (4,540 lines)
2. `torq_console/ui/web.py` (2,365 lines)
3. `maxim_integration/phase2_professional_task_optimization.py` (2,096 lines)

### Priority 2: Large Files (1500-2000 lines)
4. `torq_console/ui/command_palette.py` (1,793 lines)
5. `maxim_integration/phase1_quality_consistency_framework.py` (1,663 lines)
6. `torq_console/core/chat_manager.py` (1,615 lines)
7. `maxim_integration/advanced_agent_growth_tests.py` (1,581 lines)
8. `maxim_integration/phase2_evolutionary_learning.py` (1,527 lines)
9. `maxim_integration/phase3_system_integration_testing.py` (1,424 lines)

### Priority 3: Medium Files (1000-1500 lines)
10. `torq_console/llm/providers/websearch.py` (1,314 lines)
11. `torq_console/ui/inline_editor.py` (1,229 lines)
12. `torq_console/utils/app_builder.py` (1,183 lines)
13. `maxim_integration/observe_system.py` (1,172 lines)
14. `torq_console/agents/tools/multi_tool_composition_tool.py` (1,143 lines)
15. `torq_console/agents/tools/mcp_client_tool.py` (1,141 lines)
16. `torq_integration.py` (1,137 lines)
17. `archive/agents/enhanced_prince_flowers_v2.py` (1,119 lines)
18. `maxim_integration/phase1_learning_velocity_enhancement.py` (1,085 lines)
19. `torq_console/agents/torq_search_master.py` (1,071 lines)
20. `maxim_integration/phase4_production_deployment_monitoring.py` (1,071 lines)
21. `maxim_integration/agent_growth_monitoring_dashboard.py` (1,061 lines)
22. `torq_console/core/context_manager.py` (1,050 lines)
23. `maxim_integration/human_in_the_loop_evaluation.py` (1,041 lines)
24. `maxim_integration/prompt_optimization_workflow.py` (1,001 lines)

## Restructuring Strategy

### 1. torq_console/ui/web.py (2,365 lines) → Split into:
```
torq_console/ui/web/
├── __init__.py              # Main entry point, FastAPI app
├── routes/
│   ├── __init__.py
│   ├── api.py              # API routes
│   ├── websocket.py        # WebSocket handlers
│   ├── files.py            # File management routes
│   └── collab.py           # Collaboration routes
├── components/
│   ├── __init__.py
│   ├── layout.py           # Layout components
│   ├── editor.py           # Editor components
│   ├── chat.py             # Chat components
│   └── collab.py           # Collaboration components
├── handlers/
│   ├── __init__.py
│   ├── requests.py         # Request handlers
│   ├── responses.py        # Response utilities
│   └── auth.py             # Authentication handlers
└── utils/
    ├── __init__.py
    ├── session.py          # Session management
    ├── security.py         # Security utilities
    └── static.py           # Static file handling
```

### 2. torq_console/ui/command_palette.py (1,793 lines) → Split into:
```
torq_console/ui/command_palette/
├── __init__.py                     # Main entry point
├── commands/
│   ├── __init__.py
│   ├── core.py                     # Core command classes
│   ├── builtin.py                  # Built-in commands
│   ├── registry.py                 # Command registration
│   └── categories.py               # Command categories
├── search/
│   ├── __init__.py
│   ├── fuzzy.py                    # Fuzzy search implementation
│   ├── ranking.py                  # Search ranking algorithms
│   └── filters.py                  # Command filters
├── ui/
│   ├── __init__.py
│   ├── palette.py                  # Main palette UI
│   ├── renderer.py                 # UI rendering
│   └── keyboard.py                 # Keyboard handling
├── execution/
│   ├── __init__.py
│   ├── executor.py                 # Command execution
│   ├── validation.py               # Parameter validation
│   └── history.py                  # Command history
└── utils/
    ├── __init__.py
    ├── shortcuts.py                # Keyboard shortcuts
    └── context.py                  # Context evaluation
```

### 3. maxim_integration/phase*.py files (~12K lines total) → Split into:
```
maxim_integration/
├── core/
│   ├── __init__.py
│   ├── base.py                     # Base classes and interfaces
│   ├── config.py                   # Configuration management
│   └── metrics.py                  # Metrics collection
├── phases/
│   ├── __init__.py
│   ├── phase1_framework.py         # Phase 1: Quality framework
│   ├── phase2_optimization.py      # Phase 2: Task optimization
│   ├── phase2_learning.py          # Phase 2: Evolutionary learning
│   ├── phase3_integration.py       # Phase 3: System integration
│   └── phase4_monitoring.py        # Phase 4: Production monitoring
├── agents/
│   ├── __init__.py
│   ├── growth.py                   # Agent growth logic
│   ├── testing.py                  # Testing framework
│   └── monitoring.py               # Monitoring agents
├── evaluation/
│   ├── __init__.py
│   ├── human_loop.py               # Human-in-the-loop evaluation
│   ├── metrics.py                  # Evaluation metrics
│   └── reports.py                  # Report generation
├── optimization/
│   ├── __init__.py
│   ├── prompt_optimizer.py         # Prompt optimization
│   ├── workflow_optimizer.py       # Workflow optimization
│   └── performance.py              # Performance optimization
└── utils/
    ├── __init__.py
    ├── data_processing.py          # Data processing utilities
    ├── visualization.py            # Visualization tools
    └── dashboard.py                # Dashboard components
```

### 4. torq_console/agents/torq_prince_flowers.py (4,540 lines) → Split into:
```
torq_console/agents/torq_prince_flowers/
├── __init__.py                     # Main agent entry point
├── core/
│   ├── __init__.py
│   ├── agent.py                    # Core agent implementation
│   ├── memory.py                   # Memory management
│   ├── conversation.py             # Conversation handling
│   └── state.py                    # State management
├── capabilities/
│   ├── __init__.py
│   ├── reasoning.py                # Reasoning capabilities
│   ├── planning.py                 # Planning capabilities
│   ├── execution.py                # Task execution
│   └── learning.py                 # Learning capabilities
├── tools/
│   ├── __init__.py
│   ├── websearch.py                # Web search integration
│   ├── file_ops.py                 # File operations
│   └── analysis.py                 # Analysis tools
├── integrations/
│   ├── __init__.py
│   ├── mcp.py                      # MCP client integration
│   ├── llm.py                      # LLM provider integration
│   └── external_api.py             # External API integration
└── utils/
    ├── __init__.py
    ├── context.py                  # Context management
    ├── logging.py                  # Enhanced logging
    └── performance.py              # Performance monitoring
```

## Implementation Steps

### Phase 1: Directory Structure Setup
1. Create all new directory structures
2. Set up `__init__.py` files with proper imports
3. Create backward compatibility shims

### Phase 2: File Analysis and Planning
1. Analyze each large file for logical boundaries
2. Identify classes, functions, and dependencies
3. Plan splitting strategy for each file

### Phase 3: Systematic Splitting (Priority Order)
1. **Priority 1**: Split the 3 largest files
2. **Priority 2**: Split the next 6 large files
3. **Priority 3**: Split the remaining 14 medium files

### Phase 4: Import Updates and Testing
1. Update all imports across the codebase
2. Ensure backward compatibility
3. Run comprehensive test suite
4. Fix any broken imports or dependencies

### Phase 5: Documentation and Migration Guide
1. Create migration guide
2. Update API documentation
3. Add deprecation warnings where needed

## Benefits of Restructuring

### Improved Maintainability
- Smaller, focused modules are easier to understand and modify
- Clear separation of concerns
- Reduced cognitive load for developers

### Better Performance
- Enable lazy loading of modules
- Reduced memory footprint
- Faster import times

### Enhanced Testing
- Smaller modules are easier to test in isolation
- Better test coverage and debugging
- Easier to mock dependencies

### Code Organization
- Logical grouping of related functionality
- Clear module boundaries and responsibilities
- Better navigation and IDE support

## Backward Compatibility Strategy

### 1. Compatibility Shims
Create `__init__.py` files that re-export all original classes and functions:

```python
# Example: torq_console/ui/web.py
from .routes.api import *
from .routes.websocket import *
from .components.layout import *
# ... import all original symbols

# Maintain original module-level variables
app = FastAPI()  # Re-create original app instance
```

### 2. Deprecation Warnings
Add deprecation warnings for direct imports from old paths:

```python
import warnings
warnings.warn(
    "Direct import from torq_console.ui.web is deprecated. "
    "Import from torq_console.ui.web.routes instead.",
    DeprecationWarning,
    stacklevel=2
)
```

### 3. Gradual Migration
- Keep original files working during transition
- Provide clear migration paths
- Update documentation progressively

## Success Metrics

### Code Quality Metrics
- **Lines per file**: Target <500 lines per module
- **Cyclomatic complexity**: Reduced by 30%
- **Import dependencies**: Minimize circular dependencies

### Performance Metrics
- **Import time**: 20% faster module loading
- **Memory usage**: 15% reduction in memory footprint
- **Startup time**: 10% faster application startup

### Developer Experience Metrics
- **Code navigation**: Improved IDE support
- **Testing coverage**: Easier to achieve >90% coverage
- **Debugging**: Smaller modules enable faster debugging

## Timeline

### Week 1: Planning and Setup
- [ ] Complete detailed analysis of all files
- [ ] Create directory structures
- [ ] Set up backward compatibility framework

### Week 2: Priority 1 Files
- [ ] Split torq_prince_flowers.py (4,540 lines)
- [ ] Split web.py (2,365 lines)
- [ ] Split phase2_professional_task_optimization.py (2,096 lines)

### Week 3: Priority 2 Files
- [ ] Split 6 files (1500-2000 lines)
- [ ] Update imports and test

### Week 4: Priority 3 Files
- [ ] Split remaining 14 files (1000-1500 lines)
- [ ] Complete import updates
- [ ] Final testing and documentation

## Risk Mitigation

### Potential Risks
1. **Breaking changes**: Mitigated with compatibility shims
2. **Import errors**: Automated testing and validation
3. **Performance regression**: Benchmarking and monitoring
4. **Development disruption**: Gradual rollout with fallback

### Mitigation Strategies
1. **Comprehensive testing**: Test all functionality after each split
2. **Automated validation**: Scripts to validate imports and functionality
3. **Rollback plan**: Keep original files until migration is complete
4. **Developer communication**: Clear documentation and migration guides

---

This restructuring will transform TORQ CONSOLE into a more maintainable, performant, and developer-friendly codebase while preserving all existing functionality.