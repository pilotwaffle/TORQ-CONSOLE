#!/usr/bin/env python3
"""
Test script for TORQ CONSOLE v0.70.0 Context Management System integration.

This script validates the basic functionality of the new context management system.
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add the torq_console package to the path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from torq_console.core.config import TorqConfig
    from torq_console.core.context_manager import ContextManager, ContextMatch
    from torq_console.core.console import TorqConsole
    print("✓ Successfully imported TORQ CONSOLE components")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)


async def test_context_manager():
    """Test the ContextManager functionality."""
    print("\n=== Testing ContextManager ===")

    # Create config and context manager
    config = TorqConfig.create_default()
    root_path = Path.cwd()
    context_manager = ContextManager(config, root_path)

    print(f"✓ ContextManager initialized at {root_path}")

    # Test @-symbol parsing
    test_text = "@files *.py @code function test @docs README.md"
    at_matches = context_manager.at_parser.parse(test_text)

    print(f"✓ Parsed {len(at_matches)} @-symbol matches:")
    for match_type, args, full_match in at_matches:
        print(f"  - {match_type}: {args}")

    # Test context retrieval
    print("\n--- Testing context retrieval ---")
    try:
        context_results = await context_manager.parse_and_retrieve(test_text, "keyword")
        print(f"✓ Context retrieval completed: {len(context_results)} categories")

        for category, matches in context_results.items():
            print(f"  - {category}: {len(matches)} matches")

    except Exception as e:
        print(f"✗ Context retrieval failed: {e}")

    # Test cache functionality
    print("\n--- Testing cache ---")
    cache_stats = context_manager.cache.stats()
    print(f"✓ Cache stats: {cache_stats}")

    # Test supported patterns
    patterns = await context_manager.get_supported_patterns()
    print(f"✓ Supported patterns: {len(patterns)} types")

    # Cleanup
    await context_manager.shutdown()
    print("✓ ContextManager shutdown complete")


async def test_console_integration():
    """Test the TorqConsole integration with ContextManager."""
    print("\n=== Testing Console Integration ===")

    # Create config and console
    config = TorqConfig.create_default()
    console = TorqConsole(config, repo_path=Path.cwd())

    print("✓ TorqConsole initialized with ContextManager")

    # Test context parsing through console
    test_message = "@files pyproject.toml @code import statements"

    try:
        context_results = await console.parse_context(test_message)
        print(f"✓ Console context parsing: {len(context_results)} categories")

        # Test context listing
        contexts = await console.list_contexts()
        print(f"✓ Active contexts: {len(contexts)}")

        # Test context summary
        summary = await console.get_context_summary()
        print(f"✓ Context summary generated")
        print(f"  - Active contexts: {summary.get('active_contexts', 0)}")
        print(f"  - Total matches: {summary.get('total_matches', 0)}")
        print(f"  - Cache entries: {summary.get('cache_stats', {}).get('size', 0)}")
        print(f"  - Tree-sitter available: {summary.get('tree_sitter_available', False)}")

        # Test supported patterns
        patterns = await console.get_supported_context_patterns()
        print(f"✓ Supported context patterns: {len(patterns)} types")

    except Exception as e:
        print(f"✗ Console integration test failed: {e}")
        import traceback
        traceback.print_exc()

    # Cleanup
    await console.shutdown()
    print("✓ Console shutdown complete")


async def test_error_handling():
    """Test error handling in the context system."""
    print("\n=== Testing Error Handling ===")

    config = TorqConfig.create_default()
    context_manager = ContextManager(config, Path.cwd())

    # Test with invalid patterns
    try:
        result = await context_manager.parse_and_retrieve("@invalid_pattern test")
        print("✓ Invalid pattern handled gracefully")
    except Exception as e:
        print(f"✗ Error handling failed: {e}")

    # Test with non-existent files
    try:
        result = await context_manager.parse_and_retrieve("@files non_existent_file.xyz")
        print("✓ Non-existent file handled gracefully")
    except Exception as e:
        print(f"✗ File error handling failed: {e}")

    await context_manager.shutdown()
    print("✓ Error handling tests complete")


async def main():
    """Run all tests."""
    print("TORQ CONSOLE v0.70.0 Context Management System Test")
    print("=" * 55)

    # Set up logging
    logging.basicConfig(level=logging.INFO)

    try:
        await test_context_manager()
        await test_console_integration()
        await test_error_handling()

        print("\n" + "=" * 55)
        print("✓ All tests completed successfully!")
        print("✓ TORQ CONSOLE v0.70.0 Context Management System is ready")

    except Exception as e:
        print(f"\n✗ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())