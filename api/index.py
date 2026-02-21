"""
Vercel serverless function — PROXY MODE (v2.1).

Selectively proxies chat/learning/telemetry to Railway backend.
Everything else (agents list, status, sessions) stays local on Vercel for speed.

Architecture:
    Browser → Vercel (UI + selective proxy) → Railway (agent brain) → Supabase

Proxied routes (Railway):
    POST /api/chat              — full agent processing + learning
    POST /api/agents/*/chat     — agent-specific chat
    /api/telemetry/*            — telemetry endpoints
    /api/learning/*             — learning/policy endpoints

Local routes (Vercel, fast):
    GET  /api/agents            — static agent list
    GET  /api/agents/{id}       — agent info
    GET  /api/status            — system status
    GET  /api/sessions          — session list
    POST /api/sessions          — create session (stateless stub)
    GET  /health                — health check
    GET  /api/debug/deploy      — deployment fingerprint
"""

import os
import json
import logging
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Optional, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
os.environ.setdefault("TORQ_CONSOLE_PRODUCTION", "true")

logger = logging.getLogger("torq-vercel-proxy")

RAILWAY_URL = os.environ.get("TORQ_BACKEND_URL", "").rstrip("/")
PROXY_SECRET = os.environ.get("TORQ_PROXY_SHARED_SECRET", "")
PROXY_TIMEOUT = int(os.environ.get("TORQ_PROXY_TIMEOUT_MS", "25000")) / 1000

# Build fingerprint (set during deploy or from git)
BUILD_SHA = os.environ.get("VERCEL_GIT_COMMIT_SHA", "unknown")[:8]

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    context: Optional[dict[str, Any]] = None
    mode: Optional[str] = "single_agent"
    model: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    agent_id: str = "prince_flowers"
    timestamp: str
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="TORQ Console API",
    version="0.91.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _has_key(name: str) -> bool:
    val = os.environ.get(name, "")
    return bool(val and not val.startswith("@") and val != "")


def _proxy_to_railway(
    path: str,
    method: str = "GET",
    body: bytes = None,
    extra_headers: dict = None,
    query_string: str = "",
) -> dict:
    """
    Forward a request to Railway backend using stdlib urllib.
    
    Normalizes path joining, forwards trace headers, includes proxy secret.
    """
    if not RAILWAY_URL:
        raise HTTPException(status_code=503, detail="Backend not configured.")

    # Normalize: strip trailing slash from base, ensure path starts with /
    url = f"{RAILWAY_URL}{path}"
    if query_string:
        url = f"{url}?{query_string}"

    headers = {"Content-Type": "application/json"}

    if PROXY_SECRET:
        headers["x-torq-proxy-secret"] = PROXY_SECRET

    if extra_headers:
        headers.update(extra_headers)

    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=PROXY_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        logger.error(f"Railway {e.code}: {error_body[:500]}")
        raise HTTPException(status_code=e.code, detail=f"Backend error: {error_body[:200]}")
    except urllib.error.URLError as e:
        logger.error(f"Railway unreachable: {e}")
        raise HTTPException(status_code=502, detail=f"Backend unreachable: {str(e)}")
    except Exception as e:
        logger.error(f"Proxy error: {e}")
        raise HTTPException(status_code=500, detail=f"Proxy error: {str(e)}")


async def _chat_anthropic_fallback(message: str, model: str | None = None) -> str:
    """Fallback: direct Anthropic call when Railway is unavailable. No learning."""
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(
        model=model or "claude-sonnet-4-20250514",
        max_tokens=2048,
        system="You are Prince Flowers, the TORQ Console AI assistant for business consulting.",
        messages=[{"role": "user", "content": message}],
    )
    return resp.content[0].text


# ===========================================================================
# DEPLOYMENT FINGERPRINT (Fix: Add 2)
# ===========================================================================

@app.get("/api/debug/deploy")
async def deploy_fingerprint():
    """Deployment fingerprint — never guess which code is serving again."""
    return {
        "service": "vercel-proxy",
        "version": "0.91.0",
        "git_sha": os.environ.get("VERCEL_GIT_COMMIT_SHA", "unknown"),
        "git_ref": os.environ.get("VERCEL_GIT_COMMIT_REF", "unknown"),
        "env": "production" if os.environ.get("VERCEL") else "development",
        "backend_configured": bool(RAILWAY_URL),
        "backend_url_domain": RAILWAY_URL.split("//")[-1].split("/")[0] if RAILWAY_URL else None,
        "build_time": os.environ.get("VERCEL_GIT_COMMIT_DATE", "unknown"),
        "timestamp": _now_iso(),
    }


# ===========================================================================
# HEALTH CHECK (local, fast)
# ===========================================================================

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "torq-console",
        "platform": "vercel",
        "backend_configured": bool(RAILWAY_URL),
        "anthropic_configured": _has_key("ANTHROPIC_API_KEY"),
        "timestamp": _now_iso(),
    }


