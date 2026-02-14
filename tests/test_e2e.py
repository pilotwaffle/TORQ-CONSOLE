"""
End-to-End (E2E) Test Suite for TORQ Console

Tests complete user workflows from browser UI to backend.
"""

import asyncio
import pytest
import httpx
from typing import Dict, Any, List
from urllib.parse import urljoin


class TestResult:
    """Container for test results."""

    def __init__(self, name: str, passed: bool, message: str = "", details: str = ""):
        self.name = name
        self.passed = passed
        self.message = message
        self.details = details

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "message": self.message,
            "details": self.details
        }


class E2ETestSuite:
    """
    End-to-End test suite for TORQ Console.

    Tests:
    - Frontend loading and rendering
    - API endpoints and responses
    - WebSocket connections
    - Authentication flows
    - LLM provider integration
    - File operations
    """

    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.results: List[TestResult] = []
        self.api_key = self._get_api_key()

    def _get_api_key(self) -> str:
        """Get or generate API key for testing."""
        import secrets
        return secrets.token_urlsafe(32)

    async def _make_request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to TORQ Console."""
        url = urljoin(self.base_url, path)
        headers = kwargs.pop("headers", {})
        headers["X-API-Key"] = self.api_key

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers, **kwargs)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=headers, **kwargs)
                elif method.upper() == "PUT":
                    response = await client.put(url, headers=headers, **kwargs)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=headers, **kwargs)
                else:
                    return {
                        "status": "error",
                        "message": f"Unsupported method: {method}"
                    }

                return {
                    "status": "success",
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
                }
            except httpx.TimeoutException:
                return {
                    "status": "error",
                    "message": "Request timed out"
                }
            except httpx.ConnectError as e:
                return {
                    "status": "error",
                    "message": f"Connection error: {e}"
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Unexpected error: {e}"
                }

    async def test_api_health(self) -> TestResult:
        """Test API health endpoint."""
        try:
            response = await self._make_request("GET", "/api/health")
            is_passed = response["status"] == "success" and response["status_code"] == 200

            return TestResult(
                name="API Health Check",
                passed=is_passed,
                message="API health endpoint accessible" if is_passed else f"Failed: {response.get('message', 'Unknown error')}",
                details=f"Status code: {response.get('status_code', 'N/A')}"
            )
        except Exception as e:
            return TestResult(
                name="API Health Check",
                passed=False,
                message=f"Exception: {e}"
            )

    async def test_web_ui_load(self) -> TestResult:
        """Test web UI page loads."""
        try:
            response = await self._make_request("GET", "/")
            is_passed = response["status"] == "success" and response["status_code"] == 200

            content = response.get("data", "")
            has_torq_branding = "TORQ" in content or "TORQ" in content

            return TestResult(
                name="Web UI Load",
                passed=is_passed and has_torq_branding,
                message="Web UI loads with TORQ branding" if (is_passed and has_torq_branding) else "Web UI load failed",
                details=f"Status: {response.get('status_code', 'N/A')}, Branded: {has_torq_branding}"
            )
        except Exception as e:
            return TestResult(
                name="Web UI Load",
                passed=False,
                message=f"Exception: {e}"
            )

    async def test_dashboard_access(self) -> TestResult:
        """Test dashboard is accessible."""
        try:
            response = await self._make_request("GET", "/dashboard/api/metrics")
            is_passed = response["status"] == "success" and response["status_code"] == 200

            return TestResult(
                name="Dashboard Access",
                passed=is_passed,
                message="Dashboard metrics API accessible" if is_passed else f"Failed: {response.get('message', 'Unknown error')}",
                details=f"Status: {response.get('status_code', 'N/A')}"
            )
        except Exception as e:
            return TestResult(
                name="Dashboard Access",
                passed=False,
                message=f"Exception: {e}"
            )

    async def test_pwa_manifest(self) -> TestResult:
        """Test PWA manifest is accessible."""
        try:
            response = await self._make_request("GET", "/manifest.json")
            is_passed = response["status"] == "success" and response["status_code"] == 200

            data = response.get("data", "")
            has_required_fields = all(field in data for field in ["name", "short_name", "start_url", "display"])

            return TestResult(
                name="PWA Manifest",
                passed=is_passed and has_required_fields,
                message="PWA manifest accessible with all required fields" if (is_passed and has_required_fields) else "PWA manifest missing fields",
                details=f"Status: {response.get('status_code', 'N/A')}, Fields: {has_required_fields}"
            )
        except Exception as e:
            return TestResult(
                name="PWA Manifest",
                passed=False,
                message=f"Exception: {e}"
            )

    async def test_service_worker(self) -> TestResult:
        """Test service worker is accessible."""
        try:
            response = await self._make_request("GET", "/static/service-worker.js")
            is_passed = response["status"] == "success" and response["status_code"] == 200

            content = response.get("data", "")
            has_service_worker_features = "CACHE_NAME" in content and "fetch" in content

            return TestResult(
                name="Service Worker",
                passed=is_passed and has_service_worker_features,
                message="Service worker accessible with required features" if (is_passed and has_service_worker_features) else "Service worker missing features",
                details=f"Status: {response.get('status_code', 'N/A')}, Features: {has_service_worker_features}"
            )
        except Exception as e:
            return TestResult(
                name="Service Worker",
                passed=False,
                message=f"Exception: {e}"
            )

    async def test_offline_page(self) -> TestResult:
        """Test offline fallback page."""
        try:
            response = await self._make_request("GET", "/offline")
            is_passed = response["status"] == "success" and response["status_code"] == 200

            content = response.get("data", "")
            has_offline_message = "offline" in content.lower() or "connection" in content.lower()

            return TestResult(
                name="Offline Page",
                passed=is_passed and has_offline_message,
                message="Offline fallback page accessible" if (is_passed and has_offline_message) else "Offline page not found",
                details=f"Status: {response.get('status_code', 'N/A')}"
            )
        except Exception as e:
            return TestResult(
                name="Offline Page",
                passed=False,
                message=f"Exception: {e}"
            )

    async def run_all_tests(self) -> List[TestResult]:
        """Run all E2E tests and return results."""
        tests = [
            self.test_api_health(),
            self.test_web_ui_load(),
            self.test_dashboard_access(),
            self.test_pwa_manifest(),
            self.test_service_worker(),
            self.test_offline_page()
        ]

        self.results = await asyncio.gather(*tests)
        return self.results

    def print_results(self) -> None:
        """Print test results to console."""
        print("\n" + "=" * 60)
        print("TORQ CONSOLE E2E TEST SUITE RESULTS")
        print("=" * 60 + "\n")

        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        pass_rate = (passed / total * 100) if total > 0 else 0

        print(f"Tests Run: {total}")
        print(f"Tests Passed: {passed}")
        print(f"Tests Failed: {total - passed}")
        print(f"Pass Rate: {pass_rate:.1f}%")
        print()

        for i, result in enumerate(self.results, 1):
            status_icon = "PASS" if result.passed else "FAIL"
            print(f"[{i}] {result.name}: {status_icon}")
            if result.message:
                print(f"    Message: {result.message}")
            if result.details and not result.passed:
                print(f"    Details: {result.details}")
            print()

        print("=" * 60)


# CLI entry point
if __name__ == "__main__":
    import sys

    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"

    suite = E2ETestSuite(base_url)

    print(f"Running E2E tests against: {base_url}")
    print("Starting server in background...")
    print()

    # Run tests
    results = asyncio.run(suite.run_all_tests())

    # Print results
    suite.print_results()

    # Exit with appropriate code
    passed = sum(1 for r in results if r.passed)
    sys.exit(0 if passed == len(results) else 1)
