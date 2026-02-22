"""
Railway Standalone FastAPI app - NO heavy imports.

This is a minimal backend that:
- Does NOT import torq_console package (avoids __init__.py)
- Uses httpx for all HTTP requests (no SDK dependency issues)
- Provides only the essential endpoints for Vercel->Railway proxy
- INCLUDES Drift/Regression Monitoring System

Railway startup: uvicorn railway_app:app --host 0.0.0.0 --port 8080
"""

import os
import logging
import hashlib
import time
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta

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
    description="Agent backend with mandatory learning hook and drift monitoring",
    version=APP_VERSION
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

# Monitoring Request/Response Models
class MonitoringComputeRequest(BaseModel):
    date: Optional[str] = None  # YYYY-MM-DD format, None for today
    hour: Optional[int] = None  # 0-23 for hourly, None for all hours
    update_baseline: bool = True

class MonitoringAcknowledgeRequest(BaseModel):
    alert_id: str
    acknowledged_by: str
    note: Optional[str] = None

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
        "version": APP_VERSION,
        "git_sha": _get_git_sha(),
        "timestamp": datetime.utcnow().isoformat(),
        "supabase_configured": bool(os.environ.get("SUPABASE_URL")),
        "anthropic_configured": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "learning_hook": "mandatory",
        "monitoring_enabled": True,
        "proxy_secret_required": bool(PROXY_SECRET)
    }

# ============================================================================
# Environment Debug
# ============================================================================

