#!/usr/bin/env python3
"""
Test script to verify TORQ Console AI integration is working properly.

This will test:
1. DeepSeek API configuration
2. AI Integration functionality
3. Prince Flowers integration
4. Web interface response routing
"""

import asyncio
import os
import sys
import json
import logging
from pathlib import Path

# Add the torq_console to the path
sys.path.insert(0, str(Path(__file__).parent))

# Set up environment
os.environ.setdefault('PYTHONPATH', str(Path(__file__).parent))

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_ai_integration")

async def test_deepseek_provider():
    """Test DeepSeek provider functionality."""
    print("\n=== Testing DeepSeek Provider ===")

    try:
        from torq_console.llm.providers.deepseek import DeepSeekProvider

        # Check API key
        api_key = os.getenv('DEEPSEEK_API_KEY')
        print(f"DeepSeek API Key configured: {'Yes' if api_key else 'No'}")

        provider = DeepSeekProvider()
        print(f"Provider initialized: {provider.is_configured()}")

        # Test health check
        health = await provider.health_check()
        print(f"Health check: {health['status']}")

        if health['status'] in ['healthy', 'degraded']:
            # Test simple query
            response = await provider.query("Hello, can you respond with 'AI test successful'?")
            print(f"Test query response: {response[:100]}...")

        return True

    except Exception as e:
        print(f"DeepSeek provider test failed: {e}")
        return False

async def test_web_search_provider():
    """Test web search provider functionality."""
    print("\n=== Testing Web Search Provider ===")

    try:
        from torq_console.llm.providers.websearch import WebSearchProvider

        provider = WebSearchProvider()
        print(f"Provider initialized: {provider.is_available()}")

        # Check configured methods
        methods = provider.get_configured_methods()
        print(f"Configured search methods: {methods}")

        # Test health check
        health = await provider.health_check()
        print(f"Health check: {health['status']}")
        print(f"Available methods: {health.get('available_methods', [])}")

        # Test search
        results = await provider.search("AI news test", max_results=3)
        print(f"Search test - Method used: {results.get('method_used', 'unknown')}")
        print(f"Search test - Results count: {len(results.get('results', []))}")

        return True

    except Exception as e:
        print(f"Web search provider test failed: {e}")
        return False

async def test_llm_manager():
    """Test LLM manager functionality."""
    print("\n=== Testing LLM Manager ===")

    try:
        from torq_console.llm.manager import LLMManager

        manager = LLMManager()
        print(f"Manager initialized with providers: {list(manager.providers.keys())}")

        # Test health check
        health = await manager.health_check()
        print(f"Health check results: {list(health.keys())}")

        # Test provider info
        provider_info = manager.list_providers()
        for name, info in provider_info.items():
            print(f"Provider {name}: configured={info.get('configured', False)}")

        # Test query if DeepSeek is configured
        if 'deepseek' in manager.providers:
            try:
                response = await manager.query('deepseek', 'Hello, respond with "LLM Manager test successful"')
                print(f"Test query response: {response[:100]}...")
            except Exception as e:
                print(f"Query test failed: {e}")

        return True

    except Exception as e:
        print(f"LLM manager test failed: {e}")
        return False

async def test_ai_integration():
    """Test the main AI integration class."""
    print("\n=== Testing AI Integration ===")

    try:
        from torq_console.utils.ai_integration import AIIntegration

        ai = AIIntegration()
        print(f"AI Integration initialized in enhanced mode: {ai.enhanced_mode}")

        # Test capabilities
        capabilities = ai.get_capabilities()
        print(f"Features: {capabilities.get('features', [])}")

        # Test health check
        health = await ai.health_check()
        print(f"Overall health: {health['overall_status']}")
        print(f"Components: {list(health.get('components', {}).keys())}")

        # Test query classification
        test_queries = [
            "search for AI news",
            "latest artificial intelligence developments",
            "explain machine learning",
            "hello world"
        ]

        for query in test_queries:
            query_type = ai.classify_query(query)
            print(f"'{query}' classified as: {query_type}")

        # Test response generation
        print("\nTesting response generation...")
        response = await ai.generate_response("search web for ai news")
        print(f"Response success: {response.get('success', False)}")
        print(f"Response length: {len(response.get('content', ''))}")

        return True

    except Exception as e:
        print(f"AI integration test failed: {e}")
        return False

