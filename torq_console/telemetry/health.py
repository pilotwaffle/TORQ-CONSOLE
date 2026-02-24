"""
Telemetry Health Diagnostics

Provides deterministic diagnostics for Supabase connectivity and configuration.
This makes "wrong key" or "wrong project" impossible to miss.

Usage:
    from torq_console.telemetry.health import get_telemetry_diagnostics

    diagnostics = await get_telemetry_diagnostics()
    # Returns: supabase_project_ref, key_type_detected, write_test_result
"""

import os
import re
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _parse_project_ref(url: str) -> Optional[str]:
    """Extract Supabase project ref from URL."""
    if not url:
        return None
    match = re.search(r'//([^.]+)\.supabase\.co', url)
    return match.group(1) if match else None


def _detect_key_type(key: str) -> str:
    """
    Detect Supabase key type from prefix.

    Returns: 'service_role', 'anon', or 'missing'
    """
    if not key:
        return "missing"

    # Check the source (env var name) for more accurate detection
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    anon_key = os.environ.get("SUPABASE_ANON_KEY")

    if key == service_key and service_key:
        return "service_role"
    if key == anon_key and anon_key:
        return "anon"

    # Fallback: check by JWT structure (service_role has "role": "service_role")
    # This would require JWT decoding, so we use a heuristic
    return "unknown"


async def _test_access(url: str, key: str) -> Dict[str, Any]:
    """
    Test write access to Supabase with a minimal, best-effort check.

    Returns: {success: bool, error: str|None, http_status: int|None}
    """
    import httpx

    if not url or not key:
        return {
            "success": False,
            "error": "missing_credentials",
            "http_status": None,
        }

    # Test with a lightweight read (validates URL + key + table exists)
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Try to read telemetry_traces table (validates URL + key)
            response = await client.get(
                f"{url}/rest/v1/telemetry_traces",
                headers={
                    "apikey": key,
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                params={"select": "trace_id", "limit": 1},
            )

            if response.status_code == 200:
                # Read successful - basic connectivity works
                return {
                    "success": True,
                    "error": None,
                    "http_status": response.status_code,
                    "read_access": True,
                    "status": "healthy",
                }
            elif response.status_code == 401:
                return {
                    "success": False,
                    "error": "invalid_api_key",
                    "http_status": 401,
                    "hint": "Check SUPABASE_SERVICE_ROLE_KEY matches the project",
                    "status": "misconfigured",
                }
            else:
                # Check for PGRST204 schema cache error
                detail = response.text[:200]
                if "PGRST204" in detail or "schema cache" in detail.lower():
                    return {
                        "success": False,
                        "error": "schema_cache",
                        "http_status": response.status_code,
                        "hint": "Reload schema cache in Supabase dashboard > API",
                        "status": "misconfigured",
                    }
                return {
                    "success": False,
                    "error": f"http_{response.status_code}",
                    "http_status": response.status_code,
                    "detail": detail,
                    "status": "degraded",
                }

    except httpx.TimeoutException:
        return {
            "success": False,
            "error": "timeout",
            "http_status": None,
            "hint": "Supabase URL not reachable",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e).__class__.__name__,
            "http_status": None,
            "detail": str(e)[:200],
        }


async def get_telemetry_diagnostics() -> Dict[str, Any]:
    """
    Get comprehensive telemetry system diagnostics.

    Returns:
        {
            "supabase_project_ref": str|null,
            "supabase_url": str,
            "key_type_detected": "service_role"|"anon"|"missing",
            "key_source": "SUPABASE_SERVICE_ROLE_KEY"|"SUPABASE_ANON_KEY"|...,
            "key_prefix": str|null (first 20 chars for verification),
            "access_test": {success: bool, error: str|null, http_status: int|null},
            "tables": ["telemetry_traces", "telemetry_spans"],
            "timestamp": str,
        }
    """
    # Get configuration
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    anon_key = os.environ.get("SUPABASE_ANON_KEY")

    # Determine which key is being used
    active_key = service_key or anon_key
    key_source = (
        "SUPABASE_SERVICE_ROLE_KEY" if service_key else
        "SUPABASE_ANON_KEY" if anon_key else
        "none"
    )

    # Detect key type
    key_type = "missing"
    if service_key:
        key_type = "service_role"
    elif anon_key:
        key_type = "anon"

    # Parse project ref
    project_ref = _parse_project_ref(url) if url else None

    # Run access test (read-only, safe for schema drift)
    access_test = await _test_access(url, active_key) if url and active_key else {
        "success": False,
        "error": "no_credentials",
        "http_status": None,
    }

    return {
        "supabase_project_ref": project_ref,
        "supabase_url": url or "not_set",
        "key_type_detected": key_type,
        "key_source": key_source,
        "key_prefix": (active_key[:20] + "...") if active_key else None,
        "access_test": access_test,
        "tables": ["telemetry_traces", "telemetry_spans"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "recommendations": _get_recommendations(access_test, key_type, project_ref),
    }


def _get_recommendations(
    access_test: Dict[str, Any],
    key_type: str,
    project_ref: Optional[str],
) -> list[str]:
    """Generate actionable recommendations based on diagnostics."""
    recommendations = []

    error = access_test.get("error")

    if error == "invalid_api_key":
        if key_type == "anon":
            recommendations.append(
                "Using anon key. Set SUPABASE_SERVICE_ROLE_KEY for backend write access."
            )
        recommendations.append(
            f"Check that SUPABASE_SERVICE_ROLE_KEY matches project {project_ref or 'YOUR_PROJECT'}"
        )
        recommendations.append(
            "Regenerate service_role key in Supabase dashboard > Settings > API"
        )

    elif error == "schema_cache":
        recommendations.append(
            "PostgREST schema cache is stale. In Supabase dashboard: API > Reload schema cache"
        )
        recommendations.append(
            f"Verify migration was applied to project {project_ref or 'YOUR_PROJECT'}"
        )

    if error == "timeout":
        recommendations.append(
            "Supabase URL not reachable. Check SUPABASE_URL is correct."
        )

    if access_test.get("read_access") and access_test.get("success"):
        recommendations.append("Supabase telemetry is fully operational.")

    if not project_ref and access_test.get("error") != "no_credentials":
        recommendations.append(
            "Could not parse project ref from SUPABASE_URL. Check URL format."
        )

    return recommendations
