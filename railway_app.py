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
from typing import Optional, Dict, Any, List
from datetime import datetime

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
    version="1.0.0"
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

    try:
        # Use httpx to call Anthropic API directly
        anthropic_request = {
            "model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": request.message}]
        }

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

        if response.status_code >= 400:
            logger.error(f"[{trace_id}] Anthropic error {response.status_code}: {response.text[:500]}")
            raise HTTPException(
                status_code=500,
                detail=f"Anthropic API error: {response.status_code}"
            )

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
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

        if supabase_url and supabase_key:
            try:
                # Map to existing learning_events table schema
                learning_payload = {
                    "event_id": trace_id,
                    "event_type": "chat_interaction",
                    "category": "learning",
                    "source_agent": "prince_flowers",
                    "source_trace_id": trace_id,
                    "event_data": {
                        "session_id": request.session_id,
                        "user_query": request.message,
                        "agent_response": agent_response,
                        "reward": reward,
                        "duration_ms": int(duration * 1000),
                        "model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
                        "backend": "railway",
                    },
                    "occurred_at": datetime.utcnow().isoformat()
                }

                learning_response = await client.post(
                    f"{supabase_url}/rest/v1/learning_events",
                    headers={
                        "apikey": supabase_key,
                        "Authorization": f"Bearer {supabase_key}",
                        "Content-Type": "application/json",
                        "Prefer": "return=representation",
                    },
                    json=learning_payload
                )

                if learning_response.status_code < 400:
                    learning_recorded = True
                    logger.info(f"[{trace_id}] Learning event recorded: reward={reward:.3f}")
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
        "version": "1.0.4-standalone",
        "env": "production",
        "learning_hook": "mandatory",
        "anthropic_model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
        "supabase_configured": bool(os.environ.get("SUPABASE_URL")),
        "anthropic_configured": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "proxy_secret_required": bool(PROXY_SECRET),
        "backend": "railway",
        "timestamp": datetime.utcnow().isoformat(),
    }

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