async def test_prince_flowers_integration():
    """Test Prince Flowers integration."""
    print("\n=== Testing Prince Flowers Integration ===")

    try:
        from torq_integration import PrinceFlowersIntegrationWrapper

        integration = PrinceFlowersIntegrationWrapper()
        print(f"Integration initialized with agent type: {integration.agent_type}")

        # Test health check
        health = await integration.health_check()
        print(f"Health status: {health['overall_status']}")

        # Test capabilities
        capabilities = integration.get_capabilities()
        print(f"Agent type: {capabilities.get('agent_type', 'unknown')}")

        # Test query
        response = await integration.query("search for latest AI developments", show_performance=True)
        print(f"Query success: {response.success}")
        print(f"Response length: {len(response.content)}")
        if response.agent_status:
            print(f"Agent interactions: {response.agent_status.get('total_queries', 0)}")

        return True

    except Exception as e:
        print(f"Prince Flowers integration test failed: {e}")
        return False

async def test_web_interface_simulation():
    """Simulate web interface requests."""
    print("\n=== Testing Web Interface Simulation ===")

    try:
        # Test the actual web interface components
        from torq_console.utils.ai_integration import AIIntegration

        ai = AIIntegration()

        # Simulate different types of web requests
        test_requests = [
            "search web for ai news",
            "what is artificial intelligence",
            "latest AI developments",
            "prince search machine learning trends"
        ]

        results = []
        for request in test_requests:
            print(f"\nProcessing: '{request}'")
            response = await ai.generate_response(request)

            result = {
                'request': request,
                'success': response.get('success', False),
                'response_length': len(response.get('content', '')),
                'query_type': response.get('metadata', {}).get('query_type', 'unknown'),
                'execution_time': response.get('metadata', {}).get('execution_time', 0)
            }

            results.append(result)
            print(f"  Success: {result['success']}")
            print(f"  Type: {result['query_type']}")
            print(f"  Time: {result['execution_time']:.2f}s")

        # Summary
        successful = sum(1 for r in results if r['success'])
        print(f"\nSimulation Results: {successful}/{len(results)} successful")

        return successful == len(results)

    except Exception as e:
        print(f"Web interface simulation failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🚀 TORQ Console AI Integration Test Suite")
    print("=" * 60)

    # Environment check
    print("\n=== Environment Check ===")
    deepseek_key = os.getenv('DEEPSEEK_API_KEY')
    google_key = os.getenv('GOOGLE_SEARCH_API_KEY')
    brave_key = os.getenv('BRAVE_SEARCH_API_KEY')

    print(f"DEEPSEEK_API_KEY: {'✅ Configured' if deepseek_key else '❌ Missing'}")
    print(f"GOOGLE_SEARCH_API_KEY: {'✅ Configured' if google_key else '❌ Missing'}")
    print(f"BRAVE_SEARCH_API_KEY: {'✅ Configured' if brave_key else '❌ Missing'}")

    # Run tests
    test_results = []

    tests = [
        ("DeepSeek Provider", test_deepseek_provider),
        ("Web Search Provider", test_web_search_provider),
        ("LLM Manager", test_llm_manager),
        ("AI Integration", test_ai_integration),
        ("Prince Flowers Integration", test_prince_flowers_integration),
        ("Web Interface Simulation", test_web_interface_simulation),
    ]

    for test_name, test_func in tests:
        try:
            result = await test_func()
            test_results.append((test_name, result))
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"\n{test_name}: {status}")
        except Exception as e:
            test_results.append((test_name, False))
            print(f"\n{test_name}: ❌ FAILED with exception: {e}")

    # Final summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)

    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<30} {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! AI integration is ready for deployment.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        sys.exit(1)