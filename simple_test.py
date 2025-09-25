#!/usr/bin/env python3
"""
Simple test to check TORQ Console AI integration.
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Set up environment
sys.path.insert(0, str(Path(__file__).parent))
os.environ['PYTHONPATH'] = str(Path(__file__).parent)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("simple_test")

async def test_deepseek():
    """Test DeepSeek API directly."""
    print("=== Testing DeepSeek API ===")

    try:
        from torq_console.llm.providers.deepseek import DeepSeekProvider

        provider = DeepSeekProvider()

        # Check configuration
        api_key = os.getenv('DEEPSEEK_API_KEY')
        print(f"API Key configured: {'Yes' if api_key else 'No'}")
        print(f"Provider configured: {provider.is_configured()}")

        if provider.is_configured():
            # Test simple query
            print("Testing query...")
            response = await provider.query("Hello! Please respond briefly.")
            print(f"Response: {response[:200]}...")
            return True
        else:
            print("ERROR: Provider not configured")
            return False

    except Exception as e:
        print(f"ERROR: {e}")
        return False

async def test_ai_integration():
    """Test AI Integration."""
    print("\n=== Testing AI Integration ===")

    try:
        from torq_console.utils.ai_integration import AIIntegration

        ai = AIIntegration()
        print(f"Enhanced mode: {ai.enhanced_mode}")

        # Test simple query
        response = await ai.generate_response("What is machine learning?")
        print(f"Success: {response.get('success')}")
        print(f"Content length: {len(response.get('content', ''))}")

        if response.get('success') and len(response.get('content', '')) > 50:
            print("Response preview:", response.get('content', '')[:100] + "...")
            return True
        else:
            print("ERROR: No meaningful response")
            return False

    except Exception as e:
        print(f"ERROR: {e}")
        return False

async def test_web_interface():
    """Test web interface method."""
    print("\n=== Testing Web Interface ===")

    try:
        from torq_console.core.config import TorqConfig
        from torq_console.core.console import TorqConsole
        from torq_console.ui.web import WebUI

        config = TorqConfig()
        console = TorqConsole(config)
        web_ui = WebUI(console)

        # Test the _generate_ai_response method directly
        response = await web_ui._generate_ai_response("what is artificial intelligence", None)

        print(f"Response length: {len(response) if response else 0}")
        if response and len(response) > 50:
            print("Response preview:", response[:150] + "...")
            return True
        else:
            print("ERROR: No meaningful response from web interface")
            return False

    except Exception as e:
        print(f"ERROR: {e}")
        return False

async def main():
    """Run tests."""
    print("TORQ Console AI Integration Quick Test")
    print("=" * 50)

    # Check environment
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if api_key:
        print(f"DEEPSEEK_API_KEY found: {api_key[:15]}...")
    else:
        print("WARNING: DEEPSEEK_API_KEY not found!")

    # Run tests
    tests = [
        ("DeepSeek API", test_deepseek),
        ("AI Integration", test_ai_integration),
        ("Web Interface", test_web_interface)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"Test {test_name} crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("RESULTS:")
    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{len(results)} tests passed")
    return passed == len(results)

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Test crashed: {e}")
        sys.exit(1)