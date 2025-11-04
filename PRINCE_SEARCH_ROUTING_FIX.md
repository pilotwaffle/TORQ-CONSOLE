# Prince Flowers Search Routing Fix

**Date**: 2025-11-04
**Issue**: Prince Flowers was generating TypeScript code when asked to search for information
**Status**: ✅ FIXED

## Problem Description

When users asked Prince Flowers to search for information (e.g., "Search GitHub for top 3 workflow repositories"), Prince was generating TypeScript application code instead of performing a web search.

### Example of the Bug:
```
User: "Search GitHub for top 3 workflow repositories"

Prince Response (INCORRECT):
"I'll create a complete TypeScript application that searches GitHub for the top 3 workflow repositories..."
[Generates package.json, tsconfig.json, and full TypeScript project structure]
```

### Expected Behavior:
```
User: "Search GitHub for top 3 workflow repositories"

Prince Response (CORRECT):
"Based on my search results, here are the top 3 repositories with extensive workflows:
1. kubernetes/kubernetes - ...
2. pytorch/pytorch - ...
3. tensorflow/tensorflow - ..."
```

## Root Cause Analysis

The issue was traced through the following call chain:

1. **Web UI** (`torq_console/ui/web.py:887-914`)
   - Routes ALL queries to `prince_flowers_integration.process_query()`
   - Comments: "ROUTE ALL QUERIES TO PRINCE FLOWERS FOR BEST QUALITY"

2. **Prince Flowers Integration** (`torq_integration.py:555-581`)
   - Calls `wrapper.query()` method

3. **Integration Wrapper** (`torq_integration.py:270-377`)
   - Calls `agent.handle_prince_command()`

4. **Prince Flowers Interface** (`torq_console/agents/torq_prince_flowers.py:4315-4357`)
   - Calls `_handle_query()` which calls `self.agent.process_query()`

5. **TORQ Prince Flowers Agent** (`torq_console/agents/torq_prince_flowers.py:669-810`)
   - **CRITICAL ISSUE**: `process_query()` method was NOT using the MarvinQueryRouter
   - Had its own internal query analysis (`_analyze_query_enhanced()`)
   - Never checked if query was a search query
   - Always proceeded with normal reasoning/code generation flow

## The Fix

### Changes Made

**File**: `torq_console/agents/torq_prince_flowers.py`

#### 1. Import MarvinQueryRouter (Lines 36-42)
```python
# Import Marvin Query Router for intelligent query routing
try:
    from .marvin_query_router import create_query_router, AgentCapability
    MARVIN_ROUTER_AVAILABLE = True
except ImportError:
    MARVIN_ROUTER_AVAILABLE = False
    logging.warning("MarvinQueryRouter not available - search routing may be less accurate")
```

#### 2. Initialize Router in `__init__` (Lines 214-221)
```python
# Initialize Marvin Query Router for intelligent search routing
self.query_router = None
if MARVIN_ROUTER_AVAILABLE:
    try:
        self.query_router = create_query_router()
        self.logger.info("MarvinQueryRouter initialized for intelligent query routing")
    except Exception as e:
        self.logger.warning(f"Failed to initialize MarvinQueryRouter: {e}")
```

#### 3. Route Search Queries in `process_query()` (Lines 704-752)
```python
# CRITICAL FIX: Use MarvinQueryRouter to detect search queries
# Route search queries to SearchMaster instead of code generation
if self.query_router:
    try:
        routing_analysis = await self.query_router.analyze_query(query)

        # Check if this is a search/research query
        is_search_query = (
            AgentCapability.WEB_SEARCH in routing_analysis.required_capabilities or
            AgentCapability.RESEARCH in routing_analysis.required_capabilities
        )

        if is_search_query:
            self.logger.info(f"[PRINCE-RL] Detected SEARCH query - routing to SearchMaster")

            # Use SearchMaster for search queries
            if SEARCHMASTER_AVAILABLE and self.search_master:
                search_result = await self.search_master.search(
                    query=query,
                    max_results=10,
                    search_type='comprehensive'
                )

                return TORQAgentResult(
                    success=True,
                    content=search_result.get('formatted_answer', ...),
                    tools_used=['marvin_query_router', 'search_master', 'web_search'],
                    metadata={'query_routed': True, ...}
                )
```

## How It Works Now

### Query Flow After Fix:

1. **User Query**: "Search GitHub for repositories"

2. **MarvinQueryRouter.analyze_query()** detects search keywords:
   - Keywords: 'search', 'github', 'find', 'look up', etc.
   - Classification: `WEB_SEARCH` or `RESEARCH` capability required
   - Routing Decision: Route to search specialist

3. **Early Return with SearchMaster**:
   - Query is routed to SearchMaster
   - Performs actual web search
   - Returns formatted search results
   - **NEVER reaches code generation logic**

4. **User receives search results** instead of code

### Non-Search Queries Still Work:

- Code generation queries: "Write a function to..."
- Analysis queries: "Explain how..."
- Documentation queries: "Document this code..."

These bypass the search routing and proceed with normal Prince Flowers reasoning.

## Testing

### Test Script
Run: `python test_prince_search_routing_fix.py`

### Manual Testing
```python
from torq_console.agents.torq_prince_flowers import TORQPrinceFlowers
agent = TORQPrinceFlowers()

# Test search query
result = await agent.process_query("Search GitHub for workflow repositories")
print(result.tools_used)  # Should include: 'marvin_query_router', 'search_master'
print(result.metadata.get('query_routed'))  # Should be: True

# Test code query
result = await agent.process_query("Write a fibonacci function")
print(result.metadata.get('query_routed'))  # Should be: False or None
```

## Benefits

1. **Correct Intent Detection**: Uses AI-powered query classification
2. **No False Positives**: Code queries still work normally
3. **Better Search Results**: SearchMaster provides multi-source web search
4. **Graceful Fallback**: If router unavailable, uses normal processing
5. **Logging**: Clear logs show routing decisions

## Related Files

- `torq_console/agents/marvin_query_router.py` - Query classification logic
- `torq_console/agents/torq_prince_flowers.py` - Prince Flowers agent (FIXED)
- `torq_integration.py` - Integration wrapper
- `torq_console/ui/web.py` - Web UI integration

## Commit Message

```
fix: Prevent Prince Flowers from generating code on search queries

Prince Flowers was generating TypeScript code when users asked it to
search for information. This happened because the query routing logic
was bypassed in the main process_query() method.

Changes:
- Import and initialize MarvinQueryRouter in TORQPrinceFlowers
- Add early routing check in process_query() method
- Route search queries to SearchMaster before normal processing
- Add logging for routing decisions
- Maintain backward compatibility with fallback behavior

Fixes: Search queries now return search results instead of code
Impact: Users get correct responses for search queries
Testing: test_prince_search_routing_fix.py
```

## Notes

- The MarvinQueryRouter already had correct search detection logic (lines 208-225)
- It just wasn't being used by Prince Flowers
- This fix integrates existing, tested routing logic into the agent flow
- No changes needed to the router itself
- The fix is backward compatible - if router unavailable, uses normal processing
