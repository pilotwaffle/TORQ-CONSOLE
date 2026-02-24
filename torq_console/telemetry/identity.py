"""
Deploy Identity Module - Mandatory deploy stamping for telemetry.

Ensures all telemetry writes include deploy identity fields:
- deploy_git_sha: The exact git commit SHA
- deploy_platform: Where this is running (vercel/railway/local)
- deploy_app_version: Application version string
- deploy_version_source: How version was determined (package/git/env)
- deploy_timestamp: When this deployment started

This module provides get_deploy_identity() which MUST be called
before any telemetry write. The identity is auto-injected by
supabase_ingest_with_identity() to prevent missing data.
"""

import os
from typing import Dict, Any
from datetime import datetime, timezone


def _get_git_sha() -> str:
    """Get git SHA from environment or git command."""
    # Try env vars first (set by CI platforms)
    if sha := os.getenv("RAILWAY_GIT_COMMIT_SHA"):
        return sha[:8]
    if sha := os.getenv("VERCEL_GIT_COMMIT_SHA"):
        return sha[:8]
    if sha := os.getenv("GITHUB_SHA"):
        return sha[:8]

    # Try git command (local dev)
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass

    return "unknown"


def _get_platform() -> str:
    """Detect deployment platform."""
    if os.getenv("RAILWAY_STATIC_URL"):
        return "railway"
    if os.getenv("VERCEL"):
        return "vercel"
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        return "aws"
    return "local"


def _get_app_version() -> str:
    """Get application version."""
    # Try environment first
    if version := os.getenv("TORQ_APP_VERSION"):
        return version

    # Try reading from build metadata
    try:
        from torq_console.build_meta import BUILD_VERSION
        return BUILD_VERSION
    except ImportError:
        pass

    return "0.0.0-dev"


def _get_version_source() -> str:
    """Determine how version was sourced."""
    if os.getenv("TORQ_APP_VERSION"):
        return "env"
    try:
        from torq_console.build_meta import BUILD_VERSION
        return "package"
    except ImportError:
        pass
    return "default"


def get_deploy_identity() -> Dict[str, str]:
    """
    Get mandatory deploy identity for telemetry stamping.

    This function MUST be called before any telemetry write.
    The returned dict should be merged into trace/spans data.

    Returns:
        Dict with deploy identity fields:
        - deploy_git_sha: Git commit SHA (8 chars)
        - deploy_platform: Platform (vercel/railway/aws/local)
        - deploy_app_version: Version string
        - deploy_version_source: How version was determined
        - deploy_timestamp: ISO timestamp of identity request
    """
    return {
        "deploy_git_sha": _get_git_sha(),
        "deploy_platform": _get_platform(),
        "deploy_app_version": _get_app_version(),
        "deploy_version_source": _get_version_source(),
        "deploy_timestamp": datetime.now(timezone.utc).isoformat(),
    }


def stamp_trace_with_identity(trace: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inject deploy identity into a trace dict.

    Ensures all traces have deploy identity fields before writing.
    If fields already exist, they are NOT overwritten (caller wins).

    Args:
        trace: Trace data dict (will be modified in-place)

    Returns:
        The same trace dict with identity fields added
    """
    identity = get_deploy_identity()
    for key, value in identity.items():
        if key not in trace:  # Don't overwrite existing values
            trace[key] = value
    return trace


def stamp_spans_with_identity(spans: list) -> list:
    """
    Inject deploy identity into all spans.

    Ensures all spans have deploy identity fields before writing.

    Args:
        spans: List of span dicts (modified in-place)

    Returns:
        The same spans list with identity fields added
    """
    identity = get_deploy_identity()
    for span in spans:
        for key, value in identity.items():
            if key not in span:  # Don't overwrite existing values
                span[key] = value
    return spans


async def supabase_ingest_with_identity(
    trace: Dict[str, Any],
    spans: list = None,
) -> Dict[str, Any]:
    """
    Ingest telemetry with MANDATORY deploy identity stamping.

    This is the preferred way to write telemetry. It automatically
    injects deploy identity fields before writing to Supabase,
    ensuring governance even if callers forget.

    Args:
        trace: Trace data (identity will be auto-injected)
        spans: Optional list of spans (identity will be auto-injected)

    Returns:
        Dict with write results

    Raises:
        ValueError: If Supabase not configured
        httpx.HTTPStatusError: If write fails
    """
    from torq_console.telemetry import supabase_ingest

    # Auto-inject identity (MANDATORY)
    trace = stamp_trace_with_identity(trace.copy())
    if spans:
        spans = stamp_spans_with_identity([s.copy() for s in spans])

    return await supabase_ingest(trace, spans)
