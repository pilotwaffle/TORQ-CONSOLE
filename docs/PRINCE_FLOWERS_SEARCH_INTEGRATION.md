# Prince Flowers Search Integration

## Overview

This document describes the enhanced Prince Flowers agent integration that enables **actual web search capabilities** instead of just providing search methodologies.

## Problem Statement

Previously, when users asked Prince Flowers to perform searches (e.g., "Search GitHub and list top 3 repository links with the most workflows"), the Marvin-based Prince Flowers agent would only provide **explanations of how to search** rather than performing the actual search.

### Root Cause

The TORQ Console had **two separate Prince Flowers implementations**:

1. **MarvinPrinceFlowers** (`torq_console/agents/marvin_prince_flowers.py`)
   - New Marvin 3.0-based agent
   - Conversational and analytical capabilities
   - **No tool access** - cannot perform web searches

2. **TorqPrinceFlowers** (`torq_console/agents/torq_prince_flowers.py`)
   - Original enhanced agent with agentic RL
   - **Has SearchMaster integration** - can perform actual searches
   - Full tool ecosystem (image generation, social media, file operations, etc.)

The orchestrator was routing **all queries** to MarvinPrinceFlowers, even search queries that required tool access.

## Solution

### Intelligent Query Routing

The `MarvinAgentOrchestrator` now intelligently routes queries to the appropriate agent:

- **Search/Research Queries** → `TorqPrinceFlowers` (with SearchMaster tools)
- **Conversational/Analytical Queries** → `MarvinPrinceFlowers` (structured outputs)

### Detection Logic

The orchestrator detects search queries using two methods:

1. **Capability Analysis**: Checks if `AgentCapability.WEB_SEARCH` or `AgentCapability.RESEARCH` are needed
2. **Keyword Detection**: Scans for search-related keywords in the query:
   - `search`, `find`, `look up`, `lookup`
   - `github`, `repository`, `repo`
   - `latest`, `recent`, `news`, `trends`
   - `top`, `best`, `list`, `compare`, `popular`
   - `what is`, `what are`, `tell me about`

### Implementation Details

**File**: `torq_console/agents/marvin_orchestrator.py`

```python
async def _execute_single_agent(self, query: str, routing: RoutingDecision, context):
    # Detect if search/research capabilities are needed
    needs_search = (
        AgentCapability.WEB_SEARCH in routing.capabilities_needed or
        AgentCapability.RESEARCH in routing.capabilities_needed or
        self._is_search_query(query)
    )

    # Route to appropriate agent
    if needs_search and TORQ_PRINCE_AVAILABLE:
        # Initialize TorqPrinceFlowers lazily if needed
        if not self._torq_prince_initialized:
            await self._initialize_torq_prince()

        if self.torq_prince:
            # Use TorqPrinceFlowers for tool-based search
            response = await self.torq_prince.process_query(query)
            agent_used = "torq_prince_flowers (with tools)"
        else:
            # Fallback to Marvin Prince
            response = await self.prince_flowers.chat(query, context)
            agent_used = "marvin_prince_flowers (fallback)"
    else:
        # Use Marvin Prince for conversational/analytical tasks
        response = await self.prince_flowers.chat(query, context)
        agent_used = "marvin_prince_flowers"
```

### Lazy Initialization

TorqPrinceFlowers is initialized **lazily** (on first search query) to avoid unnecessary resource usage:

```python
async def _initialize_torq_prince(self):
    """Lazy initialization of TorqPrinceFlowers."""
    # Try Anthropic provider first, fallback to OpenAI
    llm_provider = None
    try:
        llm_provider = create_anthropic_provider()
    except Exception:
        try:
            llm_provider = create_openai_provider()
        except Exception:
            self.logger.warning("Could not initialize LLM provider")

    if llm_provider:
        self.torq_prince = TorqPrinceFlowers(llm_provider=llm_provider)
        self._torq_prince_initialized = True
```

## Usage Examples

### Search Query (Routes to TorqPrinceFlowers)

```python
from torq_console.agents.marvin_orchestrator import get_orchestrator

orchestrator = get_orchestrator()

# This will use TorqPrinceFlowers with SearchMaster
result = await orchestrator.process_query(
    "Search GitHub and list top 3 repository links with the most workflows"
)

print(f"Agent used: {result.metadata['agent_used']}")
# Output: "torq_prince_flowers (with tools)"

print(f"Used tools: {result.metadata['used_tools']}")
# Output: True
```

### Conversational Query (Routes to MarvinPrinceFlowers)

```python
# This will use MarvinPrinceFlowers for structured conversation
result = await orchestrator.process_query(
    "Can you explain how async/await works in Python?"
)

print(f"Agent used: {result.metadata['agent_used']}")
# Output: "marvin_prince_flowers"

print(f"Used tools: {result.metadata['used_tools']}")
# Output: False
```

### CLI Usage

```bash
# Search query (uses TorqPrinceFlowers with tools)
/torq-agent query "Search GitHub for repositories with most workflows"

# Conversational query (uses MarvinPrinceFlowers)
/torq-agent chat "What's the difference between async and threading?"
```

## Benefits

### 1. Actual Search Results

Instead of methodology explanations, users now get:
- Real search results with URLs
- Concrete data from web sources
- Verified information from multiple APIs