@app.get("/api/debug/env")
async def debug_env():
    """
    Debug environment variables - helps discover what env vars are actually available.
    Returns all env vars that might contain git/deployment info.
    """
    # All known git-related env vars
    git_env_vars = [
        "RAILWAY_GIT_COMMIT_SHA", "RAILWAY_GIT_COMMIT_HASH", "RAILWAY_COMMIT_SHA", "RAILWAY_COMMIT",
        "VERCEL_GIT_COMMIT_SHA", "GIT_COMMIT_SHA", "GIT_SHA", "COMMIT_SHA", "SOURCE_COMMIT",
        "HEROKU_SLUG_COMMIT", "BUILD_VCS_NUMBER", "CIRCLE_SHA1", "CI_COMMIT_SHA",
        "BUILD_SHA", "REVISION", "GITHUB_SHA"
    ]

    git_info = {}
    for var in git_env_vars:
        value = os.environ.get(var, "")
        if value:
            # Show first 12 chars if it's a long SHA
            display_value = value[:12] if len(value) > 12 else value
            git_info[var] = display_value

    return {
        "git_env_vars_found": git_info,
        "all_env_keys_count": len(os.environ),
        "anthropic_key_present": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "supabase_url_present": bool(os.environ.get("SUPABASE_URL")),
        "proxy_secret_set": bool(PROXY_SECRET),
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
        rail_git_sha = _get_git_sha() or "unknown"
        telemetry = _build_telemetry_spine(
            trace_id=trace_id,
            session_id=request.session_id,
            service="railway",
            git_sha=rail_git_sha,
            version=APP_VERSION,
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
-- Learning Debug (test Supabase write)
-- ============================================================================

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
-- Deploy Info (Un-fakeable fingerprint)
-- ============================================================================

def _get_git_sha() -> Optional[str]:
    """
    Get git SHA from multiple possible env vars (Railway, Vercel, generic).

    Checks in order of preference:
    1. RAILWAY_GIT_COMMIT_SHA (Railway-specific)
    2. RAILWAY_GIT_COMMIT_HASH (Railway alternative)
    3. RAILWAY_COMMIT_SHA / RAILWAY_COMMIT (other Railway variants)
    4. VERCEL_GIT_COMMIT_SHA (Vercel/Railway proxy)
    5. GIT_COMMIT_SHA / GIT_SHA (generic CI)
    6. SOURCE_COMMIT / COMMIT_SHA (some CI systems)
    7. HEROKU_SLUG_COMMIT (Heroku-style)
    8. BUILD_VCS_NUMBER (TeamCity-style)
    9. CIRCLE_SHA1 (CircleCI)

    Returns None gracefully if none found (doesn't block startup).
    """
    env_vars_to_check = [
        "RAILWAY_GIT_COMMIT_SHA",
        "RAILWAY_GIT_COMMIT_HASH",
        "RAILWAY_COMMIT_SHA",
        "RAILWAY_COMMIT",
        "VERCEL_GIT_COMMIT_SHA",
        "GIT_COMMIT_SHA",
        "GIT_SHA",
        "COMMIT_SHA",
        "SOURCE_COMMIT",
        "HEROKU_SLUG_COMMIT",
        "BUILD_VCS_NUMBER",
        "CIRCLE_SHA1",
    ]

    for env_var in env_vars_to_check:
        sha = os.environ.get(env_var, "").strip()
        if sha and sha != "" and sha != "unknown":
            # Return first 8-12 chars (short SHA) for readability
            return sha[:12]

    return None


def _get_deployment_id() -> Optional[str]:
    """Get deployment ID from env vars."""
    for env_var in ["RAILWAY_DEPLOYMENT_ID", "VERCEL_DEPLOYMENT_ID", "DEPLOYMENT_ID"]:
        deployment_id = os.environ.get(env_var, "").strip()
        if deployment_id and deployment_id != "":
            return deployment_id
    return None


# Single source of truth for version
APP_VERSION = "1.0.9-standalone"
APP_BUILD_TIME = os.environ.get("APP_BUILD_TIME", datetime.utcnow().isoformat())

# Build metadata from build_meta.json (committed with repo)
_BUILD_METADATA = None
try:
    import pathlib
    build_meta_path = pathlib.Path(__file__).parent.parent / "torq_console" / "build_meta.json"
    if build_meta_path.exists():
        with open(build_meta_path) as f:
            _BUILD_METADATA = json.load(f)
except Exception:
    pass  # Graceful fallback if file missing


@app.get("/api/debug/deploy")
async def deploy_info():
    """
    Deployment fingerprint - anti-drift detection.

    Returns un-fakeable proof of what code is running:
    - app_version: Semantic version for humans
    - git_sha: Immutable commit identifier from build_meta.json (most reliable)
    - deployment_id: Deployment run identifier (if available)
    - build_time: When this build was created
    - container_start_time: When this container started (proves new deployment)
    """
    # Get git SHA from build_meta.json (most reliable source)
    git_sha = _get_git_sha()  # From env vars
    build_meta_git_sha = None

    if _BUILD_METADATA:
        build_meta_git_sha = _BUILD_METADATA.get("git_short_sha") or _BUILD_METADATA.get("git_sha", "")[:12]

    # Prefer build_meta.json over env vars (it's committed with the code)
    git_sha = build_meta_git_sha or git_sha

    deployment_id = _get_deployment_id()

    return {
        # Human-readable version
        "app_version": APP_VERSION,

        # Machine-readable immutable proof (from build_meta.json)
        "git_sha": git_sha,
        "git_commit_message": _BUILD_METADATA.get("commit_message") if _BUILD_METADATA else None,
        "build_branch": _BUILD_METADATA.get("branch") if _BUILD_METADATA else None,

        # Deployment tracking
        "deployment_id": deployment_id,
        "build_time": _BUILD_METADATA.get("built_at") if _BUILD_METADATA else APP_BUILD_TIME,
        "container_start_time": APP_BUILD_TIME,  # When this container image was built

        # Service identification
        "service": "railway-backend",
        "env": "production",

        # Feature flags
        "learning_hook": "mandatory",
        "monitoring_enabled": True,
        "proxy_secret_required": bool(PROXY_SECRET),

        # Integration status
        "anthropic_model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
        "supabase_configured": bool(os.environ.get("SUPABASE_URL")),
        "anthropic_configured": bool(os.environ.get("ANTHROPIC_API_KEY")),

        # Current runtime
        "backend": "railway",
        "timestamp": datetime.utcnow().isoformat(),

        # Fingerprint hash (for quick comparison)
        "fingerprint": f"{APP_VERSION}-{git_sha or 'unknown'}-{deployment_id or 'unknown'}",
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

# ============================================================================
-- MONITORING ENDPOINTS (Drift/Regression Detection)
-- ============================================================================

def _get_supabase_client():
    """Get Supabase URL and key for requests."""
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not supabase_key:
        raise HTTPException(
            status_code=503,
            detail="Supabase not configured"
        )
    return supabase_url, supabase_key


async def _execute_supabase_function(
    function_name: str,
    params: dict = None
) -> dict:
    """Execute a PostgreSQL function via Supabase RPC."""
    supabase_url, supabase_key = _get_supabase_client()

    import httpx
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{supabase_url}/rest/v1/rpc/{function_name}",
            headers={
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}",
                "Content-Type": "application/json",
            },
            json=params or {}
        )

    if response.status_code not in (200, 201):
        logger.error(f"Function {function_name} failed: {response.status_code} {response.text}")
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Function execution failed: {response.text[:200]}"
        )

    return response.json()


