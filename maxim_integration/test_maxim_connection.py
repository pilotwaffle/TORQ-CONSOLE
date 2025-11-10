"""
Test Maxim AI API Connection
Using API key: sk_mx_mhr8zshq_6naZMAwzpYq32PGMxUUtfIKFtkHWeRX8
"""

import asyncio
import aiohttp
import json

async def test_maxim_endpoints():
    """Test different possible Maxim AI API endpoints"""

    api_key = "sk_mx_mhr8zshq_6naZMAwzpYq32PGMxUUtfIKFtkHWeRX8"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "TORQ-Console/1.0"
    }

    # Possible Maxim AI API base URLs
    base_urls = [
        "https://api.maxim.ai",
        "https://app.maxim.ai/api",
        "https://api.getmaxim.ai",
        "https://maxim.ai/api",
        "https://engine.maxim.ai",
        "https://app.getmaxim.ai/api"
    ]

    # Possible endpoints to test
    endpoints = [
        "/v1/health",
        "/v1/status",
        "/v1/user",
        "/v1/me",
        "/v1/evaluators",
        "/v1/projects",
        "/health",
        "/status",
        "/user",
        "/evaluators",
        "/projects",
        "/api/v1/status",
        "/api/v1/evaluators"
    ]

    async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as session:
        print("Testing Maxim AI API Connection...")
        print(f"API Key: {api_key[:20]}...")
        print("="*60)

        for base_url in base_urls:
            print(f"\nTesting base URL: {base_url}")

            for endpoint in endpoints:
                url = f"{base_url}{endpoint}"
                try:
                    async with session.get(url) as response:
                        status = response.status
                        if status == 200:
                            print(f"  [SUCCESS] {endpoint} - Status: {status}")
                            try:
                                data = await response.json()
                                print(f"    Response: {json.dumps(data, indent=2)[:200]}...")
                                return True, base_url, endpoint, data
                            except:
                                text = await response.text()
                                print(f"    Response: {text[:200]}...")
                                return True, base_url, endpoint, text
                        elif status == 401:
                            print(f"  [AUTH] {endpoint} - Status: {status} (API key recognized)")
                        elif status == 404:
                            print(f"  [404] {endpoint} - Status: {status}")
                        elif status == 403:
                            print(f"  [FORBIDDEN] {endpoint} - Status: {status}")
                        else:
                            print(f"  [OTHER] {endpoint} - Status: {status}")
                except aiohttp.ClientError as e:
                    print(f"  [ERROR] {endpoint} - {str(e)[:50]}")
                except Exception as e:
                    print(f"  [ERROR] {endpoint} - {str(e)[:50]}")

        print(f"\nNo successful connections found.")
        return False, None, None, None

async def test_direct_maxim_api():
    """Try direct Maxim API call based on common patterns"""

    api_key = "sk_mx_mhr8zshq_6naZMAwzpYq32PGMxUUtfIKFtkHWeRX8"

    # Try different request patterns
    test_requests = [
        {
            "url": "https://api.maxim.ai/v1/evaluators",
            "method": "GET",
            "description": "List evaluators"
        },
        {
            "url": "https://api.maxim.ai/v1/evaluations",
            "method": "POST",
            "data": {
                "prompt": "Test prompt",
                "response": "Test response",
                "evaluator_type": "quality"
            },
            "description": "Create evaluation"
        },
        {
            "url": "https://api.maxim.ai/v1/run",
            "method": "POST",
            "data": {
                "prompt": "What is 2+2?",
                "response": "4",
                "evaluators": ["accuracy", "clarity"]
            },
            "description": "Run evaluation"
        }
    ]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as session:
        print("Testing direct Maxim AI API calls...")
        print("="*60)

        for request_config in test_requests:
            print(f"\n{request_config['description']}:")
            print(f"  URL: {request_config['url']}")
            print(f"  Method: {request_config['method']}")

            try:
                if request_config['method'] == 'GET':
                    async with session.get(request_config['url']) as response:
                        status = response.status
                        print(f"  Status: {status}")

                        if status == 200:
                            data = await response.json()
                            print(f"  [SUCCESS] Response: {json.dumps(data, indent=2)[:300]}...")
                            return True
                        elif status == 401:
                            print(f"  [AUTH] Authentication required")
                        elif status == 403:
                            print(f"  [FORBIDDEN] Access denied")
                        else:
                            error_text = await response.text()
                            print(f"  [ERROR] {error_text[:200]}")

                elif request_config['method'] == 'POST':
                    async with session.post(request_config['url'], json=request_config['data']) as response:
                        status = response.status
                        print(f"  Status: {status}")

                        if status == 200 or status == 201:
                            data = await response.json()
                            print(f"  [SUCCESS] Response: {json.dumps(data, indent=2)[:300]}...")
                            return True
                        elif status == 401:
                            print(f"  [AUTH] Authentication required")
                        elif status == 403:
                            print(f"  [FORBIDDEN] Access denied")
                        else:
                            error_text = await response.text()
                            print(f"  [ERROR] {error_text[:200]}")

            except Exception as e:
                print(f"  [EXCEPTION] {str(e)[:100]}")

    return False

async def main():
    """Main test function"""
    print("Maxim AI API Connection Test")
    print(f"Using API key: sk_mx_mhr8zshq_6naZMAwzpYq32PGMxUUtfIKFtkHWeRX8")
    print("="*80)

    # Test 1: Endpoint discovery
    print("\n1. Testing endpoint discovery...")
    success, base_url, endpoint, data = await test_maxim_endpoints()

    if success:
        print(f"\n[SUCCESS] Found working endpoint!")
        print(f"Base URL: {base_url}")
        print(f"Endpoint: {endpoint}")
        return

    # Test 2: Direct API calls
    print("\n2. Testing direct API calls...")
    success = await test_direct_maxim_api()

    if success:
        print(f"\n[SUCCESS] Direct API call successful!")
        return

    # Test 3: Alternative approach - Check if it's a different API pattern
    print("\n3. Testing alternative API patterns...")

    # Maybe it's a OpenAI-compatible API?
    openai_compatible_urls = [
        "https://api.maxim.ai/v1/chat/completions",
        "https://api.maxim.ai/v1/completions"
    ]

    headers = {
        "Authorization": f"Bearer sk_mx_mhr8zshq_6naZMAwzpYq32PGMxUUtfIKFtkHWeRX8",
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as session:
        for url in openai_compatible_urls:
            try:
                data = {
                    "model": "maxim-evaluator",
                    "messages": [{"role": "user", "content": "Test"}],
                    "max_tokens": 10
                }

                async with session.post(url, json=data) as response:
                    print(f"  Testing {url}: Status {response.status}")
                    if response.status == 200:
                        result = await response.json()
                        print(f"  [SUCCESS] OpenAI-compatible API found!")
                        print(f"  Response: {json.dumps(result, indent=2)[:200]}...")
                        return
            except Exception as e:
                print(f"  Error with {url}: {str(e)[:50]}")

    print(f"\n[CONCLUSION] Could not establish connection to Maxim AI API.")
    print(f"Possible reasons:")
    print(f"1. API key is invalid or expired")
    print(f"2. Base URL is incorrect")
    print(f"3. Different authentication method required")
    print(f"4. Network connectivity issues")
    print(f"5. Maxim AI uses different API structure")

if __name__ == "__main__":
    asyncio.run(main())