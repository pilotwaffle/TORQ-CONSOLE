"""
Telemetry storage module for TORQ Console.

Provides direct Supabase access for telemetry traces and spans.
Used by Railway backend to query and expose telemetry data via the Trace Explorer API.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")


async def _query_supabase(
    table: str,
    filters: Dict[str, Any] = None,
    limit: int = 100,
    offset: int = 0,
    order: str = "created_at.desc"
) -> List[Dict[str, Any]]:
    """Query Supabase table with optional filters and pagination."""
    import httpx

    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Supabase not configured")

    # Build SELECT parameters
    select_params = ["*"]

    # Add filters
    if filters:
        for key, value in filters.items():
            if isinstance(value, str):
                select_params.append(f"{key}=eq.{value}")
            elif isinstance(value, bool):
                select_params.append(f"{key}={str(value).lower()}")
            else:
                select_params.append(f"{key}=cs.{value}")

    # Build params
    params = {
        "select": ",".join(select_params),
        "limit": limit,
        "offset": offset,
        "order": order,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
            params=params,
        )
        response.raise_for_status()
        return response.json()


async def _get_single_supabase(
    table: str,
    id_field: str,
    id_value: str,
) -> Optional[Dict[str, Any]]:
    """Get single record from Supabase by ID field."""
    import httpx

    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Supabase not configured")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
            params={id_field: f"eq.{id_value}", "limit": 1},
        )
        response.raise_for_status()
        data = response.json()
        return data[0] if data else None


async def list_traces(
    filters: Dict[str, Any] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """List telemetry traces with filtering."""
    return await _query_supabase("telemetry_traces", filters, limit, offset)


async def get_trace(trace_id: str) -> Optional[Dict[str, Any]]:
    """Get a single trace by trace_id."""
    return await _get_single_supabase("telemetry_traces", "trace_id", trace_id)


async def get_trace_spans(
    trace_id: str,
    limit: int = 500,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """Get all spans for a trace."""
    return await _query_supabase(
        "telemetry_spans",
        {"trace_id": trace_id},
        limit,
        offset,
        order="start_ms.asc",  # Spans ordered by start time for timeline
    )


async def get_telemetry_health() -> Dict[str, Any]:
    """Check telemetry system health."""
    return {
        "configured": bool(SUPABASE_URL and SUPABASE_KEY),
        "backend": "supabase",
        "tables": ["telemetry_traces", "telemetry_spans"],
    }


async def supabase_ingest(
    trace: Dict[str, Any],
    spans: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Ingest telemetry data into Supabase."""
    import httpx

    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Supabase not configured")

    results = {}

    # Store trace
    if trace:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{SUPABASE_URL}/rest/v1/telemetry_traces",
                headers={
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {SUPABASE_KEY}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal",
                },
                json=trace,
            )
            response.raise_for_status()
            results["trace"] = response.json()

    # Store spans
    if spans:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{SUPABASE_URL}/rest/v1/telemetry_spans",
                headers={
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {SUPABASE_KEY}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal",
                },
                json=spans,
            )
            response.raise_for_status()
            results["spans"] = response.json()

    return results
