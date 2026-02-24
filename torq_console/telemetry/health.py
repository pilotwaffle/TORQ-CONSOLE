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

    Returns: 'service_role', 'anon', or 'unknown'
    """
    if not key:
        return "missing"

    # Service role keys typically start witheyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
    # Anon keys also start similarly but are shorter in practice
    # The key differentiator is in the JWT payload, but we can heuristically check

    # For diagnostic purposes, we'll classify by presence only
    # Real type detection would require JWT decoding
    return "present"  # Could be service_role or anon


def _is_service_role_key(key: str) -> bool:
    """
    Check if this looks like a service_role key by checking env var name.

    This checks the source, not the key content.
    """
    # If we're using SERVICE_ROLE_KEY env var, it's likely service_role
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    anon_key = os.environ.get("SUPABASE_ANON_KEY")

    if key == service_key and service_key:
        return True
    if key == anon_key and anon_key:
        return False

    # Default guess based on length (service_role is longer)
    return len(key) > 200 if key else False


async def _test_write_access(url: str, key: str) -> Dict[str, Any]:
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

    # Test with a lightweight read first (to validate URL/key)
    # Then attempt to understand permissions
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
                # Read works, check if we have write permissions
                # Try a minimal write attempt (will fail RLS if no write access)
                test_trace = {
                    "trace_id": "__health_check__",
                    "request_id": "__health__",
                    "agent_name": "health_check",
                    "start_ms": 0,
                    "end_ms": 1,
                    "status": "test",
                }

                write_response = await client.post(
                    f"{url}/rest/v1/telemetry_traces",
                    headers={
                        "apikey": key,
                        "Authorization": f"Bearer {key}",
                        "Content-Type": "application/json",
                        "Prefer": "return=minimal",
                    },
                    json=test_trace,
                )

                if write_response.status_code in (200, 201):
                    return {
                        "success": True,
                        "error": None,
                        "http_status": write_response.status_code,
                        "write_access": True,
                    }
                else:
                    return {
                        "success": False,
                        "error": f"write_failed_{write_response.status_code}",
                        "http_status": write_response.status_code,
                        "write_access": False,
                        "detail": write_response.text[:200],
                    }
            elif response.status_code == 401:
                return {
                    "success": False,
                    "error": "invalid_api_key",
                    "http_status": 401,
                    "hint": "Check SUPABASE_SERVICE_ROLE_KEY matches the project",
                }
            else:
                return {
                    "success": False,
                    "error": f"http_{response.status_code}",
                    "http_status": response.status_code,
                    "detail": response.text[:200],
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
            "write_test": {success: bool, error: str|null},
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

    # Run write test
    write_test = await _test_write_access(url, active_key) if url and active_key else {
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
        "write_test": write_test,
        "tables": ["telemetry_traces", "telemetry_spans"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "recommendations": _get_recommendations(write_test, key_type, project_ref),
    }


def _get_recommendations(
    write_test: Dict[str, Any],
    key_type: str,
    project_ref: Optional[str],
) -> list[str]:
    """Generate actionable recommendations based on diagnostics."""
    recommendations = []

    if write_test.get("error") == "invalid_api_key":
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

    if write_test.get("error") == "timeout":
        recommendations.append(
            "Supabase URL not reachable. Check SUPABASE_URL is correct."
        )

    if write_test.get("write_access") is False:
        recommendations.append(
            "Key has read access but not write. Use service_role key for backend."
        )

    if not project_ref:
        recommendations.append(
            "Could not parse project ref from SUPABASE_URL. Check URL format."
        )

    if not recommendations and write_test.get("success"):
        recommendations.append("Supabase telemetry is fully operational.")

    return recommendations
