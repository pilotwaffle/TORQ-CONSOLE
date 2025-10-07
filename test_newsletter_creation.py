#!/usr/bin/env python3
"""
Test script to demonstrate TORQ Console with Perplexity search integration
by having Prince Flowers agent create a newsletter about NTT's Expert Knowledge Visualization AI
"""

import asyncio
import json
import aiohttp
import time
from datetime import datetime

async def test_newsletter_creation():
    """Test the complete workflow: Perplexity search + Prince Flowers newsletter generation"""

    console_url = "http://127.0.0.1:8892"

    # Newsletter creation prompt for Prince Flowers agent
    prompt = """
    Prince Flowers Agent Task: Research and Newsletter Creation

    Please use the web search capabilities to research "NTT's Expert Knowledge Visualization AI" and create a comprehensive 1200-word newsletter about this technology.

    The newsletter should include:
    1. Executive Summary (150 words)
    2. Technology Overview (300 words)
    3. Key Features and Capabilities (250 words)
    4. Business Applications and Use Cases (300 words)
    5. Market Impact and Future Outlook (200 words)

    Use web search to gather the most current information available, and structure this as a professional newsletter suitable for technology executives and AI practitioners.

    Please ensure you search for recent developments, technical specifications, and real-world implementations of NTT's Expert Knowledge Visualization AI technology.
    """

    print("🔍 Testing TORQ Console with Perplexity Search Integration")
    print("📊 Task: Create newsletter about NTT's Expert Knowledge Visualization AI")
    print(f"🌐 Console URL: {console_url}")
    print("-" * 80)

    try:
        async with aiohttp.ClientSession() as session:
            # Test the chat endpoint with the newsletter request
            print("📝 Sending request to Prince Flowers agent...")

            chat_data = {
                "message": prompt,
                "session_id": f"newsletter-test-{int(time.time())}",
                "tools": ["web_search", "prince_flowers"],
                "stream": False
            }

            start_time = time.time()

            async with session.post(
                f"{console_url}/api/chat",
                json=chat_data,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=120)  # 2 minute timeout
            ) as response:

                if response.status == 200:
                    result = await response.json()
                    end_time = time.time()

                    print(f"✅ Request completed in {end_time - start_time:.2f} seconds")
                    print("-" * 80)

                    # Display the response
                    if 'response' in result:
                        print("📄 NEWSLETTER CONTENT:")
                        print("=" * 80)
                        print(result['response'])
                        print("=" * 80)

                        # Count words
                        word_count = len(result['response'].split())
                        print(f"📊 Word count: {word_count}")

                        if word_count >= 1000:
                            print("✅ Newsletter meets minimum length requirement")
                        else:
                            print("⚠️  Newsletter is shorter than expected")

                    # Display metadata if available
                    if 'metadata' in result:
                        print("\n🔍 SEARCH METADATA:")
                        metadata = result['metadata']
                        if 'search_provider' in metadata:
                            print(f"Search Provider: {metadata['search_provider']}")
                        if 'sources_found' in metadata:
                            print(f"Sources Found: {metadata['sources_found']}")

                    return True

                else:
                    print(f"❌ Error: HTTP {response.status}")
                    error_text = await response.text()
                    print(f"Error details: {error_text}")
                    return False

    except asyncio.TimeoutError:
        print("⏱️  Request timed out - the search and newsletter generation may take longer")
        return False
    except Exception as e:
        print(f"❌ Error during request: {e}")
        return False

async def test_perplexity_direct():
    """Test Perplexity search directly"""
    print("\n🔍 Testing Perplexity Search Directly...")

    try:
        from torq_console.integrations.perplexity_search import test_perplexity_search
        result = await test_perplexity_search()
        if result:
            print("✅ Direct Perplexity test successful")
        else:
            print("❌ Direct Perplexity test failed")
        return result
    except Exception as e:
        print(f"❌ Direct Perplexity test error: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 TORQ CONSOLE + PERPLEXITY INTEGRATION TEST")
    print("=" * 80)
    print(f"🕐 Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Test 1: Direct Perplexity integration
    success1 = await test_perplexity_direct()

    print("\n" + "=" * 80)

    # Test 2: Full newsletter creation workflow
    success2 = await test_newsletter_creation()

    print("\n" + "=" * 80)
    print("📋 TEST SUMMARY:")
    print(f"✅ Direct Perplexity Test: {'PASSED' if success1 else 'FAILED'}")
    print(f"✅ Newsletter Creation Test: {'PASSED' if success2 else 'FAILED'}")

    if success1 and success2:
        print("🎉 ALL TESTS PASSED - Perplexity integration is working correctly!")
    else:
        print("⚠️  Some tests failed - check the console logs for details")

    print(f"🕐 End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main())