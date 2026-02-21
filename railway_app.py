"""
Railway Standalone FastAPI app - NO heavy imports.

This is a minimal backend that:
- Does NOT import torq_console package (avoids __init__.py)
- Uses httpx for all HTTP requests (no SDK dependency issues)
- Provides only the essential endpoints for Vercel→Railway proxy

Railway startup: uvicorn railway_app:app --host 0.0.0.0 --port 8080
"""

import os
import logging
import hashlib
import time
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set production flags
os.environ['TORQ_CONSOLE_PRODUCTION'] = 'true'
os.environ['TORQ_DISABLE_LOCAL_LLM'] = 'true'
os.environ['TORQ_DISABLE_GPU'] = 'true'

# Import FastAPI (lightweight, in requirements-railway.txt)
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger.info("Creating Railway standalone app...")

# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="TORQ Console Railway Backend",
    description="Agent backend with mandatory learning hook",
    version="1.0.7-standalone"
)

# CORS for Vercel proxy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Security Middleware (inline to avoid import)
# ============================================================================

PROXY_SECRET = os.environ.get("TORQ_PROXY_SHARED_SECRET", "")
ADMIN_TOKEN = os.environ.get("TORQ_ADMIN_TOKEN", "")

PROTECTED_PATHS = {"/api/chat", "/api/learning", "/api/telemetry"}
ADMIN_PATHS = {"/api/learning/policy/approve", "/api/learning/policy/rollback"}

@app.middleware("http")
async def proxy_auth_middleware(request: Request, call_next):
    """Validate proxy secret for protected endpoints."""
    path = request.url.path

    # Check if path requires proxy secret
    if any(path.startswith(p) for p in PROTECTED_PATHS):
        if PROXY_SECRET:
            provided = request.headers.get("x-torq-proxy-secret", "")
            if provided != PROXY_SECRET:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Invalid proxy secret"}
                )

    # Check admin paths
    if any(path.startswith(p) for p in ADMIN_PATHS):
        if ADMIN_TOKEN:
            auth_header = request.headers.get("authorization", "")
            token = auth_header[7:] if auth_header.startswith("Bearer ") else auth_header
            if not token or token != ADMIN_TOKEN:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Invalid admin token"}
                )

    response = await call_next(request)
    return response

# ============================================================================
# Request/Response Models
# ============================================================================

class ChatRequest(BaseModel):
    message: str
    session_id: str
    agent_id: Optional[str] = None
    trace_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class TelemetryIngest(BaseModel):
    trace: Dict[str, Any]
    spans: List[Dict[str, Any]]

class LearningPolicyUpdate(BaseModel):
    policy_id: str
    routing_data: Dict[str, Any]

# ============================================================================
# Helpers: Idempotency & Telemetry Spine
# ============================================================================

def _generate_event_id(trace_id: str, event_type: str, source_agent: str,
                       user_query: str, agent_response: str) -> str:
    """Generate deterministic event_id for idempotency."""
    hash_input = f"{trace_id}:{event_type}:{source_agent}:{user_query}:{agent_response}"
    return hashlib.sha256(hash_input.encode()).hexdigest()[:32]


def _build_telemetry_spine(trace_id: str, session_id: str, service: str,
                           git_sha: str, version: str, started_at: float,
                           ended_at: float, model_used: str, fallback_reason: str = None,
                           streaming_attempted: bool = False, streaming_success: bool = False) -> Dict[str, Any]:
    """Build telemetry spine metadata."""
    return {
        "trace_id": trace_id,
        "session_id": session_id,
        "request_chain": [{
            "service": service,
            "git_sha": git_sha,
            "version": version,
            "started_at": started_at,
            "ended_at": ended_at,
            "latency_ms": int((ended_at - started_at) * 1000),
            "model_used": model_used,
            "streaming_attempted": streaming_attempted,
            "streaming_success": streaming_success,
            "fallback_reason": fallback_reason,
            "timestamp": datetime.utcnow().isoformat()
        }]
    }


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    """Railway health check endpoint."""
    return {
        "status": "healthy",
        "service": "torq-console-railway",
        "version": "1.0.0-standalone",
        "timestamp": datetime.utcnow().isoformat(),
        "supabase_configured": bool(os.environ.get("SUPABASE_URL")),
        "anthropic_configured": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "learning_hook": "mandatory",
        "proxy_secret_required": bool(PROXY_SECRET)
    }