@app.get("/api/monitor/summary")
async def get_monitoring_summary(
    window: str = "7d",
    include_hourly: bool = False
):
    """
    Get monitoring summary for drift/regression detection.

    Parameters:
    - window: Time window (1d, 7d, 30d) - default 7d
    - include_hourly: Include hourly breakdown

    Returns:
    {
        "window": {"start_date": "...", "end_date": "...", "days": 7},
        "metrics": {
            "total_events": 1234,
            "avg_fallback_rate": 0.05,
            "avg_error_rate": 0.01,
            "avg_health_score": 85.5,
            "latest": {...}
        },
        "baseline": {
            "fallback_rate": 0.04,
            "error_rate": 0.01,
            "latency_p95": 2500,
            "valid_until": "..."
        },
        "trends": {"fallback_rate": "up", "latency_p95": "stable"},
        "alerts": {"total_open": 2, "by_severity": {...}, "recent": [...]},
        "generated_at": "..."
    }
    """
    # Parse window
    window_days = 7
    if window.endswith("d"):
        window_days = int(window[:-1])
    elif window.endswith("h"):
        window_days = int(window[:-1]) / 24

    supabase_url, supabase_key = _get_supabase_client()
    start_date = (datetime.now(timezone.utc) - timedelta(days=window_days)).strftime("%Y-%m-%d")

    import httpx
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Fetch daily metrics
        metrics_response = await client.get(
            f"{supabase_url}/rest/v1/mv_daily_metrics",
            headers={
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}",
            },
            params={
                "metric_date": f"gte.{start_date}",
                "order": "metric_date.desc",
            }
        )

        # Fetch alerts
        alerts_response = await client.get(
            f"{supabase_url}/rest/v1/monitoring_alerts",
            headers={
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}",
            },
            params={
                "metric_date": f"gte.{start_date}",
                "order": "created_at.desc",
            }
        )

        # Fetch baseline
        baseline_response = await client.get(
            f"{supabase_url}/rest/v1/monitoring_baseline",
            headers={
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}",
            },
            params={"baseline_name": "eq.7day_rolling"}
        )

    metrics = metrics_response.json() if metrics_response.status_code == 200 else []
    alerts = alerts_response.json() if alerts_response.status_code == 200 else []
    baseline = baseline_response.json() if baseline_response.status_code == 200 else []
    baseline_data = baseline[0] if baseline else {}

    # Calculate summary stats
    total_events = sum(m.get("total_events", 0) for m in metrics)
    avg_fallback_rate = sum(m.get("fallback_rate", 0) for m in metrics) / max(len(metrics), 1)
    avg_error_rate = sum(m.get("error_rate", 0) for m in metrics) / max(len(metrics), 1)
    avg_health_score = sum(m.get("health_score", 0) for m in metrics) / max(len(metrics), 1)

    # Alert summary
    open_alerts = [a for a in alerts if a.get("status") == "open"]
    alerts_by_severity = {}
    for alert in open_alerts:
        severity = alert.get("severity", "unknown")
        alerts_by_severity[severity] = alerts_by_severity.get(severity, 0) + 1

    # Trend calculation (compare last 3 days to previous 3)
    if len(metrics) >= 6:
        recent = metrics[:3]
        previous = metrics[3:6]

        recent_fallback = sum(m.get("fallback_rate", 0) for m in recent) / 3
        previous_fallback = sum(m.get("fallback_rate", 0) for m in previous) / 3
        fallback_trend = "up" if recent_fallback > previous_fallback * 1.1 else "down" if recent_fallback < previous_fallback * 0.9 else "stable"

        recent_latency = sum(m.get("latency_p95", 0) or 0 for m in recent) / 3
        previous_latency = sum(m.get("latency_p95", 0) or 0 for m in previous) / 3
        latency_trend = "up" if recent_latency > previous_latency * 1.1 else "down" if recent_latency < previous_latency * 0.9 else "stable"
    else:
        fallback_trend = "unknown"
        latency_trend = "unknown"

    return {
        "window": {
            "start_date": start_date,
            "end_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "days": len(metrics),
        },
        "metrics": {
            "total_events": total_events,
            "avg_fallback_rate": round(avg_fallback_rate, 4),
            "avg_error_rate": round(avg_error_rate, 4),
            "avg_health_score": round(avg_health_score, 2),
            "latest": metrics[0] if metrics else None,
        },
        "baseline": {
            "fallback_rate": baseline_data.get("baseline_fallback_rate"),
            "error_rate": baseline_data.get("baseline_error_rate"),
            "latency_p95": baseline_data.get("baseline_latency_p95"),
            "valid_until": baseline_data.get("valid_until"),
        },
        "trends": {
            "fallback_rate": fallback_trend,
            "latency_p95": latency_trend,
        },
        "alerts": {
            "total_open": len(open_alerts),
            "by_severity": alerts_by_severity,
            "recent": alerts[:5] if alerts else [],
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/monitor/alerts")
async def get_monitoring_alerts(
    threshold: str = "medium",
    status: str = "open",
    limit: int = 50
):
    """
    Get monitoring alerts filtered by threshold.

    Parameters:
    - threshold: Minimum severity level (low, medium, high, critical)
    - status: Alert status filter (open, acknowledged, resolved, ignored)
    - limit: Maximum number of alerts to return

    Returns:
    {
        "alerts": [...],
        "total_count": 10,
        "filtered_by": {"threshold": "medium", "status": "open"}
    }
    """
    severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    min_severity_level = severity_order.get(threshold, 1)

    supabase_url, supabase_key = _get_supabase_client()

    import httpx
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{supabase_url}/rest/v1/monitoring_alerts",
            headers={
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}",
            },
            params={
                "status": f"eq.{status}",
                "order": "created_at.desc",
                "limit": limit * 2,  # Fetch extra for filtering
            }
        )

    if response.status_code != 200:
        logger.error(f"Failed to fetch alerts: {response.status_code}")
        return {
            "alerts": [],
            "total_count": 0,
            "filtered_by": {"threshold": threshold, "status": status},
            "error": f"HTTP {response.status_code}"
        }

    all_alerts = response.json()

    # Filter by severity threshold
    filtered = []
    for alert in all_alerts:
        alert_severity = alert.get("severity", "low")
        if severity_order.get(alert_severity, 0) >= min_severity_level:
            filtered.append(alert)
            if len(filtered) >= limit:
                break

    return {
        "alerts": filtered,
        "total_count": len(filtered),
        "filtered_by": {"threshold": threshold, "status": status},
    }


