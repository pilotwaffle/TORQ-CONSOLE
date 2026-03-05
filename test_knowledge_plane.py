#!/usr/bin/env python3
"""
TORQ Knowledge Plane API Test Script

Tests the Knowledge Plane API endpoints after deployment.
Run this against the deployed Railway service.
"""

import httpx
import json
import sys
import asyncio
from typing import Dict, Any, Optional

# Default service URL - update with your deployed service
SERVICE_URL = "https://web-production-74ed0.up.railway.app"


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"


def print_success(msg: str):
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")


def print_error(msg: str):
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")


def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.RESET}")


def print_header(msg: str):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}{msg}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")


async def test_health(client: httpx.AsyncClient) -> bool:
    """Test the health endpoint."""
    print_header("Testing Health Endpoint")
    try:
        response = await client.get(f"{SERVICE_URL}/health", timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Health check passed")
            print_info(f"Service: {data.get('service')}")
            print_info(f"Version: {data.get('version')}")
            print_info(f"Status: {data.get('status')}")
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Health check error: {e}")
        return False


async def test_knowledge_health(client: httpx.AsyncClient) -> bool:
    """Test the Knowledge Plane health endpoint."""
    print_header("Testing Knowledge Plane Health")
    try:
        response = await client.get(f"{SERVICE_URL}/api/knowledge/health", timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            print_success("Knowledge Plane health check passed")
            print_info(f"Status: {data.get('status')}")
            print_info(f"Supabase: {data.get('supabase_configured')}")
            print_info(f"OpenAI: {data.get('openai_configured')}")
            print_info(f"Redis: {data.get('redis_configured')}")
            return True
        else:
            print_error(f"Knowledge Plane health failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Knowledge Plane health error: {e}")
        return False


async def test_store_knowledge(client: httpx.AsyncClient) -> Optional[str]:
    """Test storing knowledge."""
    print_header("Testing Store Knowledge")
    test_data = {
        "content": "FastAPI is a modern, fast web framework for building APIs with Python 3.7+ based on standard Python type hints.",
        "title": "FastAPI Framework",
        "category": "documentation",
        "tags": ["python", "fastapi", "web", "api"],
        "source": "test_script",
        "metadata": {"test": True}
    }

    try:
        response = await client.post(
            f"{SERVICE_URL}/api/knowledge/store",
            json=test_data,
            timeout=30.0
        )
        if response.status_code == 200:
            data = response.json()
            print_success("Knowledge stored successfully")
            print_info(f"ID: {data.get('id')}")
            print_info(f"Message: {data.get('message')}")
            return data.get('id')
        else:
            print_error(f"Store failed: {response.status_code}")
            print_info(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Store error: {e}")
        return None


async def test_search_knowledge(client: httpx.AsyncClient, query: str = "FastAPI") -> bool:
    """Test searching knowledge."""
    print_header(f"Testing Search Knowledge: '{query}'")
    search_data = {
        "query": query,
        "limit": 5
    }

    try:
        response = await client.post(
            f"{SERVICE_URL}/api/knowledge/search",
            json=search_data,
            timeout=30.0
        )
        if response.status_code == 200:
            data = response.json()
            print_success(f"Search completed")
            print_info(f"Query: {data.get('query')}")
            print_info(f"Total results: {data.get('total')}")
            print_info(f"Execution time: {data.get('execution_time_ms')}ms")

            if data.get('results'):
                print_info("\nTop results:")
                for i, result in enumerate(data.get('results', [])[:3], 1):
                    title = result.get('title', 'No title')
                    similarity = result.get('similarity', 'N/A')
                    print(f"  {i}. {title} (similarity: {similarity})")
            return True
        else:
            print_error(f"Search failed: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Search error: {e}")
        return False


async def test_recent_knowledge(client: httpx.AsyncClient) -> bool:
    """Test getting recent knowledge."""
    print_header("Testing Recent Knowledge")
    try:
        response = await client.get(
            f"{SERVICE_URL}/api/knowledge/recent",
            params={"limit": 5},
            timeout=30.0
        )
        if response.status_code == 200:
            data = response.json()
            print_success(f"Retrieved recent knowledge")
            print_info(f"Total: {data.get('total')}")

            if data.get('results'):
                print_info("\nRecent entries:")
                for i, result in enumerate(data.get('results', [])[:3], 1):
                    title = result.get('title', result.get('content', '')[:50] + '...')
                    print(f"  {i}. {title}")
            return True
        else:
            print_error(f"Recent knowledge failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Recent knowledge error: {e}")
        return False


async def test_stats(client: httpx.AsyncClient) -> bool:
    """Test getting statistics."""
    print_header("Testing Knowledge Stats")
    try:
        response = await client.get(
            f"{SERVICE_URL}/api/knowledge/stats",
            timeout=30.0
        )
        if response.status_code == 200:
            data = response.json()
            print_success("Retrieved statistics")
            print_info(f"Total entries: {data.get('total_entries')}")
            print_info(f"Total tags: {data.get('total_tags')}")
            print_info(f"By category: {data.get('by_category')}")
            print_info(f"By source: {data.get('by_source')}")
            return True
        else:
            print_error(f"Stats failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Stats error: {e}")
        return False


async def test_root_endpoint(client: httpx.AsyncClient) -> bool:
    """Test the root endpoint."""
    print_header("Testing Root Endpoint")
    try:
        response = await client.get(f"{SERVICE_URL}/", timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            print_success("Root endpoint accessible")
            print_info(f"Service: {data.get('service')}")
            print_info(f"Version: {data.get('version')}")
            print_info("\nAvailable endpoints:")
            for endpoint in data.get('endpoints', []):
                print(f"  - {endpoint}")
            return True
        else:
            print_error(f"Root endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Root endpoint error: {e}")
        return False


async def main():
    """Run all tests."""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}TORQ Knowledge Plane API Test Suite{Colors.RESET}")
    print(f"{Colors.BLUE}Service: {SERVICE_URL}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")

    async with httpx.AsyncClient() as client:
        results = {
            "root": await test_root_endpoint(client),
            "health": await test_health(client),
            "knowledge_health": await test_knowledge_health(client),
            "store": await test_store_knowledge(client) is not None,
            "search": await test_search_knowledge(client, "FastAPI"),
            "recent": await test_recent_knowledge(client),
            "stats": await test_stats(client)
        }

        # Summary
        print_header("Test Summary")
        passed = sum(1 for v in results.values() if v)
        total = len(results)

        for test, result in results.items():
            status = f"{Colors.GREEN}PASS{Colors.RESET}" if result else f"{Colors.RED}FAIL{Colors.RESET}"
            print(f"  {test}: {status}")

        print(f"\n{Colors.BLUE}Results: {passed}/{total} tests passed{Colors.RESET}\n")

        if passed == total:
            print_success("All tests passed!")
            return 0
        else:
            print_error(f"{total - passed} test(s) failed")
            return 1


if __name__ == "__main__":
    # Allow custom service URL
    if len(sys.argv) > 1:
        SERVICE_URL = sys.argv[1]

    exit_code = asyncio.run(main())
    sys.exit(exit_code)
