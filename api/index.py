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
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from pydantic import BaseModel, Field
import asyncio

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

# Railway proxy configuration
RAILWAY_URL = os.environ.get("TORQ_BACKEND_URL", "").rstrip("/")
PROXY_SECRET = os.environ.get("TORQ_PROXY_SHARED_SECRET", "")
PROXY_TIMEOUT = int(os.environ.get("TORQ_PROXY_TIMEOUT_MS", "25000")) / 1000

logger.info(f"Railway proxy configured: {bool(RAILWAY_URL)}")

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

_SYSTEM_PROMPT = """You are Prince Flowers, the TORQ Console AI assistant.
You are an action-oriented AI that helps with software engineering tasks.

For research/search requests: Provide information directly.
For build/implementation requests: Ask 2-3 clarifying questions first.

Be concise, helpful, and accurate."""

import time
BOOT_TIME = time.time()


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
    """Forward request to Railway backend using stdlib urllib."""
    if not RAILWAY_URL:
        raise HTTPException(status_code=503, detail="Backend not configured.")

    import urllib.request
    import urllib.error

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


async def _chat_anthropic(message: str, model: str | None = None) -> str:
    """Send a chat message via Anthropic SDK (blocking)."""
    import anthropic

    async with anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"]) as client:
        resp = await client.messages.create(
            model=model or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
            max_tokens=2048,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": message}],
        )
        return resp.content[0].text


async def _stream_anthropic(message: str, model: str | None = None):
    """Stream chat via Anthropic SDK (async generator)."""
    import anthropic

    async with anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"]) as client:
        async with client.messages.stream(
            model=model or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
            max_tokens=2048,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": message}],
        ) as stream:
            async for text in stream.text_stream:
                yield text


async def _chat_openai(message: str, model: str | None = None) -> str:
    """Send a chat message via OpenAI SDK (blocking)."""
    import openai

    async with openai.AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"]) as client:
        resp = await client.chat.completions.create(
            model=model or "gpt-4o",
            max_tokens=2048,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
        )
        return resp.choices[0].message.content