@app.post("/api/monitor/compute")
async def compute_monitoring_metrics(request: MonitoringComputeRequest):
    """
    Trigger manual metric computation and drift detection.

    Parameters:
    - date: Target date (YYYY-MM-DD), None for today
    - hour: Specific hour (0-23), None for all hours/full day
    - update_baseline: Whether to update baseline after computation

    Returns:
    {
        "metrics_computed": true,
        "rows_computed": 24,
        "metrics_inserted": 24,
        "baseline_updated": true,
        "drift_check": {...},
        "computation_time_ms": 1234
    }
    """
    start_time = time.time()

    target_date = request.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Execute metric computation function
    try:
        if request.hour is not None:
            # Compute specific hour
            result = await _execute_supabase_function(
                "compute_hourly_metrics",
                {"p_target_date": target_date, "p_target_hour": request.hour}
            )
        else:
            # Compute full day (all hours)
            result = await _execute_supabase_function(
                "compute_daily_metrics",
                {"p_target_date": target_date}
            )

        # Handle different result formats (single row vs table result)
        if isinstance(result, list) and len(result) > 0:
            result = result[0]

        rows_computed = result.get("rows_computed", 0) if isinstance(result, dict) else 1
        metrics_inserted = result.get("metrics_inserted", 0) if isinstance(result, dict) else 1

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Metric computation failed: {e}")
        return {
            "metrics_computed": False,
            "error": str(e),
            "computation_time_ms": int((time.time() - start_time) * 1000)
        }

    # Update baseline if requested
    baseline_updated = False
    baseline_data = None
    if request.update_baseline:
        try:
            baseline_data = await _execute_supabase_function("update_baseline", {})
            baseline_updated = True
        except Exception as e:
            logger.warning(f"Baseline update failed: {e}")

    # Run drift detection
    drift_check = {}
    try:
        drift_result = await _execute_supabase_function(
            "check_drift_and_alert",
            {
                "p_baseline_name": "7day_rolling",
                "p_threshold_low": 1.5,
                "p_threshold_medium": 2.0,
                "p_threshold_high": 3.0
            }
        )

        if isinstance(drift_result, list) and len(drift_result) > 0:
            drift_result = drift_result[0]

        drift_check = {
            "alerts_created": drift_result.get("alerts_created", 0) if isinstance(drift_result, dict) else 0,
            "alert_ids": drift_result.get("alert_ids", []) if isinstance(drift_result, dict) else []
        }
    except Exception as e:
        logger.warning(f"Drift check failed: {e}")
        drift_check = {"error": str(e)}

    # Refresh materialized view if we computed today's metrics
    view_refreshed = False
    if target_date >= datetime.now(timezone.utc).strftime("%Y-%m-%d"):
        try:
            await _execute_supabase_function("refresh_daily_metrics_mv", {})
            view_refreshed = True
        except Exception as e:
            logger.warning(f"Materialized view refresh failed: {e}")

    return {
        "metrics_computed": True,
        "target_date": target_date,
        "target_hour": request.hour,
        "rows_computed": rows_computed,
        "metrics_inserted": metrics_inserted,
        "baseline_updated": baseline_updated,
        "baseline_data": baseline_data,
        "view_refreshed": view_refreshed,
        "drift_check": drift_check,
        "computation_time_ms": int((time.time() - start_time) * 1000),
    }