### 2. Unified Interface

Users don't need to know which agent to use:
- Queries are automatically routed
- Seamless experience
- Best agent for each task

### 3. Tool Access

TorqPrinceFlowers provides access to:
- **SearchMaster**: Multi-source web search (DuckDuckGo, Brave, Bing, etc.)
- **GitHub API**: Repository data and workflows
- **Crypto APIs**: CoinGecko, CoinMarketCap
- **News APIs**: Latest news and trends
- **Academic APIs**: Research papers and citations

### 4. Intelligent Fallback

If TorqPrinceFlowers initialization fails:
- Automatically falls back to MarvinPrinceFlowers
- Logs warnings for debugging
- Maintains service availability

## Metrics

The orchestrator now tracks:

```python
metrics = {
    'total_requests': 100,
    'torq_prince_requests': 45,      # Search queries
    'marvin_prince_requests': 55,    # Conversational queries
    'success_rate': 0.98
}
```

Access via:
```python
metrics = orchestrator.get_comprehensive_metrics()
print(f"TorqPrince: {metrics['orchestrator']['torq_prince_requests']}")
print(f"MarvinPrince: {metrics['orchestrator']['marvin_prince_requests']}")
```

## Testing

Run the test suite:

```bash
# Run integration tests
python test_prince_search_integration.py

# Expected output:
# ✓ PASS: Search queries routed to TorqPrinceFlowers (with tools)
# ✓ PASS: Conversational queries routed to MarvinPrinceFlowers
```

## Architecture Diagram

```
User Query
    |
    v
MarvinAgentOrchestrator
    |
    ├─ Query Router (Marvin-based)
    |       |
    |       v
    |   Analyze capabilities & keywords
    |       |
    |       v
    ├─ Search Query?
    |   ├─ YES → TorqPrinceFlowers
    |   |           |
    |   |           v
    |   |       SearchMaster (with tools)
    |   |           |
    |   |           v
    |   |       Web Search APIs
    |   |           |
    |   |           v
    |   |       Concrete Results
    |   |
    |   └─ NO → MarvinPrinceFlowers
    |               |
    |               v
    |           Structured Conversation
    |               |
    |               v
    |           Analytical Response
    |
    v
Response to User
```

## Future Enhancements

### Phase 1: Tool Integration (Planned)
- Add Marvin tool wrappers for SearchMaster
- Enable MarvinPrinceFlowers to call tools directly
- Unified agent with both capabilities

### Phase 2: Multi-Tool Composition (Planned)
- Chain multiple tools for complex queries
- Coordinate SearchMaster + GitHub API + Analysis
- Pipeline execution for research workflows

### Phase 3: Learning & Optimization (Planned)
- Track which agent performs better for query types
- Adaptive routing based on success metrics
- User feedback integration

## Configuration

### Environment Variables

```bash
# Required for search capabilities
export ANTHROPIC_API_KEY=your_key_here
# Or
export OPENAI_API_KEY=your_key_here

# Optional search engine keys
export BRAVE_API_KEY=your_key_here
export SERPAPI_KEY=your_key_here
```

### Enable/Disable TorqPrince

```python
# Force disable TorqPrinceFlowers (use only MarvinPrinceFlowers)
import torq_console.agents.marvin_orchestrator as mo
mo.TORQ_PRINCE_AVAILABLE = False

# Re-enable
mo.TORQ_PRINCE_AVAILABLE = True
```

## Troubleshooting

### Issue: Search queries return methodology instead of results

**Cause**: TorqPrinceFlowers not initializing

**Solution**:
1. Check API keys are set: `echo $ANTHROPIC_API_KEY`
2. Check logs: `grep "TorqPrinceFlowers" ~/.torq/logs/`
3. Run test: `python test_prince_search_integration.py`

### Issue: "TorqPrinceFlowers not available" warning

**Cause**: Import error or missing dependencies

**Solution**:
```bash
# Check imports
python -c "from torq_console.agents.torq_prince_flowers import TorqPrinceFlowers"

# Check SearchMaster
python -c "from torq_console.agents.torq_search_master import create_search_master"
```

### Issue: All queries go to MarvinPrinceFlowers

**Cause**: Keyword detection not matching

**Solution**: Add keywords to `_is_search_query()` in orchestrator.py

## References

- **TorqPrinceFlowers**: `torq_console/agents/torq_prince_flowers.py`
- **MarvinPrinceFlowers**: `torq_console/agents/marvin_prince_flowers.py`
- **Orchestrator**: `torq_console/agents/marvin_orchestrator.py`
- **SearchMaster**: `torq_console/agents/torq_search_master.py`
- **Test Suite**: `test_prince_search_integration.py`

## Summary

The Prince Flowers search integration enables:
- ✅ **Actual web search results** instead of methodology
- ✅ **Intelligent query routing** based on capabilities
- ✅ **Tool-based execution** with SearchMaster
- ✅ **Seamless user experience** with automatic fallback
- ✅ **Comprehensive metrics** for monitoring

Users can now ask Prince Flowers to search and get **real, actionable results** with links, data, and verified information from multiple sources.

---

*Last Updated: 2025-11-04*
*Version: 1.0*
*Status: Production Ready*