# ===========================================================================
# PROXIED ROUTES (→ Railway, full agent brain + learning)
# ===========================================================================

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Chat with Prince Flowers.

    PROXY MODE: Forwards to Railway where full agent runtime + learning hook runs.
    FALLBACK MODE: Direct Anthropic call (no learning, marked as degraded).
    """
    if RAILWAY_URL:
        # === PROXY to Railway ===
        # Generate a session_id for tracking
        import uuid
        session_id = str(uuid.uuid4())

        payload = json.dumps({
            "message": req.message,
            "session_id": session_id,
        }).encode("utf-8")

        result = _proxy_to_railway(
            "/api/chat",  # Railway's chat endpoint
            method="POST",
            body=payload,
        )

        return ChatResponse(
            response=result.get("response", ""),
            agent_id=result.get("agent", "prince_flowers"),
            timestamp=result.get("timestamp", _now_iso()),
            metadata={
                "backend": "railway",
                "proxy": "vercel→railway",
                "learning_recorded": result.get("learning_recorded", False),
                "trace_id": result.get("trace_id"),
                "duration_ms": result.get("duration_ms"),
            },
        )
    else:
        # === FALLBACK: Direct Anthropic (degraded, no learning) ===
        if not _has_key("ANTHROPIC_API_KEY"):
            raise HTTPException(status_code=503, detail="No backend or API key configured.")

        text = await _chat_anthropic_fallback(req.message, req.model)
        return ChatResponse(
            response=text,
            agent_id="prince_flowers",
            timestamp=_now_iso(),
            metadata={
                "backend": "vercel-direct",
                "provider": "anthropic",
                "mode": "fallback_direct",
                "learning": False,
                "degraded": True,
                "warning": "Running without learning loop — Railway backend not configured",
            },
        )


@app.post("/api/agents/{agent_id}/chat", response_model=ChatResponse)
async def agent_chat(agent_id: str, req: ChatRequest):
    """Agent-specific chat — proxied to Railway."""
    if agent_id != "prince_flowers":
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    return await chat(req)


# --- Telemetry proxy ---

@app.api_route("/api/telemetry/{path:path}", methods=["GET", "POST"])
async def proxy_telemetry(path: str, request: Request):
    """Proxy telemetry endpoints to Railway."""
    if not RAILWAY_URL:
        raise HTTPException(status_code=503, detail="Backend not configured for telemetry.")
    body = await request.body() if request.method == "POST" else None
    return _proxy_to_railway(
        f"/api/telemetry/{path}",
        method=request.method,
        body=body,
        query_string=str(request.query_params),
    )


# --- Learning proxy ---

@app.api_route("/api/learning/{path:path}", methods=["GET", "POST"])
async def proxy_learning(path: str, request: Request):
    """Proxy learning/policy endpoints to Railway."""
    if not RAILWAY_URL:
        raise HTTPException(status_code=503, detail="Backend not configured for learning.")
    body = await request.body() if request.method == "POST" else None
    # Forward authorization header for admin endpoints
    extra_headers = {}
    auth = request.headers.get("authorization")
    if auth:
        extra_headers["authorization"] = auth
    return _proxy_to_railway(
        f"/api/learning/{path}",
        method=request.method,
        body=body,
        extra_headers=extra_headers,
        query_string=str(request.query_params),
    )


# ===========================================================================
# LOCAL ROUTES (Vercel-served, fast, no Railway dependency)
# ===========================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    mode = "PROXY → Railway" if RAILWAY_URL else "DIRECT (fallback, degraded)"
    return HTMLResponse(content=f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>TORQ Console</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:system-ui;background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);
color:#e0e0e0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:2rem}}
.c{{max-width:640px;text-align:center}}
h1{{font-size:2.5rem;background:linear-gradient(90deg,#00d2ff,#7b2ff7);
-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:.5rem}}
.v{{color:#888;margin-bottom:1.5rem}}.s{{display:inline-block;padding:.3rem .8rem;border-radius:16px;
background:#1a3a1a;color:#4caf50;font-weight:600;margin-bottom:.5rem}}
.m{{color:#00d2ff;font-size:.85rem;margin-bottom:1.5rem}}
.links a{{display:inline-block;margin:.3rem;padding:.4rem .8rem;border:1px solid #00d2ff;
border-radius:6px;color:#00d2ff;text-decoration:none;font-size:.85rem}}
.links a:hover{{background:rgba(0,210,255,.15)}}
</style></head><body><div class="c">
<h1>TORQ Console</h1><p class="v">v0.91.0</p>
<div class="s">Running</div><p class="m">Mode: {mode}</p>
<div class="links">
<a href="/docs">API Docs</a><a href="/health">Health</a>
<a href="/api/debug/deploy">Deploy Info</a></div></div></body></html>""")


@app.get("/api/agents")
async def list_agents():
    """List agents — served locally from Vercel (fast)."""
    return [
        {
            "id": "prince_flowers",
            "name": "Prince Flowers",
            "description": "TORQ Business Consulting AI — market research, tax strategy, business valuation",
            "capabilities": ["general_chat", "market_research", "tax_strategy", "business_valuation", "portfolio_analysis"],
            "status": "active",
        },
        {
            "id": "query_router",
            "name": "Marvin Query Router",
            "description": "Intelligently routes queries to appropriate processing paths",
            "capabilities": ["intent_classification", "query_analysis", "agent_selection"],
            "status": "active",
        },
    ]


@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str):
    agents = {a["id"]: a for a in (await list_agents())}
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    return agents[agent_id]


@app.get("/api/status")
async def status():
    """System status — local with optional Railway health probe."""
    result = {
        "status": "healthy",
        "service": "torq-console",
        "version": "0.91.0",
        "platform": "vercel",
        "backend": "railway" if RAILWAY_URL else "vercel-direct",
        "agents_active": 2,
        "timestamp": _now_iso(),
    }
    # Optionally probe Railway health
    if RAILWAY_URL:
        try:
            backend = _proxy_to_railway("/health")
            result["backend_status"] = backend.get("status", "unknown")
        except Exception:
            result["backend_status"] = "unreachable"
    return result


@app.get("/api/sessions")
async def list_sessions():
    return []


@app.post("/api/sessions")
async def create_session(request: Request):
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    return {
        "session_id": f"vercel-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "created_at": _now_iso(),
        "agent_id": body.get("agent_id", "prince_flowers"),
        "message_count": 0,
        "status": "active",
    }