@app.post("/api/monitor/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, request: MonitoringAcknowledgeRequest):
    """
    Acknowledge an alert.

    Parameters:
    - alert_id: UUID of the alert to acknowledge
    - acknowledged_by: Name/user acknowledging
    - note: Optional note for the acknowledgment

    Returns:
    {
        "alert_id": "...",
        "status": "acknowledged",
        "acknowledged_at": "...",
        "acknowledged_by": "..."
    }
    """
    supabase_url, supabase_key = _get_supabase_client()

    import httpx
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.patch(
            f"{supabase_url}/rest/v1/monitoring_alerts?id=eq.{alert_id}",
            headers={
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}",
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            },
            json={
                "status": "acknowledged",
                "acknowledged_at": datetime.now(timezone.utc).isoformat(),
                "acknowledged_by": request.acknowledged_by,
                "resolution_note": request.note,
            }
        )

    if response.status_code not in (200, 201):
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to acknowledge alert: {response.text[:200]}"
        )

    data = response.json()
    if data and len(data) > 0:
        return data[0]
    return {"alert_id": alert_id, "status": "acknowledged"}


@app.post("/api/monitor/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str, request: MonitoringAcknowledgeRequest):
    """
    Resolve an alert.

    Returns:
    {
        "alert_id": "...",
        "status": "resolved",
        "resolved_at": "..."
    }
    """
    supabase_url, supabase_key = _get_supabase_client()

    import httpx
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.patch(
            f"{supabase_url}/rest/v1/monitoring_alerts?id=eq.{alert_id}",
            headers={
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}",
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            },
            json={
                "status": "resolved",
                "resolved_at": datetime.now(timezone.utc).isoformat(),
                "resolution_note": request.note,
            }
        )

    if response.status_code not in (200, 201):
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to resolve alert: {response.text[:200]}"
        )

    data = response.json()
    if data and len(data) > 0:
        return data[0]
    return {"alert_id": alert_id, "status": "resolved"}


