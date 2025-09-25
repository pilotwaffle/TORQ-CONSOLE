#!/usr/bin/env python3
"""
Test script to verify the /api/chat endpoint fix

This script can be used to test the API endpoint after starting the server.
"""

import requests
import json
import time

def test_api_chat_endpoint():
    """Test the /api/chat endpoint with a search query."""

    print("🧪 TESTING TORQ Console /api/chat Endpoint Fix")
    print("=" * 50)

    # Test URL
    url = "http://127.0.0.1:8899/api/chat"

    # Test payload - the exact query that was failing
    test_query = "search web for ai news"
    payload = {
        "message": test_query,
        "include_context": True,
        "generate_response": True
    }

    print(f"🔍 Testing query: '{test_query}'")
    print(f"📡 Endpoint: {url}")
    print("🚀 Sending request...")

    try:
        # Send the request
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        print(f"📊 Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS! Endpoint is working")
            print(f"🤖 Agent: {result.get('agent', 'Unknown')}")
            print(f"📝 Response preview: {result.get('response', '')[:200]}...")

            if "Edit completed successfully" in result.get('response', ''):
                print("❌ STILL BROKEN: Getting edit response instead of AI search")
                return False
            else:
                print("✅ FIXED: Getting proper AI response!")
                return True

        else:
            print(f"❌ ERROR: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Is the TORQ Console server running?")
        print("💡 Run: python start_torq_with_fixes.py")
        return False

    except requests.exceptions.Timeout:
        print("❌ TIMEOUT: Request took too long")
        return False

    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False

def main():
    """Main test function."""
    print("Starting API endpoint test in 3 seconds...")
    print("(Make sure TORQ Console server is running)")
    time.sleep(3)

    success = test_api_chat_endpoint()

    print("\n" + "=" * 50)
    if success:
        print("🎉 TEST PASSED: The critical fix is working!")
        print("Users should now get AI search results instead of edit confirmations")
    else:
        print("💥 TEST FAILED: The fix may need additional attention")
        print("Check the server logs for more details")
    print("=" * 50)

if __name__ == "__main__":
    main()