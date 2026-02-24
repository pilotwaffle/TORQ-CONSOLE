"""
Test script for Prince Flowers Web Research capabilities.

This script tests:
1. Enhanced web search tool (Tavily, Brave, DuckDuckGo)
2. Claude Sonnet 4.6 with tool use
3. Prince Flowers agent with web research

Usage:
    python test_prince_flowers_web_research.py
"""

import asyncio
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


async def test_enhanced_web_search():
    """Test the enhanced web search tool."""
    print("\n" + "=" * 70)
    print("TEST 1: Enhanced Web Search Tool")
    print("=" * 70)

    try:
        from torq_console.agents.torq_prince_flowers.tools.websearch_enhanced import (
            create_enhanced_web_search_tool
        )

        search_tool = create_enhanced_web_search_tool()

        # Check health
        health = await search_tool.health_check()
        print(f"\nHealth Check:")
        print(f"  Available methods: {health['available_methods']}")
        print(f"  API Keys configured:")
        for provider, configured in health['api_keys_configured'].items():
            status = "[OK]" if configured else "[MISSING]"
            print(f"    {status} {provider}")

        # Perform a test search
        test_query = "latest AI developments 2024"
        print(f"\nTest Search: '{test_query}'")

        results = await search_tool.search(
            query=test_query,
            max_results=5
        )

        print(f"\nResults received: {len(results)}")
        for i, result in enumerate(results[:3], 1):
            title = result.get('title', 'No title')
            source = result.get('source', 'unknown')
            print(f"\n  {i}. [{source}] {title}")

        return len(results) > 0

    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_claude_tool_use_provider():
    """Test Claude provider with tool use."""
    print("\n" + "=" * 70)
    print("TEST 2: Claude Sonnet 4.6 with Tool Use")
    print("=" * 70)

    try:
        from torq_console.llm.providers.claude_with_tools import (
            create_claude_tool_use_provider
        )

        # Check API key
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            print("\n[FAIL] ANTHROPIC_API_KEY not set")
            return False

        print(f"\n[OK] ANTHROPIC_API_KEY configured")

        provider = create_claude_tool_use_provider({
            'tool_use_enabled': True,
            'max_tool_iterations': 5
        })

        # Check provider status
        tool_status = provider.get_tool_status()
        print(f"\nTool Status:")
        print(f"  Tool use enabled: {tool_status['tool_use_enabled']}")
        print(f"  Available tools: {tool_status['available_tools']}")
        print(f"  Web search available: {tool_status['web_search_available']}")

        if not provider.is_configured():
            print("\n[FAIL] Provider not configured")
            return False

        print(f"\n[OK] Provider configured with model: {provider.model}")

        # Test a simple query
        print(f"\nTest Query: 'What is the capital of France?'")
        response = await provider.query("What is the capital of France?")
        print(f"\nResponse: {response[:200]}...")

        return True

    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_prince_flowers_agent():
    """Test Prince Flowers agent with web research."""
    print("\n" + "=" * 70)
    print("TEST 3: Prince Flowers Agent with Web Research")
    print("=" * 70)

    try:
        from torq_console.llm.manager import LLMManager
        from torq_console.llm.manager_patch_claude_tools import patch_manager
        from torq_console.agents.torq_prince_flowers.core.agent import TORQPrinceFlowers

        # Initialize LLM Manager
        llm_manager = LLMManager()

        # Patch with tool use support
        patch_success = patch_manager(llm_manager)
        if patch_success:
            print("\n[OK] Claude Tool Use provider added to LLM Manager")
        else:
            print("\n[WARN] Claude Tool Use provider not available")

        # Get provider for agent
        llm_provider = llm_manager.get_provider('claude')

        if not llm_provider or not llm_provider.is_configured():
            print("\n[FAIL] Claude provider not configured")
            return False

        print(f"\n[OK] Claude provider configured")

        # Initialize Prince Flowers agent
        agent = TORQPrinceFlowers(llm_provider=llm_provider)

        print(f"\n[OK] Prince Flowers agent initialized")
        print(f"  Agent ID: {agent.agent_id}")
        print(f"  Version: {agent.version}")

        # Check web search tool
        if hasattr(agent, 'web_search_tool'):
            health = await agent.web_search_tool.health_check()
            print(f"\nWeb Search Tool:")
            print(f"  Available: {health.get('healthy', False)}")
            if 'enhanced_available' in health:
                print(f"  Enhanced: {health['enhanced_available']}")

        # Test a research query
        test_query = "What are the latest trends in artificial intelligence?"
        print(f"\nTest Research Query: '{test_query}'")
        print("Processing...")

        result = await agent.process_query(
            query=test_query,
            context={'mode': 'research'}
        )

        print(f"\n[OK] Response received")
        print(f"  Success: {result.success}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Tools used: {result.tools_used}")
        print(f"\nResponse preview:")
        # Use response attribute instead of content
        response_text = result.response if hasattr(result, 'response') else str(result)
        print(f"  {response_text[:300]}...")

        return result.success

    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_research_mode():
    """Test research mode specifically."""
    print("\n" + "=" * 70)
    print("TEST 4: Research Mode with Claude Tool Use")
    print("=" * 70)

    try:
        from torq_console.llm.providers.claude_with_tools import (
            create_claude_tool_use_provider
        )

        provider = create_claude_tool_use_provider({
            'tool_use_enabled': True
        })

        if not provider.is_configured():
            print("\n[FAIL] Provider not configured")
            return False

        # Test research mode
        research_query = "latest news about quantum computing"
        print(f"\nResearch Query: '{research_query}'")
        print("Performing web research...")

        response = await provider.research_mode(research_query)

        print(f"\n[OK] Research completed")
        print(f"\nResponse:")
        print(f"  {response[:500]}...")

        return True

    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all tests and print summary."""
    print("\n" + "=" * 70)
    print("PRINCE FLOWERS WEB RESEARCH TEST SUITE")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check environment variables
    print("\nEnvironment Configuration:")
    api_keys = {
        'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY'),
        'TAVILY_API_KEY': os.getenv('TAVILY_API_KEY'),
        'BRAVE_SEARCH_API_KEY': os.getenv('BRAVE_SEARCH_API_KEY')
    }

    for key, value in api_keys.items():
        status = "[OK]" if value else "[MISSING]"
        masked_value = f"{value[:8]}...{value[-4:]}" if value and len(value) > 12 else "Not set"
        print(f"  {status} {key}: {masked_value}")

    # Run tests
    results = {
        "Enhanced Web Search": await test_enhanced_web_search(),
        "Claude Tool Use Provider": await test_claude_tool_use_provider(),
        "Prince Flowers Agent": await test_prince_flowers_agent(),
        "Research Mode": await test_research_mode()
    }

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status}: {test_name}")

    print(f"\nResults: {passed}/{total} tests passed")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if passed == total:
        print("\n[SUCCESS] All tests passed! Prince Flowers is ready for web research.")
    else:
        print("\n[WARNING] Some tests failed. Check the output above for details.")

    return passed == total


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run tests
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
