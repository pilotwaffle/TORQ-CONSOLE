# Prince Flowers Web Research Setup Guide

This guide explains how to set up Prince Flowers agent to use Claude Sonnet 4.6 with web research capabilities through Claude's Tool Use API and real search APIs.

## Overview

Prince Flowers agent can now perform real-time web research using:
- **Claude Sonnet 4.6** with Tool Use API for intelligent reasoning
- **Tavily API** (AI-optimized search, already configured)
- **Brave Search API** (2,000 free queries/month, already configured)
- **DuckDuckGo** (fallback, no API key needed)

## Prerequisites

1. **Anthropic API Key** - Already configured in `.env` as `ANTHROPIC_API_KEY`
2. **Tavily API Key** - Already configured in `.env` as `TAVILY_API_KEY`
3. **Brave Search API Key** - Already configured in `.env` as `BRAVE_SEARCH_API_KEY`

## Configuration

The following environment variables are already set in `E:\TORQ-CONSOLE\.env`:

```env
# Claude API (for Sonnet 4.6)
ANTHROPIC_API_KEY=sk-ant-api03-...

# Tavily Search (AI-optimized)
TAVILY_API_KEY=tvly-dev-...

# Brave Search (2,000 free/month)
BRAVE_SEARCH_API_KEY=BSAUnqyZiLSBnEadW8-Xwo4K0h8tWOQ
```

## Components

### 1. Enhanced Web Search Tool

**Location**: `E:\TORQ-CONSOLE\torq_console\agents\torq_prince_flowers\tools\websearch_enhanced.py`

Features:
- Multi-source search (Tavily, Brave, DuckDuckGo)
- Automatic fallback between search engines
- News-specific search
- Result ranking and deduplication

### 2. Claude Tool Use Provider

**Location**: `E:\TORQ-CONSOLE\torq_console\llm\providers\claude_with_tools.py`

Features:
- Anthropic's Tool Use API integration
- Automatic tool selection based on query
- Research mode for comprehensive answers
- Web search tool execution

### 3. Prince Flowers Agent Integration

**Location**: `E:\TORQ-CONSOLE\torq_console\agents\torq_prince_flowers\core\agent.py`

The agent now has:
- Enhanced web search capabilities
- Reasoning modes that use web research
- Automatic detection of research queries

## Usage

### Python API

```python
import asyncio
from torq_console.llm.manager import LLMManager
from torq_console.llm.manager_patch_claude_tools import patch_manager
from torq_console.agents.torq_prince_flowers.core.agent import TORQPrinceFlowers

async def research_example():
    # Initialize LLM Manager with tool use support
    llm_manager = LLMManager()
    patch_manager(llm_manager)

    # Get Claude provider
    llm_provider = llm_manager.get_provider('claude')

    # Initialize Prince Flowers agent
    agent = TORQPrinceFlowers(llm_provider=llm_provider)

    # Perform web research
    result = await agent.process_query(
        query="What are the latest developments in quantum computing?",
        context={'mode': 'research'}
    )

    print(result.content)

asyncio.run(research_example())
```

### Using Claude Tool Use Provider Directly

```python
import asyncio
from torq_console.llm.providers.claude_with_tools import (
    create_claude_tool_use_provider
)

async def research_with_tools():
    # Create provider with tool use
    provider = create_claude_tool_use_provider({
        'tool_use_enabled': True,
        'model': 'claude-sonnet-4-6'
    })

    # Use research mode
    response = await provider.research_mode(
        query="latest AI news 2024"
    )

    print(response)

asyncio.run(research_with_tools())
```

### Using Enhanced Web Search Directly

```python
import asyncio
from torq_console.agents.torq_prince_flowers.tools.websearch_enhanced import (
    create_enhanced_web_search_tool
)

async def search_example():
    # Create search tool
    search_tool = create_enhanced_web_search_tool()

    # Perform search
    results = await search_tool.search(
        query="artificial intelligence trends 2024",
        max_results=10
    )

    for result in results:
        print(f"{result['title']}")
        print(f"{result['url']}")
        print(f"{result['snippet']}\n")

asyncio.run(search_example())
```

## Testing

Run the comprehensive test suite:

```bash
cd E:\TORQ-CONSOLE
python test_prince_flowers_web_research.py
```

This will test:
1. Enhanced web search tool
2. Claude Tool Use provider
3. Prince Flowers agent integration
4. Research mode functionality

## How It Works

### Research Flow

1. **Query Analysis**: Prince Flowers analyzes the query to detect research needs
2. **Tool Selection**: If web research is needed, Claude uses the web_search tool
3. **Search Execution**: The enhanced web search tool queries Tavily/Brave APIs
4. **Result Processing**: Search results are passed back to Claude
5. **Synthesis**: Claude synthesizes the information into a comprehensive answer

### Automatic Tool Use

Claude Sonnet 4.6 automatically decides when to use web search based on:
- Keywords like "latest", "recent", "current", "news"
- Questions about real-time information
- Requests for facts that may have changed

### Search Method Priority

1. **Tavily** (if API key available) - AI-optimized search with content extraction
2. **Brave** (if API key available) - Privacy-focused search
3. **DuckDuckGo** - Free fallback (no API key needed)

## Model Information

**Claude Sonnet 4.6** (`claude-sonnet-4-6`) features:
- Extended thinking (10,000 thinking tokens)
- Tool use API support
- 200K token context window
- Improved reasoning and analysis

## Troubleshooting

### Web Search Not Working

1. Check API keys are set in `.env`
2. Run the test script to diagnose issues
3. Check logs for specific error messages

### Claude Tool Use Not Available

1. Verify ANTHROPIC_API_KEY is valid
2. Check that the model is `claude-sonnet-4-6`
3. Ensure `tool_use_enabled` is set to True in config

### Import Errors

1. Ensure all new files are in the correct directories
2. Check Python path includes `E:\TORQ-CONSOLE`
3. Verify all dependencies are installed

## Files Created/Modified

### New Files

1. `E:\TORQ-CONSOLE\torq_console\agents\torq_prince_flowers\tools\websearch_enhanced.py`
   - Real web search implementation with Tavily, Brave, DuckDuckGo

2. `E:\TORQ-CONSOLE\torq_console\llm\providers\claude_with_tools.py`
   - Claude provider with Tool Use API support

3. `E:\TORQ-CONSOLE\torq_console\llm\manager_patch_claude_tools.py`
   - Patch to add tool use provider to LLM Manager

4. `E:\TORQ-CONSOLE\test_prince_flowers_web_research.py`
   - Comprehensive test suite

### Modified Files

1. `E:\TORQ-CONSOLE\torq_console\agents\torq_prince_flowers\tools\websearch.py`
   - Updated to use enhanced web search implementation

## Next Steps

1. **Run the test suite** to verify everything is working
2. **Try a research query** through Prince Flowers
3. **Customize search behavior** by modifying the enhanced search tool
4. **Add more tools** to Claude's tool use as needed

## API Limits

- **Tavily**: Free tier has limits (check Tavily dashboard)
- **Brave Search**: 2,000 free queries/month
- **Claude API**: Check Anthropic dashboard for usage limits

## References

- [Anthropic Tool Use Documentation](https://docs.anthropic.com/claude/docs/tool-use)
- [Tavily API Documentation](https://docs.tavily.com/)
- [Brave Search API](https://api.search.brave.com/app/documentation)
