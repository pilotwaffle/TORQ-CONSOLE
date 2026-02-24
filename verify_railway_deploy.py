#!/usr/bin/env python3
"""
TORQ Console Railway Deployment Verification Script

Usage:
    # Verify Railway direct access
    python verify_railway_deploy.py https://<railway-url>.up.railway.app

    # Verify via Vercel proxy
    python verify_railway_deploy.py https://torq-console.vercel.app --via-proxy

    # Verify both in one run
    python verify_railway_deploy.py https://<railway-url>.up.railway.app https://torq-console.vercel.app

This script validates that the deployment is running the expected code with:
1. Correct git_sha (matches expected commit)
2. torq-deploy-v1 contract structure
3. New telemetry health fields (key_type_detected, key_source, access_test)
4. Supabase project ref matches expected value
5. Vercel proxy relay works (end-to-end validation)

Exit codes:
    0 - All checks passed
    1 - Critical failure (endpoint missing)
    2 - Git SHA mismatch
    3 - Contract violation
    4 - Telemetry health failed
    5 - Vercel proxy relay failed
"""

import sys
import json
import urllib.request
import urllib.error
from typing import Any, Dict, Optional

# ANSI color codes
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    CYAN = '\033[0;36m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color

# Expected values - update these when deploying new commits
EXPECTED_SHA = "92070874"              # control-plane-v1-clean with deployment guide
EXPECTED_PROJECT_REF = "npukynbaglmcdvzyklqa"
EXPECTED_SCHEMA = "torq-deploy-v1"
EXPECTED_KEY_TYPE = "service_role"
EXPECTED_KEY_SOURCE = "SUPABASE_SERVICE_ROLE_KEY"

# Parse arguments
VIAPROXY_MODE = "--via-proxy" in sys.argv

# Determine URLs based on mode
if VIAPROXY_MODE:
    # --via-proxy mode: verify Vercel proxy only
    RAILWAY_URL = None
    VERCEL_URL = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != "--via-proxy" else "https://torq-console.vercel.app"
    VERIFY_MODE = "via-proxy"
else:
    # Default mode: verify Railway direct (and optionally Vercel too)
    RAILWAY_URL = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("http") else (
        sys.argv[1] if len(sys.argv) > 1 else "https://web-production-74ed0.up.railway.app"
    )
    VERCEL_URL = sys.argv[2] if len(sys.argv) > 2 else None
    VERIFY_MODE = "direct"

exit_code = 0


def header(text: str) -> None:
    """Print a section header."""
    print()
    print("=" * 70)
    print(f"{Colors.CYAN}{text}{Colors.NC}")
    print("=" * 70)


def pass_msg(text: str) -> None:
    """Print a success message."""
    print(f"{Colors.GREEN}[PASS] {text}{Colors.NC}")


def fail_msg(text: str, code: int) -> None:
    """Print a failure message and set exit code."""
    global exit_code
    print(f"{Colors.RED}[FAIL] {text}{Colors.NC}")
    exit_code = code


def warn_msg(text: str) -> None:
    """Print a warning message."""
    print(f"{Colors.YELLOW}[WARN] {text}{Colors.NC}")


def info_msg(text: str) -> None:
    """Print an info message."""
    print(f"{Colors.CYAN}[INFO] {text}{Colors.NC}")


