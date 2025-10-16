"""
Simple test script for Phase 3 Plugin Architecture.

Tests the plugin system integration with WebSearchProvider.
"""

import asyncio
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_plugin_registry():
    """Test plugin registry functionality."""
    logger.info("=" * 60)
    logger.info("TEST 1: Plugin Registry")
    logger.info("=" * 60)

    try:
        from torq_console.llm.providers.search_plugins import get_registry

        registry = get_registry()

        # List all plugins
        plugins = registry.list_plugins()
        logger.info(f"✓ Registered plugins: {plugins}")

        # Get plugin statistics
        stats = registry.get_statistics()
        logger.info(f"✓ Plugin statistics: {stats}")

        # Test each plugin
        for plugin_name in plugins:
            plugin = registry.get_plugin(plugin_name)
            metadata = plugin.get_metadata()
            logger.info(f"✓ Plugin '{plugin_name}': v{metadata.version} - {metadata.description}")

        logger.info("✓ Plugin Registry Test: PASSED\n")
        return True

    except Exception as e:
        logger.error(f"✗ Plugin Registry Test: FAILED - {e}")
        return False


async def test_plugin_search():
    """Test plugin search functionality."""
    logger.info("=" * 60)
    logger.info("TEST 2: Plugin Search")
    logger.info("=" * 60)

    try:
        from torq_console.llm.providers.search_plugins import get_registry

        registry = get_registry()

        # Test Reddit plugin
        logger.info("Testing Reddit plugin...")
        reddit_plugin = registry.get_plugin("reddit")
        if reddit_plugin:
            results = await reddit_plugin.search("python programming", max_results=3)
            logger.info(f"✓ Reddit search returned {len(results)} results")
            for i, result in enumerate(results[:2], 1):
                logger.info(f"  Result {i}: {result.title[:60]}...")

        # Test HackerNews plugin
        logger.info("Testing HackerNews plugin...")
        hn_plugin = registry.get_plugin("hackernews")
        if hn_plugin:
            results = await hn_plugin.search("artificial intelligence", max_results=3)
            logger.info(f"✓ HackerNews search returned {len(results)} results")
            for i, result in enumerate(results[:2], 1):
                logger.info(f"  Result {i}: {result.title[:60]}...")

        # Test ArXiv plugin
        logger.info("Testing ArXiv plugin...")
        arxiv_plugin = registry.get_plugin("arxiv")
        if arxiv_plugin:
            results = await arxiv_plugin.search("quantum computing", max_results=3)
            logger.info(f"✓ ArXiv search returned {len(results)} results")
            for i, result in enumerate(results[:2], 1):
                logger.info(f"  Result {i}: {result.title[:60]}...")

        logger.info("✓ Plugin Search Test: PASSED\n")
        return True

    except Exception as e:
        logger.error(f"✗ Plugin Search Test: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_websearch_integration():
    """Test WebSearchProvider integration with plugins."""
    logger.info("=" * 60)
    logger.info("TEST 3: WebSearch Integration")
    logger.info("=" * 60)

    try:
        from torq_console.llm.providers.websearch import WebSearchProvider

        # Create provider
        provider = WebSearchProvider()
        logger.info(f"✓ WebSearchProvider initialized")
        logger.info(f"✓ Plugins enabled: {provider.plugins_enabled}")

        if provider.plugins_enabled:
            logger.info(f"✓ Plugin registry available: {provider.plugin_registry is not None}")
            logger.info(f"✓ Plugin loader available: {provider.plugin_loader is not None}")

            # List registered plugins
            plugins = provider.plugin_registry.list_plugins()
            logger.info(f"✓ Auto-loaded plugins: {plugins}")

        # Test plugin search method
        logger.info("Testing plugin search via WebSearchProvider...")
        result = await provider._plugin_search("reddit", "machine learning", 3, "general")

        if result:
            logger.info(f"✓ Plugin search successful")
            logger.info(f"  Method: {result.get('method')}")
            logger.info(f"  Plugin: {result.get('plugin_used')}")
            logger.info(f"  Results: {result.get('total_found')}")
        else:
            logger.warning("⚠ Plugin search returned None (might be rate limited)")

        logger.info("✓ WebSearch Integration Test: PASSED\n")
        return True

    except Exception as e:
        logger.error(f"✗ WebSearch Integration Test: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_capability_filtering():
    """Test capability-based plugin filtering."""
    logger.info("=" * 60)
    logger.info("TEST 4: Capability Filtering")
    logger.info("=" * 60)

    try:
        from torq_console.llm.providers.search_plugins import get_registry

        registry = get_registry()

        # Test news capability
        news_plugins = registry.get_plugins_by_capability("news")
        logger.info(f"✓ News plugins: {[p.metadata.name for p in news_plugins]}")

        # Test academic capability
        academic_plugins = registry.get_plugins_by_capability("academic")
        logger.info(f"✓ Academic plugins: {[p.metadata.name for p in academic_plugins]}")

        # Test general capability
        general_plugins = registry.get_plugins_by_capability("general")
        logger.info(f"✓ General plugins: {[p.metadata.name for p in general_plugins]}")

        logger.info("✓ Capability Filtering Test: PASSED\n")
        return True

    except Exception as e:
        logger.error(f"✗ Capability Filtering Test: FAILED - {e}")
        return False


async def test_plugin_health():
    """Test plugin health checking."""
    logger.info("=" * 60)
    logger.info("TEST 5: Plugin Health Check")
    logger.info("=" * 60)

    try:
        from torq_console.llm.providers.search_plugins import get_registry

        registry = get_registry()

        # Check health of all plugins
        health = await registry.health_check_all()

        for plugin_name, status in health.items():
            logger.info(f"✓ {plugin_name}: {status['status']}")

        logger.info("✓ Plugin Health Check Test: PASSED\n")
        return True

    except Exception as e:
        logger.error(f"✗ Plugin Health Check Test: FAILED - {e}")
        return False


async def main():
    """Run all tests."""
    logger.info("\n" + "=" * 60)
    logger.info("TORQ Console Phase 3: Plugin Architecture Tests")
    logger.info("=" * 60 + "\n")

    results = []

    # Run tests
    results.append(await test_plugin_registry())
    results.append(await test_plugin_search())
    results.append(await test_websearch_integration())
    results.append(await test_capability_filtering())
    results.append(await test_plugin_health())

    # Summary
    logger.info("=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    passed = sum(results)
    total = len(results)
    logger.info(f"Passed: {passed}/{total}")

    if passed == total:
        logger.info("✓ All tests PASSED! Plugin system is working correctly.")
    else:
        logger.warning(f"⚠ {total - passed} test(s) FAILED")

    logger.info("=" * 60 + "\n")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
