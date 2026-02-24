#!/usr/bin/env python3
"""
TORQ Console - Control Plane Smoke Test Suite

Validates deployment health after every deploy.
Usage: python scripts/smoke_control_plane.py
Exit: 0 = all pass, 1 = any fail
"""

import os
import sys
import json
import urllib.request
import urllib.error
from typing import Any, Dict

# Configuration
VERCEL_URL = os.getenv("VERCEL_URL", "https://torq-console.vercel.app")
RAILWAY_URL = os.getenv("RAILWAY_URL", "https://web-production-74ed0.up.railway.app")
EXPECTED_SHA = os.getenv("EXPECTED_SHA", "")

# ANSI colors
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
NC = "\033[0m"

# Test counters
tests_passed = 0
tests_failed = 0


def log_info(msg: str) -> None:
    print(f"{YELLOW}[INFO]{NC} {msg}")


def log_pass(msg: str) -> None:
    global tests_passed
    print(f"{GREEN}[PASS]{NC} {msg}")
    tests_passed += 1


def log_fail(msg: str) -> None:
    global tests_failed
    print(f"{RED}[FAIL]{NC} {msg}")
    tests_failed += 1


def fetch(url: str, timeout: int = 15) -> Dict[str, Any]:
    """Fetch JSON from URL."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}"}
    except urllib.error.URLError as e:
        return {"error": f"URL error: {e}"}
    except Exception as e:
        return {"error": str(e)}


def json_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Get value from dict with default."""
    return data.get(key, default)


def json_has_key(data: Dict[str, Any], key: str) -> bool:
    """Check if dict has non-null key."""
    return key in data and data[key] is not None


def main() -> int:
    print("=" * 50)
    print("TORQ Console - Control Plane Smoke Test")
    print("=" * 50)
    print(f"Vercel: {VERCEL_URL}")
    print(f"Railway: {RAILWAY_URL}")
    print(f"Expected SHA: {EXPECTED_SHA or '<not specified>'}")
    print("=" * 50)
    print()

    # Test 1: Vercel Health
    log_info("Test 1: Vercel /health")
    health = fetch(f"{VERCEL_URL}/health")
    if json_get(health, "status") == "healthy":
        log_pass("Vercel /health returns healthy")
    else:
        log_fail(f"Vercel /health not healthy: {health}")
    print()

    # Test 2: Railway Health
    log_info("Test 2: Railway /health")
    health = fetch(f"{RAILWAY_URL}/health")
    if json_get(health, "status") == "healthy":
        log_pass("Railway /health returns healthy")
    else:
        log_fail(f"Railway /health not healthy: {health}")
    print()

    # Test 3: Vercel Deploy Identity
    log_info("Test 3: Vercel /api/debug/deploy identity")
    deploy = fetch(f"{VERCEL_URL}/api/debug/deploy")
    git_sha = json_get(deploy, "git_sha", "")

    if git_sha and git_sha != "unknown":
        log_pass(f"Vercel has git_sha: {git_sha[:8]}...")
    else:
        log_fail("Vercel missing git_sha or 'unknown'")

    # SHA mismatch check (FAIL HARD)
    if EXPECTED_SHA and git_sha != EXPECTED_SHA:
        log_fail(f"SHA MISMATCH: expected {EXPECTED_SHA[:8]}..., got {git_sha[:8] if git_sha else 'none'}...")
        print()
        print("=" * 50)
        print(f"{RED}CRITICAL: Deploy SHA mismatch!{NC}")
        print("=" * 50)
        return 1
    elif EXPECTED_SHA:
        log_pass(f"SHA matches expected: {EXPECTED_SHA[:8]}...")
    print()

    # Test 4: Railway Deploy Identity (torq-deploy-v1 contract)
    log_info("Test 4: Railway /api/debug/deploy identity (torq-deploy-v1)")
    deploy = fetch(f"{RAILWAY_URL}/api/debug/deploy")
    git_sha = json_get(deploy, "git_sha", "")
    schema = json_get(deploy, "_schema", "")

    if schema == "torq-deploy-v1":
        log_pass("Railway uses torq-deploy-v1 schema")
    else:
        log_fail(f"Railway schema not torq-deploy-v1: {schema}")

    if git_sha and git_sha != "unknown":
        log_pass(f"Railway has git_sha: {git_sha[:8]}...")
    else:
        log_fail("Railway missing git_sha or 'unknown'")

    # SHA mismatch check
    if EXPECTED_SHA and git_sha != EXPECTED_SHA:
        log_fail(f"SHA MISMATCH: expected {EXPECTED_SHA[:8]}..., got {git_sha[:8] if git_sha else 'none'}...")
        print()
        print("=" * 50)
        print(f"{RED}CRITICAL: Deploy SHA mismatch!{NC}")
        print("=" * 50)
        return 1
    elif EXPECTED_SHA:
        log_pass(f"SHA matches expected: {EXPECTED_SHA[:8]}...")
    print()

    # Test 5: Vercel Proxy - Learning Status
    log_info("Test 5: Vercel /api/learning/status (proxy to Railway)")
    learning = fetch(f"{VERCEL_URL}/api/learning/status")

    if "error" in learning:
        log_fail(f"Returns error: {learning['error']}")
    elif json_get(learning, "configured"):
        log_pass("Learning status returns configured=true")
    else:
        log_fail(f"Learning not configured: {learning}")
    print()

    # Test 6: Vercel Proxy - Telemetry Health
    log_info("Test 6: Vercel /api/telemetry/health (proxy to Railway)")
    telemetry = fetch(f"{VERCEL_URL}/api/telemetry/health")

    if "error" in telemetry:
        log_fail(f"Backend error from proxy: {telemetry['error']}")
    elif json_get(telemetry, "configured"):
        log_pass("Telemetry health returns configured=true")
    else:
        log_fail(f"Telemetry not configured: {telemetry}")
    print()

    # Test 7: Vercel Proxy - Traces List
    log_info("Test 7: Vercel /api/traces?limit=5 (proxy to Railway)")
    traces = fetch(f"{VERCEL_URL}/api/traces?limit=5")

    count = json_get(traces, "count", 0)
    if count > 0:
        log_pass(f"Traces API returns {count} traces")
    elif "error" in traces:
        log_fail(f"Traces API error: {traces['error']}")
    else:
        log_fail(f"Traces API returns no data: {traces}")
    print()

    # Summary
    print("=" * 50)
    print("Smoke Test Summary")
    print("=" * 50)
    print(f"Passed: {GREEN}{tests_passed}{NC}")
    print(f"Failed: {RED}{tests_failed}{NC}")
    print()

    if tests_failed == 0:
        print(f"{GREEN}All tests passed!{NC}")
        print("=" * 50)
        return 0
    else:
        print(f"{RED}Some tests failed!{NC}")
        print("=" * 50)
        return 1


if __name__ == "__main__":
    sys.exit(main())