async def _stream_openai(message: str, model: str | None = None):
    """Stream chat via OpenAI SDK (async generator)."""
    import openai

    async with openai.AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"]) as client:
        stream = await client.chat.completions.create(
            model=model or "gpt-4o",
            max_tokens=2048,
            stream=True,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


async def token_stream(message: str, model: str | None = None, provider: str = "none"):
    """Generator for SSE token stream."""
    start_time = time.time()

    try:
        stream_gen = None
        if provider == "anthropic":
            stream_gen = _stream_anthropic(message, model)
        elif provider == "openai":
            stream_gen = _stream_openai(message, model)
        
        if stream_gen:
            async for token in stream_gen:
                yield f"data: {json.dumps({'token': token})}\\n\\n"

        latency_ms = (time.time() - start_time) * 1000
        cold_start_ms = (start_time - BOOT_TIME) * 1000 if (time.time() - BOOT_TIME) < 10.0 else 0

        meta = {
            "latency_ms": latency_ms,
            "provider": provider,
            "cold_start_ms": cold_start_ms,
            "timestamp": _now_iso()
        }
        
        yield f"data: {json.dumps({'meta': meta})}\\n\\n"
        yield "data: [DONE]\\n\\n"

    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\\n\\n"
        yield "data: [DONE]\\n\\n"

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

# ===========================================================================
# DEPLOYMENT FINGERPRINT (anti-drift detection)
# ===========================================================================

@app.get("/api/debug/deploy")
async def deploy_fingerprint():
    """Deployment fingerprint - instantly know what code is live."""
    return {
        "service": "vercel-proxy",
        "version": "0.91.0",
        "git_sha": os.environ.get("VERCEL_GIT_COMMIT_SHA", "unknown"),
        "git_ref": os.environ.get("VERCEL_GIT_COMMIT_REF", "unknown"),
        "env": "production" if os.environ.get("VERCEL") else "development",
        "backend_configured": bool(RAILWAY_URL),
        "backend_url_domain": RAILWAY_URL.split("//")[-1].split("/")[0] if RAILWAY_URL else None,
        "proxy_secret_set": bool(PROXY_SECRET),
        "anthropic_model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
        "build_time": os.environ.get("VERCEL_GIT_COMMIT_DATE", "unknown"),
        "timestamp": _now_iso(),
    }


# ===========================================================================
# PROXIED ROUTES (→ Railway, full agent brain + learning)
# ===========================================================================

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Chat with Prince Flowers.

    PROXY MODE: Forwards to Railway where full agent + learning runs.
    FALLBACK MODE: Direct Anthropic/OpenAI call (no learning, EXPLICITLY marked).
    """
    import uuid
    trace_id = f"vercel-{int(time.time() * 1000)}"
    proxy_start = time.time()

    # Try Railway proxy first
    if RAILWAY_URL:
        session_id = str(uuid.uuid4())

        payload = json.dumps({
            "message": req.message,
            "session_id": session_id,
            "trace_id": trace_id,
        }).encode("utf-8")

        try:
            result = _proxy_to_railway(
                "/api/chat",  # Railway's endpoint
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
                    "degraded": False,
                },
            )
        except HTTPException as e:
            # === EXPLICIT FALLBACK: Railway failed, log telemetry ===
            proxy_latency_ms = int((time.time() - proxy_start) * 1000)
            fallback_reason = f"railway_{e.status_code}" if hasattr(e, 'status_code') else "railway_unreachable"
            logger.error(f"[{trace_id}] PROXY_FALLBACK: {fallback_reason}, latency_ms={proxy_latency_ms}")

    # Fallback: direct Anthropic/OpenAI call
    provider = "none"
    try:
        if _has_key("ANTHROPIC_API_KEY"):
            provider = "anthropic"
            text = await _chat_anthropic(req.message, req.model)
        elif _has_key("OPENAI_API_KEY"):
            provider = "openai"
            text = await _chat_openai(req.message, req.model)
        else:
            raise HTTPException(
                status_code=503,
                detail="No API key configured. Set ANTHROPIC_API_KEY or OPENAI_API_KEY in Vercel Dashboard > Settings > Environment Variables.",
            )
    except HTTPException:
        raise
    except Exception as exc:
        import traceback
        print("CHAT_API_ERROR:", repr(exc))
        print(traceback.format_exc())
        logger.exception("Chat error")
        raise HTTPException(status_code=500, detail=f"Chat error ({provider}): {exc}")

    return ChatResponse(
        response=text,
        agent_id="prince_flowers",
        timestamp=_now_iso(),
        metadata={
            "backend": "vercel-direct",
            "provider": provider,
            "mode": req.mode or "single_agent",
            "model": req.model or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
            "platform": "vercel",
            "success": True,
            "learning": False,
            "degraded": True,
            "fallback_reason": getattr(locals(), 'fallback_reason', 'no_backend_configured'),
            "trace_id": trace_id,
        },
    )


@app.post("/api/chat/stream", response_class=StreamingResponse)
async def chat_stream(req: ChatRequest):
    """
    Stream chat response (SSE) - Phase 1 Feature.
    Enabled via TORQ_STREAMING_ENABLED env var.
    """
    if os.environ.get("TORQ_STREAMING_ENABLED", "false").lower() != "true":
        raise HTTPException(status_code=400, detail="Streaming is currently disabled via feature flag.")

    provider = "none"
    if _has_key("ANTHROPIC_API_KEY"):
        provider = "anthropic"
    elif _has_key("OPENAI_API_KEY"):
        provider = "openai"
    else:
        raise HTTPException(
            status_code=503,
            detail="No API key configured.",
        )

    return StreamingResponse(
        token_stream(req.message, req.model, provider),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Torq-Provider": provider,
        },
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
        "agents_active": 1,
        "anthropic_configured": _has_key("ANTHROPIC_API_KEY"),
        "openai_configured": _has_key("OPENAI_API_KEY"),
        "streaming_enabled": os.environ.get("TORQ_STREAMING_ENABLED", "false").lower() == "true",
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
