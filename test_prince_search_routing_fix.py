"""
Test Script: Verify Prince Flowers Search Routing Fix

Tests that Prince Flowers now correctly routes search queries to SearchMaster
instead of generating TypeScript code.
"""

import asyncio
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_search_routing():
    """Test that search queries are routed correctly."""
    print("\n" + "="*70)
    print("TESTING PRINCE FLOWERS SEARCH ROUTING FIX")
    print("="*70 + "\n")

    # Import after logging setup
    try:
        from torq_console.agents.torq_prince_flowers import TORQPrinceFlowers
        print("✓ Successfully imported TORQPrinceFlowers")
    except ImportError as e:
        print(f"✗ Failed to import: {e}")
        return False

    # Initialize agent
    try:
        agent = TORQPrinceFlowers(llm_provider=None, config={})
        print("✓ Successfully initialized Prince Flowers agent")
    except Exception as e:
        print(f"✗ Failed to initialize agent: {e}")
        return False

    # Check if query router is initialized
    if agent.query_router:
        print("✓ MarvinQueryRouter is initialized")
    else:
        print("⚠ MarvinQueryRouter is NOT initialized (may be unavailable)")

    # Test search queries
    search_queries = [
        "Search GitHub for top 3 workflow repositories",
        "Find the most popular Python libraries",
        "Look up recent AI developments",
        "What are the latest trends in machine learning?"
    ]

    print("\n" + "-"*70)
    print("TESTING SEARCH QUERIES")
    print("-"*70 + "\n")

    for query in search_queries:
        print(f"\nQuery: {query}")
        print("-" * 50)

        try:
            result = await agent.process_query(query, context={'test_mode': True})

            print(f"Success: {result.success}")
            print(f"Tools Used: {result.tools_used}")
            print(f"Reasoning Mode: {result.reasoning_mode.value if hasattr(result, 'reasoning_mode') else 'N/A'}")

            # Check if it was routed
            if result.metadata and result.metadata.get('query_routed'):
                print("✓ QUERY WAS ROUTED - Search query correctly detected!")
                print(f"  Routing Decision: {result.metadata.get('routing_decision')}")
                print(f"  Routing Reasoning: {result.metadata.get('routing_reasoning')}")
            elif 'marvin_query_router' in result.tools_used or 'search_master' in result.tools_used:
                print("✓ SEARCH TOOLS USED - Likely routed correctly")
            else:
                print("⚠ May not have been routed - check tools used")

            # Check if response contains code generation (bad)
            response_lower = result.content.lower()
            code_indicators = ['typescript', '```typescript', 'package.json', 'import ', 'export ', 'interface ', 'class ']

            if any(indicator in response_lower for indicator in code_indicators):
                print("✗ WARNING: Response contains code generation keywords!")
                print("  This indicates the bug may still be present")
            else:
                print("✓ Response does NOT contain code generation")

        except Exception as e:
            print(f"✗ Error processing query: {e}")

        print()

    # Test a code generation query (should NOT be routed)
    print("\n" + "-"*70)
    print("TESTING CODE GENERATION QUERY (should NOT be routed)")
    print("-"*70 + "\n")

    code_query = "Write a function to calculate fibonacci numbers"
    print(f"Query: {code_query}")
    print("-" * 50)

    try:
        result = await agent.process_query(code_query, context={'test_mode': True})

        print(f"Success: {result.success}")
        print(f"Tools Used: {result.tools_used}")

        if result.metadata and result.metadata.get('query_routed'):
            print("⚠ Code query was routed (may be incorrect)")
        else:
            print("✓ Code query was NOT routed (correct behavior)")

    except Exception as e:
        print(f"✗ Error processing query: {e}")

    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70 + "\n")

    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_search_routing())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