def fetch_json(url: str, timeout: int = 10) -> Dict[str, Any]:
    """Fetch and parse JSON from a URL."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return json.loads(response.read().decode())
    except urllib.error.URLError as e:
        raise Exception(f"URL error: {e}")
    except json.JSONDecodeError as e:
        raise Exception(f"JSON decode error: {e}")


def get_nested(data: Dict[str, Any], *keys, default=None) -> Any:
    """Safely get nested dictionary values."""
    result = data
    for key in keys:
        if isinstance(result, dict):
            result = result.get(key)
            if result is None:
                return default
        else:
            return default
    return result


def verify_url(url: str, mode: str) -> int:
    """
    Verify a single URL (either Railway direct or Vercel proxy).

    Returns exit code for this verification.
    """
    global exit_code
    local_exit_code = 0

    print()
    print(f"{Colors.BOLD}Verifying: {url}{Colors.NC}")
    print(f"{Colors.CYAN}Mode: {mode}{Colors.NC}")
    print()

    # ========================================================================
    # Test 1: Health Check (basic liveness)
    # ========================================================================
    header("Test 1: Health Check (/health)")

    try:
        health = fetch_json(f"{url}/health")
        print(json.dumps(health, indent=2)[:500] + "...")
    except Exception as e:
        fail_msg(f"Health check endpoint unreachable: {e}", 1)
        return 1

    # Check for schema version
    schema = get_nested(health, "_schema")
    if schema == EXPECTED_SCHEMA:
        pass_msg(f"Health check returns {EXPECTED_SCHEMA} schema")
    else:
        fail_msg(f"Missing or incorrect _schema: {schema}", 3)
        local_exit_code = 3

    # Check git_sha (critical - confirms we're running new code)
    git_sha = get_nested(health, "git_sha")
    if git_sha:
        if EXPECTED_SHA in git_sha:
            pass_msg(f"Git SHA matches: {git_sha}")
        else:
            fail_msg(f"Git SHA mismatch: {git_sha} (expected: {EXPECTED_SHA})", 2)
            local_exit_code = 2
    else:
        warn_msg("Could not extract git_sha from health endpoint")
    print()

    # ========================================================================
    # Test 2: Deploy Info (detailed contract validation)
    # ========================================================================
    header("Test 2: Deploy Info (/api/debug/deploy)")

    try:
        deploy = fetch_json(f"{url}/api/debug/deploy")
        print(json.dumps(deploy, indent=2)[:800] + "...")
    except Exception as e:
        fail_msg(f"Deploy endpoint unreachable: {e}", 1)
        print()
        return 1

    print()

    # Validate contract structure
    deploy_schema = get_nested(deploy, "_schema")
    if deploy_schema == EXPECTED_SCHEMA:
        pass_msg(f"Deploy endpoint schema: {deploy_schema}")
    else:
        fail_msg(f"Deploy endpoint schema mismatch: {deploy_schema}", 3)
        local_exit_code = 3

    # Validate git_sha from deploy endpoint
    deploy_git_sha = get_nested(deploy, "git_sha")
    if deploy_git_sha:
        if EXPECTED_SHA in deploy_git_sha:
            pass_msg(f"Deploy git_sha matches: {deploy_git_sha}")
        else:
            fail_msg(f"Deploy git_sha mismatch: {deploy_git_sha} (expected: {EXPECTED_SHA})", 2)
            local_exit_code = 2
    else:
        fail_msg("Could not extract git_sha from deploy endpoint", 2)
        local_exit_code = 2

    # Validate platform
    platform = get_nested(deploy, "platform")
    if mode == "via-proxy":
        # Via proxy, platform should still report railway
        if platform == "railway":
            pass_msg(f"Proxy correctly relays Railway platform")
        else:
            warn_msg(f"Unexpected platform via proxy: {platform}")
    else:
        if platform == "railway":
            pass_msg(f"Platform detected: railway")
        else:
            warn_msg(f"Unexpected platform: {platform}")
    print()

    # ========================================================================
    # Test 3: Telemetry Health (key_type_detected validation)
    # ========================================================================
    header("Test 3: Telemetry Health (/api/telemetry/health)")

    try:
        telemetry = fetch_json(f"{url}/api/telemetry/health")
        print(json.dumps(telemetry, indent=2))
    except Exception as e:
        fail_msg(f"Telemetry health endpoint unreachable: {e}", 4)
        print()
        return 4

    print()

    # Extract fields
    project_ref = get_nested(telemetry, "supabase_project_ref")
    key_type = get_nested(telemetry, "key_type_detected")
    key_source = get_nested(telemetry, "key_source")
    access_status = get_nested(telemetry, "access_test", "status")
    http_status = get_nested(telemetry, "access_test", "http_status")
    tables = get_nested(telemetry, "tables")

    # Check if new fields exist (this confirms new code is running)
    if not key_type:
        fail_msg("key_type_detected field missing - running old code!", 4)
        local_exit_code = 4
    else:
        info_msg(f"key_type_detected present: {key_type}")

    if not key_source:
        fail_msg("key_source field missing - running old code!", 4)
        local_exit_code = 4
    else:
        info_msg(f"key_source present: {key_source}")

    if not access_status:
        fail_msg("access_test field missing - running old code!", 4)
        local_exit_code = 4
    else:
        info_msg(f"access_test present: {access_status}")

    # Validate values
    if project_ref == EXPECTED_PROJECT_REF:
        pass_msg(f"Supabase project ref: {project_ref}")
    else:
        fail_msg(f"Supabase project ref mismatch: {project_ref} (expected: {EXPECTED_PROJECT_REF})", 4)
        local_exit_code = 4

    if key_type == EXPECTED_KEY_TYPE:
        pass_msg(f"key_type_detected: {key_type}")
    else:
        warn_msg(f"key_type_detected: {key_type} (expected: {EXPECTED_KEY_TYPE})")

    if key_source == EXPECTED_KEY_SOURCE:
        pass_msg(f"key_source: {key_source}")
    else:
        warn_msg(f"key_source: {key_source} (expected: {EXPECTED_KEY_SOURCE})")

    if access_status == "healthy" and http_status == 200:
        pass_msg(f"access_test: {access_status} (HTTP {http_status})")
    else:
        fail_msg(f"access_test: {access_status} (HTTP {http_status})", 4)
        local_exit_code = 4

    # Check tables
    if tables and "telemetry_traces" in tables:
        pass_msg("telemetry_traces table configured")
    else:
        warn_msg("telemetry_traces not in tables list")

    if tables and "telemetry_spans" in tables:
        pass_msg("telemetry_spans table configured")
    else:
        warn_msg("telemetry_spans not in tables list")
    print()

    return local_exit_code


def main() -> int:
    global exit_code

    header("TORQ Console Deployment Verification")
    print(f"{Colors.BOLD}Expected Git SHA: {EXPECTED_SHA}{Colors.NC}")
    print(f"{Colors.BOLD}Expected Project Ref: {EXPECTED_PROJECT_REF}{Colors.NC}")
    print()

    # Verify Railway direct access
    if RAILWAY_URL:
        header("PART 1: Railway Direct Access")
        exit_code = verify_url(RAILWAY_URL, "direct")

    # Verify Vercel proxy (if specified)
    if VERCEL_URL:
        header("PART 2: Vercel Proxy Relay")
        vercel_code = verify_url(VERCEL_URL, "via-proxy")
        if vercel_code != 0:
            exit_code = vercel_code

    # ========================================================================
    # Summary
    # ========================================================================
    header("Verification Summary")

    if exit_code == 0:
        pass_msg("All checks passed!")
        print()
        print("Deployment is running:")
        print(f"  - Branch: control-plane-v1-clean")
        print(f"  - Commit: {EXPECTED_SHA}")
        print(f"  - Schema: {EXPECTED_SCHEMA}")
        print("  - Telemetry diagnostics: ACTIVE")
        print(f"  - Supabase project: {EXPECTED_PROJECT_REF}")
        print()

        if VIAPROXY_MODE or VERCEL_URL:
            print("Both Railway direct AND Vercel proxy paths verified!")
            print()
        print("[OK] Ready for production traffic")
    else:
        warn_msg("Some checks failed - review output above")
        print()
        print("Common issues:")
        print("  - Git SHA mismatch: Railway hasn't picked up latest commit")
        print("  - Missing fields: Old branch still deployed")
        print("  - Proxy failing: Vercel rewrites misconfigured")
        print()
        print("Fix: In Railway dashboard, change watched branch to control-plane-v1-clean")
        print("     and click Redeploy.")

    print()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