# ============================================================================
# Environment Debug
# ============================================================================

@app.get("/api/debug/env")
async def debug_env():
    """Debug environment variables."""
    return {
        "anthropic_key_present": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "anthropic_key_length": len(os.environ.get("ANTHROPIC_API_KEY", "")),
        "supabase_url_present": bool(os.environ.get("SUPABASE_URL")),
        "supabase_key_present": bool(os.environ.get("SUPABASE_SERVICE_ROLE_KEY")),
        "proxy_secret_set": bool(PROXY_SECRET),
        "admin_token_set": bool(ADMIN_TOKEN),
    }

# ============================================================================
# Chat Endpoint (with mandatory learning hook)
# ============================================================================

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Agent chat endpoint with mandatory learning hook.

    Uses httpx to call Anthropic API directly (no SDK dependencies).
    """
    import httpx
    import time

    trace_id = request.trace_id or f"chat-{int(time.time() * 1000)}"
    start_time = time.time()

    logger.info(f"[{trace_id}] Chat request: {request.message[:100]}...")

    # Check Anthropic API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error(f"[{trace_id}] ANTHROPIC_API_KEY not configured")
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY not configured"
        )

    # Circuit breaker: retry configuration
    MAX_RETRIES = 2
    RETRY_STATUS_CODES = {429, 503, 502}  # Rate limit, service unavailable, bad gateway
    RETRY_DELAY_MS = 1000

    anthropic_request = {
        "model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
        "max_tokens": 2000,
        "messages": [{"role": "user", "content": request.message}]
    }

    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json=anthropic_request,
                )

            # Success - break out of retry loop
            if response.status_code < 400:
                break

            # Check if status code is retryable
            if response.status_code in RETRY_STATUS_CODES and attempt < MAX_RETRIES:
                retry_after = None
                # Check for Retry-After header
                if "Retry-After" in response.headers:
                    retry_after = float(response.headers["Retry-After"])

                delay = retry_after if retry_after else (RETRY_DELAY_MS / 1000) * (attempt + 1)
                logger.warning(f"[{trace_id}] Anthropic {response.status_code}, retry {attempt + 1}/{MAX_RETRIES} after {delay}s")

                import asyncio
                await asyncio.sleep(delay)
                last_error = f"HTTP {response.status_code}"
                continue

            # Non-retryable error or max retries exceeded
            error_detail = f"Anthropic API error: {response.status_code}"
            if response.status_code == 429:
                error_detail += " (rate limit exceeded)"

            logger.error(f"[{trace_id}] {error_detail}: {response.text[:500]}")

            # Return structured error response
            return {
                "response": "",
                "session_id": request.session_id,
                "trace_id": trace_id,
                "agent": "prince_flowers",
                "backend": "railway",
                "learning_recorded": False,
                "duration_ms": int((time.time() - start_time) * 1000),
                "provider_status": response.status_code,
                "retry_after": response.headers.get("Retry-After"),
                "error": error_detail,
            }

        except httpx.TimeoutException as e:
            if attempt < MAX_RETRIES:
                logger.warning(f"[{trace_id}] Timeout, retry {attempt + 1}/{MAX_RETRIES}")
                import asyncio
                await asyncio.sleep((RETRY_DELAY_MS / 1000) * (attempt + 1))
                last_error = "timeout"
                continue
            else:
                return {
                    "response": "",
                    "session_id": request.session_id,
                    "trace_id": trace_id,
                    "agent": "prince_flowers",
                    "backend": "railway",
                    "learning_recorded": False,
                    "duration_ms": int((time.time() - start_time) * 1000),
                    "provider_status": 504,
                    "error": "Gateway timeout",
                }

        except httpx.NetworkError as e:
            last_error = f"Network error: {str(e)}"
            if attempt < MAX_RETRIES:
                logger.warning(f"[{trace_id}] {last_error}, retry {attempt + 1}/{MAX_RETRIES}")
                import asyncio
                await asyncio.sleep((RETRY_DELAY_MS / 1000) * (attempt + 1))
                continue
            else:
                return {
                    "response": "",
                    "session_id": request.session_id,
                    "trace_id": trace_id,
                    "agent": "prince_flowers",
                    "backend": "railway",
                    "learning_recorded": False,
                    "duration_ms": int((time.time() - start_time) * 1000),
                    "provider_status": 503,
                    "error": last_error,
                }

    # If we exhausted retries, return error
    if last_error:
        return {
            "response": "",
            "session_id": request.session_id,
            "trace_id": trace_id,
            "agent": "prince_flowers",
            "backend": "railway",
            "learning_recorded": False,
            "duration_ms": int((time.time() - start_time) * 1000),
            "provider_status": 503,
            "error": f"Max retries exceeded: {last_error}",
        }

    try:
        data = response.json()

        # Extract text from Claude's response
        agent_response = ""
        for part in data.get("content", []):
            if part.get("type") == "text":
                agent_response += part.get("text", "")

        logger.info(f"[{trace_id}] Anthropic response: {len(agent_response)} chars")

        # Calculate learning reward
        duration = time.time() - start_time
        reward = 0.5 + (0.1 if duration < 5 else 0)

        # Record learning event to Supabase (if configured)
        learning_recorded = False
        event_inserted = False
        event_duplicate = False
        learning_event_id = None

        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

        # Telemetry spine: build hop metadata
        end_time = time.time()
        rail_git_sha = os.environ.get("RAILWAY_GIT_COMMIT_SHA", "unknown")
        telemetry = _build_telemetry_spine(
            trace_id=trace_id,
            session_id=request.session_id,
            service="railway",
            git_sha=rail_git_sha,
            version="1.0.7-standalone",
            started_at=start_time,
            ended_at=end_time,
            model_used=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
            fallback_reason=None
        )

        if supabase_url and supabase_key:
            try:
                # #1: Idempotent learning receipt
                learning_event_id = _generate_event_id(
                    trace_id=trace_id,
                    event_type="chat_interaction",
                    source_agent="prince_flowers",
                    user_query=request.message,
                    agent_response=agent_response[:500]  # Hash first 500 chars for idempotency
                )

                # #2: Telemetry spine - store in event_data
                # Include top-level columns for analytics performance
                learning_payload = {
                    "event_id": learning_event_id,
                    "trace_id": trace_id,  # Top-level column for fast filtering
                    "session_id": request.session_id,  # Top-level column for fast filtering
                    "event_type": "chat_interaction",
                    "category": "learning",
                    "source_agent": "prince_flowers",
                    "source_trace_id": trace_id,
                    "event_data": {
                        "session_id": request.session_id,  # Keep in JSON too for compatibility
                        "user_query": request.message,
                        "agent_response": agent_response,
                        "reward": reward,
                        "duration_ms": int(duration * 1000),
                        "model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
                        "backend": "railway",
                        "telemetry": telemetry
                    },
                    "occurred_at": datetime.utcnow().isoformat(),
                    # For attempt counter (incremented on conflict)
                    "duplicate_count": 1,  # First attempt
                    "last_seen_at": datetime.utcnow().isoformat()
                }

                # Create new client for Supabase (previous client is closed)
                async with httpx.AsyncClient(timeout=10.0) as sb_client:
                    # Use INSERT ... ON CONFLICT for idempotency with attempt counter
                    # resolution=merge-duplicates will UPDATE on conflict, incrementing duplicate_count
                    learning_response = await sb_client.post(
                        f"{supabase_url}/rest/v1/learning_events",
                        headers={
                            "apikey": supabase_key,
                            "Authorization": f"Bearer {supabase_key}",
                            "Content-Type": "application/json",
                            "Prefer": "resolution=merge-duplicates",
                        },
                        json=learning_payload
                    )

                # Check if insert succeeded or was duplicate
                # 201 = created, 200 = updated (merge on conflict)
                if learning_response.status_code in (200, 201):
                    learning_recorded = True
                    # Check if it was a duplicate by looking at the response
                    response_data = learning_response.json() if learning_response.content else []
                    if isinstance(response_data, list) and len(response_data) > 0:
                        # Check duplicate_count to determine if this was a retry
                        duplicate_count = response_data[0].get("duplicate_count", 1)
                        if duplicate_count > 1:
                            event_inserted = False
                            event_duplicate = True
                            logger.info(f"[{trace_id}] Learning event: duplicate detected (attempt #{duplicate_count}), event_id={learning_event_id}")
                        else:
                            event_inserted = True
                            event_duplicate = False
                            logger.info(f"[{trace_id}] Learning event: inserted, event_id={learning_event_id}")
                    else:
                        # Empty response might mean conflict ignored
                        event_inserted = False
                        event_duplicate = True
                elif learning_response.status_code == 409:
                    # Conflict - already exists (idempotent)
                    learning_recorded = True
                    event_inserted = False
                    event_duplicate = True
                    logger.info(f"[{trace_id}] Learning event: duplicate (idempotent), event_id={learning_event_id}")
                else:
                    logger.warning(f"[{trace_id}] Learning recording failed: {learning_response.status_code} {learning_response.text[:200]}")

            except Exception as e:
                logger.warning(f"[{trace_id}] Learning recording failed: {e}")

        return {
            "response": agent_response,
            "session_id": request.session_id,
            "trace_id": trace_id,
            "agent": "prince_flowers",
            "backend": "railway",
            "learning_recorded": learning_recorded,
            "event_id": learning_event_id,
            "event_inserted": event_inserted,
            "event_duplicate": event_duplicate,
            "duration_ms": int(duration * 1000),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{trace_id}] Chat error: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)[:200]}")

# ============================================================================
# Telemetry Endpoints
# ============================================================================

@app.post("/api/telemetry")
async def ingest_telemetry(request: TelemetryIngest):
    """Ingest telemetry data - stores to Supabase."""
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        raise HTTPException(
            status_code=503,
            detail="Supabase not configured"
        )

    try:
        import httpx

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Store trace
            await client.post(
                f"{supabase_url}/rest/v1/telemetry_traces",
                headers={
                    "apikey": supabase_key,
                    "Authorization": f"Bearer {supabase_key}",
                    "Content-Type": "application/json"
                },
                json=request.trace
            )

            # Store spans
            if request.spans:
                await client.post(
                    f"{supabase_url}/rest/v1/telemetry_spans",
                    headers={
                        "apikey": supabase_key,
                        "Authorization": f"Bearer {supabase_key}",
                        "Content-Type": "application/json",
                        "Prefer": "return=minimal"
                    },
                    json=request.spans
                )

        return {
            "ok": True,
            "trace_id": request.trace.get("trace_id"),
            "spans_ingested": len(request.spans),
            "storage": "supabase"
        }
    except Exception as e:
        logger.error(f"Telemetry ingest error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/telemetry/health")
async def telemetry_health():
    """Check telemetry system health."""
    return {
        "configured": bool(os.environ.get("SUPABASE_URL")),
        "backend": "supabase"
    }

# ============================================================================
# Learning Endpoints
# ============================================================================

@app.get("/api/learning/status")
async def learning_status():
    """Get learning system status."""
    return {
        "configured": bool(os.environ.get("SUPABASE_URL")),
        "backend": "supabase",
        "mandatory_hook": True
    }

@app.post("/api/learning/policy/approve")
async def approve_policy(request: LearningPolicyUpdate):
    """Approve a new learning policy (admin only)."""
    return {"ok": True, "policy_id": request.policy_id, "status": "approved"}

@app.post("/api/learning/policy/rollback")
async def rollback_policy():
    """Rollback to previous policy (admin only)."""
    return {"ok": True, "status": "rolled_back"}

# ============================================================================
# Learning Debug (test Supabase write)
# ============================================================================

@app.get("/api/debug/learning/test")
async def test_learning_write():
    """Test Supabase learning_events write and return detailed status."""
    import httpx
    import time

    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    result = {
        "supabase_url_present": bool(supabase_url),
        "supabase_key_present": bool(supabase_key),
        "table_endpoint": f"{supabase_url}/rest/v1/learning_events" if supabase_url else None,
    }

    if not supabase_url or not supabase_key:
        result["error"] = "Supabase not configured"
        return result

    # Test write with correct schema
    test_trace = f"test-{int(time.time() * 1000)}"
    test_payload = {
        "event_id": test_trace,
        "event_type": "chat_interaction",
        "category": "learning",
        "source_agent": "prince_flowers",
        "source_trace_id": test_trace,
        "event_data": {
            "session_id": "debug-test",
            "user_query": "debug test query",
            "agent_response": "debug test response",
            "reward": 0.5,
            "test": True,
            "backend": "railway"
        },
        "occurred_at": datetime.utcnow().isoformat()
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{supabase_url}/rest/v1/learning_events",
                headers={
                    "apikey": supabase_key,
                    "Authorization": f"Bearer {supabase_key}",
                    "Content-Type": "application/json",
                    "Prefer": "return=representation",
                },
                json=test_payload
            )

        result["status_code"] = response.status_code
        result["response_body"] = response.text[:500]

        if response.status_code < 400:
            result["success"] = True
            result["trace_id"] = test_trace
        else:
            result["success"] = False
            result["error"] = f"HTTP {response.status_code}: {response.text[:200]}"

    except Exception as e:
        result["success"] = False
        result["error"] = f"{type(e).__name__}: {str(e)}"

    return result


# ============================================================================
# Deploy Info
# ============================================================================

@app.get("/api/debug/deploy")
async def deploy_info():
    """Deployment fingerprint - anti-drift detection."""
    return {
        "service": "railway-backend",
        "version": "1.0.7-standalone",
        "env": "production",
        "learning_hook": "mandatory",
        "anthropic_model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
        "supabase_configured": bool(os.environ.get("SUPABASE_URL")),
        "anthropic_configured": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "proxy_secret_required": bool(PROXY_SECRET),
        "backend": "railway",
        "timestamp": datetime.utcnow().isoformat(),
    }


def _build_stable_envelope(found: bool, query: dict, count: int, events: list, latest: dict = None) -> dict:
    """Build stable envelope for trace/event lookup responses."""
    result = {
        "found": found,
        "query": query,
        "count": count,
        "events": events,
    }
    if latest:
        result["latest"] = latest
    return result


def _validate_auth_header(auth_header: str | None) -> tuple[bool, str | None]:
    """
    Validate Authorization header for common issues.

    Returns: (is_valid, error_message)
    Detects: whitespace, newlines, truncation (PowerShell wrapping issues)
    """
    if not auth_header:
        return True, None  # No auth required for public endpoints

    # Check for whitespace/newlines (PowerShell wrapping guard)
    if "\n" in auth_header or "\r" in auth_header:
        return False, "Bearer token appears to contain newlines (PowerShell wrapping issue). Paste token without line breaks."

    # Check for unusual whitespace patterns
    if "  " in auth_header or "\t" in auth_header:
        return False, "Bearer token contains unusual whitespace. Check token formatting."

    # Basic Bearer token length sanity check (JWTs are typically 200-2000 chars)
    token = auth_header.replace("Bearer ", "").strip()
    if len(token) < 50:
        return False, f"Bearer token appears truncated (length {len(token)} < 50). Check token copy/paste."
    if len(token) > 4000:
        return False, f"Bearer token appears too long (length {len(token)} > 4000). Check for extra characters."

    return True, None


@app.get("/api/debug/trace/{trace_id}")
async def get_trace_info(trace_id: str, request: Request = None):
    """
    Trace lookup endpoint - returns all events for a trace_id.

    Stable envelope response:
    {
      "found": true,
      "query": {"trace_id": "...", "event_id": null},
      "count": 3,
      "events": [...],
      "latest": {...}
    }
    """
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        raise HTTPException(status_code=503, detail="Supabase not configured")

    # Auth validation (PowerShell wrapping guard)
    if request:
        auth_header = request.headers.get("Authorization")
        is_valid, error_msg = _validate_auth_header(auth_header)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Query by trace_id (top-level column, indexed) - returns ALL events (retries, fallbacks)
            # Fall back to source_trace_id for backward compatibility
            response = await client.get(
                f"{supabase_url}/rest/v1/learning_events",
                headers={
                    "apikey": supabase_key,
                    "Authorization": f"Bearer {supabase_key}",
                },
                params={
                    "select": "*",
                    "or": f"(trace_id.eq.{trace_id},source_trace_id.eq.{trace_id})",  # Check both columns
                    "order": "occurred_at.desc",
                    "limit": 100  # Allow many events for retries
                }
            )

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Supabase query failed")

        events = response.json()
        if not events:
            return _build_stable_envelope(
                found=False,
                query={"trace_id": trace_id, "event_id": None},
                count=0,
                events=[]
            )

        # Build enriched events list
        enriched_events = []
        for event in events:
            enriched_events.append({
                "event_id": event.get("event_id"),
                "event_type": event.get("event_type"),
                "category": event.get("category"),
                "source_agent": event.get("source_agent"),
                "occurred_at": event.get("occurred_at"),
                "duplicate_count": event.get("duplicate_count", 1),  # Attempt counter
                "last_seen_at": event.get("last_seen_at"),
                "telemetry": event.get("event_data", {}).get("telemetry"),
                "metadata": {
                    "model": event.get("event_data", {}).get("model"),
                    "duration_ms": event.get("event_data", {}).get("duration_ms"),
                    "backend": event.get("event_data", {}).get("backend"),
                }
            })

        latest = enriched_events[0] if enriched_events else None

        return _build_stable_envelope(
            found=True,
            query={"trace_id": trace_id, "event_id": None},
            count=len(enriched_events),
            events=enriched_events,
            latest=latest
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trace lookup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/debug/event/{event_id}")
async def get_event_info(event_id: str, request: Request = None):
    """
    Event lookup endpoint - returns one canonical record by event_id.

    Stable envelope response:
    {
      "found": true,
      "query": {"trace_id": null, "event_id": "..."},
      "count": 1,
      "events": [{...}],
      "latest": {...}
    }
    """
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        raise HTTPException(status_code=503, detail="Supabase not configured")

    # Auth validation (PowerShell wrapping guard)
    if request:
        auth_header = request.headers.get("Authorization")
        is_valid, error_msg = _validate_auth_header(auth_header)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Query by event_id (unique, indexed)
            response = await client.get(
                f"{supabase_url}/rest/v1/learning_events",
                headers={
                    "apikey": supabase_key,
                    "Authorization": f"Bearer {supabase_key}",
                },
                params={
                    "select": "*",
                    "event_id": f"eq.{event_id}",
                    "limit": 1
                }
            )

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Supabase query failed")

        events = response.json()
        if not events:
            return _build_stable_envelope(
                found=False,
                query={"trace_id": None, "event_id": event_id},
                count=0,
                events=[]
            )

        event = events[0]
        enriched = {
            "event_id": event.get("event_id"),
            "event_type": event.get("event_type"),
            "category": event.get("category"),
            "source_agent": event.get("source_agent"),
            "source_trace_id": event.get("source_trace_id"),
            "trace_id": event.get("trace_id"),  # Top-level column
            "session_id": event.get("session_id"),  # Top-level column
            "occurred_at": event.get("occurred_at"),
            "duplicate_count": event.get("duplicate_count", 1),  # Attempt counter
            "last_seen_at": event.get("last_seen_at"),
            "telemetry": event.get("event_data", {}).get("telemetry"),
            "user_query": event.get("event_data", {}).get("user_query"),
            "agent_response": event.get("event_data", {}).get("agent_response", "")[:500] + "...",
            "metadata": {
                "reward": event.get("event_data", {}).get("reward"),
                "model": event.get("event_data", {}).get("model"),
                "duration_ms": event.get("event_data", {}).get("duration_ms"),
                "backend": event.get("event_data", {}).get("backend"),
            }
        }

        return _build_stable_envelope(
            found=True,
            query={"trace_id": None, "event_id": event_id},
            count=1,
            events=[enriched],
            latest=enriched
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Event lookup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "TORQ Console Railway Backend",
        "status": "running",
        "backend": "railway",
        "endpoints": ["/health", "/api/chat", "/api/telemetry", "/api/learning"]
    }

logger.info("Railway standalone app created successfully")
"# trigger deploy" 
# trigger deploy for 1.0.8
