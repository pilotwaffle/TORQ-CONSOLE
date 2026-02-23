"""
Railway Standalone FastAPI app - NO heavy imports.

This is a minimal backend that:
- Does NOT import torq_console package (avoids __init__.py)
- Does NOT trigger any LLM provider imports
- Provides only the essential endpoints for Vercel→Railway proxy

Railway startup: uvicorn torq_console.ui.railway_standalone:app --host 0.0.0.0 --port 8080
"""

import os
import sys
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
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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
async def proxy_auth_middleware(request, call_next):
    """Validate proxy secret for protected endpoints."""
    path = request.url.path

    # Check if path requires proxy secret
    if any(path.startswith(p) for p in PROTECTED_PATHS):
        if PROXY_SECRET:
            provided = request.headers.get("x-torq-proxy-secret", "")
            if provided != PROXY_SECRET:
                return HTTPException(status_code=403, detail="Invalid proxy secret")

    # Check admin paths
    if any(path.startswith(p) for p in ADMIN_PATHS):
        if ADMIN_TOKEN:
            auth_header = request.headers.get("authorization", "")
            token = auth_header[7:] if auth_header.startswith("Bearer ") else auth_header
            if not token or token != ADMIN_TOKEN:
                return HTTPException(status_code=403, detail="Invalid admin token")

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
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "supabase_configured": bool(os.environ.get("SUPABASE_URL")),
        "anthropic_configured": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "learning_hook": "mandatory"
    }

# ============================================================================
# Chat Endpoint (with mandatory learning hook)
# ============================================================================

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Agent chat endpoint with mandatory learning hook.

    This is a simplified version that:
    1. Calls Anthropic API directly (no heavy agent imports)
    2. Records learning event to Supabase
    """
    import anthropic
    import time

    trace_id = request.trace_id or f"chat-{int(time.time() * 1000)}"
    start_time = time.time()

    logger.info(f"[{trace_id}] Chat request: {request.message[:100]}...")

    # Check Anthropic API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY not configured"
        )

    try:
        # Create Anthropic client and call
        client = anthropic.Anthropic(api_key=api_key)

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": request.message}]
        )

        agent_response = response.content[0].text

        # Calculate learning reward
        duration = time.time() - start_time
        reward = 0.5 + (0.1 if duration < 5 else 0)  # Simple reward function

        # Record learning event to Supabase (if configured)
        learning_recorded = False
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

        if supabase_url and supabase_key:
            try:
                import httpx

                learning_payload = {
                    "trace_id": trace_id,
                    "session_id": request.session_id,
                    "agent_name": "prince_flowers",
                    "user_query": request.message,
                    "agent_response": agent_response,
                    "reward": reward,
                    "metadata": {
                        "duration_ms": int(duration * 1000),
                        "model": "claude-sonnet-4-20250514",
                    }
                }

                async def record_learning():
                    async with httpx.AsyncClient() as client:
                        await client.post(
                            f"{supabase_url}/rest/v1/learning_events",
                            headers={
                                "apikey": supabase_key,
                                "Authorization": f"Bearer {supabase_key}",
                                "Content-Type": "application/json"
                            },
                            json=learning_payload
                        )

                await record_learning()
                learning_recorded = True
                logger.info(f"[{trace_id}] Learning event recorded: reward={reward:.3f}")

            except Exception as e:
                logger.warning(f"[{trace_id}] Learning recording failed: {e}")

        return {
            "response": agent_response,
            "session_id": request.session_id,
            "trace_id": trace_id,
            "agent": "prince_flowers",
            "learning_recorded": learning_recorded,
            "duration_ms": int(duration * 1000),
        }

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

        # Ingest traces
        async with httpx.AsyncClient() as client:
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
    # Simplified - just acknowledge
    return {"ok": True, "policy_id": request.policy_id, "status": "approved"}

@app.post("/api/learning/policy/rollback")
async def rollback_policy():
    """Rollback to previous policy (admin only)."""
    return {"ok": True, "status": "rolled_back"}

# ============================================================================
# Deploy Info
# ============================================================================

@app.get("/api/debug/deploy")
async def deploy_info():
    """Deployment fingerprint."""
    return {
        "service": "railway-backend",
        "version": "1.0.0-standalone",
        "env": "production",
        "learning_hook": "mandatory",
        "supabase_configured": bool(os.environ.get("SUPABASE_URL")),
        "anthropic_configured": bool(os.environ.get("ANTHROPIC_API_KEY")),
    }

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "TORQ Console Railway Backend",
        "status": "running",
        "endpoints": ["/health", "/api/chat", "/api/telemetry", "/api/learning"]
    }

logger.info("Railway standalone app created successfully")
