#!/usr/bin/env python3
"""
Direct test of the /api/chat endpoint to verify it's properly registered
"""

import requests
import json
import sys

def test_direct_chat_endpoint():
    """Test the direct chat endpoint directly"""

    url = "http://127.0.0.1:8899/api/chat"

    test_payload = {
        "message": "search web for ai news",
        "include_context": True,
        "generate_response": True
    }

    headers = {
        "Content-Type": "application/json"
    }

    print(f"Testing POST {url}")
    print(f"Payload: {json.dumps(test_payload, indent=2)}")
    print("-" * 50)

    try:
        response = requests.post(url, json=test_payload, headers=headers, timeout=30)

        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            result = response.json()
            print("SUCCESS: Chat endpoint is working!")
            print(f"Agent: {result.get('agent', 'Unknown')}")
            print(f"Response: {result.get('response', 'No response')[:200]}...")
            return True
        else:
            print(f"FAILED: HTTP {response.status_code}")
            print(f"Error: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"CONNECTION ERROR: {e}")
        return False

def test_openapi_spec():
    """Check if the endpoint appears in OpenAPI spec"""

    url = "http://127.0.0.1:8899/openapi.json"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            spec = response.json()
            paths = spec.get('paths', {})

            if '/api/chat' in paths:
                print("SUCCESS: /api/chat found in OpenAPI spec")
                chat_spec = paths['/api/chat']
                print(f"Methods: {list(chat_spec.keys())}")
                return True
            else:
                print("FAILED: /api/chat NOT found in OpenAPI spec")
                print(f"Available paths: {list(paths.keys())[:10]}")
                return False
        else:
            print(f"Failed to get OpenAPI spec: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"Error getting OpenAPI spec: {e}")
        return False

def main():
    print("TORQ Console Direct Chat Endpoint Test")
    print("=" * 60)

    # Test OpenAPI spec first
    openapi_ok = test_openapi_spec()
    print()

    # Test the actual endpoint
    endpoint_ok = test_direct_chat_endpoint()
    print()

    if openapi_ok and endpoint_ok:
        print("ALL TESTS PASSED - Chat endpoint is fully functional!")
        sys.exit(0)
    else:
        print("TESTS FAILED - Chat endpoint has issues")
        sys.exit(1)

if __name__ == "__main__":
    main()