@app.get("/api/monitor/baseline")
async def get_monitoring_baseline():
    """
    Get current monitoring baseline values.

    Returns:
    {
        "baseline_name": "7day_rolling",
        "window_days": 7,
        "fallback_rate": 0.05,
        "error_rate": 0.01,
        "latency_p95": 2500,
        "valid_until": "...",
        "last_computed": "..."
    }
    """
    supabase_url, supabase_key = _get_supabase_client()

    import httpx
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{supabase_url}/rest/v1/monitoring_baseline",
            headers={
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}",
            },
            params={"baseline_name": "eq.7day_rolling", "limit": 1}
        )

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch baseline")

    data = response.json()
    if not data:
        return {"error": "No baseline found"}

    baseline = data[0]
    return {
        "baseline_name": baseline.get("baseline_name"),
        "window_days": baseline.get("baseline_window_days"),
        "fallback_rate": baseline.get("baseline_fallback_rate"),
        "error_rate": baseline.get("baseline_error_rate"),
        "duplicate_rate": baseline.get("baseline_duplicate_rate"),
        "latency_p50": baseline.get("baseline_latency_p50"),
        "latency_p95": baseline.get("baseline_latency_p95"),
        "latency_p99": baseline.get("baseline_latency_p99"),
        "baseline_start_date": baseline.get("baseline_start_date"),
        "baseline_end_date": baseline.get("baseline_end_date"),
        "valid_until": baseline.get("valid_until"),
        "last_computed": baseline.get("computed_at"),
    }


@app.get("/api/monitor/metrics/daily")
async def get_daily_metrics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 30
):
    """
    Get daily metrics for a date range.

    Parameters:
    - start_date: Start date (YYYY-MM-DD), defaults to 30 days ago
    - end_date: End date (YYYY-MM-DD), defaults to today
    - limit: Maximum records to return

    Returns:
    {
        "metrics": [...],
        "count": 30
    }
    """
    if not start_date:
        start_date = (datetime.now(timezone.utc) - timedelta(days=limit)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    supabase_url, supabase_key = _get_supabase_client()

    import httpx
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{supabase_url}/rest/v1/mv_daily_metrics",
            headers={
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}",
            },
            params={
                "metric_date": f"gte.{start_date}",
                "metric_date": f"lte.{end_date}",
                "order": "metric_date.desc",
                "limit": limit,
            }
        )

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch metrics")

    return {
        "metrics": response.json(),
        "count": len(response.json()),
        "start_date": start_date,
        "end_date": end_date,
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "TORQ Console Railway Backend",
        "status": "running",
        "backend": "railway",
        "version": APP_VERSION,
        "git_sha": _get_git_sha(),
        "endpoints": [
            "/health",
            "/api/chat",
            "/api/telemetry",
            "/api/learning",
            "/api/monitor/summary",
            "/api/monitor/alerts",
            "/api/monitor/compute",
            "/api/monitor/baseline",
            "/api/monitor/metrics/daily",
        ]
    }

logger.info("Railway standalone app created successfully")
# trigger deploy for 1.0.9



